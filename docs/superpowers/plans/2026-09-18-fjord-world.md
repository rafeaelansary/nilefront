# The Fjord, part 1: the world — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Fjord as a place — a real moving sea, the Mälaren archipelago around it, and the player's longship riding the swell — reachable with `/tp fjord`, with nothing hostile in it yet.

**Architecture:** One new `THREE.Group` (`fjordWorld`) and one new collider array (`fjordColliders`), built by an IIFE in the same shape as `buildBirka()` and entered by `enterFjordWorld()` in the same shape as `enterSwedenWorld()`. A single pure function `fjordWaveAt(x, z, t)` is the only description of the sea surface anywhere in the file; the visible water mesh, every hull's motion, and the camera's roll all read from it, so nothing can drift out of sync with what is drawn.

**Tech Stack:** three.js r128 via CDN, one self-contained `index.html`, no build step. Verification is the repo's headless harness: `tools/audit/audit.py`, `tools/audit/fullcheck.py`, `tools/audit/bugcheck.py`, all running the real game script inside py_mini_racer against `tools/audit/three_stub.js`.

**Spec:** `docs/superpowers/specs/2026-09-18-fjord-sea-battle-design.md`

## Scope note

The spec covers the whole set piece: the world, then a two-phase boarding fight. This plan
covers **only the world** — spec build-order steps 1 and 2. It is a complete, playable,
reviewable deliverable on its own: you can `/tp fjord` and stand on a longship in a moving
sea. The fight (enemy ships, grapples, the roster, both phases, the jarl) gets its own plan
once this one is on screen and the water has had the visual passes the spec says it needs.

## Global Constraints

- Everything lives in `/Users/rafea/src/blockfront/index.html`. No new source files, no build step.
- three.js r128 only. No new CDN dependencies — the page's CSP blocks every external host but the one three.js already comes from.
- Never mutate a shared collider array in place; swap the `activeColliders` / `activeHeightZones` pointers. (See `docs`-level pattern notes and `enterSwedenWorld()`.)
- Never `scene.add()` a world's meshes directly — they belong to the world's own group, or `clearWorldGroups()` cannot remove them.
- Any new actor model added later must be registered in `tools/audit/audit.py`'s `ACTORS`. This plan adds no actors.
- Verification is green when `tools/audit/audit.py` reports `0 of N` on all three checks and every `tools/audit/bugcheck.py` suite prints `[ok ]`.
- Commit after every task. Commit messages end with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `index.html` — near `heightZonesSweden` (~line 411) | `fjordColliders`, `heightZonesFjord` declarations | Modify |
| `index.html` — near `waterRippleTex()` (~line 3251) | `FJORD_WAVES`, `fjordWaveAt()` — the surface, as a pure function | Modify |
| `index.html` — after `buildBirka()`'s IIFE (~line 8700) | `buildFjord()` IIFE: sea mesh, archipelago, the player's longship | Modify |
| `index.html` — after `enterSwedenWorld()` (~line 8730) | `enterFjordWorld()`, `fjordTick(dt, t)` | Modify |
| `index.html` — `clearWorldGroups()` (~line 3195) | add `fjordWorld` to the removal list | Modify |
| `index.html` — `adminTp()` (~line 15790) | `/tp fjord` | Modify |
| `index.html` — `animate()` (~line 17830) | call `fjordTick()` | Modify |
| `tools/audit/audit.py` — `EXPORTS` (~line 145) | register `fjordWorld` / `fjordColliders` in `__worlds`; export `fjordWaveAt` | Modify |
| `tools/audit/fjordcheck.py` | The sea's own checks. New file. | Create |

---

### Task 1: `fjordWaveAt()` — the sea surface as a pure function

Everything visible in this world reads its height from this one function. It is written and
tested before anything is drawn, because a wrong gradient here shows up later as foam in the
wrong place and ships that roll the wrong way, which is far harder to diagnose from a screenshot.

**Files:**
- Modify: `index.html` — immediately after `waterRippleTex()` (find it with `grep -n "^function waterRippleTex" index.html`)
- Modify: `tools/audit/audit.py` — the `EXPORTS` string, next to `globalThis.__worlds`
- Test: `tools/audit/fjordcheck.py` (create)

**Interfaces:**
- Consumes: nothing.
- Produces: `fjordWaveAt(x, z, t)` returning `{y, dx, dz}` — surface height in world units, and the two partial derivatives dy/dx and dy/dz. `FJORD_AMP` (number) — the maximum possible `|y|`, for callers that need to size clearances.

- [ ] **Step 1: Write the failing test**

Create `tools/audit/fjordcheck.py`:

