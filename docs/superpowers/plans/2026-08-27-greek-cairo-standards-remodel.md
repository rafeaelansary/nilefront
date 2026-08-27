# Greek Cairo-Standards Remodel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the Greek era's map, enemies and weapons up to the "Cairo standard" the Cairo and Giza rebuilds established, and fix the ground-contact and walk-animation bugs affecting every boss in the game.

**Architecture:** NILEFRONT is a single self-contained `index.html` (~7,165 lines) with no build step. Each era's map is built by an IIFE that adds meshes to `scene`, after which everything currently parented to the scene is swept into a `THREE.Group` for that era. There is no test framework; this plan introduces one — a `py_mini_racer` harness at `tools/audit/` that executes the real script body against a stubbed THREE/DOM and reads back true world-space bounding boxes. Every task is gated on that harness.

**Tech Stack:** three.js r128 (CDN), vanilla ES2020, Web Audio API, canvas-generated textures. Harness: Python 3 + `py_mini_racer`.

**Spec:** `docs/superpowers/specs/2026-08-27-greek-cairo-standards-remodel-design.md`

## Global Constraints

- **Single file.** All game changes go in `/Users/rafea/src/blockfront/index.html`. No new JS files, no build step, no new runtime dependencies.
- **Branch:** `greek-cairo-standards-remodel`. Never commit to `main`. Never touch `gh-pages`.
- **New map geometry MUST be added inside the correct era's IIFE.** Each era ends with `scene.children.slice().forEach(...)` sweeping into a group. Geometry added outside its IIFE is swallowed by the wrong era's group or orphaned entirely — the exact bug `b85ac35` had to fix.
- **Colliders** register via `addBox(x, z, w, d)`, which appends to whatever `addTarget` currently points at. Greek's IIFE sets `addTarget = greekColliders`. Do not reassign `addTarget` inside a task.
- **No balance changes.** Every weapon's `userData` (damage, fireRate, magSize, spread, muzzleZ, muzzleY, pos, recoil, name, auto, tracer, melee, range, reloadTime) and every enemy's HP/speed/scale/diff stay exactly as they are.
- **Preserve rig contracts.** Every actor model must populate `userData.bodyMeshes` (array of every mesh — hit detection) and `userData.marker` (the through-wall sprite). Humanoid rigs additionally expose `userData.legL`, `userData.legR`, `userData.armR`, `userData.armL`.
- **Preserve skin strings.** `skin==='minotaur'` drives the front-block in `damageBot` (`index.html:6594`) and the capped turn rate (`index.html:7029`); `skin==='griffin'` with `weaponType==='griffin'`/`'javelin'` drives the ranged→melee flip; `skin==='medusa'` drives heavier melee damage.
- **Ground-contact tolerance:** `0.02` world units.
- **Texture canvases must be power-of-two** (16/32/64/128) so `_finish()`'s mipmapping stays legal in a WebGL1 context.

---

## File Structure

- `tools/audit/three_stub.js` — **create.** Stubbed THREE.js + DOM, sufficient to execute the game's script body headlessly and expose real world transforms.
- `tools/audit/audit.py` — **create.** Loads `index.html`, runs the three checks, prints a table, exits non-zero on failure.
- `tools/audit/README.md` — **create.** How to run it and what each check means.
- `index.html` — **modify** throughout. Regions, by current line number:
  - `:1318-1383` Hydra arena builder
  - `:1384-1487` Colosseum arena builder
  - `:442-660` texture builders (new Greek textures go here)
  - `:2294-2862` Greek overworld IIFE
  - `:3690-3743` `makeVoxelBot` legs
  - `:3936-4360` Greek creatures
  - `:4707-4850` Hydra model
  - `:4850-4925` Champion model
  - `:4610-4707` Ifrit King model
  - `:4925-4995` Tiger model
  - `:5286-5400` Greek weapons
  - `:6980-7110` AI movement + animation loop
  - `:6136` boss spawn

---

## Task 1: Audit harness

Establishes the test gate every later task depends on. The harness already exists in prototype form at `/private/tmp/claude-501/-Users-rafea-src-blockfront/413df77c-cf22-4102-a48d-ec9fa5fec386/scratchpad/` — copy it in, do not rewrite it from scratch.

**Files:**
- Create: `tools/audit/three_stub.js`
- Create: `tools/audit/audit.py`
- Create: `tools/audit/README.md`

**Interfaces:**
- Produces: `python3 tools/audit/audit.py` — exits 0 when all checks pass, 1 otherwise. Prints one table row per actor.
- Produces (JS globals, for later checks): `__meshWorldBox(mesh)` → `{min,max}`; `__modelBoxes(root, scale)` → `[{mesh,box}]`; `__modelBounds(root, scale)` → `{min,max,count}`; `globalThis.__builders` → map of builder name to function.

- [ ] **Step 1: Copy the prototype harness into the repo**

```bash
mkdir -p tools/audit
SCRATCH=/private/tmp/claude-501/-Users-rafea-src-blockfront/413df77c-cf22-4102-a48d-ec9fa5fec386/scratchpad
cp "$SCRATCH/three_stub.js" tools/audit/three_stub.js
cp "$SCRATCH/audit.py"      tools/audit/audit.py
```

- [ ] **Step 2: Repoint `audit.py` at the repo relative to itself**

The prototype hardcodes `REPO`. Replace that line so the tool works from any cwd:

```python
REPO = pathlib.Path(__file__).resolve().parents[2]
```

- [ ] **Step 3: Run it and confirm it reproduces the spec's measured table**

Run: `python3 tools/audit/audit.py`

Expected: exit code 1, and exactly this verdict column — 8 failures, Minotaur the only `ok`:

```
Champion  (Boss III)   BURIED 0.905u
IfritKing (Boss IV)    BURIED 0.440u
Colossus  (Boss I)     BURIED 0.310u
Hydra     (Boss II)    BURIED 0.171u
Griffin                FLOATS 0.155u
Medusa (wave-6 elite)  FLOATS 0.121u
grunt (town/pyramid)   BURIED 0.100u
Tiger (Champion add)   BURIED 0.071u
Minotaur               ok
```

If any number differs, the stub is wrong — fix the stub, not the expectation.

- [ ] **Step 4: Write the README**

```markdown
# Geometry audit

Headless checks for `index.html`. No browser, no build step.

    pip install py-mini-racer
    python3 tools/audit/audit.py

Executes the game's whole inline `<script>` body inside py_mini_racer against a
stubbed THREE.js + DOM (`three_stub.js`), then reads back real world-space
bounding boxes.

## Checks

- **ground contact** — every actor model's lowest vertex sits on its arena's
  floor at the scale it actually spawns at. Catches bosses walking with their
  feet underground and creatures hovering above it.
- **connectivity** — every mesh in a model touches at least one other mesh in
  that model. Catches the recurring "chained segments rendered as a row of
  floating shards" bug (Hydra necks, Hydra tail, Saif blade, crossbow lath).
- **coplanarity** — no two meshes in a model share a near-coplanar face across
  an overlap. Catches z-fighting.

Several builders use `Math.random()`, so the audit runs each model a few times
and reports the worst case.

Exit code is 0 only when every check passes.
```

- [ ] **Step 5: Commit**

```bash
git add tools/audit
git commit -m "Add headless geometry audit harness

Executes index.html's script body in py_mini_racer against a stubbed
THREE/DOM and reads back real world-space bounding boxes. First
automated check this project has had.

Currently RED: 8 of 9 actor models fail ground contact."
```

---

## Task 2: Normalise arena floor tops to y=0

