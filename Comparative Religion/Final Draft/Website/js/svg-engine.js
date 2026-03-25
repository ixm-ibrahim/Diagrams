/* === svg-engine.js — Unified Timeline Spine Engine === */
/**
 * Public API for drawing timeline spines and SVG connectors.
 * Orchestrates geometry collection, path drawing, and stacked zone
 * processing via focused sub-modules.
 *
 * Dependencies: state.js, data-store.js, svg-geometry.js,
 *               svg-paths.js, svg-stacked.js, svg-partial.js
 * Consumers:    ui-render.js, main.js
 */

import { NOMINAL_SPINE_WIDTH, SVG_OVERLAP, FORK_BRANCH_GAP, CSS_TRANSITION_MS, RADIUS_ADJUST, SVG_ANIMATION_OVERSHOOT_MS } from './constants.js';
import { AppState } from './state.js';
import { DataStore } from './data-store.js';
import {
  STRAIGHT_THRESHOLD, SPINE_FADE_PX, MAX_CORNER_RADIUS,
  collectMarkerPositions, buildVisualRows
} from './svg-geometry.js';
import { drawEdgePath, drawTerminalReturns, buildColumnSpines } from './svg-paths.js';
import { processStackedZone } from './svg-stacked.js';
import { drawPartialStacking } from './svg-partial.js';

let observer = null;
let redrawTimer = null;
let animationFrameId = null;

/** Cached references for the animation RAF loop. Set by startAnimationRedraw(),
 *  cleared when the loop ends. Avoids redundant DOM queries and array filters
 *  on every frame (~60× per expander transition). */
let cachedViewEl = null;
let cachedVisibleNodes = null;

/* ---------------------------------------------------------------------------
 * Resize handling
 * --------------------------------------------------------------------------- */

/**
 * Debounces SVG redraws to the next frame. Multiple rapid calls (e.g. from
 * resize events or expander animations) are batched into a single draw().
 * No-ops while a page or stacking transition is in progress.
 */
export function scheduleRedraw() {
  if (AppState.isTransitioning || AppState.isStackTransitioning) return;
  if (redrawTimer) return;
  // setTimeout(fn, 0) defers execution to the next macrotask, allowing the
  // browser to coalesce multiple synchronous resize/mutation events into one redraw.
  redrawTimer = setTimeout(() => {
    redrawTimer = null;
    const viewEl = document.querySelector('.map-flow');
    if (!viewEl) return;
    const visibleNodes = DataStore.nodes.filter(
      n => n.parentId === AppState.currentParentId
    );
    try { draw(viewEl, visibleNodes); }
    catch (err) { console.error('[SVG] draw() threw:', err); }
  }, 0);
}

/**
 * Start a requestAnimationFrame loop that redraws SVG every frame for the
 * duration of an expander transition. This ensures return branches and other
 * SVG paths animate smoothly instead of snapping after the transition ends.
 *
 * Performance: caches viewEl and visibleNodes for the entire loop duration
 * since neither changes during an expander animation. This avoids a
 * querySelector + Array.filter on every frame (~60× per transition).
 */
function startAnimationRedraw() {
  if (animationFrameId) cancelAnimationFrame(animationFrameId);

  // Cache references once at animation start — the node set and view element
  // don't change during an expander open/close.
  cachedViewEl = document.querySelector('.map-flow');
  cachedVisibleNodes = cachedViewEl
    ? DataStore.nodes.filter(n => n.parentId === AppState.currentParentId)
    : null;

  if (!cachedViewEl || !cachedVisibleNodes) return;

  const start = performance.now();
  const duration = CSS_TRANSITION_MS + SVG_ANIMATION_OVERSHOOT_MS;

  function tick() {
    if (performance.now() - start > duration) {
      animationFrameId = null;
      cachedViewEl = null;
      cachedVisibleNodes = null;
      scheduleRedraw(); // one final clean redraw
      return;
    }
    // Force immediate redraw (bypass debounce)
    if (redrawTimer) { clearTimeout(redrawTimer); redrawTimer = null; }
    try { draw(cachedViewEl, cachedVisibleNodes); }
    catch (err) { /* swallow during animation */ }
    animationFrameId = requestAnimationFrame(tick);
  }
  animationFrameId = requestAnimationFrame(tick);
}

