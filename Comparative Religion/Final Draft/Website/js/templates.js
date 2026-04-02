/**
 * =============================================================================
 * templates.js — HTML Template Generators
 * =============================================================================
 * Pure HTML string generators. No DOM manipulation or state changes.
 * Each function takes data and returns an HTML string.
 *
 * Dependencies: data-store.js (DataStore.map for parent lookups)
 * Consumers: ui-render.js (nodeRow), ui-expander.js (expander),
 *            ui-expander-content.js (tabContent), ui-search.js (nodeRow)
 * =============================================================================
 */

import { DataStore } from './data-store.js';

/* ---------------------------------------------------------------------------
 * Helpers
 * --------------------------------------------------------------------------- */

/** Escape a string for safe use inside an HTML attribute (title, aria-label). */
function escapeAttr(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/**
 * Lightweight inline-markdown renderer for node text content.
 * Supports:
 *   [text](url)                    → <a href="url" target="_blank">
 *   raw URLs (https://…)           → auto-linked <a>
 *   ++underline++                  → <u>
 *   **bold**  or  __bold__        → <strong>
 *   *italic*  or  _italic_        → <em>
 *   "quoted text"                  → <em class="quoted">
 *   `code`                         → <code>
 *
 * Processing order matters: links first (so URLs inside [] aren't mangled),
 * then bold (**) before italic (*) to avoid conflicts.
 * Quoted-text rule uses smart quotes (U+201C/U+201D) and straight double quotes.
 */

/** Build nested <ul> from indented "- " lines. 2 spaces = 1 depth level. */
function buildNestedBullets(lines) {
  let html = '';
  let openLevels = 0;  // how many <ul> tags are currently open

  for (const line of lines) {
    const match = line.match(/^( *)- (.+)/);
    if (!match) continue;
    const depth = Math.floor(match[1].length / 2) + 1; // 0 spaces = level 1, 2 spaces = level 2, etc.
    const text = match[2];

    while (openLevels < depth) { html += '<ul class="bullets">'; openLevels++; }
    while (openLevels > depth) { html += '</li></ul>'; openLevels--; }

    // Close previous <li> at same level (except for the very first item)
    if (html.endsWith('</ul>')) {
      // just closed a sub-list, close the parent <li> too
      html += '</li>';
    } else if (html.endsWith('</li>')) {
      // nothing to do, previous item already closed
    } else if (html.length > 0 && !html.endsWith('<ul class="bullets">')) {
      html += '</li>';
    }

    html += `<li>${text}`;
  }

  // Close all remaining open tags
  while (openLevels > 0) { html += '</li></ul>'; openLevels--; }

  return html;
}

export function md(str) {
  if (!str || typeof str !== 'string') return str || '';

  // Placeholder map: stash links so later rules don't mangle URLs.
  const placeholders = [];
  const stash = (html) => {
    const key = `\x00PH${placeholders.length}\x00`;
    placeholders.push(html);
    return key;
  };

  let result = str
    // 1. Markdown links: [text](url)
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (_, text, url) =>
      stash(`<a href="${url}" target="_blank" rel="noopener noreferrer">${text}</a>`))
    // 2. Auto-link raw URLs (not already inside a markdown link)
    .replace(/(?<!\]\()https?:\/\/[^\s<>"'`,;)}\]]+/g, (url) =>
      stash(`<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`))
    // Underline: ++text++
    .replace(/\+\+(.+?)\+\+/g, '<u>$1</u>')
    // Bold: **text** or __text__
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    // Italic: *text* or _text_  (but not inside words for underscores)
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/(?<!\w)_(.+?)_(?!\w)/g, '<em>$1</em>')
    // Quoted text (straight or smart double quotes): italicize with class
    .replace(/\u201C(.+?)\u201D/g, '<em class="quoted">\u201C$1\u201D</em>')
    .replace(/"(.+?)"/g, '<em class="quoted">"$1"</em>')
    // Inline code
    .replace(/`(.+?)`/g, '<code>$1</code>');

  // Last: multi-line bullet lists within a single string.
  // Supports nested bullets via indentation (2 spaces per level).
  // Done last so HTML attributes from above aren't caught by earlier regexes.
  result = result.replace(/(?:^|\n)((?:[ ]*- .+(?:\n|$))+)/g, (_, block) => {
    return buildNestedBullets(block.trim().split('\n'));
  });

  // Restore stashed links.
  for (let i = 0; i < placeholders.length; i++) {
    result = result.replace(`\x00PH${i}\x00`, placeholders[i]);
  }

  return result;
}

/* ---------------------------------------------------------------------------
 * Node row (card + marker + derive button)
 * --------------------------------------------------------------------------- */

