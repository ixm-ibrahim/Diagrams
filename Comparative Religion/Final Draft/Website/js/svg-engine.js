/**
 * =============================================================================
 * svg-engine.js — SVG Connector Engine
 * =============================================================================
 * Draws DAG edge paths between node markers. All coordinates are read from
 * the DOM at draw-time via getBoundingClientRect() on .marker-dot elements,
 * so nothing here needs to stay in sync with CSS layout values.
 *
 * A mask prevents SVG paths from drawing over the HTML spine element.
 *
 * Phase 3: standard DAG edges, terminal return curves, trunk mask.
 * Phase 5: indent spines for stacked zones. (Synthetic edges TBD.)
 *
 * Dependencies: svg-paths.js (getTransitionMetrics, buildEdgePath),
 *               constants.js (STRAIGHT_THRESHOLD, MAX_CORNER_RADIUS,
 *               SPINE_FADE_PX), state.js (AppState),
 *               data-store.js (DataStore)
 * Consumers: ui-render.js (calls draw and initResizeObserver)
 * =============================================================================
 */

import { buildEdgePath } from './svg-paths.js';
import {
  STRAIGHT_THRESHOLD,
  MAX_CORNER_RADIUS,
  SPINE_FADE_PX
} from './constants.js';
import { AppState } from './state.js';
import { DataStore } from './data-store.js';

let maskCounter = 0;

let observer = null;

/* ---------------------------------------------------------------------------
 * Resize handling
 * --------------------------------------------------------------------------- */

function scheduleRedraw() {
  if (AppState.isTransitioning || AppState.isStackTransitioning) return;
  const viewEl = document.querySelector('.map-flow');
  if (!viewEl) return;
  const visibleNodes = DataStore.nodes.filter(
    n => n.parentId === AppState.currentParentId
  );
  requestAnimationFrame(() => draw(viewEl, visibleNodes));
}

/** Initializes ResizeObserver on the map container. Call once at bootstrap. */
export function initResizeObserver() {
  if (observer) return;
  const container = document.getElementById('mapContainer');
  if (!container) return;

  observer = new ResizeObserver(() => scheduleRedraw());
  observer.observe(container);
  window.addEventListener('resize', () => scheduleRedraw());
}

/* ---------------------------------------------------------------------------
 * Marker position collection
 * --------------------------------------------------------------------------- */

function collectPositions(viewEl) {
  const containerRect = viewEl.getBoundingClientRect();
  const markerPositions = new Map();
  const nodeToRowIdx = new Map();
  const visualRows = [];
  let trunkX = null;

  const groups = [...viewEl.querySelectorAll('.level-group:not([data-zone-absorbed])')];

  groups.forEach(group => {
    const nodeRowEls = [...group.querySelectorAll(':scope > .node-row, :scope > .stack-group > .node-row')];
    const baseRowIdx = parseInt(group.dataset.rowIdx) || 0;

    // Group node-rows by effective row: original nodes stay at baseRowIdx,
    // zone-absorbed nodes are keyed by their data-zone-origin-row.
    // This ensures zone-absorbed nodes get separate visual rows so that
    // edge bend-points aren't computed against the entire stack's bottom.
    const subRowMap = new Map();
    nodeRowEls.forEach(rowEl => {
      const effectiveRow = rowEl.dataset.zoneOriginRow !== undefined
        ? parseInt(rowEl.dataset.zoneOriginRow)
        : baseRowIdx;
      if (!subRowMap.has(effectiveRow)) subRowMap.set(effectiveRow, []);
      subRowMap.get(effectiveRow).push(rowEl);
    });

    const sortedKeys = [...subRowMap.keys()].sort((a, b) => a - b);

    for (const key of sortedKeys) {
      const subRowNodeEls = subRowMap.get(key);
      const subRowNodeIds = subRowNodeEls.map(r => r.dataset.id);
      let maxBottom = 0;

      subRowNodeIds.forEach(id => {
        const row = group.querySelector(
          `:scope > .node-row[data-id="${id}"], ` +
          `:scope > .stack-group > .node-row[data-id="${id}"]`
        );
        const dot = row?.querySelector('.marker-dot');
        const card = row?.querySelector('.node-card');
        if (!dot || !card) return;

        const dotRect = dot.getBoundingClientRect();
        const cardRect = card.getBoundingClientRect();
        const expander = group.querySelector('.level-expander');
        const expInner = expander?.querySelector('.exp-inner');
        const visualBottom = (expander?.classList.contains('is-open') && expInner)
          ? expInner.getBoundingClientRect().bottom - containerRect.top
          : cardRect.bottom - containerRect.top;

        const x = dotRect.left - containerRect.left + dotRect.width / 2;
        const y = dotRect.top - containerRect.top + dotRect.height / 2;
        const depth = parseInt(row.style.getPropertyValue('--indent-depth')) || 0;

        markerPositions.set(id, {
          x, y, depth,
          cardTop: cardRect.top - containerRect.top,
          cardBottom: cardRect.bottom - containerRect.top,
          visualBottom
        });

        if (trunkX === null && depth === 0) trunkX = x;
        maxBottom = Math.max(maxBottom, visualBottom);
      });

      if (subRowNodeIds.length > 0 && maxBottom > 0) {
        const rowIdx = visualRows.length;
        visualRows.push({ nodeIds: subRowNodeIds, bottom: maxBottom });
        subRowNodeIds.forEach(id => nodeToRowIdx.set(id, rowIdx));
      }
    }
  });

  if (trunkX === null) {
    const firstPos = markerPositions.values().next().value;
    trunkX = firstPos?.x ?? 0;
  }

  // Attach row-relative metrics
  for (const [id, pos] of markerPositions) {
    const idx = nodeToRowIdx.get(id);
    pos.rowBottom = idx === undefined ? pos.visualBottom : visualRows[idx].bottom;
    pos.prevRowBottom = idx > 0 ? visualRows[idx - 1].bottom : null;
  }

  return { markerPositions, visualRows, trunkX, nodeToRowIdx };
}

