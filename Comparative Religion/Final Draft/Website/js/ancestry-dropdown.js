/* === ancestry-dropdown.js — Ancestry Dropdown on Parent Badge === */
/**
 * When the user clicks a parent badge pill, this module builds a dropdown
 * listing all ancestors of the current node (cross-page parenthood chain).
 * Each entry is clickable — navigating to that ancestor's derivation page,
 * or its parent's page if the ancestor is terminal (no derivation).
 *
 * The dropdown direction (above or below the pill) is chosen based on
 * available viewport space.  It collapses on mouseleave.
 *
 * Dependencies: data-store.js, state.js, templates.js (md)
 * Consumers:    ui-events.js (delegates .ancestry-trigger clicks here)
 */

import { DataStore } from './data-store.js';
import { md } from './templates.js';

/** Currently open dropdown element (singleton — only one at a time). */
let activeDropdown = null;
let activeWrapper = null;

/**
 * Builds the ancestry chain for a given node, walking up parentId.
 * Returns an array from immediate parent → root (outermost ancestor first
 * after reversal, so the list reads top-down: root … → grandparent → parent).
 *
 * Each entry: { node, targetId } where targetId is the page to navigate to.
 */
function buildAncestry(nodeId) {
  const ancestry = [];
  let current = DataStore.map.get(nodeId);
  if (!current) return ancestry;

  // Walk up the parent chain
  let parentId = current.parentId;
  while (parentId !== null && parentId !== undefined) {
    const parentNode = DataStore.map.get(parentId);
    if (!parentNode) break;

    // Determine navigation target:
    // - If the ancestor has a derivation page (hasDerivation !== false
    //   and has children), navigate to its page (currentParentId = its id).
    // - If terminal (no derivation or no children), navigate to the page
    //   that *contains* it (currentParentId = its parentId).
    const isTerminal = parentNode.hasDerivation === false;
    const hasChildren = DataStore.nodes.some(n => n.parentId === parentNode.id);

    let targetId;
    if (!isTerminal && hasChildren) {
      // Has its own derivation page — go there
      targetId = parentNode.id;
    } else {
      // Terminal or childless — go to the page containing it
      targetId = parentNode.parentId;
    }

    ancestry.push({ node: parentNode, targetId });
    parentId = parentNode.parentId;
  }

  // Reverse so root is at the top
  ancestry.reverse();
  return ancestry;
}

/**
 * Opens the ancestry dropdown for a given badge button.
 * @param {HTMLElement} badge — the .node-badge button that was clicked
 * @param {string} nodeId — the node whose ancestry to show
 * @param {Function} onNavigate — callback(targetId) to trigger navigation
 */
