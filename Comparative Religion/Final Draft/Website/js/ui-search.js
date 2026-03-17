/**
 * =============================================================================
 * ui-search.js — Search System
 * =============================================================================
 * Handles debounced text input, node matching, and result rendering.
 * Search results replace the map view inside #mapContainer by hiding the
 * existing .map-flow (preserving its state) and appending result elements.
 *
 * Results render real node cards (via Templates.nodeRow) so they look exactly
 * like the nodes on a regular map page — same colors, badges, etc.
 *
 * Dependencies: constants.js (SEARCH_DEBOUNCE_MS),
 *               data-store.js (DataStore), state.js (AppState),
 *               templates.js (nodeRow)
 * Consumers: ui-events.js (calls debouncedSearch on input)
 * =============================================================================
 */

import { SEARCH_DEBOUNCE_MS } from './constants.js';
import { DataStore } from './data-store.js';
import { AppState } from './state.js';
import { nodeRow } from './templates.js';
import { forceCloseExpander } from './ui-expander.js';

/** Debounce timer ID. */
let searchTimeout = null;

/** Maximum results to render (prevents DOM explosion on short queries). */
const MAX_RESULTS = 100;

/**
 * Debounced search entry point. Call on every input event.
 * Waits SEARCH_DEBOUNCE_MS after the last keystroke before executing.
 *
 * @param {string} rawQuery — the raw input value
 */
export function debouncedSearch(rawQuery) {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => handleSearch(rawQuery), SEARCH_DEBOUNCE_MS);
}

/**
 * Core search handler. Matches nodes against query, renders results as
 * a flat list of real node cards.
 *
 * @param {string} rawQuery
 */
function handleSearch(rawQuery) {
  const query = rawQuery.toLowerCase().trim();
  const container = document.getElementById('mapContainer');
  if (!container) return;

  // Close any open expander before rebuilding results
  forceCloseExpander();

  // Empty query → clear results and restore map
  if (query.length === 0) {
    clearSearchResults();
    return;
  }

  // Determine search pool based on scope setting.
  // Global = all nodes. Otherwise (nested checked, or neither checked) =
  // only nodes whose parentId matches the current page.
  let searchPool;
  if (AppState.searchConfig.global) {
    searchPool = DataStore.nodes;
  } else {
    searchPool = DataStore.nodes.filter(
      node => node.parentId === AppState.currentParentId
    );
  }

  // Match against node fields.
  // Searchable text is cached on the node to avoid recomputing on every
  // keystroke.  Two caches: _searchBase (claim/soWhat/search) and
  // _searchFull (base + section contents).
  const matches = [];
  const searchNodeContents = AppState.searchConfig.nodeContents;

  for (let i = 0; i < searchPool.length; i++) {
    const node = searchPool[i];

    // Build / retrieve cached base text
    if (node._searchBase === undefined) {
      node._searchBase = `${node.claim || ''} ${node.soWhat || ''} ${node.search || ''}`.toLowerCase();
    }

    let text = node._searchBase;

    if (searchNodeContents && node.sections) {
      if (node._searchFull === undefined) {
        node._searchFull = (node._searchBase + ' ' +
          node.sections.map(sec =>
            `${sec.title || ''} ${getDeepText(sec.items)}`
          ).join(' ')
        ).toLowerCase();
      }
      text = node._searchFull;
    }

    if (text.includes(query)) {
      matches.push(node);
      if (matches.length >= MAX_RESULTS) break;
    }
  }

  // Hide existing map-flow (don't destroy — preserves state)
  const mapFlow = container.querySelector('.map-flow');
  if (mapFlow) mapFlow.style.display = 'none';

  // Remove any previous search results
  container.querySelectorAll('.search-results-wrap, .search-no-results').forEach(
    el => el.remove()
  );

  // No results
  if (matches.length === 0) {
    const noResults = document.createElement('div');
    noResults.className = 'search-no-results';
    noResults.textContent = 'No results found.';
    container.appendChild(noResults);
    return;
  }

  // Group matches by parentId
  const grouped = new Map();
  matches.forEach(node => {
    const pid = node.parentId;
    if (!grouped.has(pid)) grouped.set(pid, []);
    grouped.get(pid).push(node);
  });

  // Build grouped results
  const wrap = document.createElement('div');
  wrap.className = 'search-results-wrap';

  grouped.forEach((nodes, parentId) => {
    const parentNode = parentId ? DataStore.map.get(parentId) : null;
    const pageTitle = parentNode
      ? `${parentNode.id} — ${parentNode.claim}`
      : (DataStore.config.breadcrumbRoot || 'Root');

    const groupEl = document.createElement('div');
    groupEl.className = 'search-result-box';

    // Header (clickable to collapse — handled by bindMapClicks in ui-events.js)
    const header = document.createElement('div');
    header.className = 'search-result-header';
    header.setAttribute('role', 'button');
    header.setAttribute('aria-expanded', 'true');
    header.innerHTML = `<span class="search-result-title"><b>${escapeHTML(pageTitle)}</b></span>`;
    highlightMatches(header, query);
    groupEl.appendChild(header);

    // Content: a .map-flow with one level-group per node
    const content = document.createElement('div');
    content.className = 'search-result-content map-flow';

    nodes.forEach(node => {
      const levelGroup = document.createElement('div');
      levelGroup.className = 'level-group';

      const row = document.createElement('div');
      row.className = 'node-row';
      row.dataset.id = node.id;
      row.innerHTML = nodeRow(node);
      highlightMatches(row, query);

      const expanderEl = document.createElement('div');
      expanderEl.className = 'level-expander';

      levelGroup.appendChild(row);
      levelGroup.appendChild(expanderEl);
      content.appendChild(levelGroup);
    });

    groupEl.appendChild(content);
    wrap.appendChild(groupEl);
  });

  // If we hit the cap, show a notice so the user knows to refine their query
  if (matches.length >= MAX_RESULTS) {
    const notice = document.createElement('div');
    notice.className = 'search-no-results';
    notice.textContent = `Showing first ${MAX_RESULTS} results. Refine your search to see more.`;
    wrap.appendChild(notice);
  }

  container.appendChild(wrap);
}

