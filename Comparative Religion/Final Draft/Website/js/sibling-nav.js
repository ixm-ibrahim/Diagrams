/* === sibling-nav.js — Sibling Navigation Logic === */
/**
 * Computes and renders navigation groups (prev/next/parallel/cross-parent)
 * for derivation pages. Terminal pages use previousParentId for depth
 * preservation during lateral traversal.
 *
 * Dependencies: data-store.js, state.js
 * Consumers:    ui-render.js (calls renderSiblingNavigation)
 */

import { DataStore } from './data-store.js';
import { AppState } from './state.js';

/* ---------------------------------------------------------------------------
 * Module-level cache for node lookups
 * --------------------------------------------------------------------------- */

let nodeIdToIndexCache = null;
let parentIdToChildrenCache = null;
let lastNodesLength = 0;

/**
 * Invalidates the caches if DataStore.nodes has changed.
 * Uses array length as a cheap heuristic — if the node count changes,
 * the cache is stale and must be rebuilt.
 */
function invalidateCacheIfNeeded() {
  if (lastNodesLength !== DataStore.nodes.length) {
    nodeIdToIndexCache = null;
    parentIdToChildrenCache = null;
    lastNodesLength = DataStore.nodes.length;
  }
}

/**
 * Builds the node index cache on first use.
 * @returns {Map<string, number>} id → index
 */
function getNodeIndexCache() {
  invalidateCacheIfNeeded();
  if (nodeIdToIndexCache === null) {
    nodeIdToIndexCache = new Map();
    DataStore.nodes.forEach((n, idx) => {
      nodeIdToIndexCache.set(n.id, idx);
    });
  }
  return nodeIdToIndexCache;
}

/**
 * Builds the children cache on first use.
 * @returns {Map<string, Array>} parentId → children
 */
function getChildrenCache() {
  invalidateCacheIfNeeded();
  if (parentIdToChildrenCache === null) {
    parentIdToChildrenCache = new Map();
    DataStore.nodes.forEach(n => {
      if (!parentIdToChildrenCache.has(n.parentId)) {
        parentIdToChildrenCache.set(n.parentId, []);
      }
      parentIdToChildrenCache.get(n.parentId).push(n);
    });
  }
  return parentIdToChildrenCache;
}

function nodeIndex(id) {
  return getNodeIndexCache().get(id) ?? -1;
}

function childrenOf(parentId) {
  return getChildrenCache().get(parentId) ?? [];
}

function getEntryNodes(parentId) {
  const children = childrenOf(parentId);
  const ids = new Set(children.map(n => n.id));
  return children.filter(n => !n.prevIds?.some(pid => ids.has(pid)));
}

function getExitNodes(parentId) {
  const children = childrenOf(parentId);
  const ids = new Set(children.map(n => n.id));
  return children.filter(n => !n.nextIds?.some(nid => ids.has(nid)));
}

/** For terminal pages: resolve a sibling target through its children when
 *  we arrived from a child-level traversal (depth preservation). */
function resolveDepthTarget(siblingId, direction) {
  const prevParent = AppState.previousParentId
    ? DataStore.map.get(AppState.previousParentId)
    : null;
  // Did we arrive from inside this sibling's children?
  const arrivedFromChild = prevParent && prevParent.parentId === siblingId;

  if (arrivedFromChild) {
    // Go back to the specific exit/entry node within that sibling's children
    const children = childrenOf(siblingId);
    if (children.length > 0) {
      if (direction === 'prev') {
        const exits = getExitNodes(siblingId);
        return exits.length > 0
          ? exits.sort((a, b) => nodeIndex(b.id) - nodeIndex(a.id))[0]
          : children[children.length - 1];
      } else {
        const entries = getEntryNodes(siblingId);
        return entries.length > 0
          ? entries.sort((a, b) => nodeIndex(a.id) - nodeIndex(b.id))[0]
          : children[0];
      }
    }
  }

  return DataStore.map.get(siblingId);
}

