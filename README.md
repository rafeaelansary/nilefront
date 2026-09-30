# NILEFRONT

A browser-based voxel first-person shooter that walks Egypt's own history — Old Kingdom to Mamluk
Cairo — and then sells you passage out of it. Single self-contained `index.html` built with
[three.js](https://threejs.org/), no build step.

## Play

Open `index.html` in a browser, or serve the folder and visit it:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

Press **PLAY** to play. (Needs an internet connection the first time — three.js loads from a CDN. The
desktop build in [`electron/`](electron/) vendors it and runs fully offline.)

**SETTINGS** (on the title screen and the pause screen) holds mouse or look sensitivity, invert look,
field of view, master / music / effects volume, and graphics: HIGH, or FAST (no sun shadows, 1x
resolution ceiling) for weaker machines.

## Controls

**Desktop**
- **WASD** — move, **Space** — jump
- **Mouse** — look (click to lock the pointer)
- **Click** — shoot, **right-click** or hold **Shift** — scope (bow, sling) or raise a shield
- **1 / 2 / 3** or **mouse wheel** — switch weapon, **R** — reload
- **E** — use the travel booth, the gate and the stele when you are standing at one
- **P** — pause and resume (**Esc** also pauses, by freeing the mouse)

Movement follows the physical keys, so on an AZERTY keyboard it is **ZQSD** — and the on-screen key
captions say so once the game has seen the layout.

**Mobile / touch**
- **Left joystick** — move
- **Drag right side** — look
- **FIRE** — shoot (hold for automatic weapons), **JUMP** — jump, **SCOPE** — aim or raise a shield
- **1 / 2 / 3** — switch weapon, **BOOTH** — use the booth when standing at it, **❚❚** — pause

## The campaign

Egypt runs as one continuous ladder of waves across four eras, each with its own map, enemies and
weapons, and each handing on to the next when its boss falls:

| Waves | Era | Ends with |
|-------|-----|-----------|
| 1–3 | Old Kingdom — the pyramid and the chamber beneath it | **The Colossus** |
| 4–6 | Greek — the agora, and the marsh the Hydra lives in | **The Hydra** |
| 7–9 | Roman — the frontier fort and the Colosseum | **The Champion** |
| 10 | Mamluk Cairo | the hub, and the travel booth |

Cairo has no enemies of its own. It is where a run ends and where the rest of the game is bought.

## The travel booth

Kills bank **⭐** across the whole run. The booth in the Cairo bazaar spends it on passage to a real
destination, each of which is two maps on one ticket and ends somewhere new:

| | Destination | ⭐ | The trip |
|-|-------------|---|----------|
| 🗿 | **Mexico** | 50 | Olmec La Venta → Aztec Tenochtitlan → the Aztec Market, a second booth |
| 🛡️ | **Sweden** | 60 | Birka → the fjord and the Skerry Troll → Aldeigjuborg, a third booth |
| 🐉 | **China** | 70 | Xiangyang's wall and its breach → the chained, burning fleet at Yamen |

Each destination carries its own weapons, its own roster of enemies, and its own bosses. Clearing all
three opens the way to the game's ending — see [The ending](#the-ending).

## Weapons

Every era and destination swaps the whole loadout:

| Loadout | Weapons |
|---------|---------|
| Old Kingdom | Bow · Khopesh · Was Scepter |
| The Nile | Harpoon |
| Greek | Sling · Xiphos · Trident |
| Roman | Javelin · Pugio · Greek Fire |
| Mamluk | Qaws · Saif · Naft Pot |
| Olmec | Macana · Blowgun · Atlatl |
| Aztec | Tecpatl · Chimalli · Smoking Mirror |
| Viking | Dane Axe · Hunnish Bow · Throwing Seax |
| Song | Zhanmadao · Repeating Crossbow · Thunderclap Bomb |

Several carry a second mode — the Hunnish Bow draws and holds, the Atlatl and Throwing Seax slash at
close range instead of throwing.

## Admin panel

Press **Z · X · X · C · C · C** in order. Toggles god mode, infinite ammo, infinite money, insta-kill
and flight; jumps to any wave or destination. The same flags are reachable as `/god`, `/fly`, `/tp`
and friends in the console (two **C** presses in a row). The sequence is deliberately awkward so a cheat
cannot fire by accident mid-run.

Both are off in the portal build (the copy that carries the CrazyGames SDK): most shooters bind **C** to
crouch, and a player reaching for it would open a cheat console. Add `#dev` to the URL to turn them back
on there for testing.

## Desktop build

[`electron/`](electron/) wraps this same file in an Electron window with a vendored three.js, so it
runs with no network. See [`electron/README.md`](electron/README.md). Current build: **1.1.0**, macOS
arm64 only.

## Portal build

`tools/portal/build-portal.js` (or `build_portal.py`, the same build for a machine without Node) produces
the self-contained copy for CrazyGames or a similar portal — three.js vendored locally the same way the
desktop build does it, so the game doesn't depend on a CDN inside a sandboxed iframe, plus the CrazyGames
SDK. The store covers and the preview videos are rendered from the game itself by scripts beside it. See
[`tools/portal/README.md`](tools/portal/README.md).

## Geometry audit

`tools/audit/` runs the game's whole script headlessly inside py_mini_racer against a stubbed three.js
and reads back real world-space bounding boxes — no browser, no build step. It checks that actors
stand on the floor, that no model renders as floating shards, that every map's ramps climb and its
decks hold you, and that nothing z-fights. See [`tools/audit/README.md`](tools/audit/README.md).

```bash
pip install py-mini-racer
python3 tools/audit/fullcheck.py     # the whole game
python3 tools/audit/chinacheck.py    # one destination, end to end
python3 tools/audit/finalcheck.py    # the endgame: gate, boss, and the Nile bank
```

## Tech notes

- Rendering: three.js r128 via CDN, WebGL, dynamic shadows, canvas-generated voxel textures.
- Audio: Web Audio API, fully synthesized — no audio files. That includes the music: each region has its
  own mode, instruments and two tunes, played at calm, fight or boss intensity as the game goes.
- Type: Rubik and Cinzel (both SIL OFL), embedded in the page as WOFF2.
- The world map in the travel booth is a Natural Earth coastline mask baked into the page as base64,
  so the booth needs no network either.
- Everything is one file: twenty maps, every model, the AI, the HUD and the UI.

## The ending

China is the last road. The moment the Yamen Admiral goes down on his own flagship you are not sent home
— the Gate of Ages opens where you stand and takes you straight to the final fight. Mexico and Sweden are
optional side-roads and neither opens it.

The gate also stands, unlocked, in whichever hub you are in — Cairo, the Aztec Market or Aldeigjuborg — so
there is a way back in if you die in the arena. It is never sold at the booth and costs nothing.

Through it is one fight and no waves: **THE SUM OF AGES**, 5200 HP, a lapis-and-gold monument carrying a
rack of trophies from every boss it remembers. It spends its health walking down through four ages, and
quotes the fight each trophy came from — the Colossus' heaving ground, the Hydra's venom, the Bearer's
fire serpent, the Admiral's burning floor — calling that era's own minions up beside it as it goes. The
age is read off its health rather than latched, so dying and coming back resumes the one your damage
earned.

When it falls you land on the **bank of the Nile**: a small, quiet map with a river, a low sun and a
stele that names every boss you put down. Nothing to fight, nothing to buy. Press **E** at the stele to
read the roll, and again to begin a new run.

## Saving

Progress saves by itself at checkpoints — the start of an era, a hub, the start of a trip's leg — and the
title screen offers **CONTINUE** (and **NEW GAME**, which asks twice). On CrazyGames it is kept in their Data
module, so it follows a player who logs in; everywhere else in `localStorage`. Dying rolls you back to the
start of the current era and no further, keeps credit for bosses already beaten, respawns you on the leg
you died on if you were away on a trip, and never touches your banked ⭐.

## License

© 2026 Rafea el Ansary. All rights reserved — the source is public to read, not to reuse. See
[LICENSE](LICENSE), which also carries the notices for the only third-party pieces in here: three.js
(MIT), Natural Earth's coastline data (public domain), and the Rubik and Cinzel typefaces (SIL OFL 1.1,
full text in [OFL.txt](OFL.txt)). Everything else — every model, texture, sound and note of music — is
generated by the code itself.
