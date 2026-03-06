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
  resizeTimeout: null,

  initResizeObserver() {
    if (this.observer) return;
    this.observer = new ResizeObserver(() => {
      // Keep the guard to prevent drawing while switching pages
      // or while stack/unstack CSS transitions are animating dots
      if (AppState.isTransitioning || AppState.isStackTransitioning) return;

	  // Clear the timer if the user is still resizing
      //clearTimeout(this.resizeTimeout);
	  
	  // Set a 50ms delay before drawing
      //this.resizeTimeout = setTimeout(() => {
        const viewEl = document.querySelector('.map-flow');
        if (viewEl) {
          const visibleNodes = DataStore.nodes.filter(n => n.parentId === AppState.currentParentId);
          // Drawing directly in requestAnimationFrame ensures smooth "sliding"
          requestAnimationFrame(() => this.draw(viewEl, visibleNodes));
        }
	  //}, 50);
    });
    this.observer.observe(document.getElementById('mapContainer'));
  },

  /**
   * Measures marker-dot centers from the DOM and draws connector paths.
   * @param {HTMLElement} viewEl - The .map-flow container.
   * @param {Array} visibleNodes - Nodes for the current page.
   */
  draw(viewEl, visibleNodes) {
    const oldSvg = viewEl.querySelector('.dag-svg');
    if (oldSvg) oldSvg.remove();

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'dag-svg');

    const containerRect = viewEl.getBoundingClientRect();
    const markerPositions = new Map();
    let trunkX = null;

    // 1. Read all marker-dot centers from the DOM
    const nodeEls = viewEl.querySelectorAll('.node-row:not(.dummy-node)');
    nodeEls.forEach((el, index) => {
      const id = el.dataset.id;
      const dot = el.querySelector('.marker-dot');
      const card = el.querySelector('.node-card');
      if (!dot || !card) return;

      const dotRect = dot.getBoundingClientRect();
      const cardRect = card.getBoundingClientRect();

      // Dot center coordinates relative to the container
      const x = dotRect.left - containerRect.left + dotRect.width / 2;
      const y = dotRect.top - containerRect.top + dotRect.height / 2;

      // First node defines the trunk axis for the mask
      if (index === 0) trunkX = x;

      // Card boundaries for routing lateral paths
      const levelGroup = el.closest('.level-group');
      const levelRect = levelGroup.getBoundingClientRect();
      const levelBottom = levelRect.bottom - containerRect.top;

      const nextGroup = levelGroup.nextElementSibling;
      const gapBottom = (nextGroup?.classList.contains('level-group'))
        ? nextGroup.getBoundingClientRect().top - containerRect.top
        : levelBottom + 16;
	  
	  const expander = levelGroup.querySelector('.level-expander');
	  const expInner = expander?.querySelector('.exp-inner');

	  // Use the inner box's bottom if it exists and is visible
	  const visualBottom = (expander?.classList.contains('is-open') && expInner) 
	    ? expInner.getBoundingClientRect().bottom - containerRect.top 
	    : cardRect.bottom - containerRect.top;

	  markerPositions.set(id, {
	    x, y,
	    cardTop: cardRect.top - containerRect.top,
	    cardBottom: cardRect.bottom - containerRect.top,
	    visualBottom, // Use this for the drop calculation
	    gapBottom
	  });
    });

    // 2. Build mask to hide SVG paths behind the HTML spine
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const mask = document.createElementNS('http://www.w3.org/2000/svg', 'mask');
    mask.setAttribute('id', 'trunkMask');

    const whiteBg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    whiteBg.setAttribute('x', '0');
    whiteBg.setAttribute('y', '0');
    whiteBg.setAttribute('width', '100%');
    whiteBg.setAttribute('height', '100%');
    whiteBg.setAttribute('fill', 'white');
    mask.appendChild(whiteBg);

    if (trunkX !== null) {
      const blackStrip = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      blackStrip.setAttribute('x', trunkX - 1);
      blackStrip.setAttribute('y', '0');
      blackStrip.setAttribute('width', '2');
      blackStrip.setAttribute('height', '100%');
      blackStrip.setAttribute('fill', 'black');
      mask.appendChild(blackStrip);
    }
    defs.appendChild(mask);
    svg.appendChild(defs);

    // 2b. Compute edges to skip for stacked parallel groups.
    //     When a group is stacked, the CSS ::before spine handles vertical
    //     connections within the group. We only need ONE SVG branch into the
    //     group (to the first node) and ONE branch out (from the last node)
    //     per shared predecessor/successor.
    const skipEdges = new Set();

    viewEl.querySelectorAll('.level-group[data-stacked]').forEach(group => {
      const nodeIds = [...group.querySelectorAll(':scope > .node-row')]
        .map(r => r.dataset.id);
      const nodeIdSet = new Set(nodeIds);

      // --- Incoming edges: group by source, keep only first target ---
      const incomingBySource = new Map();
      nodeIds.forEach(nid => {
        const node = DataStore.map.get(nid);
        if (!node?.prevIds) return;
        node.prevIds.forEach(pid => {
          if (nodeIdSet.has(pid)) return; // internal edge
          if (!incomingBySource.has(pid)) incomingBySource.set(pid, []);
          incomingBySource.get(pid).push(nid);
        });
      });

      incomingBySource.forEach((targets, source) => {
        if (targets.length <= 1) return;
        const firstIdx = Math.min(...targets.map(t => nodeIds.indexOf(t)));
        targets.forEach(t => {
          if (nodeIds.indexOf(t) !== firstIdx) skipEdges.add(`${source}→${t}`);
        });
      });

      // --- Outgoing edges: group by target, keep only last source ---
      const outgoingByTarget = new Map();
      nodeIds.forEach(nid => {
        const node = DataStore.map.get(nid);
        if (!node?.nextIds) return;
        node.nextIds.forEach(nextId => {
          if (nodeIdSet.has(nextId)) return; // internal edge
          if (!outgoingByTarget.has(nextId)) outgoingByTarget.set(nextId, []);
          outgoingByTarget.get(nextId).push(nid);
        });
      });

      outgoingByTarget.forEach((sources, target) => {
        if (sources.length <= 1) return;
        const lastIdx = Math.max(...sources.map(s => nodeIds.indexOf(s)));
        sources.forEach(s => {
          if (nodeIds.indexOf(s) !== lastIdx) skipEdges.add(`${s}→${target}`);
        });
      });
    });

    // 3. Build all path segments
    let allPathData = '';
    const STRAIGHT_THRESHOLD = 5;  // Treat near-vertical connections as straight
    const MAX_CORNER_RADIUS = 12;

    visibleNodes.forEach(node => {
      if (!node.nextIds?.length) return;
      const start = markerPositions.get(node.id);
      if (!start) return;

      node.nextIds.forEach(nextId => {
        if (skipEdges.has(`${node.id}→${nextId}`)) return;

        const end = markerPositions.get(nextId);
        if (!end) return;

        if (Math.abs(start.x - end.x) < STRAIGHT_THRESHOLD) {
          // Straight vertical connection
          allPathData += `M ${start.x} ${start.y} L ${end.x} ${end.y} `;
        } else {
          // Lateral routed path: down → corner → horizontal → corner → down
          const dirX = end.x > start.x ? 1 : -1;
		  //let dropY = start.visualBottom + (end.cardTop - start.visualBottom) / 2;
		  let dropY;
          const earlyDrop = start.visualBottom + (start.gapBottom - start.visualBottom) / 2;
          
          if (dirX === 1) {
            // Outward branch: drop early (in the gap immediately after start)
            dropY = earlyDrop;
          } else {
            // Inward merge: drop late (just above the target node)
            // This ensures timelines continuing straight past nested nodes don't merge early.
            const lateDrop = end.cardTop - 16;
            dropY = Math.max(earlyDrop, lateDrop);
          }
		  
          const radius = Math.min(
            MAX_CORNER_RADIUS,
            Math.abs(end.x - start.x) / 2,
            Math.max(0, Math.abs(dropY - start.y) - 2),
            Math.max(0, Math.abs(end.y - dropY) - 2)
          );

          allPathData += `M ${start.x} ${start.y} ` +
            `L ${start.x} ${dropY - radius} ` +
            `Q ${start.x} ${dropY} ${start.x + radius * dirX} ${dropY} ` +
            `L ${end.x - radius * dirX} ${dropY} ` +
            `Q ${end.x} ${dropY} ${end.x} ${dropY + radius} ` +
            `L ${end.x} ${end.y} `;
        }
      });
    });

    // 4. Render single combined path
    if (allPathData) {
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('class', 'dag-edge');
      path.setAttribute('d', allPathData.trim());
      path.setAttribute('mask', 'url(#trunkMask)');
      svg.appendChild(path);
    }

    viewEl.prepend(svg);
  }
};


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

  buildList(items) {
    return `<ul class="bullets">${items.map(i => `<li>${i}</li>`).join('')}</ul>`;
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
          <div class="sub-body">${this.buildList(sub.items)}</div>
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
    this.els.toggleDeepSearch = byId('toggleDeepSearch');
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

      // Parallel tagging: mark groups with >1 flex children for CSS equalization.
      // Three attributes:
      //   data-parallel on the group (triggers parallel layout rules)
      //   data-first-parallel on the first real node (keeps spine-aligned marker)
      //   data-last-parallel on the last real node (keeps full derive button)
      //const totalFlexChildren = realNodeEls.length + rowNodes.filter(n => n.isDummy).length;
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

    // Compute consecutive-parallel indent depth for stacking.
    // Each run of adjacent parallel groups gets incrementing depth (1, 2, 3…).
    // A non-parallel group resets the counter.
    let consecutiveDepth = 0;
    allLevelGroups.forEach(group => {
      if ('parallel' in group.dataset) {
        consecutiveDepth++;
        group.style.setProperty('--indent-depth', consecutiveDepth);
      } else {
        consecutiveDepth = 0;
      }
    });

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

    // Phase 1b: Attach stacking observer for parallel groups
    this.setupStackingObserver(newView);

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

    row.classList.remove('is-active');
    document.body.classList.remove('is-focused');
    AppState.activeNodeId = null;
    AppState.updateTints({ expander: 'transparent' });

    // Deferred cleanup: clear innerHTML after the CSS transition completes
    setTimeout(() => {
      if (!expander.classList.contains('is-open')) expander.innerHTML = '';
    }, ANIMATION_SPEEDS.CSS_TRANSITION_MS);
  },

  openExpander(id, row, expander, headerBtn, inlineBtn) {
    const nodeData = DataStore.map.get(id);
    if (!nodeData) return;

    expander.innerHTML = Templates.expander(nodeData);
    this.bindTabEvents(expander, nodeData);
    this.bindActionEvents(expander);

    requestAnimationFrame(() => {
      expander.classList.add('is-open');
      headerBtn.setAttribute('aria-expanded', 'true');
      if (inlineBtn) inlineBtn.textContent = 'Hide';

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
   * Parallel → stacked layout observer
   *
   * Monitors each parallel level-group's width. When the available
   * width per flex child drops below STACK_THRESHOLD, the group switches
   * to a stacked (indented list) layout via the data-stacked attribute.
   *
   * The metric (groupWidth ÷ childCount) is stable regardless of whether
   * the group is currently stacked or parallel — the group fills its
   * parent container either way — so no hysteresis or special unstacking
   * logic is needed. SVG redraws are suppressed during the CSS transition
   * (400ms) and a single clean redraw fires at the end.
   * ------------------------------------------------------------------ */
  stackingObserver: null,
  _stackRedrawTimer: null,

  setupStackingObserver(view) {
    if (this.stackingObserver) {
      this.stackingObserver.disconnect();
      this.stackingObserver = null;
    }

    const parallelGroups = view.querySelectorAll('.level-group[data-parallel]');
    if (parallelGroups.length === 0) return;

    this.stackingObserver = new ResizeObserver(entries => {
      if (AppState.isTransitioning) return;

      let changed = false;

      for (const entry of entries) {
        const group = entry.target;
        const flexChildren = group.querySelectorAll(':scope > .node-row, :scope > .dummy-node');
        const count = flexChildren.length;
        if (count <= 1) continue;

        const widthPerChild = entry.contentRect.width / count;
        const shouldStack = widthPerChild < STACK_THRESHOLD;
        const isStacked = 'stacked' in group.dataset;

        if (shouldStack && !isStacked) {
          group.dataset.stacked = '';
          changed = true;
        } else if (!shouldStack && isStacked) {
          delete group.dataset.stacked;
          changed = true;
        }
      }

      if (changed) {
        // Suppress SVG redraws during the 400ms CSS transition, then
        // do one clean redraw once all positions have settled.
        AppState.isStackTransitioning = true;
        clearTimeout(this._stackRedrawTimer);
        this._stackRedrawTimer = setTimeout(() => {
          AppState.isStackTransitioning = false;
          requestAnimationFrame(() => {
            const visibleNodes = DataStore.nodes.filter(n => n.parentId === AppState.currentParentId);
            SVGEngine.draw(view, visibleNodes);
          });
        }, 420);
      }
    });

    parallelGroups.forEach(group => this.stackingObserver.observe(group));
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
  getDeepText(items) {
    if (!items) return '';
    return items.map(item => {
      if (typeof item === 'string') return item;
      let text = `${item.title || ''} ${item.detail || ''}`;
      if (item.subSections) {
        text += ' ' + item.subSections.map(sub =>
          `${sub.label || ''} ${this.getDeepText(sub.items)}`).join(' ');
      }
      if (item.children) text += ' ' + this.getDeepText(item.children);
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
      if (AppState.searchConfig.deep && node.sections) {
        text += ' ' + node.sections.map(sec =>
          `${sec.title || ''} ${this.getDeepText(sec.items)}`).join(' ');
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
      AppState.searchConfig.deep = this.els.toggleDeepSearch.checked;
      AppState.searchConfig.global = this.els.toggleGlobalSearch.checked;
      if (this.els.searchInput.value) this.handleSearch(this.els.searchInput.value);
    };

    this.els.toggleDeepSearch?.addEventListener('change', updateSearchConfig);
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