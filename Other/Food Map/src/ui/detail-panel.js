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
  GROUP_WEIGHT_LABELS,
  servingGramsFor,
} from '../data/schema.js';
import { inactiveReasons } from '../core/inactive-reasons.js';
import { scaleForItem } from '../core/unit.js';
import { escapeHtml, escapeAttr } from '../util/dom.js';

const GROUP_VARS = ['--color-animal', '--color-plant', '--color-dairy'];
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
    entries: GROUP_WEIGHT_LABELS.map((name, i) => ({
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
  /* Batch 4: full ingredient list for the ingredient-level Remix —
   * autocomplete suggestions + id→name chip labels. */
  getAllIngredients = () => [],
  getRawMeal = () => null,
  /* Tester feedback: when the user selects a dot or row and then
   * adjusts a filter that would hide it, the dot stays visible as a
   * dimmed ghost (see scene/points.js) and this panel shows a banner
   * explaining it's filtered out. The hidden-id getter is supplied by
   * main.js; if not wired, the banner simply never fires. */
  getHiddenSet = () => null,
  /* Batch 14: per-unit threshold defaults. inactiveReasons uses these
   * to skip nutrients still at the bar's edge from the "out of range"
   * list — same logic the filter pipeline uses to decide which
   * nutrients are actually active. */
  getThresholdDefaults = () => null,
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
  const chrome = root.querySelector('.rail-chrome');
  const collapseBtn = root.querySelector('.rail-collapse');
  const expandBtn   = root.querySelector('.rail-expand');

  const mobileMq = matchMedia('(max-width: 768px)');
  const isMobile = () => mobileMq.matches;

  // Batch 4: ingredient lookups for the ingredient-level Remix. Built once —
  // the ingredient dataset is immutable at runtime.
  const allIngredientsList = getAllIngredients() || [];
  const ingredientNameById = new Map(allIngredientsList.map(f => [f.id, f.name]));
  const nameOf = (id) => ingredientNameById.get(id) || id;

  function clearSelection() {
    if (state.get('selectedIngredientId') !== null) state.set({ selectedIngredientId: null });
  }
  closeBtn.addEventListener('click', clearSelection);

  /* Body-level scrim behind the mobile bottom sheet. Tapping the exposed
   * area above the sheet dismisses the selection — the previous build had
   * no tap-outside affordance, so closing meant either hitting the small
   * × or a pixel-precise drag of the grab bar. */
  const scrim = document.createElement('div');
  scrim.className = 'rail-scrim';
  scrim.hidden = true;
  scrim.setAttribute('aria-hidden', 'true');
  document.body.appendChild(scrim);
  scrim.addEventListener('click', clearSelection);
  function syncScrim() {
    scrim.hidden = !(isMobile() && root.classList.contains('is-open'));
  }
  mobileMq.addEventListener('change', syncScrim);
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
    root.style.transition = 'transform var(--duration-base) var(--ease-out)';
    root.style.transform = '';
    // Drop the temporary transition once the snap-back settles so it
    // doesn't lag the next open/close.
    setTimeout(() => { root.style.transition = ''; }, 220);
    if (dismiss) clearSelection();
  }
  function startDrag(ev) {
    if (!isMobile()) return;
    // Let the × / collapse buttons take their own taps.
    if (ev.target.closest('button')) return;
    dragging = true;
    dragStartY = ev.clientY;
    dragOffset = 0;
    // Kill the rail's transform transition so the sheet tracks the finger
    // 1:1 instead of easing toward each pointer position.
    root.style.transition = 'none';
    document.addEventListener('pointermove', onDragMove);
    document.addEventListener('pointerup', onDragEnd);
    document.addEventListener('pointercancel', onDragEnd);
    ev.preventDefault();
  }
  // Both the grab pill and the chrome row initiate the drag, so the whole
  // top strip of the sheet is a drag target rather than a thin handle.
  grab.addEventListener('pointerdown', startDrag);
  chrome.addEventListener('pointerdown', startDrag);

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
      nutrientDefaults: getThresholdDefaults
        ? getThresholdDefaults(unit)
        : null,
    });
  }

  function isCurrentlyFilteredOut(ingredient) {
    if (!ingredient) return false;
    const hidden = typeof getHiddenSet === 'function' ? getHiddenSet() : null;
    return !!(hidden && hidden.has(ingredient.id));
  }

  function showFood(ingredient) {
    const scheme = state.get('colorScheme') || 'rgb';
    const unit   = state.get('nutrientUnit') || '100g';
    const remix  = isRemixable(ingredient)
      ? buildRemixView(ingredient, state, getRawMeal)
      : null;
    const filteredOut = isCurrentlyFilteredOut(ingredient);
    body.innerHTML = renderIngredientHtml(
      ingredient,
      currentReasons(ingredient),
      scheme, remix, unit,
      filteredOut, nameOf,
    );
    body.scrollTop = 0;
    closeBtn.hidden = false;
    root.classList.add('is-open');
    syncScrim();
    if (state.get('rightRailOpen') === false) {
      state.set({ rightRailOpen: true });
    }
    if (remix) attachRemixHandlers(body, ingredient, state, {
      getAllCategories, getRawMeal, allIngredientsList, nameOf,
    });
  }
  function showEmpty() {
    body.innerHTML = renderEmptyHtml();
    closeBtn.hidden = true;
    root.classList.remove('is-open');
    syncScrim();
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
  state.subscribe(s => s.thresholdsServing,rerenderIfSelected);
  state.subscribe(s => s.thresholdMode,    rerenderIfSelected);
  state.subscribe(s => s.restrictions,     rerenderIfSelected);
  state.subscribe(s => s.colorScheme,      rerenderIfSelected);
  state.subscribe(s => s.nutrientUnit,     rerenderIfSelected);  // Phase 40 round 7
  /* Tester feedback (filtered-out banner): the banner needs to update
   * whenever ANY filter could have flipped the selected item in or out
   * of the hidden set. Adding the slices that didn't already subscribe.
   * The cost is one banner-class repaint per filter mutation while a
   * selection is open — cheap enough to not warrant a smarter check. */
  state.subscribe(s => s.tagFilter,             rerenderIfSelected);
  state.subscribe(s => s.tagFilterMatch,        rerenderIfSelected);
  state.subscribe(s => s.tagFilterScope,        rerenderIfSelected);
  state.subscribe(s => s.categoryFilter,        rerenderIfSelected);
  state.subscribe(s => s.categoryFilterMatch,   rerenderIfSelected);
  state.subscribe(s => s.categoryFilterScope,   rerenderIfSelected);
  state.subscribe(s => s.foodGroupFilter,       rerenderIfSelected);
  state.subscribe(s => s.foodGroupFilterMatch,  rerenderIfSelected);
  state.subscribe(s => s.foodGroupFilterScope,  rerenderIfSelected);
  state.subscribe(s => s.dietFilter,            rerenderIfSelected);
  state.subscribe(s => s.cuisineFilter,         rerenderIfSelected);
  state.subscribe(s => s.dietCuisineFilterMatch,rerenderIfSelected);
  state.subscribe(s => s.dietCuisineFilterScope,rerenderIfSelected);
  state.subscribe(s => s.ingredientFilterMatch, rerenderIfSelected);
  state.subscribe(s => s.ingredientFilterScope, rerenderIfSelected);
  state.subscribe(s => s.legendHidden,          rerenderIfSelected);
  // Phase 37: when the draft changes (− / + / Reset), repaint the
  // Remix section so the chips reflect current state. Repaint also
  // refreshes the nutrient / color block since the underlying
  // aggregate has shifted.
  state.subscribe(s => s.mealDraft,        rerenderIfSelected);
  // Batch 4: toggling the Remix axis (category ⇄ ingredient) repaints the
  // section so it shows the right chips + add control.
  state.subscribe(s => s.remixMode,        rerenderIfSelected);

  showEmpty();
}

