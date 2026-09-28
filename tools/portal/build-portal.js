#!/usr/bin/env node
// Assembles tools/portal/build/ — a self-contained copy of the game, ready to zip and upload to a
// game portal (CrazyGames, itch.io, etc.) — from the single-file browser game at ../../index.html.
// That file stays the one source of truth (it's also what gh-pages deploys and what the Electron
// build wraps), so this never forks the game logic: it only swaps the one line that can't survive
// a portal's iframe sandbox.
//
// The game loads three.js from a CDN by URL, which is fine for gh-pages but wrong for a portal
// submission: a review pass can run offline or behind a CSP that blocks third-party scripts, and
// "the whole game goes black" on cdnjs hiccuping is not a first impression to give a reviewer. This
// mirrors electron/scripts/build-app.js's own fix for the exact same problem — same CDN tag, same
// swap to a local file — reusing electron/vendor/three.min.js as the source rather than keeping a
// second copy that could quietly drift out of sync with the one already verified against the CDN's
// own integrity hash.
'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.join(__dirname, '..', '..');
const PORTAL_DIR = path.join(__dirname, '..', 'portal');
const SRC_HTML = path.join(ROOT, 'index.html');
const OUT_DIR = path.join(PORTAL_DIR, 'build');
const OUT_HTML = path.join(OUT_DIR, 'index.html');
const VENDOR_SRC = path.join(ROOT, 'electron', 'vendor', 'three.min.js');
const DIST_DIR = path.join(PORTAL_DIR, 'dist');

// Kept identical to electron/scripts/build-app.js's own CDN_TAG on purpose: it is the same tag in the
// same file, so if one script's copy goes stale the other's should too, and that mismatch is the
// signal to fix both together rather than let a portal build quietly diverge from the desktop one.
const CDN_TAG = `<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
        integrity="sha512-dLxUelApnYxpLt6K2iomGngnHO83iUvZytA3YjDUCjT0HDOHKXnVYdf3hU4JjM8uEhxf9nD1/ey98U3t2vZ0qQ=="
        crossorigin="anonymous" referrerpolicy="no-referrer"></script>`;
// The CrazyGames SDK rides in ahead of three.js. It is the one script this build still fetches from the
// network, and it has to be: it only works served from CrazyGames' own domain. index.html treats it as
// optional — if it is blocked or missing, the game runs and saves to localStorage exactly as it does on
// gh-pages — so it is added here, in the portal build only, and never to the gh-pages page.
const SDK_TAG = `<script src="https://sdk.crazygames.com/crazygames-sdk-v3.js"></script>`;
const LOCAL_TAG = SDK_TAG + `\n<script src="three.min.js"></script>`;

// The failure message shown if THREE never defines itself. Correct for the CDN build, wrong for this
// one: if three.min.js fails to load here it's the zip, not cdnjs, and telling a portal reviewer to
// check their network for a host this build never talks to would send them chasing the wrong thing.
// Matched literally, same reasoning as CDN_TAG -- if this copy ever drifts from index.html's own
// wording, fail loudly rather than leave one message correct and the other stale.
const CDN_ERROR_MSG = `'The game pulls its 3D library from cdnjs.cloudflare.com on first run. Check the connection, '
      + 'or whether something on this network blocks that host, and reload.');`;
const LOCAL_ERROR_MSG = `'three.min.js failed to load from this bundle. The zip may be corrupt or incomplete -- '
      + 'redownload it and reload.');`;
// The sha512 half of the CDN tag above, re-derived here (rather than string-sliced out of it) so a
// future edit to CDN_TAG can't silently desync the two.
const EXPECTED_SHA512 = CDN_TAG.match(/integrity="sha512-([^"]+)"/)[1];

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
      `index.html's three.js <script> tag has changed and no longer matches what this build script ` +
      `expects. Update CDN_TAG here (and in electron/scripts/build-app.js, and re-vendor ` +
      `electron/vendor/three.min.js if the version or hash moved) before building.`
    );
  }

  // The whole point of vendoring is shipping a copy verified byte-for-byte against what the CDN tag
  // itself claims — not a copy that happens to still be sitting in electron/vendor/ from whenever it
  // was last fetched. Checked here, not just at fetch time, so a three.js version bump upstream (which
  // changes CDN_TAG's hash) fails this build loudly instead of silently shipping a stale local copy.
  const actualSha512 = require('crypto').createHash('sha512').update(fs.readFileSync(VENDOR_SRC)).digest('base64');
  if (actualSha512 !== EXPECTED_SHA512) {
    fail(
      `${path.relative(ROOT, VENDOR_SRC)} does not match the integrity hash on index.html's own <script> ` +
      `tag. Re-vendor it:\n` +
      `  curl -fsSL https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js -o ${path.relative(ROOT, VENDOR_SRC)}`
    );
  }

  const shown = html.match(VER_RE);
  const ver = shown ? shown[1] : '0.0.0';
  if (!shown) {
    console.warn(`warning: no <div id="ver">vX.Y.Z</div> found; naming the zip NILEFRONT-v0.0.0-crazygames.zip`);
  }

  if (!html.includes(CDN_ERROR_MSG)) {
    fail(
      `The three.js failure message in index.html has changed and no longer matches what this script ` +
      `expects to rewrite. Update CDN_ERROR_MSG/LOCAL_ERROR_MSG in build-portal.js before building.`
    );
  }

  const patched = html.replace(CDN_TAG, LOCAL_TAG).replace(CDN_ERROR_MSG, LOCAL_ERROR_MSG);

  fs.rmSync(OUT_DIR, { recursive: true, force: true });
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.mkdirSync(DIST_DIR, { recursive: true });
  fs.writeFileSync(OUT_HTML, patched);
  fs.copyFileSync(VENDOR_SRC, path.join(OUT_DIR, 'three.min.js'));

  console.log(`Built ${path.relative(ROOT, OUT_HTML)} (${(patched.length / 1024).toFixed(0)} KiB) — three.js loads from a local file; the CrazyGames SDK tag is added.`);

  // Zipped with index.html AT THE ROOT of the archive, not inside a subfolder -- portals that unpack a
  // zip and look for index.html next to the other files (CrazyGames included) will not find it one
  // directory down. `cd` into OUT_DIR first so `zip` doesn't record the parent path in every entry.
  const zipName = `NILEFRONT-v${ver}-crazygames.zip`;
  const zipPath = path.join(DIST_DIR, zipName);
  fs.rmSync(zipPath, { force: true });
  try {
    execFileSync('zip', ['-r', '-X', zipPath, 'index.html', 'three.min.js'], { cwd: OUT_DIR, stdio: 'pipe' });
  } catch (e) {
    fail(
      `zip failed (${e.message}). If the 'zip' command is not installed, either install it or zip ` +
      `${path.relative(ROOT, OUT_DIR)}/ by hand -- with index.html and three.min.js at the ARCHIVE ROOT, ` +
      `not inside a folder.`
    );
  }
  const zipKB = (fs.statSync(zipPath).size / 1024).toFixed(0);
  console.log(`Zipped ${path.relative(ROOT, zipPath)} (${zipKB} KiB) — upload this file as-is.`);
}

function fail(msg) {
  console.error(`\nbuild-portal.js: ${msg}\n`);
  process.exit(1);
}

main();
