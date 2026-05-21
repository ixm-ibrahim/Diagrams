/* Hover + click picking for the ingredient InstancedMesh.
 *
 * The raycaster runs on every pointermove and resolves to an instance id;
 * the matching ingredient's id flows into state.hoveredIngredientId, and points.js does
 * the visual hover scale via setHover(index). Click (no drag, no axis sprite
 * under pointer) commits the hovered ingredient into state.selectedIngredientId. Click
 * on empty canvas clears the selection — mirrors the axis-picker's
 * empty-canvas dismiss so both panels feel consistent.
 *
 * Sprite hits take priority. The axis-picker registers its handlers first,
 * so on a sprite click we skip ingredient updates and let the picker open. Cursor
 * over a ingredient sphere is also "pointer", layered on top of the sprite cursor
 * write — last move wins, and both intents map to the same cursor.
 *
 * Tooltip: floating pill near the cursor on mouse/pen, anchored above the
 * sphere's projected screen position on touch (where the finger occludes the
 * sphere). Hover state is cleared on pointerleave / pointercancel and on
 * touch release so a tap doesn't leave a phantom hover behind.
 *
 * Phase 40.5: a click that resolves to MULTIPLE candidate dots along the
 * ray (within RAY_CLUSTER_DIST of the front hit) opens a disambiguation
 * menu instead of selecting the front hit blindly. The menu is rendered
 * by ui/pick-menu.js — picking.js just gathers the candidate list and
 * hands it off via `onMultiHit`.
 */

import * as THREE from 'three';
import { inactiveReasons } from '../core/inactive-reasons.js';
import { scaleForItem } from '../core/unit.js';

// Phase 40.5: hits whose ray-distance is within RAY_CLUSTER_DIST of the
// nearest hit count as "overlapping" for disambiguation purposes. Tuned
// so a near-coincident pair (different ingredients on top of each
// other) triggers the menu, but two clearly-separated dots along a
// long view ray don't both qualify.
const RAY_CLUSTER_DIST = 0.18;
const MAX_PICK_CANDIDATES = 8;

