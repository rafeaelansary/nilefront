#!/usr/bin/env python3
"""Headless geometry audit for NILEFRONT's index.html.

Executes the game's whole script body inside py_mini_racer against a stubbed
THREE.js + DOM, then reads back real world-space bounding boxes to check:
  1. ground contact  - every actor model sits on its arena floor
  2. connectivity    - no mesh floats free of the rest of its model
  3. coplanarity     - no two sibling faces are near-coplanar (z-fighting)

Throwaway verification tooling; lives in the scratchpad, not the repo.
"""
import json
import pathlib
import re
import sys

from py_mini_racer import MiniRacer

HERE = pathlib.Path(__file__).parent
REPO = pathlib.Path(__file__).resolve().parents[2]


def extract_script(html_path):
    html = html_path.read_text()
    # the game is one inline <script> block; the first <script> is the three.js CDN tag
    blocks = re.findall(r"<script>(.*?)</script>", html, re.S)
    if not blocks:
        raise SystemExit("no inline <script> block found")
    return max(blocks, key=len)


def build_ctx(html_path):
    ctx = MiniRacer()
    ctx.eval((HERE / "three_stub.js").read_text())
    script = extract_script(html_path)
    # The script ends by kicking off animate() and wiring listeners. requestAnimationFrame is a
    # no-op stub so that terminates, but anything that does throw must not lose the model builders
    # already defined above it -- so run it as one function body with the builders hoisted onto
    # globalThis first via a trailing export block.
    # The script ends by kicking off animate() and wiring listeners. Anything that throws partway
    # must NOT cost us the builders defined above it, so the try/catch goes INSIDE the IIFE and the
    # export block runs after it. Function declarations inside the try block still hoist to the
    # enclosing function scope under sloppy-mode Annex B semantics, so they stay reachable.
    # No try/catch wrapper around the script body: `const`/`let` are block-scoped, so wrapping it
    # in a try block would hide every top-level declaration (greekColliders, SPAWN_POINTS, ...) from
    # the export block below. The script loads cleanly against this stub, so a throw here is a real
    # regression and should surface as one.
    ctx.eval("globalThis.__err=null; (function(){\n" + script + "\n" + EXPORTS + "\n})();")
    err = ctx.eval("globalThis.__err")
    return ctx, err