export function nodeRow(node) {
  const parentNode = node.parentId ? DataStore.map.get(node.parentId) : null;
  const pillColorDark  = parentNode ? parentNode.color.borderDark  : node.color.borderDark;
  const pillColorLight = parentNode ? parentNode.color.borderLight : node.color.borderLight;

  const badgeTarget = parentNode?.parentId === null
    ? 'null' : (parentNode?.parentId || '');

  const badgeHtml = parentNode
    ? `<button class="node-badge ancestry-trigger" type="button"
         data-node-id="${node.id}"
         aria-label="View ancestry of step ${node.id}"
         title="${parentNode.id}. ${escapeAttr(parentNode.claim)}">
         <span class="badge-dot"></span>${parentNode.id}</button>`
    : '';

  const derivationHtml = (node.hasDerivation !== false)
    ? `<button class="btn-derivation trigger-derive" data-target="${node.id}"
         aria-label="Derivation details for step ${node.id}">
         <span class="label">Derivation</span><span>→</span></button>`
    : `<button class="btn-derivation" aria-hidden="true" disabled
         style="visibility: hidden; pointer-events: none;">
         <span class="label">Derivation</span><span>→</span></button>`;

  return `
    <div class="node-marker" aria-hidden="true">
      <span class="marker-dot"></span>
      <span class="marker-arrow-tip"></span>
    </div>
    <article class="node-card" data-id="${node.id}"
      style="--n-border-dark: ${node.color.borderDark}; --n-border-light: ${node.color.borderLight};
             --n-top: ${node.color.top}; --n-bottom: ${node.color.bottom};
             --p-border-dark: ${pillColorDark}; --p-border-light: ${pillColorLight};">
      <div class="node-header" role="button" tabindex="0" aria-expanded="false">
        <h2 class="node-title"><span class="id">${node.id}.</span><span class="claim-text">${md(node.claim)}</span></h2>
        <div class="node-controls">
          ${badgeHtml}
          <button class="btn-ui trigger-inline" type="button" tabindex="-1">Expand</button>
        </div>
      </div>
      <div class="node-body">
        <div class="node-so-what">${md(node.soWhat)}</div>
        <div class="node-vote-buttons" data-node-id="${node.id}">
        <button class="btn-vote btn-vote-agree" type="button" aria-pressed="false"
          aria-label="I agree with ${node.id}" data-vote="agree" data-node-id="${node.id}">
          <svg class="btn-vote__icon" viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
            <path d="M2 10.5a1.5 1.5 0 1 1 3 0v6a1.5 1.5 0 0 1-3 0v-6ZM6 10.333v5.43a2 2 0 0 0 1.106 1.79l.05.025A4 4 0 0 0 8.943 18h5.416a2 2 0 0 0 1.962-1.608l1.2-6A2 2 0 0 0 15.559 8H12V4a2 2 0 0 0-2-2 1 1 0 0 0-1 1v.667a4 4 0 0 1-.8 2.4L6.8 7.933a4 4 0 0 0-.8 2.4Z"/>
          </svg>
          <span class="btn-vote__label">I agree</span>
        </button>
        <button class="btn-vote btn-vote-disagree" type="button" aria-pressed="false"
          aria-label="I disagree with ${node.id}" data-vote="disagree" data-node-id="${node.id}">
          <svg class="btn-vote__icon" viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
            <path d="M18 9.5a1.5 1.5 0 1 1-3 0v-6a1.5 1.5 0 0 1 3 0v6ZM14 9.667V4.236a2 2 0 0 0-1.106-1.789l-.05-.025A4 4 0 0 0 11.057 2H5.641a2 2 0 0 0-1.962 1.608l-1.2 6A2 2 0 0 0 4.441 12H8v4a2 2 0 0 0 2 2 1 1 0 0 0 1-1v-.667a4 4 0 0 1 .8-2.4l1.4-1.867a4 4 0 0 0 .8-2.4Z"/>
          </svg>
          <span class="btn-vote__label">I disagree</span>
        </button>
        </div>
      </div>
    </article>
    ${derivationHtml}
  `;
}

/* ---------------------------------------------------------------------------
 * Expander panel (inline detail content below a card)
 * --------------------------------------------------------------------------- */

