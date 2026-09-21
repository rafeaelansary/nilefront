#!/usr/bin/env python3
"""Tenochtitlan: can you actually walk the map it is built around?

Every bug this file exists for was the same shape — geometry the player can SEE is walkable that the
collision layer disagrees with. A knee-high quay laid down as a solid wall across the arrival point.
Canals cut with a continuous kerb and no bridge anywhere along them. A pyramid whose one 26x20 roofY
collider covered its own stair, so the stair sealed a third of the way up. A platform with a plateau
on it and no roof under it. None of them showed up as a geometry fault, because none of them IS one:
the meshes were all correct. They only appear if you walk the route.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bugcheck import run, show

ok = True

# A walk that a player could make: head for a point, give up if something stops you dead.
WALK = """
function walk(x, z, tx, tz, steps){
  var h = getTerrainHeight(x, z, undefined);
  for(var i=0;i<steps;i++){
    var dx=tx-x, dz=tz-z, L=Math.hypot(dx,dz);
    if(L < 0.5) break;
    var r=resolveCollision(x+dx/L*0.06, z+dz/L*0.06, 0.45, h);
    if(Math.abs(r[0]-x)<1e-7 && Math.abs(r[1]-z)<1e-7) break;   // wedged
    x=r[0]; z=r[1]; h=getTerrainHeight(x,z,h);
  }
  return [x,z,h];
}
"""

# The map's whole composition is the arrival view: you land on the south quay looking north up the
# length of the precinct at the Templo Mayor's twin stair. That walk has to be possible.
ok &= show("arrival -> bridge -> round the balustrade -> up the flight -> the summit", run(WALK + """
  gameStarted = true; enterAztecWorld('t');
  var p=[camera.position.x, camera.position.z, 0], leg=[];
  [[0,19,'the bridge'],[3.0,9,'the stair foot'],[3.0,-4.0,'the flight'],[3.0,-6.6,'the deck']]
    .forEach(function(t){
      p = walk(p[0], p[1], t[0], t[1], 1600);
      leg.push(t[2]+' ('+p[0].toFixed(1)+','+p[1].toFixed(1)+') y'+p[2].toFixed(2));
    });
  if(p[2] < 12.0) throw new Error('never reached the summit: '+leg.join(' -> '));
  return leg.join(' -> ');
"""))

# The stair specifically, one flight at a time, because this is the one that sealed silently: the
# pyramid's roofY collider only stops blocking once you have REACHED the roof, and partway up a stair
# you have not. It let you climb about four units and then stood an invisible wall in front of you.
ok &= show("both flights of the twin stair climb the whole way, with no invisible wall", run("""
  gameStarted = true; enterAztecWorld('t');
  var out=[];
  [-3.0, 3.0].forEach(function(fx){
    var x=fx, z=9.0, h=0, top=0;
    for(var i=0;i<900;i++){
      var r=resolveCollision(x, z-0.05, 0.45, h);
      if(Math.abs(r[1]-(z-0.05))>1e-4) break;
      x=r[0]; z=r[1]; h=getTerrainHeight(x,z,h); top=Math.max(top,h);
      if(h >= 12.39) break;
    }
    if(top < 12.39) throw new Error('the flight at x='+fx+' stopped at y='+top.toFixed(2)+' (z='+z.toFixed(2)+')');
    out.push('x'+fx+' -> y'+top.toFixed(2));
  });
  return out.join('  ');
"""))

# ...and the middle of the stair is a WALL, not a hole. The two ramp zones stop at +-0.7; without the
# central balustrade as a collider you could step off a flight into the gap between them and drop to
# ground level inside the pyramid.
ok &= show("the gap between the two flights is solid, not a way into the pyramid", run("""
  gameStarted = true; enterAztecWorld('t');
  for(var z=-4.0; z<=4.0; z+=0.5){
    var h = getTerrainHeight(0, z, undefined);
    if(!insideCollider(0, z, 0.45, h))
      throw new Error('you can stand between the flights at z='+z.toFixed(1)+' y='+h.toFixed(2));
  }
  return 'the central balustrade is solid the whole length of the stair';