```python
#!/usr/bin/env python3
"""The Fjord's sea surface: fjordWaveAt() and the mesh that draws it."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bugcheck import run, show

ok = True

ok &= show("fjordWaveAt is deterministic, bounded, and its gradient is the real one", run("""
  if(typeof fjordWaveAt !== 'function') throw new Error('fjordWaveAt is not defined');
  if(typeof FJORD_AMP !== 'number') throw new Error('FJORD_AMP is not defined');

  // deterministic: same inputs, same answer
  var a = fjordWaveAt(3.5, -8.25, 12.0), b = fjordWaveAt(3.5, -8.25, 12.0);
  if(a.y !== b.y) throw new Error('not deterministic');

  // bounded by FJORD_AMP, sampled over a wide patch and a long time
  var peak = 0;
  for(var t=0; t<20; t+=0.37)
    for(var x=-60; x<=60; x+=3.1)
      for(var z=-60; z<=60; z+=3.1)
        peak = Math.max(peak, Math.abs(fjordWaveAt(x,z,t).y));
  if(peak > FJORD_AMP + 1e-9) throw new Error('height '+peak.toFixed(3)+' exceeds FJORD_AMP '+FJORD_AMP);
  if(peak < FJORD_AMP*0.5) throw new Error('never gets near FJORD_AMP (peak '+peak.toFixed(3)+') -- the waves cancel');

  // the gradient must match a finite difference of the height, or foam and roll go the wrong way
  var h = 1e-4, worst = 0;
  for(var i=0;i<400;i++){
    var x = Math.sin(i*12.9)*40, z = Math.cos(i*7.7)*40, t = (i%17)*0.61;
    var g = fjordWaveAt(x,z,t);
    var fdx = (fjordWaveAt(x+h,z,t).y - fjordWaveAt(x-h,z,t).y)/(2*h);
    var fdz = (fjordWaveAt(x,z+h,t).y - fjordWaveAt(x,z-h,t).y)/(2*h);
    worst = Math.max(worst, Math.abs(g.dx-fdx), Math.abs(g.dz-fdz));
  }
  if(worst > 1e-3) throw new Error('gradient disagrees with the height field by '+worst.toExponential(2));

  // it must actually move: the same point at two times must differ
  if(Math.abs(fjordWaveAt(0,0,0).y - fjordWaveAt(0,0,3.0).y) < 1e-6)
    throw new Error('the sea is not moving');

  return 'peak '+peak.toFixed(3)+' of FJORD_AMP '+FJORD_AMP+', gradient error '+worst.toExponential(1);
"""))

sys.exit(0 if ok else 1)
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python3 tools/audit/fjordcheck.py`
Expected: `[BUG] ... Error: fjordWaveAt is not defined`

- [ ] **Step 3: Write `fjordWaveAt()`**

In `index.html`, immediately after the closing `}` of `waterRippleTex()`:

```js
// ===================== THE FJORD'S SEA =====================
// The single description of the water surface in this game. The visible mesh, every hull that
// floats on it and the camera's own roll all read from this one function, so none of them can
// drift out of step with what is actually drawn — which is the failure mode that makes a boat
// scene look broken even when each piece is individually fine.
//
// Four directional waves, chosen with wavelengths that are not small multiples of each other so
// the sum never settles into a visible repeating pattern. Long low swell first, then progressively
// shorter and faster chop riding on it.
const FJORD_WAVES = [
  {amp:0.26, len:14.0, spd:0.55, dx: 0.94, dz: 0.34},   // the main swell, running up the fjord
  {amp:0.17, len: 8.5, spd:0.80, dx: 0.62, dz:-0.78},   // a second set crossing it
  {amp:0.09, len: 4.7, spd:1.15, dx:-0.31, dz: 0.95},
  {amp:0.05, len: 2.6, spd:1.60, dx: 0.80, dz: 0.60},   // chop
];
// The largest height the sum can reach. Anything that needs clearance over the water (a hull's
// freeboard, a skerry's base) sizes itself off this rather than guessing.
const FJORD_AMP = FJORD_WAVES.reduce((s,w)=>s+w.amp, 0);
// Returns the surface height at (x,z) and the two partial derivatives of that height. The
// derivatives are what foam and hull roll are computed from, so they are returned rather than
// finite-differenced by each caller: four cosines here beats eight extra evaluations there.
function fjordWaveAt(x, z, t){
  let y=0, gx=0, gz=0;
  for(let i=0;i<FJORD_WAVES.length;i++){
    const w = FJORD_WAVES[i], k = Math.PI*2/w.len;
    const phase = (x*w.dx + z*w.dz)*k + t*w.spd*k;
    y += Math.sin(phase)*w.amp;
    const c = Math.cos(phase)*w.amp*k;
    gx += c*w.dx;
    gz += c*w.dz;
  }
  return {y:y, dx:gx, dz:gz};
}
```

- [ ] **Step 4: Export it to the harness**

In `tools/audit/audit.py`, inside the `EXPORTS` string, immediately before `globalThis.__builders = {`:

```js
globalThis.__fjordWaveAt = typeof fjordWaveAt === 'function' ? fjordWaveAt : null;
```

(`fjordcheck.py` reaches `fjordWaveAt` through `bugcheck.run()`, which evaluates inside the
game's own scope, so this export is for `audit.py`-based callers only. Add it now so later
tasks that use `build_ctx` do not have to.)

- [ ] **Step 5: Run the test and watch it pass**

Run: `python3 tools/audit/fjordcheck.py`
Expected: `[ok ] fjordWaveAt is deterministic, bounded, and its gradient is the real one` and a line reporting the peak and a gradient error below 1e-3.

- [ ] **Step 6: Confirm nothing else moved**

Run: `python3 tools/audit/bugcheck.py`
Expected: every suite prints `[ok ]`.

- [ ] **Step 7: Commit**

