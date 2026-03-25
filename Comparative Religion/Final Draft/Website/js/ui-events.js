/* === ui-events.js — Event Binding === */
/**
 * Single module for all event listeners. Uses event delegation where possible.
 *
 * Dependencies: state.js, navigation.js, ui-expander.js, ui-search.js,
 *               ui-export.js, ui-agreement.js
 * Consumers:    main.js (calls init once during bootstrap)
 */

import { AppState, HOME_PAGE_ID } from './state.js';
import { DataStore } from './data-store.js';
import { NavigationController } from './navigation.js';
import { SCROLL_TO_NODE_DELAY_MS, SCROLL_PADDING_PX } from './constants.js';
import { toggleExpander } from './ui-expander.js';
import { debouncedSearch, rerunActiveSearch } from './ui-search.js';
import { exportNodes } from './ui-export.js';
import { setVote, applyVoteStates } from './ui-agreement.js';

/** Cached DOM elements. Populated by init(). */
const els = {};

/**
 * Caches DOM references and binds all event listeners.
 * Call once during bootstrap, after data is loaded.
 */
export function init() {
  els.container        = document.getElementById('mapContainer');
  els.pageHeader       = document.getElementById('pageHeader');
  els.headerToggle     = document.getElementById('headerToggle');
  els.chevronToggle    = document.getElementById('chevronToggle');
  els.themeToggle      = document.getElementById('themeToggle');
  els.searchInput        = document.getElementById('searchInput');
  els.searchFilterBtn    = document.getElementById('searchFilterBtn');
  els.searchFilterMenu   = document.getElementById('searchFilterMenu');
  els.toggleNodeContentsSearch   = document.getElementById('toggleNodeContentsSearch');
  els.toggleGlobalSearch = document.getElementById('toggleGlobalSearch');
  els.toggleNestedSearch = document.getElementById('toggleNestedSearch');
  els.exportBtn          = document.getElementById('exportBtn');

  bindThemeToggle();
  bindHeaderToggles();
  bindMapClicks();
  bindBreadcrumbClicks();
  bindEscapeKey();
  bindKeyboardActivation();
  bindSearchInput();
  bindSearchFilter();
  bindSearchCheckboxes();
  bindExportButton();
}

function bindThemeToggle() {
  if (!els.themeToggle) return;

  els.themeIcon  = document.getElementById('themeIcon');
  els.themeLabel = document.getElementById('themeLabel');

  // Wire the callback so AppState can update button text without importing UI
  AppState.onThemeChanged = (newTheme) => {
    const isLight = newTheme === 'light';
    if (els.themeIcon)  els.themeIcon.textContent  = isLight ? '☀️' : '🌙';
    if (els.themeLabel) els.themeLabel.textContent  = isLight ? 'Light' : 'Dark';
    els.themeToggle.setAttribute(
      'aria-label',
      `Switch to ${isLight ? 'dark' : 'light'} mode`
    );
  };
  // Sync button text with current theme
  AppState.onThemeChanged(AppState.theme);

  els.themeToggle.addEventListener('click', () => AppState.toggleTheme());
}

function bindHeaderToggles() {
  // Mobile hamburger menu
  els.headerToggle?.addEventListener('click', () => {
    const isExpanded = els.pageHeader.classList.toggle('is-expanded');
    els.headerToggle.setAttribute('aria-expanded', isExpanded);
  });

  // Desktop chevron collapse
  els.chevronToggle?.addEventListener('click', () => {
    const isCollapsed = els.pageHeader.classList.toggle('is-desktop-collapsed');
    els.chevronToggle.setAttribute('aria-expanded', !isCollapsed);
    els.chevronToggle.setAttribute(
      'aria-label',
      isCollapsed ? 'Expand Header' : 'Collapse Header'
    );
  });
}