/** Initializes ResizeObserver on the map container. Call once at bootstrap. */
export function initResizeObserver() {
  if (observer) return;
  const container = document.getElementById('mapContainer');
  if (!container) return;

  observer = new ResizeObserver(() => scheduleRedraw());
  observer.observe(container);
  window.addEventListener('resize', () => scheduleRedraw());

  // Theme changes alter --spine-color-solid which is baked into the SVG
  // fork-fade gradient stop-color attributes. A redraw picks up the new color.
  new MutationObserver(() => scheduleRedraw()).observe(
    document.documentElement,
    { attributes: true, attributeFilter: ['data-theme'] }
  );

  document.addEventListener('expander-settled', () => {
    if (animationFrameId) { cancelAnimationFrame(animationFrameId); animationFrameId = null; }
    cachedViewEl = null;
    cachedVisibleNodes = null;
    scheduleRedraw();
  });
  document.addEventListener('expander-animating', () => startAnimationRedraw());
}

/* ---------------------------------------------------------------------------
 * Main draw function
 * --------------------------------------------------------------------------- */

/**
 * Main SVG rendering entry point. Expects a rendered `.map-flow` element
 * already in the DOM with laid-out node cards. Measures marker positions,
 * computes connector geometry, and produces:
 *   - A single `<svg class="dag-svg">` containing all edge paths
 *   - `<div class="stacked-indent-spine">` elements for indent-level spines
 *   - Snapped positioning for the main `.map-spine` trunk line
 *
 * @param {HTMLElement} viewEl - the `.map-flow` element containing node cards
 * @param {Array<Object>} visibleNodes - node objects visible on the current page
 */
