/* === ui-expander-content.js — Tab Rendering & Scroll Helpers ===
 * Dependencies: templates.js (tabContent),
 *               constants.js (ANIMATION_SPEEDS),
 *               ui-search.js (getActiveSearchQuery, highlightMatches)
 * Consumers: ui-expander.js (calls bindTabEvents, scrollToView)
 * ============================================================= */

import { tabContent } from './templates.js';
import { ANIMATION_SPEEDS } from './constants.js';
import { getActiveSearchQuery, highlightMatches } from './ui-search.js';

/**
 * Binds tab button click handlers and renders the first tab.
 *
 * @param {HTMLElement} expander — the expander container
 * @param {Object} nodeData — the node data object with sections
 */
export function bindTabEvents(expander, nodeData) {
  const tabBtns = expander.querySelectorAll('.btn-tab');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.setAttribute('aria-selected', b === btn));
      renderTabPanel(nodeData, btn.dataset.key);
    });
  });
  // Render the first tab's content
  if (tabBtns.length > 0) renderTabPanel(nodeData, tabBtns[0].dataset.key);
}

/**
 * Renders the tab panel content for the given tab key.
 * Updates the panel HTML and highlights search matches if in search mode.
 *
 * @param {Object} nodeData — the node data object with sections
 * @param {string} key — the tab key to render
 */
function renderTabPanel(nodeData, key) {
  const panel = document.getElementById(`panel-${nodeData.id}`);
  if (!panel) return;
  const section = (nodeData.sections || []).find(
    s => s.type === 'tab' && s.title === key
  );
  panel.innerHTML = tabContent(section?.items || [], section?.numbered || false);

  // Highlight search matches in the newly rendered tab panel
  const searchQuery = getActiveSearchQuery();
  if (searchQuery) highlightMatches(panel, searchQuery);
}

/**
 * Scrolls the row into view if it's below the viewport bottom.
 * Uses a delayed scroll to avoid mid-animation jerking.
 *
 * @param {HTMLElement} el — the element to scroll into view
 */
export function scrollToView(el) {
  setTimeout(() => {
    const rect = el.getBoundingClientRect();
    if (rect.bottom > window.innerHeight) {
      const headerHeight = document.getElementById('pageHeader')?.offsetHeight ?? 0;
      window.scrollTo({
        top: window.scrollY + rect.top - headerHeight - 24,
        behavior: 'smooth'
      });
    }
  }, ANIMATION_SPEEDS.SCROLL_DELAY_MS);
}
