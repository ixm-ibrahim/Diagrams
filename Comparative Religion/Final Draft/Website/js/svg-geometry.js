/* === svg-geometry.js — Marker Collection & Transition Metrics === */
/**
 * Collects node marker positions from the DOM and computes visual row
 * groupings and transition geometry for SVG connector drawing.
 *
 * Dependencies: constants.js (SPINE_FADE_PX, STRAIGHT_THRESHOLD,
 *               MAX_CORNER_RADIUS, SPINE_HALF_W)
 * Consumers:    svg-engine.js, svg-paths.js, svg-stacked.js
 */

import {
  SPINE_FADE_PX,
  STRAIGHT_THRESHOLD,
  MAX_CORNER_RADIUS,
  SPINE_HALF_W
} from './constants.js';

// Re-export so existing consumers that import from svg-geometry.js keep working
export { SPINE_FADE_PX, STRAIGHT_THRESHOLD, MAX_CORNER_RADIUS, SPINE_HALF_W };

/* ---------------------------------------------------------------------------
 * Marker positions
 * --------------------------------------------------------------------------- */

/**
 * Collects marker dot positions and card bounds for every visible node.
 * Returns a Map<nodeId, {x, y, depth, cardTop, cardBottom, visualBottom}>.
 *
 * When an open expander exists in a level-group, ALL sibling nodes in that
 * group receive the expander's bottom as their visualBottom so downstream
 * visual-row grouping accounts for the extra height uniformly.
 */
export function collectMarkerPositions(viewEl, containerRect) {
  const positions = new Map();
  const rows = viewEl.querySelectorAll('.node-row');

  rows.forEach(row => {
    const id = row.dataset.id;
    if (!id) return;

    const dot = row.querySelector('.marker-dot');
    const card = row.querySelector('.node-card');
    if (!dot || !card) return;

    const dotRect = dot.getBoundingClientRect();
    const cardRect = card.getBoundingClientRect();

    if (dotRect.width === 0 && dotRect.height === 0) return;

    const depth = parseInt(row.style.getPropertyValue('--indent-depth')) || 0;

    const rawX = dotRect.left - containerRect.left + dotRect.width / 2;

    positions.set(id, {
      // Integer CSS pixels for SVG path generation — keeps curve control points
      // at clean coordinates so anti-aliasing stays consistent across DPRs.
      // HTML spine divs do their own device-pixel snapping independently.
      x: Math.round(rawX),
      y: dotRect.top - containerRect.top + dotRect.height / 2,
      depth,
      cardTop: cardRect.top - containerRect.top,
      cardBottom: cardRect.bottom - containerRect.top,
      visualBottom: cardRect.bottom - containerRect.top
    });
  });

  // Propagate open-expander height to ALL sibling nodes in the same
  // level-group so visual-row computation shifts uniformly.
  const levelGroups = viewEl.querySelectorAll('.level-group:not([data-zone-absorbed])');
  levelGroups.forEach(group => {
    const openExp = group.querySelector('.level-expander.is-open');
    if (!openExp) return;

    const expInner = openExp.querySelector('.exp-inner');
    if (!expInner) return;

    const expRect = expInner.getBoundingClientRect();
    if (expRect.height < 1) return;

    const expBottom = expRect.bottom - containerRect.top;

    const nodeRows = group.querySelectorAll(
      ':scope > .node-row, :scope > .stack-group > .node-row'
    );
    nodeRows.forEach(row => {
      const id = row.dataset.id;
      const pos = positions.get(id);
      if (pos && expBottom > pos.visualBottom) {
        pos.visualBottom = expBottom;
      }
    });
  });

  return positions;
}

/* ---------------------------------------------------------------------------
 * Visual rows
 * --------------------------------------------------------------------------- */

/**
 * Builds visual row groups from level-groups in the DOM.
 * Each visual row contains the node IDs and the maximum bottom Y coordinate.
 * Returns { visualRows, nodeToRowIdx }.
 */