export function attachPicking({
  renderer,
  getCamera,
  getPoints,
  getIngredients,
  getAxisNameSprites,
  state,
  ranges = null,
  onMultiHit = null,
}) {
  const dom = renderer.domElement;
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();

  const tooltip = document.createElement('div');
  tooltip.className = 'ingredient-tooltip';
  tooltip.setAttribute('role', 'tooltip');
  tooltip.hidden = true;
  document.body.appendChild(tooltip);

  let hoveredIndex = -1;
  let lastPointerType = 'mouse';
  let lastClientX = 0;
  let lastClientY = 0;

  function setPointer(ev) {
    const rect = dom.getBoundingClientRect();
    pointer.x =  ((ev.clientX - rect.left) / rect.width)  * 2 - 1;
    pointer.y = -((ev.clientY - rect.top)  / rect.height) * 2 + 1;
    lastClientX = ev.clientX;
    lastClientY = ev.clientY;
    if (ev.pointerType) lastPointerType = ev.pointerType;
  }

  function pickFood() {
    const points = getPoints();
    if (!points || !points.mesh) return -1;
    raycaster.setFromCamera(pointer, getCamera());
    const hits = raycaster.intersectObject(points.mesh, false);
    if (hits.length === 0) return -1;
    // Skip hidden (scale-0) instances — they still raycast against the
    // base-radius sphere geometry even though they paint at zero scale.
    for (const hit of hits) {
      const id = hit.instanceId;
      if (typeof id !== 'number') continue;
      const ingredient = getIngredients()?.[id];
      if (!ingredient) continue;
      return id;
    }
    return -1;
  }

  /* Phase 40.5: collect every instance along the ray, deduped by
   * instanceId, with cluster filtering. Returns an array of
   * { index, ingredient, distance } sorted near→far. */
  function pickAllAtPointer() {
    const points = getPoints();
    if (!points || !points.mesh) return [];
    raycaster.setFromCamera(pointer, getCamera());
    const hits = raycaster.intersectObject(points.mesh, false);
    if (hits.length === 0) return [];
    const ingredients = getIngredients() || [];
    const seen = new Set();
    const out = [];
    for (const hit of hits) {
      const id = hit.instanceId;
      if (typeof id !== 'number') continue;
      if (seen.has(id)) continue;
      const ingredient = ingredients[id];
      if (!ingredient) continue;
      seen.add(id);
      out.push({ index: id, ingredient, distance: hit.distance });
      if (out.length >= MAX_PICK_CANDIDATES) break;
    }
    if (out.length === 0) return out;
    const nearest = out[0].distance;
    return out.filter(h => (h.distance - nearest) <= RAY_CLUSTER_DIST);
  }

  function pickSprite() {
    const sprites = getAxisNameSprites ? getAxisNameSprites() : null;
    if (!sprites || sprites.length === 0) return null;
    // Phase 13.5 round 6: three.js's raycaster doesn't walk parent
    // visibility — when axisLabelsVisible=false, the sprites render
    // hidden but they'd still intercept clicks. Filter them out by
    // walking the parent chain.
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

  function positionTooltipAtCursor() {
    tooltip.style.left = `${Math.round(lastClientX + 14)}px`;
    tooltip.style.top  = `${Math.round(lastClientY + 14)}px`;
  }

  function positionTooltipAtSphere() {
    const points = getPoints();
    const worldPos = points && points.getInstancePosition(hoveredIndex);
    if (!worldPos) return positionTooltipAtCursor();
    const v = worldPos.clone().project(getCamera());
    const rect = dom.getBoundingClientRect();
    const x = rect.left + (v.x + 1) / 2 * rect.width;
    const y = rect.top  + (1 - (v.y + 1) / 2) * rect.height;
    tooltip.style.left = `${Math.round(x)}px`;
    tooltip.style.top  = `${Math.round(y - 28)}px`;
  }

  function showTooltip(ingredient) {
    // Phase 13.5 round 2: if the sphere is currently inactive (greyed by
    // any active filter), surface the actual reason below the name so the
    // user doesn't have to guess. Reasons are computed against current
    // state on every hover — no cache, but state lookups are O(1).
    // Phase 40 round 11: read the active threshold set + apply the
    // per-serving scale so the tooltip's "outside threshold" reason
    // matches what the table/detail panel show.
    const unit = state.get('nutrientUnit') || '100g';
    const thresholds = unit === 'serving'
      ? (state.get('thresholdsServing') || state.get('thresholds'))
      : state.get('thresholds');
    const scale = scaleForItem(ingredient, unit);
    const reasons = inactiveReasons(ingredient, {
      ingredientFilter: state.get('ingredientFilter'),
      thresholds,
      thresholdMode:    state.get('thresholdMode'),
      restrictions:     state.get('restrictions') || [],
      ranges,
      nutrientScale: scale,
      nutrientUnit:  unit,
    });

    if (reasons.length === 0) {
      tooltip.textContent = ingredient.name;
    } else {
      tooltip.innerHTML = `
        <div class="ingredient-tooltip-name">${escapeHtml(ingredient.name)}</div>
        <ul class="ingredient-tooltip-reasons">
          ${reasons.map(r => `<li>${escapeHtml(r)}</li>`).join('')}
        </ul>
      `;
    }
    tooltip.hidden = false;
    if (lastPointerType === 'touch') positionTooltipAtSphere();
    else positionTooltipAtCursor();
  }

  function escapeHtml(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function clearHover() {
    const hadHover = hoveredIndex !== -1;
    hoveredIndex = -1;
    const points = getPoints();
    if (points) points.setHover(-1);
    tooltip.hidden = true;
    if (hadHover && state.get('hoveredIngredientId') !== null) {
      state.set({ hoveredIngredientId: null });
    }
  }

  function updateHover(_ev) {
    if (pickSprite()) {
      if (hoveredIndex !== -1) clearHover();
      return false;
    }
    const idx = pickFood();
    const ingredients = getIngredients();
    if (idx >= 0 && ingredients && ingredients[idx]) {
      const points = getPoints();
      if (idx !== hoveredIndex) {
        hoveredIndex = idx;
        if (points) points.setHover(idx);
        state.set({ hoveredIngredientId: ingredients[idx].id });
      }
      showTooltip(ingredients[idx]);
      return true;
    }
    if (hoveredIndex !== -1) clearHover();
    return false;
  }

  let downX = 0, downY = 0, isDrag = false;
  const DRAG_THRESHOLD_PX = 4;

  dom.addEventListener('pointerdown', (ev) => {
    downX = ev.clientX; downY = ev.clientY; isDrag = false;
    setPointer(ev);
    updateHover(ev);
  });

  dom.addEventListener('pointermove', (ev) => {
    if (ev.buttons !== 0 &&
        (Math.abs(ev.clientX - downX) > DRAG_THRESHOLD_PX ||
         Math.abs(ev.clientY - downY) > DRAG_THRESHOLD_PX)) {
      isDrag = true;
      // A drag is camera-rotate territory; suppress hover/tooltip so the
      // scene isn't flickering names as the user spins around.
      if (hoveredIndex !== -1) clearHover();
      return;
    }
    setPointer(ev);
    const hovering = updateHover(ev);
    if (hovering) dom.style.cursor = 'pointer';
  });

  dom.addEventListener('pointerup', (ev) => {
    if (isDrag) return;
    setPointer(ev);
    // Sprite clicks are owned by the axis-picker; leave them alone.
    if (pickSprite()) return;
    const candidates = pickAllAtPointer();
    if (candidates.length === 0) {
      if (state.get('selectedIngredientId') !== null) {
        state.set({ selectedIngredientId: null });
      }
    } else if (candidates.length === 1 || !onMultiHit) {
      state.set({ selectedIngredientId: candidates[0].ingredient.id });
    } else {
      // Phase 40.5: more than one dot under the click — defer to the
      // pick-menu so the user can disambiguate. Hide the hover tooltip
      // while the menu is open; pick-menu will drive hoveredIngredientId
      // for preview.
      tooltip.hidden = true;
      onMultiHit(candidates, { clientX: ev.clientX, clientY: ev.clientY });
    }
    if (ev.pointerType === 'touch') clearHover();
  });

  dom.addEventListener('pointerleave', clearHover);
  dom.addEventListener('pointercancel', clearHover);

  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && state.get('selectedIngredientId') !== null) {
      state.set({ selectedIngredientId: null });
    }
  });

  // The instance id is only meaningful against the current dataset. When
  // the view level changes, points.js rebuilds, and the previous index
  // points at the wrong (or no) ingredient — clear and let pointermove rebuild.
  state.subscribe(s => s.viewLevel, () => clearHover());

  return { clearHover };
}
