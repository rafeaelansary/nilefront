# Islamic Era (Mamluk Cairo) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the fourth and final arc — Mamluk-era Cairo (map, Ifrit/Ghoul/Roc enemies, Ifrit King boss) — and chain it in so beating Roman's Boss III (currently a dead end confirmed by playtest — see the design spec) leads into it instead of ending the game.

**Architecture:** Reuses the exact swap pattern every prior era uses — no new infrastructure. One `THREE.Group` + collider array + height-zone array for the Cairo overworld; one more set for the Ifrit King's open-air arena. Enemies are custom model functions dispatched by skin name (like griffin/manticore/basilisk), reusing existing AI weaponTypes. See `docs/superpowers/specs/2026-08-11-islamic-era-design.md` for the full design rationale.

**Tech Stack:** Vanilla JS + three.js (CDN, no build step), all in `index.html`.

## Global Constraints

- No new infrastructure: reuse `addBox`/`addTarget`/`heightZoneTarget`/`activeColliders`/`activeHeightZones`/`clearWorldGroups()` exactly as every prior era does — do not introduce a different swap mechanism.
- No SKINS config entries for the new creatures — dispatch them as dedicated model functions in `makeVoxelBot()`, matching the Greek/Roman convention ("no SKINS entry needed").
- No automated test suite exists for this game. Every task's "test" step is a manual in-browser playtest via `http://localhost:8000` (a local server is already running for this project; if it's not, start one with `python3 -m http.server 8000` from the repo root).
- Exact HP/count/speed/placement numbers in this plan are first-pass values consistent with the established difficulty curve — verify and adjust them during each task's playtest step, the same way Roman's numbers were tuned after being first added (see `c0eb039 Rebalance minotaur frontal damage reduction and trident damage`).
- The working tree currently has **uncommitted** changes to `index.html`: the Islamic weapon loadout (`makeCrossbow`/`makeScimitar`/`makeNaftPot`, `islamicWeapons` array already added to `gunGroup`) and `zellijeTex()`. These are not separated out — Task 1's commit will include them alongside the new map code, since they all land in the same file and were already sitting in the working tree before this plan started.

---

### Task 1: Cairo overworld map (map-only, not yet reachable in normal play)

