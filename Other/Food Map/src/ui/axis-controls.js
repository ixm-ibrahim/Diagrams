/* Phase 13.75 refinement: manual axis controls panel.
 *
 * Sits next to the legend in the bottom-right corner. For each of the
 * 3 active axes (and Phase 40.6's optional Size axis), renders:
 *   - The axis name as a button — click to open the axis-picker popover
 *     (same as clicking the floating axis-name sprite in the 3D scene).
 *   - Current min – max display.
 *   - A Pan button — pointerdown enters drag mode, mouse Y delta pans
 *     the constraint window. Cursor flips to the vertical double-arrow
 *     (ns-resize) so it's visible which direction matters.
 *   - A Zoom button — same UX, mouse Y delta scales the range around
 *     its midpoint. On release the new min/max snap to the step size
 *     implied by the post-zoom range, so values land on familiar
 *     round numbers (10s of kcal, 0.1g, etc.).
 *   - A ↻ reset button — restores the dataset envelope, matching the
 *     behavior of the axis-picker popover's "Reset to full range".
 *
 * A footer button applies the current axis windows as nutrient
 * thresholds (Phase 40.11: relabeled "Filter food by axis ranges" so
 * the affordance reads clearly).
 *
 * Phase 40.6: a fourth, collapsible "Size" row maps a nutrient to dot
 * radius. Off by default; when on, the row inherits the same controls
 * as X/Y/Z. Dots clamp to MIN/MAX radius outside the constraint window.
 *
 * The panel itself is collapsible — same pattern as the legend, with a
 * close button in the header that shrinks it to a "Axes" pill which
 * re-expands on click. Persisted via state.axisControlsOpen.
 */

import { NUTRIENT_META, NUTRIENT_FIELDS } from '../data/schema.js';
import { panStep } from '../scene/axis-drag.js';

// How aggressively pan/zoom drag respond to mouse delta. Tuned so a
// natural hand movement (~150 px) traverses a useful amount of range.
const PAN_PIXELS_PER_RANGE = 200;   // 200 px of drag = one full range slide
const ZOOM_PIXELS_PER_DOUBLE = 220; // 220 px of drag = range halves or doubles

// Drag-vs-click discrimination: how many pixels of pointer movement
// before we commit a Zoom-button press to a drag. Below this, releasing
// the button opens the zoom-anchor dropdown instead.
const ZOOM_DRAG_THRESHOLD_PX = 4;

const ZOOM_ANCHOR_OPTIONS = [
  { key: 'left',   label: 'From left',   hint: 'min stays put' },
  { key: 'center', label: 'From center', hint: 'expand both sides' },
  { key: 'right',  label: 'From right',  hint: 'max stays put' },
];

function zoomAnchor(state) {
  const v = state.get('zoomAnchor');
  return (v === 'left' || v === 'right') ? v : 'center';
}

