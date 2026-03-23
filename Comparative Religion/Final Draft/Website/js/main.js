/**
 * =============================================================================
 * main.js — Application Bootstrap
 * =============================================================================
 * Entry point. Loads JSON data, then initializes all modules in the correct
 * dependency order. Each module's init() caches its own DOM references.
 *
 * Init order matters:
 *   1. loadMapData    — populates DataStore (everything else reads from it)
 *   2. applyTheme     — sets data-theme attribute before any rendering
 *   3. ui-header.init — caches header DOM refs
 *   4. ui-render.init — caches map container ref
 *   5. ui-events.init — binds all listeners (needs nav + state ready)
 *   6. NavigationController.init — reads URL, triggers first render
 *
 * Dependencies: data-store.js, state.js, ui-header.js, ui-render.js,
 *               ui-events.js, navigation.js, svg-engine.js (resize observer only)
 * =============================================================================
 */

import { DataStore, loadMapData } from './data-store.js';
import { AppState } from './state.js';
import { IS_MOBILE } from './constants.js';
import * as UIHeader from './ui-header.js';
import * as UIRender from './ui-render.js';
import * as UIEvents from './ui-events.js';
import { NavigationController } from './navigation.js';
import { initResizeObserver } from './svg-engine.js';
import { updateStackedGroups } from './ui-layout.js';
import * as Agreement from './ui-agreement.js';

document.addEventListener('DOMContentLoaded', async () => {
  try {
    // 0. Compute viewport-relative page width cap from monitor resolution.
    //    screen.width gives the monitor width in CSS pixels.
    //    --app-width-ratio (0.65) is the fraction of the screen to use.
    //    --app-max-width CSS fallback (1120px) acts as a floor so the cap
    //    never goes below a usable size on small monitors — small screens
    //    fill 100%, large screens get the ratio-based cap with side margins.
    const cs = getComputedStyle(document.documentElement);
    const ratio = parseFloat(cs.getPropertyValue('--app-width-ratio')) || 0.65;
    const floor = parseInt(cs.getPropertyValue('--app-max-width'), 10) || 1120;
    const cap = Math.max(Math.round(screen.width * ratio), floor);
    document.documentElement.style.setProperty('--app-max-width', `${cap}px`);

    const mapName =
      new URLSearchParams(window.location.search).get('map') || 'data';

    // 1. Load data and compute colors
    await loadMapData(mapName);

    // 2. Apply persisted theme (sets data-theme on <html>)
    AppState.applyTheme();

    // 2b. Load persisted agreement votes from localStorage
    Agreement.init();

    // 3–5. Initialize UI modules (each caches its own DOM refs)
    UIHeader.init();
    UIRender.init();
    UIEvents.init();   // binds theme toggle, header toggles, map clicks

    // 6. Initialize navigation (reads URL → first render + header update)
    NavigationController.init();

    // 7. Start resize observer for SVG connector redraws
    initResizeObserver();

    // 8. Keep stacked/unstacked state current as the container resizes.
    //    Runs alongside the SVG resize observer independently so a circular
    //    import between ui-render.js and svg-engine.js is never needed.
    const mapContainer = document.getElementById('mapContainer');
    if (mapContainer) {
      new ResizeObserver(() => {
        if (AppState.isTransitioning) return;
        const viewEl = document.querySelector('.map-flow');
        if (!viewEl) return;
        updateStackedGroups(viewEl, mapContainer.offsetWidth);
      }).observe(mapContainer);
    }

    // 9. Vote-button expansion: mobile → always expanded; desktop → collapsed
    //    (expand on hover handled by CSS).
    if (mapContainer) {
      if (IS_MOBILE) {
        // On mobile, mark every card as expanded and keep watching for new ones.
        const expandCards = () => {
          mapContainer.querySelectorAll('.node-card:not(.vote-expanded)').forEach(card => {
            card.classList.add('vote-expanded');
          });
        };
        expandCards();
        new MutationObserver(expandCards).observe(mapContainer, { childList: true, subtree: true });
      }
      // Desktop: no observer needed — buttons stay icon-only and expand on
      // hover via CSS :hover rules in agreement.css.
    }

    // Dev convenience
    console.log(
      `Bootstrap complete: ${DataStore.nodes.length} nodes, ` +
      `theme="${AppState.theme}"`
    );
    window.__debug = { DataStore, AppState, NavigationController, Agreement };

  } catch (error) {
    console.error('Failed to load page data:', error);
    const titleEl = document.getElementById('titleText');
    const subtitleEl = document.getElementById('subtitleText');
    if (titleEl)    titleEl.textContent = 'Error Loading Data';
    if (subtitleEl) subtitleEl.textContent = error.message;
  }
});
