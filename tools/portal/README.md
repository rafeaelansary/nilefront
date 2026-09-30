# Portal build

A self-contained copy of the game, zipped and ready to upload to a game portal (CrazyGames, itch.io,
Newgrounds — anywhere that runs a game inside its own sandboxed iframe rather than serving it from
your own domain).

```bash
node tools/portal/build-portal.js      # or, on a machine without Node:
python3 tools/portal/build_portal.py   # the same swaps and checks, byte-identical output
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

The SDK tag is also what switches the admin panel and the cheat console off: the game checks for the
SDK, and in this build C,C (which most shooters bind to crouch) does nothing. `#dev` on the URL turns
them back on, for testing a portal build in place.

## Covers and preview videos

CrazyGames asks for three covers and two preview videos. All five are made from the game itself:

- [`covers/`](covers/) — `cover_1920x1080.png`, `cover_800x1200.png`, `cover_800x800.png`, rendered by
  `python3 tools/portal/covers/src/make_covers.py` (see its README)
- [`video/`](video/) — `preview_1920x1080.mp4` (landscape, 16:9) and `preview_1080x1620.mp4` (portrait,
  2:3): 18 seconds each, silent, no cursor, opening on the cover. `python3 tools/portal/video/record.py`
  films the current portal build frame by frame in headless Chrome — build first. Its docstring says how,
  and what each of the seven shots is.

## Uploading to CrazyGames

At [developer.crazygames.com/submit](https://developer.crazygames.com/submit):

- **Game engine:** HTML5 (not "Externally hosted" — the files are uploaded directly, not iframed from
  your own server)
- **Upload files:** drag the two files from `tools/portal/build/` — `index.html` and `three.min.js` —
  straight into the upload zone. NOT the zip from `tools/portal/dist/`: CrazyGames' own dropzone
  rejects it outright ("Archive files are not supported, please drag and drop the files directly in
  the upload zone"). The zip this script also produces is for portals that *do* want one (itch.io,
  for instance) — check what each target actually accepts before assuming either format.
- **Does your game save progress:** Yes — select **Progress Save**. The game saves through the
  CrazyGames Data module (CrazyGames requires that option when it does).
- **Basic vs Full Launch:** Basic needs only the SDK's gameplay-start event, which the game sends; Full
  adds ads, account integration and landing new players straight in gameplay, and is what unlocks ad
  revenue. The game integrates gameplay start/stop, the Data module, `happytime` and the platform mute;
  it has no ad calls. The listing text, tags and form answers are in [`LISTING.md`](LISTING.md).

## Re-running after an update

Every time `index.html` changes, re-run the build and upload the two new files — there's no watch mode,
and there shouldn't be; a portal upload is a deliberate step, not something to fire on every save. If the
change is visible, re-render the covers and the videos too, so the store page still shows the game.
