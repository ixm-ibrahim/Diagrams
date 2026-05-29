/* First-run guided tour.
 *
 * Nine steps walk a new user through the top-level concept and the
 * highest-leverage controls. After each step the user can hit Next,
 * Back, or Skip.
 *
 * First-time detection (Batch 9.1):
 *   - localStorage key `foodMap.tutorialSeen` set to "1" means the
 *     tour was completed or dismissed. maybeAutoStart() checks this
 *     and bails when set.
 *   - Existing users (anyone with a persisted `foodMap.state.v1`
 *     config blob from a prior session) are GRANDFATHERED IN: the
 *     tour silently marks itself seen on first boot so it never
 *     ambushes them.
 *   - The ⋯ config menu's "Reset to defaults" clears the seen flag
 *     (and the persisted config) before reloading the page, so the
 *     tour auto-fires again on the next load. Its "Show tutorial"
 *     entry and any other in-app caller can dispatch the
 *     `food-map:start-tutorial` CustomEvent to re-run mid-session;
 *     start() ignores the seen flag.
 *
 * Spotlight strategy: four absolutely-positioned dim panels sit
 * around the target's bounding rect, leaving the target itself
 * fully visible AND fully interactive (clicks pass through the
 * gap to the real element). A pulsing ring traces the target.
 * A tooltip card auto-positions below the target with viewport
 * fallback to above / side / centered.
 *
 * Batch 9 additions:
 *   - Per-slide `callouts`: small pulsing dots anchored to either a
 *     DOM selector or one of the three 3D axis-name sprites. 3D
 *     anchors are re-projected on every animation frame so they
 *     track the sprite as the camera rotates.
 *   - Per-slide `sectionStates`: programmatic open/close of the axes
 *     panel and color guide so they're only visible on their slides.
 *   - Per-slide `canvasInteractive`: when true, the dim panels are
 *     pointer-events: none so dot clicks pass through to picking.
 */

import { worldToClient } from '../scene/pointer-math.js';

const LS_KEY = 'foodMap.tutorialSeen';

const RING_PADDING = 6;
const CARD_GAP     = 14;
const VIEWPORT_PAD = 12;
const MOBILE_BP    = 768;

/* A "smart" indicator point for a collapsible corner panel (color guide,
 * axes, active filters). While the panel is expanded its inner control
 * exists, so the dot points at that; once the panel is collapsed to a pill
 * the inner control is gone from the DOM, so the dot points at the expand
 * button instead — telling the user to open the panel first. Re-evaluated
 * every frame by positionCallouts(), so it hops as the panel opens/closes. */
function cornerTaskPoint(panelSel, expandSel, innerSel) {
  return () => {
    if (document.querySelector(innerSel)) return { dom: innerSel };
    if (document.querySelector(expandSel)) return { dom: expandSel };
    return { dom: panelSel };
  };
}

