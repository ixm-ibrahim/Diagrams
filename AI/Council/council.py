#!/usr/bin/env python3
"""
The Council — single-voice editorial pipeline.

Architecture (v2, full rebuild):

    Drafter (Opus)
        |
        v
    [Methodological Critic | Opposing-View Critic | Style Critic]   (parallel, Sonnet)
        |
        v
    Reviser (Opus)
        |
        v
    Style Auditor (Haiku)
        |
        v
    Final answer

One answer, progressively beaten on and rewritten. Diversity comes from what
each critic is checking for, not from how many voices speak.

A separate Quick mode (single Claude call, no pipeline) is preserved for
casual back-and-forth.

CLI-first (uses `claude -p`), Anthropic API key optional.

Run:  python council.py
Stop: Ctrl+C
"""

import http.server, json, subprocess, threading, webbrowser, shutil
import os, re, datetime
from urllib.parse import urlparse, unquote

PORT = 8765
CLI_TIMEOUT_SEC = 600  # bumped further; reviser + critics on long inputs need headroom

_HERE = os.path.dirname(os.path.abspath(__file__))
CHATS_DIR = os.path.join(_HERE, 'chats')
os.makedirs(CHATS_DIR, exist_ok=True)


def _slugify(text):
    s = re.sub(r'[^A-Za-z0-9\s-]', '', text or '').strip().lower()
    s = re.sub(r'[\s_-]+', '-', s)
    return s[:48].strip('-')


def _now_stamp():
    return datetime.datetime.now().strftime('%Y%m%d-%H%M%S')


def _now_iso():
    return datetime.datetime.now().isoformat()


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Council</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg:#0e0e0f; --s1:#161618; --s2:#1c1c1e; --s3:#222224;
  --border:#2a2a2e; --text:#d4cec8; --muted:#6b6670;
  --gold:#c9a84c; --red:#c0544a; --green:#4a8c6f;
  --blue:#4a72a8; --orange:#b8723a; --purple:#7a5ca8;
  --slate:#5a6470;
  --toolbar-h: 56px;        /* updated from JS to match actual toolbar height */
}
html,body { min-height:100%; background:var(--bg); color:var(--text); font-family:'DM Sans',sans-serif; font-size:15px; line-height:1.6; }

/* Toolbar */
#toolbar {
  position:sticky; top:0; z-index:40;
  display:grid; grid-template-columns: 1fr auto 1fr; align-items:center;
  padding:10px 18px;
  background:var(--bg); border-bottom:1px solid var(--border);
}
#toolbar-left { display:flex; gap:6px; align-items:center; justify-self:start; }
#toolbar-center { display:flex; gap:14px; align-items:center; justify-self:center; }
#toolbar-right { display:flex; gap:6px; align-items:center; justify-self:end; }
.tb-btn {
  background:transparent; border:1px solid var(--border); color:var(--muted);
  padding:6px 10px; border-radius:6px; cursor:pointer; font-size:14px;
  font-family:'DM Sans',sans-serif;
  transition: color .15s, border-color .15s, background .15s;
}
.tb-btn:hover { color:var(--text); border-color:var(--muted); background:var(--s2); }
.tb-title { font-family:'Cormorant Garamond',serif; font-size:22px; color:var(--gold); letter-spacing:0.04em; }

/* Mode toggle (inline in toolbar, balanced with title) */
.mode-toggle { display:inline-flex; gap:2px; padding:2px; background:var(--s1); border:1px solid var(--border); border-radius:8px; }
.mode-btn {
  background:transparent; border:none; color:var(--muted);
  padding:5px 12px; border-radius:6px; cursor:pointer; font-size:12px;
  font-family:'DM Sans',sans-serif; letter-spacing:.04em;
  transition: color .15s, background .15s;
}
.mode-btn:hover { color:var(--text); }
.mode-btn.active { color:var(--gold); background:var(--s2); }

/* Layout */
#main {
  max-width: 900px; margin: 0 auto; padding: 30px 24px 200px;
}

/* Thread / turns / message bubbles */
.thread { display:flex; flex-direction:column; gap:30px; }
.turn { display:flex; flex-direction:column; gap:12px; }

/* User message: right-aligned bubble, like a text thread */
.turn-user-row { display:flex; justify-content:flex-end; }
.turn-user {
  position:relative;
  background:rgba(201,168,76,.10);
  border:1px solid rgba(201,168,76,.30);
  padding:11px 16px; border-radius:18px 18px 4px 18px;
  font-size:14.5px; color:var(--text); white-space:pre-wrap; word-wrap:break-word;
  max-width:78%; line-height:1.55;
  box-shadow: 0 1px 2px rgba(0,0,0,.18);
}
/* Action buttons inside the user bubble, top-right corner, hover-revealed.
   Holds the edit button and the copy button side by side. */
.turn-user .user-actions {
  position:absolute; top:4px; right:6px;
  display:flex; gap:2px;
}
.turn-user .user-actions .msg-copy-btn { position:static; opacity:0; }
.turn-user:hover .user-actions .msg-copy-btn { opacity:.55; }

/* Edit-in-place: textarea + Save/Cancel buttons replace the bubble's content.
   Without an explicit width, the bubble would shrink to fit its empty
   textarea — so we give it a comfortable fixed width while editing. */
.turn-user.editing {
  padding:10px 12px;
  width:78%; max-width:78%;
  min-width:min(78%, 380px);
}
.turn-user.editing .user-actions { display:none; }
.edit-textarea {
  width:100%;
  min-height:34px;   /* one line — autoresize JS grows it as the user types */
  max-height:340px;
  resize:none;       /* JS handles autoresize; the drag handle was janky too */
  overflow-y:auto;
  background:transparent; border:none; color:var(--text);
  font-family:'DM Sans',sans-serif; font-size:14.5px; line-height:1.55;
  outline:none; padding:0;
}
.edit-actions { display:flex; gap:6px; justify-content:flex-end; margin-top:8px; }
.edit-actions button {
  background:var(--s2); border:1px solid var(--border); color:var(--text);
  padding:4px 12px; border-radius:5px; font-size:12px; cursor:pointer;
  font-family:'DM Sans',sans-serif;
  transition: color .15s, border-color .15s, background .15s;
}
.edit-actions .edit-save { color:var(--gold); border-color:rgba(201,168,76,.40); }
.edit-actions .edit-save:hover { background:rgba(201,168,76,.10); border-color:var(--gold); }
.edit-actions .edit-cancel:hover { color:#e8a89e; border-color:rgba(192,84,74,.50); }

/* AI seats: left-aligned, slightly narrower than full width to balance */
.seat-row { display:flex; justify-content:flex-start; }
.seat {
  background:var(--s1); border:1px solid var(--border); border-radius:12px;
  width:94%; max-width:94%;
  opacity:0; transform:translateY(8px);
  transition: opacity .35s ease, transform .35s ease, border-color .15s ease, box-shadow .15s ease;
  /* No overflow:hidden — the sticky header needs to escape the seat to pin to the viewport. */
}
.seat.visible { opacity:1; transform:translateY(0); }
.seat:hover { border-color:var(--muted); box-shadow: 0 2px 10px rgba(0,0,0,.20); }

/* The header sticks just below the toolbar while the seat body is in view,
   then detaches when the seat's bottom catches up to it. */
.seat-header {
  display:flex; justify-content:space-between; align-items:center;
  padding:10px 16px; background:var(--s2); cursor:pointer;
  border-bottom:1px solid var(--border);
  border-top-left-radius: 12px; border-top-right-radius: 12px;
  position: sticky; top: var(--toolbar-h); z-index: 10;
  transition: background .15s, box-shadow .15s;
  user-select:none;
}
.seat-header:hover { background:var(--s3); }
.seat-header.collapsed { border-bottom:none; border-radius: 12px; }
/* When the header is actually pinned, a subtle shadow makes it read as floating. */
.seat-header.stuck { box-shadow: 0 4px 12px rgba(0,0,0,.35); }
.seat-title { display:flex; align-items:center; gap:9px; }
.seat-icon { font-size:16px; }
.seat-name { font-family:'Cormorant Garamond',serif; font-size:18px; font-weight:600; letter-spacing:.02em; }
.seat-label { color:var(--muted); font-size:12px; letter-spacing:.04em; margin-left:6px; }
.seat-state {
  color:var(--text); font-size:12px;
  display:flex; align-items:center; gap:8px;
}
.seat-state.waiting { color:var(--muted); }
.seat-state.done { color:var(--green); }
.seat-state.error { color:var(--red); }
.seat-state .chevron { color:var(--muted); font-size:10px; transition:transform .15s; }
.seat-header.collapsed .chevron { transform:rotate(-90deg); }
.seat-body { padding:18px 22px; font-size:14.5px; line-height:1.72; color:#cdc7c0; }
.seat-body.collapsed { display:none; }

.seat[data-color=gold] .seat-name { color:var(--gold); }
.seat[data-color=red] .seat-name { color:var(--red); }
.seat[data-color=green] .seat-name { color:var(--green); }
.seat[data-color=blue] .seat-name { color:var(--blue); }
.seat[data-color=orange] .seat-name { color:var(--orange); }
.seat[data-color=purple] .seat-name { color:var(--purple); }
.seat[data-color=slate] .seat-name { color:var(--slate); }

/* The final stage gets a distinguishing border + gentle glow */
.seat.final {
  border:1px solid rgba(201,168,76,.55);
  box-shadow: 0 0 0 1px rgba(201,168,76,.10);
}
.seat.final .seat-header { background:#221d10; }
.seat.final:hover { border-color:var(--gold); box-shadow: 0 0 0 1px rgba(201,168,76,.18), 0 2px 12px rgba(0,0,0,.25); }

/* Typing dots — the animated ellipses used in seat states and chat list */
.typing { display:inline-flex; gap:4px; align-items:center; }
.typing span { width:5px; height:5px; border-radius:50%; background:var(--gold); animation: pulse 1.2s infinite ease-in-out; }
.typing span:nth-child(2) { animation-delay: .2s; }
.typing span:nth-child(3) { animation-delay: .4s; }
@keyframes pulse {
  0%, 80%, 100% { transform: scale(.7); opacity: .4; }
  40%           { transform: scale(1);  opacity: 1;  }
}
.seat-state .check { color:var(--green); font-size:13px; }

/* Hover-revealed copy button — used on both user bubbles and seat headers */
.msg-copy-btn {
  background:transparent; border:none; color:var(--muted);
  cursor:pointer; padding:3px 7px; border-radius:5px;
  font-size:13px; line-height:1;
  opacity:0; transition: opacity .15s, color .15s, background .15s;
}
.turn-user:hover .msg-copy-btn,
.seat:hover .msg-copy-btn { opacity:.55; }
.msg-copy-btn:hover { color:var(--gold); background:var(--s3); opacity:1 !important; }

/* Wrap that places the seat's copy + skip buttons to the left of the state badge */
.seat-actions { display:flex; align-items:center; gap:4px; }

/* Skip button — shown only while an agent is actually working. Skipping
   aborts just this agent's call; the next stage runs with the previous
   stage's output as input. */
.seat-skip-btn {
  display:none;
  background:transparent; border:1px solid var(--border); color:var(--muted);
  padding:3px 9px; border-radius:5px;
  font-size:11px; line-height:1.2; cursor:pointer;
  font-family:'DM Sans',sans-serif; letter-spacing:.04em;
  transition: color .15s, border-color .15s, background .15s;
}
.seat-skip-btn:hover { color:#e8a89e; border-color:rgba(192,84,74,.5); background:rgba(192,84,74,.10); }

/* Skipped state — muted, with a small body notice. */
.seat-state.skipped { color:var(--muted); }
.skipped-notice {
  font-size:13px; color:var(--muted); font-style:italic;
  padding:2px 0 6px;
}
.skipped-notice strong { color:var(--text); font-style:normal; }

/* Markdown rendering inside seat-body */
.md p { margin: 0 0 12px; }
.md p:last-child { margin-bottom: 0; }
.md strong { color:#e6dfd6; }
.md em { color:#b3aaa1; }
.md code { background:var(--s3); padding:1px 5px; border-radius:3px; font-size:0.92em; }
.md pre { background:var(--s3); padding:10px 12px; border-radius:6px; overflow-x:auto; margin:8px 0; }
.md pre code { background:none; padding:0; }
.md blockquote { border-left:3px solid var(--border); padding-left:12px; color:var(--muted); margin:8px 0; }
.md h1,.md h2,.md h3 { font-family:'Cormorant Garamond',serif; margin: 14px 0 8px; }
.md ul, .md ol { margin: 6px 0 12px 22px; }
.md li { margin-bottom: 4px; }

/* Input */
#input-bar {
  position:fixed; bottom:0; left:0; right:0; background:var(--bg);
  border-top:1px solid var(--border); padding:14px 24px;
}
#input-inner {
  max-width:900px; margin:0 auto;
  display:flex; flex-direction:column; gap:8px;
}
#input {
  width:100%; min-height:46px; max-height:280px;
  resize:none;             /* JS handles auto-resize; manual drag was janky */
  overflow-y:auto;
  background:var(--s1); border:1px solid var(--border); color:var(--text);
  padding:10px 12px; border-radius:8px; font-family:'DM Sans',sans-serif; font-size:15px; line-height:1.5;
  transition: border-color .15s, box-shadow .15s;
}
#input:focus { outline:none; border-color:var(--gold); box-shadow: 0 0 0 1px rgba(201,168,76,.25); }

/* Row beneath the textarea: mode toggle on the left, Send/Stop on the right. */
#input-controls { display:flex; justify-content:space-between; align-items:center; gap:10px; }

#send-btn, #abort-btn {
  background:var(--gold); color:#1a1408; border:none; padding:8px 22px;
  border-radius:8px; cursor:pointer; font-weight:500; font-size:14px; font-family:'DM Sans',sans-serif;
  transition: opacity .15s, transform .05s;
}
#send-btn:hover, #abort-btn:hover { opacity: .92; }
#send-btn:active, #abort-btn:active { transform: translateY(1px); }
#send-btn:disabled { opacity:0.4; cursor:not-allowed; }
#abort-btn { background:var(--red); color:#fff; display:none; }
#abort-btn.show { display:inline-block; }

/* Panels (chat list + settings) */
.panel {
  position:fixed; top:0; bottom:0; width:340px; background:var(--s1);
  border-right:1px solid var(--border); z-index:50; padding:18px; overflow-y:auto;
  transform:translateX(-100%); transition:transform 0.2s;
}
.panel.right { left:auto; right:0; border-right:none; border-left:1px solid var(--border); transform:translateX(100%); }
.panel.open { transform:translateX(0); }
.panel h3 { font-family:'Cormorant Garamond',serif; font-size:20px; margin-bottom:14px; color:var(--gold); }
.panel label { display:block; font-size:13px; color:var(--muted); margin: 12px 0 4px; }
.panel input[type=text], .panel input[type=password], .panel textarea {
  width:100%; background:var(--bg); border:1px solid var(--border); color:var(--text);
  padding:8px 10px; border-radius:6px; font-family:'DM Sans',sans-serif; font-size:14px;
}
.panel textarea { min-height:120px; resize:vertical; font-family: ui-monospace, monospace; font-size:12px; line-height:1.5; }
.panel button {
  background:var(--s2); border:1px solid var(--border); color:var(--text);
  padding:6px 12px; border-radius:6px; cursor:pointer; font-size:13px; margin-top:8px;
  font-family:'DM Sans',sans-serif;
}
.panel button:hover { border-color:var(--gold); }

#backdrop {
  position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:45;
  opacity:0; pointer-events:none; transition:opacity 0.2s;
}
#backdrop.active { opacity:1; pointer-events:auto; }

/* Full-page blocker shown when the Python server stops responding to /health.
   Sits above every other layer (toolbar, panels, modals) and blocks all clicks. */
#server-down-overlay {
  position:fixed; inset:0; z-index:9999;
  background:rgba(8,8,10,.78);
  -webkit-backdrop-filter: blur(3px); backdrop-filter: blur(3px);
  display:none; align-items:center; justify-content:center;
  opacity:0; transition: opacity .25s ease;
}
#server-down-overlay.show { display:flex; opacity:1; }
.server-down-content {
  background:var(--s1); border:1px solid var(--border); border-radius:14px;
  padding:34px 40px; max-width:480px; text-align:center;
  box-shadow: 0 12px 40px rgba(0,0,0,.55);
}
.server-down-content h2 {
  font-family:'Cormorant Garamond',serif; font-size:24px;
  color:var(--gold); margin-bottom:14px; letter-spacing:.02em;
}
.server-down-content p {
  color:var(--text); font-size:14px; margin-bottom:10px; line-height:1.55;
}
.server-down-content p:last-child { margin-bottom:0; }
.server-down-content code {
  background:var(--s3); padding:2px 6px; border-radius:4px;
  font-size:13px; color:var(--text);
}
.server-down-hint { color:var(--muted); font-size:13px; margin-top:14px; }
.server-down-spinner {
  width:34px; height:34px; margin:0 auto 18px;
  border:3px solid var(--border); border-top-color:var(--gold);
  border-radius:50%;
  animation: spin .9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Chat list */
.chat-item {
  display:flex; align-items:flex-start; gap:6px;
  padding:10px 8px; margin: 0 -8px 2px;
  border-radius:7px; cursor:pointer;
  transition: background .15s;
}
.chat-item:hover { background:var(--s2); }
.chat-item.active { background:rgba(201,168,76,.08); border-left:2px solid var(--gold); padding-left:10px; }
.chat-item-main { flex:1; min-width:0; }
.chat-item-title {
  font-size:.88rem; color:var(--text); line-height:1.4;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
  overflow:hidden; word-break:break-word;
}
.chat-item-meta { font-size:.7rem; color:var(--muted); margin-top:3px; }
.chat-item-actions { display:flex; gap:2px; flex-shrink:0; }
.chat-item-del {
  background:transparent; border:none; color:var(--muted); cursor:pointer;
  font-size:12px; padding:2px 6px; border-radius:4px;
  opacity:0; transition: opacity .15s, color .15s, background .15s;
}
.chat-item:hover .chat-item-del { opacity:.55; }
.chat-item-del:hover { color:#fff; background:var(--red); opacity:1 !important; }

/* Running indicator on a chat item — animated dots before the title */
.chat-item-typing { display:none; gap:4px; align-items:center; margin-right:8px; vertical-align:middle; }
.chat-item.running .chat-item-typing { display:inline-flex; }
.chat-item-typing span { width:5px; height:5px; border-radius:50%; background:var(--gold); animation:pulse 1.2s infinite ease-in-out; }
.chat-item-typing span:nth-child(2) { animation-delay:.2s; }
.chat-item-typing span:nth-child(3) { animation-delay:.4s; }

/* Pulsing blue "unread" dot — surfaces when a background chat completes */
.chat-item.unread .chat-item-title::before {
  content:''; display:inline-block;
  width:8px; height:8px; border-radius:50%;
  background:var(--blue); margin-right:8px; vertical-align:middle;
  animation: unreadPulse 1.8s ease-in-out infinite;
}
@keyframes unreadPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(74,114,168,.55); }
  50%      { box-shadow: 0 0 0 5px rgba(74,114,168,0);   }
}

