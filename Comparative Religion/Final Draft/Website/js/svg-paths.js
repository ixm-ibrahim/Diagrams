/* === svg-paths.js — SVG Path Drawing & Parallel Helpers === */
/**
 * Generates SVG path strings for branch/merge connectors, general edges,
 * terminal return curves, and parallel column spines.
 *
 * Dependencies: svg-geometry.js
 * Consumers:    svg-engine.js, svg-stacked.js, svg-partial.js
 */

import { SVG_OVERLAP, FORK_BRANCH_GAP, RADIUS_ADJUST, MIN_SPINE_HEIGHT } from './constants.js';
import {
  STRAIGHT_THRESHOLD, MAX_CORNER_RADIUS,
  getTransitionMetrics, getBranchRadius
} from './svg-geometry.js';

/* ---------------------------------------------------------------------------
 * Branch / merge path
 * --------------------------------------------------------------------------- */

/**
 * Generates an SVG path for a branch-enter or branch-return connector.
 * Draws ONLY the curved + horizontal portion — no vertical segments.
 */
function drawBranchPath(startId, endId, positions) {
  const metrics = getTransitionMetrics(startId, endId, positions);
  const start = positions.get(startId);
  const end = positions.get(endId);
  if (!metrics || !start || !end) return '';

  const r = getBranchRadius(startId, endId, positions);
  if (r <= 0) {
    return `M ${start.x} ${metrics.joinY} L ${end.x} ${metrics.joinY} `;
  }

  const dirX = end.x > start.x ? 1 : -1;
  const y = metrics.joinY;

  return [
    `M ${start.x} ${y - r - SVG_OVERLAP}`,
    `L ${start.x} ${y - r}`,
    `Q ${start.x} ${y} ${start.x + dirX * r} ${y}`,
    `L ${end.x - dirX * r} ${y}`,
    `Q ${end.x} ${y} ${end.x} ${y + r}`,
    `L ${end.x} ${y + r + SVG_OVERLAP}`,
  ].join(' ') + ' ';
}

/* ---------------------------------------------------------------------------
 * General edge path
 * --------------------------------------------------------------------------- */

/**
 * Generates an SVG path for a general edge (straight or L-shaped with curves).
 */
export function drawEdgePath(startId, endId, positions, options = {}) {
  const start = positions.get(startId);
  const end = positions.get(endId);
  if (!start || !end) return '';

  const {
    startAtSpine = false,
    endAtSpine = false,
    kind = 'flow',
    trunkX = null
  } = options;

  if (kind === 'branch-enter' || kind === 'branch-return') {
    return drawBranchPath(startId, endId, positions);
  }

  const hasSpineAt = (x) => trunkX !== null && Math.abs(x - trunkX) < STRAIGHT_THRESHOLD;

  const metrics = getTransitionMetrics(startId, endId, positions);
  const bendY = (metrics && Math.abs(start.x - end.x) >= STRAIGHT_THRESHOLD)
    ? metrics.joinY
    : null;

  if (bendY === null) {
    if (hasSpineAt(start.x)) return '';
    return `M ${start.x} ${start.y} L ${end.x} ${end.y} `;
  }

  const dirX = end.x > start.x ? 1 : -1;
  const startVertical = Math.max(0, bendY - start.y);
  const endVertical = Math.max(0, end.y - bendY);
  const radius = Math.min(
    MAX_CORNER_RADIUS,
    Math.abs(end.x - start.x) / 2,
    startAtSpine ? MAX_CORNER_RADIUS : Math.max(0, startVertical - RADIUS_ADJUST),
    endAtSpine ? MAX_CORNER_RADIUS : Math.max(0, endVertical - RADIUS_ADJUST)
  );

  let d = '';

  if (!hasSpineAt(start.x)) {
    d += `M ${start.x} ${start.y} L ${start.x} ${bendY - radius} `;
  } else {
    d += `M ${start.x} ${bendY - radius} `;
  }

  d += `Q ${start.x} ${bendY} ${start.x + radius * dirX} ${bendY} `;
  d += `L ${end.x - radius * dirX} ${bendY} `;
  d += `Q ${end.x} ${bendY} ${end.x} ${bendY + radius} `;

  if (!hasSpineAt(end.x)) {
    d += `L ${end.x} ${end.y} `;
  }

  return d;
}

/* ---------------------------------------------------------------------------
 * Terminal return curves (Rule 2 — parallel merge)
 * --------------------------------------------------------------------------- */

/**
 * Draws return curves for parallel nodes that have no visible successors
 * and are horizontally offset from the trunk.
 */
