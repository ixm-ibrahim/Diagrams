/* Phase 7: nutrient threshold section.
 *
 * Mode selector (Filter / Highlight / Score) at the top, then a dual-handle
 * range slider per nutrient (all 8: calories, carbs, protein, fiber, fat,
 * sodium, sugar, saturated_fat). Sliders are in real per-100g units; their
 * min/max bounds come from the dataset envelope.
 *
 * Modes (the visual effect is wired in main.js → points.js):
 *   filter — items outside [min, max] on any nutrient are hidden.
 *   score  — items are colored by RMS distance from each nutrient's
 *            target (the midpoint of [min, max]). The legend swaps
 *            to a green→red gradient bar.
 *
 * State coupling: source of truth is state.thresholds + state.thresholdMode.
 * Sliders write to state on input; state subscriber updates sliders if
 * thresholds change externally (e.g., reset, URL-hash load).
 *
 * Dual-handle implementation: two `<input type="range">` overlapped. The
 * min handle owns the lower thumb, the max handle the upper thumb. We
 * enforce min ≤ max by clamping on every input event.
 */

import { NUTRIENT_FIELDS, NUTRIENT_META } from '../data/schema.js';
import { defaultThresholds, isThresholdsAtDefaults } from '../core/scoring.js';
import { createRailSection } from './left-rail.js';

const MODES = [
  { key: 'filter', label: 'Filter', tooltip: 'Hide ingredients/meals whose values fall outside any threshold range.' },
  { key: 'score',  label: 'Score',  tooltip: 'Color each item by how close it is to the midpoint of every threshold range — green = close, red = far.' },
];

/* Tester feedback: preset nutrition profiles at the top of the section.
 * Each profile is a partial constraint map (per-100g values) that gets
 * applied on top of the dataset-default thresholds. Multiple profiles
 * can be active at once; the combine mode decides which value wins per
 * nutrient when two profiles target the same one. The values follow
 * common nutrition-label conventions (FDA "high-fiber" ≥6g/100g, etc.)
 * — they're starting points, not gospel; the user can fine-tune
 * individual sliders after applying. */
const PROFILES = [
  { key: 'keto',         label: 'Keto',         tooltip: 'Very-low-carb, high-fat: carbs ≤ 10 g/100g, fat ≥ 20 g/100g.',
    constraints: { carbs: { max: 10 }, fat: { min: 20 } } },
  { key: 'low-carb',     label: 'Low-carb',     tooltip: 'Carbs ≤ 20 g/100g.',
    constraints: { carbs: { max: 20 } } },
  { key: 'low-cal',      label: 'Low-cal',      tooltip: 'Calories ≤ 150 kcal/100g.',
    constraints: { calories: { max: 150 } } },
  { key: 'high-protein', label: 'High-protein', tooltip: 'Protein ≥ 15 g/100g.',
    constraints: { protein: { min: 15 } } },
  { key: 'low-fat',      label: 'Low-fat',      tooltip: 'Fat ≤ 5 g/100g (FDA "low-fat" cutoff is 3 g/serving — close enough at typical servings).',
    constraints: { fat: { max: 5 } } },
  { key: 'low-sodium',   label: 'Low-sodium',   tooltip: 'Sodium ≤ 140 mg/100g (FDA "low-sodium" definition).',
    constraints: { sodium: { max: 140 } } },
  { key: 'high-fiber',   label: 'High-fiber',   tooltip: 'Fiber ≥ 6 g/100g (FDA "high-fiber" definition).',
    constraints: { fiber: { min: 6 } } },
  { key: 'low-sugar',    label: 'Low-sugar',    tooltip: 'Sugar ≤ 5 g/100g.',
    constraints: { sugar: { max: 5 } } },
];
const PROFILE_BY_KEY = new Map(PROFILES.map(p => [p.key, p]));

const COMBINE_MODES = [
  { key: 'narrowest', label: 'narrowest', tooltip: 'Per nutrient, take the most restrictive value across the selected profiles (max of mins, min of maxes).' },
  { key: 'widest',    label: 'widest',    tooltip: 'Per nutrient, take the least restrictive value across the selected profiles (min of mins, max of maxes).' },
];