**Files:**
- Modify: `index.html` — collider/height-zone array declarations (~line 136-147), new map build block (insert after the Roman overworld build's `addTarget = colliders; heightZoneTarget = heightZonesOriginal;` reset, ~line 2278-2279)

**Interfaces:**
- Produces: `islamicColliders` (array), `heightZonesIslamic` (array), `islamicOverworld` (THREE.Group) — consumed by Task 2's `enterIslamicWorld()` and Task 4's `clearWorldGroups()` update.

- [ ] **Step 1: Add the collider/height-zone arrays**

In `index.html`, find this block (~line 136-138):

```js
const romanColliders = [];       // Roman overworld colliders (map built, not yet wired into wave/era progression)
const hydraColliders = [];       // Greek boss arena colliders (Boss II — the Hydra; an open-air marsh arena, not a dungeon)
const colosseumColliders = [];   // Roman boss arena colliders (Boss III — the Colosseum Champion; a full arena)
```

Add a new line after it:

```js
const islamicColliders = [];     // Islamic/Mamluk Cairo overworld colliders (waves 10-12)
```

Find this block (~line 144-147):

```js
const heightZonesOriginal = [];
const heightZonesPyramid = [];
const heightZonesGreek = [];
const heightZonesRoman = [];
```

Add a line after it:

```js
const heightZonesIslamic = [];
```

- [ ] **Step 2: Build the Cairo overworld map**

Find the end of `buildRomanOverworld()`'s IIFE and the reset lines right after it (~line 2273-2279):

```js
  oliveTreeR(-27,-15); oliveTreeR(27,14); oliveTreeR(-27,20); oliveTreeR(27,-18);
  oliveTreeR(-26,2); oliveTreeR(24,-20); oliveTreeR(-9,25); oliveTreeR(15,25);
})();
addTarget = colliders;
heightZoneTarget = heightZonesOriginal;
const romanOverworld = new THREE.Group();
scene.children.slice().forEach(o=>{ if(o===sky || o.isLight || o===overworld || o===pyramidOverworld || o===greekOverworld) return; romanOverworld.add(o); });
addTarget = colliders;
heightZoneTarget = heightZonesOriginal;
```

Insert this new block immediately after that (before the blank line + `// ---- voxel humanoid bot` comment that follows):

```js
// ===================== ISLAMIC OVERWORLD (Mamluk Cairo) — waves 10-12, the final arc =====================
// Same swap architecture as every prior overworld: its own collider/height-zone arrays, swept into its own
// group below. Not yet wired into any wave/era-transition logic in this task — see Task 2/4 for that.
addTarget = islamicColliders;
heightZoneTarget = heightZonesIslamic;
(function buildIslamicOverworld(){
  const sandstone = 0xc9a876;      // warm Citadel sandstone
  const sandstoneLight = 0xe0c89a;
  const domeMat = voxMat(0x1f7a72,{noise:10});   // turquoise-glazed tile, ties back to zellijeTex's palette
  const goldMat = metalMatP(0xc9a13a,80,0xffe8a0);
  const woodMat = voxMat(0x6b4a28,{noise:16});
  const awningMat = voxMat(0xb5342a,{noise:10}); // deep red-and-cream market awnings

  // ground: zellijeTex everywhere, a cobbled crossroads through the middle (reusing cobbleTex, same as Roman's road)
  const groundMat = new THREE.MeshLambertMaterial({map:_finish(zellijeTex(),20)});
  const ground = new THREE.Mesh(new THREE.BoxGeometry(62,1,62), groundMat); ground.position.set(0,-0.5,0); scene.add(ground);
  const roadMat = new THREE.MeshLambertMaterial({map:_finish(cobbleTex(),18), polygonOffset:true, polygonOffsetFactor:-2, polygonOffsetUnits:-2});
  function roadPath(x,z,w,d){ const m=new THREE.Mesh(new THREE.BoxGeometry(w,0.14,d),roadMat); m.position.set(x,0.07,z); m.receiveShadow=true; scene.add(m); }
  roadPath(0,0,8,58); roadPath(0,0,58,8);

  // ---- Citadel: a walled compound with crenellated (merlon) walls and two climbable corner towers ----
  function citadel(cx,cz){
    const w=16,d=14;
    addBox(cx,cz,w,d);
    const podium=new THREE.Mesh(new THREE.BoxGeometry(w,3.4,d), voxMat(sandstone,{noise:14,pattern:'plate'})); podium.position.set(cx,1.7,cz); scene.add(podium);
    const merlonMat = voxMat(sandstoneLight,{noise:12});
    for(let x=-w/2;x<=w/2;x+=1.6){
      [cz-d/2,cz+d/2].forEach(z=>{ const m=new THREE.Mesh(new THREE.BoxGeometry(0.8,0.8,0.8), merlonMat); m.position.set(cx+x,3.8,z); scene.add(m); });
    }
    for(let z=-d/2;z<=d/2;z+=1.6){
      [cx-w/2,cx+w/2].forEach(x=>{ const m=new THREE.Mesh(new THREE.BoxGeometry(0.8,0.8,0.8), merlonMat); m.position.set(x,3.8,cz+z); scene.add(m); });
    }
    const gate=new THREE.Mesh(new THREE.BoxGeometry(3.2,3,0.6), voxMat(0x241c14,{noise:10})); gate.position.set(cx,1.5,cz-d/2-0.35); scene.add(gate);
    const gateArch=new THREE.Mesh(new THREE.TorusGeometry(1.6,0.3,8,14,Math.PI), voxMat(sandstone,{noise:12})); gateArch.position.set(cx,3,cz-d/2-0.35); scene.add(gateArch);
  }
  citadel(-19,17);
  sniperTower(-25,10, 4.5, 7, 0xb8a074, 'e'); // Citadel's climbable corner towers, same proven mechanic as every prior era
  sniperTower(-13,24, 4, 6.5, 0xc0a878, 's');

  // ---- Mosque: cube base, a single hemisphere dome (turquoise-glazed), and a tall minaret ----
  function mosque(cx,cz){
    const base=new THREE.Mesh(new THREE.BoxGeometry(9,5,9), voxMat(0xe0d6be,{noise:12,pattern:'plate'})); base.position.set(cx,2.5,cz); scene.add(base);
    addBox(cx,cz,9,9);
    const dome=new THREE.Mesh(new THREE.SphereGeometry(3.4,14,8,0,Math.PI*2,0,Math.PI/2), domeMat); dome.position.set(cx,5,cz); scene.add(dome);
    const finial=new THREE.Mesh(new THREE.ConeGeometry(0.15,0.6,6), goldMat); finial.position.set(cx,8.6,cz); scene.add(finial);
    // minaret: a tall tapering tower with a small balcony ring near the top
    const minaretX=cx+6, minaretZ=cz-4;
    const shaft=new THREE.Mesh(new THREE.CylinderGeometry(0.75,0.95,9,10), voxMat(0xe0d6be,{noise:12})); shaft.position.set(minaretX,4.5,minaretZ); scene.add(shaft);
    addBox(minaretX,minaretZ,1.9,1.9);
    const balcony=new THREE.Mesh(new THREE.CylinderGeometry(1.1,1.1,0.3,10), voxMat(sandstoneLight,{noise:10})); balcony.position.set(minaretX,8.6,minaretZ); scene.add(balcony);
    const cap=new THREE.Mesh(new THREE.ConeGeometry(0.7,1.6,10), domeMat); cap.position.set(minaretX,10.2,minaretZ); scene.add(cap);
    const capFinial=new THREE.Mesh(new THREE.ConeGeometry(0.1,0.5,6), goldMat); capFinial.position.set(minaretX,11.3,minaretZ); scene.add(capFinial);
  }
  mosque(19,-17);

  // ---- Khan bazaar: a small cluster of market stalls around a cobbled square ----
  function marketStall(x,z,rot){
    const stall=new THREE.Group(); stall.position.set(x,0,z); stall.rotation.y=rot||0; scene.add(stall);
    const post=(px,pz)=>{ const p=new THREE.Mesh(new THREE.CylinderGeometry(0.08,0.08,1.8,6), woodMat); p.position.set(px,0.9,pz); stall.add(p); };
    post(-1,-0.7); post(1,-0.7); post(-1,0.7); post(1,0.7);
    const roof=new THREE.Mesh(new THREE.BoxGeometry(2.4,0.15,1.8), awningMat); roof.position.set(0,1.85,0); stall.add(roof);
    const table=new THREE.Mesh(new THREE.BoxGeometry(2.0,0.6,1.4), woodMat); table.position.set(0,0.3,0); stall.add(table);
    addBox(x,z,2.4,1.8);
  }
  marketStall(-3,-2,0); marketStall(3,-2,0.15); marketStall(0,3,1.5708);
  const bazaarFloor=new THREE.Mesh(new THREE.BoxGeometry(11,0.05,10), new THREE.MeshLambertMaterial({map:_finish(cobbleTex(),9)}));
  bazaarFloor.position.set(0,-0.005,0.5); scene.add(bazaarFloor);

  // ---- 1 more legion-tower-style lookout, reused across every era ----
  sniperTower(23,20, 4, 5.5, 0xa89e8c, 'w');

  // ---- desert palm dressing toward the open edges (local to this map, same idea as Roman's oliveTreeR) ----
  function courtyardPalm(x,z){
    const trunk=new THREE.Mesh(new THREE.CylinderGeometry(0.14,0.2,2.6,6), voxMat(0x6b5230,{noise:14})); trunk.position.set(x,1.3,z); trunk.rotation.z=0.05; scene.add(trunk);
    const leafMat=voxMat(0x4a7a3e,{noise:16});
    for(let i=0;i<6;i++){ const a=i/6*Math.PI*2;
      const leaf=new THREE.Mesh(new THREE.BoxGeometry(1.0,0.08,0.28), leafMat); leaf.position.set(x+Math.cos(a)*0.5,2.7,z+Math.sin(a)*0.5); leaf.rotation.y=a; leaf.rotation.x=-0.3; scene.add(leaf); }
    addBox(x,z,0.7,0.7);
  }
  courtyardPalm(-27,-20); courtyardPalm(27,22); courtyardPalm(-27,25); courtyardPalm(27,-22);
  courtyardPalm(-24,-3); courtyardPalm(24,4);
})();
addTarget = colliders;
heightZoneTarget = heightZonesOriginal;
const islamicOverworld = new THREE.Group();
scene.children.slice().forEach(o=>{ if(o===sky || o.isLight || o===overworld || o===pyramidOverworld || o===greekOverworld || o===romanOverworld) return; islamicOverworld.add(o); });
addTarget = colliders;
heightZoneTarget = heightZonesOriginal;
```

- [ ] **Step 3: Manually verify the map renders and collides correctly**

Open `http://localhost:8000` in a browser, start the game (click PLAY, pointer-lock), then open devtools console (`Cmd+Option+J` on Mac Chrome) and run:

```js
clearWorldGroups(); scene.add(islamicOverworld); sky.visible=true;
activeColliders=islamicColliders; activeHeightZones=heightZonesIslamic;
camera.position.set(0,1.7,10); scene.background.set(0x8fd6f2);
```

Walk around (WASD + mouse). Confirm:
- The Citadel, mosque, and khan bazaar all render without missing textures or console errors.
- Walking into any wall/stall/tower actually blocks you (colliders work).
- The two Citadel towers and the extra lookout tower are climbable via their ramps (reuses `sniperTower`, already proven).
- No z-fighting/flicker on the ground or road.

Fix any issues found before moving on (adjust positions/dimensions directly in the code above).

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "$(cat <<'EOF'
Add Mamluk Cairo overworld map (map-only turn)

Citadel, mosque, and khan bazaar landmarks for the Islamic era, following
the same swap-architecture pattern as every prior era's map. Not yet wired
into wave/era progression — that's the next task. Also picks up the
already-in-progress Islamic weapon loadout (crossbow/scimitar/naft pot) and
zellijeTex that were sitting uncommitted in the working tree.
EOF
)"
```

---

### Task 2: Ifrit, Ghoul, and Roc pack enemies + waves 10-12

**Files:**
- Modify: `index.html` — new creature model functions (insert before `makeHydra()`, ~line 3286), `makeVoxelBot()` dispatch (~line 2422-2436), `WAVES`/`ERA_START_WAVE` (~line 4368-4376), `spawnWave()` (~line 4380-4440), new `enterIslamicWorld()` function (insert after `enterRomanWorld()`, ~line 4083), debug `KeyH` handler (~line 4187-4197)

**Interfaces:**
- Consumes: `islamicColliders`, `heightZonesIslamic`, `islamicOverworld` (Task 1); `islamicWeapons` (already exists, uncommitted).
- Produces: `makeIfrit()`, `makeGhoul()`, `makeRocPack()` (model functions); `enterIslamicWorld(banner)` — consumed by Task 4's chain wiring.

- [ ] **Step 1: Add the three creature model functions**

Find the line just before `function makeHydra(){` (~line 3286) and insert this block above it:

```js
// ---- Islamic era creatures (waves 10-12): Ifrit (ranged fire djinn) / Ghoul (fast melee) / Roc pack
// (themed dive-bomber encounter, reusing the griffin's dive-then-claw AI) — no SKINS entry needed, same as
// every other era's non-humanoid monsters ----

// ifrit: a floating fire djinn — no legs, a torso that tapers into a licking flame-cone "tail" instead of
// feet, glowing ember skin, small backswept horns. The Islamic era's ranged monster (weaponType 'pistol',
// same pure-ranged AI as jackal/soldier — it holds distance rather than closing to melee like the griffin/
// basilisk hybrid). Built facing +Z directly, same convention as every other creature (mesh.lookAt in the AI loop).
function makeIfrit(){
  const g = new THREE.Group();
  const emberMat = voxMat(0xd8481c,{noise:14});
  const emberMat2 = voxMat(0xa8280e,{noise:12});
  const flameMat = new THREE.MeshBasicMaterial({color:0xff8a2a,fog:false});
  const flameMat2 = new THREE.MeshBasicMaterial({color:0xffd23a,fog:false});
  const darkMat = voxMat(0x2a140a,{noise:10});

  const chest = new THREE.Mesh(new THREE.BoxGeometry(0.56,0.5,0.32), emberMat); chest.position.set(0,1.3,0); g.add(chest);
  const belly = new THREE.Mesh(new THREE.BoxGeometry(0.4,0.36,0.26), emberMat2); belly.position.set(0,0.98,0); g.add(belly);
  [{y:0.62,r:0.26,h:0.5},{y:0.32,r:0.17,h:0.42},{y:0.1,r:0.09,h:0.34}].forEach((c,i)=>{
    const cone=new THREE.Mesh(new THREE.ConeGeometry(c.r,c.h,7), i%2? flameMat:flameMat2); cone.position.set(0,c.y,0); g.add(cone);
  });
  const tailLight = new THREE.PointLight(0xff8a2a,0.9,3.2); tailLight.position.set(0,0.4,0); g.add(tailLight);
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.34,0.36,0.32), emberMat); head.position.set(0,1.72,0); g.add(head);
  [-1,1].forEach(side=>{
    const eye=new THREE.Mesh(new THREE.BoxGeometry(0.08,0.07,0.04), flameMat2); eye.position.set(side*0.09,1.74,0.17); g.add(eye);
    const horn=new THREE.Mesh(new THREE.ConeGeometry(0.05,0.26,4), darkMat); horn.position.set(side*0.14,1.94,-0.04); horn.rotation.x=-0.5; horn.rotation.z=side*0.3; g.add(horn);
  });
  const jaw=new THREE.Mesh(new THREE.BoxGeometry(0.22,0.08,0.06), darkMat); jaw.position.set(0,1.56,0.17); g.add(jaw);
  [-1,1].forEach(side=>{
    const arm=new THREE.Mesh(new THREE.BoxGeometry(0.13,0.42,0.13), emberMat2); arm.position.set(side*0.38,1.18,0.08); arm.rotation.z=side*-0.5; g.add(arm);
    const hand=new THREE.Mesh(new THREE.SphereGeometry(0.09,6,5), flameMat); hand.position.set(side*0.5,0.98,0.22); g.add(hand);
  });
  for(let i=0;i<5;i++){ const a=(i/5)*Math.PI*2;
    const wisp=new THREE.Mesh(new THREE.SphereGeometry(0.06+Math.random()*0.05,5,4), voxMat(0x4a4038,{noise:10}));
    wisp.position.set(Math.cos(a)*0.3, 1.45+Math.sin(a)*0.1, Math.sin(a)*0.3-0.1); g.add(wisp);
  }

  g.userData.bodyMeshes = [];
  g.traverse(o=>{ if(o.isMesh) g.userData.bodyMeshes.push(o); });
  const marker = new THREE.Sprite(new THREE.SpriteMaterial({map:enemyMarkerTex(), depthTest:false, depthWrite:false, transparent:true, fog:false}));
  marker.position.set(0, 2.15, 0); marker.scale.set(1,1,1); marker.renderOrder = 9999;
  marker.raycast = function(){};
  g.add(marker); g.userData.marker = marker;
  return g;
}

