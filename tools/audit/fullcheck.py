#!/usr/bin/env python3
"""Whole-game geometry sweep.

Runs every check across every map, every weapon and every actor:

  actors   - ground contact, connectivity, coplanarity   (see audit.py)
  weapons  - connectivity, coplanarity, muzzle placement
  maps     - collider overlaps, blocked spawns, ramp corridors through
             buildings, near-coplanar world faces (including the big ground and
             water surfaces the grid check exempts), floating scenery

Exit code is 0 only when nothing is reported.

    python3 tools/audit/fullcheck.py
    python3 tools/audit/fullcheck.py --maps greekOverworld   # one map only
"""
import argparse
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from audit import build_ctx, ACTORS, TOLERANCE, CONNECT_EPS, COPLANAR_EPS, OVERLAP_MIN  # noqa: E402

REPO = HERE.parents[1]

# World coplanarity is looser than the per-model one: map geometry is huge, and a 5mm
# seam on a 40-unit wall is far more visible than the same seam on a 0.3-unit weapon part.
WORLD_COPLANAR_EPS = 0.006
# Ground slabs, lake planes and backing walls are exempt from the grid check by design (they touch
# every cell). They get their own sweep instead — see __worldBigCoplanar — reported only when the
# shared plane is this many square units or more, which is the scale a player actually sees flicker.
BIG_COPLANAR_MIN_AREA = 4.0
WORLD_OVERLAP_MIN = 0.30
# A viewmodel is held about 0.4 from the camera, so a shared face far too small to matter on a building
# fills a chunk of the screen on a weapon. OVERLAP_MIN (0.12 m^2) was sized for world geometry and hid
# real z-fighting on held models -- the tecpatl's mosaic handle passed as "ok" while visibly shimmering.
# 0.0006 m^2 is roughly a 25mm square, about the smallest inlay detail any of these models carries.
HELD_OVERLAP_MIN = 0.0006
FLOAT_MIN_GAP = 0.45   # a mesh this far above the ground with nothing under it is floating
# 0.03, not 0.004: a lot of geometry is deliberately seated with a hairline clearance above what
# it rests on, precisely to avoid the coplanar z-fighting the check above hunts for. Those are
# not floating.
FLOAT_TOUCH_EPS = 0.03

# Which spawn points apply to which map. SPAWN_POINTS is shared by every wave-bearing
# overworld; arenas and the Nile spawn their own way and are excluded.
# Maps whose spawn points get checked. mexicoOverworld was missing from this set, which meant its
# "blocked spawns: ok" line was printed without anything being tested -- and it hid three enemy spawns
# standing inside the pyramid. A destination is a wave-bearing map like any other.
WAVE_MAPS = {"pyramidOverworld", "greekOverworld", "romanOverworld", "islamicOverworld",
             "mexicoOverworld", "aztecOverworld", "swedenOverworld"}
# Maps that use their own spawn coordinates instead of the shared SPAWN_POINTS list.
MAP_SPAWNS = {"mexicoOverworld": "__laVentaSpawns", "aztecOverworld": "__tenochtitlanSpawns",
              "swedenOverworld": "__birkaSpawns"}
