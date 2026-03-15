/**
 * =============================================================================
 * svg-engine.js — Unified Timeline Spine Engine
 * =============================================================================
 * Draws vertical timeline spines and SVG branch/merge connectors for both
 * parallel (side-by-side) and stacked (indented) node layouts.
 *
 * Algorithm (6 unified rules, applied non-exclusively per transition):
 *
 *   Rule 1 — Parallel Branch: next row has multiple parallel nodes in the
 *            current zone → branch off N spines, one per node.
 *   Rule 2 — Parallel Merge: parallel zone ends → all parallel spines merge
 *            back to the parent spine that spawned them.
 *   Rule 3 — Depth Branch: next node is deeper → branch off a new indented
 *            spine from the current one.
 *   Rule 4 — Depth Continue: next node is equal or deeper → current spine
 *            continues straight down (no gaps).
 *   Rule 5 — Deepest Merge: next node is shallower (or end of zone) AND
 *            the current spine is the deepest in its zone → merge back to
 *            the parent/trunk spine via a return curve.
 *   Rule 6 — Intermediate Fade: next node is shallower (or end of zone)
 *            AND the current spine is NOT the deepest → spine fades out
 *            (no merge curve). The visual taper signals that this depth
 *            level is ending while deeper branches continue.
 *
 * Nesting is recursive: within a parallel column, that column's spine becomes
 * the trunk for rules 3–6. All merges return to the spawning spine.
 *
 * Attachment point: all horizontal branch/merge connectors connect at joinY —
 * the vertical midpoint of the gap between source row bottom and destination
 * row card top. Quadratic corners use radius so spines start/end at
 * joinY ± radius.
 *
 * Dependencies: state.js (AppState), data-store.js (DataStore)
 * Consumers: ui-render.js, main.js, ui-expander.js
 * =============================================================================
 */

import { AppState } from './state.js';
import { DataStore } from './data-store.js';

let observer = null;

/** Maximum pixel distance over which a spine fades from solid to transparent. */
const SPINE_FADE_PX = 60;

/** Horizontal distance below which two markers are considered vertically aligned. */
const STRAIGHT_THRESHOLD = 5;

/** Maximum radius for quadratic corner curves on branch/merge connectors. */
const MAX_CORNER_RADIUS = 12;

/** Half of the spine width (--spine-width: 2px). Used for mask alignment.   */
const SPINE_HALF_W = 1;

/* ---------------------------------------------------------------------------
 * Resize handling
 * --------------------------------------------------------------------------- */

let redrawTimer = null;

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

  // Listen for expander open/close settling — ui-expander.js dispatches this
  // event so it doesn't need to import scheduleRedraw (avoids module coupling).
  document.addEventListener('expander-settled', () => scheduleRedraw());
}

/* ---------------------------------------------------------------------------
 * Geometry helpers
 * --------------------------------------------------------------------------- */

/**
 * Collects marker dot positions and card bounds for every visible node.
 * Returns a Map<nodeId, {x, y, depth, cardTop, cardBottom, visualBottom}>.
 *
 * When an open expander exists in a level-group, ALL sibling nodes in that
 * group receive the expander's bottom as their visualBottom.  This ensures
 * that downstream visual-row grouping and transition-metric computation
 * uniformly account for the extra height regardless of which specific node
 * the expander is attached to or tiny cardTop bucketing differences.
 */
