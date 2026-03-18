/**
 * =============================================================================
 * ui-render.js — View Building & Rendering
 * =============================================================================
 * Creates the DOM structure for a page of nodes, adds sibling navigation,
 * and mounts with directional transition animations.
 *
 * Dependencies: graph-engine.js (computeLevels),
 *               templates.js (nodeRow),
 *               data-store.js (DataStore),
 *               state.js (AppState),
 *               constants.js (ANIMATION_SPEEDS),
 *               sibling-nav.js (renderSiblingNavigation),
 *               svg-engine.js (draw),
 *               ui-agreement.js (applyVoteStates — restores glows after render)
 * Consumers: navigation.js (renderMapWithTransition),
 *            main.js (init)
 * =============================================================================
 */

import { computeLevels } from './graph-engine.js';
import { nodeRow } from './templates.js';
import { DataStore } from './data-store.js';
import { AppState } from './state.js';
import { ANIMATION_SPEEDS, STACK_THRESHOLD, DEEP_NODE_MIN_WIDTH } from './constants.js';
import { renderSiblingNavigation } from './sibling-nav.js';
import { draw as drawSVG } from './svg-engine.js';
import { updateStackedGroups } from './ui-layout.js';
import { applyVoteStates } from './ui-agreement.js';

/** Cached container element. Set by init(). */
let container = null;

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
function buildOrderedRuns(rowNodes) {
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
 * Caches the map container DOM reference. Call once during bootstrap.
 */
export function init() {
  container = document.getElementById('mapContainer');
}

/**
 * Builds the complete DOM subtree for the current page.
 * Returns a .map-flow element ready to be appended to the container.
 *
 * @returns {HTMLElement}
 */
export function buildView() {
  const newView = document.createElement('div');
  newView.className = 'map-flow';

  // Glow sits outside the timeline-layer (unaffected by layer opacity)
  const glow = document.createElement('div');
  glow.className = 'map-spine-glow';
  glow.setAttribute('aria-hidden', 'true');
  newView.appendChild(glow);

  // Timeline layer: compositing container for spine + SVG.
  // Container-level opacity makes overlapping opaque elements safe.
  const timelineLayer = document.createElement('div');
  timelineLayer.className = 'timeline-layer';
  timelineLayer.setAttribute('aria-hidden', 'true');
  const spine = document.createElement('div');
  spine.className = 'map-spine';
  timelineLayer.appendChild(spine);
  newView.appendChild(timelineLayer);

  const visibleNodes = DataStore.nodes.filter(
    n => n.parentId === AppState.currentParentId
  );

  if (visibleNodes.length === 0) {
    // Two cases:
    //   1. Terminal node (hasDerivation: false) — show the node's own card
    //      so the user sees the endpoint of the logic chain.
    //   2. Undeveloped node (hasDerivation: true, no children yet) — show
    //      only the message, since this page is expected to have content later.
    const parentNode = AppState.currentParentId
      ? DataStore.map.get(AppState.currentParentId)
      : null;

    const isTerminal = parentNode && parentNode.hasDerivation === false;

    if (isTerminal) {
      const levelGroup = document.createElement('div');
      levelGroup.className = 'level-group';

      const row = document.createElement('div');
      row.className = 'node-row';
      row.dataset.id = parentNode.id;
      row.innerHTML = nodeRow(parentNode);
      levelGroup.appendChild(row);

      const expanderEl = document.createElement('div');
      expanderEl.className = 'level-expander';
      levelGroup.appendChild(expanderEl);

      newView.appendChild(levelGroup);
    }

    const msg = document.createElement('div');
    msg.className = 'empty-page-message';
    msg.textContent = isTerminal
      ? 'This claim concludes this branch of reasoning.'
      : 'No deeper derivations mapped for this claim yet.';
    newView.appendChild(msg);

    return newView;
  }

  const fragment = document.createDocumentFragment();
  const groupedRows = computeLevels(visibleNodes);
  const allLevelGroups = [];
  const visibleIdSet = new Set(visibleNodes.map(n => n.id));

  // Compute proportional flex weights so child nodes inherit their
  // parent's share of the row width (tree-proportional layout).
  const weights = computeFlexWeights(groupedRows);

  groupedRows.forEach((rowNodes, rowIdx) => {
    const levelGroup = document.createElement('div');
    levelGroup.className = 'level-group';
    levelGroup.dataset.rowIdx = String(rowIdx);

    const realNodeEls = [];
    const flexItems = [];

    rowNodes.forEach((node, colIdx) => {
      if (node.isDummy) {
        const dummy = document.createElement('div');
        dummy.className = 'dummy-node';
        dummy.dataset.colIdx = String(colIdx);
        levelGroup.appendChild(dummy);
        flexItems.push(dummy);
        return;
      }

      const row = document.createElement('div');
      row.className = 'node-row';
      row.dataset.id = node.id;
      row.dataset.colIdx = String(colIdx);
      row.innerHTML = nodeRow(node);
      levelGroup.appendChild(row);
      realNodeEls.push(row);
      flexItems.push(row);
    });

    // Parallel tagging for flex-basis equalization
    const totalFlexChildren = flexItems.length;
    if (totalFlexChildren > 1) {
      levelGroup.dataset.parallel = '';
      flexItems[0].dataset.firstParallel = 'true';
      flexItems[flexItems.length - 1].dataset.lastParallel = 'true';

      // The last real node only gets the full derive button (via data-last-parallel)
      // if it's truly the rightmost item. If dummies come after it, the real node
      // should use condensed buttons like all other non-last parallel nodes.
      const lastRealNode = realNodeEls.length > 0
        ? realNodeEls[realNodeEls.length - 1]
        : null;
      const lastFlexItem = flexItems[flexItems.length - 1];
      if (lastRealNode && lastRealNode !== lastFlexItem) {
        // Last flex item is a dummy — it gets flex-basis compensation via
        // data-last-parallel (already set above). The last real node does NOT
        // get data-last-parallel, so it uses condensed derive buttons.
      } else if (lastRealNode) {
        // Last flex item IS the last real node — give it the full button
        lastRealNode.dataset.lastParallel = 'true';
      }

      // Apply proportional flex weights
      const rowWeights = weights[rowIdx];
      if (rowWeights) {
        flexItems.forEach((el, colIdx) => {
          const w = rowWeights[colIdx];
          if (w !== undefined && w !== 1) {
            el.style.setProperty('--flex-weight', String(w));
          }
        });
      }

      // Record sibling groups (including single nodes) so updateStackedGroups
      // can dynamically wrap / unwrap nodes into a .stack-group column when
      // the container narrows. Nodes stay as direct level-group children here
      // so all parallel CSS keeps working correctly at full width.
      const rowWeightsForStack = weights[rowIdx];

      const stackGroupsData = [];
      let lastWasDummy = false;
      buildOrderedRuns(rowNodes).forEach(run => {
        if (run.isDummyItem) { lastWasDummy = true; return; }
        const nodeIds = run.nodes.map(({ node }) => node.id);
        const colIndices = run.nodes.map(({ colIdx }) => colIdx);
        const combinedWeight = rowWeightsForStack
          ? colIndices.reduce((sum, ci) => sum + (rowWeightsForStack[ci] ?? 1), 0)
          : run.nodes.length;

        // Merge adjacent single-node runs into a combined stack group.
        // Two adjacent single-node runs from different parents would each
        // wrap independently (a visual no-op). Merging lets them stack
        // together into a shared column when the row narrows.
        const prev = stackGroupsData[stackGroupsData.length - 1];
        if (!lastWasDummy && prev && prev._singleRun && run.nodes.length === 1) {
          prev.nodeIds.push(...nodeIds);
          prev.combinedWeight += combinedWeight;
          // Use the maximum individual threshold — the narrowest node
          // determines when the merged group must stack.
          prev.stackAt = Math.max(
            prev.stackAt,
            Math.round(STACK_THRESHOLD * run.nodes.length / combinedWeight)
          );
          // stays _singleRun = true so further adjacent singles also merge
        } else {
          // Stack when each child's allocated width drops below STACK_THRESHOLD.
          // Per-child width = containerWidth × combinedWeight / nodeCount,
          // so stackAt = STACK_THRESHOLD × nodeCount / combinedWeight.
          stackGroupsData.push({
            nodeIds,
            stackAt: Math.round(STACK_THRESHOLD * run.nodes.length / combinedWeight),
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
          const zrStackAt = Math.round(STACK_THRESHOLD * ids.length / zrWeight);
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

      if (stackGroupsData.length > 0) {
        levelGroup.dataset.stackGroups = JSON.stringify(stackGroupsData);
      }
    }

    // Shared expander (Phase 4 populates on click)
    const expanderEl = document.createElement('div');
    expanderEl.className = 'level-expander';
    levelGroup.appendChild(expanderEl);

    allLevelGroups.push(levelGroup);
    fragment.appendChild(levelGroup);
  });

  newView._allLevelGroups = allLevelGroups;
  newView.appendChild(fragment);

  // Apply initial stacked/unstacked state without waiting for first resize event
  const cw = container ? container.offsetWidth : 0;
  if (cw > 0) {
    // Cascade stacking: force ancestor parallel rows to stack when their
    // descendant zones would produce cards narrower than DEEP_NODE_MIN_WIDTH.
    // Width-independent — raises stackAt thresholds for all relevant widths.
    applyCascadeStacking(allLevelGroups);
    updateStackedGroups(newView, cw);
  }

  return newView;
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
function computeFlexWeights(groupedRows) {
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
function computeZoneOrder(allZoneIds) {
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
 * @param {number} containerWidth — measured container pixel width
 */
function applyCascadeStacking(allLevelGroups) {
  // Use the largest --marker-col value (64 px) for a conservative estimate.
  // This ensures the cascade triggers early enough even if the viewport
  // later widens above the 1120 px breakpoint where marker-col is 64 px.
  const indent = 64;

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

        // The child's cascade threshold is the container width below which
        // the child zone's deepest node is too thin.  The parent must stack
        // at those widths so it absorbs the child and gives it more room.
        const newStackAt = Math.max(parentGroup.stackAt, needed);

        if (newStackAt <= parentGroup.stackAt) continue; // already sufficient

        parentGroup.stackAt = newStackAt;
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

/** Direction → CSS animation class mappings */
const EXIT_CLASS = {
  depth: 'anim-exit-left',
  surface: 'anim-exit-right',
  'lateral-next': 'anim-exit-top',
  'lateral-prev': 'anim-exit-bottom'
};
const ENTER_CLASS = {
  depth: 'anim-enter-right',
  surface: 'anim-enter-left',
  'lateral-next': 'anim-enter-bottom',
  'lateral-prev': 'anim-enter-top'
};

/**
 * Builds a new view and animates it in, simultaneously animating old views out.
 * Transition direction determines which animation classes are applied.
 *
 * @param {'depth'|'surface'|'lateral-next'|'lateral-prev'|'none'} direction
 */
export function renderMapWithTransition(direction) {
  if (!container) return;

  const oldViews = container.querySelectorAll(
    '.map-flow, .search-result-box, .search-group'
  );
  container.style.pointerEvents = 'none';
  AppState.isTransitioning = true;

  // Lock container height to prevent layout jump during transition.
  // Skip on initial render (no old views) to avoid a brief overflow clip
  // that cuts off derivation buttons and glow effects.
  const hasOldViews = oldViews.length > 0;
  if (hasOldViews) {
    container.style.minHeight = `${container.offsetHeight}px`;
    // Clip old views individually instead of the whole container,
    // so derivation buttons and glow effects on the new view aren't cut off.
    oldViews.forEach(v => { v.style.overflow = 'hidden'; });
  }

  // Phase 1: Build new view
  const newView = buildView();
  renderSiblingNavigation(newView);
  container.appendChild(newView);

  // Restore persisted vote button states on the freshly rendered nodes
  applyVoteStates(newView);

  // Phase 2: Draw SVG connectors (needs layout to settle)
  const visibleNodes = DataStore.nodes.filter(
    n => n.parentId === AppState.currentParentId
  );
  setTimeout(() => {
    try { drawSVG(newView, visibleNodes); }
    catch (err) { console.error('[UI] Phase 2 drawSVG threw:', err); }
  }, 50);

  // Phase 3: Animate old out, new in
  oldViews.forEach(oldView => {
    if (EXIT_CLASS[direction]) oldView.classList.add(EXIT_CLASS[direction]);
    oldView.style.position = 'absolute';
    oldView.style.top = '0';
    oldView.style.left = '0';
  });

  if (ENTER_CLASS[direction]) newView.classList.add(ENTER_CLASS[direction]);
  window.scrollTo(0, 0);

  // Phase 4: Cleanup after animation completes
  setTimeout(() => {
    oldViews.forEach(v => v.remove());
    newView.classList.remove(...Object.values(ENTER_CLASS));
    container.style.pointerEvents = '';
    container.style.minHeight = '';

    // Final SVG redraw after layout is fully settled
    setTimeout(() => {
      try { drawSVG(newView, visibleNodes); }
      catch (err) { console.error('[UI] Phase 4 drawSVG threw:', err); }
    }, 50);

    AppState.isTransitioning = false;
  }, ANIMATION_SPEEDS.CSS_TRANSITION_MS);
}