```bash
git add index.html tools/audit/audit.py tools/audit/fjordcheck.py
git commit -m "$(cat <<'EOF'
Add fjordWaveAt(), the Fjord's one description of its sea

Four directional waves summed, with wavelengths deliberately not small
multiples of each other so the surface never settles into a visible repeat.
Returns the two partial derivatives alongside the height because foam and hull
roll both need the gradient, and four cosines here is cheaper than eight extra
height evaluations at every call site.

Written and tested before anything is drawn: a wrong gradient surfaces later as
foam in the wrong place and ships rolling the wrong way, which is very hard to
diagnose from a screenshot. fjordcheck.py finite-differences the height field
and holds the returned gradient to 1e-3 of it.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: the world group, `enterFjordWorld()`, and `/tp fjord`

An empty, enterable world with a flat placeholder sea. This exists so the next three tasks have
somewhere to put their geometry and something to run against — and so a mistake in the world
plumbing is caught on its own rather than tangled up with a mistake in the water.

**Files:**
- Modify: `index.html` — collider declarations (`grep -n "heightZonesSweden" index.html`, add alongside)
- Modify: `index.html` — after `buildBirka()`'s IIFE and `swedenOverworld`'s definition
- Modify: `index.html` — `clearWorldGroups()`, `adminTp()`
- Modify: `tools/audit/audit.py` — `__worlds` list
- Modify: `tools/audit/fullcheck.py` — `PLAYER_ENTRY`
- Test: `tools/audit/fjordcheck.py`

**Interfaces:**
- Consumes: `fjordWaveAt`, `FJORD_AMP` (Task 1).
- Produces: `fjordWorld` (THREE.Group), `fjordColliders` (Array), `heightZonesFjord` (Array), `enterFjordWorld(banner)`, and `FJORD_DECK_Y` (number) — the y the player's feet sit at on a deck, used by Task 5.

- [ ] **Step 1: Write the failing test**

Append to `tools/audit/fjordcheck.py`, before the `sys.exit` line:

```python
ok &= show("the Fjord is a real world: enterable, removable, and reachable from /tp", run("""
  gameStarted = true;
  if(typeof fjordWorld === 'undefined') throw new Error('fjordWorld is not defined');
  if(typeof fjordColliders === 'undefined') throw new Error('fjordColliders is not defined');

  enterFjordWorld('test');
  if(!fjordWorld.parent) throw new Error('enterFjordWorld did not add the world to the scene');
  if(activeColliders !== fjordColliders) throw new Error('activeColliders was not swapped to the Fjord');
  if(insideCollider(camera.position.x, camera.position.z, 0.45, 0))
    throw new Error('the player arrives inside geometry');

  // leaving must take the whole world with it, or its meshes draw on top of the next map
  enterSwedenWorld('back');
  if(fjordWorld.parent) throw new Error('clearWorldGroups() does not remove fjordWorld');
  if(activeColliders !== swedenColliders) throw new Error('leaving did not restore Birka colliders');

  // and /tp must reach it
  if(!adminTp(['fjord'])) throw new Error('/tp fjord did not work');
  if(!fjordWorld.parent) throw new Error('/tp fjord did not enter the world');
  return 'enter/leave/tp all clean';
"""))
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python3 tools/audit/fjordcheck.py`
Expected: `[BUG] ... Error: fjordWorld is not defined`

- [ ] **Step 3: Declare the arrays**

In `index.html`, next to the existing Birka declarations (`const swedenColliders = [];` and `const heightZonesSweden = [];`):

```js
const fjordColliders = [];       // the Fjord — Sweden's second leg, fought on longship decks
const heightZonesFjord = [];     // a deck is one level; nothing here is climbable
```

- [ ] **Step 4: Add the group, the builder stub and the enter function**

In `index.html`, after `swedenOverworld`'s block and `enterSwedenWorld()`:

```js
// ===================== THE FJORD (Sweden, leg 2) =====================
// Open water in the Mälaren archipelago. The whole leg is fought on longship decks, so nothing
// here is walkable except a deck — the sea is lethal, exactly as the Nile Wave's is.
const fjordWorld = new THREE.Group();
// Where a deck's planking sits. Everything that floats is positioned relative to this, so the
// freeboard clears FJORD_AMP and a trough never leaves a hull hanging over a hole in the sea.
const FJORD_DECK_Y = 0.62;
addTarget = fjordColliders;
heightZoneTarget = heightZonesFjord;
(function buildFjord(){
  // filled in by Tasks 3, 4 and 5. A flat placeholder sea so the world is enterable now.
  const sea = new THREE.Mesh(new THREE.BoxGeometry(400,1,400),
                             voxMat(0x3a6a88,{noise:12}));
  sea.position.set(0,-0.5,0);
  fjordWorld.add(sea);
})();
addTarget = colliders;
heightZoneTarget = heightZonesOriginal;

// Same shape as enterSwedenWorld(): world, lighting, loadout and garrison in one call.
function enterFjordWorld(banner){
  clearWorldGroups();
  scene.add(fjordWorld);
  sky.visible = true;
  activeColliders = fjordColliders;
  activeHeightZones = heightZonesFjord;
  playClamp = 24;
  // Colder and flatter than Birka: the same northern key, but over open water with no snow to
  // bounce light back up, and fog closing much nearer so the far ships arrive out of it.
  scene.background.set(0xa8bcc8); scene.fog.color.set(0xb8c8d2);
  scene.fog.near = 16; scene.fog.far = 90;
  setDistantGround(0x5a7484);
  skyTint(0xdce8f0);
  hemi.intensity = 0.76; hemi.color.set(0xc4d8e6); hemi.groundColor.set(0x38505e);
  sun.intensity = 0.58; fill.intensity = 0.34; fill.color.set(0xb4c8dc);
  camera.position.set(0, 1.7 + FJORD_DECK_Y, 3.2);
  yaw = targetYaw = 0; pitch = targetPitch = 0; vel.set(0,0,0);
  playerHeight = FJORD_DECK_Y; stuckTimer = 0;
  clearBots(); bossActive = false; showBossBar(false); pending = null; inNileArea = false;
  weapons.forEach(w=>w.visible=false);
  weapons = swedenWeapons;
  selectWeapon(0);
  setBanner(banner); setTimeout(()=>{ if(bannerEl && bannerEl.textContent===banner) setBanner(''); }, 3000);
}
```

- [ ] **Step 5: Register it with `clearWorldGroups()`**

In `clearWorldGroups()`, add `fjordWorld` to the array that is removed — after `swedenOverworld`:

```js
  [pyramidOverworld, greekOverworld, romanOverworld, islamicOverworld, mexicoOverworld, aztecOverworld, aztecMarketOverworld, swedenOverworld, fjordWorld, pyramidDungeon, greekDungeon, nileWorld, hydraArena, colosseumArena, ifritArena].forEach(g=>{ if(g.parent) scene.remove(g); });
