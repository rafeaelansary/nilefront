# Greek era: Cairo-standards remodel + map-wide boss ground/walk fixes

**Date:** 2026-08-27
**Status:** Approved design, ready for implementation planning
**Scope:** Ptolemaic Alexandria overworld, Hydra arena (Boss II), Greek era enemies,
Greek era weapons, and the actor ground-contact / walk-rig system across all four bosses.

---

## 1. Background

Two prior commits established a quality bar this repo calls the "Cairo standard":

- `2d90067` — *Rebuild the Cairo map: hero landmark, density, and a working palette*
- `b85ac35` — *Rebuild Giza's landmarks, fix orphaned scenery, close out map-wide z-fighting*

Both rebuilt a map that had the same failure: monuments scattered on a single flat
colour band, with nothing on the player's opening sightline. Two further commits
(`ee2d718`, `fc74e97`) set the matching bar for models and weapons.

The Greek era (Ptolemaic Alexandria, waves 4–6, Boss II) never got that pass. It
received shoreline and distant-scenery work in `b85ac35`, but its palette, density
and vernacular architecture were untouched, and its creature and weapon models
predate the Islamic-era redesign standard.

Separately, an audit of the actor rig turned up real, currently-shipping bugs in how
every boss meets the ground and animates while walking. Those are not Greek-specific
and are in scope.

## 2. The standard, stated explicitly

Distilled from the four commits above, a map/model meets the bar when:

1. **A hero landmark stands on the spawn sightline.** The first thing the player sees
   on entering identifies the place. Cairo got the Bab gate; Giza got the Sphinx at ~5x
   its old size.
2. **The palette has real tonal range**, carried by purpose-built canvas textures
   rather than a wash of near-identical `voxMat` hex colours. Giza gained four new
   texture builders in one commit for exactly this reason.
3. **Density reads as a place.** Giza's note: *"The old map had ~20 objects on a 60x60
   plain and read mostly as empty sand."*
4. **Vernacular buildings carry the density**; monuments are accents. Cairo's townhouses,
   bazaar and sabil do the work its mosque and Citadel cannot.
5. **Models have no floating parts and no coplanar faces.** Curved or chained runs step
   along a real direction vector derived from the segment's own rotation — the repeated
   bug class in this file (Hydra necks, Hydra tail, Saif blade, crossbow lath).
6. **Each object has one identifying silhouette cue** and a deliberate light/dark
   material break, and contrasts on purpose with the equivalent object in other eras.

## 3. Findings

### 3.1 Greek overworld vs. the standard

**Palette.** The entire 70x54 map is `gravelTex` grey plus six near-identical pale
greys: `0xe0dbc9`, `0xc4bfaf`, `0xc7c2b3`, `0xc5c0b2`, `0xb8b3a4`, `0xb3ac9c`. Cairo
has `zellijeTex` / `cairoDustTex` / `citadelStoneTex`; Giza has `gizaSandTex` /
`graniteTex` / `basaltTex` / `limestoneCasingTex`. **Greek has no purpose-built texture
of its own** — it borrows `gravelTex` (authored for a generic road surface) for both its
ground and its paths. This is the map's defining problem: it reads as one flat grey wash.

**Hero landmark.** `switchToGreekWorld()` spawns the player at `(0, 1.7, 10)` facing −Z
(`index.html:5678`). Down that sightline sit `pylonGate(0,-2)` (8u tall) and
`library(3,-11)`. The Pharos Lighthouse — the single object that identifies Alexandria —
is at `(27,21)`, behind the player's right shoulder. This is precisely the failure both
Cairo and Giza were rebuilt to correct.

**Density and building types.** ~45 objects across 70x54, and **no vernacular architecture
at all**: no houses, no agora, no stoa, no market. The map is monuments on gravel.
Playable cover inside the clamp is 2 broken statues, 2 fallen columns and 3 rock outcrops.

### 3.2 Verified bugs

All figures below are computed from the geometry in `index.html`, not estimated.

**Arena floor tops are inconsistent.** `spawnBot()` places every actor at `y=0`
(`index.html:4999`) with no terrain sampling. Floor tops:

