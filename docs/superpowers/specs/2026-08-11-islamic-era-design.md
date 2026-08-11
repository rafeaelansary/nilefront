# Islamic Era (Mamluk Cairo) — Design

## Summary

NILEFRONT's roadmap chains historical Egyptian arcs: Pharaonic (pyramid) →
Greek/Ptolemaic → Roman → Islamic. The first three are fully built and wired;
Roman's Boss III (the Colosseum Champion) currently ends the game on defeat —
but with no map transition, just a victory banner over the now-empty Colosseum
arena, a dead end confirmed by in-browser playtest (see screenshot: player
stuck in the arena, "THE CHAMPION FALLS" banner, nowhere to go).

This spec adds the fourth and (per the current roadmap) final arc: **Mamluk-era
Cairo**. Beating the Colosseum Champion now transitions into the Cairo map
(waves 10-12) instead of ending the game; the new Boss IV, the **Ifrit King**,
becomes the actual final boss and win condition.

Prior work already stubbed the era's weapon loadout (uncommitted in
`index.html`): `makeCrossbow()` (Qaws al-Ziyar), `makeScimitar()` (Saif),
`makeNaftPot()` (naphtha grenade), and a `zellijeTex()` ground texture. None of
it is wired into any map, enemy, or wave logic yet — this spec covers building
and wiring the rest of the era around that existing loadout.

## Architecture

Reuses the exact swap pattern proven out for every prior era (see
`[[pyramid-arc-architecture]]` memory) — no new infrastructure:

- One `THREE.Group` for the overworld (`islamicOverworld`) and one for the
  boss arena (`ifritArena`), only one ever `scene.add`-ed at a time via the
  existing `clearWorldGroups()` helper (its group list gets both added).
- One collider array (`islamicColliders`) and one height-zone array
  (`heightZonesIslamic`) for the overworld, swapped in via
  `activeColliders`/`activeHeightZones`, following the same
  `addTarget`/`heightZoneTarget` repointing convention every prior era's
  world-building block uses.
- The boss arena is open-air (sky visible, no climbable zones — reuses
  `heightZonesOriginal` the same way `hydraArena`/`colosseumArena` do), not a
  dungeon: entered directly via a new `enterIfritArena()`, modeled on
  `enterColosseumArena()`.
- Weapon loadout: `islamicWeapons` (already declared) swapped in wholesale via
  a single `enterIslamicWorld(banner)` function, modeled on
  `enterRomanWorld(banner)` — one function that does world + lighting +
  loadout together, since (like Roman) this era is entered via an open
  transition rather than exiting a dungeon.
- Enemy skins carry model + behavior overrides on top of existing AI
  weaponTypes, per the established convention — no new AI code.

## Map — Mamluk Cairo

Built the same way as the Roman map (`buildRomanOverworld()`): a self-contained
IIFE that repoints `addTarget`/`heightZoneTarget`, builds with the existing
`block()`/`addBox()` helpers, then sweeps everything new into `islamicOverworld`.

Ground: `zellijeTex()` (already exists) as the base terrain texture — a
turquoise/cream geometric tile pattern, distinct from Roman's terracotta,
Greek's grey gravel, and the pyramid's tan sand.

Three landmarks, each a distinct silhouette from every earlier era's:
- **Citadel** — crenellated walls + towers, the map's centerpiece (echoing how
  the amphitheater/Colosseum anchored Roman).
- **Mosque** — a single dome + minaret (Sultan Hassan–style silhouette), the
  era's most visually distinct piece.
- **Khan/bazaar** — a souk of market stalls and awnings, giving the map a
  denser, more "lived-in" area to contrast the Citadel's open plaza.

## Enemies (waves 10–12)

Continues the mythical-creature convention (Greek: minotaur/griffin/medusa;
Roman: manticore/basilisk/warhound) rather than switching to historical
soldiers:

