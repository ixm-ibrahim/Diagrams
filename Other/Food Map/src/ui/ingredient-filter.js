/* 3-level checkbox tree (food_group → category → ingredient).
 *
 * Tree shape is derived from `ingredients`:
 *   - Top level: food_group (food-science classification: Vegetables, Fruits,
 *     Grains, Protein (animal/plant), Dairy, etc.). This is independent of
 *     the 3-channel [animal, plant, dairy] used for visualization color.
 *   - Mid level: categories within each food_group (ingredient.category).
 *   - Leaf level: individual ingredients.
 *
 * Empty food_groups (groups with no ingredients in the dataset) are omitted.
 *
 * State coupling:
 *   - Source of truth = state.ingredientFilter.excludedIds. UI mutates
 *     this via excludeIds/includeIds in core/filters.js and re-reads to
 *     refresh checkbox visuals.
 *   - DOM is rendered once at mount. Filter changes only touch each
 *     checkbox's `.checked` / `.indeterminate` props — no reconciliation.
 *
 * Search:
 *   - Filters which leaves are *visible*. Checkbox state is unaffected.
 *   - Matching leaves stay visible; their category and group ancestors
 *     auto-expand to reveal them.
 *
 * Tri-state behavior:
 *   - Leaf:  checked = id not in excludedIds
 *   - Cat:   all leaves checked / unchecked / mixed → checked / unchecked / indeterminate
 *   - Group: same logic over its categories' leaves
 *   - Clicking a parent: if checked → uncheck all descendants;
 *                        if unchecked or indeterminate → check all descendants.
 *     (Matches native HTML checkbox behavior on click.)
 */

import { excludeIds, includeIds } from '../core/filters.js';
import { createRailSection } from './left-rail.js';
import { FOOD_GROUPS } from '../data/schema.js';

function buildTree(ingredients) {
  const byGroup = new Map(FOOD_GROUPS.map(name => [name, new Map()]));
  for (const ing of ingredients) {
    const group = byGroup.get(ing.food_group);
    if (!group) continue; // unknown food_group — ignored
    if (!group.has(ing.category)) group.set(ing.category, []);
    group.get(ing.category).push(ing);
  }
  // Phase 13.5: alphabetical at every level (top food_groups, mid
  // categories, leaf ingredients) so users can scan by name. FOOD_GROUPS'
  // declaration order isn't alphabetical because the constant is also
  // used elsewhere where semantic grouping matters; we sort at render.
  return [...FOOD_GROUPS]
    .sort((a, b) => a.localeCompare(b))
    .map(name => ({
      name,
      categories: [...byGroup.get(name).entries()]
        .map(([catName, leaves]) => ({
          name: catName,
          leaves: leaves.slice().sort((a, b) => a.name.localeCompare(b.name)),
        }))
        .sort((a, b) => a.name.localeCompare(b.name)),
    }))
    .filter(g => g.categories.length > 0);
}

