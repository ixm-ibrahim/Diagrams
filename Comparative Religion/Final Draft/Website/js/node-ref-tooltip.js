/* === node-ref-tooltip.js — Hover Tooltip for Node ID References === */
/**
 * When the user hovers over a .node-ref link (rendered by md()), this module
 * builds a small dropdown showing the referenced node's claim and its full
 * ancestry chain. Each entry is clickable — navigating to that node's page.
 *
 * Reuses the same visual pattern as the ancestry dropdown on parent badge
 * pills, but triggered by hover and anchored to inline text.
 *
 * Dependencies: data-store.js, templates.js (md)
 * Consumers:    ui-events.js (delegates .node-ref hover/click here)
 */

import { DataStore } from './data-store.js';
import { md } from './templates.js';

/** Currently open tooltip element (singleton — only one at a time). */
let activeWrapper = null;
let activeLink = null;
let closeTimer = null;

/**
 * Builds the ancestry chain for a node, including the node itself at the end.
 * Returns array from root → ... → parent → node.
 * Each entry: { node, targetId }
 */
function buildChain(nodeId) {
  const chain = [];
  const target = DataStore.map.get(nodeId);
  if (!target) return chain;

  // Walk up the parent chain
  const ancestors = [];
  let parentId = target.parentId;
  while (parentId !== null && parentId !== undefined) {
    const parentNode = DataStore.map.get(parentId);
    if (!parentNode) break;
    ancestors.push(parentNode);
    parentId = parentNode.parentId;
  }

  // Reverse so root is first
  ancestors.reverse();

  // Build entries: ancestors then the target node itself
  for (const node of ancestors) {
    chain.push({ node, targetId: getTargetId(node) });
  }
  chain.push({ node: target, targetId: getTargetId(target) });

  return chain;
}

/**
 * Determine navigation target for a node.
 */
function getTargetId(node) {
  const isTerminal = node.hasDerivation === false;
  const hasChildren = DataStore.nodes.some(n => n.parentId === node.id);

  if (!isTerminal && hasChildren) {
    return node.id;
  } else {
    return node.parentId;
  }
}

/**
 * Opens the node-ref tooltip near the given link element.
 * @param {HTMLElement} link — the .node-ref <a> that was hovered
 * @param {Function} onNavigate — callback(targetId) to trigger navigation
 */
export function openNodeRefTooltip(link, onNavigate) {
  const nodeId = link.dataset.node;
  if (!nodeId) return;

  // If already showing for this link, do nothing
  if (activeLink === link && activeWrapper) {
    cancelClose();
    return;
  }

  // Close any existing tooltip
  closeNodeRefTooltip();

  const chain = buildChain(nodeId);
  if (chain.length === 0) return;

  const prefix = DataStore.config.nodePrefix;

  // Build wrapper
  const wrapper = document.createElement('div');
  wrapper.className = 'node-ref-tooltip-wrap';

  const dropdown = document.createElement('div');
  dropdown.className = 'node-ref-tooltip';

  chain.forEach((entry, idx) => {
    const btn = document.createElement('button');
    btn.type = 'button';

    // The last entry is the referenced node itself — highlight it
    const isTarget = idx === chain.length - 1;
    btn.className = 'node-ref-item' + (isTarget ? ' is-target' : '');

    btn.style.paddingLeft = `${10 + idx * 10}px`;
    btn.dataset.target = entry.targetId === null ? 'null' : entry.targetId;

    btn.innerHTML = `
      <span class="node-ref-id">${prefix}${entry.node.id}</span>
      <span class="node-ref-claim">${md(entry.node.claim)}</span>
    `;

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      e.preventDefault();
      const target = entry.targetId;
      closeNodeRefTooltip();
      onNavigate(target);
    });

    dropdown.appendChild(btn);
  });

  wrapper.appendChild(dropdown);
  document.body.appendChild(wrapper);

  // Position: anchored to the link
  const linkRect = link.getBoundingClientRect();
  const viewportHeight = window.innerHeight;
  const viewportWidth = window.innerWidth;
  const spaceBelow = viewportHeight - linkRect.bottom;

  // Horizontal: center on link, but clamp to viewport
  let left = linkRect.left + linkRect.width / 2;
  wrapper.style.left = `${left}px`;

  if (spaceBelow >= 200 || spaceBelow >= linkRect.top) {
    // Open downward
    wrapper.style.top = `${linkRect.bottom + 6}px`;
    wrapper.classList.add('tooltip-down');
  } else {
    // Open upward
    wrapper.style.bottom = `${viewportHeight - linkRect.top + 6}px`;
    wrapper.classList.add('tooltip-up');
  }

  // Animate in
  requestAnimationFrame(() => {
    dropdown.classList.add('is-open');

    // After rendering, clamp horizontal position to viewport
    const tooltipRect = wrapper.getBoundingClientRect();
    if (tooltipRect.right > viewportWidth - 12) {
      const shift = tooltipRect.right - viewportWidth + 12;
      wrapper.style.left = `${left - shift}px`;
    }
    if (tooltipRect.left < 12) {
      wrapper.style.left = '12px';
    }
  });

  // Close on mouseleave with delay
  wrapper.addEventListener('mouseleave', (e) => {
    const movingTo = e.relatedTarget;
    if (movingTo === link || link.contains(movingTo)) return;
    scheduleClose();
  });

  wrapper.addEventListener('mouseenter', () => {
    cancelClose();
  });

  link.addEventListener('mouseleave', handleLinkLeave);

  // Close on outside click
  const outsideHandler = (e) => {
    if (!wrapper.contains(e.target) && e.target !== link) {
      closeNodeRefTooltip();
      document.removeEventListener('click', outsideHandler, true);
    }
  };
  setTimeout(() => {
    document.addEventListener('click', outsideHandler, true);
  }, 0);

  activeWrapper = wrapper;
  activeWrapper._outsideHandler = outsideHandler;
  activeLink = link;
}

function handleLinkLeave(e) {
  const movingTo = e.relatedTarget;
  if (activeWrapper && (movingTo === activeWrapper || activeWrapper.contains(movingTo))) return;
  scheduleClose();
}

function scheduleClose() {
  cancelClose();
  closeTimer = setTimeout(() => {
    closeNodeRefTooltip();
  }, 200);
}

function cancelClose() {
  if (closeTimer) {
    clearTimeout(closeTimer);
    closeTimer = null;
  }
}

/**
 * Closes the currently open node-ref tooltip, if any.
 */
export function closeNodeRefTooltip() {
  cancelClose();
  if (activeWrapper) {
    if (activeWrapper._outsideHandler) {
      document.removeEventListener('click', activeWrapper._outsideHandler, true);
    }
    activeWrapper.remove();
    activeWrapper = null;
  }
  if (activeLink) {
    activeLink.removeEventListener('mouseleave', handleLinkLeave);
    activeLink = null;
  }
}