- **Ifrit** — ranged fire djinn. Reuses an existing ranged AI weaponType
  (the same pattern basilisk/griffin use), new skin + fire-colored tracer.
- **Ghoul** — fast melee. Reuses the existing melee weaponType (as
  mummy/minotaur/manticore do), tuned for speed over the era's other regular
  type, same role scarab/scorpion play as "fast" outliers.
- Ifrit/Ghoul alternate as the two regular-wave types, same structure as
  every prior era.
- **Roc** — one themed pack encounter per wave (like the Roman warhound pack:
  a single spawn call per wave, not looped into the regular roster), reusing
  the Griffin's dive-then-claw AI under a new skin/model.

New model functions: `makeIfrit()`, `makeGhoul()`, `makeRoc()`. New skin
config entries alongside the existing `minotaur`/`manticore`/etc. block.
Exact HP/count/speed numbers are tuned during implementation using the
established `waveDiff(n)` curve with an era-appropriate softening multiplier
(Roman used ×0.8; as the intended hardest era so far, Islamic starts around
×0.72–0.75 and gets adjusted by playtesting, same as every prior era's
numbers were).

## Boss IV — Ifrit King

Fought in the **Citadel courtyard** — an open-air arena (`ifritArena`,
`ifritColliders`), sky visible, fire braziers for atmosphere. Player keeps
the Islamic loadout (no weapon swap on entering the arena, same as
Hydra/Colosseum).

Special mechanic: periodic **telegraphed fire-meteor strikes** at the
player's position — a preview lands first, then damage after a beat, forcing
movement to dodge. This is a third distinct "boss tool" shape alongside
Colossus's proximity AOE quake (undodgeable by breaking line of sight) and
Champion's one-time add-summon (two tigers below 25% HP) — a ranged,
telegraphed hazard rather than either of those.

Spawned via the existing generic boss path in `spawnBossFight()`
(`bossNum===4` branch, `skin='ifritking'`), same as every prior boss.

## Wiring changes

- `WAVES` grows by 3 entries (waves 10-12); `ERA_START_WAVE` gets a 4th entry
  (`9`, where era 3 begins); `currentEra` now goes up to 3.
- Roman's Boss III (`bossNum===3`) victory no longer sets `gameWon` — it calls
  `enterIslamicWorld(banner)` and advances `currentEra`/`waveIdx` into wave
  10, the same shape `bossNum===2` (Hydra) already uses to hand off into
  Roman.
- Ifrit King (`bossNum>=4`) becomes the new `gameWon` trigger with the win
  banner.
- `respawnPlayer()`'s existing `currentEra>=2` Roman carve-out (Roman has no
  dungeon to route through, so it gets its own reset branch) extends to also
  cover era 3 via `enterIslamicWorld()`.
- Small adjacent fix: the wave HUD hardcodes `'/6'` regardless of the actual
  wave count (stale since Roman's addition took the total past 6). Corrected
  to reflect the real total (12) since this line is directly touched by the
  `WAVES` extension.

## Out of scope

- Dead code cleanup: there's an orphaned `ammit` skin / shabti-whelp
  minion-summon block left over from before the Hydra replaced the Ammit
  Companion as Boss II — it never fires anymore since no boss uses the
  `ammit` skin. Not touched by this spec; flagged for a separate cleanup pass
  if wanted.
- Any post-Islamic content (the roadmap currently ends at Islamic).

## Testing

No automated test suite exists for this game (browser/WebGL, no build step).
Verification is manual in-browser playtest per the project's UI-change
convention: walk the Cairo map, confirm all three landmarks render and
collide correctly, clear waves 10-12, confirm the Roc pack and Ifrit/Ghoul
alternation work, fight the Ifrit King (confirm the fire-meteor telegraph and
dodge window feel fair), confirm the win banner fires on defeat, and confirm
respawn-mid-era correctly returns to wave 10 rather than an earlier era.
