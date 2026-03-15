/**
 * =============================================================================
 * ui-layout.js — Parallel-Row Cramp Detection
 * =============================================================================
 * Analyses rows of nodes produced by graph-engine.js and identifies which
 * parent-groups are "too cramped" — i.e. where each child's allocated pixel
 * width would fall below STACK_THRESHOLD.
 *
 * No DOM access, no DataStore access.  Pure calculation that works solely
 * from the row array and a measured container width, making it easy to
 * unit-test in isolation.
 *
 * Width model
 * -----------
 * Each unique parent referenced in a row is assumed to own an equal horizontal
 * slice of the container (containerWidth / numParentGroups).  Within that
 * slice, the per-child width is simply groupWidth / childCount.
 *
 * This mirrors the flex-weight model in ui-render.js, where each parent at
 * the previous level starts with equal weight (1 / N) and distributes it to
 * its children.  The equal-share assumption is exact for the first row, and a
 * reliable approximation for deeper rows where parent weights are already
 * proportional to their child counts.
 *
 * Root nodes (prevIds absent or empty) are treated as a single group under
 * the sentinel key null.
 *
 * Dependencies: constants.js (STACK_THRESHOLD)
 * Consumers:    (none yet — to be wired in during a later step)
 * =============================================================================
 */

import { STACK_THRESHOLD } from './constants.js';

/**
 * Keeps every parallel sibling group in `viewEl` in the correct layout state
 * (horizontal or stacked-column) for the given container width.
 *
 * Strategy — dynamic DOM wrapping, not a static wrapper:
 *   Nodes are built as direct `.level-group` children so the parallel CSS
 *   selectors (which require `> .node-row`) work correctly at full width.
 *   `buildView` records each multi-node group as JSON in
 *   `levelGroup.dataset.stackGroups`.  This function reads that metadata and:
 *     • wraps the group's nodes in a `.stack-group` column when narrow, or
 *     • moves them back as direct children when wide.
 *   This means the parallel flex-equalization and marker CSS are always active
 *   on direct children and never broken by an intermediate wrapper element.
 *
 * The function is safe to call on every resize event — it only touches the DOM
 * when a group actually crosses its threshold.
 *
 * @param {HTMLElement} viewEl         - the .map-flow element currently in DOM
 * @param {number}      containerWidth - measured pixel width of the container
 */
