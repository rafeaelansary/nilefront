#!/usr/bin/env python3
"""Which meshes in a model are z-fighting, and where.

fullcheck.py counts z-fights per model; it cannot tell you which two boxes are at fault, which
makes a count of 132 unactionable. This prints every fighting pair with both boxes' world-space
extents and the axis and gap they fight on, so a pair can be matched back to the `ab(...)`/`part(...)`
call that built it.

    python3 tools/audit/zfdetail.py                  # every weapon, worst first
    python3 tools/audit/zfdetail.py --actors         # every actor instead
    python3 tools/audit/zfdetail.py --actors Mummy   # just these (substring, case-insensitive)
    python3 tools/audit/zfdetail.py --summary        # counts only
    python3 tools/audit/zfdetail.py --exact          # only faces on exactly the same coordinate
    python3 tools/audit/zfdetail.py --under=0.002    # only pairs closer than this

A pair reading `gap 0` is two faces at exactly the same coordinate: the depth buffer has nothing to
separate them and they flicker at every distance and every scale. A pair with a small non-zero gap
may never be visible -- on a weapon held 0.4 from the camera it certainly is not (see the note in
fullcheck.py), but on an actor seen across a map at 60+ units it is, so for actors the whole list
is live.

Actors are measured at the scale they actually spawn at, and several builders randomise, so each
is built a few times and the worst run is reported.
"""
import sys, json, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from audit import build_ctx, COPLANAR_EPS, OVERLAP_MIN, ACTORS  # noqa: E402
from fullcheck import HELD_OVERLAP_MIN                          # noqa: E402

# The pair-finding half, shared by both modes: it takes a built model and returns the fighting pairs
# plus the boxes they name. Identical rule to __coplanar in three_stub.js -- deliberately, since the
# whole point is to explain a number that check produced -- with the box extents kept so a pair can
# be identified rather than just counted.
PAIRS_JS = """
globalThis.__zfPairs = function(root, scale, xeps, xomin, floorY){
  var drawn = function(m){
    if(m.visible === false) return false;
    var mt = m.material;
    if(mt && !Array.isArray(mt)){
      if(mt.depthWrite === false) return false;
      if(mt.transparent && (mt.opacity === 0)) return false;
    }
    return true;
  };
  var boxes = globalThis.__modelBoxes(root, scale).filter(function(b){ return drawn(b.mesh); });
  var AX = ['x','y','z'];
  var pairs = [];
  for(var i=0;i<boxes.length;i++) for(var j=i+1;j<boxes.length;j++){
    var cmp = globalThis.__comparableBoxes(boxes[i].mesh, boxes[i].box, boxes[j].mesh, boxes[j].box);
    if(!cmp) continue;
    var a = cmp[0], c = cmp[1];
    for(var k=0;k<3;k++){
      var ax=AX[k], u=AX[(k+1)%3], v=AX[(k+2)%3];
      var ou = Math.min(a.max[u],c.max[u]) - Math.max(a.min[u],c.min[u]);
      var ov = Math.min(a.max[v],c.max[v]) - Math.max(a.min[v],c.min[v]);
      if(ou < xomin || ov < xomin) continue;
      var oa = Math.min(a.max[ax],c.max[ax]) - Math.max(a.min[ax],c.min[ax]);
      if(oa <= 0) continue;
      var sides = [[a.min[ax],c.min[ax],'min'],[a.max[ax],c.max[ax],'max']];
      for(var s=0;s<sides.length;s++){
        var d = Math.abs(sides[s][0]-sides[s][1]);
        if(floorY !== null && floorY !== undefined && ax === 'y' && sides[s][2] === 'min'
           && Math.abs(sides[s][0]-floorY) < 0.02 && Math.abs(sides[s][1]-floorY) < 0.02) continue;
        if(d < xeps){
          pairs.push({i:i, j:j, axis:ax, side:sides[s][2],
                      gap:Math.round(d*100000)/100000,
                      at:Math.round(sides[s][0]*100000)/100000,
                      ta:boxes[i].mesh.geometry.type, tb:boxes[j].mesh.geometry.type});
        }
      }
    }
  }
  var r = function(v){ return Math.round(v*100000)/100000; };
  var used = {}, bx = {};
  pairs.forEach(function(p){ used[p.i]=1; used[p.j]=1; });
  Object.keys(used).forEach(function(n){
    var b = boxes[n];
    bx[n] = {min:[r(b.box.min.x),r(b.box.min.y),r(b.box.min.z)],
             max:[r(b.box.max.x),r(b.box.max.y),r(b.box.max.z)],
             t:b.mesh.geometry.type};
  });
  return {total: boxes.length, pairs: pairs, boxes: bx};
};
"""

ACTORS_JS = """
(function(builder, invoke, scale, xeps, xomin, floorY){
  var m = eval(invoke)(globalThis.__builders[builder]);
  return JSON.stringify(globalThis.__zfPairs(m, scale, xeps, xomin, floorY));
})
"""

