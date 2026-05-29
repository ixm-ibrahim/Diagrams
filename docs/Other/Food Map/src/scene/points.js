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

// Batch 11: when a selected dot is hidden by the current filters,
// render it at FULL pulse scale (same as a normal selection) and force
// pure red so the "this is filtered out" signal is unmistakable. The
// original gray + shrink treatment was too subtle — testers couldn't
// tell the ghost dot apart from regular faded dots in the cloud.
// Blend = 1.0 → original food-group color is fully replaced.
const DIMMED_FILTERED_RED   = new THREE.Color(1.0, 0.0, 0.0);
const DIMMED_FILTERED_BLEND = 1.0;

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
   * camera-facing Sprite with a radial-gradient texture — blending
   * mode swaps with the theme: additive on dark (so the halo reads as
   * emitted light against a near-black background), normal on light
   * (additive would push toward pure white on the already-white
   * background and the halo vanished, per tester feedback).
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

  /* Theme-driven glow settings. The constants below are the dark-mode
   * defaults (additive blending, mostly white-blended color, brighter
   * peak opacity). Light-mode swaps to normal blending so the halo
   * darkens the background instead of brightening it, keeps the
   * food-group identity color (less white-mix), and runs at a higher
   * opacity floor since normal blending doesn't accumulate. */
  let glowBlending      = THREE.AdditiveBlending;
  let glowWhiteBlend    = 0.55;
  let glowOpacityMin    = 0.175;
  let glowOpacityMax    = 0.5;
  function applyGlowThemeSettings(theme) {
    const isLight = theme === 'light';
    glowBlending   = isLight ? THREE.NormalBlending : THREE.AdditiveBlending;
    glowWhiteBlend = isLight ? 0.15 : 0.55;
    glowOpacityMin = isLight ? 0.35 : 0.175;
    glowOpacityMax = isLight ? 0.75 : 0.5;
    for (const g of [selectionGlow, previewGlow]) {
      g.material.blending = glowBlending;
      g.material.needsUpdate = true;
    }
  }
  // Read the initial theme from the document attribute (state isn't
  // imported here). main.js calls refreshTheme() on theme changes.
  applyGlowThemeSettings(document.documentElement.getAttribute('data-theme'));

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
      // Batch 11: filtered-out ghost selection blends hard toward red
      // so the "you're still selecting this, but it's not passing your
      // filters" signal is unmistakable in the cloud.
      if (isDimmedExempt(i)) {
        tmpColor.lerp(DIMMED_FILTERED_RED, DIMMED_FILTERED_BLEND);
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
   *   1. Hidden + selected (or preview) → FULL pulsing scale (batch 11:
   *      keep the ghost dot at the same size as a normal selection so
   *      the user can spot it in the cloud — the red color does the
   *      "filtered out" signaling, not a size reduction).
   *   2. Hidden → 0
   *   3. Selected / preview → pulsing scale
   *   4. Hover → HOVER_SCALE
   *   5. Default → 1
   * The Size axis multiplier scales the result. */
  function targetScale(i, now) {
    const id = ingredients[i].id;
    const isHidden = hiddenSet && hiddenSet.has(id);
    if (isHidden) {
      if (i !== selectedIndex && i !== previewIndex) return 0;
      const tSec = (now || performance.now()) / 1000;
      const base = PULSE_BASE + PULSE_AMPLITUDE * Math.sin(tSec * 2 * Math.PI * PULSE_FREQ_HZ);
      return base * sizeAxisMultiplier(i);
    }

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

  /* True iff this instance is currently in the hidden set but is also
   * the selected or preview-hovered item — i.e. the "filtered-out but
   * visible as a ghost" exemption above. Drives the red color blend
   * and the overlay/halo bypass (overlay is suppressed so the bright
   * food-group tint doesn't undo the red ghost signal). */
  function isDimmedExempt(i) {
    if (!hiddenSet) return false;
    if (i !== selectedIndex && i !== previewIndex) return false;
    const id = ingredients[i] && ingredients[i].id;
    return !!(id && hiddenSet.has(id));
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
  // Glow halo: scale (in world units) oscillates as a const; opacity
  // range is theme-driven (see applyGlowThemeSettings) so the halo stays
  // legible against either background.
  const GLOW_SCALE_MIN   = 0.08;
  const GLOW_SCALE_MAX   = 0.22;
  // Glow color: lerp the food-group color toward white. The blend amount
  // is theme-driven — heavier white-mix on dark (so the halo reads as
  // emitted light), lighter on white so it keeps the identity color and
  // doesn't dissolve into the background.
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
      // Hidden + selected/preview = dimmed ghost (handled by instance
      // color + scale). The bright always-on-top overlay would undo
      // that ghost effect, so keep it off when the item is filtered out.
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
      if (index < 0) {
        sprite.visible = false;
        return;
      }
      const isGhost = hiddenSet && hiddenSet.has(ingredients[index]?.id);
      const p = positions[index];
      if (!p) {
        sprite.visible = false;
        return;
      }
      sprite.visible = true;
      sprite.position.set(p.x, p.y, p.z);
      const glowScale = GLOW_SCALE_MIN + (GLOW_SCALE_MAX - GLOW_SCALE_MIN) * t;
      sprite.scale.set(glowScale, glowScale, glowScale);
      material.opacity = glowOpacityMin + (glowOpacityMax - glowOpacityMin) * t;
      if (isGhost) {
        /* Batch 11 follow-up: filtered-out ghost gets a pure red halo
         * so it's easy to spot in the cloud at a glance, regardless of
         * theme. No white-blend (white-mix on red shifts toward pink). */
        material.color.copy(DIMMED_FILTERED_RED);
      } else {
        tmpGlowColor.copy(originalColors[index]).lerp(WHITE, glowWhiteBlend);
        material.color.copy(tmpGlowColor);
      }
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
    // Color is now a function of hidden-AND-selected (the dimmed
    // exemption blend) — repaint instance colors so the red ghost
    // treatment flips on/off when filters move the selected dot in or
    // out of the hidden set.
    writeColors();
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
    // Color now depends on selection in one specific case: when the
    // selected item is in the hidden set (filtered out) we paint it
    // red as a "ghosted selection". Repaint so a new selection that
    // happens to be hidden picks up the red treatment immediately.
    writeColors();
  }

  function setPreviewId(id) {
    if (id === previewId) return;
    previewId = id || null;
    resolvePreviewIndex();
    // Preview can also trigger the dimmed exemption (search-hovering a
    // currently-hidden item still shows it as a ghost), so repaint on
    // preview changes too.
    writeColors();
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

  function refreshTheme() {
    applyGlowThemeSettings(document.documentElement.getAttribute('data-theme'));
  }

  return {
    mesh, ingredients,
    update, setAxes, setHover, setActiveSet, setScoreMap,
    setColorScheme, setColorFilteredSet,
    setHiddenSet, setSelectedId, setPreviewId, setSizeAxis,
    setNutrientUnit,
    refreshTheme,
    getInstancePosition, getIndexById, replayFadeIn, dispose,
  };
}
