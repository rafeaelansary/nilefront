# China, part 1: the weapons loadout — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the three-weapon `chinaWeapons` loadout (Zhanmadao, Repeating Crossbow, Thunderclap Bomb) — buildable, fireable, reloadable and switchable — before any China world exists to fire them in.

**Architecture:** Three weapon-builder functions in the same shape every existing loadout uses (`makeDaneAxe()`, `makeCrossbow()`, `makeNaftPot()`, etc.): a `THREE.Group` of primitive meshes assembled with the shared `part()`/`voxMat()`/`metalMatP()` helpers, a single `g.userData` object carrying its stats, held out of `makeXWeapon()`. No new weapon *system* — `armourPierce`, `cleaveArc`, `grenade`/`splashDamage`/`splashRadius`, `auto`/`magSize`/`reloadTime` all already exist and are read by `fire()`/`reloadWeapon()`/`damageBot()`.

**Tech Stack:** three.js r128 via CDN, one self-contained `index.html`, no build step. Verification is the repo's headless harness: `tools/audit/bugcheck.py` (weapon exercise + screen-fit), `tools/audit/audit.py`, `tools/audit/fullcheck.py`, all running the real game script inside py_mini_racer against `tools/audit/three_stub.js`.

**Spec:** `docs/superpowers/specs/2026-09-20-china-design.md` (Weapons section; build-order step 1)

## Scope note

The spec covers the whole destination: two legs, two rosters, two bosses. This plan covers
**only the weapons** — nothing hostile exists yet to use them against, and no China world
exists yet to enter. It is a complete, playable, reviewable deliverable on its own: every
weapon builds, fires, reloads, scopes and survives a weapon switch under the existing
harness, and is visible in the game's weapon list. The Xiangyang world gets its own plan
next, exactly as the Fjord's world got its own plan ahead of its fight.

## Global Constraints

- Everything lives in `/Users/rafea/src/blockfront/index.html`. No new source files besides the one test file below, no build step.
- three.js r128 only. No new CDN dependencies.
- Follow the established weapon shape exactly: a `THREE.Group`, meshes built with `part(group,w,h,d,mat,x,y,z)` (or raw `THREE.Mesh` where a segment needs its own rotation), materials from `voxMat()`/`metalMatP()`/`_finish()`, and a single `g.userData` object with `muzzleZ`, `muzzleY`, `pos` (a `THREE.Vector3`), `recoil`, `name`, plus whatever subset of `damage`/`fireRate`/`auto`/`spread`/`tracer`/`magSize`/`ammo`/`reloadTime`/`reloading`/`reloadT`/`melee`/`range`/`armourPierce`/`cleaveArc`/`cleaveRays`/`grenade`/`splashDamage`/`splashRadius`/`sfx` its own behavior needs (see `makeDaneAxe()`, `makeCrossbow()`, `makeNaftPot()` for the reference shape of each).
- Never write two meshes sharing a face plane (alternate depth/width between neighbouring segments) — this is what `fullcheck.py`'s near-coplanar check and `audit.py`'s coplanarity check both hunt for, and it is the single most common defect every existing weapon's comments call out.
- Commit after every task. Commit messages end with `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `index.html` — after `makeThrowingSeax()` and `const swedenWeapons = [...]` (~line 15728) | `// ===== CHINA LOADOUT =====` section: `makeZhanmadao()`, `makeRepeatingCrossbow()`, `makeThunderclapBomb()`, `const chinaWeapons = [...]` | Modify |
| `index.html` — the `gunGroup` build-up (~line 15731) | add `.concat(chinaWeapons)` | Modify |
| `tools/audit/bugcheck.py` — the weapon-exercise `sets` array (~line 194) | add `chinaWeapons` | Modify |
| `tools/audit/audit.py` — `__loadouts` list | add `chinaWeapons` | Modify |
| `tools/audit/chinacheck.py` | China-specific checks, starting with the loadout. New file — the two legs' world/fight checks land in this same file later. | Create |

