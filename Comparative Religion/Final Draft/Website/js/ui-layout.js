/**
 * =============================================================================
 * ui-layout.js — Parallel-Row Cramp Detection
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
 * Dependencies: constants.js (STACK_THRESHOLD)
 * Consumers:    (none yet — to be wired in during a later step)
 * =============================================================================
 */

import { STACK_THRESHOLD } from './constants.js';

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
        // Collect all nodes (must all be direct level-group children right now)
        const nodes = nodeIds.map(id =>
          levelGroup.querySelector(`:scope > .node-row[data-id="${id}"]`)
        );
        if (nodes.some(n => !n)) return; // Abort if any node is already moved

        const wrapper = document.createElement('div');
        wrapper.className = 'stack-group';
        wrapper.style.setProperty('--flex-weight', String(combinedWeight));

        // Transfer parallel edge attributes so the wrapper participates
        // in the flex-basis equalization alongside any remaining siblings.
        if (nodes[0].hasAttribute('data-first-parallel')) {
          wrapper.dataset.firstParallel = 'true';
        }
        const lastNode = nodes[nodes.length - 1];
        if (lastNode.hasAttribute('data-last-parallel')) {
          wrapper.dataset.lastParallel = 'true';
        }

        // Insert wrapper in the position of the first node, then move all nodes in
        levelGroup.insertBefore(wrapper, nodes[0]);
        nodes.forEach(n => wrapper.appendChild(n));

        // --- Zone extension: absorb descendant rows ---
        if (zoneRows) {
          zoneRows.forEach(({ rowIdx: zoneRowIdx, nodeIds: zoneNodeIds }) => {
            zoneNodeIds.forEach(id => {
              // Search the entire view — a sub-zone may have already moved
              // this node into a different stack-group.
              const node = viewEl.querySelector(`.node-row[data-id="${id}"]`);
              if (!node) return;
              // Skip if already inside THIS wrapper (idempotent)
              if (node.parentElement === wrapper) return;

              // Tag with original row so the SVG engine can create
              // separate visual rows for zone-absorbed nodes.
              node.dataset.zoneOriginRow = String(zoneRowIdx);

              // If inside another stack-group (sub-zone), extract first
              const parentSG = node.parentElement;
              if (parentSG.classList.contains('stack-group')) {
                const sourceLG = parentSG.closest('.level-group');
                if (sourceLG) sourceLG.insertBefore(node, parentSG);
                if (!parentSG.querySelector('.node-row')) parentSG.remove();
                // Mark source level-group absorbed if now empty of real nodes
                if (sourceLG && !sourceLG.querySelector(':scope > .node-row')) {
                  sourceLG.dataset.zoneAbsorbed = '';
                }
              }

              wrapper.appendChild(node);
            });

            // Mark the original level-group as absorbed if empty
            const zoneLG = viewEl.querySelector(
              `.level-group[data-row-idx="${zoneRowIdx}"]`
            );
            if (zoneLG && !zoneLG.querySelector(':scope > .node-row')) {
              zoneLG.dataset.zoneAbsorbed = '';
            }
          });
        }

        // --- DFS ordering and indent depths ---
        // Reorder wrapper children to depth-first outline order and set
        // --indent-depth on each node for CSS indentation.
        if (zoneOrder) {
          zoneOrder.forEach(({ id, depth }) => {
            const node = wrapper.querySelector(`:scope > .node-row[data-id="${id}"]`);
            if (node) {
              wrapper.appendChild(node);  // moves to end → builds DFS order
              node.style.setProperty('--indent-depth', String(depth));
            }
          });
        }

        changed = true;

      } else if (!shouldStack && isStacked) {
        const wrapper = firstNode.parentElement; // .stack-group

        // --- Zone un-absorb: move zone nodes back before unwrapping ---
        if (zoneRows) {
          // Process in reverse so earlier rows are restored first
          [...zoneRows].reverse().forEach(({ rowIdx: zoneRowIdx, nodeIds: zoneNodeIds }) => {
            const zoneLG = viewEl.querySelector(
              `.level-group[data-row-idx="${zoneRowIdx}"]`
            );
            if (!zoneLG) return;

            zoneNodeIds.forEach(id => {
              const node = wrapper.querySelector(`:scope > .node-row[data-id="${id}"]`);
              if (!node) return;

              // Remove zone origin tag and indent depth set during absorption
              delete node.dataset.zoneOriginRow;
              node.style.removeProperty('--indent-depth');

              // Restore node to its original column position using data-col-idx.
              // Dummies that never moved still sit in the level-group, so we
              // find the first child whose col-idx is higher and insert before it.
              const nodeCol = parseInt(node.dataset.colIdx) || 0;
              let insertBefore = null;
              for (const child of zoneLG.children) {
                const childCol = parseInt(child.dataset.colIdx);
                if (!isNaN(childCol) && childCol > nodeCol) {
                  insertBefore = child;
                  break;
                }
              }
              if (!insertBefore) {
                // No child with a higher colIdx — insert before the expander
                insertBefore = zoneLG.querySelector('.level-expander');
              }
              zoneLG.insertBefore(node, insertBefore);
            });

            delete zoneLG.dataset.zoneAbsorbed;
          });
        }

        // --- Unwrap trigger nodes ---
        const nodes = nodeIds.map(id =>
          wrapper.querySelector(`:scope > .node-row[data-id="${id}"]`)
        );
        if (nodes.some(n => !n)) return;

        // Restore each node as a direct level-group child, in original order,
        // by inserting them before the wrapper (which still holds its position)
        nodes.forEach(n => {
          n.style.removeProperty('--indent-depth');
          levelGroup.insertBefore(n, wrapper);
        });
        wrapper.remove();
        changed = true;
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
