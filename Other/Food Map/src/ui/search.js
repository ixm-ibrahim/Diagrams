/* Phase 40.4: name-search dropdown.
 *
 * Lives in the header. Searches across the CURRENT view level
 * (ingredients / categories / meals). Results are body-portaled
 * dropdown so they're not clipped by the header chrome.
 *
 * Behavior:
 *   - Input focused with content → dropdown opens with up to MAX_RESULTS
 *     matches (case-insensitive substring of name + secondary fields).
 *   - Restricted items (Phase 40.1 hidden set) are filtered out.
 *   - Clicking a result sets state.selectedIngredientId so the rest of
 *     the app (detail panel, scene halo, table) reacts uniformly.
 *   - Escape clears + blurs; outside click closes.
 *
 * Decoupled from picking.js — this lives entirely in DOM space.
 */

import { FOOD_GROUP_COLORS } from '../data/schema.js';

/* Progressive disclosure:
 *   - First batch: INITIAL_RESULTS rows.
 *   - "Show more" adds RESULT_STEP rows at a time.
 *   - "Show all" reveals everything that matched.
 * The dropdown is already scrollable, so the user can still scan with
 * Page Up/Down once they've expanded. */
const INITIAL_RESULTS = 20;
const RESULT_STEP     = 20;
const VIEWPORT_MARGIN = 8;