"""))

# The quay is a dock. It was a solid 34x3 wall with no roof, dropped across the entire south edge of
# the island, and the player arrives at z=23.25 pressed against it.
ok &= show("the south quay is something you step onto, not something you are pinned against", run("""
  gameStarted = true; enterAztecWorld('t');
  var x=0, z=camera.position.z, h=0;
  for(var i=0;i<400;i++){
    var want=z+0.05;
    if(want > playClamp) break;
    var r=resolveCollision(x, want, 0.45, h);
    if(Math.abs(r[1]-want)>1e-4) throw new Error('blocked at z='+z.toFixed(2)+' y='+h.toFixed(2));
    x=r[0]; z=r[1]; h=getTerrainHeight(x,z,h);
  }
  if(h < 0.5) throw new Error('walked to z='+z.toFixed(2)+' and never got up onto the quay (y='+h.toFixed(2)+')');
  if(playClamp !== 27) throw new Error('the map inherited playClamp '+playClamp+' from whatever ran before it');
  return 'up onto the quay at y'+h.toFixed(2)+', walkable out to the clamp at '+playClamp;
"""))

# Canals are a barrier you cross at bridges -- both halves of that matter. Cut with an unbroken kerb
# they walled the arrival point off from the city; bridged end to end they would stop being canals.
ok &= show("the canals are bridged where the player walks, and solid everywhere else", run("""
  gameStarted = true; enterAztecWorld('t');
  var walled=0, open=0, runs=[], cur=null;
  for(var x=-19; x<=19; x+=0.5){
    var h = getTerrainHeight(x, 16, undefined);
    var crossable = !insideCollider(x, 16, 0.45, h) && h > 0.2;
    if(crossable){ open++; if(!cur){ cur=[x,x]; runs.push(cur); } else cur[1]=x; }
    else { walled++; cur=null; }
  }
  if(!runs.length) throw new Error('the z=16 canal has no crossing at all');
  if(walled < 40) throw new Error('it is open across '+open+' of its length -- that is not a canal');
  // and one of the crossings has to be on the axis the player actually arrives on
  if(!runs.some(function(r){ return r[0] <= 0 && r[1] >= 0; }))
    throw new Error('nothing crosses it on the arrival axis; crossings at '+JSON.stringify(runs));
  return runs.length+' crossings ('+runs.map(function(r){
    return r[0].toFixed(0)+'..'+r[1].toFixed(0); }).join(', ')+'), solid for the other '+walled+' samples';
"""))

# A plateau over a collider with no roofY is unreachable at every height. The eagle house had exactly
# that, plus a ramp that ran through the precinct wall at one end and into the canal kerb at the other.
ok &= show("the eagle house platform can be climbed, by the ramp that is drawn for it", run(WALK + """
  gameStarted = true; enterAztecWorld('t');
  var p = walk(9.0, 6.0, 19.0, 6.0, 2000);
  if(p[2] < 1.5)
    throw new Error('stalled at ('+p[0].toFixed(1)+','+p[1].toFixed(1)+') y='+p[2].toFixed(2));
  return 'up the west ramp to y'+p[2].toFixed(2)+' at ('+p[0].toFixed(1)+','+p[1].toFixed(1)+')';
"""))

# The garrison has to be able to reach the player, or the map is a diorama.
ok &= show("every Tenochtitlan spawn point is on open ground", run("""
  gameStarted = true; enterAztecWorld('t');
  var pool = TENOCH_WEST.concat(TENOCH_EAST);
  if(!pool.length) throw new Error('no Tenochtitlan spawn pool to check');
  var bad=[];
  pool.forEach(function(p,i){
    var h = getTerrainHeight(p[0], p[1], undefined);
    // 0.85 is the widest enemy radius in the game, not the player's
    if(insideCollider(p[0], p[1], 0.85, h)) bad.push(i+' ('+p[0]+','+p[1]+')');
  });
  if(bad.length) throw new Error('spawns inside geometry: '+bad.join(', '));
  return pool.length+' spawn points, all clear';
"""))

sys.exit(0 if ok else 1)
