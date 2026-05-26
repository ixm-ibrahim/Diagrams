/* Phase 12: Config menu (Export / Import / Reset).
 *
 * Header button opens a small popover with three actions. Export both
 * copies the JSON to the clipboard and triggers a `ingredient-map-config.json`
 * download. Import opens a modal with a textarea + file input; on Apply
 * the parsed JSON drives state.set so every subscriber reacts in place
 * (no reload). Reset wipes the persisted blob and reloads.
 */

import {
  exportJson, importJson, clearPersisted, PERSISTABLE_KEYS,
} from '../core/persistence.js';

export function mountConfigMenu(root, { state }) {
  if (!root) return;

  root.innerHTML = `
    <button class="config-menu-button" type="button"
            aria-haspopup="true" aria-expanded="false"
            aria-label="Config" title="Config">⋯</button>
    <div class="config-menu" hidden role="menu">
      <button class="config-menu-item" data-action="tutorial" type="button" role="menuitem">
        Show tutorial
      </button>
      <button class="config-menu-item" data-action="export" type="button" role="menuitem">
        Export config…
      </button>
      <button class="config-menu-item" data-action="import" type="button" role="menuitem">
        Import config…
      </button>
      <button class="config-menu-item" data-action="reset" type="button" role="menuitem">
        Reset to defaults
      </button>
    </div>
  `;

  const btn  = root.querySelector('.config-menu-button');
  const menu = root.querySelector('.config-menu');

  btn.addEventListener('click', (ev) => {
    ev.stopPropagation();
    const open = !menu.hidden;
    menu.hidden = open;
    btn.setAttribute('aria-expanded', String(!open));
  });
  // Phase 40: pointerdown (capture) so the containment check sees the
  // original target before any in-menu re-render detaches it.
  document.addEventListener('pointerdown', (ev) => {
    if (!root.contains(ev.target)) { menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); }
  }, true);
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') { menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); }
  });

  menu.addEventListener('click', (ev) => {
    const item = ev.target.closest('.config-menu-item');
    if (!item) return;
    menu.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
    const action = item.dataset.action;
    if (action === 'export')   handleExport(state);
    if (action === 'import')   openImportModal(state);
    if (action === 'reset')    handleReset();
    if (action === 'tutorial') handleStartTutorial();
  });
}

function handleStartTutorial() {
  // Tutorial component listens for this and (re)starts regardless of
  // its tutorialSeen flag.
  document.dispatchEvent(new CustomEvent('food-map:start-tutorial'));
}

async function handleExport(state) {
  const json = exportJson(state);
  // Best-effort clipboard write (requires secure context). Failure is
  // non-blocking — the download still works.
  try { await navigator.clipboard.writeText(json); } catch { /* ignore */ }
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'ingredient-map-config.json';
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 0);
}

function handleReset() {
  if (!window.confirm('Clear all saved settings and reset to defaults? This reloads the page.')) return;
  clearPersisted();
  /* Batch 9.2 (revised): a true "Reset to defaults" should return the
   * user to the first-run experience, which includes the guided tour.
   * Clearing `foodMap.tutorialSeen` here means maybeAutoStart() will
   * fire the tour on the next page load (the persisted-config
   * grandfather check also fails because clearPersisted just dropped
   * foodMap.state.v1). */
  try { localStorage.removeItem('foodMap.tutorialSeen'); } catch { /* ignore */ }
  window.location.reload();
}

function openImportModal(state) {
  const modal = document.createElement('div');
  modal.className = 'config-modal';
  modal.innerHTML = `
    <div class="config-modal-backdrop"></div>
    <div class="config-modal-panel" role="dialog" aria-label="Import config">
      <header class="config-modal-head">
        <h2>Import config</h2>
        <button class="config-modal-close" type="button" aria-label="Close">×</button>
      </header>
      <p class="muted config-modal-help">
        Paste a JSON config from a previous export, or choose a file.
      </p>
      <input type="file" accept=".json,application/json" class="config-modal-file">
      <textarea class="config-modal-text input" rows="10"
                placeholder='{ "version": 1, ... }'
                aria-label="JSON config text"></textarea>
      <p class="config-modal-status muted" aria-live="polite"></p>
      <footer class="config-modal-actions">
        <button class="btn config-modal-cancel" type="button">Cancel</button>
        <button class="btn btn-primary config-modal-apply" type="button">Apply</button>
      </footer>
    </div>
  `;
  document.body.appendChild(modal);

  const close      = () => modal.remove();
  const closeBtn   = modal.querySelector('.config-modal-close');
  const cancelBtn  = modal.querySelector('.config-modal-cancel');
  const applyBtn   = modal.querySelector('.config-modal-apply');
  const text       = modal.querySelector('.config-modal-text');
  const file       = modal.querySelector('.config-modal-file');
  const status     = modal.querySelector('.config-modal-status');
  const backdrop   = modal.querySelector('.config-modal-backdrop');

  closeBtn.addEventListener('click', close);
  cancelBtn.addEventListener('click', close);
  backdrop.addEventListener('click', close);
  document.addEventListener('keydown', function escHandler(ev) {
    if (ev.key === 'Escape') {
      close();
      document.removeEventListener('keydown', escHandler);
    }
  });

  file.addEventListener('change', () => {
    const f = file.files[0];
    if (!f) return;
    f.text().then(t => { text.value = t; status.textContent = ''; });
  });

  applyBtn.addEventListener('click', () => {
    try {
      const applied = importJson(state, text.value);
      // Filter to keys the user actually had in their export — that's the
      // useful "what changed" number.
      const trackable = applied.filter(k => PERSISTABLE_KEYS.includes(k));
      status.textContent = `Applied ${trackable.length} of ${PERSISTABLE_KEYS.length} setting${trackable.length === 1 ? '' : 's'}.`;
      status.style.color = '';
      setTimeout(close, 800);
    } catch (err) {
      status.textContent = String(err.message || err);
      status.style.color = 'var(--color-score-bad)';
    }
  });
}
