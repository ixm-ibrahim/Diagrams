/* Phase 11: theme toggle.
 *
 * One button in the page header; click cycles light ↔ dark. The initial
 * value is restored from localStorage if set; otherwise we read the OS
 * preference. The active value is written to:
 *   - state.theme       (so the scene's theme subscriber re-reads colors)
 *   - <html data-theme> (so the CSS custom-property overrides apply)
 *   - localStorage       (so a reload picks up the user's choice)
 *
 * Three.js scene colors (background + axes) are CSS-driven via the
 * readCssColor helper in scene/setup.js; main.js handles rebuilding the
 * scene's colors on state.theme change.
 */

const LS_THEME_KEY = 'foodMap.theme';

export function mountThemeToggle(root, { state }) {
  if (!root) return;

  root.innerHTML = `
    <button class="theme-toggle" type="button"
            aria-label="Toggle theme" title="Toggle theme">
      <span class="theme-toggle-icon" aria-hidden="true">☾</span>
    </button>
  `;
  const btn  = root.querySelector('.theme-toggle');
  const icon = root.querySelector('.theme-toggle-icon');

  function applyTheme(theme) {
    const next = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    icon.textContent = next === 'dark' ? '☀' : '☾';
    btn.setAttribute('aria-label',
      next === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
    btn.title = btn.getAttribute('aria-label');
    try { localStorage.setItem(LS_THEME_KEY, next); } catch { /* private mode */ }
  }

  btn.addEventListener('click', () => {
    const current = state.get('theme') === 'dark' ? 'light' : 'dark';
    state.set({ theme: current });
  });

  // Resolve an initial concrete theme: localStorage > OS preference.
  let initial = null;
  try { initial = localStorage.getItem(LS_THEME_KEY); } catch { /* ignore */ }
  if (initial !== 'light' && initial !== 'dark') {
    initial = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  state.set({ theme: initial });
  applyTheme(initial);

  state.subscribe(s => s.theme, applyTheme);
}
