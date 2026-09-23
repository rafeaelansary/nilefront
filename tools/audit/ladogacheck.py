#!/usr/bin/env python3
"""Aldeigjuborg: can you actually walk the hub the Sweden trip now ends in?

fullcheck.py proves the geometry is sound — nothing overlaps, nothing floats, nothing z-fights. None of
that proves the map is WALKABLE, and a hub that is not walkable is worse than a fight map that is not:
there is no wave to kill and nothing to do here except walk to the booth and buy the next trip. Every
check below is a route a player will actually take, driven through the game's own resolveCollision() and
getTerrainHeight() rather than through a re-derivation of their rules.

    python3 tools/audit/ladogacheck.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bugcheck import run, show

ok = True

# A walk a player could make: head for a point, give up if something stops you dead.
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

print("=== the hub loads at all ===")

ok &= show("entering the hub sets its own map, clamp, booth and beacon", run("""
  gameStarted = true;
  enterSwedenWorld('t');                  // arrive from somewhere else, so nothing is inherited
  enterLadogaMarketHub('t');
  if(!ladogaOverworld.parent) throw new Error('the map is not in the scene');
  if(activeColliders !== ladogaColliders) throw new Error('physics is still solving another map');
  if(playClamp !== 20.5) throw new Error('inherited playClamp '+playClamp+' from whatever ran before it');
  if(currentHub !== 'ladoga') throw new Error('currentHub is '+currentHub);
  if(!inHub) throw new Error('inHub is false in a hub');
  if(BOOTH_POS.x !== LADOGA_BOOTH_POS.x || BOOTH_POS.z !== LADOGA_BOOTH_POS.z)
    throw new Error('the booth prompt points at ('+BOOTH_POS.x+','+BOOTH_POS.z+'), not this hub');
  if(boothBeacon !== LADOGA_BOOTH_BEACON) throw new Error('the spun beacon belongs to another hub');
  if(bots.filter(function(b){return b.alive;}).length) throw new Error('something spawned in a hub');
  return 'booth ('+BOOTH_POS.x+','+BOOTH_POS.z+') clamp '+playClamp;
"""))

# The one thing a hub owes the player. Arrive, walk to the booth, be inside its radius: if that fails
# the trip cannot be bought and the arc dead-ends here.
ok &= show("you can walk from where you land to the travel booth and open it", run(WALK + """
  gameStarted = true; enterLadogaMarketHub('t');
  var p = walk(camera.position.x, camera.position.z, LADOGA_BOOTH_POS.x, LADOGA_BOOTH_POS.z + 3.2, 3000);
  var d = Math.hypot(p[0]-LADOGA_BOOTH_POS.x, p[1]-LADOGA_BOOTH_POS.z);
  if(d >= BOOTH_RADIUS) throw new Error('wedged at ('+p[0].toFixed(1)+','+p[1].toFixed(1)+'), '
    + d.toFixed(2)+' from the booth — outside its '+BOOTH_RADIUS+' radius');
  camera.position.set(p[0], p[2]+1.7, p[1]);
  if(!nearBooth()) throw new Error('standing '+d.toFixed(2)+' away and nearBooth() is still false');
  return 'reached ('+p[0].toFixed(1)+','+p[1].toFixed(1)+'), '+d.toFixed(2)+' from the counter';
"""))

# The bar is built by assigning a string to #stats.innerHTML, so the place name and its icon are read
# back out of that string — the headless DOM does not parse innerHTML into child nodes the way a browser
# does. The hint IS set directly on #enemies, so that one reads normally.
ok &= show("the stats bar names THIS hub, not Cairo", run("""
  var out=[];
  [['cairo',enterHub],['aztecMarket',enterAztecMarketHub],['ladoga',enterLadogaMarketHub]]
    .forEach(function(h){
      gameStarted = true; h[1]('t');
      var bar=document.getElementById('stats').innerHTML, want=HUB_STATS[h[0]];
      if(bar.indexOf('>'+want.place+'<') < 0)
        throw new Error(h[0]+' hub does not call itself '+want.place+': '+bar);
      if(bar.indexOf(want.icon) < 0)
        throw new Error(h[0]+' hub is flying the wrong icon: '+bar);
      if(document.getElementById('enemies').textContent !== want.hint)
        throw new Error(h[0]+' hub points at "'+document.getElementById('enemies').textContent+'"');
      // and no hub may be left showing another one's
      ['Cairo','Aztec Market','Aldeigjuborg'].forEach(function(other){
        if(other !== want.place && bar.indexOf('>'+other+'<') >= 0)
          throw new Error(h[0]+' hub also claims to be '+other);
      });
      out.push(h[0]+': '+want.icon+' '+want.place+' / '+want.hint);
    });
  return out.join(' | ');
