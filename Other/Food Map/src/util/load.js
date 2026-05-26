/* Boot-time data loading helpers.
 *
 * `loadJson` is the network fetch path (used for foods.json, meals.json).
 * `loadJsonSafe` / `loadArraySafe` read from localStorage with shape
 * validation, returning the supplied fallback on any failure so a
 * corrupt cache entry never blocks boot. */

export async function loadJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} fetch failed: ${res.status}`);
  return res.json();
}

export function loadJsonSafe(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw);
    return (parsed && typeof parsed === 'object') ? { ...fallback, ...parsed } : fallback;
  } catch {
    return fallback;
  }
}

export function loadArraySafe(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : fallback;
  } catch {
    return fallback;
  }
}
