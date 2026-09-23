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

Press **START** to play. (Needs an internet connection the first time — three.js loads from a CDN. The
desktop build in [`electron/`](electron/) vendors it and runs fully offline.)

## Controls

**Desktop**
- **WASD** — move, **Space** — jump
- **Mouse** — look (click to lock the pointer)
- **Click** — shoot, **right-click** — scope where the weapon has one
- **1 / 2 / 3 / 4** or **mouse wheel** — switch weapon, **F** — reload
- **E** — open the travel booth when you are standing at it
- **P** or **Esc** — pause

**Mobile / touch**
- **Left joystick** — move
- **Drag right side** — look
- **FIRE** — shoot (hold for automatic weapons), **SCOPE** — aim
- **1 / 2 / 3 / 4** — switch weapon

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

Each destination carries its own weapons, its own roster of enemies, and its own bosses.

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
and friends in the console (three **C** presses). The sequence is deliberately awkward so a cheat
cannot fire by accident mid-run.

## Desktop build

[`electron/`](electron/) wraps this same file in an Electron window with a vendored three.js, so it
runs with no network. See [`electron/README.md`](electron/README.md). Current build: **1.1.0**, macOS
arm64 only.

## Geometry audit

`tools/audit/` runs the game's whole script headlessly inside py_mini_racer against a stubbed three.js
and reads back real world-space bounding boxes — no browser, no build step. It checks that actors
stand on the floor, that no model renders as floating shards, that every map's ramps climb and its
decks hold you, and that nothing z-fights. See [`tools/audit/README.md`](tools/audit/README.md).

```bash
pip install py-mini-racer
python3 tools/audit/fullcheck.py     # the whole game
python3 tools/audit/chinacheck.py    # one destination, end to end
```

## Tech notes

- Rendering: three.js r128 via CDN, WebGL, dynamic shadows, canvas-generated voxel textures.
- Audio: Web Audio API, fully synthesized — no audio files.
- The world map in the travel booth is a Natural Earth coastline mask baked into the page as base64,
  so the booth needs no network either.
- Everything is one file: twenty maps, every model, the AI, the HUD and the UI.

## Known gaps

- No save: ⭐ and cleared destinations do not survive a reload.
- No ending: clearing China returns you to Cairo. There is no completion state yet.
