/* === ui-agreement.js — Vote Storage, Propagation & DOM Sync ===
 *
 * Stores explicit user votes (agree / disagree) per node in localStorage,
 * computes glow propagation across the entire node graph, and applies
 * visual states (button selection, glow classes) to the DOM.
 *
 * Storage key: 'agreement-votes'
 * Storage format: JSON object mapping node IDs to 'agree' | 'disagree'
 *   e.g. { "2.3": "disagree", "2.5": "agree" }
 *
 * Propagation algorithm overview:
 *   1. Within-page forward pass: disagrees → red, red forward-propagates via
 *      nextIds. Merge nodes are red if ANY prevId is red.
 *   2. Within-page backward pass: agrees carve green zones backward via prevIds,
 *      stopping at explicit disagrees. Siblings are not touched.
 *   3. Upward: if ANY node on a derivation page is red, the parent claim
 *      becomes red on its own page.
 *   4. Fixed-point iteration: phases 1–3 repeat until stable.
 *   5. Downward fill: non-authoritative pages inherit from parent node's state.
 *   6. Auto-cleanup: disagreeing clears downstream agrees on same page.
 *
 * Dependencies: data-store.js (DataStore — for node graph),
 *              ui-agreement-panel.js (initSummaryPanel)
 * Consumers: ui-events.js (setVote), ui-render.js (applyVoteStates),
 *           main.js (init)
 * ================================================================== */

import { DataStore } from './data-store.js';
import { initSummaryPanel, renderSummaryPanel as renderPanel } from './ui-agreement-panel.js';

const STORAGE_KEY = 'agreement-votes';

/** @type {Object<string, 'agree'|'disagree'>} */
let votes = {};

/** @type {Object<string, 'red'|'green'>} Computed propagation states. */
let propagated = {};

/* ---------------------------------------------------------------------------
 * Initialisation
 * --------------------------------------------------------------------------- */

/** Load persisted votes from localStorage, then compute propagation. */
export function init() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        votes = JSON.parse(raw);
      } catch {
        // Corrupted JSON — clear the bad data and start fresh so the app
        // doesn't crash on every load. Matches test case: manually corrupt
        // the key → app starts clean instead of erroring.
        console.warn(
          '[Agreement] Corrupted vote data in localStorage — clearing and starting fresh.'
        );
        try { localStorage.removeItem(STORAGE_KEY); } catch { /* storage unavailable */ }
        votes = {};
      }
    }
  } catch {
    // localStorage is disabled entirely (e.g. private browsing with strict
    // settings, or a browser that blocks storage access). Votes work for the
    // current session but won't persist across refreshes.
    console.warn(
      '[Agreement] localStorage unavailable — votes will not persist across sessions.'
    );
    votes = {};
  }
  initSummaryPanel({ resetAll, applyVoteStates });
  recompute();
}

/* ---------------------------------------------------------------------------
 * Read / write
 * --------------------------------------------------------------------------- */

function save() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(votes));
  } catch (err) {
    // QuotaExceededError, SecurityError (storage disabled), or similar.
    // Votes continue working for this session — they just won't survive a refresh.
    console.warn('[Agreement] Could not save votes to localStorage:', err.name);
  }
}

/**
 * Record or remove an explicit vote, then recompute propagation.
 * @param {string} nodeId
 * @param {'agree'|'disagree'|null} vote — null removes
 */
export function setVote(nodeId, vote) {
  if (vote === null || vote === undefined) {
    delete votes[nodeId];
  } else {
    votes[nodeId] = vote;
  }

  // When disagreeing, "everything after it is red" — clear any explicit
  // agrees on downstream nodes (same page) since they'd be overridden.
  if (vote === 'disagree') {
    clearDownstreamAgrees(nodeId);
  }

  save();
  recompute();
}

/**
 * Remove explicit agrees from all descendants of `nodeId` on the same page.
 * Called when a disagree is placed, since the disagree's forward red
 * invalidates any downstream agrees.
 */