/* +New chat button inside the chats panel */
.add-btn {
  display:block; width:100%; text-align:center;
  background:transparent; border:1px dashed var(--border); color:var(--muted);
  padding:9px 12px; border-radius:8px; cursor:pointer; font-size:13px;
  margin-bottom:14px;
  transition: color .15s, border-color .15s, background .15s;
}
.add-btn:hover { color:var(--gold); border-color:var(--gold); background:var(--s2); }

/* Empty state */
.empty-state {
  text-align:center; color:var(--muted); font-size:13px;
  padding:30px 10px; font-style:italic;
}

/* Misc */
.notice { padding:10px 14px; background:var(--s2); border-left:3px solid var(--gold); border-radius:4px; color:var(--muted); font-size:13px; margin: 8px 0; }
.error-banner { padding:10px 14px; background:rgba(192,84,74,.08); border:1px solid rgba(192,84,74,.30); border-radius:8px; color:#e8a89e; font-size:13px; margin: 8px 0; }

/* Scroll-to-bottom button — shown when user has scrolled up from the latest content */
#scroll-down-btn {
  position:fixed; right:24px; bottom:140px;
  width:38px; height:38px; border-radius:50%;
  background:var(--gold); color:#0e0e0f; border:none; cursor:pointer;
  font-size:16px; line-height:1;
  display:flex; align-items:center; justify-content:center;
  box-shadow: 0 4px 14px rgba(0,0,0,.4);
  opacity:0; pointer-events:none; transform:translateY(8px);
  transition: opacity .2s ease, transform .2s ease;
  z-index:260;
}
#scroll-down-btn.show { opacity:.94; pointer-events:auto; transform:translateY(0); }
#scroll-down-btn:hover { opacity:1; }

/* Toast for transient feedback ("Chat deleted", etc.) */
#toast {
  position:fixed; bottom:140px; left:50%;
  transform: translateX(-50%) translateY(60px);
  background:var(--s3); border:1px solid var(--border); border-radius:8px;
  padding:10px 18px; font-size:13px; color:var(--text);
  z-index:300; opacity:0; pointer-events:none; white-space:nowrap;
  transition: opacity .25s, transform .25s;
}
#toast.show { opacity:1; transform:translateX(-50%) translateY(0); }
</style>
</head>
<body>

<div id="backdrop" onclick="closeAllPanels()"></div>

<!-- Server-down overlay. Covers everything when the Python backend stops
     answering /health. Dismisses automatically when it's back. -->
<div id="server-down-overlay" aria-live="polite">
  <div class="server-down-content">
    <div class="server-down-spinner"></div>
    <h2>Server unreachable</h2>
    <p>The Council's Python server isn't responding. The page is paused until it's back.</p>
    <p class="server-down-hint">Check that <code>python3 council.py</code> is still running in your terminal. The page will resume on its own once the server answers.</p>
  </div>
</div>

<div id="toolbar">
  <div id="toolbar-left">
    <button class="tb-btn" onclick="togglePanel('chats')" title="Chats (history)">☰</button>
    <button class="tb-btn" onclick="newChat()" title="New chat (Cmd/Ctrl+K)">+ New</button>
  </div>
  <div id="toolbar-center">
    <div class="tb-title">⚖ The Council</div>
  </div>
  <div id="toolbar-right">
    <button class="tb-btn" onclick="togglePanel('settings')" title="Settings">⚙</button>
  </div>
</div>

<!-- Chat list panel -->
<div class="panel" id="panel-chats">
  <h3>Chats</h3>
  <button class="add-btn" onclick="newChat()">+ New chat</button>
  <div id="chat-list"></div>
</div>