---

### Task 1: the three weapons and the loadout array

**Files:**
- Modify: `index.html`
- Modify: `tools/audit/bugcheck.py`
- Modify: `tools/audit/audit.py`
- Test: `tools/audit/chinacheck.py` (create)

**Interfaces:**
- Consumes: `part`, `voxMat`, `metalMatP`, `_finish`, `logTex` (existing helpers); `gunGroup`, `weapons` (existing globals).
- Produces: `chinaWeapons` (Array of 3 `THREE.Group`, order `[Zhanmadao, Repeating Crossbow, Thunderclap Bomb]`) — the next plan's `enterXiangyangWorld()` sets `weapons = chinaWeapons`.

- [ ] **Step 1: Write the failing test**

Create `tools/audit/chinacheck.py`:

```python
#!/usr/bin/env python3
"""China: the weapons loadout, then Xiangyang and Yamen as they land."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bugcheck import run, show

ok = True

ok &= show("the China loadout is three weapons, each with a complete userData block", run("""
  if(typeof chinaWeapons === 'undefined') throw new Error('chinaWeapons is not defined');
  if(chinaWeapons.length !== 3) throw new Error('expected 3 weapons, got '+chinaWeapons.length);
  var names = chinaWeapons.map(function(w){ return w.userData.name; });
  ['Zhanmadao','Repeating Crossbow','Thunderclap Bomb'].forEach(function(n){
    if(names.indexOf(n) < 0) throw new Error(n+' is missing from chinaWeapons (have: '+names.join(', ')+')');
  });
  chinaWeapons.forEach(function(w){
    var u = w.userData;
    if(!u.pos || !(u.pos.isVector3)) throw new Error(u.name+': userData.pos is not a THREE.Vector3');
    if(typeof u.muzzleZ !== 'number') throw new Error(u.name+': no muzzleZ');
    if(typeof u.recoil !== 'number') throw new Error(u.name+': no recoil');
    if(!u.melee && !u.grenade && typeof u.magSize !== 'number')
      throw new Error(u.name+': a non-melee, non-grenade weapon needs a magSize');
  });
  // the Zhanmadao is the armour-answering melee weapon, the same role the Dane Axe plays
  var dao = chinaWeapons[0].userData;
  if(!dao.melee) throw new Error('the Zhanmadao is not melee');
  if(!dao.armourPierce || dao.armourPierce < 1.5) throw new Error('the Zhanmadao has no real armourPierce');
  // the crossbow is the rapid one: distinct from every single-shot bow/crossbow already in the game
  var xbow = chinaWeapons[1].userData;
  if(!xbow.auto) throw new Error('the Repeating Crossbow is not auto-fire');
  if(!(xbow.magSize >= 8)) throw new Error('the Repeating Crossbow magazine is only '+xbow.magSize+', too small to read as repeating');
  // the bomb is a grenade, the same mechanism the Naft Pot and Grenade Launcher already use
  var bomb = chinaWeapons[2].userData;
  if(!bomb.grenade) throw new Error('the Thunderclap Bomb does not use the grenade mechanic');
  if(!(bomb.splashRadius > 0)) throw new Error('the Thunderclap Bomb has no splashRadius');
  return names.join(', ')+' -- all present with complete userData';
"""))

sys.exit(0 if ok else 1)
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python3 tools/audit/chinacheck.py`
Expected: `[BUG] ... Error: chinaWeapons is not defined`

- [ ] **Step 3: Write the Zhanmadao**

In `index.html`, immediately after `const swedenWeapons = [makeDaneAxe(), makeHunnishBow(), makeThrowingSeax()];`:

```js
// ===================== CHINA LOADOUT (Yuan conquest of Song China, 1267-1279) =====================
// Three weapons answering the two legs' own escalation: a heavy armour-breaking saber for Xiangyang's
// garrison, a rapid-fire crossbow that is nothing like the Qaws' single heavy bolt, and a thrown
// gunpowder bomb that is Yamen's whole battle in miniature before Yamen is even built.

// ZHANMADAO — the "horse-chopping saber": a long, broad, single-edged two-handed blade. Built on the
// Dane Axe's own two-hander shape (long haft, held across the body, canted off the centre line so the
// crosshair stays clear) but with a SWORD's silhouette in place of an axe's crescent head — a straight
// spine and a slowly widening edge, flaring hardest in the last third the way a real horse-chopping
// saber's does, rather than a uniform-width blade.
function makeZhanmadao(){
  const g=new THREE.Group();
  const haftMat = new THREE.MeshLambertMaterial({map:_finish(logTex(),1)});
  const haftDk  = voxMat(0x3a2a1a,{noise:14});
  const steel   = metalMatP(0xb8c0c8,120,0xffffff);
  const steelDk = metalMatP(0x767d86,70,0xc8d0d8);
  const bronze  = metalMatP(0xad8730,85,0xfff2c8);
  const leather = voxMat(0x2c221a,{noise:14});
  const ab=(w,h,d,mat,x,y,z)=>{ const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat); m.position.set(x,y,z); g.add(m); return m; };
  const acy=(rt,rb,h,seg,mat,x,y,z)=>{ const m=new THREE.Mesh(new THREE.CylinderGeometry(rt,rb,h,seg),mat); m.position.set(x,y,z); g.add(m); return m; };
  // ---- the long haft, round in section like the Dane Axe's ----
  acy(0.026,0.029,0.62,10, haftMat, 0,0.02,0);
  [[-0.10,0.16],[0.14,0.14]].forEach(([hy,hh])=>{
    acy(0.031,0.031,hh,10, leather, 0,hy,0);
    acy(0.033,0.033,0.012,10, haftDk, 0,hy+hh/2,0);
    acy(0.033,0.033,0.012,10, haftDk, 0,hy-hh/2,0);
  });
  acy(0.035,0.032,0.06,10, bronze, 0,-0.34,0);        // butt cap
  // ---- guard: a simple disc, not a crossguard -- a dao's hilt is a saber's, not a longsword's ----
  acy(0.075,0.075,0.022,10, bronze, 0,0.335,0);
  // ---- the blade: straight spine down the near side, edge flaring wide in the last third ----
  // Built as a chain of segments, each its own mesh so neighbours can alternate depth (the standing
  // rule against sharing a face plane) -- N=9, width held flat for the first five then flaring hard
  // for the last four, which is the "horse-chopping" silhouette: most of the mass is out at the tip.
  const N=9;
  let by=0.36;
  for(let i=0;i<N;i++){
    const u=i/(N-1);
    const flare = u<0.45 ? 0.0 : (u-0.45)/0.55;         // 0 for the first ~half, ramps after
    const w = 0.052 + flare*flare*0.075;                // the blade widens toward the point
    const len = 0.11;
    const thick = i%2 ? 0.020 : 0.026;
    ab(w, len, thick, i%2?steel:steelDk, w*0.5-0.046, by+len/2, 0);   // spine held near x=-0.046, edge grows +x
    by += len;
  }
  // the bright edge strip, proud of the blade's +x face along its whole run
  by=0.36;
  for(let i=0;i<N;i++){
    const u=i/(N-1);
    const flare = u<0.45 ? 0.0 : (u-0.45)/0.55;
    const w = 0.052 + flare*flare*0.075;
    const len=0.11;
    ab(0.014, len, i%2?0.022:0.030, steel, w-0.046+0.009, by+len/2, 0);
    by += len;
  }
  // the point: a continuation of the last segment's own flare, angled in rather than squared off
  const tip=new THREE.Mesh(new THREE.ConeGeometry(0.09,0.16,4), steelDk);
  tip.rotation.z = -Math.PI/2; tip.rotation.y = Math.PI/4;
  tip.position.set(0.06, by+0.03, 0); g.add(tip);
  // Held big and canted, the same solved shape the Dane Axe uses: right edge inside the frame, top
  // inside the frame, the haft's own butt leaving the BOTTOM of the frame so it reads as held rather
  // than floating. Tuned against this model's own silhouette once it is on screen (see chinacheck.py's
  // screen-fit assertion and the "look at it" step below) -- these starting numbers are the Dane Axe's
  // own solved values, not yet re-solved for this blade's different mass distribution.
  g.scale.setScalar(1.15);
  g.rotation.z = -0.40; g.rotation.y = 0.30; g.rotation.x = 0.08;
  g.userData={muzzleZ:0,muzzleY:0,pos:new THREE.Vector3(0.22,-0.42,-0.74),recoil:0.22,name:'Zhanmadao',
    restRot:{x:0.08,y:0.30,z:-0.40},
    melee:true, range:3.0, damage:180, fireRate:0.90, sfx:'axeSwing',
    // the same "smashes armour" role the Dane Axe plays against the draugr and the troll, now against
    // Xiangyang's armoured garrison guard
    armourPierce:2.0,
    cleaveArc:1.10, cleaveRays:7,
    swingAnim:true, swingT:99};
  return g;
}
```

