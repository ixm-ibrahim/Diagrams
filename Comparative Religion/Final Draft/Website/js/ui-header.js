/**
 * =============================================================================
 * ui-header.js — Header Context & Breadcrumbs
 * =============================================================================
 * Manages the page header: title, subtitle, browser tab title, breadcrumb
 * trail, search placeholder, and collapsible page introduction.
 *
 * Dependencies: data-store.js (DataStore), state.js (AppState)
 * Consumers: navigation.js (calls updateHeaderContext on every loadState)
 * =============================================================================
 */

import { TINT_SATURATION, TINT_LIGHTNESS, TINT_ALPHA } from './constants.js';
import { DataStore } from './data-store.js';
import { AppState, HOME_PAGE_ID } from './state.js';
import { md } from './templates.js';

/** Cached header DOM elements. Populated once by init(). */
const els = {};

/**
 * Caches header DOM references. Call once during bootstrap.
 */
export function init() {
  els.docTitle         = document.getElementById('docTitle');
  els.pageTitle        = document.getElementById('titleText');
  els.pageSubtitle     = document.getElementById('subtitleText');
  els.breadcrumbRoot   = document.getElementById('breadcrumbRoot');
  els.breadcrumbSep    = els.breadcrumbRoot?.nextElementSibling; // static › separator
  els.breadcrumbCurrent = document.getElementById('breadcrumbCurrent');
  els.searchInput      = document.getElementById('searchInput');
  els.introToggle      = document.getElementById('introToggle');
  els.pageIntroWrap    = document.getElementById('pageIntroWrap');
  els.pageIntroText    = document.getElementById('pageIntroText');
  els.mapToggle        = document.getElementById('mapToggle');
  els.mapCollapseWrap  = document.getElementById('mapCollapseWrap');

  // Intro toggle: expand/collapse page introduction + collapse/expand nodes
  if (els.introToggle) {
    els.introToggle.addEventListener('click', () => {
      const isOpen = els.introToggle.getAttribute('aria-expanded') === 'true';
      toggleIntro(!isOpen);
    });
  }

  // Map toggle: independently expand/collapse the node map
  if (els.mapToggle) {
    els.mapToggle.addEventListener('click', () => {
      const isOpen = els.mapToggle.getAttribute('aria-expanded') === 'true';
      toggleMap(!isOpen);
    });
  }

  // Delegate click/keyboard on collapsible intro sections
  if (els.pageIntroText) {
    els.pageIntroText.addEventListener('click', handleIntroSectionToggle);
    els.pageIntroText.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleIntroSectionToggle(e);
      }
    });
  }
}

/** Toggle a collapsible intro section when its header is clicked. */
function handleIntroSectionToggle(e) {
  const header = e.target.closest('.intro-section__header');
  if (!header) return;
  const section = header.parentElement;
  const collapsed = section.classList.toggle('is-collapsed');
  header.setAttribute('aria-expanded', String(!collapsed));
}

/**
 * Expand or collapse the page introduction panel.
 * When intro opens, the map collapses (and vice versa).
 */
function toggleIntro(open) {
  if (!els.introToggle || !els.pageIntroWrap) return;

  els.introToggle.setAttribute('aria-expanded', String(open));
  els.pageIntroWrap.classList.toggle('is-open', open);

  // Simultaneous: collapse map when intro opens, expand when intro closes
  if (open) {
    toggleMap(false);
  } else {
    toggleMap(true);
  }
}

/**
 * Expand or collapse the node map independently.
 */
function toggleMap(open) {
  if (!els.mapToggle || !els.mapCollapseWrap) return;

  els.mapToggle.setAttribute('aria-expanded', String(open));
  els.mapCollapseWrap.classList.toggle('is-map-collapsed', !open);
  els.mapToggle.classList.toggle('is-collapsed', !open);
}

