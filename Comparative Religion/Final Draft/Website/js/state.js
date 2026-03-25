/**
 * =============================================================================
 * state.js — Application State
 * =============================================================================
 * All mutable UI state lives here. Background tints are managed through a
 * single updateTints() method to prevent scattered set/clear patterns.
 *
 * Dependencies: constants.js (THEME_TRANSITION_MS)
 * Consumers: main.js, navigation.js, ui-render.js, ui-expander.js,
 *            ui-header.js, ui-search.js, ui-events.js, svg-engine.js
 *
 * DESIGN NOTE: AppState does NOT import any UI modules. The theme toggle
 * button text is updated via a callback (onThemeChanged) set during init,
 * breaking the circular dependency that existed in the original monolith.
 * =============================================================================
 */

import { THEME_TRANSITION_MS, TINT_SATURATION, TINT_LIGHTNESS, TINT_ALPHA } from './constants.js';

/** Sentinel value for the home landing page (distinct from null = project overview root). */
export const HOME_PAGE_ID = '__home__';

export const AppState = {
  theme: localStorage.getItem('theme') || 'dark',
  activeNodeId: null,
  currentParentId: null,
  previousParentId: null,   // tracks where we navigated from (for depth preservation)
  isTransitioning: false,
  isStackTransitioning: false,
  _themeTransitionTimeout: null,   // tracks pending theme-transition class removal

  searchConfig: {
    nodeContents: true,
    global: true,
    nested: false
  },

  /**
   * Optional callback invoked after theme changes.
   * Set by ui-events.js during init to update the toggle button text.
   * Signature: (newTheme: 'light' | 'dark') => void
   */
  onThemeChanged: null,

  /* ------------------------------------------------------------------
   * Theme management
   * ------------------------------------------------------------------ */
  toggleTheme() {
    document.body.classList.add('theme-transition');
    this.theme = this.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', this.theme);
    this.applyTheme();
    // Clear any pending removal timeout before scheduling a new one so rapid
    // clicks don't strip the class while the most recent transition is still running.
    clearTimeout(this._themeTransitionTimeout);
    this._themeTransitionTimeout = setTimeout(
      () => document.body.classList.remove('theme-transition'),
      THEME_TRANSITION_MS
    );
  },

  applyTheme() {
    document.documentElement.setAttribute('data-theme', this.theme);
    if (this.onThemeChanged) {
      this.onThemeChanged(this.theme);
    }
  },

  /* ------------------------------------------------------------------
   * Background tint management (centralized)
   *
   * Two CSS custom properties drive the background gradients:
   *   --bg-tint       (left side)  – reflects the current page's hue
   *   --bg-tint-right (right side) – reflects the active expander's hue
   *
   * Call updateTints() whenever page context or expander state changes.
   * Pass only the properties that are changing; omitted keys stay as-is.
   *
   * Examples:
   *   AppState.updateTints({ page: 'transparent', expander: 'transparent' });
   *   AppState.updateTints({ expander: `hsla(${hue}, ${TINT_SATURATION}%, ${TINT_LIGHTNESS}%, ${TINT_ALPHA})` });
   * ------------------------------------------------------------------ */
  updateTints({ page, expander } = {}) {
    const style = document.body.style;
    if (page !== undefined)     style.setProperty('--bg-tint', page);
    if (expander !== undefined) style.setProperty('--bg-tint-right', expander);
  }
};
