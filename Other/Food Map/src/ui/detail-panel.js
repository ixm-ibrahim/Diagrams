/* Right-rail / mobile bottom-sheet detail panel for the selected ingredient.
 *
 * Owns the right-rail chrome: a corner collapse arrow (›) that hides the
 * rail (driven by `rightRailOpen`), an inline expand handle (‹) on
 * desktop when collapsed, plus the selection contents inside the body.
 *
 * Visibility model:
 *   - Desktop: rightRailOpen drives the rail's expanded/collapsed state
 *     via the `data-right-open` attribute on `.app-main` (the grid CSS
 *     shrinks the right column to a thin handle when collapsed).
 *   - Mobile: the bottom sheet's `.is-open` follows selectedIngredientId, since
 *     a ingredient selection is the only natural trigger for the sheet to
 *     pop up. Clearing the selection slides it back down.
 *
 * The × button on desktop clears the ingredient selection without collapsing
 * the rail; on mobile it both clears the selection and slides the sheet
 * down, since the two are equivalent when selection drives visibility.
 *
 * Phase 37: when the selected item is a category-shape meal (curated,
 * corpus, or a saved remix), an inline "Remix" section lets the user
 * mutate its ingredient_categories. Mutations write to state.mealDraft
 * which main.js feeds back into activeDataset() so the dot moves live.
 * "Save" lifts the draft into userMeals; "Reset" / closing the panel
 * clears the draft.
 */

import {
  NUTRIENT_FIELDS, NUTRIENT_META,
  FOOD_GROUPS_BY_HUE, FOOD_GROUP_COLORS,
  servingGramsFor,
} from '../data/schema.js';
import { inactiveReasons } from '../core/inactive-reasons.js';
import { scaleForItem } from '../core/unit.js';

const GROUP_LABELS = ['Animal', 'Plant', 'Dairy'];
const GROUP_VARS   = ['--color-animal', '--color-plant', '--color-dairy'];
const DRAG_DISMISS_PX = 80;
const REMIX_SUGGEST_CAP = 8;

function colorBlockEntries(ingredient, scheme) {
  if (scheme === 'food_group') {
    const fgw = ingredient.food_group_weights;
    let entries;
    if (fgw) {
      entries = FOOD_GROUPS_BY_HUE.map(name => ({
        name,
        weight: fgw[name] || 0,
        css: cssFromRgb(FOOD_GROUP_COLORS[name]),
      }));
    } else if (ingredient.food_group && FOOD_GROUP_COLORS[ingredient.food_group]) {
      entries = [{
        name: ingredient.food_group,
        weight: 1,
        css: cssFromRgb(FOOD_GROUP_COLORS[ingredient.food_group]),
      }];
    } else {
      entries = [];
    }
    return {
      title: 'Food group',
      entries: entries.filter(e => e.weight > 0.001).sort((a, b) => b.weight - a.weight),
    };
  }
  const gw = ingredient.group_weights || [0, 0, 0];
  return {
    title: 'Color group',
    entries: GROUP_LABELS.map((name, i) => ({
      name,
      weight: gw[i] || 0,
      css: `var(${GROUP_VARS[i]})`,
    })).filter(e => e.weight > 0.001).sort((a, b) => b.weight - a.weight),
  };
}

function cssFromRgb(rgb) {
  if (!rgb) return 'rgb(128, 128, 128)';
  return `rgb(${Math.round(rgb[0]*255)}, ${Math.round(rgb[1]*255)}, ${Math.round(rgb[2]*255)})`;
}

/* Phase 37: a panel item is "remixable" when it's a meal aggregate
 * driven by an ingredient_categories list. Curated meals (source
 * undefined or 'curated'), corpus patterns ('corpus'), and category-
 * shape user meals (kind === 'category') all qualify. Ingredient-shape
 * user meals (kind === 'ingredient') are excluded — the meal-builder
 * left-rail card already edits those with the right granularity. */
function isRemixable(item) {
  if (!item || item.category !== 'Meal') return false;
  if (item.kind === 'ingredient') return false;
  return true;
}

/* Pull the original (pre-draft) categories for a meal — read from the
 * raw meals.json / compositional-meals.json / userMeals entries since
 * the aggregated `examples` field reflects the CURRENT (possibly drafted)
 * category list. */
function originalCategoriesFor(item, getRawMeals) {
  if (!item) return [];
  const raw = getRawMeals && getRawMeals(item.id);
  if (raw && Array.isArray(raw.ingredient_categories)) {
    return raw.ingredient_categories.slice();
  }
  // Fallback: trust the aggregate's examples (used when no raw lookup
  // is available, e.g., a category-shape user meal that's already been
  // through the aggregator without separate raw form preserved).
  return Array.isArray(item.examples) ? item.examples.slice() : [];
}