<!-- Settings panel -->
<div class="panel right" id="panel-settings">
  <h3>Settings</h3>

  <label>Provider</label>
  <div style="display:flex; gap:6px;">
    <button onclick="setProvider('cli')" id="prov-cli">CLI</button>
    <button onclick="setProvider('api')" id="prov-api">API key</button>
  </div>

  <div id="api-key-block">
    <label>Anthropic API key</label>
    <input type="password" id="api-key-input" oninput="onApiKeyInput(event)" placeholder="sk-ant-...">
    <button onclick="clearApiKey()">Clear key</button>
  </div>

  <label>Writing Goal</label>
  <textarea id="house-style-input" oninput="onHouseStyleInput()"></textarea>
  <div style="display:flex; gap:6px;">
    <button onclick="resetHouseStyle()">Reset</button>
    <button onclick="clearHouseStyle()">Clear</button>
  </div>

  <label>Reasoning Standards</label>
  <textarea id="reasoning-input" oninput="onReasoningInput()"></textarea>
  <div style="display:flex; gap:6px;">
    <button onclick="resetReasoning()">Reset</button>
    <button onclick="clearReasoning()">Clear</button>
  </div>

  <label>Model overrides (advanced)</label>
  <div style="font-size:12px; color:var(--muted); margin-bottom:6px;">
    Leave blank to use defaults. CLI mode ignores these (uses your CLI's configured model).
  </div>
  <label style="margin-top:6px;">Drafter / Reviser (heavy)</label>
  <input type="text" id="model-heavy" oninput="onModelInput('heavy', event)" placeholder="claude-opus-4-6">
  <label>Critics</label>
  <input type="text" id="model-critic" oninput="onModelInput('critic', event)" placeholder="claude-sonnet-4-6">
  <label>Style Auditor (fast)</label>
  <input type="text" id="model-fast" oninput="onModelInput('fast', event)" placeholder="claude-haiku-4-5-20251001">
  <label>Quick mode</label>
  <input type="text" id="model-quick" oninput="onModelInput('quick', event)" placeholder="claude-sonnet-4-6">
</div>

<div id="main">
  <div id="thread" class="thread"></div>
</div>

<button id="scroll-down-btn" onclick="scrollToBottom()" title="Jump to latest">↓</button>
<div id="toast"></div>

<div id="input-bar">
  <div id="input-inner">
    <textarea id="input" placeholder="Ask the Council...   (Cmd/Ctrl+Enter to send)" rows="2"></textarea>
    <div id="input-controls">
      <div class="mode-toggle" title="Quick = single Claude reply. Full = Drafter → Critics → Reviser → Style Auditor → Distiller.">
        <button class="mode-btn" id="mode-quick" onclick="setMode('quick')">Quick</button>
        <button class="mode-btn active" id="mode-full" onclick="setMode('full')">Full</button>
      </div>
      <button id="send-btn" onclick="handleSend()">Send</button>
      <button id="abort-btn" onclick="handleAbort()">Stop</button>
    </div>
  </div>
</div>

<script>
// ============================================================
// DEFAULT WRITING GOAL — prepended to every agent.
// User-editable in Settings.
// ============================================================
const DEFAULT_HOUSE_STYLE = `WRITING GOAL

Demystification. Use plain, common language and keep cognitive load low,
while staying precise enough that a specialist would agree it's
accurate. Be hard on the topic, soft on the reader: anticipate where
someone might feel defensive, but don't soften what's actually true.
Where something is uncertain, contested, or where an expert would
object, surface that directly in plain terms — don't hide it behind
jargon, hedging, emotional appeals, or common misreadings the reader
might bring in.

Drifts to avoid:
  (1) academic drift — reaching for Latinate words, nominalizations, or
      jargon when a common word works.
  (2) bland drift — hedging or both-sidesing until no real claim is
      made.
  (3) false accessibility — oversimplifying in a way a specialist would
      object to.
  (4) emotional cushioning that buries the actual point.
  (5) weight drift — using a phrase that does more work than the point
      requires. The phrase carries an extra connotation the writer did
      not intend, and the reader spends effort deciding which reading
      was meant. Recurring offenders:
        - "the standard move is to X" reads as "this always happens."
          If the point is that the move is socially permitted rather
          than that it always occurs, "an accepted move is to X" is
          closer to the actual claim and lighter on the reader.
        - "is treated as" can usually be replaced by a plain verb —
          "passes as," "counts as," "reads as," or just "is."
        - "gets X-ed" / "gets X-ed as" ("gets met with," "gets heard
          as," "gets read as") is a passive-voice tic that hides the
          subject. Replace with the plain active verb: "gets met
          with" → "is answered with"; "gets heard as" → "reads as";
          "gets read as" → "reads as." If the writer can't name the
          actor doing the action, the agentless "is" form is still
          shorter than "gets X-ed."
        - in-house jargon like "demand a ready policy solution"
          reduces to "ask for a fix on the spot." If a phrase sounds
          like a policy memo, it is doing too much work for its
          content.
If accessibility and precision seem to conflict in a sentence, flag
that sentence rather than silently picking one.

Connective tissue. Between two clauses joined by a semicolon, comma,
or em-dash, the relationship between them should be explicit. If the
second clause contradicts the first, say "but." If it replaces the
first, say "instead." If it follows from the first, say "so." Reading
"X; Y" and having to infer the relationship from context costs the
reader effort the writer can spend a single word to save. Self-check:
read each multi-clause sentence and ask whether a connective word
would make the relationship one read shorter. If yes, add it.

Self-check before releasing a version: a smart non-expert should
understand it on first read; a specialist should read it and not
wince; no sentence should hedge without saying anything. If any of
those fail, rewrite.`;

const DEFAULT_REASONING_STANDARDS = `REASONING STANDARDS (applied alongside the writing goal above):

Truth must remain distinguishable from falsehood. Any reasoning method that, applied consistently, would justify both a claim and its contradiction — or would defend any belief equally well — is not a method. Reject it.

Standards are uniform. Whatever bar of evidence and logic you apply to a competing position applies to your own. No self-exemption.

Parity-of-deficiency. If your view has an explanatory deficiency at some level, don't criticize an opposing view for the same deficiency at the same level without first showing your own view isn't subject to it.

Steelman before critique. Engage the strongest version of an opposing view. Refuting a weak version proves nothing about the strong one.

Every claim worth defending must be writable as explicit premises leading to a conclusion. Surface hidden assumptions. No "obviously this follows" used as a stand-in for an unstated chain of inference. No logical leaps where a real inference step is required.

Argument from ignorance fails in both directions. "We don't know yet, therefore X" is invalid whether X is positive or negative. Gaps are questions, not evidence either way.

Hyperskepticism is rejected. Appealing to the mere possibility of being wrong, without supplying a competing explanation that has comparable evidence and constraints, is not a refutation — it's a move that defeats any claim, true or false.

Ad hoc rescues are rejected. Modifications that apply only to the case under attack, with no principled generalization to other cases, defend false claims as effectively as true ones.

Best-fit explanation requires explicit comparison against steelmanned alternatives under uniform standards. Internal coherence alone doesn't earn the conclusion.

Mark confidence explicitly when it matters. Distinguish "firmly known" (universal observation, survives known objections) from "reasonably confident" (strong best-fit with open links) from "consistent but underdetermined" (no contradiction known, no decisive distinguisher from alternatives). Don't speak with uniform certainty regardless of evidential standing.`;

// ============================================================
// AGENT PROMPTS — six agents in the pipeline + one Quick agent.
// Each is written in the writing-goal style itself, so the agent
// sees the style modeled in the same context that asks for it.
// ============================================================

const DRAFTER_PROMPT = `You are answering the user's question directly. Write the best honest answer you can.

The writing goal and reasoning standards are prepended above. Follow them. Specifically:

Front the actual answer. If the question has a clear answer, lead with it before paragraph two. If the question doesn't have a single answer, say what the actual choice is in one sentence before exploring it. Do not preamble. Do not restate the question. Do not open with "great question." Do not survey perspectives before committing to one.

Use plain words. When a specialist term is genuinely needed, introduce it and immediately give the plain-English version in the same sentence, or skip the term if a common phrase carries the load. Words to refuse unless you gloss them right there: phenomenal, supervenience, qualia, a posteriori, qua, ontology, epistemology, instantiation, instantiated, supervenes, reducible, irreducible, constitutive, constituted, mereological, intentionality, reification, hypostatization. If you find yourself reaching for any of those, the plain version usually exists and is one substitution away.

Refuse weight-drift phrases. Specifically: "the standard move is to X," "the standard X response," "is treated as," "gets X-ed," "gets X-ed as," "the received view," "it goes without saying," "obviously," "clearly," "needless to say," "of course" (when used to wave a step past). If a move is socially accepted rather than universal, say "an accepted move is" or "one common response is" instead.

Make connectives explicit. Between any two clauses joined by a semicolon, comma, or em-dash, the relation must be named. Use "but" for contradiction, "instead" for replacement, "so" for consequence, "because" for cause, "in other words" for restatement. Read every multi-clause sentence and ask whether a connective word would make the relation one read shorter; if yes, add it.

Where the question is contested, surface that in plain terms. Don't hedge into mush. Don't both-side until no claim is made. "We don't know whether X" is a real statement; "reasonable people disagree" is wallpaper.

Where you make a claim worth defending, write it as explicit premises leading to a conclusion. Surface hidden assumptions. No logical leaps where a real inference step is needed.

Where you reference a position by name, give the actual inferential move, not the credential. "Dennett argues X because Y" is a real reference; "Dennett argues X" is not.

Length: scale to the question. A simple question gets a short answer. A complex contested question gets a longer one. Do not pad. Do not truncate.

Format: prose only. No bullet lists. No numbered sections. Paragraph breaks and clear topic sentences are the structure.

If you are answering a follow-up question that builds on a prior turn, treat the prior turn as available context, not as a script. Engage the new question.`;

const METHOD_CRITIC_PROMPT = `You are the Methodological Critic. The draft below is an answer to the user's question. Your job is to find every reasoning failure in it. You are not writing your own answer; you are auditing.

Audit the draft against this checklist:

Unearned premises — any claim doing inferential work that hasn't been argued for. Quote the sentence and say what's smuggled.

Hidden assumptions — any "obviously," "clearly," "of course" that stands in for an unstated step. Name the missing step.

Logical leaps — any inference from A to B where the step between them isn't given. Name what's skipped.

Hyperskepticism — any objection that, applied consistently, would defeat any claim equally, including the draft's own. Show the symmetry.

Argument from ignorance — any inference of the form "we don't know X, therefore Y," in either direction.

Ad hoc rescues — any modification to a claim that only applies to the case under attack with no principled generalization to other cases.

Parity-of-deficiency violations — any critique of an opposing view for a deficiency the draft itself shares at the same level, without first showing the draft doesn't have it.

Term overloading — any word doing different work in different sentences without flagging the switch. Watch especially for: physical, natural, real, purpose, random, arbitrary, need, explanation, exists.

Category errors — any explanation that answers a question at one level (mechanism, phenomenology, normative) with an account at another level, without earning the cross-level move.

Forced alignment — any reinterpretation of awkward evidence to make it fit a preferred framework, where the fit had to be coerced rather than being natural.

For each finding, quote the offending sentence verbatim, then state the problem in one or two sentences, then propose how the draft would have to change to fix it.

If the draft has none of these, say so plainly. Do not manufacture findings to fill space. "No methodological problems found" is a valid output when the draft is clean.

You may not rewrite the draft. You may not write your own version of the answer. Audit only.

Length: scale to the draft. A short draft might generate two findings; a long contested draft might generate eight. Aim for accuracy, not coverage.

Format: prose. Each finding is a short paragraph. No bullet lists.

Follow the writing goal in your own prose. Your critique is read by the Reviser; sloppy prose in the critique costs the revision pass.`;

const OPPOSE_CRITIC_PROMPT = `You are the Opposing-View Critic. The draft below commits to a position. Your job: write the strongest available case against it — the case a careful, well-read specialist who genuinely disagreed with the draft would write if given the floor.

You are not summarizing what opponents have said. You are writing the case yourself, as if you were the opposition, against this specific draft.

Constraints:

Name actual moves. "The phenomenal-concepts strategy" is a label; "the move is to say that we have two kinds of concepts about the same brain state, and the apparent gap is a gap between concepts of one thing, not a gap in reality" is the move. Always give the move, not the label.

If you name a person, the name is followed by the inference step they make, not just the position they hold. Replace "Dennett argues this is illusion" with "Dennett's move is to say the seeming-of-experience is itself a representational state, so the report of inside-feel can be a fully physical event without inside-feel in the rich sense being present." The user's writing goal explicitly forbids names-as-arguments.

Engage the draft's specific claims, not the general topic. "The draft says X in paragraph three; the strongest opposition reply is Y."

Pick the hardest version of the opposition. Steelman the opponent — not the easiest opposition, the hardest. If the draft has already addressed an opposition move, pick a harder one or a sharper version. Don't restate what the draft already engaged.

Do not write a balanced both-sides survey. You are the opposition. Argue.

Follow the writing goal: plain language, no jargon without immediate gloss, no weight drift, explicit connectives. Your critique is read by the Reviser, so its prose has to be clean enough to drive a good revision.

If the draft has no serious opposition worth engaging on its specific commitments, say so. Most drafts on contested questions have serious opposition; if this one doesn't, that's itself worth flagging.

Length: 3–6 paragraphs. Prose. No bullet lists.`;

const STYLE_CRITIC_PROMPT = `You are the Style Critic. Read the draft below sentence by sentence. Find every sentence that drifts from the writing goal prepended above.

For each offending sentence:
quote the sentence verbatim,
name the drift (academic drift, bland drift, false accessibility, emotional cushioning, weight drift, missing connective, undefined specialist term),
propose a rewrite that preserves the substance but fixes the drift.

Things to flag, with specific examples of what they look like:

Specialist terms used without an immediate plain-English gloss. Especially: phenomenal, supervenience, qualia, a posteriori, ontology, epistemology, instantiation, supervenes, reducible, irreducible, constitutive, mereological, intentionality, reification.

Weight-drift phrases. Specifically: "the standard move is to X," "the standard X response," "is treated as," "gets X-ed," "gets X-ed as," "the received view," "it goes without saying," "obviously," "clearly," "of course," "needless to say." The writing goal calls these out by name.

Semicolons, commas, and em-dashes joining clauses without explicit connective words. The relation must be named — "but," "instead," "so," "because," "in other words." Cite the sentence and propose the connective.

Hedging that says nothing: "reasonable people disagree," "it depends on your values," "this is a personal decision," "there's truth to both sides," "context matters." These are wallpaper, not claims.

Latinate vocabulary or nominalizations when a plain word works. "The explanation of consciousness" → "explaining consciousness." "The implementation of X" → "running X." "Subsequent to" → "after."

Emotional cushioning that buries the point. "This is a really hard question," "I want to be careful here," "I appreciate that you're thinking about this carefully," "what a great question."

If the draft is clean — say so. Do not manufacture findings.

You may not rewrite the entire draft. Only the offending sentences, one at a time.

Format: prose. Each finding is a short paragraph: quote, drift name, proposed rewrite. No bullet lists.`;

const REVISER_PROMPT = `You are the Reviser. You have the original draft, plus three critiques — methodological, opposing-view, and style. Your output is a single revised answer that addresses what the critiques surfaced. The reader of your output sees the new answer, not a discussion of what the critiques said.

For each methodological finding the Methodological Critic surfaced: either fix the underlying reasoning in the revised answer, or acknowledge the limit in the answer itself ("the strongest counter-argument here is X, and the answer to that is Y"). Do not pretend the finding doesn't exist. If the critic is wrong or overreaches, you may ignore the finding — but only after a real read, not by reflex.

For the opposing-view critique: the revised answer must engage the strongest opposition move the critic raised, not the easiest. Either show why the opposition's strongest move fails, or concede the relevant ground and adjust your claim. Do not ignore the opposition.

For the style critique: apply every legitimate rewrite. The critic's findings are usually correct in spirit even if their specific proposed rewrites need work; produce the cleanest version of the answer, not a mechanical search-and-replace.

You are not producing meta-commentary on the critiques. You are producing the revised answer itself.

Follow the writing goal strictly. This is the deliverable. The Style Auditor runs after you, but it can only do sentence-level cleanup. Substance-level style work — vocabulary choice, paragraph structure, where to lead with the answer, how to introduce specialist terms — is your job.

Front the actual answer. Plain language. Explicit connectives. No weight drift. No undefined specialist terms. No bland hedging. The writing goal lists the specific phrases to refuse; refuse them.

Length: comparable to the original draft, scaled to what the critiques opened up. If the draft had six paragraphs, the revision is usually five to eight. Do not pad. Do not truncate.

Format: prose. No bullet lists, no numbered sections, no preambles, no closing summary unless the question genuinely asks for action items.

End with something usable, if the question called for it. Specific things the reader should consider or do, in their own situation. Not generic platitudes. Not "it depends on your values."`;

const DISTILLER_PROMPT = `You are the Distiller. The polished final answer is below. Your job: produce a short summary — two or three sentences — that the user can read first to know what the full answer actually says.

This is not a teaser. It is the plain-words version. If the full answer is "the source of awareness can't be fully captured by external description, but it's not necessarily a separate immaterial substance — the cleanest landing is the view that physics describes structure and inside-feel is what that structure is from the inside," the distilled version is something like: "Your argument shows that brain-from-outside descriptions don't fully explain inside-feel, which is real. It does not show there's a separate soul; that would need different arguments. The cleanest place to land is the view that physics describes structure and inside-feel is what that structure is from the inside — same one thing, two faces."

Constraints:

Two or three sentences. Not paragraphs, not bullet lists, not headers. Just sentences.

Plain words. Refuse jargon more strictly than the rest of the pipeline did — this is the demystified version. If a specialist term is necessary, give the plain-English version in the same sentence. If the full answer used a term like "Russellian monism" or "phenomenal concepts," the distilled version either glosses it inline or uses the plain version instead.

State what the answer actually says, not what it touches on. "The argument is interesting and raises important questions" is wallpaper. "Your argument shows X but does not show Y" is content.

Do not editorialize. Do not add new claims. Do not soften. You are translating, not rewriting. If the full answer says something hard, the distilled version says the same hard thing in plainer words.

If the question was a follow-up in a conversation, the distilled version stands alone — someone reading just it should understand what the answer was.

Output the summary directly. No preamble ("Here's the summary:", "To distill this:"). No closer ("In short:", "Bottom line:"). Just the sentences.`;

const AUDITOR_PROMPT = `You are the Style Auditor. The answer below has been through three critiques and a revision pass. Your only job: catch what the revision still misses on style, and rewrite those sentences in place.

Your authority: sentence-level rewrites only. You may not change substance. You may not add or remove arguments. You may only rewrite sentences whose form violates the writing goal.

Things to catch and fix:

"The standard X," "the received view," "is treated as," "gets X-ed" — rewrite using the plain verb.

Unintroduced specialist terms — either gloss them inline in the same sentence, or remove them and substitute the plain version.

Semicolon / comma / em-dash joining clauses without an explicit connective — insert the connective ("but," "so," "because," "instead," "in other words").

Hedging that says nothing — "reasonable people disagree," "it depends on your values," "context matters" — cut, unless the sentence around it does real work.

Latinate phrasing when a plain word works — substitute.

Nominalizations — "the explanation of X" → "explaining X."

Output: the full answer with the offending sentences rewritten in place. No preamble, no commentary, no list of what you changed. Just the cleaned text.

If you find nothing to change, output the answer verbatim.`;

const QUICK_PROMPT = `You are responding to a user in an ongoing conversation. Engage substantively with the user's message. Read any prior conversation as context.

Follow the writing goal and reasoning standards prepended above. Be direct. Do not hedge. Do not preamble. Do not restate the question. Do not open with "great question." Just respond.`;

// ============================================================
// AGENT DEFINITIONS
// ============================================================
const DRAFTER = {
  id:'drafter', name:'The Drafter', label:'First draft',
  icon:'✎', color:'blue', stage:1, system: DRAFTER_PROMPT,
};

const METHOD_CRITIC = {
  id:'method', name:'Methodological Critic', label:'Reasoning audit',
  icon:'∴', color:'orange', stage:2, system: METHOD_CRITIC_PROMPT,
};

const OPPOSE_CRITIC = {
  id:'oppose', name:'Opposing-View Critic', label:'Strongest opposition',
  icon:'⚔', color:'red', stage:2, system: OPPOSE_CRITIC_PROMPT,
};

const STYLE_CRITIC = {
  id:'style', name:'Style Critic', label:'Writing-goal audit',
  icon:'✒', color:'purple', stage:2, system: STYLE_CRITIC_PROMPT,
};

const CRITICS = [METHOD_CRITIC, OPPOSE_CRITIC, STYLE_CRITIC];

const REVISER = {
  id:'reviser', name:'The Reviser', label:'Revision',
  icon:'❀', color:'green', stage:3, system: REVISER_PROMPT,
};

const AUDITOR = {
  id:'auditor', name:'Style Auditor', label:'Final polish',
  icon:'❖', color:'gold', stage:4, system: AUDITOR_PROMPT,
};

const DISTILLER = {
  id:'distiller', name:'The Distiller', label:'Plain-words summary',
  icon:'◇', color:'gold', stage:5, system: DISTILLER_PROMPT,
};

const QUICK = {
  id:'quick', name:'Claude', label:'Reply',
  icon:'⟡', color:'slate', stage:0, system: QUICK_PROMPT,
};

// ============================================================
// MODEL DEFAULTS — user can override in Settings.
// API mode uses these exact strings; CLI mode ignores them and
// uses whatever `claude` is configured to use.
// ============================================================
const DEFAULT_MODELS = {
  heavy:  'claude-opus-4-6',           // Drafter, Reviser
  critic: 'claude-sonnet-4-6',         // 3 critics
  fast:   'claude-haiku-4-5-20251001', // Style Auditor
  quick:  'claude-sonnet-4-6',         // Quick mode
};

// ============================================================
// STATE — single chat at a time. Per-chat parallel runtime was
// in v1; v2 ships single-chat to keep the new pipeline simple.
// ============================================================
const S = {
  provider: 'cli',          // 'cli' | 'api'
  apiKey: '',
  houseStyle: DEFAULT_HOUSE_STYLE,
  reasoningStandards: DEFAULT_REASONING_STANDARDS,
  models: { ...DEFAULT_MODELS },
  mode: 'full',             // 'quick' | 'full'
  currentChatId: null,
  chats: [],
  conversation: [],         // turns [{role, ...}, ...]
  abortController: null,    // current in-flight pipeline, if any
  busy: false,
  openPanel: null,
  unread: new Set(),        // chatIds with completed work the user hasn't seen
  running: new Set(),       // chatIds currently being processed (just current in v2)
};

// localStorage keys
const LS = {
  provider: 'council.provider',
  apiKey:   'council.apiKey',
  houseStyle: 'council.houseStyle',
  reasoning:  'council.reasoning',
  models:   'council.models',
  mode:     'council.mode',
};

// ============================================================
// PROVIDER — CLI subprocess via /ask, or Anthropic API direct.
// ============================================================
const Provider = {
  async ask({ system, prompt, model, maxTokens = 4000 }, signal) {
    const fullSystem = withPreamble(system);
    if (S.provider === 'api') {
      if (!S.apiKey) throw new Error('No API key set. Switch to CLI mode in Settings, or paste a key.');
      return await this._api({ system: fullSystem, prompt, model, maxTokens }, signal);
    }
    return await this._cli({ system: fullSystem, prompt, model }, signal);
  },

  async _cli({ system, prompt, model }, signal) {
    const r = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ system, prompt, model: model || null }),
      signal,
    });
    if (!r.ok) {
      const e = new Error(`Server error ${r.status}`);
      e.status = r.status;
      throw e;
    }
    const d = await r.json();
    if (d.error) throw new Error(d.error);
    return d.text;
  },

  async _api({ system, prompt, model, maxTokens }, signal) {
    const body = {
      model: model || DEFAULT_MODELS.heavy,
      max_tokens: maxTokens,
      system,
      messages: [{ role: 'user', content: prompt }],
    };
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': S.apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify(body),
      signal,
    });
    const d = await r.json();
    if (!r.ok) {
      const e = new Error(d.error?.message || `API error ${r.status}`);
      e.status = r.status;
      throw e;
    }
    return d.content.map(b => b.text || '').join('');
  },
};

