# Gamla Uppsala — Sweden's third leg, and the end of the trip

**Date:** 2026-09-19
**Status:** built
**Arc:** Sweden (Viking Age). Follows the Fjord, which used to end the destination.

## Why a third leg

The Fjord ended on a jarl standing on his own deck, and that was a good ending to a sea
battle. It was not an ending to *Sweden*. The trip had been a trading town and then the
water, and both of those are places people sail **between** — so the arc was missing the
place they were sailing to.

Gamla Uppsala is that place: the cult centre of Svealand, Adam of Bremen's golden temple,
the grove beside it, and the three royal mounds. It also completes a shape the first two
legs had already started without finishing:

| leg | what it is about |
|---|---|
| Birka | the living — a town, its craftsmen, its harbour |
| the Fjord | the men — a jarl and three crews |
| **Uppsala** | **the dead** — a king who will not stay in his mound |

The draugr in Birka's grave field were never explained. This is where they come from.

## The field

One new world group, built in the same shape as the Fjord's: meshes added straight into
`uppsalaWorld` rather than scooped out of the scene the way Birka's are, so its twelve point
lights leave with the map instead of staying lit in whatever loads next.

Quartered, so nothing on it is scenery you run past:

- **North — the temple.** Gilded gables, the gold chain hung round the eaves, three idols in
  the porch (Odin, Thor, Freyr, in the order Adam gives them). Solid; it is the backdrop the
  last fight of the trip is staged against, not a building you go into.
- **West — the three royal mounds.** The middle one is climbable, by a worn path up its east
  face, and it is the only high ground in the leg. From the crown the whole blót ground is a
  shooting lane.
- **East — the sacred grove.** The evergreen nobody could name, the spring, and the offering
  poles with shields, horns and skulls on their crossbars.
- **South — the road you arrive on**, its rune stones, and the thing-place.
- **Centre — the blót ground**, open, between the braziers. Where the King is fought.

### Dusk, and why

The one deliberate break from the rest of the arc. Birka is a white noon and the Fjord a blue
afternoon; a third cold daylight map would read as the same field again. The sun is on the
horizon behind the temple, the snow holds the last of it, and **every other warm thing on
screen is a fire somebody lit** — which is what makes the boss's second phase possible at all.

## The fight

Three waves that walk the map inwards from its edges:

1. **The mounds answer.** Draugr out of the turf on the west, wargs out of the grove. Nothing
   throws; the mound path is right there. This is the wave that teaches you the high ground
   is worth having.
2. **The temple's own.** Hirdmen and nisser — the first ranged wave, fought in the open
   between the braziers where the bow and the seax both have work.
3. **What else is buried here.** Draugr again, berserkir up the road behind them, and a troll
   out of the tree line. The heaviest wave of the whole trip.

`UPPSALA_DIFF` is 1.50, over Birka's 1.35 and the Fjord's 1.25: it is the last leg of the
last destination on the board.

### The Mound King

3600 HP — the hardest thing in the game, a shade over the Ifrit King who ends the campaign.
He is built on the Jarl's own frame on purpose: same height, same mail, same stance, so you
recognise the shape of a Viking lord first and notice one beat later that everything on it is
wrong. Corpse-green skin over the bone, a jaw with nothing behind it, a crown where the helm
was, and the blue corpse-light Birka's draugr carry. His sword is broken off a hand above the
guard, and his left hand is empty — the Jarl's whole fight was a shield you had to get round,
so the arc's last enemy deliberately has no guard at all. He is not defending anything.

The house shape: one telegraphed hazard, one summon, one change at half health.

- **Grave-cold** — a frost patch where you are, dodged by moving, reaching 30. That number is
  chosen against the mound: the crown is 19.6 from him, so it is a good place to shoot from
  and not a safe one.
- **The mounds answer him** — draugr out of the same turf wave one used, capped at three live
  adds like every other summon in this game.
- **At half health he puts the fires out.** All twelve braziers and torches at once; the fog
  closes to 62 and the field drops to the blue nothing underneath it. What is left burning is
  the corpse-light in his sockets and the stone in his crown, which brighten as it happens —
  so the only thing you can clearly see is the thing hunting you. It is map state re-derived
  per stage exactly as the Fjord's plank is, so dying in the dark never leaves a lit wave's
  fight in an unlit field.

## The two things that were hard

**A square collider under a round mound.** The dome was drawn at its full radius and the
collider was the square inside that circle, so at the four flats you could walk a metre into
the hillside and stand chest-deep in turf. The fix is not a bigger box: the dome's base radius
is now the collider's own half-width, so they agree exactly at the flats and fall a little
short at the corners, and the wide part of the mound is a 0.34-tall toe — the one thing you
clip, and it passes under your feet rather than through your eyeline.

**A ramp rectangle is not a slope.** `getTerrainHeight()`'s continuity rule means a ramp zone
reads as sloped ground only to someone already at its height. Three of the first spawn points
landed inside the mound path's rectangle, where a man stands at y=0 *underneath* the deck of
the path he appears to be on. All fifteen points are now solved against the built map —
clear at a 1.2 radius, on true ground, off the ramp, at least 11 from the player's arrival and
5 from each other.

## Verification

`tools/audit/uppsalacheck.py`, 7 assertions:

- the path climbs to 6.20, all 81 sampled crown points are standable, and the mound cannot be
  stepped onto from any of its flanks
- all fifteen spawn points are clear, on the ground, and off the path
- all three waves spawn with nobody inside the field, and the troll in wave three is armoured
- the King stands clear of the scenery, his whole ±4 patrol is clear, and a flood fill of the
  walkable field from the respawn point reaches him
- the fires are lit through every wave and every re-entry, go out below half health, and go
  out only for him
- the crown is 19.6 from the King — inside grave-cold's 30 — and 6.2 above all fifteen spawns
- the whole trip in one run: `Birka w1 → w2 → Fjord w1 → w2 → w3 → Jarl → Uppsala w1 → w2 →
  w3 → Mound King → Cairo`

`fjordcheck.py`'s ending assertion was rewritten rather than deleted: the Jarl hands the trip
on to Uppsala now instead of sending the player home, and that handover is what it checks.
`audit.py` 0 of 36 on ground contact and floating parts, with the Mound King at 0 coplanar
faces across 77 meshes. `fullcheck.py` unchanged at 66 problem groups; `uppsalaWorld` is clean
on all five map checks at 481 meshes and 89 colliders.