- [ ] **Step 4: Write the Repeating Crossbow**

Immediately after `makeZhanmadao()`:

```js
// REPEATING CROSSBOW (Zhuge Nu) — the historical multi-bolt magazine crossbow: a gravity-fed box of
// bolts over the tiller, worked by a lever that both draws the string and drops the next bolt into
// the groove. Built on the Qaws' tiller/lath/string shape (see makeCrossbow()) but with that magazine
// box added and the stats inverted -- fast and weak instead of slow and heavy -- so it reads as a
// completely different weapon despite the shared silhouette family.
function makeRepeatingCrossbow(){
  const g=new THREE.Group();
  const wood=metalMatP(0x6a4522,28,0x2e2012), woodDark=metalMatP(0x462c16,22,0x1c1208);
  const steel=metalMatP(0x9aa2aa,85,0xe8eef2), dark=voxMat(0x241e1a,{noise:10});
  const bambooM=voxMat(0xc0a860,{noise:10}), bambooDk=voxMat(0x8a7440,{noise:10});
  const cordMat=new THREE.MeshBasicMaterial({color:0xe0d6c0,fog:false});
  // ---- tiller ----
  part(g,0.07,0.12,0.22,wood,0,-0.015,0.24);
  part(g,0.062,0.088,0.70,wood,0,0.005,-0.05);
  part(g,0.11,0.06,0.13,woodDark,0,0.005,-0.44);
  // ---- the magazine box: the feature that names the weapon. Sits ON TOP of the tiller, open at the
  // bottom over the groove so gravity drops one bolt at a time -- built as a bamboo-slat hopper, wider
  // at the top than the base so it visibly holds a stack rather than reading as a solid block.
  part(g,0.09,0.09,0.34, bambooM, 0,0.135,-0.08);
  part(g,0.075,0.09,0.30, bambooDk, 0,0.135,-0.08);      // inset face, so the hopper reads as a box with walls
  for(let i=0;i<5;i++) part(g,0.006,0.088,0.30, bambooDk, -0.044+i*0.022,0.135,-0.08);  // the slats
  part(g,0.10,0.02,0.36, wood, 0,0.185,-0.08);           // its lid
  // the lever, hinged at the rear of the box -- one stroke both draws the string and re-cocks the box
  part(g,0.02,0.16,0.03, dark, 0,0.10,0.14).rotation.x=-0.3;
  // ---- rail groove + a bolt sitting in it (shorter and lighter than the Qaws' single heavy bolt) ----
  part(g,0.024,0.020,0.66,dark,0,0.052,-0.06);
  part(g,0.013,0.013,0.30,woodDark,0,0.066,-0.22);
  const bhead=new THREE.Mesh(new THREE.ConeGeometry(0.015,0.055,4), steel); bhead.rotation.x=-1.5708; bhead.position.set(0,0.066,-0.38); g.add(bhead);
  // ---- nut / lock housing ----
  part(g,0.07,0.05,0.085,steel,0,0.045,-0.02);
  // ---- recurved lath, the same chained-segment construction the Qaws uses (each segment positioned
  // along the previous segment's own rotated direction, never by a naive linear x-step) ----
  const LZ=-0.38;
  [-1,1].forEach(side=>{
    let lx=0, lz=LZ, phi=0.10;
    [{len:0.13,t:0.028},{len:0.12,t:0.022},{len:0.10,t:0.017}].forEach((s,i)=>{
      const dx=Math.cos(phi), dz=-Math.sin(phi);
      const cx=lx+side*dx*s.len/2, cz=lz+dz*s.len/2;
      const seg=new THREE.Mesh(new THREE.BoxGeometry(s.len,s.t,s.t), i===2?dark:steel);
      seg.position.set(cx,0.012,cz);
      seg.rotation.y = side>0 ? phi : (Math.PI - phi);
      g.add(seg);
      lx += side*dx*s.len; lz += dz*s.len; phi += 0.26;
    });
    const tipX=lx, tipZ=lz, nutZ=-0.06;
    const len=Math.hypot(tipX, nutZ-tipZ);
    const str=new THREE.Mesh(new THREE.BoxGeometry(len,0.008,0.008), cordMat);
    str.position.set(tipX/2, 0.012, (tipZ+nutZ)/2);
    str.rotation.y = Math.atan2(tipZ-nutZ, -tipX);
    g.add(str);
  });
  // ---- trigger + stirrup ----
  part(g,0.026,0.08,0.028,steel,0,-0.085,0.1).rotation.x=-0.18;
  part(g,0.016,0.10,0.016,steel,-0.045,-0.055,-0.46);
  part(g,0.016,0.10,0.016,steel, 0.045,-0.055,-0.46);
  part(g,0.106,0.016,0.016,steel,0,-0.105,-0.46);

  g.userData={muzzleZ:-0.50,muzzleY:0.066,pos:new THREE.Vector3(0.23,-0.22,-0.38),recoil:0.06,name:'Repeating Crossbow',
    // fast and weak, the inverse of the Qaws (damage 156, fireRate 1.3, magSize 4): a stream of light
    // bolts rather than one heavy one -- distinct in FEEL from every other bow/crossbow/gun in the game,
    // all of which fire a single projectile at a time
    damage:34, fireRate:0.11, auto:true, spread:0.028, tracer:0xd8d0c0,
    magSize:12, ammo:12, reloadTime:1.7, reloading:false, reloadT:0};
  return g;
}
```