PLAYER_ENTRY = {
    "pyramidOverworld": (0, 18),
    "greekOverworld": (0, 10),
    "romanOverworld": (0, 10),
    "islamicOverworld": (0, 10),
    "mexicoOverworld": (0, 27),
    "aztecOverworld": (0, 24),
    "swedenOverworld": (0, 24),
    "fjordWorld": (0, 3.4),
    "xiangyangWorld": (0, 24),
    "yamenWorld": (-16, 3.0),
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
    "aztecOverworld": "heightZonesAztec",
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
      var cop  = globalThis.__coplanar(m, scale, xeps, xomin, floor);
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
                          CONNECT_EPS, COPLANAR_EPS, HELD_OVERLAP_MIN))
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
          // Split, the way audit.py's actor check already splits: coincident faces are the defect,
          // near ones are candidates. See the note over the header below for why the line is here.
          var exact = 0;
          for(var q=0;q<cop.length;q++) if(cop[q].gap === 0) exact++;
          out.push({loadout:ln, name: ud.name || '?', meshes:b.count,
                    orphans:conn.orphans.length, coplanar:cop.length, exact:exact,
                    frontZ: Math.round(b.min.z*1000)/1000,
                    muzzleZ: ud.muzzleZ === undefined ? null : ud.muzzleZ,
                    melee: !!ud.melee});
        });
      });
      return JSON.stringify(out);
    })
    """)
    weapons = json.loads(wfn(CONNECT_EPS, COPLANAR_EPS, HELD_OVERLAP_MIN))
    # Two columns, and only the first one fails the run — the same policy audit.py states for actors
    # ("drive the first column to zero; treat the second as a list of candidates"), applied here too.
    #
    # The reason the line sits at exactly zero rather than anywhere inside COPLANAR_EPS: a viewmodel is
    # drawn 0.3-0.5 units from a camera whose near plane is 0.1, and depth precision there is enormous.
    # One step of a 24-bit buffer at 0.4 units is 9.5e-8 units; even a 16-bit buffer resolves 2.4e-5. A
    # pair held 0.001 apart is tens to tens of thousands of steps apart and cannot fight, at any of the
    # scales these models are drawn at. A pair at 0.000 has nothing between it at any precision and
    # always fights. There is no third case on a held weapon, so `near` is reported and not enforced.
    #
    # It is still worth reading. A part that ended up a hair off another is usually a part that was MEANT
    # to be flush with it, and that is often a modelling mistake even when it does not shimmer. Use
    # `python3 tools/audit/zfdetail.py --under=0.002` to see the closest of them.
    #
    # The ACTORS table above deliberately does NOT do this, and the difference is not an oversight. An
    # actor is seen across a map, and precision falls off with the square of the distance: at 60 units a
    # 0.005 gap is two depth steps, and by 120 units the buffer cannot resolve it at all and the pair
    # really does fight. So for anything standing in the world, near-coplanar is a live defect and stays
    # enforced. For something held 0.4 from the eye, it is not one. Same check, same epsilon, different
    # verdict, because the distance the thing is drawn at is what decides.
    hdr = (f"{'weapon':16} {'loadout':18} {'meshes':>7} {'orphans':>8} "
           f"{'coincident':>11} {'near':>6}  verdict")
    print(hdr)
    print("-" * len(hdr))
    for w in weapons:
        bad = []
        if w["orphans"]:
            bad.append(f"{w['orphans']} FLOATING PARTS")
        if w["exact"]:
            bad.append(f"{w['exact']} COINCIDENT FACES")
        # a ranged weapon's tracer should not spawn inside its own model
        if not w["melee"] and w["muzzleZ"] is not None and w["muzzleZ"] > w["frontZ"] + 0.02:
            bad.append(f"MUZZLE INSIDE MODEL (muzzleZ {w['muzzleZ']} vs tip {w['frontZ']})")
        if bad:
            problems += 1
        near = w["coplanar"] - w["exact"]
        print(f"{w['name']:16} {w['loadout'].replace('Weapons',''):18} {w['meshes']:>7} "
              f"{w['orphans']:>8} {w['exact']:>11} {near:>6}  {'; '.join(bad) if bad else 'ok'}")

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
    (function(name, eps, omin, groundY, minGap, touchEps, BIG_COPLANAR_MIN_AREA){
      var W = globalThis.__worlds[name];
      var cop = globalThis.__worldCoplanar(W.group, eps, omin, 4, groundY);
      var big = globalThis.__worldBigCoplanar(W.group, eps, BIG_COPLANAR_MIN_AREA, groundY);
      // Falling snow is SUPPOSED to hang in mid-air. Birka's is a live particle group, so every flake
      // in it counted as floating scenery and this map reported ~130 faults that are the weather doing
      // its job -- a false positive big enough to bury anything real underneath it. bugcheck.py has
      // subtracted them by count for a while; passed to the sweep instead, they are also barred from
      // holding anything else up, which snow should not be doing either.
      var flake = [];
      if(globalThis.__airborne)
        globalThis.__airborne.traverse(function(o){ if(o.isMesh) flake.push(o); });
      var flo = globalThis.__worldFloaters(W.group, groundY, minGap, touchEps, flake);
      var n = 0; W.group.traverse(function(o){ if(o.isMesh) n++; });
      return JSON.stringify({meshes:n, coplanar:cop.slice(0,6), coplanarN:cop.length,
                             big:big.slice(0,6), bigN:big.length,
                             floaters:flo.slice(0,6), floatersN:flo.length,
                             colliders: W.colliders ? W.colliders.length : null});
    })
    """)

    # Both of these hand the question back to the engine: same colliders, same height zones, same
    # insideCollider() the player is moved by. A check that re-implements the rules can only ever be
    # a second opinion, and it is the wrong one exactly where the rules are subtle.
    spawn_fn = ctx.eval("""
    (function(name, zonesName, ptsJson){
      var pts = JSON.parse(ptsJson);
      var W = globalThis.__worlds[name];
      var Z = (zonesName && globalThis.__world[zonesName]) || [];
      globalThis.__world.setActive(W.colliders, Z);
      var gth = globalThis.__world.getTerrainHeight, ic = globalThis.__world.insideCollider;
      var out = [];
      pts.forEach(function(p){
        var sx=p[1], sz=p[2], rr=p[3];
        var h = gth(sx, sz, undefined);
        if(!ic(sx, sz, rr, h)) return;
        // name the box it is actually in, for the report
        var hit = null;
        W.colliders.forEach(function(b){
          if(hit) return;
          var nx=Math.min(Math.max(sx,b.x1),b.x2), nz=Math.min(Math.max(sz,b.z1),b.z2);
          if((sx-nx)*(sx-nx)+(sz-nz)*(sz-nz) < rr*rr) hit = b;
        });
        out.push([p[0], sx, sz, hit]);
      });
      return JSON.stringify(out);
    })
    """)
    ramp_fn = ctx.eval("""
    (function(name, zonesName, radius){
      var W = globalThis.__worlds[name];
      var Z = (zonesName && globalThis.__world[zonesName]) || [];
      globalThis.__world.setActive(W.colliders, Z);
      var gth = globalThis.__world.getTerrainHeight, ic = globalThis.__world.insideCollider;
      var out = [];
      Z.forEach(function(zn){
        if(zn.type !== 'ramp') return;
        var bad=0, tot=0, first=null;
        for(var t=0; t<=1.0001; t+=0.04){
          // three lines along the ramp -- the middle and both shoulders, inset by the player's radius
          for(var u=0.25; u<=0.76; u+=0.25){
            var x, z;
            if(zn.axisX){ x = zn.x1 + (zn.x2-zn.x1)*t; z = zn.z1 + (zn.z2-zn.z1)*u; }
            else        { x = zn.x1 + (zn.x2-zn.x1)*u; z = zn.z1 + (zn.z2-zn.z1)*t; }
            var h = gth(x, z, undefined);
            tot++;
            if(ic(x, z, radius, h)){
              bad++;
              if(!first) first = [Math.round(x*10)/10, Math.round(z*10)/10, Math.round(h*100)/100];
            }
          }
        }
        if(bad) out.push({bad:bad, tot:tot, at:first, rect:[zn.x1, zn.z1, zn.x2, zn.z2]});
      });
      return JSON.stringify(out);
    })
    """)

    # Roof decks that throw you off sideways instead of stopping you at the edge.
    #
    # A collider carrying a roofY is skipped for anyone whose terrain height already matches that roof
    # -- that is what makes a deck walkable. The skip is decided by sampling the terrain AT THE ACTOR,
    # so it lasts exactly as far as the plateau zone reaches. Where the collider's footprint is WIDER
    # than its plateau there is a rim of deck that the roof rule does not cover, and an actor who steps
    # into it is judged to be buried inside the box. resolveStep() then ejects him along the box's
    # SHORTEST axis out -- and on a thin rim the shortest way out is the outside face, so he is fired
    # off the roof horizontally, several units, in mid-air.
    #
    # This is not the same thing as walking off an edge, which is fine and which every roof allows. The
    # test is the outcome: step off the plateau while still inside the footprint, resolve, and ask where
    # the engine put you. Landing somewhere with floor under it at roof height = you were stopped (the
    # Great Pyramid's terraces do this correctly, pushing you back onto the summit). Landing somewhere
    # with nothing under it = you were thrown.
    deck_fn = ctx.eval("""
    (function(name, radius){
      var W = globalThis.__worlds[name];
      globalThis.__world.setActive(W.colliders, W.zones || []);
      var gth = globalThis.__world.getTerrainHeight, rc = globalThis.__world.resolveCollision;
      var out = [];
      (W.colliders || []).forEach(function(c){
        if(c.roofY === null || c.roofY === undefined) return;
        var stands = function(x,z){ return gth(x, z, c.roofY) >= c.roofY - 0.4; };
        // keep the sample count sane on the big footprints
        var step = Math.max(0.1, Math.min((c.x2-c.x1), (c.z2-c.z1)) / 40);
        var thrown = 0, tot = 0, first = null, worst = 0;
        for(var x=c.x1+step/2; x<c.x2; x+=step){
          for(var z=c.z1+step/2; z<c.z2; z+=step){
            if(stands(x,z)) continue;                 // on the deck: nothing to answer for
            // reachable only if there is real deck within a stride of here
            if(!(stands(x-step,z)||stands(x+step,z)||stands(x,z-step)||stands(x,z+step))) continue;
            tot++;
            var r = rc(x, z, radius, c.roofY);
            if(stands(r[0], r[1])) continue;          // pushed back onto the deck -- correct
            var d = Math.sqrt((r[0]-x)*(r[0]-x) + (r[1]-z)*(r[1]-z));
            thrown++;
            if(d > worst) worst = d;
            if(!first) first = [Math.round(x*100)/100, Math.round(z*100)/100,
                                Math.round(r[0]*100)/100, Math.round(r[1]*100)/100];
          }
        }
        if(thrown) out.push({thrown:thrown, tot:tot, at:first, roofY:c.roofY,
                             worst:Math.round(worst*100)/100,
                             rect:[c.x1, c.z1, c.x2, c.z2]});
      });
      out.sort(function(a,b){ return b.worst - a.worst; });
      return JSON.stringify(out);
    })
    """)

    for name in names:
        dead = name in DEAD_WORLDS
        if dead and args.skip_dead:
            continue
        r = json.loads(mfn(name, WORLD_COPLANAR_EPS, WORLD_OVERLAP_MIN, 0.0,
                          FLOAT_MIN_GAP, FLOAT_TOUCH_EPS, BIG_COPLANAR_MIN_AREA))
        tag = "  [built but never reachable]" if dead else ""
        print(f"\n--- {name}{tag}")
        print(f"    meshes {r['meshes']}, colliders {r['colliders']}")

        cols = json.loads(ctx.eval(
            f"JSON.stringify((globalThis.__worlds['{name}'].colliders)||[])"))

        # A RING BARRIER: N collider boxes whose centres all sit on one circle, each covering its own arc
        # of a curved wall. Axis-aligned boxes cannot tile a circle without lapping at the diagonals — the
        # lap is forced by the geometry, not a mistake — so overlaps BETWEEN TWO MEMBERS of the same ring
        # are structural and exempt. This replaces an older rule that exempted only byte-identical boxes,
        # which silently stopped applying the moment a ring was built correctly: sizing every segment the
        # same is exactly the bug that left 2.5-unit walk-through holes in the Colosseum's barrier, because
        # a segment's true footprint depends on the angle it sits at. Rings are found geometrically rather
        # than hard-coded per map; every arena in this project is built concentric with the origin.
        # A ring has to actually BE a ring: at least 8 boxes sharing one radius to within 0.2, whose
        # bearings run the whole way round with no gap wider than 3x the mean spacing. A looser test
        # (radius buckets alone) silently swallowed 20 scattered buildings in the town map as a "ring"
        # and hid four genuine overlaps with them, which is exactly the kind of false negative that
        # makes a checker worse than none.
        def ring_ids(boxes):
            pts = []
            for k, b in enumerate(boxes):
                x0, x1, z0, z1 = rect(b)
                cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
                pts.append((k, math.hypot(cx, cz), math.atan2(cz, cx)))
            members = set()
            order = sorted(pts, key=lambda q: q[1])
            i = 0
            while i < len(order):
                j = i
                while j + 1 < len(order) and order[j + 1][1] - order[i][1] <= 0.2:
                    j += 1
                grp = order[i:j + 1]
                if len(grp) >= 8 and order[i][1] > 1.0:
                    angs = sorted(q[2] for q in grp)
                    gaps = [angs[t + 1] - angs[t] for t in range(len(angs) - 1)]
                    gaps.append(angs[0] + 2 * math.pi - angs[-1])
                    if max(gaps) <= (2 * math.pi / len(angs)) * 3.0:
                        members.update(q[0] for q in grp)
                i = j + 1
            return members

        ring = ring_ids(cols)

        # collider overlaps
        ov = []
        for i in range(len(cols)):
            ax0, ax1, az0, az1 = rect(cols[i])
            for j in range(i + 1, len(cols)):
                if i in ring and j in ring:
                    continue
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
            pool = spawns
            if name in MAP_SPAWNS:
                pool = json.loads(ctx.eval("JSON.stringify(globalThis.%s||[])" % MAP_SPAWNS[name])) or spawns
            pts = [("player entry", PLAYER_ENTRY.get(name, (0, 10)), 0.9)]
            # 0.85 is the measured widest enemy radius, not 0.55: a spawn that only clears a narrow
            # enemy still drops a manticore or a mud golem inside the scenery.
            pts += [(f"SPAWN[{i}]", tuple(p), 0.85) for i, p in enumerate(pool)]
            # Ask the GAME, rather than re-deriving its rules here. The hand-rolled box test had no
            # notion of roofY, so it called a walkable dock a blocked spawn -- and anything it got
            # wrong in the other direction would have been a real bug reported as clean.
            hits = json.loads(spawn_fn(name, HEIGHT_ZONES.get(name, ""),
                                       json.dumps([[l, float(sx), float(sz), rr]
                                                   for l, (sx, sz), rr in pts])))
            for label, sx, sz, b in hits:
                bad_spawns.append((label, (sx, sz), b))

        # Ramps you cannot actually climb. A stair is a walkable corridor: if anything solid sits in
        # it the player climbs into a wall — the collider stops them while the height zone keeps
        # lifting. This used to compare rectangles and SKIP every collider carrying a roofY, on the
        # theory that a tower's own footprint legitimately abuts its ramp. That exemption hid the
        # worst case in the game: the Templo Mayor's 26x20 roofY box covered its own stair, and a
        # roofY only lifts once you have reached the roof, so the stair sealed a third of the way up.
        # It now walks each ramp and asks insideCollider() at the height the ramp itself puts you at.
        ramp_hits = []
        zones = json.loads(ctx.eval(
            "JSON.stringify(globalThis.__world['%s'] || [])" % HEIGHT_ZONES[name])) \
            if name in HEIGHT_ZONES else []
        if zones:
            ramp_hits = json.loads(ramp_fn(name, HEIGHT_ZONES.get(name, ""), 0.45))

        # 0.45 is the player's radius. A bot's is 0.85 and fares worse, but the player is the one who
        # has to be able to hold a rampart.
        deck_hits = json.loads(deck_fn(name, 0.45))

        if not dead:
            problems += (bool(ov) + bool(bad_spawns) + bool(r["coplanarN"])
                         + bool(r["floatersN"]) + bool(ramp_hits) + bool(deck_hits))

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
        report("near-coplanar ground / water surfaces", r["bigN"],
               [f"{h['axis']} gap {h['gap']} over {h['area']} sq units "
                f"at ({h['x']}, {h['y']}, {h['z']})" for h in r["big"]])
        report("ramps blocked by something solid", len(ramp_hits),
               [f"ramp x[{h['rect'][0]:.1f},{h['rect'][2]:.1f}] z[{h['rect'][1]:.1f},{h['rect'][3]:.1f}] "
                f"blocked at {h['bad']}/{h['tot']} points, first at "
                f"({h['at'][0]}, {h['at'][1]}) y={h['at'][2]}" for h in ramp_hits])
        report("roof decks that throw you off", len(deck_hits),
               [f"deck y={h['roofY']} x[{h['rect'][0]:.1f},{h['rect'][2]:.1f}] "
                f"z[{h['rect'][1]:.1f},{h['rect'][3]:.1f}]: {h['thrown']}/{h['tot']} rim points fire "
                f"you off, worst {h['worst']}u — ({h['at'][0]}, {h['at'][1]}) lands at "
                f"({h['at'][2]}, {h['at'][3]})" for h in deck_hits[:6]])
        report("floating scenery", r["floatersN"],
               [f"underside y={f['y']} at ({f['x']}, {f['z']})" for f in r["floaters"]])

    print()
    print("=" * 78)
    print(f"{problems} problem group(s) reported")
    print("=" * 78)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
