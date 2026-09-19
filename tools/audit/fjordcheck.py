#!/usr/bin/env python3
"""The Fjord: the sea, the three ships, and the three fights they make."""
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
  function afloat(x,z){ return fjordNearestDeck(x,z,fjordDecks(false))[2] > 1e-8; }
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
  // ...and once the third ship is lashed on you come back up on the MIDDLE deck, not all the way home
  jumpToDestStage(d,1,FJORD_WAVES.length);
  for(var j=0;j<6;j++){
    player.alive=true; player.hp=player.maxHp; damagePlayer(9999); respawnPlayer();
    var fx=camera.position.x, fz=camera.position.z;
    if(fjordNearestDeck(fx,fz,[FJORD_FOE_DECK])[2] > 1e-8)
      throw new Error('a death at the Jarl put you at '+fx.toFixed(1)+','+fz.toFixed(1)+' -- not the middle deck');
    if(insideCollider(fx,fz,0.45,0)) throw new Error('respawned inside their cargo at '+fx.toFixed(1)+','+fz.toFixed(1));
  }
  return '10 deaths, '+Object.keys(seen).length+' distinct deck spots, unstick lands aboard too, '
       + 'and a death at the Jarl keeps the deck you took';
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

# ---- the third keel: wave three, and the deck the arena grows by ----
# The whole set piece is built on "the arena grows as you win", and until the Jarl's ship there was
# exactly one growth in it. This asserts the second one from both ends: nothing of his exists while
# the duel is on -- not the hull's position, not the plank, not the gap in the rail -- and all three
# are there on wave three, on a stage that can be entered cold.
ok &= show("wave three lashes the third ship on, and only wave three", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  var gateX = FJORD_JARL_X + FJORD_RAIL_X;
  jumpToDestStage(d,1,0);
  if(fjordLashed) throw new Error('the Jarl is alongside during the duel');
  if(fjordJarlPlank.visible) throw new Error('his plank is down during the duel');
  if(!insideCollider(gateX,0,0.45,0)) throw new Error('his rail gap is open before he is there');
  if(Math.abs(fjordJarlShip.grp.position.x - FJORD_JARL_FAR.x) > 0.01)
    throw new Error('his hull is not out in the fog: x='+fjordJarlShip.grp.position.x.toFixed(2));
  if(fjordDecks(false).indexOf(FJORD_JARL_DECK) >= 0) throw new Error('his deck is walkable in wave one');
  jumpToDestStage(d,1,2);
  if(!fjordLashed) throw new Error('wave three did not lash him on');
  if(!fjordJarlPlank.visible) throw new Error('the second plank never dropped');
  if(insideCollider(gateX,0,0.45,0)) throw new Error('his rail gap never opened');
  if(Math.abs(fjordJarlShip.grp.position.x - FJORD_JARL_X) > 0.01)
    throw new Error('his hull did not come alongside: x='+fjordJarlShip.grp.position.x.toFixed(2));
  if(fjordJarlShip.grp.rotation.y !== 0) throw new Error('he lashed on at an angle');
  if(!fjordJarlShip.lashed) throw new Error('his hull is still riding the swell with men on it');
  if(fjordDecks(false).indexOf(FJORD_JARL_DECK) < 0) throw new Error('his deck is not floor');
  if(fjordDecks(true).indexOf(FJORD_JARL_DECK) < 0) throw new Error('his deck is not floor for the crew');
  // the champion is on it, and he is the armoured one
  var troll = bots.filter(function(b){ return b.skin==='troll'; })[0];
  if(!troll) throw new Error('wave three has no troll in it');
  if(!troll.armoured) throw new Error('the troll is not armoured -- the axe has nothing to answer');
  if(fjordNearestDeck(troll.mesh.position.x, troll.mesh.position.z, [FJORD_JARL_DECK])[2] > 1e-8)
    throw new Error('the champion is not on the jarl deck');
  // ...and going back to the duel sends the whole thing out to sea again
  jumpToDestStage(d,1,0);
  if(fjordLashed || fjordJarlPlank.visible) throw new Error('re-entering wave one left him lashed on');
  if(!insideCollider(gateX,0,0.45,0)) throw new Error('re-entering wave one left his rail gap open');
  return 'out in the fog for waves one and two, alongside for three, and back out on re-entry';
"""))

# His deck is spawn ground for the only pool in the game that is a ship -- and the troll standing on
# it is 1.9 across, so "clear" here means clear at a radius nothing else in this leg is measured at.
ok &= show("every place a man stands on the Jarl's deck is on it, and clear", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,1,2);
  FJORD_JARL_POOL.forEach(function(p){
    if(fjordNearestDeck(p[0],p[1],[FJORD_JARL_DECK])[2] > 1e-8)
      throw new Error('spawn '+p+' is not on his deck at all');
    if(insideCollider(p[0],p[1],1.1,0)) throw new Error('spawn '+p+' is inside his cargo at a 1.1 radius');
  });
  // no two of them on top of each other, or wave three spawns men inside men
  for(var i=0;i<FJORD_JARL_POOL.length;i++) for(var j=i+1;j<FJORD_JARL_POOL.length;j++){
    var a=FJORD_JARL_POOL[i], b=FJORD_JARL_POOL[j];
    if(Math.hypot(a[0]-b[0], a[1]-b[1]) < 1.6) throw new Error('spawns '+a+' and '+b+' are on top of each other');
  }
  return FJORD_JARL_POOL.length+' places to stand, all aboard him and all clear at 1.1';
"""))

