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
  controls.minDistance = 0.6;
  controls.maxDistance = 8;

  controls.update();
  return controls;
}
