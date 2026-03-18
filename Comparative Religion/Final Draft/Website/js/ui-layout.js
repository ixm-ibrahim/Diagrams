/**
 * =============================================================================
 * ui-layout.js — Parallel-Row Cramp Detection & Stack Orchestration
 * =============================================================================
 * Analyses rows of nodes produced by graph-engine.js and identifies which
 * parent-groups are "too cramped" — i.e. where each child's allocated pixel
 * width would fall below STACK_THRESHOLD.
 *
 * No DOM access, no DataStore access.  Pure calculation that works solely
 * from the row array and a measured container width, making it easy to
 * unit-test in isolation.
 *
 * Width model
 * -----------
 * Each unique parent referenced in a row is assumed to own an equal horizontal
 * slice of the container (containerWidth / numParentGroups).  Within that
 * slice, the per-child width is simply groupWidth / childCount.
 *
 * This mirrors the flex-weight model in ui-render.js, where each parent at
 * the previous level starts with equal weight (1 / N) and distributes it to
 * its children.  The equal-share assumption is exact for the first row, and a
 * reliable approximation for deeper rows where parent weights are already
 * proportional to their child counts.
 *
 * Root nodes (prevIds absent or empty) are treated as a single group under
 * the sentinel key null.
 *
 * Dependencies: constants.js, ui-layout-stacking.js, ui-layout-integrity.js
 * Consumers:    main.js, ui-render.js
 * =============================================================================
 */

import { STACK_THRESHOLD } from './constants.js';
import {
  wrapStackGroup,
  handlePartialZone,
  unwrapStackGroup
} from './ui-layout-stacking.js';
import { ensureExpanderIntegrity } from './ui-layout-integrity.js';

/**
 * Keeps every parallel sibling group in `viewEl` in the correct layout state
 * (horizontal or stacked-column) for the given container width.
 *
 * Strategy — dynamic DOM wrapping, not a static wrapper:
 *   Nodes are built as direct `.level-group` children so the parallel CSS
 *   selectors (which require `> .node-row`) work correctly at full width.
 *   `buildView` records each multi-node group as JSON in
 *   `levelGroup.dataset.stackGroups`.  This function reads that metadata and:
 *     • wraps the group's nodes in a `.stack-group` column when narrow, or
 *     • moves them back as direct children when wide.
 *   This means the parallel flex-equalization and marker CSS are always active
 *   on direct children and never broken by an intermediate wrapper element.
 *
 * The function is safe to call on every resize event — it only touches the DOM
 * when a group actually crosses its threshold.
 *
 * @param {HTMLElement} viewEl         - the .map-flow element currently in DOM
 * @param {number}      containerWidth - measured pixel width of the container
 */
export function updateStackedGroups(viewEl, containerWidth) {
  let changed = false;

  // Snapshot the active node's vertical position before any DOM changes.
  // If a stacked→parallel transition moves it significantly, we scroll.
  const activeRowBefore = viewEl.querySelector('.node-row.is-active');
  const activeTopBefore = activeRowBefore
    ? activeRowBefore.getBoundingClientRect().top
    : null;

  viewEl.querySelectorAll('.level-group[data-stack-groups]').forEach(levelGroup => {
    let groups;
    try { groups = JSON.parse(levelGroup.dataset.stackGroups); }
    catch { return; }

    groups.forEach(({ nodeIds, stackAt, combinedWeight, zoneRows, zoneOrder }) => {
      const shouldStack = containerWidth < stackAt;

      // Locate the first node — it tells us the current wrapping state
      const firstNode = levelGroup.querySelector(
        `:scope > .node-row[data-id="${nodeIds[0]}"], ` +
        `:scope > .stack-group > .node-row[data-id="${nodeIds[0]}"]`
      );
      if (!firstNode) return;

      const isStacked = firstNode.parentElement.classList.contains('stack-group');

      if (shouldStack && !isStacked) {
        // --- Wrap ---
        if (wrapStackGroup(viewEl, levelGroup, containerWidth, nodeIds, combinedWeight, zoneRows, zoneOrder)) {
          changed = true;
        }

      } else if (shouldStack && isStacked) {
        // --- Partial zone release / absorption ---
        if (handlePartialZone(viewEl, levelGroup, containerWidth, firstNode, zoneRows, zoneOrder)) {
          changed = true;
        }

      } else if (!shouldStack && isStacked) {
        // --- Unwrap ---
        if (unwrapStackGroup(viewEl, levelGroup, nodeIds, zoneRows)) {
          changed = true;
        }
      }
    });

    // Toggle data-has-stacked so CSS can prevent cross-axis stretch on
    // direct .node-row siblings when a .stack-group column is present.
    const hasAnyStacked = levelGroup.querySelector(':scope > .stack-group') !== null;
    if (hasAnyStacked) {
      levelGroup.dataset.hasStacked = '';
    } else {
      delete levelGroup.dataset.hasStacked;
    }

  });

  // Always run integrity when an open expander exists — breakout margins
  // and accommodation spacers must track container-width changes that don't
  // cross a stacking threshold (e.g. two sibling stack-groups in the same
  // level-group resizing between thresholds).
  if (changed || viewEl.querySelector('.level-expander.is-open')) {
    ensureExpanderIntegrity(viewEl);
  }

  // When a stacked→parallel transition moves the active (expanded) node
  // significantly, scroll to keep it visible.  Compare its position before
  // and after the DOM update to detect movement.
  if (activeTopBefore !== null && changed) {
    const activeRowAfter = viewEl.querySelector('.node-row.is-active');
    if (activeRowAfter) {
      const activeTopAfter = activeRowAfter.getBoundingClientRect().top;
      const drift = Math.abs(activeTopAfter - activeTopBefore);
      if (drift > 60) {
        // Node moved substantially — scroll so its top edge sits just
        // below the page header with some padding.
        const header = document.querySelector('.app-header, #pageHeader, header');
        const headerBottom = header ? header.getBoundingClientRect().bottom : 0;
        const targetTop = Math.max(headerBottom, 0) + 16;
        window.scrollTo({
          top: window.scrollY + activeTopAfter - targetTop,
          behavior: 'smooth'
        });
      }
    }
  }

  return changed;
}