`spawnBot()` places every actor at `y=0` with no terrain sampling, so an arena floor whose top face is not at `y=0` buries every actor in it by that amount. Two of the four arenas are wrong.

**Files:**
- Modify: `index.html:1332` (Hydra platform), `index.html:1396` (Colosseum floor)
- Test: `tools/audit/audit.py`

**Interfaces:**
- Consumes: the harness from Task 1.
- Produces: `ACTORS` floor-top column in `audit.py` becomes `0.00` for all four arenas.

- [ ] **Step 1: Update the test's expected floor tops to 0.00**

In `tools/audit/audit.py`, the `ACTORS` table's 4th column is the arena floor top. Change the Hydra row from `0.25` to `0.00`, the Champion row from `0.10` to `0.00`, and the Tiger row from `0.10` to `0.00`.

- [ ] **Step 2: Run the audit to confirm the new expectation fails**

Run: `python3 tools/audit/audit.py`

Expected: FAIL. Hydra now reports `FLOATS 0.079u` (its model bottom is at +0.079 but the floor is asserted at 0), Champion still `BURIED 0.805u`, Tiger now `FLOATS 0.029u`.

- [ ] **Step 3: Drop the Hydra platform so its top face lands at y=0**

The platform is 0.6 tall, so its centre must sit at `-0.3`. The stone lip below it (0.4 tall, currently centred `-0.35`) must drop in step so it stays *below* the marble rather than poking through it — its top goes to `-0.3`, so its centre goes to `-0.5`.

At `index.html:1332`, replace:

```js
  hblock(R*2,0.6,R*2, marbleFloorMat, 0,-0.05,0);
  hblock(R*2+1.2,0.4,R*2+1.2, stoneMat, 0,-0.35,0); // a slightly wider stone lip below the marble
```

with:

```js
  // Floor top must land exactly at y=0: spawnBot() places every actor at y=0 with no terrain
  // sampling, so any other top face buries (or floats) every bot in the arena by the difference.
  // This platform used to top out at +0.25, which is what sank the Hydra 0.17 into its own floor.
  hblock(R*2,0.6,R*2, marbleFloorMat, 0,-0.3,0);
  hblock(R*2+1.2,0.4,R*2+1.2, stoneMat, 0,-0.5,0); // wider stone lip, dropped in step to stay under the marble
```

- [ ] **Step 4: Drop the Colosseum floor so its top face lands at y=0**

The floor is 0.4 tall, so its centre must sit at `-0.2`. At `index.html:1396`, replace:

```js
  const floor = new THREE.Mesh(new THREE.BoxGeometry(R*2.1,0.4,R*2.1), sandMat); floor.position.set(0,-0.1,0); colosseumArena.add(floor);
```

with:

```js
  // -0.2, not -0.1: a 0.4-tall floor centred at -0.1 tops out at +0.1, and spawnBot() puts every
  // actor at y=0 regardless — so the Champion and its tigers stood 0.1 inside the sand. Matches the
  // pyramid dungeon and Ifrit arena, both of which already top out at 0.
  const floor = new THREE.Mesh(new THREE.BoxGeometry(R*2.1,0.4,R*2.1), sandMat); floor.position.set(0,-0.2,0); colosseumArena.add(floor);
```

- [ ] **Step 5: Run the audit**

Run: `python3 tools/audit/audit.py`

Expected: still FAIL overall (models are fixed in Task 3), but the *floor* half of the discrepancy is gone. Hydra should now read `FLOATS 0.079u` and Tiger `FLOATS 0.029u` — both now above their floor rather than below it, which is what proves the floors moved.

- [ ] **Step 6: Commit**

```bash
git add index.html tools/audit/audit.py
git commit -m "Land every arena floor's top face on y=0

spawnBot() places every actor at y=0 with no terrain sampling, so an
arena whose floor tops out anywhere else buries or floats every bot in
it. The Hydra platform topped out at +0.25 and the Colosseum floor at
+0.10; the pyramid dungeon and Ifrit arena were already correct."
```

---

## Task 3: Seat every actor model on y=0

With floors normalised, the remaining error is in the models. Fix by moving the offending parts, **not** by offsetting the root group — the root carries the marker sprite and the chest-height raycast origin, so shifting it would break aim and hit detection.

**Files:**
- Modify: `index.html:3724-3730` (`makeVoxelBot` legs), `:4908-4914` (Champion legs), `:4653-4665` (Ifrit flame base), `:4044-4055` (Griffin legs), `:4076-4082` (Medusa coils), `:4967-4980` (Tiger legs)
- Test: `tools/audit/audit.py`

**Interfaces:**
- Consumes: `__modelBounds(root, scale)` from Task 1; floors at `y=0` from Task 2.
- Produces: `python3 tools/audit/audit.py` ground-contact section exits 0.

- [ ] **Step 1: Run the audit to capture the exact remaining offsets**

Run: `python3 tools/audit/audit.py`

Record each model's `minY`. That number is exactly how far each model's parts must move — every fix below is "add `-minY` to the lowest parts' Y".

- [ ] **Step 2: Raise `makeVoxelBot`'s legs by 0.10**

At `index.html:3731`, the leg group sits at `y=0.7` and its boot at local `-0.72` with height `0.16`, so the boot bottom lands at `-0.10`. Raise the group. Replace:

```js
    leg.position.set(side*0.16, 0.7, 0); g.add(leg); return leg;
```

with:

```js
    // 0.80, not 0.70: the boot hangs to local -0.72 and is 0.16 tall, so its underside sits at
    // (0.70 - 0.72 - 0.08) = -0.10 — every grunt in the game stood 0.1 inside the floor, and the
    // Colossus, which reuses this rig at scale 3.1, stood 0.31 inside it.
    leg.position.set(side*0.16, 0.80, 0); g.add(leg); return leg;
```

- [ ] **Step 3: Raise the Champion's legs by 0.35**

At `index.html:4908-4913`, replace the leg block:

```js
  // legs with greaves + sandals
  [-1,1].forEach(s=>{
    const thigh=new THREE.Mesh(new THREE.BoxGeometry(0.28,0.5,0.28), skinMat); thigh.position.set(s*0.24,0.32,0); g.add(thigh);
    const greave=new THREE.Mesh(new THREE.BoxGeometry(0.26,0.4,0.26), armorMat); greave.position.set(s*0.24,-0.04,0.02); g.add(greave);
    const foot=new THREE.Mesh(new THREE.BoxGeometry(0.28,0.14,0.4), voxMat(0x5a4020,{noise:10})); foot.position.set(s*0.24,-0.28,0.08); g.add(foot);
  });
```

with:

```js
  // legs with greaves + sandals. Every Y here is 0.35 higher than it was: the foot is 0.14 tall and
  // sat at -0.28, putting its underside at -0.35 — and at the boss scale of 2.3 that is 0.8 of a unit
  // below the arena floor, so the Champion's feet and shins were entirely underground. Rebuilt as
  // hip-pivoted groups in the next task; the Y correction lands here first so the two are separable.
  [-1,1].forEach(s=>{
    const thigh=new THREE.Mesh(new THREE.BoxGeometry(0.28,0.5,0.28), skinMat); thigh.position.set(s*0.24,0.67,0); g.add(thigh);
    const greave=new THREE.Mesh(new THREE.BoxGeometry(0.26,0.4,0.26), armorMat); greave.position.set(s*0.24,0.31,0.02); g.add(greave);
    const foot=new THREE.Mesh(new THREE.BoxGeometry(0.28,0.14,0.4), voxMat(0x5a4020,{noise:10})); foot.position.set(s*0.24,0.07,0.08); g.add(foot);
  });
```

