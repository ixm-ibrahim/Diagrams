/**
 * =============================================================================
 * svg-paths.js — SVG Path Math
 * =============================================================================
 * Pure functions that compute SVG path strings from marker positions.
 * No DOM access, no side effects — these are testable with hardcoded inputs.
 *
 * Dependencies: constants.js (STRAIGHT_THRESHOLD, MAX_CORNER_RADIUS)
 * Consumers: svg-engine.js
 * =============================================================================
 */

import { STRAIGHT_THRESHOLD, MAX_CORNER_RADIUS } from './constants.js';

/**
 * Computes the bend-point metrics for an edge between two marker positions.
 *
 * @param {Map} markerPositions
 * @param {string} startId
 * @param {string} endId
 * @returns {Object|null} { start, end, gapTop, gapBottom, gap, joinY, radius }
 */
export function getTransitionMetrics(markerPositions, startId, endId) {
  const start = markerPositions.get(startId);
  const end = markerPositions.get(endId);
  if (!start || !end) return null;

  // Launch from the bottom of the entire row (not individual card)
  const gapTop = start.rowBottom !== undefined ? start.rowBottom : start.visualBottom;

  // For long edges skipping rows, bend in the gap above the destination
  const effectiveGapTop = (end.prevRowBottom !== undefined && end.prevRowBottom > gapTop)
    ? end.prevRowBottom
    : gapTop;

  const gapBottom = end.cardTop;
  const gap = Math.max(0, gapBottom - effectiveGapTop);
  const joinY = effectiveGapTop + gap / 2;
  const dx = Math.abs(end.x - start.x);

  const radius = dx < STRAIGHT_THRESHOLD
    ? 0
    : Math.max(0, Math.min(MAX_CORNER_RADIUS, dx / 3, Math.max(0, gap / 2 - 1)));

  return { start, end, gapTop: effectiveGapTop, gapBottom, gap, joinY, radius };
}

/**
 * Builds an SVG path string for a single edge between two nodes.
 *
 * @param {Map} markerPositions
 * @param {string} startId
 * @param {string} endId
 * @param {Object} options — { startAtSpine, endAtSpine, kind }
 * @returns {string} SVG path data
 */
export function buildEdgePath(markerPositions, startId, endId, options = {}) {
  const start = markerPositions.get(startId);
  const end = markerPositions.get(endId);
  if (!start || !end) return '';

  const {
    startAtSpine = false,
    endAtSpine = false,
    kind = 'flow'
  } = options;

  // Branch enter/return: horizontal connector at the bend point
  if (kind === 'branch-enter' || kind === 'branch-return') {
    const metrics = getTransitionMetrics(markerPositions, startId, endId);
    if (!metrics || metrics.radius <= 0) {
      return `M ${start.x} ${metrics?.joinY ?? start.y} L ${end.x} ${metrics?.joinY ?? end.y} `;
    }
    const dirX = end.x > start.x ? 1 : -1;
    const y = metrics.joinY;
    const r = metrics.radius;
    return [
      `M ${start.x} ${y - r}`,
      `Q ${start.x} ${y} ${start.x + dirX * r} ${y}`,
      `L ${end.x - dirX * r} ${y}`,
      `Q ${end.x} ${y} ${end.x} ${y + r}`
    ].join(' ') + ' ';
  }

  // Standard flow edge
  const metrics = getTransitionMetrics(markerPositions, startId, endId);
  const bendY = (metrics && Math.abs(start.x - end.x) >= STRAIGHT_THRESHOLD)
    ? metrics.joinY
    : null;

  // Straight vertical line (dots are aligned)
  if (bendY === null) {
    return `M ${start.x} ${start.y} L ${end.x} ${end.y} `;
  }

  // Bent path with rounded corners
  const dirX = end.x > start.x ? 1 : -1;
  const startVertical = Math.max(0, bendY - start.y);
  const endVertical = Math.max(0, end.y - bendY);
  const radius = Math.min(
    MAX_CORNER_RADIUS,
    Math.abs(end.x - start.x) / 2,
    startAtSpine ? MAX_CORNER_RADIUS : Math.max(0, startVertical - 2),
    endAtSpine ? MAX_CORNER_RADIUS : Math.max(0, endVertical - 2)
  );

  let d = `M ${start.x} ${startAtSpine ? bendY - radius : start.y} `;
  if (!startAtSpine) d += `L ${start.x} ${Math.max(start.y, bendY - radius)} `;
  d += `Q ${start.x} ${bendY} ${start.x + radius * dirX} ${bendY} `;
  d += `L ${end.x - radius * dirX} ${bendY} `;
  d += `Q ${end.x} ${bendY} ${end.x} ${bendY + radius} `;
  if (!endAtSpine) d += `L ${end.x} ${end.y} `;

  return d;
}