function clearDownstreamAgrees(nodeId) {
  const node = DataStore.map.get(nodeId);
  if (!node) return;

  const pageNodeIds = new Set(
    DataStore.nodes.filter(n => (n.parentId ?? null) === (node.parentId ?? null))
      .map(n => n.id)
  );

  // BFS forward via nextIds on the same page
  const queue = (node.nextIds || []).filter(nid => pageNodeIds.has(nid));
  const visited = new Set();
  while (queue.length > 0) {
    const id = queue.shift();
    if (visited.has(id)) continue;
    visited.add(id);

    if (votes[id] === 'agree') delete votes[id];

    const n = DataStore.map.get(id);
    if (n) {
      for (const nid of (n.nextIds || [])) {
        if (pageNodeIds.has(nid) && !visited.has(nid)) queue.push(nid);
      }
    }
  }
}

/** @returns {'agree'|'disagree'|null} */
export function getVote(nodeId) {
  return votes[nodeId] ?? null;
}

/** @returns {Object<string, 'agree'|'disagree'>} snapshot */
export function getAllVotes() {
  return { ...votes };
}

export function voteCount() {
  return Object.keys(votes).length;
}

/** @returns {'red'|'green'|null} computed propagation state */
export function getNodeState(nodeId) {
  return propagated[nodeId] ?? null;
}

/** @returns {Object<string, 'red'|'green'>} full computed states */
export function getAllStates() {
  return { ...propagated };
}

export function resetAll() {
  votes = {};
  propagated = {};
  save();
  renderPanel(votes);
}

/* ===========================================================================
 * PROPAGATION ALGORITHM
 * =========================================================================== */

/** Rebuild `propagated` from scratch based on current `votes` + DataStore. */
function recompute() {
  propagated = {};

  // No disagrees → no propagation needed (agrees only take effect
  // relative to a disagree; explicit agree buttons are shown via applyVoteStates)
  const hasDisagree = Object.values(votes).some(v => v === 'disagree');
  if (!hasDisagree) {
    renderPanel(votes);
    return;
  }

  // --- Build lookup structures ---
  const nodeMap = DataStore.map;                       // Map<id, node>
  const pageMap = buildPageMap(DataStore.nodes);        // Map<parentId|null, node[]>

  // Sort page IDs deepest-first for bottom-up processing
  const allPageIds = [...pageMap.keys()];
  allPageIds.sort((a, b) => depth(b) - depth(a));

  // Identify authoritative pages (pages that contain explicit votes)
  const authoritativePages = new Set();
  for (const id of Object.keys(votes)) {
    const node = nodeMap.get(id);
    if (node) authoritativePages.add(node.parentId ?? null);
  }

  // --- Fixed-point loop: within-page + upward propagation ---
  // Track nodes forced red by upward propagation (child page has reds).
  // These must survive the forward pass re-computation on their own page.
  const upwardReds = new Set();

  const MAX_ITER = 50;
  let convergedAt = -1;   // -1 means we hit the cap without stabilising

  for (let iter = 0; iter < MAX_ITER; iter++) {
    let changed = false;

    for (const pageParentId of allPageIds) {
      const pageNodes = pageMap.get(pageParentId);

      // Determine if this page should be processed this round
      const isAuthoritative = authoritativePages.has(pageParentId);
      const hasExternalStates = pageNodes.some(n => propagated[n.id] != null);
      if (!isAuthoritative && !hasExternalStates) continue;

      // Within-page propagation (passes parent node's state for inheritance)
      const parentState = pageParentId != null
        ? (propagated[pageParentId] || null)
        : null;
      if (propagatePage(pageNodes, isAuthoritative, parentState, upwardReds)) changed = true;

      // Upward: if any node on page is red → parent claim = red
      if (pageParentId != null) {
        const parentNode = nodeMap.get(pageParentId);
        if (parentNode) {
          const anyRed = pageNodes.some(n => propagated[n.id] === 'red');
          if (anyRed && votes[pageParentId] !== 'agree' &&
              propagated[pageParentId] !== 'red') {
            propagated[pageParentId] = 'red';
            upwardReds.add(pageParentId);
            changed = true;
          }
        }
      }
    }

    if (!changed) {
      convergedAt = iter + 1;
      break;
    }
  }

  if (convergedAt === -1) {
    console.warn(
      `[Agreement] Propagation hit the ${MAX_ITER}-iteration cap — ` +
      'result may be incomplete.'
    );
  } else {
    console.debug(
      `[Agreement] Propagation converged in ${convergedAt} ` +
      `${convergedAt === 1 ? 'iteration' : 'iterations'}.`
    );
  }

  // Update summary panel after computation
  renderPanel(votes);

  // --- Downward propagation: top-down fill for non-authoritative pages ---
  allPageIds.sort((a, b) => depth(a) - depth(b));  // shallowest first

  for (const pageParentId of allPageIds) {
    const pageNodes = pageMap.get(pageParentId);
    for (const node of pageNodes) {
      if (propagated[node.id] == null) continue;       // no state to cascade
      if (node.hasDerivation === false) continue;       // terminal node
      const derivPage = pageMap.get(node.id);
      if (!derivPage) continue;

      // Skip authoritative pages — they computed their own states
      if (authoritativePages.has(node.id)) continue;

      // All children inherit this node's state (overrides previous inheritance)
      const inherited = propagated[node.id];
      for (const child of derivPage) {
        propagated[child.id] = inherited;
      }
    }
  }
}