// ghoul: a gaunt, hunched grave-robber creature — the Islamic era's fast melee monster (weaponType 'knife',
// same chase AI as mummy/manticore). Built low and lean on all fours rather than upright, reading as fast
// and animalistic rather than a shambling zombie reskin.
function makeGhoul(){
  const g = new THREE.Group();
  const skinMat = voxMat(0x7a8a6a,{noise:16});
  const skinDark = voxMat(0x566048,{noise:14});
  const wrapMat = voxMat(0x3a3428,{noise:12});
  const clawMat = new THREE.MeshLambertMaterial({color:0x1c1810});

  const torso = new THREE.Mesh(new THREE.BoxGeometry(0.4,0.36,0.62), skinMat); torso.position.set(0,0.58,0); torso.rotation.x=0.35; g.add(torso);
  const wrap = new THREE.Mesh(new THREE.BoxGeometry(0.44,0.2,0.4), wrapMat); wrap.position.set(0,0.62,0.05); wrap.rotation.x=0.35; g.add(wrap);
  const neck = new THREE.Mesh(new THREE.BoxGeometry(0.18,0.22,0.2), skinDark); neck.position.set(0,0.78,0.36); neck.rotation.x=0.5; g.add(neck);
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.28,0.26,0.3), skinMat); head.position.set(0,0.9,0.5); g.add(head);
  [-1,1].forEach(side=>{
    const eye=new THREE.Mesh(new THREE.BoxGeometry(0.06,0.05,0.03), new THREE.MeshBasicMaterial({color:0xd4e838,fog:false})); eye.position.set(side*0.08,0.92,0.64); g.add(eye);
    const ear=new THREE.Mesh(new THREE.BoxGeometry(0.05,0.12,0.06),skinDark); ear.position.set(side*0.15,1.0,0.44); g.add(ear);
  });
  const jaw=new THREE.Mesh(new THREE.BoxGeometry(0.18,0.1,0.14), skinDark); jaw.position.set(0,0.78,0.6); g.add(jaw);
  [-1,1].forEach(side=>{
    const limb=new THREE.Mesh(new THREE.BoxGeometry(0.13,0.5,0.13), skinDark); limb.position.set(side*0.2,0.32,0.38); limb.rotation.x=-0.3; g.add(limb);
    const claw=new THREE.Mesh(new THREE.ConeGeometry(0.06,0.16,4), clawMat); claw.position.set(side*0.2,0.08,0.52); claw.rotation.x=1.9; g.add(claw);
  });
  [-1,1].forEach(side=>{
    const leg=new THREE.Mesh(new THREE.BoxGeometry(0.15,0.48,0.15), skinDark); leg.position.set(side*0.16,0.28,-0.28); g.add(leg);
    const foot=new THREE.Mesh(new THREE.BoxGeometry(0.16,0.1,0.22), skinDark); foot.position.set(side*0.16,0.06,-0.2); g.add(foot);
  });
  const tail=new THREE.Mesh(new THREE.BoxGeometry(0.1,0.1,0.3), skinDark); tail.position.set(0,0.5,-0.45); tail.rotation.x=-0.3; g.add(tail);

  g.userData.bodyMeshes = [];
  g.traverse(o=>{ if(o.isMesh) g.userData.bodyMeshes.push(o); });
  const marker = new THREE.Sprite(new THREE.SpriteMaterial({map:enemyMarkerTex(), depthTest:false, depthWrite:false, transparent:true, fog:false}));
  marker.position.set(0, 1.3, 0); marker.scale.set(1,1,1); marker.renderOrder = 9999;
  marker.raycast = function(){};
  g.add(marker); g.userData.marker = marker;
  return g;
}

function makeRocUnit(){
  const g = new THREE.Group();
  const body = g;
  const featherMat = voxMat(0x4a3a2e,{noise:16});
  const featherMat2 = voxMat(0x2e2018,{noise:14});
  const beakMat = new THREE.MeshLambertMaterial({color:0xe0a838});
  const talonMat = new THREE.MeshLambertMaterial({color:0x1c1810});
  const eyeMat = new THREE.MeshBasicMaterial({color:0xffd23a,fog:false});

  const torso = new THREE.Mesh(new THREE.BoxGeometry(0.42,0.4,0.8), featherMat); torso.position.set(0,0.9,0); body.add(torso);
  const chest = new THREE.Mesh(new THREE.BoxGeometry(0.36,0.34,0.32), featherMat2); chest.position.set(0,0.9,0.42); body.add(chest);
  const neck = new THREE.Mesh(new THREE.BoxGeometry(0.2,0.3,0.22), featherMat); neck.position.set(0,1.16,0.5); neck.rotation.x=-0.3; body.add(neck);
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.24,0.22,0.26), featherMat2); head.position.set(0,1.4,0.66); body.add(head);
  const beak = new THREE.Mesh(new THREE.ConeGeometry(0.08,0.32,4), beakMat); beak.rotation.x=1.5708; beak.position.set(0,1.37,0.9); body.add(beak);
  [-1,1].forEach(side=>{ const eye=new THREE.Mesh(new THREE.BoxGeometry(0.05,0.05,0.03), eyeMat); eye.position.set(side*0.1,1.44,0.8); body.add(eye); });
  [-1,1].forEach(side=>{
    const wingRoot=new THREE.Group(); wingRoot.position.set(side*0.28,1.0,-0.05); wingRoot.rotation.z=side*-0.4; body.add(wingRoot);
    const w1=new THREE.Mesh(new THREE.BoxGeometry(0.75,0.1,0.5),featherMat); w1.position.set(side*0.4,0.05,0); wingRoot.add(w1);
    const w2=new THREE.Mesh(new THREE.BoxGeometry(0.65,0.08,0.38),featherMat2); w2.position.set(side*0.95,-0.08,-0.05); wingRoot.add(w2);
    const w3=new THREE.Mesh(new THREE.BoxGeometry(0.5,0.06,0.26),featherMat); w3.position.set(side*1.4,-0.18,-0.08); wingRoot.add(w3);
  });
  [-1,1].forEach(side=>{
    const leg=new THREE.Mesh(new THREE.BoxGeometry(0.12,0.3,0.12), talonMat); leg.position.set(side*0.14,0.6,0.1); body.add(leg);
    const talon=new THREE.Mesh(new THREE.BoxGeometry(0.18,0.08,0.24), talonMat); talon.position.set(side*0.14,0.42,0.2); body.add(talon);
  });
  const tailFan = new THREE.Mesh(new THREE.BoxGeometry(0.36,0.06,0.4), featherMat2); tailFan.position.set(0,0.85,-0.55); tailFan.rotation.x=0.3; body.add(tailFan);
  return g;
}
// roc pack: 3 giant rocs sharing one hitbox/HP/AI, same pack mechanic as the warhound/scarab packs — the
// Islamic era's themed pack encounter, reusing the griffin's dive-then-claw AI (weaponType 'javelin') under
// this new skin/model.
function makeRocPack(){
  const g = new THREE.Group();
  const formation = [ {x:-0.6, z:0.15, ry:-0.25, s:1.0}, {x:0.55, z:0.0, ry:0.3, s:0.92}, {x:0.0, z:-0.45, ry:0.05, s:1.08} ];
  formation.forEach(f=>{
    const unit = makeRocUnit();
    unit.position.set(f.x,0,f.z); unit.rotation.y=f.ry; unit.scale.setScalar(f.s);
    g.add(unit);
  });
  g.userData.bodyMeshes = [];
  g.traverse(o=>{ if(o.isMesh) g.userData.bodyMeshes.push(o); });
  const marker = new THREE.Sprite(new THREE.SpriteMaterial({map:enemyMarkerTex(), depthTest:false, depthWrite:false, transparent:true, fog:false}));
  marker.position.set(0, 1.7, 0); marker.scale.set(1,1,1); marker.renderOrder = 9999;
  marker.raycast = function(){};
  g.add(marker); g.userData.marker = marker;
  return g;
}
```

- [ ] **Step 2: Dispatch the new skins in `makeVoxelBot()`**

Find (~line 2436):

```js
  if(skinName==='tiger') return makeTiger();
