/* Boot-overlay error UI.
 *
 * The boot overlay lives in index.html and stays visible until boot()
 * resolves; on failure these helpers swap it into an error state with
 * the exception's stack trace, and offer a localStorage reset button
 * so the user can recover from a corrupt persisted state without
 * editing devtools.
 *
 * Extracted out of main.js so the entry file's surface area stays
 * focused on the actual app boot orchestration. */

export function showBootError(err) {
  const overlay = document.getElementById('boot-overlay');
  const msg     = document.getElementById('boot-message');
  const details = document.getElementById('boot-error');
  const stack   = document.getElementById('boot-error-stack');
  if (!overlay) {
    // No DOM (extremely unlikely) — fall back to console.
    console.error('[ingredient-map] boot failed', err);
    return;
  }
  overlay.hidden = false;
  overlay.classList.remove('is-fading');
  overlay.classList.add('has-error');
  if (msg)     msg.textContent = 'The app failed to load.';
  if (details) details.hidden = false;
  if (details) details.open = true;
  if (stack)   stack.textContent = (err && (err.stack || err.message)) || String(err);
}

export function hideBootOverlay() {
  const overlay = document.getElementById('boot-overlay');
  if (!overlay) return;
  overlay.classList.add('is-fading');
  setTimeout(() => { overlay.hidden = true; }, 220);
}

export function wireBootResetButton() {
  const btn = document.getElementById('boot-error-reset');
  if (!btn) return;
  btn.addEventListener('click', () => {
    try {
      // Phase 12 unified key plus the legacy per-slice keys, in case the
      // problem is in any of them.
      const KEYS = [
        'foodMap.state.v1',
        'foodMap.tableColumns',
        'foodMap.compositeWeights',
        'foodMap.userMeals',
        'foodMap.theme',
      ];
      for (const k of KEYS) {
        try { localStorage.removeItem(k); } catch {}
      }
    } finally {
      window.location.reload();
    }
  });
}
