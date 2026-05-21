/* Phase 11: global keyboard shortcuts + the ? help overlay.
 *
 *   R       reset camera to the default isometric (matches the ⟲ snap)
 *   T       toggle 3D / Table view
 *   1 2 3   snap to X / Y / Z axis (matches the X/Y/Z snap buttons)
 *   [       collapse the left rail
 *   ]       expand the left rail
 *   ?       open the help overlay (Esc or click backdrop closes)
 *
 * Esc is already handled inside individual components (axis picker,
 * detail panel, etc.) — we don't override it here to avoid stomping
 * those local close behaviors.
 *
 * Shortcuts are suppressed while the user is typing in a text field
 * (input/textarea/contenteditable), so they don't fire on every "t"
 * in the ingredient search.
 */

export function mountShortcuts({ state, onSnap }) {
  const overlay = buildHelpOverlay();
  document.body.appendChild(overlay.root);

  function isTyping(target) {
    if (!target) return false;
    if (target.isContentEditable) return true;
    const tag = target.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
  }

  document.addEventListener('keydown', (ev) => {
    if (ev.metaKey || ev.ctrlKey || ev.altKey) return;
    if (isTyping(ev.target)) return;

    switch (ev.key) {
      case 'r': case 'R':
        onSnap?.('free');
        break;
      case 't': case 'T':
        state.set({ view: state.get('view') === 'table' ? '3d' : 'table' });
        break;
      case '1': onSnap?.('x'); break;
      case '2': onSnap?.('y'); break;
      case '3': onSnap?.('z'); break;
      case '[':
        if (state.get('leftRailOpen')) state.set({ leftRailOpen: false });
        break;
      case ']':
        if (!state.get('leftRailOpen')) state.set({ leftRailOpen: true });
        break;
      case '?':
        overlay.toggle();
        break;
      case 'Escape':
        if (overlay.isOpen()) { overlay.close(); ev.stopPropagation(); }
        break;
      default:
        return;
    }
  });
}

function buildHelpOverlay() {
  const root = document.createElement('div');
  root.className = 'shortcut-help';
  root.hidden = true;
  root.innerHTML = `
    <div class="shortcut-help-backdrop"></div>
    <div class="shortcut-help-panel" role="dialog" aria-label="Keyboard shortcuts">
      <header class="shortcut-help-head">
        <h2>Keyboard shortcuts</h2>
        <button class="shortcut-help-close" type="button" aria-label="Close">×</button>
      </header>
      <dl class="shortcut-list">
        <dt><kbd>R</kbd></dt><dd>Reset camera to default isometric view</dd>
        <dt><kbd>T</kbd></dt><dd>Toggle between 3D and Table view</dd>
        <dt><kbd>1</kbd> / <kbd>2</kbd> / <kbd>3</kbd></dt><dd>Snap camera to X / Y / Z axis</dd>
        <dt><kbd>[</kbd> / <kbd>]</kbd></dt><dd>Collapse / expand the left panel</dd>
        <dt><kbd>?</kbd></dt><dd>Show / hide this overlay</dd>
        <dt><kbd>Esc</kbd></dt><dd>Close the open panel or overlay</dd>
      </dl>
    </div>
  `;

  function open()  { root.hidden = false; }
  function close() { root.hidden = true;  }
  function isOpen() { return !root.hidden; }
  function toggle() { isOpen() ? close() : open(); }

  root.querySelector('.shortcut-help-close').addEventListener('click', close);
  root.querySelector('.shortcut-help-backdrop').addEventListener('click', close);

  return { root, open, close, isOpen, toggle };
}
