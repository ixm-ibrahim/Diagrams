/* === ui-render-weights.js — Flex weight computation and DFS zone ordering === */
/**
 * Dependencies: data-store.js (DataStore)
 * Consumers: ui-render.js (buildView)
 * =============================================================================
 */

import { DataStore } from './data-store.js';

/**
 * Walks a row of nodes in order and groups consecutive real nodes that share
 * the same primary parent into runs.  Dummy nodes terminate any open run and
 * are returned as singleton items so they remain direct flex children.
 *
 * Each node entry retains its original column index from `rowNodes` so the
 * caller can map it back to `rowWeights[colIdx]` from computeFlexWeights.
 *
 * @param {Array<Object>} rowNodes
 * @returns {Array<
 *   { isDummyItem: true,  node: Object, colIdx: number } |
 *   { parentId: string|null, nodes: Array<{ node: Object, colIdx: number }> }
 * >}
 */
export function buildOrderedRuns(rowNodes) {
  const runs = [];
  let current = null;

  rowNodes.forEach((node, colIdx) => {
    if (node.isDummy) {
      if (current) { runs.push(current); current = null; }
      runs.push({ isDummyItem: true, node, colIdx });
      return;
    }
    const pid = node.prevIds?.[0] ?? null;
    if (!current || current.parentId !== pid) {
      if (current) runs.push(current);
      current = { parentId: pid, nodes: [{ node, colIdx }] };
    } else {
      current.nodes.push({ node, colIdx });
    }
  });
  if (current) runs.push(current);
  return runs;
}

/**
 * Computes proportional flex weights using flow-based distribution.
 * Each parent distributes its weight equally to all its children in the
 * next row. Children with multiple parents accumulate weight from each.
 *
 * This correctly handles DAGs like node 3:
 *   [3.2(0.5), 3.3(0.5)] → [3.4, 3.5, 3.6] (all children of both)
 *   3.2 gives 0.5/3 to each, 3.3 gives 0.5/3 to each → each gets 1/3
 *
 * @param {Array<Array<Object>>} groupedRows — rows from computeLevels
 * @returns {Array<Array<number>>} weights[rowIdx][colIdx]
 */
export function computeFlexWeights(groupedRows) {
  const weights = [];

  // Build column index lookup: nodeId → { rowIdx, colIdx }
  const colOf = new Map();
  groupedRows.forEach((row, rowIdx) => {
    row.forEach((item, colIdx) => {
      if (item.id) colOf.set(item.id, { rowIdx, colIdx });
      if (item.isDummy) colOf.set(`dummy:${item.sourceId}:${item.targetId}:${rowIdx}`, { rowIdx, colIdx });
    });
  });

  for (let rowIdx = 0; rowIdx < groupedRows.length; rowIdx++) {
    const row = groupedRows[rowIdx];
    const rowWeights = new Array(row.length).fill(0);

    if (rowIdx === 0 || row.length <= 1) {
      rowWeights.fill(1);
      weights.push(rowWeights);
      continue;
    }

    const prevRow = groupedRows[rowIdx - 1];
    const prevWeights = weights[rowIdx - 1];

    // For each parent in the prev row, find how many children it has in
    // this row, then distribute its weight equally among them.
    prevRow.forEach((parent, parentColIdx) => {
      const parentWeight = prevWeights[parentColIdx] || 1;

      // Find all items in the current row that claim this parent
      const childColIndices = [];

      row.forEach((child, childColIdx) => {
        if (child.isDummy) {
          // Dummy's parent is its sourceId (or another dummy with same sourceId)
          if (parent.id === child.sourceId ||
              (parent.isDummy && parent.sourceId === child.sourceId)) {
            childColIndices.push(childColIdx);
          }
        } else {
          // Real node: parent is in prevIds
          const prevIds = child.prevIds || [];
          if (parent.id && prevIds.includes(parent.id)) {
            childColIndices.push(childColIdx);
          }
          // Also match dummy parents that route to this child
          if (parent.isDummy && parent.targetId === child.id) {
            childColIndices.push(childColIdx);
          }
        }
      });

      if (childColIndices.length > 0) {
        const share = parentWeight / childColIndices.length;
        childColIndices.forEach(ci => { rowWeights[ci] += share; });
      }
    });

    // If any items got zero (no parent found), give them equal share of remainder
    const zeroCount = rowWeights.filter(w => w === 0).length;
    if (zeroCount > 0) {
      const total = rowWeights.reduce((a, b) => a + b, 0);
      const remainder = Math.max(0, 1 - total);
      const fallback = remainder / zeroCount || 1 / row.length;
      rowWeights.forEach((w, i) => { if (w === 0) rowWeights[i] = fallback; });
    }

    weights.push(rowWeights);
  }

  return weights;
}