```

- [ ] **Step 6: Add `/tp fjord`**

In `adminTp()`, next to the existing `if(first === 'nile')` line:

```js
  if(first === 'fjord'){ enterFjordWorld('🌊 The fjord — open water, and the fog is thinning'); chatSay('✓ the Fjord', 'ok'); return true; }
```

...and add it to the `/tp` doc comment above the function, under the `/tp nile` line:

```js
//   /tp fjord          the Fjord, Sweden's second leg
```

- [ ] **Step 7: Register it with the audit harness**

In `tools/audit/audit.py`, in the `__worlds` pair list, after the `swedenOverworld` entry:

```js
 ['fjordWorld','fjordColliders'],
```

In `tools/audit/fullcheck.py`, add to `PLAYER_ENTRY`:

```python
    "fjordWorld": (0, 3.2),
```

- [ ] **Step 8: Run the test and watch it pass**

Run: `python3 tools/audit/fjordcheck.py`
Expected: both checks `[ok ]`, the second reporting `enter/leave/tp all clean`.

- [ ] **Step 9: Confirm the map registers and nothing regressed**

Run: `python3 tools/audit/fullcheck.py --maps fjordWorld`
Expected: a `--- fjordWorld` section appears with a mesh count.
Run: `python3 tools/audit/bugcheck.py`
Expected: every suite `[ok ]`.

- [ ] **Step 10: Commit**

```bash
git add index.html tools/audit/audit.py tools/audit/fullcheck.py tools/audit/fjordcheck.py
git commit -m "$(cat <<'EOF'
Add the Fjord as an enterable world, with a placeholder sea

Group, colliders, height zones, enterFjordWorld() and /tp fjord -- the same
shape as Birka's, so the next tasks have somewhere to put geometry and a
mistake in the world plumbing is caught on its own rather than tangled up with
a mistake in the water.

Lighting continues Birka's northern key but colder and flatter: no snow to
bounce light back up, and fog closing at 90 instead of 110 so the far ships
will arrive out of it.

Registered in clearWorldGroups(), in audit.py's __worlds and in fullcheck's
PLAYER_ENTRY, so the map sweep covers it from its first commit rather than
being added to the checks later.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: the swell — the sea mesh that reads from `fjordWaveAt()`

**Files:**
- Modify: `index.html` — `buildFjord()`, replacing the placeholder sea; and `animate()`
- Test: `tools/audit/fjordcheck.py`

**Interfaces:**
- Consumes: `fjordWaveAt`, `FJORD_AMP` (Task 1); `fjordWorld` (Task 2).
- Produces: `fjordSea` (object) — `{mesh, geo, cols, seg, size}`, and `fjordTick(dt, t)` which advances the surface and everything floating on it. Task 5 extends `fjordTick`.

- [ ] **Step 1: Write the failing test**

Append to `tools/audit/fjordcheck.py`, before `sys.exit`:

```python
ok &= show("the sea mesh is the wave function, and its foam follows real steepness", run("""
  gameStarted = true;
  enterFjordWorld('test');
  if(typeof fjordSea === 'undefined' || !fjordSea) throw new Error('fjordSea is not defined');
  if(typeof fjordTick !== 'function') throw new Error('fjordTick is not defined');

  var T = 7.25;
  fjordTick(0.016, T);

  // every vertex must sit exactly where fjordWaveAt() says it does
  var pos = fjordSea.geo.attributes.position, seg = fjordSea.seg, size = fjordSea.size;
  var worst = 0, checked = 0;
  for(var i=0;i<pos.count;i+=7){
    var col = i % (seg+1), row = (i / (seg+1))|0;
    var x = -size/2 + col*(size/seg), z = -size/2 + row*(size/seg);
    worst = Math.max(worst, Math.abs(pos.getY(i) - fjordWaveAt(x,z,T).y));
    checked++;
  }
  if(worst > 1e-6) throw new Error('mesh disagrees with fjordWaveAt by '+worst.toExponential(2));

  // it must actually move between frames
  var before = pos.getY(0);
  fjordTick(0.016, T + 1.7);
  if(Math.abs(pos.getY(0) - before) < 1e-6) throw new Error('the mesh does not move with time');

  // Foam: the whitest water must be the steepest water. Compared as the top fifth against the
  // bottom fifth by brightness rather than against a fixed threshold -- the palette is a tuning
  // knob and an absolute cutoff would break every time somebody adjusted a colour.
  var cols = fjordSea.cols, samples = [];
  for(var i=0;i<pos.count;i+=7){
    var c = (i % (seg+1)), r = (i/(seg+1))|0;
    var x = -size/2 + c*(size/seg), z = -size/2 + r*(size/seg);
    var g = fjordWaveAt(x,z,T+1.7);
    samples.push({bright:cols.getX(i), steep:Math.hypot(g.dx,g.dz)});
  }
  samples.sort(function(a,b){ return a.bright - b.bright; });
  var fifth = Math.max(1, (samples.length/5)|0), lo = 0, hi = 0;
  for(var i=0;i<fifth;i++){ lo += samples[i].steep; hi += samples[samples.length-1-i].steep; }
  lo /= fifth; hi /= fifth;
  if(samples[samples.length-1].bright - samples[0].bright < 0.05)
    throw new Error('the sea is all one tone -- no crest/trough shading at all');
  if(hi <= lo*1.2)
    throw new Error('foam is not on the steep water (whitest fifth '+hi.toFixed(3)+
                    ' vs darkest fifth '+lo.toFixed(3)+')');
  return checked+' vertices match, steepness of the whitest fifth '+hi.toFixed(2)+
         ' against the darkest '+lo.toFixed(2);
"""))
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python3 tools/audit/fjordcheck.py`
Expected: `[BUG] ... Error: fjordSea is not defined`