export function expander(node) {
  const rowSections = (node.sections || []).filter(s => s.type === 'row');
  const logicGroupHtml = rowSections
    .map((s, idx) => logicRow(s.title, s.items, idx + 1, s.numbered))
    .join('');

  const tabSections = (node.sections || []).filter(s => s.type === 'tab');

  // Action slot: "disagree → derive" button, or agree/disagree toggles
  let actionHtml = '';
  if (node.hasDerivation !== false) {
    actionHtml = `<button class="btn-action btn-derivation-disagree trigger-derive"
      type="button" data-target="${node.id}">Disagree? See how this is derived <span class="action-arrow">→</span></button>`;
  } else {
    actionHtml = `
      <button class="btn-action btn-agree" type="button" aria-pressed="false"
        data-vote="agree" data-node-id="${node.id}">I agree</button>
      <button class="btn-action btn-disagree" type="button" aria-pressed="false"
        data-vote="disagree" data-node-id="${node.id}">I disagree</button>
    `;
  }
  const actionSlotHtml = `<div class="panel-action-slot">${actionHtml}</div>`;

  let tabAreaHtml = '';
  if (tabSections.length > 0) {
    const defaultTab = tabSections[0].title;
    const tabButtonsHtml = tabSections.map(s => `
      <button class="btn-tab" data-key="${s.title}"
        aria-selected="${s.title === defaultTab}" aria-controls="panel-${node.id}">
        ${s.title}
      </button>
    `).join('');

    tabAreaHtml = `
      <div class="tab-area">
        <div class="tab-list" role="tablist" aria-label="Logic Implications">${tabButtonsHtml}</div>
        ${actionSlotHtml}
        <div class="tab-panel" id="panel-${node.id}" role="tabpanel"></div>
      </div>
    `;
  } else {
    tabAreaHtml = `<div class="tab-area" style="grid-template-columns: 1fr;">${actionSlotHtml}</div>`;
  }

  const hasContent = logicGroupHtml !== '' || tabSections.length > 0;
  const placeholderHtml = hasContent
    ? ''
    : '<p class="expander-empty">This section has yet to be populated.</p>';

  return `<div class="exp-inner">${placeholderHtml}<div class="logic-group">${logicGroupHtml}</div>${tabAreaHtml}</div>`;
}

/* ---------------------------------------------------------------------------
 * Logic sections (row-type sections inside expander)
 * --------------------------------------------------------------------------- */

function logicRow(label, items, step, isNumbered) {
  if (!items?.length) return '';
  const isComplex = typeof items[0] === 'object' && items[0] !== null;
  const content = isComplex
    ? `<div class="mini-stack">${items.map((it, idx) => recursiveMiniNode(it, isNumbered ? idx + 1 : null)).join('')}</div>`
    : buildList(items);

  return `
    <div class="logic-section">
      <div class="logic-header" data-step="${step}" role="button" tabindex="0" aria-expanded="true">${label}</div>
      <div class="logic-content"><div class="logic-content-inner">${content}</div></div>
    </div>
  `;
}

function buildList(items) {
  return `<ul class="bullets">${items.map(i => `<li>${md(i)}</li>`).join('')}</ul>`;
}

/* ---------------------------------------------------------------------------
 * Recursive mini-nodes (nested expandable sub-arguments)
 * --------------------------------------------------------------------------- */

function recursiveMiniNode(data, num) {
  const prefix = num ? `<span class="id">${num}.</span> ` : '';
  const title = data.title || data;
  const content = buildMiniNodeContent(data);
  return `
    <div class="mini-node">
      <button class="mini-trigger" type="button" aria-expanded="false">${prefix}<span class="mini-title-text">${md(title)}</span></button>
      <div class="mini-content-wrap"><div class="mini-content-inner">${content}</div></div>
    </div>
  `;
}

function buildMiniNodeContent(data) {
  const parts = [];
  if (data.detail) {
    parts.push(`<div class="mini-detail-wrap"><div class="sub-body">${md(data.detail)}</div></div>`);
  }
  if (data.subSections?.length) {
    parts.push(data.subSections.map(sub => `
      <div class="sub-section">
        <div class="sub-label">${md(sub.label)}</div>
        <div class="sub-body">${buildList(sub.items)}</div>
      </div>
    `).join(''));
  }
  if (data.children?.length) {
    parts.push(`<div class="mini-stack mini-stack--nested">
      ${data.children.map((c, idx) => recursiveMiniNode(c, idx + 1)).join('')}
    </div>`);
  }
  return parts.join('');
}

/* ---------------------------------------------------------------------------
 * Tab content (tab-type sections inside expander)
 * --------------------------------------------------------------------------- */

export function tabContent(items, isNumbered) {
  if (!items?.length) return `<ul class="bullets"><li>—</li></ul>`;
  const isComplex = typeof items[0] === 'object' && items[0] !== null;
  if (isComplex) {
    return `<div class="mini-stack">${items.map((it, idx) => recursiveMiniNode(it, isNumbered ? idx + 1 : null)).join('')}</div>`;
  }
  return buildList(items);
}