/**
 * Computes DFS ordering and indent depths for nodes in a stacked zone.
 *
 * DFS ordering: entry points (nodes whose parents are all outside the zone)
 * are visited first, in their original array order.  Each node's children
 * (via nextIds) that are inside the zone are visited immediately, but only
 * once ALL of a child's zone-parents have been visited (prevents a node
 * appearing before one of its parents in the outline).
 *
 * Indent depths:
 *   - Entry points → depth 1
 *   - Single zone-parent → parent depth + 1
 *   - Multiple zone-parents, all siblings → parent depth + 1
 *     (Parents are "siblings" when they all share the same zone-grandparents.
 *      This covers co-parents at the same level feeding into a shared child.)
 *   - Multiple zone-parents, from different branches → deepest parent's depth
 *     (NOT + 1).  This "merge-back" rule prevents the outline from drifting
 *     rightward every time genuinely separate branches rejoin.
 *
 * @param {string[]} allZoneIds — trigger node IDs + absorbed zone node IDs
 * @returns {Array<{ id: string, depth: number }>}  DFS-ordered entries
 */
export function computeZoneOrder(allZoneIds) {
  const zoneSet = new Set(allZoneIds);

  // For each zone node, collect its parents that are also in the zone.
  const zoneParentsOf = new Map();
  for (const id of allZoneIds) {
    const node = DataStore.map.get(id);
    if (!node) { zoneParentsOf.set(id, []); continue; }
    zoneParentsOf.set(id, (node.prevIds || []).filter(pid => zoneSet.has(pid)));
  }

  // Entry points: zone nodes with no zone-parents (all parents outside).
  const entryPoints = allZoneIds.filter(id => zoneParentsOf.get(id).length === 0);

  const visited = new Set();
  const order = [];
  const depths = new Map();

  function tryVisit(id) {
    if (visited.has(id)) return;
    // Don't visit until every zone-parent has been placed.
    if (!(zoneParentsOf.get(id) || []).every(pid => visited.has(pid))) return;

    visited.add(id);

    // --- Compute indent depth ---
    // Depth tracks the "parallel breadth" of the DAG at each generation.
    // Expansion (fewer parents → more children) increases depth.
    // Convergence (more parents → fewer children) decreases depth.
    // Equal breadth keeps depth unchanged.
    const zoneParents = zoneParentsOf.get(id);
    let depth;
    if (zoneParents.length === 0) {
      depth = 1;                                       // entry point
    } else if (zoneParents.length === 1) {
      // Single parent — always indent one level deeper.
      // Zones only absorb rows with 2+ descendants, so the parent always
      // has siblings at its depth.  A child must indent to show hierarchy.
      const parentDepth = depths.get(zoneParents[0]) || 1;
      depth = parentDepth + 1;
    } else {
      // Multiple zone-parents.
      const maxParentDepth = Math.max(...zoneParents.map(pid => depths.get(pid) || 1));
      const minParentDepth = Math.min(...zoneParents.map(pid => depths.get(pid) || 1));

      if (minParentDepth !== maxParentDepth) {
        depth = maxParentDepth;    // deep merge → merge-back
      } else {
        // Same-depth parents: compare breadth to decide direction.
        // Collect the union of all zone-children these parents produce.
        const parentChildUnion = new Set();
        for (const pid of zoneParents) {
          const pNode = DataStore.map.get(pid);
          if (pNode) {
            (pNode.nextIds || []).filter(nid => zoneSet.has(nid))
              .forEach(nid => parentChildUnion.add(nid));
          }
        }
        const childCount  = parentChildUnion.size;
        const parentCount = zoneParents.length;
        if (childCount > parentCount) {
          depth = maxParentDepth + 1;                   // expansion
        } else if (childCount < parentCount) {
          depth = Math.max(1, maxParentDepth - 1);      // convergence
        } else {
          depth = maxParentDepth;                        // same breadth
        }
      }
    }
    depths.set(id, depth);
    order.push({ id, depth });

    // Visit zone-children in nextIds order (preserves declared sibling order).
    const node = DataStore.map.get(id);
    if (node) {
      (node.nextIds || []).filter(nid => zoneSet.has(nid))
        .forEach(childId => tryVisit(childId));
    }
  }

  entryPoints.forEach(id => tryVisit(id));
  return order;
}
