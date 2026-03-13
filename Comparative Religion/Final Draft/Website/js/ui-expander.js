/**
 * =============================================================================
 * ui-expander.js — Expander Panel Management
 * =============================================================================
 * Manages the inline detail panel that opens below a node card.
 * Only one expander can be open at a time across the entire page.
 *
 * Dependencies: data-store.js (DataStore), state.js (AppState),
 *               templates.js (expander, tabContent),
 *               constants.js (ANIMATION_SPEEDS)
 * Consumers: ui-events.js (calls toggleExpander on click)
 * =============================================================================
 */

import { DataStore } from './data-store.js';
import { AppState } from './state.js';
import { expander as expanderTemplate, tabContent } from './templates.js';
import { ANIMATION_SPEEDS } from './constants.js';

/**
 * Toggles the expander for the given node ID.
 * If already open, closes it. If another is open, closes that first.
 *
 * @param {string} id — node ID
 */
export function toggleExpander(id) {
  const row = document.querySelector(`.node-row[data-id="${id}"]`);
  if (!row) return;

  const levelGroup = row.closest('.level-group');
  const expander = levelGroup.querySelector('.level-expander');
  const headerBtn = row.querySelector('.node-header');
  const inlineBtn = row.querySelector('.trigger-inline');

  if (AppState.activeNodeId === id) {
    // Explicit close: animate the reverse
    closeExpander(row, expander, headerBtn, inlineBtn, true);
  } else {
    // Close any previously open expander instantly (no reverse animation)
    if (AppState.activeNodeId !== null) {
      const activeRow = document.querySelector(
        `.node-row[data-id="${AppState.activeNodeId}"]`
      );
      if (activeRow) {
        const g = activeRow.closest('.level-group');
        closeExpander(
          activeRow,
          g.querySelector('.level-expander'),
          activeRow.querySelector('.node-header'),
          activeRow.querySelector('.trigger-inline'),
          false
        );
      }
    }
    openExpander(id, row, expander, headerBtn, inlineBtn);
  }
}

/* ---------------------------------------------------------------------------
 * Close
 * --------------------------------------------------------------------------- */

/**
 * @param {boolean} animated — true for reverse animation, false for instant snap
 */
function closeExpander(row, expander, headerBtn, inlineBtn, animated) {
  if (!animated) {
    // Instant: suppress CSS transitions
    expander.style.transition = 'none';
    expander.offsetHeight; // force reflow
  }

  // Trigger the reverse animation by removing is-open
  expander.classList.remove('is-open');
  headerBtn.setAttribute('aria-expanded', 'false');
  if (inlineBtn) inlineBtn.textContent = 'Expand';

  row.classList.remove('is-active');
  AppState.activeNodeId = null;
  AppState.updateTints({ expander: 'transparent' });

  // Defer focus dimming removal slightly so the close animation is visible
  // against the dimmed background (otherwise everything brightens instantly
  // and the shrinking panel is invisible against bright cards).
  if (animated) {
    setTimeout(() => {
      // Only remove focus if no other expander has opened in the meantime
      if (AppState.activeNodeId === null) {
        document.body.classList.remove('is-focused');
      }
    }, ANIMATION_SPEEDS.CSS_TRANSITION_MS * 0.6);
  } else {
    document.body.classList.remove('is-focused');
  }

  const cleanupDelay = animated ? ANIMATION_SPEEDS.CSS_TRANSITION_MS : 0;
  setTimeout(() => {
    // DOM moves after animation is complete — moving mid-animation kills it
    const levelGroup = row.closest('.level-group');
    if (levelGroup && expander.parentNode !== levelGroup) {
      levelGroup.appendChild(expander);
    }
    expander.style.marginLeft = '';
    expander.style.flex = '';
    if (!expander.classList.contains('is-open')) expander.innerHTML = '';
    expander.style.transition = '';
  }, cleanupDelay);
}

/* ---------------------------------------------------------------------------
 * Open
 * --------------------------------------------------------------------------- */

function openExpander(id, row, expander, headerBtn, inlineBtn) {
  const nodeData = DataStore.map.get(id);
  if (!nodeData) return;

  // In stacked mode, move the expander to right after the clicked row
  const levelGroup = row.closest('.level-group');
  if (levelGroup?.hasAttribute('data-stacked')) {
    row.after(expander);
    const indentDepth = row.style.getPropertyValue('--indent-depth') || '0';
    expander.style.marginLeft = `calc(var(--stacked-indent) * ${indentDepth})`;
    expander.style.flex = `0 0 calc(100% - var(--stacked-indent) * ${indentDepth})`;
  }

  expander.innerHTML = expanderTemplate(nodeData);
  bindTabEvents(expander, nodeData);
  bindActionEvents(expander);

  requestAnimationFrame(() => {
    expander.classList.add('is-open');
    headerBtn.setAttribute('aria-expanded', 'true');
    if (inlineBtn) inlineBtn.textContent = 'Hide';

    row.classList.add('is-active');
    document.body.classList.add('is-focused');
    AppState.activeNodeId = id;
    AppState.updateTints({
      expander: `hsla(${nodeData.hue}, 80%, 50%, 0.35)`
    });

    scrollToView(row);
  });
}

/* ---------------------------------------------------------------------------
 * Tab events
 * --------------------------------------------------------------------------- */

function bindTabEvents(expander, nodeData) {
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

function renderTabPanel(nodeData, key) {
  const panel = document.getElementById(`panel-${nodeData.id}`);
  if (!panel) return;
  const section = (nodeData.sections || []).find(
    s => s.type === 'tab' && s.title === key
  );
  panel.innerHTML = tabContent(section?.items || [], section?.numbered || false);
}

/* ---------------------------------------------------------------------------
 * Action events (agree/disagree toggles)
 * --------------------------------------------------------------------------- */

function bindActionEvents(expander) {
  const agreeBtn = expander.querySelector('.btn-agree');
  const disagreeBtn = expander.querySelector('.btn-disagree');

  if (agreeBtn && disagreeBtn) {
    agreeBtn.addEventListener('click', () => {
      agreeBtn.setAttribute('aria-pressed', 'true');
      disagreeBtn.setAttribute('aria-pressed', 'false');
    });
    disagreeBtn.addEventListener('click', () => {
      disagreeBtn.setAttribute('aria-pressed', 'true');
      agreeBtn.setAttribute('aria-pressed', 'false');
    });
  }
}

/* ---------------------------------------------------------------------------
 * Scroll into view
 * --------------------------------------------------------------------------- */

function scrollToView(el) {
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

