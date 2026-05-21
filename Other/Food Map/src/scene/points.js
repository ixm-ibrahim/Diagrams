/* InstancedMesh of ingredient spheres.
 *
 * One geometry, one material, n instances. Per-instance:
 *   color    = vec3(animal, plant, dairy) — pure additive RGB of weights
 *              by default. Phase 6's filter blends toward a neutral gray
 *              for inactive ingredients. Phase 7's Score mode overrides the
 *              color entirely with a green→red gradient mapped from the
 *              per-ingredient score.
 *   position = normalize.js projection through the current axis config.
 *   scale    = staggered fade-in on first load, then 1.0 baseline. Hover
 *              (Phase 5) bumps to HOVER_SCALE.
 *              Phase 40.3: the SELECTED instance pulses (animated scale
 *              oscillation) so the user can see where their focus is in
 *              both the 3D scene and the table.
 *              Phase 40.6: the optional Size axis layers a per-instance
 *              size multiplier on top (clamped to constraint window).
 *              Phase 40.1: items in the HIDDEN set render at scale 0,
 *              hard-filtered out (used by dietary restrictions).
 *
 * State setters (called from main.js as state mutates):
 *   setHover(index)        — Phase 5, single index or -1.
 *   setActiveSet(set|null) — Phase 6/7, ingredients to keep at full color.
 *   setScoreMap(map|null)  — Phase 7 Score mode, per-ingredient gradient.
 *   setHiddenSet(set|null) — Phase 40.1, ids to remove from view (scale 0).
 *   setSelectedId(id|null) — Phase 40.3, drives the pulsing halo.
 *   setSizeAxis({enabled, nutrient, constraint}) — Phase 40.6.
 */

import * as THREE from 'three';
import { normalizeDataset } from '../core/normalize.js';
import { FOOD_GROUPS, FOOD_GROUP_COLORS } from '../data/schema.js';
import { makeScaleGetter, normalizeUnit } from '../core/unit.js';

const SPHERE_RADIUS = 0.018;
const SPHERE_SEGMENTS = [14, 10];
// Phase 13.5 round 2: with ~860 ingredients, a 10ms per-point stagger
// ran the load reveal for ~9 seconds. Cap the total stagger at ~2 seconds
// so the dataset fades in promptly regardless of count.
const FADE_TOTAL_STAGGER_MS = 2000;
const FADE_DURATION_MS = 240;
const HOVER_SCALE = 1.4;
const HOVER_TWEEN_RATE = 0.22;
const TWEEN_EPSILON = 0.001;

const INACTIVE_GRAY = new THREE.Color(0.5, 0.5, 0.5);
const INACTIVE_BLEND = 0.82;
// Phase 13.75: legend-checkbox filtering. Items whose color channel /
// food_group is unchecked render at a smaller scale with a dimmed
// color, distinct from the (full-size, heavily-greyed) threshold
// inactive treatment so the user can tell why something is dimmed.
const COLOR_FILTER_SCALE = 0.35;
const COLOR_FILTER_BLEND = 0.4;

// Phase 40.6: per-instance Size axis multiplier range. The dot's radius
// is lerp(MIN, MAX, t) where t is the clamped normalized position of
// the chosen nutrient inside its constraint window.
const SIZE_AXIS_MIN_MUL = 0.45;
const SIZE_AXIS_MAX_MUL = 2.0;

// Phase 40.3: selection pulse. PULSE_BASE is the average scale; the
// instance oscillates ±PULSE_AMPLITUDE at PULSE_FREQ_HZ. Tuned to be
// visibly alive but not seizure-inducing in dark mode.
const PULSE_BASE      = 1.4;
const PULSE_AMPLITUDE = 0.22;
const PULSE_FREQ_HZ   = 1.6;

// Score-mode gradient endpoints: green at 0 (best — closest to targets),
// red at 1 (worst). Slightly muted so it doesn't blow out against the
// scene's lit material.
const SCORE_GOOD = new THREE.Color(0.30, 0.78, 0.45);
const SCORE_BAD  = new THREE.Color(0.92, 0.36, 0.32);

function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3);
}

