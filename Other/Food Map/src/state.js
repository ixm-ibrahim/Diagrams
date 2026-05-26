/* Observable global state.
 *
 * One shallow object. Views subscribe via a selector function and receive the
 * selected slice on change; they only re-render when their selected value
 * differs from last time (referentially or by ===). No framework, no proxy
 * magic — just a Set of subscribers and a setter that does shallow merge.
 *
 * The initial state shape lives in `state-shape.js` (split out so the field
 * list stays scannable and this file remains small).
 *
 * Usage:
 *   import { state } from './state.js';
 *   state.subscribe(s => s.selectedIngredientId, id => render(id));
 *   state.set({ selectedIngredientId: 'egg-white' });
 *   const all = state.get();
 */

import { INITIAL_STATE } from './state-shape.js';

const _state = { ...INITIAL_STATE };
const _subs = new Set();

function _notify(prev) {
  for (const sub of _subs) {
    const next = sub.selector(_state);
    if (next !== sub.last) {
      sub.last = next;
      sub.callback(next, sub.selector(prev));
    }
  }
}

export const state = {
  get(key) {
    return key === undefined ? _state : _state[key];
  },

  set(patch) {
    const prev = { ..._state };
    Object.assign(_state, patch);
    _notify(prev);
  },

  subscribe(selector, callback) {
    const sub = { selector, callback, last: selector(_state) };
    _subs.add(sub);
    return () => _subs.delete(sub);
  },
};
