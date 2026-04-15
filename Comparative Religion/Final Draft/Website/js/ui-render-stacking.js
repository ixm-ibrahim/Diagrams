/* === ui-render-stacking.js — Cascade stacking and zone extension logic === */
/**
 * Dependencies: constants.js (STACK_THRESHOLD, DEEP_NODE_MIN_WIDTH),
 *               data-store.js (DataStore),
 *               ui-render-weights.js (computeZoneOrder)
 * Consumers: ui-render.js (buildView)
 * =============================================================================
 */

import { STACK_THRESHOLD, DEEP_NODE_MIN_WIDTH } from './constants.js';
import { DataStore } from './data-store.js';
import { computeZoneOrder } from './ui-render-weights.js';

/**
 * Computes stack group metadata for a row (zone extension, deduplication, DFS ordering).
 * Called from buildView for each parallel row to set up the stackGroups JSON.
 *
 * Builds:
 *   1. Initial stackGroupsData from runs
 *   2. Zone extension: tracks descendants that should absorb into each group
 *   3. Deduplication: resolves conflicting claims across groups
 *   4. DFS ordering: computes zone order for each group's full zone
 *
 * @param {Array<Object>} rowNodes — nodes in the current row
 * @param {number} rowIdx — index of this row
 * @param {Array<Array<Object>>} groupedRows — all rows (from computeLevels)
 * @param {Array<Array<number>>} weights — flex weights from computeFlexWeights
 * @param {Set<string>} visibleIdSet — set of all visible node IDs in this level
 * @returns {Array<Object>} stackGroupsData — stack group configurations
 */
