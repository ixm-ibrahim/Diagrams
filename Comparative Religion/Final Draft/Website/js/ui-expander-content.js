/* === ui-expander-content.js — Tab Rendering & Scroll Helpers ===
 * Dependencies: templates.js (tabContent),
 *               ui-search.js (getActiveSearchQuery, highlightMatches)
 * Consumers: ui-expander.js (calls bindTabEvents, scrollToView)
 * ============================================================= */

import { tabContent } from './templates.js';

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
 * Scrolls the row into view so the card sits just below the sticky header
 * and the expander content is fully visible (not hidden under the card).
 * Uses a delayed scroll to avoid mid-animation jerking.
 *
 * @param {HTMLElement} el — the element to scroll into view
 */
export function scrollToView(el, { instant = false } = {}) {
  // Use a single RAF so we read geometry after the DOM changes from
  // open/close have been applied, but scroll starts immediately —
  // overlapping with the expander's open animation for a fluid feel.
  //
  // In accordion mode (instant=true), use instant scroll to avoid a
  // race between smooth-scroll and the expanding content that causes
  // the row's sticky translateY to overshoot, placing the expander
  // visually behind the card.
  requestAnimationFrame(() => {
    const rect = el.getBoundingClientRect();
    const headerHeight = document.getElementById('pageHeader')?.offsetHeight ?? 0;
    const stickyTop = headerHeight + 12 + 8; // header sticky offset (12px) + gap (8px)

    // Scroll so the row top sits just below the header.
    const targetScrollY = window.scrollY + rect.top - stickyTop + 4;

    // Scroll if the row isn't already properly positioned
    if (Math.abs(rect.top - stickyTop) > 2 || rect.bottom > window.innerHeight) {
      window.scrollTo({
        top: targetScrollY,
        behavior: instant ? 'instant' : 'smooth'
      });
    }
  });
}
