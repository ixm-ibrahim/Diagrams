/* Axes, ticks, billboard labels, dynamic "★ Best" / "✗ Worst" corner
 * indicators, and a unit-cube wireframe.
 *
 * Axes emanate from origin and extend along +X / +Y / +Z. Each axis has
 * two independent settings: `direction` (semantic — which value is best)
 * and `orientation` (visual — how values lay out on the axis).
 *
 * `orientation` controls tick value ordering and ingredient positions:
 *   'ascending'  → values rise from min at origin to max at tip.
 *   'descending' → values fall from max at origin to min at tip.
 *
 * `direction` × `orientation` decides which END of each axis is "best":
 *   max + ascending  → best at tip (position 1)
 *   min + descending → best at tip (position 1)
 *   max + descending → best at origin (position 0)
 *   min + ascending  → best at origin (position 0)
 *
 * The "★ Best" sprite floats at the cube corner formed by each axis's best
 * end. "✗ Worst" floats at the opposite corner. Both move when the user
 * flips either direction or orientation in the axis picker.
 */

import * as THREE from 'three';
import { readCssColor, readCssString } from './setup.js';
import { NUTRIENT_META } from '../data/schema.js';
import { effectiveRange } from '../core/normalize.js';

// Phase 13.75: exported so the axis-drag interaction can compute screen
// projections without duplicating the geometry.
export const AXIS_LEN = 1.0;
const TICK_FRACTIONS = [0.25, 0.5, 0.75, 1.0];
const TICK_HALF_LEN = 0.018;

const AXIS_COLOR_VARS = ['--color-axis-x', '--color-axis-y', '--color-axis-z'];
export const AXIS_DIRS = [
  new THREE.Vector3(1, 0, 0),
  new THREE.Vector3(0, 1, 0),
  new THREE.Vector3(0, 0, 1),
];

function makeTextSprite(text, {
  color = '#000',
  fontSize = 22,
  fontWeight = 400,
  font = 'sans-serif',
  padding = 6,
  worldHeight = 0.055,
  alwaysOnTop = false,
} = {}) {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const cssFont = `${fontWeight} ${fontSize}px ${font}`;

  const measureCanvas = document.createElement('canvas');
  const mctx = measureCanvas.getContext('2d');
  mctx.font = cssFont;
  const textW = Math.ceil(mctx.measureText(text).width);
  const textH = Math.ceil(fontSize * 1.3);

  const canvasW = textW + padding * 2;
  const canvasH = textH + padding * 2;

  const canvas = document.createElement('canvas');
  canvas.width  = canvasW * dpr;
  canvas.height = canvasH * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.font = cssFont;
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'center';
  ctx.fillStyle = color;
  ctx.fillText(text, canvasW / 2, canvasH / 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  texture.needsUpdate = true;

  const material = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthTest: !alwaysOnTop,
    depthWrite: false,
  });
  const sprite = new THREE.Sprite(material);
  if (alwaysOnTop) sprite.renderOrder = 10;

  const worldWidth = worldHeight * (canvasW / canvasH);
  sprite.scale.set(worldWidth, worldHeight, 1);
  return sprite;
}

/* Value at axis fraction t, governed by orientation only.
 *   orientation='ascending'  → t=0 is min, t=1 is max.
 *   orientation='descending' → t=0 is max, t=1 is min.
 */
function tickValueAt(t, range, orientation) {
  return orientation === 'descending'
    ? range.max - t * (range.max - range.min)
    : range.min + t * (range.max - range.min);
}

/* Where on this axis does "best" live, given direction + orientation?
 * Returns 1 (tip) when direction and orientation are aligned in the sense
 * that the preferred value ends up at the tip; 0 (origin) otherwise.
 */
function bestEnd(axis) {
  const dirMax = axis.direction === 'max';
  const oriAsc = axis.orientation === 'ascending';
  return dirMax === oriAsc ? 1 : 0;
}