/** Delegated click handler on #mapContainer for all interactive elements. */
function bindMapClicks() {
  els.container?.addEventListener('click', (e) => {
    // Links inside card text: let them navigate normally.
    if (e.target.closest('a[href]')) return;

    // Vote buttons: compact icon buttons on non-terminal cards (.btn-vote)
    // and full-sized buttons in terminal node expanders (.btn-action[data-vote])
    const voteBtn = e.target.closest('.btn-vote, .btn-action[data-vote]');
    if (voteBtn) {
      e.stopPropagation(); // prevent bubbling to node-header
      // Guard: ignore vote clicks during page transitions (half-rendered state)
      if (AppState.isTransitioning) return;
      const nodeId    = voteBtn.dataset.nodeId;
      const vote      = voteBtn.dataset.vote;   // 'agree' or 'disagree'
      const isPressed = voteBtn.getAttribute('aria-pressed') === 'true';
      const isAuto    = voteBtn.classList.contains('is-auto');

      if (isPressed && !isAuto) {
        // Explicitly selected → toggle off (remove the explicit vote;
        // node may revert to auto-selected from propagation)
        setVote(nodeId, null);
      } else {
        // Not selected, or auto-selected from propagation →
        // create / upgrade to an explicit vote
        setVote(nodeId, vote);
      }

      // Recompute propagation already ran inside setVote();
      // now sync every visible button on the page at once
      applyVoteStates(els.container);

      return;
    }

    // Navigation: derive buttons, sibling nav, badge pills
    const deriveBtn = e.target.closest('.trigger-derive');
    if (deriveBtn) {
      const targetId = deriveBtn.dataset.target === 'null'
        ? null
        : deriveBtn.dataset.target;
      // Guard: if target node doesn't exist in the data, log and bail
      if (targetId != null && !DataStore.map.has(targetId)) {
        console.warn(`[derive] Target node "${targetId}" not found in DataStore. Ignoring click.`);
        return;
      }
      const direction = deriveBtn.dataset.direction || null;
      NavigationController.navigate(targetId, direction);
      return;
    }

    // Search result header: toggle collapse (Phase 6)
    const searchHeader = e.target.closest('.search-result-header');
    if (searchHeader) {
      const box = searchHeader.closest('.search-result-box');
      const collapsed = box.classList.toggle('is-collapsed');
      searchHeader.setAttribute('aria-expanded', !collapsed);
      return;
    }

    // Node card header: toggle expander
    const nodeHeader = e.target.closest('.node-header');
    if (nodeHeader) {
      // Guard: ignore expander clicks during page transitions (view is half-rendered)
      if (AppState.isTransitioning) return;
      const card = nodeHeader.closest('.node-card');
      if (card) toggleExpander(card.dataset.id);
      return;
    }

    // Logic section header: toggle collapse
    const logicHeader = e.target.closest('.logic-header');
    if (logicHeader) {
      const section = logicHeader.closest('.logic-section');
      const collapsed = section.classList.toggle('is-collapsed');
      logicHeader.setAttribute('aria-expanded', !collapsed);
      return;
    }

    // Mini-node trigger: toggle open/close
    const miniTrigger = e.target.closest('.mini-trigger');
    if (miniTrigger) {
      const miniNode = miniTrigger.closest('.mini-node');
      const isOpen = miniNode.classList.toggle('is-open');
      miniTrigger.setAttribute('aria-expanded', isOpen);
    }
  });
}

function bindEscapeKey() {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && AppState.activeNodeId !== null) {
      toggleExpander(AppState.activeNodeId);
    }
  });
}

/**
 * Keyboard activation for role="button" elements that are divs (not <button>).
 * Fires their click handler on Enter or Space, matching the ARIA button pattern.
 * Defensive: browsers fire click for Enter on role="button" natively, but
 * Space requires an explicit handler in some environments.
 */
function bindKeyboardActivation() {
  els.container?.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;

    // Node header: toggle expander
    const nodeHeader = e.target.closest('.node-header[role="button"]');
    if (nodeHeader) {
      e.preventDefault(); // prevent Space from scrolling the page
      nodeHeader.click();
      return;
    }

    // Logic section header: toggle collapse
    const logicHeader = e.target.closest('.logic-header[role="button"]');
    if (logicHeader) {
      e.preventDefault();
      logicHeader.click();
    }
  });
}

