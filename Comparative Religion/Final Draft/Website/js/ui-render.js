/**
 * =============================================================================
 * ui-render.js — View Building & Rendering
 * =============================================================================
 * Creates the DOM structure for a page of nodes, adds sibling navigation,
 * and mounts with directional transition animations.
 *
 * Public API: init(), buildView(), renderMapWithTransition(), EXIT_CLASS, ENTER_CLASS
 *
 * Dependencies: graph-engine.js (computeLevels),
 *               templates.js (nodeRow),
 *               data-store.js (DataStore),
 *               state.js (AppState),
 *               constants.js (ANIMATION_SPEEDS),
 *               sibling-nav.js (renderSiblingNavigation),
 *               svg-engine.js (draw),
 *               ui-agreement.js (applyVoteStates — restores glows after render),
 *               ui-layout.js (updateStackedGroups),
 *               ui-render-weights.js (computeFlexWeights, buildOrderedRuns),
 *               ui-render-stacking.js (buildStackGroups, applyCascadeStacking)
 * Consumers: navigation.js (renderMapWithTransition),
 *            main.js (init)
 * =============================================================================
 */

import { computeLevels } from './graph-engine.js';
import { nodeRow } from './templates.js';
import { DataStore } from './data-store.js';
import { AppState } from './state.js';
import { ANIMATION_SPEEDS, SVG_SETTLE_DELAY_MS } from './constants.js';
import { renderSiblingNavigation } from './sibling-nav.js';
import { draw as drawSVG } from './svg-engine.js';
import { updateStackedGroups } from './ui-layout.js';
import { applyVoteStates } from './ui-agreement.js';
import { computeFlexWeights, buildOrderedRuns } from './ui-render-weights.js';
import { buildStackGroups, applyCascadeStacking } from './ui-render-stacking.js';

/** Cached container element. Set by init(). */
let container = null;

/**
 * Caches the map container DOM reference. Call once during bootstrap.
 */
export function init() {
  container = document.getElementById('mapContainer');
}

/**
 * Builds the complete DOM subtree for the current page.
 * Returns a .map-flow element ready to be appended to the container.
 *
 * @returns {HTMLElement}
 */