# The boss himself. He ends the trip, so the two things that can silently ruin that are: he spawns
# inside his own ship, or there is no walkable line from where you respawn to where he stands.
ok &= show("the Jarl stands clear on his own deck, and you can walk to him", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,1,FJORD_WAVES.length);
  var boss = bots.filter(function(b){ return b.boss; })[0];
  if(!boss) throw new Error('no boss on the boss stage');
  if(boss.skin !== 'jarl') throw new Error('the Fjord ends on a '+boss.skin);
  if(!fjordPlanked || !fjordLashed) throw new Error('the boss stage did not open both crossings');
  if(insideCollider(FJORD_BOSS.x, FJORD_BOSS.z, boss.radius, 0))
    throw new Error('the Jarl spawns inside his own ship');
  if(fjordNearestDeck(FJORD_BOSS.x, FJORD_BOSS.z, [FJORD_JARL_DECK])[2] > 1e-8)
    throw new Error('the Jarl is not on his own deck');
  // flood the walkable floor from where a death puts you, at the player's own radius, and see
  // whether it reaches him
  var R=0.45, step=0.25, rects=fjordDecks(false);
  function free(x,z){ return !insideCollider(x,z,R,0) && fjordNearestDeck(x,z,rects)[2] <= 1e-8; }
  var sp = usableSpawns()[0], seen={}, stack=[[sp.x,sp.z]], best=1e9;
  seen[Math.round(sp.x/step)+','+Math.round(sp.z/step)]=1;
  if(!free(sp.x,sp.z)) throw new Error('the respawn point itself is not walkable');
  while(stack.length){
    var c=stack.pop();
    best=Math.min(best, Math.hypot(c[0]-FJORD_BOSS.x, c[1]-FJORD_BOSS.z));
    [[step,0],[-step,0],[0,step],[0,-step]].forEach(function(dv){
      var nx=c[0]+dv[0], nz=c[1]+dv[1], k=Math.round(nx/step)+','+Math.round(nz/step);
      if(seen[k] || !free(nx,nz)) return;
      seen[k]=1; stack.push([nx,nz]);
    });
  }
  if(best > 2.6) throw new Error('the closest you can walk to the Jarl is '+best.toFixed(2)+' -- out of axe reach');
  return Object.keys(seen).length+' walkable spots from the respawn, closest approach '+best.toFixed(2);
