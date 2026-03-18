/* === ui-layout-stacking.js — Stack Wrapping & Zone Management === */
/*
 * Three extracted branch operations from updateStackedGroups(), each handling
 * a distinct layout state transition:
 *   - wrapStackGroup: narrow container → wrap nodes in stack-group column
 *   - handlePartialZone: stacked mode → absorb/release zone rows
 *   - unwrapStackGroup: wide container → unwrap nodes back to direct children
 *
 * Dependencies: (none)
 * Consumers:    ui-layout.js
 */

/**
 * Wrap a parallel group into a stack-group column, absorbing zone rows if
 * they fall below their thresholds. Applies DFS ordering and handles expander
 * migration.
 *
 * Called when: containerWidth < stackAt && !isStacked
 */
export function wrapStackGroup(
  viewEl,
  levelGroup,
  containerWidth,
  nodeIds,
  combinedWeight,
  zoneRows,
  zoneOrder
) {
  // Collect all nodes (must all be direct level-group children right now)
  const nodes = nodeIds.map(id =>
    levelGroup.querySelector(`:scope > .node-row[data-id="${id}"]`)
  );
  if (nodes.some(n => !n)) return false; // Abort if any node is already moved

  const wrapper = document.createElement('div');
  wrapper.className = 'stack-group';
  wrapper.style.setProperty('--flex-weight', String(combinedWeight));

  // Transfer parallel edge attributes so the wrapper participates
  // in the flex-basis equalization alongside any remaining siblings.
  if (nodes[0].hasAttribute('data-first-parallel')) {
    wrapper.dataset.firstParallel = 'true';
  }
  const lastNode = nodes[nodes.length - 1];
  if (lastNode.hasAttribute('data-last-parallel')) {
    wrapper.dataset.lastParallel = 'true';
  }

  // Insert wrapper in the position of the first node, then move all nodes in
  levelGroup.insertBefore(wrapper, nodes[0]);
  nodes.forEach(n => wrapper.appendChild(n));

  // --- Zone extension: absorb descendant rows ---
  if (zoneRows) {
    zoneRows.forEach(({ rowIdx: zoneRowIdx, nodeIds: zoneNodeIds, stackAt: zoneStackAt }) => {
      // Only absorb zone rows whose own stacking threshold is crossed
      // AND whose home level-group wouldn't re-stack them.
      if (zoneStackAt && containerWidth >= zoneStackAt) {
        // Single-node zone rows have nothing to be parallel with — always absorb.
        if (zoneNodeIds.length > 1) {
          const zoneLG = viewEl.querySelector(
            `.level-group[data-row-idx="${zoneRowIdx}"]`
          );
          const homeSGs = zoneLG?.dataset.stackGroups
            ? (() => { try { return JSON.parse(zoneLG.dataset.stackGroups); } catch { return null; } })()
            : null;
          const wouldReStack = homeSGs?.some(sg =>
            containerWidth < sg.stackAt && sg.nodeIds.some(id => zoneNodeIds.includes(id))
          );
          if (!wouldReStack) return; // Safe to skip
        }
      }

      zoneNodeIds.forEach(id => {
        const node = viewEl.querySelector(`.node-row[data-id="${id}"]`);
        if (!node) return;
        if (node.parentElement === wrapper) return;

        node.dataset.zoneOriginRow = String(zoneRowIdx);

        // Extract from another stack-group if needed
        const parentSG = node.parentElement;
        if (parentSG.classList.contains('stack-group')) {
          const sourceLG = parentSG.closest('.level-group');
          if (sourceLG) sourceLG.insertBefore(node, parentSG);
          if (!parentSG.querySelector('.node-row')) {
            const orphanedExp = parentSG.querySelector('.level-expander');
            if (orphanedExp && sourceLG) sourceLG.appendChild(orphanedExp);
            parentSG.remove();
          }
          if (sourceLG && !sourceLG.querySelector(':scope > .node-row')) {
            sourceLG.dataset.zoneAbsorbed = '';
          }
        }

        wrapper.appendChild(node);
      });

      const zoneLG = viewEl.querySelector(
        `.level-group[data-row-idx="${zoneRowIdx}"]`
      );
      if (zoneLG && !zoneLG.querySelector(':scope > .node-row')) {
        zoneLG.dataset.zoneAbsorbed = '';
      }
    });
  }

  // --- DFS ordering and indent depths ---
  if (zoneOrder) {
    zoneOrder.forEach(({ id, depth }) => {
      const node = wrapper.querySelector(`:scope > .node-row[data-id="${id}"]`);
      if (node) {
        wrapper.appendChild(node);
        node.style.setProperty('--indent-depth', String(depth));
      }
    });
  }

  // --- Rescue open expander into the stack-group ---
  const activeRow = wrapper.querySelector(':scope > .node-row.is-active');
  if (activeRow) {
    let expander = viewEl.querySelector('.level-expander.is-open');
    if (!expander) {
      expander = levelGroup.querySelector(':scope > .level-expander');
    }
    if (expander && expander.classList.contains('is-open')) {
      activeRow.after(expander);
      const lgRect = levelGroup.getBoundingClientRect();
      const sgRect = wrapper.getBoundingClientRect();
      const breakoutLeft = sgRect.left - lgRect.left;
      const breakoutRight = lgRect.right - sgRect.right;
      expander.style.flex = '0 0 auto';
      expander.style.width = 'auto';
      expander.style.marginLeft = `-${breakoutLeft}px`;
      expander.style.marginRight = `-${breakoutRight}px`;
    }
  }

  return true;
}

