/* Phase 9 / Phase 40 round 4: user-meal editor.
 *
 * Pared back to a single responsibility: let the user create and edit
 * their own meals. The Meals section in the left rail used to also host
 * filter dropdowns (Restrictions / Food groups / Categories /
 * Ingredients / Nutrients / Modify meals) and a read-only curated-meal
 * list, but the tester feedback was that:
 *   - The filter dropdowns duplicated left-rail sections.
 *   - Browsing curated meals belongs in the Table view (viewLevel=meal).
 *
 * So this section is now just "+ New meal" plus the user's meal cards.
 * Two meal shapes are supported:
 *   1. Ingredient-shape: the original Phase 9 meal — a list of
 *      { ingredientId, grams } entries with per-ingredient gram sliders.
 *   2. Category-shape: created by saving a Remix from the detail panel
 *      (Phase 37). Carries an `ingredient_categories` list and renders
 *      as a read-only chip list with name + delete.
 *
 * Tester feedback (this round):
 *   - User meals now support free-form tags (saved on `meal.tags`).
 *   - Each card collapses via the header click so a long list stays
 *     scannable. Collapsed state is session-only (a Set keyed by meal
 *     id) so it doesn't bloat persistence.
 *   - The description input is rendered inside the collapsible body,
 *     not above it, so the collapsed card is a single tight row.
 */

import { createRailSection } from './left-rail.js';
import { escapeHtml, escapeAttr, cssEscape } from '../util/dom.js';

const DEFAULT_GRAMS  = 100;
const GRAMS_MIN      = 5;
const GRAMS_MAX      = 500;
const GRAMS_STEP     = 5;
const SUGGESTION_CAP = 8;

// Session-only collapsed state for individual meal cards. Persisting
// this on userMeals would trigger an autosave on every toggle and isn't
// worth the round-trip.
const collapsedMeals = new Set();

export function mountMealBuilder(host, { state, ingredients }) {
  if (!host) return;

  const { root: section, body } = createRailSection({
    title: 'Your meals',
    initiallyCollapsed: true,
    tooltip: 'Compose your own meals. Either pick ingredients with gram sliders, or save a remix from any meal\'s detail panel. Click a card\'s header to collapse it.',
  });
  host.appendChild(section);

  const ingredientById = new Map(ingredients.map(f => [f.id, f]));

  body.classList.add('meal-builder');
  body.innerHTML = `
    <p class="meal-builder-blurb muted">
      Build your own meals. To browse all meals, switch to the Table view.
    </p>
    <div class="meal-builder-list"></div>
    <button class="btn meal-builder-add" type="button">+ New meal</button>
  `;

  const userListEl = body.querySelector('.meal-builder-list');
  const addBtn     = body.querySelector('.meal-builder-add');

  addBtn.addEventListener('click', () => {
    const meals = state.get('userMeals') || [];
    const newId = `meal-${Date.now().toString(36)}-${Math.floor(Math.random() * 1e6).toString(36)}`;
    // Newly-created meals open expanded so the user can immediately
    // start composing.
    collapsedMeals.delete(newId);
    const next = [...meals, {
      id: newId,
      name: `Meal ${meals.length + 1}`,
      ingredients: [],
      tags: [],
    }];
    state.set({ userMeals: next });
  });

  function commitMeals(meals) {
    state.set({ userMeals: meals });
  }

  function render() {
    const userMeals = state.get('userMeals') || [];
    if (userMeals.length === 0) {
      userListEl.innerHTML = `<p class="meal-builder-empty muted">
        No meals yet — click "+ New meal" to compose one.</p>`;
      return;
    }
    userListEl.innerHTML = userMeals
      .map(m => isCategoryShapeUserMeal(m)
        ? renderCategoryUserMealHtml(m)
        : renderUserMealHtml(m, ingredientById))
      .join('');
    for (const meal of userMeals) {
      const card = userListEl.querySelector(`[data-meal-id="${cssEscape(meal.id)}"]`);
      if (!card) continue;
      bindCardCollapse(card, meal);
      if (isCategoryShapeUserMeal(meal)) {
        bindCategoryMealInteractions(card, meal, userMeals, commitMeals);
      } else {
        bindMealInteractions(card, meal, userMeals, commitMeals, ingredients, ingredientById);
      }
      bindTagInteractions(card, meal, commitMeals, state);
    }
  }

  render();
  state.subscribe(s => s.userMeals, render);
}