- [ ] **Step 4: Raise the Ifrit King's flame base by 0.44**

Read `index.html:4653-4665` first and identify every mesh whose world-space bottom is below 0 — the flame base cone is the lowest. Raise each by exactly the `minY` magnitude the audit reported (0.22 in local units, since the Ifrit spawns at scale 2.0). Add a comment stating the measured figure and that the Ifrit floats, so its *design* bottom is a deliberate hover gap of 0, not a negative.

- [ ] **Step 5: Lower the Griffin by 0.155 and the Medusa by 0.097**

Griffin (`index.html:4044-4055`): its lowest parts are the front talons (`talon.position.y=0.2`, h=0.09) and rear paws (`paw.position.y=0.22`, h=0.11). Subtract 0.155 from every leg/talon/paw Y so the talons touch 0.

Medusa (`index.html:4076-4082`): the coil segments are generated from the `coilSegs` table, whose lowest entry gives `y - s*0.7/2 = 0.097`. Subtract 0.097 from each `y` in the `coilSegs` table, and from the `plate` offsets derived from them.

Both need a comment giving the measured float distance and noting the audit is what caught it.

- [ ] **Step 6: Lower the Tiger by its measured offset**

Read `index.html:4967-4980`, find the paw/leg meshes, and subtract the audit's reported `minY` from each.

- [ ] **Step 7: Run the audit**

Run: `python3 tools/audit/audit.py`

Expected: **every** row reads `ok`, and the ground-contact section reports `0 of 9 actors fail`.

- [ ] **Step 8: Commit**

```bash
git add index.html
git commit -m "Seat every actor model on the floor

Eight of the game's nine actor models were buried in or hovering above
their own floor. Worst was the Colosseum Champion at 0.9 units under the
sand — feet and greaves entirely below it. Fixed by moving the offending
parts, not the root group, since the root carries the marker sprite and
the chest-height raycast origin.

Ground-contact audit is now green for all 9."
```

---

## Task 4: Connectivity and coplanarity checks

Adds the two remaining checks from the spec, then fixes whatever they surface. Doing this before the model rebuilds means the rebuilds are gated by it.

**Files:**
- Modify: `tools/audit/audit.py`, `tools/audit/three_stub.js`
- Modify: `index.html` (fixes for whatever the checks surface)

**Interfaces:**
- Consumes: `__modelBoxes(root, scale)` from Task 1.
- Produces: `check_connectivity(ctx)` and `check_coplanarity(ctx)` in `audit.py`, both called from `main()`.

- [ ] **Step 1: Add the connectivity check**

Add to `tools/audit/audit.py`:

```python
CONNECT_EPS = 0.001  # boxes this close count as touching


def check_connectivity(ctx, runs=5):
    """Every mesh in a model must overlap or touch at least one other mesh in it.

    Catches the recurring 'chained segments render as a row of floating shards' bug.
    Builders use Math.random(), so run each model several times and keep the worst.
    """
    js = """
    (function(builder, invoke, scale, eps){
      var b = globalThis.__builders[builder];
      var m = eval(invoke)(b);
      var boxes = globalThis.__modelBoxes(m, scale);
      function touches(a, c){
        return a.min.x <= c.max.x + eps && c.min.x <= a.max.x + eps &&
               a.min.y <= c.max.y + eps && c.min.y <= a.max.y + eps &&
               a.min.z <= c.max.z + eps && c.min.z <= a.max.z + eps;
      }
      var orphans = 0;
      for(var i=0;i<boxes.length;i++){
        var hit = false;
        for(var j=0;j<boxes.length;j++){
          if(i===j) continue;
          if(touches(boxes[i].box, boxes[j].box)){ hit = true; break; }
        }
        if(!hit) orphans++;
      }
      return JSON.stringify({orphans:orphans, total:boxes.length});
    })
    """
    fn = ctx.eval(js)
    worst = {}
    for builder, invoke, scale, _floor, label in ACTORS:
        for _ in range(runs):
            r = json.loads(fn(builder, invoke, scale, CONNECT_EPS))
            if r["orphans"] > worst.get(label, (-1, 0))[0]:
                worst[label] = (r["orphans"], r["total"])
    return worst
```

- [ ] **Step 2: Run it and record the baseline**

Run: `python3 tools/audit/audit.py`

