/* Arcball-style camera controls.
 *
 * Built on Three.js's OrbitControls: mouse drag rotates, wheel zooms,
 * single-finger touch rotates, two-finger pinch zooms. Pan is disabled —
 * the only camera affordances are rotate around the unit cube and dolly in
 * and out. Keeping the choices small means the user can't get lost in the
 * scene; Phase 11 adds keyboard-driven preset angles for fast resets.
 */

import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export function attachControls(camera, domElement) {
  const controls = new OrbitControls(camera, domElement);

  controls.target.set(0.5, 0.5, 0.5); // center of unit cube
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.enablePan = false;
  controls.rotateSpeed = 0.85;
  controls.zoomSpeed = 0.9;
  // Tester feedback: zoom used to be effectively infinite, especially
  // in orthographic mode where minDistance/maxDistance don't apply.
  // The perspective bounds are tightened so a user can't lose the cube
  // by scrolling, and the orthographic min/maxZoom give the same envelope.
  // Defaults shown by SNAP_POSITIONS sit at ~3 units from the target —
  // 1.0 keeps the closest dot inspection useful, 6 still shows the full
  // cube comfortably.
  controls.minDistance = 1.0;
  controls.maxDistance = 6;
  // Orthographic zoom: 1 = ORTHO_FRUSTUM_HEIGHT (2.4 world units shown
  // vertically). 0.4 → 6 units (cube small but readable);
  // 10 → 0.24 units (individual dots still pickable).
  controls.minZoom = 0.4;
  controls.maxZoom = 10;

  controls.update();
  return controls;
}