export function mountDetailPanel(root, {
  state,
  getCurrentIngredients,
  ranges = null,
  getAllCategories = () => [],
  getRawMeal = () => null,
}) {
  if (!root) return;

  root.classList.add('right-rail', 'detail-panel');
  root.removeAttribute('hidden');
  root.innerHTML = `
    <header class="rail-chrome">
      <button class="rail-collapse" type="button"
              aria-label="Hide details" title="Hide details">
        <span aria-hidden="true">→</span>
      </button>
      <button class="detail-close" type="button" aria-label="Clear selection" hidden>×</button>
    </header>
    <div class="detail-grab" aria-hidden="true"></div>
    <div class="detail-body"></div>
    <button class="rail-expand" type="button"
            aria-label="Show details" title="Show details">
      <span aria-hidden="true">←</span>
    </button>
    <div class="rail-resize" data-rail="right" role="separator"
         aria-orientation="vertical" aria-label="Resize details panel"></div>
  `;

  const body = root.querySelector('.detail-body');
  const closeBtn = root.querySelector('.detail-close');
  const grab = root.querySelector('.detail-grab');
  const collapseBtn = root.querySelector('.rail-collapse');
  const expandBtn   = root.querySelector('.rail-expand');

  function clearSelection() {
    if (state.get('selectedIngredientId') !== null) state.set({ selectedIngredientId: null });
  }
  closeBtn.addEventListener('click', clearSelection);
  collapseBtn.addEventListener('click', () => state.set({ rightRailOpen: false }));
  expandBtn.addEventListener('click',   () => state.set({ rightRailOpen: true }));

  const appMain = document.querySelector('.app-main');
  function applyRailOpen(open) {
    root.classList.toggle('is-collapsed', !open);
    if (appMain) appMain.setAttribute('data-right-open', open ? 'true' : 'false');
  }
  applyRailOpen(state.get('rightRailOpen'));
  state.subscribe(s => s.rightRailOpen, applyRailOpen);

  let dragStartY = 0;
  let dragOffset = 0;
  let dragging = false;
  function onDragMove(ev) {
    if (!dragging) return;
    dragOffset = Math.max(0, ev.clientY - dragStartY);
    root.style.transform = `translateY(${dragOffset}px)`;
  }
  function onDragEnd() {
    if (!dragging) return;
    dragging = false;
    document.removeEventListener('pointermove', onDragMove);
    document.removeEventListener('pointerup', onDragEnd);
    document.removeEventListener('pointercancel', onDragEnd);
    const dismiss = dragOffset > DRAG_DISMISS_PX;
    root.style.transform = '';
    if (dismiss) clearSelection();
  }
  grab.addEventListener('pointerdown', (ev) => {
    if (!matchMedia('(max-width: 768px)').matches) return;
    dragging = true;
    dragStartY = ev.clientY;
    dragOffset = 0;
    document.addEventListener('pointermove', onDragMove);
    document.addEventListener('pointerup', onDragEnd);
    document.addEventListener('pointercancel', onDragEnd);
    ev.preventDefault();
  });

  function currentReasons(ingredient) {
    const unit = state.get('nutrientUnit') || '100g';
    const thresholds = unit === 'serving'
      ? (state.get('thresholdsServing') || state.get('thresholds'))
      : state.get('thresholds');
    const scale = scaleForItem(ingredient, unit);
    return inactiveReasons(ingredient, {
      ingredientFilter: state.get('ingredientFilter'),
      thresholds,
      thresholdMode:    state.get('thresholdMode'),
      restrictions:     state.get('restrictions') || [],
      ranges,
      nutrientScale: scale,
      nutrientUnit:  unit,
    });
  }

  function showFood(ingredient) {
    const scheme = state.get('colorScheme') || 'rgb';
    const unit   = state.get('nutrientUnit') || '100g';
    const remix  = isRemixable(ingredient)
      ? buildRemixView(ingredient, state, getRawMeal)
      : null;
    body.innerHTML = renderIngredientHtml(ingredient, currentReasons(ingredient), scheme, remix, unit);
    body.scrollTop = 0;
    closeBtn.hidden = false;
    root.classList.add('is-open');
    if (state.get('rightRailOpen') === false) {
      state.set({ rightRailOpen: true });
    }
    if (remix) attachRemixHandlers(body, ingredient, state, getAllCategories, getRawMeal);
  }
  function showEmpty() {
    body.innerHTML = renderEmptyHtml();
    closeBtn.hidden = true;
    root.classList.remove('is-open');
  }

  state.subscribe(s => s.selectedIngredientId, (id) => {
    if (!id) { showEmpty(); return; }
    const ingredients = getCurrentIngredients();
    const ingredient = ingredients && ingredients.find(f => f.id === id);
    if (!ingredient) { showEmpty(); return; }
    showFood(ingredient);
  });

  function rerenderIfSelected() {
    const id = state.get('selectedIngredientId');
    if (!id) return;
    const ingredients = getCurrentIngredients();
    const ingredient = ingredients && ingredients.find(f => f.id === id);
    if (ingredient) showFood(ingredient);
  }
  state.subscribe(s => s.ingredientFilter, rerenderIfSelected);
  state.subscribe(s => s.thresholds,       rerenderIfSelected);
  state.subscribe(s => s.thresholdMode,    rerenderIfSelected);
  state.subscribe(s => s.restrictions,     rerenderIfSelected);
  state.subscribe(s => s.colorScheme,      rerenderIfSelected);
  state.subscribe(s => s.nutrientUnit,     rerenderIfSelected);  // Phase 40 round 7
  // Phase 37: when the draft changes (− / + / Reset), repaint the
  // Remix section so the chips reflect current state. Repaint also
  // refreshes the nutrient / color block since the underlying
  // aggregate has shifted.
  state.subscribe(s => s.mealDraft,        rerenderIfSelected);

  showEmpty();
}

