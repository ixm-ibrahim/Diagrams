/* Phase 13.75: drag an axis line to pan its min/max window.
 *
 * ===========================================================================
 * !!! DISABLED — DO NOT REMOVE !!!
 *
 * Round 5 of Phase 13.75: the canonical pan/zoom UI moved into the
 * dedicated "Axes" panel (src/ui/axis-controls.js). Per the user, the
 * 3D-canvas axis-drag affordance is intentionally turned off — it
 * conflicts with camera orbit, the hover dot was unreliable, and the
 * panel's Pan/Zoom buttons are now the single discoverable entry
 * point. The code below is retained verbatim so we can revive it
 * cheaply if the panel UX ever falls short.
 *
 * Behavior here is gated by a single early-return in the pointerdown
 * handler (search for "DISABLED"). The hover-dot DOM is still created,
 * but never shown because the pointermove pickAxis path is unreached.
 *
 * To re-enable: delete the DISABLED early-return in the pointerdown
 * listener. Nothing else has changed in this file.
 * ===========================================================================
 *
 * Pointer-down on (or near) an axis line freezes the camera orbit,
 * captures the start state, and switches the cursor. While dragging,
 * the mouse delta is projected onto the axis's screen-space direction
 * and converted into a data-space pan (signed by orientation so
 * dragging toward the tip shifts the visible window toward the tip's
 * data end). Pointer-up restores camera control.
 *
 * Scale (perpendicular drag) isn't wired yet — the existing axis-picker
 * popover handles explicit range edits, and a single-affordance pan is
 * easier to learn. Add a scroll-to-scale variant later if needed.
 *
 * The handler registers in the capture phase so it can pre-empt
 * OrbitControls' bubble-phase listener; on a successful axis hit it
 * stops propagation and disables `controls.enabled` for the duration.
 */

// DISABLED: see top-of-file banner. Flip to false to re-enable the
// 3D-canvas axis-drag behavior.
const AXIS_LINE_DRAG_DISABLED = true;

import * as THREE from 'three';
import { AXIS_DIRS, AXIS_LEN, AXIS_COLOR_VARS } from './axes.js';
import { pointerNDC, worldToClient } from './pointer-math.js';
import { readCssString } from './setup.js';

const RAYCAST_LINE_THRESHOLD = 0.04;
const MIN_SCREEN_AXIS_LEN_PX = 10;

/* Phase 13.75 refinement: pick a clean step size for a given range so
 * the pan snaps to familiar increments. Aim for ~1% of range, then
 * round down to the nearest power of 10:
 *   range 100   → step 1
 *   range 1000  → step 10
 *   range 30000 → step 100
 *   range 1     → step 0.01
 */
export function panStep(range) {
  if (!(range > 0) || !Number.isFinite(range)) return 0;
  const exp = Math.floor(Math.log10(range) - 2);
  return Math.pow(10, exp);
}

