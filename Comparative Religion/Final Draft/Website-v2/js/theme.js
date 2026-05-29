/* Light/dark theme toggle with localStorage persistence.
 * Default: system preference; respected on first load.
 */

const STORAGE_KEY = "site-theme";

export function initTheme() {
  const stored = localStorage.getItem(STORAGE_KEY);
  const systemDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  const initial = stored || (systemDark ? "dark" : "light");
  applyTheme(initial);

  const btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      applyTheme(next);
      localStorage.setItem(STORAGE_KEY, next);
    });
  }
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const icon = document.getElementById("theme-icon");
  const label = document.getElementById("theme-label");
  if (icon) icon.textContent = theme === "dark" ? "☀" : "☾";
  if (label) label.textContent = theme === "dark" ? "Light" : "Dark";
}