/** Computes grouped navigation for the current page. */
export function computeSiblingNav() {
  const parentNode = AppState.currentParentId
    ? DataStore.map.get(AppState.currentParentId)
    : null;
  if (!parentNode) return { top: [], bottom: [] };

  const siblings = DataStore.nodes.filter(
    n => n.parentId === parentNode.parentId
  );
  const siblingIds = new Set(siblings.map(n => n.id));
  const myIndex = nodeIndex(parentNode.id);
  const isTerminal = parentNode.hasDerivation === false;
  const hasChildren = childrenOf(parentNode.id).length > 0;
  const isEmptyPage = !hasChildren;

  // --- Prev / Next within parent scope ---
  const prevNodes = (parentNode.prevIds || [])
    .filter(pid => siblingIds.has(pid))
    .map(pid => {
      if (isTerminal && isEmptyPage) return resolveDepthTarget(pid, 'prev');
      return DataStore.map.get(pid);
    })
    .filter(Boolean);

  const nextNodes = (parentNode.nextIds || [])
    .filter(nid => siblingIds.has(nid))
    .map(nid => {
      if (isTerminal && isEmptyPage) return resolveDepthTarget(nid, 'next');
      return DataStore.map.get(nid);
    })
    .filter(Boolean);

  // --- Parallel siblings (share ≥1 predecessor, or both are entry nodes) ---
  const myPrevSet = new Set(parentNode.prevIds || []);
  const parallelSiblings = siblings.filter(s => {
    if (s.id === parentNode.id) return false;
    const sPrevs = new Set(s.prevIds || []);
    if (myPrevSet.size === 0 && sPrevs.size === 0) return true;
    for (const pid of sPrevs) {
      if (myPrevSet.has(pid)) return true;
    }
    return false;
  });
  parallelSiblings.sort((a, b) => nodeIndex(a.id) - nodeIndex(b.id));
  const parallelBefore = parallelSiblings.filter(s => nodeIndex(s.id) < myIndex);
  const parallelAfter = parallelSiblings.filter(s => nodeIndex(s.id) > myIndex);

  // --- Cross-parent boundary traversal ---
  // When the current page is the first or last child of its parent (no
  // prev/next siblings within the same parent scope), we look one level up
  // to find navigation targets across parent boundaries. For example, if
  // the current page is the first child and has no prevNodes, we find the
  // parent's predecessor siblings and target their last exit nodes.
  const crossPrev = [];
  const crossNext = [];

  if (prevNodes.length === 0 && parentNode.parentId !== null) {
    const parent = DataStore.map.get(parentNode.parentId);
    const grandSiblings = DataStore.nodes.filter(
      n => n.parentId === parent?.parentId
    );
    const grandSiblingIds = new Set(grandSiblings.map(n => n.id));

    (parent?.prevIds || []).filter(parentId => grandSiblingIds.has(parentId)).forEach(prevPid => {
      const children = childrenOf(prevPid);
      if (children.length > 0) {
        const exits = getExitNodes(prevPid);
        const target = exits.length > 0
          ? exits.sort((a, b) => nodeIndex(b.id) - nodeIndex(a.id))[0]
          : children[children.length - 1];
        crossPrev.push(target);
      } else {
        const n = DataStore.map.get(prevPid);
        if (n) crossPrev.push(n);
      }
    });
  }

  if (nextNodes.length === 0 && parentNode.parentId !== null) {
    const parent = DataStore.map.get(parentNode.parentId);
    const grandSiblings = DataStore.nodes.filter(
      n => n.parentId === parent?.parentId
    );
    const grandSiblingIds = new Set(grandSiblings.map(n => n.id));

    (parent?.nextIds || []).filter(nextId => grandSiblingIds.has(nextId)).forEach(nextPid => {
      const children = childrenOf(nextPid);
      if (children.length > 0) {
        const entries = getEntryNodes(nextPid);
        const target = entries.length > 0
          ? entries.sort((a, b) => nodeIndex(a.id) - nodeIndex(b.id))[0]
          : children[0];
        crossNext.push(target);
      } else {
        const n = DataStore.map.get(nextPid);
        if (n) crossNext.push(n);
      }
    });
  }

  // --- Assemble grouped top/bottom ---
  // When depth preservation resolves a prev/next target into a different
  // parent's children, reclassify those as cross-parent with ⇤/⇥ arrows.
  const prevSame = [];
  const prevCross = [];
  prevNodes.forEach(n => {
    if (n.parentId === parentNode.parentId) prevSame.push(n);
    else prevCross.push(n);
  });

  const nextSame = [];
  const nextCross = [];
  nextNodes.forEach(n => {
    if (n.parentId === parentNode.parentId) nextSame.push(n);
    else nextCross.push(n);
  });

  // Merge depth-resolved cross targets with boundary-traversal cross targets
  const allCrossPrev = [...crossPrev, ...prevCross];
  const allCrossNext = [...crossNext, ...nextCross];

  /*
   * Arrow vocabulary:
   *   ↑ ↓  — standard vertical nav (prev/next and cross-parent)
   *   ⇤ ⇥  — parallel traversal (left/right with bar, since ←→ are derivation)
   *   ⇧ ⇩  — terminal node nav (bold arrows, signals depth change)
   */
  const isTerminalTarget = (n) =>
    n.hasDerivation === false && childrenOf(n.id).length === 0;
  const weAreTerminal = isTerminal && isEmptyPage;

  const prevArrow = (n) => (isTerminalTarget(n) || weAreTerminal) ? '⇧' : '↑';
  const nextArrow = (n) => (isTerminalTarget(n) || weAreTerminal) ? '⇩' : '↓';

  const top = [];
  const bottom = [];

  if (allCrossPrev.length > 0)
    top.push(makeGroup('Continue from Previous Section', 'cross', 'prev-btn',
      allCrossPrev.map(n => ({ node: n, arrow: prevArrow(n), direction: 'lateral-prev' }))));
  if (prevSame.length > 0)
    top.push(makeGroup(
      prevSame.length > 1 ? 'Previous Steps in Logic' : 'Previous Step in Logic',
      'prev', 'prev-btn',
      prevSame.map(n => ({ node: n, arrow: prevArrow(n) }))));
  if (parallelBefore.length > 0)
    top.push(makeGroup(
      parallelBefore.length > 1 ? 'Parallel Steps' : 'Parallel Step',
      'parallel', 'parallel-prev-btn',
      parallelBefore.map(n => ({ node: n, arrow: '⇤' }))));

  if (parallelAfter.length > 0)
    bottom.push(makeGroup(
      parallelAfter.length > 1 ? 'Parallel Steps' : 'Parallel Step',
      'parallel', 'parallel-next-btn',
      parallelAfter.map(n => ({ node: n, arrow: '⇥' }))));
  if (nextSame.length > 0)
    bottom.push(makeGroup(
      nextSame.length > 1 ? 'Next Steps in Logic' : 'Next Step in Logic',
      'next', 'next-btn',
      nextSame.map(n => ({ node: n, arrow: nextArrow(n) }))));
  if (allCrossNext.length > 0)
    bottom.push(makeGroup('Continue to Next Section', 'cross', 'next-btn',
      allCrossNext.map(n => ({ node: n, arrow: nextArrow(n), direction: 'lateral-next' }))));

  return { top, bottom };
}