export function mountIngredientFilter(host, { state, ingredients }) {
  if (!host) return;

  const tree = buildTree(ingredients);
  const totalLeaves = ingredients.length;

  const { root: section, body } = createRailSection({
    title: 'Filter by ingredient',
    tooltip: 'A 3-level tree (food group → category → ingredient). Uncheck individual items to remove them from the map and the table.',
  });
  host.appendChild(section);

  const root = body;
  root.classList.add('ingredient-filter');
  root.innerHTML = `
    <div class="ingredient-filter-controls">
      <input type="search" class="input ingredient-filter-search"
             placeholder="Search ingredients…"
             aria-label="Search ingredients">
      <span class="ingredient-filter-count muted"></span>
    </div>
    <div class="ingredient-filter-bulk-row">
      <button class="btn-link ingredient-filter-bulk" type="button"></button>
    </div>
    <div class="filter-modes-row">
      <div class="filter-mode-pair">
        <span class="filter-mode-label muted">Allow extras:</span>
        <div class="filter-scope-toggle seg-group" role="group"
             aria-label="ANY (extras allowed) vs ALL (only the selected ingredients)"
             title="ANY — meals can contain other ingredients too. ALL — meals must contain ONLY the selected ingredients (no extras).">
          <button type="button" class="seg-btn seg-btn-sm" data-scope="any">ANY</button>
          <button type="button" class="seg-btn seg-btn-sm" data-scope="all">ALL</button>
        </div>
      </div>
      <div class="filter-mode-pair">
        <span class="filter-mode-label muted">Combine:</span>
        <div class="filter-match-toggle seg-group" role="group"
             aria-label="OR (at least one) vs AND (every one)"
             title="OR — at least one checked ingredient must be present. AND — every checked ingredient must be present.">
          <button type="button" class="seg-btn seg-btn-sm" data-match="any">OR</button>
          <button type="button" class="seg-btn seg-btn-sm" data-match="all">AND</button>
        </div>
      </div>
    </div>
    <div class="ingredient-filter-tree" role="tree"></div>
  `;

  const searchInput = root.querySelector('.ingredient-filter-search');
  const countEl     = root.querySelector('.ingredient-filter-count');
  const bulkBtn     = root.querySelector('.ingredient-filter-bulk');
  const matchGroup  = root.querySelector('.filter-match-toggle');
  const scopeGroup  = root.querySelector('.filter-scope-toggle');
  const treeEl      = root.querySelector('.ingredient-filter-tree');

  /* Phase 40 round 9: TWO independent toggles per section.
   *   match (AND/OR): how multiple selections combine — within-section logic
   *   scope (ANY/ALL): whether items can carry extras beyond the selection
   * State stays per-filter so each section is independently configurable. */
  function refreshToggles() {
    const matchCur = state.get('ingredientFilterMatch') || 'any';
    matchGroup.querySelectorAll('[data-match]').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.match === matchCur);
    });
    const scopeCur = state.get('ingredientFilterScope') || 'any';
    scopeGroup.querySelectorAll('[data-scope]').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.scope === scopeCur);
    });
  }
  matchGroup.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-match]');
    if (!btn) return;
    state.set({ ingredientFilterMatch: btn.dataset.match });
  });
  scopeGroup.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-scope]');
    if (!btn) return;
    state.set({ ingredientFilterScope: btn.dataset.scope });
  });
  state.subscribe(s => s.ingredientFilterMatch, refreshToggles);
  state.subscribe(s => s.ingredientFilterScope, refreshToggles);
  refreshToggles();

  /* Phase 40 round 3: smart Check-all / Uncheck-all toggle. Label flips
   * with majority state: shows "Uncheck all" when ≥half are checked,
   * "Check all" otherwise. */
  function refreshBulkLabel() {
    const filter = state.get('ingredientFilter') || { excludedIds: [] };
    const excluded = (filter.excludedIds || []).length;
    const checkedCount = totalLeaves - excluded;
    const majorityChecked = checkedCount * 2 >= totalLeaves;
    bulkBtn.textContent = majorityChecked ? 'Uncheck all' : 'Check all';
    bulkBtn.dataset.action = majorityChecked ? 'uncheck' : 'check';
  }
  bulkBtn.addEventListener('click', () => {
    const action = bulkBtn.dataset.action;
    if (action === 'uncheck') {
      state.set({ ingredientFilter: { excludedIds: ingredients.map(f => f.id) } });
    } else {
      state.set({ ingredientFilter: { excludedIds: [] } });
    }
  });
  state.subscribe(s => s.ingredientFilter, refreshBulkLabel);
  refreshBulkLabel();

  // Per-node DOM refs so updates are O(visible) not O(rerender).
  /** @type {Array<{ group, categories: Array<{ category, leaves: Array<{ingredient, checkbox, row}>, checkbox, row, body, disclose }>, checkbox, row, body, disclose }>} */
  const nodes = [];

  treeEl.innerHTML = tree.map((group, gi) => {
    const leavesInGroup = group.categories.reduce((acc, c) => acc + c.leaves.length, 0);
    return `
      <div class="filter-group" data-group="${escapeAttr(group.name)}">
        <div class="filter-row filter-row-group">
          <button class="filter-disclose" type="button" aria-expanded="true">
            <span aria-hidden="true">▾</span>
          </button>
          <label class="filter-check">
            <input type="checkbox" class="filter-checkbox" data-level="group" data-gi="${gi}">
            <span class="filter-label">${escapeHtml(group.name)}</span>
          </label>
          <span class="filter-count muted">${leavesInGroup}</span>
        </div>
        <div class="filter-body">
          ${group.categories.map((cat, ci) => `
            <div class="filter-category" data-category="${escapeAttr(cat.name)}">
              <div class="filter-row filter-row-category">
                <button class="filter-disclose" type="button" aria-expanded="false">
                  <span aria-hidden="true">▸</span>
                </button>
                <label class="filter-check">
                  <input type="checkbox" class="filter-checkbox" data-level="category"
                         data-gi="${gi}" data-ci="${ci}">
                  <span class="filter-label">${escapeHtml(cat.name)}</span>
                </label>
                <span class="filter-count muted">${cat.leaves.length}</span>
              </div>
              <ul class="filter-leaves" hidden>
                ${cat.leaves.map((leaf, li) => `
                  <li class="filter-leaf" data-id="${escapeAttr(leaf.id)}">
                    <label class="filter-check">
                      <input type="checkbox" class="filter-checkbox" data-level="leaf"
                             data-gi="${gi}" data-ci="${ci}" data-li="${li}"
                             data-id="${escapeAttr(leaf.id)}">
                      <span class="filter-label">${escapeHtml(leaf.name)}</span>
                    </label>
                  </li>`).join('')}
              </ul>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }).join('');

  // Wire DOM refs into `nodes` so updates can target each checkbox cheaply.
  tree.forEach((group, gi) => {
    const groupEl = treeEl.querySelector(`.filter-group[data-group="${cssEscape(group.name)}"]`);
    const groupNode = {
      group, gi,
      el: groupEl,
      row: groupEl.querySelector('.filter-row-group'),
      checkbox: groupEl.querySelector(`.filter-checkbox[data-level="group"]`),
      body: groupEl.querySelector(':scope > .filter-body'),
      disclose: groupEl.querySelector(':scope > .filter-row-group .filter-disclose'),
      categories: [],
    };

    group.categories.forEach((cat, ci) => {
      const catEl = groupEl.querySelectorAll('.filter-category')[ci];
      const catNode = {
        category: cat, gi, ci,
        el: catEl,
        row: catEl.querySelector('.filter-row-category'),
        checkbox: catEl.querySelector(`.filter-checkbox[data-level="category"]`),
        body: catEl.querySelector('.filter-leaves'),
        disclose: catEl.querySelector('.filter-disclose'),
        leaves: [],
      };

      cat.leaves.forEach((leaf, li) => {
        const leafEl = catEl.querySelectorAll('.filter-leaf')[li];
        catNode.leaves.push({
          ingredient: leaf, gi, ci, li,
          el: leafEl,
          checkbox: leafEl.querySelector('.filter-checkbox'),
        });
      });

      groupNode.categories.push(catNode);
    });

    nodes.push(groupNode);
  });

  // Disclosure toggles — both food_group and category levels default
  // closed so the filter tree opens compact and the user picks which
  // branches to drill into.
  for (const groupNode of nodes) {
    setDisclosed(groupNode, false);
    groupNode.disclose.addEventListener('click', () => {
      const open = groupNode.body.hasAttribute('hidden') ? true : !isDisclosed(groupNode);
      setDisclosed(groupNode, open);
    });
    for (const catNode of groupNode.categories) {
      setDisclosed(catNode, false);
      catNode.disclose.addEventListener('click', () => {
        setDisclosed(catNode, !isDisclosed(catNode));
      });
    }
  }

  // Checkbox click handlers — drive state mutations.
  // Native checkbox click semantics: indeterminate → checked → unchecked → checked → …
  // For groups/categories we override to: any state → if checked, uncheck all;
  // if not checked (= unchecked or indeterminate), check all. The browser has
  // already flipped `.checked` by the time `change` fires, so we read what it
  // wants and propagate to descendants.
  treeEl.addEventListener('change', (ev) => {
    const cb = ev.target;
    if (!(cb instanceof HTMLInputElement) || cb.type !== 'checkbox') return;
    const level = cb.dataset.level;
    const wantChecked = cb.checked;

    if (level === 'leaf') {
      const id = cb.dataset.id;
      const filter = state.get('ingredientFilter');
      const next = wantChecked ? includeIds(filter, [id]) : excludeIds(filter, [id]);
      state.set({ ingredientFilter: next });
      return;
    }

    if (level === 'category') {
      const cat = nodes[+cb.dataset.gi].categories[+cb.dataset.ci];
      const ids = cat.leaves.map(l => l.ingredient.id);
      const filter = state.get('ingredientFilter');
      const next = wantChecked ? includeIds(filter, ids) : excludeIds(filter, ids);
      state.set({ ingredientFilter: next });
      return;
    }

    if (level === 'group') {
      const group = nodes[+cb.dataset.gi];
      const ids = group.categories.flatMap(c => c.leaves.map(l => l.ingredient.id));
      const filter = state.get('ingredientFilter');
      const next = wantChecked ? includeIds(filter, ids) : excludeIds(filter, ids);
      state.set({ ingredientFilter: next });
      return;
    }
  });

  // Re-render checkbox state from the filter.
  function refreshCheckboxes() {
    const filter = state.get('ingredientFilter');
    const excluded = new Set(filter?.excludedIds || []);
    let visible = 0;
    let active = 0;

    for (const groupNode of nodes) {
      let groupChecked = 0;
      let groupTotal = 0;

      for (const catNode of groupNode.categories) {
        let catChecked = 0;
        const catTotal = catNode.leaves.length;

        for (const leafNode of catNode.leaves) {
          const isExcluded = excluded.has(leafNode.ingredient.id);
          leafNode.checkbox.checked = !isExcluded;
          leafNode.checkbox.indeterminate = false;
          if (!isExcluded) { catChecked++; active++; }
        }

        if (catChecked === 0) {
          catNode.checkbox.checked = false;
          catNode.checkbox.indeterminate = false;
        } else if (catChecked === catTotal) {
          catNode.checkbox.checked = true;
          catNode.checkbox.indeterminate = false;
        } else {
          catNode.checkbox.checked = false;
          catNode.checkbox.indeterminate = true;
        }

        groupChecked += catChecked;
        groupTotal += catTotal;
      }

      if (groupChecked === 0) {
        groupNode.checkbox.checked = false;
        groupNode.checkbox.indeterminate = false;
      } else if (groupChecked === groupTotal) {
        groupNode.checkbox.checked = true;
        groupNode.checkbox.indeterminate = false;
      } else {
        groupNode.checkbox.checked = false;
        groupNode.checkbox.indeterminate = true;
      }
    }

    // Search-visibility count is recomputed in applySearch.
    visible = totalLeaves;
    countEl.dataset.activeCount = String(active);
    countEl.dataset.totalCount = String(totalLeaves);
    updateCountText();
  }

  function updateCountText() {
    const v = Number(countEl.dataset.visibleCount ?? totalLeaves);
    countEl.textContent = `${v} of ${totalLeaves} visible`;
  }

  // --- Search ---

  function applySearch(q) {
    const query = q.trim().toLowerCase();
    let visibleLeaves = 0;

    for (const groupNode of nodes) {
      let groupAnyVisible = false;

      for (const catNode of groupNode.categories) {
        let catAnyVisible = false;
        const catMatchesSelf = !query || catNode.category.name.toLowerCase().includes(query);

        for (const leafNode of catNode.leaves) {
          const matchesSelf = !query || leafNode.ingredient.name.toLowerCase().includes(query);
          const visible = !query || matchesSelf || catMatchesSelf
                                  || groupNode.group.name.toLowerCase().includes(query);
          leafNode.el.hidden = !visible;
          if (visible) { catAnyVisible = true; visibleLeaves++; }
        }

        catNode.el.hidden = !catAnyVisible;
        if (catAnyVisible) groupAnyVisible = true;

        // While searching, force categories open so matches are visible;
        // when search clears, restore the user's manual open state by
        // collapsing categories (they default closed).
        if (query) setDisclosed(catNode, catAnyVisible);
        else       setDisclosed(catNode, false);
      }

      groupNode.el.hidden = !groupAnyVisible;
      // While searching, force groups open so matches are visible; when
      // search clears, collapse back to the default closed state.
      if (query) setDisclosed(groupNode, groupAnyVisible);
      else       setDisclosed(groupNode, false);
    }

    countEl.dataset.visibleCount = String(visibleLeaves);
    updateCountText();
  }

  searchInput.addEventListener('input', (ev) => applySearch(ev.target.value));

  // --- Initial render + subscriptions ---

  refreshCheckboxes();
  applySearch('');
  state.subscribe(s => s.ingredientFilter, refreshCheckboxes);
}

// --- Helpers ---

function isDisclosed(node) {
  return node.disclose.getAttribute('aria-expanded') === 'true';
}

function setDisclosed(node, open) {
  node.disclose.setAttribute('aria-expanded', open ? 'true' : 'false');
  node.disclose.querySelector('span').textContent = open ? '▾' : '▸';
  if (open) node.body.removeAttribute('hidden');
  else      node.body.setAttribute('hidden', '');
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function escapeAttr(s) {
  return escapeHtml(s);
}
function cssEscape(s) {
  if (typeof CSS !== 'undefined' && CSS.escape) return CSS.escape(String(s));
  return String(s).replace(/(["\\])/g, '\\$1');
}
