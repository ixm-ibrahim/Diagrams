/* === ui-expander.js — Expander Panel Management ===
 * Dependencies: data-store.js (DataStore), state.js (AppState),
 *               templates.js (expander),
 *               constants.js (ANIMATION_SPEEDS),
 *               ui-agreement.js (applyVoteStates),
 *               ui-search.js (getActiveSearchQuery, highlightMatches),
 *               ui-expander-content.js (bindTabEvents, scrollToView)
 * Consumers: ui-events.js (calls toggleExpander on click),
 *            other modules (call forceCloseExpander)
 * ================================================================ */

import { DataStore } from './data-store.js';
import { AppState } from './state.js';
import { expander as expanderTemplate } from './templates.js';
import { ANIMATION_SPEEDS, CSS_TRANSITION_MS, FOCUS_DIM_DELAY_RATIO, EXPANDER_SPACER_MARGIN_PX, TINT_SATURATION, TINT_LIGHTNESS, TINT_ALPHA } from './constants.js';
import { getActiveSearchQuery, highlightMatches } from './ui-search.js';
import { applyVoteStates } from './ui-agreement.js';
import { bindTabEvents, scrollToView } from './ui-expander-content.js';

/**
 * Toggles the expander for the given node ID.
 * If already open, closes it. If another is open, closes that first.
 *
 * @param {string} id — node ID
 */