export function updateStackedGroups(viewEl, containerWidth) {
  let changed = false;

  // Snapshot the active node's vertical position before any DOM changes.
  // If a stacked→parallel transition moves it significantly, we scroll.
  const activeRowBefore = viewEl.querySelector('.node-row.is-active');
  const activeTopBefore = activeRowBefore
    ? activeRowBefore.getBoundingClientRect().top
    : null;

  viewEl.querySelectorAll('.level-group[data-stack-groups]').forEach(levelGroup => {
    let groups;
    try { groups = JSON.parse(levelGroup.dataset.stackGroups); }
    catch { return; }

    groups.forEach(({ nodeIds, stackAt, combinedWeight, zoneRows, zoneOrder }) => {
      const shouldStack = containerWidth < stackAt;

      // Locate the first node — it tells us the current wrapping state
      const firstNode = levelGroup.querySelector(
        `:scope > .node-row[data-id="${nodeIds[0]}"], ` +
        `:scope > .stack-group > .node-row[data-id="${nodeIds[0]}"]`
      );
      if (!firstNode) return;

      const isStacked = firstNode.parentElement.classList.contains('stack-group');

      if (shouldStack && !isStacked) {
        // --- Wrap ---
        // Collect all nodes (must all be direct level-group children right now)
        const nodes = nodeIds.map(id =>
          levelGroup.querySelector(`:scope > .node-row[data-id="${id}"]`)
        );
        if (nodes.some(n => !n)) return; // Abort if any node is already moved

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
            // This prevents convergence rows from being pulled in prematurely
            // when only the parent row is narrow, while still absorbing rows
            // that would just re-stack at the wrong depth in their home LG.
            if (zoneStackAt && containerWidth >= zoneStackAt) {
              // Single-node zone rows (alongside dummies) have nothing to be
              // parallel with — always absorb them into the parent zone.
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
                if (!wouldReStack) return; // Safe to skip — nodes will stay parallel
              }
              // Otherwise fall through to absorb
            }
            zoneNodeIds.forEach(id => {
              // Search the entire view — a sub-zone may have already moved
              // this node into a different stack-group.
              const node = viewEl.querySelector(`.node-row[data-id="${id}"]`);
              if (!node) return;
              // Skip if already inside THIS wrapper (idempotent)
              if (node.parentElement === wrapper) return;

              // Tag with original row so the SVG engine can create
              // separate visual rows for zone-absorbed nodes.
              node.dataset.zoneOriginRow = String(zoneRowIdx);

              // If inside another stack-group (sub-zone), extract first
              const parentSG = node.parentElement;
              if (parentSG.classList.contains('stack-group')) {
                const sourceLG = parentSG.closest('.level-group');
                if (sourceLG) sourceLG.insertBefore(node, parentSG);

                if (!parentSG.querySelector('.node-row')) {
                  // Rescue any expander before destroying the stack-group —
                  // otherwise it's lost when the SG is removed from the DOM.
                  const orphanedExp = parentSG.querySelector('.level-expander');
                  if (orphanedExp && sourceLG) sourceLG.appendChild(orphanedExp);
                  parentSG.remove();
                }
                // Mark source level-group absorbed if now empty of real nodes
                if (sourceLG && !sourceLG.querySelector(':scope > .node-row')) {
                  sourceLG.dataset.zoneAbsorbed = '';
                }
              }

              wrapper.appendChild(node);
            });

            // Mark the original level-group as absorbed if empty
            const zoneLG = viewEl.querySelector(
              `.level-group[data-row-idx="${zoneRowIdx}"]`
            );
            if (zoneLG && !zoneLG.querySelector(':scope > .node-row')) {
              zoneLG.dataset.zoneAbsorbed = '';
            }
          });
        }

        // --- DFS ordering and indent depths ---
        // Reorder wrapper children to depth-first outline order and set
        // --indent-depth on each node for CSS indentation.
        if (zoneOrder) {
          zoneOrder.forEach(({ id, depth }) => {
            const node = wrapper.querySelector(`:scope > .node-row[data-id="${id}"]`);
            if (node) {
              wrapper.appendChild(node);  // moves to end → builds DFS order
              node.style.setProperty('--indent-depth', String(depth));
            }
          });
        }

        // --- Rescue open expander into the stack-group ---
        // If an expander is currently open for a node that just moved into
        // this stack-group, move the expander inside the wrapper right after
        // that node and recompute the breakout margins so it still spans
        // the full level-group width.
        const activeRow = wrapper.querySelector(
          ':scope > .node-row.is-active'
        );
        if (activeRow) {
          // Search globally for the open expander — it may be in the host
          // level-group, in a zone-absorbed level-group, or already in the
          // wrapper from a previous cycle.  There is only ever one open
          // expander at a time, so a broad search is safe.
          let expander = viewEl.querySelector('.level-expander.is-open');
          if (!expander) {
            // Fall back to the host level-group's (closed) expander so a
            // simple stack (no zone absorption) still works.
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

        changed = true;

      } else if (shouldStack && isStacked) {
        // --- Partial zone release / absorption ---
        // The host group stays stacked, but individual zone rows may need
        // to be released (container widened above their threshold) or
        // absorbed (container narrowed below their threshold).
        if (zoneRows) {
          const wrapper = firstNode.parentElement; // .stack-group

          zoneRows.forEach(({ rowIdx: zoneRowIdx, nodeIds: zoneNodeIds, stackAt: zoneStackAt }) => {
            if (!zoneStackAt) return;

            const zoneLG = viewEl.querySelector(
              `.level-group[data-row-idx="${zoneRowIdx}"]`
            );
            if (!zoneLG) return;

            const zoneWide = containerWidth >= zoneStackAt;

            // Check current state: are these nodes in the wrapper or in their home LG?
            const sampleNode = wrapper.querySelector(`:scope > .node-row[data-id="${zoneNodeIds[0]}"]`);
            const isAbsorbed = !!sampleNode;

            if (zoneWide && isAbsorbed) {
              // Don't release single-node zone rows — they have nothing to be
              // parallel with (only dummies), so keep them in the indented stack.
              if (zoneNodeIds.length <= 1) return;

              // Don't release if the home LG would just re-stack these nodes
              // at the wrong depth — keep them absorbed with correct zone depths.
              const homeSGs = zoneLG.dataset.stackGroups
                ? (() => { try { return JSON.parse(zoneLG.dataset.stackGroups); } catch { return null; } })()
                : null;
              const wouldReStack = homeSGs?.some(sg =>
                containerWidth < sg.stackAt && sg.nodeIds.some(id => zoneNodeIds.includes(id))
              );
              if (wouldReStack) return;

              // --- Release zone row back to its home level-group ---
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
              // --- Absorb zone row into wrapper ---
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

              // Mark zone LG as absorbed if empty
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
        }

      } else if (!shouldStack && isStacked) {
        const wrapper = firstNode.parentElement; // .stack-group

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
              // Grab it BEFORE moving the node so the sibling relationship
              // is still intact.
              let attachedExp = null;
              if (node.classList.contains('is-active')) {
                const nextSib = node.nextElementSibling;
                if (nextSib && nextSib.classList.contains('level-expander')) {
                  attachedExp = nextSib;
                } else {
                  // Might not be adjacent — search the wrapper
                  attachedExp = wrapper.querySelector('.level-expander.is-open');
                }
              }

              // Remove zone origin tag and indent depth set during absorption
              delete node.dataset.zoneOriginRow;
              node.style.removeProperty('--indent-depth');

              // Restore node to its original column position using data-col-idx.
              // Dummies that never moved still sit in the level-group, so we
              // find the first child whose col-idx is higher and insert before it.
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
                // No child with a higher colIdx — insert before the expander.
                // MUST use :scope > to ensure it's a direct child (insertBefore
                // requires the reference node to be a child of the parent).
                insertBefore = zoneLG.querySelector(':scope > .level-expander');
              }
              // Safety: if insertBefore is somehow not a direct child, fall
              // back to appendChild to avoid losing the node entirely.
              if (insertBefore && insertBefore.parentElement === zoneLG) {
                zoneLG.insertBefore(node, insertBefore);
              } else {
                zoneLG.appendChild(node);
              }

              // Move the expander to the node's home level-group.
              // The expander element may have originated from the host
              // level-group (levelGroup), so we must:
              //   (a) remove any duplicate empty expander in zoneLG first,
              //   (b) create a replacement empty expander in the host LG.
              if (attachedExp) {
                attachedExp.style.marginLeft = '';
                attachedExp.style.marginRight = '';
                attachedExp.style.flex = '';
                attachedExp.style.width = '';

                // Remove the home LG's original (empty) expander to avoid
                // duplicates — the open one we're moving in replaces it.
                const homeExp = zoneLG.querySelector('.level-expander');
                if (homeExp && homeExp !== attachedExp) homeExp.remove();

                zoneLG.appendChild(attachedExp);

                // Ensure the host level-group still has an expander element
                // (it just lost the one we moved out).
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
        if (nodes.some(n => !n)) return;

        // Restore each node as a direct level-group child, in original order,
        // by inserting them before the wrapper (which still holds its position)
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
        changed = true;
      }
    });

    // Toggle data-has-stacked so CSS can prevent cross-axis stretch on
    // direct .node-row siblings when a .stack-group column is present.
    const hasAnyStacked = levelGroup.querySelector(':scope > .stack-group') !== null;
    if (hasAnyStacked) {
      levelGroup.dataset.hasStacked = '';
    } else {
      delete levelGroup.dataset.hasStacked;
    }

  });

  // Always run integrity when an open expander exists — breakout margins
  // and accommodation spacers must track container-width changes that don't
  // cross a stacking threshold (e.g. two sibling stack-groups in the same
  // level-group resizing between thresholds).
  if (changed || viewEl.querySelector('.level-expander.is-open')) {
    ensureExpanderIntegrity(viewEl);
  }

  // When a stacked→parallel transition moves the active (expanded) node
  // significantly, scroll to keep it visible.  Compare its position before
  // and after the DOM update to detect movement.
  if (activeTopBefore !== null && changed) {
    const activeRowAfter = viewEl.querySelector('.node-row.is-active');
    if (activeRowAfter) {
      const activeTopAfter = activeRowAfter.getBoundingClientRect().top;
      const drift = Math.abs(activeTopAfter - activeTopBefore);
      if (drift > 60) {
        // Node moved substantially — scroll so its top edge sits just
        // below the page header with some padding.
        const header = document.querySelector('.app-header, #pageHeader, header');
        const headerBottom = header ? header.getBoundingClientRect().bottom : 0;
        const targetTop = Math.max(headerBottom, 0) + 16;
        window.scrollTo({
          top: window.scrollY + activeTopAfter - targetTop,
          behavior: 'smooth'
        });
      }
    }
  }

  return changed;
}

/* ---------------------------------------------------------------------------
 * Expander integrity cleanup
 *
 * After any stacking/unstacking transition the open expander may have been
 * displaced (moved to a different level-group, left at the wrong position
 * inside a wrapper, or duplicated).  This function enforces two invariants:
 *
 *   1. The open expander (if any) is the immediate next sibling of the
 *      active node-row, with correct breakout margins when inside a
 *      stack-group.
 *   2. Every visible (non-zone-absorbed) level-group has exactly one
 *      .level-expander element so future click interactions work.
 * --------------------------------------------------------------------------- */
function ensureExpanderIntegrity(viewEl) {
  const openExp = viewEl.querySelector('.level-expander.is-open');
  const activeRow = viewEl.querySelector('.node-row.is-active');

  // --- Position the open expander correctly ---
  if (openExp && activeRow) {
    const stackGroup = activeRow.closest('.stack-group');

    if (stackGroup) {
      // Stacked mode: expander must be right after the active row inside
      // the stack-group so it appears inline (tree-view style).
      if (openExp.previousElementSibling !== activeRow ||
          openExp.parentElement !== activeRow.parentElement) {
        activeRow.after(openExp);
      }
      // Reset positioning from parallel or mixed mode
      openExp.style.position = '';
      openExp.style.top = '';
      openExp.style.left = '';
      // Clear parallel pull-up — not needed in stacked mode
      delete openExp.dataset.parallelPull;
      openExp.style.removeProperty('--parallel-pull');
      const lg = stackGroup.closest('.level-group');
      lg.style.paddingBottom = '';
      const lgRect = lg.getBoundingClientRect();
      const sgRect = stackGroup.getBoundingClientRect();
      openExp.style.flex = '0 0 auto';
      openExp.style.width = 'auto';
      openExp.style.marginLeft = `-${sgRect.left - lgRect.left}px`;
      openExp.style.marginRight = `-${lgRect.right - sgRect.right}px`;

      // --- Accommodation spacers for sibling stack-groups ---
      // Remove stale spacers and recreate so nodes in sibling columns
      // shift down to make room for the breakout expander.
      document.querySelectorAll('.expander-spacer').forEach(s => s.remove());
      const expInner = openExp.querySelector('.exp-inner');
      const spacerHeight = expInner ? expInner.scrollHeight + 16 : 0;
      if (spacerHeight > 0) {
        // Use index-based placement: the active node's position in its
        // stack determines the insertion point in every sibling stack.
        // This is robust against per-node height differences that make
        // bounding-rect comparisons flaky across resize breakpoints.
        const stackRows = Array.from(
          stackGroup.querySelectorAll(':scope > .node-row')
        );
        const activeIdx = stackRows.indexOf(activeRow);

        lg.querySelectorAll(':scope > .stack-group').forEach(sg => {
          if (sg === stackGroup) return;
          const siblingRows = Array.from(
            sg.querySelectorAll(':scope > .node-row')
          );
          if (siblingRows.length === 0) return;

          const spacer = document.createElement('div');
          spacer.className = 'expander-spacer';
          spacer.style.height = spacerHeight + 'px';

          // Insert after the node at the same index, or after the last
          // node if the sibling stack has fewer nodes.
          const targetIdx = Math.min(activeIdx, siblingRows.length - 1);
          siblingRows[targetIdx].after(spacer);
        });
      }
    } else {
      const lg = activeRow.closest('.level-group');
      const hasStackedSibling = lg.querySelector(':scope > .stack-group');

      if (hasStackedSibling) {
        // Mixed parallel+stacked mode: the level-group has a tall stack-group
        // alongside shorter parallel node-rows.  flex-wrap places the expander
        // below the tallest item (the stack-group), far below the clicked row.
        // Fix: position the expander absolutely right below the active row.
        if (openExp.parentElement !== lg) {
          lg.appendChild(openExp);
        }

        const rowRect = activeRow.getBoundingClientRect();
        const lgRect = lg.getBoundingClientRect();
        const topOffset = rowRect.bottom - lgRect.top;

        openExp.style.position = 'absolute';
        openExp.style.top = topOffset + 'px';
        openExp.style.left = '0';
        openExp.style.width = '100%';
        openExp.style.flex = 'none';
        openExp.style.marginLeft = '';
        openExp.style.marginRight = '';

        // --- Accommodation spacers for sibling stack-groups ---
        // Push stack-group content below the expander down so
        // the absolute-positioned expander doesn't overlap nodes.
        // The first node in each stack-group is on the same visual "row"
        // as the parallel active node — the spacer goes right after it.
        // Its height = expander height + any height difference between the
        // active row and that first stack node (the active row may be taller).
        document.querySelectorAll('.expander-spacer').forEach(s => s.remove());
        const expInner = openExp.querySelector('.exp-inner');
        const expHeight = expInner ? expInner.scrollHeight + 16 : 0;
        if (expHeight > 0) {
          const rowBottom = rowRect.bottom;
          lg.querySelectorAll(':scope > .stack-group').forEach(sg => {
            const sgNodes = Array.from(
              sg.querySelectorAll(':scope > .node-row')
            );
            if (sgNodes.length < 2) return; // need 2+ nodes for a spacer to matter
            const firstNode = sgNodes[0];
            const firstNodeBottom = firstNode.getBoundingClientRect().bottom;
            const heightDiff = Math.max(0, rowBottom - firstNodeBottom);
            const spacer = document.createElement('div');
            spacer.className = 'expander-spacer';
            spacer.style.height = (expHeight + heightDiff) + 'px';
            firstNode.after(spacer);
          });
        }

        // Ensure level-group is tall enough so content below shifts down.
        // Recalculate after spacers are added (they grow the stack-group).
        lg.style.paddingBottom = '';
        const naturalHeight = lg.offsetHeight;
        const neededHeight = topOffset + expHeight;
        if (neededHeight > naturalHeight) {
          lg.style.paddingBottom = (neededHeight - naturalHeight) + 'px';
        }
      } else {
        // Pure parallel mode: update the negative-margin pull-up so the
        // expander tracks the clicked node's bottom on resize.
        if (openExp.parentElement !== lg) {
          lg.appendChild(openExp);
        } else {
          const lastChild = lg.lastElementChild;
          if (lastChild !== openExp) lg.appendChild(openExp);
        }
        openExp.style.marginLeft = '';
        openExp.style.marginRight = '';
        openExp.style.flex = '';
        openExp.style.width = '';
        openExp.style.position = '';
        openExp.style.top = '';
        openExp.style.left = '';
        lg.style.paddingBottom = '';
        document.querySelectorAll('.expander-spacer').forEach(s => s.remove());

        // Recalculate pull-up for current node-card heights.
        // Always check when there are multiple siblings — the expander may
        // have transitioned from stacked mode where parallelPull was cleared.
        const siblingNodes = lg.querySelectorAll(':scope > .node-row');
        if (siblingNodes.length > 1) {
          const clickedCard = activeRow.querySelector('.node-card');
          const clickedBottom = clickedCard
            ? clickedCard.getBoundingClientRect().bottom
            : activeRow.getBoundingClientRect().bottom;
          let tallestCardBottom = clickedBottom;
          siblingNodes.forEach(n => {
            const card = n.querySelector('.node-card');
            const b = card ? card.getBoundingClientRect().bottom
                           : n.getBoundingClientRect().bottom;
            if (b > tallestCardBottom) tallestCardBottom = b;
          });
          const pullUp = tallestCardBottom - clickedBottom;
          if (pullUp > 0) {
            openExp.style.setProperty('--parallel-pull', `-${pullUp}px`);
            openExp.dataset.parallelPull = '';
          } else {
            openExp.style.removeProperty('--parallel-pull');
            delete openExp.dataset.parallelPull;
          }
        }
      }
    }
  } else if (openExp && !activeRow) {
    // Orphaned open expander with no active node — close it
    openExp.classList.remove('is-open');
    openExp.innerHTML = '';
  }

  // --- Ensure every visible level-group has exactly one expander ---
  viewEl.querySelectorAll('.level-group:not([data-zone-absorbed])').forEach(lg => {
    const allExp = lg.querySelectorAll('.level-expander');
    if (allExp.length === 0) {
      const newExp = document.createElement('div');
      newExp.className = 'level-expander';
      lg.appendChild(newExp);
    } else if (allExp.length > 1) {
      // Keep the open one; remove extras
      let kept = null;
      allExp.forEach(exp => {
        if (exp.classList.contains('is-open')) { kept = exp; }
      });
      if (!kept) kept = allExp[0];
      allExp.forEach(exp => { if (exp !== kept) exp.remove(); });
    }
  });
}

/**
 * Given one row from computeLevels() and the container's current pixel width,
 * groups real nodes by their shared DAG parent(s), estimates the per-child
 * pixel width for each group, and returns every group whose per-child width
 * falls below STACK_THRESHOLD.
 *
 * Dummy nodes (node.isDummy === true) are excluded from grouping — they only
 * occupy flex space as lane-holders and are not candidates for stacking.
 *
 * A node that lists multiple prevIds contributes to a separate group for each
 * parent.  This correctly handles DAG merges: each parent independently "owns"
 * a horizontal slice, so a shared child can be cramped on one parent's side
 * but not another's.
 *
 * A row with zero or one real node is never cramped (no side-by-side layout
 * exists to collapse), so an empty array is returned immediately.
 *
 * @param {Array<Object>} rowNodes
 *   One inner array from computeLevels() — may contain real nodes and/or
 *   dummy objects ({ isDummy: true, sourceId, targetId }).
 *
 * @param {number} containerWidth
 *   Current pixel width of the .map-flow container, as measured from the DOM
 *   (e.g. via ResizeObserver or getBoundingClientRect).
 *
 * @returns {Array<{
 *   parentId:      string | null,
 *   children:      Array<Object>,
 *   perChildWidth: number
 * }>}
 *   One entry per cramped group.  parentId is null for the synthetic group
 *   that collects root-level nodes (no prevIds).  Returns an empty array when
 *   no group is cramped.
 */
export function identifyCrampedGroups(rowNodes, containerWidth) {
  const realNodes = rowNodes.filter(n => !n.isDummy);

  // A row with one or zero real nodes has nothing side-by-side to collapse.
  if (realNodes.length <= 1) return [];

  // Collect the unique parent IDs referenced across this row.
  // Using a Set ensures each parent is counted exactly once even when several
  // children share the same predecessor.
  const parentIds = new Set();
  realNodes.forEach(n => {
    if (n.prevIds && n.prevIds.length > 0) {
      n.prevIds.forEach(pid => parentIds.add(pid));
    } else {
      parentIds.add(null); // root-level nodes share a synthetic null group
    }
  });

  // Divide the container equally among all parent groups.
  const perGroupWidth = containerWidth / parentIds.size;

  const crampedGroups = [];

  parentIds.forEach(pid => {
    // Each group's children are the real nodes that list this parent.
    const children = realNodes.filter(n =>
      pid === null
        ? (!n.prevIds || n.prevIds.length === 0)
        : (n.prevIds || []).includes(pid)
    );

    if (children.length === 0) return;

    const perChildWidth = perGroupWidth / children.length;

    if (perChildWidth < STACK_THRESHOLD) {
      crampedGroups.push({ parentId: pid, children, perChildWidth });
    }
  });

  return crampedGroups;
}
