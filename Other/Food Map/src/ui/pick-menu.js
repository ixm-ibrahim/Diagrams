/* Phase 40.5: ray-disambiguation floating menu.
 *
 * Opens at the click coordinates whenever a single click resolves to
 * more than one dot along the ray (within RAY_CLUSTER_DIST in
 * picking.js). Each row previews its dot via state.hoveredIngredientId
 * on hover, and commits state.selectedIngredientId on click.
 *
 * Click outside / Escape dismisses without committing.
 */

import { FOOD_GROUP_COLORS } from '../data/schema.js';

const VIEWPORT_MARGIN = 12;

export function attachPickMenu({ state }) {
  const menu = document.createElement('div');
  menu.className = 'pick-menu';
  menu.hidden = true;
  menu.setAttribute('role', 'menu');
  document.body.appendChild(menu);

  let activeCandidates = [];

  function close() {
    if (menu.hidden) return;
    menu.hidden = true;
    menu.innerHTML = '';
    activeCandidates = [];
    // Clear any preview hover this menu left behind.
    if (state.get('hoveredIngredientId') !== null) {
      state.set({ hoveredIngredientId: null });
    }
    document.removeEventListener('pointerdown', onOutside, true);
    document.removeEventListener('keydown', onKey);
  }

  function onOutside(ev) {
    if (menu.contains(ev.target)) return;
    close();
  }
  function onKey(ev) {
    if (ev.key === 'Escape') close();
  }

  function open(candidates, { clientX, clientY }) {
    if (!Array.isArray(candidates) || candidates.length <= 1) return;
    activeCandidates = candidates;
    menu.innerHTML = candidates.map((c, i) => {
      const ing = c.ingredient;
      const swatch = swatchCss(ing);
      const subtitle = subtitleFor(ing);
      return `
        <button class="pick-menu-row" type="button" role="menuitem"
                data-index="${i}">
          <span class="pick-menu-swatch" style="background: ${swatch};"
                aria-hidden="true"></span>
          <span class="pick-menu-text">
            <span class="pick-menu-name">${escapeHtml(ing.name)}</span>
            ${subtitle
              ? `<span class="pick-menu-sub">${escapeHtml(subtitle)}</span>`
              : ''}
          </span>
        </button>
      `;
    }).join('');

    menu.style.left = '0px';
    menu.style.top  = '0px';
    menu.hidden = false;

    // Position after un-hiding so we can measure size.
    const rect = menu.getBoundingClientRect();
    const left = Math.min(
      Math.max(VIEWPORT_MARGIN, clientX + 6),
      window.innerWidth  - rect.width  - VIEWPORT_MARGIN,
    );
    const top = Math.min(
      Math.max(VIEWPORT_MARGIN, clientY + 6),
      window.innerHeight - rect.height - VIEWPORT_MARGIN,
    );
    menu.style.left = `${Math.round(left)}px`;
    menu.style.top  = `${Math.round(top)}px`;

    document.addEventListener('pointerdown', onOutside, true);
    document.addEventListener('keydown', onKey);
  }

  menu.addEventListener('pointerover', (ev) => {
    const row = ev.target.closest('.pick-menu-row');
    if (!row) return;
    const idx = +row.dataset.index;
    const cand = activeCandidates[idx];
    if (!cand) return;
    if (state.get('hoveredIngredientId') !== cand.ingredient.id) {
      state.set({ hoveredIngredientId: cand.ingredient.id });
    }
  });
  menu.addEventListener('pointerout', (ev) => {
    // Only clear when leaving the menu entirely — moving between rows
    // is handled by pointerover.
    if (menu.contains(ev.relatedTarget)) return;
    if (state.get('hoveredIngredientId') !== null) {
      state.set({ hoveredIngredientId: null });
    }
  });

  menu.addEventListener('click', (ev) => {
    const row = ev.target.closest('.pick-menu-row');
    if (!row) return;
    const idx = +row.dataset.index;
    const cand = activeCandidates[idx];
    if (!cand) return;
    state.set({ selectedIngredientId: cand.ingredient.id });
    close();
  });

  return { open, close };
}

function swatchCss(ing) {
  // Phase 40.5: surface food_group color when available (categories /
  // meals have food_group_weights), fall back to A/P/D blend for
  // individual ingredients.
  if (ing.food_group && FOOD_GROUP_COLORS[ing.food_group]) {
    const c = FOOD_GROUP_COLORS[ing.food_group];
    return `rgb(${Math.round(c[0]*255)}, ${Math.round(c[1]*255)}, ${Math.round(c[2]*255)})`;
  }
  const [a = 0, p = 0, d = 0] = ing.group_weights || [];
  return `rgb(${Math.round(a*255)}, ${Math.round(p*255)}, ${Math.round(d*255)})`;
}

function subtitleFor(ing) {
  if (ing.category === 'Meal') {
    return ing.cuisine || 'Meal';
  }
  const parts = [ing.food_group, ing.category].filter(Boolean);
  return parts.join(' · ');
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
