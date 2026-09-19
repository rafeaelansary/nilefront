#!/usr/bin/env python3
"""The Fjord: the sea, the two ships, and the two fights they make."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bugcheck import run, show

ok = True

ok &= show("fjordWaveAt is deterministic, bounded, moving, and its gradient is the real one", run("""
  var a=fjordWaveAt(3.5,-8.25,12), b=fjordWaveAt(3.5,-8.25,12);
  if(a.y!==b.y) throw new Error('not deterministic');
  var peak=0;
  for(var t=0;t<20;t+=0.37) for(var x=-60;x<=60;x+=3.1) for(var z=-60;z<=60;z+=3.1)
    peak=Math.max(peak, Math.abs(fjordWaveAt(x,z,t).y));
  if(peak > FJORD_AMP+1e-9) throw new Error('height '+peak.toFixed(3)+' exceeds FJORD_AMP');
  if(peak < FJORD_AMP*0.5) throw new Error('the waves cancel: peak only '+peak.toFixed(3));
  var h=1e-4, worst=0;
  for(var i=0;i<400;i++){
    var x=Math.sin(i*12.9)*40, z=Math.cos(i*7.7)*40, t=(i%17)*0.61, g=fjordWaveAt(x,z,t);
    worst=Math.max(worst,
      Math.abs(g.dx-(fjordWaveAt(x+h,z,t).y-fjordWaveAt(x-h,z,t).y)/(2*h)),
      Math.abs(g.dz-(fjordWaveAt(x,z+h,t).y-fjordWaveAt(x,z-h,t).y)/(2*h)));
  }
  if(worst>1e-3) throw new Error('gradient off by '+worst.toExponential(2));
  if(Math.abs(fjordWaveAt(0,0,0).y-fjordWaveAt(0,0,3).y)<1e-6) throw new Error('the sea is not moving');
  return 'peak '+peak.toFixed(3)+', gradient error '+worst.toExponential(1);
"""))

ok &= show("the sea mesh IS the wave function, and its foam is on the steep water", run("""
  gameStarted=true; enterFjordWorld('t');
  var T=7.25; fjordTick(0.016,T);
  var pos=fjordSea.geo.attributes.position, seg=fjordSea.seg, size=fjordSea.size, worst=0, n=0;
  for(var i=0;i<pos.count;i+=7){
    var c=i%(seg+1), r=(i/(seg+1))|0;
    worst=Math.max(worst, Math.abs(pos.getY(i)-fjordWaveAt(-size/2+c*(size/seg), -size/2+r*(size/seg), T).y)); n++;
  }
  if(worst>1e-6) throw new Error('mesh disagrees with fjordWaveAt by '+worst.toExponential(2));
  var y0=pos.getY(0); fjordTick(0.016,T+1.7);
  if(Math.abs(pos.getY(0)-y0)<1e-6) throw new Error('the mesh does not move');
  var samples=[];
  for(var i=0;i<pos.count;i+=7){
    var c=i%(seg+1), r=(i/(seg+1))|0;
    var g=fjordWaveAt(-size/2+c*(size/seg), -size/2+r*(size/seg), T+1.7);
    samples.push({b:fjordSea.cols.getX(i), s:Math.hypot(g.dx,g.dz)});
  }
  samples.sort(function(p,q){return p.b-q.b;});
  var f=(samples.length/5)|0, lo=0, hi=0;
  for(var i=0;i<f;i++){ lo+=samples[i].s; hi+=samples[samples.length-1-i].s; }
  lo/=f; hi/=f;
  if(samples[samples.length-1].b-samples[0].b<0.05) throw new Error('the sea is all one tone');
  if(hi<=lo*1.2) throw new Error('foam is not on the steep water');
  return n+' vertices match; whitest fifth steepness '+hi.toFixed(2)+' vs darkest '+lo.toFixed(2);
