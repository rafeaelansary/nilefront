#!/usr/bin/env python3
"""Whole-game geometry sweep.

Runs every check across every map, every weapon and every actor:

  actors   - ground contact, connectivity, coplanarity   (see audit.py)
  weapons  - connectivity, coplanarity, muzzle placement
  maps     - collider overlaps, blocked spawns, ramp corridors through
             buildings, near-coplanar world faces, floating scenery

Exit code is 0 only when nothing is reported.

    python3 tools/audit/fullcheck.py
    python3 tools/audit/fullcheck.py --maps greekOverworld   # one map only
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from audit import build_ctx, ACTORS, TOLERANCE, CONNECT_EPS, COPLANAR_EPS, OVERLAP_MIN  # noqa: E402

REPO = HERE.parents[1]

# World coplanarity is looser than the per-model one: map geometry is huge, and a 5mm
# seam on a 40-unit wall is far more visible than the same seam on a 0.3-unit weapon part.
WORLD_COPLANAR_EPS = 0.006
WORLD_OVERLAP_MIN = 0.30
FLOAT_MIN_GAP = 0.45   # a mesh this far above the ground with nothing under it is floating
# 0.03, not 0.004: a lot of geometry is deliberately seated with a hairline clearance above what
# it rests on, precisely to avoid the coplanar z-fighting the check above hunts for. Those are
# not floating.
FLOAT_TOUCH_EPS = 0.03

# Which spawn points apply to which map. SPAWN_POINTS is shared by every wave-bearing
# overworld; arenas and the Nile spawn their own way and are excluded.
WAVE_MAPS = {"pyramidOverworld", "greekOverworld", "romanOverworld", "islamicOverworld"}
PLAYER_ENTRY = {
    "pyramidOverworld": (0, 18),
    "greekOverworld": (0, 10),
    "romanOverworld": (0, 10),
    "islamicOverworld": (0, 10),
}
# Built but never reached: startGame() drops the player straight into the pyramid
# overworld, and enterDungeon() only ever runs with dungeonWasPyramid true.
DEAD_WORLDS = {"overworld", "dungeon", "greekDungeon"}

# Which height-zone array belongs to which map, for the ramp-corridor check. Only maps with climbable
# watchtowers have one.
HEIGHT_ZONES = {
    "pyramidOverworld": "heightZonesPyramid",
    "greekOverworld": "heightZonesGreek",
    "romanOverworld": "heightZonesRoman",
    "islamicOverworld": "heightZonesIslamic",
}


def rect(b):
    return b["x1"], b["x2"], b["z1"], b["z2"]


def desc(b):
    return (f"x{(b['x1']+b['x2'])/2:7.1f} z{(b['z1']+b['z2'])/2:7.1f} "
            f"{b['x2']-b['x1']:5.1f}x{b['z2']-b['z1']:5.1f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", nargs="*", help="limit to these world names")
    ap.add_argument("--skip-dead", action="store_true",
                    help="skip worlds that are built but never reachable")
    args = ap.parse_args()

    ctx, err = build_ctx(REPO / "index.html")
    if err:
        print(f"SCRIPT FAILED TO LOAD: {err}", file=sys.stderr)
        return 1

    problems = 0

    # ---------------------------------------------------------------- actors
    print("=" * 78)
    print("ACTORS")
    print("=" * 78)
    fn = ctx.eval("""
    (function(builder, invoke, scale, floor, tol, ceps, xeps, xomin){
      var m = eval(invoke)(globalThis.__builders[builder]);
      var b = globalThis.__modelBounds(m, scale);
      var conn = globalThis.__connectivity(m, scale, ceps);
      var cop  = globalThis.__coplanar(m, scale, xeps, xomin);
      return JSON.stringify({
        minY: b.min.y, gap: b.min.y - floor, meshes: b.count,
        orphans: conn.orphans.length, coplanar: cop.length,
        worstGap: cop.length ? Math.min.apply(null, cop.map(function(h){return h.gap;})) : null
      });
    })
    """)
    hdr = f"{'model':24} {'meshes':>7} {'floor gap':>10} {'orphans':>8} {'z-fights':>9}  verdict"
    print(hdr)
    print("-" * len(hdr))
    for builder, invoke, scale, floor, label in ACTORS:
        r = json.loads(fn(builder, invoke, scale, floor, TOLERANCE,
                          CONNECT_EPS, COPLANAR_EPS, OVERLAP_MIN))
        bad = []
        if abs(r["gap"]) > TOLERANCE:
            bad.append("BURIED" if r["gap"] < 0 else "FLOATS")
        if r["orphans"]:
            bad.append(f"{r['orphans']} FLOATING PARTS")
        if r["coplanar"]:
            bad.append(f"{r['coplanar']} Z-FIGHTS (worst {r['worstGap']})")
        if bad:
            problems += 1
        print(f"{label:24} {r['meshes']:>7} {r['gap']:>+10.3f} {r['orphans']:>8} "
              f"{r['coplanar']:>9}  {'; '.join(bad) if bad else 'ok'}")

    # --------------------------------------------------------------- weapons
    print()
    print("=" * 78)
    print("WEAPONS")
    print("=" * 78)
    wfn = ctx.eval("""
    (function(ceps, xeps, xomin){
      var out = [];
      Object.keys(globalThis.__loadouts).forEach(function(ln){
        var arr = globalThis.__loadouts[ln];
        if(!arr) return;
        arr.forEach(function(w){
          var conn = globalThis.__connectivity(w, 1, ceps);
          var cop  = globalThis.__coplanar(w, 1, xeps, xomin);
          var b    = globalThis.__modelBounds(w, 1);
          var ud   = w.userData || {};
          out.push({loadout:ln, name: ud.name || '?', meshes:b.count,
                    orphans:conn.orphans.length, coplanar:cop.length,
                    frontZ: Math.round(b.min.z*1000)/1000,
                    muzzleZ: ud.muzzleZ === undefined ? null : ud.muzzleZ,
                    melee: !!ud.melee});
        });
      });
      return JSON.stringify(out);
    })
    """)
    weapons = json.loads(wfn(CONNECT_EPS, COPLANAR_EPS, OVERLAP_MIN))
    hdr = f"{'weapon':16} {'loadout':18} {'meshes':>7} {'orphans':>8} {'z-fights':>9}  verdict"
    print(hdr)
    print("-" * len(hdr))
    for w in weapons:
        bad = []
        if w["orphans"]:
            bad.append(f"{w['orphans']} FLOATING PARTS")
        if w["coplanar"]:
            bad.append(f"{w['coplanar']} Z-FIGHTS")
        # a ranged weapon's tracer should not spawn inside its own model
        if not w["melee"] and w["muzzleZ"] is not None and w["muzzleZ"] > w["frontZ"] + 0.02:
            bad.append(f"MUZZLE INSIDE MODEL (muzzleZ {w['muzzleZ']} vs tip {w['frontZ']})")
        if bad:
            problems += 1
        print(f"{w['name']:16} {w['loadout'].replace('Weapons',''):18} {w['meshes']:>7} "
              f"{w['orphans']:>8} {w['coplanar']:>9}  {'; '.join(bad) if bad else 'ok'}")

    # ------------------------------------------------------------------ maps
    print()
    print("=" * 78)
    print("MAPS")
    print("=" * 78)
    names = json.loads(ctx.eval("JSON.stringify(Object.keys(globalThis.__worlds))"))
    if args.maps:
        names = [n for n in names if n in args.maps]
    spawns = json.loads(ctx.eval("JSON.stringify(globalThis.__world.SPAWN_POINTS)"))

    mfn = ctx.eval("""
    (function(name, eps, omin, groundY, minGap, touchEps){
      var W = globalThis.__worlds[name];
      var cop = globalThis.__worldCoplanar(W.group, eps, omin, 4);
      var flo = globalThis.__worldFloaters(W.group, groundY, minGap, touchEps);
      var n = 0; W.group.traverse(function(o){ if(o.isMesh) n++; });
      return JSON.stringify({meshes:n, coplanar:cop.slice(0,6), coplanarN:cop.length,
                             floaters:flo.slice(0,6), floatersN:flo.length,
                             colliders: W.colliders ? W.colliders.length : null});
    })
    """)

    for name in names:
        dead = name in DEAD_WORLDS
        if dead and args.skip_dead:
            continue
        r = json.loads(mfn(name, WORLD_COPLANAR_EPS, WORLD_OVERLAP_MIN, 0.0,
                          FLOAT_MIN_GAP, FLOAT_TOUCH_EPS))
        tag = "  [built but never reachable]" if dead else ""
        print(f"\n--- {name}{tag}")
        print(f"    meshes {r['meshes']}, colliders {r['colliders']}")

        cols = json.loads(ctx.eval(
            f"JSON.stringify((globalThis.__worlds['{name}'].colliders)||[])"))

        # collider overlaps
        ov = []
        for i in range(len(cols)):
            ax0, ax1, az0, az1 = rect(cols[i])
            for j in range(i + 1, len(cols)):
                bx0, bx1, bz0, bz1 = rect(cols[j])
                ox = min(ax1, bx1) - max(ax0, bx0)
                oz = min(az1, bz1) - max(az0, bz0)
                if ox <= 0.05 or oz <= 0.05:
                    continue
                # Two thin walls meeting at a right angle lap by design at the corner — every dungeon,
                # arena and L-shaped piece of cover is built that way. Judged by aspect ratio rather than
                # by an absolute length, so a 5-unit cover wall with a 2-unit return counts as well as a
                # 46-unit chamber wall, and only when the lap is no bigger than the walls' own thickness.
                aw, ad = ax1 - ax0, az1 - az0
                bw, bd = bx1 - bx0, bz1 - bz0
                def thin(w, d):
                    return max(w, d) / max(min(w, d), 1e-6) >= 2.2
                if thin(aw, ad) and thin(bw, bd):
                    thick = max(min(aw, ad), min(bw, bd)) + 0.05
                    if ox <= thick and oz <= thick:
                        continue
                # A tiled run of IDENTICAL panels laid deliberately over-wide so their footprints lap and
                # the seam cannot be walked through. Every arena's barrier ring is built that way (see the
                # `*1.08` in the Colosseum's collider loop) — the overlap is the point, not a defect.
                if (abs(aw - bw) < 1e-6 and abs(ad - bd) < 1e-6
                        and ox < aw * 0.4 and oz < ad * 0.9):
                    continue
                ov.append((round(ox, 2), round(oz, 2), cols[i], cols[j]))

        # blocked spawns
        bad_spawns = []
        if name in WAVE_MAPS:
            pts = [("player entry", PLAYER_ENTRY.get(name, (0, 10)), 0.9)]
            pts += [(f"SPAWN[{i}]", tuple(p), 0.55) for i, p in enumerate(spawns)]
            for label, (sx, sz), rr in pts:
                for b in cols:
                    x0, x1, z0, z1 = rect(b)
                    if x0 - rr < sx < x1 + rr and z0 - rr < sz < z1 + rr:
                        bad_spawns.append((label, (sx, sz), b))
                        break

        # ramp corridors running through buildings. A watchtower stair is a walkable corridor: if a
        # building collider sits inside it the player climbs into a wall — the collider stops them while the
        # height zone keeps lifting. Towers got taller once, their stairs got longer with them, and seven
        # buildings ended up inside a flight before anyone noticed.
        ramp_hits = []
        zones = json.loads(ctx.eval(
            "JSON.stringify(globalThis.__world['%s'] || [])" % HEIGHT_ZONES[name])) \
            if name in HEIGHT_ZONES else []
        for zn in zones:
            if zn.get("type") != "ramp":
                continue
            for b in cols:
                if b.get("roofY") is not None:
                    continue        # the tower's own footprint legitimately abuts its ramp
                ox = min(zn["x2"], b["x2"]) - max(zn["x1"], b["x1"])
                oz = min(zn["z2"], b["z2"]) - max(zn["z1"], b["z1"])
                if ox > 0.2 and oz > 0.2:
                    ramp_hits.append((zn, b, round(ox, 2), round(oz, 2)))

        if not dead:
            problems += (bool(ov) + bool(bad_spawns) + bool(r["coplanarN"])
                         + bool(r["floatersN"]) + bool(ramp_hits))

        def report(title, n, rows):
            if not n:
                print(f"    {title}: ok")
                return
            print(f"    {title}: {n}")
            for row in rows:
                print(f"        {row}")

        report("collider overlaps", len(ov),
               [f"({desc(a)}) vs ({desc(b)})  overlap {ox}x{oz}" for ox, oz, a, b in ov[:6]])
        report("blocked spawns", len(bad_spawns),
               [f"{lbl} at {pos} inside {desc(b)}" for lbl, pos, b in bad_spawns])
        report("near-coplanar world faces", r["coplanarN"],
               [f"{h['axis']} gap {h['gap']} at ({h['x']}, {h['y']}, {h['z']})"
                for h in r["coplanar"]])
        report("ramp corridors through buildings", len(ramp_hits),
               [f"ramp x[{zn['x1']:.1f},{zn['x2']:.1f}] z[{zn['z1']:.1f},{zn['z2']:.1f}] "
                f"hits ({desc(b)}) by {ox}x{oz}" for zn, b, ox, oz in ramp_hits])
        report("floating scenery", r["floatersN"],
               [f"underside y={f['y']} at ({f['x']}, {f['z']})" for f in r["floaters"]])

    print()
    print("=" * 78)
    print(f"{problems} problem group(s) reported")
    print("=" * 78)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
