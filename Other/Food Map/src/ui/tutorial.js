/* First-run guided tour.
 *
 * Six steps walk a new user through the top-level concept and the
 * highest-leverage controls. After each step the user can hit Next,
 * Back, or Skip. Auto-fires once per browser (foodMap.tutorialSeen
 * localStorage key). Existing users (anyone who already has a
 * persisted foodMap.state.v1 blob from a prior session) are
 * grandfathered in — they shouldn't be ambushed.
 *
 * Anyone can relaunch the tour from the ⋯ config menu, which
 * dispatches a `food-map:start-tutorial` CustomEvent we listen for.
 *
 * Spotlight strategy: four absolutely-positioned dim panels sit
 * around the target's bounding rect, leaving the target itself
 * fully visible AND fully interactive (clicks pass through the
 * gap to the real element). A pulsing ring traces the target.
 * A tooltip card auto-positions below the target with viewport
 * fallback to above / side / centered.
 */

const LS_KEY = 'foodMap.tutorialSeen';

const RING_PADDING = 6;
const CARD_GAP     = 14;
const VIEWPORT_PAD = 12;
const MOBILE_BP    = 768;

export function mountTutorial({ state } = {}) {
  let root = null;
  let stepIdx = 0;
  let steps = [];
  let reposRAF = 0;
  let onResize = null;
  let savedRailOpen = null;

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
    steps = buildSteps();
    buildDom();
    if (state && isMobile()) {
      savedRailOpen = state.get('leftRailOpen');
    }
    renderStep();
    onResize = () => scheduleReposition();
    window.addEventListener('resize', onResize);
    window.addEventListener('scroll', onResize, true);
    document.addEventListener('keydown', onKey, true);
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
    cancelAnimationFrame(reposRAF);
    reposRAF = 0;
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

  function buildSteps() {
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
      },
      {
        target: '#canvas-container',
        title: 'The 3D map',
        body:
          'Every sphere is one food. Color hints at the food group — red for ' +
          'animal, green for plant, blue for dairy (other groups blend in). ' +
          'Drag to orbit, scroll or pinch to zoom. Click a sphere to open its ' +
          'full nutrient breakdown in the right panel.',
        tip: 'Click an axis label to swap which nutrient that axis represents.',
        prefer: 'center',
        beforeShow: () => {
          if (state && state.get('view') !== '3d') state.set({ view: '3d' });
        },
      },
      {
        target: '#view-level',
        title: 'Zoom out',
        body:
          'Look at individual ingredients, broader category groups (like "fruits"), ' +
          'or whole meals. Each level plots the same nutrient space at a different ' +
          'granularity, and every filter you set works at all three levels.',
        tip: 'Try "Meals" to see hundreds of complete dishes positioned by their averages.',
        prefer: 'bottom',
      },
      {
        target: '#rail-left',
        title: 'Nutrient thresholds + filters',
        body:
          'The left rail lives at filters. The very top section is Nutrient ' +
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
        beforeShow: () => {
          if (state && isMobile()) state.set({ leftRailOpen: true });
          if (state && state.get('view') !== '3d') state.set({ view: '3d' });
        },
      },
      {
        target: '#axis-controls',
        title: 'Axes + Fit visible',
        body:
          'The Axes panel in the bottom-right lets you pan, zoom, and reset each ' +
          'axis. After you apply filters that cluster every dot into one corner, ' +
          'click "Fit visible" to zoom the cube around just those visible dots — ' +
          'the cluster suddenly fills the whole space.',
        tip: '"Filter by axis ranges" sends each axis\'s current window to Nutrient thresholds — handy for converting a zoom into a filter.',
        prefer: 'left',
        beforeShow: () => {
          if (state && state.get('view') !== '3d') state.set({ view: '3d' });
          if (state && state.get('axisControlsOpen') === false) {
            state.set({ axisControlsOpen: true });
          }
        },
      },
      {
        target: '#view-toggle',
        title: 'Or as a table',
        body:
          'Toggle to a sortable table of the same data. Click any column to sort, ' +
          'pick which columns to show, and tune the composite-score weights. All ' +
          'the left-rail filters still apply.',
        tip: 'You’re now in table view. Try sorting by Protein to find protein-dense foods.',
        prefer: 'bottom',
        beforeShow: () => {
          if (state && state.get('view') !== 'table') state.set({ view: 'table' });
        },
      },
      {
        target: '#config-menu-slot',
        title: "You're set",
        body:
          'A few extras you’ll probably want:',
        bullets: [
          'Search any food, category, or meal by name in the header search.',
          'Color guide (bottom-right): uncheck rows to hide whole food groups.',
          'Build your own meals in the left rail’s "Your meals" section.',
          'Toggle theme and per-serving vs per-100g from the header.',
          'Active filters chip rail (bottom-left) shows everything currently on — click any chip to clear it.',
          'Restart this tour any time from this menu.',
        ],
        tip: 'Hit "Got it" to start exploring.',
        prefer: 'bottom-left',
        isLast: true,
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
        <p class="tutorial-tip" hidden></p>
        <div class="tutorial-dots" aria-hidden="true"></div>
        <div class="tutorial-actions">
          <button class="btn tutorial-skip"  type="button">Skip tour</button>
          <span class="tutorial-actions-spacer"></span>
          <button class="btn tutorial-back"  type="button">Back</button>
          <button class="btn btn-primary tutorial-next" type="button">Next →</button>
        </div>
      </div>
    `;
    document.body.appendChild(root);

    root.querySelector('.tutorial-next').addEventListener('click', next);
    root.querySelector('.tutorial-back').addEventListener('click', back);
    root.querySelector('.tutorial-skip').addEventListener('click', () => end());
    root.querySelector('.tutorial-skip-x').addEventListener('click', () => end());

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

    if (step.beforeShow) {
      try { step.beforeShow(); } catch {}
    }

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

    scheduleReposition();
  }

  function scheduleReposition() {
    cancelAnimationFrame(reposRAF);
    reposRAF = requestAnimationFrame(reposition);
  }

  function reposition() {
    if (!root) return;
    const step = steps[stepIdx];
    const ring = root.querySelector('.tutorial-ring');
    const card = root.querySelector('.tutorial-card');
    const dimTop    = root.querySelector('.tutorial-dim-top');
    const dimRight  = root.querySelector('.tutorial-dim-right');
    const dimBottom = root.querySelector('.tutorial-dim-bottom');
    const dimLeft   = root.querySelector('.tutorial-dim-left');

    const vw = window.innerWidth;
    const vh = window.innerHeight;

    if (!step.target) {
      // No spotlight — single full-screen dim. Hide ring, center the card.
      ring.hidden = true;
      Object.assign(dimTop.style,    fullPanel());
      Object.assign(dimRight.style,  hiddenPanel());
      Object.assign(dimBottom.style, hiddenPanel());
      Object.assign(dimLeft.style,   hiddenPanel());
      card.style.left = '';
      card.style.top  = '';
      card.style.right = '';
      card.style.bottom = '';
      card.classList.add('is-centered');
      return;
    }

    const el = document.querySelector(step.target);
    if (!el) {
      // Target missing (e.g. element conditionally rendered). Fall back
      // to centered card with full-screen dim.
      ring.hidden = true;
      Object.assign(dimTop.style,    fullPanel());
      Object.assign(dimRight.style,  hiddenPanel());
      Object.assign(dimBottom.style, hiddenPanel());
      Object.assign(dimLeft.style,   hiddenPanel());
      card.style.left = '';
      card.style.top  = '';
      card.classList.add('is-centered');
      return;
    }

    const r = el.getBoundingClientRect();
    /* Clamp the rect to the viewport. An off-screen rail or a rect
     * that's wider than the viewport produces a useless cutout
     * otherwise. */
    const t = Math.max(0, Math.min(vh, r.top    - RING_PADDING));
    const b = Math.max(0, Math.min(vh, r.bottom + RING_PADDING));
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
    placeCard(card, { l, t, r: ri, b }, step.prefer || 'bottom', vw, vh);
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
