/**
 * =============================================================================
 * navigation.js — Navigation Controller
 * =============================================================================
 * Manages page-level navigation: URL state, browser history, transition
 * direction detection, and coordinating header + render updates.
 *
 * Dependencies: state.js (AppState), data-store.js (DataStore),
 *               ui-header.js (updateHeaderContext),
 *               ui-render.js (renderMapWithTransition)
 * Consumers: ui-events.js (calls navigate on click), main.js (calls init)
 * =============================================================================
 */

import { AppState, HOME_PAGE_ID } from './state.js';
import { DataStore } from './data-store.js';
import { updateHeaderContext } from './ui-header.js';
import { renderMapWithTransition } from './ui-render.js';
import { clearSearchResults } from './ui-search.js';

/* ---------------------------------------------------------------------------
 * Module-level cache for node index lookups in getDirection()
 * --------------------------------------------------------------------------- */

let nodeIndexCache = null;
let lastNodesLength = 0;

/**
 * Invalidates the cache if DataStore.nodes has changed.
 * Uses array length as a cheap heuristic — if the node count changes,
 * the cache is stale and must be rebuilt.
 */
function invalidateCacheIfNeeded() {
  if (lastNodesLength !== DataStore.nodes.length) {
    nodeIndexCache = null;
    lastNodesLength = DataStore.nodes.length;
  }
}

/**
 * Builds the node index cache on first use.
 * @returns {Map<string, number>} id → index
 */
function getNodeIndexCache() {
  invalidateCacheIfNeeded();
  if (nodeIndexCache === null) {
    nodeIndexCache = new Map();
    DataStore.nodes.forEach((n, idx) => {
      nodeIndexCache.set(n.id, idx);
    });
  }
  return nodeIndexCache;
}

export const NavigationController = {
  init() {
    window.addEventListener('popstate', (e) => {
      const nodeId = e.state?.nodeId;
      this.loadState(nodeId === HOME_PAGE_ID ? HOME_PAGE_ID : nodeId ?? null, 'restore');
    });

    let initialNode = new URLSearchParams(window.location.search).get('node');
    let explicitRoot = false;

    if (initialNode === 'root') {
      // Explicit root (Project Overview) — normalize to null
      initialNode = null;
      explicitRoot = true;
    } else if (initialNode === HOME_PAGE_ID) {
      // Home page URL param (shouldn't normally appear but handle it)
    } else if (initialNode !== null && !DataStore.map.has(initialNode)) {
      console.warn(`Node "${initialNode}" not found. Defaulting to root.`);
      initialNode = null;
    }

    // Default to home page if no node specified and config has a homePage
    if (initialNode === null && !explicitRoot && DataStore.config.homePage) {
      initialNode = HOME_PAGE_ID;
    }

    this.loadState(initialNode, 'replace');
  },

  /**
   * Public navigation entry point.
   * @param {string|null} targetId
   * @param {string|null} explicitDirection — override auto-detected direction
   */
  navigate(targetId, explicitDirection = null) {
    if (AppState.isTransitioning) return;
    this.loadState(targetId, 'push', explicitDirection);
  },

  /**
   * Determines spatial direction for the transition animation.
   * @returns {'depth'|'surface'|'lateral-next'|'lateral-prev'|'none'}
   */
  getDirection(fromId, toId) {
    if (fromId === toId) return 'none';
    // Home page transitions
    if (fromId === HOME_PAGE_ID) return 'depth';
    if (toId === HOME_PAGE_ID) return 'surface';
    if (!fromId && toId) return 'depth';
    if (fromId && !toId) return 'surface';

    const fromNode = DataStore.map.get(fromId);
    const toNode = DataStore.map.get(toId);

    if (toNode?.parentId === fromId) return 'depth';
    if (fromNode?.parentId === toId) return 'surface';

    // Same-parent lateral
    if (fromNode && toNode && fromNode.parentId === toNode.parentId) {
      const cache = getNodeIndexCache();
      const fromIndex = cache.get(fromId) ?? -1;
      const toIndex = cache.get(toId) ?? -1;
      return toIndex > fromIndex ? 'lateral-next' : 'lateral-prev';
    }

    return 'surface';
  },

  /**
   * Core state loader.
   * @param {string|null} nodeId
   * @param {'push'|'replace'|'restore'} historyAction
   * @param {string|null} explicitDirection — if set, overrides getDirection()
   */
  loadState(nodeId, historyAction = 'push', explicitDirection = null) {
    const searchInput = document.getElementById('searchInput');
    if (searchInput?.value) searchInput.value = '';
    clearSearchResults();

    const prevId = AppState.currentParentId;
    const direction = explicitDirection || this.getDirection(prevId, nodeId);

    // Track where we came from (used by sibling-nav for depth preservation)
    AppState.previousParentId = prevId;
    AppState.currentParentId = nodeId;
    AppState.activeNodeId = null;
    document.body.classList.remove('is-focused');

    const url = new URL(window.location);
    if (nodeId === HOME_PAGE_ID) url.searchParams.delete('node');
    else if (nodeId) url.searchParams.set('node', nodeId);
    else {
      // Project overview root: use ?node=root to distinguish from home page
      if (DataStore.config.homePage) url.searchParams.set('node', 'root');
      else url.searchParams.delete('node');
    }

    if (historyAction === 'push') {
      window.history.pushState({ nodeId }, '', url);
    } else if (historyAction === 'replace') {
      window.history.replaceState({ nodeId }, '', url);
    }

    updateHeaderContext();
    renderMapWithTransition(direction);
  }
};
