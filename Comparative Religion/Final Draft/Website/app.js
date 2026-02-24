/**
 * ==========================================
 * GLOBAL CONFIGURATIONS & STATE
 * ==========================================
 */
const ANIMATION_SPEEDS = {
  CSS_TRANSITION_MS: 500,
  SCROLL_DELAY_MS: 510
};

/**
 * Centralized data store for the application.
 */
const DataStore = {
  config: {},
  nodes: [],
  map: new Map() // Fast lookup dictionary for nodes by ID
};

const AppState = {
  theme: localStorage.getItem('theme') || 'dark',
  activeNodeId: null,      // The node currently expanded in the UI
  currentParentId: null,   // The level we are viewing (null = root level)
  
  searchConfig: {
    deep: true,
    global: true
  },
  
  toggleTheme() {
    document.body.classList.add('theme-transition'); // 1. Add transition class
    
    this.theme = this.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', this.theme);
    this.applyTheme();
    
    // 2. Remove class after CSS transition finishes (300ms)
    setTimeout(() => document.body.classList.remove('theme-transition'), 300); 
  },

  applyTheme() {
    document.documentElement.setAttribute('data-theme', this.theme);
    if (AppUI.els.themeToggle) {
      const isLight = this.theme === 'light';
      AppUI.els.themeToggle.textContent = isLight ? '☀️ Light' : '🌙 Dark';
      AppUI.els.themeToggle.setAttribute('aria-label', `Switch to ${isLight ? 'dark' : 'light'} mode`);
    }
  }
};

/**
 * ==========================================
 * PERCEPTUAL COLOR ENGINE
 * ==========================================
 */

/**
 * Calculates a visually distinct hue based on a node's index among its siblings.
 * @param {number} index - The index of the node.
 * @param {number} totalNodes - The total number of sibling nodes.
 * @returns {number} The calculated hue value.
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
 * ==========================================
 * NAVIGATION & ROUTING CONTROLLER
 * ==========================================
 */