"""))

# The river went olive in play: a washed-out blue base colour multiplied by a golden-hour hemisphere.
# Lambert light is a MULTIPLY, so this is a property of the pair, not of either one alone.
ok &= show("the river renders blue, not green", run("""
  gameStarted = true; enterLadogaMarketHub('t');
  var water=null;
  ladogaOverworld.traverse(function(o){
    if(o.isMesh && o.geometry && o.geometry.parameters && o.geometry.parameters.width===400) water=o; });
  if(!water) throw new Error('did not find the river');
  var c=water.material.color;
  // the lit term every Lambert surface on this map is multiplied by
  var L=['r','g','b'].map(function(k){
    return hemi.color[k]*hemi.intensity + sun.color[k]*sun.intensity*0.5 + fill.color[k]*fill.intensity; });
  var lit=['r','g','b'].map(function(k,i){ return Math.min(1, c[k]*L[i]); });
  if(!(lit[2] > lit[1] && lit[1] >= lit[0]))
    throw new Error('lit river is rgb('+lit.map(function(v){return Math.round(v*255);}).join(',')
      + ') — blue is not the dominant channel');
  return 'base #'+c.getHexString()+' lights to rgb('+lit.map(function(v){return Math.round(v*255);}).join(',')+')';
"""))

# No dark skies: every map that SHOWS a sky dome has to render above a floor once WORLD_DAMP has taken
# its 30%. The Greek dungeon is exempt and only the Greek dungeon: sky.visible is false in there.
ok &= show("no map with a visible sky renders a dark one", run("""
  gameStarted = true;
  var maps = [
    ['roman',enterRomanWorld],['cairo',enterIslamicWorld],['laventa',enterMexicoWorld],
    ['tenochtitlan',enterAztecWorld],['aztecmarket',enterAztecMarketWorld],['birka',enterSwedenWorld],
    ['fjord',enterFjordWorld],['ladoga',enterLadogaWorld],['xiangyang',enterXiangyangWorld],
    ['yamen',enterYamenWorld]];
  var dark=[];
  maps.forEach(function(m){
    m[1]('t');
    var b=scene.background, lum=(0.2126*b.r + 0.7152*b.g + 0.0722*b.b)*255;
    if(sky.visible && lum < 110) dark.push(m[0]+' '+Math.round(lum));
  });
  [['nile',enterNileWave],['hydra',enterHydraArena],['colosseum',enterColosseumArena],
   ['ifrit',enterIfritArena]].forEach(function(m){
    m[1]();
    var b=scene.background, lum=(0.2126*b.r + 0.7152*b.g + 0.0722*b.b)*255;
    if(sky.visible && lum < 110) dark.push(m[0]+' '+Math.round(lum));
  });
  pyramidPhase=false; enterDungeon();
  if(sky.visible) throw new Error('the Greek dungeon is showing a sky dome; it is a sealed cave');
  if(dark.length) throw new Error('dark skies: '+dark.join(', '));
  return 'every visible sky is at or above luminance 110';