export function mountTutorial({
  state,
  /* Optional refs for 3D-anchored callouts. Each is a getter so the
   * tutorial doesn't capture stale handles when the scene rebuilds. */
  getCamera = null,
  getCanvas = null,
  getAxisNameSprites = null,
  /* Round 3: clean-slate helpers for the guided use-case flows. */
  getAllIngredientIds = () => [],
  resetScene = () => {},
} = {}) {
  let root = null;
  let stepIdx = 0;
  let steps = [];
  let reposRAF = 0;      // persistent per-frame loop (ring + card + callouts)
  let calloutEls = [];   // reusable pool of indicator-dot DOM nodes
  let currentPoint = null; // active indicator source (spec | fn | array), resolved per frame
  let onResize = null;
  let savedRailOpen = null;
  /* Mobile: the × collapses the tour to a slim bar (header + the current
   * step's instruction) instead of ending it — the full card eats most of
   * a phone screen, so the user needs a way to tuck it aside and actually
   * touch the controls behind it. Only "Skip tour" (in the expanded card)
   * ends the tour. The bar auto-advances its step text as checklist tasks
   * complete and surfaces a Next button once the slide is done. */
  let collapsed = false;
  /* Batch 5: per-slide interactive checklist. A slide may declare `tasks`
   * (1–3 actions). They gate sequentially — only the first not-yet-done task
   * is "active" and shows an on-screen indicator; later ones stay locked
   * (greyed) until the ones before them complete. Completion is detected two
   * ways: a state-slice predicate (`watch`+`equals`) / change (`changed`), or a
   * DOM event (`dom`) for actions that fire no state change (Fit visible,
   * orbit/zoom, axis snap, the table Columns menu). */
  let taskDone = [];          // bool per task on the current slide
  let taskBaselines = [];     // snapshot for `changed` tasks (slide-entry value)
  let taskStateUnsubs = [];   // global state subscriptions (set up in start)
  let taskDomCleanup = [];    // per-slide DOM listener removers

  function maybeAutoStart() {
    const seen = safeRead(LS_KEY) === '1';
    if (seen) return;
    /* If the user already has a persisted config blob, treat them as
     * an existing user and silently mark the tour seen. The tour is
     * for first-timers; surprising returning users would be rude. */
    if (safeRead('foodMap.state.v1')) {
      markSeen();
      return;
    }
    // Wait for the boot overlay to actually be gone — it has a ~220 ms
    // fade-out and sits at z-index 10000, well above the tutorial. Poll
    // briefly with a hard timeout so we never block forever.
    const t0 = performance.now();
    function tryStart() {
      const overlay = document.getElementById('boot-overlay');
      const cleared = !overlay || overlay.hidden ||
        getComputedStyle(overlay).display === 'none';
      if (cleared || performance.now() - t0 > 2000) { start(); return; }
      setTimeout(tryStart, 60);
    }
    setTimeout(tryStart, 240);
  }

  function start() {
    if (root) return; // already open
    stepIdx = 0;
    collapsed = false;
    steps = buildSteps();
    buildDom();
    if (state && isMobile()) {
      savedRailOpen = state.get('leftRailOpen');
    }
    wireTaskStateWatchers();
    renderStep();
    /* A persistent rAF loop keeps the spotlight ring, dim panels, card, and
     * indicator dots aligned with their targets EVERY frame. The bottom-right
     * Axes / Color-guide panels reflow when one collapses, the left rail and
     * table appear/disappear, the camera orbits — a one-shot measurement goes
     * stale immediately (the slide-5 misalignment). Re-measuring per frame is
     * cheap while a modal tour is up and self-corrects against any layout. */
    startLiveLoop();
    onResize = () => scheduleReposition();
    window.addEventListener('resize', onResize);
    window.addEventListener('scroll', onResize, true);
    document.addEventListener('keydown', onKey, true);
    // Mobile: fade the card whenever the user reaches past it to touch the
    // app (orbit/pinch the map, drag a slider, etc.) so the live result is
    // visible under the instructions. See onGlobalPointerDown.
    document.addEventListener('pointerdown', onGlobalPointerDown, true);
  }

  /* While the expanded card is up on a phone, the moment the user starts a
   * gesture anywhere that ISN'T the card or the collapsed bar, fade the
   * card out (it covers most of the screen) so they can watch the map /
   * rail react. It snaps back when the finger lifts. The card's dim panels
   * are already pointer-events:none on task slides, so the gesture itself
   * lands on the app underneath regardless. */
  function onGlobalPointerDown(ev) {
    if (!root || collapsed || !isMobile()) return;
    const card = root.querySelector('.tutorial-card');
    const bar  = root.querySelector('.tutorial-collapsed');
    if (card && card.contains(ev.target)) return;
    if (bar && bar.contains(ev.target)) return;
    root.classList.add('is-interacting');
    const clear = () => {
      if (root) root.classList.remove('is-interacting');
      document.removeEventListener('pointerup', clear, true);
      document.removeEventListener('pointercancel', clear, true);
    };
    document.addEventListener('pointerup', clear, true);
    document.addEventListener('pointercancel', clear, true);
  }

  function end({ markAsSeen = true } = {}) {
    if (!root) return;
    if (markAsSeen) markSeen();
    if (onResize) {
      window.removeEventListener('resize', onResize);
      window.removeEventListener('scroll', onResize, true);
      onResize = null;
    }
    document.removeEventListener('keydown', onKey, true);
    document.removeEventListener('pointerdown', onGlobalPointerDown, true);
    document.body.classList.remove('tutorial-target-in-header');
    stopLiveLoop();
    calloutEls = [];
    currentPoint = null;
    // Batch 5: tear down checklist watchers + per-slide DOM listeners.
    for (const un of taskStateUnsubs) { try { un(); } catch {} }
    taskStateUnsubs = [];
    teardownTaskDom();
    taskDone = [];
    taskBaselines = [];
    root.classList.add('is-leaving');
    const node = root;
    root = null;
    setTimeout(() => { try { node.remove(); } catch {} }, 180);
    // Restore left rail on mobile if we opened it for a step.
    if (state && isMobile() && savedRailOpen === false) {
      state.set({ leftRailOpen: false });
    }
    savedRailOpen = null;
  }

  function onKey(ev) {
    if (!root) return;
    if (ev.key === 'Escape')      { ev.preventDefault(); end(); }
    else if (ev.key === 'ArrowRight') { ev.preventDefault(); next(); }
    else if (ev.key === 'ArrowLeft')  { ev.preventDefault(); back(); }
    else if (ev.key === 'Enter')      { ev.preventDefault(); next(); }
  }

  function next() {
    if (stepIdx >= steps.length - 1) { end(); return; }
    stepIdx += 1;
    renderStep();
  }
  function back() {
    if (stepIdx <= 0) return;
    stepIdx -= 1;
    renderStep();
  }

  /* --- Mobile collapse/expand --- */

  function collapse() {
    if (!root || collapsed) return;
    collapsed = true;
    root.classList.add('is-collapsed');
    updateCollapsedBar();
    // Only the card is hidden (CSS). The dim panels + ring stay so the
    // highlight remains, but the dims go pointer-events:none (CSS) so the
    // app behind is fully touchable; the live loop keeps everything tracking.
    scheduleReposition();
  }

  function expand() {
    if (!root || !collapsed) return;
    collapsed = false;
    root.classList.remove('is-collapsed');
    /* Do NOT call renderStep() here: that re-fires the slide's beforeShow
     * (which resets the scene / filters) and re-inits the checklist back to
     * task 1 — the "collapsing resets me to step 1" bug. The card DOM still
     * holds the current slide (it was only CSS-hidden), so we just refresh
     * the live bits (checklist UI + indicator) and re-measure the spotlight. */
    renderTasksUI();
    updateTaskIndicator();
    scheduleReposition();
  }

  /* The collapsed bar's Next: advance to the next slide AND expand it so
   * the user reads the new slide's full card, mirroring "expand into the
   * next slide" from the spec. On the last slide it finishes the tour. */
  function collapsedNext() {
    if (stepIdx >= steps.length - 1) { end(); return; }
    collapsed = false;
    root.classList.remove('is-collapsed');
    next();
  }

  // Whether the current slide is "done" — every checklist task complete,
  // or the slide has no tasks at all (welcome / wrap-up / pure-info).
  function slideComplete() {
    const tasks = (steps[stepIdx] && steps[stepIdx].tasks) || [];
    if (tasks.length === 0) return true;
    return firstIncompleteIndex() >= tasks.length;
  }

  function updateCollapsedBar() {
    if (!root) return;
    const bar = root.querySelector('.tutorial-collapsed');
    if (!bar) return;
    const step = steps[stepIdx];
    const tasks = (step && step.tasks) || [];
    const progEl = bar.querySelector('.tutorial-collapsed-progress');
    const stepEl = bar.querySelector('.tutorial-collapsed-step');
    const nextBtn = bar.querySelector('.tutorial-collapsed-next');

    if (progEl) progEl.textContent = `${stepIdx + 1}/${steps.length}`;

    let stepText;
    if (tasks.length === 0) {
      // No checklist — show the slide title as the "current step".
      stepText = step ? step.title : '';
    } else {
      const idx = firstIncompleteIndex();
      stepText = idx < tasks.length
        ? tasks[idx].label
        : 'Step complete';
    }
    if (stepEl) stepEl.textContent = stepText;

    if (nextBtn) {
      const done = slideComplete();
      nextBtn.hidden = !done;
      nextBtn.textContent = (step && step.isLast) ? 'Finish' : 'Next →';
    }
  }

  /* Mobile only. When a slide spotlights a control in the (horizontally-
   * scrolling) header, the sticky "Food Map" + ☰ cluster can sit on top of
   * the very button the slide wants tapped — so hide that cluster for the
   * duration of those slides (body class → CSS). Also bring the target into
   * view ONCE if it's currently scrolled off-screen, without pinning the
   * strip (the user can still swipe it afterwards; the ring re-measures and
   * follows). Called from renderStep after beforeShow. */
  function updateHeaderForStep(step) {
    const headerEl = document.querySelector('.app-header');
    if (!isMobile() || !headerEl) {
      document.body.classList.remove('tutorial-target-in-header');
      return;
    }
    const tgt = effectiveTarget(step);
    const selectors = tgt ? (Array.isArray(tgt) ? tgt : [tgt]) : [];
    const inHeader = selectors
      .map(s => document.querySelector(s))
      .filter(el => el && headerEl.contains(el));
    document.body.classList.toggle('tutorial-target-in-header', inHeader.length > 0);
    if (!inHeader.length) {
      /* No header control spotlighted on this slide. Return the strip to
       * its start so controls a PREVIOUS header slide scrolled away come
       * back — most importantly the 3D/Table toggle on the table slide,
       * which slide 8 (camera/theme/settings) leaves scrolled off to the
       * left, hidden under the sticky ☰ + title cluster. */
      if (headerEl.scrollLeft !== 0) headerEl.scrollLeft = 0;
      return;
    }
    // Measure AFTER toggling the class so the hidden cluster's reflow is
    // accounted for, then scroll into view only if currently clipped.
    const hRect = headerEl.getBoundingClientRect();
    let minL = Infinity, maxR = -Infinity;
    for (const el of inHeader) {
      const rc = el.getBoundingClientRect();
      minL = Math.min(minL, rc.left  - hRect.left + headerEl.scrollLeft);
      maxR = Math.max(maxR, rc.right - hRect.left + headerEl.scrollLeft);
    }
    const viewL = headerEl.scrollLeft;
    const viewR = headerEl.scrollLeft + headerEl.clientWidth;
    if (minL < viewL || maxR > viewR) {
      headerEl.scrollLeft = Math.max(0, (minL + maxR) / 2 - headerEl.clientWidth / 2);
    }
  }

  function buildSteps() {
    /* sectionStates lets a slide declare which collapsible panels
     * should be open / closed while it's visible. Panels not named are
     * left alone. The defaults below close the axes panel and color
     * guide so they're hidden until the user reaches the slide that
     * actually explains them (Batch 9.4). */
    const SECTIONS_DEFAULT = { axisControlsOpen: false, legendOpen: false };

    /* Mobile uses touch gestures and a bottom sheet instead of a mouse and
     * a docked right rail, so a handful of steps phrase their instructions
     * differently. Evaluated once when the steps are built. */
    const mob = isMobile();

    return [
      {
        target: null,
        title: 'Welcome to Food Map',
        body:
          'Foods plotted in 3D, where position tells you about their nutrients. ' +
          'The closer a sphere sits to the corner labeled "Best", the lower its ' +
          'calories and carbs and the higher its protein — by default. You can ' +
          'pick any nutrients you like for the three axes.',
        tip: 'Use Next to walk through the basics. Skip ends the tour any time.',
        sectionStates: SECTIONS_DEFAULT,
      },
      {
        target: '#canvas-container',
        title: 'The 3D map',
        body:
          'Every sphere is one food. Color hints at the food group — red for ' +
          'animal, green for plant, blue for dairy (other groups blend in). ' +
          (mob
            ? 'Drag with one finger to orbit, pinch to zoom. Tap a sphere to open ' +
              'its full nutrient breakdown in the panel that slides up from the bottom.'
            : 'Drag to orbit, scroll to zoom (pinch on a trackpad). Click a sphere ' +
              'to open its full nutrient breakdown in the right panel.'),
        tip: (mob ? 'Tap' : 'Click') + ' an axis label to swap which nutrient that axis represents.',
        prefer: 'center',
        // Card pinned out of the way so the whole map stays clickable.
        cardCorner: 'bottom-left',
        // Highlight only the 3D view, not the header bar above it (the canvas
        // sits behind the fixed header).
        clampBelowHeader: true,
        sectionStates: SECTIONS_DEFAULT,
        // The whole map is the target, so these gestures need no point dot —
        // the spotlight ring already frames where to act.
        // Mobile zoom is a pinch (no 'wheel' event fires), so the separate
        // scroll-to-zoom task can't settle there — fold it into the orbit
        // task and use touch verbs.
        tasks: mob ? [
          { label: 'Drag to orbit; pinch to zoom', dom: { event: 'pointerdown', sel: '#canvas-container' } },
          { label: 'Tap a sphere to open its details', changed: s => s.selectedIngredientId },
        ] : [
          { label: 'Drag to orbit the map', dom: { event: 'pointerdown', sel: '#canvas-container' } },
          { label: 'Scroll to zoom in and out', dom: { event: 'wheel', sel: '#canvas-container' } },
          { label: 'Click a sphere to open its details', changed: s => s.selectedIngredientId },
        ],
        beforeShow: () => {
          if (state && state.get('view') !== '3d') state.set({ view: '3d' });
        },
      },
      {
        /* Spotlight spans BOTH the level toggle and the per-100g /
         * per-serving toggle — they're separate controls but logically
         * one decision ("what am I plotting and in what unit?"). */
        target: ['#view-level', '#unit-toggle-slot'],
        title: 'Ingredients, categories, meals',
        body:
          'Look at individual ingredients, broader category groups (like ' +
          '"fruits"), or whole meals. Each level plots the same nutrient space ' +
          'at a different granularity, and every filter you set works at all ' +
          'three levels.',
        bullets: [
          'Try "Meals" to see hundreds of complete dishes positioned by their averages.',
          'The per-100g / per-serving toggle next to it switches the unit every ' +
          'nutrient threshold and table column reads against.',
        ],
        tip: 'Each level re-plots the same space; the unit toggle rescales every nutrient reading.',
        prefer: 'bottom',
        /* Batch 9.5: dim panels go pointer-events: none so the user
         * can actually click dots while the spotlight calls out the
         * level toggle. The card + ring + callouts stay clickable. */
        canvasInteractive: true,
        sectionStates: SECTIONS_DEFAULT,
        tasks: [
          { label: 'Switch to the Meals level', point: { dom: '#view-level' },
            watch: s => s.viewLevel, equals: 'meal' },
          { label: 'Switch between per-serving and per-100g', point: { dom: '#unit-toggle-slot' },
            changed: s => s.nutrientUnit },
        ],
      },
      {
        target: '#rail-left',
        title: 'Nutrient thresholds + filters',
        body:
          (mob
            ? 'This panel (the ☰ menu, top-left) holds every filter. '
            : 'The left rail holds every filter. ') +
          'The very top section is Nutrient ' +
          'thresholds — drag the min/max sliders to filter or score by nutrient. ' +
          'Below it: dietary restrictions, diet & cuisine, food group, category, ' +
          'ingredient, and tag filters. Everything composes.',
        bullets: [
          'Threshold modes: Filter (hide out-of-range) or Score (color visible items by closeness to target).',
          'Per-100g vs per-serving (header toggle) keeps a SEPARATE threshold set for each — switching the unit swaps which set is active.',
          'Threshold ranges (and almost every other setting) persist across reloads.',
        ],
        tip: 'Open the top section and try narrowing one slider — the 3D map and the table both react.',
        prefer: 'right',
        sectionStates: SECTIONS_DEFAULT,
        tasks: [
          // Smart dot: points at the section header until it's expanded, then
          // hops onto the first slider.
          { label: 'Drag a nutrient slider to narrow the range',
            point: () => (document.querySelector('#section-thresholds')?.dataset.collapsed === 'true'
              ? { dom: '#section-thresholds .rail-section-toggle' }
              : { dom: '#section-thresholds .threshold-row' }),
            changed: s => (s.nutrientUnit === 'serving' ? s.thresholdsServing : s.thresholds) },
          { label: 'Switch the mode between Filter and Score',
            point: () => (document.querySelector('#section-thresholds')?.dataset.collapsed === 'true'
              ? { dom: '#section-thresholds .rail-section-toggle' }
              : { dom: '#section-thresholds .threshold-modes' }),
            changed: s => s.thresholdMode },
        ],
        beforeShow: () => {
          if (state && isMobile()) state.set({ leftRailOpen: true });
          if (state && state.get('view') !== '3d') state.set({ view: '3d' });
        },
      },
      {
        target: '#axis-controls',
        title: 'Axes + Zoom to fit',
        body:
          'The Axes panel in the bottom-right lets you pan, zoom, and reset each ' +
          'axis. After you apply filters that cluster every dot into one corner, ' +
          'click "Zoom to fit" to zoom the cube around just those visible dots — ' +
          'the cluster suddenly fills the whole space.',
        tip: '"Filter by axis ranges" sends each axis\'s current window to Nutrient thresholds — handy for converting a zoom into a filter.',
        prefer: 'left',
        /* Batch 9.4: open the axes panel programmatically. The color
         * guide stays closed — its own slide handles that. */
        sectionStates: { axisControlsOpen: true, legendOpen: false },
        tasks: [
          // Smart dot: sits on the X-axis label; once the user clicks it and
          // the picker opens, it hops to the Nutrient dropdown, then returns
          // to the label if they close the picker without choosing.
          // Watches only the axis NUTRIENT identities — "Zoom to fit" changes
          // each axis's constraint, so keying off the whole axes object would
          // let step 2 inadvertently complete this one.
          { label: 'Click any axis label, then pick a different nutrient',
            point: () => (document.querySelector('.axis-picker:not([hidden])')
              ? { dom: '.axis-picker .axis-picker-nutrient' }
              : [{ axisIndex: 0 }, { axisIndex: 1 }, { axisIndex: 2 }]),
            changed: s => (s.axes || []).map(a => a && a.nutrient).join('|') },
          { label: 'Click "Zoom to fit" to frame the visible dots',
            point: cornerTaskPoint('#axis-controls', '#axis-controls .axis-controls-expand',
              '#axis-controls [data-action="fit-visible"]'),
            dom: { event: 'click', sel: '#axis-controls [data-action="fit-visible"]' } },
        ],
        beforeShow: () => {
          if (state && state.get('view') !== '3d') state.set({ view: '3d' });
        },
      },
      /* Batch 9.7: new slide explaining the color scheme. The dual
       * schemes (food_group hues vs additive RGB animal/plant/dairy)
       * aren't obvious from the dots alone — a tester missed them. */
      {
        target: '#legend',
        title: 'Color guide',
        body:
          'Open in the bottom-right. Two schemes — switch between them with the ' +
          'A/P/D vs Food group toggle at the top of the panel:',
        bullets: [
          'A/P/D: each sphere gets an additive RGB blend of three food-group ' +
            'weights. Red = animal, green = plant, blue = dairy. A meal with ' +
            'animal + dairy looks magenta; all three blends toward white.',
          'Food group: each sphere takes its food group\'s single hue (Beverages, ' +
            'Dairy, Fruits, Grains, Vegetables, etc.) — easier to scan when you ' +
            'want to spot one group at a glance.',
          'Unchecking a row in the legend hides every item in that channel / ' +
            'group from the map, the table, and the active-filters chip rail.',
        ],
        tip: 'Try both schemes — the A/P/D blend reveals composite meals, ' +
             'Food group is faster for "show me only the proteins".',
        prefer: 'left',
        /* Batch 9.4: open the legend programmatically; the axes panel
         * closes again so the user's attention isn't split. */
        sectionStates: { axisControlsOpen: false, legendOpen: true },
        // This slide demos hiding groups, so don't let the cross-slide
        // hygiene reset legendHidden while we're on it.
        keepLegend: true,
        tasks: [
          { label: 'Switch the color scheme (A/P/D or Food group)',
            point: cornerTaskPoint('#legend', '#legend .legend-expand', '#legend .legend-scheme'),
            changed: s => s.colorScheme },
          { label: 'Hide a group by unchecking its row',
            point: cornerTaskPoint('#legend', '#legend .legend-expand', '#legend .legend-item'),
            changed: s => s.legendHidden },
        ],
        beforeShow: () => {
          if (state && state.get('view') !== '3d') state.set({ view: '3d' });
          // Score mode tints dots by score and overrides the color scheme, so
          // the color guide wouldn't show. Turn it off and say so.
          if (state && state.get('thresholdMode') === 'score') {
            state.set({ thresholdMode: 'filter' });
            showToast('Switched off Score mode so the color guide shows.');
          }
        },
      },
      /* Active-filters chip rail — the running tally of everything that's
       * narrowing the view. It auto-hides when nothing's on, so we switch a
       * filter on in beforeShow to give the user a chip to clear. */
      {
        target: '#active-filters',
        title: 'Active filters',
        body:
          'Whenever a filter is on, it appears as a chip in the bottom-left — a ' +
          'running list of everything currently narrowing the map and table. ' +
          'We turned one on so you can see it; click the chip to switch it off.',
        tasks: [
          { label: 'Click the chip to clear that filter',
            point: cornerTaskPoint('#active-filters', '#active-filters .active-filters-expand',
              '#active-filters .active-filter-chip-x'),
            changed: s => s.tagFilter },
        ],
        tip: "It's the quickest way to see — and undo — what's filtering your view.",
        // Sit the card right above the bottom-left chip rail (target-relative,
        // left-aligned with #active-filters) instead of pinning it to the far
        // corner. `prefer: 'top'` because the rail hugs the bottom edge.
        prefer: 'top',
        sectionStates: SECTIONS_DEFAULT,
        beforeShow: () => {
          if (state && state.get('view') !== '3d') state.set({ view: '3d' });
          // Put a filter on so the rail — and a chip to clear — is visible.
          if (state) state.set({ tagFilter: ['high-protein'] });
        },
      },
      /* Camera + appearance + settings — the right-side header cluster.
       * One slide because the user reads them as one group ("everything
       * controlling how the app looks and behaves globally"). Multi-
       * target spotlight unions all three rects. */
      {
        target: ['#view-3d-controls', '#theme-toggle-slot', '#config-menu-slot'],
        title: 'Camera, theme, and settings',
        body:
          'The right side of the header has the controls that govern HOW you ' +
          'see the map, not what\'s in it:',
        bullets: [
          'Perspective vs orthographic: orthographic flattens depth so ' +
            'distances along each axis read literally — useful when you\'re ' +
            'comparing exact nutrient values instead of just shape.',
          'X / Y / Z buttons snap the camera to look straight down that axis, ' +
            'collapsing the cube into a 2D scatter of the other two nutrients.',
          'Light / dark theme toggles instantly and persists across reloads.',
          'The ⋯ menu holds Export / Import config as JSON, "Reset to ' +
            'defaults", and "Show tutorial" — your way back to this tour ' +
            'any time.',
        ],
        prefer: 'bottom-left',
        sectionStates: SECTIONS_DEFAULT,
        beforeShow: () => {
          if (state && state.get('view') !== '3d') state.set({ view: '3d' });
          // Clear the demo filter the previous (Active filters) slide turned on.
          if (state && (state.get('tagFilter') || []).length) state.set({ tagFilter: [] });
        },
        tasks: [
          { label: 'Switch between Perspective and Orthographic',
            point: { dom: '#view-3d-controls [data-group="cameraMode"]' },
            changed: s => s.cameraMode },
          { label: 'Snap the camera to an axis with X, Y, or Z',
            point: { dom: '#view-3d-controls [data-action="snap"]' },
            dom: { event: 'click', sel: '#view-3d-controls [data-action="snap"]' } },
          { label: 'Switch the light or dark theme', point: { dom: '#theme-toggle-slot' },
            changed: s => s.theme },
        ],
      },
      {
        target: '#table-container',
        title: 'Or as a table',
        body:
          'Here is the same data as a sortable table. Click any column header to ' +
          'sort, open Columns to show/hide fields and tune the composite-score ' +
          'weights, and every left-rail filter still applies. Use the 3D / Table ' +
          'toggle in the header to switch back any time.',
        tip: 'Switch back to 3D from the header toggle whenever you want the shape view again.',
        // Card bottom-right so it never covers the Columns button or the
        // sortable headers (both along the top of the table).
        cardCorner: 'bottom-right',
        sectionStates: SECTIONS_DEFAULT,
        tasks: [
          { label: 'Sort by a column (e.g. Protein)',
            point: { dom: '.data-table thead .data-th-btn' },
            changed: s => s.tableSort },
          { label: 'Open the Columns menu', point: { dom: '.table-columns-btn' },
            dom: { event: 'click', sel: '.table-columns-btn' } },
        ],
        // Put the user in the table so the steps act on what's highlighted.
        beforeShow: () => {
          if (state && state.get('view') !== 'table') state.set({ view: 'table' });
        },
      },
      /* Guided use-case flows — gated, do-it-yourself checklists. Three in
       * order: fit-nutrients (Batch 5), meals-from-held-ingredients and
       * remix-a-meal (Batch 6). */
      {
        target: null,
        title: 'Try it: meals that fit your nutrients',
        body:
          'A quick run-through of the most common goal — find whole meals that ' +
          'match a nutrient target. Do each step in order; the next one unlocks ' +
          'as you go, and the pulsing dot shows where to click.',
        tasks: [
          { label: 'Switch to the Meals level', point: { dom: '#view-level' },
            watch: s => s.viewLevel, equals: 'meal' },
          { label: "Raise a nutrient's minimum on a slider",
            point: () => (document.querySelector('#section-thresholds')?.dataset.collapsed === 'true'
              ? { dom: '#section-thresholds .rail-section-toggle' }
              : { dom: '#section-thresholds .threshold-row' }),
            changed: s => (s.nutrientUnit === 'serving' ? s.thresholdsServing : s.thresholds) },
          { label: 'Switch the mode to Score to rank meals by fit',
            point: () => (document.querySelector('#section-thresholds')?.dataset.collapsed === 'true'
              ? { dom: '#section-thresholds .rail-section-toggle' }
              : { dom: '#section-thresholds .threshold-modes' }),
            watch: s => s.thresholdMode, equals: 'score' },
        ],
        tip: 'The surviving meals are now tinted green→red by how well they hit ' +
             'your target — open one to see its ingredients.',
        // Bottom-right keeps the header level toggle and the left rail clear.
        cardCorner: 'bottom-right',
        sectionStates: SECTIONS_DEFAULT,
        beforeShow: () => {
          // Start the demo from a clean scene (no leftover filters/score-mode).
          resetScene();
          collapseLeftRailSections();
          if (state && state.get('view') !== '3d') state.set({ view: '3d' });
          if (state && isMobile()) state.set({ leftRailOpen: true });
        },
      },
      /* Batch 6: use-case flow #2 — which meals can I make from the
       * ingredients I have? Uses the meal-level ingredient filter (Batch 3),
       * which matches each meal's specific example_ingredients. */
      {
        target: null,
        title: 'Try it: meals from ingredients you have',
        body:
          'Got a few ingredients and want ideas? We have cleared the ingredient ' +
          'list — select the ingredients you have in "Filter by ingredient", and ' +
          'the map narrows to meals that actually use them (matched by specific ' +
          'ingredient, not category).',
        tasks: [
          { label: 'Switch to the Meals level', point: { dom: '#view-level' },
            watch: s => s.viewLevel, equals: 'meal' },
          // Smart dot: section header until expanded, then the search box (the
          // quick way to find an ingredient to click in the long tree).
          { label: 'Select the ingredients you have',
            point: () => (document.querySelector('#section-ingredient')?.dataset.collapsed === 'true'
              ? { dom: '#section-ingredient .rail-section-toggle' }
              : { dom: '#section-ingredient .ingredient-filter-search' }),
            changed: s => s.ingredientFilter },
          { label: 'Choose AND (uses all) or OR (uses any)',
            point: { dom: '#section-ingredient .filter-match-toggle' },
            dom: { event: 'click', sel: '.filter-match-toggle' } },
        ],
        tip: 'Set "Allow extras" to ALL for meals you can make with ONLY what you have.',
        // Bottom-right keeps the header level toggle and the left rail clear.
        cardCorner: 'bottom-right',
        sectionStates: SECTIONS_DEFAULT,
        beforeShow: () => {
          // Clean slate, then start the ingredient filter from EMPTY so the
          // single step "select the ingredients you have" is all it takes.
          resetScene();
          collapseLeftRailSections();
          if (state) state.set({ ingredientFilter: { excludedIds: getAllIngredientIds() } });
          if (state && state.get('view') !== '3d') state.set({ view: '3d' });
          if (state && isMobile()) state.set({ leftRailOpen: true });
        },
      },
      /* Use-case flow #3 — reshape meals. Primary tool is the left-rail
       * "Modify all meals" overlay (Phase 35: inject/strip a category across
       * EVERY meal, state.mealComposition); the per-meal right-rail Remix
       * (Batch 4) is the final step as a one-dish alternative. */
      {
        target: null,
        title: 'Try it: reshape meals to fit you',
        body:
          '"Modify all meals" (left rail) is a global what-if: inject or strip a ' +
          'whole category across every meal at once — drop refined grains from ' +
          'everything, or add leafy greens to every dish — and the meal dots ' +
          'reposition together. Want to change just one dish instead? Remix it ' +
          'per-meal as the final step.',
        tasks: [
          { label: 'Switch to the Meals level', point: { dom: '#view-level' },
            watch: s => s.viewLevel, equals: 'meal' },
          // Smart dot: section header until expanded, then the +/− list.
          { label: 'In "Modify all meals", add (+) or remove (−) a category',
            point: () => (document.querySelector('#section-modify-meals')?.dataset.collapsed === 'true'
              ? { dom: '#section-modify-meals .rail-section-toggle' }
              : { dom: '#section-modify-meals .compose-meals-list' }),
            changed: s => s.mealComposition },
          // Per-meal alternative. Smart dot: click a meal first (canvas), then
          // the Remix controls once the detail panel exists.
          { label: 'Or tweak one dish: open a meal and swap an ingredient in Remix',
            point: () => (document.querySelector('.detail-remix')
              ? { dom: '.detail-remix' }
              : { dom: '#canvas-container' }),
            changed: s => s.mealDraft },
        ],
        tip: 'Modify-all reshapes the whole set ("what if every meal were lower-' +
             'carb?"); Remix saves a single custom dish to Your meals.',
        // Bottom-center clears BOTH side rails — step 2 lives in the left rail,
        // step 3 in the right-rail Remix panel.
        cardCorner: 'bottom-center',
        sectionStates: SECTIONS_DEFAULT,
        beforeShow: () => {
          // Clean slate — clears the held-ingredient filter from the previous
          // flow so meals are visible/clickable here.
          resetScene();
          collapseLeftRailSections();
          // Start the global overlay empty so step 2's baseline is empty and
          // only a real +/− completes it.
          if (state) state.set({ mealComposition: { added: [], removed: [] } });
          if (state && state.get('view') !== '3d') state.set({ view: '3d' });
          if (state && isMobile()) state.set({ leftRailOpen: true });
          // Clear any stale remix draft so step 3 only completes on a real edit
          // (selecting a meal clears the draft, so it can't false-complete).
          if (state && state.get('mealDraft')) state.set({ mealDraft: null });
        },
      },
      {
        // Centered, no spotlight — a prominent wrap-up. (No tasks here, so
        // nothing to point at; the ⋯ menu is referenced in the bullets.)
        target: null,
        title: "You're set",
        body:
          'A few extras you\'ll probably want:',
        bullets: [
          /* Batch 9.8: first bullet calls out when each view earns
           * its keep. Tester didn't grok why 3D existed at all. */
          '3D vs Table — 3D is the right tool for "show me the shape of ' +
            'this dataset" (clusters, outliers, where the bulk of foods sit). ' +
            'Table is the right tool for "rank these by X" or "show me a ' +
            'precise nutrient column". Most workflows hop between them.',
          'Search any food, category, or meal by name in the header search.',
          'Color guide (bottom-right): uncheck rows to hide whole food groups.',
          'Build your own meals in the left rail\'s "Your meals" section.',
          'Toggle theme and per-serving vs per-100g from the header.',
          'Active filters chip rail (bottom-left) shows everything currently on — click any chip to clear it.',
          'Restart this tour any time from this menu.',
        ],
        tip: 'Hit "Got it" to start exploring.',
        isLast: true,
        sectionStates: SECTIONS_DEFAULT,
        beforeShow: () => {
          if (state && state.get('view') !== '3d') state.set({ view: '3d' });
        },
      },
    ];
  }

  function buildDom() {
    root = document.createElement('div');
    root.className = 'tutorial';
    root.innerHTML = `
      <div class="tutorial-dim tutorial-dim-top"    data-tutorial-advance="0"></div>
      <div class="tutorial-dim tutorial-dim-right"  data-tutorial-advance="0"></div>
      <div class="tutorial-dim tutorial-dim-bottom" data-tutorial-advance="0"></div>
      <div class="tutorial-dim tutorial-dim-left"   data-tutorial-advance="0"></div>
      <div class="tutorial-ring" aria-hidden="true"></div>
      <div class="tutorial-card" role="dialog" aria-live="polite" aria-labelledby="tutorial-title">
        <div class="tutorial-meta">
          <span class="tutorial-progress"></span>
          <button class="tutorial-skip-x" type="button" aria-label="End tour">×</button>
        </div>
        <h3 class="tutorial-title" id="tutorial-title"></h3>
        <p class="tutorial-body"></p>
        <ul class="tutorial-bullets" hidden></ul>
        <ol class="tutorial-tasks" hidden></ol>
        <p class="tutorial-tip" hidden></p>
        <div class="tutorial-dots" aria-hidden="true"></div>
        <div class="tutorial-actions">
          <button class="btn tutorial-skip"  type="button">Skip tour</button>
          <span class="tutorial-actions-spacer"></span>
          <button class="btn tutorial-back"  type="button">Back</button>
          <button class="btn btn-primary tutorial-next" type="button">Next →</button>
        </div>
      </div>
      <div class="tutorial-collapsed" role="region" aria-label="Guided tour (collapsed)">
        <div class="tutorial-collapsed-text">
          <span class="tutorial-collapsed-title">
            Guided tour <span class="tutorial-collapsed-progress muted"></span>
          </span>
          <span class="tutorial-collapsed-step"></span>
        </div>
        <button class="btn btn-primary tutorial-collapsed-next" type="button" hidden>Next →</button>
        <button class="tutorial-collapsed-expand" type="button"
                aria-label="Expand the tour" title="Expand the tour">⤢</button>
      </div>
    `;
    document.body.appendChild(root);

    root.querySelector('.tutorial-next').addEventListener('click', next);
    root.querySelector('.tutorial-back').addEventListener('click', back);
    root.querySelector('.tutorial-skip').addEventListener('click', () => end());
    // Mobile: × tucks the tour into the collapsed bar instead of ending it.
    // Desktop keeps the original dismiss behavior.
    root.querySelector('.tutorial-skip-x').addEventListener('click', () => {
      if (isMobile()) collapse(); else end();
    });
    root.querySelector('.tutorial-collapsed-expand').addEventListener('click', expand);
    root.querySelector('.tutorial-collapsed-next').addEventListener('click', collapsedNext);

    // Dim panels swallow clicks so the user can't accidentally interact
    // with the app outside the highlighted target. They don't advance —
    // Next / Back / Skip are the only controls.
    root.querySelectorAll('.tutorial-dim').forEach(panel => {
      panel.addEventListener('click', (ev) => ev.stopPropagation());
    });
  }

  function renderStep() {
    if (!root) return;
    const step = steps[stepIdx];
    const card  = root.querySelector('.tutorial-card');
    const title = root.querySelector('.tutorial-title');
    const body  = root.querySelector('.tutorial-body');
    const tip   = root.querySelector('.tutorial-tip');
    const prog  = root.querySelector('.tutorial-progress');
    const back  = root.querySelector('.tutorial-back');
    const nextB = root.querySelector('.tutorial-next');
    const skip  = root.querySelector('.tutorial-skip');
    const dots  = root.querySelector('.tutorial-dots');

    /* Batch 9.4: apply per-slide section states (axes panel + color
     * guide) BEFORE beforeShow so the slide's own beforeShow can still
     * override on a case-by-case basis. */
    if (state && step.sectionStates) {
      for (const [key, want] of Object.entries(step.sectionStates)) {
        if (state.get(key) !== want) state.set({ [key]: want });
      }
    }

    /* Mobile: start every slide with the floating corner panels (color
     * guide, axes, active filters) AND the left filter drawer collapsed.
     * They eat the small screen, and the per-slide auto-open from
     * sectionStates above is disorienting on a phone — instead the
     * checklist's smart callout dot points at the relevant pill/section so
     * the user opens it themselves. This also gives each slide a clean
     * slate (nothing left open from the previous slide). Slides that
     * genuinely need the drawer (thresholds, the use-case flows) reopen it
     * in their beforeShow below, which runs AFTER this. */
    if (state && isMobile()) {
      const patch = {};
      for (const k of ['legendOpen', 'axisControlsOpen', 'activeFiltersOpen', 'leftRailOpen']) {
        if (state.get(k) !== false) patch[k] = false;
      }
      if (Object.keys(patch).length) state.set(patch);
    }

    /* Mobile: the × isn't a dismiss — it tucks the tour into the top bar.
     * Label it so the user knows where it's going. Desktop keeps the plain
     * close ×. (Set every render since the breakpoint can change on resize.) */
    const skipX = root.querySelector('.tutorial-skip-x');
    if (skipX) {
      if (isMobile()) {
        skipX.innerHTML = 'Hide <span aria-hidden="true">▴</span>';
        skipX.setAttribute('aria-label', 'Hide the tour (collapses to the top)');
        skipX.classList.add('is-hide');
      } else {
        skipX.textContent = '×';
        skipX.setAttribute('aria-label', 'End tour');
        skipX.classList.remove('is-hide');
      }
    }

    /* Round 3: cross-slide hygiene — unless this slide is the color guide
     * (which lets the user hide groups as a demo), clear any hidden legend
     * rows so the scene isn't mysteriously empty on a later slide. */
    if (state && !step.keepLegend) {
      const lh = state.get('legendHidden') || {};
      if ((lh.rgb && lh.rgb.length) || (lh.food_group && lh.food_group.length)) {
        state.set({ legendHidden: { rgb: [], food_group: [] } });
      }
    }

    if (step.beforeShow) {
      try { step.beforeShow(); } catch {}
    }

    /* Batch 9.5 / Batch 5: slides that want clicks to pass through to the
     * app (e.g. "click a dot", or any slide with interactive tasks) get
     * pointer-events: none on the dim panels via this root-level class. */
    const hasTasks = Array.isArray(step.tasks) && step.tasks.length > 0;
    root.classList.toggle('is-canvas-interactive', !!step.canvasInteractive || hasTasks);

    /* Batch 5: (re)initialise this slide's checklist. initTasksForStep also
     * (re)builds the on-screen indicator — pointing at the active task, or
     * the slide's static callouts when it has none. */
    initTasksForStep(step);

    title.textContent = step.title;
    body.textContent  = step.body;
    const bullets = root.querySelector('.tutorial-bullets');
    bullets.innerHTML = '';
    if (Array.isArray(step.bullets) && step.bullets.length > 0) {
      bullets.hidden = false;
      for (const b of step.bullets) {
        const li = document.createElement('li');
        li.textContent = b;
        bullets.appendChild(li);
      }
    } else {
      bullets.hidden = true;
    }
    if (step.tip) {
      tip.hidden = false;
      tip.textContent = step.tip;
    } else {
      tip.hidden = true;
      tip.textContent = '';
    }
    prog.textContent  = `${stepIdx + 1} of ${steps.length}`;
    back.disabled     = stepIdx === 0;
    nextB.textContent = step.isLast ? 'Got it' : 'Next →';
    skip.hidden       = !!step.isLast;

    // Dot indicator
    dots.innerHTML = '';
    for (let i = 0; i < steps.length; i++) {
      const d = document.createElement('span');
      d.className = 'tutorial-dot' + (i === stepIdx ? ' is-active' : '');
      dots.appendChild(d);
    }

    card.classList.remove('is-centered');
    root.classList.toggle('is-centered', !step.target);

    updateHeaderForStep(step);
    updateCollapsedBar();
    scheduleReposition();
  }

  function startLiveLoop() {
    stopLiveLoop();
    const tick = () => {
      if (!root) return;
      reposition();
      positionCallouts();
      reposRAF = requestAnimationFrame(tick);
    };
    reposRAF = requestAnimationFrame(tick);
  }
  function stopLiveLoop() {
    if (reposRAF) { cancelAnimationFrame(reposRAF); reposRAF = 0; }
  }
  // Immediate one-shot (render / resize / scroll) — the live loop keeps it
  // aligned thereafter.
  function scheduleReposition() {
    if (root) reposition();
  }

  function reposition() {
    if (!root) return;

    /* The collapse affordance is a mobile convenience; if the viewport grew
     * back to desktop while collapsed, re-expand. */
    if (collapsed && !isMobile()) { expand(); return; }

    /* When collapsed we keep the spotlight (dim panels + ring) so the
     * highlighted region stays highlighted and the user can still see —
     * and, on interactive task slides, touch — what the step is about. Only
     * the big card is hidden (via CSS), replaced by the slim top bar. So
     * the positioning below runs in BOTH states; the card just isn't
     * visible while collapsed. */
    const step = steps[stepIdx];
    const ring = root.querySelector('.tutorial-ring');
    const card = root.querySelector('.tutorial-card');
    const dimTop    = root.querySelector('.tutorial-dim-top');
    const dimRight  = root.querySelector('.tutorial-dim-right');
    const dimBottom = root.querySelector('.tutorial-dim-bottom');
    const dimLeft   = root.querySelector('.tutorial-dim-left');

    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const tgt = effectiveTarget(step);

    if (!tgt) {
      // No spotlight — single full-screen dim. A cardCorner keeps the card
      // out of the way of the controls the slide's tasks point at; otherwise
      // center it.
      ring.hidden = true;
      Object.assign(dimTop.style,    fullPanel());
      Object.assign(dimRight.style,  hiddenPanel());
      Object.assign(dimBottom.style, hiddenPanel());
      Object.assign(dimLeft.style,   hiddenPanel());
      if (step.cardCorner) {
        card.classList.remove('is-centered');
        pinCardToCorner(card, step.cardCorner, vw, vh);
      } else {
        card.classList.add('is-centered');
        centerCard(card, vw, vh);
      }
      return;
    }

    /* Batch 9 follow-up: `target` may be a string OR an array of
     * strings. Array form unions the bounding rects so a single
     * spotlight can span two adjacent header controls (the
     * Ingredients/Categories/Meals toggle and the per-100g/serving
     * toggle, in particular). Missing selectors are skipped; if none
     * resolve, fall back to centered. */
    const selectors = Array.isArray(tgt) ? tgt : [tgt];
    const els = selectors.map(sel => document.querySelector(sel)).filter(Boolean);
    /* The header is a horizontal-scroll strip on mobile; we bring a
     * spotlighted header control into view ONCE per slide (updateHeaderForStep,
     * called from renderStep) rather than re-centering every frame here —
     * the latter pinned scrollLeft and made the strip impossible to swipe.
     * The ring/dims below re-measure each frame, so they still follow the
     * target as the user scrolls it around. */
    const rects = [];
    for (const el of els) {
      const rc = el.getBoundingClientRect();
      if (rc.width === 0 && rc.height === 0) continue;
      rects.push(rc);
    }
    if (rects.length === 0) {
      // Target missing (e.g. element conditionally rendered). Fall back
      // to full-screen dim; keep the card in its corner if pinned, else
      // center it.
      ring.hidden = true;
      Object.assign(dimTop.style,    fullPanel());
      Object.assign(dimRight.style,  hiddenPanel());
      Object.assign(dimBottom.style, hiddenPanel());
      Object.assign(dimLeft.style,   hiddenPanel());
      if (step.cardCorner) {
        card.classList.remove('is-centered');
        pinCardToCorner(card, step.cardCorner, vw, vh);
        return;
      }
      card.classList.add('is-centered');
      centerCard(card, vw, vh);
      return;
    }
    // Union the rects into a single DOMRect-ish struct.
    let uTop    = Infinity, uLeft   = Infinity;
    let uBottom = -Infinity, uRight = -Infinity;
    for (const rc of rects) {
      if (rc.top    < uTop)    uTop    = rc.top;
      if (rc.left   < uLeft)   uLeft   = rc.left;
      if (rc.bottom > uBottom) uBottom = rc.bottom;
      if (rc.right  > uRight)  uRight  = rc.right;
    }
    const r = { top: uTop, left: uLeft, bottom: uBottom, right: uRight };
    /* Clamp the rect to the viewport. An off-screen rail or a rect
     * that's wider than the viewport produces a useless cutout
     * otherwise. */
    let   t = Math.max(0, Math.min(vh, r.top    - RING_PADDING));
    const b = Math.max(0, Math.min(vh, r.bottom + RING_PADDING));
    /* The canvas spans the full viewport BEHIND the fixed header (.app-main is
     * inset:0), so a raw #canvas-container rect would put the header inside the
     * spotlight. clampBelowHeader pushes the cutout's top below the header so
     * only the 3D view is highlighted. */
    if (step.clampBelowHeader) {
      const header = document.querySelector('.app-header');
      if (header) t = Math.min(b, Math.max(t, header.getBoundingClientRect().bottom));
    }
    const l = Math.max(0, Math.min(vw, r.left   - RING_PADDING));
    const ri= Math.max(0, Math.min(vw, r.right  + RING_PADDING));

    Object.assign(dimTop.style, {
      display: 'block', left: '0px', top: '0px',
      width:  vw + 'px', height: t + 'px',
    });
    Object.assign(dimBottom.style, {
      display: 'block', left: '0px', top: b + 'px',
      width:  vw + 'px', height: Math.max(0, vh - b) + 'px',
    });
    Object.assign(dimLeft.style, {
      display: 'block', left: '0px', top: t + 'px',
      width:  l + 'px', height: Math.max(0, b - t) + 'px',
    });
    Object.assign(dimRight.style, {
      display: 'block', left: ri + 'px', top: t + 'px',
      width:  Math.max(0, vw - ri) + 'px', height: Math.max(0, b - t) + 'px',
    });

    ring.hidden = false;
    Object.assign(ring.style, {
      left:   l + 'px',
      top:    t + 'px',
      width:  Math.max(0, ri - l) + 'px',
      height: Math.max(0, b - t) + 'px',
    });

    card.classList.remove('is-centered');
    if (step.cardCorner) {
      // Pin to a fixed corner regardless of the target — used where the
      // target-relative card would cover another control the slide needs.
      pinCardToCorner(card, step.cardCorner, vw, vh);
    } else {
      placeCard(card, { l, t, r: ri, b }, step.prefer || 'bottom', vw, vh);
    }
  }

  /* Center the card in the viewport. The card is position:absolute inside a
   * full-screen fixed overlay that does NOT itself center, and the entrance
   * animation uses `transform`, so CSS transform-centering would fight it —
   * hence explicit left/top like pinCardToCorner (matches the "Layout JS still
   * sets left/top" note on the .is-centered CSS rule). Used by the welcome and
   * wrap-up slides (target null, no cardCorner). */
  function centerCard(card, vw, vh) {
    card.style.right = '';
    card.style.bottom = '';
    const cw = Math.min(360, vw - VIEWPORT_PAD * 2);
    card.style.width = cw + 'px';
    const ch = card.offsetHeight || 200;
    card.style.left = Math.max(VIEWPORT_PAD, (vw - cw) / 2) + 'px';
    card.style.top  = Math.max(VIEWPORT_PAD, (vh - ch) / 2) + 'px';
  }

  /* Pin the card to a screen corner: '{top|bottom}-{left|center|right}'. */
  function pinCardToCorner(card, corner, vw, vh) {
    card.style.left = '';
    card.style.top = '';
    card.style.right = '';
    card.style.bottom = '';
    const cw = Math.min(360, vw - VIEWPORT_PAD * 2);
    card.style.width = cw + 'px';
    const ch = card.offsetHeight || 200;
    const isTop = corner.startsWith('top');
    card.style.top = (isTop ? VIEWPORT_PAD : Math.max(VIEWPORT_PAD, vh - ch - VIEWPORT_PAD)) + 'px';
    if (corner.endsWith('center')) {
      card.style.left = Math.max(VIEWPORT_PAD, (vw - cw) / 2) + 'px';
    } else if (corner.endsWith('right')) {
      card.style.left = Math.max(VIEWPORT_PAD, vw - cw - VIEWPORT_PAD) + 'px';
    } else {
      card.style.left = VIEWPORT_PAD + 'px';
    }
  }

  /* ---- Batch 5: interactive checklist ---- */

  // Slices any task might key off. A single change in any of these re-runs
  // checkTasks for the current slide. (state.set mutates in place, so we can't
  // subscribe to "any change" — this fixed list is the explicit surface.)
  const TASK_WATCH_SLICES = [
    s => s.viewLevel, s => s.view, s => s.nutrientUnit,
    s => s.thresholds, s => s.thresholdsServing, s => s.thresholdMode,
    s => s.colorScheme, s => s.legendHidden, s => s.cameraMode, s => s.theme,
    s => s.tableSort, s => s.selectedIngredientId, s => s.axes,
    // Batch 6 use-case flows: ingredient filter + meal remix draft.
    s => s.ingredientFilter, s => s.ingredientFilterMatch,
    s => s.ingredientFilterScope, s => s.mealDraft,
    s => s.tagFilter,   // active-filters slide
    s => s.mealComposition, // slide 12: "Modify all meals" overlay
  ];
  function wireTaskStateWatchers() {
    if (!state) return;
    for (const sel of TASK_WATCH_SLICES) {
      taskStateUnsubs.push(state.subscribe(sel, () => checkTasks()));
    }
  }

  function firstIncompleteIndex() {
    const idx = taskDone.findIndex(d => !d);
    return idx === -1 ? taskDone.length : idx;
  }

  /* The element the spotlight ring frames. Slides with an explicit `target`
   * (the retrofitted 2–8) keep framing it. Task slides with no target (the
   * use-case flows) ring the ACTIVE step's DOM point instead, so the blue
   * border wraps the left rail / right panel / header control for the step
   * you're on — and moves to the next as you complete each. Axis-anchored
   * points (3D sprites) have no DOM rect, so those fall back to no ring. */
  function effectiveTarget(step) {
    if (step && step.target) return step.target;
    const tasks = (step && step.tasks) || [];
    if (tasks.length > 0) {
      const idx = firstIncompleteIndex();
      const active = idx < tasks.length ? tasks[idx] : null;
      // Ring the first DOM-anchored point of the active step (axis-only
      // points have no DOM rect, so they get a dot but no ring).
      for (const s of resolvePoints(active && active.point)) {
        if (s && s.dom) return s.dom;
      }
    }
    return null;
  }

  function teardownTaskDom() {
    for (const c of taskDomCleanup) { try { c(); } catch {} }
    taskDomCleanup = [];
  }

  function initTasksForStep(step) {
    teardownTaskDom();
    const tasks = (step && step.tasks) || [];
    taskDone = tasks.map(() => false);
    const st = state ? state.get() : null;
    taskBaselines = tasks.map(t => (typeof t.changed === 'function' && st) ? t.changed(st) : undefined);

    // DOM-event tasks: delegated on document (capture) so they fire even for
    // controls created after the slide opens (e.g. the table Columns button).
    tasks.forEach((t, i) => {
      if (!t.dom) return;
      const handler = (ev) => {
        if (firstIncompleteIndex() !== i) return;      // gated: not its turn
        if (!(ev.target && ev.target.closest && ev.target.closest(t.dom.sel))) return;
        taskDone[i] = true;
        renderTasksUI(); updateTaskIndicator(); checkTasks();
      };
      document.addEventListener(t.dom.event, handler, true);
      taskDomCleanup.push(() => document.removeEventListener(t.dom.event, handler, true));
    });

    renderTasksUI();
    updateTaskIndicator();
    // A watch/equals task can be satisfied the moment the slide opens — settle.
    checkTasks();
  }

  function checkTasks() {
    if (!root) return;
    const step = steps[stepIdx];
    const tasks = (step && step.tasks) || [];
    // Guard: beforeShow can mutate state (firing this) before initTasksForStep
    // has reset taskDone to the new slide's length. Skip until they match.
    if (tasks.length === 0 || taskDone.length !== tasks.length) return;
    const st = state ? state.get() : null;
    let changed = false;
    for (let i = 0; i < tasks.length; i++) {
      if (taskDone[i]) continue;
      const t = tasks[i];
      let done = false;
      if (st) {
        if (typeof t.watch === 'function') done = t.watch(st) === t.equals;
        else if (typeof t.changed === 'function') done = t.changed(st) !== taskBaselines[i];
      }
      if (done) { taskDone[i] = true; changed = true; continue; }
      break; // first not-done active task (DOM tasks settle via their handler)
    }
    if (changed) { renderTasksUI(); updateTaskIndicator(); }
  }

  function renderTasksUI() {
    if (!root) return;
    const wrap = root.querySelector('.tutorial-tasks');
    if (!wrap) return;
    const tasks = (steps[stepIdx] && steps[stepIdx].tasks) || [];
    if (tasks.length === 0) { wrap.hidden = true; wrap.innerHTML = ''; return; }
    wrap.hidden = false;
    const active = firstIncompleteIndex();
    wrap.innerHTML = '';
    tasks.forEach((t, i) => {
      const li = document.createElement('li');
      li.className = 'tutorial-task ' +
        (taskDone[i] ? 'is-done' : i === active ? 'is-active' : 'is-locked');
      const mark = document.createElement('span');
      mark.className = 'tutorial-task-mark';
      mark.setAttribute('aria-hidden', 'true');
      mark.textContent = taskDone[i] ? '✓' : String(i + 1);
      const label = document.createElement('span');
      label.className = 'tutorial-task-label';
      label.textContent = t.label;
      li.appendChild(mark);
      li.appendChild(label);
      wrap.appendChild(li);
    });
    wrap.classList.toggle('is-complete', active >= tasks.length);
  }

  // The on-screen indicator follows the active task; with no tasks it falls
  // back to the slide's static callouts.
  function updateTaskIndicator() {
    const step = steps[stepIdx];
    const tasks = (step && step.tasks) || [];
    if (tasks.length > 0) {
      // Show the ACTIVE step's indicator. Its `point` may resolve to several
      // dots (e.g. one per axis) and move/change as the UI changes.
      const idx = firstIncompleteIndex();
      const active = idx < tasks.length ? tasks[idx] : null;
      currentPoint = active ? active.point : null;
    } else {
      currentPoint = (step && step.callouts) || null;
    }
    // Keep the collapsed bar's step text + Next button in sync as tasks
    // complete (this runs on every task-state change).
    updateCollapsedBar();
    /* Re-sync the header for the now-active task: on the use-case flows the
     * focus moves from a header control (e.g. "Switch to the Meals level"
     * → #view-level) onto the left rail, so the ☰/title cluster should
     * reappear and the strip reset once the header step is done. */
    updateHeaderForStep(step);
    positionCallouts();
  }

  /* Resolve an indicator source into a flat array of specs. A source can be:
   *   - a spec object: { dom: '<selector>' } | { axisIndex: 0|1|2 }
   *   - a function returning a spec OR an array of specs (re-run each frame,
   *     so a "smart" dot tracks moving targets AND the count can change —
   *     e.g. 3 axis labels collapsing to 1 picker dropdown, or a section
   *     header that becomes a slider once expanded)
   *   - an array of any of the above */
  function resolvePoints(src) {
    if (!src) return [];
    let p = src;
    if (typeof p === 'function') { try { p = p(); } catch { return []; } }
    if (!p) return [];
    const arr = Array.isArray(p) ? p : [p];
    const out = [];
    for (let el of arr) {
      if (typeof el === 'function') { try { el = el(); } catch { el = null; } }
      if (el) out.push(el);
    }
    return out;
  }

  /* Position the indicator dots every frame (driven by the live loop). The
   * current point source is resolved fresh so dots track moving DOM targets /
   * orbiting axis sprites and a changing dot count; the node pool grows as
   * needed and unused nodes are hidden. */
  function positionCallouts() {
    if (!root) return;
    const specs = resolvePoints(currentPoint);
    while (calloutEls.length < specs.length) {
      const node = document.createElement('div');
      node.className = 'tutorial-callout';
      root.appendChild(node);
      calloutEls.push(node);
    }
    const camera = typeof getCamera === 'function' ? getCamera() : null;
    const canvas = typeof getCanvas === 'function' ? getCanvas() : null;
    const sprites = typeof getAxisNameSprites === 'function'
      ? getAxisNameSprites() : null;
    for (let i = 0; i < calloutEls.length; i++) {
      const node = calloutEls[i];
      const spec = i < specs.length ? specs[i] : null;
      if (!spec) { node.hidden = true; continue; }
      if (spec.dom) {
        const el = document.querySelector(spec.dom);
        if (!el) { node.hidden = true; continue; }
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) { node.hidden = true; continue; }
        node.hidden = false;
        node.style.left = `${Math.round(rect.right - 8)}px`;
        node.style.top  = `${Math.round(rect.top - 8)}px`;
      } else if (typeof spec.axisIndex === 'number') {
        if (!camera || !canvas || !sprites || !sprites[spec.axisIndex]) {
          node.hidden = true; continue;
        }
        const pos = sprites[spec.axisIndex].position;
        const { x, y } = worldToClient(pos, camera, canvas);
        if (!Number.isFinite(x) || !Number.isFinite(y)) {
          node.hidden = true; continue;
        }
        node.hidden = false;
        node.style.left = `${Math.round(x - 9)}px`;
        node.style.top  = `${Math.round(y - 9)}px`;
      } else {
        node.hidden = true;
      }
    }
  }

  function placeCard(card, rect, prefer, vw, vh) {
    // Reset
    card.style.left = '';
    card.style.top  = '';
    card.style.right = '';
    card.style.bottom = '';

    const cw = Math.min(360, vw - VIEWPORT_PAD * 2);
    card.style.width = cw + 'px';
    const ch = card.offsetHeight || 200;

    const spaceBelow = vh - rect.b - CARD_GAP;
    const spaceAbove = rect.t - CARD_GAP;
    const spaceRight = vw - rect.r - CARD_GAP;
    const spaceLeft  = rect.l - CARD_GAP;

    let placement = prefer;
    // Auto-fallback: if preferred placement doesn't fit, pick whatever does.
    if (placement === 'center') {
      // Use centered placement.
      card.style.left = Math.max(VIEWPORT_PAD, (vw - cw) / 2) + 'px';
      card.style.top  = Math.max(VIEWPORT_PAD, (vh - ch) / 2) + 'px';
      return;
    }
    if (placement === 'bottom' && spaceBelow < ch + VIEWPORT_PAD) {
      placement = spaceAbove >= ch + VIEWPORT_PAD ? 'top'
        : spaceRight >= cw + VIEWPORT_PAD ? 'right'
        : spaceLeft  >= cw + VIEWPORT_PAD ? 'left'
        : 'center';
    }
    if (placement === 'top' && spaceAbove < ch + VIEWPORT_PAD) {
      placement = spaceBelow >= ch + VIEWPORT_PAD ? 'bottom'
        : spaceRight >= cw + VIEWPORT_PAD ? 'right'
        : spaceLeft  >= cw + VIEWPORT_PAD ? 'left'
        : 'center';
    }
    if (placement === 'right' && spaceRight < cw + VIEWPORT_PAD) {
      placement = spaceLeft  >= cw + VIEWPORT_PAD ? 'left'
        : spaceBelow >= ch + VIEWPORT_PAD ? 'bottom'
        : spaceAbove >= ch + VIEWPORT_PAD ? 'top'
        : 'center';
    }
    if (placement === 'left' && spaceLeft < cw + VIEWPORT_PAD) {
      placement = spaceRight >= cw + VIEWPORT_PAD ? 'right'
        : spaceBelow >= ch + VIEWPORT_PAD ? 'bottom'
        : spaceAbove >= ch + VIEWPORT_PAD ? 'top'
        : 'center';
    }
    if (placement === 'bottom-left') {
      // Card anchored under a top-right element (e.g. config menu).
      placement = 'bottom';
      if (spaceBelow < ch + VIEWPORT_PAD) placement = 'top';
      const right = Math.max(VIEWPORT_PAD, vw - rect.r);
      card.style.right = right + 'px';
      card.style.top   = (placement === 'bottom' ? rect.b + CARD_GAP : Math.max(VIEWPORT_PAD, rect.t - ch - CARD_GAP)) + 'px';
      return;
    }

    if (placement === 'center') {
      card.style.left = Math.max(VIEWPORT_PAD, (vw - cw) / 2) + 'px';
      card.style.top  = Math.max(VIEWPORT_PAD, (vh - ch) / 2) + 'px';
      return;
    }

    if (placement === 'bottom') {
      const left = clamp(rect.l, VIEWPORT_PAD, vw - cw - VIEWPORT_PAD);
      card.style.left = left + 'px';
      card.style.top  = (rect.b + CARD_GAP) + 'px';
    } else if (placement === 'top') {
      const left = clamp(rect.l, VIEWPORT_PAD, vw - cw - VIEWPORT_PAD);
      card.style.left = left + 'px';
      card.style.top  = Math.max(VIEWPORT_PAD, rect.t - ch - CARD_GAP) + 'px';
    } else if (placement === 'right') {
      const top = clamp(rect.t, VIEWPORT_PAD, vh - ch - VIEWPORT_PAD);
      card.style.left = (rect.r + CARD_GAP) + 'px';
      card.style.top  = top + 'px';
    } else if (placement === 'left') {
      const top = clamp(rect.t, VIEWPORT_PAD, vh - ch - VIEWPORT_PAD);
      card.style.left = Math.max(VIEWPORT_PAD, rect.l - cw - CARD_GAP) + 'px';
      card.style.top  = top + 'px';
    }
  }

  function fullPanel()   { return { display: 'block', left: '0px', top: '0px', width: '100vw', height: '100vh' }; }
  function hiddenPanel() { return { display: 'none' }; }

  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function isMobile() { return matchMedia(`(max-width: ${MOBILE_BP}px)`).matches; }

  /* The use-case flows (slides 10–12) each guide the user to ONE left-rail
   * section, so they start with every section collapsed — the smart dot then
   * points at the right section's header to open. Mirrors the rail's own
   * collapseAll(): data-collapsed is each section's source of truth, so write
   * it and sync the chevron + aria. (The rail's MutationObserver picks this up
   * to hide its "Collapse all" button.) */
  function collapseLeftRailSections() {
    document.querySelectorAll('.left-rail .rail-section[data-collapsed="false"]')
      .forEach(section => {
        section.dataset.collapsed = 'true';
        const toggle  = section.querySelector('.rail-section-toggle');
        const chevron = section.querySelector('.rail-section-chevron');
        if (toggle)  toggle.setAttribute('aria-expanded', 'false');
        if (chevron) chevron.textContent = '▸';
      });
  }

  /* Round 3: transient notice when a slide auto-adjusts app state (e.g. the
   * color guide turning Score mode back off so colors are visible). */
  function showToast(msg) {
    if (!root) return;
    const toast = document.createElement('div');
    toast.className = 'tutorial-toast';
    toast.textContent = msg;
    root.appendChild(toast);
    setTimeout(() => { try { toast.classList.add('is-leaving'); } catch {} }, 2600);
    setTimeout(() => { try { toast.remove(); } catch {} }, 3000);
  }

  function markSeen() { try { localStorage.setItem(LS_KEY, '1'); } catch {} }

  // Listen for the relaunch event from the config menu.
  document.addEventListener('food-map:start-tutorial', () => {
    // Always (re)start regardless of seen flag.
    if (root) return;
    start();
  });

  maybeAutoStart();

  return { start, end };
}

function safeRead(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
