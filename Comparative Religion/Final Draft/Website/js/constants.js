/**
 * =============================================================================
 * constants.js — Timing & Configuration Constants
 * =============================================================================
 * Central location for all timing values, thresholds, and configuration.
 * Every other JS module imports values from here instead of using bare numbers.
 *
 * Dependencies: none
 *
 * Consumers: state.js, ui-render.js, ui-expander.js,
 *            ui-layout.js, ui-events.js, ui-search.js,
 *            svg-geometry.js, svg-engine.js, ui-events.js
 * =============================================================================
 */

/* ---------------------------------------------------------------------------
 * Animation timing
 * --------------------------------------------------------------------------- */

/**
 * Page transition animation duration (ms).
 * MUST match --page-transition-duration in tokens.css (0.5s = 500ms).
 */
export const CSS_TRANSITION_MS = 500;

/**
 * ANIMATION_SPEEDS — legacy convenience object.
 * Prefer the named exports above; this is kept for backward compatibility.
 */
export const ANIMATION_SPEEDS = {
  CSS_TRANSITION_MS,
  SCROLL_DELAY_MS: 510
};

/**
 * Delay (ms) before scrolling after a page transition.
 * Slightly longer than CSS_TRANSITION_MS so scroll happens after animation.
 */
export const SCROLL_DELAY_MS = 510;

/**
 * Duration (ms) of the theme-transition class on body.
 * MUST match --theme-transition-duration in tokens.css (0.3s = 300ms).
 */
export const THEME_TRANSITION_MS = 300;

/**
 * Debounce delay (ms) for search input.
 */
export const SEARCH_DEBOUNCE_MS = 150;

/**
 * Multiplier applied to CSS_TRANSITION_MS to delay focus-dimming removal
 * during expander close animation, so the panel is visible against the
 * dimmed background before everything brightens.
 */
export const FOCUS_DIM_DELAY_RATIO = 0.6;

/* ---------------------------------------------------------------------------
 * Layout thresholds
 * --------------------------------------------------------------------------- */

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

/* ---------------------------------------------------------------------------
 * SVG geometry constants
 * --------------------------------------------------------------------------- */

/** Maximum pixel distance over which a spine fades from solid to transparent. */
export const SPINE_FADE_PX = 60;

/** Horizontal distance (px) below which two markers are considered vertically aligned. */
export const STRAIGHT_THRESHOLD = 5;

/** Maximum radius (px) for quadratic corner curves on branch/merge connectors. */
export const MAX_CORNER_RADIUS = 12;

/** Half of the spine width (--spine-width: 2px). Used for SVG mask alignment. */
export const SPINE_HALF_W = 1;

/* ---------------------------------------------------------------------------
 * Search
 * --------------------------------------------------------------------------- */

/** Maximum search results to render (prevents DOM explosion on short queries). */
export const MAX_RESULTS = 100;

/* ---------------------------------------------------------------------------
 * UI timing — small delays used in setTimeout calls
 * --------------------------------------------------------------------------- */

/** Delay (ms) to let layout settle before drawing/redrawing SVG connectors. */
export const SVG_SETTLE_DELAY_MS = 50;

/** Delay (ms) after navigation before scrolling to a specific node. */
export const SCROLL_TO_NODE_DELAY_MS = 600;

/**
 * Net margin offset (px) added to expander spacer height to account for
 * the expander's negative top margin (-8) plus bottom margin (+24).
 */
export const EXPANDER_SPACER_MARGIN_PX = 16;
