/**
 * =============================================================================
 * ui-events.js — Event Binding
 * =============================================================================
 * Single module for all event listeners. Uses event delegation where possible
 * to minimize listener count.
 *
 * Dependencies: state.js (AppState), navigation.js (NavigationController),
 *               ui-expander.js (toggleExpander)
 * Consumers: main.js (calls init once during bootstrap)
 * =============================================================================
 */

import { AppState } from './state.js';
import { NavigationController } from './navigation.js';
import { toggleExpander } from './ui-expander.js';

/** Cached DOM elements. Populated by init(). */
const els = {};

/**
 * Caches DOM references and binds all event listeners.
 * Call once during bootstrap, after data is loaded.
 */
export function init() {
  els.container      = document.getElementById('mapContainer');
  els.pageHeader     = document.getElementById('pageHeader');
  els.headerToggle   = document.getElementById('headerToggle');
  els.chevronToggle  = document.getElementById('chevronToggle');
  els.themeToggle    = document.getElementById('themeToggle');

  bindThemeToggle();
  bindHeaderToggles();
  bindMapClicks();
  bindBreadcrumbClicks();
  bindEscapeKey();
}

/* ---------------------------------------------------------------------------
 * Theme toggle
 * --------------------------------------------------------------------------- */
function bindThemeToggle() {
  if (!els.themeToggle) return;

  // Wire the callback so AppState can update button text without importing UI
  AppState.onThemeChanged = (newTheme) => {
    const isLight = newTheme === 'light';
    els.themeToggle.textContent = isLight ? '☀️ Light' : '🌙 Dark';
    els.themeToggle.setAttribute(
      'aria-label',
      `Switch to ${isLight ? 'dark' : 'light'} mode`
    );
  };
  // Sync button text with current theme
  AppState.onThemeChanged(AppState.theme);

  els.themeToggle.addEventListener('click', () => AppState.toggleTheme());
}

/* ---------------------------------------------------------------------------
 * Header collapse toggles (desktop chevron + mobile hamburger)
 * --------------------------------------------------------------------------- */
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

/* ---------------------------------------------------------------------------
 * Delegated map container click handler
 *
 * Single listener on #mapContainer handles all interactive elements.
 * Priority order: trigger-derive → search-result-header → node-header
 *                 → logic-header → mini-trigger
 * --------------------------------------------------------------------------- */
function bindMapClicks() {
  els.container?.addEventListener('click', (e) => {
    // Navigation: derive buttons, sibling nav, badge pills
    const deriveBtn = e.target.closest('.trigger-derive');
    if (deriveBtn) {
      const targetId = deriveBtn.dataset.target === 'null'
        ? null
        : deriveBtn.dataset.target;
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

/* ---------------------------------------------------------------------------
 * Escape key: closes active expander
 * --------------------------------------------------------------------------- */
function bindEscapeKey() {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && AppState.activeNodeId !== null) {
      toggleExpander(AppState.activeNodeId);
    }
  });
}

/* ---------------------------------------------------------------------------
 * Breadcrumb click delegation (outside the map container)
 * --------------------------------------------------------------------------- */
function bindBreadcrumbClicks() {
  document.addEventListener('click', (e) => {
    const crumb = e.target.closest('.crumb-link');
    if (crumb) {
      e.preventDefault();
      NavigationController.navigate(
        crumb.dataset.target === 'null' ? null : crumb.dataset.target
      );
    }
  });
}
