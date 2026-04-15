/**
 * =============================================================================
 * 1. CONSTANTS
 * =============================================================================
 * Central location for all timing values and configuration.
 * CSS_TRANSITION_MS must match the animation duration in styles.css §20.
 */
const ANIMATION_SPEEDS = {
  CSS_TRANSITION_MS: 500,
  SCROLL_DELAY_MS: 510
};

/**
 * Maximum pixel distance over which a spine fades from solid to transparent.
 * Clamped to 30% of the spine's total height so short spines don't over-fade.
 */
const SPINE_FADE_PX = 60;

let maskCounter = 0;

/**
 * Per-flex-child width threshold (px) below which a parallel level-group
 * collapses into a stacked indented list.
 *
 * Calibrated from real-world layout measurements:
 *   3-child row (e.g. 2.2-2.4): controls wrap at ~904px viewport → per-child ≈ 289
 *   2-child row (e.g. 2.6-2.7): controls wrap at ~569px viewport → per-child ≈ 267
 * A threshold of 290 nails the 3-child case and triggers ~47px early for 2-child,
 * which is acceptable since cards are already very narrow at that point.
 *
 * The metric (groupWidth / childCount) is stable regardless of stacked/unstacked
 * state because the group fills its parent either way, so no hysteresis is needed.
 */
const STACK_THRESHOLD = 290;


/**
 * =============================================================================
 * 2. DATA STORE
 * =============================================================================
 * Holds the loaded JSON data. Populated once during bootstrap, then read-only.
 *   config  – page-level settings (title, subtitle, nodePrefix, etc.)
 *   nodes   – flat array of all node objects (augmented with .color and .hue)
 *   map     – Map<nodeId, node> for O(1) lookups
 */
const DataStore = {
  config: {},
  nodes: [],
  map: new Map()
};


/**
 * =============================================================================
 * 3. APPLICATION STATE
 * =============================================================================
 * All mutable UI state lives here. Background tints are managed through a
 * single updateTints() method to prevent the scattered set/clear pattern
 * that previously made tint state fragile.
 */
const AppState = {
  theme: localStorage.getItem('theme') || 'dark',
  activeNodeId: null,
  currentParentId: null,
  isTransitioning: false,
  isStackTransitioning: false,

  searchConfig: {
    deep: true,
    global: true
  },

  /* ------------------------------------------------------------------
   * Theme management
   * ------------------------------------------------------------------ */
  toggleTheme() {
    document.body.classList.add('theme-transition');
    this.theme = this.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', this.theme);
    this.applyTheme();
    setTimeout(() => document.body.classList.remove('theme-transition'), 300);
  },

  applyTheme() {
    document.documentElement.setAttribute('data-theme', this.theme);
    if (AppUI.els.themeToggle) {
      const isLight = this.theme === 'light';
      AppUI.els.themeToggle.textContent = isLight ? '☀️ Light' : '🌙 Dark';
      AppUI.els.themeToggle.setAttribute('aria-label', `Switch to ${isLight ? 'dark' : 'light'} mode`);
    }
  },

  /* ------------------------------------------------------------------
   * Background tint management (centralized)
   *
   * Two CSS custom properties drive the background gradients:
   *   --bg-tint       (left side)  – reflects the current page's hue
   *   --bg-tint-right (right side) – reflects the active expander's hue
   *
   * Call updateTints() whenever page context or expander state changes.
   * Pass only the properties that are changing; omitted keys stay as-is.
   *
   * Examples:
   *   AppState.updateTints({ page: 'transparent', expander: 'transparent' });
   *   AppState.updateTints({ expander: `hsla(${hue}, 80%, 50%, 0.35)` });
   * ------------------------------------------------------------------ */
  updateTints({ page, expander } = {}) {
    const style = document.body.style;
    if (page !== undefined)     style.setProperty('--bg-tint', page);
    if (expander !== undefined) style.setProperty('--bg-tint-right', expander);
  }
};


/**
 * =============================================================================
 * 4. PERCEPTUAL COLOR ENGINE
 * =============================================================================
 * Assigns visually distinct hues to sibling nodes using perceptual anchors.
 * The anchors are hand-tuned to avoid metameric confusion zones.
 */
function getPerceptualHue(index, totalNodes) {
  const anchors = [0, 30, 55, 130, 180, 225, 260, 315, 340];
  if (totalNodes <= anchors.length) return anchors[index];

  const progress = index / (totalNodes - 1);
  const position = progress * (anchors.length - 1);
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  const fraction = position - lower;

  if (lower >= anchors.length - 1) return anchors[anchors.length - 1];
  return anchors[lower] + fraction * (anchors[upper] - anchors[lower]);
}


/**
 * =============================================================================
 * 5. DAG GRAPH ENGINE
 * =============================================================================
 * Computes the topological level (row) for each visible node and sorts
 * columns by barycenter to minimize edge crossings. Injects invisible
 * "dummy" spacer nodes for edges that skip levels, so the flex layout
 * holds visual lanes for SVG connectors.
 */
const GraphEngine = {
  computeLevels(visibleNodes) {
    const nodeMap = new Map(visibleNodes.map(n => [n.id, n]));
    const levels = new Map();

    function getLevel(nodeId) {
      if (levels.has(nodeId)) return levels.get(nodeId);
      const node = nodeMap.get(nodeId);
      if (!node?.prevIds?.length) { levels.set(nodeId, 0); return 0; }

      let maxPrev = -1;
      for (const prevId of node.prevIds) {
        if (nodeMap.has(prevId)) maxPrev = Math.max(maxPrev, getLevel(prevId));
      }
      const level = maxPrev + 1;
      levels.set(nodeId, level);
      return level;
    }

    visibleNodes.forEach(n => getLevel(n.id));

    let maxLevel = -1;
    for (const lvl of levels.values()) if (lvl > maxLevel) maxLevel = lvl;

    const rows = Array.from({ length: maxLevel + 1 }, () => []);

    // Assign nodes to rows; inject dummies for long edges
    visibleNodes.forEach(node => {
      const nodeLvl = levels.get(node.id);
      rows[nodeLvl].push(node);

      if (node.nextIds) {
        node.nextIds.forEach(nextId => {
          if (!nodeMap.has(nextId)) return;
          const nextLvl = levels.get(nextId);
          for (let i = nodeLvl + 1; i < nextLvl; i++) {
            rows[i].push({ isDummy: true, sourceId: node.id, targetId: nextId });
          }
        });
      }
    });

    // Sort each row by barycenter (average X-position of parents in the row above)
    for (let i = 1; i <= maxLevel; i++) {
      rows[i].sort((a, b) => {
        const barycenter = (n) => {
          if (n.isDummy) {
            return rows[i - 1].findIndex(p =>
              p.id === n.sourceId || (p.isDummy && p.sourceId === n.sourceId));
          }
          let sum = 0, count = 0;
          n.prevIds.forEach(pid => {
            const idx = rows[i - 1].findIndex(p =>
              p.id === pid || (p.isDummy && p.targetId === n.id && p.sourceId === pid));
            if (idx !== -1) { sum += idx; count++; }
          });
          return count === 0 ? 0 : sum / count;
        };
        return barycenter(a) - barycenter(b);
      });
    }

    return rows;
  }
};


/**
 * =============================================================================
 * 6. SVG CONNECTOR ENGINE
 * =============================================================================
 * Draws DAG edge paths between node markers. All coordinates are read from
 * the DOM at draw-time via getBoundingClientRect() on .marker-dot elements,
 * so nothing here needs to stay in sync with CSS layout values.
 *
 * A mask prevents SVG paths from drawing over the HTML spine element.
 */
