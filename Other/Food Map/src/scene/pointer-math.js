/* Pointer / screen math shared by scene interaction modules.
 *
 * picking.js and axis-drag.js both convert PointerEvent client coords
 * into Normalized Device Coordinates, and both project a world-space
 * point onto client pixel coordinates for DOM-overlay positioning.
 * Both operations are extracted here so the two callers stay aligned.
 */

import * as THREE from 'three';

/* Write the event's clientX/clientY → NDC into `outVec2` (a
 * THREE.Vector2). Returns the same vector for chaining. If `outVec2`
 * is omitted, allocates and returns a fresh one. */
export function pointerNDC(event, domElement, outVec2) {
  const rect = domElement.getBoundingClientRect();
  const out = outVec2 || new THREE.Vector2();
  out.x =  ((event.clientX - rect.left) / rect.width)  * 2 - 1;
  out.y = -((event.clientY - rect.top)  / rect.height) * 2 + 1;
  return out;
}

/* Project a world-space THREE.Vector3 to client-space pixel coords
 * (matching MouseEvent.clientX/clientY). Returns `{ x, y }`. The world
 * vector is not mutated. */
export function worldToClient(worldPos, camera, domElement) {
  const v = worldPos.clone().project(camera);
  const rect = domElement.getBoundingClientRect();
  return {
    x: rect.left + (v.x + 1) / 2 * rect.width,
    y: rect.top  + (1 - (v.y + 1) / 2) * rect.height,
  };
}