// Position a sprite just outside a unit-cube corner.
function spriteAtCorner(corner, distance = 0.10) {
  const out = new THREE.Vector3(corner.x - 0.5, corner.y - 0.5, corner.z - 0.5);
  if (out.lengthSq() === 0) return corner.clone();
  out.normalize().multiplyScalar(distance);
  return corner.clone().add(out);
}

/**
 * Build the axes group and add it to the scene.
 *
 * @param {THREE.Scene} scene
 * @param {Array<{nutrient: string, direction: 'min'|'max', constraint?: {min: number, max: number}}>} axes — length 3.
 * @param {Record<string, {min:number, max:number}>} ranges
 * @returns {{ group: THREE.Group, axisNameSprites: THREE.Sprite[], tickLabelSprites: THREE.Sprite[][], labelsGroup: THREE.Group }}
 */
export function buildAxes(scene, axes, ranges) {
  if (!Array.isArray(axes) || axes.length !== 3) {
    throw new Error('buildAxes: axes must be an array of length 3');
  }

  const group = new THREE.Group();
  group.name = 'axes';

  // Phase 13.5 round 4: only the large axis-NAME labels go under a
  // toggleable group. Tick numbers and ★ Best / ✗ Worst markers stay
  // visible always — they're small and don't visually block dots.
  const labelsGroup = new THREE.Group();
  labelsGroup.name = 'axis-name-labels';
  group.add(labelsGroup);

  const axisColors = AXIS_COLOR_VARS.map((v, i) =>
    readCssColor(v, ['#d97706', '#ca8a04', '#7c3aed'][i]));
  const cTick     = readCssColor('--color-axis-tick', '#5b6270');
  const textColor  = readCssString('--color-text', '#14171c');
  const mutedColor = readCssString('--color-text-muted', '#5b6270');
  const fontFamily = readCssString('--font-family', 'sans-serif');

  // --- Axis lines from origin ---
  for (let i = 0; i < 3; i++) {
    const geom = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      AXIS_DIRS[i].clone().multiplyScalar(AXIS_LEN),
    ]);
    const mat = new THREE.LineBasicMaterial({ color: axisColors[i] });
    const line = new THREE.Line(geom, mat);
    line.name = `axis-${'xyz'[i]}`;
    group.add(line);
  }

  // --- Tick marks ---
  const tickPoints = [];
  for (const t of TICK_FRACTIONS) {
    // X axis ticks — small bar in ±Y at z=0
    tickPoints.push(new THREE.Vector3(t, -TICK_HALF_LEN, 0));
    tickPoints.push(new THREE.Vector3(t,  TICK_HALF_LEN, 0));
    // Y axis ticks — small bar in ±X at z=0
    tickPoints.push(new THREE.Vector3(-TICK_HALF_LEN, t, 0));
    tickPoints.push(new THREE.Vector3( TICK_HALF_LEN, t, 0));
    // Z axis ticks — small bar in ±X at y=0
    tickPoints.push(new THREE.Vector3(-TICK_HALF_LEN, 0, t));
    tickPoints.push(new THREE.Vector3( TICK_HALF_LEN, 0, t));
  }
  const tickGeom = new THREE.BufferGeometry().setFromPoints(tickPoints);
  const tickMat  = new THREE.LineBasicMaterial({ color: cTick });
  const ticks = new THREE.LineSegments(tickGeom, tickMat);
  ticks.name = 'ticks';
  group.add(ticks);

  // --- Tick labels — always ascending ---
  const tickLabelOffsets = [
    new THREE.Vector3(0,    -0.07, 0),    // X axis labels below the line
    new THREE.Vector3(-0.08, 0,    0),    // Y axis labels left of the line
    new THREE.Vector3(-0.08, 0,    0),    // Z axis labels left of the line
  ];

  /* Tester feedback: tick numbers along the depth axis also need to
   * fade in orthographic snap views. Collected per-axis so the
   * caller can target them. */
  const tickLabelSprites = [[], [], []];
  for (let i = 0; i < 3; i++) {
    const axis = axes[i];
    const range = effectiveRange(axis, ranges);
    const meta = NUTRIENT_META[axis.nutrient];
    if (!range || !meta) continue;

    for (const t of TICK_FRACTIONS) {
      const raw = tickValueAt(t, range, axis.orientation);
      const label = makeTextSprite(meta.format(raw),
        { color: mutedColor, fontSize: 22, font: fontFamily });
      label.position.copy(AXIS_DIRS[i]).multiplyScalar(t).add(tickLabelOffsets[i]);
      // Tick numbers stay attached to the root axes group — small and
      // never large enough to obscure a sphere click target.
      group.add(label);
      tickLabelSprites[i].push(label);
    }
  }

  // --- Axis name labels at each tip ("Calories ▾", clickable) ---
  const axisNameSprites = [];
  for (let i = 0; i < 3; i++) {
    const { nutrient } = axes[i];
    const meta = NUTRIENT_META[nutrient];
    const text = `${meta.label} ▾`;
    const sprite = makeTextSprite(text, {
      color: textColor, fontSize: 26, fontWeight: 600,
      font: fontFamily, worldHeight: 0.07, alwaysOnTop: true,
    });
    sprite.position.copy(AXIS_DIRS[i]).multiplyScalar(AXIS_LEN + 0.10);
    sprite.userData = { kind: 'axis-name', axisIndex: i };
    sprite.cursor = 'pointer';
    labelsGroup.add(sprite);
    axisNameSprites.push(sprite);
  }

  // --- Dynamic corner indicators based on per-axis direction × orientation ---
  const bestCorner = new THREE.Vector3(
    bestEnd(axes[0]), bestEnd(axes[1]), bestEnd(axes[2]),
  );
  const worstCorner = new THREE.Vector3(
    1 - bestCorner.x, 1 - bestCorner.y, 1 - bestCorner.z,
  );

  const best = makeTextSprite('★ Best', {
    color: textColor, fontSize: 26, fontWeight: 700,
    font: fontFamily, worldHeight: 0.075, alwaysOnTop: true,
  });
  best.position.copy(spriteAtCorner(bestCorner, 0.11));
  // Best/Worst sit at the cube corners, never over the dot cloud — keep
  // them visible even when axis names are hidden.
  group.add(best);

  const worst = makeTextSprite('✗ Worst', {
    color: mutedColor, fontSize: 24, fontWeight: 600,
    font: fontFamily, worldHeight: 0.065, alwaysOnTop: true,
  });
  worst.position.copy(spriteAtCorner(worstCorner, 0.10));
  group.add(worst);

  // --- Unit-cube wireframe (omit the 3 edges that ARE the axes from origin) ---
  const v = (x, y, z) => new THREE.Vector3(x, y, z);
  const cubeEdgePoints = [
    // 3 edges meeting at the far corner (1,1,1)
    v(1,1,1), v(0,1,1),
    v(1,1,1), v(1,0,1),
    v(1,1,1), v(1,1,0),
    // 6 other cube edges (skip the 3 axis edges that emanate from origin)
    v(1,0,0), v(1,1,0),
    v(1,0,0), v(1,0,1),
    v(0,1,0), v(1,1,0),
    v(0,1,0), v(0,1,1),
    v(0,0,1), v(1,0,1),
    v(0,0,1), v(0,1,1),
  ];
  const cubeGeom = new THREE.BufferGeometry().setFromPoints(cubeEdgePoints);
  const cubeMat = new THREE.LineBasicMaterial({
    color: cTick, transparent: true, opacity: 0.28,
  });
  const cubeWire = new THREE.LineSegments(cubeGeom, cubeMat);
  cubeWire.name = 'unit-cube';
  group.add(cubeWire);

  scene.add(group);
  return { group, axisNameSprites, tickLabelSprites, labelsGroup };
}

/**
 * Dispose all GPU resources owned by an axes group and detach it from its
 * parent. Use before rebuilding axes after an axis-config change.
 */
export function disposeAxes(group) {
  if (!group) return;
  group.traverse(obj => {
    if (obj.geometry) obj.geometry.dispose();
    if (obj.material) {
      if (obj.material.map) obj.material.map.dispose();
      obj.material.dispose();
    }
  });
  if (group.parent) group.parent.remove(group);
}