const SVGEngine = {
  observer: null,

  /** Shared redraw trigger — called by both ResizeObserver and window resize. */
  _scheduleRedraw() {
    if (AppState.isTransitioning || AppState.isStackTransitioning) return;
    const viewEl = document.querySelector('.map-flow');
    if (viewEl) {
      AppUI.applyResponsiveRunLayout(viewEl);
      const visibleNodes = DataStore.nodes.filter(n => n.parentId === AppState.currentParentId);
      requestAnimationFrame(() => this.draw(viewEl, visibleNodes));
    }
  },

  initResizeObserver() {
    if (this.observer) return;

    this.observer = new ResizeObserver(() => this._scheduleRedraw());
    this.observer.observe(document.getElementById('mapContainer'));
    window.addEventListener('resize', () => this._scheduleRedraw());
  },

  draw(viewEl, visibleNodes) {
    const oldSvg = viewEl.querySelector('.dag-svg');
    if (oldSvg) oldSvg.remove();
    viewEl.querySelectorAll('.stacked-indent-spine').forEach(el => el.remove());

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'dag-svg');

    const containerRect = viewEl.getBoundingClientRect();
    const markerPositions = new Map();
    const nodeToRowIdx = new Map();
    const visualRows = [];
    const STRAIGHT_THRESHOLD = 5;
    const MAX_CORNER_RADIUS = 12;
    let trunkX = null;

    const groups = [...viewEl.querySelectorAll('.level-group')];
    const pageStacked = 'pageStacked' in (viewEl.dataset || {});
    const timelinePlan = viewEl._timelinePlan || null;

    groups.forEach(group => {
      const groupNodeIds = [...group.querySelectorAll(':scope > .node-row')].map(r => r.dataset.id);
      let maxBottom = 0;

      groupNodeIds.forEach(id => {
        const row = group.querySelector(`:scope > .node-row[data-id="${id}"]`);
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
          x,
          y,
          depth,
          cardTop: cardRect.top - containerRect.top,
          cardBottom: cardRect.bottom - containerRect.top,
          visualBottom
        });

        if (trunkX === null && depth === 0) trunkX = x;
        maxBottom = Math.max(maxBottom, visualBottom);
      });

      const rowIdx = visualRows.length;
      visualRows.push({ nodeIds: groupNodeIds, bottom: maxBottom });
      groupNodeIds.forEach(id => nodeToRowIdx.set(id, rowIdx));
    });

    if (trunkX === null) {
      const firstPos = markerPositions.values().next().value;
      trunkX = firstPos?.x ?? 0;
    }

    for (const [id, pos] of markerPositions) {
      const idx = nodeToRowIdx.get(id);
      pos.rowBottom = idx === undefined ? pos.visualBottom : visualRows[idx].bottom;
      pos.prevRowBottom = idx > 0 ? visualRows[idx - 1].bottom : null;
    }

    const runByNodeId = new Map();
    const indentSpines = [];
    const skipEdges = new Set();
    const syntheticEdges = [];

    const getTransitionMetrics = (startId, endId) => {
      const start = markerPositions.get(startId);
      const end = markerPositions.get(endId);
      if (!start || !end) return null;

      // 1. Launch branches from the bottom of the *entire row*, not the individual card.
      // This ensures all parallel nodes launch their branches at the exact same Y-coordinate.
      const gapTop = start.rowBottom !== undefined ? start.rowBottom : start.visualBottom;

      // 2. If an edge skips rows, bend it in the gap immediately above its destination,
      // instead of splitting the massive gap across multiple rows (which cuts through nodes).
      const effectiveGapTop = (end.prevRowBottom !== undefined && end.prevRowBottom > gapTop) 
        ? end.prevRowBottom 
        : gapTop;

      const gapBottom = end.cardTop;
      const gap = Math.max(0, gapBottom - effectiveGapTop);
      
      // The horizontal merge line is now perfectly centered in the correct gap
      const joinY = effectiveGapTop + gap / 2;
      const dx = Math.abs(end.x - start.x);
      
      const radius = dx < STRAIGHT_THRESHOLD
        ? 0
        : Math.max(0, Math.min(MAX_CORNER_RADIUS, dx / 3, Math.max(0, gap / 2 - 1)));

      return { start, end, gapTop: effectiveGapTop, gapBottom, gap, joinY, radius };
    };

    const buildIndentSpines = (spineBlocks) => {
      spineBlocks.forEach(block => {
        const firstPos = markerPositions.get(block.startId);
        const lastPos = markerPositions.get(block.endId);
        if (!firstPos || !lastPos) return;

        const prevDepth = block.prevId ? (markerPositions.get(block.prevId)?.depth ?? 0) : 0;
        const nextDepth = block.nextId ? (markerPositions.get(block.nextId)?.depth ?? 0) : 0;

        let top = firstPos.y;
        if (block.prevId && prevDepth < block.depth) {
          const entryMetrics = getTransitionMetrics(block.prevId, block.startId);
          if (entryMetrics) top = entryMetrics.joinY + entryMetrics.radius;
        }

        let bottom = lastPos.visualBottom;
        let fade = false;

        if (block.nextId) {
          const exitMetrics = getTransitionMetrics(block.endId, block.nextId);

          if (nextDepth < block.depth) {
            if (exitMetrics) {
              bottom = Math.max(top + 8, exitMetrics.joinY - exitMetrics.radius);
              // Fade if the block's last node is deeper than this spine's depth,
              // meaning the return branch originates from a deeper X position
              // and this spine doesn't directly connect to it.
              const endDepth = markerPositions.get(block.endId)?.depth ?? block.depth;
              fade = endDepth > block.depth;
            }
          } else if (nextDepth === block.depth) {
            if (exitMetrics) bottom = Math.max(top + 8, exitMetrics.joinY - exitMetrics.radius);
            fade = true;
          }
        } else {
          // Terminal spine (no subsequent node): the terminal-return code draws
          // a curve from this spine back to the trunk, so keep it solid.
          fade = false;
        }

        const height = bottom - top;
        if (height > 0 && Math.abs(firstPos.x - trunkX) >= STRAIGHT_THRESHOLD) {
          indentSpines.push({ x: Math.round(firstPos.x), top, height, depth: block.depth, fade });
        }
      });
    };

    if (pageStacked && timelinePlan) {
      const order = timelinePlan.displayOrder.filter(id => markerPositions.has(id));
      syntheticEdges.push(...timelinePlan.transitions.filter(edge =>
        markerPositions.has(edge.startId) && markerPositions.has(edge.endId)
      ));
      visibleNodes.forEach(node => {
        (node.nextIds || []).forEach(nextId => {
          if (markerPositions.has(nextId)) skipEdges.add(`${node.id}→${nextId}`);
        });
      });
      buildIndentSpines(timelinePlan.spineBlocks);
    } else {
      (viewEl._parallelRuns || []).forEach(run => {
        run.displayOrder.forEach(id => runByNodeId.set(id, run));
        if (!run.isStacked) return;

        const order = run.displayOrder.filter(id => markerPositions.has(id));
        if (order.length === 0) return;

        const depthOf = id => run.depthMap.get(id) || 0;

        for (let i = 0; i < order.length - 1; i++) {
          const currentId = order[i];
          const nextId = order[i + 1];
          const currentDepth = depthOf(currentId);
          const nextDepth = depthOf(nextId);
          if (currentDepth !== nextDepth) {
            syntheticEdges.push({
              startId: currentId,
              endId: nextId,
              kind: nextDepth > currentDepth ? 'branch-enter' : 'branch-return',
              startDepth: currentDepth,
              endDepth: nextDepth,
              startAtSpine: nextDepth < currentDepth,
              endAtSpine: nextDepth > currentDepth
            });
          }
        }

        const orderSet = new Set(order);
        const firstId = order[0];
        const lastId = order[order.length - 1];

        order.forEach(id => {
          const node = DataStore.map.get(id);
          if (!node) return;

          (node.prevIds || []).forEach(prevId => {
            if (!orderSet.has(prevId) && id !== firstId) {
              skipEdges.add(`${prevId}→${id}`);
            }
            if (orderSet.has(prevId)) {
              skipEdges.add(`${prevId}→${id}`);
            }
          });

          (node.nextIds || []).forEach(nextId => {
            if (!orderSet.has(nextId) && id !== lastId) {
              skipEdges.add(`${id}→${nextId}`);
            }
            if (orderSet.has(nextId)) {
              skipEdges.add(`${id}→${nextId}`);
            }
          });
        });

        const spineBlocks = AppUI.buildStackedSpineBlocks(order, run.depthMap);
        buildIndentSpines(spineBlocks);
      });
    }

    const maskId = `timelineMask-${++maskCounter}`;
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

    // Mask indent spine regions at their actual vertical bounds (not full height).
    // This prevents SVG/spine overlap where they coexist, while leaving branch
    // curves fully visible above and below the spine extent.
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

    const drawEdgePath = (startId, endId, options = {}) => {
      const start = markerPositions.get(startId);
      const end = markerPositions.get(endId);
      if (!start || !end) return '';

      const {
        startAtSpine = false,
        endAtSpine = false,
        kind = 'flow'
      } = options;

      if (kind === 'branch-enter' || kind === 'branch-return') {
        const metrics = getTransitionMetrics(startId, endId);
        if (!metrics || metrics.radius <= 0) return `M ${start.x} ${metrics?.joinY ?? start.y} L ${end.x} ${metrics?.joinY ?? end.y} `;
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

      const metrics = getTransitionMetrics(startId, endId);
      const bendY = (metrics && Math.abs(start.x - end.x) >= STRAIGHT_THRESHOLD) ? metrics.joinY : null;

      if (bendY === null) {
        return `M ${start.x} ${start.y} L ${end.x} ${end.y} `;
      }

      const effectiveBendY = bendY;
      const dirX = end.x > start.x ? 1 : -1;
      const startVertical = Math.max(0, effectiveBendY - start.y);
      const endVertical = Math.max(0, end.y - effectiveBendY);
      const radius = Math.min(
        MAX_CORNER_RADIUS,
        Math.abs(end.x - start.x) / 2,
        startAtSpine ? MAX_CORNER_RADIUS : Math.max(0, startVertical - 2),
        endAtSpine ? MAX_CORNER_RADIUS : Math.max(0, endVertical - 2)
      );

      let d = `M ${start.x} ${startAtSpine ? effectiveBendY - radius : start.y} `;

      if (!startAtSpine) {
        d += `L ${start.x} ${Math.max(start.y, effectiveBendY - radius)} `;
      }

      d += `Q ${start.x} ${effectiveBendY} ${start.x + radius * dirX} ${effectiveBendY} `;
      d += `L ${end.x - radius * dirX} ${effectiveBendY} `;
      d += `Q ${end.x} ${effectiveBendY} ${end.x} ${effectiveBendY + radius} `;

      if (!endAtSpine) {
        d += `L ${end.x} ${end.y} `;
      }

      return d;
    };

    let allPathData = '';

    if (!pageStacked) {
      visibleNodes.forEach(node => {
        (node.nextIds || []).forEach(nextId => {
          if (markerPositions.has(nextId) && !skipEdges.has(`${node.id}→${nextId}`)) {
            allPathData += drawEdgePath(node.id, nextId);
          }
        });
      });
    }

    syntheticEdges.forEach(edge => {
      allPathData += drawEdgePath(edge.startId, edge.endId, edge);
    });

    if (trunkX !== null) {
      const visibleIdSet = new Set(visibleNodes.map(n => n.id));
      const terminalOffSpine = visibleNodes.filter(node => {
        if (node.nextIds?.some(nid => visibleIdSet.has(nid))) return false;
        const pos = markerPositions.get(node.id);
        return pos && Math.abs(pos.x - trunkX) >= STRAIGHT_THRESHOLD;
      });

      if (terminalOffSpine.length > 0) {
        const byX = new Map();
        for (const node of terminalOffSpine) {
          const pos = markerPositions.get(node.id);
          const xKey = Math.round(pos.x);
          if (!byX.has(xKey) || pos.y > byX.get(xKey).y) {
            byX.set(xKey, pos);
          }
        }

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

        for (const [, pos] of byX) {
          const dirX = trunkX > pos.x ? 1 : -1;
          const radius = Math.min(
            MAX_CORNER_RADIUS,
            Math.abs(trunkX - pos.x) / 2,
            Math.max(0, Math.abs(mergeY - pos.y) - 2)
          );

          allPathData += `M ${pos.x} ${pos.y} ` +
            `L ${pos.x} ${mergeY - radius} ` +
            `Q ${pos.x} ${mergeY} ${pos.x + radius * dirX} ${mergeY} ` +
            `L ${trunkX - radius * dirX} ${mergeY} ` +
            `Q ${trunkX} ${mergeY} ${trunkX} ${mergeY + radius} `;
        }
      }
    }

    for (const spineInfo of indentSpines) {
      const fadeZone = spineInfo.fade ? Math.min(SPINE_FADE_PX, spineInfo.height * 0.3) : 0;
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

    if (allPathData) {
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('class', 'dag-edge');
      path.setAttribute('d', allPathData.trim());
      path.setAttribute('mask', `url(#${maskId})`);
      svg.appendChild(path);
    }

    viewEl.prepend(svg);
  },
};