DETAIL_JS = """
(function(xeps, xomin){
  var out = [];
  Object.keys(globalThis.__loadouts).forEach(function(ln){
    var arr = globalThis.__loadouts[ln];
    if(!arr) return;
    arr.forEach(function(w){
      var ud = w.userData || {};
      // Same filter __coplanar applies, so indices here line up with the boxes it compared.
      var drawn = function(m){
        if(m.visible === false) return false;
        var mt = m.material;
        if(mt && !Array.isArray(mt)){
          if(mt.depthWrite === false) return false;
          if(mt.transparent && (mt.opacity === 0)) return false;
        }
        return true;
      };
      var boxes = globalThis.__modelBoxes(w, 1).filter(function(b){ return drawn(b.mesh); });
      var AX = ['x','y','z'];
      var pairs = [];
      for(var i=0;i<boxes.length;i++) for(var j=i+1;j<boxes.length;j++){
        var cmp = globalThis.__comparableBoxes(boxes[i].mesh, boxes[i].box, boxes[j].mesh, boxes[j].box);
        if(!cmp) continue;
        var a = cmp[0], c = cmp[1];
        for(var k=0;k<3;k++){
          var ax=AX[k], u=AX[(k+1)%3], v=AX[(k+2)%3];
          var ou = Math.min(a.max[u],c.max[u]) - Math.max(a.min[u],c.min[u]);
          var ov = Math.min(a.max[v],c.max[v]) - Math.max(a.min[v],c.min[v]);
          if(ou < xomin || ov < xomin) continue;
          var oa = Math.min(a.max[ax],c.max[ax]) - Math.max(a.min[ax],c.min[ax]);
          if(oa <= 0) continue;
          var sides = [[a.min[ax],c.min[ax],'min'],[a.max[ax],c.max[ax],'max']];
          for(var s=0;s<sides.length;s++){
            var d = Math.abs(sides[s][0]-sides[s][1]);
            if(d < xeps){
              pairs.push({i:i, j:j, axis:ax, side:sides[s][2],
                          gap:Math.round(d*100000)/100000,
                          at:Math.round(sides[s][0]*100000)/100000,
                          ovl:Math.round(Math.min(ou,ov)*1000)/1000,
                          ta:boxes[i].mesh.geometry.type, tb:boxes[j].mesh.geometry.type});
            }
          }
        }
      }
      if(!pairs.length) return;
      var dump = function(b){
        var r = function(v){ return Math.round(v*100000)/100000; };
        return {min:[r(b.box.min.x),r(b.box.min.y),r(b.box.min.z)],
                max:[r(b.box.max.x),r(b.box.max.y),r(b.box.max.z)],
                t:b.mesh.geometry.type};
      };
      var used = {};
      pairs.forEach(function(p){ used[p.i]=1; used[p.j]=1; });
      var bx = {};
      Object.keys(used).forEach(function(n){ bx[n] = dump(boxes[n]); });
      out.push({loadout:ln.replace('Weapons',''), name: ud.name || '?',
                total: boxes.length, pairs: pairs, boxes: bx});
    });
  });
  return JSON.stringify(out);
})
"""


def size(b):
    return [round(b["max"][k] - b["min"][k], 5) for k in range(3)]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    summary_only = "--summary" in sys.argv
    # Only faces at EXACTLY the same coordinate. Per audit.py's note, those are the real defect --
    # nothing in the depth buffer separates them, so they flicker at every distance and every scale.
    # A pair merely close may never flicker; this is the list that must go to zero.
    exact_only = "--exact" in sys.argv
    # --under X: only pairs closer than X. Faces a few tenths of a millimetre apart behave like
    # coincident ones on a model held 0.4 from the camera, so they are worth the same attention.
    under = None
    for a in sys.argv[1:]:
        if a.startswith("--under="):
            under = float(a.split("=", 1)[1])

    actors_mode = "--actors" in sys.argv

    ctx, err = build_ctx(pathlib.Path(__file__).resolve().parents[2] / "index.html")
    if err:
        print(f"SCRIPT FAILED TO LOAD: {err}", file=sys.stderr)
        return 1

    if actors_mode:
        ctx.eval(PAIRS_JS)
        fn = ctx.eval(ACTORS_JS)
        data = []
        for builder, invoke, scale, floor, label in ACTORS:
            # Several builders randomise; keep the worst of a few runs, as audit.py does.
            worst = None
            for _ in range(3):
                r = json.loads(fn(builder, invoke, scale, COPLANAR_EPS, OVERLAP_MIN, floor))
                if worst is None or len(r["pairs"]) > len(worst["pairs"]):
                    worst = r
            worst["name"] = label
            worst["loadout"] = builder
            data.append(worst)
    else:
        data = json.loads(ctx.eval(DETAIL_JS)(COPLANAR_EPS, HELD_OVERLAP_MIN))
    if exact_only or under is not None:
        lim = 0.0 if exact_only else under
        for w in data:
            w["pairs"] = [p for p in w["pairs"] if p["gap"] <= lim] if exact_only \
                else [p for p in w["pairs"] if p["gap"] < lim]
        data = [w for w in data if w["pairs"]]
    data.sort(key=lambda w: -len(w["pairs"]))

    if args:
        want = [a.lower() for a in args]
        data = [w for w in data if any(a in w["name"].lower() for a in want)]

    grand = 0
    for w in data:
        exact = sum(1 for p in w["pairs"] if p["gap"] == 0)
        grand += len(w["pairs"])
        print(f"\n{'='*78}\n{w['name']}  ({w['loadout']})  "
              f"{len(w['pairs'])} pairs, {exact} exactly coincident, {w['total']} meshes\n{'='*78}")
        if summary_only:
            continue
        # group by the offending box pair so one bad mesh reads as one entry, not six
        byp = {}
        for p in w["pairs"]:
            byp.setdefault((p["i"], p["j"]), []).append(p)
        for (i, j), ps in sorted(byp.items(), key=lambda kv: -len(kv[1])):
            a, b = w["boxes"][str(i)], w["boxes"][str(j)]
            faces = ", ".join(f"{p['axis']}.{p['side']}@{p['at']} gap {p['gap']}" for p in ps)
            print(f"  #{i:<3} {a['t']:<16} size {size(a)}  at {a['min']}")
            print(f"  #{j:<3} {b['t']:<16} size {size(b)}  at {b['min']}")
            print(f"       -> {len(ps)} face(s): {faces}\n")

    print(f"\n{grand} fighting pairs across {len(data)} weapon(s)")


if __name__ == "__main__":
    main()