export function mountNutrientThresholds(host, { state, ranges, getDefaultThreshold = null, getSliderBounds = null }) {
  if (!host) return;

  /* Tester feedback: slider bounds must stay fixed regardless of which
   * profile is selected or whether the user is in per-100g vs per-serving
   * mode. main.js supplies a stable bounds function spanning both unit
   * modes; fall back to the dataset envelope if it isn't provided. */
  function sliderBoundsFor(nutrient) {
    if (typeof getSliderBounds === 'function') {
      const b = getSliderBounds(nutrient);
      if (b && Number.isFinite(b.min) && Number.isFinite(b.max)) return b;
    }
    const r = ranges[nutrient];
    return r ? { min: r.min, max: r.max } : { min: 0, max: 1 };
  }

  // Phase 40.11: reset targets the USER default (boot-initial value),
  // not the dataset envelope. This keeps active-filter chips quiet
  // after a reset — if the user-default for calories is 0–1000, a
  // reset to 0–902 (dataset envelope) would erroneously generate a
  // "Calories ≤ 902" chip even though the user just "reset".
  function userDefaultFor(nutrient) {
    if (typeof getDefaultThreshold === 'function') {
      const d = getDefaultThreshold(nutrient);
      if (d) return { min: d.min, max: d.max };
    }
    const r = ranges[nutrient];
    return r ? { min: r.min, max: r.max } : { min: 0, max: 1 };
  }
  function fullUserDefaults() {
    const out = {};
    for (const nutrient of NUTRIENT_FIELDS) out[nutrient] = userDefaultFor(nutrient);
    return out;
  }
  /* Batch 12: Reset-all (and the per-row ↻ button) target the slider's
   * actual full range — what the user can SEE as the slider envelope —
   * not the boot-time preset default. Iron's preset default is 0–25 mg
   * but the slider runs to 100 mg; testers expected reset to land on
   * the visible bar's min/max, since that's the only spec the UI
   * surfaces unambiguously. */
  function fullSliderBounds() {
    const out = {};
    for (const nutrient of NUTRIENT_FIELDS) out[nutrient] = sliderBoundsFor(nutrient);
    return out;
  }

  /* Phase 40 round 11: the section edits whichever threshold set
   * matches the current nutrient unit. State has two slots:
   *   state.thresholds        — per-100g
   *   state.thresholdsServing — per-serving (same numeric defaults)
   * The two are independently editable; switching the unit toggle in
   * the header flips which one this section reads and writes. */
  function activeSlotKey() {
    return (state.get('nutrientUnit') || '100g') === 'serving'
      ? 'thresholdsServing' : 'thresholds';
  }
  function activeThresholds() {
    return state.get(activeSlotKey()) || fullUserDefaults();
  }
  function setActiveThresholds(next) {
    state.set({ [activeSlotKey()]: next });
  }

  const { root: section, body } = createRailSection({
    title: 'Nutrient thresholds',
    id: 'section-thresholds',
    tooltip: 'Set min/max ranges per nutrient. Modes: Filter hides anything out of range; Highlight scales matching dots up; Score colors every dot by how close it is to your targets.',
  });
  host.appendChild(section);

  /* Phase 40 round 11: section title gets a "per 100g" / "per serving"
   * suffix that follows the global unit toggle, so the user knows
   * which slot they're editing. */
  function refreshSectionTitle() {
    const titleEl = section.querySelector('.rail-section-title');
    if (!titleEl) return;
    const unit = (state.get('nutrientUnit') || '100g') === 'serving'
      ? 'per serving' : 'per 100g';
    titleEl.innerHTML = `Nutrient thresholds <span class="muted">(${unit})</span>`;
  }
  refreshSectionTitle();
  state.subscribe(s => s.nutrientUnit, refreshSectionTitle);

  body.classList.add('nutrient-thresholds');
  body.innerHTML = `
    <div class="threshold-modes seg-group" role="tablist" aria-label="Threshold mode">
      ${MODES.map(m =>
        `<button class="seg-btn" type="button" data-mode="${m.key}" role="tab" title="${m.tooltip}">${m.label}</button>`
      ).join('')}
    </div>
    <button class="threshold-restore-coloring btn-link" type="button" hidden
            title="Switch back to Filter mode so dots keep their food-group colors. Threshold values are preserved.">
      ↻ Restore normal coloring
    </button>
    <div class="threshold-profiles" aria-label="Nutrient profile presets">
      <button class="profile-dropdown-trigger" type="button"
              aria-haspopup="true" aria-expanded="false"
              title="Apply preset nutrient profiles. Each click stacks its constraints onto the current thresholds — strictness governed by the Combine mode below.">
        <span class="profile-dropdown-label">Profile presets</span>
        <span class="profile-dropdown-caret" aria-hidden="true">▾</span>
      </button>
      <div class="profile-dropdown-panel" hidden role="menu">
        <div class="profile-dropdown-head">
          <label class="threshold-profile-combine">
            <span class="muted">Combine:</span>
            <select class="threshold-profile-mode"
                    aria-label="Combine mode"
                    title="How each profile's values merge with the current thresholds. Narrowest tightens (intersection); widest loosens (union).">
              ${COMBINE_MODES.map(c => `<option value="${c.key}" title="${c.tooltip}">${c.label}</option>`).join('')}
            </select>
          </label>
        </div>
        <div class="profile-dropdown-list" role="group" aria-label="Profiles">
          ${PROFILES.map(p => `
            <button class="profile-apply-btn" type="button" data-key="${p.key}" title="${p.tooltip}">
              ${p.label}
            </button>
          `).join('')}
        </div>
      </div>
    </div>
    <div class="threshold-list"></div>
    <button class="threshold-reset-all btn btn-ghost" type="button">↻ Reset all</button>
  `;

  const modeBtns    = body.querySelectorAll('.threshold-modes .seg-btn');
  const listEl      = body.querySelector('.threshold-list');
  const resetAll    = body.querySelector('.threshold-reset-all');

  /* Mobile: while a finger is actively dragging a threshold slider, fade
   * the drawer (and its scrim) almost out so the live filtering on the 3D
   * map behind is visible. The panel stays interactive (opacity doesn't
   * block pointer events), so the drag continues; it snaps back the moment
   * the finger lifts. */
  const sliderMq = matchMedia('(max-width: 768px)');
  listEl.addEventListener('pointerdown', (ev) => {
    if (!sliderMq.matches) return;
    if (!ev.target.closest('input[type="range"]')) return;
    document.body.classList.add('threshold-dragging');
    const end = () => {
      document.body.classList.remove('threshold-dragging');
      document.removeEventListener('pointerup', end);
      document.removeEventListener('pointercancel', end);
    };
    document.addEventListener('pointerup', end);
    document.addEventListener('pointercancel', end);
  });
  const profileTrigger = body.querySelector('.profile-dropdown-trigger');
  const profilePanel   = body.querySelector('.profile-dropdown-panel');
  const profileApplyBtns = body.querySelectorAll('.profile-apply-btn');
  const profileMode    = body.querySelector('.threshold-profile-mode');

  // One row per nutrient.
  const rows = {};
  for (const nutrient of NUTRIENT_FIELDS) {
    const meta = NUTRIENT_META[nutrient];
    // Slider bounds: stable, never change across profile picks or unit
    // toggles. Computed once at construction.
    const r = sliderBoundsFor(nutrient);
    const row = document.createElement('div');
    row.className = 'threshold-row';
    row.innerHTML = `
      <div class="threshold-row-head">
        <span class="threshold-row-label">${meta.label}</span>
        <span class="threshold-row-value muted"></span>
        <button class="threshold-row-reset btn-ghost" type="button"
                aria-label="Reset ${meta.label}" title="Reset">↻</button>
      </div>
      <div class="threshold-range">
        <div class="threshold-range-track" aria-hidden="true"></div>
        <input type="range" class="threshold-range-min"
               min="${r.min}" max="${r.max}" step="${stepFor(r)}" value="${r.min}"
               aria-label="${meta.label} minimum (${meta.unitLong})">
        <input type="range" class="threshold-range-max"
               min="${r.min}" max="${r.max}" step="${stepFor(r)}" value="${r.max}"
               aria-label="${meta.label} maximum (${meta.unitLong})">
      </div>
    `;

    const minInput = row.querySelector('.threshold-range-min');
    const maxInput = row.querySelector('.threshold-range-max');
    const valueEl  = row.querySelector('.threshold-row-value');
    const trackEl  = row.querySelector('.threshold-range-track');
    const resetEl  = row.querySelector('.threshold-row-reset');

    function commit(next) {
      const cur = activeThresholds() || defaultThresholds(ranges);
      setActiveThresholds({ ...cur, [nutrient]: next });
    }

    minInput.addEventListener('input', () => {
      let lo = +minInput.value;
      const hi = +maxInput.value;
      if (lo > hi) { lo = hi; minInput.value = String(lo); }
      commit({ min: lo, max: hi });
    });
    maxInput.addEventListener('input', () => {
      const lo = +minInput.value;
      let hi = +maxInput.value;
      if (hi < lo) { hi = lo; maxInput.value = String(hi); }
      commit({ min: lo, max: hi });
    });
    resetEl.addEventListener('click', () => {
      // Batch 12: ↻ resets to the slider's full visible range, matching
      // the Reset-all button.
      const d = sliderBoundsFor(nutrient);
      commit({ min: d.min, max: d.max });
    });

    listEl.appendChild(row);
    rows[nutrient] = { minInput, maxInput, valueEl, trackEl, meta, range: r };
  }

  resetAll.addEventListener('click', () => {
    // Batch 12: Reset-all targets the slider's full visible bounds, not
    // the boot-time preset defaults. See fullSliderBounds() above.
    setActiveThresholds(fullSliderBounds());
  });

  // --- Profile presets ---
  //
  // Tester feedback: profiles are pure one-shot apply buttons. Clicking
  // a profile stacks its constraints onto the current thresholds per
  // the active Combine mode (narrowest → tighten; widest → loosen).
  // No active set, no asterisks, no tracking — the threshold sliders
  // ARE the result, and they already persist on their own.

  function applyProfile(key) {
    const p = PROFILE_BY_KEY.get(key);
    if (!p) return;
    const mode = state.get('nutrientProfileMode') || 'narrowest';
    const current = activeThresholds() || fullUserDefaults();
    const next = {};
    for (const nutrient of NUTRIENT_FIELDS) {
      next[nutrient] = current[nutrient]
        ? { ...current[nutrient] }
        : { ...userDefaultFor(nutrient) };
    }
    for (const [nutrient, c] of Object.entries(p.constraints)) {
      const slot = next[nutrient];
      if (!slot) continue;
      if (typeof c.min === 'number') {
        // Narrowest = stricter floor (higher min); widest = looser (lower min).
        slot.min = mode === 'widest' ? Math.min(slot.min, c.min) : Math.max(slot.min, c.min);
      }
      if (typeof c.max === 'number') {
        // Narrowest = stricter ceiling (lower max); widest = looser (higher max).
        slot.max = mode === 'widest' ? Math.max(slot.max, c.max) : Math.min(slot.max, c.max);
      }
      if (slot.min > slot.max) slot.min = slot.max;
    }
    setActiveThresholds(next);
  }

  function syncCombineMode() {
    const mode = state.get('nutrientProfileMode') || 'narrowest';
    if (profileMode.value !== mode) profileMode.value = mode;
  }
  syncCombineMode();
  state.subscribe(s => s.nutrientProfileMode, syncCombineMode);

  function openPanel() {
    profilePanel.hidden = false;
    profileTrigger.setAttribute('aria-expanded', 'true');
  }
  function closePanel() {
    profilePanel.hidden = true;
    profileTrigger.setAttribute('aria-expanded', 'false');
  }
  profileTrigger.addEventListener('click', () => {
    if (profilePanel.hidden) openPanel(); else closePanel();
  });
  document.addEventListener('pointerdown', (ev) => {
    if (profilePanel.hidden) return;
    if (profilePanel.contains(ev.target) || profileTrigger.contains(ev.target)) return;
    closePanel();
  }, true);
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && !profilePanel.hidden) closePanel();
  });

  for (const btn of profileApplyBtns) {
    btn.addEventListener('click', () => {
      applyProfile(btn.dataset.key);
      /* Leave the popup open so the user can chain multiple
       * applications (Keto then High-protein, etc.) without having
       * to re-open the menu each time. */
    });
  }
  profileMode.addEventListener('change', () => {
    state.set({ nutrientProfileMode: profileMode.value });
  });

  // Mode selector
  for (const btn of modeBtns) {
    btn.addEventListener('click', () => {
      state.set({ thresholdMode: btn.dataset.mode });
    });
  }
  /* Tester feedback: in Score mode there was no quick way to "stop
   * coloring" without losing the threshold values — the user had to
   * click Filter mode (counterintuitive when their threshold edits
   * felt distinct from the gradient). The button below switches mode
   * back to Filter (which keeps thresholds and restores default
   * coloring) and is only visible while Score is active. */
  const restoreBtn = body.querySelector('.threshold-restore-coloring');
  if (restoreBtn) {
    restoreBtn.addEventListener('click', () => {
      state.set({ thresholdMode: 'filter' });
    });
  }
  function applyMode(mode) {
    for (const btn of modeBtns) {
      btn.classList.toggle('is-active', btn.dataset.mode === mode);
      btn.setAttribute('aria-selected', btn.dataset.mode === mode ? 'true' : 'false');
    }
    if (restoreBtn) restoreBtn.hidden = mode !== 'score';
  }
  applyMode(state.get('thresholdMode') || 'filter');
  state.subscribe(s => s.thresholdMode, applyMode);

  // Sync sliders + value display + track-fill when state changes.
  function refresh() {
    const t = activeThresholds() || defaultThresholds(ranges);
    for (const nutrient of NUTRIENT_FIELDS) {
      const row = rows[nutrient];
      const tn  = t[nutrient];
      if (!row || !tn) continue;
      if (row.minInput.value !== String(tn.min)) row.minInput.value = String(tn.min);
      if (row.maxInput.value !== String(tn.max)) row.maxInput.value = String(tn.max);
      row.valueEl.textContent = `${row.meta.format(tn.min)} – ${row.meta.format(tn.max)}`;
      // Paint the active span of the track so the user can see the range.
      const r = row.range;
      const span = Math.max(1e-6, r.max - r.min);
      const a = ((tn.min - r.min) / span) * 100;
      const b = ((tn.max - r.min) / span) * 100;
      row.trackEl.style.setProperty('--lo', `${a}%`);
      row.trackEl.style.setProperty('--hi', `${b}%`);
    }
    // Disabled iff every threshold already equals the slider's full
    // bound — i.e., there's nothing left for Reset-all to widen.
    resetAll.disabled = isThresholdsAtDefaults(t, fullSliderBounds());
  }

  refresh();
  state.subscribe(s => s.thresholds,        refresh);
  state.subscribe(s => s.thresholdsServing, refresh); // Phase 40 round 11
  state.subscribe(s => s.nutrientUnit,      refresh); // re-read the active slot when toggled

  /* Tester feedback: a user meal whose nutrient values fall outside the
   * baseline slider bounds should expand the slider to fit. When the
   * meal is deleted, the bound retracts. getSliderBounds re-reads
   * userMeals each call (data-driven), so we just need to refresh DOM
   * here in response to userMeals changes — and bump any threshold
   * value that was pinned to the old max so the user's "no upper limit"
   * intent rides the new bound.
   *
   * Batch 14 fix: the slider bounds are now per-unit, so the bar must
   * also rebuild when the user toggles 100g ↔ serving. The earlier
   * unit-agnostic bar stayed the same width in both modes and the
   * default handle sat mid-bar in the off-unit mode (calories+carbs in
   * 100g, fiber/sodium/sat_fat/iron in serving). */
  applyDataDrivenBounds();
  state.subscribe(s => s.userMeals,    applyDataDrivenBounds);
  state.subscribe(s => s.nutrientUnit, applyDataDrivenBounds);

  function applyDataDrivenBounds() {
    const cur = activeThresholds() || fullUserDefaults();
    const nextThresholds = {};
    let valuesChanged = false;
    for (const nutrient of NUTRIENT_FIELDS) {
      const row = rows[nutrient];
      if (!row) continue;
      const oldMax = +row.maxInput.max;
      const oldMin = +row.minInput.min;
      const newBounds = sliderBoundsFor(nutrient);
      const step = stepFor(newBounds);

      if (newBounds.min !== oldMin || newBounds.max !== oldMax) {
        row.range = newBounds;
        row.minInput.min  = String(newBounds.min);
        row.minInput.max  = String(newBounds.max);
        row.minInput.step = String(step);
        row.maxInput.min  = String(newBounds.min);
        row.maxInput.max  = String(newBounds.max);
        row.maxInput.step = String(step);
      }

      const t = cur[nutrient];
      if (!t) { nextThresholds[nutrient] = { ...newBounds }; valuesChanged = true; continue; }
      let { min, max } = t;
      // If the user was at the old "no upper limit" (threshold sat at
      // the slider's previous max), follow the new bound up so the
      // freshly-added user meal stays visible.
      if (Number.isFinite(oldMax) && max >= oldMax && newBounds.max > oldMax) {
        max = newBounds.max;
      }
      // Clamp to the new bound (so a shrink doesn't leave the handle
      // off-track).
      if (max > newBounds.max) max = newBounds.max;
      if (min < newBounds.min) min = newBounds.min;
      if (min > max) min = max;
      if (min !== t.min || max !== t.max) valuesChanged = true;
      nextThresholds[nutrient] = { min, max };
    }
    if (valuesChanged) setActiveThresholds(nextThresholds);
    else refresh();
  }
}

/** Pick a slider step that's not maddening for the nutrient's scale. */
function stepFor(range) {
  const span = range.max - range.min;
  if (span > 500) return 5;
  if (span > 100) return 1;
  if (span > 10)  return 0.5;
  return 0.1;
}
