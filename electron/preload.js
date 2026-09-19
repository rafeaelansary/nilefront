// Runs in the renderer with Node access, before the game's own script — but exposes nothing to
// it. The game is self-contained browser code (three.js, WebGL, Web Audio, DOM) with no need for
// filesystem, native, or IPC access, so there is nothing to bridge across contextIsolation yet.
//
// If a future desktop-only feature needs main-process access (native save-file dialogs, a
// persistent high-score file instead of localStorage, Steam/controller APIs, etc.), add it here
// with contextBridge.exposeInMainWorld(...) — never by turning contextIsolation or
// nodeIntegration back on in main.js.
'use strict';
