/* === svg-stacked.js — Stacked Zone Processing (Rules 3–6) === */
/**
 * Computes spine blocks and transitions for stacked/indented node zones,
 * then generates SVG paths and spine info.
 *
 * Dependencies: svg-geometry.js, svg-paths.js
 * Consumers:    svg-engine.js
 */

import { MIN_SPINE_HEIGHT, FORK_BRANCH_GAP } from './constants.js';
import {
  STRAIGHT_THRESHOLD, MAX_CORNER_RADIUS, SPINE_FADE_PX,
  getTransitionMetrics, getBranchRadius
} from './svg-geometry.js';
import { drawEdgePath } from './svg-paths.js';

/* ---------------------------------------------------------------------------
 * Spine block computation
 * --------------------------------------------------------------------------- */

/**
 * Builds contiguous spine blocks for each indent depth level.
 * A spine block is a range of consecutive nodes (in display order) that
 * are all at >= a given depth level.
 */
export function buildSpineBlocks(displayOrder, depthMap) {
  const blocks = [];
  const depthOf = id => depthMap.get(id) || 0;
  const maxDepth = Math.max(...displayOrder.map(depthOf), 0);

  for (let depth = 1; depth <= maxDepth; depth++) {
    let blockStartIndex = -1;

    const flush = endIndex => {
      if (blockStartIndex === -1) return;
      blocks.push({
        depth,
        startId: displayOrder[blockStartIndex],
        endId: displayOrder[endIndex],
        prevId: blockStartIndex > 0 ? displayOrder[blockStartIndex - 1] : null,
        nextId: endIndex < displayOrder.length - 1 ? displayOrder[endIndex + 1] : null
      });
      blockStartIndex = -1;
    };

    displayOrder.forEach((id, idx) => {
      if (depthOf(id) >= depth) {
        if (blockStartIndex === -1) blockStartIndex = idx;
      } else {
        flush(idx - 1);
      }
    });
    flush(displayOrder.length - 1);
  }

  return blocks;
}

/**
 * Builds transitions (branch-enter and branch-return) between consecutive
 * nodes with different indent depths.
 */
export function buildTransitions(displayOrder, depthMap) {
  const transitions = [];
  const depthOf = id => depthMap.get(id) || 0;

  for (let i = 0; i < displayOrder.length - 1; i++) {
    const startId = displayOrder[i];
    const endId = displayOrder[i + 1];
    const startDepth = depthOf(startId);
    const endDepth = depthOf(endId);
    if (startDepth === endDepth) continue;

    transitions.push({
      startId,
      endId,
      kind: endDepth > startDepth ? 'branch-enter' : 'branch-return',
      startAtSpine: endDepth < startDepth,
      endAtSpine: endDepth > startDepth
    });
  }

  return transitions;
}

/* ---------------------------------------------------------------------------
 * Stacked zone processing
 * --------------------------------------------------------------------------- */

/**
 * Processes a stacked zone: computes spine blocks and transitions,
 * then generates SVG paths and spine info.
 *
 * @param {string[]} displayOrder — node IDs in DFS display order
 * @param {Map<string, number>} depthMap — nodeId → indent depth
 * @param {Map<string, Object>} positions — marker positions
 * @param {number} zoneTrunkX — X position of the trunk spine for this zone
 * @param {Array} indentSpines — accumulator for spine info objects
 * @param {Array} allPathData — accumulator for SVG path strings
 * @param {number|null} mainTrunkX — main trunk X for terminal return target
 */