"""))

print("\n=== the four quarters are all reachable from the street ===")

# Every quarter of this map is somewhere you go to look at something. A quarter you cannot walk into is
# scenery, and the "i'm stuck" reports have all been of this shape: geometry the player can see is
# walkable that the collision layer disagrees with.
ok &= show("quay -> street -> gate, the length of the map, unobstructed", run(WALK + """
  gameStarted = true; enterLadogaMarketHub('t');
  var p=[camera.position.x, camera.position.z, 0], leg=[];
  [[0,14,'the quay head'],[0,4,'mid-street'],[0,-8,'before the gate'],[0,-13.5,'the gate mouth']]
    .forEach(function(t){
      p = walk(p[0], p[1], t[0], t[1], 2500);
      if(Math.hypot(p[0]-t[0], p[1]-t[1]) > 1.2)
        throw new Error('stopped short of '+t[2]+' at ('+p[0].toFixed(1)+','+p[1].toFixed(1)+')');
      leg.push(t[2]+' ('+p[0].toFixed(1)+','+p[1].toFixed(1)+')');
    });
  return leg.join(' -> ');
"""))

ok &= show("the gate is a way through the palisade, not a picture of one", run(WALK + """
  gameStarted = true; enterLadogaMarketHub('t');
  var p = walk(0, -12, 0, -17.5, 2000);
  if(p[1] > -16.2) throw new Error('the gate is shut: stopped at z='+p[1].toFixed(2));
  // ...and the wall either side of it is NOT a way through, or it is not a wall
  [-9.7, 9.7, -17, 17].forEach(function(wx){
    var q = walk(wx, -12, wx, -18, 1200);
    if(q[1] < -15.8) throw new Error('walked through the palisade at x='+wx+' to z='+q[1].toFixed(2));
  });
  return 'through the gate to z='+p[1].toFixed(2)+', solid at x=-9.7, 9.7, -17, 17';
"""))

ok &= show("both rows can be walked into, and down, without wedging", run(WALK + """
  gameStarted = true; enterLadogaMarketHub('t');
  var out=[];
  // The aisle between each row's two lines of stalls, entered off the street and walked end to end.
  // z=2.5 because that is a gap between stalls (they sit at 11, 6, -1, -8, each 2.6 deep) and clear of
  // the banner poles lining the street: a straight-line seeker steers for nothing, so the route it is
  // given has to be one a player would actually take rather than a diagonal through a flagpole.
  [[13.5,'the eastern stalls'], [-13.5,'the fur row']].forEach(function(pair){
    var ax=pair[0];
    var p = walk(0, 2.5, ax, 2.5, 2500);
    if(Math.abs(p[0]-ax) > 1.2)
      throw new Error('cannot get into '+pair[1]+' off the street: stopped at x='+p[0].toFixed(1));
    var q = walk(p[0], p[1], ax, -10, 2500);
    if(q[1] > -8.8)
      throw new Error(pair[1]+' aisle is blocked at z='+q[1].toFixed(1));
    out.push(pair[1]+' x'+q[0].toFixed(1)+' z'+p[1].toFixed(1)+'..'+q[1].toFixed(1));
  });
  return out.join('; ');
"""))

print("\n=== the waterline, which is where a river map gets it wrong ===")

# The bank runs to z=+21.5 and the clamp stops at 20.5. That gap is the whole design: there is no quay
# kerb to get pinned against and no way to walk out onto water that is not floor. Both halves matter.
ok &= show("you can walk to the clamp on the water side and still be standing on the quay", run("""
  gameStarted = true; enterLadogaMarketHub('t');
  var x=0, z=camera.position.z, h=getTerrainHeight(0,z,undefined);
  for(var i=0;i<600;i++){
    var want = z+0.05;
    if(want > playClamp) break;
    var r = resolveCollision(x, want, 0.45, h);
    if(Math.abs(r[1]-want) > 1e-4) throw new Error('blocked at z='+z.toFixed(2)+' short of the clamp');
    x=r[0]; z=r[1]; h=getTerrainHeight(x,z,h);
  }
  if(z < playClamp - 0.1) throw new Error('stopped at z='+z.toFixed(2)+', clamp is '+playClamp);
  if(playClamp >= 21.5) throw new Error('the clamp ('+playClamp+') reaches past the bank edge at 21.5');
  return 'walked out to z='+z.toFixed(2)+' with the bank edge at 21.5';