/**
 * =============================================================================
 * 7. TEMPLATE ENGINE
/**
 * =============================================================================
 * 7. TEMPLATE ENGINE
 * =============================================================================
 * Pure HTML string generators. No DOM manipulation or state changes.
 *
 * Key change from original: the marker now contains a real <span class="marker-dot">
 * element instead of using ::before, so the SVG engine can measure its center
 * directly via getBoundingClientRect().
 */
const Templates = {
  nodeRow(node) {
    const parentNode = node.parentId ? DataStore.map.get(node.parentId) : null;
    const pillColorDark = parentNode ? parentNode.color.borderDark : node.color.borderDark;
    const pillColorLight = parentNode ? parentNode.color.borderLight : node.color.borderLight;

    // Badge navigates to grandparent (or root if parent is top-level)
    const badgeTarget = parentNode?.parentId === null ? 'null' : (parentNode?.parentId || '');
    const badgeHtml = parentNode
      ? `<button class="node-badge trigger-derive" type="button" data-target="${badgeTarget}"
           aria-label="Go to parent step ${parentNode.id}">
           <span class="badge-dot"></span>${parentNode.id}</button>`
      : '';

    // Hidden placeholder preserves grid column when no derivation exists
    const derivationHtml = (node.hasDerivation !== false)
      ? `<button class="btn-derivation trigger-derive" data-target="${node.id}"
           aria-label="Derivation details for step ${node.id}">
           <span class="label">Derivation</span><span>→</span></button>`
      : `<button class="btn-derivation" aria-hidden="true" disabled
           style="visibility: hidden; pointer-events: none;">
           <span class="label">Derivation</span><span>→</span></button>`;

    return `
      <div class="node-marker" aria-hidden="true">
        <span class="marker-dot"></span>
        <span class="marker-arrow-tip"></span>
      </div>
      <article class="node-card" data-id="${node.id}"
        style="--n-border-dark: ${node.color.borderDark}; --n-border-light: ${node.color.borderLight};
               --n-top: ${node.color.top}; --n-bottom: ${node.color.bottom};
               --p-border-dark: ${pillColorDark}; --p-border-light: ${pillColorLight};">
        <div class="node-header" role="button" aria-expanded="false">
          <h2 class="node-title"><span class="id">${node.id}.</span><span class="claim-text">${node.claim}</span></h2>
          <div class="node-controls">
            ${badgeHtml}
            <button class="btn-ui trigger-inline" type="button" tabindex="-1">Expand</button>
          </div>
        </div>
        <p class="node-so-what">${node.soWhat}</p>
      </article>
      ${derivationHtml}
    `;
  },

  expander(node) {
    const rowSections = (node.sections || []).filter(s => s.type === 'row');
    const logicGroupHtml = rowSections
      .map((s, idx) => this.logicRow(s.title, s.items, idx + 1, s.numbered))
      .join('');

    const tabSections = (node.sections || []).filter(s => s.type === 'tab');

    // Action slot: "disagree → derive" button, or agree/disagree toggles
    let actionHtml = '';
    if (node.hasDerivation !== false) {
      actionHtml = `<button class="btn-action btn-derivation-disagree trigger-derive"
        type="button" data-target="${node.id}">Disagree? See how this is derived →</button>`;
    } else {
      actionHtml = `
        <button class="btn-action btn-agree" type="button" aria-pressed="true">I agree</button>
        <button class="btn-action btn-disagree" type="button" aria-pressed="false">I disagree</button>
      `;
    }
    const actionSlotHtml = `<div class="panel-action-slot">${actionHtml}</div>`;

    let tabAreaHtml = '';
    if (tabSections.length > 0) {
      const defaultTab = tabSections[0].title;
      const tabButtonsHtml = tabSections.map(s => `
        <button class="btn-tab" data-key="${s.title}"
          aria-selected="${s.title === defaultTab}" aria-controls="panel-${node.id}">
          ${s.title}
        </button>
      `).join('');

      tabAreaHtml = `
        <div class="tab-area">
          <div class="tab-list" role="tablist" aria-label="Logic Implications">${tabButtonsHtml}</div>
          ${actionSlotHtml}
          <div class="tab-panel" id="panel-${node.id}" role="tabpanel"></div>
        </div>
      `;
    } else {
      tabAreaHtml = `<div class="tab-area" style="grid-template-columns: 1fr;">${actionSlotHtml}</div>`;
    }

    return `<div class="exp-inner"><div class="logic-group">${logicGroupHtml}</div>${tabAreaHtml}</div>`;
  },

  logicRow(label, items, step, isNumbered) {
    if (!items?.length) return '';
    const isComplex = typeof items[0] === 'object' && items[0] !== null;
    const content = isComplex
      ? `<div class="mini-stack">${items.map((it, idx) => this.recursiveMiniNode(it, isNumbered ? idx + 1 : null)).join('')}</div>`
      : this.buildList(items);

    return `
      <div class="logic-section">
        <div class="logic-header" data-step="${step}" aria-expanded="true" role="button">${label}</div>
        <div class="logic-content">${content}</div>
      </div>
    `;
  },

  buildList(items, listType) {
    const tag = listType === 'ordered' ? 'ol' : 'ul';
    const cls = listType === 'ordered' ? 'numbered' : 'bullets';
    return `<${tag} class="${cls}">${items.map(i => {
      if (typeof i === 'object' && i !== null && i.text !== undefined) {
        const subList = i.items?.length
          ? `<ul class="bullets">${i.items.map(s => `<li>${s}</li>`).join('')}</ul>`
          : '';
        return `<li>${i.text}${subList}</li>`;
      }
      return `<li>${i}</li>`;
    }).join('')}</${tag}>`;
  },

  buildMiniNodeContent(data) {
    const parts = [];
    if (data.detail) {
      parts.push(`<div style="padding:10px 0; text-align: left;"><div class="sub-body">${data.detail}</div></div>`);
    }
    if (data.subSections?.length) {
      parts.push(data.subSections.map(sub => `
        <div class="sub-section">
          <div class="sub-label">${sub.label}</div>
          <div class="sub-body">${this.buildList(sub.items, sub.listType)}</div>
        </div>
      `).join(''));
    }
    if (data.children?.length) {
      parts.push(`<div class="mini-stack" style="margin-top:12px;">
        ${data.children.map((c, idx) => this.recursiveMiniNode(c, idx + 1)).join('')}
      </div>`);
    }
    return parts.join('');
  },

  recursiveMiniNode(data, num) {
    const prefix = num ? `<span class="id">${num}.</span> ` : '';
    const title = data.title || data;
    const content = this.buildMiniNodeContent(data);
    return `
      <div class="mini-node">
        <button class="mini-trigger" type="button" aria-expanded="false">${prefix}${title}</button>
        <div class="mini-content-wrap">${content}</div>
      </div>
    `;
  },

  tabContent(items, isNumbered) {
    if (!items?.length) return `<ul class="bullets"><li>—</li></ul>`;
    const isComplex = typeof items[0] === 'object' && items[0] !== null;
    if (isComplex) {
      return `<div class="mini-stack">${items.map((it, idx) => this.recursiveMiniNode(it, isNumbered ? idx + 1 : null)).join('')}</div>`;
    }
    return this.buildList(items);
  }
};


