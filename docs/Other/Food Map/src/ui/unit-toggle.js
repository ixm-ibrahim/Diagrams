/* Phase 40 round 8: global per-100g / per-serving toggle.
 *
 * Mounted in the header so it's always visible in BOTH the 3D view
 * and the table view. Earlier rounds duplicated this toggle in the
 * detail panel and the table toolbar; tester correctly noted those
 * left the 3D canvas without one. Single source of truth now.
 *
 * State key: state.nutrientUnit = '100g' | 'serving'.
 */

export function mountUnitToggle(root, { state }) {
  if (!root) return;

  root.classList.add('unit-toggle');
  root.innerHTML = `
    <div class="unit-toggle-group seg-group" role="group" aria-label="Nutrient unit">
      <button type="button" class="seg-btn seg-btn-sm" data-unit="100g">per 100g</button>
      <button type="button" class="seg-btn seg-btn-sm" data-unit="serving">per serving</button>
    </div>
  `;

  const group = root.querySelector('.unit-toggle-group');

  function refresh() {
    const cur = state.get('nutrientUnit') || '100g';
    group.querySelectorAll('[data-unit]').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.unit === cur);
    });
  }
  group.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-unit]');
    if (!btn) return;
    if (state.get('nutrientUnit') !== btn.dataset.unit) {
      state.set({ nutrientUnit: btn.dataset.unit });
    }
  });
  refresh();
  state.subscribe(s => s.nutrientUnit, refresh);
}