/* --- Phase 37 Remix builder + handlers --- */

function buildRemixView(item, state, getRawMeal) {
  const original = originalCategoriesFor(item, getRawMeal);
  const draft    = state.get('mealDraft');
  const draftMatches = draft && draft.mealId === item.id && Array.isArray(draft.categories);
  const active = draftMatches ? draft.categories.slice() : original.slice();
  const isDirty = draftMatches && !sameCategorySet(active, original);
  return {
    active,
    original,
    isDirty,
    mealId: item.id,
  };
}

function sameCategorySet(a, b) {
  if (a.length !== b.length) return false;
  const sa = new Set(a);
  for (const x of b) if (!sa.has(x)) return false;
  return true;
}

function attachRemixHandlers(body, item, state, getAllCategories, getRawMeal) {
  const section = body.querySelector('.detail-remix');
  if (!section) return;
  const chipsEl   = section.querySelector('.remix-chips');
  const inputEl   = section.querySelector('.remix-add-input');
  const suggEl    = section.querySelector('.remix-add-suggestions');
  const resetBtn  = section.querySelector('.remix-reset');
  const saveBtn   = section.querySelector('.remix-save');

  function setDraft(nextCategories) {
    state.set({
      mealDraft: { mealId: item.id, categories: nextCategories.slice() },
    });
  }

  function currentActive() {
    const draft = state.get('mealDraft');
    if (draft && draft.mealId === item.id && Array.isArray(draft.categories)) {
      return draft.categories.slice();
    }
    return originalCategoriesFor(item, getRawMeal);
  }

  chipsEl.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.remix-chip-remove');
    if (!btn) return;
    const value = btn.closest('.remix-chip')?.dataset.value;
    if (!value) return;
    const active = currentActive().filter(c => c !== value);
    setDraft(active);
  });

  inputEl.addEventListener('input', () => {
    const q = inputEl.value.trim().toLowerCase();
    if (!q) { suggEl.hidden = true; suggEl.innerHTML = ''; return; }
    const allCats = getAllCategories() || [];
    const active = new Set(currentActive());
    const matches = allCats
      .filter(c => !active.has(c) && c.toLowerCase().includes(q))
      .slice(0, REMIX_SUGGEST_CAP);
    if (matches.length === 0) {
      suggEl.hidden = true;
      suggEl.innerHTML = '';
      return;
    }
    suggEl.innerHTML = matches.map(c =>
      `<button class="remix-add-option" type="button" role="option" data-value="${escapeAttr(c)}">${escapeHtml(c)}</button>`
    ).join('');
    suggEl.hidden = false;
  });

  suggEl.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.remix-add-option');
    if (!btn) return;
    const value = btn.dataset.value;
    const active = currentActive();
    if (!active.includes(value)) {
      setDraft([...active, value]);
    }
    inputEl.value = '';
    suggEl.hidden = true;
    suggEl.innerHTML = '';
  });

  inputEl.addEventListener('blur', () => {
    setTimeout(() => { suggEl.hidden = true; }, 150);
  });

  resetBtn?.addEventListener('click', () => {
    state.set({ mealDraft: null });
  });

  saveBtn?.addEventListener('click', () => {
    const active = currentActive();
    if (active.length === 0) {
      window.alert('A meal needs at least one category.');
      return;
    }
    const defaultName = `${item.name} (remix)`;
    const name = window.prompt('Save remix as:', defaultName);
    if (name == null) return; // user cancelled
    const trimmed = String(name).trim() || defaultName;
    const id = `usercat-${item.id}-${Date.now().toString(36)}`;
    const meals = state.get('userMeals') || [];
    state.set({
      userMeals: [...meals, {
        id,
        name: trimmed,
        ingredient_categories: active.slice(),
      }],
      // Clear the draft and jump selection to the new user meal so the
      // user immediately sees their save persist as a new dot.
      mealDraft: null,
      selectedIngredientId: id,
    });
  });
}

