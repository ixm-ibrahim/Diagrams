/**
 * =============================================================================
 * color-engine.js — Perceptual Color Engine
 * =============================================================================
 * Assigns visually distinct hues to sibling nodes using perceptual anchors.
 * The anchors are hand-tuned to avoid metameric confusion zones where
 * adjacent hues become indistinguishable.
 *
 * Dependencies: none
 * Consumers: data-store.js (called during bootstrap color assignment)
 * =============================================================================
 */

/**
 * Returns a perceptually spaced hue (0–360) for a node at the given index
 * within a group of totalNodes siblings.
 *
 * For small groups (≤9), returns exact anchor values.
 * For larger groups, interpolates linearly between adjacent anchors.
 *
 * @param {number} index      — zero-based position in the sibling group
 * @param {number} totalNodes — total siblings in the group
 * @returns {number} hue angle (0–360)
 */
export function getPerceptualHue(index, totalNodes) {
  // Hand-tuned anchor hues spanning the full wheel.
  // Gaps are wider where human perception is less sensitive (greens, blues).
  const anchors = [0, 30, 55, 130, 180, 225, 260, 315, 340];

  if (totalNodes <= anchors.length) return anchors[index];

  // Interpolate for groups larger than the anchor count
  const progress = index / (totalNodes - 1);
  const position = progress * (anchors.length - 1);
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  const fraction = position - lower;

  if (lower >= anchors.length - 1) return anchors[anchors.length - 1];
  return anchors[lower] + fraction * (anchors[upper] - anchors[lower]);
}

/**
 * Computes the four-color set for a node given its hue.
 * These are set as inline CSS custom properties on each card.
 *
 * @param {number} hue — hue angle (0–360)
 * @returns {{ borderDark: string, borderLight: string, top: string, bottom: string }}
 */
export function computeNodeColors(hue) {
  return {
    borderDark:  `hsl(${hue}, 95%, 68%)`,
    borderLight: `hsl(${hue}, 90%, 34%)`,
    top:         `hsl(${hue}, 85%, 93%)`,
    bottom:      `hsl(${hue}, 90%, 84%)`
  };
}