function withPreamble(systemPrompt) {
  const style     = (S.houseStyle || '').trim();
  const standards = (S.reasoningStandards || '').trim();
  const parts = [style, standards].filter(Boolean);
  if (!parts.length) return systemPrompt;
  return `${parts.join('\n\n---\n\n')}\n\n---\n\n${systemPrompt}`;
}

// ============================================================
// RETRY — exponential backoff on transient failures.
// ============================================================
function isRetryable(err) {
  if (!err) return false;
  if (err.name === 'AbortError') return false;
  const status = err.status;
  if (status === 400 || status === 401 || status === 403) return false;
  const msg = (err.message || '').toLowerCase();
  if (msg.includes('authentication') || msg.includes('invalid_api_key')) return false;
  return true;
}

function backoffMs(attempt) {
  return Math.min(1000 * Math.pow(2, attempt), 10000);
}

function sleepWithAbort(ms, signal) {
  return new Promise((resolve, reject) => {
    if (signal && signal.aborted) return reject(new DOMException('Aborted', 'AbortError'));
    const t = setTimeout(resolve, ms);
    if (signal) signal.addEventListener('abort', () => {
      clearTimeout(t); reject(new DOMException('Aborted', 'AbortError'));
    }, { once: true });
  });
}

async function askWithRetry(agent, prompt, modelKey, signal, maxAttempts = 4) {
  let lastErr;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await Provider.ask({
        system: agent.system,
        prompt,
        model: S.provider === 'api' ? (S.models[modelKey] || DEFAULT_MODELS[modelKey]) : null,
      }, signal);
    } catch (err) {
      lastErr = err;
      if (!isRetryable(err) || attempt === maxAttempts - 1) throw err;
      await sleepWithAbort(backoffMs(attempt), signal);
    }
  }
  throw lastErr;
}

// ============================================================
// PER-AGENT SKIP
//
// Each agent gets its own AbortController so the user can skip just that
// agent's call without killing the whole pipeline. A skip is recorded in
// _skipRequested before the controller is aborted, so the catch handler can
// tell a "user wants to skip" abort apart from a "pipeline-wide Stop" abort.
// When a skip is detected, the agent's effective output becomes the input
// that was already heading into the NEXT stage (the fallback value).
// ============================================================
const _activeAgentControllers = new Map();   // agentId -> AbortController
const _skipRequested = new Set();            // agentIds the user asked to skip

function requestSkip(agentId) {
  _skipRequested.add(agentId);
  const ac = _activeAgentControllers.get(agentId);
  if (ac) ac.abort();
}

async function askAgentWithSkip(agent, prompt, modelKey, pipelineSignal, fallbackInput) {
  const agentAc = new AbortController();
  _activeAgentControllers.set(agent.id, agentAc);
  // If the whole pipeline is already stopping, propagate immediately.
  if (pipelineSignal.aborted) agentAc.abort();
  const onPipelineAbort = () => agentAc.abort();
  pipelineSignal.addEventListener('abort', onPipelineAbort, { once: true });
  try {
    const text = await askWithRetry(agent, prompt, modelKey, agentAc.signal);
    return { text, skipped: false };
  } catch (err) {
    // Distinguish a per-agent skip (user pressed Skip on this seat) from a
    // whole-pipeline abort (user pressed Stop).
    if (err.name === 'AbortError' && _skipRequested.has(agent.id)) {
      _skipRequested.delete(agent.id);
      return { text: fallbackInput, skipped: true };
    }
    throw err;
  } finally {
    _activeAgentControllers.delete(agent.id);
    pipelineSignal.removeEventListener('abort', onPipelineAbort);
  }
}

// ============================================================
// CONVERSATION PREAMBLE — for follow-up turns in the same chat.
// Drafter and Reviser see this. Critics do not — they audit the
// current draft against the current question, period.
// ============================================================
function conversationPreamble() {
  if (!S.conversation.length) return '';
  let s = `## Prior conversation\n\n`;
  for (let i = 0; i < S.conversation.length; i++) {
    const t = S.conversation[i];
    if (t.role === 'user') {
      s += `User: ${t.content}\n\n`;
    } else if (t.role === 'assistant') {
      // For pipeline turns, prior assistant content is the final auditor output.
      // For quick turns, it's the quick reply itself.
      const final = t.final || t.content || '';
      if (final) s += `Council: ${final}\n\n`;
    }
  }
  return s;
}