/**
 * In stacked mode, absorb or release individual zone rows based on their
 * thresholds. The host group stays stacked; only zone descendants move.
 *
 * Called when: containerWidth < stackAt && isStacked && zoneRows
 */
export function handlePartialZone(
  viewEl,
  levelGroup,
  containerWidth,
  firstNode,
  zoneRows,
  zoneOrder
) {
  let changed = false;
  const wrapper = firstNode.parentElement; // .stack-group

  if (!zoneRows) return changed;

  zoneRows.forEach(({ rowIdx: zoneRowIdx, nodeIds: zoneNodeIds, stackAt: zoneStackAt }) => {
    if (!zoneStackAt) return;

    const zoneLG = viewEl.querySelector(
      `.level-group[data-row-idx="${zoneRowIdx}"]`
    );
    if (!zoneLG) return;

    const zoneWide = containerWidth >= zoneStackAt;
    const sampleNode = wrapper.querySelector(`:scope > .node-row[data-id="${zoneNodeIds[0]}"]`);
    const isAbsorbed = !!sampleNode;

    if (zoneWide && isAbsorbed) {
      // Release: zone row back to home level-group
      if (zoneNodeIds.length <= 1) return; // Keep single-node rows absorbed

      const homeSGs = zoneLG.dataset.stackGroups
        ? (() => { try { return JSON.parse(zoneLG.dataset.stackGroups); } catch { return null; } })()
        : null;
      const wouldReStack = homeSGs?.some(sg =>
        containerWidth < sg.stackAt && sg.nodeIds.some(id => zoneNodeIds.includes(id))
      );
      if (wouldReStack) return;

      zoneNodeIds.forEach(id => {
        const node = wrapper.querySelector(`:scope > .node-row[data-id="${id}"]`);
        if (!node) return;

        // Handle attached expander
        let attachedExp = null;
        if (node.classList.contains('is-active')) {
          const nextSib = node.nextElementSibling;
          if (nextSib && nextSib.classList.contains('level-expander')) {
            attachedExp = nextSib;
          } else {
            attachedExp = wrapper.querySelector('.level-expander.is-open');
          }
        }

        delete node.dataset.zoneOriginRow;
        node.style.removeProperty('--indent-depth');

        // Restore to original column position
        const nodeCol = parseInt(node.dataset.colIdx) || 0;
        let insertBefore = null;
        for (const child of zoneLG.children) {
          const childCol = parseInt(child.dataset.colIdx);
          if (!isNaN(childCol) && childCol > nodeCol) {
            insertBefore = child;
            break;
          }
        }
        if (!insertBefore) {
          insertBefore = zoneLG.querySelector(':scope > .level-expander');
        }
        if (insertBefore && insertBefore.parentElement === zoneLG) {
          zoneLG.insertBefore(node, insertBefore);
        } else {
          zoneLG.appendChild(node);
        }

        // Move expander back
        if (attachedExp) {
          attachedExp.style.marginLeft = '';
          attachedExp.style.marginRight = '';
          attachedExp.style.flex = '';
          attachedExp.style.width = '';
          const homeExp = zoneLG.querySelector('.level-expander');
          if (homeExp && homeExp !== attachedExp) homeExp.remove();
          zoneLG.appendChild(attachedExp);
          if (!levelGroup.querySelector('.level-expander')) {
            const replacement = document.createElement('div');
            replacement.className = 'level-expander';
            levelGroup.appendChild(replacement);
          }
        }
      });

      delete zoneLG.dataset.zoneAbsorbed;

      // Re-apply DFS ordering on remaining wrapper children
      if (zoneOrder) {
        zoneOrder.forEach(({ id, depth }) => {
          const node = wrapper.querySelector(`:scope > .node-row[data-id="${id}"]`);
          if (node) {
            wrapper.appendChild(node);
            node.style.setProperty('--indent-depth', String(depth));
          }
        });
      }

      changed = true;

    } else if (!zoneWide && !isAbsorbed) {
      // Absorb: zone row into wrapper
      zoneNodeIds.forEach(id => {
        const node = viewEl.querySelector(`.node-row[data-id="${id}"]`);
        if (!node) return;
        if (node.parentElement === wrapper) return;

        node.dataset.zoneOriginRow = String(zoneRowIdx);

        // Extract from another stack-group if needed
        const parentSG = node.parentElement;
        if (parentSG.classList.contains('stack-group')) {
          const sourceLG = parentSG.closest('.level-group');
          if (sourceLG) sourceLG.insertBefore(node, parentSG);
          if (!parentSG.querySelector('.node-row')) {
            const orphanedExp = parentSG.querySelector('.level-expander');
            if (orphanedExp && sourceLG) sourceLG.appendChild(orphanedExp);
            parentSG.remove();
          }
          if (sourceLG && !sourceLG.querySelector(':scope > .node-row')) {
            sourceLG.dataset.zoneAbsorbed = '';
          }
        }

        wrapper.appendChild(node);
      });

      if (zoneLG && !zoneLG.querySelector(':scope > .node-row')) {
        zoneLG.dataset.zoneAbsorbed = '';
      }

      // Re-apply DFS ordering on all wrapper children
      if (zoneOrder) {
        zoneOrder.forEach(({ id, depth }) => {
          const node = wrapper.querySelector(`:scope > .node-row[data-id="${id}"]`);
          if (node) {
            wrapper.appendChild(node);
            node.style.setProperty('--indent-depth', String(depth));
          }
        });
      }

      changed = true;
    }
  });

  return changed;
}