/* ---------------------------------------------------------------------------
 * Within-page propagation
 *
 * Processes one page's nodes in topological order. Returns true if any
 * node state changed (so the outer loop knows to keep iterating).
 * --------------------------------------------------------------------------- */

/**
 * Compute states for one page's nodes. Two passes:
 *   1. Forward (topo order): disagrees → red, prevs determine rest
 *   2. Backward from agrees: the agree node + its ancestors turn green
 *      (stops at explicit disagrees). Siblings are NOT touched.
 *
 * @param {Array}   pageNodes
 * @param {boolean} isAuthoritative — page has its own explicit votes
 * @param {string|null} parentState — propagated state of the parent node ('red'|'green'|null)
 * @param {Set<string>} upwardReds — nodes forced red by upward propagation
 * @returns {boolean} changed
 */
function propagatePage(pageNodes, isAuthoritative, parentState, upwardReds) {
  const pageNodeIds = new Set(pageNodes.map(n => n.id));
  const sorted = topoSort(pageNodes, pageNodeIds);
  const nodeById = new Map(pageNodes.map(n => [n.id, n]));
  const hasDisagreeOnPage = pageNodes.some(n => votes[n.id] === 'disagree');

  // Snapshot old states to detect changes at the end
  const oldStates = {};
  for (const n of pageNodes) oldStates[n.id] = propagated[n.id];

  // --- Helper: compute a single node from its prevs + explicit vote ---
  function computeNode(node) {
    if (votes[node.id] === 'disagree') return 'red';
    // Upward reds (node forced red because its child derivation page has
    // reds) must survive regardless of whether the node has predecessors
    // on this page. Without this check, first-nodes that were forced red
    // by upward propagation would be overwritten to 'green' below.
    if (upwardReds.has(node.id)) return 'red';
    // Agrees are handled in Pass 2 (backward BFS), not here.
    // Red must flow past agree nodes in Pass 1 so the backward pass
    // can carve out the correct green zone between disagree and agree.

    const prevsOnPage = (node.prevIds || []).filter(pid => pageNodeIds.has(pid));
    if (prevsOnPage.length > 0) {
      const anyPrevRed = prevsOnPage.some(pid => propagated[pid] === 'red');
      return anyPrevRed ? 'red' : 'green';
    }
    // First node (no predecessors on page)
    if (isAuthoritative && hasDisagreeOnPage) return 'green';
    return parentState || 'green';
  }

  // --- Pass 1: Forward propagation (topo order) ---
  for (const node of sorted) propagated[node.id] = computeNode(node);

  // --- Pass 2: Backward BFS from each explicit agree ---
  for (const node of pageNodes) {
    if (votes[node.id] !== 'agree') continue;
    propagated[node.id] = 'green';

    const queue = (node.prevIds || []).filter(pid => pageNodeIds.has(pid));
    const visited = new Set();
    while (queue.length > 0) {
      const id = queue.shift();
      if (visited.has(id)) continue;
      visited.add(id);
      if (votes[id] === 'disagree') continue;
      propagated[id] = 'green';
      const prev = nodeById.get(id);
      if (prev) {
        for (const pid of (prev.prevIds || [])) {
          if (pageNodeIds.has(pid) && !visited.has(pid)) queue.push(pid);
        }
      }
    }
  }

  // Detect whether anything changed
  let changed = false;
  for (const n of pageNodes) {
    if (propagated[n.id] !== oldStates[n.id]) { changed = true; break; }
  }
  return changed;
}

/* ---------------------------------------------------------------------------
 * Topological sort (Kahn's algorithm, scoped to one page)
 * --------------------------------------------------------------------------- */