- [ ] **Step 3: Replace the placeholder sea**

In `buildFjord()`, replace the placeholder block with:

```js
  // ---- the sea ----
  // A segmented plane whose vertices are moved every frame to wherever fjordWaveAt() says the
  // surface is. 96 units across at 64 segments is a vertex every 1.5 units — fine enough that a
  // 2.6-unit chop wave is not stair-stepped, coarse enough that the per-frame update is ~4k
  // writes, which is nothing beside the draw calls this map already makes.
  // Beyond it sits a much larger flat plane in the same deep tone, so the moving water runs out
  // into calm distance rather than ending at a visible edge — everything past the fog is flat
  // anyway, and 400x400 of moving vertices would not be.
  const SEA=96, SEG=64;
  const seaGeo = new THREE.PlaneGeometry(SEA, SEA, SEG, SEG);
  seaGeo.rotateX(-Math.PI/2);
  const seaCols = new THREE.BufferAttribute(new Float32Array(seaGeo.attributes.position.count*3), 3);
  seaGeo.setAttribute('color', seaCols);
  const seaMat = new THREE.MeshLambertMaterial({vertexColors:true});
  const seaMesh = new THREE.Mesh(seaGeo, seaMat);
  seaMesh.receiveShadow = true;
  fjordWorld.add(seaMesh);
  fjordSea = {mesh:seaMesh, geo:seaGeo, cols:seaCols, seg:SEG, size:SEA};
  // the calm distance
  const far = new THREE.Mesh(new THREE.BoxGeometry(420,1,420), voxMat(0x2e5064,{noise:10}));
  far.position.set(0,-0.75,0);
  fjordWorld.add(far);
```

Declare `fjordSea` next to `FJORD_DECK_Y` so it is in scope for `fjordTick()`:

```js
let fjordSea = null;
```

- [ ] **Step 4: Write `fjordTick()`**

After `enterFjordWorld()`:

```js
// Advances the sea and everything floating on it. Called once a frame from animate(), and only
// while the Fjord is the world on screen.
// Colour comes from the surface's own SHAPE rather than from a texture: height picks the base
// tone (deep slate in the troughs, pale grey-green on the shoulders) and steepness — the
// magnitude of the gradient fjordWaveAt() already returns — whitens it toward foam. Foam then
// appears where the water is genuinely steep, which moves with the waves, instead of wherever a
// texture happens to be light.
const FJORD_TROUGH = new THREE.Color(0x24455c);
const FJORD_CREST  = new THREE.Color(0x5b8ba6);
const FJORD_FOAM   = new THREE.Color(0xdfeaf0);
const _fjc = new THREE.Color();
function fjordTick(dt, t){
  if(!fjordSea) return;
  const pos = fjordSea.geo.attributes.position, cols = fjordSea.cols;
  const seg = fjordSea.seg, size = fjordSea.size, step = size/seg;
  for(let i=0;i<pos.count;i++){
    const c = i % (seg+1), r = (i/(seg+1))|0;
    const x = -size/2 + c*step, z = -size/2 + r*step;
    const w = fjordWaveAt(x, z, t);
    pos.setY(i, w.y);
    const lift = (w.y/FJORD_AMP)*0.5 + 0.5;              // 0 in the deepest trough, 1 at the peak
    const steep = Math.min(1, Math.hypot(w.dx, w.dz)*1.9);
    _fjc.copy(FJORD_TROUGH).lerp(FJORD_CREST, lift).lerp(FJORD_FOAM, steep*steep*lift);
    cols.setXYZ(i, _fjc.r, _fjc.g, _fjc.b);
  }
  pos.needsUpdate = true;
  cols.needsUpdate = true;
  fjordSea.geo.computeVertexNormals();                    // or the swell is lit as if it were flat
}
```

- [ ] **Step 5: Call it from `animate()`**

In `animate()`, next to the existing `waterSurfaces.forEach(...)` block:

```js
  if(fjordWorld.parent) fjordTick(dt, t);
```

- [ ] **Step 6: Run the test and watch it pass**

Run: `python3 tools/audit/fjordcheck.py`
Expected: three `[ok ]` lines; the third reports the vertex match and a higher foam steepness than dull steepness.

- [ ] **Step 7: Look at it**

Run: `python3 -m http.server 8000`, open `http://localhost:8000`, press START, open the console with `C,C` and type `/tp fjord`.
Expected: water that moves, with lighter crests and foam on the steep faces. Judge it. The spec says to expect two or three passes here; tune `FJORD_WAVES`, the two base colours and the `1.9` steepness scale until it looks like cold water.

- [ ] **Step 8: Commit**

