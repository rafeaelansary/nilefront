#!/usr/bin/env python3
"""Gamla Uppsala: the field, the mound you can get up, and the king who is under it."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bugcheck import run, show

ok = True

# The map's one piece of vertical geometry, and the only climbable thing in the Sweden arc since
# Birka's Borg. A ramp zone is a flat rectangle that reads as sloped only to someone already at its
# height (getTerrainHeight's continuity rule), so the two ways it goes wrong are: it cannot be
# climbed at all, or it can be climbed from the side without walking the path.
ok &= show("the king's mound can be walked up, and only up the path", run("""
  gameStarted=true; enterUppsalaWorld('t');
  // up the path, one step at a time, exactly as the movement code would
  camera.position.set(MOUND_RAMP_X1+1.0, 1.7, MOUND_Z); playerHeight=0;
  var peak=0;
  for(var i=0;i<1200;i++){
    var nx = camera.position.x - 0.035;
    if(!insideCollider(nx, camera.position.z, 0.45, playerHeight)) camera.position.x = nx;
    playerHeight = getTerrainHeight(camera.position.x, camera.position.z, playerHeight);
    peak = Math.max(peak, playerHeight);
    if(camera.position.x < MOUND_X) break;
  }
  if(peak < MOUND_H - 0.01) throw new Error('the path only climbs to '+peak.toFixed(2)+' of '+MOUND_H);
  // the whole crown is standable once you are up there
  var stand=0, miss=0;
  for(var dx=-4;dx<=4;dx++) for(var dz=-4;dz<=4;dz++){
    if(getTerrainHeight(MOUND_X+dx, MOUND_Z+dz, MOUND_H) > MOUND_H-0.01) stand++; else miss++;
  }
  if(miss) throw new Error(miss+' spots on the crown are not standable');
  // ...and you cannot get up it from the side: at ground level the mound is a wall, not a hill.
  // Sampled INSIDE the collider's own half-width, where a square and a circle actually agree — every
  // one of those points must be solid, and none of them may report the crown's height to someone
  // standing at ground level.
  var solid=0, n=0, holes=[];
  var HW = (MOUND_HW);
  for(var a=0;a<16;a++){
    var ang=a/16*Math.PI*2, px=MOUND_X+Math.cos(ang)*HW*0.9, pz=MOUND_Z+Math.sin(ang)*HW*0.9;
    if(px > MOUND_RAMP_X0-0.5 && Math.abs(pz-MOUND_Z) < MOUND_RAMP_HZ) continue;   // that is the path
    n++;
    if(getTerrainHeight(px,pz,0) > 0.01) holes.push([px.toFixed(1),pz.toFixed(1)]);
    if(insideCollider(px,pz,0.45,0)) solid++;
  }
  if(holes.length) throw new Error('the mound can be stepped onto at '+JSON.stringify(holes));
  if(solid !== n) throw new Error('only '+solid+' of '+n+' points inside the mound are solid');
  return 'path climbs to '+peak.toFixed(2)+', '+stand+' standable spots on the crown, all '+n+' flanks solid';
"""))

# Fifteen spawn points across three pools, and the failure modes are all invisible from a screenshot:
# a man inside the temple wall, a man on the ramp rectangle standing under the path's own deck, or a
# man materialising in the player's face on the road they arrived by.
ok &= show("every place a man is put down on this field is clear, and on the ground", run("""
  gameStarted=true; enterUppsalaWorld('t');
  var pools={west:UPPSALA_WEST, east:UPPSALA_EAST, south:UPPSALA_SOUTH}, n=0;
  function onRamp(x,z){
    return x >= MOUND_RAMP_X0-0.8 && x <= MOUND_RAMP_X1+0.8 &&
           z >= MOUND_Z-MOUND_RAMP_HZ-0.8 && z <= MOUND_Z+MOUND_RAMP_HZ+0.8;
  }
  Object.keys(pools).forEach(function(k){
    pools[k].forEach(function(p){
      n++;
      if(insideCollider(p[0],p[1],1.2,0)) throw new Error(k+' '+p+' is inside something at a 1.2 radius');
      if(getTerrainHeight(p[0],p[1],0) !== 0) throw new Error(k+' '+p+' is up on a height zone');
      if(onRamp(p[0],p[1])) throw new Error(k+' '+p+' is on the mound path -- he would stand under it');
      if(Math.hypot(p[0], p[1]-25) < 11) throw new Error(k+' '+p+' is on top of the player arrival');
    });
    for(var i=0;i<pools[k].length;i++) for(var j=i+1;j<pools[k].length;j++){
      var a=pools[k][i], b=pools[k][j];
      if(Math.hypot(a[0]-b[0], a[1]-b[1]) < 5)
        throw new Error(k+': '+a+' and '+b+' are on top of each other');
    }
  });
  return n+' points across three pools, all clear at 1.2 and off the path';
