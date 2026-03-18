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

import { AppState } from './state.js';
import { DataStore } from './data-store.js';
import {
  STRAIGHT_THRESHOLD, SPINE_FADE_PX,
  collectMarkerPositions, buildVisualRows
} from './svg-geometry.js';
import { drawEdgePath, drawTerminalReturns, buildColumnSpines } from './svg-paths.js';
import { processStackedZone } from './svg-stacked.js';
import { drawPartialStacking } from './svg-partial.js';

let observer = null;
let redrawTimer = null;

/* ---------------------------------------------------------------------------
 * Resize handling
 * --------------------------------------------------------------------------- */

export function scheduleRedraw() {
  if (AppState.isTransitioning || AppState.isStackTransitioning) return;
  if (redrawTimer) return;
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

/** Initializes ResizeObserver on the map container. Call once at bootstrap. */
export function initResizeObserver() {
  if (observer) return;
  const container = document.getElementById('mapContainer');
  if (!container) return;

  observer = new ResizeObserver(() => scheduleRedraw());
  observer.observe(container);
  window.addEventListener('resize', () => scheduleRedraw());
  document.addEventListener('expander-settled', () => scheduleRedraw());
}

/* ---------------------------------------------------------------------------
 * Main draw function
 * --------------------------------------------------------------------------- */

export function draw(viewEl, visibleNodes) {
  const timelineLayer = viewEl.querySelector('.timeline-layer');
  const renderTarget = timelineLayer || viewEl;

  const oldSvg = renderTarget.querySelector('.dag-svg');
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

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'dag-svg');

  // Determine trunk X (depth-0 / main spine position)
  let trunkX = null;
  for (const [, pos] of positions) {
    if (pos.depth === 0) { trunkX = pos.x; break; }
  }
  if (trunkX === null) {
    const firstPos = positions.values().next().value;
    trunkX = firstPos?.x ?? 0;
  }

  const indentSpines = [];
  const allPathData = [];
  const stackGroups = viewEl.querySelectorAll('.stack-group');

  if (stackGroups.length > 0) {
    // Check if page is fully stacked
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
    } else {
      drawPartialStacking(stackGroups, viewEl, visibleNodes, positions, trunkX,
                          indentSpines, allPathData, visualRows, nodeToRowIdx);
    }
  } else {
    // Pure parallel edge drawing
    const visibleIdSet = new Set(visibleNodes.map(n => n.id));
    const emptySet = new Set();
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

  // Device-pixel-perfect spine width: round the nominal 2 CSS-px to the
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
  const dpr = window.devicePixelRatio || 1;
  const perfectWidth = Math.round(2 * dpr) / dpr;
  const halfW = perfectWidth / 2;
  document.documentElement.style.setProperty('--spine-width', `${perfectWidth}px`);

  // Render SVG paths — uses integer CSS coordinates (from collectMarkerPositions)
  // so curve control points stay clean and anti-alias consistently across DPRs.
  const combinedPath = allPathData.join('').trim();
  if (combinedPath) {
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('class', 'dag-edge');
    path.setAttribute('d', combinedPath);
    svg.appendChild(path);
  }

  // Snap .map-spine left position to device pixel grid.
  const mapSpineEl = viewEl.querySelector('.map-spine');
  if (mapSpineEl && trunkX !== null) {
    mapSpineEl.style.left = `${Math.round((trunkX - halfW) * dpr) / dpr}px`;
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
    const snappedLeft = Math.round((spineInfo.x - halfW) * dpr) / dpr;

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

  // Swap old elements for new
  if (oldSvg) oldSvg.remove();
  oldIndentSpines.forEach(el => el.remove());
  renderTarget.appendChild(svg);
  newIndentSpines.forEach(s => renderTarget.appendChild(s));
}