"""))

# THE SHIELD WALL, as arithmetic. At half health frontal damage halves, and the Dane Axe's
# armourPierce is x2 against a boss -- so the axe comes through the wall at exactly its own damage
# and everything else comes through at half. If either number ever moves, this is the fight that
# quietly stops having a question in it.
ok &= show("the shield wall halves what hits it, and the axe reads straight through", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,1,FJORD_WAVES.length);
  var boss = bots.filter(function(b){ return b.boss; })[0];
  var axe = swedenWeapons[0].userData, bow = swedenWeapons[1].userData;
  if(!axe.armourPierce) throw new Error('the Dane Axe has no armourPierce left');
  // stand in front of him, and make him face you
  boss.mesh.position.set(FJORD_BOSS.x, 0, FJORD_BOSS.z);
  camera.position.set(FJORD_BOSS.x, 1.7, FJORD_BOSS.z-3.2);
  boss.facing = 0;
  function hit(dmg){ var h0=boss.hp; damageBot(boss, dmg); var d0=h0-boss.hp; boss.hp=h0; return d0; }
  if(boss.wallUp) throw new Error('the wall is up before he is hurt');
  if(Math.abs(hit(100)-100) > 1e-6) throw new Error('the wall is already reducing damage at full health');
  // drive him under half and let the AI set the shield, the way the fight does
  boss.hp = boss.maxHp*0.4;
  for(var i=0;i<20;i++) animate();
  if(!boss.wallUp) throw new Error('he never set his shield at 40% health');
  var frontal = hit(100), pierced = hit(axe.damage*axe.armourPierce), plain = hit(bow.damage);
  if(Math.abs(frontal-50) > 1e-6) throw new Error('frontal damage is '+frontal+', not halved');
  if(Math.abs(pierced-axe.damage) > 1e-6)
    throw new Error('the axe reads '+pierced.toFixed(1)+' through the wall, not its own '+axe.damage);
  if(Math.abs(plain-bow.damage*0.5) > 1e-6) throw new Error('the bow reads '+plain.toFixed(1)+' through the wall');
  // ...and from behind him the shield is not in the way
  camera.position.set(FJORD_BOSS.x, 1.7, FJORD_BOSS.z+3.2);
  if(Math.abs(hit(100)-100) > 1e-6) throw new Error('the wall works from behind him too');
  return 'front 50 of 100, axe '+pierced.toFixed(0)+' of its own '+axe.damage+', behind him 100 of 100';
"""))

# The whole leg, start to finish, in one run: three waves, the boss, and the crossing it hands on to.
# Every piece of this is asserted somewhere above in isolation -- what this one catches is the ladder
# coming apart at a JOIN, which is the failure no single-stage test can see.
#
# The Jarl used to end the Sweden trip and send the player home to Cairo. He does not any more: a third
# leg follows him now, so what this asserts is the HANDOVER -- his death crosses to Gamla Uppsala, on
# the leg machinery, with the right map under the player's feet when it lands.
ok &= show("the whole leg plays through: three fights, the Jarl, and the crossing inland", run("""
  gameStarted=true; var wasGod=godMode; godMode=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,1,0);
  var seen=[], want=['3', '5+plank', '5+plank+lash', '1+plank+lash'];
  for(var w=0; w<FJORD_WAVES.length+1; w++){
    seen.push(bots.filter(function(b){return b.alive;}).length
              + (fjordPlanked?'+plank':'') + (fjordLashed?'+lash':''));
    bots.forEach(function(b){ if(b.alive) damageBot(b, 1e6); });
    for(var i=0;i<600 && !bots.some(function(b){return b.alive;}); i++) animate();
  }
  for(var k=0;k<want.length;k++) if(seen[k] !== want[k])
    throw new Error('stage '+(k+1)+' was '+seen[k]+', expected '+want[k]+' (whole ladder: '+seen.join(' ')+')');
  if(bossActive) throw new Error('the boss bar is still up after he fell');
  for(var i=0;i<900;i++) animate();
  if(inHub) throw new Error('clearing the Jarl went home instead of inland');
  if(!tripDest) throw new Error('the trip ended on the Jarl');
  var leg = curLeg();
  if(!leg || leg.place !== 'Gamla Uppsala')
    throw new Error('the Jarl handed on to '+(leg ? leg.place : 'nowhere'));
  if(fjordWorld.parent) throw new Error('the Fjord is still in the scene on the next leg');
  if(!uppsalaWorld.parent) throw new Error('the crossing did not land on Uppsala');
  if(tripWave !== 0) throw new Error('the next leg started at wave '+(tripWave+1));
  return seen.join(' -> ')+' -> Gamla Uppsala';
"""))

sys.exit(0 if ok else 1)