"""))

# The design, as an assertion. Wave one is a throwing duel and NOTHING in it may be able to reach the
# player -- the first version of this leg dropped eight melee enemies onto decks touching the player's
# and killed them on arrival, so this is the check that exists to stop that ever coming back.
ok &= show("wave one cannot touch you: every enemy is ranged, and out of reach", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,1,0);
  if(bots.length !== 3) throw new Error('wave one should be three men, got '+bots.length);
  var melee = bots.filter(function(b){ return b.weaponType==='knife'; });
  if(melee.length) throw new Error(melee.length+' melee enemies in the throwing duel');
  if(fjordPlanked) throw new Error('the plank is down during the duel');
  // the gap: nearest point of their deck to the nearest point of yours, against the 3.4 at which a
  // javelin-carrier stops throwing and starts swinging
  var gap = FJORD_FOE_DECK.x2 - FJORD_OWN_DECK.x1 < 0
          ? FJORD_OWN_DECK.x1 - FJORD_FOE_DECK.x2 : 0;
  if(gap <= 3.4) throw new Error('the decks are '+gap.toFixed(2)+' apart -- inside melee reach');
  // and the leash must hold every one of them on their own ship even while they chase
  bots.forEach(function(b){
    b.mesh.position.x = 0; b.mesh.position.z = 0;       // shove one straight onto the player's deck
    fjordTick(0.016, 2.0);
    if(b.mesh.position.x > FJORD_FOE_DECK.x2 + 1e-6)
      throw new Error('a hirdman walked off his ship to x='+b.mesh.position.x.toFixed(2));
  });
  return 'three throwers, '+gap.toFixed(2)+' of water between the decks, all leashed aboard';
"""))

ok &= show("wave two drops the plank and opens the crossing both ways", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,1,0);
  if(fjordGangplank.visible) throw new Error('the plank is visible in wave one');
  if(!insideCollider(-FJORD_RAIL_X,0,0.45,0)) throw new Error('the rail gap is open during the duel');
  jumpToDestStage(d,1,1);
  if(!fjordPlanked) throw new Error('wave two did not drop the plank');
  if(!fjordGangplank.visible) throw new Error('the plank is still hidden');
  if(insideCollider(-FJORD_RAIL_X,0,0.45,0)) throw new Error('the rail gap never opened');
  if(bots.length !== 5) throw new Error('wave two should be five, got '+bots.length);
  if(!bots.some(function(b){return b.weaponType==='knife';})) throw new Error('nobody to meet you on the rail');
  // ...and now a bot IS allowed to come back across
  var b0 = bots[0];
  b0.mesh.position.x = 0; b0.mesh.position.z = 0;
  fjordTick(0.016, 2.0);
  if(Math.abs(b0.mesh.position.x) > 1e-6) throw new Error('the crossing did not open for the crew');
  // the boss keeps it down, and re-entering the leg puts it back up
  jumpToDestStage(d,1,FJORD_WAVES.length);
  if(!fjordPlanked) throw new Error('the plank came up for the boss');
  jumpToDestStage(d,1,0);
  if(fjordPlanked) throw new Error('re-entering wave one left the plank down');
  return 'plank down on wave two, held for the boss, back up on re-entry';
"""))

# The sea used to be lethal ground: you could stand on it for a frame and were then killed for it.
# It is now not ground at all. Both halves of that matter -- you are put back on the ship, and you
# are NOT hurt for having been pushed there -- so both are asserted.
ok &= show("the sea is not walkable: it stops you, it does not drown you", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,1,0);
  function rects(){ return fjordPlanked ? [FJORD_OWN_DECK, FJORD_PLANK, FJORD_FOE_DECK] : [FJORD_OWN_DECK]; }
  function afloat(x,z){ return fjordNearestDeck(x,z,rects())[2] > 1e-8; }
  function put(x,z){
    player.hp=player.maxHp; player.alive=true;
    camera.position.set(x,1.7,z); fjordClampPlayer();
    if(player.hp < player.maxHp) throw new Error('drowned at '+x+','+z+' instead of being stopped');
    if(afloat(camera.position.x, camera.position.z))
      throw new Error('left standing on the water at '+camera.position.x.toFixed(2)+','+camera.position.z.toFixed(2));
    return [camera.position.x, camera.position.z];
  }
  [[0,0],[1.2,5.9],[-1.2,-5.9],[2.0,0]].forEach(function(p){
    var r = put(p[0],p[1]);
    if(Math.abs(r[0]-p[0])>1e-9 || Math.abs(r[1]-p[1])>1e-9)
      throw new Error('your own deck moved you at '+JSON.stringify(p));
  });
  // ...and from anywhere out there you come back to the ship, never to theirs before the plank
  var far = [[-4,0],[0,9],[6,0],[-12,-6],[0,-11],[-5,3],[14,14],[FJORD_FOE_X,0]];
  far.forEach(function(p){
    var r = put(p[0],p[1]);
    if(fjordNearestDeck(r[0],r[1],[FJORD_OWN_DECK])[2] > 1e-8)
      throw new Error('the water at '+JSON.stringify(p)+' put you somewhere that is not your deck');
  });
  jumpToDestStage(d,1,1);
  put(FJORD_FOE_X,0); put(-5.05,0);              // their deck and the plank, once it is down
  var side = put(-5.05,2.6);                      // ...and the water beside the plank is still water
  if(Math.abs(side[1]) > 0.95+1e-9) throw new Error('you walked off the side of the plank');
  return far.length+' stretches of water, four deck points held, the plank walkable and its edges solid';
"""))