/* --- Phase 37 Remix builder + handlers --- */

/* Batch 4: the Remix view is mode-aware. One section, toggled between editing
 * the meal's broad `ingredient_categories` (category mode) and its specific
 * `example_ingredients` (ingredient mode). The active mode decides what the
 * chips, the add-control, and Save operate on; the draft carries either a
 * `categories` list or an `ingredients` (id) list to match. */
function buildRemixView(item, state, getRawMeal) {
  const mode  = state.get('remixMode') || 'ingredient';
  const draft = state.get('mealDraft');
  const draftMatches = draft && draft.mealId === item.id;

  if (mode === 'ingredient') {
    const original = originalIngredientsFor(item, getRawMeal);
    const hasDraft = draftMatches && Array.isArray(draft.ingredients);
    const active = hasDraft ? draft.ingredients.slice() : original.slice();
    return { mode, active, original, isDirty: hasDraft && !sameMembers(active, original), mealId: item.id };
  }
  const original = originalCategoriesFor(item, getRawMeal);
  const hasDraft = draftMatches && Array.isArray(draft.categories);
  const active = hasDraft ? draft.categories.slice() : original.slice();
  return { mode, active, original, isDirty: hasDraft && !sameMembers(active, original), mealId: item.id };
}

/* Pre-draft specific ingredient ids for a meal — read from the raw record so
 * it reflects the meal as authored, not the (possibly drafted) aggregate. */