export function attachAxisDrag({
  renderer, getCamera, controls, getAxesGroup, state,
}) {
  const dom = renderer.domElement;
  const raycaster = new THREE.Raycaster();
  raycaster.params.Line = { threshold: RAYCAST_LINE_THRESHOLD };
  const pointer = new THREE.Vector2();

  let dragging = null;
  let hoverIdx = -1;

  // Phase 13.75 refinement: a colored dot DOM element that follows the
  // cursor while over an axis line. The grab cursor was unreliable —
  // browsers sometimes drop cursor changes during fast hover transits.
  // The dot gives a positive visual confirmation, colored by which
  // axis is being hovered.
  const hoverDot = document.createElement('div');
  hoverDot.className = 'axis-hover-dot';
  hoverDot.hidden = true;
  document.body.appendChild(hoverDot);

  function showHoverDot(idx, clientX, clientY) {
    const varName = AXIS_COLOR_VARS[idx];
    if (varName) {
      hoverDot.style.background = readCssString(varName, '#888');
    }
    hoverDot.style.left = `${clientX}px`;
    hoverDot.style.top  = `${clientY}px`;
    hoverDot.hidden = false;
  }
  function hideHoverDot() {
    hoverDot.hidden = true;
  }

  function setPointerFromEvent(ev) {
    pointerNDC(ev, dom, pointer);
  }

  function axisLineObjects() {
    const group = getAxesGroup ? getAxesGroup() : null;
    if (!group) return [];
    const out = [];
    for (const child of group.children) {
      if (child.name === 'axis-x') out.push({ obj: child, idx: 0 });
      if (child.name === 'axis-y') out.push({ obj: child, idx: 1 });
      if (child.name === 'axis-z') out.push({ obj: child, idx: 2 });
    }
    return out;
  }

  function pickAxis(ev) {
    setPointerFromEvent(ev);
    const lines = axisLineObjects();
    if (lines.length === 0) return -1;
    raycaster.setFromCamera(pointer, getCamera());
    const hits = raycaster.intersectObjects(lines.map(l => l.obj), false);
    if (hits.length === 0) return -1;
    const hit = lines.find(l => l.obj === hits[0].object);
    return hit ? hit.idx : -1;
  }

  function screenAxisGeom(axisIdx) {
    const cam = getCamera();
    const origin = worldToClient(new THREE.Vector3(0, 0, 0), cam, dom);
    const tip    = worldToClient(AXIS_DIRS[axisIdx].clone().multiplyScalar(AXIS_LEN), cam, dom);
    const dx = tip.x - origin.x;
    const dy = tip.y - origin.y;
    const len = Math.hypot(dx, dy);
    return { dx, dy, len };
  }

  // --- Drag ---

  dom.addEventListener('pointerdown', (ev) => {
    // DISABLED — see banner at top of file. Pan/zoom now lives in the
    // axis-controls panel. Keep the rest of the handler intact so it
    // can be revived by flipping AXIS_LINE_DRAG_DISABLED to false.
    if (AXIS_LINE_DRAG_DISABLED) return;
    // Only primary button / touch / pen.
    if (ev.button !== 0 && ev.pointerType === 'mouse') return;
    const idx = pickAxis(ev);
    if (idx === -1) return;
    const axes = state.get('axes') || [];
    const axis = axes[idx];
    if (!axis || !axis.constraint) return;

    dragging = {
      axisIdx: idx,
      startX: ev.clientX,
      startY: ev.clientY,
      startConstraint: { min: axis.constraint.min, max: axis.constraint.max },
      // Capture orientation at drag start; it shouldn't flip mid-drag.
      orientation: axis.orientation || 'ascending',
      pointerId: ev.pointerId,
    };
    if (controls) controls.enabled = false;
    try { dom.setPointerCapture(ev.pointerId); } catch { /* ignore */ }
    dom.style.cursor = 'grabbing';
    ev.preventDefault();
    ev.stopImmediatePropagation();
  }, { capture: true });

  dom.addEventListener('pointermove', (ev) => {
    // DISABLED — see banner at top of file. Skip the hover affordance
    // since the underlying drag is off; otherwise users would see the
    // grab cursor / dot but pressing wouldn't do anything.
    if (AXIS_LINE_DRAG_DISABLED && !dragging) return;
    if (!dragging) {
      // Hover affordance: cursor flips to grab over an axis AND a
      // colored dot follows the cursor (the cursor change alone isn't
      // always reliable across browsers).
      if (ev.buttons === 0) {
        const idx = pickAxis(ev);
        if (idx !== -1) {
          dom.style.cursor = 'grab';
          showHoverDot(idx, ev.clientX, ev.clientY);
        } else if (hoverIdx !== -1) {
          dom.style.cursor = '';
          hideHoverDot();
        }
        hoverIdx = idx;
      }
      return;
    }
    // Phase 13.75 refinement: keep the dot on the cursor while dragging
    // so it visibly follows along the axis instead of freezing in place.
    showHoverDot(dragging.axisIdx, ev.clientX, ev.clientY);
    const geom = screenAxisGeom(dragging.axisIdx);
    if (!Number.isFinite(geom.len) || geom.len < MIN_SCREEN_AXIS_LEN_PX) {
      // Axis is edge-on to the camera; can't sensibly pan along it.
      return;
    }
    const ndx = geom.dx / geom.len; // unit screen-x along axis
    const ndy = geom.dy / geom.len; // unit screen-y along axis
    const mouseDx = ev.clientX - dragging.startX;
    const mouseDy = ev.clientY - dragging.startY;
    const parallelPx = mouseDx * ndx + mouseDy * ndy;
    const range = dragging.startConstraint.max - dragging.startConstraint.min;
    let dataDelta = parallelPx * (range / geom.len);

    // Sign convention: dragging toward the tip of the axis should
    // shift the visible window toward whatever data value the tip
    // currently shows. With orientation='ascending' the tip = max
    // value, so a +parallelPx (toward tip) increases min and max.
    // With orientation='descending' the tip = min value, so it
    // decreases instead.
    if (dragging.orientation === 'descending') dataDelta = -dataDelta;

    // Phase 13.75 refinement: snap the pan to a round step (~1% of
    // range, rounded to a power of 10) so values land on familiar
    // increments — range 100 → step 1, 1000 → 10, 30000 → 100, etc.
    const step = panStep(range);
    if (step > 0) dataDelta = Math.round(dataDelta / step) * step;

    const axes = state.get('axes').map((a, i) => {
      if (i !== dragging.axisIdx) return a;
      return {
        ...a,
        constraint: {
          min: dragging.startConstraint.min + dataDelta,
          max: dragging.startConstraint.max + dataDelta,
        },
      };
    });
    state.set({ axes });
    ev.preventDefault();
    ev.stopImmediatePropagation();
  }, { capture: true });

  function endDrag(ev) {
    if (!dragging) return;
    try { dom.releasePointerCapture(dragging.pointerId); } catch { /* ignore */ }
    if (controls) controls.enabled = true;
    dom.style.cursor = '';
    hoverIdx = -1;
    hideHoverDot();
    dragging = null;
    if (ev) {
      ev.preventDefault();
      ev.stopImmediatePropagation();
    }
  }
  dom.addEventListener('pointerleave', hideHoverDot);
  dom.addEventListener('pointerup',     endDrag, { capture: true });
  dom.addEventListener('pointercancel', endDrag, { capture: true });
}
