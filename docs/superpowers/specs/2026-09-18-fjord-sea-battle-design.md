# The Fjord — a Viking sea battle as Sweden's second leg

**Date:** 2026-09-18
**Status:** approved design, not yet implemented
**Arc:** Sweden (Viking Age). Follows Birka, which is complete at two waves.

## What this is

A boarding action fought on the decks of lashed longships in the Mälaren archipelago,
entered by clearing Birka. Two phases: hold your own deck against ships that grapple on,
then cross onto the last one and clear it.

It is the Viking arc's counterpart to the Nile Wave, and it is deliberately built as that
wave's **inverse**. The Nile Wave is a shrinking siege — you cannot move, you have one
weapon, the boat degrades under you, and you hold until it is over. This is an advance:
the arena **grows** as you win, you keep your whole loadout, and the pressure comes from
having nowhere to stand rather than from something eating the floor. Two set pieces on
water in one game have to differ in their verbs, not just their props.

## Why a leg and not a third Birka wave

`SWEDEN_LEGS` is already a list. A leg carries its own world, roster, spawn pools,
difficulty step, HUD name and boss, and `advanceTripLeg()` already crosses from one to the
next with a banner (`pending='legcross'`). Mexico runs La Venta → Tenochtitlan on exactly
this machinery and the Egypt campaign swaps maps three times mid-run.

So Birka stays a clean two-wave leg. Clearing it carries the player out onto the water,
and the sea fight gets its own wave ladder and its own boss without any of it being
crammed into Birka's roster or spawn pools.

**No new infrastructure is required for the structure.** Everything below is content and
one new world group.

## The world

New `fjordWorld` group and `fjordColliders` array, built by an IIFE in the same shape as
`buildBirka()`, entered by `enterFjordWorld()` modelled on `enterSwedenWorld()`:
world swap, lighting, loadout, garrison, all in one call.

### Water — the part that has to actually be good

Every water surface in the game today is a flat box with a ripple texture, and the entire
animation is `position.y = baseY + sin(t*1.5 + phase)*0.03` plus an emissive pulse
(see `waterSurfaces` in the animate loop). That is fine for a courtyard pool and it will
not carry a sea battle. The requirement here is explicit: the water and the terrain have
to be good enough to look at.

1. **Real swell.** A segmented plane, ~64x64, displaced every frame by a sum of three or
   four directional waves of differing wavelength, amplitude and heading. Roughly 4k
   vertex writes per frame, which is negligible next to the draw calls the map already
   makes. One shared function `fjordWaveAt(x, z, t) -> {y, nx, nz}` is the single source
   of truth for the surface — every consumer below reads it, so nothing can ever drift
   out of sync with the visible water.
2. **Colour from shape, not from a texture.** Vertex colours (`vertexColors: true` is
   supported on the r128 Lambert material the game already uses): deep slate in the
   troughs, pale grey-green on the shoulders, whitening to foam on the steepest crests.
   Steepness comes from the same function's gradient, so foam appears where the water is
   actually steep rather than wherever a texture happens to be bright.
3. **The ships ride it.** The single biggest win, and the thing most often missed: each
   hull samples `fjordWaveAt()` at its own position to drive heave, pitch and roll. Static
   ships on moving water read as broken; ships lifting and rolling *in the same swell*
   sell the scene on their own. Lashed hulls sample at their own centres, so grappled
   ships work against each other exactly as real ones do.
4. **The deck moves, the floor does not.** The player's ship rolls visually; the camera
   takes a heavily damped share of it (target ~25%), and the collision plane stays flat.
   Full camera roll on a deck is nauseating and would fight the movement code; none at all
   makes the scene a diorama. The damping factor is a tuning knob, not a fixed constant.
5. **Foam collars.** A ring of white geometry riding each hull at the waterline, so a ship
   is joined to the sea rather than sitting on it.

### Terrain — the archipelago

Birka is on Lake Mälaren, so the setting is the archipelago: bare granite skerries with
snow caps and a few wind-bent pines, two or three larger wooded islands, receding into
fog. None of it is walkable and none of it is a collider — it exists for parallax, for
depth, and to say where the player is. Heavier fog than Birka, with the far ships coming
out of it.

Lighting continues Birka's cold northern key (pale sky, low sun, snow bounce) so the two
legs read as one journey, but colder and flatter over open water.

## The fight

### Phase A — hold your deck

The player starts amidships on their own longship. Enemy ships row in out of the fog and
grapple: one at first, then two at once. Raiders come over the rails.

The deck is about three units wide with no cover but the mast and the shield rail. This is
what makes Birka's loadout pay off in a way the town never quite did:

- the **Dane Axe**'s `cleaveArc` is built for a line of men on a narrow deck
- the **Hunnish Bow**'s charged shot has a real job while a ship is still closing
- the **Throwing Seax** is the answer to the scramble once they are aboard

Going over the side is death, handled the way the Nile Wave already handles sinking —
`damagePlayer(9999)` — so no new fall or drowning system is needed.

### Phase B — counter-board

The last ship grapples and stays. The player crosses onto it and clears it forward, stem
to stern, ending on the leg's boss at the enemy stern. The walkable area grows by one deck
when the crossing opens.

### Roster

- **Berserkr** — already built (`makeBerserkr`), already Birka's wave-2 enemy, and the
  frenzy reads even better on a deck where backing away is not an option.
- **Troll** — already built (`makeTroll`), currently staged in `SWEDEN_STATS` and fielded
  nowhere. A jarl's champion on the last deck is a far better home for it than another
  ground wave, and it is why the model was built ahead of a wave to put it in.
- **One new type: a shielded spearman** who holds the rail. The roster's gap is an enemy
  that must be *broken* rather than out-run or out-ranged — something the axe's
  `armourPierce` answers and the seax does not.
- **Boss:** the enemy jarl, at the stern of the last ship. Ends the Sweden trip.

## Build order

The water and the archipelago are built **first, as a standalone piece the player can walk
out and look at**, before any fighting goes in. Two reasons: it is the part carrying the
whole set piece, and it is the part that can only be verified by rendering it and looking,
so it needs the most iteration and should not be blocked behind a fight controller.

1. Water system + archipelago + lighting, reachable via `/tp`, nothing hostile in it.
2. The player's longship, riding the swell, with the deck walkable and the sides lethal.
3. Enemy ships: approach, grapple, lash. Still nothing aboard them.
4. Phase A — the hold, with the existing berserkr.
5. The shielded spearman.
6. Phase B — the crossing, and the widened arena.
7. The jarl, and the troll as his champion.

Each step is playable on its own and each is verifiable by the existing harness
(`audit.py` for any new actor, `fullcheck.py` for the new map, `bugcheck.py` for the leg).

## Cost, honestly

This is the largest single piece of the arc — larger than the berserkr and the troll
together. `nileWorld` is 4399 meshes; three or four longships plus an archipelago is
perhaps 1200–1800, plus a wave system, plus a two-phase fight controller. It is several
sessions of work, and the water specifically should be expected to need two or three
visual passes, because it can only be judged by looking at it.

## Open questions

None blocking. Tuning values called out above (roll damping, wave amplitude, how many
ships, the difficulty step over Birka) are all to be settled by playing it, not decided
here.
