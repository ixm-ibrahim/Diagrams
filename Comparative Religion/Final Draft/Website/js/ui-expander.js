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
import { stopAnimationRedraw } from './svg-engine.js';

/* --- Expander animation guard ---
 * True while an expander open/close animation is in progress.
 * Checked by ensureExpanderIntegrity() to avoid destroying animated
 * spacers mid-transition (the ResizeObserver fires during the animation
 * and would otherwise recreate them with instant heights).             */
let _expanderAnimating = false;

/** @returns {boolean} Whether an expander animation is currently running. */
export function isExpanderAnimating() { return _expanderAnimating; }

/* --- Sticky card via scroll-driven transform ---
 * CSS position:sticky fails inside flex-wrap:wrap containers in many
 * browsers.  Instead we listen to scroll events and apply a translateY
 * on the active row to pin it below the page header.  The row's
 * original layout position is preserved; only the visual position shifts.
 * The z-index on .node-row.is-active (set in CSS) ensures it paints
 * above the expander.                                                    */
let _stickyCleanup = null;

function setupStickyScroll(row, expander, stickyTop) {
  if (_stickyCleanup) _stickyCleanup();

  const expInner = expander.querySelector('.exp-inner');
  let currentTranslateY = 0;
  let ticking = false;
  let hasFade = false;

  const update = () => {
    ticking = false;
    if (!row.classList.contains('is-active')) return;

    const rowRect = row.getBoundingClientRect();
    // Subtract our current transform to get the row's *natural* viewport top
    const naturalTop = rowRect.top - currentTranslateY;
    const rowHeight = rowRect.height;

    // Boundary: the expander's bottom, not the full level-group.
    // The row should unstick once the expansion content has scrolled
    // past the viewport — not when the entire container scrolls out.
    const expanderBottom = expander.getBoundingClientRect().bottom;

    if (naturalTop < stickyTop) {
      // Pin the row at stickyTop, but don't let it overshoot the
      // expander bottom.  The max clamp naturally scrolls the row
      // away with the expander instead of hard-snapping it back.
      const target = stickyTop - naturalTop;
      const max = Math.max(0, expanderBottom - rowHeight - naturalTop - 20);
      currentTranslateY = Math.max(0, Math.min(target, max));
      row.style.transform = `translateY(${currentTranslateY}px)`;

      // Fade mask: make expander content dissolve as it scrolls under the row.
      // Calculate how many pixels of .exp-inner are behind the pinned row.
      if (expInner) {
        const eiTop = expInner.getBoundingClientRect().top;
        const rowBottom = rowRect.top + rowHeight;  // visual bottom of pinned row
        const overlap = rowBottom - eiTop;
        if (overlap > 0) {
          expInner.style.setProperty('--mask-clip', `${overlap}px`);
          if (!hasFade) { expInner.classList.add('has-stuck-fade'); hasFade = true; }
        } else if (hasFade) {
          expInner.classList.remove('has-stuck-fade');
          hasFade = false;
        }
      }
    } else {
      if (currentTranslateY !== 0) {
        currentTranslateY = 0;
        row.style.transform = '';
      }
      if (hasFade && expInner) {
        expInner.classList.remove('has-stuck-fade');
        hasFade = false;
      }
    }
  };

  const onScroll = () => {
    if (!ticking) { requestAnimationFrame(update); ticking = true; }
  };

  window.addEventListener('scroll', onScroll, { passive: true });
  // Run once immediately so the row pins if the page is already scrolled
  onScroll();

  _stickyCleanup = () => {
    window.removeEventListener('scroll', onScroll);
    currentTranslateY = 0;
    row.style.removeProperty('transform');
    if (expInner) {
      expInner.classList.remove('has-stuck-fade');
      expInner.style.removeProperty('--mask-clip');
    }
    hasFade = false;
    _stickyCleanup = null;
  };
}

function cleanupStickyScroll() {
  if (_stickyCleanup) _stickyCleanup();
}

/**
 * Toggles the expander for the given node ID.
 * If already open, closes it. If another is open, closes that first.
 *
 * @param {string} id — node ID
 */