function makeGroup(label, type, btnClass, items) {
  return { label, type, btnClass, items };
}

/**
 * Renders sibling navigation areas (prev/next/parallel) into the given view.
 * Computes navigation groups via computeSiblingNav(), then creates DOM elements
 * for "top" groups (prepended above content) and "bottom" groups (appended below).
 *
 * @param {HTMLElement} view - the `.map-flow` element to prepend/append navigation into
 */
export function renderSiblingNavigation(view) {
  const { top, bottom } = computeSiblingNav();
  const prefix = DataStore.config.nodePrefix;

  if (top.length > 0) {
    const area = document.createElement('div');
    area.className = 'sibling-nav-area prev';
    top.forEach(group => area.appendChild(renderGroup(group, prefix)));
    view.prepend(area);
  }

  if (bottom.length > 0) {
    const area = document.createElement('div');
    area.className = 'sibling-nav-area next';
    bottom.forEach(group => area.appendChild(renderGroup(group, prefix)));
    view.appendChild(area);
  }
}

function renderGroup(group, prefix) {
  const wrapper = document.createElement('div');
  wrapper.className = `sibling-nav-group sibling-nav-${group.type}`;

  const label = document.createElement('div');
  label.className = 'sibling-label';
  label.textContent = group.label;
  wrapper.appendChild(label);

  group.items.forEach(item => {
    const btn = document.createElement('button');
    btn.className = `btn-sibling ${group.btnClass} trigger-derive`;
    btn.type = 'button';
    btn.dataset.target = item.node.id;
    if (item.direction) btn.dataset.direction = item.direction;
    btn.innerHTML = `
      <span class="sibling-arrow">${item.arrow}</span>
      <span class="sibling-id">${prefix}${item.node.id}.</span>
      <span class="sibling-claim">${item.node.claim}</span>
    `;
    wrapper.appendChild(btn);
  });

  return wrapper;
}
