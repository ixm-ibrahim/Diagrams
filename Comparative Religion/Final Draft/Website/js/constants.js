/**
 * =============================================================================
 * constants.js — Timing & Configuration Constants
 * =============================================================================
 * Central location for all timing values, thresholds, and configuration.
 * Every other JS module imports values from here instead of using bare numbers.
 *
 * Dependencies: none
 *
 * Consumers: state.js, svg-engine.js, ui-render.js, ui-expander.js,
 *            ui-layout.js, ui-events.js
 * =============================================================================
 */

/**
 * Animation timing.
 * CSS_TRANSITION_MS must match --page-transition-duration in tokens.css.
 * SCROLL_DELAY_MS should be slightly longer so scroll happens after animation.
 */
export const ANIMATION_SPEEDS = {
  CSS_TRANSITION_MS: 500,
  SCROLL_DELAY_MS: 510
};

/**
 * Maximum pixel distance over which a spine fades from solid to transparent.
 * Clamped to 30% of the spine's total height so short spines don't over-fade.
 */
export const SPINE_FADE_PX = 60;

/**
 * Per-flex-child width threshold (px) below which a parallel level-group
 * collapses into a stacked indented list.
 *
 * Calibrated from real-world layout measurements:
 *   3-child row (e.g. 2.2-2.4): controls wrap at ~904px viewport → per-child ≈ 289
 *   2-child row (e.g. 2.6-2.7): controls wrap at ~569px viewport → per-child ≈ 267
 *   4-child 2-parent row (e.g. 6.4-6.7): app max 1084px → per-child ≈ 271
 * 270 avoids permanently stacking 4-child rows at max width while still
 * triggering well before cards become unusable.
 *
 * The metric (groupWidth / childCount) is stable regardless of stacked/unstacked
 * state because the group fills its parent either way, so no hysteresis is needed.
 */
export const STACK_THRESHOLD = 270;

/**
 * Minimum effective card width (px) for the deepest node in a stacked zone.
 *
 * When a zone's deepest node would be narrower than this after indentation,
 * ancestor parallel rows are forced to stack ("cascade stacking") so the
 * zone gets wider.  Each cascade level increases zone width at the cost of
 * one extra indent level, so the loop converges quickly.
 *
 * Effective card width = containerWidth × combinedWeight − maxDepth × indent.
 *
 * 200 px gives enough room for a card title + badge at all breakpoints.
 */
export const DEEP_NODE_MIN_WIDTH = 200;

/**
 * Horizontal pixel distance below which two marker dots are considered
 * vertically aligned (straight line, no bend needed).
 */
export const STRAIGHT_THRESHOLD = 5;

/**
 * Maximum radius (px) for rounded corners on SVG connector bends.
 */
export const MAX_CORNER_RADIUS = 12;

/**
 * Debounce delay (ms) for search input.
 */
export const SEARCH_DEBOUNCE_MS = 150;

/**
 * Duration (ms) of the theme-transition class on body.
 */
export const THEME_TRANSITION_MS = 300;