/**
 * Unwrap a stack-group back to direct level-group children when container
 * widens above threshold. Release zone rows back to their home level-groups.
 *
 * Called when: containerWidth >= stackAt && isStacked
 */
export function unwrapStackGroup(
  viewEl,
  levelGroup,
  nodeIds,
  zoneRows
) {
  const firstNode = levelGroup.querySelector(
    `:scope > .stack-group > .node-row[data-id="${nodeIds[0]}"]`
  );
  if (!firstNode) return false;

  const wrapper = firstNode.parentElement;

  // --- Zone un-absorb: move zone nodes back before unwrapping ---
  if (zoneRows) {
    // Process in reverse so earlier rows are restored first
    [...zoneRows].reverse().forEach(({ rowIdx: zoneRowIdx, nodeIds: zoneNodeIds }) => {
      const zoneLG = viewEl.querySelector(
        `.level-group[data-row-idx="${zoneRowIdx}"]`
      );
      if (!zoneLG) return;

      zoneNodeIds.forEach(id => {
        const node = wrapper.querySelector(`:scope > .node-row[data-id="${id}"]`);
        if (!node) return;

        // If this node has an open expander in the wrapper, it must
        // travel back with the node to the original level-group.
        let attachedExp = null;
        if (node.classList.contains('is-active')) {
          const nextSib = node.nextElementSibling;
          if (nextSib && nextSib.classList.contains('level-expander')) {
            attachedExp = nextSib;
          } else {
            attachedExp = wrapper.querySelector('.level-expander.is-open');
          }
        }

        delete node.dataset.zoneOriginRow;
        node.style.removeProperty('--indent-depth');

        // Restore node to its original column position
        const nodeCol = parseInt(node.dataset.colIdx) || 0;
        let insertBefore = null;
        for (const child of zoneLG.children) {
          const childCol = parseInt(child.dataset.colIdx);
          if (!isNaN(childCol) && childCol > nodeCol) {
            insertBefore = child;
            break;
          }
        }
        if (!insertBefore) {
          insertBefore = zoneLG.querySelector(':scope > .level-expander');
        }
        if (insertBefore && insertBefore.parentElement === zoneLG) {
          zoneLG.insertBefore(node, insertBefore);
        } else {
          zoneLG.appendChild(node);
        }

        // Move expander back to home level-group
        if (attachedExp) {
          attachedExp.style.marginLeft = '';
          attachedExp.style.marginRight = '';
          attachedExp.style.flex = '';
          attachedExp.style.width = '';

          const homeExp = zoneLG.querySelector('.level-expander');
          if (homeExp && homeExp !== attachedExp) homeExp.remove();

          zoneLG.appendChild(attachedExp);

          // Ensure the host level-group still has an expander
          if (!levelGroup.querySelector('.level-expander')) {
            const replacement = document.createElement('div');
            replacement.className = 'level-expander';
            levelGroup.appendChild(replacement);
          }
        }
      });

      delete zoneLG.dataset.zoneAbsorbed;
    });
  }

  // --- Unwrap trigger nodes ---
  const nodes = nodeIds.map(id =>
    wrapper.querySelector(`:scope > .node-row[data-id="${id}"]`)
  );
  if (nodes.some(n => !n)) return false;

  // Restore each node as a direct level-group child, in original order
  nodes.forEach(n => {
    n.style.removeProperty('--indent-depth');
    levelGroup.insertBefore(n, wrapper);
  });

  // Rescue any expander that was moved into the stack-group while open
  const strandedExp = wrapper.querySelector('.level-expander');
  if (strandedExp) {
    strandedExp.style.marginLeft = '';
    strandedExp.style.marginRight = '';
    strandedExp.style.flex = '';
    strandedExp.style.width = '';
    levelGroup.appendChild(strandedExp);
  }
  wrapper.remove();

  return true;
}