```

Add three lines after it:

```js
  if(skinName==='tiger') return makeTiger();
  if(skinName==='ifrit') return makeIfrit();
  if(skinName==='ghoul') return makeGhoul();
  if(skinName==='roc') return makeRocPack();
```

- [ ] **Step 3: Extend `WAVES` and `ERA_START_WAVE`**

Find (~line 4368):

```js
const WAVES=[3,4,5, 6,7,9, 7,8,10]; // 9 waves; a boss after wave 3 and after wave 6 — Roman waves 7-9 have no boss yet
```

Replace with:

```js
const WAVES=[3,4,5, 6,7,9, 7,8,10, 9,10,12]; // 12 waves; a boss after wave 3, 6, 9, and 12
```

Find (~line 4376):

```js
const ERA_START_WAVE=[0,3,6]; // waveIdx where each era begins — era 0 (pyramid) starts at wave 1, era 1 at wave 4, era 2 (Roman) at wave 7
```

Replace with:

```js
const ERA_START_WAVE=[0,3,6,9]; // waveIdx where each era begins — era 0 (pyramid) starts at wave 1, era 1 (Greek) at wave 4, era 2 (Roman) at wave 7, era 3 (Islamic) at wave 10
```

- [ ] **Step 4: Add the Islamic branch to `spawnWave()`**

Find (~line 4380-4390):

```js
function spawnWave(n){
  clearBots();
  const count=WAVES[n];
  const pyramid = n<3; // waves 1-3: desert/pyramid reskin, ahead of the stone-temple boss dungeon
  const roman = n>=6;  // waves 7-9: Roman legionaries — no boss/dungeon for this era yet
```

Replace the `roman` line and add an `islamic` line:

```js
function spawnWave(n){
  clearBots();
  const count=WAVES[n];
  const pyramid = n<3;        // waves 1-3: desert/pyramid reskin, ahead of the stone-temple boss dungeon
  const roman = n>=6 && n<9;  // waves 7-9: Roman legionaries
  const islamic = n>=9;       // waves 10-12: Islamic/Mamluk Cairo, the final regular waves before Boss IV
```

Find the difficulty-multiplier line (~line 4390):

```js
  const diff = pyramid ? waveDiff(n) : roman ? waveDiff(n)*0.8 : waveDiff(n)*0.88;
```

Replace with:

```js
  const diff = pyramid ? waveDiff(n) : roman ? waveDiff(n)*0.8 : islamic ? waveDiff(n)*0.72 : waveDiff(n)*0.88;
```

Find the per-bot roster branch (~line 4396-4412):

```js
    } else if(roman){
      // regular roster alternates two Roman monsters — manticore (winged lion/scorpion melee brute) and
      // basilisk (crested serpent, javelin weaponType giving the same ranged/melee-hybrid AI the Greek
      // griffin uses). A single hound pack (3 hounds sharing one HP/AI) is added once per wave below,
      // instead of looping hounds into this roster.
      skin = (i%2===0) ? 'manticore' : 'basilisk';
      wt = skin==='basilisk' ? 'javelin' : 'knife';
    } else {
```

Insert an `islamic` branch between the `roman` branch and the final `else` (Greek):

```js
    } else if(roman){
      // regular roster alternates two Roman monsters — manticore (winged lion/scorpion melee brute) and
      // basilisk (crested serpent, javelin weaponType giving the same ranged/melee-hybrid AI the Greek
      // griffin uses). A single hound pack (3 hounds sharing one HP/AI) is added once per wave below,
      // instead of looping hounds into this roster.
      skin = (i%2===0) ? 'manticore' : 'basilisk';
      wt = skin==='basilisk' ? 'javelin' : 'knife';
    } else if(islamic){
      // regular roster alternates two Islamic monsters — ifrit (ranged fire djinn, holds distance) and
      // ghoul (fast melee grave-robber). A roc pack (3 rocs sharing one HP/AI) is added once per wave
      // below, same convention as the Roman warhound pack.
      skin = (i%2===0) ? 'ifrit' : 'ghoul';
      wt = skin==='ifrit' ? 'pistol' : 'knife';
    } else {
```

Find the HP line (~line 4415):

```js
    const hp = (!pyramid && !roman && n===5) ? 245 : roman ? [290,320,300][n-6] : Math.round(BOT_MAX_HP*diff);
```

Replace with:

```js
    const hp = (!pyramid && !roman && !islamic && n===5) ? 245 : roman ? [290,320,300][n-6] : islamic ? [330,360,340][n-9] : Math.round(BOT_MAX_HP*diff);
```

Find the Roman warhound pack block (~line 4432-4437):

```js
  if(roman){ // one hound pack per Roman wave — a themed encounter, not looped into the regular roster.
    // HP scaled up ~1.4x over a regular grunt to represent 3 hounds sharing a single pool.
    const sp=SPAWN_POINTS[(n*5+2) % SPAWN_POINTS.length];
    const gruntHp=[290,320,300][n-6];
    spawnBot(sp[0],sp[1],0x201d19,[sp[0]-2,0,sp[1]],[sp[0]+2,0,sp[1]],'knife',
      {skin:'warhound', hp:Math.round(gruntHp*1.4), diff, speed:1+(diff-1)*0.5});
  }
```

Add a matching Islamic block right after it:

```js
  if(roman){ // one hound pack per Roman wave — a themed encounter, not looped into the regular roster.
    // HP scaled up ~1.4x over a regular grunt to represent 3 hounds sharing a single pool.
    const sp=SPAWN_POINTS[(n*5+2) % SPAWN_POINTS.length];
    const gruntHp=[290,320,300][n-6];
    spawnBot(sp[0],sp[1],0x201d19,[sp[0]-2,0,sp[1]],[sp[0]+2,0,sp[1]],'knife',
      {skin:'warhound', hp:Math.round(gruntHp*1.4), diff, speed:1+(diff-1)*0.5});
  }
  if(islamic){ // one roc pack per Islamic wave, same "themed pack, not regular roster" convention
    const sp=SPAWN_POINTS[(n*5+2) % SPAWN_POINTS.length];
    const gruntHp=[330,360,340][n-9];
    spawnBot(sp[0],sp[1],0x4a3a2e,[sp[0]-2,0,sp[1]],[sp[0]+2,0,sp[1]],'javelin',
      {skin:'roc', hp:Math.round(gruntHp*1.4), diff, speed:1+(diff-1)*0.5});
  }
```

Find the HUD line (~line 4439):

```js
  document.getElementById('wave').textContent=(n+1)+'/6';
```

Replace with (fixes the stale hardcoded total — it's been wrong since Roman pushed the count past 6):

```js
  document.getElementById('wave').textContent=(n+1)+'/'+WAVES.length;
```

- [ ] **Step 5: Add `enterIslamicWorld()`**

Find `enterRomanWorld()`'s closing brace (~line 4083):

```js
function enterRomanWorld(banner){
  clearWorldGroups();
  scene.add(romanOverworld);
  sky.visible = true;
  activeColliders = romanColliders;
  activeHeightZones = heightZonesRoman;
  scene.background.set(0x8fd6f2); scene.fog.color.set(0x9fdcf0); scene.fog.near=40; scene.fog.far=220;
  hemi.intensity=0.85; hemi.color.set(0xbfe3ff); hemi.groundColor.set(0x55603f);
  sun.intensity=0.95; fill.intensity=0.25; fill.color.set(0xaecbe0);
  camera.position.set(0,1.7,10); yaw=targetYaw=0; pitch=targetPitch=0; vel.set(0,0,0); playerHeight=0; stuckTimer=0;
  clearBots(); bossActive=false; showBossBar(false); pending=null; inNileArea=false;
  weapons.forEach(w=>w.visible=false);
  weapons = romanWeapons;
  selectWeapon(0);
  setBanner(banner); setTimeout(()=>{ if(bannerEl && bannerEl.textContent===banner) setBanner(''); },3000);
}
```

Insert a new function right after its closing `}`:

```js
// swaps in the Islamic/Cairo map + loadout — used by both the real post-Boss-III victory transition (Task 4)
// and by respawnPlayer() for era-3 deaths (Task 4). Modeled directly on enterRomanWorld(): an open
// transition, not exiting a dungeon, so world+lighting+loadout all happen in one call.
function enterIslamicWorld(banner){
  clearWorldGroups();
  scene.add(islamicOverworld);
  sky.visible = true;
  activeColliders = islamicColliders;
  activeHeightZones = heightZonesIslamic;
  scene.background.set(0x8fd6f2); scene.fog.color.set(0xe8dcc0); scene.fog.near=38; scene.fog.far=210; // bright, warm Cairo daylight
  hemi.intensity=0.9; hemi.color.set(0xfff0d0); hemi.groundColor.set(0x6a5a38);
  sun.intensity=1.0; fill.intensity=0.25; fill.color.set(0xffe6b8);
  camera.position.set(0,1.7,10); yaw=targetYaw=0; pitch=targetPitch=0; vel.set(0,0,0); playerHeight=0; stuckTimer=0;
  clearBots(); bossActive=false; showBossBar(false); pending=null; inNileArea=false;
  weapons.forEach(w=>w.visible=false);
  weapons = islamicWeapons;
  selectWeapon(0);
  setBanner(banner); setTimeout(()=>{ if(bannerEl && bannerEl.textContent===banner) setBanner(''); },3000);
}
```

**IMPORTANT:** `clearWorldGroups()` (~line 1220) does not yet know about `islamicOverworld`, so calling `enterIslamicWorld()` right now will leave the Roman/Greek/etc. group in the scene alongside it. This gets fixed in Task 4 — for this task's manual test (Step 7 below), that's expected and fine.

- [ ] **Step 6: Update the `KeyH` debug jump to target the new era**

Find (~line 4187-4197):

```js
  // ==================== DEBUG — REMOVE BEFORE SHIPPING ====================
  // H: jumps straight to the first wave of the most recent era (Roman) for testing — same transition
  // enterRomanWorld()+wave7 spawn already used for the real Boss II victory / era-2 respawn.
  if (e.code==='KeyH' && player.alive){
    clearBots();
    enterRomanWorld('🏛 Jumped to the Roman frontier');
    // bossNum MUST match the era (era 2 is reached by beating bosses I+II) — without this the wave-9 boss
    // trigger does bossNum++ from 0→1 and wrongly spawns Boss I (the Colossus), then its defeat path flips
    // you into the Greek map with mismatched era/wave state (Roman enemies in the Greek map).
    currentEra=2; bossNum=2; waveIdx=ERA_START_WAVE[2]; pending='wave'; betweenTimer=1.2;
  }
```

Replace with:

```js
  // ==================== DEBUG — REMOVE BEFORE SHIPPING ====================
  // H: jumps straight to the first wave of the most recent era (Islamic) for testing — same transition
  // enterIslamicWorld()+wave10 spawn used for the real Boss III victory / era-3 respawn (Task 4).
  if (e.code==='KeyH' && player.alive){
    clearBots();
    enterIslamicWorld('🕌 Jumped to Mamluk Cairo');
    // bossNum MUST match the era (era 3 is reached by beating bosses I+II+III) — without this the wave-12
    // boss trigger does bossNum++ from 0→1 and wrongly spawns Boss I, then its defeat path sends you into
    // the wrong map with mismatched era/wave state.
    currentEra=3; bossNum=3; waveIdx=ERA_START_WAVE[3]; pending='wave'; betweenTimer=1.2;
  }
```

- [ ] **Step 7: Manually verify waves 10-12**

Refresh the page, start the game, press `H` to jump to Mamluk Cairo. Confirm:
- The world loads with the Islamic loadout equipped (Qaws crossbow / Saif scimitar / Naft Pot).
- Wave 10 spawns Ifrit (ranged, holds distance, fires orange tracers) alternating with Ghoul (closes in fast), plus one roc pack that dives in and claws at close range.
- Press `L` (kills all enemies) to clear each wave quickly and confirm wave 11 and 12 also spawn correctly with escalating counts/HP.
- HUD wave counter reads e.g. `10/12` correctly (not `10/6`).
- After wave 12 clears, nothing happens yet (no boss trigger — that's Task 3). This is expected for this task.

Note any visual/collision issues with the new creature models and fix them in Step 1's code before committing.

- [ ] **Step 8: Commit**

```bash
git add index.html
git commit -m "$(cat <<'EOF'
Add Ifrit/Ghoul/Roc enemies and wire Islamic waves 10-12

Extends WAVES/ERA_START_WAVE, adds the Islamic roster branch to
spawnWave(), and adds enterIslamicWorld() (not yet reachable through
normal play — no boss trigger fires after wave 12 yet, and
clearWorldGroups() doesn't know about islamicOverworld yet). Also fixes
the wave HUD's hardcoded "/6" total, stale since Roman pushed the wave
count past 6.
EOF
)"
```

---

### Task 3: Ifrit King (Boss IV) — model, arena, fire-meteor mechanic

**Files:**
- Modify: `index.html` — `makeIfritKing()` (after the Task 2 creature functions, before `makeHydra()`), `makeVoxelBot()` dispatch, `ifritColliders` array, `ifritArena` group + build IIFE (after `buildColosseumArena()`, ~line 1206), `enterIfritArena()` (after `enterColosseumArena()`, ~line 4107), `spawnBossFight()` (~line 4443-4462), fire-meteor VFX system (after `spawnQuakeEffect()`, ~line 4878, and its per-frame update alongside the quake-effects loop, ~line 5118), `onAllDead()`'s boss-trigger line (~line 4515-4516)

**Interfaces:**
- Consumes: `makeIfrit()`'s visual style (Task 2, for consistency); `spawnBot()`, `showBossBar()`, `setBossBar()`, `shakeAmt`, `SFX.explosion()`, `damagePlayer()` (all pre-existing).
- Produces: `makeIfritKing()`, `ifritArena`, `enterIfritArena()`, `spawnFireMeteor(x,z)` — consumed by Task 4.

- [ ] **Step 1: Add the Ifrit King model**

Insert this right after the `makeRocPack()` function added in Task 2 (still before `makeHydra()`):

```js
// ifrit king: a towering fire djinn lord — Boss IV, the Islamic era's boss and (per the current roadmap)
// the campaign's final boss. Built like a scaled-up, more ornamented ifrit: a wider ember-glass chest
// plate, a crown of curved horns, a raging multi-cone flame column instead of the regular ifrit's slim
// flame tail, and twin burning braziers floating at its shoulders.
function makeIfritKing(){
  const g = new THREE.Group();
  const emberMat = voxMat(0xc93a14,{noise:14});
  const emberMat2 = voxMat(0x8a2008,{noise:12});
  const goldMat = metalMatP(0xe0a830,85,0xfff2c8);
  const flameMat = new THREE.MeshBasicMaterial({color:0xff8a2a,fog:false});
  const flameMat2 = new THREE.MeshBasicMaterial({color:0xffd23a,fog:false});
  const darkMat = voxMat(0x201008,{noise:10});

  const chest = new THREE.Mesh(new THREE.BoxGeometry(0.9,0.85,0.55), emberMat); chest.position.set(0,2.1,0); g.add(chest);
  const plate = new THREE.Mesh(new THREE.BoxGeometry(0.6,0.55,0.05), goldMat); plate.position.set(0,2.15,0.29); g.add(plate);
  const belly = new THREE.Mesh(new THREE.BoxGeometry(0.62,0.55,0.42), emberMat2); belly.position.set(0,1.55,0); g.add(belly);
  [{y:1.0,r:0.44,h:0.85},{y:0.5,r:0.3,h:0.7},{y:0.14,r:0.18,h:0.55},{y:-0.1,r:0.08,h:0.4}].forEach((c,i)=>{
    const cone=new THREE.Mesh(new THREE.ConeGeometry(c.r,c.h,8), i%2? flameMat:flameMat2); cone.position.set(0,c.y,0); g.add(cone);
  });
  const flameLight = new THREE.PointLight(0xff8a2a,1.6,7); flameLight.position.set(0,0.6,0); g.add(flameLight);
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.5,0.52,0.46), emberMat); head.position.set(0,2.75,0); g.add(head);
  [-1,1].forEach(side=>{
    const eye=new THREE.Mesh(new THREE.BoxGeometry(0.12,0.1,0.05), flameMat2); eye.position.set(side*0.13,2.78,0.25); g.add(eye);
    for(let i=0;i<2;i++){ const horn=new THREE.Mesh(new THREE.ConeGeometry(0.07-i*0.02,0.4-i*0.12,4), darkMat);
      horn.position.set(side*(0.2+i*0.1),3.05+i*0.1,-0.05-i*0.08); horn.rotation.x=-0.6; horn.rotation.z=side*(0.35+i*0.15); g.add(horn); }
  });
  const jaw=new THREE.Mesh(new THREE.BoxGeometry(0.3,0.1,0.08), darkMat); jaw.position.set(0,2.5,0.25); g.add(jaw);
  const crownBand=new THREE.Mesh(new THREE.CylinderGeometry(0.28,0.3,0.1,8), goldMat); crownBand.position.set(0,3.0,0); g.add(crownBand);
  [-1,1].forEach(side=>{
    const arm=new THREE.Mesh(new THREE.BoxGeometry(0.24,0.7,0.24), emberMat2); arm.position.set(side*0.62,2.0,0.12); arm.rotation.z=side*-0.4; g.add(arm);
    const hand=new THREE.Mesh(new THREE.SphereGeometry(0.16,7,6), flameMat); hand.position.set(side*0.85,1.55,0.36); g.add(hand);
    const brazier=new THREE.Mesh(new THREE.CylinderGeometry(0.14,0.2,0.16,8), darkMat); brazier.position.set(side*1.0,2.6,-0.1); g.add(brazier);
    const brazierFlame=new THREE.Mesh(new THREE.ConeGeometry(0.13,0.3,6), flameMat2); brazierFlame.position.set(side*1.0,2.78,-0.1); g.add(brazierFlame);
    const brazierLight = new THREE.PointLight(0xffb84a,0.8,3); brazierLight.position.set(side*1.0,2.7,-0.1); g.add(brazierLight);
  });

  g.userData.bodyMeshes = [];
  g.traverse(o=>{ if(o.isMesh) g.userData.bodyMeshes.push(o); });
  const marker = new THREE.Sprite(new THREE.SpriteMaterial({map:enemyMarkerTex(), depthTest:false, depthWrite:false, transparent:true, fog:false}));
  marker.position.set(0, 3.5, 0); marker.scale.set(1.4,1.4,1); marker.renderOrder = 9999;
  marker.raycast = function(){};
  g.add(marker); g.userData.marker = marker;
  return g;
}
```

Add its dispatch line in `makeVoxelBot()`, right after the `roc` line added in Task 2:

```js
  if(skinName==='roc') return makeRocPack();
  if(skinName==='ifritking') return makeIfritKing();
