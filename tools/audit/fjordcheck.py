#!/usr/bin/env python3
"""The Fjord: the sea, the hulls that float on it, and the decks you may stand on."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bugcheck import run, show

ok = True

ok &= show("fjordWaveAt is deterministic, bounded, moving, and its gradient is the real one", run("""
  if(typeof fjordWaveAt !== 'function') throw new Error('fjordWaveAt is not defined');
  var a = fjordWaveAt(3.5,-8.25,12), b = fjordWaveAt(3.5,-8.25,12);
  if(a.y !== b.y) throw new Error('not deterministic');
  var peak = 0;
  for(var t=0;t<20;t+=0.37) for(var x=-60;x<=60;x+=3.1) for(var z=-60;z<=60;z+=3.1)
    peak = Math.max(peak, Math.abs(fjordWaveAt(x,z,t).y));
  if(peak > FJORD_AMP + 1e-9) throw new Error('height '+peak.toFixed(3)+' exceeds FJORD_AMP '+FJORD_AMP);
  if(peak < FJORD_AMP*0.5) throw new Error('the waves cancel: peak only '+peak.toFixed(3));
  // the gradient must BE the derivative of the height, or foam and hull roll go the wrong way
  var h=1e-4, worst=0;
  for(var i=0;i<400;i++){
    var x=Math.sin(i*12.9)*40, z=Math.cos(i*7.7)*40, t=(i%17)*0.61, g=fjordWaveAt(x,z,t);
    worst = Math.max(worst,
      Math.abs(g.dx - (fjordWaveAt(x+h,z,t).y - fjordWaveAt(x-h,z,t).y)/(2*h)),
      Math.abs(g.dz - (fjordWaveAt(x,z+h,t).y - fjordWaveAt(x,z-h,t).y)/(2*h)));
  }
  if(worst > 1e-3) throw new Error('gradient is off by '+worst.toExponential(2));
  if(Math.abs(fjordWaveAt(0,0,0).y - fjordWaveAt(0,0,3).y) < 1e-6) throw new Error('the sea is not moving');
  return 'peak '+peak.toFixed(3)+' of '+FJORD_AMP.toFixed(2)+', gradient error '+worst.toExponential(1);
"""))

ok &= show("the sea mesh IS the wave function, and its foam is on the steep water", run("""
  gameStarted = true; enterFjordWorld('t');
  var T = 7.25; fjordTick(0.016, T);
  var pos = fjordSea.geo.attributes.position, seg = fjordSea.seg, size = fjordSea.size;
  var worst = 0, n = 0;
  for(var i=0;i<pos.count;i+=7){
    var c=i%(seg+1), r=(i/(seg+1))|0;
    var x=-size/2+c*(size/seg), z=-size/2+r*(size/seg);
    worst = Math.max(worst, Math.abs(pos.getY(i) - fjordWaveAt(x,z,T).y)); n++;
  }
  if(worst > 1e-6) throw new Error('mesh disagrees with fjordWaveAt by '+worst.toExponential(2));
  var y0 = pos.getY(0); fjordTick(0.016, T+1.7);
  if(Math.abs(pos.getY(0)-y0) < 1e-6) throw new Error('the mesh does not move between frames');
  // whitest fifth against darkest fifth by steepness -- an absolute cutoff would break the moment
  // somebody retuned the palette
  var samples=[];
  for(var i=0;i<pos.count;i+=7){
    var c=i%(seg+1), r=(i/(seg+1))|0;
    var x=-size/2+c*(size/seg), z=-size/2+r*(size/seg), g=fjordWaveAt(x,z,T+1.7);
    samples.push({b:fjordSea.cols.getX(i), s:Math.hypot(g.dx,g.dz)});
  }
  samples.sort(function(p,q){ return p.b-q.b; });
  var f=(samples.length/5)|0, lo=0, hi=0;
  for(var i=0;i<f;i++){ lo+=samples[i].s; hi+=samples[samples.length-1-i].s; }
  lo/=f; hi/=f;
  if(samples[samples.length-1].b - samples[0].b < 0.05) throw new Error('the sea is all one tone');
  if(hi <= lo*1.2) throw new Error('foam is not on the steep water: '+hi.toFixed(3)+' vs '+lo.toFixed(3));
  return n+' vertices match; whitest fifth steepness '+hi.toFixed(2)+' vs darkest '+lo.toFixed(2);