/* Kept exported so main.js (and any other dataset-filter consumer) can
 * skip filterMealsByMealFilters when the legacy mealFilters slot is
 * empty. Always returns true now that the dropdowns have been removed
 * — the slot only exists for backwards-compat hydration. */
export function isMealFiltersEmpty(_f) {
  return true;
}

// --- User meal shape detection ---

function isCategoryShapeUserMeal(meal) {
  return !!(meal && Array.isArray(meal.ingredient_categories) && meal.ingredient_categories.length > 0);
}

// --- Shared card chrome ---

function cardCollapseAttr(meal) {
  return collapsedMeals.has(meal.id) ? 'true' : 'false';
}

function cardHeaderHtml(meal, { badgeHtml = '' } = {}) {
  const collapsed = collapsedMeals.has(meal.id);
  return `
    <header class="meal-card-head">
      <button class="meal-card-collapse" type="button"
              aria-expanded="${collapsed ? 'false' : 'true'}"
              title="${collapsed ? 'Expand' : 'Collapse'}">
        <span class="meal-card-chevron" aria-hidden="true">${collapsed ? '▸' : '▾'}</span>
      </button>
      <input class="input meal-name" value="${escapeAttr(meal.name)}" aria-label="Meal name">
      ${badgeHtml}
      <button class="meal-delete" type="button" aria-label="Delete meal" title="Delete">×</button>
    </header>
  `;
}

function tagsBlockHtml(meal) {
  const tags = Array.isArray(meal.tags) ? meal.tags : [];
  const chips = tags.map(t => `
    <span class="meal-tag-chip" data-tag="${escapeAttr(t)}">
      <span class="meal-tag-label">${escapeHtml(t)}</span>
      <button class="meal-tag-remove" type="button" aria-label="Remove tag ${escapeAttr(t)}" title="Remove">×</button>
    </span>
  `).join('');
  return `
    <div class="meal-tags">
      <div class="meal-tag-chips">${chips}</div>
      <input class="input meal-tag-input" type="text"
             placeholder="Add tag (press Enter)…"
             aria-label="Add tag — press Enter to confirm">
    </div>
  `;
}

function bindCardCollapse(card, meal) {
  const btn = card.querySelector('.meal-card-collapse');
  const chev = card.querySelector('.meal-card-chevron');
  if (!btn) return;
  // Click anywhere on the header (except the inputs/buttons themselves)
  // toggles collapse — but the explicit chevron button is the focusable
  // affordance for keyboards/AT.
  const head = card.querySelector('.meal-card-head');
  function toggle() {
    const isCollapsed = collapsedMeals.has(meal.id);
    if (isCollapsed) collapsedMeals.delete(meal.id);
    else collapsedMeals.add(meal.id);
    const next = !isCollapsed;
    card.dataset.collapsed = String(next);
    btn.setAttribute('aria-expanded', String(!next));
    btn.title = next ? 'Expand' : 'Collapse';
    if (chev) chev.textContent = next ? '▸' : '▾';
  }
  btn.addEventListener('click', (ev) => { ev.stopPropagation(); toggle(); });
  if (head) {
    head.addEventListener('click', (ev) => {
      // Ignore clicks on form controls within the header.
      const target = ev.target;
      if (target.closest('input, button, textarea, select, a')) return;
      toggle();
    });
  }
}