```

- [ ] **Step 2: Add `ifritColliders` and the arena group + build**

Find (~line 138, right after `colosseumColliders`):

```js
const colosseumColliders = [];   // Roman boss arena colliders (Boss III — the Colosseum Champion; a full arena)
```

Add a line after it:

```js
const ifritColliders = [];       // Islamic boss arena colliders (Boss IV — the Ifrit King; the Citadel courtyard)
```

Find the end of `buildColosseumArena()`'s IIFE (~line 1204-1206):

```js
  colosseumArena.add(new THREE.AmbientLight(0xffe6c0, 0.5));
})();

addTarget = colliders;   // back to overworld for anything built later
```

Insert the Ifrit arena build right before that final `addTarget = colliders;` line:

```js
  colosseumArena.add(new THREE.AmbientLight(0xffe6c0, 0.5));
})();

// ===== IFRIT ARENA (Boss IV) — the Citadel's inner courtyard: a walled, crenellated square, open sky,
// fire braziers lighting a warm dusk fight. Open-air like the Hydra marsh/Colosseum pit, not a dungeon. =====
const ifritArena = new THREE.Group();
addTarget = ifritColliders;
(function buildIfritArena(){
  const wallMat = voxMat(0xb89468,{noise:14,pattern:'plate'});
  const merlonMat = voxMat(0xa07f52,{noise:12});
  const darkMat = voxMat(0x241c14,{noise:10});
  const floorMat = new THREE.MeshLambertMaterial({map:_finish(zellijeTex(),16)});
  function iblock(w,h,d,mat,x,y,z){ const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat); m.position.set(x,y,z); m.castShadow=true; m.receiveShadow=true; ifritArena.add(m); return m; }
  const R=17;
  const floor=new THREE.Mesh(new THREE.BoxGeometry(R*2,0.4,R*2), floorMat); floor.position.set(0,-0.2,0); ifritArena.add(floor);
  [[0,-R,R*2+2,1.4],[0,R,R*2+2,1.4],[-R,0,1.4,R*2+2],[R,0,1.4,R*2+2]].forEach(([x,z,w,d])=>{
    iblock(w,4.4,d, wallMat, x,2.2,z); addBox(x,z,w,d);
  });
  const merlonSpacing=1.8;
  for(let x=-R;x<=R;x+=merlonSpacing){
    [-R,R].forEach(z=>{ const m=new THREE.Mesh(new THREE.BoxGeometry(0.9,0.9,0.9), merlonMat); m.position.set(x,4.85,z); ifritArena.add(m); });
  }
  for(let z=-R;z<=R;z+=merlonSpacing){
    [-R,R].forEach(x=>{ const m=new THREE.Mesh(new THREE.BoxGeometry(0.9,0.9,0.9), merlonMat); m.position.set(x,4.85,z); ifritArena.add(m); });
  }
  [[-R+2,-R+2],[R-2,-R+2],[-R+2,R-2],[R-2,R-2]].forEach(([x,z])=>{
    const stand=new THREE.Mesh(new THREE.CylinderGeometry(0.16,0.22,1.1,8), darkMat); stand.position.set(x,0.55,z); ifritArena.add(stand);
    const bowl=new THREE.Mesh(new THREE.CylinderGeometry(0.32,0.24,0.24,8), darkMat); bowl.position.set(x,1.15,z); ifritArena.add(bowl);
    const flame=new THREE.Mesh(new THREE.ConeGeometry(0.24,0.5,7), new THREE.MeshBasicMaterial({color:0xff8a2a,fog:false})); flame.position.set(x,1.5,z); ifritArena.add(flame);
    const light=new THREE.PointLight(0xff8a2a,1.1,9); light.position.set(x,1.6,z); ifritArena.add(light);
  });
  // cover in the courtyard, same broad/tall logic as the Colosseum's coverWall (the boss fires fast at
  // chest height) — just two, so the fire-meteor telegraph (the boss's other tool) still has room to punish camping
  function courtyardCover(x,z,w,rot){
    const wall=new THREE.Group(); wall.position.set(x,0,z); wall.rotation.y=rot||0; ifritArena.add(wall);
    const main=new THREE.Mesh(new THREE.BoxGeometry(w,3.2,0.7), wallMat); main.position.set(0,1.6,0); wall.add(main);
    addBox(x,z,w,0.9); // axis-aligned approximation — small rotation (±0.25 rad), same approach the Colosseum's coverWall main panel uses
  }
  courtyardCover(-5,9,4.6,0.25); courtyardCover(5,9,4.6,-0.25);
  ifritArena.add(new THREE.AmbientLight(0xffb87a, 0.5));
})();