Expected: some models report orphan meshes. Record the list — that is the work for Step 4. A model whose parts are all deliberately separate (the Ifrit's floating flame motes, if any) needs an explicit allowlist entry with a comment, not a geometry change.

- [ ] **Step 3: Add the coplanarity check**

Two boxes that overlap in two axes and whose faces sit within `COPLANAR_EPS` on the third will z-fight across that overlap. Add:

```python
COPLANAR_EPS = 0.004   # faces closer than this fight in the depth buffer
OVERLAP_MIN  = 0.02    # ignore slivers: the shared area must be at least this wide


def check_coplanarity(ctx, runs=5):
    js = """
    (function(builder, invoke, scale, eps, omin){
      var b = globalThis.__builders[builder];
      var m = eval(invoke)(b);
      var boxes = globalThis.__modelBoxes(m, scale);
      var hits = [];
      var AX = ['x','y','z'];
      for(var i=0;i<boxes.length;i++) for(var j=i+1;j<boxes.length;j++){
        var a = boxes[i].box, c = boxes[j].box;
        for(var k=0;k<3;k++){
          var ax = AX[k], u = AX[(k+1)%3], v = AX[(k+2)%3];
          var ou = Math.min(a.max[u],c.max[u]) - Math.max(a.min[u],c.min[u]);
          var ov = Math.min(a.max[v],c.max[v]) - Math.max(a.min[v],c.min[v]);
          if(ou < omin || ov < omin) continue;
          var pairs = [[a.min[ax],c.min[ax]],[a.min[ax],c.max[ax]],
                       [a.max[ax],c.min[ax]],[a.max[ax],c.max[ax]]];
          for(var p=0;p<4;p++){
            var d = Math.abs(pairs[p][0]-pairs[p][1]);
            if(d > 0 && d < eps){ hits.push({axis:ax, gap:d}); }
          }
        }
      }
      return JSON.stringify({hits:hits.length});
    })
    """
    fn = ctx.eval(js)
    worst = {}
    for builder, invoke, scale, _floor, label in ACTORS:
        for _ in range(runs):
            r = json.loads(fn(builder, invoke, scale, COPLANAR_EPS, OVERLAP_MIN))
            worst[label] = max(worst.get(label, 0), r["hits"])
    return worst
```

- [ ] **Step 4: Wire both into `main()` and fix what they surface**

Print both alongside the ground-contact table and fold their failures into the exit code. Then fix each real hit in `index.html` — the established fix for a coplanar pair is to derive the upper part's position from its own height so it sits flush on the lower part's real top with a hairline clearance, exactly as the ruined-wall crenellation fixes in the working tree do.

- [ ] **Step 5: Run the audit**

Run: `python3 tools/audit/audit.py`

Expected: exit 0 across all three checks, stable across repeated runs (the checks each run 5 times because several builders randomise).

- [ ] **Step 6: Commit**

```bash
git add tools/audit index.html
git commit -m "Add connectivity + coplanarity checks to the geometry audit

Connectivity catches the recurring 'chained segments render as floating
shards' bug this file has hit on the Hydra necks, the Hydra tail, the
Saif blade and the crossbow lath. Coplanarity is the same sweep the Giza
rebuild used to go from ~190 flagged overlaps to zero.

Both run each model 5 times, since several builders randomise."
```

---

## Task 5: Boss walk rigs

Three separate defects, all in how bosses animate while moving.

**Files:**
- Modify: `index.html:4908-4915` (Champion legs → hip-pivoted groups), `:7099-7101` (walk term), `:6992` (boss `b.moving`)
- Modify: `index.html:4707-4849` (Hydra idle), `:4610-4706` (Ifrit hover)

**Interfaces:**
- Consumes: the Champion's corrected leg Y values from Task 3.
- Produces: `makeChampion()` exposes `userData.legL` / `userData.legR` as `THREE.Group`s pivoted at the hip, matching `makeVoxelBot`'s contract, so the existing `index.html:7100` animation drives them with no AI-loop change.

- [ ] **Step 1: Rebuild the Champion's legs as hip-pivoted groups**

Replace the leg block from Task 3 Step 3 with two groups pivoted at the hip, so `rotation.x` swings the whole leg the way `makeVoxelBot`'s does. The hip pivot sits at `y=0.92` (top of the thigh); each child's Y is its previous absolute Y minus 0.92.

```js
  // legs with greaves + sandals, built as hip-pivoted groups rather than loose meshes.
  // These were previously six free meshes and userData.legL/legR were set to null, so the shared
  // animation at the bottom of the AI loop (guarded by `if(ud.legL)`) skipped this boss entirely —
  // Boss III slid across the arena with completely rigid legs. Pivot is the hip, matching makeVoxelBot.
  function championLeg(s){
    const leg = new THREE.Group();
    leg.position.set(s*0.24, 0.92, 0);
    const thigh=new THREE.Mesh(new THREE.BoxGeometry(0.28,0.5,0.28), skinMat); thigh.position.set(0,-0.25,0); leg.add(thigh);
    const greave=new THREE.Mesh(new THREE.BoxGeometry(0.26,0.4,0.26), armorMat); greave.position.set(0,-0.61,0.02); leg.add(greave);
    const foot=new THREE.Mesh(new THREE.BoxGeometry(0.28,0.14,0.4), voxMat(0x5a4020,{noise:10})); foot.position.set(0,-0.85,0.08); leg.add(foot);
    g.add(leg); return leg;
  }
  const champLegL = championLeg(-1), champLegR = championLeg(1);
```

Then at `index.html:4915` replace:

```js
  g.userData.legL = null; g.userData.legR = null; g.userData.armR = armR; g.userData.armL = armL;
```

with:

```js
  g.userData.legL = champLegL; g.userData.legR = champLegR; g.userData.armR = armR; g.userData.armL = armL;
```

- [ ] **Step 2: Run the audit to confirm the rebuild kept ground contact**

Run: `python3 tools/audit/audit.py`

Expected: Champion still `ok`. The hip pivot at `0.92` with the foot at local `-0.85` and half-height `0.07` puts the sole at `0.92 - 0.85 - 0.07 = 0.00`.

- [ ] **Step 3: Ease `b.moving` instead of flipping it**

At `index.html:6992`, the boss branch sets `b.moving` to a hard 0 or 1, so the leg swing snaps from mid-stride to rest in a single frame when the boss crosses `distToPlayer == 4`. Introduce a smoothed companion value. Replace:

```js
    if(b.boss){
      if(distToPlayer>4){ b.moving=1; moveActor(b.mesh, toPX, toPZ, b.speed*dt, R); } else b.moving=0;
    } else if(canEngage){
```

with:

```js
    if(b.boss){
      if(distToPlayer>4){ b.moving=1; moveActor(b.mesh, toPX, toPZ, b.speed*dt, R); } else b.moving=0;
      // b.moving is a hard 0/1 flip, and the leg swing below multiplies straight through it — so
      // crossing this 4-unit threshold snapped the legs from mid-stride to rest in one frame, a
      // visible pop on every approach. b.gait eases toward it instead and drives the animation.
    } else if(canEngage){
```

Then at `index.html:7099`, replace:

```js
    const walk = Math.sin(t*7 + b.t*3) * (b.moving?1:0);
```

with:

```js
    // gait ramps over ~0.2s toward b.moving rather than tracking it instantly — see the boss branch above
    b.gait = (b.gait===undefined) ? (b.moving?1:0) : b.gait + ((b.moving?1:0) - b.gait) * Math.min(1, dt*5);
    const walk = Math.sin(t*7 + b.t*3) * b.gait;
```

- [ ] **Step 4: Give the Hydra body undulation and the Ifrit King a hover bob**

Both are legless by design, so neither gets a leg rig — they get idle motion driven off the same `walk`/`b.gait` terms so they still respond to movement.

Add to `makeHydra()`, just before the `bodyMeshes` collection: capture the trunk segments and neck root groups into `g.userData.hydraTrunk` (array) and `g.userData.hydraNecks` (array), recording each one's authored base Y so the animation can offset around it rather than drifting:

```js
  g.userData.hydraTrunk = trunkMeshes.map(m => ({mesh:m, baseY:m.position.y, z:m.position.z}));
```

Add to `makeIfritKing()`: `g.userData.hoverBase = <the group's authored rest Y>`.

Then in the AI loop, after the `walk` line, add:

```js
    // legless bosses: no leg rig, so they get idle motion instead of sliding rigidly.
    // Both ride b.gait, so they settle when the boss stops rather than writhing on the spot.
    if(ud.hydraTrunk){
      for(const s of ud.hydraTrunk){
        s.mesh.position.y = s.baseY + Math.sin(t*4 + s.z*1.6) * 0.06 * (0.35 + 0.65*b.gait);
      }
    }
    if(ud.hoverBase !== undefined){
      b.mesh.position.y = ud.hoverBase + Math.sin(t*1.6 + b.t) * 0.18;
    }
```

- [ ] **Step 5: Run the audit**

Run: `python3 tools/audit/audit.py`

Expected: exit 0. All three checks green. Note that the audit measures models at rest, so idle motion does not affect it — the hover offset is applied to the live bot mesh in the loop, not baked into the builder.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "Give every boss a working walk

The Colosseum Champion set userData.legL/legR to null, so the shared leg
animation - guarded by `if(ud.legL)` - skipped it entirely and Boss III
slid across the arena with rigid legs. Its legs are hip-pivoted groups
now, matching makeVoxelBot's contract, so the existing animation drives
them with no AI-loop change.

b.moving is a hard 0/1 flip that the leg swing multiplied straight
through, so crossing the 4-unit engage threshold snapped the legs from
mid-stride to rest in a single frame. A smoothed b.gait drives the
animation instead.

The Hydra and Ifrit King are legless by design and got idle motion
- body undulation and a hover bob - rather than sliding rigidly."
```

---

## Task 6: Boss collision radius from the model

`const R = b.boss?1.2:0.55*(b.scale||1)` (`index.html:6988`) is a constant for every boss regardless of size. The Hydra is 3.1 units across and ~7.9 long at spawn scale, so its body and tail pass through the arena's columns and cover walls.

**Files:**
- Modify: `index.html:4995-5010` (`spawnBot`), `:6988` (radius lookup)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `data.radius` on every bot, set once at spawn; the AI loop reads it instead of recomputing.

- [ ] **Step 1: Compute and store the radius at spawn**

In `spawnBot()` (`index.html:4995`), after `bot.scale.setScalar(opts.scale)` and before the `data` object is built, measure the model:

```js
  // Boss collision radius used to be a flat 1.2 for every boss regardless of model. The Hydra's
  // trunk alone is 1.3 wide at scale 2.4 - 1.56 half-width - and it is ~7.9 long nose to tail, so
  // its body and tail walked straight through the arena's columns and cover walls. Measure the
  // actual footprint once at spawn instead. Ordinary bots keep the tuned 0.55*scale.
  let radius = 0.55*(opts.scale||1);
  if(opts.boss){
    const bb = new THREE.Box3().setFromObject(bot);
    radius = Math.max(Math.abs(bb.max.x), Math.abs(bb.min.x), Math.abs(bb.max.z), Math.abs(bb.min.z));
    radius = Math.max(1.2, Math.min(3.2, radius));   // floor at the old value, cap so it still fits doorways
  }
```

Add `radius` to the `data` object literal.

- [ ] **Step 2: Read it in the AI loop**

At `index.html:6988`, replace:

```js
    const R = b.boss?1.2:0.55*(b.scale||1);
```

with:

```js
    const R = b.radius !== undefined ? b.radius : (b.boss?1.2:0.55*(b.scale||1));
```

- [ ] **Step 3: Verify in the browser**

Run: `python3 -m http.server 8000` and open `http://localhost:8000`.

Use the `KeyG` god-mode toggle (`c1bd041`) to reach Boss II quickly. Confirm the Hydra's body no longer passes through the broken columns, and that it can still navigate between the ruined walls rather than getting permanently wedged. If it wedges, lower the cap in Step 1.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "Derive boss collision radius from the model's real footprint

A flat 1.2 for every boss meant the Hydra - 3.1 units across and ~7.9
long at spawn scale - walked its body and tail straight through the
arena's columns and cover walls. Measured once at spawn, floored at the
old 1.2 and capped so bosses still fit between obstacles."
```

---

## Task 7: Greek texture set

Four new texture builders. This is the map's defining gap: the whole 70x54 Greek map is `gravelTex` plus six near-identical pale greys, where Cairo and Giza each got a purpose-built set.

**Files:**
- Modify: `index.html` — add after `beachSandTex()` (`:613-626`), before `citadelStoneTex()` (`:627`)

**Interfaces:**
- Produces: `pentelicMarbleTex()`, `paintedStuccoTex()`, `greekRoofTileTex()`, `harbourFlagstoneTex()`. Each returns a **canvas**, matching the convention of `gravelTex`/`terracottaTex`/`cairoDustTex` — callers wrap them with `_finish(tex(), repeat)`.

- [ ] **Step 1: Write the four builders**

Follow the existing house style exactly: `const P=<power of two>, c=_mkCanvas(P), x=c.getContext('2d')`, a base fill, a deterministic per-pixel noise pass using `Math.abs(Math.sin(i*A+j*B)*C%1)`, then feature passes. Return the canvas, not a texture.

```js
// ---- Greek palette. Alexandria had none of its own: the whole map ran on gravelTex (authored as a
// generic road surface) plus six near-identical pale greys, which is why it read as one flat wash
// where Cairo and Giza each read as a place. Same reasoning as the gizaSandTex/graniteTex/basaltTex
// set added for Giza — an era needs its own materials before landmarks and density can carry it. ----

// Pentelic marble: the stone the Greeks actually built in. It weathers to a warm gold, NOT the cool
// dead grey this map has been using — that warmth against a blue sky is the single most recognisable
// thing about Greek ruins, and it is what gives the map somewhere to sit between its sand and its sea.
function pentelicMarbleTex(){ const P=32,c=_mkCanvas(P),x=c.getContext('2d');
  x.fillStyle='#e6dfcb'; x.fillRect(0,0,P,P);
  for(let j=0;j<P;j++)for(let i=0;i<P;i++){
    const n=Math.abs(Math.sin(i*5.3+j*11.7)*4375.5%1);
    const v=228+((n-0.5)*22)|0;
    x.fillStyle=`rgb(${v},${(v-6)|0},${(v-22)|0})`; x.fillRect(i,j,1,1);
  }
  // fine grey veining — a few shallow diagonal runs, not a marble-countertop swirl
  x.strokeStyle='rgba(150,146,132,0.35)'; x.lineWidth=1;
  for(let k=0;k<5;k++){
    const y0=Math.random()*P;
    x.beginPath(); x.moveTo(0,y0);
    x.lineTo(P, y0 + (Math.random()-0.5)*10);
    x.stroke();
  }
  return c; }

// Painted stucco: Greek public architecture was NOT bare white stone, it was painted. Ochre, Greek
// blue and oxblood over lime plaster. This is the map's actual colour source — the one material here
// that is allowed to be loud, used on entablatures and trim rather than whole walls.
function paintedStuccoTex(){ const P=32,c=_mkCanvas(P),x=c.getContext('2d');
  x.fillStyle='#efe8d6'; x.fillRect(0,0,P,P);            // lime plaster ground
  const bands=[['#c8892c',6],['#2f5f8a',5],['#8f2f26',5]]; // ochre / Greek blue / oxblood
  let y=6;
  for(const [col,h] of bands){ x.fillStyle=col; x.fillRect(0,y,P,h); y+=h+4; }
  for(let j=0;j<P;j++)for(let i=0;i<P;i++){
    const n=Math.abs(Math.sin(i*7.1+j*3.9)*4375.5%1);
    if(n>0.86){ x.fillStyle='rgba(0,0,0,0.10)'; x.fillRect(i,j,1,1); }   // plaster grain / wear
  }
  return c; }

// Terracotta pan-and-cover roof tiling. Seen almost entirely edge-on from ground level, so what has
// to read is the ridged profile — a flat orange field reads as nothing at all from a player's eye height.
function greekRoofTileTex(){ const P=32,c=_mkCanvas(P),x=c.getContext('2d');
  x.fillStyle='#a8552c'; x.fillRect(0,0,P,P);
  for(let col=0;col<P;col+=8){
    x.fillStyle='#b96234'; x.fillRect(col,0,6,P);          // pan tile
    x.fillStyle='#8c4423'; x.fillRect(col+6,0,2,P);        // cover tile, the raised ridge
    x.fillStyle='rgba(0,0,0,0.18)'; x.fillRect(col+5,0,1,P); // shadow line down the ridge's side
  }
  for(let row=0;row<P;row+=11){ x.fillStyle='rgba(0,0,0,0.14)'; x.fillRect(0,row,P,1); } // course laps
  return c; }

// Worn quay flagstones for the waterfront and agora paving — large dressed slabs, deliberately a
// different grain from gravelTex's loose chips so paved ground reads as built rather than trodden.
function harbourFlagstoneTex(){ const P=32,c=_mkCanvas(P),x=c.getContext('2d');
  x.fillStyle='#8f8b80'; x.fillRect(0,0,P,P);              // recessed joint colour, shows between slabs
  const slab=16;
  for(let by=0;by<P;by+=slab)for(let bx=0;bx<P;bx+=slab){
    // per-slab tone, deterministic so the texture is stable between reloads
    const n=Math.abs(Math.sin(bx*4.1+by*9.3)*137%1);
    const v=(150+n*28)|0;
    x.fillStyle=`rgb(${v},${(v-3)|0},${(v-11)|0})`;
    x.fillRect(bx+1,by+1,slab-2,slab-2);                   // 1px inset all round = the joint
  }
  // wear: scattered darker pits and a few lighter scuffs, so slabs don't read as flat panels
  for(let j=0;j<P;j++)for(let i=0;i<P;i++){
    const n=Math.abs(Math.sin(i*6.7+j*2.3)*4375.5%1);
    if(n>0.93){ x.fillStyle='rgba(60,58,52,0.22)'; x.fillRect(i,j,1,1); }
    else if(n<0.04){ x.fillStyle='rgba(255,252,240,0.16)'; x.fillRect(i,j,1,1); }
  }
  return c; }
```

- [ ] **Step 2: Smoke-test that the new builders run**

Run: `python3 tools/audit/audit.py`

Expected: exit 0. The audit executes the whole script body, so a syntax error or a bad canvas call in any new builder fails the load with a clear message.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "Add a Greek texture set: Pentelic marble, painted stucco, roof tile, flagstone

Alexandria had no materials of its own - the whole 70x54 map ran on
gravelTex plus six near-identical pale greys, which is why it read as one
flat wash. Same gap the Giza rebuild filled with gizaSandTex/graniteTex/
basaltTex/limestoneCasingTex.

Pentelic marble weathers warm gold rather than the cool dead grey the map
was using, and painted stucco reflects that Greek public architecture was
painted, not bare stone - together they are the map's colour source."
```

---

## Task 8: Apply the Greek palette

Repalette the existing landmarks off the six flat greys and onto the new textures. **Silhouettes do not change in this task** — it is purely tonal, so any visual regression is isolated to materials.

**Files:**
- Modify: `index.html:2299-2660` — `pharosLighthouse`, `library`, `templeOfPoseidon`, `altar`, `pylonGate`, `obelisk`, `sphinx`, `brokenStatue`, `seaCave`, `fallenColumn`, and the ground/path materials

**Interfaces:**
- Consumes: `pentelicMarbleTex()`, `paintedStuccoTex()`, `greekRoofTileTex()`, `harbourFlagstoneTex()` from Task 7.

- [ ] **Step 1: Define the shared material set at the top of the IIFE**

Immediately after `const bronzeMat = metalMatP(0xad8730,80,0xffe9b0);` (`index.html:2300`), add:

```js
  // One shared palette for the whole map, so the era reads as a single place rather than a dozen
  // independently-chosen greys. Warm marble is the dominant note, painted stucco the accent, and
  // terracotta the roofline — the three-way break Cairo gets from sandstone/lapis/awning.
  const marbleMat    = new THREE.MeshLambertMaterial({map:_finish(pentelicMarbleTex(),4)});
  const marbleTrim   = new THREE.MeshLambertMaterial({map:_finish(pentelicMarbleTex(),2)});
  const stuccoMat    = new THREE.MeshLambertMaterial({map:_finish(paintedStuccoTex(),1)});
  const roofTileMat  = new THREE.MeshLambertMaterial({map:_finish(greekRoofTileTex(),3)});
  const flagstoneMat = new THREE.MeshLambertMaterial({map:_finish(harbourFlagstoneTex(),8)});
```

- [ ] **Step 2: Repalette each landmark**

Work through the six flat greys and replace each usage:

| old | replace with |
|---|---|
| `0xe0dbc9` (bright wall) | `marbleMat` |
| `0xc4bfaf`, `0xc7c2b3` (column/wall) | `marbleMat` |
| `0xc5c0b2`, `0xb8b3a4` (trim/cornice) | `marbleTrim` |
| `0xb3ac9c` (plinth/base) | `marbleTrim` |
| `0xc9a671` (roof) | `roofTileMat` |

Entablatures, pediments and cornices take `stuccoMat` so the painted band actually appears where a Greek building would carry it. `voxMat(hex, …)` calls that take a colour become plain `new THREE.Mesh(geo, <sharedMat>)`.

Leave the Egyptian-holdover objects — pylon gate, obelisks, sphinxes — on their existing hieroglyph-patterned sandstone. They are deliberately *not* Greek, and repalettng them would erase the Ptolemaic fusion the map is built around.

- [ ] **Step 3: Swap the paths to flagstone**

At `index.html:2317`, the crossroads currently reuses `gravelTex` at a denser repeat. Replace `marblePathMat`'s map with `_finish(harbourFlagstoneTex(),10)`, keeping the `polygonOffset` settings exactly as they are — those are what stop the path z-fighting against the ground slab.

- [ ] **Step 4: Verify in the browser**

Run: `python3 -m http.server 8000`, open `http://localhost:8000`, reach the Greek era.

Confirm: the map has visible tonal range rather than one grey wash; nothing turned into an untextured flat colour; the crossroads still does not z-fight.

- [ ] **Step 5: Run the audit and commit**

Run: `python3 tools/audit/audit.py` — expected exit 0.

```bash
git add index.html
git commit -m "Repalette Alexandria onto the new Greek materials

Silhouettes unchanged - purely tonal, so any regression is isolated to
materials. The six near-identical greys collapse into one shared palette:
warm Pentelic marble as the dominant note, painted stucco on entablatures
and pediments as the accent, terracotta on the rooflines.

The pylon gate, obelisks and sphinxes deliberately keep their hieroglyph
sandstone - they are the Egyptian holdover the Ptolemaic fusion rests on."
```

---

## Task 9: Hero landmark

**Files:**
- Modify: `index.html:2326-2354` (`pharosLighthouse` + `causeway` + their call sites)

**Interfaces:**
- Consumes: the Task 8 palette.

- [ ] **Step 1: Confirm the spawn sightline**

`switchToGreekWorld()` (`index.html:5678`) sets `camera.position.set(0,1.7,10)` with `yaw=0`, so the player looks down **−Z** from `(0,10)`. Anything meant to dominate the opening view must sit near `x≈0` at `z < 0`.

- [ ] **Step 2: Move and enlarge the Pharos**

Move the call from `pharosLighthouse(27,21)` to roughly `pharosLighthouse(0,-26)` — on the sightline, beyond the pylon gate at `z=-2` so the gate frames it. Scale every dimension in the function up by ~1.7 so the total height goes from ~17 to ~28. Widen its collider (`addBox`) to match.

Check against the `playClamp = 32` boundary: at `z=-26` with a base 15 wide, the structure spans `z=-33.5..-18.5`, which sits outside the clamp but inside the `B=33` boundary barrier — verify the barrier does not cut through it, and push the lighthouse to `z=-24` if it does.

- [ ] **Step 3: Move the causeway with it**

`causeway(27,7,15.5)` must follow the lighthouse or it becomes a walkway to nowhere. Re-aim it along the new approach.

- [ ] **Step 4: Give the harbour corner a replacement silhouette**

The Pharos was the only tall object anchoring `(27,21)`. Leaving it empty just relocates the problem. Add a shipsheds block — a row of open-fronted vaulted boat bays facing the water — using `marbleMat` and `roofTileMat`, with colliders.

- [ ] **Step 5: Verify in the browser**

Reach the Greek era and confirm the opening view is dominated by the lighthouse framed by the pylon gate, that the harbour corner still has a profile, and that the boundary barrier does not slice through either.

- [ ] **Step 6: Run the audit and commit**

Run: `python3 tools/audit/audit.py` — expected exit 0.

```bash
git add index.html
git commit -m "Put the Pharos on Alexandria's spawn sightline

The player enters at (0,10) looking -Z and the lighthouse stood at
(27,21) - behind their right shoulder - so the opening view was a low
gate and bare gravel. Same failure Cairo and Giza were each rebuilt to
fix. It now stands down the sightline at ~28 units tall with the pylon
gate framing it, and shipsheds fill the harbour corner it vacated."
```

---

## Task 10: Density and cover

Takes the map from ~45 objects to 90-110, with at least 20 usable combat cover pieces.

**Files:**
- Modify: `index.html:2294-2860` (inside the Greek IIFE, before the DISTANT SCENERY block at `:2660`)

- [ ] **Step 1: Add a stoa**

A long colonnaded market hall — the defining Greek civic building and the map's biggest missing type. Two storeys, a deep colonnade along its open face, `marbleMat` walls, `roofTileMat` roof, `stuccoMat` entablature. Colliders on the back wall and each column.

- [ ] **Step 2: Add an agora with market stalls**

A paved square (`flagstoneMat`) with awninged stalls, crates, amphora stacks and a speaker's platform. The stalls reuse the existing `marketStall` pattern (`index.html:862`) reskinned to Greek colours.

- [ ] **Step 3: Add a townhouse block**

Flat-roofed courtyard houses, 2-3 units tall, clustered rather than evenly spaced — the same lesson Cairo's townhouses and palm groves record. These carry most of the density.

- [ ] **Step 4: Add combat cover**

At least 20 collider'd, chest-height-or-taller pieces distributed across the playable area, not clustered at the edges: fallen columns, plinths, altars, cisterns, stacked amphorae, low walls. Reuse the existing `fallenColumn`/`brokenStatue`/`rockOutcrop` helpers where they fit.

- [ ] **Step 5: Count**

Add a temporary `console.log` of `greekColliders.length` and the scene child count, load the page, confirm the target range, then remove the log.

- [ ] **Step 6: Verify in the browser**

Play waves 4-6. Confirm the map reads as a city rather than monuments on gravel, that cover is actually usable against the ranged grunts, and that nothing blocks the crossroads or traps the player.

- [ ] **Step 7: Run the audit and commit**

Run: `python3 tools/audit/audit.py` — expected exit 0.

```bash
git add index.html
git commit -m "Give Alexandria a city: stoa, agora, townhouses, real cover

~45 objects on 70x54 with no vernacular architecture at all - no houses,
no market, no civic buildings - so the map read as monuments standing on
gravel. Cairo's townhouses and Khan bazaar are what carry that map; this
is Alexandria's equivalent.

Playable cover goes from 7 pieces to 20+, distributed across the map
rather than clustered at its edges."
```

---

## Task 11: Hydra arena

**Files:**
- Modify: `index.html:1318-1383`

- [ ] **Step 1: Repalette onto the Greek materials**

The arena's builders run *before* the Greek overworld IIFE, so `pentelicMarbleTex()` etc. must be defined above both — Task 7 places them at `:627`, which satisfies this. Replace `marbleFloorMat`/`marbleWallMat` with the Pentelic set and give the broken columns `marbleTrim`.

- [ ] **Step 2: Rebalance cover for the corrected boss radius**

Task 6 gave the Hydra its true footprint, so it can no longer clip through the columns, ruined walls and fallen blocks. Widen the gaps between cover so the boss can still path around the arena, and confirm the player still has line-of-sight breaks. These two must be tuned together.

- [ ] **Step 3: Verify in the browser**

Reach Boss II via god mode. Confirm: the Hydra never wedges permanently; the ruined walls still break line of sight; the arena reads as Greek marble rather than generic grey.

- [ ] **Step 4: Run the audit and commit**

Run: `python3 tools/audit/audit.py` — expected exit 0.

```bash
git add index.html
git commit -m "Repalette the Hydra arena and reopen its cover

Now that the Hydra has its real collision footprint it can no longer walk
through the columns and ruined walls, so the gaps between them had to
widen or the fight wedges. Cover still breaks line of sight - that is
what the ruined walls are for - but the boss can path around it."
```

---

## Task 12: Rebuild the Minotaur

Ground-up rebuild to the Ifrit/Ghoul/Roc standard. One creature per task so each can be reviewed and reverted independently.

**Files:**
- Modify: `index.html:3937-4005` (`makeMinotaur`)

**Interfaces:**
- Produces: `makeMinotaur()` → `THREE.Group` with `userData.bodyMeshes` and `userData.marker`. **No** `legL`/`legR`/`armR`/`armL` — it is not on the humanoid rig, and the AI loop's `if(ud.legL)` guard handles that.
- Must keep the `body.rotation.y = Math.PI` flip wrapper: the AI loop sets this bot's `rotation.y` directly rather than using `lookAt()` (`index.html:7029`), so without the flip the model faces away from its target.

- [ ] **Step 1: Rebuild**

Design direction: the current model reads as a person with a cow's head. A minotaur should read as *bull-first* — massive forward-slung shoulders, a chest deeper than it is wide, a head carried low and forward between the shoulders rather than perched on top, and horns as the widest point of the silhouette. Follow the Ghoul's note at `index.html:4470` for how that "shoulders high, head slung low" read was achieved there.

Preserve: overall height (~2.5 local units, so it stays consistent against the player's 1.7 eye height), the `hornMat`/`furMat`/`skinMat` three-way material break, ground contact at `y=0`.

- [ ] **Step 2: Run the audit**

Run: `python3 tools/audit/audit.py`

Expected: exit 0 — Minotaur `ok` on ground contact, zero orphans, zero coplanar pairs.

- [ ] **Step 3: Verify in the browser**

Play wave 4. Confirm the minotaur reads as a minotaur at a glance from across the map, that its front-block mechanic still triggers (shoot it head-on, then flank it — flank hits should do more), and that its capped turn rate still lets you circle it.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "Rebuild the Minotaur: bull-first silhouette

The old model read as a person with a cow's head - an upright human
torso with the bull confined to the skull. Rebuilt around forward-slung
shoulders with the head carried low between them and the horns as the
widest point, the same silhouette-first approach the Ghoul rebuild used.

Front-block mechanic and capped turn rate are untouched: both key off
skin==='minotaur', and the rotation.y flip wrapper is preserved."
```

---

## Task 13: Rebuild the Griffin

**Files:**
- Modify: `index.html:4008-4064` (`makeGriffin`)

**Interfaces:**
- Produces: `makeGriffin()` → `THREE.Group`, built facing **+Z** with no flip wrapper — this bot is turned by `mesh.lookAt()`, which already points a plain `Object3D`'s local +Z at its target.

- [ ] **Step 1: Rebuild**

Design direction: the wings are the whole silhouette and the current ones are three flat slabs per side laid nearly horizontal, so from the front the creature has almost no profile. Follow the Roc's note at `index.html:4557` — broad overlapping panels in a strong dihedral V — so the griffin reads as a raptor from any angle. The eagle front / lion rear split should be visible in *shape*, not only in colour.

Preserve: ground contact (talons at `y=0` — the old model floated 0.155), the white-head/tawny-body contrast, overall scale.

- [ ] **Step 2: Run the audit**

Run: `python3 tools/audit/audit.py` — expected exit 0.

- [ ] **Step 3: Verify in the browser**

Play wave 5. Confirm the griffin reads from the front as well as the side, and that its ranged-screech → melee flip still happens at 3.4 units.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "Rebuild the Griffin: wings that read from the front

Three near-horizontal flat slabs per side meant the creature had almost
no silhouette head-on. Rebuilt with broad overlapping panels in a strong
dihedral V, the same fix the Roc rebuild used, and the eagle/lion split
now reads in shape rather than only in colour.

Also lands its talons on the floor - the old model floated 0.155u."
```

---

## Task 14: Rebuild the Medusa

**Files:**
- Modify: `index.html:4066-4135` (`makeMedusa`)

**Interfaces:**
- Produces: `makeMedusa()` → `THREE.Group`, built facing **+Z**, no flip wrapper (turned via `lookAt()`).

- [ ] **Step 1: Rebuild**

Design direction: the snake-hair is the identifying cue and the current 12 tendrils are short and uniform, so they read as a spiky helmet. Make them longer, unevenly curled, and chain-built — and note the recurring bug class: a chained curve must step along its own segment's rotated direction vector, never a bare linear offset paired with a rotation. See the Hydra neck note (`index.html:4779`) and the Saif blade note (`index.html:5536`) for how that has bitten this file before.

The serpentine lower body should coil with real overlap rather than stacking boxes.

Preserve: ground contact, the tank role's visual weight (it has the highest grunt HP), the green-scale/gold-jewelry material break.

- [ ] **Step 2: Run the audit**

Run: `python3 tools/audit/audit.py`

Expected: exit 0. **The connectivity check is the important one here** — it is exactly the check that catches chained-segment tendrils rendering as floating shards.

- [ ] **Step 3: Verify in the browser**

Play wave 6 and confirm the elite Medusa reads correctly and its heavier melee still lands.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "Rebuild the Medusa: real snakes, real coils

Twelve short uniform tendrils read as a spiky helmet rather than a head
of snakes. They are chain-built now, stepping along each segment's own
rotated direction vector - the bug class this file has hit on the Hydra
necks, the Hydra tail, the Saif blade and the crossbow lath, and the one
the audit's connectivity check now guards.

The lower body coils with real overlap instead of stacked boxes."
```

---

## Task 15: Rebuild the Xiphos and Trident

**Files:**
- Modify: `index.html:5359-5382` (`makeXiphos`), `:5384-5400` (`makeTrident`)

**Interfaces:**
- Produces: both return `THREE.Group` with **byte-identical `userData`** to what they have today.

- [ ] **Step 1: Record the current userData**

Copy both `g.userData={...}` blocks verbatim into a scratch note. They go back unchanged — this task changes geometry only.

- [ ] **Step 2: Rebuild the Xiphos**

Currently 5 primitives, less detailed than the Pugio that was written to contrast with it. Its identifying cue is the **leaf shape**: a real xiphos widens past the guard before tapering to the point, and the current single straight cone misses that entirely.

Build: a leaf blade as chained segments that widen then taper (stepping along the direction vector, per the Saif note), a raised midrib down its length, a proper Greek cross-guard, and a ribbed grip with bone/ivory inlay for the light/dark break. Keep the khopesh convention — hand near `y=0`, blade rising upward.

Must stay visually distinct from the Pugio (cool steel, broad short blade, lobed grip) and the Saif (curved, gold furniture).

- [ ] **Step 3: Rebuild the Trident**

Currently 7 plain cylinders and cones in one flat bronze tone. Add: **barbs** on each prong (the identifying cue on any real fishing trident), a socketed ferrule where the head meets the shaft, cord binding at the socket, a butt-spike, and a two-tone bronze treatment so it is not one flat colour.

- [ ] **Step 4: Restore the userData blocks verbatim**

Diff against the scratch note from Step 1. Any difference is a balance change and must be reverted.

- [ ] **Step 5: Run the audit**

Run: `python3 tools/audit/audit.py`

Expected: exit 0. Weapons are in `ACTORS` only for connectivity/coplanarity, not ground contact — a held weapon has no floor.

- [ ] **Step 6: Verify in the browser**

Reach the Greek era and cycle to weapons 2 and 3. Confirm: both read clearly at first-person scale; neither clips the camera near plane; the Xiphos still swings and the Trident still fires with its tracer.

- [ ] **Step 7: Commit**

```bash
git add index.html
git commit -m "Rebuild the Xiphos and Trident

The Xiphos was 5 primitives - less detailed than the Pugio explicitly
written to contrast with it - and its straight cone blade missed the
weapon's one identifying cue: a xiphos is leaf-shaped, widening past the
guard before tapering. It now has that profile, a midrib, a cross-guard
and an inlaid grip.

The Trident was 7 plain cylinders in one flat bronze tone, with no barbs
- the identifying cue on any real trident. Barbs, a socketed ferrule,
cord binding, a butt-spike and a two-tone finish.

No balance changes: both userData blocks are unchanged."
```

---

## Task 16: Full-arc playthrough

**Files:** none — verification only.

- [ ] **Step 1: Run the audit one final time**

Run: `python3 tools/audit/audit.py`

Expected: exit 0, all three checks, run 5x for stability against the randomised builders.

- [ ] **Step 2: Play the whole game**

Run: `python3 -m http.server 8000`, open `http://localhost:8000`, and play from wave 1 through to Boss IV.

Confirm at each stage:
- Waves 1-3 + Nile wave + Boss I: grunts and the Colossus stand on the floor; the Colossus's walk cycle reads.
- Waves 4-6: Alexandria reads as a city; the Pharos dominates the opening view; cover is usable; all three creatures read at a glance.
- Boss II: the Hydra never wedges; its body undulates; the arena reads as Greek marble.
- Boss III: **the Champion walks** — this is the headline fix — and its feet are on the sand.
- Boss IV: the Ifrit King hovers with a bob and is not sunk into the courtyard.

- [ ] **Step 3: Commit any fixes, then open the PR**

```bash
git push -u origin greek-cairo-standards-remodel
gh pr create --title "Greek era: Cairo-standards remodel + map-wide boss ground/walk fixes" --body "$(cat <<'EOF'
Brings the Greek era up to the bar the Cairo and Giza rebuilds set, and fixes
ground-contact and walk-animation bugs affecting every boss in the game.

## Boss fixes (all eras)

Eight of the game's nine actor models were buried in or floating above their own
floor. The Colosseum Champion was worst at 0.9 units under the sand, with its
feet and greaves entirely below it — and it set `userData.legL/legR` to null, so
the shared leg animation skipped it and Boss III slid across the arena with rigid
legs. Two arenas also had floors topping out above the y=0 that `spawnBot()`
places every actor at.

Boss collision radius was a flat 1.2 regardless of model, so the Hydra — 3.1
units across and ~7.9 long — walked through the arena's columns and cover.

## Greek era

Alexandria had no materials of its own: the whole 70x54 map ran on `gravelTex`
plus six near-identical pale greys. It now has a Pentelic marble / painted
stucco / terracotta palette. The Pharos moved onto the spawn sightline, a stoa,
agora and townhouse block give the map a city, and cover goes from 7 pieces to
20+. All three creatures and both era weapons rebuilt.

## Tooling

`tools/audit/` — a py_mini_racer harness that executes `index.html`'s script body
headlessly and checks ground contact, connectivity and coplanarity. The first
automated check this project has had.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-Review

**Spec coverage.** Every section of the spec maps to a task: §4.2 → Tasks 2-6; §4.3 → Task 7; §4.4 → Tasks 8-10; §4.5 → Task 11; §4.6 → Tasks 12-14; §4.7 → Task 15; §5 → Tasks 1, 4, 16. The spec's six-task split became sixteen plan tasks because the spec's Task 1 contains five independently-reviewable changes and its creature task contains three independent rebuilds.

**Deviation from the spec, flagged.** The spec originally called the harness throwaway scratchpad tooling. It is committed to `tools/audit/` instead, because every task here uses it as its test gate and a throwaway tool cannot serve as a regression check across sixteen tasks. The spec has been updated to match.

**Known gap.** Tasks 9-14 specify design *direction* (what must read, which precedent to follow, what to preserve) rather than literal geometry. That is deliberate — model geometry is iterated against what it looks like on screen, and pre-writing 200 lines of speculative vertex positions would be false precision. Every one of those tasks is gated by the audit plus a named in-browser check, and each preserves an explicitly listed contract.
