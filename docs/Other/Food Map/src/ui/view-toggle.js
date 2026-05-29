/* Phase 8: 3D ↔ table view toggle.
 *
 * Mounts a small segmented control in the page header next to the
 * Phase 4.5 view-controls. Drives state.view; the rest of the app
 * (canvas vs table visibility, view-control visibility) reacts via
 * state subscriptions.
 */

const OPTIONS = [
  { value: '3d',    label: '3D'    },
  { value: 'table', label: 'Table' },
];

export function mountViewToggle(root, { state }) {
  if (!root) return;

  root.innerHTML = `
    <div class="seg-group" role="group" aria-label="View">
      ${OPTIONS.map(o =>
        `<button type="button" class="seg-btn" data-value="${o.value}">${o.label}</button>`).join('')}
    </div>
  `;

  function sync() {
    const view = state.get('view');
    root.querySelectorAll('.seg-btn').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.value === view);
    });
  }

  root.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.seg-btn');
    if (!btn) return;
    const value = btn.dataset.value;
    if (value && state.get('view') !== value) state.set({ view: value });
  });

  state.subscribe(s => s.view, sync);
  sync();
}