function collectMarkerPositions(viewEl, containerRect) {
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

    // Skip hidden/collapsed nodes (zero-size markers from display:none ancestors)
    if (dotRect.width === 0 && dotRect.height === 0) return;

    const depth = parseInt(row.style.getPropertyValue('--indent-depth')) || 0;

    positions.set(id, {
      x: Math.round(dotRect.left - containerRect.left + dotRect.width / 2),
      y: dotRect.top - containerRect.top + dotRect.height / 2,
      depth,
      cardTop: cardRect.top - containerRect.top,
      cardBottom: cardRect.bottom - containerRect.top,
      visualBottom: cardRect.bottom - containerRect.top
    });
  });

  // --- Propagate open-expander height to ALL sibling nodes in the same
  //     level-group.  An expander is a level-group–wide panel; its height
  //     must be reflected by every node in the group so that visual-row
  //     computation and transition metrics shift uniformly.
  //
  //     Search WITHOUT `:scope >` so we also find expanders that were
  //     moved inside a stack-group by openExpander (stacked mode). ---
  const levelGroups = viewEl.querySelectorAll('.level-group:not([data-zone-absorbed])');
  levelGroups.forEach(group => {
    const openExp = group.querySelector('.level-expander.is-open');
    if (!openExp) return;

    const expInner = openExp.querySelector('.exp-inner');
    if (!expInner) return;

    const expRect = expInner.getBoundingClientRect();
    // Skip zero-height expanders (still animating or collapsed)
    if (expRect.height < 1) return;

    const expBottom = expRect.bottom - containerRect.top;

    // Apply to every node-row in this group (direct children AND
    // nodes inside stack-groups)
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

/**
 * Builds visual row groups from level-groups in the DOM.
 * Each visual row contains the node IDs and the maximum bottom Y coordinate.
 * Returns { visualRows, nodeToRowIdx }.
 */
function buildVisualRows(viewEl, positions) {
  const visualRows = [];
  const nodeToRowIdx = new Map();

  // Gather rows from level-groups (including stack-groups within them)
  const levelGroups = viewEl.querySelectorAll('.level-group:not([data-zone-absorbed])');

  levelGroups.forEach(group => {
    // Collect direct node-rows AND node-rows inside stack-groups
    const nodeRows = group.querySelectorAll(':scope > .node-row, :scope > .stack-group > .node-row');
    if (nodeRows.length === 0) return;

    // Group nodes by their visual row position (same cardTop = same row)
    const rowBuckets = new Map();
    nodeRows.forEach(row => {
      const id = row.dataset.id;
      const pos = positions.get(id);
      if (!pos) return;

      // Round cardTop to nearest 5px to bucket nodes on the same visual row
      const bucket = Math.round(pos.cardTop / 5) * 5;
      if (!rowBuckets.has(bucket)) rowBuckets.set(bucket, []);
      rowBuckets.get(bucket).push(id);
    });

    // Sort buckets by Y position and create visual rows
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

/**
 * Computes the transition geometry between two nodes.
 * Returns { joinY, radius, gapTop, gapBottom, gap } or null.
 */
function getTransitionMetrics(startId, endId, positions) {
  const start = positions.get(startId);
  const end = positions.get(endId);
  if (!start || !end) return null;

  // Launch from the bottom of the entire row (not individual card)
  const gapTop = start.rowBottom !== undefined ? start.rowBottom : start.visualBottom;

  // If edge skips rows, bend in the gap immediately above destination
  let effectiveGapTop = (end.prevRowBottom !== undefined && end.prevRowBottom > gapTop)
    ? end.prevRowBottom
    : gapTop;

  const gapBottom = end.cardTop;

  // When the target card starts above the effective gap top (row overlap
  // caused by taller parallel nodes on the same visual row), fall back to
  // the source card's own bottom. This ensures branch curves have usable
  // vertical space even when parallel siblings are taller than the source.
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
 * Spine block computation (for stacked/indented nodes)
 * --------------------------------------------------------------------------- */

/**
 * Builds contiguous spine blocks for each indent depth level.
 * A spine block is a range of consecutive nodes (in display order) that are
 * all at >= a given depth level.
 *
 * @param {string[]} displayOrder — node IDs in DFS order
 * @param {Map<string, number>} depthMap — nodeId → indent depth
 * @returns {Array<{depth, startId, endId, prevId, nextId}>}
 */
function buildSpineBlocks(displayOrder, depthMap) {
  const blocks = [];
  const depthOf = id => depthMap.get(id) || 0;
  const maxDepth = Math.max(...displayOrder.map(depthOf), 0);

  for (let depth = 1; depth <= maxDepth; depth++) {
    let blockStartIndex = -1;

    const flush = endIndex => {
      if (blockStartIndex === -1) return;
      blocks.push({
        depth,
        startId: displayOrder[blockStartIndex],
        endId: displayOrder[endIndex],
        prevId: blockStartIndex > 0 ? displayOrder[blockStartIndex - 1] : null,
        nextId: endIndex < displayOrder.length - 1 ? displayOrder[endIndex + 1] : null
      });
      blockStartIndex = -1;
    };

    displayOrder.forEach((id, idx) => {
      if (depthOf(id) >= depth) {
        if (blockStartIndex === -1) blockStartIndex = idx;
      } else {
        flush(idx - 1);
      }
    });
    flush(displayOrder.length - 1);
  }

  return blocks;
}

/**
 * Builds transitions (branch-enter and branch-return) between consecutive
 * nodes with different indent depths.
 *
 * @param {string[]} displayOrder — node IDs in DFS order
 * @param {Map<string, number>} depthMap — nodeId → indent depth
 * @returns {Array<{startId, endId, kind, startAtSpine, endAtSpine}>}
 */
function buildTransitions(displayOrder, depthMap) {
  const transitions = [];
  const depthOf = id => depthMap.get(id) || 0;

  for (let i = 0; i < displayOrder.length - 1; i++) {
    const startId = displayOrder[i];
    const endId = displayOrder[i + 1];
    const startDepth = depthOf(startId);
    const endDepth = depthOf(endId);
    if (startDepth === endDepth) continue;

    transitions.push({
      startId,
      endId,
      kind: endDepth > startDepth ? 'branch-enter' : 'branch-return',
      startAtSpine: endDepth < startDepth,
      endAtSpine: endDepth > startDepth
    });
  }

  return transitions;
}


/* ---------------------------------------------------------------------------
 * SVG path drawing
 * --------------------------------------------------------------------------- */

/**
 * Computes the radius for a branch-enter or branch-return curve.
 * Uses the same approach as parallel edges: constrained by horizontal distance
 * and vertical distance from dot centers to the bend point (not by the small
 * inter-card gap). This produces curves that match parallel mode in size.
 */
function getBranchRadius(startId, endId, positions) {
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

/**
 * Generates an SVG path for a branch-enter or branch-return connector.
 * Draws ONLY the curved + horizontal portion. Vertical segments are NOT
 * drawn — HTML spine elements handle those, eliminating SVG↔spine overlap.
 */
function drawBranchPath(startId, endId, positions) {
  const metrics = getTransitionMetrics(startId, endId, positions);
  const start = positions.get(startId);
  const end = positions.get(endId);
  if (!metrics || !start || !end) return '';

  const r = getBranchRadius(startId, endId, positions);
  if (r <= 0) {
    return `M ${start.x} ${metrics.joinY} L ${end.x} ${metrics.joinY} `;
  }

  const dirX = end.x > start.x ? 1 : -1;
  const y = metrics.joinY;

  // Short overlap lines (2px) extend into the HTML spines at each end,
  // ensuring the SVG stroke seamlessly blends with the CSS-rendered spine.
  // Without this, sub-pixel rendering differences between CSS and SVG can
  // produce a visible seam at the junction.
  const OVERLAP = 2;

  return [
    `M ${start.x} ${y - r - OVERLAP}`,
    `L ${start.x} ${y - r}`,
    `Q ${start.x} ${y} ${start.x + dirX * r} ${y}`,
    `L ${end.x - dirX * r} ${y}`,
    `Q ${end.x} ${y} ${end.x} ${y + r}`,
    `L ${end.x} ${y + r + OVERLAP}`,
  ].join(' ') + ' ';
}

/**
 * Generates an SVG path for a general edge (straight or L-shaped with curves).
 */
function drawEdgePath(startId, endId, positions, options = {}) {
  const start = positions.get(startId);
  const end = positions.get(endId);
  if (!start || !end) return '';

  const {
    startAtSpine = false,
    endAtSpine = false,
    kind = 'flow',
    trunkX = null
  } = options;

  // Branch-enter / branch-return use the dedicated branch path
  if (kind === 'branch-enter' || kind === 'branch-return') {
    return drawBranchPath(startId, endId, positions);
  }

  // Helper: check if an X position is covered by an HTML spine (trunk).
  // Verticals at the trunk are handled by the .map-spine HTML element;
  // verticals at non-trunk positions (parallel columns) must be drawn in SVG.
  const hasSpineAt = (x) => trunkX !== null && Math.abs(x - trunkX) < STRAIGHT_THRESHOLD;

  const metrics = getTransitionMetrics(startId, endId, positions);
  const bendY = (metrics && Math.abs(start.x - end.x) >= STRAIGHT_THRESHOLD)
    ? metrics.joinY
    : null;

  // Straight vertical line
  if (bendY === null) {
    // HTML trunk spine covers verticals at the trunk X position.
    // Non-trunk verticals (parallel columns) must be drawn in SVG.
    if (hasSpineAt(start.x)) return '';
    return `M ${start.x} ${start.y} L ${end.x} ${end.y} `;
  }

  const dirX = end.x > start.x ? 1 : -1;
  const startVertical = Math.max(0, bendY - start.y);
  const endVertical = Math.max(0, end.y - bendY);
  const radius = Math.min(
    MAX_CORNER_RADIUS,
    Math.abs(end.x - start.x) / 2,
    startAtSpine ? MAX_CORNER_RADIUS : Math.max(0, startVertical - 2),
    endAtSpine ? MAX_CORNER_RADIUS : Math.max(0, endVertical - 2)
  );

  let d = '';

  // Start vertical: SVG draws it only if no HTML spine at start.x
  if (!hasSpineAt(start.x)) {
    d += `M ${start.x} ${start.y} L ${start.x} ${bendY - radius} `;
  } else {
    d += `M ${start.x} ${bendY - radius} `;
  }

  d += `Q ${start.x} ${bendY} ${start.x + radius * dirX} ${bendY} `;
  d += `L ${end.x - radius * dirX} ${bendY} `;
  d += `Q ${end.x} ${bendY} ${end.x} ${bendY + radius} `;

  // End vertical: SVG draws it only if no HTML spine at end.x
  if (!hasSpineAt(end.x)) {
    d += `L ${end.x} ${end.y} `;
  }

  return d;
}


/* ---------------------------------------------------------------------------
 * Main draw function
 * --------------------------------------------------------------------------- */

/**
 * Draws all timeline spines and SVG connectors for the current view.
 *
 * @param {HTMLElement} viewEl — the .map-flow element
 * @param {Array<Object>} visibleNodes — nodes on this page
 */
export function draw(viewEl, visibleNodes) {
  // --- Find timeline layer (compositing container for spine + SVG) ---
  const timelineLayer = viewEl.querySelector('.timeline-layer');
  const renderTarget = timelineLayer || viewEl;

  // --- Collect old elements for deferred removal (atomic swap) ---
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

  // --- Create SVG element ---
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'dag-svg');

  // --- Determine trunk X (depth-0 / main spine position) ---
  let trunkX = null;
  for (const [, pos] of positions) {
    if (pos.depth === 0) { trunkX = pos.x; break; }
  }
  if (trunkX === null) {
    const firstPos = positions.values().next().value;
    trunkX = firstPos?.x ?? 0;
  }

  // --- Collect indent spine info for both stacked zones and page-level stacking ---
  const indentSpines = [];
  const allPathData = [];

  // --- Detect stacking mode and process accordingly ---
  const stackGroups = viewEl.querySelectorAll('.stack-group');

  if (stackGroups.length > 0) {
    // Check if page is fully stacked: no level-group has multiple direct
    // (non-stack-group) node-rows side by side.
    const levelGroups = viewEl.querySelectorAll('.level-group:not([data-zone-absorbed])');
    let isFullyStacked = true;
    for (const lg of levelGroups) {
      const directRows = lg.querySelectorAll(':scope > .node-row');
      if (directRows.length > 1) {
        isFullyStacked = false;
        break;
      }
    }

    if (isFullyStacked) {
      // ---- FULLY STACKED: unified display order across ALL nodes ----
      // Walk every .node-row in DOM order (top-to-bottom visual order).
      // Non-stacked nodes get depth 0 from --indent-depth being unset.
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
      // All edges handled by unified processing — no parallel edges needed.

    } else {
      // ---- PARTIAL STACKING: per-stack-group + parallel edges ----
      const stackedNodeIds = new Set();

      // Pre-populate stackedNodeIds with ALL stack-group nodes so that
      // BFS lookups during zone trunk spine extension can find nodes in
      // OTHER groups (processed later in the forEach).
      stackGroups.forEach(sg => {
        sg.querySelectorAll(':scope > .node-row').forEach(row => {
          if (row.dataset.id && positions.has(row.dataset.id)) {
            stackedNodeIds.add(row.dataset.id);
          }
        });
      });

      // Track which groups have terminal returns handled by processStackedZone
      const groupHasTerminalReturn = new Map();

      stackGroups.forEach(sg => {
        const nodeRows = sg.querySelectorAll(':scope > .node-row');
        if (nodeRows.length < 2) return;

        const displayOrder = [];
        const depthMap = new Map();
        nodeRows.forEach(row => {
          const id = row.dataset.id;
          if (!id || !positions.has(id)) return;
          displayOrder.push(id);
          depthMap.set(id, parseInt(row.style.getPropertyValue('--indent-depth')) || 0);
          stackedNodeIds.add(id);
        });

        if (displayOrder.length < 2) return;

        // Determine the trunk X for this stack-group
        let sgTrunkX = null;
        for (const id of displayOrder) {
          const d = depthMap.get(id);
          const pos = positions.get(id);
          if (d === 0 && pos) { sgTrunkX = pos.x; break; }
        }
        if (sgTrunkX === null) {
          const minDepth = Math.min(...displayOrder.map(id => depthMap.get(id) || 0));
          for (const id of displayOrder) {
            if ((depthMap.get(id) || 0) === minDepth) {
              sgTrunkX = positions.get(id)?.x ?? trunkX;
              break;
            }
          }
        }

        // Check if the zone ends off its own trunk (needs terminal return)
        const zoneLastId = displayOrder[displayOrder.length - 1];
        const zoneLastPos = positions.get(zoneLastId);
        const hasTerminalReturn = zoneLastPos &&
          Math.abs(zoneLastPos.x - sgTrunkX) >= STRAIGHT_THRESHOLD;

        // Pass mainTrunkX so the deepest return curve goes all the way
        // to the main trunk (matching fully-stacked behaviour).
        processStackedZone(displayOrder, depthMap, positions, sgTrunkX,
                           indentSpines, allPathData,
                           hasTerminalReturn ? trunkX : null);

        // Zone trunk spine when offset from main trunk
        if (Math.abs(sgTrunkX - trunkX) >= STRAIGHT_THRESHOLD) {
          const firstId = displayOrder[0];
          const lastId = displayOrder[displayOrder.length - 1];
          const firstPos = positions.get(firstId);
          const lastPos = positions.get(lastId);
          if (firstPos && lastPos) {
            let spineBottom = lastPos.visualBottom;

            // BFS from all nodes in this group through their descendants.
            // If deeper stacked descendants exist (X >= sgTrunkX), extend
            // the zone trunk spine to cover them — the trunk visually
            // continues as long as deeper branches are active beneath it.
            const visibleMap = new Map(visibleNodes.map(n => [n.id, n]));
            const bfsVisited = new Set(displayOrder);
            const bfsQueue = [];
            for (const id of displayOrder) {
              const node = visibleMap.get(id);
              for (const nid of (node?.nextIds || [])) {
                if (!bfsVisited.has(nid) && positions.has(nid)) bfsQueue.push(nid);
              }
            }
            while (bfsQueue.length > 0) {
              const id = bfsQueue.shift();
              if (bfsVisited.has(id)) continue;
              bfsVisited.add(id);
              const p = positions.get(id);
              if (!p) continue;
              // Stop at main-trunk nodes (merge points)
              if (Math.abs(p.x - trunkX) < STRAIGHT_THRESHOLD) continue;
              // Only follow stacked descendants at deeper-or-equal X
              if (!stackedNodeIds.has(id) || p.x < sgTrunkX) continue;
              spineBottom = Math.max(spineBottom, p.rowBottom || p.visualBottom);
              const node = visibleMap.get(id);
              for (const nid of (node?.nextIds || [])) {
                if (!bfsVisited.has(nid) && positions.has(nid)) bfsQueue.push(nid);
              }
            }

            // Fade when zone ends deeper than the trunk depth (Rule 6)
            const lastDepth = depthMap.get(lastId) || 0;
            indentSpines.push({
              x: Math.round(sgTrunkX),
              top: firstPos.y,
              height: spineBottom - firstPos.y,
              depth: 0,
              fade: lastDepth > 0
            });
          }
        }

        // Record per-group for edge-drawing decisions below
        const sgIndex = stackedNodeIds.size; // unique key
        sg._groupKey = sgIndex;
        if (hasTerminalReturn) groupHasTerminalReturn.set(sg, true);
      });

      // Build maps for stack-group membership: first/last node per group
      const nodeToGroup = new Map();   // nodeId → groupIndex
      const groupFirst = new Map();    // groupIndex → first nodeId
      const groupLast = new Map();     // groupIndex → last nodeId
      const groupSg = new Map();       // groupIndex → stack-group element
      let groupIdx = 0;
      stackGroups.forEach(sg => {
        const rows = sg.querySelectorAll(':scope > .node-row');
        const ids = Array.from(rows).map(r => r.dataset.id).filter(Boolean);
        if (ids.length === 0) return;
        const gi = groupIdx++;
        ids.forEach(id => nodeToGroup.set(id, gi));
        groupFirst.set(gi, ids[0]);
        groupLast.set(gi, ids[ids.length - 1]);
        groupSg.set(gi, sg);
      });

      // Draw edges, handling stacked ↔ non-stacked boundaries:
      //  - Non-stacked → non-stacked: draw normally
      //  - Non-stacked → stacked: draw edge to the GROUP'S FIRST node only
      //  - Stacked → non-stacked: skip if processStackedZone drew the terminal
      //    return (Rule 5 already connects deepest spine back to trunk);
      //    otherwise draw edge from the GROUP'S LAST node.
      //  - Stacked → stacked (same group): skip (handled by processStackedZone)
      //  - Stacked → stacked (different groups): draw from last of source to first of target
      const visibleIdSet = new Set(visibleNodes.map(n => n.id));
      const drawnEdgeKeys = new Set();  // prevent duplicate edges

      visibleNodes.forEach(node => {
        const srcStacked = stackedNodeIds.has(node.id);
        const srcGroup = nodeToGroup.get(node.id);

        // If source is stacked, only the LAST node of its group emits outgoing edges
        if (srcStacked && node.id !== groupLast.get(srcGroup)) return;

        (node.nextIds || []).forEach(nextId => {
          if (!positions.has(nextId)) return;

          const tgtStacked = stackedNodeIds.has(nextId);
          const tgtGroup = nodeToGroup.get(nextId);

          // Skip intra-group edges (spine handles vertical connection)
          if (srcStacked && tgtStacked && srcGroup === tgtGroup) return;

          // Skip stacked→non-stacked edges when processStackedZone already
          // drew the terminal return curve to the main trunk (Rule 5).
          if (srcStacked && !tgtStacked) {
            const sg = groupSg.get(srcGroup);
            if (sg && groupHasTerminalReturn.has(sg)) return;
          }

          // For edges INTO a stacked group, redirect to the group's first node
          let effectiveTarget = tgtStacked ? groupFirst.get(tgtGroup) : nextId;
          // For edges FROM a stacked group, source is already the last node (filtered above)
          const effectiveSource = srcStacked ? groupLast.get(srcGroup) : node.id;

          if (!effectiveTarget || !effectiveSource) return;

          // Skip edges where the target is on the same visual row or above
          // the source. These arise when a redirected group-first node sits
          // on the same row as the source (e.g. 2.1.3 → 2.1.6 on page 2.1),
          // which would produce a backwards U-shaped path.
          //
          // However, when the skip fires on a REDIRECTED target, fall back to
          // the actual target node.  Off-trunk sources (e.g. 2.1.4) need their
          // own edge to children deep inside a stack-group even when the
          // group-first node sits above them.
          const srcPos = positions.get(effectiveSource);
          let tgtPos = positions.get(effectiveTarget);
          if (srcPos && tgtPos) {
            // Use cardBottom (not rowBottom) — rowBottom can be inflated by
            // an open expander in the same level-group, which would cause
            // edges from unrelated sibling nodes to be wrongly skipped.
            const srcBottom = srcPos.cardBottom || srcPos.visualBottom;
            if (tgtPos.cardTop <= srcBottom) {
              // Redirected target is above source — try the actual target
              if (effectiveTarget !== nextId) {
                const actualTgtPos = positions.get(nextId);
                if (actualTgtPos && actualTgtPos.cardTop > srcBottom) {
                  effectiveTarget = nextId;
                  tgtPos = actualTgtPos;
                } else {
                  return;
                }
              } else {
                return;
              }
            }
          }

          // Deduplicate: same effective edge may arise from multiple DAG edges
          const edgeKey = `${effectiveSource}->${effectiveTarget}`;
          if (drawnEdgeKeys.has(edgeKey)) return;
          drawnEdgeKeys.add(edgeKey);

          allPathData.push(drawEdgePath(effectiveSource, effectiveTarget, positions, { trunkX }));
        });
      });

      drawTerminalReturns(visibleNodes, visibleIdSet, positions, trunkX,
                          visualRows, nodeToRowIdx, stackedNodeIds, allPathData);

      // Build column spines for non-stacked parallel parents with off-trunk subtrees
      indentSpines.push(...buildColumnSpines(visibleNodes, positions, trunkX, stackedNodeIds));
    }

  } else {
    // ---- NO STACK GROUPS: pure parallel edge drawing ----
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

    // Build column spines for non-trunk parallel parents with off-trunk subtrees
    indentSpines.push(...buildColumnSpines(visibleNodes, positions, trunkX));
  }

  // --- Render SVG paths (no mask needed — vertical segments are not drawn) ---
  const combinedPath = allPathData.join('').trim();
  if (combinedPath) {
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('class', 'dag-edge');
    path.setAttribute('d', combinedPath);
    svg.appendChild(path);
  }

  // --- Build indent spine HTML elements ---
  const newIndentSpines = [];
  for (const spineInfo of indentSpines) {
    const fadeZone = spineInfo.fade
      ? Math.min(SPINE_FADE_PX, spineInfo.height * 0.3)
      : 0;
    // Use solid (opaque) color — the timeline-layer opacity handles transparency.
    const background = spineInfo.fade
      ? `linear-gradient(180deg, var(--spine-color-solid) ${((spineInfo.height - fadeZone) / spineInfo.height * 100).toFixed(1)}%, transparent)`
      : 'var(--spine-color-solid)';

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
    newIndentSpines.push(spine);
  }

  // --- Swap old elements for new ---
  if (oldSvg) oldSvg.remove();
  oldIndentSpines.forEach(el => el.remove());
  renderTarget.appendChild(svg);
  newIndentSpines.forEach(s => renderTarget.appendChild(s));

}


/* ---------------------------------------------------------------------------
 * Stacked zone processing (Rules 3–6)
 * --------------------------------------------------------------------------- */

/**
 * Processes a stacked zone: computes spine blocks and transitions,
 * then generates SVG paths and spine info.
 *
 * @param {string[]} displayOrder — node IDs in DFS display order
 * @param {Map<string, number>} depthMap — nodeId → indent depth
 * @param {Map<string, Object>} positions — marker positions
 * @param {number} zoneTrunkX — X position of the trunk spine for this zone
 * @param {Array} indentSpines — accumulator for spine info objects
 * @param {Array} allPathData — accumulator for SVG path strings
 */
function processStackedZone(displayOrder, depthMap, positions, zoneTrunkX,
                            indentSpines, allPathData, mainTrunkX = null) {
  const spineBlocks = buildSpineBlocks(displayOrder, depthMap);
  const transitions = buildTransitions(displayOrder, depthMap);

  // Pre-compute terminal return mergeY so spine bottoms can be capped
  // to prevent overlap with the return curve SVG strokes.
  //
  // Instead of assuming a fixed 20px gap, measure the actual gap to the
  // next trunk-level node below the zone.  This keeps the terminal return
  // curve aligned with parallel edges that share the same destination
  // (they use getTransitionMetrics which measures the real gap).
  const termLastId = displayOrder[displayOrder.length - 1];
  const termLastPos = positions.get(termLastId);
  let terminalMergeY = null;
  if (termLastPos && Math.abs(termLastPos.x - zoneTrunkX) >= STRAIGHT_THRESHOLD) {
    const termRowBottom = termLastPos.rowBottom || termLastPos.visualBottom;
    const returnTargetXEarly = mainTrunkX !== null ? mainTrunkX : zoneTrunkX;
    // Find the closest node below the zone at the return target X
    let nextTrunkCardTop = null;
    for (const [, pos] of positions) {
      if (Math.abs(pos.x - returnTargetXEarly) < STRAIGHT_THRESHOLD && pos.cardTop > termRowBottom) {
        if (nextTrunkCardTop === null || pos.cardTop < nextTrunkCardTop) {
          nextTrunkCardTop = pos.cardTop;
        }
      }
    }
    const actualGap = nextTrunkCardTop !== null
      ? nextTrunkCardTop - termRowBottom
      : 20;  // fallback
    terminalMergeY = termRowBottom + actualGap / 2;
  }

  // --- Generate indent spine HTML elements (Rule 4 — depth continue) ---
  spineBlocks.forEach(block => {
    const firstPos = positions.get(block.startId);
    const lastPos = positions.get(block.endId);
    if (!firstPos || !lastPos) return;

    const prevDepth = block.prevId
      ? (positions.get(block.prevId)?.depth ?? depthMap.get(block.prevId) ?? 0)
      : 0;
    const nextDepth = block.nextId
      ? (positions.get(block.nextId)?.depth ?? depthMap.get(block.nextId) ?? 0)
      : 0;

    // Top of spine: if entered from a shallower depth, start exactly at the
    // entry curve endpoint (joinY + r). No overlap — prevents opacity doubling.
    let top = firstPos.y;
    if (block.prevId && prevDepth < block.depth) {
      const r = getBranchRadius(block.prevId, block.startId, positions);
      const entryMetrics = getTransitionMetrics(block.prevId, block.startId, positions);
      if (entryMetrics && r > 0) {
        top = entryMetrics.joinY + r;
      }
    }

    // Bottom of spine: depends on what follows.
    // Ends exactly at the exit curve start (joinY - r) — no overlap.
    let bottom = lastPos.visualBottom;
    let fade = false;

    if (block.nextId) {
      const exitMetrics = getTransitionMetrics(block.endId, block.nextId, positions);

      if (nextDepth < block.depth) {
        // Rule 5: merging back — spine ends at the merge curve
        if (exitMetrics) {
          const r = getBranchRadius(block.endId, block.nextId, positions);
          bottom = Math.max(top + 8, exitMetrics.joinY - r);
          // Fade if the block's last node is deeper than this spine's depth
          const endDepth = positions.get(block.endId)?.depth ?? depthMap.get(block.endId) ?? block.depth;
          fade = endDepth > block.depth;
        }
      } else if (nextDepth === block.depth) {
        // Same depth continues — spine fades at the boundary
        if (exitMetrics) {
          const r = getBranchRadius(block.endId, block.nextId, positions);
          bottom = Math.max(top + 8, exitMetrics.joinY - r);
        }
        fade = true;
      }
      // If nextDepth > block.depth: spine continues (Rule 4), bottom stays at visualBottom
    } else {
      // Terminal spine: last block in display order — no nextId.
      // Fade if the block's last node is deeper than this spine's depth
      // (matching Rule 5 behavior for zones that end mid-depth).
      const endDepth = positions.get(block.endId)?.depth ?? depthMap.get(block.endId) ?? block.depth;
      fade = endDepth > block.depth;
      // Cap bottom to prevent overlap with the terminal return curve
      if (terminalMergeY !== null && Math.abs(firstPos.x - zoneTrunkX) >= STRAIGHT_THRESHOLD) {
        const dx = Math.abs(zoneTrunkX - firstPos.x);
        const termR = Math.min(
          MAX_CORNER_RADIUS,
          dx / 2,
          Math.max(0, Math.abs(terminalMergeY - lastPos.y) - 2)
        );
        bottom = Math.min(bottom, terminalMergeY - termR);
      }
    }

    const height = bottom - top;
    if (height > 0 && Math.abs(firstPos.x - zoneTrunkX) >= STRAIGHT_THRESHOLD) {
      indentSpines.push({
        x: Math.round(firstPos.x),
        top,
        height,
        depth: block.depth,
        fade
      });
    }
  });

  // --- Generate SVG branch/merge paths (Rules 3, 5 and 6) ---
  transitions.forEach(edge => {
    allPathData.push(drawEdgePath(edge.startId, edge.endId, positions, edge));
  });

  // --- Terminal return curves (Rules 5 & 6): end of display order off-trunk ---
  const lastId = displayOrder[displayOrder.length - 1];
  const lastPos = positions.get(lastId);
  if (lastPos && Math.abs(lastPos.x - zoneTrunkX) >= STRAIGHT_THRESHOLD) {
    const lastDepth = depthMap.get(lastId) || 0;
    if (lastDepth > 0) {
      // Find the DEEPEST active depth and its X position.
      // Walk backwards until we hit a depth-0 (trunk) node.
      let deepestDepth = 0;
      let deepestX = null;
      for (let i = displayOrder.length - 1; i >= 0; i--) {
        const id = displayOrder[i];
        const d = depthMap.get(id) || 0;
        if (d === 0) break;           // reached trunk — stop
        const pos = positions.get(id);
        if (pos && d > deepestDepth) {
          deepestDepth = d;
          deepestX = pos.x;
        }
      }

      // Compute merge Y: below the last row.
      // Use the actual gap to the next trunk node (matching getTransitionMetrics)
      // so parallel edges and terminal returns align perfectly.
      const rowBottomOfLast = lastPos.rowBottom || lastPos.visualBottom;
      const returnTargetX = mainTrunkX !== null ? mainTrunkX : zoneTrunkX;
      let nextTrunkCardTop = null;
      for (const [, pos] of positions) {
        if (Math.abs(pos.x - returnTargetX) < STRAIGHT_THRESHOLD && pos.cardTop > rowBottomOfLast) {
          if (nextTrunkCardTop === null || pos.cardTop < nextTrunkCardTop) {
            nextTrunkCardTop = pos.cardTop;
          }
        }
      }
      const actualGap = nextTrunkCardTop !== null
        ? nextTrunkCardTop - rowBottomOfLast
        : 20;  // fallback
      const mergeY = rowBottomOfLast + actualGap / 2;

      // Rule 5 — Deepest Merge: ONLY the deepest spine gets a return curve.
      // Intermediate spines (Rule 6) just fade — no merge curves needed.
      // Target: returnTargetX computed above.

      if (deepestX !== null && Math.abs(deepestX - returnTargetX) >= STRAIGHT_THRESHOLD) {
        const dirX = returnTargetX > deepestX ? 1 : -1;
        const radius = Math.min(
          MAX_CORNER_RADIUS,
          Math.abs(returnTargetX - deepestX) / 2,
          Math.max(0, Math.abs(mergeY - lastPos.y) - 2)
        );

        // Only curves + horizontal — no vertical segments
        allPathData.push(
          `M ${deepestX} ${mergeY - radius} ` +
          `Q ${deepestX} ${mergeY} ${deepestX + radius * dirX} ${mergeY} ` +
          `L ${returnTargetX - radius * dirX} ${mergeY} ` +
          `Q ${returnTargetX} ${mergeY} ${returnTargetX} ${mergeY + radius} `
        );
      }
    }
  }
}


/* ---------------------------------------------------------------------------
 * Parallel column spines (Rule 4 analog for parallel layout)
 * --------------------------------------------------------------------------- */

/**
 * Builds HTML spine elements for non-trunk parallel nodes that own a subtree.
 * A "column spine" acts as a local trunk for a node's descendant subtree in
 * parallel layout — the visual analog of Rule 4 (depth-continue).
 *
 * The BFS stops at trunk nodes (nodes at trunkX) because those are
 * convergence/merge points where branches rejoin the main spine. This
 * prevents the spine from extending through merge points and behind
 * unrelated rows (which was the bug with the previous implementation).
 *
 * @param {Array} visibleNodes — nodes on this page
 * @param {Map} positions — marker positions from collectMarkerPositions
 * @param {number} trunkX — X position of the main trunk spine
 * @param {Set} [excludeIds] — node IDs to skip (e.g. stacked nodes)
 * @returns {Array<{x, top, height, depth, fade}>} spine info objects
 */
function buildColumnSpines(visibleNodes, positions, trunkX, excludeIds = new Set()) {
  const spines = [];
  const visibleMap = new Map(visibleNodes.map(n => [n.id, n]));
  const visibleIdSet = new Set(visibleNodes.map(n => n.id));

  // Find non-trunk nodes that have visible successors ALSO at non-trunk positions.
  // Simple terminals (whose only successors are on the trunk) don't need column spines.
  const columnRoots = [];
  for (const node of visibleNodes) {
    if (excludeIds.has(node.id)) continue;
    const pos = positions.get(node.id);
    if (!pos) continue;
    if (Math.abs(pos.x - trunkX) < STRAIGHT_THRESHOLD) continue;

    // Check if any visible successor is also off-trunk
    const hasOffTrunkChild = (node.nextIds || []).some(nid => {
      const cPos = positions.get(nid);
      return cPos && Math.abs(cPos.x - trunkX) >= STRAIGHT_THRESHOLD;
    });
    if (!hasOffTrunkChild) continue;

    columnRoots.push(node);
  }

  if (columnRoots.length === 0) return spines;

  // Group column roots by X position to merge overlapping spines.
  const columns = new Map(); // xKey → { x, rootIds[], minY, maxBottom }

  for (const node of columnRoots) {
    const pos = positions.get(node.id);
    const xKey = Math.round(pos.x);
    if (!columns.has(xKey)) {
      columns.set(xKey, { x: pos.x, rootIds: [], minY: Infinity, maxBottom: 0 });
    }
    const col = columns.get(xKey);
    col.rootIds.push(node.id);
    col.minY = Math.min(col.minY, pos.y);
    col.maxBottom = Math.max(col.maxBottom, pos.visualBottom);
  }

  for (const [, col] of columns) {
    // BFS from all column roots to find the deepest off-trunk descendant.
    // STOP at trunk nodes — those are merge/convergence points.
    const visited = new Set(col.rootIds);
    const queue = [];
    let maxBottom = col.maxBottom;

    for (const rootId of col.rootIds) {
      const node = visibleMap.get(rootId);
      for (const nid of (node?.nextIds || [])) {
        if (visibleIdSet.has(nid) && !visited.has(nid)) queue.push(nid);
      }
    }

    while (queue.length > 0) {
      const id = queue.shift();
      if (visited.has(id)) continue;
      visited.add(id);

      const p = positions.get(id);
      if (!p) continue;

      // Stop at trunk nodes — they're merge points, not part of this subtree
      if (Math.abs(p.x - trunkX) < STRAIGHT_THRESHOLD) continue;

      const isSameX  = Math.abs(p.x - col.x) < STRAIGHT_THRESHOLD;
      const isStacked = excludeIds.has(id);

      // Determine whether to extend the spine height and continue BFS.
      //  • Same-X descendants: always extend & traverse (direct column chain).
      //  • Stacked descendants at X >= col.x: extend & traverse — they are
      //    visually nested deeper in this column's subtree. A stacked node
      //    at X < col.x is in a shallower parent zone (e.g. 3.4 at x=76
      //    under 3.3 at x=342) — the parent trunk spine handles those.
      //  • Different-X non-stacked: stop — traversing through other columns
      //    would find spurious same-X descendants (e.g. 3.3→3.5→3.8).
      let shouldExtend  = isSameX;
      let shouldTraverse = isSameX;

      if (isStacked && !isSameX) {
        if (p.x >= col.x) {
          shouldExtend  = true;
          shouldTraverse = true;
        }
      }

      if (shouldExtend) {
        maxBottom = Math.max(maxBottom, p.rowBottom || p.visualBottom);
      }
      if (!shouldTraverse) continue;

      const n = visibleMap.get(id);
      for (const nid of (n?.nextIds || [])) {
        if (visibleIdSet.has(nid) && !visited.has(nid)) queue.push(nid);
      }
    }

    // Only create the spine if BFS found same-X descendants that extend
    // beyond the root nodes. Otherwise there's no subtree to connect.
    if (maxBottom <= col.maxBottom) continue;

    const height = maxBottom - col.minY;
    if (height > 8) {
      spines.push({
        x: Math.round(col.x),
        top: col.minY,
        height,
        depth: 0,
        fade: true
      });
    }
  }

  return spines;
}


/* ---------------------------------------------------------------------------
 * Parallel terminal returns (Rule 2)
 * --------------------------------------------------------------------------- */

/**
 * Draws return curves for parallel nodes that have no visible successors
 * and are horizontally offset from the trunk.
 */
function drawTerminalReturns(visibleNodes, visibleIdSet, positions, trunkX,
                             visualRows, nodeToRowIdx, excludeIds, allPathData) {
  const terminalOffSpine = visibleNodes.filter(node => {
    if (excludeIds.has(node.id)) return false;
    if (node.nextIds?.some(nid => visibleIdSet.has(nid))) return false;
    const pos = positions.get(node.id);
    return pos && Math.abs(pos.x - trunkX) >= STRAIGHT_THRESHOLD;
  });

  if (terminalOffSpine.length === 0) return;

  // Group by X position (only keep the deepest node at each X)
  const byX = new Map();
  for (const node of terminalOffSpine) {
    const pos = positions.get(node.id);
    const xKey = Math.round(pos.x);
    if (!byX.has(xKey) || pos.y > byX.get(xKey).y) {
      byX.set(xKey, pos);
    }
  }

  // Compute standard gap between rows
  const firstTerminalRowIdx = Math.min(
    ...terminalOffSpine.map(n => nodeToRowIdx.get(n.id)).filter(i => i !== undefined)
  );
  let standardGap = 20;
  if (firstTerminalRowIdx > 0 && visualRows[firstTerminalRowIdx]) {
    const sampleIds = visualRows[firstTerminalRowIdx].nodeIds;
    if (sampleIds.length > 0) {
      const samplePos = positions.get(sampleIds[0]);
      if (samplePos) {
        const rawGap = samplePos.cardTop - visualRows[firstTerminalRowIdx - 1].bottom;
        // When an open expander inflates the previous row's bottom beyond the
        // terminal nodes' cardTop the raw gap goes negative.  Clamp to the
        // default so the merge line always lands *below* maxRowBottom.
        standardGap = Math.max(rawGap, 20);
      }
    }
  }

  // Find the max row bottom among all terminal nodes
  let maxRowBottom = 0;
  for (const node of visibleNodes) {
    if (!node.nextIds?.some(nid => visibleIdSet.has(nid))) {
      const pos = positions.get(node.id);
      if (pos) maxRowBottom = Math.max(maxRowBottom, pos.rowBottom);
    }
  }
  const mergeY = maxRowBottom + standardGap / 2;

  for (const [, pos] of byX) {
    const dirX = trunkX > pos.x ? 1 : -1;
    const radius = Math.min(
      MAX_CORNER_RADIUS,
      Math.abs(trunkX - pos.x) / 2,
      Math.max(0, Math.abs(mergeY - pos.y) - 2)
    );

    // Vertical from dot down to merge curve, then curve back to trunk.
    // These nodes are always off-trunk (filtered above), so SVG must
    // draw the vertical — no HTML spine exists at this X position.
    allPathData.push(
      `M ${pos.x} ${pos.y} ` +
      `L ${pos.x} ${mergeY - radius} ` +
      `Q ${pos.x} ${mergeY} ${pos.x + radius * dirX} ${mergeY} ` +
      `L ${trunkX - radius * dirX} ${mergeY} ` +
      `Q ${trunkX} ${mergeY} ${trunkX} ${mergeY + radius} `
    );
  }
}