function originalIngredientsFor(item, getRawMeal) {
  const raw = getRawMeal && getRawMeal(item.id);
  if (raw && Array.isArray(raw.example_ingredients)) return raw.example_ingredients.slice();
  if (raw && Array.isArray(raw.ingredients)) {
    return raw.ingredients.map(i => i.ingredientId).filter(Boolean);
  }
  return Array.isArray(item.example_ingredients) ? item.example_ingredients.slice() : [];
}

function sameMembers(a, b) {
  if (a.length !== b.length) return false;
  const sa = new Set(a);
  for (const x of b) if (!sa.has(x)) return false;
  return true;
}

function attachRemixHandlers(body, item, state, {
  getAllCategories, getRawMeal, allIngredientsList = [], nameOf = (x) => x,
}) {
  const section = body.querySelector('.detail-remix');
  if (!section) return;
  const chipsEl   = section.querySelector('.remix-chips');
  const inputEl   = section.querySelector('.remix-add-input');
  const suggEl    = section.querySelector('.remix-add-suggestions');
  const resetBtn  = section.querySelector('.remix-reset');
  const saveBtn   = section.querySelector('.remix-save');
  const modeGroup = section.querySelector('.remix-mode-toggle');

  const mode = state.get('remixMode') || 'ingredient';
  const ingById = new Map(allIngredientsList.map(f => [f.id, f]));

  // Switching the Remix axis clears any in-flight draft so each mode starts
  // from the meal's original list (the two drafts aren't interchangeable).
  modeGroup?.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-mode]');
    if (!btn || btn.dataset.mode === mode) return;
    state.set({ remixMode: btn.dataset.mode, mealDraft: null });
  });

  function setDraft(nextMembers) {
    const key = mode === 'ingredient' ? 'ingredients' : 'categories';
    state.set({ mealDraft: { mealId: item.id, [key]: nextMembers.slice() } });
  }

  function currentActive() {
    const draft = state.get('mealDraft');
    if (draft && draft.mealId === item.id) {
      if (mode === 'ingredient' && Array.isArray(draft.ingredients)) return draft.ingredients.slice();
      if (mode === 'category'  && Array.isArray(draft.categories))  return draft.categories.slice();
    }
    return mode === 'ingredient'
      ? originalIngredientsFor(item, getRawMeal)
      : originalCategoriesFor(item, getRawMeal);
  }

  chipsEl.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.remix-chip-remove');
    if (!btn) return;
    const value = btn.closest('.remix-chip')?.dataset.value;
    if (!value) return;
    setDraft(currentActive().filter(c => c !== value));
  });

  inputEl.addEventListener('input', () => {
    const q = inputEl.value.trim().toLowerCase();
    if (!q) { suggEl.hidden = true; suggEl.innerHTML = ''; return; }
    const active = new Set(currentActive());
    let options; // [{ value, label }]
    if (mode === 'ingredient') {
      options = allIngredientsList
        .filter(f => !active.has(f.id) && f.name.toLowerCase().includes(q))
        .slice(0, REMIX_SUGGEST_CAP)
        .map(f => ({ value: f.id, label: f.name }));
    } else {
      options = (getAllCategories() || [])
        .filter(c => !active.has(c) && c.toLowerCase().includes(q))
        .slice(0, REMIX_SUGGEST_CAP)
        .map(c => ({ value: c, label: c }));
    }
    if (options.length === 0) { suggEl.hidden = true; suggEl.innerHTML = ''; return; }
    suggEl.innerHTML = options.map(o =>
      `<button class="remix-add-option" type="button" role="option" data-value="${escapeAttr(o.value)}">${escapeHtml(o.label)}</button>`
    ).join('');
    suggEl.hidden = false;
  });

  suggEl.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.remix-add-option');
    if (!btn) return;
    const value = btn.dataset.value;
    const active = currentActive();
    if (!active.includes(value)) setDraft([...active, value]);
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
    const noun = mode === 'ingredient' ? 'ingredient' : 'category';
    if (active.length === 0) {
      window.alert(`A meal needs at least one ${noun}.`);
      return;
    }
    const defaultName = `${item.name} (remix)`;
    const name = window.prompt('Save remix as:', defaultName);
    if (name == null) return; // user cancelled
    const trimmed = String(name).trim() || defaultName;
    const meals = state.get('userMeals') || [];
    let entry;
    if (mode === 'ingredient') {
      // Ingredient-shape user meal: each specific ingredient at its own
      // typical serving, matching the live-dot plate model.
      const ingredientsList = active.map(id => ({
        ingredientId: id,
        grams: (ingById.get(id)?.serving_grams) || 100,
      }));
      entry = { id: `useting-${item.id}-${Date.now().toString(36)}`, name: trimmed, ingredients: ingredientsList };
    } else {
      entry = { id: `usercat-${item.id}-${Date.now().toString(36)}`, name: trimmed, ingredient_categories: active.slice() };
    }
    state.set({
      userMeals: [...meals, entry],
      // Clear the draft and jump selection to the new user meal so the user
      // immediately sees their save persist as a new dot.
      mealDraft: null,
      selectedIngredientId: entry.id,
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

function renderIngredientHtml(ingredient, reasons = [], scheme = 'rgb', remix = null, unit = '100g', filteredOut = false, nameOf = (x) => x) {
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

  /* Tester feedback: when the selected item is filtered out of the
   * current view, surface a banner right under the header so it's the
   * first thing the user sees — the dot is still visible (rendered as
   * a dimmed ghost in scene/points.js) so the panel needs to explain
   * why the dot stopped looking normal. Reasons reuse the same
   * inactiveReasons output that used to live in a bottom-of-panel
   * "Why this is greyed out" section. */
  const filteredBanner = filteredOut ? `
    <section class="detail-section detail-filtered-out">
      <header class="detail-filtered-head">
        <span class="detail-filtered-icon" aria-hidden="true">⚠</span>
        <strong>Filtered out of the current view</strong>
      </header>
      <p class="detail-filtered-blurb muted">
        This item doesn't pass your active filters or thresholds.
        Adjust them — or clear your selection — to remove the ghost dot.
      </p>
      ${reasons.length > 0 ? `
        <ul class="detail-filtered-reasons">
          ${reasons.map(r => `<li>${escapeHtml(r)}</li>`).join('')}
        </ul>` : ''}
    </section>` : '';

  return `
    <header class="detail-header">
      <h2 class="detail-name">${escapeHtml(ingredient.name)}${formChip}${draftBadge}</h2>
      <p class="detail-subtitle muted">${subtitle}</p>
      ${mealBlurb}
      ${tagChips}
    </header>

    ${filteredBanner}

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

    ${remix ? renderRemixHtml(remix, nameOf) : ''}

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

    ${(!filteredOut && reasons.length > 0) ? `
    <section class="detail-section detail-reasons">
      <h3 class="detail-section-title">Why this is greyed out</h3>
      <ul class="detail-reasons-list">
        ${reasons.map(r => `<li>${escapeHtml(r)}</li>`).join('')}
      </ul>
    </section>` : ''}
  `;
}

function renderRemixHtml(remix, nameOf = (x) => x) {
  const isIng = remix.mode === 'ingredient';
  const labelFor = (v) => (isIng ? nameOf(v) : v);
  const noun = isIng ? 'ingredient' : 'category';

  const chips = remix.active.map(v => `
    <span class="remix-chip" data-value="${escapeAttr(v)}">
      <span class="remix-chip-label">${escapeHtml(labelFor(v))}</span>
      <button class="remix-chip-remove" type="button"
              aria-label="Remove ${escapeHtml(labelFor(v))}" title="Remove">×</button>
    </span>`).join('');

  /* One section, two axes. The toggle picks whether the chips below edit the
   * meal's specific ingredients or its broad categories; the dot recomputes
   * live either way. */
  const modeToggle = `
    <div class="remix-mode-toggle seg-group" role="group" aria-label="Remix by ingredient or category">
      <button type="button" class="seg-btn seg-btn-sm${isIng ? ' is-active' : ''}" data-mode="ingredient">Ingredients</button>
      <button type="button" class="seg-btn seg-btn-sm${!isIng ? ' is-active' : ''}" data-mode="category">Categories</button>
    </div>`;

  return `
    <section class="detail-section detail-remix">
      <header class="remix-header">
        <h3 class="detail-section-title">Remix</h3>
        ${remix.isDirty
          ? `<button class="remix-reset btn-link" type="button" title="Revert to original">Reset</button>`
          : ''}
      </header>
      ${modeToggle}
      <p class="remix-blurb muted">
        ${isIng
          ? "Swap the specific ingredients this meal uses. The dot shifts live; save your version to keep it."
          : "Swap this meal's broad category set. The dot shifts live; save your version to keep it."}
      </p>
      <div class="remix-chips" role="list">
        ${chips || `<span class="muted">(no ${noun}s — add one below)</span>`}
      </div>
      <div class="remix-add-wrapper">
        <input class="input remix-add-input" type="text"
               placeholder="Add ${isIng ? 'an ingredient' : 'a category'}…" autocomplete="off"
               aria-label="Add ${isIng ? 'an ingredient' : 'a category'}">
        <div class="remix-add-suggestions" hidden role="listbox"></div>
      </div>
      <div class="remix-actions">
        <button class="btn remix-save" type="button"
                ${remix.isDirty ? '' : 'disabled'}
                title="${remix.isDirty ? 'Save remix as a new user meal' : `Edit ${noun}s above to enable`}">
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