function bindSearchInput() {
  els.searchInput?.addEventListener('input', (e) => {
    debouncedSearch(e.target.value);
  });
}

function bindSearchFilter() {
  // Button toggles dropdown open/closed
  els.searchFilterBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = els.searchFilterMenu.classList.toggle('is-open');
    els.searchFilterBtn.setAttribute('aria-expanded', isOpen);
  });

  // Click anywhere outside the dropdown closes it
  document.addEventListener('click', (e) => {
    if (
      els.searchFilterMenu?.classList.contains('is-open') &&
      !e.target.closest('.search-input-wrap')
    ) {
      els.searchFilterMenu.classList.remove('is-open');
      els.searchFilterBtn.setAttribute('aria-expanded', 'false');
    }
  });
}

/** Global ↔ Nested are mutually exclusive; Node Contents is independent. */
function bindSearchCheckboxes() {
  /** Reads all three checkboxes and pushes their state into AppState. */
  const syncConfig = () => {
    AppState.searchConfig.nodeContents = els.toggleNodeContentsSearch?.checked  ?? true;
    AppState.searchConfig.global = els.toggleGlobalSearch?.checked ?? true;
    AppState.searchConfig.nested = els.toggleNestedSearch?.checked ?? false;
    rerunActiveSearch();
  };

  // "Search node contents" — independent, just sync state
  els.toggleNodeContentsSearch?.addEventListener('change', syncConfig);

  // "Search all pages (Global)" — unchecks nested when checked
  els.toggleGlobalSearch?.addEventListener('change', (e) => {
    if (e.target.checked && els.toggleNestedSearch) {
      els.toggleNestedSearch.checked = false;
    }
    syncConfig();
  });

  // "Search only current page" — unchecks global when checked
  els.toggleNestedSearch?.addEventListener('change', (e) => {
    if (e.target.checked && els.toggleGlobalSearch) {
      els.toggleGlobalSearch.checked = false;
    }
    syncConfig();
  });
}

function bindExportButton() {
  els.exportBtn?.addEventListener('click', () => exportNodes());
}

function bindBreadcrumbClicks() {
  // Custom navigate-to events dispatched from home page buttons
  document.addEventListener('navigate-to', (e) => {
    NavigationController.navigate(e.detail.target);
  });

  document.addEventListener('click', (e) => {
    const crumb = e.target.closest('.crumb-link');
    if (crumb) {
      e.preventDefault();
      const target = crumb.dataset.target;
      if (target === HOME_PAGE_ID) {
        NavigationController.navigate(HOME_PAGE_ID);
      } else {
        NavigationController.navigate(target === 'null' ? null : target);
      }
      return;
    }

    // Vote summary panel links: navigate to the node's page, then scroll
    // to the specific node. If already on that page, just scroll.
    const voteLink = e.target.closest('.vote-link');
    if (voteLink) {
      e.preventDefault();
      const targetPage = voteLink.dataset.target === 'null' ? null : voteLink.dataset.target;
      const nodeId     = voteLink.dataset.nodeId;
      const alreadyOnPage = AppState.currentParentId === targetPage;

      if (alreadyOnPage) {
        // Just scroll to the node
        scrollToNode(nodeId);
      } else {
        // Navigate, then scroll after the transition settles
        NavigationController.navigate(targetPage);
        setTimeout(() => scrollToNode(nodeId), SCROLL_TO_NODE_DELAY_MS);
      }
    }
  });
}

/** Scroll a node card into view by its ID. */
function scrollToNode(nodeId) {
  const card = document.querySelector(`.node-card[data-id="${nodeId}"]`);
  if (!card) return;
  const headerHeight = document.getElementById('pageHeader')?.offsetHeight ?? 0;
  const summaryHeight = document.getElementById('voteSummary')?.offsetHeight ?? 0;
  const rect = card.getBoundingClientRect();
  const offset = headerHeight + summaryHeight + SCROLL_PADDING_PX;
  if (rect.top < offset || rect.bottom > window.innerHeight) {
    window.scrollTo({
      top: window.scrollY + rect.top - offset,
      behavior: 'smooth'
    });
  }
}

