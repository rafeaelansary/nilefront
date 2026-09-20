# China — Xiangyang and Yamen, the next destination after Sweden

**Date:** 2026-09-20
**Status:** approved design, not yet implemented
**Arc:** a new trip, sold from the Cairo booth alongside Mexico and Sweden. China only —
Kyushu/Japan (the placeholder's dashed leg) is explicitly deferred, not built here.

## What this is

Two legs, Yuan-conquest-of-Song-China, 1267–1279:

1. **Xiangyang** — the siege the Mongols spent six years breaking, finally cracked with
   counterweight trebuchets. A walled river-fortress, bombarded.
2. **Yamen** — the naval battle that ended the Song dynasty, 1279. Song's fleet chained
   hull-to-hull into one floating fortress; the Mongols burned it.

`DESTINATIONS` already carries a placeholder for this — `{flag:'🐉', name:'China & Japan',
era:'Yuan China to Kyushu · 1271–1281', price:70, ready:false, leg:{lon:133, lat:33}}` — a
dashed second leg to Kyushu. This spec builds the China half only and leaves that entry
`ready:false` until Japan exists; the booth card's era text and dashed leg stay as a visible
promise of what completes the trip later, exactly as Mexico's Aztec Market already sells
Sweden ahead of it being built.

## Why two legs, and why these two

Every trip so far pairs a lower-key opener with a harder finale on a different kind of
ground: La Venta's plaza → Tenochtitlan's precinct (temple to temple, but a harder one);
Birka's hall → the Fjord's decks (land to water). China's pyramid/Greek/Roman/Islamic
predecessors are all *also* "assault a walled city" — so the thing that has to carry the
distinction here is not the shape, it's each leg's era-specific military technology, which
neither Mexico nor Sweden had reason to lean on:

- **Xiangyang** is the siege that ends with the counterweight trebuchet (the "Hui-hui
  Pao") breaking a wall that five years of the ordinary kind could not. That is a real,
  specific, game-able escalation — not "more soldiers," but a new siege engine entering
  the fight partway through.
- **Yamen** is the battle Chinese gunpowder weapons (fire lances, thrown thunderclap
  bombs) were already a real part of, on a set piece — a chained, burning fleet — that is
  the structural *inverse* of the Fjord rather than a reskin of it: the Fjord's arena
  **grows** as the player wins; Yamen's **burns and shrinks**, the same way the Nile Wave
  was built as the Fjord's own inverse before it existed.

No new infrastructure is required for the trip/leg structure itself — `SWEDEN_LEGS` and
`MEXICO_LEGS` are the proof this scales to a third destination on the same machinery
(`travelTo()`, `advanceTripLeg()`, `curLeg()`, `onWave`/`onBoss`). What's new is a fourth
loadout, two world builds, two rosters, and the fire-spreading mechanic Yamen needs.

## Weapons — the CHINA loadout

Three weapons, the same one-heavy-melee / one-ranged / one-thrown shape every loadout so
far has used (Dane Axe / Hunnish Bow / Throwing Seax; Khopesh / Was Scepter / Bow, etc.):

- **Zhanmadao** — a heavy two-handed "horse-chopping saber." The armour-answering melee
  weapon, `armourPierce` role, same job the Dane Axe does against the draugr and now the
  troll: the one melee weapon that reads full damage through an armoured enemy.
- **Repeating Crossbow** (Zhuge Nu) — the primary ranged weapon. Multi-bolt, fires faster
  and hits softer than a single bow; distinct in *feel* from every bow/sling/gun already in
  the game, which all fire one projectile at a time.
- **Thunderclap Bomb** (Zhen Tian Lei) — thrown gunpowder grenade, the utility/thrown slot
  the Throwing Seax and the Naft Pot fill elsewhere. Doubles as the visual/thematic bridge
  into Yamen, where the same family of weapon is what the battle is actually about.

Built the same way every other loadout is: `CHINA_WEAPONS` array, `switchToChinaLoadout()`-
style swap on `enter()`, reusing `part()`/`metalMatP()`/`voxMat()` and the existing
muzzle/viewmodel conventions. No new weapon *system* — `armourPierce`, `cleaveArc` (if the
Zhanmadao wants one, the way the Dane Axe does) and thrown-projectile arcs all already
exist.

## Leg 1 — Xiangyang (the siege)

### The world

A walled Song river-fortress on the Han River, under bombardment. Quartering, in the shape
every world build in this game uses (see Gamla Uppsala's now-deleted quartering comment for
the pattern, or Birka's): walls and a gatehouse on the approach side, the town inside them,
the river along one edge (a flat plane, not a Fjord-scale swell — this is not a water leg),
and a Mongol siege line outside with the trebuchets themselves as scenery — visibly lobbing
at the wall, not a mechanic the player operates.

**The wall breach is the one piece of "map mutates per wave" this leg needs**, on the exact
pattern `fjordSetPlank`/`fjordSetLash` and `uppsalaSetFires` already proved: a section of
wall is a collider and a mesh; `xiangyangSetBreach(open)` swaps both, re-derived per wave
(never an event) so entry, death, and `/tp` all agree. Early waves are fought outside the
walls or at the gatehouse; the breach opens for a later wave and the fight moves inside the
town for the boss.

### Roster

- **Song infantry** (dao, spear) — the baseline, analogous to the hirdman: a melee-capable
  regular.
- **Song crossbowman** — ranged regular, analogous to the nisse/hirdman's throwing half:
  holds the walls and towers.
- **One armoured elite** — a Song garrison guard in heavier lamellar, the enemy the
  Zhanmadao's `armourPierce` is *for*, the same role the draugr and the troll play
  elsewhere. Not a monster — Song China gets no mythological wave-elite the way Greek and
  Roman eras do; the escalation here is tactical (the breach, the walls), not bestiary.
- **Boss: a Song siege commander** (invented, not a specific historical figure — Xiangyang's
  real defender, Lü Wenhuan, eventually surrendered rather than falling in a last stand, and
  turning that into a boss fight the player kills would be both inaccurate and tasteless).
  Fought at the gatehouse or in the breach itself once it opens; a mechanic built from the
  siege itself is preferred over an invented gimmick — e.g. calling down a real trebuchet
  strike, telegraphed the way every other boss hazard already is, rather than a shield or a
  frost patch that has nothing to do with why this fight is happening.

## Leg 2 — Yamen (the finale)

### The world

Song's fleet, chained bow-to-stern into a single floating fortress in the Pearl River
Delta — the real historical detail, and the whole reason this leg does not look like the
Fjord. Where the Fjord is three separate hulls the player crosses between as they open,
Yamen starts **connected**: the walkable floor is already every deck at once, junk-style
Chinese ships reusing the Fjord's proven water system (`fjordWaveAt`-equivalent swell,
vertex-coloured foam, hulls that ride it) rather than inventing a new one.

**The fire is the leg's one mechanic**, and it is the Fjord's "arena grows" beat inverted:
sections of the chained fleet catch fire over the course of the fight (telegraphed the same
way a boss hazard is — a patch that ignites after a warning beat) and, once burning, join a
`yamenBurning` list the way `uppsalaFires` tracked lit braziers, except walking IS damage
here rather than light going out. Late in the fight most of the rear fleet is alight and the
player is pushed toward the flagship at the bow, which is where the boss is — pressure from
**behind**, the mirror of the Fjord's pressure from **ahead**.

### Roster

- **Song marine** (dao/spear, shipboard version of the Xiangyang infantry stat block reused,
  not reinvented — the way the hirdman's javelin already does double duty as both a thrown
  and melee weapon across the Fjord's two phases).
- **Song naval crossbowman** — same relationship to the marine that the crossbowman has to
  the infantry at Xiangyang.
- **Boss: the Song commander with the dragon banner** — a named naval commander (invented,
  matching the Xiangyang boss's treatment; not Zhang Shijie, and absolutely not the child
  emperor Lu Xiufu carried into the sea, which stays out of this game entirely), fought on
  the flagship at the bow. Dragon iconography on the banner and the ship's prow pays off the
  trip's own `🐉` flag without requiring a literal monster — the same move the Xiuhcoatl
  Bearer already makes (a human bearer, a mythic emblem). Boss mechanic should read off the
  fire itself where possible: e.g. the commander can set a section of his own flagship
  alight to cut off an escape route, rather than an unrelated gimmick.

## Build order

Same discipline the Fjord doc used, and for the same reason: the water/world is what can
only be judged by looking at it, so it goes in first and standalone.

1. `CHINA_WEAPONS` loadout (Zhanmadao, Repeating Crossbow, Thunderclap Bomb) — buildable and
   testable (`fire/reload/scope/switch`) before any world exists to fire them in.
2. Xiangyang world: walls, gatehouse, town, river, trebuchet scenery — reachable via `/tp`,
   nothing hostile, breach closed.
3. `xiangyangSetBreach()` and the wave ladder outside the walls.
4. The armoured elite, then the breach opening and the fight moving inside.
5. The Xiangyang boss (siege commander + trebuchet-strike hazard).
6. Yamen world: the chained fleet, reusing the Fjord's water system wholesale.
7. The fire mechanic (`yamenSetFire`-style, re-derivable per wave) on a *cold* map first —
   provably re-derivable before anything is fighting on it, the same order the Fjord's plank
   and lash went in.
8. Yamen's roster (marine, naval crossbowman).
9. The Yamen boss (dragon-banner commander + fire-based mechanic).
10. `CHINA_LEGS`, the `DESTINATIONS` entry (`ready:true`, era text trimmed to China only,
    Kyushu leg left in place but still dashed/unreached), hub/`/tp` wiring.

Each step is playable and verifiable on its own, on the existing harness: `audit.py` for
every new actor and weapon, `fullcheck.py` for both new worlds, a new `xiangyangcheck.py`
and `yamencheck.py` (or one `chinacheck.py` covering both legs, matching `fjordcheck.py`'s
shape) for the leg-specific assertions — breach state, fire state, spawn pools solved
against the built maps, the whole trip playing through in one run.

## Cost, honestly

This is a full destination, not a leg addition — closer in size to the whole of Sweden
(Birka + Fjord + Uppsala, later cut) than to any single piece of it. A new loadout, two
world builds each on the scale of Birka or the Fjord, two rosters, one new per-leg mechanic
each (the breach, the fire), two bosses. Expect this to run several sessions, the same
estimate the Fjord doc gave honestly for one leg alone.

## Open questions

None blocking implementation of the plan above. Left to be settled by building and playing,
not decided here: exact wave counts and difficulty steps for both legs, the trebuchet
strike's numbers, how much of the chained fleet is on fire at what wave, and the two
bosses' HP relative to the troll's 3600 (Yamen, as the trip's true finale, should land at or
above it; Xiangyang should land below it, the way the Fjord's Jarl once sat under the Mound
King).