function renderEmptyHtml() {
  return `
    <div class="detail-empty">
      <p>Click a ingredient in the map to see its nutrient profile.</p>
    </div>
  `;
}

function renderIngredientHtml(ingredient, reasons = [], scheme = 'rgb', remix = null, unit = '100g') {
  const block = colorBlockEntries(ingredient, scheme);
  const groupRows = block.entries.map(e => {
    const p = Math.round(e.weight * 100);
    return `<span class="detail-group-seg"
                   style="flex: ${e.weight}; background: ${e.css};"
                   title="${escapeHtml(e.name)} ${p}%"></span>`;
  }).join('');

  const groupLegend = block.entries.map(e => `
    <li>
      <span class="detail-group-swatch" style="background: ${e.css};"></span>
      ${escapeHtml(e.name)} <span class="muted">${pct(e.weight)}</span>
    </li>`).join('');

  const ariaLabel = block.entries
    .map(e => `${e.name} ${pct(e.weight)}`)
    .join(', ');

  /* Display multiplier for the unit toggle. The source data is always
   * per-100g; when the user picks 'serving' we scale every nutrient
   * cell by servingGrams/100. For meals and category aggregates,
   * `serving_grams` is now stamped on the aggregate itself (sum of
   * constituent category servings for meals, RACC value for
   * categories) so this picks up the realistic plate weight rather
   * than the old flat 350g. */
  const servingGrams = servingGramsFor(ingredient);
  const isPerServing = unit === 'serving';
  const scale = scaleForItem(ingredient, unit);
  const unitSuffix = isPerServing
    ? `per serving (${servingGrams}g)`
    : `per 100g`;

  const nutrientRows = NUTRIENT_FIELDS.map(field => {
    const meta = NUTRIENT_META[field];
    const value = (+ingredient[field] || 0) * scale;
    const formatted = meta.format(value);
    return `
      <tr>
        <th scope="row">${meta.label}</th>
        <td>${formatted}</td>
      </tr>`;
  }).join('');

  /* Phase 40.8: macro completeness hint. Scaled to the same unit
   * (per 100g or per serving) so it stays consistent with the
   * numbers above. Skipped for beverages (≈100% water by mass) and
   * when the remainder is non-positive. */
  const macroRemainderHtml = (() => {
    if (ingredient.food_group === 'Beverages') return '';
    const protein = +ingredient.protein || 0;
    const fat     = +ingredient.fat     || 0;
    const carbs   = +ingredient.carbs   || 0;
    const remainder = 100 - protein - fat - carbs;
    if (!(remainder > 1)) return '';
    const scaled = Math.round(remainder * scale);
    return `
      <tr class="detail-nutrient-remainder">
        <th scope="row" title="Water plus anything not in protein/fat/carbs">
          Water / other
        </th>
        <td>~${scaled}g <span class="muted">${unitSuffix}</span></td>
      </tr>`;
  })();

  /* Phase 40 round 8: per-100g / per-serving toggle moved to the
   * header so the 3D view shows it too. The section heading still
   * reflects the current unit so the context isn't lost. */

  const examplesList = (ingredient.examples || []).slice(0, 12)
    .map(e => `<li>${escapeHtml(e)}</li>`).join('');

  const subtitleParts = [ingredient.food_group, ingredient.category];
  if (ingredient.subcategory && ingredient.subcategory !== ingredient.category) {
    subtitleParts.push(ingredient.subcategory);
  }
  const subtitle = subtitleParts.filter(Boolean).map(escapeHtml).join(' · ');
  const formChip = ingredient.form
    ? `<span class="detail-form-chip">${escapeHtml(ingredient.form)}</span>`
    : '';
  // Phase 37: badge in the header signals an unsaved remix draft.
  const draftBadge = (remix && remix.isDirty)
    ? `<span class="detail-draft-badge" title="Unsaved remix">draft</span>`
    : '';

  // Tester feedback: meals need a short description near the top so the
  // user can recognize unfamiliar dish names. Curated meals already carry
  // `notes`; user meals can supply their own via the meal-builder card.
  // For non-meal items, `notes` (when present) still renders in the
  // bottom Notes section to avoid duplicating a redundant string.
  const isMeal = ingredient.category === 'Meal';
  const mealBlurb = (isMeal && ingredient.notes)
    ? `<p class="detail-blurb">${escapeHtml(ingredient.notes)}</p>`
    : '';
  // Show tags as small chips beneath the header when present. User meals
  // can carry user-authored tags; ingredients carry tags derived via
  // effectiveTags. Either source surfaces here.
  const tags = Array.isArray(ingredient.tags) ? ingredient.tags : [];
  const tagChips = tags.length > 0
    ? `<ul class="detail-tags">${tags.map(t =>
        `<li class="detail-tag-chip">${escapeHtml(t)}</li>`).join('')}</ul>`
    : '';

  return `
    <header class="detail-header">
      <h2 class="detail-name">${escapeHtml(ingredient.name)}${formChip}${draftBadge}</h2>
      <p class="detail-subtitle muted">${subtitle}</p>
      ${mealBlurb}
      ${tagChips}
    </header>

    <section class="detail-section">
      <h3 class="detail-section-title">${escapeHtml(block.title)}</h3>
      <div class="detail-group-bar" role="img" aria-label="${escapeHtml(ariaLabel)}">
        ${groupRows}
      </div>
      <ul class="detail-group-legend">${groupLegend}</ul>
    </section>

    <section class="detail-section">
      <h3 class="detail-section-title">${isPerServing ? `Per serving (${servingGrams}g)` : 'Per 100g'}</h3>
      <table class="detail-nutrients">
        <tbody>${nutrientRows}${macroRemainderHtml}</tbody>
      </table>
    </section>

    ${remix ? renderRemixHtml(remix) : ''}

    ${ingredient.examples && ingredient.examples.length ? `
    <section class="detail-section">
      <h3 class="detail-section-title">Examples</h3>
      <ul class="detail-examples">${examplesList}</ul>
    </section>` : ''}

    ${(ingredient.notes && !isMeal) ? `
    <section class="detail-section">
      <h3 class="detail-section-title">Notes</h3>
      <p class="detail-notes">${escapeHtml(ingredient.notes)}</p>
    </section>` : ''}

    ${reasons.length > 0 ? `
    <section class="detail-section detail-reasons">
      <h3 class="detail-section-title">Why this is greyed out</h3>
      <ul class="detail-reasons-list">
        ${reasons.map(r => `<li>${escapeHtml(r)}</li>`).join('')}
      </ul>
    </section>` : ''}
  `;
}