```bash
git add index.html tools/audit/fjordcheck.py
git commit -m "$(cat <<'EOF'
Give the Fjord a sea that actually moves

A 96x96 plane at 64 segments -- a vertex every 1.5 units -- with every vertex
moved each frame to wherever fjordWaveAt() says the surface is, and a large
flat plane of the same deep tone beyond it so the moving water runs out into
calm distance instead of ending at a visible edge.

Colour comes from the surface's own shape rather than from a texture: height
picks the base tone and STEEPNESS whitens it toward foam, using the gradient
fjordWaveAt() already returns. Foam therefore appears where the water is
genuinely steep and travels with the waves, rather than sitting wherever a
texture happens to be light. Normals are recomputed each frame or the swell is
lit as though it were flat, which undoes the whole effect.

fjordcheck.py holds every vertex to 1e-6 of the wave function and asserts that
the whitest vertices are measurably steeper than the rest -- foam in the wrong
place is the failure that is hardest to see in a still.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: the archipelago

**Files:**
- Modify: `index.html` — `buildFjord()`
- Test: `tools/audit/fjordcheck.py`

**Interfaces:**
- Consumes: `fjordWorld`, `FJORD_AMP`.
- Produces: nothing other tasks read. Pure scenery.

- [ ] **Step 1: Write the failing test**

Append to `tools/audit/fjordcheck.py`, before `sys.exit`:

```python
ok &= show("the archipelago is scenery only, and stands clear of the water", run("""
  gameStarted = true;
  enterFjordWorld('test');
  // It is scenery: the fight is on decks, so nothing out there may be solid. A collider on a
  // skerry would block the player against an island they can never reach.
  // Stated as "every collider belongs to a ship" rather than "there are none", because the next
  // task adds the longship's rails and a flat count would fail the moment it lands.
  var strays = fjordColliders.filter(function(b){ return Math.abs(b.x) > 8 || Math.abs(b.z) > 8; });
  if(strays.length)
    throw new Error('the archipelago is solid: '+strays.length+' colliders away from the ships, '+
                    'first at '+JSON.stringify([strays[0].x, strays[0].z]));
  if(heightZonesFjord.length !== 0) throw new Error('nothing in the Fjord is climbable');

  // count what is out there, and check it is out THERE -- islands inside the play area would be
  // solid-looking obstacles the player sails straight through
  var n = 0, tooClose = [];
  fjordWorld.traverse(function(o){
    if(!o.isMesh || !o.geometry || !o.geometry._half) return;
    var h = o.geometry._half;
    if(h.x > 40 || h.z > 40) return;                       // the sea planes themselves
    n++;
    var d = Math.hypot(o.position.x, o.position.z);
    if(d < 26 && o.position.y > -FJORD_AMP) tooClose.push([o.position.x|0, o.position.z|0]);
  });
  if(n < 12) throw new Error('only '+n+' pieces of scenery -- that is not an archipelago');
  if(tooClose.length) throw new Error('scenery inside the play area at '+JSON.stringify(tooClose.slice(0,4)));
  return n+' pieces, all clear of the play area';
"""))
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python3 tools/audit/fjordcheck.py`
Expected: `[BUG] ... only 0 pieces of scenery -- that is not an archipelago`

- [ ] **Step 3: Build the archipelago**

Append inside `buildFjord()`, after the sea:

```js
  // ---- the archipelago ----
  // Mälaren's skerries: bare granite, snow-capped, with a few wind-bent pines. None of it is a
  // collider and none of it is reachable — it is here for parallax, for depth, and to say where
  // the player is. Everything sits at least 30 out, well beyond playClamp, so it reads as
  // distance rather than as an obstacle the ship refuses to reach.
  const graniteF = voxMat(0x6a6f72,{noise:18});
  const graniteD = voxMat(0x4a4f54,{noise:16});
  const snowF    = voxMat(0xdfe8ee,{noise:8});
  const pineF    = voxMat(0x27402f,{noise:16});
  const trunkF   = voxMat(0x3e2f22,{noise:14});
  function fb(w,h,d,mat,x,y,z){ const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);
    m.position.set(x,y,z); m.castShadow=true; m.receiveShadow=true; fjordWorld.add(m); return m; }
  function pine(x,y,z,s){
    fb(0.3*s,1.6*s,0.3*s, trunkF, x, y+0.8*s, z);
    for(let i=0;i<3;i++) fb((2.2-i*0.6)*s, 0.9*s, (2.2-i*0.6)*s, pineF, x, y+1.7*s+i*0.75*s, z);
  }
  // [x, z, radius, height, pines] — spread all round the horizon, with two larger wooded
  // islands to break the ring up so it does not read as a fence.
  [[-38,-22, 7, 2.6, 3], [ 34,-30, 5, 1.8, 2], [ 44,  6, 9, 3.4, 5],
   [ 22, 41, 6, 2.2, 2], [-16, 46, 4, 1.4, 0], [-45, 18, 8, 3.0, 4],
   [-31, 36, 3, 1.0, 0], [ 48,-14, 4, 1.6, 1], [  6,-44, 6, 2.4, 2],
   [-52, -4, 5, 2.0, 1], [ 30, 24, 3, 1.1, 0], [-8, -38, 4, 1.5, 1]
  ].forEach(([ix,iz,r,h,np], k)=>{
    // the rock: a squat mass with a couple of shelves, not a cone — granite breaks in slabs
    fb(r*2, h, r*1.7, graniteF, ix, h/2 - 0.4, iz);
    fb(r*1.5, h*0.45, r*2.1, graniteD, ix, h*0.28 - 0.4, iz);
    fb(r*1.1, h*0.30, r*1.2, graniteF, ix, h*0.86 - 0.4, iz);
    // snow on the crown
    fb(r*1.15, 0.30, r*1.0, snowF, ix, h - 0.34, iz);
    // a skirt of wet rock at the waterline, so the island meets the sea instead of floating on it
    fb(r*2.2, 0.5, r*1.9, graniteD, ix, -0.45, iz);
    for(let p=0;p<np;p++){
      const a = k*1.7 + p*2.4;
      pine(ix + Math.cos(a)*r*0.5, h - 0.4, iz + Math.sin(a)*r*0.4, 0.8 + (p%2)*0.35);
    }
  });
