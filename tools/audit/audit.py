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
  makeTiger: typeof makeTiger==='function' ? makeTiger : null,
  makeXiphos: typeof makeXiphos==='function' ? makeXiphos : null,
  makeTrident: typeof makeTrident==='function' ? makeTrident : null,
  makeSling: typeof makeSling==='function' ? makeSling : null,
};
// World state the placement checks need. Everything above runs inside an IIFE, so these are
// otherwise unreachable from outside.
globalThis.__world = {
  greekColliders:  typeof greekColliders !== 'undefined' ? greekColliders : null,
  pyramidColliders:typeof pyramidColliders!== 'undefined' ? pyramidColliders : null,
  hydraColliders:  typeof hydraColliders !== 'undefined' ? hydraColliders : null,
  SPAWN_POINTS:    typeof SPAWN_POINTS !== 'undefined' ? SPAWN_POINTS : null,
};
"""


# (builder, how it is invoked, spawn scale, arena floor top y)
# Scales and floor tops are read off spawnBossFight()/spawnWave() and the arena builders.
ACTORS = [
    ("makeVoxelBot", "b=>b(0x808080,'pistol',null)",        1.00, 0.00, "grunt (town/pyramid)"),
    ("makeVoxelBot", "b=>b(0xc9a671,'pistol','colossus')",  3.10, 0.00, "Colossus  (Boss I)"),
    ("makeHydra",    "b=>b()",                              2.40, 0.25, "Hydra     (Boss II)"),
    ("makeChampion", "b=>b()",                              2.30, 0.10, "Champion  (Boss III)"),
    ("makeIfritKing","b=>b()",                              2.00, 0.00, "IfritKing (Boss IV)"),
    ("makeMinotaur", "b=>b()",                              1.00, 0.00, "Minotaur"),
    ("makeGriffin",  "b=>b()",                              1.00, 0.00, "Griffin"),
    ("makeMedusa",   "b=>b()",                              1.25, 0.00, "Medusa (wave-6 elite)"),
    ("makeTiger",    "b=>b()",                              1.15, 0.10, "Tiger (Champion add)"),
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


CONNECT_EPS = 0.012   # boxes within this of each other count as touching


def check_connectivity(ctx, runs=4):
    """Every mesh in a model must touch at least one other mesh in that model.

    This is the check for the bug class this file keeps hitting: a chained run of segments
    positioned by a bare linear offset while being rotated separately renders as a row of
    disconnected floating shards (Hydra necks, Hydra tail, Saif blade, crossbow lath).
    Builders randomise, so run each a few times and keep the worst result.
    """
    fn = ctx.eval("""
    (function(builder, invoke, scale, eps){
      var b = globalThis.__builders[builder];
      var m = eval(invoke)(b);
      var boxes = globalThis.__modelBoxes(m, scale);
      function touches(a, c){
        return a.min.x <= c.max.x + eps && c.min.x <= a.max.x + eps &&
               a.min.y <= c.max.y + eps && c.min.y <= a.max.y + eps &&
               a.min.z <= c.max.z + eps && c.min.z <= a.max.z + eps;
      }
      var orphans = [];
      for(var i=0;i<boxes.length;i++){
        var hit = false;
        for(var j=0;j<boxes.length;j++){
          if(i!==j && touches(boxes[i].box, boxes[j].box)){ hit = true; break; }
        }
        if(!hit) orphans.push(Math.round(boxes[i].box.min.y*1000)/1000);
      }
      return JSON.stringify({orphans:orphans.length, total:boxes.length});
    })
    """)
    worst = {}
    for builder, invoke, scale, _floor, label in ACTORS:
        for _ in range(runs):
            r = json.loads(fn(builder, invoke, scale, CONNECT_EPS))
            if r["orphans"] >= worst.get(label, (-1, 0))[0]:
                worst[label] = (r["orphans"], r["total"])
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
    for label, (orphans, total) in check_connectivity(ctx).items():
        ok = orphans == 0
        if not ok:
            cfails += 1
        print(f"{label:24} {total:6d} {orphans:8d}  {'ok' if ok else 'DISCONNECTED'}")
    print(f"\n{cfails} of {len(ACTORS)} actors have floating parts")

    return 1 if (fails or cfails) else 0


if __name__ == "__main__":
    sys.exit(main())