addTarget = colliders;   // back to overworld for anything built later
```

- [ ] **Step 3: Add `enterIfritArena()`**

Find `enterColosseumArena()`'s closing brace (~line 4107):

```js
function enterColosseumArena(){
  clearWorldGroups();
  scene.add(colosseumArena);
  sky.visible = true;
  activeColliders = colosseumColliders;
  activeHeightZones = heightZonesOriginal;
  scene.background.set(0x8fd6f2); scene.fog.color.set(0xd8c4a0); scene.fog.near=45; scene.fog.far=200; // warm daylit arena
  hemi.intensity=0.9; hemi.color.set(0xffe6c0); hemi.groundColor.set(0x6a5030);
  sun.intensity=1.0; fill.intensity=0.25; fill.color.set(0xffd8a0);
  camera.position.set(0,1.7,17); yaw=targetYaw=0; pitch=targetPitch=0; vel.set(0,0,0); playerHeight=0; stuckTimer=0;
}
```

Insert a new function right after it:

```js
function enterIfritArena(){
  clearWorldGroups();
  scene.add(ifritArena);
  sky.visible = true;
  activeColliders = ifritColliders;
  activeHeightZones = heightZonesOriginal;
  scene.background.set(0x8a4a2e); scene.fog.color.set(0xa85a34); scene.fog.near=22; scene.fog.far=90; // warm dusk, fire-lit
  hemi.intensity=0.55; hemi.color.set(0xffb87a); hemi.groundColor.set(0x3a2414);
  sun.intensity=0.5; fill.intensity=0.3; fill.color.set(0xff8a4a);
  camera.position.set(0,1.7,14); yaw=targetYaw=0; pitch=targetPitch=0; vel.set(0,0,0); playerHeight=0; stuckTimer=0;
}
```

**IMPORTANT:** like Task 2's `enterIslamicWorld()`, `clearWorldGroups()` doesn't know about `ifritArena` yet — that's fixed in Task 4.

- [ ] **Step 4: Add the `bossNum===4` branch to `spawnBossFight()`**

Find (~line 4443-4462):

```js
function spawnBossFight(){
  clearBots();
  bossNum++;
  bossActive=true;
  // Boss I = Sandstone Colossus (pyramid dungeon); Boss II = Lernaean Hydra (open-air marsh arena);
  // Boss III = Colosseum Champion (amphitheatre arena). Each swaps in its own arena world.
  let skin, col, hp, scale, speed, label;
  if(bossNum===1){
    enterDungeon();
    skin='colossus'; col=0xc9a671; hp=1450; scale=3.1; speed=1.5; label='BOSS I';
  } else if(bossNum===2){
    enterHydraArena();
    skin='hydra'; col=0x35502e; hp=1750; scale=2.4; speed=1.7; label='BOSS II';
  } else {
    enterColosseumArena();
    skin='champion'; col=0x8a9299; hp=2100; scale=2.3; speed=2.1; label='BOSS III';
  }
```

Replace with:

```js
function spawnBossFight(){
  clearBots();
  bossNum++;
  bossActive=true;
  // Boss I = Sandstone Colossus (pyramid dungeon); Boss II = Lernaean Hydra (open-air marsh arena);
  // Boss III = Colosseum Champion (amphitheatre arena); Boss IV = Ifrit King (Citadel courtyard, the
  // current final boss). Each swaps in its own arena world.
  let skin, col, hp, scale, speed, label;
  if(bossNum===1){
    enterDungeon();
    skin='colossus'; col=0xc9a671; hp=1450; scale=3.1; speed=1.5; label='BOSS I';
  } else if(bossNum===2){
    enterHydraArena();
    skin='hydra'; col=0x35502e; hp=1750; scale=2.4; speed=1.7; label='BOSS II';
  } else if(bossNum===3){
    enterColosseumArena();
    skin='champion'; col=0x8a9299; hp=2100; scale=2.3; speed=2.1; label='BOSS III';
  } else {
    enterIfritArena();
    skin='ifritking'; col=0xc93a14; hp=2450; scale=2.0; speed=1.8; label='BOSS IV';
  }
```

- [ ] **Step 5: Add the fire-meteor VFX system**

Find `spawnQuakeEffect()`'s closing brace (~line 4878):

```js
  const light = new THREE.PointLight(0xd8b982, 2.4, 14); light.position.y = 1; grp.add(light);
  quakeEffects.push({grp, cracks, debris, dustMat, dust, light, t:0, dur:1.1});
}
```

Insert a new effect system right after it:

```js
// Ifrit King fire meteor: a telegraph ring grows/pulses at the target point for `impactAt` seconds (the
// player's real dodge window), then a burst deals AOE damage if they're still standing in it. Modeled on
// spawnQuakeEffect()'s timed-array-of-effects pattern.
const fireMeteors = [];
function spawnFireMeteor(x,z){
  const grp = new THREE.Group(); grp.position.set(x,0.05,z); scene.add(grp);
  const ringMat = new THREE.MeshBasicMaterial({color:0xff4a1a, transparent:true, opacity:0.85, fog:false, side:THREE.DoubleSide});
  const ring = new THREE.Mesh(new THREE.RingGeometry(1.6,2.0,20), ringMat); ring.rotation.x=-Math.PI/2; grp.add(ring);
  const fillMat = new THREE.MeshBasicMaterial({color:0xff8a2a, transparent:true, opacity:0.3, fog:false, side:THREE.DoubleSide});
  const fill = new THREE.Mesh(new THREE.CircleGeometry(2.0,20), fillMat); fill.rotation.x=-Math.PI/2; fill.position.y=0.01; grp.add(fill);
  fireMeteors.push({grp, ring, ringMat, fillMat, x, z, t:0, impactAt:0.9, dur:1.5, impacted:false});
}
```

Find the end of the quake-effects per-frame update loop (~line 5118-5119):

```js
    if(s>=1){ scene.remove(q.grp); quakeEffects.splice(i,1); }
  }