```

- [ ] **Step 4: Run the test and watch it pass**

Run: `python3 tools/audit/fjordcheck.py`
Expected: four `[ok ]` lines; the last reports the scenery count.

- [ ] **Step 5: Run the map sweep**

Run: `python3 tools/audit/fullcheck.py --maps fjordWorld`
Expected: a `--- fjordWorld` section. `near-coplanar world faces` and `floating scenery` should be low. Fix any coplanar pair it names by separating the two faces by at least 0.01; the islands' stacked slabs are the likely source, and the deliberately different widths above are what keep them apart.

- [ ] **Step 6: Look at it**

Serve and `/tp fjord`. Expected: a ring of snow-capped granite skerries in the fog, at varying distances, with pines on the larger ones. Judge the fog distance against them — `scene.fog.far` is 90 and the furthest island is ~52 out, so they should be present but softened.

- [ ] **Step 7: Commit**

```bash
git add index.html tools/audit/fjordcheck.py
git commit -m "$(cat <<'EOF'
Put the Mälaren archipelago round the Fjord

Twelve snow-capped granite skerries with wind-bent pines on the larger ones,
spread all round the horizon at varying distance with two bigger wooded islands
breaking the ring up so it does not read as a fence.

None of it is a collider and none of it is reachable. That is asserted rather
than assumed: the fight is on decks, and a collider on an island the player can
never get to would block them against something invisible. fjordcheck.py fails
if the archipelago adds a single collider or height zone, or if any of it
strays inside the play area.

Rocks are built as squat slabbed masses rather than cones, because granite
breaks in slabs, and each carries a skirt of wet rock at the waterline so the
island meets the sea instead of floating on it.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: the player's longship, riding the swell

**Files:**
- Modify: `index.html` — `buildFjord()`, `fjordTick()`, and the player-death path
- Test: `tools/audit/fjordcheck.py`

**Interfaces:**
- Consumes: `fjordWaveAt`, `FJORD_AMP`, `FJORD_DECK_Y`, `fjordSea`, `fjordTick`.
- Produces: `fjordShips` (Array of `{grp, x, z, roll, pitch}`) — Task 6 (the fight plan) adds enemy ships to this same array so they float by the same rule.

- [ ] **Step 1: Write the failing test**

Append to `tools/audit/fjordcheck.py`, before `sys.exit`:

```python
ok &= show("the longship rides the same swell the sea is drawn from", run("""
  gameStarted = true;
  enterFjordWorld('test');
  if(typeof fjordShips === 'undefined' || !fjordShips.length) throw new Error('fjordShips is empty');
  var ship = fjordShips[0];

  var T = 4.5;
  fjordTick(0.016, T);
  var w = fjordWaveAt(ship.x, ship.z, T);
  if(Math.abs(ship.grp.position.y - (w.y + FJORD_DECK_Y)) > 1e-6)
    throw new Error('the hull is not sitting on the surface: hull '+ship.grp.position.y.toFixed(4)+
                    ' vs water '+(w.y+FJORD_DECK_Y).toFixed(4));
  // roll and pitch must come from the slope, so a hull leans INTO the wave rather than wobbling freely
  if(Math.abs(ship.grp.rotation.z + w.dx*FJORD_HEEL) > 1e-6) throw new Error('roll does not follow the slope');
  if(Math.abs(ship.grp.rotation.x - w.dz*FJORD_HEEL) > 1e-6) throw new Error('pitch does not follow the slope');

  // it must move between frames
  var y0 = ship.grp.position.y;
  fjordTick(0.016, T + 2.2);
  if(Math.abs(ship.grp.position.y - y0) < 1e-6) throw new Error('the ship does not heave');

  // the deck is walkable and the sea is not: stepping off the rail must be lethal
  var before = player.hp;
  camera.position.set(0, 1.7 + FJORD_DECK_Y, 30);     // well over the side
  fjordTick(0.016, T);
  if(player.hp >= before) throw new Error('walking off the deck into the sea did not kill the player');
  return 'hull heaves and heels with the surface; the sea is lethal';
"""))
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python3 tools/audit/fjordcheck.py`
Expected: `[BUG] ... Error: fjordShips is empty`

- [ ] **Step 3: Build the ship**

**Port Birka's longship rather than inventing a second one.** It already exists as the local
`ship(px, pz, rot, scale, sailMat)` inside `buildBirka()` — find it with
`grep -n "function ship(px,pz,rot,scale,sailMat)" index.html` and read the whole function before
you start. It builds, in this order: four clinker strakes each stepped out and up from the one
below; a sheer strake along the rail; stem and stern rising to a carved head; the mast; a furled
sail with red stripes; the yard; oars shipped along both rails; and shields on the rail. Copy that
body verbatim into `buildFjord()` with exactly four changes:

1. It already builds into a local `THREE.Group` called `K` — keep that, and **return `K`** instead
   of letting it fall out of scope. Birka's version adds `K` to the `scene`; add it to `fjordWorld`.
2. **Drop the `addBox(...)` call at the end of it.** Birka's ship is an obstacle you walk around;
   this one is a deck you stand on, and its collision is the four rails added in the snippet below.
3. **Add a deck.** Birka's ship has no walkable surface because nobody ever stands on it. Add one
   plank slab spanning the hull, with its TOP face at `y = 0` inside the group:
   `const deck = new THREE.Mesh(new THREE.BoxGeometry(2.6, 0.18, 9.2), plankF); deck.position.set(0, -0.09, 0); deck.receiveShadow = true; K.add(deck);`
   where `plankF` is `new THREE.MeshLambertMaterial({map:_finish(nileDeckPlankTex(),2)})`.
   Top face at `y = 0` is load-bearing: the group rides at `FJORD_DECK_Y`, so the planking then
   sits exactly where `playerHeight` puts the player's feet, at every point of the swell.
