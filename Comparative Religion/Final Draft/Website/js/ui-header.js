/**
 * =============================================================================
 * ui-header.js — Header Context & Breadcrumbs
 * =============================================================================
 * Manages the page header: title, subtitle, browser tab title, breadcrumb
 * trail, and search placeholder. Called on every navigation to update context.
 *
 * Dependencies: data-store.js (DataStore), state.js (AppState)
 * Consumers: navigation.js (calls updateHeaderContext on every loadState)
 * =============================================================================
 */

import { DataStore } from './data-store.js';
import { AppState } from './state.js';

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
  els.breadcrumbCurrent = document.getElementById('breadcrumbCurrent');
  els.searchInput      = document.getElementById('searchInput');
}

/**
 * Updates header text, breadcrumbs, and tints to reflect the current page.
 * Called after every navigation state change.
 */
export function updateHeaderContext() {
  // Reset expander tint; page tint set below based on context
  AppState.updateTints({ expander: 'transparent' });

  if (!AppState.currentParentId) {
    // Root level
    AppState.updateTints({ page: 'transparent' });

    if (els.docTitle)
      els.docTitle.textContent = `${DataStore.config.title} - Map`;
    if (els.pageTitle)
      els.pageTitle.textContent = DataStore.config.title;
    if (els.pageSubtitle)
      els.pageSubtitle.textContent = DataStore.config.subtitle;
    if (els.breadcrumbRoot)
      els.breadcrumbRoot.innerHTML =
        `<a href="#" class="crumb-link" data-target="null">${DataStore.config.breadcrumbRoot}</a>`;
    if (els.breadcrumbCurrent)
      els.breadcrumbCurrent.textContent = DataStore.config.title;
  } else {
    // Sub-page: show parent node's context
    const parentNode = DataStore.map.get(AppState.currentParentId);
    if (!parentNode) return;

    AppState.updateTints({
      page: `hsla(${parentNode.hue}, 80%, 50%, 0.35)`
    });

    const prefix = DataStore.config.nodePrefix;
    if (els.docTitle)
      els.docTitle.textContent = `${prefix}${parentNode.id} - Map`;
    if (els.pageTitle)
      els.pageTitle.textContent = `${prefix}${parentNode.id}. ${parentNode.claim}`;
    if (els.pageSubtitle)
      els.pageSubtitle.textContent = parentNode.soWhat;

    renderBreadcrumbs(parentNode.id);
  }

  if (els.searchInput)
    els.searchInput.placeholder = DataStore.config.searchPlaceholder;
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
  const crumbs = [
    { label: DataStore.config.breadcrumbRoot, target: 'null' },
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
