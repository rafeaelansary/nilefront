#!/usr/bin/env python3
"""Does the harness see instanced geometry?

brickWall() -- the game's only InstancedMesh -- builds a wall as cols*rows bricks
placed with setMatrixAt(). If the stub drops those per-instance transforms, the
whole wall measures as ONE brick sitting at the wall's centre, which is usually
mid-air. Every such wall then reads as floating scenery, and anything resting on
one loses its support and reads as floating too.

This asserts the stub reports a wall at its true size, so that class of false
positive cannot come back.

    python3 tools/audit/instancecheck.py
"""
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from audit import build_ctx  # noqa: E402

REPO = HERE.parents[1]

# w, h, thickness, and the y the wall is centred on
CASES = [
    (6.0, 3.0, 0.3, 1.5, 0.0, "plain wall, 6x3"),
    (4.0, 2.4, 0.25, 1.2, 0.0, "narrower wall"),
    (6.0, 3.0, 0.3, 1.5, 0.7854, "wall rotated 45 degrees"),
]

TOL = 0.12  # bricks are inset 6% of a cell, so the union falls just short of w/h


def main():
    ctx, err = build_ctx(REPO / "index.html")
    if err:
        print(f"boot error: {err}", file=sys.stderr)
        return 1

    fn = ctx.eval("""
    (function(w,h,th,y,rotY){
      var g = globalThis.__builders.brickWall(w,h,th,0x808080,0,y,0,rotY);
      var boxes = globalThis.__worldBoxes(g);
      var min={x:Infinity,y:Infinity,z:Infinity}, max={x:-Infinity,y:-Infinity,z:-Infinity};
      var instanced = 0, counted = 0;
      boxes.forEach(function(b){
        if(b.mesh.isInstancedMesh){ instanced++; counted += (b.mesh.count||0); }
        min.x=Math.min(min.x,b.box.min.x); min.y=Math.min(min.y,b.box.min.y); min.z=Math.min(min.z,b.box.min.z);
        max.x=Math.max(max.x,b.box.max.x); max.y=Math.max(max.y,b.box.max.y); max.z=Math.max(max.z,b.box.max.z);
      });
      return JSON.stringify({
        meshes: boxes.length, instanced: instanced, instances: counted,
        sx: max.x-min.x, sy: max.y-min.y, sz: max.z-min.z,
        ymin: min.y, ymax: max.y
      });
    })
    """)

    hdr = (f"{'case':26} {'instances':>9} {'wide':>8} {'want':>7} "
           f"{'tall':>8} {'want':>7} {'base y':>8}  verdict")
    print(hdr)
    print("-" * len(hdr))

    fails = 0
    for w, h, th, y, rot, label in CASES:
        r = json.loads(fn(w, h, th, y, rot))
        # Turning a wall about y does not shrink it, it just spreads it across both ground axes:
        # the AABB of a w x th box rotated by rot is exactly this. A 6-wide wall at 45 degrees is
        # therefore ~4.4 on each axis, not 6, and comparing against w would fail a correct answer.
        c, s = abs(math.cos(rot)), abs(math.sin(rot))
        want_x = w * c + th * s
        bad = []
        if r["instances"] == 0:
            bad.append("NO INSTANCES RECORDED")
        if abs(r["sx"] - want_x) > TOL:
            bad.append(f"WIDTH {r['sx']:.3f} != {want_x:.3f}")
        if abs(r["sz"] - (w * s + th * c)) > TOL:
            bad.append(f"DEPTH {r['sz']:.3f} != {w * s + th * c:.3f}")
        if abs(r["sy"] - h) > TOL:
            bad.append(f"HEIGHT {r['sy']:.3f} != {h}")
        # the wall is centred on y, so it must reach down to y - h/2
        if abs(r["ymin"] - (y - h / 2)) > TOL:
            bad.append(f"BASE {r['ymin']:.3f} != {y - h / 2}")
        if bad:
            fails += 1
        print(f"{label:26} {r['instances']:>9} {r['sx']:>8.3f} {want_x:>7.2f} "
              f"{r['sy']:>8.3f} {h:>7} {r['ymin']:>8.3f}  "
              f"{'; '.join(bad) if bad else 'ok'}")

    print()
    if fails:
        print(f"{fails} of {len(CASES)} FAILED — the harness is not seeing instance transforms.")
        print("Every brickWall in the game is invisible to the world sweeps at its real size.")
        return 1
    print(f"all {len(CASES)} ok — instanced walls measure at their true extent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
