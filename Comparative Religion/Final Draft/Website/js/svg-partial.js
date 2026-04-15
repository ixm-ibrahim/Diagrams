/* === svg-partial.js — Partial Stacking Edge Routing === */
/**
 * Handles the mixed parallel+stacked layout case: processes each
 * stack-group zone, builds zone trunk spines, and routes edges
 * across stacked/non-stacked boundaries.
 *
 * Dependencies: svg-geometry.js, svg-paths.js, svg-stacked.js
 * Consumers:    svg-engine.js
 */

import { SVG_OVERLAP, FORK_BRANCH_GAP, RADIUS_ADJUST } from './constants.js';
import { STRAIGHT_THRESHOLD, MAX_CORNER_RADIUS } from './svg-geometry.js';
import { drawEdgePath, drawTerminalReturns, buildColumnSpines } from './svg-paths.js';
import { processStackedZone } from './svg-stacked.js';
import { DataStore } from './data-store.js';

/**
 * Draws edges and spines for partially-stacked layouts where some
 * level-groups contain stack-groups alongside parallel nodes.
 */
export function drawPartialStacking(stackGroups, viewEl, visibleNodes, positions,
                                    trunkX, indentSpines, allPathData, forkPathData,
                                    visualRows, nodeToRowIdx) {
  const stackedNodeIds = new Set();
  const groupHasTerminalReturn = new Map();

  // Pre-populate stackedNodeIds
  stackGroups.forEach(sg => {
    sg.querySelectorAll(':scope > .node-row').forEach(row => {
      if (row.dataset.id && positions.has(row.dataset.id)) stackedNodeIds.add(row.dataset.id);
    });
  });

  // Process each stack-group zone
  stackGroups.forEach(sg => {
    const nodeRows = sg.querySelectorAll(':scope > .node-row');
    if (nodeRows.length < 2) return;

    const displayOrder = [];
    const depthMap = new Map();
    nodeRows.forEach(row => {
      const id = row.dataset.id;
      if (!id || !positions.has(id)) return;
      displayOrder.push(id);
      depthMap.set(id, parseInt(row.style.getPropertyValue('--indent-depth')) || 0);
      stackedNodeIds.add(id);
    });
    if (displayOrder.length < 2) return;

    let sgTrunkX = null;
    for (const id of displayOrder) {
      if ((depthMap.get(id) || 0) === 0 && positions.get(id)) {
        sgTrunkX = positions.get(id).x; break;
      }
    }
    if (sgTrunkX === null) {
      const minDepth = Math.min(...displayOrder.map(id => depthMap.get(id) || 0));
      for (const id of displayOrder) {
        if ((depthMap.get(id) || 0) === minDepth) {
          sgTrunkX = positions.get(id)?.x ?? trunkX; break;
        }
      }
    }

    const zoneLastPos = positions.get(displayOrder[displayOrder.length - 1]);
    const hasTerminalReturn = zoneLastPos &&
      Math.abs(zoneLastPos.x - sgTrunkX) >= STRAIGHT_THRESHOLD;

    // Pre-compute whether this zone needs a zone-to-main-trunk return.
    // Needed before the spine is created so the spine knows not to fade.
    const zoneOffMainTrunk = Math.abs(sgTrunkX - trunkX) >= STRAIGHT_THRESHOLD;
    let willDrawZoneReturn = false;
    if (!hasTerminalReturn && zoneOffMainTrunk) {
      const zoneIdSet = new Set(displayOrder);
      willDrawZoneReturn = true;
      for (const id of displayOrder) {
        const node = DataStore.map.get(id);
        if (node && (node.nextIds || []).some(nid => !zoneIdSet.has(nid) && positions.has(nid))) {
          willDrawZoneReturn = false;
          break;
        }
      }
    }

    processStackedZone(displayOrder, depthMap, positions, sgTrunkX,
                       indentSpines, allPathData,
                       hasTerminalReturn ? trunkX : null);

    // Zone trunk spine when offset from main trunk
    if (zoneOffMainTrunk) {
      const firstPos = positions.get(displayOrder[0]);
      const lastPos = positions.get(displayOrder[displayOrder.length - 1]);
      if (firstPos && lastPos) {
        let spineBottom = lastPos.visualBottom;
        const visibleMap = new Map(visibleNodes.map(n => [n.id, n]));
        const bfsVisited = new Set(displayOrder);
        const bfsQueue = [];
        for (const id of displayOrder) {
          const node = visibleMap.get(id);
          for (const nid of (node?.nextIds || [])) {
            if (!bfsVisited.has(nid) && positions.has(nid)) bfsQueue.push(nid);
          }
        }
        while (bfsQueue.length > 0) {
          const id = bfsQueue.shift();
          if (bfsVisited.has(id)) continue;
          bfsVisited.add(id);
          const p = positions.get(id);
          if (!p) continue;
          if (Math.abs(p.x - trunkX) < STRAIGHT_THRESHOLD) continue;
          if (!stackedNodeIds.has(id) || p.x < sgTrunkX) continue;
          spineBottom = Math.max(spineBottom, p.rowBottom || p.visualBottom);
          const node = visibleMap.get(id);
          for (const nid of (node?.nextIds || [])) {
            if (!bfsVisited.has(nid) && positions.has(nid)) bfsQueue.push(nid);
          }
        }
        const lastDepth = depthMap.get(displayOrder[displayOrder.length - 1]) || 0;
        // Don't fade the spine if a return curve will connect at its bottom.
        const fade = willDrawZoneReturn ? false : lastDepth > 0;
        indentSpines.push({
          x: Math.round(sgTrunkX), top: firstPos.y,
          height: spineBottom - firstPos.y, depth: 0, fade
        });
      }
    }

    if (hasTerminalReturn) groupHasTerminalReturn.set(sg, true);

    // Zone-to-main-trunk return: when the zone's internal return was
    // skipped (all zone nodes at the same indent depth → zone trunk IS
    // their X) but the zone trunk itself is off the main trunk, draw a
    // return curve from the zone trunk back to the main trunk.
    if (willDrawZoneReturn && zoneLastPos) {
      const rowBottom = zoneLastPos.rowBottom || zoneLastPos.visualBottom;

      // Horizontal range the return curve will cross
      const minHX = Math.min(sgTrunkX, trunkX);
      const maxHX = Math.max(sgTrunkX, trunkX);

      // Find the lowest card bottom in the horizontal path that extends
      // below the zone's last row.  This ensures the horizontal leg of the
      // return curve clears ALL cards between sgTrunkX and trunkX — not
      // just those aligned with the main trunk.
      let clearBelow = rowBottom;
      for (const [, pos] of positions) {
        if (pos.x >= minHX && pos.x <= maxHX && pos.rowBottom > rowBottom) {
          if (pos.rowBottom > clearBelow) clearBelow = pos.rowBottom;
        }
      }

      // Find the next card top below the clearance line (from any node,
      // not just trunk-aligned) to center the merge point in the gap.
      let nextCardTopBelow = null;
      for (const [, pos] of positions) {
        if (pos.cardTop > clearBelow) {
          if (nextCardTopBelow === null || pos.cardTop < nextCardTopBelow) {
            nextCardTopBelow = pos.cardTop;
          }
        }
      }

      const mergeY = nextCardTopBelow !== null
        ? Math.round(clearBelow + (nextCardTopBelow - clearBelow) / 2)
        : Math.round(clearBelow + FORK_BRANCH_GAP);

      const dirX = trunkX > sgTrunkX ? -1 : 1;
      const radius = Math.min(
        MAX_CORNER_RADIUS,
        Math.abs(trunkX - sgTrunkX) / 2,
        Math.max(0, Math.abs(mergeY - rowBottom) - RADIUS_ADJUST)
      );

      allPathData.push(
        `M ${sgTrunkX} ${rowBottom} ` +
        `L ${sgTrunkX} ${mergeY - radius} ` +
        `Q ${sgTrunkX} ${mergeY} ${sgTrunkX - radius * dirX} ${mergeY} ` +
        `L ${trunkX + radius * dirX} ${mergeY} ` +
        `Q ${trunkX} ${mergeY} ${trunkX} ${mergeY + radius} `
      );
      groupHasTerminalReturn.set(sg, true);
    }
  });

  // Build stacked↔non-stacked edge routing maps
  const nodeToGroup = new Map();
  const groupFirst = new Map();
  const groupLast = new Map();
  const groupSg = new Map();
  let groupIdx = 0;
  stackGroups.forEach(sg => {
    const rows = sg.querySelectorAll(':scope > .node-row');
    const ids = Array.from(rows).map(r => r.dataset.id).filter(Boolean);
    if (ids.length === 0) return;
    const gi = groupIdx++;
    ids.forEach(id => nodeToGroup.set(id, gi));
    groupFirst.set(gi, ids[0]);
    groupLast.set(gi, ids[ids.length - 1]);
    groupSg.set(gi, sg);
  });

  const visibleIdSet = new Set(visibleNodes.map(n => n.id));
  const drawnEdgeKeys = new Set();

  visibleNodes.forEach(node => {
    const srcStacked = stackedNodeIds.has(node.id);
    const srcGroup = nodeToGroup.get(node.id);
    if (srcStacked && node.id !== groupLast.get(srcGroup)) return;

    (node.nextIds || []).forEach(nextId => {
      if (!positions.has(nextId)) return;
      const tgtStacked = stackedNodeIds.has(nextId);
      const tgtGroup = nodeToGroup.get(nextId);
      if (srcStacked && tgtStacked && srcGroup === tgtGroup) return;
      if (srcStacked && !tgtStacked) {
        const sg = groupSg.get(srcGroup);
        if (sg && groupHasTerminalReturn.has(sg)) return;
      }

      let effectiveTarget = tgtStacked ? groupFirst.get(tgtGroup) : nextId;
      const effectiveSource = srcStacked ? groupLast.get(srcGroup) : node.id;
      if (!effectiveTarget || !effectiveSource) return;

      const srcPos = positions.get(effectiveSource);
      let tgtPos = positions.get(effectiveTarget);
      if (srcPos && tgtPos) {
        const srcBottom = srcPos.cardBottom || srcPos.visualBottom;
        if (tgtPos.cardTop <= srcBottom) {
          if (effectiveTarget !== nextId) {
            const actualTgtPos = positions.get(nextId);
            if (actualTgtPos && actualTgtPos.cardTop > srcBottom) {
              effectiveTarget = nextId;
              tgtPos = actualTgtPos;
            } else { return; }
          } else { return; }
        }
      }

      const edgeKey = `${effectiveSource}->${effectiveTarget}`;
      if (drawnEdgeKeys.has(edgeKey)) return;
      drawnEdgeKeys.add(edgeKey);
      allPathData.push(drawEdgePath(effectiveSource, effectiveTarget, positions, { trunkX }));
    });
  });

  // First-row branches: stack groups whose entry node has no visible
  // predecessor need an explicit branch from the main trunk.
  stackGroups.forEach(sg => {
    const firstRow = sg.querySelector(':scope > .node-row');
    if (!firstRow) return;
    const firstId = firstRow.dataset.id;
    if (!firstId || !positions.has(firstId)) return;
    const node = DataStore.map.get(firstId);
    if (!node) return;
    if ((node.prevIds || []).some(pid => visibleIdSet.has(pid))) return;
    const pos = positions.get(firstId);
    if (Math.abs(pos.x - trunkX) < STRAIGHT_THRESHOLD) return;

    const bendY = Math.round(pos.cardTop - FORK_BRANCH_GAP);
    const dirX = pos.x > trunkX ? 1 : -1;
    const dx = Math.abs(pos.x - trunkX);
    const vSpace = Math.max(0, pos.y - bendY);
    const r = Math.min(MAX_CORNER_RADIUS, dx / 2, Math.max(0, vSpace - RADIUS_ADJUST));
    forkPathData.push(
      `M ${trunkX} ${bendY - r} ` +
      `Q ${trunkX} ${bendY} ${trunkX + r * dirX} ${bendY} ` +
      `L ${pos.x - r * dirX} ${bendY} ` +
      `Q ${pos.x} ${bendY} ${pos.x} ${bendY + r} ` +
      `L ${pos.x} ${pos.y + SVG_OVERLAP} `
    );
  });

  // First-row branches for non-stacked off-spine nodes with no visible
  // predecessors.  In pure parallel mode, svg-engine.js handles this;
  // in partially-stacked mode, the pure-parallel code path doesn't run,
  // so we must replicate the logic here for any non-stacked parallel
  // node that sits off-trunk and has no predecessor edge reaching it.
  visibleNodes.forEach(node => {
    if (stackedNodeIds.has(node.id)) return;
    if ((node.prevIds || []).some(pid => visibleIdSet.has(pid))) return;
    const pos = positions.get(node.id);
    if (!pos || Math.abs(pos.x - trunkX) < STRAIGHT_THRESHOLD) return;

    const bendY = Math.round(pos.cardTop - FORK_BRANCH_GAP);
    const dirX = pos.x > trunkX ? 1 : -1;
    const dx = Math.abs(pos.x - trunkX);
    const vSpace = Math.max(0, pos.y - bendY);
    const r = Math.min(MAX_CORNER_RADIUS, dx / 2, Math.max(0, vSpace - RADIUS_ADJUST));
    forkPathData.push(
      `M ${trunkX} ${bendY - r} ` +
      `Q ${trunkX} ${bendY} ${trunkX + r * dirX} ${bendY} ` +
      `L ${pos.x - r * dirX} ${bendY} ` +
      `Q ${pos.x} ${bendY} ${pos.x} ${bendY + r} ` +
      `L ${pos.x} ${pos.y + SVG_OVERLAP} `
    );
  });

  drawTerminalReturns(visibleNodes, visibleIdSet, positions, trunkX,
                      visualRows, nodeToRowIdx, stackedNodeIds, allPathData);
  indentSpines.push(...buildColumnSpines(visibleNodes, positions, trunkX, stackedNodeIds));
}
