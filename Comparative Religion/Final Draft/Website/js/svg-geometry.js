/* === svg-geometry.js — Marker Collection & Transition Metrics === */
/**
 * Collects node marker positions from the DOM and computes visual row
 * groupings and transition geometry for SVG connector drawing.
 *
 * Dependencies: constants.js (SPINE_FADE_PX, STRAIGHT_THRESHOLD,
 *               MAX_CORNER_RADIUS, SPINE_HALF_W)
 * Consumers:    svg-engine.js, svg-paths.js, svg-stacked.js, svg-partial.js
 */

import {
  SPINE_FADE_PX,
  STRAIGHT_THRESHOLD,
  MAX_CORNER_RADIUS,
  SPINE_HALF_W,
  ROW_BUCKET_PX,
  RADIUS_ADJUST
} from './constants.js';

// Re-export so existing consumers that import from svg-geometry.js keep working
export { SPINE_FADE_PX, STRAIGHT_THRESHOLD, MAX_CORNER_RADIUS, SPINE_HALF_W };

/* ---------------------------------------------------------------------------
 * Marker positions
 * --------------------------------------------------------------------------- */

/**
 * Measures all node marker dot positions and card bounding boxes from the
 * live DOM, returning a position map used by all SVG drawing routines.
 *
 * When an open expander exists in a level-group, ALL sibling nodes in that
 * group receive the expander's bottom as their visualBottom so downstream
 * visual-row grouping accounts for the extra height uniformly.
 *
 * @param {HTMLElement} viewEl - the `.map-flow` element containing node cards
 * @param {DOMRect} containerRect - bounding rect of the viewEl (for coordinate offset)
 * @returns {Map<string, {x: number, y: number, depth: number, cardTop: number, cardBottom: number, visualBottom: number}>}
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

    // The card may have a CSS hover transform (e.g. translateY(-2px)) that
    // shifts its bounding rect away from its layout position.  SVG connectors
    // must use the resting (non-hovered) position so branches don't shift
    // depending on whether the mouse happens to be over the card during redraw.
    let cardYShift = 0;
    const ct = getComputedStyle(card).transform;
    if (ct && ct !== 'none') {
      const m = ct.match(/matrix3d\((.+)\)/) || ct.match(/matrix\((.+)\)/);
      if (m) {
        const v = m[1].split(',').map(Number);
        cardYShift = v.length === 16 ? (v[13] || 0) : (v[5] || 0);
      }
    }

    positions.set(id, {
      // Integer CSS pixels for SVG path generation — keeps curve control points
      // at clean coordinates so anti-aliasing stays consistent across DPRs.
      // HTML spine divs do their own device-pixel snapping independently.
      x: Math.round(rawX),
      y: dotRect.top - containerRect.top + dotRect.height / 2,
      depth,
      cardTop: cardRect.top - containerRect.top - cardYShift,
      cardBottom: cardRect.bottom - containerRect.top - cardYShift,
      visualBottom: cardRect.bottom - containerRect.top - cardYShift
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
 * Groups node markers into visual rows by Y-coordinate bucketing. Markers
 * whose cardTop values fall within ROW_BUCKET_PX pixels of each other are
 * placed in the same visual row. Each row tracks the maximum bottom Y so
 * downstream gap calculations know where the row ends.
 *
 * @param {HTMLElement} viewEl - the `.map-flow` element
 * @param {Map<string, Object>} positions - marker positions from collectMarkerPositions
 * @returns {{ visualRows: Array<{nodeIds: string[], bottom: number}>, nodeToRowIdx: Map<string, number> }}
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

      const bucket = Math.round(pos.cardTop / ROW_BUCKET_PX) * ROW_BUCKET_PX;
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
 * Computes the curve geometry between two connected visual rows. Determines
 * the vertical midpoint where branch curves bend (joinY) and the appropriate
 * corner radius.
 *
 * @param {string} startId - source node ID
 * @param {string} endId - target node ID
 * @param {Map<string, Object>} positions - marker positions
 * @returns {{ joinY: number, radius: number, gapTop: number, gapBottom: number, gap: number } | null}
 *   joinY is the Y-coordinate where a branch curve meets the trunk (the bend point)
 */
export function getTransitionMetrics(startId, endId, positions) {
  const start = positions.get(startId);
  const end = positions.get(endId);
  if (!start || !end) return null;

  // "Gap" is the vertical whitespace between two connected rows — the space
  // where SVG curves bend. Multiple gap values handle edge cases:
  //   - gapTop: bottom edge of the source row (accounts for expanders)
  //   - effectiveGapTop: adjusted for intervening rows that extend below gapTop
  //   - gapBottom: top edge of the target node's card
  //   - gap: the actual usable vertical space for the curve bend
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
  // branchBendY: the Y-coordinate where branch curves meet the horizontal segment
  const branchBendY = effectiveGapTop + gap / 2;

  // Guard: if any position measurement was missing or produced non-finite values
  // (e.g. during mid-transition DOM states), bail out so callers skip this edge.
  if (!Number.isFinite(branchBendY)) return null;

  const dx = Math.abs(end.x - start.x);
  // Radius is constrained by three factors to ensure the curve always fits:
  //   1. MAX_CORNER_RADIUS — aesthetic cap so curves don't become too round
  //   2. dx / 2 — can't exceed half the horizontal distance (curves would overlap)
  //   3. gap / 2 - RADIUS_ADJUST/2 — can't exceed half the vertical gap (curves would clip into cards)
  const radius = dx < STRAIGHT_THRESHOLD
    ? 0
    : Math.min(MAX_CORNER_RADIUS, dx / 2, Math.max(0, gap / 2 - RADIUS_ADJUST / 2));

  return { joinY: branchBendY, radius, gapTop: effectiveGapTop, gapBottom, gap };
}

/* ---------------------------------------------------------------------------
 * Branch radius
 * --------------------------------------------------------------------------- */

/**
 * Computes the corner radius for a branch curve (enter or return).
 * The radius is constrained by horizontal distance, vertical distance from
 * each dot center to the bend point, and the MAX_CORNER_RADIUS cap — ensuring
 * the curve always fits within the available space without clipping nodes.
 *
 * @param {string} startId - source node ID
 * @param {string} endId - target node ID
 * @param {Map<string, Object>} positions - marker positions
 * @returns {number} corner radius in pixels
 */
export function getBranchRadius(startId, endId, positions) {
  const start = positions.get(startId);
  const end = positions.get(endId);
  const metrics = getTransitionMetrics(startId, endId, positions);
  if (!start || !end || !metrics) return 0;

  const dx = Math.abs(end.x - start.x);
  if (dx < STRAIGHT_THRESHOLD) return 0;

  const y = metrics.joinY;
  // Guard: if joinY is somehow missing or non-finite, bail out to avoid NaN
  // propagating through all downstream path arithmetic.
  if (!Number.isFinite(y)) return 0;

  const startVertical = Math.max(0, y - start.y);
  const endVertical = Math.max(0, end.y - y);

  return Math.min(
    MAX_CORNER_RADIUS,
    dx / 2,
    Math.max(0, startVertical - RADIUS_ADJUST),
    Math.max(0, endVertical - RADIUS_ADJUST)
  );
}
