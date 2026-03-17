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

import { AppState } from './state.js';
import { DataStore } from './data-store.js';
import { updateHeaderContext } from './ui-header.js';
import { renderMapWithTransition } from './ui-render.js';
import { clearSearchResults } from './ui-search.js';

export const NavigationController = {
  init() {
    window.addEventListener('popstate', (e) => {
      this.loadState(e.state?.nodeId ?? null, 'restore');
    });

    let initialNode = new URLSearchParams(window.location.search).get('node');

    if (initialNode !== null && !DataStore.map.has(initialNode)) {
      console.warn(`Node "${initialNode}" not found. Defaulting to root.`);
      initialNode = null;
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
    if (!fromId && toId) return 'depth';
    if (fromId && !toId) return 'surface';

    const fromNode = DataStore.map.get(fromId);
    const toNode = DataStore.map.get(toId);

    if (toNode?.parentId === fromId) return 'depth';
    if (fromNode?.parentId === toId) return 'surface';

    // Same-parent lateral
    if (fromNode && toNode && fromNode.parentId === toNode.parentId) {
      const fromIndex = DataStore.nodes.findIndex(n => n.id === fromId);
      const toIndex = DataStore.nodes.findIndex(n => n.id === toId);
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
    if (nodeId) url.searchParams.set('node', nodeId);
    else url.searchParams.delete('node');

    if (historyAction === 'push') {
      window.history.pushState({ nodeId }, '', url);
    } else if (historyAction === 'replace') {
      window.history.replaceState({ nodeId }, '', url);
    }

    updateHeaderContext();
    renderMapWithTransition(direction);
  }
};
