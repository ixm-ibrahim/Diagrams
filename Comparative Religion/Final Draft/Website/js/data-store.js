/**
 * =============================================================================
 * data-store.js — Data Store & Bootstrap Loader
 * =============================================================================
 * Holds the loaded JSON data. Populated once during bootstrap via loadMapData(),
 * then read-only for the rest of the application's lifetime.
 *
 *   config  — page-level settings (title, subtitle, nodePrefix, etc.)
 *   nodes   — flat array of all node objects (augmented with .color and .hue)
 *   map     — Map<nodeId, node> for O(1) lookups
 *
 * Dependencies: color-engine.js (getPerceptualHue, computeNodeColors)
 * Consumers: every module that reads node data or config
 * =============================================================================
 */

import { getPerceptualHue, computeNodeColors } from './color-engine.js';

export const DataStore = {
  config: {},
  nodes: [],
  map: new Map()
};

/**
 * Default config values. Merged with the JSON's config block so that
 * missing keys never produce 'undefined' in the UI.
 */
const CONFIG_DEFAULTS = {
  title: 'Map',
  subtitle: '',
  breadcrumbRoot: 'Home',
  searchPlaceholder: 'Search...',
  nodePrefix: ''
};

/**
 * Fetches the JSON data file, computes perceptual colors per sibling group,
 * and populates DataStore.
 *
 * @param {string} mapName — filename without extension (default: 'data')
 * @throws {Error} if the fetch fails or JSON is malformed
 */
export async function loadMapData(mapName = 'data') {
  const response = await fetch(`${mapName}.json`);
  if (!response.ok) {
    throw new Error(`Could not find a file named ${mapName}.json`);
  }

  const pageData = await response.json();

  // --- Sort nodes by numeric ID ---
  // The JSON order is arbitrary. Everything downstream (colors, graph levels,
  // sibling nav, flex weights) depends on array order, so we normalize it
  // once here. IDs like "1.3.10" are compared segment-by-segment numerically.
  pageData.nodes.sort(compareNodeIds);

  // --- Compute perceptual colors per sibling group ---
  // Group nodes by parentId so siblings share the same hue palette.
  // Within each group, nodes are already in ID order from the sort above.
  const parentGroups = new Map();
  pageData.nodes.forEach(node => {
    const pid = node.parentId;
    if (!parentGroups.has(pid)) parentGroups.set(pid, []);
    parentGroups.get(pid).push(node);
  });

  parentGroups.forEach(siblings => {
    siblings.forEach((node, index) => {
      const hue = Math.floor(getPerceptualHue(index, siblings.length));
      node.color = computeNodeColors(hue);
      node.hue = hue;
      DataStore.map.set(node.id, node);
    });
  });

  // --- Merge loaded config with safe defaults ---
  DataStore.config = { ...CONFIG_DEFAULTS, ...pageData.config };
  DataStore.nodes = pageData.nodes;
}

/**
 * Resolves a node ID to the page (parent) that contains it.
 * Non-terminal nodes with children are their own page; terminal/childless
 * nodes live on their parent's page.
 * @param {string} nodeId
 * @returns {string|null} the page-level node ID, or null for root
 */
export function resolveNodePageId(nodeId) {
  const node = DataStore.map.get(nodeId);
  if (!node) return null;
  const hasChildren = DataStore.nodes.some(n => n.parentId === node.id);
  const isTerminal = node.hasDerivation === false;
  return (!isTerminal && hasChildren) ? node.id : node.parentId;
}

/**
 * Builds a proper href URL for navigating to a given node.
 * Works correctly when opened in a new tab.
 * @param {string} nodeId — the node to link to
 * @returns {string} a relative URL like "?node=1.1.1" or "?node=root"
 */
export function buildNodeHref(nodeId) {
  const pageId = resolveNodePageId(nodeId);
  if (pageId === null || pageId === undefined) return '?node=root';
  return `?node=${pageId}`;
}

/**
 * Builds a proper href URL for a breadcrumb/nav target.
 * @param {string} target — a node ID, 'null' (for root), or HOME_PAGE_ID
 * @param {string} homePageId — the HOME_PAGE_ID constant
 * @returns {string}
 */
export function buildTargetHref(target, homePageId) {
  if (target === homePageId || target === 'null' || target === null) {
    return '?';
  }
  return `?node=${target}`;
}

/**
 * Compares two nodes by their IDs in numeric segment order.
 * "1.3.2" vs "1.3.10" → splits to [1,3,2] vs [1,3,10] → 2 < 10.
 * Nodes at different depths sort parents before children: "1" < "1.1".
 */
function compareNodeIds(a, b) {
  const pa = a.id.split('.').map(Number);
  const pb = b.id.split('.').map(Number);
  const len = Math.max(pa.length, pb.length);
  for (let i = 0; i < len; i++) {
    const sa = pa[i] ?? -1;  // missing segments sort before present ones
    const sb = pb[i] ?? -1;
    if (sa !== sb) return sa - sb;
  }
  return 0;
}