/**
 * Renders the page intro text. Converts \n into block elements:
 *   ###  heading        → <h4>
 *   ##   heading        → <h3>  (non-collapsible)
 *   ##>  heading        → collapsible section, collapsed by default
 *   ##>! heading        → collapsible section, expanded by default
 *   everything else     → <p>
 * Applies inline markdown to each element's content.
 *
 * Collapsible sections span from one ##> header to the next ##> header
 * (or end of text). Uses grid-template-rows animation like logic-sections.
 */
export function renderIntro(text) {
  if (!text) return '';

  const lines = text.split('\n');
  const blocks = [];          // array of { type, content } or { type:'section', ... }
  let currentSection = null;  // accumulates lines for a collapsible section

  for (const line of lines) {
    if (!line.trim()) continue;

    // Collapsible section header: ##> Title  or  ##>! Title
    const collapseMatch = line.match(/^##>\s*(!?)\s*(.+)/);
    if (collapseMatch) {
      // Close previous section if any
      if (currentSection) {
        blocks.push(currentSection);
      }
      currentSection = {
        type: 'section',
        title: collapseMatch[2],
        expanded: collapseMatch[1] === '!',
        lines: []
      };
      continue;
    }

    // If inside a collapsible section, accumulate lines
    if (currentSection) {
      currentSection.lines.push(line);
      continue;
    }

    // Regular block-level elements
    const h3 = line.match(/^###\s+(.+)/);
    if (h3) { blocks.push({ type: 'h4', content: h3[1] }); continue; }
    const h2 = line.match(/^##\s+(.+)/);
    if (h2) { blocks.push({ type: 'h3', content: h2[1] }); continue; }
    blocks.push({ type: 'p', content: line });
  }

  // Close trailing section
  if (currentSection) blocks.push(currentSection);

  // Render
  return blocks.map(block => {
    if (block.type === 'section') {
      const bodyHtml = renderLines(block.lines);
      const collapsed = block.expanded ? '' : ' is-collapsed';
      const ariaExp = block.expanded ? 'true' : 'false';
      return `<div class="intro-section${collapsed}">` +
        `<div class="intro-section__header" role="button" tabindex="0" aria-expanded="${ariaExp}">${md(block.title)}</div>` +
        `<div class="intro-section__body"><div class="intro-section__inner">${bodyHtml}</div></div>` +
        `</div>`;
    }
    if (block.type === 'h3') return `<h3 class="intro-heading">${md(block.content)}</h3>`;
    if (block.type === 'h4') return `<h4 class="intro-heading">${md(block.content)}</h4>`;
    return `<p>${md(block.content)}</p>`;
  }).join('');
}

/**
 * Render an array of body lines inside a collapsible section.
 * Supports:
 *   ###>  Title   → nested collapsible, collapsed by default
 *   ###>! Title   → nested collapsible, expanded by default
 *   ###   Title   → plain <h4>
 *   ##    Title   → plain <h3>
 *   - bullet      → grouped into <ul>
 *   other         → <p>
 */
function renderLines(lines) {
  const parts = [];
  let bulletBuffer = [];
  let subSection = null; // accumulates lines for a nested collapsible

  const flushBullets = () => {
    if (bulletBuffer.length) {
      parts.push(md(bulletBuffer.join('\n')));
      bulletBuffer = [];
    }
  };

  const flushSub = () => {
    if (subSection) {
      flushBullets();
      const bodyHtml = renderLeafLines(subSection.lines);
      const collapsed = subSection.expanded ? '' : ' is-collapsed';
      const ariaExp = subSection.expanded ? 'true' : 'false';
      parts.push(
        `<div class="intro-section intro-section--nested${collapsed}">` +
        `<div class="intro-section__header" role="button" tabindex="0" aria-expanded="${ariaExp}">${md(subSection.title)}</div>` +
        `<div class="intro-section__body"><div class="intro-section__inner">${bodyHtml}</div></div>` +
        `</div>`
      );
      subSection = null;
    }
  };

  for (const line of lines) {
    // Nested collapsible: ###> Title  or  ###>! Title
    const subMatch = line.match(/^###>\s*(!?)\s*(.+)/);
    if (subMatch) {
      flushSub();
      flushBullets();
      subSection = {
        title: subMatch[2],
        expanded: subMatch[1] === '!',
        lines: []
      };
      continue;
    }

    // If inside a nested section, accumulate
    if (subSection) {
      subSection.lines.push(line);
      continue;
    }

    if (/^\s*- /.test(line)) {
      bulletBuffer.push(line);
      continue;
    }
    flushBullets();
    const h3 = line.match(/^###\s+(.+)/);
    if (h3) { parts.push(`<h4 class="intro-heading">${md(h3[1])}</h4>`); continue; }
    const h2 = line.match(/^##\s+(.+)/);
    if (h2) { parts.push(`<h3 class="intro-heading">${md(h2[1])}</h3>`); continue; }
    parts.push(`<p>${md(line)}</p>`);
  }
  flushSub();
  flushBullets();
  return parts.join('');
}

/**
 * Render leaf-level lines (inside a nested ###> section).
 * No further nesting — just headings, bullets, and paragraphs.
 */
function renderLeafLines(lines) {
  const html = [];
  let bulletBuffer = [];

  const flushBullets = () => {
    if (bulletBuffer.length) {
      html.push(md(bulletBuffer.join('\n')));
      bulletBuffer = [];
    }
  };

  for (const line of lines) {
    if (/^\s*- /.test(line)) { bulletBuffer.push(line); continue; }
    flushBullets();
    const h3 = line.match(/^###\s+(.+)/);
    if (h3) { html.push(`<h4 class="intro-heading">${md(h3[1])}</h4>`); continue; }
    const h2 = line.match(/^##\s+(.+)/);
    if (h2) { html.push(`<h3 class="intro-heading">${md(h2[1])}</h3>`); continue; }
    html.push(`<p>${md(line)}</p>`);
  }
  flushBullets();
  return html.join('');
}

/**
 * Updates header text, breadcrumbs, and tints to reflect the current page.
 * Called after every navigation state change.
 */
export function updateHeaderContext() {
  // Reset expander tint; page tint set below based on context
  AppState.updateTints({ expander: 'transparent' });

  // Reset intro state on every navigation
  if (els.introToggle) {
    els.introToggle.setAttribute('aria-expanded', 'false');
    els.introToggle.hidden = true;
  }
  if (els.pageIntroWrap) {
    els.pageIntroWrap.classList.remove('is-open');
  }
  if (els.pageIntroText) {
    els.pageIntroText.innerHTML = '';
  }
  // Reset map to visible
  if (els.mapToggle) {
    els.mapToggle.setAttribute('aria-expanded', 'true');
    els.mapToggle.hidden = true;
    els.mapToggle.classList.remove('is-collapsed');
  }
  if (els.mapCollapseWrap) {
    els.mapCollapseWrap.classList.remove('is-map-collapsed');
  }

  const isHome = AppState.currentParentId === HOME_PAGE_ID;

  // Show/hide the static breadcrumb separator + current label
  // (hidden on home page since "Home" alone is sufficient)
  if (els.breadcrumbSep) els.breadcrumbSep.style.display = isHome ? 'none' : '';
  if (els.breadcrumbCurrent) els.breadcrumbCurrent.style.display = isHome ? 'none' : '';

  if (isHome) {
    // Home landing page
    AppState.updateTints({ page: 'transparent' });

    const homeTitle = DataStore.config.homeTitle || DataStore.config.breadcrumbRoot || 'Home';
    const homeSubtitle = DataStore.config.homeSubtitle || '';
    if (els.docTitle)
      els.docTitle.textContent = homeTitle;
    if (els.pageTitle)
      els.pageTitle.innerHTML = md(homeTitle);
    if (els.pageSubtitle)
      els.pageSubtitle.innerHTML = md(homeSubtitle);
    if (els.breadcrumbRoot)
      els.breadcrumbRoot.innerHTML =
        `<a href="#" class="crumb-link" data-target="${HOME_PAGE_ID}">${DataStore.config.breadcrumbRoot}</a>`;

  } else if (!AppState.currentParentId) {
    // Root level (Project Overview) — check config for pageIntro
    AppState.updateTints({ page: 'transparent' });

    if (els.docTitle)
      els.docTitle.textContent = `${DataStore.config.title} - Map`;
    if (els.pageTitle)
      els.pageTitle.innerHTML = md(DataStore.config.title);
    if (els.pageSubtitle)
      els.pageSubtitle.innerHTML = md(DataStore.config.subtitle);
    if (els.breadcrumbRoot)
      els.breadcrumbRoot.innerHTML = DataStore.config.homePage
        ? `<a href="#" class="crumb-link" data-target="${HOME_PAGE_ID}">${DataStore.config.breadcrumbRoot}</a>`
        : `<a href="#" class="crumb-link" data-target="null">${DataStore.config.breadcrumbRoot}</a>`;
    if (els.breadcrumbCurrent)
      els.breadcrumbCurrent.textContent = DataStore.config.title;

    // Root-level pageIntro from config (optional)
    const rootIntro = DataStore.config.pageIntro;
    if (rootIntro) {
      setIntroVisible(rootIntro);
    }
  } else {
    // Sub-page: show parent node's context
    const parentNode = DataStore.map.get(AppState.currentParentId);
    if (!parentNode) return;

    AppState.updateTints({
      page: `hsla(${parentNode.hue}, ${TINT_SATURATION}%, ${TINT_LIGHTNESS}%, ${TINT_ALPHA})`
    });

    const prefix = DataStore.config.nodePrefix;
    if (els.docTitle)
      els.docTitle.textContent = `${prefix}${parentNode.id} - Map`;
    if (els.pageTitle)
      els.pageTitle.innerHTML = `${prefix}${parentNode.id}. ${md(parentNode.claim)}`;
    if (els.pageSubtitle)
      els.pageSubtitle.innerHTML = md(parentNode.soWhat);

    // Page intro from node data
    if (parentNode.pageIntro) {
      setIntroVisible(parentNode.pageIntro);
    }

    renderBreadcrumbs(parentNode.id);
  }

  if (els.searchInput)
    els.searchInput.placeholder = DataStore.config.searchPlaceholder;
}

/**
 * Show the intro toggle and map toggle, and populate intro content.
 */
function setIntroVisible(introText) {
  if (els.pageIntroText) {
    els.pageIntroText.innerHTML = renderIntro(introText);
  }
  if (els.introToggle) {
    els.introToggle.hidden = false;
  }
  if (els.mapToggle) {
    els.mapToggle.hidden = false;
  }
}

/**
 * Builds the breadcrumb trail by walking up the parentId chain.
 * @param {string} activeNodeId — the current page's parent node ID
 */
function renderBreadcrumbs(activeNodeId) {
  if (!els.breadcrumbRoot || !els.breadcrumbCurrent) return;

  // Walk up the tree to build lineage
  const lineage = [];
  let current = DataStore.map.get(activeNodeId);
  while (current) {
    lineage.unshift(current);
    current = DataStore.map.get(current.parentId);
  }

  const prefix = DataStore.config.nodePrefix;

  // Build crumbs as an array of { label, target } so we can link separators
  const homeTarget = DataStore.config.homePage ? HOME_PAGE_ID : 'null';
  const crumbs = [
    { label: DataStore.config.breadcrumbRoot, target: homeTarget },
    { label: DataStore.config.title, target: 'null' }
  ];
  for (let i = 0; i < lineage.length - 1; i++) {
    const node = lineage[i];
    crumbs.push({ label: `${prefix}${node.id}`, target: node.id });
  }

  // Render: each separator links to the NEXT crumb's target
  let html = '';
  crumbs.forEach((crumb, i) => {
    if (i > 0) {
      html += ` <a href="#" class="crumb-link sep" data-target="${crumbs[i].target}" aria-label="Navigate to ${crumbs[i].label}">›</a> `;
    }
    html += `<a href="#" class="crumb-link" data-target="${crumb.target}">${crumb.label}</a>`;
  });

  els.breadcrumbRoot.innerHTML = html;
  els.breadcrumbCurrent.textContent =
    `${prefix}${lineage[lineage.length - 1].id}`;
}