# Runs at the END of the game script, inside its scope, so every builder is in scope here.
EXPORTS = """
globalThis.__builders = {
  makeVoxelBot: typeof makeVoxelBot==='function' ? makeVoxelBot : null,
  makeMinotaur: typeof makeMinotaur==='function' ? makeMinotaur : null,
  makeGriffin: typeof makeGriffin==='function' ? makeGriffin : null,
  makeMedusa: typeof makeMedusa==='function' ? makeMedusa : null,
  makeHydra: typeof makeHydra==='function' ? makeHydra : null,
  makeChampion: typeof makeChampion==='function' ? makeChampion : null,
  makeIfritKing: typeof makeIfritKing==='function' ? makeIfritKing : null,
  makeSwampStalker: typeof makeSwampStalker==='function' ? makeSwampStalker : null,
  makeWereJaguar: typeof makeWereJaguar==='function' ? makeWereJaguar : null,
  makeMonolithVanguard: typeof makeMonolithVanguard==='function' ? makeMonolithVanguard : null,
  makeMudGolem: typeof makeMudGolem==='function' ? makeMudGolem : null,
  makeTiger: typeof makeTiger==='function' ? makeTiger : null,
  makeXiphos: typeof makeXiphos==='function' ? makeXiphos : null,
  makeTrident: typeof makeTrident==='function' ? makeTrident : null,
  makeSling: typeof makeSling==='function' ? makeSling : null,
  makeBow: typeof makeBow==='function' ? makeBow : null,
  makeKhopesh: typeof makeKhopesh==='function' ? makeKhopesh : null,
  makeWasScepter: typeof makeWasScepter==='function' ? makeWasScepter : null,
  makeHarpoon: typeof makeHarpoon==='function' ? makeHarpoon : null,
  makeJavelin: typeof makeJavelin==='function' ? makeJavelin : null,
  makePugio: typeof makePugio==='function' ? makePugio : null,
  makeGreekFire: typeof makeGreekFire==='function' ? makeGreekFire : null,
  makeCrossbow: typeof makeCrossbow==='function' ? makeCrossbow : null,
  makeScimitar: typeof makeScimitar==='function' ? makeScimitar : null,
  makeNaftPot: typeof makeNaftPot==='function' ? makeNaftPot : null,
  makeColossus: typeof makeColossus==='function' ? makeColossus : null,
  makeMummy: typeof makeMummy==='function' ? makeMummy : null,
  makeJackal: typeof makeJackal==='function' ? makeJackal : null,
  makeScarab: typeof makeScarab==='function' ? makeScarab : null,
  makeScorpion: typeof makeScorpion==='function' ? makeScorpion : null,
  makeShabti: typeof makeShabti==='function' ? makeShabti : null,
  makeHippo: typeof makeHippo==='function' ? makeHippo : null,
  makeCrocodile: typeof makeCrocodile==='function' ? makeCrocodile : null,
  makeWarHoundPack: typeof makeWarHoundPack==='function' ? makeWarHoundPack : null,
  makeWarHoundUnit: typeof makeWarHoundUnit==='function' ? makeWarHoundUnit : null,
  makeManticore: typeof makeManticore==='function' ? makeManticore : null,
  makeBasilisk: typeof makeBasilisk==='function' ? makeBasilisk : null,
  makeIfrit: typeof makeIfrit==='function' ? makeIfrit : null,
  makeGhoul: typeof makeGhoul==='function' ? makeGhoul : null,
  makeRoc: typeof makeRoc==='function' ? makeRoc : null,
};
// World state the placement checks need. Everything above runs inside an IIFE, so these are
// otherwise unreachable from outside.
globalThis.__world = {
  greekColliders:  typeof greekColliders !== 'undefined' ? greekColliders : null,
  pyramidColliders:typeof pyramidColliders!== 'undefined' ? pyramidColliders : null,
  hydraColliders:  typeof hydraColliders !== 'undefined' ? hydraColliders : null,
  nileColliders:   typeof nileColliders !== 'undefined' ? nileColliders : null,
  romanColliders:  typeof romanColliders !== 'undefined' ? romanColliders : null,
  islamicColliders:typeof islamicColliders!== 'undefined' ? islamicColliders : null,
  SPAWN_POINTS:    typeof SPAWN_POINTS !== 'undefined' ? SPAWN_POINTS : null,
  heightZonesGreek:   typeof heightZonesGreek   !== 'undefined' ? heightZonesGreek   : null,
  heightZonesPyramid: typeof heightZonesPyramid !== 'undefined' ? heightZonesPyramid : null,
  heightZonesRoman:   typeof heightZonesRoman   !== 'undefined' ? heightZonesRoman   : null,
  heightZonesIslamic: typeof heightZonesIslamic !== 'undefined' ? heightZonesIslamic : null,
  heightZonesMexico:  typeof heightZonesMexico  !== 'undefined' ? heightZonesMexico  : null,
  heightZonesOriginal:typeof heightZonesOriginal!== 'undefined' ? heightZonesOriginal: null,
};
// Every world group and its collider array, for the whole-game sweep.
globalThis.__worlds = {};
[['overworld','colliders'],['pyramidOverworld','pyramidColliders'],['greekOverworld','greekColliders'],
 ['romanOverworld','romanColliders'],['islamicOverworld','islamicColliders'],
 ['mexicoOverworld','mexicoColliders'],
 ['dungeon','dungeonColliders'],['pyramidDungeon','pyramidDungeonColliders'],
 ['greekDungeon','greekDungeonColliders'],['nileWorld','nileColliders'],
 ['hydraArena','hydraColliders'],['colosseumArena','colosseumColliders'],
 ['ifritArena','ifritColliders']].forEach(function(pair){
  var g=null, c=null;
  try { g = eval(pair[0]); } catch(e) {}
  try { c = eval(pair[1]); } catch(e) {}
  if(g) globalThis.__worlds[pair[0]] = {group:g, colliders:c};
});
globalThis.__loadouts = {};
['originalWeapons','pyramidWeapons','nileWeapons','greekWeapons','romanWeapons','islamicWeapons','mexicoWeapons'].forEach(function(n){
  try { globalThis.__loadouts[n] = eval(n); } catch(e) {}
});
"""