export function processStackedZone(displayOrder, depthMap, positions, zoneTrunkX,
                                   indentSpines, allPathData, mainTrunkX = null) {
  const spineBlocks = buildSpineBlocks(displayOrder, depthMap);
  const transitions = buildTransitions(displayOrder, depthMap);

  // Pre-compute terminal return mergeY so spine bottoms can be capped.
  // Center the merge point in the gap between the last off-spine node and the
  // next trunk node below.  Fall back to FORK_BRANCH_GAP for true terminal cases.
  const termLastId = displayOrder[displayOrder.length - 1];
  const termLastPos = positions.get(termLastId);
  let terminalMergeY = null;
  if (termLastPos && Math.abs(termLastPos.x - zoneTrunkX) >= STRAIGHT_THRESHOLD) {
    const termRowBottom = termLastPos.rowBottom || termLastPos.visualBottom;
    const returnTargetXEarly = mainTrunkX !== null ? mainTrunkX : zoneTrunkX;
    let nextTrunkCardTop = null;
    for (const [, pos] of positions) {
      if (Math.abs(pos.x - returnTargetXEarly) < STRAIGHT_THRESHOLD && pos.cardTop > termRowBottom) {
        if (nextTrunkCardTop === null || pos.cardTop < nextTrunkCardTop) {
          nextTrunkCardTop = pos.cardTop;
        }
      }
    }
    terminalMergeY = nextTrunkCardTop !== null
      ? Math.round(termRowBottom + (nextTrunkCardTop - termRowBottom) / 2)
      : Math.round(termRowBottom + FORK_BRANCH_GAP);
  }

  // Generate indent spine HTML elements (Rule 4 — depth continue)
  spineBlocks.forEach(block => {
    const firstPos = positions.get(block.startId);
    const lastPos = positions.get(block.endId);
    if (!firstPos || !lastPos) return;

    const prevDepth = block.prevId
      ? (positions.get(block.prevId)?.depth ?? depthMap.get(block.prevId) ?? 0) : 0;
    const nextDepth = block.nextId
      ? (positions.get(block.nextId)?.depth ?? depthMap.get(block.nextId) ?? 0) : 0;

    let top = firstPos.y;
    if (block.prevId && prevDepth < block.depth) {
      const r = getBranchRadius(block.prevId, block.startId, positions);
      const entryMetrics = getTransitionMetrics(block.prevId, block.startId, positions);
      if (entryMetrics && r > 0) top = entryMetrics.joinY + r;
    }

    let bottom = lastPos.visualBottom;
    let fade = false;

    if (block.nextId) {
      const exitMetrics = getTransitionMetrics(block.endId, block.nextId, positions);
      if (nextDepth < block.depth) {
        if (exitMetrics) {
          const r = getBranchRadius(block.endId, block.nextId, positions);
          bottom = Math.max(top + MIN_SPINE_HEIGHT, exitMetrics.joinY - r);
          const endDepth = positions.get(block.endId)?.depth ?? depthMap.get(block.endId) ?? block.depth;
          fade = endDepth > block.depth;
        }
      } else if (nextDepth === block.depth) {
        if (exitMetrics) {
          const r = getBranchRadius(block.endId, block.nextId, positions);
          bottom = Math.max(top + MIN_SPINE_HEIGHT, exitMetrics.joinY - r);
        }
        fade = true;
      }
    } else {
      const endDepth = positions.get(block.endId)?.depth ?? depthMap.get(block.endId) ?? block.depth;
      fade = endDepth > block.depth;
      if (terminalMergeY !== null && Math.abs(firstPos.x - zoneTrunkX) >= STRAIGHT_THRESHOLD) {
        const dx = Math.abs(zoneTrunkX - firstPos.x);
        const termR = Math.min(
          MAX_CORNER_RADIUS, dx / 2,
          Math.max(0, Math.abs(terminalMergeY - lastPos.y) - 2)
        );
        bottom = Math.min(bottom, terminalMergeY - termR);
      }
    }

    const height = bottom - top;
    if (height > 0 && Math.abs(firstPos.x - zoneTrunkX) >= STRAIGHT_THRESHOLD) {
      indentSpines.push({ x: Math.round(firstPos.x), top, height, depth: block.depth, fade });
    }
  });

  // Generate SVG branch/merge paths (Rules 3, 5 and 6)
  transitions.forEach(edge => {
    allPathData.push(drawEdgePath(edge.startId, edge.endId, positions, edge));
  });

  // Terminal return curves (Rules 5 & 6): end of display order off-trunk
  const lastId = displayOrder[displayOrder.length - 1];
  const lastPos = positions.get(lastId);
  if (lastPos && Math.abs(lastPos.x - zoneTrunkX) >= STRAIGHT_THRESHOLD) {
    const lastDepth = depthMap.get(lastId) || 0;
    if (lastDepth > 0) {
      let deepestDepth = 0;
      let deepestX = null;
      for (let i = displayOrder.length - 1; i >= 0; i--) {
        const id = displayOrder[i];
        const d = depthMap.get(id) || 0;
        if (d === 0) break;
        const pos = positions.get(id);
        if (pos && d > deepestDepth) { deepestDepth = d; deepestX = pos.x; }
      }

      const rowBottomOfLast = lastPos.rowBottom || lastPos.visualBottom;
      const returnTargetX = mainTrunkX !== null ? mainTrunkX : zoneTrunkX;

      // Center merge point in the gap between last off-spine node and next
      // trunk node.  Fall back to FORK_BRANCH_GAP for true terminal cases.
      let nextTrunkCardTop2 = null;
      for (const [, pos] of positions) {
        if (Math.abs(pos.x - returnTargetX) < STRAIGHT_THRESHOLD && pos.cardTop > rowBottomOfLast) {
          if (nextTrunkCardTop2 === null || pos.cardTop < nextTrunkCardTop2) {
            nextTrunkCardTop2 = pos.cardTop;
          }
        }
      }
      const mergeY = nextTrunkCardTop2 !== null
        ? Math.round(rowBottomOfLast + (nextTrunkCardTop2 - rowBottomOfLast) / 2)
        : Math.round(rowBottomOfLast + FORK_BRANCH_GAP);

      if (deepestX !== null && Math.abs(deepestX - returnTargetX) >= STRAIGHT_THRESHOLD) {
        const dirX = returnTargetX > deepestX ? 1 : -1;
        const radius = Math.min(
          MAX_CORNER_RADIUS,
          Math.abs(returnTargetX - deepestX) / 2,
          Math.max(0, Math.abs(mergeY - lastPos.y) - 2)
        );

        // Start from the last node's visualBottom so the path connects
        // seamlessly with the indent spine above (no gap).
        allPathData.push(
          `M ${deepestX} ${rowBottomOfLast} ` +
          `L ${deepestX} ${mergeY - radius} ` +
          `Q ${deepestX} ${mergeY} ${deepestX + radius * dirX} ${mergeY} ` +
          `L ${returnTargetX - radius * dirX} ${mergeY} ` +
          `Q ${returnTargetX} ${mergeY} ${returnTargetX} ${mergeY + radius} `
        );
      }
    }
  }
}
