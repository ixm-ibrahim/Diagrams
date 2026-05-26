/* Phase 40.5: ray-disambiguation floating menu.
 *
 * Opens at the click coordinates whenever a single click resolves to
 * more than one dot along the ray (picking.js returns every dot the ray
 * passes through, front-to-back). Each row previews its dot via
 * state.hoveredIngredientId on hover, and commits state.selectedIngredientId
 * on click.
 *
 * Tester feedback: the menu used to silently cap at 8 candidates even
 * when more sat under the click. picking.js now returns the full
 * cluster; this module pages the display with PAGE_SIZE-row chunks
 * and a footer that exposes "Show more" + "Show all" — same
 * progressive-disclosure pattern as ui/search.js.
 *
 * Click outside / Escape dismisses without committing.
 */

import { FOOD_GROUP_COLORS } from '../data/schema.js';
import { escapeHtml } from '../util/dom.js';

const VIEWPORT_MARGIN = 12;
const PAGE_SIZE = 8;

export function attachPickMenu({ state }) {
  const menu = document.createElement('div');
  menu.className = 'pick-menu';
  menu.hidden = true;
  menu.setAttribute('role', 'menu');
  document.body.appendChild(menu);

  let activeCandidates = [];
  let displayLimit = PAGE_SIZE;
  let lastAnchor = { clientX: 0, clientY: 0 };

  function close() {
    if (menu.hidden) return;
    menu.hidden = true;
    menu.innerHTML = '';
    activeCandidates = [];
    displayLimit = PAGE_SIZE;
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

  /* Render the current `activeCandidates` slice (0..displayLimit) plus
   * a progressive-disclosure footer when more candidates remain. Called
   * on open() and again whenever the user clicks Show more / Show all. */
  function renderMenu() {
    const total = activeCandidates.length;
    const shown = Math.min(displayLimit, total);
    const rowsHtml = activeCandidates.slice(0, shown).map((c, i) => {
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

    let footerHtml = '';
    if (total > shown) {
      const remaining = total - shown;
      const stepSize = Math.min(PAGE_SIZE, remaining);
      // Drop the "Show more" button when one more step would expose
      // every remaining candidate — keeps the choice clean (same rule
      // as ui/search.js).
      const showStepBtn = remaining > stepSize;
      footerHtml = `<div class="pick-menu-footer">`;
      if (showStepBtn) {
        footerHtml += `<button class="pick-menu-more" type="button" data-action="more">
          Show ${stepSize} more
        </button>`;
      }
      footerHtml += `<button class="pick-menu-more" type="button" data-action="all">
        Show all (${remaining}${showStepBtn ? ' more total' : ' more'})
      </button>`;
      footerHtml += `</div>`;
    }

    menu.innerHTML = rowsHtml + footerHtml;
  }

  /* Recompute menu position after a render (Show more / Show all
   * changes the height; without re-anchoring, the menu can spill off
   * the bottom of the viewport). */
  function positionMenu() {
    menu.style.left = '0px';
    menu.style.top  = '0px';
    // Force a reflow so getBoundingClientRect returns the post-render size.
    const rect = menu.getBoundingClientRect();
    const left = Math.min(
      Math.max(VIEWPORT_MARGIN, lastAnchor.clientX + 6),
      window.innerWidth  - rect.width  - VIEWPORT_MARGIN,
    );
    const top = Math.min(
      Math.max(VIEWPORT_MARGIN, lastAnchor.clientY + 6),
      window.innerHeight - rect.height - VIEWPORT_MARGIN,
    );
    menu.style.left = `${Math.round(left)}px`;
    menu.style.top  = `${Math.round(top)}px`;
  }

  function open(candidates, { clientX, clientY }) {
    if (!Array.isArray(candidates) || candidates.length <= 1) return;
    activeCandidates = candidates;
    displayLimit = PAGE_SIZE;
    lastAnchor = { clientX, clientY };
    renderMenu();
    menu.hidden = false;
    positionMenu();

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
    const more = ev.target.closest('.pick-menu-more');
    if (more) {
      const action = more.dataset.action;
      if (action === 'more') {
        displayLimit = Math.min(activeCandidates.length, displayLimit + PAGE_SIZE);
      } else {
        displayLimit = activeCandidates.length;
      }
      renderMenu();
      positionMenu();
      return;
    }
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