- [ ] **Step 5: Write the Thunderclap Bomb**

Immediately after `makeRepeatingCrossbow()`:

```js
// THUNDERCLAP BOMB (Zhen Tian Lei) — a thrown cast-iron gunpowder shell, on the exact grenade
// mechanism the Naft Pot and the Grenade Launcher already use (userData.grenade routes through
// launchGrenade()/explodeAt()). A ribbed cast-iron sphere and a twisted-paper fuse in place of the Naft
// Pot's clay vessel and burning wick -- a different era's incendiary, not a reskin of the same object.
function makeThunderclapBomb(){
  const g=new THREE.Group();
  const iron=voxMat(0x2c2c2e,{noise:12}), ironDk=voxMat(0x18181a,{noise:10});
  const paper=voxMat(0xc8bc98,{noise:12}), leather=voxMat(0x4a3320,{noise:14});
  const PZ=-0.10, PY=-0.03;
  // the shell: a sphere, segmented by cast ribs -- the historical Zhen Tian Lei was cast in a mould
  // with a visible seam and ridge, not a smooth ball
  const shell=new THREE.Mesh(new THREE.SphereGeometry(0.115,10,8), iron); shell.position.set(0,PY,PZ); g.add(shell);
  [[-0.04,0.113],[0.0,0.117],[0.04,0.113]].forEach(([dy,r])=>{
    const band=new THREE.Mesh(new THREE.CylinderGeometry(r,r,0.014,10), ironDk); band.position.set(0,PY+dy,PZ); g.add(band);
  });
  // the fuse housing at the top, and a twisted paper fuse coming out of it
  const neck=new THREE.Mesh(new THREE.CylinderGeometry(0.030,0.044,0.05,8), ironDk); neck.position.set(0,PY+0.125,PZ); g.add(neck);
  const fuse=new THREE.Mesh(new THREE.CylinderGeometry(0.010,0.014,0.09,6), paper); fuse.position.set(0,PY+0.19,PZ); fuse.rotation.z=0.18; g.add(fuse);
  const spark=new THREE.Mesh(new THREE.ConeGeometry(0.024,0.05,6), new THREE.MeshBasicMaterial({color:0xffb347,fog:false}));
  spark.position.set(0.012,PY+0.235,PZ); g.add(spark);
  const L=new THREE.PointLight(0xffb347,0.7,1.3); L.position.set(0.012,PY+0.235,PZ); g.add(L);
  // corded sling into the fist, the same physically-connected-handle shape the Naft Pot uses so the
  // hand has something real to hold rather than hovering beside the shell
  [-1,1].forEach(s=>{
    const cord=new THREE.Mesh(new THREE.BoxGeometry(0.013,0.19,0.013), leather);
    cord.position.set(s*0.070,PY-0.12,PZ+0.05); cord.rotation.x=-0.3; cord.rotation.z=s*-0.33; g.add(cord);
  });
  const knot=new THREE.Mesh(new THREE.BoxGeometry(0.16,0.085,0.14), leather); knot.position.set(0,PY-0.205,PZ+0.11); g.add(knot);
  const handle=new THREE.Mesh(new THREE.CylinderGeometry(0.026,0.026,0.15,8), leather); handle.position.set(0,PY-0.28,PZ+0.14); handle.rotation.x=0.35; g.add(handle);

  g.userData={muzzleZ:-0.26,muzzleY:0.1,pos:new THREE.Vector3(0.24,-0.24,-0.1),recoil:0.15,name:'Thunderclap Bomb',
    damage:0, splashDamage:190, splashRadius:4.6, fireRate:1.1, auto:false, spread:0.0, tracer:0xffb347, grenade:true,
    magSize:5, ammo:5, reloadTime:1.9, reloading:false, reloadT:0};
  return g;
}
const chinaWeapons = [makeZhanmadao(), makeRepeatingCrossbow(), makeThunderclapBomb()];
```

