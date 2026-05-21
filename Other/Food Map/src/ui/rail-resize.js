/* Phase 11 polish: drag-to-resize for the left/right rails on desktop.
 *
 * Each rail mounts a thin `.rail-resize` element at its inner edge.
 * Pointer-down on the handle starts a drag; on every move we update
 * `--left-rail-w` or `--right-rail-w` on :root, which the layout's grid
 * template and the header's right/legend offsets all read from.
 *
 * Non-persistent: the rail widths reset on reload (per the user's
 * spec). Mobile hides the handles via @media, so the listener is a
 * no-op there.
 *
 * Min/max widths come from CSS custom properties so they live next to
 * the other layout tokens (--rail-min-w, --rail-max-w).
 */

const MIN_PX_FALLBACK = 160;
const MAX_PX_FALLBACK = 640;

function readPxVar(name, fallback) {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  if (!raw) return fallback;
  const n = parseFloat(raw);
  return Number.isFinite(n) ? n : fallback;
}

function clampWidth(px) {
  const min = readPxVar('--rail-min-w', MIN_PX_FALLBACK);
  const max = readPxVar('--rail-max-w', MAX_PX_FALLBACK);
  return Math.max(min, Math.min(max, px));
}

export function attachRailResize() {
  document.addEventListener('pointerdown', (ev) => {
    const handle = ev.target.closest('.rail-resize');
    if (!handle) return;
    if (!matchMedia('(min-width: 769px)').matches) return;

    const rail = handle.dataset.rail; // 'left' | 'right'
    if (rail !== 'left' && rail !== 'right') return;

    ev.preventDefault();
    handle.setPointerCapture(ev.pointerId);
    handle.classList.add('is-dragging');
    document.body.classList.add('is-rail-resizing');

    function onMove(moveEv) {
      const x = moveEv.clientX;
      const px = rail === 'left'
        ? x                                 // left rail: width = pointer x
        : window.innerWidth - x;            // right rail: width = window - pointer x
      const next = clampWidth(px);
      document.documentElement.style.setProperty(
        rail === 'left' ? '--left-rail-w' : '--right-rail-w',
        `${next}px`,
      );
    }

    function onUp() {
      handle.releasePointerCapture(ev.pointerId);
      handle.classList.remove('is-dragging');
      document.body.classList.remove('is-rail-resizing');
      handle.removeEventListener('pointermove', onMove);
      handle.removeEventListener('pointerup', onUp);
      handle.removeEventListener('pointercancel', onUp);
    }

    handle.addEventListener('pointermove', onMove);
    handle.addEventListener('pointerup', onUp);
    handle.addEventListener('pointercancel', onUp);
  });
}