# A walk, not a teleport: the clamp has to hold against the actual movement path (resolve collision,
# then clamp) frame after frame, including in the gap-mouth corner where a rail ends and open water
# starts. 4000 steps of shoving in random directions is cheaper than reasoning about that corner.
ok &= show("you cannot walk off either ship, in 4000 steps of trying", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,1,1);                          // plank down: the most open the map ever is
  camera.position.set(0.3,1.7,0);
  var seed=12345, escapes=0, onPlank=0;
  function rnd(){ seed=(seed*1103515245+12345)&0x7fffffff; return seed/0x7fffffff; }
  for(var i=0;i<4000;i++){
    var a=rnd()*Math.PI*2, step=0.18;
    var r=resolveCollision(camera.position.x+Math.cos(a)*step, camera.position.z+Math.sin(a)*step, 0.45, 0);
    camera.position.x=r[0]; camera.position.z=r[1];
    fjordClampPlayer();
    var rects=[FJORD_OWN_DECK, FJORD_PLANK, FJORD_FOE_DECK];
    if(fjordNearestDeck(camera.position.x, camera.position.z, rects)[2] > 1e-8) escapes++;
    if(fjordNearestDeck(camera.position.x, camera.position.z, [FJORD_PLANK])[2] <= 1e-8) onPlank++;
  }
  if(escapes) throw new Error(escapes+' of 4000 steps ended up over water');
  if(!onPlank) throw new Error('4000 steps never found the plank -- the walk never left the home deck');
  return 'never off the ship; '+onPlank+' of those steps were out on the plank';
"""))

# The bug this leg shipped with: PLAYER_SPAWNS is one shared list of town-square points, and out here
# every one of them is open sea. Nothing rejected them, because spawnUsable() only knows colliders.
ok &= show("a death in the Fjord stands you back up on your own deck", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,1,1);
  var seen={};
  for(var i=0;i<10;i++){
    player.alive=true; player.hp=player.maxHp;
    damagePlayer(9999);
    if(player.alive) throw new Error('9999 damage did not kill the player');
    respawnPlayer();
    var x=camera.position.x, z=camera.position.z;
    if(fjordNearestDeck(x,z,[FJORD_OWN_DECK])[2] > 1e-8)
      throw new Error('respawned at '+x.toFixed(1)+','+z.toFixed(1)+' -- that is not your deck');
    if(insideCollider(x,z,0.45,0)) throw new Error('respawned inside the cargo at '+x.toFixed(1)+','+z.toFixed(1));
    seen[x.toFixed(2)+','+z.toFixed(2)] = 1;
  }
  // and the recovery/unstick path reads the same list
  var rec = pickRecoverySpot(FJORD_FOE_X, 4);
  if(fjordNearestDeck(rec.x,rec.z,[FJORD_OWN_DECK])[2] > 1e-8) throw new Error('the unstick spot is in the sea');
  return '10 deaths, '+Object.keys(seen).length+' distinct deck spots, unstick lands aboard too';
"""))

# The point of a bigger deck. Cover only counts if it stands above the line the AI actually shoots
# along -- chest 1.2 to eye 1.7 -- and the old knee-high crates did not, so the duel had no cover in
# it at all. For EVERY man's spawn there must be somewhere on your deck he cannot see you, and
# somewhere you can see him: one without the other is a hiding hole or a firing squad.
ok &= show("every thrower on that deck has a spot you can hide from, and a spot you can shoot from", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,1,0);
  clearBots();                                     // the men themselves are not the cover under test
  scene.updateMatrixWorld();                       // nothing renders headlessly, and a raycast needs
                                                   // world matrices or every prop is tested at the origin
  var stand=[];
  for(var x=-0.5; x<=2.0; x+=0.25) for(var z=-5.9; z<=5.9; z+=0.25){
    if(!insideCollider(x,z,0.45,0) && fjordNearestDeck(x,z,[FJORD_OWN_DECK])[2] <= 1e-8) stand.push([x,z]);
  }
  if(stand.length < 200) throw new Error('only '+stand.length+' places to stand on your own deck');
  var worstHide=1e9, worstShoot=1e9, chest=new THREE.Vector3(), dir=new THREE.Vector3();
  FJORD_WEST.concat(FJORD_EAST).forEach(function(sp){
    var hide=0, shoot=0;
    for(var i=0;i<stand.length;i++){
      var px=stand[i][0], pz=stand[i][1];
      camera.position.set(px,1.7,pz);
      chest.set(sp[0],1.2,sp[1]);
      dir.subVectors(camera.position, chest);
      var dist=dir.length(); dir.normalize();
      var hh=firstHit(chest, dir, dist+1, null);
      if(!hh || hh.dist >= dist-1.2) shoot++; else hide++;
    }
    worstHide=Math.min(worstHide,hide); worstShoot=Math.min(worstShoot,shoot);
  });
  if(worstHide < 12) throw new Error('a thrower with only '+worstHide+' places on the whole deck you can break his line from');
  if(worstShoot < 12) throw new Error('a thrower you can only answer from '+worstShoot+' places');
  return stand.length+' standing places; worst thrower: '+worstHide+' hide from him, '+worstShoot+' shoot back at him';