export function buildView() {
  // Guard: if currentParentId is set but doesn't exist in the data, fall back to root
  if (AppState.currentParentId != null && !DataStore.map.has(AppState.currentParentId)) {
    console.warn(`[buildView] Node "${AppState.currentParentId}" not found in DataStore. Falling back to root.`);
    AppState.currentParentId = null;
  }

  const newView = document.createElement('div');
  newView.className = 'map-flow';

  // Glow sits outside the timeline-layer (unaffected by layer opacity)
  const glow = document.createElement('div');
  glow.className = 'map-spine-glow';
  glow.setAttribute('aria-hidden', 'true');
  newView.appendChild(glow);

  // Timeline layer: compositing container for spine + SVG.
  // Container-level opacity makes overlapping opaque elements safe.
  const timelineLayer = document.createElement('div');
  timelineLayer.className = 'timeline-layer';
  timelineLayer.setAttribute('aria-hidden', 'true');
  const spine = document.createElement('div');
  spine.className = 'map-spine';
  timelineLayer.appendChild(spine);
  newView.appendChild(timelineLayer);

  const visibleNodes = DataStore.nodes.filter(
    n => n.parentId === AppState.currentParentId
  );

  if (visibleNodes.length === 0) {
    // Two cases:
    //   1. Terminal node (hasDerivation: false) — show the node's own card
    //      so the user sees the endpoint of the logic chain.
    //   2. Undeveloped node (hasDerivation: true, no children yet) — show
    //      only the message, since this page is expected to have content later.
    const parentNode = AppState.currentParentId
      ? DataStore.map.get(AppState.currentParentId)
      : null;

    const isTerminal = parentNode && parentNode.hasDerivation === false;

    if (isTerminal) {
      const levelGroup = document.createElement('div');
      levelGroup.className = 'level-group';

      const row = document.createElement('div');
      row.className = 'node-row';
      row.dataset.id = parentNode.id;
      row.innerHTML = nodeRow(parentNode);
      levelGroup.appendChild(row);

      const expanderEl = document.createElement('div');
      expanderEl.className = 'level-expander';
      levelGroup.appendChild(expanderEl);

      newView.appendChild(levelGroup);
    }

    const msg = document.createElement('div');
    // Terminal messages sit below the node card — left-aligned is appropriate.
    // Undeveloped messages have no card above them, so we center them prominently.
    msg.className = isTerminal
      ? 'empty-page-message'
      : 'empty-page-message empty-page-message--undeveloped';
    msg.textContent = isTerminal
      ? 'This claim concludes this branch of reasoning.'
      : 'No deeper derivations mapped for this claim yet.';
    newView.appendChild(msg);

    return newView;
  }

  const fragment = document.createDocumentFragment();
  const groupedRows = computeLevels(visibleNodes);
  const allLevelGroups = [];
  const visibleIdSet = new Set(visibleNodes.map(n => n.id));

  // Compute proportional flex weights so child nodes inherit their
  // parent's share of the row width (tree-proportional layout).
  const weights = computeFlexWeights(groupedRows);

  groupedRows.forEach((rowNodes, rowIdx) => {
    const levelGroup = document.createElement('div');
    levelGroup.className = 'level-group';
    levelGroup.dataset.rowIdx = String(rowIdx);

    const realNodeEls = [];
    const flexItems = [];

    rowNodes.forEach((node, colIdx) => {
      if (node.isDummy) {
        const dummy = document.createElement('div');
        dummy.className = 'dummy-node';
        dummy.dataset.colIdx = String(colIdx);
        levelGroup.appendChild(dummy);
        flexItems.push(dummy);
        return;
      }

      const row = document.createElement('div');
      row.className = 'node-row';
      row.dataset.id = node.id;
      row.dataset.colIdx = String(colIdx);
      row.innerHTML = nodeRow(node);
      levelGroup.appendChild(row);
      realNodeEls.push(row);
      flexItems.push(row);
    });

    // Parallel tagging for flex-basis equalization
    const totalFlexChildren = flexItems.length;
    if (totalFlexChildren > 1) {
      levelGroup.dataset.parallel = '';
      flexItems[0].dataset.firstParallel = 'true';
      flexItems[flexItems.length - 1].dataset.lastParallel = 'true';

      // The last real node only gets the full derive button (via data-last-parallel)
      // if it's truly the rightmost item. If dummies come after it, the real node
      // should use condensed buttons like all other non-last parallel nodes.
      const lastRealNode = realNodeEls.length > 0
        ? realNodeEls[realNodeEls.length - 1]
        : null;
      const lastFlexItem = flexItems[flexItems.length - 1];
      if (lastRealNode && lastRealNode !== lastFlexItem) {
        // Last flex item is a dummy — it gets flex-basis compensation via
        // data-last-parallel (already set above). The last real node does NOT
        // get data-last-parallel, so it uses condensed derive buttons.
      } else if (lastRealNode) {
        // Last flex item IS the last real node — give it the full button
        lastRealNode.dataset.lastParallel = 'true';
      }

      // Apply proportional flex weights
      const rowWeights = weights[rowIdx];
      if (rowWeights) {
        flexItems.forEach((el, colIdx) => {
          const w = rowWeights[colIdx];
          if (w !== undefined && w !== 1) {
            el.style.setProperty('--flex-weight', String(w));
          }
        });
      }

      // Record sibling groups (including single nodes) so updateStackedGroups
      // can dynamically wrap / unwrap nodes into a .stack-group column when
      // the container narrows. Nodes stay as direct level-group children here
      // so all parallel CSS keeps working correctly at full width.
      const stackGroupsData = buildStackGroups(
        rowNodes, rowIdx, groupedRows, weights, visibleIdSet
      );

      if (stackGroupsData.length > 0) {
        levelGroup.dataset.stackGroups = JSON.stringify(stackGroupsData);
      }
    }

    // Shared expander (Phase 4 populates on click)
    const expanderEl = document.createElement('div');
    expanderEl.className = 'level-expander';
    levelGroup.appendChild(expanderEl);

    allLevelGroups.push(levelGroup);
    fragment.appendChild(levelGroup);
  });

  newView._allLevelGroups = allLevelGroups;
  newView.appendChild(fragment);

  // Apply initial stacked/unstacked state without waiting for first resize event
  const cw = container ? container.offsetWidth : 0;
  if (cw > 0) {
    // Cascade stacking: force ancestor parallel rows to stack when their
    // descendant zones would produce cards narrower than DEEP_NODE_MIN_WIDTH.
    // Width-independent — raises stackAt thresholds for all relevant widths.
    applyCascadeStacking(allLevelGroups);
    updateStackedGroups(newView, cw);
  }

  return newView;
}