"""))

ok &= show("all three waves spawn, and nothing spawns inside the field", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  var counts=[];
  for(var w=0; w<UPPSALA_WAVES.length; w++){
    jumpToDestStage(d,2,w);
    if(!bots.length) throw new Error('wave '+(w+1)+' spawned nobody');
    bots.forEach(function(b){
      var x=b.mesh.position.x, z=b.mesh.position.z;
      if(insideCollider(x,z,1.1,0)) throw new Error('wave '+(w+1)+' put a '+b.skin+' inside something');
      if(getTerrainHeight(x,z,0) !== 0) throw new Error('wave '+(w+1)+' put a '+b.skin+' on a height zone');
    });
    counts.push((w+1)+':'+bots.length);
  }
  // the troll is the wave-three weight, and it is armoured -- the axe has to have something to answer
  jumpToDestStage(d,2,2);
  var troll = bots.filter(function(b){ return b.skin==='troll'; })[0];
  if(!troll) throw new Error('wave three has no troll in it');
  if(!troll.armoured) throw new Error('the troll is not armoured');
  return counts.join(' ')+', and a troll in the last one';
"""))

# The boss, and the two ways a boss on an outdoor map silently breaks: he stands inside the scenery,
# or there is no walkable line from a respawn to where he is.
ok &= show("the Mound King stands on open ground, and you can walk to him", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,2,UPPSALA_WAVES.length);
  var boss = bots.filter(function(b){ return b.boss; })[0];
  if(!boss) throw new Error('no boss on the boss stage');
  if(boss.skin !== 'moundking') throw new Error('Uppsala ends on a '+boss.skin);
  if(insideCollider(UPPSALA_BOSS.x, UPPSALA_BOSS.z, boss.radius, 0))
    throw new Error('the King spawns inside the field');
  if(getTerrainHeight(UPPSALA_BOSS.x, UPPSALA_BOSS.z, 0) !== 0)
    throw new Error('the King spawns on a height zone -- he would stand underneath it');
  // his whole patrol line, which runs +-4 around his own x
  for(var px=UPPSALA_BOSS.x-4; px<=UPPSALA_BOSS.x+4; px+=0.5)
    if(insideCollider(px, UPPSALA_BOSS.z, boss.radius, 0))
      throw new Error('his patrol walks into something at x='+px.toFixed(1));
  // flood the walkable field from a respawn point and make sure it reaches him
  var R=0.45, step=0.5, sp=usableSpawns()[0], seen={}, stack=[[sp.x,sp.z]], best=1e9;
  function free(x,z){ return Math.abs(x)<28 && Math.abs(z)<28 && !insideCollider(x,z,R,0); }
  seen[Math.round(sp.x/step)+','+Math.round(sp.z/step)]=1;
  while(stack.length){
    var c=stack.pop();
    best=Math.min(best, Math.hypot(c[0]-UPPSALA_BOSS.x, c[1]-UPPSALA_BOSS.z));
    [[step,0],[-step,0],[0,step],[0,-step]].forEach(function(dv){
      var nx=c[0]+dv[0], nz=c[1]+dv[1], k=Math.round(nx/step)+','+Math.round(nz/step);
      if(seen[k] || !free(nx,nz)) return;
      seen[k]=1; stack.push([nx,nz]);
    });
  }
  if(best > 1.6) throw new Error('the closest you can walk to the King is '+best.toFixed(2));
  return Object.keys(seen).length+' walkable spots, closest approach '+best.toFixed(2);
