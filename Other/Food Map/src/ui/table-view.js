/* Phase 8: sortable, filterable table view.
 *
 * Renders the current dataset as a table. Columns include identity
 * (name, category, group), all 8 per-100g nutrients, and a derived
 * composite score driven by user-adjustable weights.
 *
 * Composition with the rest of the app:
 *   - Reads `getCurrentIngredients()` for the current dataset (ingredients,
 *     category aggregates, or meal aggregates depending on viewLevel).
 *   - Reads the active set for ingredient + threshold filters — rows
 *     for excluded ids are HIDDEN here (not faded as in the 3D scene).
 *   - Clicking a row sets selectedIngredientId, so the detail panel opens
 *     the same way it does from a 3D pick. Selection persists across
 *     view switches because both views read the same state slice.
 *
 * State coupling:
 *   tableColumns      — column-id → visible bool. Persisted in main.js.
 *   compositeWeights  — per-nutrient weight ∈ [0, 2]. Persisted.
 *   tableSort         — { column, direction } | null. Session-only.
 *
 * Composite score:
 *   score = Σ w_n × orient(n, normalized(n))
 *   where orient flips the normalized value when "low is best" is the
 *   nutrient's default direction. Higher score = better. Renormalized
 *   across visible rows so the bar always fills [0, 100].
 */

import {
  NUTRIENT_FIELDS, NUTRIENT_META, NUTRIENT_DEFAULTS,
  FOOD_GROUPS, FOOD_GROUP_COLORS,
} from '../data/schema.js';
import { scaleForItem } from '../core/unit.js';
import { isWithinThresholds, distanceFromTargets } from '../core/scoring.js';
import { beginLoading } from './loading.js';

const GROUP_LABELS = ['Animal', 'Plant', 'Dairy'];

// Identity columns are ordered broadest → most refined:
//   name → food_group → category → subcategory.
// "Group" (animal/plant/dairy) was removed in Phase 13.5 round 3 — the
// colored dot next to the name in the Name column already conveys the
// same information visually, and the legend (now visible in both views)
// is the canonical key for what the dot means.
// Phase 13.5 round 6: each column carries a `defaultWidth` so the
// fixed-layout table doesn't squash everything into equal columns. The
// user can drag any edge to override.
const COLUMN_DEFS = [
  { id: 'name',          label: 'Name',        type: 'text',    align: 'left',  defaultWidth: 220, always: true },
  { id: 'food_group',    label: 'Food group',  type: 'text',    align: 'left',  defaultWidth: 130 },
  { id: 'category',      label: 'Category',    type: 'text',    align: 'left',  defaultWidth: 140 },
  { id: 'subcategory',   label: 'Subcategory', type: 'text',    align: 'left',  defaultWidth: 140 },
  ...NUTRIENT_FIELDS.map(n => ({
    id: n, label: NUTRIENT_META[n].label, type: 'nutrient', align: 'right', defaultWidth: 84,
  })),
  { id: 'composite',     label: 'Score',       type: 'composite', align: 'right', defaultWidth: 110 },
];