"""))

ok &= show("the whole clamped square is solid ground — nowhere to walk off the bank", run("""
  gameStarted = true; enterLadogaMarketHub('t');
  // the bank slab covers x +-24 and z -24..21.5; the clamp is 20.5, so every reachable point is on it
  if(playClamp > 20.5) throw new Error('clamp '+playClamp+' is outside the tested envelope');
  var edge = [];
  for(var a=-playClamp; a<=playClamp; a+=0.5){
    [[a, playClamp], [a, -playClamp], [playClamp, a], [-playClamp, a]].forEach(function(pt){
      if(pt[1] > 21.5 || pt[1] < -24 || Math.abs(pt[0]) > 24) edge.push(pt);
    });
  }
  if(edge.length) throw new Error(edge.length+' reachable points are off the bank, e.g. '+JSON.stringify(edge[0]));
  return 'every point inside the clamp is over the bank slab';
"""))

print("\n=== respawning here puts you back in this hub, not in Cairo ===")

ok &= show("every shared player spawn is clear of the market's own geometry", run("""
  gameStarted = true; enterLadogaMarketHub('t');
  var blocked = usableSpawns().filter(function(v){
    return insideCollider(v.x, v.z, 0.85, getTerrainHeight(v.x, v.z, undefined));
  });
  // usableSpawns() already filters at the player's own 0.45; this re-tests at 0.85, the widest actor
  // radius, so a spawn that only just clears does not get called clean
  if(blocked.length) throw new Error(blocked.length+' spawns are inside geometry: '
    + JSON.stringify(blocked.map(function(v){ return [v.x, v.z]; })));
  if(usableSpawns().length < 4) throw new Error('only '+usableSpawns().length+' usable spawns on this map');
  return usableSpawns().length+' usable spawns, all clear at r=0.85';
"""))

ok &= show("dying in the hub wakes you up in the hub", run("""
  gameStarted = true; enterLadogaMarketHub('t');
  player.alive = false; player.hp = 0;
  respawnPlayer();
  if(currentHub !== 'ladoga') throw new Error('woke up in '+currentHub);
  if(!ladogaOverworld.parent) throw new Error('woke up on another map entirely');
  if(tripDest) throw new Error('woke up with a trip still live');
  if(insideCollider(camera.position.x, camera.position.z, 0.45, playerHeight))
    throw new Error('woke up inside geometry at ('+camera.position.x.toFixed(1)+','+camera.position.z.toFixed(1)+')');
  return 'awake on the quay at ('+camera.position.x.toFixed(1)+','+camera.position.z.toFixed(1)+')';
"""))

print("\n=== and it is where the Sweden trip actually ends ===")

ok &= show("clearing the Fjord comes home here, and this hub sells China", run("""
  gameStarted = true;
  var sweden = DESTINATIONS.filter(function(d){ return d.name === 'Sweden'; })[0];
  if(!sweden) throw new Error('no Sweden in DESTINATIONS');
  if(sweden.homeHub !== enterLadogaMarketHub)
    throw new Error('Sweden still comes home to '+(sweden.homeHub ? 'some other hub' : 'Cairo'));
  // walk the real path: buy the trip, jump to its last leg, clear it, and see where returnToHub() lands
  travelTo({name:'Sweden', legs:SWEDEN_LEGS, homeHub:sweden.homeHub, homeBanner:sweden.homeBanner});
  tripLeg = SWEDEN_LEGS.length - 1;
  advanceTripLeg();
  if(pending !== 'triphome') throw new Error('the last leg did not end the trip (pending='+pending+')');
  returnToHub();
  if(currentHub !== 'ladoga') throw new Error('the trip came home to '+currentHub);
  if(tripDest) throw new Error('came home with the trip still live');
  // `ready` is gone: every card on the board is now a built destination by construction, so what makes
  // one buyable is that it has a road to walk and a way to start walking it.
  var china = DESTINATIONS.filter(function(d){
    return d.name === 'China' && d.legs && d.legs.length && typeof d.go === 'function' && !d.done;
  })[0];
  if(!china) throw new Error('China is not buyable from here');
  return 'home at Aldeigjuborg, and China is on the board at '+china.price;
"""))

print()
print('ALL OK' if ok else 'PROBLEMS FOUND')
sys.exit(0 if ok else 1)