function bindTagInteractions(card, meal, commit, state) {
  const tagInput = card.querySelector('.meal-tag-input');
  const chipsEl  = card.querySelector('.meal-tag-chips');
  if (!tagInput || !chipsEl) return;

  function commitTags(nextTags) {
    const meals = state.get('userMeals') || [];
    const next = meals.map(m => m.id === meal.id ? { ...m, tags: nextTags } : m);
    commit(next);
  }

  tagInput.addEventListener('keydown', (ev) => {
    if (ev.key !== 'Enter' && ev.key !== ',') return;
    ev.preventDefault();
    const value = tagInput.value.trim().replace(/^#/, '');
    if (!value) return;
    const current = Array.isArray(meal.tags) ? meal.tags : [];
    if (current.includes(value)) { tagInput.value = ''; return; }
    commitTags([...current, value]);
    tagInput.value = '';
  });

  chipsEl.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.meal-tag-remove');
    if (!btn) return;
    const chip = btn.closest('.meal-tag-chip');
    if (!chip) return;
    const value = chip.dataset.tag;
    const current = Array.isArray(meal.tags) ? meal.tags : [];
    commitTags(current.filter(t => t !== value));
  });
}

// --- Read-only category card (saved Remix) ---

function renderCategoryUserMealHtml(meal) {
  const cats = (meal.ingredient_categories || []).map(c =>
    `<li class="meal-static-cat">${escapeHtml(c)}</li>`).join('');
  return `
    <article class="meal-card meal-card-user-category" data-meal-id="${escapeAttr(meal.id)}" data-collapsed="${cardCollapseAttr(meal)}">
      ${cardHeaderHtml(meal, { badgeHtml: '<span class="meal-badge muted" title="Saved remix">remix</span>' })}
      <div class="meal-card-body">
        <textarea class="input meal-description" rows="2"
                  placeholder="Short description (optional)"
                  aria-label="Meal description">${escapeHtml(meal.notes || '')}</textarea>
        ${tagsBlockHtml(meal)}
        <ul class="meal-static-list">${cats}</ul>
      </div>
    </article>
  `;
}

function bindCategoryMealInteractions(card, meal, allMeals, commit) {
  const nameInput = card.querySelector('.meal-name');
  const descInput = card.querySelector('.meal-description');
  const deleteBtn = card.querySelector('.meal-delete');

  nameInput.addEventListener('change', () => {
    const next = allMeals.map(m => m.id === meal.id
      ? { ...m, name: nameInput.value.trim() || m.name }
      : m);
    commit(next);
  });

  descInput.addEventListener('change', () => {
    const text = descInput.value.trim();
    const next = allMeals.map(m => m.id === meal.id
      ? { ...m, notes: text || undefined }
      : m);
    commit(next);
  });

  deleteBtn.addEventListener('click', () => {
    if (!window.confirm(`Delete "${meal.name}"?`)) return;
    collapsedMeals.delete(meal.id);
    commit(allMeals.filter(m => m.id !== meal.id));
  });
}

// --- Ingredient-shape user meal card (gram-mixture) ---

function renderUserMealHtml(meal, ingredientById) {
  const totals = computeTotals(meal, ingredientById);
  const ingredients = meal.ingredients.map((ing, idx) => {
    const ingredient = ingredientById.get(ing.ingredientId);
    const label = ingredient ? ingredient.name : '(removed)';
    return `
      <li class="meal-ingredient" data-index="${idx}">
        <div class="meal-ingredient-head">
          <span class="meal-ingredient-name">${escapeHtml(label)}</span>
          <span class="meal-ingredient-grams muted">${ing.grams}g</span>
          <button class="meal-ingredient-remove" type="button"
                  aria-label="Remove ${escapeHtml(label)}" title="Remove">×</button>
        </div>
        <input type="range" class="meal-ingredient-slider"
               min="${GRAMS_MIN}" max="${GRAMS_MAX}" step="${GRAMS_STEP}"
               value="${ing.grams}"
               aria-label="${escapeHtml(label)} grams">
      </li>`;
  }).join('');

  return `
    <article class="meal-card" data-meal-id="${escapeAttr(meal.id)}" data-collapsed="${cardCollapseAttr(meal)}">
      ${cardHeaderHtml(meal)}
      <div class="meal-card-body">
        <textarea class="input meal-description" rows="2"
                  placeholder="Short description (optional)"
                  aria-label="Meal description">${escapeHtml(meal.notes || '')}</textarea>
        ${tagsBlockHtml(meal)}
        <ul class="meal-ingredients">${ingredients}</ul>
        <div class="meal-add-wrapper">
          <input class="input meal-add-input" type="text"
                 placeholder="Add ingredient…" autocomplete="off"
                 aria-label="Search ingredients">
          <div class="meal-add-suggestions" hidden role="listbox"></div>
        </div>
        <footer class="meal-stats muted">
          ${totals.grams}g · ${Math.round(totals.calories)} kcal
        </footer>
      </div>
    </article>
  `;
}

