/* Three.js scene scaffolding — renderer, both cameras (perspective +
 * orthographic), and a ResizeObserver that keeps the canvas matched to its
 * container as rails open and close.
 *
 * Both cameras coexist from boot. `setCameraMode(mode)` swaps which one is
 * active while preserving position and look-at. Callers should re-read the
 * active camera (via `getActiveCamera()`) each frame and pass it to
 * `renderer.render` and to OrbitControls — which is why we expose getters
 * rather than a bare reference.
 *
 * Theme-reactive in spirit: every color value is read from a CSS custom
 * property via getComputedStyle so Phase 11's theme toggle can rerun the
 * read and the scene will pick up the new palette without code changes.
 */

import * as THREE from 'three';

export function readCssColor(name, fallback = '#000000') {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  if (!value) return new THREE.Color(fallback);
  try {
    return new THREE.Color(value);
  } catch {
    return new THREE.Color(fallback);
  }
}

export function readCssString(name, fallback = '') {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}

const TARGET = new THREE.Vector3(0.5, 0.5, 0.5);
const DEFAULT_POSITION = new THREE.Vector3(2.4, 1.9, 2.4);
const ORTHO_FRUSTUM_HEIGHT = 2.4; // world units shown vertically at zoom=1

/**
 * Mount a renderer, both cameras, lighting, and a resize hook.
 * Returns getters so callers always read the *currently active* camera.
 */
export function createScene(container) {
  if (!(container instanceof HTMLElement)) {
    throw new Error('createScene: container must be an HTMLElement');
  }

  const scene = new THREE.Scene();
  scene.background = readCssColor('--color-bg', '#0e1014');

  const initialWidth  = Math.max(container.clientWidth, 1);
  const initialHeight = Math.max(container.clientHeight, 1);
  const aspect = initialWidth / initialHeight;

  // Perspective camera (default).
  const persp = new THREE.PerspectiveCamera(50, aspect, 0.05, 100);
  persp.position.copy(DEFAULT_POSITION);
  persp.lookAt(TARGET);

  // Orthographic camera, framed to roughly match what the perspective camera
  // shows at the default distance. Switching modes preserves position/target.
  const halfH = ORTHO_FRUSTUM_HEIGHT / 2;
  const halfW = halfH * aspect;
  const ortho = new THREE.OrthographicCamera(-halfW, halfW, halfH, -halfH, 0.05, 100);
  ortho.position.copy(DEFAULT_POSITION);
  ortho.lookAt(TARGET);

  let activeCamera = persp;

  // Lighting tuned so sphere materials (Phase 4 InstancedMesh) shade in 3D
  // without their per-instance colors getting dimmed too far. Sprites and
  // lines are unlit and unaffected.
  scene.add(new THREE.AmbientLight(0xffffff, 0.95));
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.3);
  dirLight.position.set(1.5, 2.0, 1.5);
  scene.add(dirLight);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(initialWidth, initialHeight, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.domElement.style.display = 'block';
  renderer.domElement.style.width = '100%';
  renderer.domElement.style.height = '100%';
  container.appendChild(renderer.domElement);

  function resize() {
    const w = Math.max(container.clientWidth, 1);
    const h = Math.max(container.clientHeight, 1);
    const a = w / h;
    persp.aspect = a;
    persp.updateProjectionMatrix();
    const hh = ORTHO_FRUSTUM_HEIGHT / 2;
    const hw = hh * a;
    ortho.left   = -hw;
    ortho.right  =  hw;
    ortho.top    =  hh;
    ortho.bottom = -hh;
    ortho.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  }

  const resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(container);
  window.addEventListener('resize', resize);

  function getActiveCamera() { return activeCamera; }

  /**
   * Swap the active camera. Position and look-at are preserved across modes.
   * Callers are responsible for re-pointing OrbitControls afterward.
   */
  function setCameraMode(mode) {
    const next = mode === 'orthographic' ? ortho : persp;
    if (next === activeCamera) return next;
    next.position.copy(activeCamera.position);
    next.up.copy(activeCamera.up);
    next.lookAt(TARGET);
    activeCamera = next;
    return next;
  }

  function dispose() {
    resizeObserver.disconnect();
    window.removeEventListener('resize', resize);
    renderer.dispose();
    if (renderer.domElement.parentNode === container) {
      container.removeChild(renderer.domElement);
    }
  }

  return {
    scene,
    renderer,
    persp,
    ortho,
    getActiveCamera,
    setCameraMode,
    resize,
    dispose,
    target: TARGET,
    defaultPosition: DEFAULT_POSITION,
  };
}