export function draw(viewEl, visibleNodes) {
  const timelineLayer = viewEl.querySelector('.timeline-layer');
  const renderTarget = timelineLayer || viewEl;

  // During animation RAF loops, reuse the existing SVG element and clear its
  // children instead of removing/re-creating it. This avoids the DOM overhead
  // of element creation + insertion ~60× per transition.  Outside animations,
  // the same path runs but the cost is negligible for a single call.
  let oldSvg = renderTarget.querySelector('.dag-svg');
  const oldIndentSpines = renderTarget.querySelectorAll('.stacked-indent-spine');

  if (!visibleNodes || visibleNodes.length === 0) {
    if (oldSvg) oldSvg.remove();
    oldIndentSpines.forEach(el => el.remove());
    return;
  }

  const containerRect = viewEl.getBoundingClientRect();
  const positions = collectMarkerPositions(viewEl, containerRect);
  if (positions.size === 0) return;

  const { visualRows, nodeToRowIdx } = buildVisualRows(viewEl, positions);

  // Reuse existing SVG element during animation loops; create fresh otherwise.
  let svg;
  const isAnimating = animationFrameId !== null;
  if (isAnimating && oldSvg) {
    svg = oldSvg;
    // Clear children without removing the element from the DOM tree
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    oldSvg = null; // prevent removal below
  } else {
    svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'dag-svg');
  }

  const mapSpineEl = viewEl.querySelector('.map-spine');

  // Determine trunk X (main spine position).
  // Use the first depth-0 node's marker X — all depth-0 nodes share the
  // same grid column so any one gives a stable value that doesn't shift
  // when expanders open or visual rows change.
  // Fallback: when ALL nodes are off-spine (e.g. a page whose only row is
  // parallel and has been stacked), compute the spine center from the CSS
  // --marker-col variable which always reflects the depth-0 column width.
  let trunkX = null;
  for (const [, pos] of positions) {
    if (pos.depth === 0) { trunkX = pos.x; break; }
  }
  if (trunkX === null) {
    // All nodes are off-spine (e.g. all-parallel page in stacked mode).
    // The trunk position is the center of the marker column: marker-col / 2.
    // Read --marker-col from the first node-row's computed style (it's set on :root
    // but inherited). This avoids depending on the spine element's prior style.left.
    const firstRow = viewEl.querySelector('.node-row');
    if (firstRow) {
      const markerCol = parseFloat(getComputedStyle(firstRow).getPropertyValue('--marker-col'));
      if (markerCol > 0) {
        trunkX = Math.round(markerCol / 2);
      }
    }
  }
  if (trunkX === null) {
    const firstPos = positions.values().next().value;
    trunkX = firstPos?.x ?? 0;
  }

  const indentSpines = [];
  const allPathData = [];
  const forkPathData = [];   // first-row fork branches (rendered with spine-fade gradient)
  const stackGroups = viewEl.querySelectorAll('.stack-group');

  // --- Layout mode detection ---
  // Three mutually exclusive layout modes determine how edges are drawn:
  //   1. Fully stacked: every level-group has ≤1 direct node-row (all parallel
  //      groups have been wrapped into stack-group columns). Process the entire
  //      page as one unified stacked zone with indent spines.
  //   2. Partially stacked: some level-groups contain stack-groups alongside
  //      parallel nodes. Each stack-group zone is processed independently,
  //      with cross-zone edges routed between stacked and non-stacked nodes.
  //   3. Pure parallel: no stack-groups exist. Standard edge paths are drawn
  //      between parallel node markers using branch/merge curves.
  if (stackGroups.length > 0) {
    const levelGroups = viewEl.querySelectorAll('.level-group:not([data-zone-absorbed])');
    let isFullyStacked = true;
    for (const lg of levelGroups) {
      if (lg.querySelectorAll(':scope > .node-row').length > 1) {
        isFullyStacked = false;
        break;
      }
    }

    if (isFullyStacked) {
      const allNodeRows = viewEl.querySelectorAll('.node-row');
      const unifiedOrder = [];
      const unifiedDepthMap = new Map();
      allNodeRows.forEach(row => {
        const id = row.dataset.id;
        if (!id || !positions.has(id)) return;
        unifiedOrder.push(id);
        unifiedDepthMap.set(id, parseInt(row.style.getPropertyValue('--indent-depth')) || 0);
      });
      if (unifiedOrder.length >= 2) {
        processStackedZone(unifiedOrder, unifiedDepthMap, positions, trunkX,
                           indentSpines, allPathData);
      }
      // First-row branch: if the zone starts with nodes at depth > 0
      // (first-row parallel nodes with no predecessor), draw a branch
      // from the trunk to the first off-spine node.
      if (unifiedOrder.length > 0) {
        const firstId = unifiedOrder[0];
        const firstDepth = unifiedDepthMap.get(firstId) || 0;
        if (firstDepth > 0) {
          const firstPos = positions.get(firstId);
          if (firstPos && Math.abs(firstPos.x - trunkX) >= STRAIGHT_THRESHOLD) {
            const bendY = Math.round(firstPos.cardTop - FORK_BRANCH_GAP);
            const dirX = firstPos.x > trunkX ? 1 : -1;
            const dx = Math.abs(firstPos.x - trunkX);
            const vSpace = Math.max(0, firstPos.y - bendY);
            const r = Math.min(MAX_CORNER_RADIUS, dx / 2, Math.max(0, vSpace - RADIUS_ADJUST));
            forkPathData.push(
              // No vertical segment on the trunk — the spine div already
              // provides that visual.  Starting at the curve avoids
              // doubled alpha where the fork overlaps the fading spine.
              `M ${trunkX} ${bendY - r} ` +
              `Q ${trunkX} ${bendY} ${trunkX + r * dirX} ${bendY} ` +
              `L ${firstPos.x - r * dirX} ${bendY} ` +
              `Q ${firstPos.x} ${bendY} ${firstPos.x} ${bendY + r} ` +
              `L ${firstPos.x} ${firstPos.y + SVG_OVERLAP} `
            );
          }
        }
      }
    } else {
      drawPartialStacking(stackGroups, viewEl, visibleNodes, positions, trunkX,
                          indentSpines, allPathData, forkPathData, visualRows, nodeToRowIdx);
    }
  } else {
    // Pure parallel edge drawing
    const visibleIdSet = new Set(visibleNodes.map(n => n.id));
    const emptySet = new Set();

    // First-row branches: off-spine nodes with no visible predecessors need
    // an explicit branch from the trunk since no parent edge reaches them.
    const firstRowOffSpine = visibleNodes.filter(node => {
      if (node.prevIds && node.prevIds.some(pid => visibleIdSet.has(pid))) return false;
      const pos = positions.get(node.id);
      return pos && Math.abs(pos.x - trunkX) >= STRAIGHT_THRESHOLD;
    });
    if (firstRowOffSpine.length > 0) {
      // Bend point sits midway between the top of the view and the first
      // row's card top, mirroring getTransitionMetrics joinY placement.
      const minCardTop = Math.min(
        ...firstRowOffSpine.map(n => positions.get(n.id).cardTop)
      );
      const bendY = Math.round(minCardTop - FORK_BRANCH_GAP);

      for (const node of firstRowOffSpine) {
        const pos = positions.get(node.id);
        const dirX = pos.x > trunkX ? 1 : -1;
        const dx = Math.abs(pos.x - trunkX);
        const vSpace = Math.max(0, pos.y - bendY);
        const r = Math.min(MAX_CORNER_RADIUS, dx / 2, Math.max(0, vSpace - RADIUS_ADJUST));

        forkPathData.push(
          `M ${trunkX} ${bendY - r} ` +
          `Q ${trunkX} ${bendY} ${trunkX + r * dirX} ${bendY} ` +
          `L ${pos.x - r * dirX} ${bendY} ` +
          `Q ${pos.x} ${bendY} ${pos.x} ${bendY + r} ` +
          `L ${pos.x} ${pos.y + SVG_OVERLAP} `
        );
      }
    }

    visibleNodes.forEach(node => {
      (node.nextIds || []).forEach(nextId => {
        if (!positions.has(nextId)) return;
        allPathData.push(drawEdgePath(node.id, nextId, positions, { trunkX }));
      });
    });
    drawTerminalReturns(visibleNodes, visibleIdSet, positions, trunkX,
                        visualRows, nodeToRowIdx, emptySet, allPathData);
    indentSpines.push(...buildColumnSpines(visibleNodes, positions, trunkX));
  }

  // Device-pixel-perfect spine width: round the nominal NOMINAL_SPINE_WIDTH CSS-px to the
  // nearest whole number of device pixels so every spine and SVG stroke
  // occupies an exact device-pixel count with zero anti-aliasing.
  //   DPR 0.9  → round(1.8)/0.9 = 2/0.9  ≈ 2.222px → exactly 2 device px
  //   DPR 1.0  → round(2.0)/1.0 = 2/1.0  = 2.000px → exactly 2 device px
  //   DPR 1.25 → round(2.5)/1.25= 3/1.25 = 2.400px → exactly 3 device px
  //   DPR 1.35 → round(2.7)/1.35= 3/1.35 ≈ 2.222px → exactly 3 device px
  //   DPR 1.5  → round(3.0)/1.5 = 3/1.5  = 2.000px → exactly 3 device px
  //   DPR 2.0  → round(4.0)/2.0 = 4/2.0  = 2.000px → exactly 4 device px
  // Setting --spine-width on :root propagates to .map-spine, .marker-arm,
  // .btn-derivation::before, .dag-edge stroke-width, and --spine-left calc.
  const devicePixelRatio = window.devicePixelRatio || 1;
  const perfectWidth = Math.round(NOMINAL_SPINE_WIDTH * devicePixelRatio) / devicePixelRatio;
  const halfW = perfectWidth / 2;
  document.documentElement.style.setProperty('--spine-width', `${perfectWidth}px`);

  // Render SVG paths — uses integer CSS coordinates (from collectMarkerPositions)
  // so curve control points stay clean and anti-alias consistently across DPRs.
  // Filter out any path segments containing NaN (from stale/missing positions during
  // layout transitions) to avoid invalid SVG d-attribute errors in the console.
  const combinedPath = allPathData.filter(p => p && !p.includes('NaN')).join('').trim();
  if (combinedPath) {
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('class', 'dag-edge');
    path.setAttribute('d', combinedPath);
    svg.appendChild(path);
  }

  // Fork branch paths: rendered with a gradient stroke that mirrors the
  // spine's fade-in so the branch blends seamlessly out of the spine rather
  // than appearing as a fully-opaque line against a half-transparent spine.
  const combinedForkPath = forkPathData.filter(p => p && !p.includes('NaN')).join('').trim();
  if (combinedForkPath) {
    const spineColor = getComputedStyle(document.documentElement)
      .getPropertyValue('--spine-color-solid').trim();
    const spineHeight = viewEl.offsetHeight || 1;
    // Match the CSS gradient: min(5%, --spine-fade-cap)
    const spineFadeCap = parseFloat(getComputedStyle(document.documentElement)
      .getPropertyValue('--spine-fade-cap')) || SPINE_FADE_PX;
    const fadeEnd = Math.min(0.05 * spineHeight, spineFadeCap);

    const NS = 'http://www.w3.org/2000/svg';
    const defs = document.createElementNS(NS, 'defs');

    const grad = document.createElementNS(NS, 'linearGradient');
    grad.setAttribute('id', 'fork-fade');
    grad.setAttribute('gradientUnits', 'userSpaceOnUse');
    grad.setAttribute('x1', '0');
    grad.setAttribute('y1', '0');
    grad.setAttribute('x2', '0');
    grad.setAttribute('y2', String(fadeEnd));

    const s1 = document.createElementNS(NS, 'stop');
    s1.setAttribute('offset', '0');
    s1.setAttribute('stop-color', spineColor);
    s1.setAttribute('stop-opacity', '0');

    const s2 = document.createElementNS(NS, 'stop');
    s2.setAttribute('offset', '1');
    s2.setAttribute('stop-color', spineColor);
    s2.setAttribute('stop-opacity', '1');

    grad.appendChild(s1);
    grad.appendChild(s2);
    defs.appendChild(grad);

    // Mask: hide the fork path in the narrow vertical strip where the spine
    // div sits so the two semi-transparent layers don't compound alpha.
    const mask = document.createElementNS(NS, 'mask');
    mask.setAttribute('id', 'fork-spine-mask');
    const maskBg = document.createElementNS(NS, 'rect');
    maskBg.setAttribute('width', '100%');
    maskBg.setAttribute('height', '100%');
    maskBg.setAttribute('fill', 'white');
    mask.appendChild(maskBg);
    const maskHide = document.createElementNS(NS, 'rect');
    maskHide.setAttribute('x', String(trunkX - halfW));
    maskHide.setAttribute('y', '0');
    maskHide.setAttribute('width', String(perfectWidth));
    maskHide.setAttribute('height', '100%');
    maskHide.setAttribute('fill', 'black');
    mask.appendChild(maskHide);
    defs.appendChild(mask);

    svg.appendChild(defs);

    const forkPath = document.createElementNS(NS, 'path');
    forkPath.setAttribute('class', 'dag-edge dag-edge-fork');
    forkPath.setAttribute('d', combinedForkPath);
    forkPath.setAttribute('mask', 'url(#fork-spine-mask)');
    svg.appendChild(forkPath);
  }

  // Snap .map-spine left position to device pixel grid.
  if (mapSpineEl && trunkX !== null) {
    mapSpineEl.style.left = `${Math.round((trunkX - halfW) * devicePixelRatio) / devicePixelRatio}px`;
  }

  // Build indent spine HTML elements
  const newIndentSpines = [];
  for (const spineInfo of indentSpines) {
    const fadeZone = spineInfo.fade
      ? Math.min(SPINE_FADE_PX, spineInfo.height * 0.3) : 0;
    const background = spineInfo.fade
      ? `linear-gradient(180deg, var(--spine-color-solid) ${((spineInfo.height - fadeZone) / spineInfo.height * 100).toFixed(1)}%, transparent)`
      : 'var(--spine-color-solid)';

    // Snap left edge to device pixel grid for zero anti-aliasing.
    const snappedLeft = Math.round((spineInfo.x - halfW) * devicePixelRatio) / devicePixelRatio;

    const spine = document.createElement('div');
    spine.className = 'stacked-indent-spine';
    spine.style.cssText = `
      position: absolute;
      left: ${snappedLeft}px;
      top: ${spineInfo.top}px;
      height: ${spineInfo.height}px;
      width: ${perfectWidth}px;
      background: ${background};
      pointer-events: none;
      z-index: 1;
    `;
    newIndentSpines.push(spine);
  }

  // Swap old elements for new. When reusing the SVG (animation loop),
  // oldSvg was set to null above so we skip the redundant remove+append.
  if (oldSvg) oldSvg.remove();
  oldIndentSpines.forEach(el => el.remove());
  if (!svg.parentNode) renderTarget.appendChild(svg);
  newIndentSpines.forEach(s => renderTarget.appendChild(s));
}