- [ ] **Step 6: Wire it into `gunGroup`**

In `index.html`, find (`grep -n "gunGroup.add(w)" index.html`):

```js
originalWeapons.concat(pyramidWeapons).concat(nileWeapons).concat(greekWeapons).concat(romanWeapons).concat(islamicWeapons).concat(mexicoWeapons).concat(aztecWeapons).concat(swedenWeapons).forEach(w=>{ w.visible=false; gunGroup.add(w); });
```

Change to:

```js
originalWeapons.concat(pyramidWeapons).concat(nileWeapons).concat(greekWeapons).concat(romanWeapons).concat(islamicWeapons).concat(mexicoWeapons).concat(aztecWeapons).concat(swedenWeapons).concat(chinaWeapons).forEach(w=>{ w.visible=false; gunGroup.add(w); });
```

- [ ] **Step 7: Register with the harness**

In `tools/audit/bugcheck.py`, in the weapon-exercise test (`grep -n "var sets=" tools/audit/bugcheck.py`):

```js
  var sets=[originalWeapons,pyramidWeapons,nileWeapons,greekWeapons,romanWeapons,
            islamicWeapons,mexicoWeapons,aztecWeapons,swedenWeapons,chinaWeapons];
```

Update the test's own label two lines above (currently reads `"fire / reload / scope / switch on all 23 weapons without throwing"` — the true count has drifted from this before; leave the string as `"fire / reload / scope / switch on every weapon without throwing"` so it stops needing to be hand-updated every time a loadout is added) and change the `n+' weapons exercised'` return, which already counts dynamically, is left as-is.