4. Keep the scale at 1 — Birka beaches its knarr at a reduced scale, and this one is full size.

Then, as the local group factory:

```js
  // ---- the ships ----
  // Built into their own groups rather than straight into the world, because every one of them
  // moves every frame. The construction follows Birka's own longship: clinker strakes stepped out
  // and up, carved stem and stern, mast, furled sail, oars shipped along the rail, shields on it.
  const fjordShipGroup = (x, z, rot) => {
    const K = new THREE.Group();
    K.position.set(x, FJORD_DECK_Y, z);
    K.rotation.y = rot;
    fjordWorld.add(K);
    return K;
  };
  const own = fjordShipGroup(0, 0, 0);
  fjordShips.push({grp:own, x:0, z:0, roll:0, pitch:0});
  // The deck's walkable rectangle, as a collider ring: the RAILS are solid, the deck is not.
  // Same arrangement the Nile Wave's boat uses -- the player moves freely on the planking and
  // cannot walk through the sides.
  addBox(0,  4.6, 2.9, 0.4);   // stem rail
  addBox(0, -4.6, 2.9, 0.4);   // stern rail
  addBox( 1.45, 0, 0.4, 9.6);  // starboard
  addBox(-1.45, 0, 0.4, 9.6);  // port
```

Declare, next to `fjordSea`:

```js
const fjordShips = [];
// How hard a hull leans into the slope it is sitting on. Multiplied by the surface gradient, so
// a steep face heels the ship further than a gentle one. Tuned by eye; too much and the deck is
// unusable, too little and the ship reads as a decal on moving water.
const FJORD_HEEL = 0.55;
```

- [ ] **Step 4: Float them in `fjordTick()`**

At the end of `fjordTick()`, before the closing brace:

```js
  // Everything that floats reads the SAME function the visible surface was just built from, so a
  // hull can never sit above or below the water it is drawn on. Heave from the height, heel and
  // pitch from the gradient — a ship leans into the face it is on rather than wobbling to its own
  // clock, and two ships lashed together work against each other exactly as real ones do.
  for(let i=0;i<fjordShips.length;i++){
    const s = fjordShips[i], w = fjordWaveAt(s.x, s.z, t);
    s.grp.position.y = w.y + FJORD_DECK_Y;
    s.grp.rotation.z = -w.dx*FJORD_HEEL;
    s.grp.rotation.x =  w.dz*FJORD_HEEL;
    s.roll = s.grp.rotation.z; s.pitch = s.grp.rotation.x;
  }
  // The player stands on the first ship: their feet follow its deck, and the camera takes a
  // heavily damped share of its roll. Full roll on a deck is nauseating and fights the movement
  // code; none at all makes the scene a diorama. 0.25 is the starting point, tune by playing it.
  if(fjordShips.length){
    const own = fjordShips[0];
    playerHeight = FJORD_DECK_Y + fjordWaveAt(own.x, own.z, t).y;
    camera.rotation.z = own.roll * 0.25;
  }
  // The sea is lethal, the way the Nile Wave's is. Off the deck is off the ship.
  if(player.alive && Math.hypot(camera.position.x, camera.position.z) > 6.0) damagePlayer(9999);
```

- [ ] **Step 5: Run the test and watch it pass**

Run: `python3 tools/audit/fjordcheck.py`
Expected: five `[ok ]` lines, the last reporting that the hull heaves and heels and the sea is lethal.

- [ ] **Step 6: Run everything**

Run: `python3 tools/audit/audit.py` — expected `0 of N` on all three checks.
Run: `python3 tools/audit/bugcheck.py` — expected every suite `[ok ]`.
Run: `python3 tools/audit/fullcheck.py --maps fjordWorld` — expected no new coplanar or floating findings beyond what Task 4 left.

- [ ] **Step 7: Look at it, and tune**

Serve and `/tp fjord`. Walk the deck. Expected: the ship lifts and heels with the swell under you, the horizon tilts slightly, and walking over the rail kills you. Tune `FJORD_HEEL` and the `0.25` camera share until the motion reads as a boat rather than as a lurch. This is the pass the spec warns about — expect to come back to `FJORD_WAVES` too now that there is something on the water to judge the scale against.

- [ ] **Step 8: Commit**

```bash
git add index.html tools/audit/fjordcheck.py
git commit -m "$(cat <<'EOF'
Float the player's longship on the Fjord's swell

The hull reads the same fjordWaveAt() the visible surface was built from, so it
can never sit above or below the water it is drawn on -- which is the single
thing that makes a boat scene look broken even when every piece of it is
individually fine. Heave comes from the height, heel and pitch from the
gradient, so a ship leans INTO the face it is sitting on rather than wobbling to
its own clock. Two hulls lashed together will therefore work against each other
the way real ones do, which is what the boarding fight needs.

The deck moves; the floor does not. playerHeight follows the deck so the player
rides it, and the camera takes a quarter of the roll -- full roll on a deck is
nauseating and fights the movement code, none at all makes the scene a diorama.

Off the deck is off the ship: over the rail is damagePlayer(9999), the same way
the Nile Wave handles going under, so no drowning system is needed.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

## What this plan does NOT cover

Deliberately left to a second plan, once the water has been looked at and tuned:

- enemy ships: approach, grapple, lashing the hulls together
- phase A, the hold, and the raiders coming over the rail
- the shielded spearman (a new actor — needs an `ACTORS` row in `audit.py`)
- phase B, the crossing, and the walkable area widening by a deck
- the jarl boss and the troll as his champion
- wiring the Fjord into `SWEDEN_LEGS` as leg 2 with its own wave ladder

Until that plan lands, the Fjord is reachable only through `/tp fjord`; Sweden remains a
one-leg destination and nothing in the campaign changes.