export function mountAxisControls(root, { state, openAxisPicker, getAxisDefault, getSizeAxisDefault, onFitToVisible }) {
  if (!root) return;
  root.classList.add('axis-controls');
  root.removeAttribute('hidden');

  function isOpen() {
    return state.get('axisControlsOpen') !== false;
  }

  function render() {
    // Any open zoom-anchor menu references a button in the current DOM
    // — re-rendering would orphan it.
    closeZoomMenu();
    if (!isOpen()) {
      renderCollapsed();
      return;
    }
    root.classList.remove('is-collapsed');

    const axes = state.get('axes') || [];
    const axisLabels = ['X', 'Y', 'Z'];
    const rowsHtml = axes.map((axis, i) => {
      if (!axis) return '';
      const meta = NUTRIENT_META[axis.nutrient] || { label: axis.nutrient, format: v => `${v}` };
      const c = axis.constraint || { min: 0, max: 1 };
      return `
        <div class="axis-row" data-axis="${i}">
          <div class="axis-row-top">
            <span class="axis-row-tag" data-axis-color="${axisLabels[i].toLowerCase()}">${axisLabels[i]}</span>
            <button type="button" class="axis-row-name" data-action="open-picker"
                    title="Change which nutrient is on this axis">${escapeHtml(meta.label)}</button>
            <button type="button" class="btn btn-ghost axis-row-pan" data-action="pan"
                    title="Hold and drag to pan">Pan</button>
            <button type="button" class="btn btn-ghost axis-row-zoom" data-action="zoom"
                    title="Hold and drag to zoom — click for anchor options"
                    aria-haspopup="menu">Zoom <span class="axis-row-zoom-caret" aria-hidden="true">▾</span></button>
          </div>
          <div class="axis-row-bottom">
            <span class="axis-row-range muted">
              ${escapeHtml(meta.format(c.min))} – ${escapeHtml(meta.format(c.max))}
            </span>
            <button type="button" class="btn btn-ghost axis-row-reset" data-action="reset"
                    title="Reset to default range">
              <span aria-hidden="true">↻</span>
            </button>
          </div>
        </div>
      `;
    }).join('');

    root.innerHTML = `
      <div class="axis-controls-header">
        <strong class="axis-controls-title">Axes</strong>
        <div class="axis-controls-header-actions">
          <button type="button" class="axis-controls-reset-all" data-action="reset-all"
                  title="Reset every axis's min/max — X, Y, Z, and Size — to defaults">
            <span aria-hidden="true">↻</span> Reset all
          </button>
          <button type="button" class="axis-controls-close" data-action="close"
                  title="Collapse">×</button>
        </div>
      </div>
      ${rowsHtml}
      ${sizeAxisRowHtml()}
      <div class="axis-controls-footer">
        <button type="button" class="btn axis-controls-fit" data-action="fit-visible"
                title="Zoom each axis to fit the currently-visible dots — handy for inspecting a cluster after applying filters">
          <span aria-hidden="true">⤢</span> Fit visible
        </button>
        <button type="button" class="btn axis-controls-capture" data-action="capture-thresholds"
                title="Copies each axis's current min/max into the nutrient thresholds filter">
          Filter by axis ranges
        </button>
      </div>
    `;

    wireRows();
    wireSizeAxis();
  }

  function renderCollapsed() {
    root.classList.add('is-collapsed');
    root.innerHTML = `<button class="axis-controls-expand" type="button">Axes</button>`;
    root.querySelector('.axis-controls-expand').addEventListener('click', () => {
      state.set({ axisControlsOpen: true });
    });
  }

  /* Phase 40.6: Size axis row. Collapsed = header + enable toggle. Expanded
   * = nutrient picker, range display, pan/zoom/reset matching X/Y/Z.
   * A short blurb sits above the row in both states so the user
   * understands what "Size" actually does before they enable it. */
  function sizeAxisRowHtml() {
    const sz = state.get('sizeAxis') || { enabled: false, nutrient: null, constraint: null };
    const enabled = !!sz.enabled;
    const blurb = `
      <p class="axis-row-size-blurb muted">
        4th axis — nutrient → dot size (clamped to range).
      </p>
    `;
    if (!enabled) {
      return `
        ${blurb}
        <div class="axis-row axis-row-size axis-row-size-collapsed" data-axis="size">
          <div class="axis-row-top">
            <span class="axis-row-tag axis-row-size-tag">Size</span>
            <span class="axis-row-name axis-row-size-disabled muted">off</span>
            <button type="button" class="btn btn-ghost axis-row-size-toggle"
                    data-action="size-enable" title="Enable the size axis">Enable</button>
          </div>
        </div>
      `;
    }
    const nutrient = sz.nutrient || 'fat';
    const constraint = sz.constraint || { min: 0, max: 100 };
    const meta = NUTRIENT_META[nutrient] || { label: nutrient, format: v => `${v}` };
    const nutrientOptions = NUTRIENT_FIELDS.map(n =>
      `<option value="${escapeAttr(n)}" ${n === nutrient ? 'selected' : ''}>${escapeHtml(NUTRIENT_META[n].label)}</option>`
    ).join('');
    return `
      ${blurb}
      <div class="axis-row axis-row-size" data-axis="size">
        <div class="axis-row-top">
          <span class="axis-row-tag axis-row-size-tag">Size</span>
          <select class="axis-row-size-select" aria-label="Size axis nutrient">
            ${nutrientOptions}
          </select>
          <button type="button" class="btn btn-ghost axis-row-pan" data-action="size-pan"
                  title="Hold and drag to pan">Pan</button>
          <button type="button" class="btn btn-ghost axis-row-zoom" data-action="size-zoom"
                  title="Hold and drag to zoom — click for anchor options"
                  aria-haspopup="menu">Zoom <span class="axis-row-zoom-caret" aria-hidden="true">▾</span></button>
        </div>
        <div class="axis-row-bottom">
          <span class="axis-row-range muted">
            ${escapeHtml(meta.format(constraint.min))} – ${escapeHtml(meta.format(constraint.max))}
          </span>
          <button type="button" class="btn btn-ghost axis-row-reset" data-action="size-reset"
                  title="Reset to default range">
            <span aria-hidden="true">↻</span>
          </button>
          <button type="button" class="btn btn-ghost axis-row-size-toggle"
                  data-action="size-disable" title="Turn the size axis off">Disable</button>
        </div>
      </div>
    `;
  }

  function wireRows() {
    root.querySelectorAll('.axis-row').forEach(rowEl => {
      const axisKey = rowEl.dataset.axis;
      if (axisKey === 'size') return; // size handled in wireSizeAxis
      const axisIdx = +axisKey;
      rowEl.querySelector('[data-action="open-picker"]').addEventListener('click', (ev) => {
        if (typeof openAxisPicker === 'function') {
          openAxisPicker(axisIdx, ev.currentTarget);
        }
      });
      const panBtn   = rowEl.querySelector('[data-action="pan"]');
      const zoomBtn  = rowEl.querySelector('[data-action="zoom"]');
      const resetBtn = rowEl.querySelector('[data-action="reset"]');
      panBtn.addEventListener('pointerdown',  (ev) => startDrag(ev, axisIdx, 'pan',  panBtn));
      zoomBtn.addEventListener('pointerdown', (ev) =>
        startZoomPress(ev, { kind: 'axis', axisIdx }, zoomBtn));
      resetBtn.addEventListener('click', () => resetAxis(axisIdx));
    });

    const closeBtn = root.querySelector('[data-action="close"]');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => state.set({ axisControlsOpen: false }));
    }

    const resetAllBtn = root.querySelector('[data-action="reset-all"]');
    if (resetAllBtn) {
      resetAllBtn.addEventListener('click', resetAllAxes);
    }

    const capture = root.querySelector('[data-action="capture-thresholds"]');
    if (capture) {
      capture.addEventListener('click', () => {
        // Phase 40 round 11: write to whichever threshold slot is active
        // (per-100g vs per-serving) so the captured ranges show up in the
        // sliders the user is currently looking at.
        const axes = state.get('axes') || [];
        const slotKey = (state.get('nutrientUnit') || '100g') === 'serving'
          ? 'thresholdsServing' : 'thresholds';
        const cur  = state.get(slotKey) || {};
        const next = { ...cur };
        for (const axis of axes) {
          if (!axis || !axis.nutrient || !axis.constraint) continue;
          next[axis.nutrient] = { min: axis.constraint.min, max: axis.constraint.max };
        }
        state.set({ [slotKey]: next });
      });
    }

    /* Tester feedback: after applying filters that cluster every dot
     * into one corner of the cube, the user wants a one-click way to
     * zoom the axes so that cluster fills the whole cube. main.js
     * supplies onFitToVisible because it already has the dataset + the
     * hidden set + the unit-aware scale getter. */
    const fitBtn = root.querySelector('[data-action="fit-visible"]');
    if (fitBtn) {
      fitBtn.addEventListener('click', () => {
        if (typeof onFitToVisible === 'function') onFitToVisible();
      });
    }
  }

  function wireSizeAxis() {
    const row = root.querySelector('.axis-row[data-axis="size"]');
    if (!row) return;
    const enableBtn = row.querySelector('[data-action="size-enable"]');
    const disableBtn = row.querySelector('[data-action="size-disable"]');
    const select = row.querySelector('.axis-row-size-select');
    const panBtn = row.querySelector('[data-action="size-pan"]');
    const zoomBtn = row.querySelector('[data-action="size-zoom"]');
    const resetBtn = row.querySelector('[data-action="size-reset"]');

    if (enableBtn) {
      enableBtn.addEventListener('click', () => {
        // Pick a sensible first nutrient: fat reads as a high-contrast
        // demo on the ingredient view. Falls back to whichever already
        // exists in sizeAxis state.
        const cur = state.get('sizeAxis') || {};
        const nutrient = cur.nutrient || 'fat';
        const constraint = cur.constraint || defaultConstraintForSize(nutrient);
        state.set({ sizeAxis: { enabled: true, nutrient, constraint } });
      });
    }
    if (disableBtn) {
      disableBtn.addEventListener('click', () => {
        const cur = state.get('sizeAxis') || {};
        state.set({ sizeAxis: { ...cur, enabled: false } });
      });
    }
    if (select) {
      select.addEventListener('change', () => {
        const cur = state.get('sizeAxis') || {};
        const nutrient = select.value;
        const constraint = defaultConstraintForSize(nutrient);
        state.set({ sizeAxis: { ...cur, nutrient, constraint } });
      });
    }
    if (panBtn)   panBtn.addEventListener('pointerdown',  (ev) => startSizeDrag(ev, 'pan', panBtn));
    if (zoomBtn)  zoomBtn.addEventListener('pointerdown', (ev) =>
      startZoomPress(ev, { kind: 'size' }, zoomBtn));
    if (resetBtn) resetBtn.addEventListener('click', () => {
      const cur = state.get('sizeAxis') || {};
      if (!cur.nutrient) return;
      state.set({ sizeAxis: { ...cur, constraint: defaultConstraintForSize(cur.nutrient) } });
    });
  }

  function defaultConstraintForSize(nutrient) {
    // Size axis reads raw per-100g ingredient values (it isn't scaled
    // by the per-serving toggle the way position is), so its default
    // window must always come from the per-100g defaults — never from
    // the unit-aware getAxisDefault used by X/Y/Z.
    const getter = typeof getSizeAxisDefault === 'function'
      ? getSizeAxisDefault
      : getAxisDefault;
    if (typeof getter === 'function') {
      const d = getter(nutrient);
      if (d) return { min: d.min, max: d.max };
    }
    const normalized = state.get('normalized');
    const r = normalized && normalized.ranges && normalized.ranges[nutrient];
    return r ? { min: r.min, max: r.max } : { min: 0, max: 1 };
  }

  /* Reset every axis's constraint window — X, Y, Z, and Size (whether
   * Size is currently enabled or not, so re-enabling lands on a clean
   * range). Leaves nutrient choices and the Size enable flag alone;
   * only the min/max windows reset. */
  function resetAllAxes() {
    const axes = state.get('axes') || [];
    const nextAxes = axes.map(axis => {
      if (!axis || !axis.nutrient) return axis;
      let def;
      if (typeof getAxisDefault === 'function') {
        def = getAxisDefault(axis.nutrient);
      }
      if (!def) {
        const normalized = state.get('normalized');
        const range = normalized && normalized.ranges && normalized.ranges[axis.nutrient];
        if (!range) return axis;
        def = { min: range.min, max: range.max };
      }
      return { ...axis, constraint: { min: def.min, max: def.max } };
    });
    state.set({ axes: nextAxes });

    const sz = state.get('sizeAxis') || {};
    if (sz.nutrient) {
      state.set({ sizeAxis: { ...sz, constraint: defaultConstraintForSize(sz.nutrient) } });
    }
  }

  function resetAxis(axisIdx) {
    // Phase 13.75 round 6: reset to the canonical per-nutrient default
    // (calories 0–1000, protein 0–100, etc.) — same target as the
    // axis-picker popover's reset, and matches the first-load axis
    // cube. Falls back to the dataset envelope only if no default is
    // wired in (defensive — the live app always passes one).
    const axes = state.get('axes') || [];
    const axis = axes[axisIdx];
    if (!axis) return;
    let next;
    if (typeof getAxisDefault === 'function') {
      next = getAxisDefault(axis.nutrient);
    } else {
      const normalized = state.get('normalized');
      const range = normalized && normalized.ranges && normalized.ranges[axis.nutrient];
      if (!range) return;
      next = { min: range.min, max: range.max };
    }
    if (!next) return;
    const nextAxes = axes.map((a, i) => i === axisIdx
      ? { ...a, constraint: { min: next.min, max: next.max } } : a);
    state.set({ axes: nextAxes });
  }

  // --- Pointer-capture drag for pan / zoom ---
  //
  // Press the button, the cursor flips to ns-resize (vertical double
  // arrow), and pointer events stay routed to the button thanks to
  // setPointerCapture. clientY delta drives the axis constraint.

  let activeDrag = null;

  function startDrag(ev, axisIdx, mode, button) {
    if (ev.button !== 0 && ev.pointerType === 'mouse') return;
    ev.preventDefault();
    ev.stopPropagation();
    const axes = state.get('axes') || [];
    const axis = axes[axisIdx];
    if (!axis || !axis.constraint) return;

    activeDrag = {
      kind: 'axis',
      axisIdx,
      mode,
      startConstraint: { min: axis.constraint.min, max: axis.constraint.max },
      orientation: axis.orientation || 'ascending',
      pointerId: ev.pointerId,
      lastY: ev.clientY,
      cumulativeY: 0,
      zoomAnchor: zoomAnchor(state),
      button,
    };

    button.classList.add('is-active');
    document.body.classList.add('axis-drag-locked');
    try { button.setPointerCapture(ev.pointerId); } catch { /* ignore */ }

    button.addEventListener('pointermove',   onDragMove);
    button.addEventListener('pointerup',     endDrag);
    button.addEventListener('pointercancel', endDrag);
    document.addEventListener('keydown',     onKeyDown);
  }

  function startSizeDrag(ev, mode, button) {
    if (ev.button !== 0 && ev.pointerType === 'mouse') return;
    ev.preventDefault();
    ev.stopPropagation();
    const sz = state.get('sizeAxis') || {};
    if (!sz.enabled || !sz.constraint) return;
    activeDrag = {
      kind: 'size',
      mode,
      startConstraint: { min: sz.constraint.min, max: sz.constraint.max },
      orientation: 'ascending',
      pointerId: ev.pointerId,
      lastY: ev.clientY,
      cumulativeY: 0,
      zoomAnchor: zoomAnchor(state),
      button,
    };
    button.classList.add('is-active');
    document.body.classList.add('axis-drag-locked');
    try { button.setPointerCapture(ev.pointerId); } catch { /* ignore */ }
    button.addEventListener('pointermove',   onDragMove);
    button.addEventListener('pointerup',     endDrag);
    button.addEventListener('pointercancel', endDrag);
    document.addEventListener('keydown',     onKeyDown);
  }

  /* Zoom button has dual behavior: a quick click opens the anchor
   * dropdown (Left / Center / Right), a drag does the actual zoom. We
   * defer the visual drag setup (class, locked cursor, pointer capture
   * on the button) until the user's pointer has moved past a small
   * threshold — released-before-moved is treated as a click. */
  function startZoomPress(ev, target, button) {
    if (ev.button !== 0 && ev.pointerType === 'mouse') return;
    ev.preventDefault();
    ev.stopPropagation();

    // Toggle-off: clicking the same Zoom button while its menu is open
    // closes the menu instead of reopening it.
    if (activeZoomMenu && activeZoomMenu.button === button) {
      closeZoomMenu();
      return;
    }

    const startX = ev.clientX;
    const startY = ev.clientY;
    const pid = ev.pointerId;
    let committed = false;

    try { button.setPointerCapture(pid); } catch { /* ignore */ }

    function commit(ev2) {
      committed = true;
      if (target.kind === 'axis') {
        const axes = state.get('axes') || [];
        const axis = axes[target.axisIdx];
        if (!axis || !axis.constraint) return false;
        activeDrag = {
          kind: 'axis',
          axisIdx: target.axisIdx,
          mode: 'zoom',
          startConstraint: { min: axis.constraint.min, max: axis.constraint.max },
          orientation: axis.orientation || 'ascending',
          pointerId: pid,
          lastY: startY,
          cumulativeY: 0,
          zoomAnchor: zoomAnchor(state),
          button,
        };
      } else {
        const sz = state.get('sizeAxis') || {};
        if (!sz.enabled || !sz.constraint) return false;
        activeDrag = {
          kind: 'size',
          mode: 'zoom',
          startConstraint: { min: sz.constraint.min, max: sz.constraint.max },
          orientation: 'ascending',
          pointerId: pid,
          lastY: startY,
          cumulativeY: 0,
          zoomAnchor: zoomAnchor(state),
          button,
        };
      }
      button.classList.add('is-active');
      document.body.classList.add('axis-drag-locked');
      document.addEventListener('keydown', onKeyDown);
      return true;
    }

    function onMove(ev2) {
      if (!committed) {
        const dx = Math.abs(ev2.clientX - startX);
        const dy = Math.abs(ev2.clientY - startY);
        if (dx < ZOOM_DRAG_THRESHOLD_PX && dy < ZOOM_DRAG_THRESHOLD_PX) return;
        if (!commit(ev2)) {
          cleanup();
          return;
        }
      }
      onDragMove(ev2);
    }

    function onUp(ev2) {
      // Always clean up our own listeners — endDrag only knows about
      // its own (startDrag) set, not the ones startZoomPress installed.
      cleanup();
      if (committed) {
        endDrag(ev2);
      } else {
        openZoomMenu(button, target);
      }
    }

    function cleanup() {
      button.removeEventListener('pointermove',   onMove);
      button.removeEventListener('pointerup',     onUp);
      button.removeEventListener('pointercancel', onUp);
      try { button.releasePointerCapture(pid); } catch { /* ignore */ }
    }

    button.addEventListener('pointermove',   onMove);
    button.addEventListener('pointerup',     onUp);
    button.addEventListener('pointercancel', onUp);
  }

  /* Tiny popover menu anchored to the Zoom button. Picking an option
   * updates state.zoomAnchor (persisted) and closes. The next zoom
   * drag — including subsequent drags from the same or other axis
   * rows — uses the new anchor. */
  let activeZoomMenu = null;
  function openZoomMenu(button, target) {
    closeZoomMenu();
    const current = zoomAnchor(state);
    const menu = document.createElement('div');
    menu.className = 'zoom-anchor-menu';
    menu.setAttribute('role', 'menu');
    menu.innerHTML = `
      <div class="zoom-anchor-menu-title">Zoom from…</div>
      ${ZOOM_ANCHOR_OPTIONS.map(opt => `
        <button type="button" class="zoom-anchor-option ${opt.key === current ? 'is-current' : ''}"
                data-anchor="${opt.key}" role="menuitemradio"
                aria-checked="${opt.key === current ? 'true' : 'false'}">
          <span class="zoom-anchor-check" aria-hidden="true">${opt.key === current ? '✓' : ''}</span>
          <span class="zoom-anchor-label">${escapeHtml(opt.label)}</span>
          <span class="zoom-anchor-hint muted">${escapeHtml(opt.hint)}</span>
        </button>
      `).join('')}
    `;
    document.body.appendChild(menu);
    positionZoomMenu(menu, button);
    activeZoomMenu = { el: menu, button };

    menu.addEventListener('click', (ev) => {
      const opt = ev.target.closest('[data-anchor]');
      if (!opt) return;
      state.set({ zoomAnchor: opt.dataset.anchor });
      closeZoomMenu();
    });

    setTimeout(() => {
      document.addEventListener('pointerdown', onOutsidePointer, true);
      document.addEventListener('keydown', onMenuKeydown);
    }, 0);
  }

  function positionZoomMenu(menu, button) {
    const rect = button.getBoundingClientRect();
    menu.style.left = '0px';
    menu.style.top  = '0px';
    const w = menu.offsetWidth;
    const h = menu.offsetHeight;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    let left = rect.left - w - 8;
    let top  = rect.top - 4;
    if (left < 8) left = rect.right + 8;
    if (left + w > vw - 8) left = vw - w - 8;
    if (top + h > vh - 8) top = vh - h - 8;
    if (top < 8) top = 8;
    menu.style.left = `${Math.round(left)}px`;
    menu.style.top  = `${Math.round(top)}px`;
  }

  function closeZoomMenu() {
    if (!activeZoomMenu) return;
    document.removeEventListener('pointerdown', onOutsidePointer, true);
    document.removeEventListener('keydown', onMenuKeydown);
    activeZoomMenu.el.remove();
    activeZoomMenu = null;
  }

  function onOutsidePointer(ev) {
    if (!activeZoomMenu) return;
    if (activeZoomMenu.el.contains(ev.target)) return;
    if (activeZoomMenu.button.contains(ev.target)) return;
    closeZoomMenu();
  }

  function onMenuKeydown(ev) {
    if (ev.key === 'Escape') closeZoomMenu();
  }

  function onDragMove(ev) {
    if (!activeDrag) return;
    const dy = ev.clientY - activeDrag.lastY;
    activeDrag.lastY = ev.clientY;
    activeDrag.cumulativeY += dy;
    applyDrag();
  }

  function applyDrag() {
    if (!activeDrag) return;
    const start = activeDrag.startConstraint;
    const startRange = start.max - start.min;
    if (!(startRange > 0)) return;

    const dy = -activeDrag.cumulativeY;

    let next = { ...start };
    if (activeDrag.mode === 'pan') {
      const panFraction = dy / PAN_PIXELS_PER_RANGE;
      let shift = panFraction * startRange;
      if (activeDrag.orientation === 'descending') shift = -shift;
      next = { min: start.min + shift, max: start.max + shift };
    } else if (activeDrag.mode === 'zoom') {
      const factor = Math.pow(2, -dy / ZOOM_PIXELS_PER_DOUBLE);
      const newRange = startRange * factor;
      // Anchor decides which edge stays fixed. 'left' pins min, 'right'
      // pins max, 'center' (default) expands/contracts around the midpoint.
      const anchor = activeDrag.zoomAnchor || 'center';
      if (anchor === 'left') {
        next = { min: start.min, max: start.min + newRange };
      } else if (anchor === 'right') {
        next = { min: start.max - newRange, max: start.max };
      } else {
        const mid = (start.min + start.max) / 2;
        const half = newRange / 2;
        next = { min: mid - half, max: mid + half };
      }
    }

    if (activeDrag.kind === 'size') {
      const sz = state.get('sizeAxis') || {};
      state.set({ sizeAxis: { ...sz, constraint: next } });
      return;
    }
    const axes = state.get('axes') || [];
    const nextAxes = axes.map((a, i) => i === activeDrag.axisIdx
      ? { ...a, constraint: next } : a);
    state.set({ axes: nextAxes });
  }

  function endDrag(ev) {
    if (!activeDrag) return;
    const btn = activeDrag.button;
    const pid = activeDrag.pointerId;
    const wasZoom = activeDrag.mode === 'zoom';
    const drag = activeDrag;

    if (btn) {
      btn.classList.remove('is-active');
      btn.removeEventListener('pointermove',   onDragMove);
      btn.removeEventListener('pointerup',     endDrag);
      btn.removeEventListener('pointercancel', endDrag);
      try { btn.releasePointerCapture(pid); } catch { /* ignore */ }
    }
    document.body.classList.remove('axis-drag-locked');
    document.removeEventListener('keydown', onKeyDown);
    activeDrag = null;

    if (wasZoom) {
      if (drag.kind === 'size') snapZoomedSize();
      else                       snapZoomedAxis(drag.axisIdx);
    }

    render();
    if (ev) {
      ev.preventDefault();
      ev.stopPropagation();
    }
  }

  function snapZoomedAxis(axisIdx) {
    const axes = state.get('axes') || [];
    const axis = axes[axisIdx];
    if (!axis || !axis.constraint) return;
    const c = axis.constraint;
    const range = c.max - c.min;
    if (!(range > 0)) return;
    const step = panStep(range);
    if (!(step > 0)) return;
    const snappedMin = Math.round(c.min / step) * step;
    const snappedMax = Math.round(c.max / step) * step;
    if (!(snappedMax > snappedMin)) return;
    if (snappedMin === c.min && snappedMax === c.max) return;
    const nextAxes = axes.map((a, i) => i === axisIdx
      ? { ...a, constraint: { min: snappedMin, max: snappedMax } } : a);
    state.set({ axes: nextAxes });
  }

  function snapZoomedSize() {
    const sz = state.get('sizeAxis') || {};
    if (!sz.constraint) return;
    const c = sz.constraint;
    const range = c.max - c.min;
    if (!(range > 0)) return;
    const step = panStep(range);
    if (!(step > 0)) return;
    const snappedMin = Math.round(c.min / step) * step;
    const snappedMax = Math.round(c.max / step) * step;
    if (!(snappedMax > snappedMin)) return;
    if (snappedMin === c.min && snappedMax === c.max) return;
    state.set({ sizeAxis: { ...sz, constraint: { min: snappedMin, max: snappedMax } } });
  }

  function onKeyDown(ev) {
    if (ev.key === 'Escape') endDrag();
  }

  // Phase 13.75 round 4: while a pan/zoom drag is active, skip the
  // full re-render — each `state.set({ axes })` from applyDrag would
  // otherwise tear down the very button whose pointer events drive
  // the drag, and the listener would die mid-gesture. Instead, just
  // refresh the range display for the axis being dragged. A full
  // render runs after endDrag to catch up.
  function refreshRangeOnly(axisIdx) {
    const axes = state.get('axes') || [];
    const axis = axes[axisIdx];
    if (!axis) return;
    const meta = NUTRIENT_META[axis.nutrient] || { format: v => `${v}` };
    const c = axis.constraint || { min: 0, max: 1 };
    const row = root.querySelector(`.axis-row[data-axis="${axisIdx}"]`);
    if (!row) return;
    const rangeEl = row.querySelector('.axis-row-range');
    if (rangeEl) rangeEl.textContent = `${meta.format(c.min)} – ${meta.format(c.max)}`;
  }

  function refreshSizeRangeOnly() {
    const sz = state.get('sizeAxis') || {};
    if (!sz.nutrient || !sz.constraint) return;
    const meta = NUTRIENT_META[sz.nutrient] || { format: v => `${v}` };
    const row = root.querySelector('.axis-row[data-axis="size"]');
    if (!row) return;
    const rangeEl = row.querySelector('.axis-row-range');
    if (rangeEl) rangeEl.textContent = `${meta.format(sz.constraint.min)} – ${meta.format(sz.constraint.max)}`;
  }

  /* Tester feedback: when an axis fades out (orthographic snap), its
   * row in this panel greys out so the user knows it's currently
   * unselectable. main.js publishes state.hiddenAxisIndex; we just
   * toggle a class on the matching row. */
  function applyHiddenAxisClass() {
    const hidden = state.get('hiddenAxisIndex');
    for (const rowEl of root.querySelectorAll('.axis-row')) {
      const ax = rowEl.dataset.axis;
      if (ax === 'size') continue;
      const idx = +ax;
      rowEl.classList.toggle('is-faded', idx === hidden);
    }
  }

  function renderAndDecorate() {
    render();
    applyHiddenAxisClass();
  }
  renderAndDecorate();
  state.subscribe(s => s.axes, () => {
    if (activeDrag && activeDrag.kind === 'axis') {
      refreshRangeOnly(activeDrag.axisIdx);
      return;
    }
    renderAndDecorate();
  });
  state.subscribe(s => s.sizeAxis, () => {
    if (activeDrag && activeDrag.kind === 'size') {
      refreshSizeRangeOnly();
      return;
    }
    renderAndDecorate();
  });
  state.subscribe(s => s.axisControlsOpen, renderAndDecorate);
  state.subscribe(s => s.hiddenAxisIndex, applyHiddenAxisClass);
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function escapeAttr(s) { return escapeHtml(s); }