export function buildStackGroups(
  rowNodes, rowIdx, groupedRows, weights, visibleIdSet
) {
  const stackGroupsData = [];

  // Build initial groups from ordered runs (sibling groups).
  // Each group tracks: nodeIds, stackAt threshold, combinedWeight
  let lastWasDummy = false;
  const runs = buildOrderedRunsForStacking(rowNodes);

  // Compute total row weight so stacking thresholds reflect the group's
  // actual fraction of the container.  When a parallel sibling (e.g. a
  // terminal node) has no children in this row, its weight doesn't flow
  // forward, so the row's total weight falls below 1.0.  Without
  // normalization the threshold is inflated, causing premature stacking
  // that visually misplaces children under the wrong parent.
  const rowWeightsForStack = weights[rowIdx];
  const totalRowWeight = rowWeightsForStack
    ? rowWeightsForStack.reduce((sum, w) => sum + w, 0) : 0;

  runs.forEach(run => {
    if (run.isDummyItem) { lastWasDummy = true; return; }
    const nodeIds = run.nodes.map(({ node }) => node.id);
    const colIndices = run.nodes.map(({ colIdx }) => colIdx);
    const combinedWeight = rowWeightsForStack
      ? colIndices.reduce((sum, ci) => sum + (rowWeightsForStack[ci] ?? 1), 0)
      : run.nodes.length;

    // Effective fraction: the share of container width this group actually
    // receives in the flex layout.  Normalise against the row's total
    // weight so that a group which is the *only* content in a row is
    // treated as occupying 100%, not its absolute weight.
    const effectiveFraction = totalRowWeight > 0
      ? combinedWeight / totalRowWeight
      : combinedWeight;

    // Merge adjacent single-node runs into a combined stack group.
    // Two adjacent single-node runs from different parents would each
    // wrap independently (a visual no-op). Merging lets them stack
    // together into a shared column when the row narrows.
    const prev = stackGroupsData[stackGroupsData.length - 1];
    if (!lastWasDummy && prev && prev._singleRun && run.nodes.length === 1) {
      prev.nodeIds.push(...nodeIds);
      prev.combinedWeight += combinedWeight;
      // Recompute effective fraction for the merged group
      const mergedFraction = totalRowWeight > 0
        ? prev.combinedWeight / totalRowWeight
        : prev.combinedWeight;
      // Use the maximum individual threshold — the narrowest node
      // determines when the merged group must stack.
      prev.stackAt = Math.max(
        prev.stackAt,
        Math.round(STACK_THRESHOLD * run.nodes.length / mergedFraction)
      );
      // stays _singleRun = true so further adjacent singles also merge
    } else {
      // Stack when each child's allocated width drops below STACK_THRESHOLD.
      // Per-child width = containerWidth × effectiveFraction / nodeCount,
      // so stackAt = STACK_THRESHOLD × nodeCount / effectiveFraction.
      stackGroupsData.push({
        nodeIds,
        stackAt: Math.round(STACK_THRESHOLD * run.nodes.length / effectiveFraction),
        combinedWeight,
        _singleRun: run.nodes.length === 1
      });
    }
    lastWasDummy = false;
  });

  // Clean up temporary merge flag
  stackGroupsData.forEach(g => delete g._singleRun);

  // Zone extension: once a group stacks, absorb subsequent rows that
  // still have 2+ real descendant nodes (i.e. the DAG hasn't merged
  // back to a single thread yet).  Stored per-group so
  // updateStackedGroups can pull descendant nodes into the same
  // .stack-group column when the trigger threshold is crossed.
  stackGroupsData.forEach(group => {
    const zoneSet = new Set(group.nodeIds);
    const zoneRows = [];

    for (let r = rowIdx + 1; r < groupedRows.length; r++) {
      const nextRow = groupedRows[r];
      const descendants = nextRow.filter(n =>
        !n.isDummy && (n.prevIds || []).some(pid => zoneSet.has(pid))
      );
      if (descendants.length === 0) break;

      // Count distinct zone-member parents of the descendants.
      // If descendants < zone-parents, branches are merging — stop.
      // E.g. [3.7,3.8] (2) have zone-parents [3.4,3.5,3.6] (3) → merge.
      // But [4.5,4.6] (2) have zone-parents [4.2,4.4] (2) → continuation.
      const zoneParents = new Set();
      const outsideParents = new Set();
      descendants.forEach(n => {
        (n.prevIds || []).forEach(pid => {
          if (zoneSet.has(pid)) {
            zoneParents.add(pid);
          } else if (visibleIdSet.has(pid)) {
            outsideParents.add(pid);
          }
        });
      });
      // Convergence: fewer descendants than zone-parents means
      // branches are merging.  Stop if:
      //   - any parent is outside the zone (external merge), or
      //   - collapsing to a single node with no dummies (single-thread
      //     continuation, no width-stealing to compensate).
      // Continue if 2+ descendants remain and all parents are internal —
      // this is a fan-in that's still parallel and should stay in the
      // stacked outline.  Also continue when dummies coexist (they
      // steal width, so absorbing lets the level-group collapse).
      if (descendants.length < zoneParents.size) {
        if (outsideParents.size > 0) break;
        const rowHasDummies = nextRow.some(n => n.isDummy);
        if (descendants.length <= 1 && !rowHasDummies) break;
      }
      // Don't absorb if outside parents sit in the same row as the
      // zone's trigger nodes — they're parallel siblings in another
      // group, so absorbing the descendants into just this zone would
      // misposition them (they should span ALL parent groups).
      if (outsideParents.size > 0) {
        const sameRowIds = new Set(
          rowNodes.filter(n => !n.isDummy).map(n => n.id)
        );
        if ([...outsideParents].some(pid => sameRowIds.has(pid))) break;
      }
      // Don't absorb if more of the descendants' parents are outside
      // the zone than inside — the row is a merge point that should
      // remain visible to its other parents' edge paths.
      if (outsideParents.size > zoneParents.size) break;

      const ids = descendants.map(n => n.id);
      // Compute the zone row's own stacking threshold so
      // updateStackedGroups only absorbs it when the row would
      // actually be too narrow to stay parallel.
      let zrWeight = 0;
      for (let ci = 0; ci < nextRow.length; ci++) {
        if (!nextRow[ci].isDummy && ids.includes(nextRow[ci].id)) {
          zrWeight += (weights[r] ? weights[r][ci] : 1) || 1;
        }
      }
      if (zrWeight === 0) zrWeight = ids.length;
      // Normalise against the zone row's total weight (same reasoning as
      // the trigger row — parent weight may not fully flow forward).
      const zrTotalWeight = (weights[r] || []).reduce((sum, w) => sum + w, 0) || 1;
      const zrEffective = zrTotalWeight > 0 ? zrWeight / zrTotalWeight : zrWeight;
      const zrStackAt = Math.round(STACK_THRESHOLD * ids.length / zrEffective);
      zoneRows.push({ rowIdx: r, nodeIds: ids, stackAt: zrStackAt });
      ids.forEach(id => zoneSet.add(id));
    }

    if (zoneRows.length > 0) {
      group.zoneRows = zoneRows;
    }
  });

  // Deduplicate zone node claims across groups in the same row.
  // If multiple groups both want to absorb the same node, the group
  // with the highest stackAt (stacks at the widest width) wins.
  // This prevents conflicting absorption/release cycles on resize.
  const nodeClaimedBy = new Map(); // nodeId → { groupIdx, stackAt }
  stackGroupsData.forEach((group, gi) => {
    (group.zoneRows || []).forEach(zr => {
      zr.nodeIds.forEach(nid => {
        const existing = nodeClaimedBy.get(nid);
        if (!existing || group.stackAt > existing.stackAt) {
          nodeClaimedBy.set(nid, { groupIdx: gi, stackAt: group.stackAt });
        }
      });
    });
  });
  stackGroupsData.forEach((group, gi) => {
    if (!group.zoneRows) return;
    group.zoneRows = group.zoneRows.map(zr => ({
      ...zr,
      nodeIds: zr.nodeIds.filter(nid => {
        const winner = nodeClaimedBy.get(nid);
        return winner && winner.groupIdx === gi;
      })
    })).filter(zr => zr.nodeIds.length > 0);
    if (group.zoneRows.length === 0) delete group.zoneRows;
  });

  // Compute DFS ordering and indent depths for each group's full zone
  // (trigger nodes + absorbed nodes).  Stored in the JSON metadata so
  // updateStackedGroups can reorder and indent the DOM at runtime.
  stackGroupsData.forEach(group => {
    const allZoneIds = [...group.nodeIds];
    if (group.zoneRows) {
      group.zoneRows.forEach(zr => allZoneIds.push(...zr.nodeIds));
    }
    if (allZoneIds.length > 1) {
      group.zoneOrder = computeZoneOrder(allZoneIds);
    }
  });

  // Potential companions: for each zone row in each group, identify nodes
  // that are NOT being absorbed by this group but whose parent sits in the
  // trigger row and is NOT part of this group's nodeIds.  At runtime, if
  // the parent is still a direct flex child (its own group didn't stack),
  // wrapStackGroup wraps parent + child into a mini-column so they stay
  // vertically adjacent instead of landing in a far-away level-group.
  const triggerRowRealIds = new Set(
    rowNodes.filter(n => !n.isDummy).map(n => n.id)
  );

  stackGroupsData.forEach(group => {
    if (!group.zoneRows) return;

    group.zoneRows.forEach(zr => {
      const zoneRowAllNodes = groupedRows[zr.rowIdx].filter(n => !n.isDummy);
      const notAbsorbed = zoneRowAllNodes.filter(n => !zr.nodeIds.includes(n.id));
      if (notAbsorbed.length === 0) return;

      const companions = [];
      notAbsorbed.forEach(orphan => {
        (orphan.prevIds || []).forEach(pid => {
          if (!triggerRowRealIds.has(pid)) return;
          // Parent must NOT be in this group's trigger nodes
          if (group.nodeIds.includes(pid)) return;
          companions.push({ childId: orphan.id, parentId: pid });
        });
      });

      if (companions.length > 0) {
        zr.potentialCompanions = companions;
      }
    });
  });

  return stackGroupsData;
}