```

Insert the fire-meteor update loop right after that closing `}`:

```js
    if(s>=1){ scene.remove(q.grp); quakeEffects.splice(i,1); }
  }

  // ----- fire meteors (Ifrit King): telegraph ring grows/pulses, then a burst deals AOE damage if the
  // player is still standing in it — the dodge window IS the telegraph duration -----
  for(let i=fireMeteors.length-1;i>=0;i--){
    const m=fireMeteors[i]; m.t+=dt;
    if(!m.impacted){
      const growT = Math.min(1, m.t/m.impactAt);
      m.ring.scale.setScalar(0.3+growT*0.7);
      m.ringMat.opacity = 0.5 + Math.sin(m.t*18)*0.35; // fast pulse reads as urgent, not just growing
      if(m.t >= m.impactAt){
        m.impacted = true;
        const distToImpact = Math.hypot(camera.position.x-m.x, camera.position.z-m.z);
        if(distToImpact < 2.0 && player.alive) damagePlayer(Math.round(24*(1-distToImpact/2.0*0.3)));
        shakeAmt = Math.max(shakeAmt, 0.25);
        SFX.explosion();
        m.fillMat.opacity = 0.9; m.fillMat.color.set(0xffd23a);
      }
    } else {
      const fadeT = Math.min(1, (m.t-m.impactAt)/(m.dur-m.impactAt));
      m.ringMat.opacity = 0.6*(1-fadeT);
      m.fillMat.opacity = 0.9*(1-fadeT);
      m.grp.scale.setScalar(1+fadeT*1.5);
    }
    if(m.t >= m.dur){ scene.remove(m.grp); fireMeteors.splice(i,1); }
  }
```

- [ ] **Step 6: Add the Ifrit King's special-ability trigger**

Find the Colosseum Champion's tiger-release block (~line 5324-5334):

```js
    // Colosseum Champion (Boss III): when badly wounded (≤25% HP), looses TWO tigers — once only
    if(b.boss && b.skin==='champion' && player.alive && !b.tigersReleased && b.hp <= b.maxHp*0.25){
      b.tigersReleased = true;
      [-1,1].forEach(s=>{
        const sx = Math.max(-18, Math.min(18, b.mesh.position.x + s*4));
        const sz = Math.max(-18, Math.min(14, b.mesh.position.z + 2));
        spawnBot(sx, sz, 0xd9832a, [sx-2,0,sz],[sx+2,0,sz], 'knife', {skin:'tiger', hp:200, diff:1.0, speed:1.95, scale:1.15});
      });
      SFX.boss();
      setBanner('⚠ The Champion looses two tigers!'); setTimeout(()=>{ if(bossActive) setBanner(''); },1800);
    }
```

Insert a new block right after it:

```js
    // Ifrit King (Boss IV): periodically calls down a telegraphed fire meteor at the player's CURRENT
    // position — a ranged, dodge-driven hazard, distinct from the Colossus's proximity quake (no telegraph,
    // can't be dodged by movement alone) and the Champion's one-time add-summon above.
    if(b.boss && b.skin==='ifritking' && player.alive){
      b.meteorCd = b.meteorCd===undefined ? 4 : b.meteorCd - dt;
      if(b.meteorCd <= 0 && distToPlayer < 26){
        b.meteorCd = 7 + Math.random()*2;
        spawnFireMeteor(camera.position.x, camera.position.z);
      }
    }
```

- [ ] **Step 7: Add the wave-12 boss trigger in `onAllDead()`**

Find (~line 4515-4516):

```js
  if(waveIdx===2 || waveIdx===5 || waveIdx===8){ pending='boss'; betweenTimer=2.2;
    setBanner(waveIdx===5?'The Lernaean Hydra rises from the marsh…':waveIdx===8?'The Champion of the arena strides forth…':'A boss awaits below…'); }