export function buildPoints(scene, ingredients, axes, ranges, { animate = true } = {}) {
  const n = ingredients.length;

  const geometry = new THREE.SphereGeometry(SPHERE_RADIUS, SPHERE_SEGMENTS[0], SPHERE_SEGMENTS[1]);
  const material = new THREE.MeshLambertMaterial({ color: 0xffffff });
  const mesh = new THREE.InstancedMesh(geometry, material, n);
  mesh.name = 'ingredient-points';

  // Phase 13.5 round 3: two color schemes.
  //   'rgb'        — additive [animal, plant, dairy] channels (original).
  //   'food_group' — each food_group has a fixed color; multi-group
  //                  aggregates lerp by weight across the 11 colors.
  const originalColorsByScheme = { rgb: new Array(n), food_group: new Array(n) };
  for (let i = 0; i < n; i++) {
    const ing = ingredients[i];
    const [animal, plant, dairy] = ing.group_weights;
    originalColorsByScheme.rgb[i] = new THREE.Color().setRGB(animal, plant, dairy);

    let r = 0, g = 0, b = 0, total = 0;
    if (ing.food_group_weights) {
      // Aggregate (category/meal): weighted sum across food_groups.
      for (const grp of FOOD_GROUPS) {
        const w = ing.food_group_weights[grp];
        if (!(w > 0)) continue;
        const c = FOOD_GROUP_COLORS[grp];
        if (!c) continue;
        r += w * c[0]; g += w * c[1]; b += w * c[2]; total += w;
      }
    } else if (ing.food_group && FOOD_GROUP_COLORS[ing.food_group]) {
      // Individual ingredient: single food_group → its color.
      const c = FOOD_GROUP_COLORS[ing.food_group];
      r = c[0]; g = c[1]; b = c[2]; total = 1;
    }
    if (total > 0) {
      originalColorsByScheme.food_group[i] = new THREE.Color(r / total, g / total, b / total);
    } else {
      originalColorsByScheme.food_group[i] = new THREE.Color(0.5, 0.5, 0.5);
    }
  }
  let colorScheme = 'rgb';
  let originalColors = originalColorsByScheme[colorScheme];

  let activeSet = null;
  let scoreMap = null;
  let colorFilteredSet = null; // Phase 13.75 legend-checkbox filter
  let hiddenSet = null;        // Phase 40.1 hard-filter (restrictions)
  let selectedId = null;       // Phase 40.3 selection pulse
  let selectedIndex = -1;      // resolved from selectedId
  let previewId = null;        // Phase 40 round 2: search-hover preview pulse
  let previewIndex = -1;       // resolved from previewId

  // Phase 40.6 Size axis state
  let sizeAxisEnabled = false;
  let sizeAxisNutrient = null;
  let sizeAxisMin = 0;
  let sizeAxisMax = 1;

  function resolveSelectedIndex() {
    selectedIndex = -1;
    if (!selectedId) return;
    for (let i = 0; i < n; i++) {
      if (ingredients[i].id === selectedId) { selectedIndex = i; return; }
    }
  }
  function resolvePreviewIndex() {
    previewIndex = -1;
    if (!previewId) return;
    for (let i = 0; i < n; i++) {
      if (ingredients[i].id === previewId) { previewIndex = i; return; }
    }
  }
  resolveSelectedIndex();
  resolvePreviewIndex();

  /* Phase 40 round 2: always-on-top overlay meshes for selection and
   * search-preview. depthTest off + high renderOrder so a dot occluded
   * by neighbors still shows its pulse. Each is a plain single-sphere
   * Mesh that mirrors its target instance's position + color, and pulses
   * exactly like the instance would. When inactive, mesh.visible = false. */
  function makeOverlay(name) {
    const m = new THREE.MeshLambertMaterial({
      color: 0xffffff,
      transparent: true,
      depthTest: false,
      depthWrite: false,
    });
    const mesh = new THREE.Mesh(geometry, m);
    mesh.name = name;
    mesh.renderOrder = 999;
    mesh.visible = false;
    mesh.matrixAutoUpdate = false;
    scene.add(mesh);
    return mesh;
  }
  const selectionOverlay = makeOverlay('selection-overlay');
  const previewOverlay   = makeOverlay('preview-overlay');

  /* Glow halos for the selected and preview-hovered dots. Each is a
   * camera-facing Sprite with a radial-gradient texture and additive
   * blending — reads as a soft light source radiating from the dot.
   * Pulses scale + opacity in sync with the size-pulse + color-pulse
   * so the dot appears to "breathe light". */
  function makeGlowTexture() {
    const c = document.createElement('canvas');
    c.width = c.height = 128;
    const g = c.getContext('2d');
    const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    grad.addColorStop(0,    'rgba(255,255,255,1.0)');
    grad.addColorStop(0.35, 'rgba(255,255,255,0.45)');
    grad.addColorStop(0.7,  'rgba(255,255,255,0.12)');
    grad.addColorStop(1,    'rgba(255,255,255,0)');
    g.fillStyle = grad;
    g.fillRect(0, 0, 128, 128);
    const tex = new THREE.CanvasTexture(c);
    tex.needsUpdate = true;
    return tex;
  }
  const glowTexture = makeGlowTexture();
  function makeGlow(name) {
    const mat = new THREE.SpriteMaterial({
      map: glowTexture,
      color: 0xffffff,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthTest: false,
      depthWrite: false,
    });
    const sprite = new THREE.Sprite(mat);
    sprite.name = name;
    sprite.renderOrder = 998; // just under the overlay sphere
    sprite.visible = false;
    scene.add(sprite);
    return { sprite, material: mat };
  }
  const selectionGlow = makeGlow('selection-glow');
  const previewGlow   = makeGlow('preview-glow');

  // Declared above writeColors so the initial writeColors() call below
  // doesn't hit a TDZ on hoveredIndex (the hover-tint branch reads it).
  let hoveredIndex = -1;

  const tmpColor = new THREE.Color();
  function writeColors() {
    for (let i = 0; i < n; i++) {
      const id = ingredients[i].id;
      if (scoreMap && scoreMap.has(id)) {
        const t = scoreMap.get(id);
        tmpColor.copy(SCORE_GOOD).lerp(SCORE_BAD, Math.max(0, Math.min(1, t)));
      } else {
        // Phase 40 round 3: per tester feedback, filters now HIDE dots
        // entirely instead of greying them. So there's no "inactive
        // blend" branch here — non-passing items end up in hiddenSet
        // and render at scale 0. Only score-mode coloring remains.
        tmpColor.copy(originalColors[i]);
      }
      // Selection and cursor-hover used to lerp the base instance color
      // toward white, but a tester rightly pointed out that washed the
      // food-group identity out completely. The size pulse + always-on-
      // top overlay (and the glow halo for preview-hover) carry the
      // "this dot is the one" signal — the color stays unchanged so the
      // user can still read what food group it belongs to.
      mesh.setColorAt(i, tmpColor);
    }
    mesh.instanceColor.needsUpdate = true;
  }
  writeColors();

  /* Phase 40 round 10: track the current axes and nutrient unit so we
   * can recompute positions whenever EITHER changes — per-serving
   * mode scales each item's nutrient values by its serving size / 100
   * before projection, so the cloud rearranges to reflect serving
   * comparisons instead of per-100g comparisons. */
  let currentAxes = axes;
  let nutrientUnit = '100g'; // 'serving' to enable scaling
  let getScale = makeScaleGetter(nutrientUnit);
  let positions = normalizeDataset(ingredients, currentAxes, getScale).positions;

  const currentScale = new Float32Array(n);

  const tmpMatrix = new THREE.Matrix4();
  function writeMatrices() {
    for (let i = 0; i < n; i++) {
      const s = currentScale[i];
      const p = positions[i];
      tmpMatrix.makeScale(s, s, s);
      tmpMatrix.setPosition(p.x, p.y, p.z);
      mesh.setMatrixAt(i, tmpMatrix);
    }
    mesh.instanceMatrix.needsUpdate = true;
  }

  currentScale.fill(animate ? 0 : 1);
  writeMatrices();
  scene.add(mesh);

  let startTime = performance.now();
  let fadeDone = !animate;
  // Per-instance stagger: spread the dataset's reveal across
  // FADE_TOTAL_STAGGER_MS so larger datasets still finish promptly.
  const perPointDelayMs = n > 1 ? FADE_TOTAL_STAGGER_MS / n : 0;

  /* Phase 40.6: per-instance size multiplier driven by the optional
   * Size axis. Linear interpolation between SIZE_AXIS_MIN_MUL and
   * SIZE_AXIS_MAX_MUL as the chosen nutrient walks its constraint
   * window. Out-of-range values clamp (no extrapolation beyond MAX). */
  function sizeAxisMultiplier(i) {
    if (!sizeAxisEnabled || !sizeAxisNutrient) return 1;
    const v = ingredients[i][sizeAxisNutrient];
    if (!Number.isFinite(v)) return 1;
    const span = sizeAxisMax - sizeAxisMin;
    if (!(span > 0)) return 1;
    const t = Math.max(0, Math.min(1, (v - sizeAxisMin) / span));
    return SIZE_AXIS_MIN_MUL + t * (SIZE_AXIS_MAX_MUL - SIZE_AXIS_MIN_MUL);
  }

  /* Compose the per-instance target scale. Order:
   *   1. Hidden → 0
   *   2. Selected / preview → pulsing scale
   *   3. Hover → HOVER_SCALE
   *   4. Default → 1
   * The Size axis multiplier scales the result. */
  function targetScale(i, now) {
    const id = ingredients[i].id;
    if (hiddenSet && hiddenSet.has(id)) return 0;

    let base;
    if (i === selectedIndex || i === previewIndex) {
      const tSec = (now || performance.now()) / 1000;
      base = PULSE_BASE + PULSE_AMPLITUDE * Math.sin(tSec * 2 * Math.PI * PULSE_FREQ_HZ);
    } else if (i === hoveredIndex) {
      base = HOVER_SCALE;
    } else {
      base = 1;
    }
    return base * sizeAxisMultiplier(i);
  }

  function update(now) {
    let needsWrite = false;

    if (!fadeDone) {
      const elapsed = now - startTime;
      let allDone = true;
      for (let i = 0; i < n; i++) {
        // Tester feedback: when the 3D view reappears after the table
        // view (replayFadeIn), filtered-out dots used to pop into
        // existence and then shrink back to 0 once the fade finished.
        // Keep hidden instances at scale 0 throughout the fade so the
        // filter is honored from the very first frame.
        if (hiddenSet && hiddenSet.has(ingredients[i].id)) {
          currentScale[i] = 0;
          continue;
        }
        const t = (elapsed - i * perPointDelayMs) / FADE_DURATION_MS;
        if (t < 1) allDone = false;
        const progress = Math.max(0, Math.min(1, t));
        currentScale[i] = easeOutCubic(progress);
      }
      if (allDone) fadeDone = true;
      needsWrite = true;
    } else {
      for (let i = 0; i < n; i++) {
        const target = targetScale(i, now);
        // The selected and preview instances are constantly oscillating,
        // so always ease toward target — TWEEN_EPSILON gate would freeze
        // the pulse halfway. Same for size axis if it's animating.
        if (i === selectedIndex || i === previewIndex) {
          currentScale[i] = target;
          needsWrite = true;
          continue;
        }
        const diff = target - currentScale[i];
        if (Math.abs(diff) > TWEEN_EPSILON) {
          currentScale[i] += diff * HOVER_TWEEN_RATE;
          needsWrite = true;
        } else if (currentScale[i] !== target) {
          currentScale[i] = target;
          needsWrite = true;
        }
      }
    }

    if (needsWrite) writeMatrices();
    updateOverlays(now);
    return needsWrite;
  }

  /* Always-on-top overlays for selected + preview-hovered dots. Each
   * dot gets two layers: an overlay sphere (mirrors the instance,
   * always renders above any occluders) and a glow halo (additive
   * sprite, soft falloff).
   *
   * Both pulse in three dimensions, all in sync with the same sine
   * wave at PULSE_FREQ_HZ:
   *   - Size: the underlying instance scale already oscillates via
   *           targetScale().
   *   - Color: overlay tint oscillates between the dot's native
   *           food-group color (0) and pure white (TINT_PULSE_MAX),
   *           so the dot LOOKS like it's pulsing color, while still
   *           returning to its identity color every cycle.
   *   - Glow:  halo sprite's scale + opacity oscillate too — reads
   *           as a light source breathing in/out of brightness.
   *
   * Selection and preview behave the same here; a tester explicitly
   * asked for both to pulse the same way. */
  const tmpOverlayMatrix = new THREE.Matrix4();
  const tmpOverlayColor  = new THREE.Color();
  const WHITE            = new THREE.Color(1, 1, 1);
  // Color-pulse range. MIN=0 (native color), MAX close to 1 (pure
  // bright white) — the user explicitly asked for "contrasting white,
  // not washed out white at all".
  const TINT_PULSE_MIN   = 0.0;
  const TINT_PULSE_MAX   = 0.95;
  // Glow halo: scale (in world units) and opacity both oscillate.
  const GLOW_SCALE_MIN   = 0.08;
  const GLOW_SCALE_MAX   = 0.22;
  const GLOW_OPACITY_MIN = 0.175;
  const GLOW_OPACITY_MAX = 0.5;
  // Glow color: lerp the food-group color toward white so the halo
  // is bright but still tinted by identity (Vegetables glow green-
  // white, Sweets violet-white, etc.).
  const GLOW_COLOR_WHITE_BLEND = 0.55;
  const tmpGlowColor = new THREE.Color();

  function updateOverlays(now) {
    const tSec = (now || performance.now()) / 1000;
    // 0..1 oscillation in phase with the scale pulse. At pulseT=0 the
    // dot is at its native color; at pulseT=1 it's at peak white.
    const pulseT = 0.5 + 0.5 * Math.sin(tSec * 2 * Math.PI * PULSE_FREQ_HZ);
    const tintNow =
      TINT_PULSE_MIN + (TINT_PULSE_MAX - TINT_PULSE_MIN) * pulseT;
    syncOverlay(selectionOverlay, selectedIndex, tintNow);
    syncOverlay(previewOverlay,   previewIndex,  tintNow);
    syncGlow(selectionGlow, selectedIndex, pulseT);
    syncGlow(previewGlow,   previewIndex,  pulseT);

    function syncOverlay(overlay, index, tintAmount) {
      if (index < 0 || (hiddenSet && hiddenSet.has(ingredients[index]?.id))) {
        overlay.visible = false;
        return;
      }
      const p = positions[index];
      if (!p) {
        overlay.visible = false;
        return;
      }
      overlay.visible = true;
      const scl = currentScale[index];
      tmpOverlayMatrix.makeScale(scl, scl, scl);
      tmpOverlayMatrix.setPosition(p.x, p.y, p.z);
      overlay.matrix.copy(tmpOverlayMatrix);
      overlay.matrixWorldNeedsUpdate = true;
      tmpOverlayColor.copy(originalColors[index]);
      tmpOverlayColor.lerp(WHITE, tintAmount);
      overlay.material.color.copy(tmpOverlayColor);
    }

    function syncGlow(glow, index, t) {
      const { sprite, material } = glow;
      if (index < 0 || (hiddenSet && hiddenSet.has(ingredients[index]?.id))) {
        sprite.visible = false;
        return;
      }
      const p = positions[index];
      if (!p) {
        sprite.visible = false;
        return;
      }
      sprite.visible = true;
      sprite.position.set(p.x, p.y, p.z);
      const glowScale = GLOW_SCALE_MIN + (GLOW_SCALE_MAX - GLOW_SCALE_MIN) * t;
      sprite.scale.set(glowScale, glowScale, glowScale);
      material.opacity = GLOW_OPACITY_MIN + (GLOW_OPACITY_MAX - GLOW_OPACITY_MIN) * t;
      tmpGlowColor.copy(originalColors[index]).lerp(WHITE, GLOW_COLOR_WHITE_BLEND);
      material.color.copy(tmpGlowColor);
    }
  }

  function setAxes(newAxes) {
    currentAxes = newAxes;
    positions = normalizeDataset(ingredients, currentAxes, getScale).positions;
    if (fadeDone) writeMatrices();
  }

  /* Phase 40 round 10: per-100g ↔ per-serving toggle. Rebuilds the
   * positions and rewrites the InstancedMesh matrices so the dots
   * physically move. The unit also flows into picking implicitly
   * because picking reads instance world positions. */
  function setNutrientUnit(unit) {
    const next = normalizeUnit(unit);
    if (nutrientUnit === next) return;
    nutrientUnit = next;
    getScale = makeScaleGetter(nutrientUnit);
    positions = normalizeDataset(ingredients, currentAxes, getScale).positions;
    if (fadeDone) writeMatrices();
  }

  function setHover(index) {
    if (index === hoveredIndex) return;
    hoveredIndex = (typeof index === 'number' && index >= 0 && index < n) ? index : -1;
  }

  function setActiveSet(set) {
    activeSet = (set instanceof Set) ? set : null;
    writeColors();
  }

  function setHiddenSet(set) {
    hiddenSet = (set instanceof Set) ? set : null;
    /* Tester feedback: filter changes (per-100g ↔ per-serving, etc.)
     * used to take ~150ms because the per-instance scale tweens at
     * HOVER_TWEEN_RATE in both directions. Newly-hidden dots shrank
     * slowly out; newly-visible dots grew slowly in. We now snap to
     * the new target scale immediately in both directions so filter
     * responses feel instant. The initial pop-in animation is still
     * preserved (handled by the !fadeDone branch in update()). */
    if (!fadeDone) return;
    const now = performance.now();
    let dirty = false;
    for (let i = 0; i < n; i++) {
      const target = targetScale(i, now);
      if (currentScale[i] !== target) {
        currentScale[i] = target;
        dirty = true;
      }
    }
    if (dirty) writeMatrices();
  }

  function setSelectedId(id) {
    if (id === selectedId) return;
    selectedId = id || null;
    resolveSelectedIndex();
    // Color isn't a function of selection anymore — the size pulse +
    // always-on-top overlay carry the visual signal. No writeColors.
  }

  function setPreviewId(id) {
    if (id === previewId) return;
    previewId = id || null;
    resolvePreviewIndex();
    // No writeColors — preview tint lives on the overlay mesh, not the
    // base instance color. The instance's own pulse is driven by
    // targetScale recognizing previewIndex.
  }

  function setSizeAxis(config) {
    const enabled = !!(config && config.enabled && config.nutrient && config.constraint);
    sizeAxisEnabled = enabled;
    sizeAxisNutrient = enabled ? config.nutrient : null;
    if (enabled) {
      sizeAxisMin = +config.constraint.min;
      sizeAxisMax = +config.constraint.max;
      if (!(sizeAxisMax > sizeAxisMin)) {
        // Defensive — a degenerate window collapses to "no effect".
        sizeAxisEnabled = false;
      }
    }
    // Scales are interpolated in update(); no immediate write needed.
  }

  function setScoreMap(map) {
    scoreMap = (map instanceof Map) ? map : null;
    writeColors();
  }

  function setColorScheme(scheme) {
    if (!originalColorsByScheme[scheme]) return;
    if (colorScheme === scheme) return;
    colorScheme = scheme;
    originalColors = originalColorsByScheme[scheme];
    writeColors();
  }

  function setColorFilteredSet(set) {
    colorFilteredSet = (set instanceof Set) ? set : null;
    writeColors();
    // Scales are updated by the animation loop reading targetScale(i);
    // no explicit redraw needed here.
  }

  function getInstancePosition(index) {
    if (typeof index !== 'number' || index < 0 || index >= n) return null;
    const p = positions[index];
    return new THREE.Vector3(p.x, p.y, p.z);
  }

  function getIndexById(id) {
    if (!id) return -1;
    for (let i = 0; i < n; i++) if (ingredients[i].id === id) return i;
    return -1;
  }

  function dispose() {
    geometry.dispose();
    material.dispose();
    scene.remove(mesh);
    if (selectionOverlay) {
      scene.remove(selectionOverlay);
      selectionOverlay.material.dispose();
    }
    if (previewOverlay) {
      scene.remove(previewOverlay);
      previewOverlay.material.dispose();
    }
    if (selectionGlow) {
      scene.remove(selectionGlow.sprite);
      selectionGlow.material.dispose();
    }
    if (previewGlow) {
      scene.remove(previewGlow.sprite);
      previewGlow.material.dispose();
    }
    glowTexture.dispose();
  }

  // Phase 13.5 round 3: re-run the load reveal. Used when the 3D view
  // returns to visibility (e.g., user switches back from the table view)
  // so the dataset "pops in" again rather than appearing instantly.
  function replayFadeIn() {
    currentScale.fill(0);
    startTime = performance.now();
    fadeDone = false;
    writeMatrices();
  }

  return {
    mesh, ingredients,
    update, setAxes, setHover, setActiveSet, setScoreMap,
    setColorScheme, setColorFilteredSet,
    setHiddenSet, setSelectedId, setPreviewId, setSizeAxis,
    setNutrientUnit,
    getInstancePosition, getIndexById, replayFadeIn, dispose,
  };
}