"""))

ok &= show("lashed hulls are a floor, un-lashed hulls ride the swell", run("""
  gameStarted = true; enterFjordWorld('t');
  var T = 4.5; fjordTick(0.016, T);
  if(fjordShips.length !== 4) throw new Error('expected 4 hulls, got '+fjordShips.length);
  // your own deck and the two alongside are lashed: dead flat, or the bots standing on them at y=0
  // would be knee-deep in planking
  [0,1,2].forEach(function(i){
    var s = fjordShips[i];
    if(!s.lashed) throw new Error('ship '+i+' should be lashed for the hold');
    if(Math.abs(s.grp.position.y) > 1e-9 || Math.abs(s.grp.rotation.z) > 1e-9)
      throw new Error('lashed ship '+i+' is still moving: y='+s.grp.position.y+' roll='+s.grp.rotation.z);
  });
  // the third is still rowing in, so it heaves and heels on the real surface
  var b = fjordShips[3], w = fjordWaveAt(b.x, b.z, T);
  if(b.lashed) throw new Error('the bow ship is lashed before the boss is called');
  if(Math.abs(b.grp.position.y - (w.y-0.10)) > 1e-9) throw new Error('the bow ship is not on the water');
  if(Math.abs(b.grp.rotation.z + w.dx*0.55) > 1e-9) throw new Error('it does not heel with the slope');
  var y0 = b.grp.position.y; fjordTick(0.016, T+2.2);
  if(Math.abs(b.grp.position.y - y0) < 1e-6) throw new Error('the bow ship does not heave');
  return 'three lashed flat, the fourth heaving on the swell';
"""))

ok &= show("the boss grapples the third ship and the arena grows", run("""
  gameStarted = true;
  var d = DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d, 1, 0);
  if(fjordBowLashed) throw new Error('the bow is lashed at the start of the leg');
  if(fjordGangplank.visible) throw new Error('the gangplank is down before anyone grapples');
  // the boss stage is what calls it
  jumpToDestStage(d, 1, FJORD_WAVES.length);
  if(!bossActive) throw new Error('the boss stage spawned no boss');
  if(!fjordBowLashed) throw new Error('the boss arrived but the third ship never grappled');
  if(!fjordGangplank.visible) throw new Error('the gangplank never dropped');
  if(!fjordShips[3].lashed) throw new Error('the bow hull is still floating free under the boss');
  var boss = bots.filter(function(b){return b.boss;})[0];
  if(boss.mesh.position.z > FJORD_BOW_DECK.z2) throw new Error('the boss is not on the third ship');
  return 'bow grappled, plank down, boss on the far deck at z='+boss.mesh.position.z;
"""))

ok &= show("every deck holds you up and the fjord does not", run("""
  gameStarted = true;
  var d = DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d, 1, 0);
  function stand(x,z){
    player.hp = player.maxHp; player.alive = true;
    camera.position.set(x, 1.7, z);
    fjordTick(0.016, 3.0);
    return player.hp;
  }
  // the three lashed decks must all be solid ground
  [[0,0],[0,3.5],[-3.6,0],[-4.5,-4],[3.6,0],[4.5,4]].forEach(function(p){
    if(stand(p[0],p[1]) < player.maxHp) throw new Error('fell through the deck at '+JSON.stringify(p));
  });
  // and the water between and beyond them must not be
  [[0,8],[8,0],[-9,-9],[0,-8.5],[0,-20]].forEach(function(p){
    if(stand(p[0],p[1]) > 0) throw new Error('stood on open water at '+JSON.stringify(p));
  });
  // the far deck only holds you up once it has grappled
  if(stand(0,-11.6) > 0) throw new Error('the un-grappled third ship held the player up');
  jumpToDestStage(d, 1, FJORD_WAVES.length);
  if(stand(0,-11.6) < player.maxHp) throw new Error('the grappled third ship does not hold the player up');
  if(stand(0,-5.6) < player.maxHp) throw new Error('the gangplank does not hold the player up');
  return 'six deck points solid, five stretches of water lethal, the crossing opens with the boss';
"""))

ok &= show("you can actually cross between lashed hulls, and not off the bow until it is time", run("""
  gameStarted = true;
  var d = DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d, 1, 0);
  function stand(x,z){
    player.hp = player.maxHp; player.alive = true;
    camera.position.set(x,1.7,z); fjordTick(0.016, 3.0); return player.hp;
  }
  // The gap between your hull and each raider's. Butted rectangles left a strip of nothing here and
  // crossing between two ships that are lashed together drowned you, which is the one move a
  // boarding action has to allow.
  [[-1.42,0],[-1.42,2.5],[-1.8,-2.0],[1.42,0],[1.8,2.0],[2.0,-1.5]].forEach(function(p){
    if(stand(p[0],p[1]) < player.maxHp) throw new Error('drowned crossing a lashed gap at '+JSON.stringify(p));
  });
  // the bow is railed while there is nothing out there to reach...
  if(fjordColliders.indexOf(fjordBowRail) < 0) throw new Error('the bow rail is missing during the hold');
  if(!insideCollider(0, -5.0, 0.45, 0)) throw new Error('the bow rail is not actually solid');
  // ...and the rail coming off IS the crossing opening
  jumpToDestStage(d, 1, FJORD_WAVES.length);
  if(fjordColliders.indexOf(fjordBowRail) >= 0) throw new Error('the bow rail never came off');
  if(insideCollider(0, -5.0, 0.45, 0)) throw new Error('the bow is still blocked after the grapple');
  // and re-entering the leg must put it back, or a death mid-boss leaves the bow open forever
  jumpToDestStage(d, 1, 0);
  if(fjordColliders.indexOf(fjordBowRail) < 0) throw new Error('re-entering the leg did not restore the bow rail');
  return 'six crossing points safe; bow railed, opened by the grapple, restored on re-entry';
"""))

sys.exit(0 if ok else 1)
