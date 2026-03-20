/**
 * =============================================================================
 * ui-export.js — JSON Export
 * =============================================================================
 * Exports the currently visible nodes (or search results) as a JSON file
 * in the same format as the original data.json.
 *
 * Uses the File System Access API (showSaveFilePicker) when available to
 * present a native save-as dialog. Falls back to a Blob + <a download>
 * approach for browsers that don't support it.
 *
 * Dependencies: data-store.js (DataStore), state.js (AppState),
 *               graph-engine.js (computeLevels)
 * Consumers: ui-events.js (binds the export button click)
 * =============================================================================
 */

import { FILENAME_MAX_LENGTH } from './constants.js';
import { DataStore } from './data-store.js';
import { AppState } from './state.js';
import { computeLevels } from './graph-engine.js';

/**
 * Gathers the relevant nodes and triggers a JSON file download.
 *
 * Normal view (no search active): exports all nodes whose parentId matches
 * the current page's parent, ordered by DAG layout (top row first, left to
 * right within each row).
 *
 * Search results view: exports all nodes currently shown in search results,
 * in the order they appear on screen (grouped by parent page).
 */
export async function exportNodes() {
  const isSearchActive = hasActiveSearch();

  let orderedNodes;
  let filename;
  let config;

  if (isSearchActive) {
    orderedNodes = collectSearchResultNodes();
    filename = buildSearchFilename();
    config = buildSearchConfig();
  } else {
    orderedNodes = collectPageNodes();
    filename = buildPageFilename();
    config = { ...DataStore.config };
  }

  // Build the export payload in the same shape as data.json
  const payload = {
    config,
    nodes: orderedNodes.map(stripInternalFields)
  };

  const jsonStr = JSON.stringify(payload, null, 2);

  // Try native save-as dialog first, fall back to anchor download
  if (window.showSaveFilePicker) {
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: filename,
        types: [{
          description: 'JSON file',
          accept: { 'application/json': ['.json'] }
        }]
      });
      const writable = await handle.createWritable();
      await writable.write(jsonStr);
      await writable.close();
      return;
    } catch (err) {
      // User cancelled the dialog — not an error
      if (err.name === 'AbortError') return;
      // Fall through to anchor fallback for other errors
      console.warn('[Export] showSaveFilePicker failed, using fallback:', err);
    }
  }

  // Fallback: Blob + temporary anchor
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();

  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

/* ---------------------------------------------------------------------------
 * Helpers
 * --------------------------------------------------------------------------- */

/** Returns true when a non-empty search query is active and results are shown. */
function hasActiveSearch() {
  const input = document.getElementById('searchInput');
  if (!input || !input.value.trim()) return false;
  const container = document.getElementById('mapContainer');
  return !!container?.querySelector('.search-results-wrap');
}

/**
 * Collects nodes for the current page in DAG layout order:
 * top row first, left to right within each row, skipping dummy spacers.
 */
function collectPageNodes() {
  const visibleNodes = DataStore.nodes.filter(
    n => n.parentId === AppState.currentParentId
  );

  if (visibleNodes.length === 0) return [];

  const rows = computeLevels(visibleNodes);
  const ordered = [];
  for (const row of rows) {
    for (const item of row) {
      if (!item.isDummy) {
        ordered.push(item);
      }
    }
  }
  return ordered;
}

/**
 * Collects nodes from the rendered search results in DOM order.
 * Walks .node-row elements inside the search-results-wrap.
 */
function collectSearchResultNodes() {
  const container = document.getElementById('mapContainer');
  if (!container) return [];

  const wrap = container.querySelector('.search-results-wrap');
  if (!wrap) return [];

  const nodes = [];
  const rows = wrap.querySelectorAll('.node-row[data-id]');
  rows.forEach(row => {
    const node = DataStore.map.get(row.dataset.id);
    if (node) nodes.push(node);
  });
  return nodes;
}

/**
 * Builds the config block for search result exports.
 * Replaces the page-specific config with search-specific metadata.
 */
function buildSearchConfig() {
  const input = document.getElementById('searchInput');
  const query = input?.value?.trim() || '';

  // Read active filter states from the DOM checkboxes
  const nodeContentsSearch = document.getElementById('toggleNodeContentsSearch')?.checked ?? true;
  const globalSearch = document.getElementById('toggleGlobalSearch')?.checked ?? true;
  const nestedSearch = document.getElementById('toggleNestedSearch')?.checked ?? false;

  // Determine search scope description
  let scope;
  if (nestedSearch) {
    const parentNode = AppState.currentParentId
      ? DataStore.map.get(AppState.currentParentId)
      : null;
    scope = parentNode
      ? `Current page only (${parentNode.id} — ${parentNode.claim})`
      : 'Current page only (root)';
  } else if (globalSearch) {
    scope = 'All pages';
  } else {
    scope = 'Current page';
  }

  return {
    exportType: 'search-results',
    searchQuery: query,
    searchScope: scope,
    searchNodeContents: nodeContentsSearch,
    resultCount: collectSearchResultNodes().length,
    sourceTitle: DataStore.config.title || 'Map'
  };
}

/**
 * Builds a filename for page exports.
 * Root page → "root-nodes.json", sub-page → "page-{id}-nodes.json".
 */
function buildPageFilename() {
  if (!AppState.currentParentId) return 'root-nodes.json';
  return `page-${AppState.currentParentId}-nodes.json`;
}

/**
 * Builds a filename for search result exports.
 * Includes the search term (sanitized) if short enough.
 */
function buildSearchFilename() {
  const input = document.getElementById('searchInput');
  const raw = input?.value?.trim() || '';

  if (raw.length === 0 || raw.length > FILENAME_MAX_LENGTH) return 'search-results.json';

  const safe = raw
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

  return safe ? `search-${safe}-nodes.json` : 'search-results.json';
}

/**
 * Returns a clean copy of a node with internal/computed fields stripped.
 * The exported JSON should match the original data.json format — no
 * runtime caches (.color, .hue, ._searchBase, ._searchFull).
 */
function stripInternalFields(node) {
  const clean = {};
  for (const key of Object.keys(node)) {
    if (key === 'color' || key === 'hue' || key.startsWith('_')) continue;
    clean[key] = node[key];
  }
  return clean;
}
