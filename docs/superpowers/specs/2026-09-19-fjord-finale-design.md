# The Fjord's finale — the third keel, and the Jarl

**Date:** 2026-09-19
**Status:** built
**Arc:** Sweden (Viking Age). Completes the leg specified in
`2026-09-18-fjord-sea-battle-design.md`, and with it the whole destination.

## What was missing

The Fjord shipped as a world, a duel and a boarding: two waves on two hulls, ending on the
Skerry Troll standing on the crew's own deck. Three things the original spec asked for were
not in it.

1. **The arena never grew twice.** "The walkable area grows by one deck when the crossing
   opens" happened once, at the plank, and then the fight had nowhere further to go.
2. **The boss was a monster.** The whole arc's language is men in ships — a hall, a harbour,
   a crew, a raid — and it ended on a troll, which is the one thing out here that nobody
   sailed.
3. **The troll had no job.** It was built for a wave that was still being designed, then
   promoted to boss because there was nothing else to promote.

## What it is now

Three waves and a boss, each fought at a different distance, which is the only variable this
map has and the only one it needs.

| | the fight | the ship |
|---|---|---|
| 1 | **The duel** — three hirdmen throwing across 5.2 of water | his black sail out in the fog |
| 2 | **The boarding** — the plank drops; three hirdmen and two berserkir | he starts rowing in |
| 3 | **The shield wall** — his hird hold the middle hull, the Skerry Troll holds the gangway | lashed alongside |
| ☠ | **JARL HÁKON**, 3000 HP, at his own stern | his deck is the arena |

The troll is demoted from boss to champion, which is the job the model was built for. The
Jarl is a new actor, and he is the arc's last word on the same silhouette it has been using
throughout.

## The three decisions worth recording

**The Jarl's hull is the third growth, and it moves.** Every other hull out here is scenery
or floor. His is built where he waits — out past the skerries, heaving on the full swell for
the whole duel — rows in over seven and a half seconds when the boarding plank drops, and
lashes on for wave three. The lash is a re-derivable STATE, not an event, exactly as the
plank is: arriving, dying, respawning and `/tp`-ing to the boss all put his ship where the
current wave says it should be. Nothing about it is a new mechanism — a mesh's visibility, a
rail collider spliced out, two more rectangles in the list everything walks on.

**He is built as the hirdman's superior, not as a second monster.** Same helm-and-round-shield
shape, one rank up, separated at distance by colour instead of form: gold on the helm and the
shield boss, a madder-red cloak, mail to the knee. His face is a gilded mask, so the one enemy
in the arc who never shows you a face is the one whose shield you have to get round.

**The shield wall is arithmetic, not a system.** At half health he sets his shield and keeps
it there; frontal damage halves through the same facing-arc rule the minotaur's lowered head
and the Monolith Vanguard's stone shield already use. The number it meets is the Dane Axe's
`armourPierce`, which is ×2 against a boss. The axe therefore comes through the wall at
exactly full damage and nothing else does. The last enemy of the arc is answered by the arc's
first weapon, or by going round him on a hull 4.9 wide.

## Deviations from the original spec

- **No new shielded spearman.** The spec asked for "an enemy that must be broken rather than
  out-run or out-ranged". The hirdman already carries a painted round shield and a sheaf of
  spears, and the enemy that must be *broken* turned out to be the troll — armoured, in a
  gangway, with nowhere to go round him. A second shielded man would have been a reskin of
  one enemy fighting next to it.
- **The troll is the champion, not the jarl's bodyguard in the boss fight.** Adds fought
  alongside a boss on a 4.9-wide deck are a crowd, not a fight. He holds wave three instead,
  which is where the player has time to deal with him properly.
- **Sweden still comes home to Cairo.** There is no hub at this end of the trip to sell
  passage onward and the Aztec Market is where the ticket was bought. Only the banner is its
  own.

## Two real defects the build surfaced

Both were found by the headless harness, and both were in the *existing* map rather than in
the new content:

- A chase AI walks a straight line, and a straight line at a man on another deck walks into
  the rail **beside** the gangway. With two hulls the one enemy who crossed started amidships
  and fell into the gap by luck. With three, the boss met the rail four metres from the only
  way off his ship and slid along it at the rate of the z component of a heading that was
  almost all x — which looks exactly like a boss who has decided not to fight you. Anyone who
  must leave his deck to reach you now walks to the gangway first.
- The rail gap was 1.90 either side of amidships and the plank is 1.9 wide, so a 0.95-radius
  body standing on the plank's own edge grazed the rail and stopped a metre and a half short
  of the deck. The gap is a hole in the collider only, so it is 2.10 now.

## Verification

`tools/audit/fjordcheck.py`, 15 assertions, all green — six of them new:

- wave three lashes the third ship on, and **only** wave three (checked from both ends,
  including that returning to the duel sends the whole thing back out to sea)
- every point of his spawn pool is on his deck and clear at the 1.1 radius a 1.9-wide troll
  needs, and no two are inside each other
- the Jarl spawns clear of his own ship, and a flood fill of the walkable floor from the
  respawn point reaches within 0.07 of him
- the shield wall as arithmetic: 50 of 100 from the front, 185 of the axe's own 185 through
  it, 100 of 100 from behind
- a death at the Jarl stands you back up on the middle deck — you keep the ship you took
- the whole ladder in one run: `3 -> 5+plank -> 5+plank+lash -> 1+plank+lash -> Cairo`

`audit.py`: 0 of 35 on ground contact and floating parts, with the Jarl at 0 near-coplanar
faces across 81 meshes. `fullcheck.py`: `fjordWorld` at 370 meshes with no coplanar faces, no
floating scenery and no collider overlaps; the whole-game problem count unchanged at 66.