/* ---------------------------------------------------------------------------
 * Terminal return curves: nodes ending a branch off the trunk merge back
 * --------------------------------------------------------------------------- */

function buildTerminalReturns(
  markerPositions, visibleNodes, trunkX, nodeToRowIdx, visualRows
) {
  const visibleIdSet = new Set(visibleNodes.map(n => n.id));

  const terminalOffSpine = visibleNodes.filter(node => {
    if (node.nextIds?.some(nid => visibleIdSet.has(nid))) return false;
    const pos = markerPositions.get(node.id);
    return pos && Math.abs(pos.x - trunkX) >= STRAIGHT_THRESHOLD;
  });

  if (terminalOffSpine.length === 0) return '';

  // Group by X — only the deepest terminal at each X needs a curve
  const byX = new Map();
  for (const node of terminalOffSpine) {
    const pos = markerPositions.get(node.id);
    const xKey = Math.round(pos.x);
    if (!byX.has(xKey) || pos.y > byX.get(xKey).y) {
      byX.set(xKey, pos);
    }
  }

  // Compute merge Y from the bottom of the last terminal row
  const firstTerminalRowIdx = Math.min(
    ...terminalOffSpine.map(n => nodeToRowIdx.get(n.id)).filter(i => i !== undefined)
  );
  let standardGap = 20;
  if (firstTerminalRowIdx > 0) {
    const sampleId = visualRows[firstTerminalRowIdx].nodeIds[0];
    const samplePos = markerPositions.get(sampleId);
    if (samplePos) {
      standardGap = samplePos.cardTop - visualRows[firstTerminalRowIdx - 1].bottom;
    }
  }

  let maxRowBottom = 0;
  for (const node of visibleNodes) {
    if (!node.nextIds?.some(nid => visibleIdSet.has(nid))) {
      const pos = markerPositions.get(node.id);
      if (pos) maxRowBottom = Math.max(maxRowBottom, pos.rowBottom);
    }
  }
  const mergeY = maxRowBottom + standardGap / 2;

  let pathData = '';
  for (const [, pos] of byX) {
    const dirX = trunkX > pos.x ? 1 : -1;
    const radius = Math.min(
      MAX_CORNER_RADIUS,
      Math.abs(trunkX - pos.x) / 2,
      Math.max(0, Math.abs(mergeY - pos.y) - 2)
    );
    pathData +=
      `M ${pos.x} ${pos.y} ` +
      `L ${pos.x} ${mergeY - radius} ` +
      `Q ${pos.x} ${mergeY} ${pos.x + radius * dirX} ${mergeY} ` +
      `L ${trunkX - radius * dirX} ${mergeY} ` +
      `Q ${trunkX} ${mergeY} ${trunkX} ${mergeY + radius} `;
  }
  return pathData;
}

/* ---------------------------------------------------------------------------
 * Indent spine computation (Phase 5)
 * --------------------------------------------------------------------------- */