export function buildVisualRows(viewEl, positions) {
  const visualRows = [];
  const nodeToRowIdx = new Map();

  const levelGroups = viewEl.querySelectorAll('.level-group:not([data-zone-absorbed])');

  levelGroups.forEach(group => {
    const nodeRows = group.querySelectorAll(':scope > .node-row, :scope > .stack-group > .node-row');
    if (nodeRows.length === 0) return;

    const rowBuckets = new Map();
    nodeRows.forEach(row => {
      const id = row.dataset.id;
      const pos = positions.get(id);
      if (!pos) return;

      const bucket = Math.round(pos.cardTop / 5) * 5;
      if (!rowBuckets.has(bucket)) rowBuckets.set(bucket, []);
      rowBuckets.get(bucket).push(id);
    });

    const sortedBuckets = [...rowBuckets.entries()].sort((a, b) => a[0] - b[0]);
    sortedBuckets.forEach(([, ids]) => {
      let maxBottom = 0;
      ids.forEach(id => {
        const pos = positions.get(id);
        if (pos) maxBottom = Math.max(maxBottom, pos.visualBottom);
      });

      const rowIdx = visualRows.length;
      visualRows.push({ nodeIds: ids, bottom: maxBottom });
      ids.forEach(id => nodeToRowIdx.set(id, rowIdx));
    });
  });

  // Annotate positions with row-level bottom
  for (const [id, pos] of positions) {
    const idx = nodeToRowIdx.get(id);
    pos.rowBottom = idx !== undefined ? visualRows[idx].bottom : pos.visualBottom;
    pos.prevRowBottom = idx > 0 ? visualRows[idx - 1].bottom : null;
  }

  return { visualRows, nodeToRowIdx };
}

/* ---------------------------------------------------------------------------
 * Transition metrics
 * --------------------------------------------------------------------------- */

/**
 * Computes the transition geometry between two nodes.
 * Returns { joinY, radius, gapTop, gapBottom, gap } or null.
 */
export function getTransitionMetrics(startId, endId, positions) {
  const start = positions.get(startId);
  const end = positions.get(endId);
  if (!start || !end) return null;

  const gapTop = start.rowBottom !== undefined ? start.rowBottom : start.visualBottom;

  let effectiveGapTop = (end.prevRowBottom !== undefined && end.prevRowBottom > gapTop)
    ? end.prevRowBottom
    : gapTop;

  const gapBottom = end.cardTop;

  if (gapBottom < effectiveGapTop) {
    effectiveGapTop = start.cardBottom !== undefined
      ? start.cardBottom
      : start.visualBottom;
  }

  const gap = Math.max(0, gapBottom - effectiveGapTop);
  const joinY = effectiveGapTop + gap / 2;

  const dx = Math.abs(end.x - start.x);
  const radius = dx < STRAIGHT_THRESHOLD
    ? 0
    : Math.min(MAX_CORNER_RADIUS, dx / 2, Math.max(0, gap / 2 - 1));

  return { joinY, radius, gapTop: effectiveGapTop, gapBottom, gap };
}

/* ---------------------------------------------------------------------------
 * Branch radius
 * --------------------------------------------------------------------------- */

/**
 * Computes the radius for a branch-enter or branch-return curve.
 * Constrained by horizontal distance and vertical distance from dot
 * centers to the bend point.
 */
export function getBranchRadius(startId, endId, positions) {
  const start = positions.get(startId);
  const end = positions.get(endId);
  const metrics = getTransitionMetrics(startId, endId, positions);
  if (!start || !end || !metrics) return 0;

  const dx = Math.abs(end.x - start.x);
  if (dx < STRAIGHT_THRESHOLD) return 0;

  const y = metrics.joinY;
  const startVertical = Math.max(0, y - start.y);
  const endVertical = Math.max(0, end.y - y);

  return Math.min(
    MAX_CORNER_RADIUS,
    dx / 2,
    Math.max(0, startVertical - 2),
    Math.max(0, endVertical - 2)
  );
}
