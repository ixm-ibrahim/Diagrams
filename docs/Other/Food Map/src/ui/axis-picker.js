/* Axis picker.
 *
 * Click an axis-name label ("Calories ▾") in the 3D scene to open a popover
 * next to it. The popover lets the user:
 *   - swap the nutrient bound to that axis (other axes' nutrients are
 *     disabled so each nutrient is used at most once)
 *   - flip the direction (↓ low is best  /  ↑ high is best)
 *   - set a min/max constraint range in raw nutrient units, with a reset
 *     button that pulls the range back to the dataset envelope
 *
 * Changing the nutrient also resets the constraint to the new nutrient's
 * dataset envelope (units would be meaningless otherwise — 100 kcal vs
 * 100 mg sodium are not the same value).
 *
 * The popover closes on Esc, click-outside, or camera move.
 */

import * as THREE from 'three';
import { NUTRIENT_META, NUTRIENT_FIELDS, NUTRIENT_DEFAULTS } from '../data/schema.js';

export function mountAxisPicker({ getCamera, renderer, controls, state, getAxisNameSprites, getAxisDefault }) {
  const dom = renderer.domElement;
  const raycaster = new THREE.Raycaster();
  raycaster.params.Sprite = { threshold: 0 };
  const pointer = new THREE.Vector2();

  const popover = document.createElement('div');
  popover.className = 'axis-picker';
  popover.setAttribute('role', 'dialog');
  popover.setAttribute('aria-label', 'Axis configuration');
  popover.hidden = true;
  document.body.appendChild(popover);

  let openAxisIndex = -1;
  let openSprite = null;
  // When the picker is opened via a DOM anchor (Axes-panel row click)
  // rather than a 3D axis-name sprite, remember the anchor so re-renders
  // and resizes keep the popover next to the clicked button instead of
  // snapping to the 3D label.
  let openAnchorEl = null;

  function spriteToScreen(sprite) {
    const v = sprite.position.clone();
    v.project(getCamera());
    const rect = dom.getBoundingClientRect();
    return {
      x: rect.left + (v.x + 1) / 2 * rect.width,
      y: rect.top  + (1 - (v.y + 1) / 2) * rect.height,
    };
  }

  function fmtNumberInputValue(v) {
    // Show one decimal under 10, integer above. Strip trailing .0 for cleanliness.
    if (typeof v !== 'number' || !Number.isFinite(v)) return '';
    if (Math.abs(v) >= 10) return String(Math.round(v));
    return String(Math.round(v * 10) / 10);
  }

  function renderPopover(axisIndex) {
    const axes = state.get('axes');
    const ranges = state.get('normalized').ranges;
    const current = axes[axisIndex];
    const range = ranges[current.nutrient];
    const constraint = current.constraint ?? { min: range.min, max: range.max };

    const usedByOthers = new Set(
      axes.filter((_, i) => i !== axisIndex).map(a => a.nutrient)
    );

    const unitLong = NUTRIENT_META[current.nutrient].unitLong;
    const unitShort = NUTRIENT_META[current.nutrient].unit;

    popover.innerHTML = `
      <div class="axis-picker-title">Axis ${axisIndex + 1}</div>
      <label class="axis-picker-field">
        <span class="axis-picker-label">Nutrient</span>
        <select class="axis-picker-nutrient input">
          ${NUTRIENT_FIELDS.map(n => {
            const meta = NUTRIENT_META[n];
            const used = usedByOthers.has(n) && n !== current.nutrient;
            const sel  = n === current.nutrient ? ' selected' : '';
            const dis  = used ? ' disabled' : '';
            const suffix = used ? ' — in use' : '';
            return `<option value="${n}"${sel}${dis}>${meta.label} (${meta.unitLong})${suffix}</option>`;
          }).join('')}
        </select>
      </label>
      <div class="axis-picker-row">
        <fieldset class="axis-picker-field axis-picker-orientation">
          <legend class="axis-picker-label">Axis</legend>
          <label class="axis-picker-radio">
            <input type="radio" name="ax-ori" value="ascending"${current.orientation === 'ascending' ? ' checked' : ''}>
            <span>↗ ascending</span>
          </label>
          <label class="axis-picker-radio">
            <input type="radio" name="ax-ori" value="descending"${current.orientation === 'descending' ? ' checked' : ''}>
            <span>↘ descending</span>
          </label>
        </fieldset>
        <fieldset class="axis-picker-field axis-picker-direction">
          <legend class="axis-picker-label">Best when</legend>
          <label class="axis-picker-radio">
            <input type="radio" name="ax-dir" value="min"${current.direction === 'min' ? ' checked' : ''}>
            <span>↓ low</span>
          </label>
          <label class="axis-picker-radio">
            <input type="radio" name="ax-dir" value="max"${current.direction === 'max' ? ' checked' : ''}>
            <span>↑ high</span>
          </label>
        </fieldset>
      </div>
      <fieldset class="axis-picker-field axis-picker-range">
        <legend class="axis-picker-label">Range (${unitLong})</legend>
        <div class="axis-picker-range-row">
          <label>
            <span>Min</span>
            <input type="number" class="axis-picker-range-min input"
                   step="any" inputmode="decimal"
                   value="${fmtNumberInputValue(constraint.min)}">
            <span class="axis-picker-unit muted">${unitShort}</span>
          </label>
          <label>
            <span>Max</span>
            <input type="number" class="axis-picker-range-max input"
                   step="any" inputmode="decimal"
                   value="${fmtNumberInputValue(constraint.max)}">
            <span class="axis-picker-unit muted">${unitShort}</span>
          </label>
        </div>
        <button type="button" class="axis-picker-reset btn btn-ghost"
                title="Reset to dataset range (${fmtNumberInputValue(range.min)}–${fmtNumberInputValue(range.max)} ${unitShort})">
          <span aria-hidden="true">↻</span>
          <span>Reset to full range</span>
        </button>
      </fieldset>
    `;

    popover.querySelector('.axis-picker-nutrient').addEventListener('change', e => {
      const newNutrient = e.target.value;
      // Per-nutrient settings persist across swaps: save the leaving
      // nutrient's full settings, restore the incoming nutrient's.
      const allAxes = state.get('axes');
      const oldAxis = allAxes[axisIndex];
      const oldNutrient = oldAxis.nutrient;
      const prefs = state.get('nutrientPrefs') || {};

      const updatedPrefs = {
        ...prefs,
        [oldNutrient]: {
          direction: oldAxis.direction,
          orientation: oldAxis.orientation,
          constraint: oldAxis.constraint,
        },
      };
      const target = updatedPrefs[newNutrient] || {
        direction: NUTRIENT_DEFAULTS[newNutrient].direction,
        orientation: NUTRIENT_DEFAULTS[newNutrient].orientation,
        constraint: { min: ranges[newNutrient].min, max: ranges[newNutrient].max },
      };

      const newAxes = allAxes.map((a, i) =>
        i === axisIndex ? {
          nutrient: newNutrient,
          direction: target.direction,
          orientation: target.orientation,
          constraint: target.constraint,
        } : a);

      state.set({ nutrientPrefs: updatedPrefs, axes: newAxes });
      reanchorPopover(axisIndex);
    });
    popover.querySelectorAll('input[name="ax-dir"]').forEach(input => {
      input.addEventListener('change', () => {
        if (input.checked) updateAxis(axisIndex, { direction: input.value });
      });
    });
    popover.querySelectorAll('input[name="ax-ori"]').forEach(input => {
      input.addEventListener('change', () => {
        if (input.checked) updateAxis(axisIndex, { orientation: input.value });
      });
    });

    const minInput = popover.querySelector('.axis-picker-range-min');
    const maxInput = popover.querySelector('.axis-picker-range-max');
    function commitRange() {
      const minV = Number(minInput.value);
      const maxV = Number(maxInput.value);
      if (!Number.isFinite(minV) || !Number.isFinite(maxV)) return;
      // Swap if user inverted; keeps the constraint usable instead of yelling.
      const lo = Math.min(minV, maxV);
      const hi = Math.max(minV, maxV);
      updateAxis(axisIndex, { constraint: { min: lo, max: hi } });
    }
    minInput.addEventListener('change', commitRange);
    maxInput.addEventListener('change', commitRange);

    popover.querySelector('.axis-picker-reset').addEventListener('click', () => {
      // Phase 13.75 round 6: reset to the canonical per-nutrient
      // default (e.g. calories 0–1000, protein 0–100) rather than the
      // dataset envelope. The envelope was the original behavior but
      // gave ragged values like 0–902 kcal; defaults keep the axis
      // cube on round numbers and matches first-load.
      const def = typeof getAxisDefault === 'function'
        ? getAxisDefault(current.nutrient)
        : { min: range.min, max: range.max };
      updateAxis(axisIndex, {
        constraint: { min: def.min, max: def.max },
      });
    });
  }

  function updateAxis(axisIndex, patch) {
    const axes = state.get('axes').map((a, i) =>
      i === axisIndex ? { ...a, ...patch } : a);
    state.set({ axes });
    reanchorPopover(axisIndex);
  }

  // Axes rebuild drops our sprite reference. Re-anchor to the freshly-built
  // sprite on the next frame and re-render the popover so its values reflect
  // the committed state. The popover stays open until the user dismisses it
  // (Esc, click-outside, or click on empty canvas).
  function reanchorPopover(axisIndex) {
    requestAnimationFrame(() => {
      if (openAxisIndex !== axisIndex) return;
      if (openAnchorEl) {
        renderPopover(axisIndex);
        positionAtElement(openAnchorEl);
        return;
      }
      const sprites = getAxisNameSprites();
      const newSprite = sprites[axisIndex];
      if (newSprite) {
        openSprite = newSprite;
        renderPopover(axisIndex);
        positionPopover(newSprite);
      }
    });
  }

  function open(axisIndex, sprite) {
    openAxisIndex = axisIndex;
    openSprite = sprite;
    openAnchorEl = null;
    renderPopover(axisIndex);
    popover.hidden = false;
    positionPopover(sprite);
  }

  function positionPopover(sprite) {
    const screen = spriteToScreen(sprite);
    popover.style.left = '0px';
    popover.style.top  = '0px';
    const w = popover.offsetWidth;
    const h = popover.offsetHeight;
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    let left = screen.x + 16;
    let top  = screen.y - h / 2;
    if (left + w > vw - 8) left = screen.x - w - 16;
    if (left < 8) left = 8;
    if (top  + h > vh - 8) top = vh - h - 8;
    if (top  < 8) top = 8;

    popover.style.left = `${Math.round(left)}px`;
    popover.style.top  = `${Math.round(top)}px`;
  }

  function close() {
    if (popover.hidden) return;
    popover.hidden = true;
    openAxisIndex = -1;
    openSprite = null;
    openAnchorEl = null;
  }

  function setPointer(ev) {
    const rect = dom.getBoundingClientRect();
    pointer.x =  ((ev.clientX - rect.left) / rect.width)  * 2 - 1;
    pointer.y = -((ev.clientY - rect.top)  / rect.height) * 2 + 1;
  }

  function spriteUnderPointer() {
    const sprites = getAxisNameSprites();
    if (!sprites || sprites.length === 0) return null;
    // Phase 13.5 round 7: three.js's raycaster doesn't walk ancestor
    // visibility, so an axis-name sprite under labelsGroup.visible=false
    // would still open the picker. Mirror the visibility filter from
    // scene/picking.js so a hidden label is truly inert.
    const visibleSprites = sprites.filter(s => {
      let o = s;
      while (o) {
        if (o.visible === false) return false;
        o = o.parent;
      }
      return true;
    });
    if (visibleSprites.length === 0) return null;
    raycaster.setFromCamera(pointer, getCamera());
    const hits = raycaster.intersectObjects(visibleSprites, false);
    return hits.length ? hits[0].object : null;
  }

  let downX = 0, downY = 0, isDrag = false;
  dom.addEventListener('pointerdown', (ev) => {
    downX = ev.clientX; downY = ev.clientY; isDrag = false;
  });
  dom.addEventListener('pointermove', (ev) => {
    if (ev.buttons !== 0 && (Math.abs(ev.clientX - downX) > 4 || Math.abs(ev.clientY - downY) > 4)) {
      isDrag = true;
    }
    setPointer(ev);
    const sprite = spriteUnderPointer();
    dom.style.cursor = sprite ? 'pointer' : '';
  });
  dom.addEventListener('pointerup', (ev) => {
    if (isDrag) return;
    setPointer(ev);
    const sprite = spriteUnderPointer();
    if (sprite) {
      const axisIndex = sprite.userData?.axisIndex;
      if (typeof axisIndex === 'number') open(axisIndex, sprite);
    } else if (!popover.hidden) {
      close();
    }
  });

  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') close();
  });
  document.addEventListener('pointerdown', (ev) => {
    if (popover.hidden) return;
    if (popover.contains(ev.target)) return;
    if (dom.contains(ev.target)) return;
    close();
  });

  // Keep the popover anchored to its sprite as the camera moves. OrbitControls
  // fires 'change' on every frame while it's animating, including the damping
  // tail after a drag, so the popover tracks naturally.
  if (controls) {
    controls.addEventListener('change', () => {
      if (!popover.hidden && openSprite) positionPopover(openSprite);
    });
  }
  window.addEventListener('resize', () => {
    if (popover.hidden) return;
    if (openAnchorEl) positionAtElement(openAnchorEl);
    else if (openSprite) positionPopover(openSprite);
  });

  // Phase 13.75: open the picker programmatically for a given axis
  // index. If an anchor element is passed (the user clicked the row in
  // the Axes panel), anchor to that DOM element so the popover appears
  // next to what was clicked. Without an anchor (called from another
  // code path that didn't pass one), fall back to the 3D axis-name
  // sprite. If neither is available, do nothing.
  function openForAxis(axisIndex, anchorEl = null) {
    if (typeof axisIndex !== 'number' || axisIndex < 0 || axisIndex > 2) return;
    if (anchorEl) {
      openAxisIndex = axisIndex;
      openSprite = null;
      openAnchorEl = anchorEl;
      renderPopover(axisIndex);
      popover.hidden = false;
      positionAtElement(anchorEl);
      return;
    }
    const sprites = getAxisNameSprites();
    const sprite = sprites && sprites[axisIndex];
    if (sprite) open(axisIndex, sprite);
  }

  function positionAtElement(el) {
    if (!el) return;
    const rect = el.getBoundingClientRect();
    popover.style.left = '0px';
    popover.style.top  = '0px';
    const w = popover.offsetWidth;
    const h = popover.offsetHeight;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    let left = rect.left - w - 12;
    let top  = rect.top + rect.height / 2 - h / 2;
    if (left < 8) left = rect.right + 12;
    if (left + w > vw - 8) left = vw - w - 8;
    if (top  + h > vh - 8) top = vh - h - 8;
    if (top  < 8) top = 8;
    popover.style.left = `${Math.round(left)}px`;
    popover.style.top  = `${Math.round(top)}px`;
  }

  return { close, openForAxis };
}