/**
 * Computes vertical indent spines for stacked zones, plus the set of DAG
 * edges to suppress so the spines replace redundant fan-out / fan-in paths.
 *
 * For each stack-group, walks its DFS-ordered node-rows and finds contiguous
 * runs at each indent depth.  A "run" at depth D is a maximal sequence of
 * consecutive nodes (in DOM/DFS order) where no node has depth < D.  Only
 * nodes at exactly depth D are run endpoints; deeper nodes (children) sit
 * inside the run but don't start or end it.
 *
 * Each run produces one vertical spine positioned at the X of depth-D
 * markers.  Multi-node runs span dot-center to dot-center; single-node
 * runs span cardTop to cardBottom for visibility.
 *
 * Edge consolidation: when multiple edges from the same external parent go
 * to nodes in a spine run, only the edge to the FIRST node is kept (the
 * spine connects the rest).  When multiple edges from run nodes go to the
 * same external target, only the edge from the LAST node is kept.
 *
 * @param {HTMLElement} viewEl — the .map-flow element
 * @param {Map} markerPositions — id → { x, y, cardTop, cardBottom, … }
 * @returns {{ spines: Array<{ x, top, height, fade }>, skipEdges: Set<string> }}
 */
function computeIndentSpines(viewEl, markerPositions) {
  const spines = [];
  const skipEdges = new Set();

  for (const sg of viewEl.querySelectorAll('.stack-group')) {
    // Collect node entries in DOM order (already DFS-sorted by updateStackedGroups)
    const entries = [];
    for (const row of sg.querySelectorAll(':scope > .node-row')) {
      const id = row.dataset.id;
      const depth = parseInt(row.style.getPropertyValue('--indent-depth')) || 0;
      const pos = markerPositions.get(id);
      if (pos && depth > 0) entries.push({ id, depth, pos });
    }

    if (entries.length === 0) continue;

    // All unique depths present in this stack-group
    const allDepths = [...new Set(entries.map(e => e.depth))].sort((a, b) => a - b);

    for (const d of allDepths) {
      let runNodes = []; // nodes at exactly depth d in the current run

      const flushRun = () => {
        if (runNodes.length === 0) return;
        const first = runNodes[0];
        const last = runNodes[runNodes.length - 1];

        // --- Spine geometry ---
        // Multi-node: dot-center → dot-center.
        // Single-node: cardTop → cardBottom for a visible short spine.
        const top = runNodes.length === 1 ? first.pos.cardTop : first.pos.y;
        const bottom = runNodes.length === 1 ? first.pos.cardBottom : last.pos.y;
        const height = bottom - top;

        if (height > 0) {
          spines.push({ x: first.pos.x, top, height, fade: false });
        }

        // --- Edge consolidation (only for multi-node runs) ---
        if (runNodes.length > 1) {
          const runIdSet = new Set(runNodes.map(n => n.id));

          // Group incoming edges by external source
          const incomingBySource = new Map();
          for (const rn of runNodes) {
            const node = DataStore.map.get(rn.id);
            if (!node) continue;
            for (const pid of (node.prevIds || [])) {
              if (runIdSet.has(pid)) continue;          // internal — skip
              if (!incomingBySource.has(pid)) incomingBySource.set(pid, []);
              incomingBySource.get(pid).push(rn.id);
            }
          }
          // Same parent → multiple run members: keep only edge to first
          for (const [sourceId, targets] of incomingBySource) {
            if (targets.length <= 1) continue;
            const firstInRun = runNodes.find(rn => targets.includes(rn.id)).id;
            for (const tid of targets) {
              if (tid !== firstInRun) skipEdges.add(`${sourceId}→${tid}`);
            }
          }

          // Group outgoing edges by external target
          const outgoingByTarget = new Map();
          for (const rn of runNodes) {
            const node = DataStore.map.get(rn.id);
            if (!node) continue;
            for (const nid of (node.nextIds || [])) {
              if (runIdSet.has(nid)) continue;          // internal — skip
              if (!outgoingByTarget.has(nid)) outgoingByTarget.set(nid, []);
              outgoingByTarget.get(nid).push(rn.id);
            }
          }
          // Same target ← multiple run members: keep only edge from last
          for (const [targetId, sources] of outgoingByTarget) {
            if (sources.length <= 1) continue;
            const lastInRun = [...runNodes].reverse().find(rn => sources.includes(rn.id)).id;
            for (const sid of sources) {
              if (sid !== lastInRun) skipEdges.add(`${sid}→${targetId}`);
            }
          }
        }

        runNodes = [];
      };

      for (const entry of entries) {
        if (entry.depth < d) {
          // A shallower node breaks the run
          flushRun();
        } else if (entry.depth === d) {
          // At target depth — extend or start run
          runNodes.push(entry);
        }
        // entry.depth > d: child node, keep run open but don't add
      }
      flushRun(); // close final run
    }
  }

  return { spines, skipEdges };
}