| Arena | definition | floor top |
|---|---|---|
| Pyramid dungeon | `pblock(R*2,1,...,0,-0.5,0)` (`:1163`) | `0.00` correct |
| Ifrit arena | `floor.position.set(0,-0.2,0)`, h=0.4 (`:1499`) | `0.00` correct |
| Colosseum arena | `floor.position.set(0,-0.1,0)`, h=0.4 (`:1396`) | **`+0.10`** |
| Hydra arena | `hblock(R*2,0.6,...,0,-0.05,0)` (`:1332`) | **`+0.25`** |

**Models are seated below their own origin.** Lowest local-Y vertex per model, times the
scale it actually spawns at:

| Model | lowest local Y | spawn scale | world Y | vs. its floor |
|---|---|---|---|---|
| Champion (Boss III) | −0.35 | 2.3 | −0.805 | **0.905u buried** |
| Colossus (Boss I) | −0.10 | 3.1 | −0.310 | 0.310u buried |
| grunts (`makeVoxelBot`) | −0.10 | 1.0 | −0.100 | 0.100u buried |
| Griffin | +0.155 | 1.0 | +0.155 | **floats 0.155u** |
| Medusa | +0.097 | 1.25 | +0.121 | floats 0.121u |

The Champion's case is the worst: its feet (`foot.position.y = -0.28`, h=0.14) and
greaves (`greave.position.y = -0.04`, h=0.4) are both entirely below the arena floor.

**Walk rigs.**

- `index.html:4915` sets `g.userData.legL = null; g.userData.legR = null` on the
  Champion. The AI loop's leg animation (`index.html:7100`) is guarded by `if(ud.legL)`,
  so it is skipped entirely. **Boss III glides across the arena with rigid legs and
  buried feet.**
- The Hydra has no rig either — it slides with a completely static body.
- `const walk = Math.sin(t*7 + b.t*3) * (b.moving?1:0)` (`index.html:7099`). `b.moving`
  is a hard 0/1 flip, set for bosses by `if(distToPlayer>4){ b.moving=1 } else b.moving=0`
  (`index.html:6992`). Crossing that threshold snaps the legs from mid-stride to rest in
  a single frame — a visible pop on every approach, on every boss with a leg rig.

**Boss collision radius is a constant.** `const R = b.boss?1.2:0.55*(b.scale||1)`
(`index.html:6988`). The Hydra's trunk is 1.3 wide at scale 2.4 — 3.1u across, half-width
1.56 — and roughly 7.9u long nose to tail. At `R=1.2` its body and tail pass straight
through the arena's broken columns, ruined walls and fallen blocks.

### 3.3 Greek weapons vs. the standard

- **Xiphos** (`index.html:makeXiphos`) — 5 primitives: sphere pommel, cylinder grip, box
  guard, one 4-sided cone blade. The Roman **Pugio** was explicitly written to contrast
  with it and has *more* detail (midrib, lobed waisted grip, two-tone steel). The Xiphos
  is currently the least detailed blade in the game, and its straight cone misses the
  weapon's one identifying cue: a real xiphos is *leaf-shaped* — it widens past the guard
  before tapering to the point.
- **Trident** — 7 plain cylinders and cones. No barbs (the identifying cue on any real
  fishing trident), no socket ferrule where head meets shaft, no binding, no butt-spike,
  and a single flat bronze tone with no light/dark break.
- **Sling** — already rebuilt from a reference image with correct band mathematics.
  Needs polish only, not a rebuild.

## 4. Design

### 4.1 Ordering rationale

The palette work comes **first**, before landmark and density work, because every object
added in those later steps is *made of* these materials. Building the density pass on the
current grey wash and then re-texturing means authoring the same geometry's materials
twice. This ordering was explicitly approved.

### 4.2 Task 1 — Ground contact and walk rigs (all eras)

Not Greek-specific, but it gates the Hydra arena work, so it goes first.