export function mountSearch(root, {
  state,
  getCurrentIngredients,
  isHidden = () => false,
}) {
  if (!root) return;

  root.classList.add('search-box');
  // Phase 40 round 2: custom clear button. The native ::-webkit-search-cancel
  // button is ~12px and finicky to click; this one is 28×28 and uses the
  // full bounding box as a hit target.
  root.innerHTML = `
    <input class="search-input input" type="search"
           placeholder="Search…" aria-label="Search ingredients, categories, or meals"
           autocomplete="off">
    <button class="search-clear" type="button" aria-label="Clear search" title="Clear" hidden>×</button>
  `;
  const inputEl = root.querySelector('.search-input');
  const clearBtn = root.querySelector('.search-clear');

  function syncClearVisibility() {
    clearBtn.hidden = !inputEl.value;
  }
  clearBtn.addEventListener('click', (ev) => {
    ev.preventDefault();
    inputEl.value = '';
    syncClearVisibility();
    close();
    inputEl.focus();
  });

  const dropdown = document.createElement('div');
  dropdown.className = 'search-dropdown';
  dropdown.hidden = true;
  dropdown.setAttribute('role', 'listbox');
  document.body.appendChild(dropdown);

  let allMatches  = [];   // full sorted list; lastResults is its prefix
  let lastResults = [];
  let activeIndex = -1;
  let displayLimit = INITIAL_RESULTS;

  function close() {
    if (dropdown.hidden) return;
    dropdown.hidden = true;
    dropdown.innerHTML = '';
    allMatches  = [];
    lastResults = [];
    activeIndex = -1;
    displayLimit = INITIAL_RESULTS;
    // Phase 40 round 2: clear the preview pulse when the dropdown closes
    // — leaving it on would orphan a pulsing dot with no menu to dismiss.
    if (state.get('previewIngredientId') !== null) {
      state.set({ previewIngredientId: null });
    }
    document.removeEventListener('pointerdown', onOutside, true);
  }

  function onOutside(ev) {
    if (root.contains(ev.target) || dropdown.contains(ev.target)) return;
    close();
  }

  function positionDropdown() {
    if (dropdown.hidden) return;
    const rect = inputEl.getBoundingClientRect();
    dropdown.style.left = `${Math.round(Math.max(VIEWPORT_MARGIN, rect.left))}px`;
    dropdown.style.top  = `${Math.round(rect.bottom + 4)}px`;
    dropdown.style.minWidth = `${Math.round(rect.width)}px`;
  }

  function render() {
    if (lastResults.length === 0) {
      dropdown.innerHTML = `<p class="search-empty muted">No matches.</p>`;
      return;
    }
    const rowsHtml = lastResults.map((r, i) => `
      <button class="search-row${i === activeIndex ? ' is-active' : ''}"
              type="button" role="option" data-index="${i}">
        <span class="search-swatch" style="background: ${swatchCss(r)};"
              aria-hidden="true"></span>
        <span class="search-text">
          <span class="search-name">${escapeHtml(r.name)}</span>
          <span class="search-sub muted">${escapeHtml(subtitleFor(r))}</span>
        </span>
      </button>
    `).join('');

    // Progressive-disclosure footer. Renders when more matches exist
    // than are currently shown. "Show more" adds a single step of
    // RESULT_STEP; "Show all" jumps straight to everything.
    let footerHtml = '';
    const total = allMatches.length;
    const shown = lastResults.length;
    if (total > shown) {
      const remaining = total - shown;
      const stepSize = Math.min(RESULT_STEP, remaining);
      // Drop the "Show more" button when one more step would equal
      // "Show all" anyway — keeps the choice clean.
      const showStepBtn = remaining > stepSize;
      footerHtml = `<div class="search-footer">`;
      if (showStepBtn) {
        footerHtml += `<button class="search-more" type="button" data-action="more">
          Show ${stepSize} more
        </button>`;
      }
      footerHtml += `<button class="search-more" type="button" data-action="all">
        Show all (${remaining}${showStepBtn ? ' more total' : ' more'})
      </button>`;
      footerHtml += `</div>`;
    }

    dropdown.innerHTML = rowsHtml + footerHtml;
  }

  function open(q) {
    const all = getCurrentIngredients() || [];
    const query = String(q || '').trim().toLowerCase();
    if (!query) {
      lastResults = [];
      activeIndex = -1;
      dropdown.hidden = true;
      return;
    }
    // Collect ALL matches first, then sort, then slice — otherwise a
    // pre-cap in the loop excludes high-ranking items that happen to
    // appear later in the dataset iteration order. Example bug: in
    // Meals view, the corpus list contains thousands of multi-category
    // patterns like "Other vegetables + Red meat + Salt & seasonings"
    // that match "red meat" as a substring. They fill the 12-row cap
    // before the loop ever reaches the single-category "Red meat"
    // pattern, even though it's a prefix match and should be #1.
    const matches = [];
    for (const item of all) {
      if (!item || !item.name) continue;
      if (isHidden(item.id)) continue;
      const hay = item.name.toLowerCase();
      if (!hay.includes(query)) continue;
      matches.push(item);
    }
    // Sort tiers: exact name → prefix match → substring match.
    // Within every tier, ALPHABETICAL (case-insensitive). The earlier
    // length-based tiebreaker bubbled short names like "Milk" above
    // longer prefix matches like "Mloukhia", which combined with the
    // 12-row cap meant the long ones were silently dropped. Tester
    // explicitly asked for alphabetical scan order.
    matches.sort((a, b) => {
      const an = a.name.toLowerCase();
      const bn = b.name.toLowerCase();
      const aExact = an === query ? 0 : 1;
      const bExact = bn === query ? 0 : 1;
      if (aExact !== bExact) return aExact - bExact;
      const aPrefix = an.startsWith(query) ? 0 : 1;
      const bPrefix = bn.startsWith(query) ? 0 : 1;
      if (aPrefix !== bPrefix) return aPrefix - bPrefix;
      return an.localeCompare(bn);
    });
    allMatches  = matches;
    displayLimit = INITIAL_RESULTS;
    lastResults = matches.slice(0, displayLimit);
    activeIndex = matches.length > 0 ? 0 : -1;
    dropdown.hidden = false;
    render();
    positionDropdown();
    document.addEventListener('pointerdown', onOutside, true);
  }

  function expandResults(target) {
    if (allMatches.length === 0) return;
    displayLimit = target === 'all'
      ? allMatches.length
      : Math.min(displayLimit + RESULT_STEP, allMatches.length);
    lastResults = allMatches.slice(0, displayLimit);
    render();
    positionDropdown();
  }

  function commit(idx) {
    const r = lastResults[idx];
    if (!r) return;
    state.set({ selectedIngredientId: r.id });
    inputEl.value = '';
    syncClearVisibility();
    close();
    inputEl.blur();
  }

  inputEl.addEventListener('input', () => {
    syncClearVisibility();
    open(inputEl.value);
  });
  inputEl.addEventListener('focus', () => {
    // Bug-fix: only re-open if the dropdown is currently closed.
    // Previously, programmatic refocus (after clicking "Show more" /
    // "Show all") would call open() which reset displayLimit back to
    // INITIAL_RESULTS, undoing the expansion.
    if (inputEl.value.trim() && dropdown.hidden) open(inputEl.value);
  });

  inputEl.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') {
      if (dropdown.hidden && !inputEl.value) {
        inputEl.blur();
      } else {
        inputEl.value = '';
        close();
      }
      return;
    }
    if (dropdown.hidden) return;
    if (ev.key === 'ArrowDown') {
      ev.preventDefault();
      if (lastResults.length === 0) return;
      activeIndex = (activeIndex + 1) % lastResults.length;
      render();
    } else if (ev.key === 'ArrowUp') {
      ev.preventDefault();
      if (lastResults.length === 0) return;
      activeIndex = (activeIndex - 1 + lastResults.length) % lastResults.length;
      render();
    } else if (ev.key === 'Enter') {
      ev.preventDefault();
      if (activeIndex >= 0) commit(activeIndex);
    }
  });

  dropdown.addEventListener('click', (ev) => {
    const more = ev.target.closest('.search-more');
    if (more) {
      expandResults(more.dataset.action);
      // Keep focus on the input so the user can keep typing.
      inputEl.focus();
      return;
    }
    const row = ev.target.closest('.search-row');
    if (!row) return;
    commit(+row.dataset.index);
  });

  // Phase 40 round 2: hovering a row previews the corresponding dot in
  // the 3D scene (pulses + draws above any occluders) without opening
  // the detail panel. Two pulses can coexist — the selected dot AND the
  // currently-previewed search row — which is exactly what the user
  // wants for "where am I about to land?".
  dropdown.addEventListener('pointerover', (ev) => {
    const row = ev.target.closest('.search-row');
    if (!row) return;
    const r = lastResults[+row.dataset.index];
    if (!r) return;
    if (state.get('previewIngredientId') !== r.id) {
      state.set({ previewIngredientId: r.id });
    }
  });
  dropdown.addEventListener('pointerout', (ev) => {
    // Only clear when the pointer leaves the dropdown entirely; row→row
    // movement is handled by pointerover above.
    if (dropdown.contains(ev.relatedTarget)) return;
    if (state.get('previewIngredientId') !== null) {
      state.set({ previewIngredientId: null });
    }
  });

  window.addEventListener('resize', positionDropdown);
  window.addEventListener('scroll', positionDropdown, true);

  // Phase 40.4: switching view level changes what "name" means — close
  // any open results so we don't accidentally commit an ingredient id
  // that doesn't resolve in the new dataset.
  state.subscribe(s => s.viewLevel, () => {
    inputEl.value = '';
    close();
  });
  state.subscribe(s => s.categoryGroupBy, () => {
    inputEl.value = '';
    close();
  });

  return { close };
}

function swatchCss(item) {
  if (item.food_group && FOOD_GROUP_COLORS[item.food_group]) {
    const c = FOOD_GROUP_COLORS[item.food_group];
    return `rgb(${Math.round(c[0]*255)}, ${Math.round(c[1]*255)}, ${Math.round(c[2]*255)})`;
  }
  const [a = 0, p = 0, d = 0] = item.group_weights || [];
  return `rgb(${Math.round(a*255)}, ${Math.round(p*255)}, ${Math.round(d*255)})`;
}

function subtitleFor(item) {
  if (item.category === 'Meal') return item.cuisine || 'Meal';
  const parts = [item.food_group, item.category].filter(Boolean);
  return parts.join(' · ');
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
