/* === svg-partial.js — Partial Stacking Edge Routing === */
/**
 * Handles the mixed parallel+stacked layout case: processes each
 * stack-group zone, builds zone trunk spines, and routes edges
 * across stacked/non-stacked boundaries.
 *
 * Dependencies: svg-geometry.js, svg-paths.js, svg-stacked.js
 * Consumers:    svg-engine.js
 */

import { STRAIGHT_THRESHOLD } from './svg-geometry.js';
import { drawEdgePath, drawTerminalReturns, buildColumnSpines } from './svg-paths.js';
import { processStackedZone } from './svg-stacked.js';

/**
 * Draws edges and spines for partially-stacked layouts where some
 * level-groups contain stack-groups alongside parallel nodes.
 */
export function drawPartialStacking(stackGroups, viewEl, visibleNodes, positions,
                                    trunkX, indentSpines, allPathData,
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

    processStackedZone(displayOrder, depthMap, positions, sgTrunkX,
                       indentSpines, allPathData,
                       hasTerminalReturn ? trunkX : null);

    // Zone trunk spine when offset from main trunk
    if (Math.abs(sgTrunkX - trunkX) >= STRAIGHT_THRESHOLD) {
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
        indentSpines.push({
          x: Math.round(sgTrunkX), top: firstPos.y,
          height: spineBottom - firstPos.y, depth: 0, fade: lastDepth > 0
        });
      }
    }

    if (hasTerminalReturn) groupHasTerminalReturn.set(sg, true);
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

  drawTerminalReturns(visibleNodes, visibleIdSet, positions, trunkX,
                      visualRows, nodeToRowIdx, stackedNodeIds, allPathData);
  indentSpines.push(...buildColumnSpines(visibleNodes, positions, trunkX, stackedNodeIds));
}
