# BLOCKFRONT

A browser-based, Pixel-Gun-3D–inspired voxel first-person shooter. Single self-contained
`index.html` built with [three.js](https://threejs.org/) — no build step required.

## Play

Open `index.html` in a browser, or serve the folder and visit it:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

Press **START** to play. (Needs an internet connection the first time — three.js loads from a CDN.)

## Controls

**Desktop**
- **WASD** — move
- **Mouse** — look (click to lock the pointer)
- **Click** — shoot (hold for the auto rifle)
- **1 / 2 / 3** or **mouse wheel** — switch weapon

**Mobile / touch**
- **Left joystick** — move
- **Drag right side** — look
- **FIRE button** — shoot (hold for auto rifle)
- **1 / 2 / 3 buttons** — switch weapon

## Weapons

1. **Pistol** — fast, semi-auto, accurate
2. **Rifle** — full-auto, rapid, lower per-shot damage
3. **Ray Gun** — high-damage blue energy weapon

## Gameplay

- Voxel town arena with solid buildings, cover, and props.
- Enemies wander and take cover; pistol enemies shoot at range, knife enemies charge in.
- Red indicators float above enemies (visible through walls).
- Clear **3 waves** of enemies, then defeat the **boss** (own health bar) to win.
- Player has a health bar that **regenerates** when you avoid damage; take cover to heal.
- Distinct synthesized sound effects for the player's weapons vs. the enemies'.

## Tech notes

- Rendering: three.js (r128) via CDN, WebGL, dynamic shadows, canvas-generated voxel textures.
- Audio: Web Audio API, fully synthesized (no audio files).
- Everything is in one file (`index.html`): scene, map generator, AI, weapons, HUD, and UI.

## Roadmap / ideas

- Custom character skins
- More weapons and maps
- Vendored three.js for fully offline play

## Version

**v0.1** — first tagged prototype: 3 weapons, wave + boss loop, mobile controls,
collision, enemy AI, sounds, title screen.