const NavigationController = {
  init() {
    window.addEventListener('popstate', (e) => {
      const nodeId = e.state ? e.state.nodeId : null;
      this.loadState(nodeId, 'restore');
    });

    const urlParams = new URLSearchParams(window.location.search);
    const initialNode = urlParams.get('node');
    this.loadState(initialNode, 'replace');
  },

  navigate(targetId) {
    this.loadState(targetId, 'push');
  },

  /**
   * Determines the spatial direction for the transition animation.
   * @param {string|null} fromId 
   * @param {string|null} toId 
   * @returns {string} Direction string ('depth', 'surface', 'lateral-next', 'lateral-prev', 'none')
   */
  getDirection(fromId, toId) {
    if (fromId === toId) return 'none';
    if (!fromId && toId) return 'depth'; 
    if (fromId && !toId) return 'surface';
    
    const fromNode = DataStore.map.get(fromId);
    const toNode = DataStore.map.get(toId);
    
    if (toNode && toNode.parentId === fromId) return 'depth';
    if (fromNode && fromNode.parentId === toId) return 'surface';
    
    if (fromNode && toNode && fromNode.parentId === toNode.parentId) {
      const fromIndex = DataStore.nodes.findIndex(n => n.id === fromId);
      const toIndex = DataStore.nodes.findIndex(n => n.id === toId);
      return toIndex > fromIndex ? 'lateral-next' : 'lateral-prev';
    }
    
    return 'surface'; 
  },

  loadState(nodeId, historyAction = 'push') {
    if (AppUI.els.searchInput && AppUI.els.searchInput.value) {
      AppUI.els.searchInput.value = '';
      document.body.classList.remove('is-searching');
    }

    const prevId = AppState.currentParentId;
    const direction = this.getDirection(prevId, nodeId);

    AppState.currentParentId = nodeId;
    AppState.activeNodeId = null; 
    document.body.classList.remove('is-focused'); 

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
 * ==========================================
 * TEMPLATE GENERATION ENGINE
 * ==========================================
 */
const Templates = {
  nodeRow(node) {
    const parentNode = node.parentId ? DataStore.map.get(node.parentId) : null;
    const pillColorDark = parentNode ? parentNode.color.borderDark : node.color.borderDark;
    const pillColorLight = parentNode ? parentNode.color.borderLight : node.color.borderLight;

    const badgeTarget = parentNode && parentNode.parentId === null ? 'null' : (parentNode ? parentNode.parentId : '');
    
    // Updated button to use badgeTarget
    const badgeHtml = parentNode
      ? `<button class="node-badge trigger-derive" type="button" data-target="${badgeTarget}" aria-label="Go to parent step ${parentNode.id}"><span class="badge-dot"></span>${parentNode.id}</button>` 
      : '';
      
    const derivationHtml = (node.hasDerivation !== false)
      ? `<button class="btn-derivation trigger-derive" data-target="${node.id}" aria-label="Derivation details for step ${node.id}"><span class="label">Derivation</span><span>→</span></button>`
      : `<button class="btn-derivation" aria-hidden="true" disabled style="visibility: hidden; pointer-events: none;"><span class="label">Derivation</span><span>→</span></button>`;

    return `
      <div class="node-marker" aria-hidden="true"><span class="marker-arrow-tip"></span></div>
      <article class="node-card" data-id="${node.id}" 
        style="--n-border-dark: ${node.color.borderDark}; --n-border-light: ${node.color.borderLight}; --n-top: ${node.color.top}; --n-bottom: ${node.color.bottom}; --p-border-dark: ${pillColorDark}; --p-border-light: ${pillColorLight};">
        <div class="node-header" role="button" aria-expanded="false" aria-controls="exp-${node.id}">
          <h2 class="node-title"><span class="id">${node.id}.</span> ${node.claim}</h2>
          <div class="node-controls">
            ${badgeHtml}
            <button class="btn-ui trigger-inline" type="button" tabindex="-1">Expand</button>
          </div>
        </div>
        <p class="node-so-what">${node.soWhat}</p>
      </article>
      ${derivationHtml}
      <div class="node-expander" id="exp-${node.id}" role="region" aria-labelledby="node-title-${node.id}"></div>
    `;
  },
  
  expander(node) {
    const rowSections = (node.sections || []).filter(s => s.type === "row");
    const logicGroupHtml = rowSections.map((s, idx) => this.logicRow(s.title, s.items, idx + 1, s.numbered)).join('');

    const tabSections = (node.sections || []).filter(s => s.type === "tab");
    let tabAreaHtml = '';
    
    let actionHtml = '';
    if (node.hasDerivation !== false) {
      actionHtml = `<button class="btn-action btn-derivation-disagree trigger-derive" type="button" data-target="${node.id}">Disagree? See how this is derived →</button>`;
    } else {
      actionHtml = `
        <button class="btn-action btn-agree" type="button" aria-pressed="true">I agree</button>
        <button class="btn-action btn-disagree" type="button" aria-pressed="false">I disagree</button>
      `;
    }
    
    const actionSlotHtml = actionHtml ? `<div class="panel-action-slot">${actionHtml}</div>` : '';

    if (tabSections.length > 0) {
      const defaultTab = tabSections[0].title;
      const tabButtonsHtml = tabSections.map(s => `
        <button class="btn-tab" data-key="${s.title}" aria-selected="${s.title === defaultTab}" aria-controls="panel-${node.id}">
          ${s.title}
        </button>
      `).join('');

      tabAreaHtml = `
        <div class="tab-area">
          <div class="tab-list" role="tablist" aria-label="Logic Implications">
            ${tabButtonsHtml}
          </div>
          ${actionSlotHtml}
          <div class="tab-panel" id="panel-${node.id}" role="tabpanel"></div>
        </div>
      `;
    } else if (actionSlotHtml) {
      tabAreaHtml = `<div class="tab-area" style="grid-template-columns: 1fr;">${actionSlotHtml}</div>`;
    }

    return `<div class="exp-inner"><div class="logic-group">${logicGroupHtml}</div>${tabAreaHtml}</div>`;
  },

  logicRow(label, items, step, isNumbered) {
    if (!items || items.length === 0) return '';
    const isComplex = typeof items[0] === 'object' && items[0] !== null;
    const content = isComplex 
      ? `<div class="mini-stack">${items.map((it, idx) => this.recursiveMiniNode(it, isNumbered ? idx + 1 : null)).join('')}</div>`
      : this.buildList(items);
    
    return `
      <div class="logic-section" data-step="${step}">
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
    if (data.detail) parts.push(`<div style="padding:10px 0; text-align: left;"><div class="sub-body">${data.detail}</div></div>`);
    if (data.subSections?.length > 0) {
      parts.push(data.subSections.map(sub => `
        <div class="sub-section">
          <div class="sub-label">${sub.label}</div>
          <div class="sub-body">${this.buildList(sub.items)}</div>
        </div>
      `).join(''));
    }
    if (data.children?.length > 0) {
      parts.push(`<div class="mini-stack" style="margin-top:12px;">${data.children.map((c, idx) => this.recursiveMiniNode(c, idx + 1)).join('')}</div>`);
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
    if (!items || items.length === 0) return `<ul class="bullets"><li>—</li></ul>`;
    const isComplex = typeof items[0] === 'object' && items[0] !== null;
    if (isComplex) return `<div class="mini-stack">${items.map((it, idx) => this.recursiveMiniNode(it, isNumbered ? idx + 1 : null)).join('')}</div>`;
    return this.buildList(items);
  }
};

/**
 * ==========================================
 * UI CONTROLLER & EVENT HANDLERS
 * ==========================================
 */
const AppUI = {
  els: {},

  init() {
    this.cacheDOM();
    AppState.applyTheme();
    this.bindEvents();
  },

  cacheDOM() {
    this.els.docTitle = document.getElementById('docTitle');
    this.els.pageTitle = document.getElementById('titleText');
    this.els.pageSubtitle = document.getElementById('subtitleText');
    this.els.breadcrumbRoot = document.getElementById('breadcrumbRoot');
    this.els.breadcrumbCurrent = document.getElementById('breadcrumbCurrent');
    this.els.container = document.getElementById('mapContainer');
    this.els.searchInput = document.getElementById('searchInput');
    this.els.themeToggle = document.getElementById('themeToggle');
    this.els.headerToggle = document.getElementById('headerToggle');
    this.els.chevronToggle = document.getElementById('chevronToggle');
    this.els.pageHeader = document.getElementById('pageHeader');
    this.els.searchFilterBtn = document.getElementById('searchFilterBtn');
    this.els.searchFilterMenu = document.getElementById('searchFilterMenu');
    this.els.toggleDeepSearch = document.getElementById('toggleDeepSearch');
    this.els.toggleGlobalSearch = document.getElementById('toggleGlobalSearch');
	this.els.toggleNestedSearch = document.getElementById('toggleNestedSearch');
  },

  updateHeaderContext() {
    document.body.style.setProperty('--bg-tint-right', 'transparent'); 
    
    if (!AppState.currentParentId) {
      document.body.style.setProperty('--bg-tint', 'transparent'); 
      
      if (this.els.docTitle) this.els.docTitle.textContent = `${DataStore.config.title} - Map`;
      if (this.els.pageTitle) this.els.pageTitle.textContent = DataStore.config.title;
      if (this.els.pageSubtitle) this.els.pageSubtitle.textContent = DataStore.config.subtitle;
      if (this.els.breadcrumbRoot) this.els.breadcrumbRoot.innerHTML = `<a href="#" class="crumb-link" data-target="null">${DataStore.config.breadcrumbRoot}</a>`;
      if (this.els.breadcrumbCurrent) this.els.breadcrumbCurrent.textContent = DataStore.config.title;
    } else {
      const parentNode = DataStore.map.get(AppState.currentParentId);
      if (!parentNode) return;

      document.body.style.setProperty('--bg-tint', `hsla(${parentNode.hue}, 80%, 50%, 0.35)`);

      if (this.els.docTitle) this.els.docTitle.textContent = `${DataStore.config.nodePrefix}${parentNode.id} - Map`;
      if (this.els.pageTitle) this.els.pageTitle.textContent = `${DataStore.config.nodePrefix}${parentNode.id}. ${parentNode.claim}`;
      if (this.els.pageSubtitle) this.els.pageSubtitle.textContent = parentNode.soWhat;
      
      this.renderBreadcrumbs(parentNode.id);
    }
    if (this.els.searchInput) this.els.searchInput.placeholder = DataStore.config.searchPlaceholder;
  },

  renderBreadcrumbs(activeNodeId) {
    if (!this.els.breadcrumbRoot || !this.els.breadcrumbCurrent) return;
    
    const lineage = [];
    let current = DataStore.map.get(activeNodeId);
    while (current) {
      lineage.unshift(current);
      current = DataStore.map.get(current.parentId);
    }

    let html = `<a href="#" class="crumb-link" data-target="null">${DataStore.config.breadcrumbRoot}</a>`;
    html += ` <span class="sep" aria-hidden="true">›</span> <a href="#" class="crumb-link" data-target="null">${DataStore.config.title}</a>`;

    for (let i = 0; i < lineage.length - 1; i++) {
      const node = lineage[i];
      html += ` <span class="sep" aria-hidden="true">›</span> <a href="#" class="crumb-link" data-target="${node.id}">${DataStore.config.nodePrefix}${node.id}</a>`;
    }

    this.els.breadcrumbRoot.innerHTML = html;
    
    const activeNode = lineage[lineage.length - 1];
    this.els.breadcrumbCurrent.textContent = `${DataStore.config.nodePrefix}${activeNode.id}`;
  },

  /**
   * Builds the incoming DOM view based on the current state.
   * @private
   */
  _buildIncomingView() {
    const newView = document.createElement('div');
    newView.className = 'map-flow';
    newView.innerHTML = '<div class="map-spine" aria-hidden="true"></div>';
    
    const visibleNodes = DataStore.nodes.filter(node => node.parentId === AppState.currentParentId);
    
    if (visibleNodes.length === 0) {
      newView.innerHTML += `<div style="padding: 40px 20px; text-align: center; color: var(--text-muted);">No deeper derivations mapped for this claim yet.</div>`;
    } else {
      const fragment = document.createDocumentFragment();
      visibleNodes.forEach(node => {
        const row = document.createElement('div');
        row.className = 'node-row';
        row.dataset.id = node.id;
        row.dataset.search = node.search;
        row.innerHTML = Templates.nodeRow(node);
        fragment.appendChild(row);
      });
      newView.appendChild(fragment);
    }
    return newView;
  },

  /**
   * Prepends/Appends navigation cards for adjacent siblings if applicable.
   * @private
   */
  _appendSiblingNavigation(view) {
    const parentNode = AppState.currentParentId ? DataStore.map.get(AppState.currentParentId) : null;
    if (!parentNode) return;

    const prevNode = DataStore.nodes.find(n => n.nextSiblingId === parentNode.id);
    if (prevNode) {
      const prevHeader = document.createElement('div');
      prevHeader.className = 'sibling-nav-area prev';
      prevHeader.innerHTML = `
        <div class="sibling-label">Previous Step in Logic</div>
        <button class="btn-sibling prev-btn trigger-derive" data-target="${prevNode.id}" type="button">
          <span class="sibling-arrow">↑</span>
          <span class="sibling-id">${DataStore.config.nodePrefix}${prevNode.id}.</span>
          <span class="sibling-claim">${prevNode.claim}</span>
        </button>
      `;
      view.prepend(prevHeader);
    }

    if (parentNode.nextSiblingId) {
      const nextNode = DataStore.map.get(parentNode.nextSiblingId);
      if (nextNode) {
        const nextFooter = document.createElement('div');
        nextFooter.className = 'sibling-nav-area next';
        nextFooter.innerHTML = `
          <div class="sibling-label">Next Step in Logic</div>
          <button class="btn-sibling next-btn trigger-derive" data-target="${nextNode.id}" type="button">
            <span class="sibling-arrow">↓</span>
            <span class="sibling-id">${DataStore.config.nodePrefix}${nextNode.id}.</span>
            <span class="sibling-claim">${nextNode.claim}</span>
          </button>
        `;
        view.appendChild(nextFooter);
      }
    }
  },

  renderMapWithTransition(direction) {
    const oldViews = this.els.container.querySelectorAll('.map-flow, .search-result-box, .search-group');
    this.els.container.style.pointerEvents = 'none';
    
    const currentHeight = this.els.container.offsetHeight;
    this.els.container.style.minHeight = `${currentHeight}px`;
    this.els.container.style.overflow = 'hidden';
    
    const newView = this._buildIncomingView();
    this._appendSiblingNavigation(newView);

    oldViews.forEach(oldView => {
      if (direction === 'depth') oldView.classList.add('anim-exit-left');
      else if (direction === 'surface') oldView.classList.add('anim-exit-right');
      else if (direction === 'lateral-next') oldView.classList.add('anim-exit-top');
      else if (direction === 'lateral-prev') oldView.classList.add('anim-exit-bottom');
      
      oldView.style.position = 'absolute';
      oldView.style.top = '0';
      oldView.style.left = '0';
    });

    if (direction === 'depth') newView.classList.add('anim-enter-right');
    else if (direction === 'surface') newView.classList.add('anim-enter-left');
    else if (direction === 'lateral-next') newView.classList.add('anim-enter-bottom');
    else if (direction === 'lateral-prev') newView.classList.add('anim-enter-top');

    this.els.container.appendChild(newView);
    window.scrollTo(0, 0); 

    setTimeout(() => {
      oldViews.forEach(oldView => oldView.remove()); 
      newView.classList.remove('anim-enter-right', 'anim-enter-left', 'anim-enter-bottom', 'anim-enter-top');
      this.els.container.style.pointerEvents = ''; 
      
      this.els.container.style.minHeight = '';
      this.els.container.style.overflow = '';
      
    }, ANIMATION_SPEEDS.CSS_TRANSITION_MS);
  },
  
  bindEvents() {
    this.els.themeToggle?.addEventListener('click', () => AppState.toggleTheme());

    this.els.headerToggle?.addEventListener('click', () => {
      const isExpanded = this.els.pageHeader.classList.toggle('is-expanded');
      this.els.headerToggle.setAttribute('aria-expanded', isExpanded);
    });

    this.els.chevronToggle?.addEventListener('click', () => {
      const isCollapsed = this.els.pageHeader.classList.toggle('is-desktop-collapsed');
      this.els.chevronToggle.setAttribute('aria-expanded', !isCollapsed);
      this.els.chevronToggle.setAttribute('aria-label', isCollapsed ? 'Expand Header' : 'Collapse Header');
    });

    let searchTimeout;
    this.els.searchInput?.addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => this.handleSearch(e.target.value), 150);
    });
    
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

    const updateSearchConfig = () => {
      AppState.searchConfig.deep = this.els.toggleDeepSearch.checked;
      AppState.searchConfig.global = this.els.toggleGlobalSearch.checked;
      if (this.els.searchInput.value) {
        this.handleSearch(this.els.searchInput.value);
      }
    };
    
    this.els.toggleDeepSearch?.addEventListener('change', updateSearchConfig);
    
    // Global checkbox logic
    this.els.toggleGlobalSearch?.addEventListener('change', (e) => {
      if (e.target.checked && this.els.toggleNestedSearch) {
        this.els.toggleNestedSearch.checked = false;
      }
      updateSearchConfig();
    });

    // Nested checkbox logic
    this.els.toggleNestedSearch?.addEventListener('change', (e) => {
      if (e.target.checked && this.els.toggleGlobalSearch) {
        this.els.toggleGlobalSearch.checked = false;
      }
      updateSearchConfig();
    });

    document.addEventListener('click', (e) => {
      const crumb = e.target.closest('.crumb-link');
      if (crumb) {
        e.preventDefault();
        const targetId = crumb.dataset.target === "null" ? null : crumb.dataset.target;
        NavigationController.navigate(targetId);
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && AppState.activeNodeId !== null) {
        this.toggleExpander(AppState.activeNodeId);
      }
    });
	
	this.els.container?.addEventListener('click', (e) => this.handleMapClick(e));
  },

  /**
   * Recursively flattens complex data structures into searchable string content.
   * @private
   */
  _getDeepText(items) {
    if (!items) return '';
    return items.map(item => {
      if (typeof item === 'string') return item;
      
      let text = `${item.title || ''} ${item.detail || ''}`;
      
      if (item.subSections) {
        text += ' ' + item.subSections.map(sub => `${sub.label || ''} ${this._getDeepText(sub.items)}`).join(' ');
      }
      
      if (item.children) {
        text += ' ' + this._getDeepText(item.children);
      }
      
      return text;
    }).join(' ');
  },

  handleSearch(rawQuery) {
    const query = rawQuery.toLowerCase().trim();
    
    if (query.length === 0) {
      document.body.classList.remove('is-searching');
      this.els.container.innerHTML = ''; // 1. Instantly clear search results
      NavigationController.loadState(AppState.currentParentId, 'replace');
      return;
    }

    if (AppState.activeNodeId !== null) {
       this.toggleExpander(AppState.activeNodeId);
    }

    document.body.classList.add('is-searching');

    let searchPool = DataStore.nodes;
    if (!AppState.searchConfig.global) {
      searchPool = DataStore.nodes.filter(node => {
        // If we are on the root level, nested search is effectively global
        if (AppState.currentParentId === null) return true;
        
        // Traverse upwards to see if the current view is an ancestor of this node
        let current = node;
        while (current) {
          if (current.parentId === AppState.currentParentId || current.id === AppState.currentParentId) return true;
          current = DataStore.map.get(current.parentId);
        }
        return false;
      });
    }

    const matches = searchPool.filter(node => {
      let searchableText = `${node.claim} ${node.soWhat} ${node.search || ''}`;
      
      if (AppState.searchConfig.deep) {
        let deepContent = '';
        if (node.sections) {
          deepContent = node.sections.map(sec => `${sec.title || ''} ${this._getDeepText(sec.items)}`).join(' ');
        }
        searchableText += ` ${deepContent}`;
      }
      
      return searchableText.toLowerCase().includes(query);
    });

    if (this.els.pageTitle) this.els.pageTitle.textContent = "Global Search";
    if (this.els.pageSubtitle) this.els.pageSubtitle.textContent = `Found ${matches.length} result${matches.length !== 1 ? 's' : ''} for "${query}"`;
    if (this.els.breadcrumbCurrent) this.els.breadcrumbCurrent.textContent = "Search Results";
    document.body.style.setProperty('--bg-tint', 'transparent'); 

    this.els.container.innerHTML = '';
    
    if (matches.length === 0) {
      this.els.container.innerHTML = '<div class="map-flow"><div style="padding: 40px 20px; text-align: center; color: var(--text-muted);">No results found across any derivations.</div></div>';
      return;
    }

    // Group matches by parentId. The Map preserves our BFS insertion order!
    const groupedResults = new Map();
    matches.forEach(node => {
      if (!groupedResults.has(node.parentId)) groupedResults.set(node.parentId, []);
      groupedResults.get(node.parentId).push(node);
    });

    const fragment = document.createDocumentFragment();

    groupedResults.forEach((nodes, parentId) => {
      const parentNode = parentId ? DataStore.map.get(parentId) : null;
      // 3. Format strictly as "[id]. [claim]"
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

  handleMapClick(e) {
    const deriveBtn = e.target.closest('.trigger-derive');
    if (deriveBtn) {
      // Translate 'null' string to actual null for root navigation
      const targetId = deriveBtn.dataset.target === "null" ? null : deriveBtn.dataset.target;
      NavigationController.navigate(targetId);
      return;
    }
	
	const searchHeaderElement = e.target.closest('.search-result-header'); // Updated class
    if (searchHeaderElement) {
      const groupElement = searchHeaderElement.closest('.search-result-box'); // Updated class
      const isCollapsed = groupElement.classList.toggle('is-collapsed');
      searchHeaderElement.setAttribute('aria-expanded', !isCollapsed);
      return;
    }
	
    const headerElement = e.target.closest('.node-header');
    if (headerElement) { 
      const cardElement = headerElement.closest('.node-card');
      if (cardElement) this.toggleExpander(cardElement.dataset.id);
      return;
    }

    const logicHeaderElement = e.target.closest('.logic-header');
    if (logicHeaderElement) {
      const sectionElement = logicHeaderElement.closest('.logic-section');
      const isCollapsed = sectionElement.classList.toggle('is-collapsed');
      logicHeaderElement.setAttribute('aria-expanded', !isCollapsed);
      return;
    }

    const miniTriggerElement = e.target.closest('.mini-trigger');
    if (miniTriggerElement) {
      const nodeElement = miniTriggerElement.closest('.mini-node');
      const isOpen = nodeElement.classList.toggle('is-open');
      miniTriggerElement.setAttribute('aria-expanded', isOpen);
    }
  },

  toggleExpander(id) {
    const row = document.querySelector(`.node-row[data-id="${id}"]`);
    if (!row) return;

    const expander = document.getElementById(`exp-${id}`);
    const headerBtn = row.querySelector('.node-header');
    const inlineBtn = row.querySelector('.trigger-inline');

    if (AppState.activeNodeId === id) {
      this.closeExpander(row, expander, headerBtn, inlineBtn);
    } else {
      if (AppState.activeNodeId !== null) this.toggleExpander(AppState.activeNodeId);
      this.openExpander(id, row, expander, headerBtn, inlineBtn);
    }
  },

  closeExpander(row, expander, headerBtn, inlineBtn) {
    expander.classList.remove('is-open');
    headerBtn.setAttribute('aria-expanded', 'false');
    if(inlineBtn) inlineBtn.textContent = "Expand";
    
    row.classList.remove('is-active');
    document.body.classList.remove('is-focused');
    AppState.activeNodeId = null;
	
	document.body.style.setProperty('--bg-tint-right', 'transparent');

    setTimeout(() => {
      if (!expander.classList.contains('is-open')) expander.innerHTML = '';
    }, ANIMATION_SPEEDS.CSS_TRANSITION_MS);
  },

  openExpander(id, row, expander, headerBtn, inlineBtn) {
    const nodeData = DataStore.nodes.find(n => n.id === id);
    if (!nodeData) return;

    expander.innerHTML = Templates.expander(nodeData);
    this.bindTabEvents(expander, nodeData);
    this.bindActionEvents(expander);
    
    requestAnimationFrame(() => {
      expander.classList.add('is-open');
      headerBtn.setAttribute('aria-expanded', 'true');
      if(inlineBtn) inlineBtn.textContent = "Hide";
      
      row.classList.add('is-active');
      document.body.classList.add('is-focused');
      AppState.activeNodeId = id;
	  
      document.body.style.setProperty('--bg-tint-right', `hsla(${nodeData.hue}, 80%, 50%, 0.35)`);
	  
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
        const headerHeight = this.els.pageHeader ? this.els.pageHeader.offsetHeight : 0;
        const padding = 24; 
        window.scrollTo({ top: window.scrollY + rect.top - headerHeight - padding, behavior: 'smooth' });
      }
    }, ANIMATION_SPEEDS.SCROLL_DELAY_MS);
  }
};

/**
 * ==========================================
 * DATA LOADER & BOOTSTRAP
 * ==========================================
 */
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const mapName = urlParams.get('map') || 'data'; 
    
    const response = await fetch(`${mapName}.json`);
    if (!response.ok) throw new Error(`Could not find a file named ${mapName}.json`);

    const pageData = await response.json();

    const parentGroups = new Map();
    pageData.nodes.forEach(node => {
      const pId = node.parentId;
      if (!parentGroups.has(pId)) parentGroups.set(pId, []);
      parentGroups.get(pId).push(node);
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

    DataStore.config = pageData.config;
    DataStore.nodes = pageData.nodes;
    
    AppUI.init();
    NavigationController.init(); 

  } catch (error) {
    console.error("Failed to load page data:", error);
    document.getElementById('titleText').textContent = "Error Loading Data";
    document.getElementById('subtitleText').textContent = error.message;
  }
});