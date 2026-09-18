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
  if(!insideCollider(-1.6,0,0.45,0)) throw new Error('the rail gap is open during the duel');
  jumpToDestStage(d,1,1);
  if(!fjordPlanked) throw new Error('wave two did not drop the plank');
  if(!fjordGangplank.visible) throw new Error('the plank is still hidden');
  if(insideCollider(-1.6,0,0.45,0)) throw new Error('the rail gap never opened');
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

ok &= show("both decks hold you up, the plank only when it is there, the water never", run("""
  gameStarted=true;
  var d=DESTINATIONS.filter(function(x){return x.name==='Sweden';})[0];
  jumpToDestStage(d,1,0);
  function stand(x,z){
    player.hp=player.maxHp; player.alive=true;
    camera.position.set(x,1.7,z); fjordTick(0.016,3.0); return player.hp;
  }
  [[0,0],[1.2,4.0],[-1.2,-4.0]].forEach(function(p){
    if(stand(p[0],p[1])<player.maxHp) throw new Error('fell through your own deck at '+JSON.stringify(p));
  });
  [[-4,0],[0,8],[6,0],[-12,-6]].forEach(function(p){
    if(stand(p[0],p[1])>0) throw new Error('stood on open water at '+JSON.stringify(p));
  });
  if(stand(FJORD_FOE_X,0)>0) throw new Error('reached their deck before the plank was down');
  jumpToDestStage(d,1,1);
  if(stand(-4,0)<player.maxHp) throw new Error('the plank does not hold you up');
  if(stand(FJORD_FOE_X,0)<player.maxHp) throw new Error('their deck does not hold you up after boarding');
  if(stand(-4,3)>0) throw new Error('the water beside the plank held you up');
  return 'three deck points, four stretches of water, and the plank only once it is down';
"""))

sys.exit(0 if ok else 1)