# (builder, how it is invoked, spawn scale, arena floor top y)
# Scales and floor tops are read off spawnBossFight()/spawnWave() and the arena builders.
ACTORS = [
    ("makeVoxelBot", "b=>b(0x808080,'pistol',null)",        1.00, 0.00, "grunt (town/pyramid)"),
    ("makeColossus", "b=>b()",                              3.10, 0.00, "Colossus  (Boss I)"),
    ("makeHydra",    "b=>b()",                              2.40, 0.00, "Hydra     (Boss II)"),
    ("makeChampion", "b=>b()",                              2.30, 0.00, "Champion  (Boss III)"),
    ("makeIfritKing","b=>b()",                              2.00, 0.00, "IfritKing (Boss IV)"),
    ("makeMummy",    "b=>b()",                              1.00, 0.00, "Mummy"),
    ("makeJackal",   "b=>b()",                              1.00, 0.00, "Jackal"),
    ("makeScarab",   "b=>b()",                              0.85, 0.00, "Scarab swarm"),
    ("makeScorpion", "b=>b()",                              1.30, 0.00, "Scorpion stalker"),
    ("makeShabti",   "b=>b()",                              0.55, 0.00, "Shabti whelp"),
    ("makeHippo",    "b=>b()",                              1.30, 0.00, "Hippo"),
    ("makeCrocodile","b=>b()",                              1.00, 0.00, "Crocodile"),
    ("makeMinotaur", "b=>b()",                              1.00, 0.00, "Minotaur"),
    ("makeGriffin",  "b=>b()",                              1.00, 0.00, "Griffin"),
    ("makeMedusa",   "b=>b()",                              1.25, 0.00, "Medusa (wave-6 elite)"),
    ("makeTiger",    "b=>b()",                              1.15, 0.00, "Tiger (Champion add)"),
    # Roman-era regular roster. All three spawn through spawnBot() with no opts.scale, so they run at 1.0.
    ("makeWarHoundPack","b=>b()",                           1.00, 0.00, "War hound pack"),
    ("makeManticore","b=>b()",                              1.00, 0.00, "Manticore"),
    ("makeBasilisk", "b=>b()",                              1.00, 0.00, "Basilisk"),
    # La Venta roster (Olmec Mexico). All four spawn at 1.0 except the golem, which is scaled up.
    ("makeSwampStalker","b=>b()",                           1.00, 0.00, "Swamp Stalker"),
    ("makeWereJaguar","b=>b()",                             1.00, 0.00, "Were-Jaguar"),
    ("makeMonolithVanguard","b=>b()",                       1.00, 0.00, "Monolith Vanguard"),
    ("makeMudGolem", "b=>b()",                              1.25, 0.00, "Mud Golem"),
]

TOLERANCE = 0.02  # a model may sit at most this far above/below its floor


def ground_contact(ctx):
    rows = []
    for builder, invoke, scale, floor, label in ACTORS:
        js = (
            "(function(){"
            f"  var b = globalThis.__builders['{builder}'];"
            f"  var m = ({invoke})(b);"
            f"  var bb = globalThis.__modelBounds(m, {scale});"
            "   return JSON.stringify({minY:bb.min.y, maxY:bb.max.y, n:bb.count});"
            "})()"
        )
        r = json.loads(ctx.eval(js))
        gap = r["minY"] - floor
        rows.append((label, scale, floor, r["minY"], gap, r["n"]))
    return rows


CONNECT_EPS = 0.004   # surface samples within this of another mesh count as joined