/**
 * =============================================================================
 * 8. NAVIGATION CONTROLLER
 * =============================================================================
 * Manages page-level navigation: URL state, history, and transition direction.
 */
const NavigationController = {
  init() {
    window.addEventListener('popstate', (e) => {
      this.loadState(e.state?.nodeId ?? null, 'restore');
    });

    let initialNode = new URLSearchParams(window.location.search).get('node');
    
    // VALIDATION: If the URL node ID doesn't exist in the JSON, discard it
    if (initialNode !== null && !DataStore.map.has(initialNode)) {
      console.warn(`Node ${initialNode} not found. Defaulting to root.`);
      initialNode = null; 
    }

    this.loadState(initialNode, 'replace');
  },

  navigate(targetId) {
    // Prevent double-clicks from overlapping animations and breaking the DOM
    if (AppState.isTransitioning) return;
	
	this.loadState(targetId, 'push');
  },

  /**
   * Determines spatial direction for the transition animation.
   * @returns {'depth'|'surface'|'lateral-next'|'lateral-prev'|'none'}
   */
  getDirection(fromId, toId) {
    if (fromId === toId) return 'none';
    if (!fromId && toId) return 'depth';
    if (fromId && !toId) return 'surface';

    const fromNode = DataStore.map.get(fromId);
    const toNode = DataStore.map.get(toId);

    if (toNode?.parentId === fromId) return 'depth';
    if (fromNode?.parentId === toId) return 'surface';

    if (fromNode && toNode && fromNode.parentId === toNode.parentId) {
      const fromIndex = DataStore.nodes.findIndex(n => n.id === fromId);
      const toIndex = DataStore.nodes.findIndex(n => n.id === toId);
      return toIndex > fromIndex ? 'lateral-next' : 'lateral-prev';
    }

    return 'surface';
  },

  loadState(nodeId, historyAction = 'push') {
    // Clear search if active
    if (AppUI.els.searchInput?.value) {
      AppUI.els.searchInput.value = '';
    }

    const prevId = AppState.currentParentId;
    const direction = this.getDirection(prevId, nodeId);

    AppState.currentParentId = nodeId;
    AppState.activeNodeId = null;
    document.body.classList.remove('is-focused');

    // Update URL
    const url = new URL(window.location);
    if (nodeId) url.searchParams.set('node', nodeId);
    else url.searchParams.delete('node');

    if (historyAction === 'push') window.history.pushState({ nodeId }, '', url);
    else if (historyAction === 'replace') window.history.replaceState({ nodeId }, '', url);

    AppUI.updateHeaderContext();
    AppUI.renderMapWithTransition(direction);
  }
};


/**
 * =============================================================================
 * 9. UI CONTROLLER
 * =============================================================================
 * Owns all DOM interactions: rendering, event binding, expander management,
 * and search. Organized into lifecycle phases:
 *
 *   init → cacheDOM → bindEvents → (user interaction cycle)
 *
 * Render lifecycle (per navigation):
 *   1. buildView()            – Create DOM structure
 *   2. mountAndDraw(view)     – Append to container, draw SVG connectors
 *   3. animateTransition()    – Animate old→new with direction-based classes
 */
