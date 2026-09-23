#!/usr/bin/env node
// Assembles electron/app/ — the thing main.js actually loads — from the single-file browser game
// at ../../index.html. That file stays the one source of truth (it's what gh-pages deploys too),
// so this never forks the game logic: it only swaps the one line that can't survive offline.
//
// The game loads three.js from a CDN by URL, which is fine in a browser tab but wrong for a
// desktop app — a "game" that needs internet just to reach its own render engine on first launch
// isn't really offline software. So this replaces that <script> tag with a local, vendored copy
// (electron/vendor/three.min.js, fetched once and checked byte-for-byte against the CDN tag's own
// integrity hash — see README) and copies it alongside the generated index.html. Everything else
// in the file is copied verbatim.
'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..', '..');
const ELECTRON_DIR = path.join(__dirname, '..');
const SRC_HTML = path.join(ROOT, 'index.html');
const OUT_DIR = path.join(ELECTRON_DIR, 'app');
const OUT_HTML = path.join(OUT_DIR, 'index.html');
const VENDOR_SRC = path.join(ELECTRON_DIR, 'vendor', 'three.min.js');
const VENDOR_OUT_DIR = path.join(OUT_DIR, 'vendor');

// The exact tag as it appears in index.html today. Matched literally rather than with a loose
// regex on purpose: if the CDN version, hash, or attributes ever change upstream, this script
// should fail loudly and tell you to update it, not silently ship a build that still points at
// a URL the offline app can never reach.
const CDN_TAG = `<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
        integrity="sha512-dLxUelApnYxpLt6K2iomGngnHO83iUvZytA3YjDUCjT0HDOHKXnVYdf3hU4JjM8uEhxf9nD1/ey98U3t2vZ0qQ=="
        crossorigin="anonymous" referrerpolicy="no-referrer"></script>`;
const LOCAL_TAG = `<script src="vendor/three.min.js"></script>`;

// The build number the title screen shows. It is written into index.html by hand, and package.json's
// version is what actually names the DMG — two strings that mean the same thing and can drift, which
// is how you get a build whose installer says 1.2.0 and whose start screen says 1.1.0. Same rule as
// the CDN tag above: catch it here rather than ship it.
const VER_RE = /<div id="ver">v([0-9]+\.[0-9]+\.[0-9]+)<\/div>/;

function main() {
  if (!fs.existsSync(SRC_HTML)) {
    fail(`Can't find the game at ${SRC_HTML}`);
  }
  if (!fs.existsSync(VENDOR_SRC)) {
    fail(
      `Missing ${VENDOR_SRC}.\n` +
      `Vendor three.js r128 once with:\n` +
      `  curl -fsSL https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js -o electron/vendor/three.min.js\n` +
      `(and check its sha512 against the integrity="" attribute on index.html's own <script> tag).`
    );
  }

  const html = fs.readFileSync(SRC_HTML, 'utf8');
  if (!html.includes(CDN_TAG)) {
    fail(
      `index.html's three.js <script> tag has changed and no longer matches what this build ` +
      `script expects. Update CDN_TAG in electron/scripts/build-app.js (and re-vendor ` +
      `electron/vendor/three.min.js if the version or hash moved) before building.`
    );
  }

  const pkgVer = require(path.join(ELECTRON_DIR, 'package.json')).version;
  const shown = html.match(VER_RE);
  if (!shown) {
    fail(
      `index.html no longer carries the <div id="ver">vX.Y.Z</div> build label on its title screen. ` +
      `Restore it, or drop VER_RE from electron/scripts/build-app.js if the label is gone for good.`
    );
  }
  if (shown[1] !== pkgVer) {
    fail(
      `Version mismatch: the title screen says v${shown[1]}, package.json says ${pkgVer}.\n` +
      `The DMG is named from package.json, so shipping this would put two different numbers on one ` +
      `build. Update whichever one is stale before building.`
    );
  }

  const patched = html.replace(CDN_TAG, LOCAL_TAG);

  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.mkdirSync(VENDOR_OUT_DIR, { recursive: true });
  fs.writeFileSync(OUT_HTML, patched);
  fs.copyFileSync(VENDOR_SRC, path.join(VENDOR_OUT_DIR, 'three.min.js'));

  console.log(`Built ${path.relative(ROOT, OUT_HTML)} (${(patched.length / 1024).toFixed(0)} KiB) — three.js now loads from a local file, no network needed.`);
}

function fail(msg) {
  console.error(`\nbuild-app.js: ${msg}\n`);
  process.exit(1);
}

main();