export function openAncestryDropdown(badge, nodeId, onNavigate) {
  // Close any existing dropdown first
  closeAncestryDropdown();

  const ancestry = buildAncestry(nodeId);
  if (ancestry.length === 0) return;

  const prefix = DataStore.config.nodePrefix;

  // Create wrapper (positioned relative to badge)
  const wrapper = document.createElement('div');
  wrapper.className = 'ancestry-dropdown-wrap';

  const dropdown = document.createElement('div');
  dropdown.className = 'ancestry-dropdown';

  ancestry.forEach((entry, idx) => {
    const btn = document.createElement('button');
    btn.className = 'ancestry-item';
    btn.type = 'button';
    const isTerminal = entry.node.hasDerivation === false
      && !DataStore.nodes.some(n => n.parentId === entry.node.id);

    // Show indent based on depth from root
    btn.style.paddingLeft = `${12 + idx * 12}px`;

    btn.dataset.target = entry.targetId === null ? 'null' : entry.targetId;
    btn.innerHTML = `
      <span class="ancestry-id">${prefix}${entry.node.id}</span>
      <span class="ancestry-claim">${md(entry.node.claim)}</span>
      ${isTerminal ? '<span class="ancestry-terminal">terminal</span>' : ''}
    `;
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const target = entry.targetId;
      closeAncestryDropdown();
      onNavigate(target);
    });
    dropdown.appendChild(btn);
  });

  wrapper.appendChild(dropdown);

  // Pick up colors from the node card:
  // - Node's own color (--n-border) → background tint
  // - Parent pill color (--p-border) → top border accent
  const card = badge.closest('.node-card');
  if (card) {
    const style = getComputedStyle(card);
    const nodeDark   = style.getPropertyValue('--n-border-dark').trim();
    const nodeLight  = style.getPropertyValue('--n-border-light').trim();
    const pillDark   = style.getPropertyValue('--p-border-dark').trim();
    const pillLight  = style.getPropertyValue('--p-border-light').trim();
    if (nodeDark)  wrapper.style.setProperty('--ancestry-bg-dark', nodeDark);
    if (nodeLight) wrapper.style.setProperty('--ancestry-bg-light', nodeLight);
    if (pillDark)  wrapper.style.setProperty('--ancestry-border-dark', pillDark);
    if (pillLight) wrapper.style.setProperty('--ancestry-border-light', pillLight);
  }

  // Attach to document.body with fixed positioning so ancestor
  // overflow: hidden (e.g. on .node-card) doesn't clip the dropdown.
  document.body.appendChild(wrapper);

  // Measure badge position and available space
  const badgeRect = badge.getBoundingClientRect();
  const viewportHeight = window.innerHeight;
  const spaceAbove = badgeRect.top;
  const spaceBelow = viewportHeight - badgeRect.bottom;

  // Horizontal: align right edge of dropdown with right edge of badge
  wrapper.style.right = `${window.innerWidth - badgeRect.right}px`;

  if (spaceBelow >= spaceAbove || spaceBelow > 300) {
    // Open downward: top edge just below the badge
    wrapper.style.top = `${badgeRect.bottom + 6}px`;
    wrapper.classList.add('ancestry-down');
  } else {
    // Open upward: bottom edge just above the badge
    wrapper.style.bottom = `${viewportHeight - badgeRect.top + 6}px`;
    wrapper.classList.add('ancestry-up');
  }

  // Animate in
  requestAnimationFrame(() => {
    dropdown.classList.add('is-open');
  });

  // Close on mouseleave — but keep open if mouse moves back to badge
  const handleLeave = (e) => {
    // relatedTarget is what the mouse moved TO
    const movingTo = e.relatedTarget;
    if (movingTo === badge || badge.contains(movingTo)) return;
    closeAncestryDropdown();
  };
  wrapper.addEventListener('mouseleave', handleLeave);

  // Also keep open when mouse re-enters from badge
  badge.addEventListener('mouseleave', (e) => {
    const movingTo = e.relatedTarget;
    if (movingTo === wrapper || wrapper.contains(movingTo)) return;
    // Small delay so the mouse has time to reach the dropdown
    setTimeout(() => {
      if (!wrapper.matches(':hover') && !badge.matches(':hover')) {
        closeAncestryDropdown();
      }
    }, 150);
  }, { once: true });

  // Also close if user clicks outside
  const outsideHandler = (e) => {
    if (!wrapper.contains(e.target) && e.target !== badge) {
      closeAncestryDropdown();
      document.removeEventListener('click', outsideHandler, true);
    }
  };
  setTimeout(() => {
    document.addEventListener('click', outsideHandler, true);
  }, 0);

  activeDropdown = dropdown;
  activeWrapper = wrapper;
  activeWrapper._outsideHandler = outsideHandler;
}

/**
 * Closes the currently open ancestry dropdown, if any.
 */
export function closeAncestryDropdown() {
  if (activeWrapper) {
    if (activeWrapper._outsideHandler) {
      document.removeEventListener('click', activeWrapper._outsideHandler, true);
    }
    activeWrapper.remove();
    activeWrapper = null;
    activeDropdown = null;
  }
}
