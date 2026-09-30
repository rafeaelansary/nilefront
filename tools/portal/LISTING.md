# CrazyGames listing — Nilefront

Paste-ready text for the developer portal. Last revised for v1.3.0 (resubmission after the 2026-09-28
"overall quality" rejection). Portal page:
https://developer.crazygames.com/games/a6428cd3-2d80-4229-a847-5c08aa61f72b

## Fixed by the portal (can't be changed here)

- **Name:** Nilefront
- **Category:** Shooting

## Form options

- **Progress Save:** selected — the game saves through the CrazyGames Data module (required when it does).
- **Upload:** HTML5 — drag the two files in `tools/portal/build/` (`index.html`, `three.min.js`) into the
  upload zone; CrazyGames' uploader refuses the zip. Build them first: `python3 tools/portal/build_portal.py`.
- **Covers:** `tools/portal/covers/cover_1920x1080.png` (landscape), `cover_800x1200.png` (portrait),
  `cover_800x800.png` (square)
- **Preview videos:** `tools/portal/video/preview_1920x1080.mp4` (landscape) and `preview_1080x1620.mp4`
  (portrait). Both are required. Exactly 20 s, silent, H.264, ~25 MB and ~19 MB (the limit is 50 MB).
- **Orientation (mobile):** landscape

## Tags (max 5)

1 Player · 3D · FPS — plus two of the portal's own tags. Pick whichever of these its tag list offers,
in this order of preference: **Blocky** (or Voxel / Pixel), **Boss Battle** (or Boss Fight),
**History** (or Historical / Egypt). Only use tags the portal's dropdown actually lists.

## Description (plain text, no HTML)

Nilefront is a voxel first-person shooter that walks Egypt's own history — from the Old Kingdom pyramids to Ptolemaic Alexandria, the Roman frontier, and Mamluk Cairo — one wave of enemies and one boss at a time.

Once Cairo falls quiet, spend the stars you've earned on passage to the wider world: Olmec and Aztec Mexico, Viking Age Sweden, and Yuan China each add their own maps, their own enemies, and their own boss fights — with a new arsenal of weapons for every era and destination.

Walk every road and a gate opens to the final fight: a monument built from every boss you've beaten, guarding the way to a quiet stretch of the Nile where the whole journey ends.

Your progress saves automatically — press Continue to pick up where you left off. Mouse sensitivity, field of view, volume and graphics quality are all in Settings.

## Controls

Desktop
WASD — move, Space — jump
Mouse — look (click to lock the pointer)
Click — shoot
Right-click or hold Shift — scope (bow, sling) or raise a shield
1 / 2 / 3 or mouse wheel — switch weapon, R — reload
E — use the travel booth, the gate and inscriptions
P — pause and resume (Esc also pauses)
AZERTY keyboards: ZQSD to move

Mobile / touch
Left thumb — move, drag right side — look
FIRE — shoot (hold for automatic weapons), JUMP — jump
SCOPE — aim (bow, sling) or raise a shield
1 / 2 / 3 — switch weapon
BOOTH — open the travel booth when standing at it
❚❚ — pause

## What changed since the rejected v1.1.0 (for the notes field, if there is one)

v1.3.0 (this upload):

- New sky: the blotchy painted clouds are gone — a clean gradient with blocky voxel clouds that drift
- Music: every region has its own score (an Egyptian maqam over modern drums and synths, a Roman march,
  Aztec slit drums, Viking drones, Chinese pentatonic), rising from calm to fight to boss
- Settings menu on the title and pause screens: mouse sensitivity, invert look, field of view, master /
  music / effects volume, and a FAST graphics mode for weaker devices
- Title screen shows the game: a slow camera over the first map instead of a dark overlay
- Interface redrawn in two embedded typefaces, with drawn icons in the HUD instead of emoji
- Fixed: a large flat square flashed over the screen on every bow, sling or thrown-weapon shot
- Faster pacing: two waves before every boss instead of three, in Egypt and on every destination
- The first bow is held bigger and canted, wholly on screen from tip to tip, clear of the crosshair and the
  HUD, instead of running off the top edge with its string down the side
- The Giza processional way is laid basalt paving again (a name clash had swapped in a noisy texture)
- Emoji replaced by drawn icons throughout (warnings, boss bar, booth, stars), so the game looks the same
  on Windows, macOS, ChromeOS and phones
- Fixed: pausing with P left the mouse captured, so the pause menu could not be clicked
- Developer console and admin shortcuts removed from this build (C,C no longer opens anything)
- Travel booth has a CLOSE button and a touch hint; key captions follow AZERTY layouts
- iOS: audio resumes on the next tap after an interruption

v1.2.0:

- Title screen with a controls card, a loading state, and a first-run tutorial
- Saved progress (CrazyGames Data module) with Continue / New Game
- CrazyGames SDK: gameplay start/stop, happytime on boss kills, completion %, mute setting
- Frame rate: 3–4x faster on every map (lighting baked; adaptive resolution on slow devices)
- Game feel: enemies break apart on death, hit and kill markers, damage direction, screen shake, UI sounds
- Mobile: weapon buttons no longer run off landscape phones; title screen fits short screens
- New cover art
