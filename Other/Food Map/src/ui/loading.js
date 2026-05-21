/* In-app loading indicator.
 *
 * Two entry points:
 *   beginLoading(label, total?) → handle
 *     Returns { update(done), finish() }. Use when the work has knowable
 *     progress (e.g. chunked table render). Pass `total` to enable the
 *     progress bar.
 *   withLoading(label, syncFn)
 *     Wraps a synchronous operation. Defers the work one animation frame
 *     so the browser can paint the (delayed) spinner before the main
 *     thread blocks. Use sparingly — most callers should chunk their
 *     work via beginLoading instead.
 *
 * The CSS owns the appearance and the 250 ms delay before the indicator
 * becomes visible, so fast operations never produce a visible flash.
 */

let active = 0;
let label = 'Loading…';
let total = 0;
let done  = 0;

function el()  { return document.getElementById('loading-indicator'); }
function lblEl(){ return document.querySelector('#loading-indicator .loading-label'); }
function trkEl(){ return document.querySelector('#loading-indicator .loading-progress-track'); }
function barEl(){ return document.querySelector('#loading-indicator .loading-progress-bar'); }

function refresh() {
  const indicator = el();
  if (!indicator) return;
  if (active <= 0) {
    indicator.classList.remove('is-loading');
    const trk = trkEl();
    if (trk) trk.hidden = true;
    return;
  }
  indicator.classList.add('is-loading');
  const l = lblEl();
  if (l) l.textContent = label;
  const trk = trkEl();
  const bar = barEl();
  if (trk && bar) {
    if (total > 0) {
      trk.hidden = false;
      const pct = Math.max(0, Math.min(100, (done / total) * 100));
      bar.style.setProperty('--pct', `${pct.toFixed(1)}%`);
    } else {
      trk.hidden = true;
    }
  }
}

export function beginLoading(newLabel = 'Loading…', newTotal = 0) {
  active++;
  label = newLabel;
  total = newTotal;
  done  = 0;
  refresh();
  return {
    update(nextDone) {
      done = nextDone;
      refresh();
    },
    setLabel(next) {
      label = next;
      refresh();
    },
    finish() {
      active = Math.max(0, active - 1);
      refresh();
    },
  };
}

export function withLoading(newLabel, syncFn) {
  const handle = beginLoading(newLabel);
  // Double rAF so the browser has a chance to render the indicator
  // before sync work blocks the main thread.
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      try { syncFn(); } finally { handle.finish(); }
    });
  });
}
