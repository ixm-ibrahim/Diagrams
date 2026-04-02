/**
 * =============================================================================
 * graph-engine.js — DAG Graph Layout Engine
 * =============================================================================
 * Computes the topological level (row) for each visible node and sorts
 * columns by barycenter to minimize edge crossings. Injects invisible
 * "dummy" spacer nodes for edges that skip levels, so the flex layout
 * holds visual lanes for SVG connectors.
 *
 * Dependencies: none
 * Consumers: ui-render.js (called during buildView)
 * =============================================================================
 */

/**
 * Given the set of visible nodes for a page, returns an array-of-arrays
 * where each inner array is one visual row (topological level).
 *
 * Nodes with no visible predecessors land on level 0.
 * Dummy nodes ({ isDummy: true, sourceId, targetId }) fill gaps where
 * an edge spans multiple levels.
 *
 * @param {Array<Object>} visibleNodes — nodes to lay out
 * @returns {Array<Array<Object>>} rows[level] = [node|dummy, ...]
 */
export function computeLevels(visibleNodes) {
  const nodeMap = new Map(visibleNodes.map(n => [n.id, n]));
  const levels = new Map();

  function getLevel(nodeId) {
    if (levels.has(nodeId)) return levels.get(nodeId);
    const node = nodeMap.get(nodeId);
    if (!node?.prevIds?.length) {
      levels.set(nodeId, 0);
      return 0;
    }

    let maxPrevLevel = -1;
    for (const prevId of node.prevIds) {
      if (nodeMap.has(prevId)) {
        maxPrevLevel = Math.max(maxPrevLevel, getLevel(prevId));
      }
    }
    const level = maxPrevLevel + 1;
    levels.set(nodeId, level);
    return level;
  }

  visibleNodes.forEach(n => getLevel(n.id));

  // Find the maximum level
  let maxLevel = -1;
  for (const lvl of levels.values()) {
    if (lvl > maxLevel) maxLevel = lvl;
  }

  if (maxLevel < 0) return [];

  const rows = Array.from({ length: maxLevel + 1 }, () => []);

  // Assign nodes to rows; inject dummies for long edges
  visibleNodes.forEach(node => {
    const nodeLvl = levels.get(node.id);
    rows[nodeLvl].push(node);

    if (node.nextIds) {
      node.nextIds.forEach(nextId => {
        if (!nodeMap.has(nextId)) return;
        const nextLvl = levels.get(nextId);
        for (let i = nodeLvl + 1; i < nextLvl; i++) {
          rows[i].push({ isDummy: true, sourceId: node.id, targetId: nextId });
        }
      });
    }
  });

  // Continuation dummies: terminal nodes that end before the last level
  // leave a gap in subsequent rows, allowing flex layout to redistribute
  // their space to unrelated nodes.  Injecting invisible spacers holds
  // the terminal node's visual lane so its siblings' children stay
  // correctly positioned beneath their parent.
  visibleNodes.forEach(node => {
    const nodeLvl = levels.get(node.id);
    if (nodeLvl >= maxLevel) return;
    const hasVisibleNext = (node.nextIds || []).some(nid => nodeMap.has(nid));
    if (hasVisibleNext) return;
    for (let i = nodeLvl + 1; i <= maxLevel; i++) {
      rows[i].push({ isDummy: true, sourceId: node.id, targetId: null });
    }
  });

  // Barycenter sorting: minimize visual edge crossings by positioning each
  // node near the average column index of its parents in the row above.
  // Nodes whose parents cluster on the left sort leftward, and vice versa.
  // This is a standard DAG layout heuristic that produces cleaner diagrams
  // than naive insertion order, especially for wide graphs with many edges.
  for (let i = 1; i <= maxLevel; i++) {
    rows[i].sort((a, b) => {
      const barycenter = (n) => {
        if (n.isDummy) {
          return rows[i - 1].findIndex(p =>
            p.id === n.sourceId || (p.isDummy && p.sourceId === n.sourceId));
        }
        let sum = 0, count = 0;
        n.prevIds.forEach(pid => {
          const idx = rows[i - 1].findIndex(p =>
            p.id === pid || (p.isDummy && p.targetId === n.id && p.sourceId === pid));
          if (idx !== -1) { sum += idx; count++; }
        });
        return count === 0 ? 0 : sum / count;
      };
      return barycenter(a) - barycenter(b);
    });
  }

  return rows;
}