export function toggleExpander(id) {
  const allRows = document.querySelectorAll(`.node-row[data-id="${id}"]`);
  const row = Array.from(allRows).find(r => r.offsetParent !== null) || allRows[0];
  if (!row) return;

  const levelGroup = row.closest('.level-group');
  const stackGroup = row.closest('.stack-group');
  const expander = levelGroup.querySelector('.level-expander')
    || row.parentElement?.querySelector(':scope > .level-expander');
  const headerBtn = row.querySelector('.node-header');
  const inlineBtn = row.querySelector('.trigger-inline');

  if (AppState.activeNodeId === id) {
    closeExpander(row, expander, headerBtn, inlineBtn, true);
    // Scroll the row to just below the header so it doesn't end up
    // behind or above it after the expander collapses.
    scrollToView(row);
  } else {
    // Accordion switch: close previous, then open new.
    if (AppState.activeNodeId !== null) {
      const activeRows = document.querySelectorAll(
        `.node-row[data-id="${AppState.activeNodeId}"]`
      );
      const activeRow = Array.from(activeRows).find(r => r.offsetParent !== null)
        || activeRows[0];
      if (activeRow) {
        const g = activeRow.closest('.level-group');
        const prevExp = g.querySelector('.level-expander')
          || activeRow.parentElement?.querySelector(':scope > .level-expander')
          || document.querySelector('.level-expander.is-open');
        closeExpander(
          activeRow,
          prevExp,
          activeRow.querySelector('.node-header'),
          activeRow.querySelector('.trigger-inline'),
          false,
          true
        );
      }
    }

    // Snap scroll before opening — ALWAYS instant-snap in accordion mode.
    // A smooth scroll races with the expanding content (the expander grows
    // during the animation, inflating page height, which causes the browser's
    // smooth-scroll to overshoot).  An instant snap positions the row at
    // stickyTop immediately, so setupStickyScroll needs zero translateY and
    // the expander opens cleanly below the card instead of behind it.
    const pageHeader = document.getElementById('pageHeader');
    const stickyTop = pageHeader
      ? pageHeader.getBoundingClientRect().height + 12 + 8
      : 120;
    const rowRect = row.getBoundingClientRect();
    if (Math.abs(rowRect.top - stickyTop) > 2) {
      window.scrollTo({
        top: window.scrollY + rowRect.top - stickyTop + 4,
        behavior: 'instant'
      });
    }

    // Re-query the expander (cleanup may have replaced it)
    const freshExp = levelGroup.querySelector('.level-expander')
      || row.parentElement?.querySelector(':scope > .level-expander');
    openExpander(id, row, freshExp || expander, headerBtn, inlineBtn, { accordion: true });
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
  cleanupStickyScroll();
  // Best-effort DOM cleanup — the elements may already be removed
  const activeRows = document.querySelectorAll('.node-row.is-active');
  const openExpanders = document.querySelectorAll('.level-expander.is-open');
  const spacers = document.querySelectorAll('.expander-spacer');

  activeRows.forEach(r => {
    r.classList.remove('is-active');
    r.style.removeProperty('--sticky-top');
    r.style.transform = '';
  });
  openExpanders.forEach(e => {
    e.classList.remove('is-open');
    e.innerHTML = '';
  });
  spacers.forEach(s => s.remove());
  _expanderAnimating = false;

  AppState.activeNodeId = null;
  AppState.updateTints({ expander: 'transparent' });
  document.body.classList.remove('is-focused');
}

/**
 * @param {boolean} animated — true for reverse animation, false for instant snap
 */
function closeExpander(row, expander, headerBtn, inlineBtn, animated, keepFocused = false) {
  cleanupStickyScroll();
  // Guard: expander may have been displaced by a layout transition
  if (!expander) {
    row.classList.remove('is-active');
    AppState.activeNodeId = null;
    AppState.updateTints({ expander: 'transparent' });
    if (!keepFocused) document.body.classList.remove('is-focused');
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
    _expanderAnimating = true;
    document.querySelectorAll('.expander-spacer').forEach(s => {
      s.style.height = '0px';
    });
    // Start continuous SVG redraw so return branches animate smoothly
    document.dispatchEvent(new Event('expander-animating'));
  }

  row.classList.remove('is-active');
  row.style.removeProperty('--sticky-top');
  AppState.activeNodeId = null;
  AppState.updateTints({ expander: 'transparent' });

  // Defer focus dimming removal slightly so the close animation is visible
  // against the dimmed background (otherwise everything brightens instantly
  // and the shrinking panel is invisible against bright cards).
  // When keepFocused is true (accordion switch), skip removal entirely —
  // the incoming expander will maintain the is-focused state.
  if (!keepFocused) {
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
  }

  const cleanup = () => {
    const levelGroup = row.closest('.level-group');
    if (levelGroup) {
      levelGroup.style.paddingBottom = '';
      const fresh = document.createElement('div');
      fresh.className = 'level-expander';
      if (expander.parentNode === levelGroup) {
        expander.replaceWith(fresh);
      } else {
        expander.remove();
        levelGroup.appendChild(fresh);
      }
    }
    document.querySelectorAll('.expander-spacer').forEach(s => s.remove());
  };

  if (animated) {
    // DOM moves after animation is complete — moving mid-animation kills it
    setTimeout(() => {
      // Stop the SVG animation RAF loop BEFORE touching the DOM so it
      // can't draw another frame with positions shifted by cleanup().
      stopAnimationRedraw();
      // Check BEFORE cleanup() replaces the expander whether focus
      // was inside the panel so we can return it to the node header.
      const shouldReturnFocus = expander.contains(document.activeElement);
      cleanup();
      // Return focus to the node header if it was in the closing panel
      if (shouldReturnFocus && headerBtn) headerBtn.focus();
      _expanderAnimating = false;
      // Wait one frame after cleanup's DOM mutations so the browser
      // fully commits layout before the final SVG redraw measures
      // element positions.  Without this, getBoundingClientRect()
      // can return stale values intermittently.
      requestAnimationFrame(() => {
        document.dispatchEvent(new Event('expander-settled'));
      });
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

function openExpander(id, row, expander, headerBtn, inlineBtn, { accordion = false } = {}) {
  const nodeData = DataStore.map.get(id);
  if (!nodeData) return;

  const levelGroup = row.closest('.level-group');
  const stackGroup = row.closest('.stack-group');

  if (stackGroup) {
    row.after(expander);
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
  // Compute sticky offset: card sticks just below the page header.
  // The header is position:sticky at top:12px, so once stuck its bottom
  // is stable in the viewport. We measure it now and set as a CSS var.
  const pageHeader = document.getElementById('pageHeader');
  if (pageHeader) {
    const headerRect = pageHeader.getBoundingClientRect();
    const stickyTop = headerRect.height + 12 + 8; // header top offset (12px) + gap (8px)
    row.style.setProperty('--sticky-top', `${stickyTop}px`);
  }

  requestAnimationFrame(() => {
    // Suppress browser scroll anchoring during the expand animation.
    // As the expander grows (grid-template-rows 0fr → 1fr), elements below
    // it shift down in the flow.  The browser's default overflow-anchor
    // behaviour tries to keep those elements at the same viewport position
    // by auto-scrolling the page downward — which forces setupStickyScroll
    // to apply a large translateY on the active row, making the card
    // visually overlap/cover the expander content.
    // Disabling anchoring for the duration of the animation prevents this.
    const htmlEl = document.documentElement;
    const prevAnchor = htmlEl.style.overflowAnchor;
    htmlEl.style.overflowAnchor = 'none';

    expander.classList.add('is-open');
    headerBtn.setAttribute('aria-expanded', 'true');
    if (inlineBtn) inlineBtn.textContent = 'Hide';

    _expanderAnimating = true;
    document.dispatchEvent(new Event('expander-animating'));

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
      _expanderAnimating = false;
      // Restore scroll anchoring now that the layout has settled
      htmlEl.style.overflowAnchor = prevAnchor;
      // Trigger a scroll update so the stuck-fade mask applies
      // retroactively if the user scrolled during the animation
      // (the fade logic was suppressed while _expanderAnimating was true).
      window.dispatchEvent(new Event('scroll'));
      document.dispatchEvent(new Event('expander-settled'));
    }, ANIMATION_SPEEDS.CSS_TRANSITION_MS);

    // In accordion mode, use instant scroll and also do a second correction
    // after a brief delay — the first instant scroll may have been clamped
    // when the page was at max scroll (before the expander started growing).
    if (accordion) {
      // Immediate instant scroll (may be clamped)
      scrollToView(row, { instant: true });
      // Second correction after the expander has grown enough to un-clamp
      setTimeout(() => {
        if (AppState.activeNodeId !== id) return;
        const rr = row.getBoundingClientRect();
        const st = parseFloat(row.style.getPropertyValue('--sticky-top')) || 120;
        if (Math.abs(rr.top - st) > 2) {
          window.scrollTo({
            top: window.scrollY + rr.top - st + 4,
            behavior: 'instant'
          });
        }
      }, 50);
    } else {
      scrollToView(row);
    }

    // Activate scroll-driven sticky immediately so it responds from the
    // first scroll.  The max-clamp inside the handler naturally adapts
    // as the expander animates to its full height.
    const stickyTopVal = parseFloat(row.style.getPropertyValue('--sticky-top')) || 120;
    setupStickyScroll(row, expander, stickyTopVal);

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