/**
 * Internal helper: builds ordered runs for stacking (groups consecutive
 * real nodes by parent, with dummies as singletons).
 * @param {Array<Object>} rowNodes
 * @returns {Array}
 */
function buildOrderedRunsForStacking(rowNodes) {
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
 * Cascade stacking: when a stacked zone's deepest node would be narrower
 * than DEEP_NODE_MIN_WIDTH, force ancestor parallel rows to stack so the
 * zone gets wider.
 *
 * Strategy:
 *   Each group already has pre-computed zoneRows / zoneOrder covering its
 *   full descendant zone.  The cascade raises ancestor groups' stackAt to
 *   the mathematical threshold at which their deepest node reaches
 *   DEEP_NODE_MIN_WIDTH:
 *
 *     cascadeStackAt = (DEEP_NODE_MIN_WIDTH + maxDepth × indent) / weight
 *
 *   The runtime updateStackedGroups processes level-groups top-down, so
 *   the widest ancestor group absorbs everything first; narrower descendant
 *   groups become no-ops (their trigger nodes are already wrapped).
 *
 * @param {HTMLElement[]} allLevelGroups — level-group elements (index = rowIdx)
 */
export function applyCascadeStacking(allLevelGroups) {
  // Read the actual stacked indent from CSS so the cascade threshold
  // matches the real layout rather than a hardcoded worst-case estimate.
  // Falls back to 64px if the CSS variable is unavailable.
  const indent = parseInt(
    getComputedStyle(document.documentElement).getPropertyValue('--stacked-indent'), 10
  ) || 64;

  // Build nodeId → rowIdx lookup from the level-group DOM.
  const nodeRowIdx = new Map();
  allLevelGroups.forEach((lg, ri) => {
    [...lg.querySelectorAll(':scope > .node-row, :scope > .dummy-node')]
      .forEach(el => { if (el.dataset.id) nodeRowIdx.set(el.dataset.id, ri); });
  });

  // Parse stackGroupsData from each level-group into working arrays.
  const allStackData = allLevelGroups.map(lg => {
    if (!lg.dataset.stackGroups) return null;
    try { return JSON.parse(lg.dataset.stackGroups); }
    catch { return null; }
  });

  /**
   * Minimum containerWidth that keeps the deepest node ≥ MIN_WIDTH
   * when this group is stacked and its zone is active.
   */
  function cascadeThreshold(group) {
    if (!group.zoneOrder || group.zoneOrder.length === 0) return 0;
    const maxDepth = Math.max(...group.zoneOrder.map(e => e.depth));
    // deepestWidth = C × W − maxDepth × indent  ≥  MIN_WIDTH
    // ⟹  C ≥ (MIN_WIDTH + maxDepth × indent) / W
    return Math.ceil(
      (DEEP_NODE_MIN_WIDTH + maxDepth * indent) / group.combinedWeight
    );
  }

  // Width-independent bottom-up cascade.
  //
  // For every group with a zone, compute the container width below which
  // its zone's deepest node is too thin (cascadeThreshold).  If that
  // threshold exceeds the parent group's stackAt, the parent must also
  // stack at those widths — raise its stackAt to match.  When the parent
  // stacks, it absorbs this group's nodes into its own (wider) zone.
  //
  // Example: group at weight 0.25 has cascadeThreshold 1568.  Its parent
  // at weight 0.5 has stackAt 1080.  Below 1568 the child zone is too
  // thin, but the parent doesn't stack until below 1080.  Raising the
  // parent's stackAt to 1568 makes it stack earlier, absorbing the child
  // into a zone twice as wide.
  let cascadeOccurred = true;
  while (cascadeOccurred) {
    cascadeOccurred = false;

    for (let ri = allStackData.length - 1; ri >= 0; ri--) {
      const groups = allStackData[ri];
      if (!groups) continue;

      for (const group of groups) {
        if (!group.zoneOrder || group.zoneOrder.length === 0) continue;

        const needed = cascadeThreshold(group);
        if (needed <= 0) continue;

        // --- Find parent row's group ---
        const triggerParentIds = new Set();
        group.nodeIds.forEach(id => {
          const node = DataStore.map.get(id);
          if (node) (node.prevIds || []).forEach(pid => triggerParentIds.add(pid));
        });

        let parentGroup = null;
        for (const pid of triggerParentIds) {
          const pri = nodeRowIdx.get(pid);
          if (pri === undefined || pri >= ri) continue;
          const parentGroups = allStackData[pri];
          if (!parentGroups) continue;
          for (const pg of parentGroups) {
            if (pg.nodeIds.includes(pid)) { parentGroup = pg; break; }
          }
          if (parentGroup) break;
        }

        if (!parentGroup) continue; // can't cascade further

        // Store the cascade threshold separately from the group's own
        // stackAt.  stackAt controls when the group's own cards are too
        // narrow (per-child < STACK_THRESHOLD).  cascadeStackAt controls
        // when zone children would be too thin — it only prevents UN-stacking,
        // it doesn't force stacking when per-child width is still healthy.
        const prev = parentGroup.cascadeStackAt || 0;
        const newCascade = Math.max(prev, needed);

        if (newCascade <= prev) continue;

        parentGroup.cascadeStackAt = newCascade;
        cascadeOccurred = true;
      }
    }
  }

  // Write back any modified stackGroupsData.
  allLevelGroups.forEach((lg, ri) => {
    if (allStackData[ri]) {
      lg.dataset.stackGroups = JSON.stringify(allStackData[ri]);
    }
  });
}