// ============================================================
// PIPELINE — the new shape.
// Drafter -> [3 critics in parallel] -> Reviser -> Style Auditor
// ============================================================
async function runPipeline(question, signal) {
  const ctx = { question, stages: {} };

  // Stage 1: Drafter — skip falls back to the user's question.
  setSeatState(DRAFTER, 'working');
  const draftPrompt = conversationPreamble() +
    `## Current question\n\n${question}\n\nWrite your answer now.`;
  const drafterRes = await askAgentWithSkip(DRAFTER, draftPrompt, 'heavy', signal, question);
  ctx.stages.draft = drafterRes.text;
  if (drafterRes.skipped) renderSeatSkipped(DRAFTER);
  else                    renderSeat(DRAFTER, drafterRes.text);

  // Stage 2: Critics in parallel — each can be skipped independently.
  CRITICS.forEach(c => setSeatState(c, 'working'));
  const criticPrompt = `## Question the user asked\n\n${question}\n\n## Draft to audit\n\n${ctx.stages.draft}\n\nNow produce your critique.`;
  const criticResults = await Promise.allSettled(
    CRITICS.map(c => askAgentWithSkip(c, criticPrompt, 'critic', signal, `[${c.name} skipped by user]`))
  );
  ctx.stages.critiques = {};
  for (let i = 0; i < CRITICS.length; i++) {
    const c = CRITICS[i];
    const r = criticResults[i];
    if (r.status === 'fulfilled') {
      ctx.stages.critiques[c.id] = r.value.text;
      if (r.value.skipped) renderSeatSkipped(c);
      else                 renderSeat(c, r.value.text);
    } else {
      ctx.stages.critiques[c.id] = `[${c.name} failed: ${r.reason?.message || 'unknown error'}]`;
      renderSeatError(c, r.reason?.message || 'failed');
    }
  }

  // Only treat real failures as a fatal condition. Skips are user intent —
  // the Reviser can still run on whatever critiques did come through (or none).
  const realFailures = criticResults.filter(r => r.status === 'rejected').length;
  if (realFailures === CRITICS.length) {
    throw new Error('All three critics failed. Pipeline aborted.');
  }

  // Stage 3: Reviser — skip falls back to the draft.
  setSeatState(REVISER, 'working');
  let reviserPrompt = conversationPreamble() +
    `## Question the user asked\n\n${question}\n\n## Original draft\n\n${ctx.stages.draft}\n\n`;
  for (const c of CRITICS) {
    reviserPrompt += `## ${c.name} — ${c.label}\n\n${ctx.stages.critiques[c.id]}\n\n`;
  }
  reviserPrompt += `Produce the revised answer now. The reader sees your output as the answer, not a discussion of the critiques.`;
  const reviserRes = await askAgentWithSkip(REVISER, reviserPrompt, 'heavy', signal, ctx.stages.draft);
  ctx.stages.revised = reviserRes.text;
  if (reviserRes.skipped) renderSeatSkipped(REVISER);
  else                    renderSeat(REVISER, reviserRes.text);

  // Stage 4: Style Auditor — skip falls back to the revised answer.
  setSeatState(AUDITOR, 'working');
  const auditorPrompt = `## Question the user asked\n\n${question}\n\n## Answer to polish\n\n${ctx.stages.revised}\n\nOutput the polished version now. Full text, sentence-level rewrites only, no commentary.`;
  const auditorRes = await askAgentWithSkip(AUDITOR, auditorPrompt, 'fast', signal, ctx.stages.revised);
  ctx.stages.polished = auditorRes.text;
  if (auditorRes.skipped) renderSeatSkipped(AUDITOR);
  else                    renderSeat(AUDITOR, auditorRes.text, /*open=*/false);

  // Stage 5: Distiller — skip falls back to the polished answer.
  setSeatState(DISTILLER, 'working');
  const distillerPrompt = `## Question the user asked\n\n${question}\n\n## Polished answer to distill\n\n${ctx.stages.polished}\n\nProduce the two-or-three-sentence plain-words summary now.`;
  const distillerRes = await askAgentWithSkip(DISTILLER, distillerPrompt, 'fast', signal, ctx.stages.polished);
  ctx.stages.distilled = distillerRes.text;
  if (distillerRes.skipped) renderSeatSkipped(DISTILLER, /*open=*/true);
  else                      renderSeat(DISTILLER, distillerRes.text, /*open=*/true);

  // Return the polished version. Follow-up turns need the full answer as
  // context — the summary is too compressed, the draft too raw.
  return ctx.stages.polished;
}

// Render a seat that the user skipped. The body shows a small notice; the
// next stage will already have received the fallback as its real input.
function renderSeatSkipped(agent, open) {
  const seat = seatEl(agent); if (!seat) return;
  const body = seat.querySelector('.seat-body');
  body.innerHTML = `<div class="skipped-notice"><strong>Skipped.</strong> The next stage used the previous stage's output as its input.</div>`;
  setSeatState(agent, 'skipped');
  if (open) {
    seat.querySelector('.seat-header').classList.remove('collapsed');
    body.classList.remove('collapsed');
  }
  scrollToBottom(/*smooth=*/true);
}

async function runQuick(question, signal) {
  setSeatState(QUICK, 'working');
  const prompt = conversationPreamble() +
    `## New user message\n\n${question}\n\nRespond as the assistant.`;
  const reply = await askWithRetry(QUICK, prompt, 'quick', signal);
  renderSeat(QUICK, reply, /*open=*/true);
  return reply;
}

// ============================================================
// THREAD RENDERING
// ============================================================
function thread() { return document.getElementById('thread'); }

function clearThread() { thread().innerHTML = ''; }

let _currentTurnEl = null;  // div.turn for the in-progress turn

function startTurn(question) {
  const turn = document.createElement('div');
  turn.className = 'turn';

  // User message: right-aligned bubble in its own row, like a text thread.
  // S.conversation already includes this user turn (handleSend pushed it
  // before calling startTurn), so its index is the last entry.
  const userRow = document.createElement('div');
  userRow.className = 'turn-user-row';
  userRow.appendChild(makeUserBubble(question, S.conversation.length - 1));
  turn.appendChild(userRow);

  // AI seats: left-aligned, in seat-row wrappers, fade in on creation.
  const seatList = (S.mode === 'full')
    ? [DRAFTER, ...CRITICS, REVISER, AUDITOR, DISTILLER]
    : [QUICK];
  seatList.forEach((agent, idx) => {
    const row = document.createElement('div');
    row.className = 'seat-row';
    // Gold-glow only on the final stage; nothing is open at creation time
    // (each seat opens on its own completion via renderSeat).
    const isFinal = (agent === DISTILLER) || (agent === QUICK);
    // Quick mode has just one agent — skipping is meaningless. Pipeline
    // agents are skippable by default.
    const isSkippable = agent !== QUICK;
    row.appendChild(makeSeat(agent, { final: isFinal, skippable: isSkippable }));
    turn.appendChild(row);
    // Stagger the fade-in slightly so the eye can follow.
    setTimeout(() => {
      const s = row.querySelector('.seat'); if (s) s.classList.add('visible');
    }, 60 + idx * 50);
  });

  thread().appendChild(turn);
  _currentTurnEl = turn;
  scrollToBottom(/*smooth=*/true);
}

function makeSeat(agent, opts) {
  const { final = false, open = false, skippable = true } = opts || {};
  const seat = document.createElement('div');
  seat.className = 'seat' + (final ? ' final' : '');
  seat.dataset.agentId = agent.id;
  seat.dataset.color = agent.color;
  // Seats start collapsed by default. Final/headline seats open on completion
  // via renderSeat(..., true). The two concepts are now independent so the
  // Style Auditor can be non-final (no gold glow) while still appearing in
  // the pipeline.
  const collapsed = !open;
  // Quick mode has a single agent, so skipping is meaningless. Only render
  // the Skip button on agents that have a previous-stage output to fall back to.
  const skipBtnHtml = skippable
    ? `<button class="seat-skip-btn" onclick="event.stopPropagation(); requestSkip('${agent.id}')" title="Skip — next stage uses previous output">Skip</button>`
    : '';
  seat.innerHTML = `
    <div class="seat-header ${collapsed ? 'collapsed' : ''}" onclick="toggleSeat(this)">
      <div class="seat-title">
        <span class="seat-icon">${agent.icon}</span>
        <span class="seat-name">${agent.name}</span>
        <span class="seat-label">${agent.label}</span>
      </div>
      <div class="seat-actions">
        <button class="msg-copy-btn" onclick="event.stopPropagation(); copyMessageText(this)" title="Copy this response">⧉</button>
        ${skipBtnHtml}
        <div class="seat-state waiting">
          <span class="state-label">waiting</span>
          <span class="chevron">▾</span>
        </div>
      </div>
    </div>
    <div class="seat-body md ${collapsed ? 'collapsed' : ''}"></div>
  `;
  return seat;
}

// User-bubble factory — shared between live sends (startTurn) and history rendering.
// turnIndex is the 0-based position of this user turn in S.conversation;
// it's stamped on the element so the edit handler can truncate from here.
function makeUserBubble(text, turnIndex) {
  const u = document.createElement('div');
  u.className = 'turn-user';
  if (turnIndex != null) u.dataset.turnIndex = String(turnIndex);

  // textContent (not innerHTML) keeps user input safe; pre-wrap CSS keeps newlines.
  const content = document.createElement('span');
  content.className = 'user-msg-content';
  content.textContent = text || '';
  u.appendChild(content);

  const actions = document.createElement('div');
  actions.className = 'user-actions';

  const editBtn = document.createElement('button');
  editBtn.className = 'msg-copy-btn';
  editBtn.title = 'Edit this message';
  editBtn.textContent = '✎';
  editBtn.onclick = (ev) => { ev.stopPropagation(); startEdit(u); };
  actions.appendChild(editBtn);

  const copyBtn = document.createElement('button');
  copyBtn.className = 'msg-copy-btn';
  copyBtn.title = 'Copy this message';
  copyBtn.textContent = '⧉';
  copyBtn.onclick = (ev) => { ev.stopPropagation(); copyMessageText(copyBtn); };
  actions.appendChild(copyBtn);

  u.appendChild(actions);
  return u;
}

// ============================================================
// INLINE MESSAGE EDIT — click ✎ on a user bubble to edit in place.
// Saving discards every turn from this one onward (backend truncate),
// then re-sends with the new text. No branching.
// ============================================================
function startEdit(bubble) {
  if (!bubble || bubble.classList.contains('editing')) return;
  const turnIndex = parseInt(bubble.dataset.turnIndex, 10);
  if (isNaN(turnIndex)) { showToast("Can't edit this message"); return; }
  const current = bubble.querySelector('.user-msg-content')?.textContent || '';
  // Stash the original markup so Cancel can restore it without a re-render.
  bubble._originalHTML = bubble.innerHTML;
  bubble.classList.add('editing');
  bubble.innerHTML = `
    <textarea class="edit-textarea" spellcheck="true"></textarea>
    <div class="edit-actions">
      <button class="edit-cancel" onclick="cancelEdit(this)">Cancel</button>
      <button class="edit-save" onclick="saveEdit(this)">Save &amp; resend</button>
    </div>
  `;
  const ta = bubble.querySelector('.edit-textarea');
  ta.value = current;
  ta.focus();
  // Move caret to end and autosize.
  ta.setSelectionRange(ta.value.length, ta.value.length);
  ta.style.height = 'auto';
  ta.style.height = Math.min(ta.scrollHeight, 340) + 'px';
  ta.addEventListener('input', () => {
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 340) + 'px';
  });
  ta.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') { ev.preventDefault(); cancelEdit(ta); }
    if (ev.key === 'Enter' && (ev.metaKey || ev.ctrlKey)) { ev.preventDefault(); saveEdit(ta); }
  });
}

function cancelEdit(el) {
  const bubble = el.closest('.turn-user');
  if (!bubble) return;
  bubble.classList.remove('editing');
  if (bubble._originalHTML) {
    bubble.innerHTML = bubble._originalHTML;
    // Re-bind onclick handlers on the restored buttons.
    const btns = bubble.querySelectorAll('.msg-copy-btn');
    if (btns[0]) btns[0].onclick = (ev) => { ev.stopPropagation(); startEdit(bubble); };
    if (btns[1]) btns[1].onclick = (ev) => { ev.stopPropagation(); copyMessageText(btns[1]); };
  }
}

async function saveEdit(el) {
  const bubble = el.closest('.turn-user');
  if (!bubble) return;
  const turnIndex = parseInt(bubble.dataset.turnIndex, 10);
  if (isNaN(turnIndex)) { showToast('Edit failed'); return; }
  const newText = bubble.querySelector('.edit-textarea').value.trim();
  if (!newText) { showToast('Empty message'); return; }

  // If a pipeline is in flight, confirm before tearing it down.
  if (S.busy) {
    if (!confirm('A response is in progress. Save will stop it and re-run with the edited message. Continue?')) return;
    handleAbort();
    await waitForCurrentRun();
  }
  await _restartFromTurn(turnIndex, newText);
}