function bindMealInteractions(card, meal, allMeals, commit, ingredients, ingredientById) {
  const nameInput = card.querySelector('.meal-name');
  const descInput = card.querySelector('.meal-description');
  const deleteBtn = card.querySelector('.meal-delete');
  const addInput  = card.querySelector('.meal-add-input');
  const suggEl    = card.querySelector('.meal-add-suggestions');

  nameInput.addEventListener('change', () => {
    const next = allMeals.map(m => m.id === meal.id
      ? { ...m, name: nameInput.value.trim() || m.name }
      : m);
    commit(next);
  });

  descInput.addEventListener('change', () => {
    const text = descInput.value.trim();
    const next = allMeals.map(m => m.id === meal.id
      ? { ...m, notes: text || undefined }
      : m);
    commit(next);
  });

  deleteBtn.addEventListener('click', () => {
    if (!window.confirm(`Delete "${meal.name}"?`)) return;
    collapsedMeals.delete(meal.id);
    commit(allMeals.filter(m => m.id !== meal.id));
  });

  card.querySelectorAll('.meal-ingredient').forEach(li => {
    const idx     = +li.dataset.index;
    const slider  = li.querySelector('.meal-ingredient-slider');
    const gramsEl = li.querySelector('.meal-ingredient-grams');
    const remove  = li.querySelector('.meal-ingredient-remove');

    slider.addEventListener('input', () => {
      const g = +slider.value;
      gramsEl.textContent = `${g}g`;
      const next = allMeals.map(m => m.id !== meal.id ? m : {
        ...m,
        ingredients: m.ingredients.map((ing, i) => i === idx ? { ...ing, grams: g } : ing),
      });
      commit(next);
    });
    remove.addEventListener('click', () => {
      const next = allMeals.map(m => m.id !== meal.id ? m : {
        ...m,
        ingredients: m.ingredients.filter((_, i) => i !== idx),
      });
      commit(next);
    });
  });

  addInput.addEventListener('input', () => {
    const q = addInput.value.trim().toLowerCase();
    if (!q) { suggEl.hidden = true; suggEl.innerHTML = ''; return; }
    const matches = ingredients
      .filter(f => f.name.toLowerCase().includes(q))
      .slice(0, SUGGESTION_CAP);
    if (matches.length === 0) {
      suggEl.hidden = true;
      suggEl.innerHTML = '';
      return;
    }
    suggEl.innerHTML = matches.map(f =>
      `<button class="meal-add-option" type="button" role="option"
               data-ingredient-id="${escapeAttr(f.id)}">${escapeHtml(f.name)}</button>`
    ).join('');
    suggEl.hidden = false;
  });

  suggEl.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.meal-add-option');
    if (!btn) return;
    const ingredientId = btn.dataset.ingredientId;
    if (!ingredientById.has(ingredientId)) return;
    const next = allMeals.map(m => m.id !== meal.id ? m : {
      ...m,
      ingredients: [...m.ingredients, { ingredientId, grams: DEFAULT_GRAMS }],
    });
    commit(next);
    addInput.value = '';
    suggEl.hidden = true;
    suggEl.innerHTML = '';
  });

  addInput.addEventListener('blur', () => {
    setTimeout(() => { suggEl.hidden = true; }, 150);
  });
}

function computeTotals(meal, ingredientById) {
  let grams = 0;
  let calories = 0;
  for (const ing of meal.ingredients) {
    const ingredient = ingredientById.get(ing.ingredientId);
    if (!ingredient) continue;
    grams    += ing.grams;
    calories += (ingredient.calories || 0) * (ing.grams / 100);
  }
  return { grams, calories };
}