/**
 * Removes all search result elements and restores the map-flow visibility.
 * Called when the search input is cleared.
 */
export function clearSearchResults() {
  forceCloseExpander();

  const container = document.getElementById('mapContainer');
  if (!container) return;

  container.querySelectorAll('.search-results-wrap, .search-no-results').forEach(
    el => el.remove()
  );

  const mapFlow = container.querySelector('.map-flow');
  if (mapFlow) mapFlow.style.display = '';
}

/**
 * Immediately re-runs the current search (if any).
 * Called by ui-events.js when a filter checkbox changes while a search is active.
 */
export function rerunActiveSearch() {
  const input = document.getElementById('searchInput');
  if (input?.value) {
    handleSearch(input.value);
  }
}

/* ---------------------------------------------------------------------------
 * Internal helpers
 * --------------------------------------------------------------------------- */

/** Minimal HTML escape to prevent XSS in dynamically generated content. */
function escapeHTML(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Returns the current active search query (lowercase, trimmed), or empty
 * string if no search is active. Used by ui-expander.js to highlight
 * matches inside expanded content.
 */
export function getActiveSearchQuery() {
  const input = document.getElementById('searchInput');
  return input?.value?.toLowerCase().trim() || '';
}

/**
 * Walks all text nodes inside `el` and wraps occurrences of `query` in
 * <mark class="search-highlight">. Operates on the live DOM so it's safe —
 * it never touches tag names or attributes.
 *
 * @param {HTMLElement} el     — container to walk
 * @param {string}      query  — lowercase search string
 */
export function highlightMatches(el, query) {
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null);
  const nodesToSplit = [];

  // Phase 1: collect matches (can't mutate DOM while walking)
  while (walker.nextNode()) {
    const textNode = walker.currentNode;
    const idx = textNode.nodeValue.toLowerCase().indexOf(query);
    if (idx !== -1) {
      nodesToSplit.push({ node: textNode, index: idx, length: query.length });
    }
  }

  // Phase 2: wrap each match
  for (let i = nodesToSplit.length - 1; i >= 0; i--) {
    const { node, index, length } = nodesToSplit[i];
    const after = node.splitText(index + length);
    const matchText = node.splitText(index);
    const mark = document.createElement('mark');
    mark.className = 'search-highlight';
    mark.appendChild(matchText.cloneNode(true));
    matchText.parentNode.replaceChild(mark, matchText);
    // `after` stays in place automatically
  }
}

/** Recursively flattens section items into searchable text. */
function getDeepText(items) {
  if (!items) return '';
  return items.map(item => {
    if (typeof item === 'string') return item;
    let text = `${item.title || ''} ${item.detail || ''}`;
    if (item.subSections) {
      text += ' ' + item.subSections.map(sub =>
        `${sub.label || ''} ${getDeepText(sub.items)}`
      ).join(' ');
    }
    if (item.children) text += ' ' + getDeepText(item.children);
    return text;
  }).join(' ');
}