const AppUI = {
  els: {},

  init() {
    this.cacheDOM();
    AppState.applyTheme();
    this.bindEvents();
    SVGEngine.initResizeObserver();
  },

  cacheDOM() {
    const byId = id => document.getElementById(id);
    this.els.docTitle = byId('docTitle');
    this.els.pageTitle = byId('titleText');
    this.els.pageSubtitle = byId('subtitleText');
    this.els.breadcrumbRoot = byId('breadcrumbRoot');
    this.els.breadcrumbCurrent = byId('breadcrumbCurrent');
    this.els.container = byId('mapContainer');
    this.els.searchInput = byId('searchInput');
    this.els.themeToggle = byId('themeToggle');
    this.els.headerToggle = byId('headerToggle');
    this.els.chevronToggle = byId('chevronToggle');
    this.els.pageHeader = byId('pageHeader');
    this.els.searchFilterBtn = byId('searchFilterBtn');
    this.els.searchFilterMenu = byId('searchFilterMenu');
    this.els.toggleNodeContentsSearch = byId('toggleNodeContentsSearch');
    this.els.toggleGlobalSearch = byId('toggleGlobalSearch');
    this.els.toggleNestedSearch = byId('toggleNestedSearch');
  },

  /* ------------------------------------------------------------------
   * Header & breadcrumb updates
   * ------------------------------------------------------------------ */
  updateHeaderContext() {
    // Reset expander tint; page tint set below based on context
    AppState.updateTints({ expander: 'transparent' });

    if (!AppState.currentParentId) {
      // Root level
      AppState.updateTints({ page: 'transparent' });
      if (this.els.docTitle) this.els.docTitle.textContent = `${DataStore.config.title} - Map`;
      if (this.els.pageTitle) this.els.pageTitle.textContent = DataStore.config.title;
      if (this.els.pageSubtitle) this.els.pageSubtitle.textContent = DataStore.config.subtitle;
      if (this.els.breadcrumbRoot) {
        this.els.breadcrumbRoot.innerHTML = `<a href="#" class="crumb-link" data-target="null">${DataStore.config.breadcrumbRoot}</a>`;
      }
      if (this.els.breadcrumbCurrent) this.els.breadcrumbCurrent.textContent = DataStore.config.title;
    } else {
      // Sub-page: show parent node's context
      const parentNode = DataStore.map.get(AppState.currentParentId);
      if (!parentNode) return;

      AppState.updateTints({ page: `hsla(${parentNode.hue}, 80%, 50%, 0.35)` });

      const prefix = DataStore.config.nodePrefix;
      if (this.els.docTitle) this.els.docTitle.textContent = `${prefix}${parentNode.id} - Map`;
      if (this.els.pageTitle) this.els.pageTitle.textContent = `${prefix}${parentNode.id}. ${parentNode.claim}`;
      if (this.els.pageSubtitle) this.els.pageSubtitle.textContent = parentNode.soWhat;

      this.renderBreadcrumbs(parentNode.id);
    }

    if (this.els.searchInput) this.els.searchInput.placeholder = DataStore.config.searchPlaceholder;
  },

  renderBreadcrumbs(activeNodeId) {
    if (!this.els.breadcrumbRoot || !this.els.breadcrumbCurrent) return;

    // Walk up the tree to build lineage
    const lineage = [];
    let current = DataStore.map.get(activeNodeId);
    while (current) {
      lineage.unshift(current);
      current = DataStore.map.get(current.parentId);
    }

    const prefix = DataStore.config.nodePrefix;
    let html = `<a href="#" class="crumb-link" data-target="null">${DataStore.config.breadcrumbRoot}</a>`;
    html += ` <span class="sep" aria-hidden="true">›</span> <a href="#" class="crumb-link" data-target="null">${DataStore.config.title}</a>`;

    for (let i = 0; i < lineage.length - 1; i++) {
      const node = lineage[i];
      html += ` <span class="sep" aria-hidden="true">›</span> <a href="#" class="crumb-link" data-target="${node.id}">${prefix}${node.id}</a>`;
    }

    this.els.breadcrumbRoot.innerHTML = html;
    this.els.breadcrumbCurrent.textContent = `${prefix}${lineage[lineage.length - 1].id}`;
  },

  /* ------------------------------------------------------------------
   * View building
   * ------------------------------------------------------------------ */
  buildView() {
    const newView = document.createElement('div');
    newView.className = 'map-flow';
    newView.innerHTML = '<div class="map-spine" aria-hidden="true"></div>';

    const visibleNodes = DataStore.nodes.filter(n => n.parentId === AppState.currentParentId);

    if (visibleNodes.length === 0) {
      newView.innerHTML += `<div style="padding: 40px 20px; text-align: center; color: var(--text-muted);">
        No deeper derivations mapped for this claim yet.</div>`;
      return newView;
    }

    const fragment = document.createDocumentFragment();
    const groupedRows = GraphEngine.computeLevels(visibleNodes);
    const allLevelGroups = [];

    groupedRows.forEach((rowNodes, levelIndex) => {
      const levelGroup = document.createElement('div');
      levelGroup.className = 'level-group';

      const realNodeEls = [];
	  const flexItems = [];

      rowNodes.forEach(node => {
        if (node.isDummy) {
          // Dummies are pure flex spacers — no grid layout, no containment.
          // They hold a flex lane so SVG connectors can route through the row.
          const dummy = document.createElement('div');
          dummy.className = 'dummy-node';
          levelGroup.appendChild(dummy);
		  flexItems.push(dummy);
          return;
        }

        const row = document.createElement('div');
        row.className = 'node-row';
        row.dataset.id = node.id;
        row.innerHTML = Templates.nodeRow(node);
        levelGroup.appendChild(row);
        realNodeEls.push(row);
		flexItems.push(row);
      });

      // Parallel tagging: groups with more than one flex lane are treated as
      // responsive branch rows. The first/last flags keep marker and derive
      // button alignment stable in both wide and stacked modes.
      const totalFlexChildren = flexItems.length;
      if (totalFlexChildren > 1) {
        levelGroup.dataset.parallel = '';

        // Assign first/last column compensations regardless of node type
        flexItems[0].dataset.firstParallel = 'true';
        flexItems[flexItems.length - 1].dataset.lastParallel = 'true';

        // Ensure the last real node always keeps the full derive button
        if (realNodeEls.length > 0) {
          realNodeEls[realNodeEls.length - 1].dataset.lastParallel = 'true';
        }
      }

      // Shared expander drawer at the end of each level-group
      const expanderEl = document.createElement('div');
      expanderEl.className = 'level-expander';
      levelGroup.appendChild(expanderEl);

      allLevelGroups.push(levelGroup);
      fragment.appendChild(levelGroup);
    });

    const parallelRuns = [];
    let activeRun = [];

    const flushRun = () => {
      if (activeRun.length === 0) return;
      parallelRuns.push(this.buildParallelRunModel(activeRun));
      activeRun = [];
    };

    allLevelGroups.forEach(group => {
      if ('parallel' in group.dataset) activeRun.push(group);
      else flushRun();
    });
    flushRun();

    newView._parallelRuns = parallelRuns;
    newView._timelinePlan = this.buildTimelinePlan(allLevelGroups);
    newView.appendChild(fragment);
    return newView;
  },

  /**
   * Prepends/appends prev/next sibling navigation buttons.
   */
  appendSiblingNavigation(view) {
    const parentNode = AppState.currentParentId ? DataStore.map.get(AppState.currentParentId) : null;
    if (!parentNode) return;

    const prefix = DataStore.config.nodePrefix;

    // Previous sibling
    if (parentNode.prevIds?.length) {
      const prevNode = DataStore.map.get(parentNode.prevIds[0]);
      if (prevNode) {
        const el = document.createElement('div');
        el.className = 'sibling-nav-area prev';
        el.innerHTML = `
          <div class="sibling-label">Previous Step in Logic</div>
          <button class="btn-sibling prev-btn trigger-derive" data-target="${prevNode.id}" type="button">
            <span class="sibling-arrow">↑</span>
            <span class="sibling-id">${prefix}${prevNode.id}.</span>
            <span class="sibling-claim">${prevNode.claim}</span>
          </button>
        `;
        view.prepend(el);
      }
    }

    // Next sibling
    if (parentNode.nextIds?.length) {
      const nextNode = DataStore.map.get(parentNode.nextIds[0]);
      if (nextNode) {
        const el = document.createElement('div');
        el.className = 'sibling-nav-area next';
        el.innerHTML = `
          <div class="sibling-label">Next Step in Logic</div>
          <button class="btn-sibling next-btn trigger-derive" data-target="${nextNode.id}" type="button">
            <span class="sibling-arrow">↓</span>
            <span class="sibling-id">${prefix}${nextNode.id}.</span>
            <span class="sibling-claim">${nextNode.claim}</span>
          </button>
        `;
        view.appendChild(el);
      }
    }
  },

  /* ------------------------------------------------------------------
   * Render lifecycle with transition animation
   * ------------------------------------------------------------------ */
  renderMapWithTransition(direction) {
    const oldViews = this.els.container.querySelectorAll('.map-flow, .search-result-box, .search-group');
    this.els.container.style.pointerEvents = 'none';
    AppState.isTransitioning = true;

    // Lock container height to prevent layout jump during transition
    this.els.container.style.minHeight = `${this.els.container.offsetHeight}px`;
    this.els.container.style.overflow = 'hidden';

    // Phase 1: Build
    const newView = this.buildView();
    this.appendSiblingNavigation(newView);
    this.els.container.appendChild(newView);

    // Phase 1b: Resolve wide-vs-stacked layout before first paint
    this.applyResponsiveRunLayout(newView);

    // Phase 2: Draw SVG connectors (needs layout to be settled)
    requestAnimationFrame(() => {
      const visibleNodes = DataStore.nodes.filter(n => n.parentId === AppState.currentParentId);
      requestAnimationFrame(() => SVGEngine.draw(newView, visibleNodes));
    });

    // Phase 3: Animate
    // Direction → animation class mapping
    const exitMap = { depth: 'anim-exit-left', surface: 'anim-exit-right', 'lateral-next': 'anim-exit-top', 'lateral-prev': 'anim-exit-bottom' };
    const enterMap = { depth: 'anim-enter-right', surface: 'anim-enter-left', 'lateral-next': 'anim-enter-bottom', 'lateral-prev': 'anim-enter-top' };

    oldViews.forEach(oldView => {
      if (exitMap[direction]) oldView.classList.add(exitMap[direction]);
      oldView.style.position = 'absolute';
      oldView.style.top = '0';
      oldView.style.left = '0';
    });

    if (enterMap[direction]) newView.classList.add(enterMap[direction]);
    window.scrollTo(0, 0);

    // Phase 4: Cleanup after animation completes
    setTimeout(() => {
      oldViews.forEach(v => v.remove());
      newView.classList.remove(...Object.values(enterMap));
      this.els.container.style.pointerEvents = '';
      this.els.container.style.minHeight = '';
      this.els.container.style.overflow = '';

      // Final SVG redraw after layout is fully settled
      const visibleNodes = DataStore.nodes.filter(n => n.parentId === AppState.currentParentId);
      requestAnimationFrame(() => SVGEngine.draw(newView, visibleNodes));

      AppState.isTransitioning = false;

    }, ANIMATION_SPEEDS.CSS_TRANSITION_MS);
  },

  /* ------------------------------------------------------------------
   * Expander management
   * ------------------------------------------------------------------ */
  toggleExpander(id) {
    const row = document.querySelector(`.node-row[data-id="${id}"]`);
    if (!row) return;

    const levelGroup = row.closest('.level-group');
    const expander = levelGroup.querySelector('.level-expander');
    const headerBtn = row.querySelector('.node-header');
    const inlineBtn = row.querySelector('.trigger-inline');

    if (AppState.activeNodeId === id) {
      this.closeExpander(row, expander, headerBtn, inlineBtn);
    } else {
      // Close any previously open expander first
      if (AppState.activeNodeId !== null) {
        const activeRow = document.querySelector(`.node-row[data-id="${AppState.activeNodeId}"]`);
        if (activeRow) {
          const g = activeRow.closest('.level-group');
          this.closeExpander(activeRow, g.querySelector('.level-expander'),
            activeRow.querySelector('.node-header'), activeRow.querySelector('.trigger-inline'));
        }
      }
      this.openExpander(id, row, expander, headerBtn, inlineBtn);
    }
  },

  closeExpander(row, expander, headerBtn, inlineBtn) {
    expander.classList.remove('is-open');
    headerBtn.setAttribute('aria-expanded', 'false');
    if (inlineBtn) inlineBtn.textContent = 'Expand';

    // Animate sibling spacers closed
    document.querySelectorAll('.expander-spacer').forEach(s => {
      s.style.height = '0px';
    });

    row.classList.remove('is-active');
    document.body.classList.remove('is-focused');
    AppState.activeNodeId = null;
    AppState.updateTints({ expander: 'transparent' });

    // Move expander back to end of level-group (may have been repositioned
    // in stacked mode by openExpander).
    const levelGroup = row.closest('.level-group');
    if (levelGroup) {
      levelGroup.appendChild(expander);
    }
    expander.style.marginLeft = '';
    expander.style.marginRight = '';
    expander.style.flex = '';
    expander.style.width = '';

    // Deferred cleanup: clear innerHTML after the CSS transition completes
    setTimeout(() => {
      if (!expander.classList.contains('is-open')) expander.innerHTML = '';
      document.querySelectorAll('.expander-spacer').forEach(s => s.remove());
    }, ANIMATION_SPEEDS.CSS_TRANSITION_MS);
  },

  openExpander(id, row, expander, headerBtn, inlineBtn) {
    const nodeData = DataStore.map.get(id);
    if (!nodeData) return;

    const levelGroup = row.closest('.level-group');
    const stackGroup = row.closest('.stack-group');

    if (stackGroup) {
      // Stacked mode: move after the clicked row
      row.after(expander);
      // Break out using negative margins on both sides (avoids explicit
      // pixel width which inflates the stack-group's intrinsic cross-size).
      const lgRect = levelGroup.getBoundingClientRect();
      const sgRect = stackGroup.getBoundingClientRect();
      const breakoutLeft = sgRect.left - lgRect.left;
      const breakoutRight = lgRect.right - sgRect.right;

      expander.style.flex = '0 0 auto';
      expander.style.width = 'auto';
      expander.style.marginLeft = `-${breakoutLeft}px`;
      expander.style.marginRight = `-${breakoutRight}px`;
    }

    expander.innerHTML = Templates.expander(nodeData);
    this.bindTabEvents(expander, nodeData);
    this.bindActionEvents(expander);

    // Measure content height and create sibling spacers
    let spacerHeight = 0;
    if (stackGroup) {
      const expInner = expander.querySelector('.exp-inner');
      spacerHeight = expInner ? expInner.scrollHeight + 16 : 0;
      const clickedRect = row.getBoundingClientRect();
      const clickedTop = clickedRect.top;
      const expanderStart = clickedRect.bottom;
      const siblingStacks = levelGroup.querySelectorAll(':scope > .stack-group');
      siblingStacks.forEach(sg => {
        if (sg === stackGroup) return;
        const spacer = document.createElement('div');
        spacer.className = 'expander-spacer';
        const siblingRows = sg.querySelectorAll(':scope > .node-row');
        let insertAfter = null;
        for (const sibRow of siblingRows) {
          const sibRect = sibRow.getBoundingClientRect();
          const sameLevelOrAbove = sibRect.top <= clickedTop + 5;
          const endsAboveExpander = sibRect.bottom <= expanderStart + 5;
          if (sameLevelOrAbove && endsAboveExpander) {
            insertAfter = sibRow;
          }
        }
        if (insertAfter) {
          insertAfter.after(spacer);
        } else {
          sg.prepend(spacer);
        }
      });
    }

    requestAnimationFrame(() => {
      expander.classList.add('is-open');
      headerBtn.setAttribute('aria-expanded', 'true');
      if (inlineBtn) inlineBtn.textContent = 'Hide';

      // Animate spacers to match expander height
      if (spacerHeight > 0) {
        document.querySelectorAll('.expander-spacer').forEach(s => {
          s.style.height = spacerHeight + 'px';
        });
      }

      row.classList.add('is-active');
      document.body.classList.add('is-focused');
      AppState.activeNodeId = id;
      AppState.updateTints({ expander: `hsla(${nodeData.hue}, 80%, 50%, 0.35)` });

      this.scrollToView(row);
    });
  },

  bindTabEvents(expander, nodeData) {
    const tabBtns = expander.querySelectorAll('.btn-tab');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.setAttribute('aria-selected', b === btn));
        this.renderTabContent(nodeData, btn.dataset.key);
      });
    });
    if (tabBtns.length > 0) this.renderTabContent(nodeData, tabBtns[0].dataset.key);
  },

  bindActionEvents(expander) {
    const agreeBtn = expander.querySelector('.btn-agree');
    const disagreeBtn = expander.querySelector('.btn-disagree');

    if (agreeBtn && disagreeBtn) {
      agreeBtn.addEventListener('click', () => {
        agreeBtn.setAttribute('aria-pressed', 'true');
        disagreeBtn.setAttribute('aria-pressed', 'false');
      });
      disagreeBtn.addEventListener('click', () => {
        disagreeBtn.setAttribute('aria-pressed', 'true');
        agreeBtn.setAttribute('aria-pressed', 'false');
      });
    }
  },

  renderTabContent(nodeData, key) {
    const panel = document.getElementById(`panel-${nodeData.id}`);
    if (!panel) return;
    const section = (nodeData.sections || []).find(s => s.type === 'tab' && s.title === key);
    panel.innerHTML = Templates.tabContent(section?.items || [], section?.numbered || false);
  },

  scrollToView(el) {
    setTimeout(() => {
      const rect = el.getBoundingClientRect();
      if (rect.bottom > window.innerHeight) {
        const headerHeight = this.els.pageHeader?.offsetHeight ?? 0;
        window.scrollTo({
          top: window.scrollY + rect.top - headerHeight - 24,
          behavior: 'smooth'
        });
      }
    }, ANIMATION_SPEEDS.SCROLL_DELAY_MS);
  },

  /* ------------------------------------------------------------------
   * Parallel run modelling + responsive stacked layout
   * ------------------------------------------------------------------ */
  buildParallelRunModel(groups) {
    const displayOrder = [];
    const nodeIds = new Set();
    const rowIndexById = new Map();
    const colIndexById = new Map();
    const actualRows = [];
    let maxChildCount = 0;

    groups.forEach((group, rowIndex) => {
      const orderedIds = [...group.querySelectorAll(':scope > .node-row')].map(row => row.dataset.id);
      actualRows.push(orderedIds);
      orderedIds.forEach((id, colIndex) => {
        displayOrder.push(id);
        nodeIds.add(id);
        rowIndexById.set(id, rowIndex);
        colIndexById.set(id, colIndex);
      });
      maxChildCount = Math.max(
        maxChildCount,
        group.querySelectorAll(':scope > .node-row, :scope > .dummy-node').length
      );
    });

    const depthMap = this.computeStackedDepthMap(actualRows, nodeIds);

    return {
      groups,
      nodeIds,
      displayOrder,
      rowIndexById,
      colIndexById,
      depthMap,
      actualRows,
      maxChildCount,
      isStacked: false
    };
  },

  buildTimelinePlan(groups) {
    const actualRows = [];
    const nodeIds = new Set();

    groups.forEach(group => {
      const orderedIds = [...group.querySelectorAll(':scope > .node-row')].map(row => row.dataset.id);
      actualRows.push(orderedIds);
      orderedIds.forEach(id => nodeIds.add(id));
    });

    const depthMap = this.computeStackedDepthMap(actualRows, nodeIds);
    const displayOrder = this.computeStackedDisplayOrder(actualRows, nodeIds);

    return {
      actualRows,
      displayOrder,
      nodeIds,
      depthMap,
      transitions: this.buildStackedTransitions(displayOrder, depthMap),
      spineBlocks: this.buildStackedSpineBlocks(displayOrder, depthMap)
    };
  },

  computeStackedDisplayOrder(actualRows, nodeIds) {
    const rowIndexOf = new Map();
    const colIndexOf = new Map();
    const rowMajorOrder = [];

    actualRows.forEach((rowIds, rowIndex) => {
      rowIds.forEach((id, colIndex) => {
        rowIndexOf.set(id, rowIndex);
        colIndexOf.set(id, colIndex);
        rowMajorOrder.push(id);
      });
    });

    const compareVisualOrder = (a, b) => {
      const rowDiff = (rowIndexOf.get(a) ?? 0) - (rowIndexOf.get(b) ?? 0);
      if (rowDiff !== 0) return rowDiff;
      return (colIndexOf.get(a) ?? 0) - (colIndexOf.get(b) ?? 0);
    };

    const childMap = new Map();
    nodeIds.forEach(id => childMap.set(id, []));

    nodeIds.forEach(id => {
      const node = DataStore.map.get(id);
      if (!node) return;
      (node.nextIds || []).forEach(nextId => {
        if (!nodeIds.has(nextId)) return;
        childMap.get(id).push(nextId);
      });
    });

    childMap.forEach(children => children.sort(compareVisualOrder));

    const roots = rowMajorOrder.filter(id => {
      const node = DataStore.map.get(id);
      return !node || !(node.prevIds || []).some(pid => nodeIds.has(pid));
    });

    const emitted = new Set();
    const displayOrder = [];

    const canEmit = id => {
      const node = DataStore.map.get(id);
      if (!node) return true;
      return (node.prevIds || []).every(pid => !nodeIds.has(pid) || emitted.has(pid));
    };

    const visit = id => {
      if (emitted.has(id) || !canEmit(id)) return false;
      emitted.add(id);
      displayOrder.push(id);
      (childMap.get(id) || []).forEach(childId => {
        visit(childId);
      });
      return true;
    };

    roots.forEach(visit);

    let madeProgress = true;
    while (displayOrder.length < rowMajorOrder.length && madeProgress) {
      madeProgress = false;
      rowMajorOrder.forEach(id => {
        if (visit(id)) madeProgress = true;
      });
    }

    if (displayOrder.length < rowMajorOrder.length) {
      rowMajorOrder.forEach(id => {
        if (!emitted.has(id)) displayOrder.push(id);
      });
    }

    return displayOrder;
  },

  buildStackedTransitions(displayOrder, depthMap) {
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
        startDepth,
        endDepth,
        startAtSpine: endDepth < startDepth,
        endAtSpine: endDepth > startDepth
      });
    }

    return transitions;
  },

  buildStackedSpineBlocks(displayOrder, depthMap) {
    const blocks = [];
    const depthOf = id => depthMap.get(id) || 0;
    const maxDepth = Math.max(...displayOrder.map(depthOf), 0);

    for (let depth = 1; depth <= maxDepth; depth++) {
      let blockStartIndex = -1;
      const flush = endIndex => {
        if (blockStartIndex === -1) return;
        const ids = displayOrder.slice(blockStartIndex, endIndex + 1);

        // Find the last node at exactly this depth and the first deeper node after it.
        // Used by buildIndentSpines to fade the spine at depth hand-off points.
        let lastIdAtDepth = null;
        let firstDeeperIdAfter = null;
        for (let i = ids.length - 1; i >= 0; i--) {
          if (depthOf(ids[i]) === depth) {
            lastIdAtDepth = ids[i];
            if (i < ids.length - 1) firstDeeperIdAfter = ids[i + 1];
            break;
          }
        }

        blocks.push({
          depth,
          startId: displayOrder[blockStartIndex],
          endId: displayOrder[endIndex],
          prevId: blockStartIndex > 0 ? displayOrder[blockStartIndex - 1] : null,
          nextId: endIndex < displayOrder.length - 1 ? displayOrder[endIndex + 1] : null,
          maxDepthWithin: Math.max(...ids.map(depthOf), depth),
          lastIdAtDepth,
          firstDeeperIdAfter
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
  },

  computeStackedDepthMap(actualRows, nodeIds) {
    const depthMap = new Map();
    const rowDepths = [];
    const rowIndexOf = new Map();

    actualRows.forEach((rowIds, rowIndex) => {
      rowIds.forEach(id => rowIndexOf.set(id, rowIndex));
    });

    const getParentDepths = node => (node?.prevIds || [])
      .filter(pid => nodeIds.has(pid))
      .map(pid => depthMap.get(pid) ?? 0);

    actualRows.forEach((rowIds, rowIndex) => {
      if (rowIds.length === 0) return;
      if (rowIndex === 0) {
        rowDepths[rowIndex] = 0;
        rowIds.forEach(id => depthMap.set(id, 0));
        return;
      }

      const prevRowIds = actualRows[rowIndex - 1] || [];
      const prevRowSet = new Set(prevRowIds);
      const rowNodes = rowIds.map(id => DataStore.map.get(id)).filter(Boolean);
      const parentIdsByNode = rowNodes.map(node => (node.prevIds || []).filter(pid => nodeIds.has(pid)));
      const parentDepths = parentIdsByNode.flatMap(parentIds =>
        parentIds.map(pid => depthMap.get(pid) ?? 0)
      );
      const minParentDepth = parentDepths.length ? Math.min(...parentDepths) : 0;
      const maxParentDepth = parentDepths.length ? Math.max(...parentDepths) : 0;
      const parentRowIndices = new Set(parentIdsByNode.flatMap(parentIds =>
        parentIds.map(pid => rowIndexOf.get(pid)).filter(idx => idx !== undefined)
      ));

      const parentsCoverEntirePrevRow = prevRowIds.length > 0 && rowNodes.every(node => {
        const inPrevRow = (node.prevIds || []).filter(pid => prevRowSet.has(pid));
        return inPrevRow.length === prevRowIds.length;
      });

      const sharedSinglePrevParent = (() => {
        if (rowNodes.length === 0) return null;
        const first = (rowNodes[0].prevIds || []).find(pid => prevRowSet.has(pid));
        if (!first) return null;
        const everyNodeUsesOnlyFirst = rowNodes.every(node => {
          const inPrevRow = (node.prevIds || []).filter(pid => prevRowSet.has(pid));
          return inPrevRow.length === 1 && inPrevRow[0] === first;
        });
        return everyNodeUsesOnlyFirst ? first : null;
      })();

      const everyNodeHasExactlyOneParent = parentIdsByNode.every(parentIds => parentIds.length === 1);
      const allParentsComeFromPrevRow = parentIdsByNode.every(parentIds =>
        parentIds.length > 0 && parentIds.every(pid => prevRowSet.has(pid))
      );

      let rowDepth;

      if (rowIds.length === 1) {
        const soleParentIds = parentIdsByNode[0] || [];
        if (soleParentIds.length > 1) {
          rowDepth = Math.max(0, minParentDepth - 1);
        } else if (soleParentIds.length === 1) {
          const parentId = soleParentIds[0];
          const parentDepth = depthMap.get(parentId) ?? 0;
          rowDepth = prevRowSet.size > 1 ? parentDepth + 1 : parentDepth;
        } else {
          rowDepth = 0;
        }
      } else if (sharedSinglePrevParent) {
        rowDepth = (depthMap.get(sharedSinglePrevParent) ?? 0) + 1;
      } else if (parentsCoverEntirePrevRow) {
        const prevRowDepth = rowDepths[rowIndex - 1] ?? 0;
        if (rowIds.length > prevRowIds.length) rowDepth = prevRowDepth + 1;
        else if (rowIds.length < prevRowIds.length) rowDepth = Math.max(0, prevRowDepth - 1);
        else rowDepth = prevRowDepth;
      } else if (everyNodeHasExactlyOneParent && allParentsComeFromPrevRow) {
        rowDepth = maxParentDepth + 1;
      } else if (parentRowIndices.size > 1) {
        rowDepth = Math.max(0, minParentDepth - 1);
      } else {
        rowDepth = Math.max(minParentDepth, maxParentDepth);
      }

      rowDepths[rowIndex] = rowDepth;
      rowIds.forEach(id => depthMap.set(id, rowDepth));
    });

    return depthMap;
  },

  applyPageStackLayout(view, timelinePlan) {
    if (!view || !timelinePlan) return;

    if (!view._pageStackState) {
      const originalGroups = [...view.querySelectorAll(':scope > .level-group')];
      view._pageStackState = {
        originalGroups,
        originalChildrenByGroup: originalGroups.map(group => [...group.childNodes]),
        host: null
      };
    }

    const state = view._pageStackState;
    if (!state.host) {
      const host = document.createElement('div');
      host.className = 'page-stacked-host';

      timelinePlan.displayOrder.forEach(id => {
        const row = view.querySelector(`.node-row[data-id="${id}"]`);
        if (!row) return;

        const group = document.createElement('div');
        group.className = 'level-group';
        group.dataset.stacked = '';
        row.style.setProperty('--indent-depth', String(timelinePlan.depthMap.get(id) || 0));
        group.appendChild(row);

        const expanderEl = document.createElement('div');
        expanderEl.className = 'level-expander';
        group.appendChild(expanderEl);
        host.appendChild(group);
      });

      state.host = host;
      state.originalGroups[0]?.before(host);
    }

    state.originalGroups.forEach(group => {
      group.hidden = true;
      delete group.dataset.stacked;
    });

    view.dataset.pageStacked = '';
  },

  restorePageStackLayout(view) {
    const state = view?._pageStackState;
    if (!state) return;

    if (state.host) {
      state.originalGroups.forEach((group, index) => {
        state.originalChildrenByGroup[index].forEach(child => group.appendChild(child));
        group.hidden = false;
      });
      state.host.remove();
      state.host = null;
    }

    delete view.dataset.pageStacked;
  },

  applyResponsiveRunLayout(view, suppressAnimation = true) {
    const runs = view?._parallelRuns || [];
    const timelinePlan = view?._timelinePlan || null;
    if (!runs.length && !timelinePlan) return;

    if (suppressAnimation) view.classList.add('no-stack-transition');

    let pageShouldStack = false;
    runs.forEach(run => {
      const width = run.groups[0]?.getBoundingClientRect().width || 0;
      const shouldStack = run.maxChildCount > 1 && (width / run.maxChildCount) < STACK_THRESHOLD;
      run.isStacked = shouldStack;
      if (shouldStack) pageShouldStack = true;
    });

    const originalGroups = view._pageStackState?.originalGroups || [...view.querySelectorAll(':scope > .level-group')];

    if (pageShouldStack && timelinePlan) {
      this.applyPageStackLayout(view, timelinePlan);
    } else {
      this.restorePageStackLayout(view);
    }

    originalGroups.forEach(group => {
      delete group.dataset.stacked;
      group.querySelectorAll(':scope > .node-row').forEach(row => {
        row.style.removeProperty('--indent-depth');
      });
    });

    if (!pageShouldStack) {
      runs.forEach(run => {
        run.groups.forEach(group => {
          if (run.isStacked) group.dataset.stacked = '';
          else delete group.dataset.stacked;

          group.querySelectorAll(':scope > .node-row').forEach(row => {
            if (run.isStacked) {
              row.style.setProperty('--indent-depth', String(run.depthMap.get(row.dataset.id) || 0));
            }
          });
        });
      });
    }

    const pageStackGroups = view._pageStackState?.host
      ? [...view._pageStackState.host.querySelectorAll(':scope > .level-group')]
      : [];
    pageStackGroups.forEach(group => {
      group.dataset.stacked = '';
      group.querySelectorAll(':scope > .node-row').forEach(row => {
        row.style.setProperty('--indent-depth', String(timelinePlan?.depthMap.get(row.dataset.id) || 0));
      });
    });

    if (suppressAnimation) {
      view.offsetHeight;
      view.classList.remove('no-stack-transition');
    }
  },

  /* ------------------------------------------------------------------
   * Delegated click handling
   *
   * Single listener on #mapContainer handles all interactive elements.
   * Priority order: trigger-derive → search-result-header → node-header
   *                 → logic-header → mini-trigger
   * ------------------------------------------------------------------ */
  handleMapClick(e) {
    const deriveBtn = e.target.closest('.trigger-derive');
    if (deriveBtn) {
      const targetId = deriveBtn.dataset.target === 'null' ? null : deriveBtn.dataset.target;
      NavigationController.navigate(targetId);
      return;
    }

    const searchHeader = e.target.closest('.search-result-header');
    if (searchHeader) {
      const box = searchHeader.closest('.search-result-box');
      const collapsed = box.classList.toggle('is-collapsed');
      searchHeader.setAttribute('aria-expanded', !collapsed);
      return;
    }

    const nodeHeader = e.target.closest('.node-header');
    if (nodeHeader) {
      const card = nodeHeader.closest('.node-card');
      if (card) this.toggleExpander(card.dataset.id);
      return;
    }

    const logicHeader = e.target.closest('.logic-header');
    if (logicHeader) {
      const section = logicHeader.closest('.logic-section');
      const collapsed = section.classList.toggle('is-collapsed');
      logicHeader.setAttribute('aria-expanded', !collapsed);
      return;
    }

    const miniTrigger = e.target.closest('.mini-trigger');
    if (miniTrigger) {
      const miniNode = miniTrigger.closest('.mini-node');
      const isOpen = miniNode.classList.toggle('is-open');
      miniTrigger.setAttribute('aria-expanded', isOpen);
    }
  },

  /* ------------------------------------------------------------------
   * Search
   * ------------------------------------------------------------------ */

  /** Recursively flattens complex data structures into searchable text. */
  getNestedText(items) {
    if (!items) return '';
    return items.map(item => {
      if (typeof item === 'string') return item;
      let text = `${item.title || ''} ${item.detail || ''}`;
      if (item.subSections) {
        text += ' ' + item.subSections.map(sub =>
          `${sub.label || ''} ${this.getNestedText(sub.items)}`).join(' ');
      }
      if (item.children) text += ' ' + this.getNestedText(item.children);
      return text;
    }).join(' ');
  },

  handleSearch(rawQuery) {
    const query = rawQuery.toLowerCase().trim();

    if (query.length === 0) {
      this.els.container.innerHTML = '';
      NavigationController.loadState(AppState.currentParentId, 'replace');
      return;
    }

    if (AppState.activeNodeId !== null) this.toggleExpander(AppState.activeNodeId);

    // Determine search pool based on scope setting
    let searchPool = DataStore.nodes;
    if (!AppState.searchConfig.global) {
      searchPool = DataStore.nodes.filter(node => {
        if (AppState.currentParentId === null) return true;
        let current = node;
        while (current) {
          if (current.parentId === AppState.currentParentId || current.id === AppState.currentParentId) return true;
          current = DataStore.map.get(current.parentId);
        }
        return false;
      });
    }

    // Match against searchable text
    const matches = searchPool.filter(node => {
      let text = `${node.claim} ${node.soWhat} ${node.search || ''}`;
      if (AppState.searchConfig.nodeContents && node.sections) {
        text += ' ' + node.sections.map(sec =>
          `${sec.title || ''} ${this.getNestedText(sec.items)}`).join(' ');
      }
      return text.toLowerCase().includes(query);
    });

    // Update header for search context
    if (this.els.pageTitle) this.els.pageTitle.textContent = 'Global Search';
    if (this.els.pageSubtitle) this.els.pageSubtitle.textContent =
      `Found ${matches.length} result${matches.length !== 1 ? 's' : ''} for "${query}"`;
    if (this.els.breadcrumbCurrent) this.els.breadcrumbCurrent.textContent = 'Search Results';
    AppState.updateTints({ page: 'transparent' });

    this.els.container.innerHTML = '';

    if (matches.length === 0) {
      this.els.container.innerHTML = `<div class="map-flow">
        <div style="padding: 40px 20px; text-align: center; color: var(--text-muted);">
          No results found across any derivations.</div></div>`;
      return;
    }

    // Group matches by parentId (Map preserves insertion order)
    const grouped = new Map();
    matches.forEach(node => {
      if (!grouped.has(node.parentId)) grouped.set(node.parentId, []);
      grouped.get(node.parentId).push(node);
    });

    const fragment = document.createDocumentFragment();
    grouped.forEach((nodes, parentId) => {
      const parentNode = parentId ? DataStore.map.get(parentId) : null;
      const pageTitle = parentNode ? `${parentNode.id}. ${parentNode.claim}` : DataStore.config.title;

      const groupEl = document.createElement('div');
      groupEl.className = 'search-result-box';
      groupEl.innerHTML = `
        <div class="search-result-header" role="button" aria-expanded="true">
          <span><b>${pageTitle}</b></span>
        </div>
        <div class="search-result-content map-flow" style="margin-top: 0; padding-bottom: 16px;">
          <div class="map-spine" aria-hidden="true" style="top: 16px;"></div>
        </div>
      `;

      const flowEl = groupEl.querySelector('.map-flow');
      nodes.forEach(node => {
        const row = document.createElement('div');
        row.className = 'node-row';
        row.dataset.id = node.id;
        row.innerHTML = Templates.nodeRow(node);
        flowEl.appendChild(row);
      });

      fragment.appendChild(groupEl);
    });

    this.els.container.appendChild(fragment);
  },

  /* ------------------------------------------------------------------
   * Event binding
   * ------------------------------------------------------------------ */
  bindEvents() {
    this.els.themeToggle?.addEventListener('click', () => AppState.toggleTheme());

    // Mobile hamburger menu
    this.els.headerToggle?.addEventListener('click', () => {
      const isExpanded = this.els.pageHeader.classList.toggle('is-expanded');
      this.els.headerToggle.setAttribute('aria-expanded', isExpanded);
    });

    // Desktop chevron collapse
    this.els.chevronToggle?.addEventListener('click', () => {
      const isCollapsed = this.els.pageHeader.classList.toggle('is-desktop-collapsed');
      this.els.chevronToggle.setAttribute('aria-expanded', !isCollapsed);
      this.els.chevronToggle.setAttribute('aria-label', isCollapsed ? 'Expand Header' : 'Collapse Header');
    });

    // Search input (debounced)
    let searchTimeout;
    this.els.searchInput?.addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => this.handleSearch(e.target.value), 150);
    });

    // Search filter dropdown
    this.els.searchFilterBtn?.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = this.els.searchFilterMenu.classList.toggle('is-open');
      this.els.searchFilterBtn.setAttribute('aria-expanded', isOpen);
    });

    document.addEventListener('click', (e) => {
      if (this.els.searchFilterMenu?.classList.contains('is-open') && !e.target.closest('.search-input-wrap')) {
        this.els.searchFilterMenu.classList.remove('is-open');
        this.els.searchFilterBtn.setAttribute('aria-expanded', 'false');
      }
    });

    // Search config toggles (global and nested are mutually exclusive)
    const updateSearchConfig = () => {
      AppState.searchConfig.nodeContents = this.els.toggleNodeContentsSearch.checked;
      AppState.searchConfig.global = this.els.toggleGlobalSearch.checked;
      if (this.els.searchInput.value) this.handleSearch(this.els.searchInput.value);
    };

    this.els.toggleNodeContentsSearch?.addEventListener('change', updateSearchConfig);
    this.els.toggleGlobalSearch?.addEventListener('change', (e) => {
      if (e.target.checked && this.els.toggleNestedSearch) this.els.toggleNestedSearch.checked = false;
      updateSearchConfig();
    });
    this.els.toggleNestedSearch?.addEventListener('change', (e) => {
      if (e.target.checked && this.els.toggleGlobalSearch) this.els.toggleGlobalSearch.checked = false;
      updateSearchConfig();
    });

    // Breadcrumb navigation (global click delegation)
    document.addEventListener('click', (e) => {
      const crumb = e.target.closest('.crumb-link');
      if (crumb) {
        e.preventDefault();
        NavigationController.navigate(crumb.dataset.target === 'null' ? null : crumb.dataset.target);
      }
    });

    // Escape key closes active expander
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && AppState.activeNodeId !== null) {
        this.toggleExpander(AppState.activeNodeId);
      }
    });

    // Delegated map container click handler
    this.els.container?.addEventListener('click', (e) => this.handleMapClick(e));
  }
};