- **Normalise arena floors** so every one tops out at `y=0`, matching the pyramid dungeon
  and Ifrit arena. Colosseum: `-0.1 → -0.2`. Hydra platform: `-0.05 → -0.3`, with the
  stone lip below it moved in step so the two don't invert.
- **Re-seat every model** whose lowest vertex is not within a small tolerance of `y=0` at
  its spawn scale: Champion, Colossus / `makeVoxelBot`, Griffin, Medusa, plus anything the
  audit harness turns up. Fix by moving the offending parts, not by offsetting the group —
  a group offset breaks the marker sprite and chest-height raycast origins.
- **Give the Champion a real leg rig.** Restructure its thigh/greave/foot into two
  `THREE.Group`s pivoted at the hip, assigned to `userData.legL` / `legR`, matching the
  `makeVoxelBot` convention so the existing animation code drives it with no AI-loop change.
- **Give the Hydra and Ifrit King idle motion.** The Hydra is a serpent — it should get a
  body undulation and neck sway rather than legs. The Ifrit King floats, so a hover bob.
  Both driven from the same `walk` term so they respond to movement.
- **Ease `b.moving`** into a continuous 0..1 factor instead of a hard flip, so leg swing
  ramps down over ~0.2s rather than snapping.
- **Derive boss collision radius from the model's bounding box** at spawn scale rather
  than the constant `1.2`, stored on the bot data at spawn time.

### 4.3 Task 2 — Greek texture set and palette

Four new texture builders, following the existing `_mkCanvas` / power-of-two convention so
`_finish()` mipmapping stays legal:

- `pentelicMarbleTex()` — warm-white marble with fine grey veining and a faint golden cast
  (real Pentelic marble weathers gold, which is what distinguishes it from the map's
  current dead grey).
- `paintedStuccoTex()` — the polychromy that actually covered Greek public architecture:
  ochre, Greek-blue and oxblood-red bands over lime plaster. This is the map's colour source.
- `greekRoofTileTex()` — terracotta pan-and-cover tiling, seen edge-on from the ground so
  it needs the ridged profile, not a flat orange.
- `harbourFlagstoneTex()` — large worn quay slabs for the waterfront and agora paving,
  distinct from `gravelTex`'s loose chips.

Then repalette the existing landmarks (Pharos, Library, Temple of Poseidon, pylon gate,
obelisks, altar) off the six flat greys and onto these, keeping each building's silhouette
unchanged so the change is purely tonal.

### 4.4 Task 3 — Greek overworld: landmark, density, cover

- **Hero landmark.** Reposition the Pharos from `(27,21)` to stand on the −Z spawn
  sightline, and raise it from its current ~17u to roughly 26–30u so it dominates the
  opening view the way Giza's rebuilt Sphinx does. It must stand beyond the pylon gate,
  not between the player and it, so the gate reads as a near-frame — the same composition
  Giza uses with its broken gate and pyramids. The Heptastadion causeway moves with it so
  the lighthouse still connects visibly to the city. Because the Pharos currently anchors
  the harbour corner, the waterfront needs a replacement silhouette (a quay warehouse
  block or shipsheds) so that corner does not become the new empty sightline.
- **Vernacular density.** An agora quarter — a stoa (long colonnaded market hall), market
  stalls, and a block of flat-roofed Greek townhouses. These are what the map is missing;
  they carry density the way Cairo's townhouses and Khan bazaar do, and they give the
  street grid a reason to exist.
- **Cover pass.** Bring total object count inside the clamp from ~45 to roughly 90–110,
  in line with Cairo's density on a comparable footprint, with at least 20 of those being
  usable combat cover (chest-height or taller, with a collider) distributed across the
  playable area rather than clustered at the edges. Current usable cover is 7 objects.

All new geometry registers colliders through the existing `addBox` / `addTarget` mechanism
and is built inside `buildGreekOverworld()` so the group sweep picks it up unchanged.

### 4.5 Task 4 — Hydra arena

Repalette onto the new Greek textures; apply the floor fix from Task 1; and thicken/reposition
cover so it still functions against the Hydra's corrected (much larger) collision radius —
cover that the boss can no longer walk through changes the fight's geometry.