function renderRemixHtml(remix) {
  const chips = remix.active.map(c => `
    <span class="remix-chip" data-value="${escapeAttr(c)}">
      <span class="remix-chip-label">${escapeHtml(c)}</span>
      <button class="remix-chip-remove" type="button"
              aria-label="Remove ${escapeHtml(c)}" title="Remove">×</button>
    </span>`).join('');

  return `
    <section class="detail-section detail-remix">
      <header class="remix-header">
        <h3 class="detail-section-title">Remix</h3>
        ${remix.isDirty
          ? `<button class="remix-reset btn-link" type="button" title="Revert to original">Reset</button>`
          : ''}
      </header>
      <p class="remix-blurb muted">
        Edit this meal's category set. The dot shifts live; save your version to keep it.
      </p>
      <div class="remix-chips" role="list">
        ${chips || '<span class="muted">(no categories — add one below)</span>'}
      </div>
      <div class="remix-add-wrapper">
        <input class="input remix-add-input" type="text"
               placeholder="Add a category…" autocomplete="off"
               aria-label="Add a category">
        <div class="remix-add-suggestions" hidden role="listbox"></div>
      </div>
      <div class="remix-actions">
        <button class="btn remix-save" type="button"
                ${remix.isDirty ? '' : 'disabled'}
                title="${remix.isDirty ? 'Save remix as a new user meal' : 'Edit categories above to enable'}">
          Save as new meal
        </button>
      </div>
    </section>
  `;
}

function pct(w) {
  return `${Math.round(w * 100)}%`;
}

/* Phase 40 round 8: wireUnitToggle removed — the toggle moved to the
 * header (src/ui/unit-toggle.js) so it's visible across views. */

function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
function escapeAttr(s) { return escapeHtml(s); }
