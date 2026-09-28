# Portal build

A self-contained copy of the game, zipped and ready to upload to a game portal (CrazyGames, itch.io,
Newgrounds — anywhere that runs a game inside its own sandboxed iframe rather than serving it from
your own domain).

```bash
node tools/portal/build-portal.js
```

Produces:

- `tools/portal/build/` — `index.html` + `three.min.js`, gitignored, safe to delete and regenerate
- `tools/portal/dist/NILEFRONT-vX.Y.Z-crazygames.zip` — upload this file as-is

## Why this exists

`../../index.html` loads three.js from `cdnjs.cloudflare.com` at runtime. That's fine for gh-pages,
but wrong for a portal submission: a review pass can run offline or behind a CSP that blocks
third-party scripts, and "the whole game goes black because a CDN hiccuped" is not a first impression
to give a reviewer. This script does exactly what
[`electron/scripts/build-app.js`](../../electron/scripts/build-app.js) already does for the desktop
build — swaps that one `<script>` tag for a local, vendored copy — reusing
`electron/vendor/three.min.js` as the source rather than keeping a second copy that could quietly
drift out of sync with the one already verified against the CDN tag's own integrity hash.

It also adds the **CrazyGames SDK** `<script>` tag (v3, from `sdk.crazygames.com`) ahead of three.js —
the one thing this build still loads over the network, because the SDK only works served from
CrazyGames' own domain. The game treats it as optional: through it, progress saves to CrazyGames' Data
module and the game reports gameplay start/stop, boss kills (`happytime`) and completion; without it (blocked,
offline, or any other host) the game runs the same and saves to `localStorage`. The gh-pages
`index.html` never gets this tag.

It also rewrites the "three.js did not load" error message, since the CDN build's version blames
`cdnjs.cloudflare.com` — which this build never talks to. If `three.min.js` fails to load here, the
real cause is almost always a bad zip.

Both swaps are matched against the exact current text and fail loudly if either has changed upstream,
the same policy `build-app.js` follows — a silently-stale swap is worse than a build that refuses to
run.

## Uploading to CrazyGames

At [developer.crazygames.com/submit](https://developer.crazygames.com/submit):

- **Game engine:** HTML5 (not "Externally hosted" — the files are uploaded directly, not iframed from
  your own server)
- **Upload files:** drag the two files from `tools/portal/build/` — `index.html` and `three.min.js` —
  straight into the upload zone. NOT the zip from `tools/portal/dist/`: CrazyGames' own dropzone
  rejects it outright ("Archive files are not supported, please drag and drop the files directly in
  the upload zone"). The zip this script also produces is for portals that *do* want one (itch.io,
  for instance) — check what each target actually accepts before assuming either format.
- **Does your game save progress:** No — see the README's own "Not gaps" section on why that's
  intentional
- **Basic vs Full Launch:** Basic needs no SDK and is the fast path to live; Full requires the
  CrazyGames SDK (ad hooks, `GameplayStart`/`GameplayStop`, auth, cloud save) and is what unlocks ad
  revenue. Nothing in this repo wires up that SDK yet — decide separately whether that's worth doing.

## Re-running after an update

Every time `index.html` changes, re-run `node tools/portal/build-portal.js` and upload the new zip —
there's no watch mode, and there shouldn't be; a portal upload is a deliberate step, not something to
fire on every save.