### 4.6 Task 5 — Greek enemies (ground-up rebuild)

Minotaur, Griffin and Medusa rebuilt from scratch to the Ifrit/Ghoul/Roc standard, keeping
their names, roles and combat mechanics exactly as they are. Specifically preserved:

- `skin==='minotaur'` drives the facing-based front-block mechanic in `damageBot` and the
  capped turn rate in the AI loop.
- `skin==='griffin'` / `weaponType==='javelin'` drives the ranged-to-melee mode flip.
- `skin==='medusa'` drives the heavier melee damage.
- Every model must keep `userData.bodyMeshes` and `userData.marker` populated the same way,
  since hit detection and the through-wall marker depend on them.

Design direction per creature: silhouette first, one unmistakable identifying cue, a real
light/dark material break, and ground contact at `y=0` verified by the harness.

### 4.7 Task 6 — Greek weapons

- **Xiphos** — rebuild with the leaf-shaped blade profile (widening past the guard, then
  tapering), a raised midrib, a proper Greek cross-guard, and a ribbed or wrapped grip with
  bone/ivory inlay for the light/dark break. Must stay visually distinct from both the Pugio
  and the Saif.
- **Trident** — rebuild with barbed prongs, a socketed ferrule at the head/shaft joint, cord
  binding, a butt-spike, and a two-tone bronze treatment.
- **Sling** — polish only.

Every weapon's `userData` block (damage, fireRate, magSize, muzzleZ, pos, recoil, and the
Sling's `slingAnim` rig references) is preserved exactly. **No balance changes in this work.**

## 5. Verification

A `py_mini_racer` harness in the scratchpad — the technique already used for the `b85ac35`
z-fighting sweep, and this project's established approach for hard JS questions here.

It stubs `THREE` (Group, Mesh, BoxGeometry, CylinderGeometry, ConeGeometry, SphereGeometry,
Vector3, materials, lights) with enough fidelity to track parent/child transforms, then
instantiates every creature, boss and weapon builder and computes real world-space
bounding boxes.

Assertions:

1. **Ground contact** — for every actor model, `minY * spawnScale` sits within tolerance of
   its arena's floor top. No model buried, none floating.
2. **No near-coplanar sibling faces** — the same overlap sweep `b85ac35` used to go from
   ~190 flagged overlaps to zero. Run repeatedly, since several builders use `Math.random()`.
3. **No disconnected parts** — every mesh in a model must overlap or touch at least one
   other mesh in that model. This is the check that would have caught the Hydra-neck and
   Saif-blade bugs before playtest.

The harness is throwaway tooling and lives in the scratchpad, not the repo.

Beyond the harness, the game is loaded in a browser and the Greek arc played through
waves 4–6 and Boss II, plus each other boss fight reached via the debug path, to confirm
the walk rigs read correctly in motion.

## 6. Out of scope

- The `greekDungeon` chamber (`index.html:1231`). Boss II uses the Hydra arena; the dungeon
  is unreachable dead code. Confirmed out of scope.
- Any balance, damage, HP or wave-composition change.
- The Roman and Islamic maps, except where Task 1's ground/walk fixes necessarily touch
  their bosses and arenas.
- The uncommitted anisotropy/mipmapping work already in the working tree, which is
  independent and should be committed separately.

## 7. Risks

- **Single-file scale.** `index.html` is 7,165 lines and every era is built by sweeping
  `scene.children` into a group. New geometry must be added inside the correct IIFE, or it
  gets swallowed by the wrong map — the exact bug `b85ac35` had to fix for the distant-ground
  plane and skyline.
- **Rebuilding creatures risks hitboxes.** Hit detection reads `userData.bodyMeshes`, so a
  rebuilt model with a different bounding volume changes how easy an enemy is to hit even
  with damage numbers untouched. The harness checks geometry; playtest is what checks feel.
- **Boss radius change alters fights.** Giving the Hydra its true radius means it can no
  longer clip through cover — which is correct, but it makes the arena genuinely tighter.
  Task 4's cover pass is what compensates, and the two must land together.