"""))

# The fires are the leg's one piece of map state, and like the Fjord's plank they are re-derived per
# stage rather than toggled by an event -- so dying in the dark and coming back cannot leave the field
# black for a wave that is supposed to be lit.
ok &= show("the King puts the fires out at half health, and only he can", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,2,0);
  if(uppsalaOut) throw new Error('the field is dark in wave one');
  if(!uppsalaFires.length) throw new Error('there are no fires on this map at all');
  var litNow = uppsalaFires.filter(function(f){ return f.flame.visible && f.light.intensity > 0; }).length;
  if(litNow !== uppsalaFires.length) throw new Error(litNow+' of '+uppsalaFires.length+' fires are lit in wave one');
  jumpToDestStage(d,2,UPPSALA_WAVES.length);
  if(uppsalaOut) throw new Error('the field is dark before he does anything');
  var boss = bots.filter(function(b){ return b.boss; })[0];
  boss.hp = boss.maxHp*0.9;
  for(var i=0;i<30;i++) animate();
  if(uppsalaOut) throw new Error('the fires went out at 90% health');
  boss.hp = boss.maxHp*0.45;
  for(var i=0;i<40;i++) animate();
  if(!uppsalaOut) throw new Error('the fires are still lit below half health');
  var out = uppsalaFires.filter(function(f){ return !f.flame.visible && f.light.intensity === 0; }).length;
  if(out !== uppsalaFires.length) throw new Error('only '+out+' of '+uppsalaFires.length+' fires went out');
  // ...and every way back into this leg lights them again
  jumpToDestStage(d,2,1);
  if(uppsalaOut) throw new Error('a wave re-entry left the field dark');
  jumpToDestStage(d,2,UPPSALA_WAVES.length);
  if(uppsalaOut) throw new Error('re-entering the boss stage left the field dark');
  return uppsalaFires.length+' fires: lit through three waves, out below half, lit again on every re-entry';
"""))

# The mound is the bow's reason to exist here, and it is only worth building if it is BOTH: a place
# worth standing, and not a place that wins the fight on its own.
ok &= show("the mound crown is a shooting position, not a safe one", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,2,UPPSALA_WAVES.length);
  var reach = Math.hypot(MOUND_X-UPPSALA_BOSS.x, MOUND_Z-UPPSALA_BOSS.z);
  if(reach > 30) throw new Error('the crown is '+reach.toFixed(1)+' from the King -- outside his grave-cold, so camping it is free');
  if(reach < 12) throw new Error('the crown is only '+reach.toFixed(1)+' from him -- that is not a vantage, it is the fight');
  // and the drop off it is a real drop: standing on the crown you are above every wave's spawn
  var above = 0;
  UPPSALA_WEST.concat(UPPSALA_EAST, UPPSALA_SOUTH).forEach(function(p){
    if(getTerrainHeight(p[0],p[1],0) < MOUND_H - 1) above++;
  });
  if(above !== 15) throw new Error('only '+above+' of 15 spawn points are below the crown');
  return 'crown is '+reach.toFixed(1)+' from the King, '+MOUND_H.toFixed(1)+' above all 15 spawns';
"""))

# The whole arc in one run. Three legs, seven waves, two bosses, and the road home -- what this catches
# that the per-stage checks cannot is the ladder coming apart at a JOIN, which is where a leg added
# after the fact actually breaks.
ok &= show("the whole Sweden trip plays through: Birka, the Fjord, Uppsala, Cairo", run("""
  gameStarted=true; var wasGod=godMode; godMode=true;
  travelTo({name:'Sweden', legs:SWEDEN_LEGS});
  var seen=[], guard=0;
  while(tripDest && guard++ < 40){
    var leg=curLeg();
    seen.push(leg.place+(bossActive?' BOSS':' w'+(tripWave+1))+':'+bots.filter(function(b){return b.alive;}).length);
    bots.forEach(function(b){ if(b.alive) damageBot(b, 1e9); });
    for(var i=0;i<900 && !bots.some(function(b){return b.alive;}) && tripDest; i++) animate();
  }
  for(var i=0;i<600;i++) animate();
  godMode=wasGod;
  var want = ['Birka w1','Birka w2','The Fjord w1','The Fjord w2','The Fjord w3','The Fjord BOSS',
              'Gamla Uppsala w1','Gamla Uppsala w2','Gamla Uppsala w3','Gamla Uppsala BOSS'];
  if(seen.length !== want.length)
    throw new Error('the trip ran '+seen.length+' stages, not '+want.length+': '+seen.join(' '));
  for(var k=0;k<want.length;k++) if(seen[k].indexOf(want[k]) !== 0)
    throw new Error('stage '+(k+1)+' was '+seen[k]+', expected '+want[k]);
  if(!inHub) throw new Error('clearing the King did not send you home');
  if(tripDest) throw new Error('the trip is still running after it ended');
  if(uppsalaWorld.parent) throw new Error('Uppsala is still in the scene back in Cairo');
  if(bots.length) throw new Error(bots.length+' followed you home');
  return seen.join(' -> ')+' -> Cairo';
"""))

sys.exit(0 if ok else 1)
