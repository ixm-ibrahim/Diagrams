/* Phase 9: user-defined meals rendered as torus rings at the gram-weighted
 * centroid of each meal's ingredients, with thin desaturated connector
 * lines from the ring to each ingredient sphere.
 *
 * Visibility:
 *   Rings only show when state.viewLevel === 'individual', where the
 *   underlying ingredient spheres exist at the same projection. Aggregate
 *   views (categories/meal-patterns) hide the rings because the ingredient
 *   positions wouldn't correspond to anything on-screen.
 *
 * Position model:
 *   Each ingredient's normalized position depends on the current axis config.
 *   The meal's ring sits at Σ(grams_i · pos_i) / Σ(grams_i) — a true
 *   gram-weighted centroid, which also happens to be where you'd plot
 *   the meal if you treated its per-100g nutrient profile as a ingredient
 *   (since both nutrients and position are linear in the ingredients).
 *
 * Color palette: cycled per meal, so the user can tell two meals apart
 * even if their centroids land near each other.
 */

import * as THREE from 'three';
import { normalizeDataset } from '../core/normalize.js';
import { makeScaleGetter, normalizeUnit } from '../core/unit.js';

const RING_RADIUS         = 0.04;
const RING_TUBE           = 0.008;
const RING_SEGMENTS       = 32;
const RING_TUBE_SEGMENTS  = 8;
const CONNECTOR_OPACITY   = 0.45;

const MEAL_COLORS = [
  '#ff6b6b', '#4ecdc4', '#ffd166', '#a78bfa',
  '#26de81', '#fd9644', '#5bc0de', '#e573b7',
];

function colorForIndex(i) {
  return MEAL_COLORS[i % MEAL_COLORS.length];
}

export function buildMeals(scene, ingredients, axes, ranges) {
  const group = new THREE.Group();
  group.name = 'user-meals';
  scene.add(group);

  // Per-meal { ring, lines, ringMat, lineMat } so we can dispose cleanly.
  const meshesById = new Map();

  let currentAxes = axes;
  let nutrientUnit = '100g';
  let getScale = makeScaleGetter(nutrientUnit);
  let positionsByIngredientId = computePositionsByIngredientId(ingredients, currentAxes);

  function computePositionsByIngredientId(ingredients, axes) {
    const { positions } = normalizeDataset(ingredients, axes, getScale);
    const m = new Map();
    for (const p of positions) m.set(p.id, p);
    return m;
  }

  function disposeMeal(entry) {
    if (entry.ring) {
      group.remove(entry.ring);
      entry.ring.geometry.dispose();
      entry.ring.material.dispose();
    }
    if (entry.lines) {
      group.remove(entry.lines);
      entry.lines.geometry.dispose();
      entry.lines.material.dispose();
    }
  }

  function update(meals) {
    // Remove rings whose meals are gone.
    for (const [id, entry] of meshesById) {
      if (!meals.find(m => m.id === id)) {
        disposeMeal(entry);
        meshesById.delete(id);
      }
    }

    meals.forEach((meal, index) => {
      const centroid = computeCentroid(meal, positionsByIngredientId);
      let entry = meshesById.get(meal.id);

      if (!centroid) {
        // No ingredients with valid positions — drop any existing ring.
        if (entry) { disposeMeal(entry); meshesById.delete(meal.id); }
        return;
      }

      const colorHex = colorForIndex(index);

      if (!entry) {
        const ringGeometry = new THREE.TorusGeometry(
          RING_RADIUS, RING_TUBE, RING_TUBE_SEGMENTS, RING_SEGMENTS,
        );
        const ringMaterial = new THREE.MeshBasicMaterial({ color: colorHex });
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.name = `meal-ring-${meal.id}`;
        group.add(ring);

        const lineMaterial = new THREE.LineBasicMaterial({
          color: colorHex,
          transparent: true,
          opacity: CONNECTOR_OPACITY,
        });
        const lineGeometry = new THREE.BufferGeometry();
        const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
        lines.name = `meal-lines-${meal.id}`;
        group.add(lines);

        entry = { ring, lines };
        meshesById.set(meal.id, entry);
      } else {
        // Keep the same color across re-renders even if index shifts —
        // simplest is to recolor whenever the user reorders meals.
        entry.ring.material.color.set(colorHex);
        entry.lines.material.color.set(colorHex);
      }

      entry.ring.position.set(centroid.x, centroid.y, centroid.z);
      entry.ring.lookAt(centroid.x + 1, centroid.y, centroid.z);

      // Connector lines: from centroid to each ingredient's position.
      const segmentVerts = [];
      for (const ing of meal.ingredients) {
        const p = positionsByIngredientId.get(ing.ingredientId);
        if (!p) continue;
        segmentVerts.push(centroid.x, centroid.y, centroid.z);
        segmentVerts.push(p.x, p.y, p.z);
      }
      const positionAttr = new THREE.BufferAttribute(new Float32Array(segmentVerts), 3);
      entry.lines.geometry.setAttribute('position', positionAttr);
      entry.lines.geometry.computeBoundingSphere();
    });
  }

  function setAxes(newAxes) {
    currentAxes = newAxes;
    positionsByIngredientId = computePositionsByIngredientId(ingredients, currentAxes);
    // Caller is responsible for invoking update(meals) after axes change.
  }

  /* Phase 40 round 10: per-100g vs per-serving toggle. Same idea as
   * points.js — recompute the per-ingredient projected positions
   * because the centroid math is linear in those positions. */
  function setNutrientUnit(unit) {
    const next = normalizeUnit(unit);
    if (nutrientUnit === next) return;
    nutrientUnit = next;
    getScale = makeScaleGetter(nutrientUnit);
    positionsByIngredientId = computePositionsByIngredientId(ingredients, currentAxes);
  }

  function setVisible(v) {
    group.visible = !!v;
  }

  function dispose() {
    for (const [, entry] of meshesById) disposeMeal(entry);
    meshesById.clear();
    scene.remove(group);
  }

  return { group, update, setAxes, setVisible, setNutrientUnit, dispose };
}

function computeCentroid(meal, positionsByIngredientId) {
  let sumGrams = 0;
  let cx = 0, cy = 0, cz = 0;
  for (const ing of meal.ingredients) {
    const pos = positionsByIngredientId.get(ing.ingredientId);
    if (!pos) continue;
    cx += ing.grams * pos.x;
    cy += ing.grams * pos.y;
    cz += ing.grams * pos.z;
    sumGrams += ing.grams;
  }
  if (sumGrams <= 0) return null;
  return { x: cx / sumGrams, y: cy / sumGrams, z: cz / sumGrams };
}