/** Direction → CSS animation class mappings */
export const EXIT_CLASS = {
  depth: 'anim-exit-left',
  surface: 'anim-exit-right',
  'lateral-next': 'anim-exit-top',
  'lateral-prev': 'anim-exit-bottom'
};
export const ENTER_CLASS = {
  depth: 'anim-enter-right',
  surface: 'anim-enter-left',
  'lateral-next': 'anim-enter-bottom',
  'lateral-prev': 'anim-enter-top'
};

/**
 * Builds a new view and animates it in, simultaneously animating old views out.
 * Transition direction determines which animation classes are applied.
 *
 * @param {'depth'|'surface'|'lateral-next'|'lateral-prev'|'none'} direction
 */
export function renderMapWithTransition(direction) {
  if (!container) return;

  const oldViews = container.querySelectorAll(
    '.map-flow, .search-result-box, .search-group'
  );
  container.style.pointerEvents = 'none';
  AppState.isTransitioning = true;

  // Lock container height to prevent layout jump during transition.
  // Skip on initial render (no old views) to avoid a brief overflow clip
  // that cuts off derivation buttons and glow effects.
  const hasOldViews = oldViews.length > 0;
  if (hasOldViews) {
    container.style.minHeight = `${container.offsetHeight}px`;
    // Clip old views individually instead of the whole container,
    // so derivation buttons and glow effects on the new view aren't cut off.
    oldViews.forEach(v => { v.style.overflow = 'hidden'; });
  }

  // Phase 1: Build new view
  const newView = buildView();
  renderSiblingNavigation(newView);
  container.appendChild(newView);

  // Restore persisted vote button states on the freshly rendered nodes
  applyVoteStates(newView);

  // Phase 2: Draw SVG connectors (needs layout to settle)
  const visibleNodes = DataStore.nodes.filter(
    n => n.parentId === AppState.currentParentId
  );
  setTimeout(() => {
    try { drawSVG(newView, visibleNodes); }
    catch (err) { console.error('[UI] Phase 2 drawSVG threw:', err); }
  }, SVG_SETTLE_DELAY_MS);

  // Phase 3: Animate old out, new in
  oldViews.forEach(oldView => {
    if (EXIT_CLASS[direction]) oldView.classList.add(EXIT_CLASS[direction]);
    oldView.style.position = 'absolute';
    oldView.style.top = '0';
    oldView.style.left = '0';
  });

  if (ENTER_CLASS[direction]) newView.classList.add(ENTER_CLASS[direction]);
  window.scrollTo(0, 0);

  // Phase 4: Cleanup after animation completes
  setTimeout(() => {
    newView.classList.remove(...Object.values(ENTER_CLASS));
    container.style.pointerEvents = '';
    container.style.minHeight = '';

    // Mark transition complete *before* the forced catch-up updates so they
    // run with the correct (post-resize) container dimensions and won't be
    // blocked by the isTransitioning guard.
    AppState.isTransitioning = false;

    // Forced catch-up: replay any resize events that were skipped while
    // isTransitioning was true. Ensures stacked layout is never stale after
    // a resize that happened mid-animation.
    if (container) {
      updateStackedGroups(newView, container.offsetWidth);
    }

    // Defensive overflow cleanup: explicitly reset before removal so that if
    // an exception or async delay ever prevented removal, no overflow:hidden
    // would linger on an element still visible in the DOM and clip card glows.
    oldViews.forEach(v => {
      v.style.overflow = '';
      v.remove();
    });

    // Final SVG redraw after layout is fully settled. Runs after the forced
    // stacking update above so connectors are drawn on the final geometry.
    setTimeout(() => {
      try { drawSVG(newView, visibleNodes); }
      catch (err) { console.error('[UI] Phase 4 drawSVG threw:', err); }
    }, SVG_SETTLE_DELAY_MS);
  }, ANIMATION_SPEEDS.CSS_TRANSITION_MS);
}