/**
 * Given one row from computeLevels() and the container's current pixel width,
 * groups real nodes by their shared DAG parent(s), estimates the per-child
 * pixel width for each group, and returns every group whose per-child width
 * falls below STACK_THRESHOLD.
 *
 * Dummy nodes (node.isDummy === true) are excluded from grouping — they only
 * occupy flex space as lane-holders and are not candidates for stacking.
 *
 * A node that lists multiple prevIds contributes to a separate group for each
 * parent.  This correctly handles DAG merges: each parent independently "owns"
 * a horizontal slice, so a shared child can be cramped on one parent's side
 * but not another's.
 *
 * A row with zero or one real node is never cramped (no side-by-side layout
 * exists to collapse), so an empty array is returned immediately.
 *
 * @param {Array<Object>} rowNodes
 *   One inner array from computeLevels() — may contain real nodes and/or
 *   dummy objects ({ isDummy: true, sourceId, targetId }).
 *
 * @param {number} containerWidth
 *   Current pixel width of the .map-flow container, as measured from the DOM
 *   (e.g. via ResizeObserver or getBoundingClientRect).
 *
 * @returns {Array<{
 *   parentId:      string | null,
 *   children:      Array<Object>,
 *   perChildWidth: number
 * }>}
 *   One entry per cramped group.  parentId is null for the synthetic group
 *   that collects root-level nodes (no prevIds).  Returns an empty array when
 *   no group is cramped.
 */
export function identifyCrampedGroups(rowNodes, containerWidth) {
  const realNodes = rowNodes.filter(n => !n.isDummy);

  // A row with one or zero real nodes has nothing side-by-side to collapse.
  if (realNodes.length <= 1) return [];

  // Collect the unique parent IDs referenced across this row.
  // Using a Set ensures each parent is counted exactly once even when several
  // children share the same predecessor.
  const parentIds = new Set();
  realNodes.forEach(n => {
    if (n.prevIds && n.prevIds.length > 0) {
      n.prevIds.forEach(pid => parentIds.add(pid));
    } else {
      parentIds.add(null); // root-level nodes share a synthetic null group
    }
  });

  // Divide the container equally among all parent groups.
  const perGroupWidth = containerWidth / parentIds.size;

  const crampedGroups = [];

  parentIds.forEach(pid => {
    // Each group's children are the real nodes that list this parent.
    const children = realNodes.filter(n =>
      pid === null
        ? (!n.prevIds || n.prevIds.length === 0)
        : (n.prevIds || []).includes(pid)
    );

    if (children.length === 0) return;

    const perChildWidth = perGroupWidth / children.length;

    if (perChildWidth < STACK_THRESHOLD) {
      crampedGroups.push({ parentId: pid, children, perChildWidth });
    }
  });

  return crampedGroups;
}
