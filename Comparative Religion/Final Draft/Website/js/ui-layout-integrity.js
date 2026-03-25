/* === ui-layout-integrity.js — Expander Integrity & Positioning === */
/*
 * Enforces invariants on open expanders after stacking/unstacking transitions:
 *   1. Open expander is the immediate next sibling of the active node-row,
 *      with correct breakout margins when inside a stack-group.
 *   2. Every visible level-group has exactly one .level-expander element.
 *
 * Dependencies: ui-expander.js (isExpanderAnimating)
 * Consumers:    ui-layout.js
 */

import { isExpanderAnimating } from './ui-expander.js';

/**
 * Enforces expander positioning invariants after stacking transitions.
 * Ensures the open expander is the immediate next sibling of the active
 * node-row, and that every visible level-group has exactly one
 * .level-expander element.
 *
 * @param {HTMLElement} viewEl — the .map-flow container
 */
export function ensureExpanderIntegrity(viewEl) {
  const openExp = viewEl.querySelector('.level-expander.is-open');
  const activeRow = viewEl.querySelector('.node-row.is-active');

  // --- Position the open expander correctly ---
  if (openExp && activeRow) {
    const stackGroup = activeRow.closest('.stack-group');

    if (stackGroup) {
      // Stacked mode: expander must be right after the active row inside
      // the stack-group so it appears inline (tree-view style).
      if (openExp.previousElementSibling !== activeRow ||
          openExp.parentElement !== activeRow.parentElement) {
        activeRow.after(openExp);
      }
      // Reset positioning from parallel or mixed mode
      openExp.style.position = '';
      openExp.style.top = '';
      openExp.style.left = '';
      // Clear parallel pull-up — not needed in stacked mode
      delete openExp.dataset.parallelPull;
      openExp.style.removeProperty('--parallel-pull');
      const lg = stackGroup.closest('.level-group');
      lg.style.paddingBottom = '';
      const lgRect = lg.getBoundingClientRect();
      const sgRect = stackGroup.getBoundingClientRect();
      openExp.style.flex = '0 0 auto';
      openExp.style.width = 'auto';
      openExp.style.marginLeft = `-${sgRect.left - lgRect.left}px`;
      openExp.style.marginRight = `-${lgRect.right - sgRect.right}px`;

      // --- Accommodation spacers for sibling stack-groups ---
      // Remove stale spacers and recreate so nodes in sibling columns
      // shift down to make room for the breakout expander.
      // Skip while an expander animation is running — the spacers are
      // mid-transition and destroying them would cause a visual jump.
      if (!isExpanderAnimating()) {
        document.querySelectorAll('.expander-spacer').forEach(s => s.remove());
        const expInner = openExp.querySelector('.exp-inner');
        const spacerHeight = expInner ? expInner.scrollHeight + 16 : 0;
        if (spacerHeight > 0) {
          // Use index-based placement: the active node's position in its
          // stack determines the insertion point in every sibling stack.
          // This is robust against per-node height differences that make
          // bounding-rect comparisons flaky across resize breakpoints.
          const stackRows = Array.from(
            stackGroup.querySelectorAll(':scope > .node-row')
          );
          const activeIdx = stackRows.indexOf(activeRow);

          lg.querySelectorAll(':scope > .stack-group').forEach(sg => {
            if (sg === stackGroup) return;
            const siblingRows = Array.from(
              sg.querySelectorAll(':scope > .node-row')
            );
            if (siblingRows.length === 0) return;

            const spacer = document.createElement('div');
            spacer.className = 'expander-spacer';
            spacer.style.height = spacerHeight + 'px';

            // Insert after the node at the same index, or after the last
            // node if the sibling stack has fewer nodes.
            const targetIdx = Math.min(activeIdx, siblingRows.length - 1);
            siblingRows[targetIdx].after(spacer);
          });
        }
      }
    } else {
      const lg = activeRow.closest('.level-group');
      const hasStackedSibling = lg.querySelector(':scope > .stack-group');

      if (hasStackedSibling) {
        // Mixed parallel+stacked mode: the level-group has a tall stack-group
        // alongside shorter parallel node-rows.  flex-wrap places the expander
        // below the tallest item (the stack-group), far below the clicked row.
        // Fix: position the expander absolutely right below the active row.
        if (openExp.parentElement !== lg) {
          lg.appendChild(openExp);
        }

        const rowRect = activeRow.getBoundingClientRect();
        const lgRect = lg.getBoundingClientRect();
        const topOffset = rowRect.bottom - lgRect.top;

        openExp.style.position = 'absolute';
        openExp.style.top = topOffset + 'px';
        openExp.style.left = '0';
        openExp.style.width = '100%';
        openExp.style.flex = 'none';
        openExp.style.marginLeft = '';
        openExp.style.marginRight = '';

        // --- Accommodation spacers for sibling stack-groups ---
        // Skip while an expander animation is running.
        if (!isExpanderAnimating()) {
          document.querySelectorAll('.expander-spacer').forEach(s => s.remove());
          const expInner = openExp.querySelector('.exp-inner');
          const expHeight = expInner ? expInner.scrollHeight + 16 : 0;
          if (expHeight > 0) {
            const rowBottom = rowRect.bottom;
            lg.querySelectorAll(':scope > .stack-group').forEach(sg => {
              const sgNodes = Array.from(
                sg.querySelectorAll(':scope > .node-row')
              );
              if (sgNodes.length < 2) return;
              const firstNode = sgNodes[0];
              const firstNodeBottom = firstNode.getBoundingClientRect().bottom;
              const heightDiff = Math.max(0, rowBottom - firstNodeBottom);
              const spacer = document.createElement('div');
              spacer.className = 'expander-spacer';
              spacer.style.height = (expHeight + heightDiff) + 'px';
              firstNode.after(spacer);
            });
          }

          // Ensure level-group is tall enough so content below shifts down.
          lg.style.paddingBottom = '';
          const naturalHeight = lg.offsetHeight;
          const neededHeight = topOffset + expHeight;
          if (neededHeight > naturalHeight) {
            lg.style.paddingBottom = (neededHeight - naturalHeight) + 'px';
          }
        }
      } else {
        // Pure parallel mode: update the negative-margin pull-up so the
        // expander tracks the clicked node's bottom on resize.
        if (openExp.parentElement !== lg) {
          lg.appendChild(openExp);
        } else {
          const lastChild = lg.lastElementChild;
          if (lastChild !== openExp) lg.appendChild(openExp);
        }
        openExp.style.marginLeft = '';
        openExp.style.marginRight = '';
        openExp.style.flex = '';
        openExp.style.width = '';
        openExp.style.position = '';
        openExp.style.top = '';
        openExp.style.left = '';
        lg.style.paddingBottom = '';
        if (!isExpanderAnimating()) {
          document.querySelectorAll('.expander-spacer').forEach(s => s.remove());
        }

        // Recalculate pull-up for current node-card heights.
        // Always check when there are multiple siblings — the expander may
        // have transitioned from stacked mode where parallelPull was cleared.
        const siblingNodes = lg.querySelectorAll(':scope > .node-row');
        if (siblingNodes.length > 1) {
          const clickedCard = activeRow.querySelector('.node-card');
          const clickedBottom = clickedCard
            ? clickedCard.getBoundingClientRect().bottom
            : activeRow.getBoundingClientRect().bottom;
          let tallestCardBottom = clickedBottom;
          siblingNodes.forEach(n => {
            const card = n.querySelector('.node-card');
            const b = card ? card.getBoundingClientRect().bottom
                           : n.getBoundingClientRect().bottom;
            if (b > tallestCardBottom) tallestCardBottom = b;
          });
          const pullUp = tallestCardBottom - clickedBottom;
          if (pullUp > 0) {
            openExp.style.setProperty('--parallel-pull', `-${pullUp}px`);
            openExp.dataset.parallelPull = '';
          } else {
            openExp.style.removeProperty('--parallel-pull');
            delete openExp.dataset.parallelPull;
          }
        }
      }
    }
  } else if (openExp && !activeRow) {
    // Orphaned open expander with no active node — close it
    openExp.classList.remove('is-open');
    openExp.innerHTML = '';
  }

  // --- Ensure every visible level-group has exactly one expander ---
  viewEl.querySelectorAll('.level-group:not([data-zone-absorbed])').forEach(lg => {
    const allExp = lg.querySelectorAll('.level-expander');
    if (allExp.length === 0) {
      const newExp = document.createElement('div');
      newExp.className = 'level-expander';
      lg.appendChild(newExp);
    } else if (allExp.length > 1) {
      // Keep the open one; remove extras
      let kept = null;
      allExp.forEach(exp => {
        if (exp.classList.contains('is-open')) { kept = exp; }
      });
      if (!kept) kept = allExp[0];
      allExp.forEach(exp => { if (exp !== kept) exp.remove(); });
    }
  });
}
