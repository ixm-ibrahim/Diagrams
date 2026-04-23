# Data Format Specification

Each node in `data.json` follows this structure:

```json
{
  "id": "1.2.3",
  "parentId": "1.2",
  "nextIds": ["1.2.4"],
  "prevIds": ["1.2.2"],
  "hasDerivation": true,
  "claim": "The one-line conclusion at this level",
  "shortTitle": "Optional breadcrumb label",
  "soWhat": "Why this matters / what it enables",
  "search": "keywords for search indexing",
  "sections": [
    { "type": "row", "title": "Observations", "numbered": true, "items": [...] },
    { "type": "row", "title": "Conclusion", "numbered": true, "items": [...] },
    { "type": "row", "title": "If Rejected", "numbered": false, "items": [...] },
    { "type": "tab", "title": "Unlocks", "numbered": false, "items": [...] },
    { "type": "tab", "title": "Eliminates", "numbered": false, "items": [...] },
    { "type": "tab", "title": "Unknowns", "numbered": false, "items": [...] },
    { "type": "tab", "title": "Objections", "numbered": true, "items": [...] }
  ]
}
```

## Section types

- `row` sections (Observations, Conclusion, If Rejected) — always visible,
  stacked vertically.
- `tab` sections (Unlocks, Eliminates, Unknowns, Objections) — shown as
  switchable tabs.

## Item formats

Items support three formats:

### Plain strings — simple bullet points
```json
"items": ["Red", "Hot", "Pressure", "Hungry"]
```

### Nested bullets — main point with sub-points
Uses `text` for the main bullet and `items` for nested bullets. Use for
Conclusion items that need supporting explanation, or anywhere a point has
sub-points that aren't complex enough for expandable sections:
```json
"items": [
  {
    "text": "Something is happening.",
    "items": [
      "\"Phenomenon\" is the label for anything that occurs.",
      "This is the starting point — nothing more basic is available."
    ]
  }
]
```

### Expandable sections — collapsible sub-arguments
Use for If Rejected (cascading consequences) and Objections (structured
refutation):

**Objections format:**
```json
"items": [
  {
    "title": "The objection stated in its strongest form",
    "subSections": [
      { "label": "Objection Basis", "items": ["Why someone holds this..."] },
      { "label": "Objection Commitments", "items": ["The specific assumptions the objection requires..."] },
      { "label": "What's Missing", "items": ["What the objection overlooks..."] },
      { "label": "Correction", "items": ["The resolution..."] }
    ]
  }
]
```

**If Rejected format:**
```json
"items": [
  {
    "title": "The rejection is self-defeating",
    "detail": "Explanation of why...",
    "children": [
      {
        "title": "Cascading consequence",
        "detail": "Further explanation..."
      }
    ]
  }
]
```

## Other fields

**`hasDerivation`**: `true` = this node has child nodes on a sub-page.
`false` = terminal node (all reasoning is in its own sections).

**`shortTitle`**: Optional condensed breadcrumb label (e.g., "Phenomenological
Grounding" for node 1.1). Add when fleshing out a node.

**Navigation**: `nextIds`/`prevIds` connect siblings at the same level.
`parentId` points up.

**Inline markdown**: The website renders `**bold**`, `*italic*`,
`` `code` ``, and `"quoted text"` (auto-italicized) in all text fields.

**Node ID references**: Node IDs in parentheses — like `(1.1.3)` or
`(1.1.3 — qualities)` — render as clickable links with hover tooltips.
**Be frugal with references outside of Unlocks and Unknowns.** In
Conclusion, If Rejected, Eliminates, and Objections, use a reference only
on first mention within an item. Don't stack references like "Direction
(1.2.5.1.2), success (1.2.5.1.3), failure (1.2.5.1.4)" in one sentence —
say "Direction, success, and failure all require wanting" and let the reader
follow links from Unlocks.

**If Rejected `children` format**: Each child **must** be an object with
`title` and `detail` — NOT a plain string. Plain strings render as empty
collapsible containers. If consequences are short, fold them into the
parent's `detail` instead.

## Output format

Output each node as a standalone JSON block — NOT embedded in data.json.
Use this template:

```json
{
  "id": "X.X.X",
  "parentId": "X.X",
  "nextIds": ["..."],
  "prevIds": ["..."],
  "hasDerivation": false,
  "claim": "...",
  "shortTitle": "...",
  "soWhat": "...",
  "search": "...",
  "sections": [...]
}
```

The node will be merged into data.json separately.