function topoSort(pageNodes, pageNodeIds) {
  const inDeg = new Map();
  const adj   = new Map();
  const byId  = new Map();

  for (const n of pageNodes) {
    inDeg.set(n.id, 0);
    adj.set(n.id, []);
    byId.set(n.id, n);
  }

  for (const n of pageNodes) {
    for (const nxt of (n.nextIds || [])) {
      if (pageNodeIds.has(nxt)) {
        adj.get(n.id).push(nxt);
        inDeg.set(nxt, (inDeg.get(nxt) || 0) + 1);
      }
    }
  }

  const queue = [];
  for (const n of pageNodes) {
    if (inDeg.get(n.id) === 0) queue.push(n);
  }

  const sorted = [];
  while (queue.length > 0) {
    const node = queue.shift();
    sorted.push(node);
    for (const nxtId of adj.get(node.id)) {
      const d = inDeg.get(nxtId) - 1;
      inDeg.set(nxtId, d);
      if (d === 0) queue.push(byId.get(nxtId));
    }
  }

  return sorted;
}

/* ---------------------------------------------------------------------------
 * Helpers
 * --------------------------------------------------------------------------- */

/** Group nodes by parentId → node[]. */
function buildPageMap(nodes) {
  const map = new Map();
  for (const n of nodes) {
    const pid = n.parentId ?? null;
    if (!map.has(pid)) map.set(pid, []);
    map.get(pid).push(n);
  }
  return map;
}

/** Depth of a node ID: null → 0, "1" → 1, "1.2" → 2, "1.2.3" → 3. */
function depth(id) {
  if (id == null) return 0;
  return id.split('.').length;
}

/* ---------------------------------------------------------------------------
 * DOM synchronisation
 * --------------------------------------------------------------------------- */

/**
 * Walk every vote button in `root` and set its aria-pressed + is-auto state
 * to match: (1) the explicit vote if one exists, or (2) the propagated state.
 *
 * Always pass an explicit root (e.g. the map container or a freshly built
 * newView) so the queries are scoped to the visible content rather than the
 * entire document. The default falls back to #mapContainer for safety.
 *
 * @param {HTMLElement} [root]
 */
export function applyVoteStates(root) {
  if (!root) root = document.getElementById('mapContainer') ?? document;
  // --- Update vote buttons ---
  root.querySelectorAll('[data-node-id][data-vote]').forEach(btn => {
    const nodeId   = btn.dataset.nodeId;
    const btnVote  = btn.dataset.vote;   // 'agree' | 'disagree'
    const explicit = votes[nodeId] ?? null;
    const computed = propagated[nodeId] ?? null;

    if (explicit === btnVote) {
      btn.setAttribute('aria-pressed', 'true');
      btn.classList.remove('is-auto');
    } else if (
      explicit == null && computed != null &&
      ((computed === 'red'   && btnVote === 'disagree') ||
       (computed === 'green' && btnVote === 'agree'))
    ) {
      btn.setAttribute('aria-pressed', 'true');
      btn.classList.add('is-auto');
    } else {
      btn.setAttribute('aria-pressed', 'false');
      btn.classList.remove('is-auto');
    }
  });

  // --- Update node card glows ---
  root.querySelectorAll('.node-card[data-id]').forEach(card => {
    const nodeId   = card.dataset.id;
    const explicit = votes[nodeId] ?? null;
    const computed = propagated[nodeId] ?? null;

    // Effective state: explicit agree overrides propagated red for display
    const effective = explicit === 'agree' ? 'green'
                    : explicit === 'disagree' ? 'red'
                    : computed;

    card.classList.toggle('glow-red',        effective === 'red');
    card.classList.toggle('glow-green',      effective === 'green');
    card.classList.toggle('glow-core',       explicit === 'disagree');
    card.classList.toggle('glow-core-agree', explicit === 'agree');

    // Also mark the parent .node-row so we can target the sibling
    // derive button and the adjacent level-expander's tint overlay.
    const row = card.closest('.node-row');
    if (row) {
      row.classList.toggle('row-core',       explicit === 'disagree');
      row.classList.toggle('row-core-agree', explicit === 'agree');
      row.classList.toggle('row-red',        effective === 'red');
      row.classList.toggle('row-green',      effective === 'green');
    }
  });

}