export function drawTerminalReturns(visibleNodes, visibleIdSet, positions, trunkX,
                                    visualRows, nodeToRowIdx, excludeIds, allPathData) {
  const terminalOffSpine = visibleNodes.filter(node => {
    if (excludeIds.has(node.id)) return false;
    if (node.nextIds?.some(nid => visibleIdSet.has(nid))) return false;
    const pos = positions.get(node.id);
    return pos && Math.abs(pos.x - trunkX) >= STRAIGHT_THRESHOLD;
  });

  if (terminalOffSpine.length === 0) return;

  const byX = new Map();
  for (const node of terminalOffSpine) {
    const pos = positions.get(node.id);
    const xKey = Math.round(pos.x);
    if (!byX.has(xKey) || pos.y > byX.get(xKey).y) {
      byX.set(xKey, pos);
    }
  }

  // Compute maxRowBottom only from the off-spine terminal nodes, not ALL
  // terminal nodes.  Including on-trunk terminals (like a successor node
  // that sits on the spine below the fork) inflates maxRowBottom, pushing
  // the merge point past nodes that should appear AFTER the return.
  let maxRowBottom = 0;
  for (const node of terminalOffSpine) {
    const pos = positions.get(node.id);
    if (pos) maxRowBottom = Math.max(maxRowBottom, pos.rowBottom);
  }

  // Compute the full horizontal range the return lines will span (from
  // all off-spine columns to trunkX). Any card in this range whose bottom
  // extends below maxRowBottom must be cleared.
  let minHX = trunkX, maxHX = trunkX;
  for (const [, pos] of byX) {
    if (pos.x < minHX) minHX = pos.x;
    if (pos.x > maxHX) maxHX = pos.x;
  }
  let clearBelow = maxRowBottom;
  for (const [, pos] of positions) {
    if (pos.x >= minHX && pos.x <= maxHX && pos.rowBottom > maxRowBottom) {
      if (pos.rowBottom > clearBelow) clearBelow = pos.rowBottom;
    }
  }

  // Find the next card top below the clearance line (from any node) so
  // the merge point is centered in the gap. Fall back to FORK_BRANCH_GAP
  // when no card exists below (true page-terminal case).
  let nextTrunkCardTop = null;
  for (const [, pos] of positions) {
    if (pos.cardTop > clearBelow) {
      if (nextTrunkCardTop === null || pos.cardTop < nextTrunkCardTop) {
        nextTrunkCardTop = pos.cardTop;
      }
    }
  }
  const mergeY = nextTrunkCardTop !== null
    ? Math.round(clearBelow + (nextTrunkCardTop - clearBelow) / 2)
    : Math.round(clearBelow + FORK_BRANCH_GAP);

  for (const [, pos] of byX) {
    const dirX = trunkX > pos.x ? 1 : -1;
    const radius = Math.min(
      MAX_CORNER_RADIUS,
      Math.abs(trunkX - pos.x) / 2,
      Math.max(0, Math.abs(mergeY - pos.y) - RADIUS_ADJUST)
    );

    allPathData.push(
      `M ${pos.x} ${pos.y} ` +
      `L ${pos.x} ${mergeY - radius} ` +
      `Q ${pos.x} ${mergeY} ${pos.x + radius * dirX} ${mergeY} ` +
      `L ${trunkX - radius * dirX} ${mergeY} ` +
      `Q ${trunkX} ${mergeY} ${trunkX} ${mergeY + radius} `
    );
  }
}

/* ---------------------------------------------------------------------------
 * Parallel column spines (Rule 4 analog for parallel layout)
 * --------------------------------------------------------------------------- */

/**
 * Builds HTML spine elements for non-trunk parallel nodes that own a subtree.
 * A "column spine" acts as a local trunk for a node's descendant subtree.
 * BFS stops at trunk nodes (merge/convergence points).
 */
export function buildColumnSpines(visibleNodes, positions, trunkX, excludeIds = new Set()) {
  const spines = [];
  const visibleMap = new Map(visibleNodes.map(n => [n.id, n]));
  const visibleIdSet = new Set(visibleNodes.map(n => n.id));

  const columnRoots = [];
  for (const node of visibleNodes) {
    if (excludeIds.has(node.id)) continue;
    const pos = positions.get(node.id);
    if (!pos) continue;
    if (Math.abs(pos.x - trunkX) < STRAIGHT_THRESHOLD) continue;

    const hasOffTrunkChild = (node.nextIds || []).some(nid => {
      const cPos = positions.get(nid);
      return cPos && Math.abs(cPos.x - trunkX) >= STRAIGHT_THRESHOLD;
    });
    if (!hasOffTrunkChild) continue;
    columnRoots.push(node);
  }

  if (columnRoots.length === 0) return spines;

  const columns = new Map();
  for (const node of columnRoots) {
    const pos = positions.get(node.id);
    const xKey = Math.round(pos.x);
    if (!columns.has(xKey)) {
      columns.set(xKey, { x: pos.x, rootIds: [], minY: Infinity, maxBottom: 0 });
    }
    const col = columns.get(xKey);
    col.rootIds.push(node.id);
    col.minY = Math.min(col.minY, pos.y);
    col.maxBottom = Math.max(col.maxBottom, pos.visualBottom);
  }

  for (const [, col] of columns) {
    const visited = new Set(col.rootIds);
    const queue = [];
    let maxBottom = col.maxBottom;

    for (const rootId of col.rootIds) {
      const node = visibleMap.get(rootId);
      for (const nid of (node?.nextIds || [])) {
        if (visibleIdSet.has(nid) && !visited.has(nid)) queue.push(nid);
      }
    }

    while (queue.length > 0) {
      const id = queue.shift();
      if (visited.has(id)) continue;
      visited.add(id);

      const p = positions.get(id);
      if (!p) continue;
      if (Math.abs(p.x - trunkX) < STRAIGHT_THRESHOLD) continue;

      const isSameX = Math.abs(p.x - col.x) < STRAIGHT_THRESHOLD;
      const isStacked = excludeIds.has(id);

      let shouldExtend = isSameX;
      let shouldTraverse = isSameX;

      if (isStacked && !isSameX) {
        if (p.x >= col.x) {
          shouldExtend = true;
          shouldTraverse = true;
        }
      }

      if (shouldExtend) {
        maxBottom = Math.max(maxBottom, p.rowBottom || p.visualBottom);
      }
      if (!shouldTraverse) continue;

      const n = visibleMap.get(id);
      for (const nid of (n?.nextIds || [])) {
        if (visibleIdSet.has(nid) && !visited.has(nid)) queue.push(nid);
      }
    }

    if (maxBottom <= col.maxBottom) continue;

    const height = maxBottom - col.minY;
    if (height > MIN_SPINE_HEIGHT) {
      spines.push({
        x: Math.round(col.x),
        top: col.minY,
        height,
        depth: 0,
        fade: true
      });
    }
  }

  return spines;
}