function toggleSeat(headerEl) {
  const seat = headerEl.closest('.seat');
  const body = seat.querySelector('.seat-body');
  headerEl.classList.toggle('collapsed');
  body.classList.toggle('collapsed');
}

function seatEl(agent) {
  if (!_currentTurnEl) return null;
  return _currentTurnEl.querySelector(`.seat[data-agent-id="${agent.id}"]`);
}

// state is one of: 'waiting', 'working', 'done', 'skipped', 'error'.
// 'working' renders animated dots and exposes the Skip button; others render plain text.
function setSeatState(agent, state, label) {
  const seat = seatEl(agent); if (!seat) return;
  applySeatState(seat, state, label);
}

function applySeatState(seat, state, label) {
  const stateEl = seat.querySelector('.seat-state'); if (!stateEl) return;
  stateEl.classList.remove('waiting', 'working', 'done', 'skipped', 'error');
  stateEl.classList.add(state);
  // The Skip button is only meaningful while the agent is actively running.
  const skipBtn = seat.querySelector('.seat-skip-btn');
  if (skipBtn) skipBtn.style.display = (state === 'working') ? 'inline-block' : 'none';
  let bodyHtml = '';
  if (state === 'working')      bodyHtml = `<span class="typing"><span></span><span></span><span></span></span>`;
  else if (state === 'done')    bodyHtml = `<span class="check">✓</span>`;
  else if (state === 'skipped') bodyHtml = `<span class="state-label">skipped</span>`;
  else                          bodyHtml = `<span class="state-label">${escapeHtml(label || state)}</span>`;
  stateEl.innerHTML = `${bodyHtml}<span class="chevron">▾</span>`;
}

function renderSeat(agent, text, open) {
  const seat = seatEl(agent); if (!seat) return;
  const body = seat.querySelector('.seat-body');
  body.innerHTML = renderMarkdown(text);
  setSeatState(agent, 'done');
  if (open) {
    // Auto-expand when the caller flags this seat as the headline of its turn.
    seat.querySelector('.seat-header').classList.remove('collapsed');
    body.classList.remove('collapsed');
  }
  scrollToBottom(/*smooth=*/true);
}

function renderSeatError(agent, msg) {
  const seat = seatEl(agent); if (!seat) return;
  const body = seat.querySelector('.seat-body');
  body.innerHTML = `<div class="error-banner">${escapeHtml(msg)}</div>`;
  setSeatState(agent, 'error', 'error');
  // Auto-expand so the error is visible without an extra click.
  seat.querySelector('.seat-header').classList.remove('collapsed');
  body.classList.remove('collapsed');
}

// ============================================================
// LIGHTWEIGHT MARKDOWN RENDERER — paragraphs, bold/italic,
// code, blockquotes, headers, simple lists. No external deps.
// ============================================================
function renderMarkdown(text) {
  if (!text) return '';
  const lines = text.split('\n');
  const out = [];
  let i = 0;
  let inCode = false;
  let codeBuf = [];
  while (i < lines.length) {
    const ln = lines[i];
    if (ln.startsWith('```')) {
      if (!inCode) { inCode = true; codeBuf = []; }
      else { out.push(`<pre><code>${escapeHtml(codeBuf.join('\n'))}</code></pre>`); inCode = false; }
      i++; continue;
    }
    if (inCode) { codeBuf.push(ln); i++; continue; }

    // Headers
    let m = ln.match(/^(#{1,3})\s+(.*)$/);
    if (m) { out.push(`<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`); i++; continue; }

    // Blockquote (one line at a time)
    if (ln.startsWith('> ')) { out.push(`<blockquote>${inline(ln.slice(2))}</blockquote>`); i++; continue; }

    // Lists
    if (/^[-*]\s+/.test(ln)) {
      const items = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        items.push(`<li>${inline(lines[i].replace(/^[-*]\s+/, ''))}</li>`);
        i++;
      }
      out.push(`<ul>${items.join('')}</ul>`); continue;
    }
    if (/^\d+\.\s+/.test(ln)) {
      const items = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        items.push(`<li>${inline(lines[i].replace(/^\d+\.\s+/, ''))}</li>`);
        i++;
      }
      out.push(`<ol>${items.join('')}</ol>`); continue;
    }

    // Paragraph (gather contiguous non-empty lines)
    if (ln.trim() === '') { i++; continue; }
    const para = [];
    while (i < lines.length && lines[i].trim() !== '' && !lines[i].startsWith('```') && !/^#{1,3}\s/.test(lines[i]) && !lines[i].startsWith('> ') && !/^[-*]\s/.test(lines[i]) && !/^\d+\.\s/.test(lines[i])) {
      para.push(lines[i]); i++;
    }
    out.push(`<p>${inline(para.join(' '))}</p>`);
  }
  return out.join('\n');
}

function inline(s) {
  s = escapeHtml(s);
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/(^|[^*])\*([^*]+)\*/g, '$1<em>$2</em>');
  s = s.replace(/_([^_]+)_/g, '<em>$1</em>');
  return s;
}

function escapeHtml(s) {
  return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ============================================================
// PRIOR TURN RENDERING — when loading an existing chat.
// ============================================================
function renderPriorTurn(turn, turnIndex) {
  const turnEl = document.createElement('div');
  turnEl.className = 'turn';
  if (turn.role === 'user') {
    const row = document.createElement('div');
    row.className = 'turn-user-row';
    row.appendChild(makeUserBubble(turn.content || '', turnIndex));
    turnEl.appendChild(row);
    thread().appendChild(turnEl);
    return;
  }
  // assistant
  if (turn.mode === 'quick') {
    const row = document.createElement('div'); row.className = 'seat-row';
    const seat = makeSeat(QUICK, { final: true, open: true, skippable: false });
    seat.classList.add('visible');
    row.appendChild(seat);
    turnEl.appendChild(row);
    thread().appendChild(turnEl);
    const body = seat.querySelector('.seat-body');
    body.innerHTML = renderMarkdown(turn.content || turn.final || '');
    setSeatStateOn(seat, 'done');
    return;
  }
  // full pipeline (also handles legacy 'pipeline' / pre-Distiller chats
  // where 'auditor' or 'final_synth' was the final stage).
  const seats = turn.seats || [];
  const hasDistiller = seats.some(r => r.id === 'distiller');
  for (const r of seats) {
    const agent = agentById(r.id) || {id:r.id, name:r.name, label:r.label, icon:r.icon, color:r.color};
    // New shape: Distiller is the headline. Old shape (no distiller): Auditor / Final Synth is.
    const isHeadline = hasDistiller
      ? r.id === 'distiller'
      : (r.id === 'auditor' || r.id === 'final_synth');
    const row = document.createElement('div'); row.className = 'seat-row';
    const seat = makeSeat(agent, { final: isHeadline, open: isHeadline });
    seat.classList.add('visible');
    row.appendChild(seat);
    turnEl.appendChild(row);
    const body = seat.querySelector('.seat-body');
    if (r.skipped) {
      body.innerHTML = `<div class="skipped-notice"><strong>Skipped.</strong> The next stage used the previous stage's output as its input.</div>`;
      setSeatStateOn(seat, 'skipped');
    } else {
      body.innerHTML = renderMarkdown(r.text || '');
      setSeatStateOn(seat, 'done');
    }
  }
  thread().appendChild(turnEl);
}

// State-setter that works on a known seat element (used by prior-turn rendering
// where _currentTurnEl is not set).
function setSeatStateOn(seat, state, label) {
  applySeatState(seat, state, label);
}

function agentById(id) {
  return [DRAFTER, ...CRITICS, REVISER, AUDITOR, DISTILLER, QUICK].find(a => a.id === id);
}

// ============================================================
// HANDLE SEND
// ============================================================
// _activeRun holds the in-flight handleSend promise so other code (mode switch,
// edit-and-resend) can await its full unwind before starting a new run.
let _activeRun = null;

async function waitForCurrentRun() {
  if (_activeRun) { try { await _activeRun; } catch (_) {} }
}

async function handleSend() {
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text || S.busy) return;

  // Track this run so other code (mode switch / edit-resend) can await it.
  let resolveDone;
  _activeRun = new Promise(r => { resolveDone = r; });

  // Ensure we have a chat to write into.
  if (!S.currentChatId) {
    await newChat(/*silent=*/true);
  }

  S.busy = true;
  S.running.add(S.currentChatId);
  document.getElementById('send-btn').disabled = true;
  document.getElementById('abort-btn').classList.add('show');
  input.value = '';
  autoResizeInput.call(input);  // collapse the textarea back to its base size
  refreshChatList();             // surface the running indicator immediately

  const ac = new AbortController();
  S.abortController = ac;

  // Save user turn.
  const userTurn = { role: 'user', content: text, mode: S.mode };
  await apiAppendTurn(S.currentChatId, userTurn);
  S.conversation.push(userTurn);

  startTurn(text);

  let finalText = '';
  let savedTurn = null;
  try {
    if (S.mode === 'full') {
      finalText = await runPipeline(text, ac.signal);
      savedTurn = {
        role: 'assistant',
        mode: 'full',
        seats: [
          { ...DRAFTER, text: _readSeatBody(DRAFTER), skipped: _wasSkipped(DRAFTER) },
          ...CRITICS.map(c => ({ ...c, text: _readSeatBody(c), skipped: _wasSkipped(c) })),
          { ...REVISER, text: _readSeatBody(REVISER), skipped: _wasSkipped(REVISER) },
          { ...AUDITOR, text: _readSeatBody(AUDITOR), skipped: _wasSkipped(AUDITOR) },
          { ...DISTILLER, text: _readSeatBody(DISTILLER), skipped: _wasSkipped(DISTILLER) },
        ],
        final: finalText,    // polished answer — used as context in follow-up turns
        distilled: _readSeatBody(DISTILLER),  // the 2-3 sentence summary, kept as metadata
        timestamp: new Date().toISOString(),
      };
    } else {
      finalText = await runQuick(text, ac.signal);
      savedTurn = {
        role: 'assistant',
        mode: 'quick',
        content: finalText,
        final: finalText,
        timestamp: new Date().toISOString(),
      };
    }
    await apiAppendTurn(S.currentChatId, savedTurn);
    S.conversation.push(savedTurn);
  } catch (err) {
    if (err.name === 'AbortError') {
      appendError('Stopped.');
    } else {
      appendError(err.message || String(err));
    }
  } finally {
    S.busy = false;
    S.running.delete(S.currentChatId);
    document.getElementById('send-btn').disabled = false;
    document.getElementById('abort-btn').classList.remove('show');
    S.abortController = null;
    await refreshChatList();  // updated_at and running status changed
    if (resolveDone) resolveDone();
    _activeRun = null;
  }
}

function handleAbort() {
  if (S.abortController) S.abortController.abort();
  // Stop any animated ellipses immediately — without this, seats stay in
  // their last 'working' state until the abort propagates up to handleSend's
  // catch block, which can take a beat. Set them to 'stopped' right now.
  if (_currentTurnEl) {
    _currentTurnEl.querySelectorAll('.seat-state.working').forEach(stateEl => {
      const seat = stateEl.closest('.seat');
      if (seat) applySeatState(seat, 'error', 'stopped');
    });
  }
}

function _readSeatBody(agent) {
  const seat = seatEl(agent);
  if (!seat) return '';
  const body = seat.querySelector('.seat-body');
  return body ? body.innerText : '';
}

function _wasSkipped(agent) {
  const seat = seatEl(agent);
  return !!(seat && seat.querySelector('.seat-state.skipped'));
}

function appendError(msg) {
  if (!_currentTurnEl) return;
  const e = document.createElement('div');
  e.className = 'error-banner';
  e.textContent = msg;
  _currentTurnEl.appendChild(e);
}

// ============================================================
// CHAT MANAGEMENT
// ============================================================
async function newChat(silent) {
  const r = await fetch('/chats/new', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ title: 'New chat' }),
  });
  const meta = await r.json();
  S.currentChatId = meta.id;
  S.conversation = [];
  clearThread();
  await refreshChatList();
  if (!silent) document.getElementById('input').focus();
}

async function loadChat(id) {
  const r = await fetch('/chats/' + encodeURIComponent(id));
  if (!r.ok) return;
  const data = await r.json();
  S.currentChatId = id;
  S.conversation = data.turns || [];
  S.unread.delete(id);   // opening clears the unread indicator
  clearThread();
  for (let i = 0; i < S.conversation.length; i++) {
    renderPriorTurn(S.conversation[i], i);
  }
  await refreshChatList();
  closeAllPanels();
  // Land at the latest content rather than the top.
  setTimeout(() => scrollToBottom(false), 50);
}

async function deleteChat(id, ev) {
  ev.stopPropagation();
  if (!confirm('Delete this chat?')) return;
  await fetch('/chats/' + encodeURIComponent(id), { method:'DELETE' });
  if (S.currentChatId === id) {
    S.currentChatId = null;
    S.conversation = [];
    clearThread();
  }
  S.unread.delete(id);
  S.running.delete(id);
  await refreshChatList();
  showToast('Chat deleted');
}