```

Replace with:

```js
  if(waveIdx===2 || waveIdx===5 || waveIdx===8 || waveIdx===11){ pending='boss'; betweenTimer=2.2;
    setBanner(waveIdx===5?'The Lernaean Hydra rises from the marsh…':waveIdx===8?'The Champion of the arena strides forth…':waveIdx===11?'The Ifrit King rises from the flame…':'A boss awaits below…'); }
```

- [ ] **Step 8: Manually verify the boss fight**

Refresh, start the game, press `H` to jump to Cairo (wave 10, `bossNum=3`), press `L` repeatedly to clear waves 10, 11, 12. Confirm:
- After wave 12 clears, the banner "The Ifrit King rises from the flame…" shows and the fight transitions into the Citadel courtyard (`enterIfritArena()` fires — note the overworld map will still be in the scene alongside it until Task 4's `clearWorldGroups()` fix; that's expected here).
- The Ifrit King model renders without errors, boss HP bar shows.
- Fire-meteor telegraph rings appear periodically at your position, pulse, then detonate — confirm you can dodge out in time and confirm standing in one at impact damages you.
- Killing the boss (via `L`) doesn't yet do anything special beyond the existing `bossActive=false` cleanup — the actual victory routing is Task 4.

- [ ] **Step 9: Commit**

```bash
git add index.html
git commit -m "$(cat <<'EOF'
Add Ifrit King (Boss IV): model, Citadel courtyard arena, fire-meteor attack

Wires the wave-12 boss trigger and spawnBossFight()'s bossNum===4 branch.
Not yet reachable through normal Roman-victory play, and clearWorldGroups()
still doesn't know about islamicOverworld/ifritArena — both fixed in the
next task, which is also where the actual campaign-ending dead-end bug
gets fixed.
EOF
)"
```

---

### Task 4: Chain the full campaign together (fixes the reported dead-end bug)

**Files:**
- Modify: `index.html` — `clearWorldGroups()` (~line 1220), `onAllDead()`'s boss-victory branch (~line 4483-4501), `respawnPlayer()` (~line 4916-4923)

**Interfaces:**
- Consumes: everything from Tasks 1-3 (`islamicOverworld`, `ifritArena`, `enterIslamicWorld()`, `spawnBossFight()`'s `bossNum===4` branch).

- [ ] **Step 1: Register the new groups in `clearWorldGroups()`**

Find (~line 1220):

```js
function clearWorldGroups(){
  [pyramidOverworld, greekOverworld, romanOverworld, pyramidDungeon, greekDungeon, nileWorld, hydraArena, colosseumArena].forEach(g=>{ if(g.parent) scene.remove(g); });
}
```

Replace with:

```js
function clearWorldGroups(){
  [pyramidOverworld, greekOverworld, romanOverworld, islamicOverworld, pyramidDungeon, greekDungeon, nileWorld, hydraArena, colosseumArena, ifritArena].forEach(g=>{ if(g.parent) scene.remove(g); });
}
```

- [ ] **Step 2: Fix the actual bug — Roman Boss III routes into Cairo instead of ending the game**

Find (~line 4483-4501):

```js
  if(bossActive){
    // boss defeated
    bossActive=false; showBossBar(false);
    // used to set gameWon=true + exitDungeon() here and just show "YOU WIN" — but gameWon disables firing
    // entirely and turns the next pointer-lock click into a full restart, so there was nowhere to actually
    // go afterward. Ammit falling now leads into the Roman map instead (playable, not "game over") — wave 7
    // (the first Roman wave) spawns after the usual between-wave pause, same as any other era transition.
    if(bossNum===2){
      // Hydra down → cross into the Roman frontier (wave 7)
      enterRomanWorld('🏆 The Hydra falls! The Roman frontier awaits…');
      currentEra=2; waveIdx=ERA_START_WAVE[2]; pending='wave'; betweenTimer=2.4;
      return;
    }
    if(bossNum>=3){
      // Colosseum Champion down → the campaign's final boss; victory. gameWon disables firing and turns the
      // next pointer-lock click into a fresh run (the intended "you beat it" end state).
      gameWon=true;
      setBanner('🏆 THE CHAMPION FALLS — you have conquered the arena! 🏛');
      return;
    }
```

Replace with:

```js
  if(bossActive){
    // boss defeated
    bossActive=false; showBossBar(false);
    // used to set gameWon=true + exitDungeon() here and just show "YOU WIN" — but gameWon disables firing
    // entirely and turns the next pointer-lock click into a full restart, so there was nowhere to actually
    // go afterward. Each mid-campaign boss falling leads into the next era's map instead (playable, not
    // "game over"); only the actual final boss (currently the Ifrit King) ends the run.
    if(bossNum===2){
      // Hydra down → cross into the Roman frontier (wave 7)
      enterRomanWorld('🏆 The Hydra falls! The Roman frontier awaits…');
      currentEra=2; waveIdx=ERA_START_WAVE[2]; pending='wave'; betweenTimer=2.4;
      return;
    }
    if(bossNum===3){
      // Colosseum Champion down → cross into Mamluk Cairo (wave 10) — this used to just set gameWon and
      // strand the player in the empty Colosseum arena with nowhere to go; that was the reported bug.
      enterIslamicWorld('🏆 The Champion falls! The gates of Cairo open…');
      currentEra=3; waveIdx=ERA_START_WAVE[3]; pending='wave'; betweenTimer=2.4;
      return;
    }
    if(bossNum>=4){
      // Ifrit King down → the campaign's final boss; victory. gameWon disables firing and turns the next
      // pointer-lock click into a fresh run (the intended "you beat it" end state).
      gameWon=true;
      setBanner('🏆 THE IFRIT KING FALLS — you have conquered Cairo! 🕌');
      return;
    }
```

- [ ] **Step 3: Extend `respawnPlayer()` for era-3 deaths**

Find (~line 4916-4923):

```js
  bossNum = currentEra; // keep credit for any boss(es) already defeated in earlier eras
  // exitDungeon() only knows the pyramid/greek pairing (dungeonWasPyramid) — there's no Roman dungeon yet,
  // so era 2 gets its own reset here instead of routing through that
  if(currentEra >= 2) enterRomanWorld('💀 back to Wave 7');
  else exitDungeon();
  waveIdx = ERA_START_WAVE[currentEra];
  clearBots(); spawnWave(waveIdx);
  if(currentEra < 2){ setBanner('💀 back to Wave '+(waveIdx+1)); setTimeout(()=>{ if(!gameWon) setBanner(''); },1500); }
```

Replace with:

```js
  bossNum = currentEra; // keep credit for any boss(es) already defeated in earlier eras
  // exitDungeon() only knows the pyramid/greek pairing (dungeonWasPyramid) — there's no Roman/Islamic
  // dungeon, so eras 2 and 3 each get their own reset here instead of routing through that
  if(currentEra >= 3) enterIslamicWorld('💀 back to Wave 10');
  else if(currentEra >= 2) enterRomanWorld('💀 back to Wave 7');
  else exitDungeon();
  waveIdx = ERA_START_WAVE[currentEra];
  clearBots(); spawnWave(waveIdx);
  if(currentEra < 2){ setBanner('💀 back to Wave '+(waveIdx+1)); setTimeout(()=>{ if(!gameWon) setBanner(''); },1500); }
```

- [ ] **Step 4: Manually verify the full campaign chain end-to-end**

This is the real regression test for the reported bug. Refresh the page and play through for real (no debug keys) — or use `L` to speed-clear waves and `H`/console shortcuts to skip to specific points, but confirm at minimum:

1. Beat Boss III (Colosseum Champion) — either play there or jump via console: `bossNum=2; spawnBossFight();` then `L` to kill it. Confirm you now land in the **Cairo overworld** with the Islamic loadout equipped and wave 10 incoming — **not** stuck in the empty Colosseum arena. This is the exact bug from the screenshot; confirm it's gone.
2. Clear waves 10-12, confirm Boss IV (Ifrit King) triggers correctly in the Citadel courtyard.
3. Beat the Ifrit King — confirm the "🏆 THE IFRIT KING FALLS" banner shows and firing is disabled (the real end state).
4. Separately, test dying mid-Islamic-era (e.g. let an enemy kill you during wave 10): confirm you respawn back at wave 10 in the Cairo map, not rolled back to an earlier era.
5. Confirm no two world groups are ever visible/overlapping at once at any transition (this was the exact "fused maps" bug `clearWorldGroups()` was written to prevent — see its comment).

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "$(cat <<'EOF'
Chain the Islamic era into the campaign, fixing the Roman victory dead-end

Roman's Boss III now transitions into Mamluk Cairo instead of stranding
the player in the empty Colosseum arena (the bug reported via playtest
screenshot). The Ifrit King (Boss IV) is now the actual final boss and
win condition. clearWorldGroups() and respawnPlayer() both updated to
know about the new era.
EOF
)"
```