"""))

# ...and cover you cannot walk past is a wall. The troll comes back across that plank at radius 0.95.
ok &= show("a 1.9-wide troll can walk your whole deck, cargo and all", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,1,1);
  var R=0.95, step=0.2;
  function key(i,j){ return i+','+j; }
  function free(x,z,rect){ return !insideCollider(x,z,R,0) && fjordNearestDeck(x,z,[rect])[2] <= 1e-8; }
  ['own','foe'].forEach(function(which){
    var rect = which==='own' ? FJORD_OWN_DECK : FJORD_FOE_DECK;
    // start at the deck's end of the plank and flood the deck from there
    var sx = which==='own' ? FJORD_OWN_DECK.x1+R+0.05 : FJORD_FOE_DECK.x2-R-0.05, sz = 0;
    if(!free(sx,sz,rect)) throw new Error(which+': the plank mouth itself is blocked');
    var seen={}, stack=[[sx,sz]], minZ=0, maxZ=0;
    seen[key(Math.round(sx/step), Math.round(sz/step))]=1;
    while(stack.length){
      var c=stack.pop(); minZ=Math.min(minZ,c[1]); maxZ=Math.max(maxZ,c[1]);
      [[step,0],[-step,0],[0,step],[0,-step]].forEach(function(dv){
        var nx=c[0]+dv[0], nz=c[1]+dv[1], k=key(Math.round(nx/step), Math.round(nz/step));
        if(seen[k] || !free(nx,nz,rect)) return;
        seen[k]=1; stack.push([nx,nz]);
      });
    }
    if(minZ > -(FJORD_DECK_HL-1.6) || maxZ < FJORD_DECK_HL-1.6)
      throw new Error(which+' deck: a troll off the plank only reaches z '+minZ.toFixed(1)+'..'+maxZ.toFixed(1));
  });
  return 'both decks walk end to end at radius '+R;
"""))

# The climax, run for real: 1500 frames of animate() per case, with the player standing still. The
# boss walks straight at you and does not slide along what blocks him, so anything he can catch a
# shoulder on between his deck and yours ends the fight early in his favour -- he stops, you shoot
# him from cover, and the boarding never happens. This caught exactly that: at a 1.15 rail gap he
# stalled at the gangway for every player position except dead amidships, and at a 1.90 one the Jarl
# grazed the rail from the plank's own edge and stopped a metre and a half short of the deck.
#
# 1500 frames rather than the 900 this ran at while the boss stood on the middle deck: the Jarl is
# two crossings away, not one, and the walk from his stern to your deck takes about 1100 of them.
# Frames, not seconds -- the headless clock runs as fast as the loop does.
ok &= show("the Jarl gets off his ship and onto yours, wherever you stand", run("""
  gameStarted=true;
  var wasGod = godMode; godMode = true;                 // the point is where HE gets to, not your HP
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  var out=[];
  [0, 4.5, -5.5, 6.8, -6.8].forEach(function(pz){
    jumpToDestStage(d,1,FJORD_WAVES.length);
    var boss=bots.filter(function(b){return b.boss;})[0];
    if(!boss) throw new Error('no boss on the boss stage');
    for(var i=0;i<1500;i++){ camera.position.set(1.0,1.7,pz); animate(); }
    var bx=boss.mesh.position.x, bz=boss.mesh.position.z;
    var dist=Math.hypot(bx-1.0, bz-pz);
    // either he is aboard your deck, or he has closed to the range at which a boss stops walking
    if(bx <= FJORD_OWN_DECK.x1 && dist > 4.3)
      throw new Error('with you at z'+pz+' the Jarl stalled at x'+bx.toFixed(2)+' z'+bz.toFixed(2)+', '+dist.toFixed(2)+' away');
    out.push('z'+pz+':'+(bx > FJORD_OWN_DECK.x1 ? 'aboard' : 'in reach of you'));
  });
  godMode = wasGod;
  return out.join(' ');
"""))

sys.exit(0 if ok else 1)
