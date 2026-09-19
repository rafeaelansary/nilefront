// NILEFRONT desktop — a thin Electron shell around the browser game.
//
// The game itself (../index.html, and everything it inlines) is untouched: this process only
// opens a window, points it at the build script's output (app/index.html — see
// scripts/build-app.js and its comment for why that's a separate file from the source), and
// keeps the window from doing anything a desktop game window shouldn't — opening external links
// in itself, navigating away, running with Node access it never needs.
'use strict';
const { app, BrowserWindow, Menu, shell } = require('electron');
const path = require('path');

const APP_HTML = path.join(__dirname, 'app', 'index.html');
// Matches the game's own sky colour (scene.background, index.html) so the window isn't a flash
// of white while the page's first frame renders.
const SKY_COLOR = '#8fd6f2';

// Only one window makes sense for a single-player game; a second launch should focus the
// existing one instead of opening a confusing second copy.
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    const win = BrowserWindow.getAllWindows()[0];
    if (win) {
      if (win.isMinimized()) win.restore();
      win.focus();
    }
  });

  app.whenReady().then(() => {
    buildMenu();
    createWindow();

    // macOS convention: clicking the dock icon with no windows open should reopen one.
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });

  // Standard desktop-app convention: quit when the last window closes, except on macOS, where
  // apps normally stay running (in the dock/menu bar) until Cmd+Q.
  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
  });
}

function createWindow() {
  const win = new BrowserWindow({
    title: 'NILEFRONT',
    width: 1440,
    height: 900,
    minWidth: 960,
    minHeight: 600,
    backgroundColor: SKY_COLOR,
    autoHideMenuBar: true, // the game draws its own HUD; a visible menu bar is just clutter
    webPreferences: {
      // The game is pure browser tech (three.js, WebGL, Web Audio, DOM) and never needs Node —
      // so it never gets it. contextIsolation + sandbox + nodeIntegration:false is the standard
      // hardened default for content that doesn't need main-process access.
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  win.loadFile(APP_HTML);

  // Keep the game inside its own window. window.open() and target=_blank have no reason to fire
  // here, but if something ever tries, send it to the OS browser rather than opening a second
  // Electron window pointed at an arbitrary URL.
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
  win.webContents.on('will-navigate', (event, url) => {
    if (url !== win.webContents.getURL()) {
      event.preventDefault();
      shell.openExternal(url);
    }
  });

  if (!app.isPackaged) {
    // Dev builds only — a shipped build shouldn't invite players into devtools by default.
    win.webContents.on('before-input-event', (event, input) => {
      if (input.key === 'F12' || (input.control && input.shift && input.key.toLowerCase() === 'i')) {
        win.webContents.toggleDevTools();
      }
    });
  }
}

function buildMenu() {
  // Deliberately sparse: just enough that Cmd+Q/Ctrl+Q, fullscreen, and reload work the way a
  // player expects from any desktop app, without a File/Edit/View bar sitting over a game HUD.
  const isMac = process.platform === 'darwin';
  const template = [
    ...(isMac ? [{ role: 'appMenu' }] : []),
    {
      label: 'View',
      submenu: [
        { role: 'togglefullscreen' }, // binds F11 / Ctrl+Cmd+F per-platform automatically
        { role: 'reload' },
      ],
    },
    {
      role: 'windowMenu',
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}