async function refreshChatList() {
  const r = await fetch('/chats');
  const d = await r.json();
  S.chats = d.chats || [];
  const list = document.getElementById('chat-list');
  list.innerHTML = '';
  if (!S.chats.length) {
    list.innerHTML = `<div class="empty-state">No chats yet. Ask a question to start one.</div>`;
    return;
  }
  for (const c of S.chats) {
    let cls = 'chat-item';
    if (c.id === S.currentChatId)    cls += ' active';
    if (S.running.has(c.id))         cls += ' running';
    if (S.unread.has(c.id))          cls += ' unread';
    const row = document.createElement('div');
    row.className = cls;
    const turns = c.turn_count || 0;
    const turnsTxt = turns ? `${turns} turn${turns === 1 ? '' : 's'}` : 'empty';
    const whenTxt  = relativeTime(c.updated_at || c.created_at);
    const sep = turnsTxt && whenTxt ? ' · ' : '';
    const runningDots = `<span class="chat-item-typing"><span></span><span></span><span></span></span>`;
    row.innerHTML = `
      <div class="chat-item-main">
        <div class="chat-item-title">${runningDots}${escapeHtml(c.title || c.id)}</div>
        <div class="chat-item-meta">${turnsTxt}${sep}${escapeHtml(whenTxt)}</div>
      </div>
      <div class="chat-item-actions">
        <button class="chat-item-del" title="Delete chat">✕</button>
      </div>
    `;
    row.querySelector('.chat-item-main').onclick = () => loadChat(c.id);
    row.querySelector('.chat-item-del').onclick  = (ev) => deleteChat(c.id, ev);
    list.appendChild(row);
  }
}

// "Just now", "5m ago", "2h ago", "Yesterday", "May 14"
function relativeTime(iso) {
  if (!iso) return '';
  const then = new Date(iso);
  if (isNaN(then.getTime())) return '';
  const diffMs = Date.now() - then.getTime();
  const sec = Math.floor(diffMs / 1000);
  if (sec < 60)   return 'just now';
  const min = Math.floor(sec / 60);
  if (min < 60)   return `${min}m ago`;
  const hr  = Math.floor(min / 60);
  if (hr < 24)    return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  if (day === 1)  return 'yesterday';
  if (day < 7)    return `${day}d ago`;
  // Older: short date
  return then.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

async function apiAppendTurn(chatId, turn) {
  await fetch('/chats/' + encodeURIComponent(chatId) + '/turns', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ turn }),
  });
}

// ============================================================
// PANELS
// ============================================================
function togglePanel(which) {
  if (S.openPanel === which) { closeAllPanels(); return; }
  closeAllPanels();
  const id = which === 'chats' ? 'panel-chats' : 'panel-settings';
  document.getElementById(id).classList.add('open');
  document.getElementById('backdrop').classList.add('active');
  S.openPanel = which;
}

function closeAllPanels() {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('open'));
  document.getElementById('backdrop').classList.remove('active');
  S.openPanel = null;
}

// ============================================================
// SETTINGS
// ============================================================
async function setMode(m) {
  // Tolerate legacy 'pipeline' value from earlier saves.
  if (m === 'pipeline') m = 'full';
  // No-op if mode hasn't actually changed.
  if (m === S.mode) return;
  // If a run is in flight, ask the user, then abort + restart the same
  // question in the new mode. The user almost always means "ask this again
  // in the other mode" — not "discard and do nothing."
  if (S.busy) {
    const target = m === 'quick' ? 'Quick' : 'Full';
    if (!confirm(`A response is in progress. Switch to ${target} mode and re-ask?`)) return;
    // Capture the question being processed before the abort wipes the run.
    // The latest user turn is the one whose response is being generated;
    // its assistant turn hasn't been saved yet, so it sits at the end of
    // S.conversation.
    let lastUserIdx = -1;
    for (let i = S.conversation.length - 1; i >= 0; i--) {
      if (S.conversation[i].role === 'user') { lastUserIdx = i; break; }
    }
    const lastUserText = lastUserIdx >= 0 ? S.conversation[lastUserIdx].content : null;
    handleAbort();
    await waitForCurrentRun();
    _applyMode(m);
    if (lastUserText && lastUserIdx >= 0 && S.currentChatId) {
      await _restartFromTurn(lastUserIdx, lastUserText);
    }
    return;
  }
  _applyMode(m);
}

function _applyMode(m) {
  S.mode = m;
  document.getElementById('mode-quick').classList.toggle('active', m === 'quick');
  document.getElementById('mode-full').classList.toggle('active', m === 'full');
  localStorage.setItem(LS.mode, m);
}

// Truncate the chat at the given user-turn index, re-render the (now shorter)
// thread, drop the text into the input, and send. Used by both the mode-switch
// restart and the saveEdit flow.
async function _restartFromTurn(userTurnIndex, text) {
  try {
    const r = await fetch('/chats/' + encodeURIComponent(S.currentChatId) + '/truncate', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ keep_through_seq: userTurnIndex }),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok || data.error) {
      showToast('Could not restart: ' + (data.error || `HTTP ${r.status}`));
      return;
    }
  } catch (e) {
    showToast('Could not restart: ' + (e.message || e));
    return;
  }
  S.conversation = S.conversation.slice(0, userTurnIndex);
  clearThread();
  for (let i = 0; i < S.conversation.length; i++) renderPriorTurn(S.conversation[i], i);
  const input = document.getElementById('input');
  input.value = text;
  autoResizeInput.call(input);
  await handleSend();
}

function setProvider(p) {
  S.provider = p;
  document.getElementById('prov-cli').style.borderColor = p === 'cli' ? 'var(--gold)' : 'var(--border)';
  document.getElementById('prov-api').style.borderColor = p === 'api' ? 'var(--gold)' : 'var(--border)';
  document.getElementById('api-key-block').style.display = p === 'api' ? 'block' : 'none';
  localStorage.setItem(LS.provider, p);
}

function onApiKeyInput(ev) {
  S.apiKey = ev.target.value.trim();
  localStorage.setItem(LS.apiKey, S.apiKey);
}

function clearApiKey() {
  S.apiKey = '';
  document.getElementById('api-key-input').value = '';
  localStorage.removeItem(LS.apiKey);
}

function onHouseStyleInput() {
  S.houseStyle = document.getElementById('house-style-input').value;
  localStorage.setItem(LS.houseStyle, S.houseStyle);
}

function resetHouseStyle() {
  S.houseStyle = DEFAULT_HOUSE_STYLE;
  document.getElementById('house-style-input').value = DEFAULT_HOUSE_STYLE;
  localStorage.setItem(LS.houseStyle, DEFAULT_HOUSE_STYLE);
}

function clearHouseStyle() {
  S.houseStyle = '';
  document.getElementById('house-style-input').value = '';
  localStorage.setItem(LS.houseStyle, '');
}

function onReasoningInput() {
  S.reasoningStandards = document.getElementById('reasoning-input').value;
  localStorage.setItem(LS.reasoning, S.reasoningStandards);
}

function resetReasoning() {
  S.reasoningStandards = DEFAULT_REASONING_STANDARDS;
  document.getElementById('reasoning-input').value = DEFAULT_REASONING_STANDARDS;
  localStorage.setItem(LS.reasoning, DEFAULT_REASONING_STANDARDS);
}

function clearReasoning() {
  S.reasoningStandards = '';
  document.getElementById('reasoning-input').value = '';
  localStorage.setItem(LS.reasoning, '');
}

function onModelInput(key, ev) {
  S.models[key] = ev.target.value.trim() || DEFAULT_MODELS[key];
  localStorage.setItem(LS.models, JSON.stringify(S.models));
}

// ============================================================
// BOOTSTRAP
// ============================================================
function loadFromStorage() {
  S.provider = localStorage.getItem(LS.provider) || 'cli';
  S.apiKey   = localStorage.getItem(LS.apiKey) || '';
  S.houseStyle = localStorage.getItem(LS.houseStyle);
  if (S.houseStyle === null) S.houseStyle = DEFAULT_HOUSE_STYLE;
  S.reasoningStandards = localStorage.getItem(LS.reasoning);
  if (S.reasoningStandards === null) S.reasoningStandards = DEFAULT_REASONING_STANDARDS;
  try {
    const m = JSON.parse(localStorage.getItem(LS.models) || 'null');
    if (m) S.models = { ...DEFAULT_MODELS, ...m };
  } catch (_) {}
  S.mode = localStorage.getItem(LS.mode) || 'full';
  if (S.mode === 'pipeline') S.mode = 'full';  // legacy
}

function bindUI() {
  const input = document.getElementById('input');

  input.addEventListener('keydown', (e) => {
    // Cmd/Ctrl+Enter to send. Plain Enter inserts a newline.
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); handleSend(); }
  });

  // Auto-resize the textarea as the user types. The input bar is fixed to
  // the bottom of the viewport, so growing the textarea pushes the top of
  // the bar upward, which is what the user expects.
  input.addEventListener('input', autoResizeInput);
  autoResizeInput.call(input);  // initial size

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAllPanels();
    // Cmd/Ctrl+K: new chat
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault(); newChat();
    }
  });

  // Show / hide the scroll-to-bottom button + update sticky-header state.
  window.addEventListener('scroll', onScroll, { passive: true });

  // Keep --toolbar-h in sync with the actual toolbar height; affects where
  // sticky seat headers pin to.
  updateToolbarHeightVar();
  window.addEventListener('resize', () => {
    updateToolbarHeightVar();
    updateInputBarOffset();
  });

  document.getElementById('api-key-input').value = S.apiKey;
  document.getElementById('house-style-input').value = S.houseStyle;
  document.getElementById('reasoning-input').value = S.reasoningStandards;
  document.getElementById('model-heavy').value = S.models.heavy === DEFAULT_MODELS.heavy ? '' : S.models.heavy;
  document.getElementById('model-critic').value = S.models.critic === DEFAULT_MODELS.critic ? '' : S.models.critic;
  document.getElementById('model-fast').value = S.models.fast === DEFAULT_MODELS.fast ? '' : S.models.fast;
  document.getElementById('model-quick').value = S.models.quick === DEFAULT_MODELS.quick ? '' : S.models.quick;
  setMode(S.mode);
  setProvider(S.provider);
  updateInputBarOffset();  // adjust bottom-of-page padding for current input height
}

// Auto-resize the textarea to fit its content, capped at MAX_INPUT_HEIGHT.
const MAX_INPUT_HEIGHT = 280;
function autoResizeInput() {
  const el = this instanceof HTMLElement ? this : document.getElementById('input');
  el.style.height = 'auto';
  const newH = Math.min(el.scrollHeight, MAX_INPUT_HEIGHT);
  el.style.height = newH + 'px';
  updateInputBarOffset();
}

// Reserve enough bottom padding on <main> so the input bar never covers content.
function updateInputBarOffset() {
  const bar = document.getElementById('input-bar');
  if (!bar) return;
  const h = bar.offsetHeight || 80;
  document.getElementById('main').style.paddingBottom = (h + 60) + 'px';
}

// Smooth-scroll to the bottom of the page so the latest content is visible.
function scrollToBottom(smooth) {
  window.scrollTo({ top: document.body.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
}

function updateScrollDownBtn() {
  const btn = document.getElementById('scroll-down-btn');
  if (!btn) return;
  const nearBottom = (window.innerHeight + window.scrollY) >= (document.body.scrollHeight - 200);
  btn.classList.toggle('show', !nearBottom && document.body.scrollHeight > window.innerHeight + 300);
}

// Push the actual toolbar height into a CSS variable so the sticky seat
// headers pin at exactly the right spot regardless of font/zoom.
function updateToolbarHeightVar() {
  const tb = document.getElementById('toolbar');
  if (!tb) return;
  document.documentElement.style.setProperty('--toolbar-h', tb.offsetHeight + 'px');
}

// Add `.stuck` to a seat-header whenever it is actually pinned at the top
// (its bounding rect's top equals the toolbar height). The class is what
// gives the floating drop shadow that signals "this header is now sticky."
let _stickyRafQueued = false;
function checkStickyHeaders() {
  if (_stickyRafQueued) return;
  _stickyRafQueued = true;
  requestAnimationFrame(() => {
    _stickyRafQueued = false;
    const toolbarH = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--toolbar-h')) || 56;
    document.querySelectorAll('.seat-header').forEach(h => {
      const rect = h.getBoundingClientRect();
      // Stuck = top is sitting right at the toolbar's bottom (within 1px tolerance).
      const isStuck = Math.abs(rect.top - toolbarH) <= 1;
      h.classList.toggle('stuck', isStuck);
    });
  });
}

// Single scroll listener does both the scroll-down button and sticky detection.
function onScroll() {
  updateScrollDownBtn();
  checkStickyHeaders();
}

// Quick transient feedback ("Chat deleted", "Settings saved", etc.)
let _toastTimer = null;
function showToast(msg, ms = 1800) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => t.classList.remove('show'), ms);
}