export function toggleExpander(id) {
  // When search results duplicate a node-row from the hidden map-flow,
  // querySelectorAll may return both.  Prefer the visible one (offsetParent
  // is null for elements inside display:none ancestors).
  const allRows = document.querySelectorAll(`.node-row[data-id="${id}"]`);
  const row = Array.from(allRows).find(r => r.offsetParent !== null) || allRows[0];
  if (!row) return;

  const levelGroup = row.closest('.level-group');
  // Search for the expander in the level-group first, then fall back to
  // the parent container (stack-group) — layout transitions can displace it.
  const expander = levelGroup.querySelector('.level-expander')
    || row.parentElement?.querySelector(':scope > .level-expander');
  const headerBtn = row.querySelector('.node-header');
  const inlineBtn = row.querySelector('.trigger-inline');

  if (AppState.activeNodeId === id) {
    // Explicit close: animate the reverse
    closeExpander(row, expander, headerBtn, inlineBtn, true);
  } else {
    // Close any previously open expander instantly (no reverse animation)
    if (AppState.activeNodeId !== null) {
      const activeRows = document.querySelectorAll(
        `.node-row[data-id="${AppState.activeNodeId}"]`
      );
      const activeRow = Array.from(activeRows).find(r => r.offsetParent !== null)
        || activeRows[0];
      if (activeRow) {
        const g = activeRow.closest('.level-group');
        // The expander might be in the level-group, in an adjacent
        // stack-group wrapper, or displaced by a zone absorption.
        // Search broadly to avoid null reference errors.
        const prevExp = g.querySelector('.level-expander')
          || activeRow.parentElement?.querySelector(':scope > .level-expander')
          || document.querySelector('.level-expander.is-open');
        closeExpander(
          activeRow,
          prevExp,
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
 * Immediately resets all expander-related state without requiring DOM
 * references to the active row. Use when the DOM is about to be rebuilt
 * (e.g. search results changing) and the active row may no longer exist.
 */
export function forceCloseExpander() {
  if (AppState.activeNodeId === null) return;

  // Best-effort DOM cleanup — the elements may already be removed
  // Consolidate three separate querySelectorAll calls into one pass
  const activeRows = document.querySelectorAll('.node-row.is-active');
  const openExpanders = document.querySelectorAll('.level-expander.is-open');
  const spacers = document.querySelectorAll('.expander-spacer');

  activeRows.forEach(r => r.classList.remove('is-active'));
  openExpanders.forEach(e => {
    e.classList.remove('is-open');
    e.innerHTML = '';
  });
  spacers.forEach(s => s.remove());

  AppState.activeNodeId = null;
  AppState.updateTints({ expander: 'transparent' });
  document.body.classList.remove('is-focused');
}

/**
 * @param {boolean} animated — true for reverse animation, false for instant snap
 */
function closeExpander(row, expander, headerBtn, inlineBtn, animated) {
  // Guard: expander may have been displaced by a layout transition
  if (!expander) {
    row.classList.remove('is-active');
    AppState.activeNodeId = null;
    AppState.updateTints({ expander: 'transparent' });
    document.body.classList.remove('is-focused');
    document.querySelectorAll('.expander-spacer').forEach(s => s.remove());
    const levelGroup = row.closest('.level-group');
    if (levelGroup) levelGroup.style.paddingBottom = '';
    return;
  }

  if (!animated) {
    // Instant: suppress CSS transitions
    expander.style.transition = 'none';
    expander.offsetHeight; // force reflow
  }

  // Trigger the reverse animation by removing is-open
  expander.classList.remove('is-open');
  headerBtn.setAttribute('aria-expanded', 'false');
  if (inlineBtn) inlineBtn.textContent = 'Expand';

  // Animate sibling spacers closed in sync with the expander
  if (animated) {
    document.querySelectorAll('.expander-spacer').forEach(s => {
      s.style.height = '0px';
    });
    // Start continuous SVG redraw so return branches animate smoothly
    document.dispatchEvent(new Event('expander-animating'));
  }

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
    }, CSS_TRANSITION_MS * FOCUS_DIM_DELAY_RATIO);
  } else {
    document.body.classList.remove('is-focused');
  }

  const cleanup = () => {
    const levelGroup = row.closest('.level-group');
    // Always move expander back to the end of the level-group.
    // This handles stacked mode where parentNode is a stack-group,
    // and pure parallel mode where it was relocated to map-flow.
    if (levelGroup) {
      levelGroup.style.paddingBottom = '';
      levelGroup.appendChild(expander);
    }
    delete expander.dataset.parallelPull;
    expander.style.removeProperty('--parallel-pull');
    expander.style.marginLeft = '';
    expander.style.marginRight = '';
    expander.style.flex = '';
    expander.style.width = '';
    expander.style.position = '';
    expander.style.top = '';
    expander.style.left = '';
    expander.style.zIndex = '';
    if (!expander.classList.contains('is-open')) expander.innerHTML = '';
    expander.style.transition = '';
    // Remove sibling spacers
    document.querySelectorAll('.expander-spacer').forEach(s => s.remove());
  };

  if (animated) {
    // DOM moves after animation is complete — moving mid-animation kills it
    setTimeout(() => {
      // Check BEFORE cleanup() clears expander.innerHTML whether focus
      // was inside the panel so we can return it to the node header.
      const shouldReturnFocus = expander.contains(document.activeElement);
      cleanup();
      // Return focus to the node header if it was in the closing panel
      if (shouldReturnFocus && headerBtn) headerBtn.focus();
      // Force SVG redraw after the expander DOM has settled — the
      // ResizeObserver may not fire a final event once the CSS animation
      // reaches 0fr, leaving the SVG connectors at stale positions.
      document.dispatchEvent(new Event('expander-settled'));
    }, ANIMATION_SPEEDS.CSS_TRANSITION_MS);
  } else {
    // Instant close: run cleanup synchronously so a subsequent openExpander
    // in the same call-stack finds the expander already reset in the level-group.
    cleanup();
  }
}

/* ---------------------------------------------------------------------------
 * Open
 * --------------------------------------------------------------------------- */

function openExpander(id, row, expander, headerBtn, inlineBtn) {
  const nodeData = DataStore.map.get(id);
  if (!nodeData) return;

  const levelGroup = row.closest('.level-group');
  const stackGroup = row.closest('.stack-group');

  if (stackGroup) {
    // Stacked mode: move the expander right after the clicked row inside
    // the stack-group so it appears inline (tree-view style).
    row.after(expander);
    // Break out of the narrow stack-group column to full level-group width
    // using negative margins on BOTH sides.  This avoids setting an explicit
    // pixel width (which inflates the stack-group's intrinsic cross-size and
    // corrupts the parallel flex layout).  With width: auto and align-items:
    // stretch (the default), the element stretches to:
    //   containerWidth + |marginLeft| + |marginRight| = levelGroup width.
    const lgRect = levelGroup.getBoundingClientRect();
    const sgRect = stackGroup.getBoundingClientRect();
    const breakoutLeft = sgRect.left - lgRect.left;
    const breakoutRight = lgRect.right - sgRect.right;

    expander.style.flex = '0 0 auto';
    expander.style.width = 'auto';
    expander.style.marginLeft = `-${breakoutLeft}px`;
    expander.style.marginRight = `-${breakoutRight}px`;
  } else if (levelGroup.querySelector(':scope > .stack-group')) {
    // Mixed parallel+stacked mode: the level-group has a tall stack-group
    // alongside shorter parallel node-rows.  flex-wrap places the expander
    // below the tallest item (the stack-group), far below the clicked row.
    // Fix: position the expander absolutely right below the active row.
    const rowRect = row.getBoundingClientRect();
    const lgRect = levelGroup.getBoundingClientRect();
    const topOffset = rowRect.bottom - lgRect.top;

    expander.style.position = 'absolute';
    expander.style.top = topOffset + 'px';
    expander.style.left = '0';
    expander.style.width = '100%';
    expander.style.flex = 'none';
  } else {
    // Pure parallel mode: sibling nodes may have different heights, so
    // flex-wrap places the expander below the tallest — not the clicked one.
    // Keep the expander in flow but use negative margin-top to pull it up
    // to align with the clicked node's bottom edge.
    const siblingNodes = levelGroup.querySelectorAll(':scope > .node-row');
    if (siblingNodes.length > 1) {
      // Measure NODE-CARD bottoms, not node-row bottoms, because
      // align-items:stretch makes all rows the same height.
      const clickedCard = row.querySelector('.node-card');
      const clickedBottom = clickedCard
        ? clickedCard.getBoundingClientRect().bottom
        : row.getBoundingClientRect().bottom;
      let tallestCardBottom = clickedBottom;
      siblingNodes.forEach(n => {
        const card = n.querySelector('.node-card');
        const b = card ? card.getBoundingClientRect().bottom
                       : n.getBoundingClientRect().bottom;
        if (b > tallestCardBottom) tallestCardBottom = b;
      });
      const pullUp = tallestCardBottom - clickedBottom;
      if (pullUp > 0) {
        expander.style.setProperty('--parallel-pull', `-${pullUp}px`);
        expander.dataset.parallelPull = '';
      }
    }
  }

  expander.innerHTML = expanderTemplate(nodeData);
  bindTabEvents(expander, nodeData);

  // Restore persisted vote states on the freshly rendered expander buttons
  applyVoteStates(expander);

  // Highlight search matches inside the expander content when in search mode
  const searchQuery = getActiveSearchQuery();
  if (searchQuery) highlightMatches(expander, searchQuery);

  // Measure the expander's natural content height (before animation starts)
  // so we can create matching spacers in sibling stack-group columns.
  let spacerHeight = 0;
  if (stackGroup) {
    const expInner = expander.querySelector('.exp-inner');
    // scrollHeight gives full content height even while grid-template-rows: 0fr
    // +EXPANDER_SPACER_MARGIN_PX accounts for the expander's net margin effect (-8 top + 24 bottom)
    spacerHeight = expInner ? expInner.scrollHeight + EXPANDER_SPACER_MARGIN_PX : 0;

    // Create spacers in each sibling stack-group so nodes below the
    // expander in ALL columns shift down.  Use index-based placement:
    // the clicked node's position in its stack determines the insertion
    // point in every sibling stack.  This is robust against per-node
    // height differences that make bounding-rect comparisons flaky.
    const stackRows = Array.from(
      stackGroup.querySelectorAll(':scope > .node-row')
    );
    const activeIdx = stackRows.indexOf(row);

    const siblingStacks = levelGroup.querySelectorAll(':scope > .stack-group');
    siblingStacks.forEach(sg => {
      if (sg === stackGroup) return;
      const siblingRows = Array.from(
        sg.querySelectorAll(':scope > .node-row')
      );
      if (siblingRows.length === 0) return;

      const spacer = document.createElement('div');
      spacer.className = 'expander-spacer';

      const targetIdx = Math.min(activeIdx, siblingRows.length - 1);
      siblingRows[targetIdx].after(spacer);
    });
  }

  // requestAnimationFrame defers to after the browser completes layout, ensuring
  // the expander's initial 0fr state is rendered before triggering the 1fr animation.
  requestAnimationFrame(() => {
    expander.classList.add('is-open');
    headerBtn.setAttribute('aria-expanded', 'true');
    if (inlineBtn) inlineBtn.textContent = 'Hide';

    // Start continuous SVG redraw so return branches animate smoothly
    document.dispatchEvent(new Event('expander-animating'));

    // Animate spacers to match expander height
    if (spacerHeight > 0) {
      document.querySelectorAll('.expander-spacer').forEach(s => {
        s.style.height = spacerHeight + 'px';
      });
    }

    // For absolute-positioned expanders (mixed parallel+stacked):
    // 1. Create spacers in stack-groups so their content shifts down
    // 2. Ensure level-group is tall enough for content below
    if (expander.style.position === 'absolute') {
      const expInner = expander.querySelector('.exp-inner');
      const expHeight = expInner ? expInner.scrollHeight + EXPANDER_SPACER_MARGIN_PX : 0;
      const topOffset = parseFloat(expander.style.top) || 0;

      // Create spacers in sibling stack-groups to push their content down.
      // The first node in each stack-group is on the same visual "row" as
      // the parallel active node — spacer goes right after it.  Height
      // compensates for any difference between active row and first node.
      if (expHeight > 0) {
        const rowBottom = row.getBoundingClientRect().bottom;
        levelGroup.querySelectorAll(':scope > .stack-group').forEach(sg => {
          const sgNodes = Array.from(
            sg.querySelectorAll(':scope > .node-row')
          );
          if (sgNodes.length < 2) return;
          const firstNode = sgNodes[0];
          const firstNodeBottom = firstNode.getBoundingClientRect().bottom;
          const heightDiff = Math.max(0, rowBottom - firstNodeBottom);
          const targetHeight = expHeight + heightDiff;
          const spacer = document.createElement('div');
          spacer.className = 'expander-spacer';
          // Start at 0 — animate to target height
          firstNode.after(spacer);
          requestAnimationFrame(() => {
            spacer.style.height = targetHeight + 'px';
          });
        });
      }

      // Ensure level-group is tall enough (after spacers added)
      levelGroup.style.paddingBottom = '';
      const naturalHeight = levelGroup.offsetHeight;
      const neededHeight = topOffset + expHeight;
      if (neededHeight > naturalHeight) {
        levelGroup.style.paddingBottom = (neededHeight - naturalHeight) + 'px';
      }
    }

    row.classList.add('is-active');
    document.body.classList.add('is-focused');
    AppState.activeNodeId = id;
    AppState.updateTints({
      expander: `hsla(${nodeData.hue}, ${TINT_SATURATION}%, ${TINT_LIGHTNESS}%, ${TINT_ALPHA})`
    });

    // Force SVG redraw after the open animation settles so connectors
    // account for the expander's full height (the ResizeObserver may
    // fire mid-animation with intermediate positions).
    setTimeout(() => {
      document.dispatchEvent(new Event('expander-settled'));
    }, ANIMATION_SPEEDS.CSS_TRANSITION_MS);

    scrollToView(row);

    // Keyboard focus: move focus to the first interactive element in the
    // expander after the animation has settled.  preventScroll suppresses
    // the browser's own scroll-on-focus so our scrollToView() drives it.
    setTimeout(() => {
      if (AppState.activeNodeId !== id) return; // closed before timeout fired
      const focusTarget = expander.querySelector('.btn-tab, .btn-action');
      if (focusTarget) focusTarget.focus({ preventScroll: true });
    }, ANIMATION_SPEEDS.CSS_TRANSITION_MS);
  });
}