def check_connectivity(ctx, runs=4):
    """Every mesh in a model must touch at least one other mesh in that model.

    This is the check for the bug class this file keeps hitting: a chained run of segments
    positioned by a bare linear offset while being rotated separately renders as a row of
    disconnected floating shards (Hydra necks, Hydra tail, Saif blade, crossbow lath).
    Builders randomise, so run each a few times and keep the worst result.
    """
    fn = ctx.eval("""
    (function(builder, invoke, scale, eps){
      var m = eval(invoke)(globalThis.__builders[builder]);
      return JSON.stringify(globalThis.__connectivity(m, scale, eps));
    })
    """)
    worst = {}
    for builder, invoke, scale, _floor, label in ACTORS:
        for _ in range(runs):
            r = json.loads(fn(builder, invoke, scale, CONNECT_EPS))
            n = len(r["orphans"])
            if n >= worst.get(label, (-1, 0, []))[0]:
                worst[label] = (n, r["total"], r["detail"])
    return worst


# 0.005: a gap under about 5mm at this scale is what actually shimmers on screen. Anything looser
# flags every small part nested inside a larger one, where the coincident faces are interior and
# never visible.
COPLANAR_EPS = 0.005
# 0.12: the shared face area has to be big enough to actually be seen fighting.
OVERLAP_MIN  = 0.12


def check_coplanar(ctx, runs=3):
    fn = ctx.eval("""
    (function(builder, invoke, scale, eps, omin){
      var m = eval(invoke)(globalThis.__builders[builder]);
      return JSON.stringify(globalThis.__coplanar(m, scale, eps, omin));
    })
    """)
    worst = {}
    for builder, invoke, scale, _floor, label in ACTORS:
        for _ in range(runs):
            hits = json.loads(fn(builder, invoke, scale, COPLANAR_EPS, OVERLAP_MIN))
            if len(hits) >= worst.get(label, (-1, []))[0]:
                worst[label] = (len(hits), hits[:4])
    return worst


def main():
    html_path = REPO / "index.html"
    ctx, err = build_ctx(html_path)
    if err:
        print(f"script threw during load: {err}", file=sys.stderr)
        return 1

    names = json.loads(ctx.eval(
        "JSON.stringify(Object.keys(globalThis.__builders||{}).filter(k=>globalThis.__builders[k]))"
    ))
    missing = json.loads(ctx.eval(
        "JSON.stringify(Object.keys(globalThis.__builders||{}).filter(k=>!globalThis.__builders[k]))"
    ))
    if missing:
        print("builders MISSING:", missing, file=sys.stderr)
        return 1
    print(f"{len(names)} builders reachable\n")

    print(f"{'model':24} {'scale':>6} {'floorY':>7} {'minY':>8} {'gap':>8}  {'meshes':>6}  verdict")
    print("-" * 86)
    fails = 0
    for label, scale, floor, min_y, gap, n in ground_contact(ctx):
        if abs(gap) <= TOLERANCE:
            verdict = "ok"
        elif gap < 0:
            verdict = f"BURIED {abs(gap):.3f}u"
            fails += 1
        else:
            verdict = f"FLOATS {gap:.3f}u"
            fails += 1
        print(f"{label:24} {scale:6.2f} {floor:7.2f} {min_y:8.3f} {gap:+8.3f}  {n:6d}  {verdict}")

    print(f"\n{fails} of {len(ACTORS)} actors fail ground contact (tolerance {TOLERANCE}u)")

    print(f"\n{'model':24} {'meshes':>6} {'orphans':>8}  verdict")
    print("-" * 52)
    cfails = 0
    for label, (orphans, total, detail) in check_connectivity(ctx).items():
        ok = orphans == 0
        if not ok:
            cfails += 1
        note = '' if ok else '  ' + ', '.join(f"{d['type'][:-8]}@y{d['y']}" for d in detail)
        print(f"{label:24} {total:6d} {orphans:8d}  {'ok' if ok else 'DISCONNECTED'}{note}")
    print(f"\n{cfails} of {len(ACTORS)} actors have floating parts")

    print(f"\n{'model':24} {'z-fight pairs':>14}  worst gaps")
    print("-" * 62)
    zfails = 0
    for label, (n, hits) in check_coplanar(ctx).items():
        if n:
            zfails += 1
            note = "  " + ", ".join(f"{h['axis']}@{h['gap']}" for h in hits)
        else:
            note = "  ok"
        print(f"{label:24} {n:>14}{note}")
    print(f"\n{zfails} of {len(ACTORS)} actors have near-coplanar faces")

    return 1 if (fails or cfails or zfails) else 0


if __name__ == "__main__":
    sys.exit(main())