// ============================================================
// SERVER-DOWN DETECTION
//
// Poll /health on a short interval. When the request fails (network error,
// timeout, or non-2xx), show a full-page overlay that blocks the UI until
// the server answers again. Polls more frequently while down so recovery
// feels snappy; spaces out when healthy to keep noise down.
// ============================================================
let _serverDown = false;
let _healthTimer = null;
const HEALTH_INTERVAL_UP   = 5000;   // when server is healthy
const HEALTH_INTERVAL_DOWN = 1000;   // poll faster while we're trying to recover
const HEALTH_TIMEOUT_MS    = 2000;

async function pingHealth() {
  let ok = false;
  try {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), HEALTH_TIMEOUT_MS);
    const r = await fetch('/health', { signal: ac.signal, cache: 'no-store' });
    clearTimeout(timer);
    ok = r.ok;
  } catch (_) {
    ok = false;
  }
  if (ok) setServerUp();
  else    setServerDown();
  scheduleNextHealthCheck();
}

function scheduleNextHealthCheck() {
  clearTimeout(_healthTimer);
  _healthTimer = setTimeout(pingHealth, _serverDown ? HEALTH_INTERVAL_DOWN : HEALTH_INTERVAL_UP);
}

function setServerDown() {
  if (_serverDown) return;
  _serverDown = true;
  const ov = document.getElementById('server-down-overlay');
  if (ov) ov.classList.add('show');
}

function setServerUp() {
  if (!_serverDown) return;
  _serverDown = false;
  const ov = document.getElementById('server-down-overlay');
  if (ov) ov.classList.remove('show');
  showToast('Server reconnected');
}

// Copy the content of a thread item — works for both user bubbles and seats.
// For seats, copies just the body (the response itself), not the header.
async function copyMessageText(button) {
  const container = button.closest('.turn-user, .seat');
  if (!container) return;
  let text = '';
  if (container.classList.contains('turn-user')) {
    const content = container.querySelector('.user-msg-content');
    text = content ? content.textContent : container.textContent;
  } else {
    const body = container.querySelector('.seat-body');
    text = body ? body.innerText : '';
  }
  if (!text || !text.trim()) { showToast('Nothing to copy'); return; }
  try {
    await navigator.clipboard.writeText(text);
    showToast('Copied');
  } catch (e) {
    // Fallback for browsers/contexts where clipboard API is unavailable.
    const ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); showToast('Copied'); }
    catch (_) { showToast('Copy failed'); }
    finally { document.body.removeChild(ta); }
  }
}

(async function init() {
  loadFromStorage();
  bindUI();
  await refreshChatList();
  // Refresh chat-list relative timestamps every minute so "5m ago" doesn't go stale.
  setInterval(refreshChatList, 60_000);
  // Kick off health polling. Runs forever; pingHealth schedules its own next tick.
  pingHealth();
})();
</script>
</body>
</html>"""


# ============================================================
# HTTP SERVER
# ============================================================

class Handler(http.server.BaseHTTPRequestHandler):

    # ---------------- routing ----------------

    def do_GET(self):
        path = urlparse(self.path).path
        # /health is cheap and the frontend polls it to detect when the
        # Python process is gone. Keep this branch first so it short-circuits.
        if path == '/health':
            return self._json({'ok': True})
        if path in ('/', '/index.html'):
            return self._serve_html()
        if path == '/chats':
            return self._chats_list()
        if path.startswith('/chats/'):
            rest = path[len('/chats/'):]
            if rest and '/' not in rest:
                return self._chats_get(unquote(rest))
        self.send_response(404); self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/ask':
            return self._handle_ask()
        if path == '/chats/new':
            return self._chats_create()
        if path.startswith('/chats/') and path.endswith('/turns'):
            chat_id = unquote(path[len('/chats/'):-len('/turns')])
            return self._chats_append(chat_id)
        if path.startswith('/chats/') and path.endswith('/truncate'):
            chat_id = unquote(path[len('/chats/'):-len('/truncate')])
            return self._chats_truncate(chat_id)
        self.send_response(404); self.end_headers()

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path.startswith('/chats/'):
            chat_id = unquote(path[len('/chats/'):])
            return self._chats_delete(chat_id)
        self.send_response(404); self.end_headers()

    # ---------------- HTML ----------------

    def _serve_html(self):
        body = HTML.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    # ---------------- chat store ----------------

    def _chat_dir(self, chat_id):
        if not chat_id or '/' in chat_id or '\\' in chat_id or chat_id.startswith('.'):
            return None
        return os.path.join(CHATS_DIR, chat_id)

    def _read_meta(self, chat_dir):
        p = os.path.join(chat_dir, 'meta.json')
        if not os.path.exists(p): return {}
        try:
            with open(p, encoding='utf-8') as f: return json.load(f)
        except Exception:
            return {}

    def _write_meta(self, chat_dir, meta):
        with open(os.path.join(chat_dir, 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    def _chats_list(self):
        items = []
        try:
            for name in os.listdir(CHATS_DIR):
                p = os.path.join(CHATS_DIR, name)
                if not os.path.isdir(p): continue
                meta = self._read_meta(p)
                if not meta:
                    meta = {'id': name, 'title': name, 'created_at': '',
                            'updated_at': '', 'turn_count': 0}
                else:
                    meta.setdefault('id', name)
                items.append(meta)
            items.sort(key=lambda m: (m.get('updated_at') or m.get('created_at') or m.get('id') or ''), reverse=True)
        except Exception as e:
            self._json({'chats': [], 'error': str(e)}); return
        self._json({'chats': items})

    def _chats_create(self):
        payload = self._read_json_body() or {}
        title = (payload.get('title') or 'New chat').strip() or 'New chat'
        stamp = _now_stamp()
        slug = _slugify(title)
        chat_id = f"{stamp}-{slug}" if slug else stamp
        suffix = 1
        base_id = chat_id
        while os.path.exists(os.path.join(CHATS_DIR, chat_id)):
            suffix += 1
            chat_id = f"{base_id}-{suffix}"
        chat_dir = os.path.join(CHATS_DIR, chat_id)
        try:
            os.makedirs(chat_dir, exist_ok=False)
        except Exception as e:
            self._json({'error': str(e)}, status=500); return
        meta = {
            'id': chat_id,
            'title': title,
            'created_at': _now_iso(),
            'updated_at': _now_iso(),
            'turn_count': 0,
        }
        self._write_meta(chat_dir, meta)
        self._json(meta)

    def _chats_get(self, chat_id):
        chat_dir = self._chat_dir(chat_id)
        if not chat_dir or not os.path.isdir(chat_dir):
            self.send_response(404); self.end_headers(); return
        meta = self._read_meta(chat_dir)
        turns = []
        try:
            for fname in sorted(os.listdir(chat_dir)):
                if fname == 'meta.json' or not fname.endswith('.json'): continue
                try:
                    with open(os.path.join(chat_dir, fname), encoding='utf-8') as f:
                        turns.append(json.load(f))
                except Exception:
                    pass
        except Exception as e:
            self._json({'error': str(e)}, status=500); return
        self._json({'meta': meta, 'turns': turns})

    def _chats_append(self, chat_id):
        chat_dir = self._chat_dir(chat_id)
        if not chat_dir or not os.path.isdir(chat_dir):
            self.send_response(404); self.end_headers(); return
        payload = self._read_json_body() or {}
        turn = payload.get('turn')
        if not isinstance(turn, dict) or 'role' not in turn:
            self.send_response(400); self.end_headers(); return
        existing = [f for f in os.listdir(chat_dir)
                    if f.endswith('.json') and f != 'meta.json']
        seq = len(existing) + 1
        role = re.sub(r'[^a-z]', '', (turn.get('role') or 'unknown').lower()) or 'unknown'
        fname = f"{seq:04d}-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}-{role}.json"
        turn_record = dict(turn)
        turn_record.setdefault('seq', seq)
        turn_record.setdefault('timestamp', _now_iso())
        with open(os.path.join(chat_dir, fname), 'w', encoding='utf-8') as f:
            json.dump(turn_record, f, indent=2, ensure_ascii=False)
        meta = self._read_meta(chat_dir)
        meta.setdefault('id', chat_id)
        meta['turn_count'] = seq
        meta['updated_at'] = _now_iso()
        if seq == 1 and role == 'user':
            content = (turn.get('content') or '').strip()
            if content:
                meta['title'] = content[:80]
        self._write_meta(chat_dir, meta)
        self._json(meta)

    def _chats_truncate(self, chat_id):
        """Delete every turn file whose seq is greater than keep_through_seq.
        Used by the message-edit feature: editing turn N discards turn N
        and every turn after it, then the client re-sends with the new text.
        """
        chat_dir = self._chat_dir(chat_id)
        if not chat_dir or not os.path.isdir(chat_dir):
            self.send_response(404); self.end_headers(); return
        payload = self._read_json_body() or {}
        keep_through = payload.get('keep_through_seq')
        if not isinstance(keep_through, int) or keep_through < 0:
            self.send_response(400); self.end_headers(); return
        try:
            deleted = 0
            failures = []
            for fname in os.listdir(chat_dir):
                if not fname.endswith('.json') or fname == 'meta.json':
                    continue
                m = re.match(r'^(\d+)-', fname)
                if not m: continue
                seq = int(m.group(1))
                if seq > keep_through:
                    try:
                        os.remove(os.path.join(chat_dir, fname))
                        deleted += 1
                    except Exception as e:
                        failures.append(f'{fname}: {type(e).__name__}: {e}')
            # If we couldn't actually delete the turn files, surface that as
            # a hard error so the client can refuse to proceed.
            if failures:
                self._json({
                    'truncated': deleted,
                    'kept_through': keep_through,
                    'error': 'Could not delete some turn files',
                    'details': failures,
                }, status=500)
                return
            meta = self._read_meta(chat_dir)
            meta.setdefault('id', chat_id)
            meta['turn_count'] = keep_through
            meta['updated_at'] = _now_iso()
            self._write_meta(chat_dir, meta)
        except Exception as e:
            self._json({'error': str(e)}, status=500); return
        self._json({'truncated': deleted, 'kept_through': keep_through})

    def _chats_delete(self, chat_id):
        chat_dir = self._chat_dir(chat_id)
        if not chat_dir or not os.path.isdir(chat_dir):
            self.send_response(404); self.end_headers(); return
        try:
            shutil.rmtree(chat_dir)
        except Exception as e:
            self._json({'error': str(e)}, status=500); return
        self._json({'deleted': chat_id})

    # ---------------- helpers ----------------

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        length = int(self.headers.get('Content-Length', 0) or 0)
        if not length: return {}
        try:
            return json.loads(self.rfile.read(length).decode('utf-8'))
        except Exception:
            return {}

    # ---------------- /ask (CLI provider) ----------------

    def _handle_ask(self):
        length = int(self.headers.get('Content-Length', 0))
        payload = json.loads(self.rfile.read(length))
        system = payload.get('system', '')
        prompt = payload.get('prompt', '')
        model  = payload.get('model') or None
        full   = f"{system}\n\n---\n\n{prompt}" if system else prompt

        args = ['claude']
        if model:
            args.extend(['--model', str(model)])
        args.append('-p')

        try:
            result = subprocess.run(
                args,
                input=full,
                capture_output=True, text=True,
                encoding='utf-8', errors='replace',
                timeout=CLI_TIMEOUT_SEC,
            )
            if result.returncode != 0:
                err = (result.stderr or '').strip() or f'claude exited with code {result.returncode}'
                data = {'text': '', 'error': err}
            else:
                data = {'text': (result.stdout or '').strip(), 'error': ''}
        except FileNotFoundError as e:
            data = {'text': '', 'error':
                f'Could not spawn `claude` ({e}). The Python server cannot find it on PATH. '
                f'Check that `claude --version` works in the terminal where you launched python council.py.'}
        except subprocess.TimeoutExpired:
            data = {'text': '', 'error':
                f'Claude CLI timed out after {CLI_TIMEOUT_SEC}s. Input was {len(full)} chars.'}
        except Exception as e:
            data = {'text': '', 'error': f'{type(e).__name__}: {e}'}

        body = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, *a): pass


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    if not shutil.which('claude'):
        print("⚠  `claude` not found on PATH.")
        print("   Install Claude Code: https://claude.ai/code")
        print("   Or add an API key via the Settings panel (⚙).\n")

    url = f'http://localhost:{PORT}'
    # ThreadingHTTPServer so the three parallel critic calls actually run
    # in parallel instead of being serialized by the server.
    srv = http.server.ThreadingHTTPServer(('localhost', PORT), Handler)
    print(f"⚖  The Council is in session  →  {url}")
    print(f"   Pipeline: Drafter → 3 Critics → Reviser → Style Auditor")
    print(f"   Stop with Ctrl+C\n")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