export function mountTableView(host, { state, getCurrentIngredients, getActiveSet, getHiddenSet = () => null, ranges }) {
  if (!host) return;

  host.classList.add('table-view');
  host.innerHTML = `
    <div class="table-toolbar">
      <div class="table-toolbar-left">
        <button class="btn btn-ghost table-columns-btn" type="button"
                aria-haspopup="true" aria-expanded="false">
          <span>Columns</span>
          <span aria-hidden="true">▾</span>
        </button>
        <input class="input table-search" type="search"
               placeholder="Search…"
               aria-label="Search by name">
        <span class="table-rowcount muted" aria-live="polite"></span>
      </div>
    </div>
    <div class="table-columns-menu" hidden role="menu"></div>
    <div class="table-scroll">
      <table class="data-table">
        <thead></thead>
        <tbody></tbody>
      </table>
    </div>
  `;

  const columnsBtn  = host.querySelector('.table-columns-btn');
  const columnsMenu = host.querySelector('.table-columns-menu');
  const searchEl    = host.querySelector('.table-search');
  const rowcountEl  = host.querySelector('.table-rowcount');
  const theadEl     = host.querySelector('.data-table thead');
  const tbodyEl     = host.querySelector('.data-table tbody');

  /* Phase 40 round 8: unit toggle moved to the header (mountUnitToggle).
   * Table just re-renders on nutrientUnit changes. */
  state.subscribe(s => s.nutrientUnit, () => renderBody());

  // Phase 13.5 round 3: name-only search box. Filters the visible rows
  // by case-insensitive substring; composes with the existing active-set
  // filter from main.js. Session-only (no reason to persist a stale
  // search across reloads).
  let searchQuery = '';
  searchEl.addEventListener('input', () => {
    searchQuery = searchEl.value.trim().toLowerCase();
    renderBody();
  });
  /* Tester feedback: the placeholder used to read "Search ingredients…"
   * even after the user switched to Categories or Meals view. The text
   * now follows state.viewLevel so it always names what the user is
   * actually about to search. */
  function syncSearchPlaceholder() {
    const level = state.get('viewLevel') || 'individual';
    const noun = level === 'meal' ? 'meals'
      : level === 'category'
        ? (state.get('categoryGroupBy') === 'subcategory' ? 'subcategories'
          : state.get('categoryGroupBy') === 'food_group' ? 'food groups'
          : 'categories')
        : 'ingredients';
    searchEl.placeholder = `Search ${noun}…`;
    searchEl.setAttribute('aria-label', `Search ${noun} by name`);
  }
  syncSearchPlaceholder();
  state.subscribe(s => s.viewLevel,       syncSearchPlaceholder);
  state.subscribe(s => s.categoryGroupBy, syncSearchPlaceholder);

  // --- Columns menu (column visibility + composite weights) ---

  function renderColumnsMenu() {
    const cols = state.get('tableColumns') || {};
    const weights = state.get('compositeWeights') || {};
    const level = state.get('viewLevel');

    // Hide columns the current view level zeroes out anyway (Phase
    // 13.5 round 5) so the menu doesn't offer toggles that have no
    // effect.
    const colItems = COLUMN_DEFS
      .filter(c => !c.always && !viewLevelHidesColumn(level, c.id))
      .map(c => {
        const visible = cols[c.id] !== false;
        return `
          <label class="table-columns-item">
            <input type="checkbox" data-column="${c.id}" ${visible ? 'checked' : ''}>
            <span>${c.label}</span>
          </label>`;
      }).join('');

    const weightItems = NUTRIENT_FIELDS.map(n => {
      const w = weights[n] != null ? weights[n] : 1;
      return `
        <label class="table-weight-item">
          <span class="table-weight-label">${NUTRIENT_META[n].label}</span>
          <input type="range" min="0" max="2" step="0.1" value="${w}"
                 data-weight="${n}" aria-label="${NUTRIENT_META[n].label} weight">
          <span class="table-weight-value muted">${w.toFixed(1)}×</span>
        </label>`;
    }).join('');

    columnsMenu.innerHTML = `
      <div class="table-columns-section">
        <div class="table-columns-title">Visible columns</div>
        ${colItems}
      </div>
      <div class="table-columns-section">
        <div class="table-columns-title">Composite-score weights</div>
        ${weightItems}
      </div>
    `;

    columnsMenu.querySelectorAll('input[data-column]').forEach(cb => {
      cb.addEventListener('change', () => {
        const id = cb.dataset.column;
        const next = { ...state.get('tableColumns'), [id]: cb.checked };
        state.set({ tableColumns: next });
      });
    });
    columnsMenu.querySelectorAll('input[data-weight]').forEach(slider => {
      slider.addEventListener('input', () => {
        const id = slider.dataset.weight;
        const v = Number(slider.value);
        const next = { ...state.get('compositeWeights'), [id]: v };
        state.set({ compositeWeights: next });
        const label = slider.parentElement.querySelector('.table-weight-value');
        if (label) label.textContent = `${v.toFixed(1)}×`;
      });
    });
  }

  columnsBtn.addEventListener('click', () => {
    const open = !columnsMenu.hidden;
    columnsMenu.hidden = open;
    columnsBtn.setAttribute('aria-expanded', String(!open));
  });
  // Phase 40: pointerdown (capture) so the containment check sees the
  // original target before any in-menu state change detaches it.
  document.addEventListener('pointerdown', (ev) => {
    if (columnsMenu.hidden) return;
    if (columnsMenu.contains(ev.target) || columnsBtn.contains(ev.target)) return;
    columnsMenu.hidden = true;
    columnsBtn.setAttribute('aria-expanded', 'false');
  }, true);
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && !columnsMenu.hidden) {
      columnsMenu.hidden = true;
      columnsBtn.setAttribute('aria-expanded', 'false');
    }
  });

  // --- Composite-score computation ---

  function computeComposite(ingredient, weights) {
    let total = 0;
    for (const n of NUTRIENT_FIELDS) {
      const w = weights[n];
      if (!w) continue;
      const r = ranges[n];
      const norm = (ingredient[n] - r.min) / Math.max(1e-6, r.max - r.min);
      const oriented = NUTRIENT_DEFAULTS[n].direction === 'max' ? norm : 1 - norm;
      total += w * oriented;
    }
    return total;
  }

  // --- Header + rows ---

  // Phase 13.5 round 5: per-viewLevel column blacklist. Category
  // aggregates have category === name (so showing both is redundant)
  // and meal aggregates fake category = 'Meal' across the board, so
  // those identity columns get hidden for the relevant view.
  function viewLevelHidesColumn(level, columnId) {
    if (level === 'category') {
      return columnId === 'category' || columnId === 'subcategory';
    }
    if (level === 'meal') {
      return columnId === 'food_group'
          || columnId === 'category'
          || columnId === 'subcategory';
    }
    return false;
  }

  function visibleColumns() {
    const cols = state.get('tableColumns') || {};
    const level = state.get('viewLevel');
    return COLUMN_DEFS.filter(c => {
      if (viewLevelHidesColumn(level, c.id)) return false;
      return c.always || cols[c.id] !== false;
    });
  }

  function dominantGroup(ingredient) {
    const w = ingredient.group_weights || [0, 0, 0];
    let idx = 0;
    let max = -Infinity;
    for (let i = 0; i < 3; i++) if (w[i] > max) { max = w[i]; idx = i; }
    return GROUP_LABELS[idx];
  }

  function groupBlendCss(ingredient) {
    // Phase 13.5 round 3: dot color follows the active legend scheme.
    if ((state.get('colorScheme') || 'rgb') === 'food_group') {
      let r = 0, g = 0, b = 0, total = 0;
      const fgw = ingredient.food_group_weights;
      if (fgw) {
        for (const grp of FOOD_GROUPS) {
          const w = fgw[grp]; if (!(w > 0)) continue;
          const c = FOOD_GROUP_COLORS[grp]; if (!c) continue;
          r += w * c[0]; g += w * c[1]; b += w * c[2]; total += w;
        }
      } else if (ingredient.food_group && FOOD_GROUP_COLORS[ingredient.food_group]) {
        const c = FOOD_GROUP_COLORS[ingredient.food_group];
        r = c[0]; g = c[1]; b = c[2]; total = 1;
      }
      if (total > 0) {
        return `rgb(${Math.round(r/total*255)}, ${Math.round(g/total*255)}, ${Math.round(b/total*255)})`;
      }
      return 'rgb(128, 128, 128)';
    }
    const [a = 0, p = 0, d = 0] = ingredient.group_weights || [];
    return `rgb(${Math.round(a * 255)}, ${Math.round(p * 255)}, ${Math.round(d * 255)})`;
  }

  // Phase 13.5 round 5: per-column widths, session-only. Initial value
  // null means "let the browser auto-size"; a pixel value overrides.
  const columnWidths = new Map();

  function renderHeader() {
    const sort = state.get('tableSort');
    const cols = visibleColumns();
    theadEl.innerHTML = `
      <tr>
        ${cols.map(c => {
          const isSort = sort && sort.column === c.id;
          const arrow = isSort ? (sort.direction === 'asc' ? '▲' : '▼') : '';
          const styleParts = [];
          if (c.align === 'right') styleParts.push('text-align: right');
          // User-resized width wins; otherwise use the per-column default
          // so fixed-layout doesn't equally distribute space.
          const w = columnWidths.get(c.id) || c.defaultWidth;
          if (w) styleParts.push(`width: ${w}px`);
          const styleAttr = styleParts.length ? ` style="${styleParts.join('; ')}"` : '';
          const alignAttr = c.align ? ` data-align="${c.align}"` : '';
          return `<th class="col-${c.id}" data-column="${c.id}"${alignAttr}${styleAttr}>
                    <button class="data-th-btn" type="button">
                      <span>${c.label}</span>
                      <span class="data-th-arrow">${arrow}</span>
                    </button>
                    <div class="th-resize" data-column-resize="${c.id}" aria-hidden="true"></div>
                  </th>`;
        }).join('')}
      </tr>
    `;
    theadEl.querySelectorAll('th[data-column]').forEach(th => {
      // Apply tracked width (the inline style template above only handles
      // the initial render; this catches re-renders without re-templating).
      const w = columnWidths.get(th.dataset.column);
      if (w) th.style.width = `${w}px`;

      // Sort handler on the .data-th-btn (NOT the whole th) so the
      // resize handle's clicks don't trigger a sort.
      const sortBtn = th.querySelector('.data-th-btn');
      if (sortBtn) sortBtn.addEventListener('click', () => {
        const id = th.dataset.column;
        const current = state.get('tableSort');
        let next;
        if (!current || current.column !== id) {
          next = { column: id, direction: 'asc' };
        } else if (current.direction === 'asc') {
          next = { column: id, direction: 'desc' };
        } else {
          next = null;
        }
        state.set({ tableSort: next });
      });
    });
    wireColumnResize();
  }

  function wireColumnResize() {
    theadEl.querySelectorAll('.th-resize').forEach(handle => {
      handle.addEventListener('pointerdown', (ev) => startResize(ev, handle));
    });
  }

  const tableEl = host.querySelector('.data-table');

  function startResize(ev, handle) {
    const th = handle.closest('th');
    if (!th) return;
    ev.preventDefault();
    ev.stopPropagation();
    const startX = ev.clientX;
    const startW = th.getBoundingClientRect().width;
    const column = handle.dataset.columnResize;
    handle.setPointerCapture(ev.pointerId);
    handle.classList.add('is-dragging');
    tableEl.classList.add('is-resizing');

    function onMove(mv) {
      const dx = mv.clientX - startX;
      const next = Math.max(48, Math.round(startW + dx));
      th.style.width = `${next}px`;
      columnWidths.set(column, next);
    }
    function onUp() {
      handle.releasePointerCapture(ev.pointerId);
      handle.classList.remove('is-dragging');
      tableEl.classList.remove('is-resizing');
      handle.removeEventListener('pointermove', onMove);
      handle.removeEventListener('pointerup', onUp);
      handle.removeEventListener('pointercancel', onUp);
    }
    handle.addEventListener('pointermove', onMove);
    handle.addEventListener('pointerup', onUp);
    handle.addEventListener('pointercancel', onUp);
  }

  function compareForColumn(a, b, column, weights) {
    if (column === 'name')        return a.name.localeCompare(b.name);
    if (column === 'food_group')  return (a.food_group  || '').localeCompare(b.food_group  || '');
    if (column === 'category')    return (a.category    || '').localeCompare(b.category    || '');
    if (column === 'subcategory') return (a.subcategory || '').localeCompare(b.subcategory || '');
    if (column === 'group')       return dominantGroup(a).localeCompare(dominantGroup(b));
    if (column === 'composite') {
      return computeComposite(a, weights) - computeComposite(b, weights);
    }
    return (a[column] ?? 0) - (b[column] ?? 0);
  }

  /* Bug-fix: large datasets (3700+ meal aggregates) make renderBody's
   * single .join take long enough to be felt. The render is now split:
   *   - Small (<800 rows): synchronous single-shot like before.
   *   - Large: streamed in 500-row chunks across animation frames with
   *     a progress indicator. The loading-indicator's delayed-fade CSS
   *     hides the chip during short renders, so this only surfaces for
   *     workloads where it would genuinely help.
   * `renderToken` lets a newer render cancel a still-running chunked
   * one — the in-flight render checks the token between chunks and
   * bails when it changes. */
  const CHUNK_ROW_THRESHOLD = 800;
  const CHUNK_SIZE = 500;
  let renderToken = 0;
  let activeLoadingHandle = null;

  // Tester feedback: Score mode tints each row with a green→red
  // gradient mirroring the 3D scene's per-dot coloring. Soft alpha
  // so the row text stays readable on both themes.
  const SCORE_GOOD_RGB = [0.30, 0.78, 0.45];
  const SCORE_BAD_RGB  = [0.92, 0.36, 0.32];
  function scoreTintCss(t) {
    const r = SCORE_GOOD_RGB[0] + (SCORE_BAD_RGB[0] - SCORE_GOOD_RGB[0]) * t;
    const g = SCORE_GOOD_RGB[1] + (SCORE_BAD_RGB[1] - SCORE_GOOD_RGB[1]) * t;
    const b = SCORE_GOOD_RGB[2] + (SCORE_BAD_RGB[2] - SCORE_GOOD_RGB[2]) * t;
    return `rgba(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)}, 0.20)`;
  }

  function buildRowHtml(ingredient, cols, weights, minScore, scoreSpread, selectedId, modeMark) {
    const cells = cols.map(c => {
      const align = c.align === 'right' ? ' style="text-align: right"' : '';
      if (c.id === 'name')        return `<td class="cell-name"${align} title="${escapeAttr(ingredient.name)}">
        <span class="ingredient-color-dot" style="background: ${groupBlendCss(ingredient)}" aria-hidden="true"></span>
        <span class="cell-name-text">${escapeHtml(ingredient.name)}</span>
      </td>`;
      if (c.id === 'food_group')  return `<td${align} title="${escapeAttr(ingredient.food_group  || '')}">${escapeHtml(ingredient.food_group  || '')}</td>`;
      if (c.id === 'category')    return `<td${align} title="${escapeAttr(ingredient.category    || '')}">${escapeHtml(ingredient.category    || '')}</td>`;
      if (c.id === 'subcategory') return `<td${align} title="${escapeAttr(ingredient.subcategory || '')}">${escapeHtml(ingredient.subcategory || '')}</td>`;
      if (c.id === 'group')       return `<td${align} title="${escapeAttr(dominantGroup(ingredient))}">${dominantGroup(ingredient)}</td>`;
      if (c.id === 'composite') {
        const raw = computeComposite(ingredient, weights);
        const pct = ((raw - minScore) / scoreSpread) * 100;
        return `<td${align} title="${pct.toFixed(0)} / 100">
          <div class="composite-cell">
            <div class="composite-bar" style="--pct: ${pct.toFixed(1)}%"></div>
            <span class="composite-value">${pct.toFixed(0)}</span>
          </div>
        </td>`;
      }
      const meta = NUTRIENT_META[c.id];
      const unit = state.get('nutrientUnit') || '100g';
      const scale = scaleForItem(ingredient, unit);
      const formatted = meta.format((+ingredient[c.id] || 0) * scale);
      return `<td${align} title="${escapeAttr(formatted)}">${formatted}</td>`;
    }).join('');
    const classes = [];
    if (ingredient.id === selectedId) classes.push('is-selected');
    if (modeMark && modeMark.kind === 'score')     classes.push('is-scored');
    const classAttr = classes.length ? ` class="${classes.join(' ')}"` : '';
    const styleAttr = (modeMark && modeMark.style) ? ` style="${modeMark.style}"` : '';
    return `<tr data-id="${escapeAttr(ingredient.id)}"${classAttr}${styleAttr}>${cells}</tr>`;
  }

  function renderBody() {
    const all = getCurrentIngredients();
    const activeSet = getActiveSet();
    const hiddenSet = typeof getHiddenSet === 'function' ? getHiddenSet() : null;
    let visibleFoods = activeSet ? all.filter(f => activeSet.has(f.id)) : all.slice();
    if (hiddenSet && hiddenSet.size > 0) {
      visibleFoods = visibleFoods.filter(f => !hiddenSet.has(f.id));
    }
    if (searchQuery) {
      visibleFoods = visibleFoods.filter(f => f.name.toLowerCase().includes(searchQuery));
    }

    const sort = state.get('tableSort');
    const weights = state.get('compositeWeights') || {};
    if (sort) {
      visibleFoods.sort((a, b) => {
        const cmp = compareForColumn(a, b, sort.column, weights);
        return sort.direction === 'asc' ? cmp : -cmp;
      });
    }

    let minScore = Infinity;
    let maxScore = -Infinity;
    for (const f of visibleFoods) {
      const s = computeComposite(f, weights);
      if (s < minScore) minScore = s;
      if (s > maxScore) maxScore = s;
    }
    const scoreSpread = Math.max(1e-6, maxScore - minScore);

    // Threshold mode → per-row tint. Score mode lerps green→red by
    // per-row RMS distance from each nutrient's midpoint,
    // renormalized across the current row set.
    const mode = state.get('thresholdMode') || 'filter';
    const unit = state.get('nutrientUnit') || '100g';
    const thresholds = unit === 'serving'
      ? (state.get('thresholdsServing') || state.get('thresholds'))
      : state.get('thresholds');
    const modeMarks = new Map();
    if (mode === 'score' && thresholds) {
      const dists = visibleFoods.map(f =>
        distanceFromTargets(f, thresholds, ranges, scaleForItem(f, unit))
      );
      let dMin = Infinity, dMax = -Infinity;
      for (const d of dists) { if (d < dMin) dMin = d; if (d > dMax) dMax = d; }
      const dSpread = Math.max(1e-6, dMax - dMin);
      for (let i = 0; i < visibleFoods.length; i++) {
        const t = (dists[i] - dMin) / dSpread;
        modeMarks.set(visibleFoods[i].id, {
          kind: 'score',
          style: `background: ${scoreTintCss(t)}`,
        });
      }
    }

    const cols = visibleColumns();
    const selectedId = state.get('selectedIngredientId');
    const total = visibleFoods.length;

    // Update rowcount immediately so the toolbar reflects the new state
    // even while the body is still streaming in.
    rowcountEl.textContent = `${total} of ${all.length} shown`;

    // Cancel any in-flight chunked render — the new one supersedes it.
    renderToken++;
    if (activeLoadingHandle) {
      activeLoadingHandle.finish();
      activeLoadingHandle = null;
    }

    if (total < CHUNK_ROW_THRESHOLD) {
      tbodyEl.innerHTML = visibleFoods
        .map(f => buildRowHtml(f, cols, weights, minScore, scoreSpread, selectedId, modeMarks.get(f.id)))
        .join('');
      return;
    }

    // Large render — clear immediately, then stream rows in chunks.
    tbodyEl.innerHTML = '';
    const myToken = renderToken;
    const handle = beginLoading(`Loading ${total.toLocaleString()} rows…`, total);
    activeLoadingHandle = handle;

    let i = 0;
    function step() {
      if (myToken !== renderToken) {
        // A newer render took over; abandon this one.
        handle.finish();
        return;
      }
      const end = Math.min(total, i + CHUNK_SIZE);
      let html = '';
      for (let k = i; k < end; k++) {
        const f = visibleFoods[k];
        html += buildRowHtml(f, cols, weights, minScore, scoreSpread, selectedId, modeMarks.get(f.id));
      }
      tbodyEl.insertAdjacentHTML('beforeend', html);
      i = end;
      handle.update(i);
      if (i < total) {
        requestAnimationFrame(step);
      } else {
        handle.finish();
        if (activeLoadingHandle === handle) activeLoadingHandle = null;
      }
    }
    requestAnimationFrame(step);
  }

  tbodyEl.addEventListener('click', (ev) => {
    const row = ev.target.closest('tr[data-id]');
    if (!row) return;
    state.set({ selectedIngredientId: row.dataset.id });
  });

  function renderAll() {
    renderColumnsMenu();
    renderHeader();
    renderBody();
  }

  renderAll();

  state.subscribe(s => s.tableColumns,     renderAll);
  state.subscribe(s => s.compositeWeights, () => { renderHeader(); renderBody(); });
  state.subscribe(s => s.tableSort,        () => { renderHeader(); renderBody(); });
  state.subscribe(s => s.ingredientFilter,      renderBody);
  state.subscribe(s => s.ingredientFilterMatch, renderBody); // Phase 40 round 3
  state.subscribe(s => s.thresholds,            renderBody);
  state.subscribe(s => s.thresholdsServing,     renderBody); // Phase 40 round 11
  state.subscribe(s => s.thresholdMode,         renderBody);
  state.subscribe(s => s.restrictions,          renderBody);
  state.subscribe(s => s.tagFilter,             renderBody);  // Phase 26
  state.subscribe(s => s.categoryFilter,        renderBody);  // Phase 40 round 4
  state.subscribe(s => s.foodGroupFilter,       renderBody);  // Phase 40 round 4
  state.subscribe(s => s.dietFilter,            renderBody);  // Phase 40 round 7
  state.subscribe(s => s.cuisineFilter,         renderBody);  // Phase 40 round 7
  state.subscribe(s => s.dietCuisineFilterMatch,renderBody);  // Phase 40 round 8
  state.subscribe(s => s.ingredientFilterScope, renderBody);  // Phase 40 round 9
  state.subscribe(s => s.categoryFilterScope,   renderBody);  // Phase 40 round 9
  state.subscribe(s => s.tagFilterScope,        renderBody);  // Phase 40 round 9
  state.subscribe(s => s.dietCuisineFilterScope,renderBody);  // Phase 40 round 9
  state.subscribe(s => s.legendHidden,          renderBody);  // Phase 40 round 3 — color filter is now a real filter
  state.subscribe(s => s.colorScheme,           renderBody);  // legendHidden's effective key depends on scheme
  state.subscribe(s => s.viewLevel,        renderAll);
  state.subscribe(s => s.categoryGroupBy,  renderAll); // Phase 13.5 round 7
  // Tester feedback: "Modify all meals" + user meal edits weren't
  // reaching the table. Re-render when the underlying meal dataset
  // shifts so the table tracks the 3D view.
  state.subscribe(s => s.mealComposition,  renderBody);
  state.subscribe(s => s.userMeals,        renderBody);
  state.subscribe(s => s.mealDraft,        renderBody);
  state.subscribe(s => s.selectedIngredientId,   () => {
    // Only swap the selection class — a full rebuild would jump scroll.
    const id = state.get('selectedIngredientId');
    tbodyEl.querySelectorAll('tr.is-selected').forEach(tr => tr.classList.remove('is-selected'));
    if (id) {
      const tr = tbodyEl.querySelector(`tr[data-id="${cssEscape(id)}"]`);
      if (tr) {
        tr.classList.add('is-selected');
        // Phase 40.3: scroll the freshly-selected row into view so a
        // 3D click that targeted an off-screen row is visible when the
        // user flips to the table.
        if (typeof tr.scrollIntoView === 'function') {
          tr.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
      }
    }
  });
  // Phase 40.3: when switching from table → 3D and back, scroll the
  // currently-selected row into view. Same view-mode subscription as
  // the canvas/table swap in main.js, but landing in this module.
  state.subscribe(s => s.view, (view) => {
    if (view !== 'table') return;
    const id = state.get('selectedIngredientId');
    if (!id) return;
    // Wait one frame for the table to re-show before measuring.
    requestAnimationFrame(() => {
      const tr = tbodyEl.querySelector(`tr[data-id="${cssEscape(id)}"]`);
      if (tr && typeof tr.scrollIntoView === 'function') {
        tr.scrollIntoView({ block: 'center' });
      }
    });
  });
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function escapeAttr(s) { return escapeHtml(s); }
function cssEscape(s) {
  if (typeof CSS !== 'undefined' && CSS.escape) return CSS.escape(String(s));
  return String(s).replace(/(["\\])/g, '\\$1');
}