In `tools/audit/audit.py`, in the `EXPORTS` string's `__loadouts` block:

```js
['originalWeapons','pyramidWeapons','nileWeapons','greekWeapons','romanWeapons','islamicWeapons','mexicoWeapons','aztecWeapons','swedenWeapons','chinaWeapons'].forEach(function(n){
```

- [ ] **Step 8: Run the test and watch it pass**

Run: `python3 tools/audit/chinacheck.py`
Expected: `[ok ] the China loadout is three weapons, each with a complete userData block`

- [ ] **Step 9: Run the full harness**

Run: `python3 tools/audit/bugcheck.py`
Expected: every suite `[ok ]`, including `every weapon, every operation` (now exercising 3 more weapons — the reported count goes up by 3 from whatever it printed before this task).

Run: `python3 tools/audit/audit.py`
Expected: no new failures attributable to the three new weapons (ground contact and connectivity apply to actors, not weapons, but the run must still complete without a JS exception from the new code).

Run: `python3 tools/audit/fullcheck.py`
Expected: whole-game `problem group(s)` count does not increase (weapon meshes are checked for coplanarity as part of the exercise pass inside `bugcheck.py`, not `fullcheck.py`'s world sweep — this run is to confirm nothing else broke).

- [ ] **Step 10: Look at it, and tune**

Run: `python3 -m http.server 8000`, open `http://localhost:8000`, press START, open the console with `C,C`, and switch to each new weapon in turn (there is no `/tp` entry point yet, since no China world exists — cycle weapons with the scroll wheel/number keys from wherever you already are, or temporarily set `weapons = chinaWeapons; selectWeapon(0);` from the console to preview them).
Expected: each weapon sits in-frame with room around the crosshair, matching the same silhouette rules `makeDaneAxe()`'s comment documents (right edge inside the frame, top inside the frame, a melee weapon's haft leaving the bottom of the frame). Tune each weapon's `g.scale`/`g.rotation`/`pos` until it does; these are starting values carried over from the Dane Axe/Qaws/Naft Pot, not yet re-solved for these models' own proportions.

- [ ] **Step 11: Commit**

```bash
git add index.html tools/audit/bugcheck.py tools/audit/audit.py tools/audit/chinacheck.py
git commit -m "$(cat <<'EOF'
Add the China loadout: Zhanmadao, Repeating Crossbow, Thunderclap Bomb

Three weapons for the Xiangyang/Yamen destination, built on the exact shapes
the game already has rather than new mechanisms: the Zhanmadao is a two-hander
on the Dane Axe's own held/canted/armourPierce/cleaveArc shape with a sword's
silhouette instead of an axe's; the Repeating Crossbow inverts the Qaws' single
heavy bolt into fast, weak, auto-fire streams of light ones, with the
historical gravity-fed magazine box as its one new physical feature; the
Thunderclap Bomb is a cast-iron shell on the exact grenade mechanism the Naft
Pot and Grenade Launcher already use.

No China world exists yet -- this is buildable, fireable, reloadable and
switchable under the existing harness on its own, the same way the Fjord's
water went in before anything could fight on it.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## What this plan does NOT cover

Deliberately left to later plans, matching the spec's own build order:

- the Xiangyang world, its wall-breach mechanic, and its wave ladder
- the Xiangyang roster (infantry, crossbowman, the armoured elite) and its boss
- the Yamen world, reusing the Fjord's water system, and its fire mechanic
- the Yamen roster and its dragon-banner boss
- `CHINA_LEGS`, the `DESTINATIONS` entry, and hub/`/tp` wiring

Until those land, `chinaWeapons` exists and is fully tested but is not reachable from normal
play — nothing in `DESTINATIONS` points at it yet.