/**
 * =============================================================================
 * 10. BOOTSTRAP
 * =============================================================================
 * Loads JSON data, computes node colors, and initializes the application.
 */
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const mapName = new URLSearchParams(window.location.search).get('map') || 'data';
    const response = await fetch(`${mapName}.json`);
    if (!response.ok) throw new Error(`Could not find a file named ${mapName}.json`);

    const pageData = await response.json();

    // Compute perceptual colors per sibling group
    const parentGroups = new Map();
    pageData.nodes.forEach(node => {
      const pid = node.parentId;
      if (!parentGroups.has(pid)) parentGroups.set(pid, []);
      parentGroups.get(pid).push(node);
    });

    parentGroups.forEach(siblings => {
      siblings.forEach((node, index) => {
        const hue = Math.floor(getPerceptualHue(index, siblings.length));
        node.color = {
          borderDark: `hsl(${hue}, 95%, 68%)`,
          borderLight: `hsl(${hue}, 90%, 34%)`,
          top: `hsl(${hue}, 85%, 93%)`,
          bottom: `hsl(${hue}, 90%, 84%)`
        };
        node.hue = hue;
        DataStore.map.set(node.id, node);
      });
    });

    // Merge loaded config with safe defaults to prevent 'undefined' in the UI
    DataStore.config = {
      title: 'Map',
      subtitle: '',
      breadcrumbRoot: 'Home',
      searchPlaceholder: 'Search...',
      nodePrefix: '',
      ...pageData.config
    };
	
    DataStore.nodes = pageData.nodes;

    AppUI.init();
    NavigationController.init();

  } catch (error) {
    console.error('Failed to load page data:', error);
    document.getElementById('titleText').textContent = 'Error Loading Data';
    document.getElementById('subtitleText').textContent = error.message;
  }
});