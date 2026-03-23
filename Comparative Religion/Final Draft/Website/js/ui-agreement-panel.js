/* === ui-agreement-panel.js — Vote Summary Panel ===
 *
 * Renders and manages the vote summary panel UI. Receives votes data and
 * callback functions as parameters to avoid circular dependencies with
 * ui-agreement.js.
 *
 * Dependencies: data-store.js (DataStore — for node graph)
 * Consumers: ui-agreement.js (initSummaryPanel)
 * ============================================================ */

import { SNIPPET_MAX_LENGTH, SNIPPET_TRUNCATE_AT } from './constants.js';
import { DataStore } from './data-store.js';
import { md } from './templates.js';

/** Cached summary panel DOM refs. Populated by initSummaryPanel(). */
const sp = {};

/** Store callback references passed from ui-agreement.js */
let callbacks = {};

/**
 * Bind toggle, reset, and confirm events. Called once from init().
 * @param {Object} cbs — { resetAll, applyVoteStates }
 */
export function initSummaryPanel(cbs) {
  callbacks = cbs;

  sp.panel      = document.getElementById('voteSummary');
  sp.toggle     = document.getElementById('voteSummaryToggle');
  sp.count      = document.getElementById('voteSummaryCount');
  sp.body       = document.getElementById('voteSummaryBody');
  sp.list       = document.getElementById('voteSummaryList');
  sp.reset      = document.getElementById('voteSummaryReset');
  sp.confirm    = document.getElementById('voteSummaryConfirm');
  sp.confirmYes = document.getElementById('voteSummaryConfirmYes');
  sp.confirmNo  = document.getElementById('voteSummaryConfirmNo');
  if (!sp.panel) return;

  // Toggle open/closed
  sp.toggle.addEventListener('click', () => {
    const isOpen = sp.panel.getAttribute('aria-expanded') === 'true';
    sp.panel.setAttribute('aria-expanded', !isOpen);
    sp.toggle.setAttribute('aria-expanded', !isOpen);
  });

  // Reset All → show confirmation
  sp.reset.addEventListener('click', () => {
    sp.confirm.hidden = false;
    sp.reset.hidden   = true;
  });

  // Confirm yes → clear everything
  sp.confirmYes.addEventListener('click', () => {
    callbacks.resetAll();
    // Re-apply to current page
    const container = document.getElementById('mapContainer');
    if (container) callbacks.applyVoteStates(container);
  });

  // Confirm no → cancel
  sp.confirmNo.addEventListener('click', () => {
    sp.confirm.hidden = true;
    sp.reset.hidden   = false;
  });

  // Vote list item clicks are handled by the vote-link delegation in ui-events.js

  // Initial render
  renderSummaryPanel({});
}

/** Track whether the panel is currently visible (avoids redundant animations). */
let panelVisible = false;

/**
 * Smoothly expand the panel from zero height.
 * Removes `hidden`, measures natural height, then transitions from 0.
 */
function expandPanel() {
  if (panelVisible) return;
  panelVisible = true;

  const el = sp.panel;
  el.hidden = false;
  // Start collapsed so CSS transition has a from-state
  el.classList.add('is-collapsed');
  // Force layout so the browser registers the collapsed state
  void el.offsetHeight;
  // Measure the natural (auto) height by temporarily removing the collapse
  el.style.height = 'auto';
  const fullHeight = el.scrollHeight;
  // Reset to 0 so the transition runs
  el.style.height = '0';
  void el.offsetHeight;
  // Transition to full height
  el.classList.remove('is-collapsed');
  el.style.height = `${fullHeight}px`;

  // After transition ends, switch to auto height so the panel can resize
  // if the user expands/collapses the body or adds more votes.
  const onEnd = () => {
    el.removeEventListener('transitionend', onEnd);
    if (panelVisible) el.style.height = 'auto';
  };
  el.addEventListener('transitionend', onEnd);
}

/**
 * Smoothly contract the panel to zero height, then hide it.
 */
function contractPanel() {
  if (!panelVisible) return;
  panelVisible = false;

  const el = sp.panel;
  // Lock the current height so the transition has a from-state
  el.style.height = `${el.scrollHeight}px`;
  void el.offsetHeight;
  // Transition to collapsed
  el.classList.add('is-collapsed');
  el.style.height = '0';

  const onEnd = () => {
    el.removeEventListener('transitionend', onEnd);
    if (!panelVisible) el.hidden = true;
  };
  el.addEventListener('transitionend', onEnd);
}

/**
 * Rebuild the summary panel contents from the provided votes.
 * Smoothly expands when votes first appear, contracts when all removed.
 * @param {Object<string, 'agree'|'disagree'>} votes
 */
export function renderSummaryPanel(votes) {
  if (!sp.panel) return;

  const voteEntries = Object.entries(votes);
  const count = voteEntries.length;

  if (count === 0) {
    contractPanel();
    return;
  }

  // Update count badge
  sp.count.textContent = count;

  // Reset confirmation state
  sp.confirm.hidden = true;
  sp.reset.hidden   = false;

  // Sort votes by node ID (numeric segment order, matching the argument structure)
  voteEntries.sort((a, b) => {
    const pa = a[0].split('.').map(Number);
    const pb = b[0].split('.').map(Number);
    for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
      const sa = pa[i] ?? -1;
      const sb = pb[i] ?? -1;
      if (sa !== sb) return sa - sb;
    }
    return 0;
  });

  // Build list HTML
  sp.list.innerHTML = voteEntries.map(([nodeId, vote]) => {
    const node = DataStore.map.get(nodeId);
    const claim = node?.claim ?? '';
    const snippet = claim.length > SNIPPET_MAX_LENGTH ? claim.slice(0, SNIPPET_TRUNCATE_AT) + '...' : claim;
    const iconClass = vote === 'disagree' ? 'is-disagree' : 'is-agree';
    const parentId = node?.parentId ?? 'null';
    return `<li class="vote-summary__item vote-link" data-node-id="${nodeId}"
                data-target="${parentId}" role="button" tabindex="0">
      <span class="vote-summary__item-icon ${iconClass}"></span>
      <span class="vote-summary__item-id">${nodeId}.</span>
      <span class="vote-summary__item-text">${md(snippet)}</span>
    </li>`;
  }).join('');

  // Expand if this is the first vote (panel was hidden)
  expandPanel();
}