/* ---------------------------------------------------------------------------
 * Main draw function
 * --------------------------------------------------------------------------- */

/**
 * Draws all SVG connectors for the current page.
 *
 * @param {HTMLElement} viewEl — the .map-flow element
 * @param {Array<Object>} visibleNodes — nodes on this page
 */
export function draw(viewEl, visibleNodes) {
  // Clean previous render
  const oldSvg = viewEl.querySelector('.dag-svg');
  if (oldSvg) oldSvg.remove();
  viewEl.querySelectorAll('.stacked-indent-spine').forEach(el => el.remove());

  if (visibleNodes.length === 0) return;

  const { markerPositions, visualRows, trunkX, nodeToRowIdx } =
    collectPositions(viewEl);

  if (markerPositions.size === 0) return;

  // Phase 5: compute indent spines + consolidated edge set for stacked zones
  const syntheticEdges = [];
  const { spines: indentSpines, skipEdges } = computeIndentSpines(viewEl, markerPositions);

  // --- Build SVG with trunk mask ---
  const maskId = `timelineMask-${++maskCounter}`;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'dag-svg');

  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  const mask = document.createElementNS('http://www.w3.org/2000/svg', 'mask');
  mask.setAttribute('id', maskId);

  const whiteBg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  whiteBg.setAttribute('x', '0');
  whiteBg.setAttribute('y', '0');
  whiteBg.setAttribute('width', '100%');
  whiteBg.setAttribute('height', '100%');
  whiteBg.setAttribute('fill', 'white');
  mask.appendChild(whiteBg);

  const mainStrip = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  mainStrip.setAttribute('x', trunkX - 1);
  mainStrip.setAttribute('y', '0');
  mainStrip.setAttribute('width', '2');
  mainStrip.setAttribute('height', '100%');
  mainStrip.setAttribute('fill', 'black');
  mask.appendChild(mainStrip);

  // Phase 5: indent spine mask strips added here
  indentSpines.forEach(spineInfo => {
    const strip = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    strip.setAttribute('x', spineInfo.x - 1);
    strip.setAttribute('y', String(spineInfo.top));
    strip.setAttribute('width', '2');
    strip.setAttribute('height', String(spineInfo.height));
    strip.setAttribute('fill', 'black');
    mask.appendChild(strip);
  });

  defs.appendChild(mask);
  svg.appendChild(defs);

  // --- Draw edges ---
  let allPathData = '';

  // Standard DAG edges
  visibleNodes.forEach(node => {
    (node.nextIds || []).forEach(nextId => {
      if (markerPositions.has(nextId) && !skipEdges.has(`${node.id}→${nextId}`)) {
        allPathData += buildEdgePath(markerPositions, node.id, nextId);
      }
    });
  });

  // Synthetic edges (Phase 5)
  syntheticEdges.forEach(edge => {
    allPathData += buildEdgePath(markerPositions, edge.startId, edge.endId, edge);
  });

  // Terminal return curves
  if (trunkX !== null) {
    allPathData += buildTerminalReturns(
      markerPositions, visibleNodes, trunkX, nodeToRowIdx, visualRows
    );
  }

  // --- Render indent spines (Phase 5) ---
  for (const spineInfo of indentSpines) {
    const fadeZone = spineInfo.fade
      ? Math.min(SPINE_FADE_PX, spineInfo.height * 0.3) : 0;
    const background = spineInfo.fade
      ? `linear-gradient(180deg, var(--spine-color) ${((spineInfo.height - fadeZone) / spineInfo.height * 100).toFixed(1)}%, transparent)`
      : 'var(--spine-color)';
    const spine = document.createElement('div');
    spine.className = 'stacked-indent-spine';
    spine.style.cssText = `
      position: absolute;
      left: ${spineInfo.x - 1}px;
      top: ${spineInfo.top}px;
      height: ${spineInfo.height}px;
      width: var(--spine-width);
      background: ${background};
      pointer-events: none;
      z-index: 1;
    `;
    viewEl.appendChild(spine);
  }

  // --- Append path ---
  if (allPathData) {
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('class', 'dag-edge');
    path.setAttribute('d', allPathData.trim());
    path.setAttribute('mask', `url(#${maskId})`);
    svg.appendChild(path);
  }

  viewEl.prepend(svg);
}
