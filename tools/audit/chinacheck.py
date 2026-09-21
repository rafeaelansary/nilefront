#!/usr/bin/env python3
"""China: the weapons loadout, then Xiangyang and Yamen as they land."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bugcheck import run, show

ok = True

# The engine change the whole Xiangyang redesign rests on. Before it, spawnBot() placed every actor at
# y=0 and left groundY unseeded, so the per-frame terrain code (which feeds a bot its own last height as
# curH) rejected any raised zone on the first frame and every frame after -- an enemy placed on a
# rampart stood inside the wall forever. Asserted against Birka's Borg, which is the only climbable
# plateau in the game that predates China, so this is testing the ENGINE and not the new map.
ok &= show("a bot spawned on raised ground stands on it, not inside it", run("""
  gameStarted = true;
  enterSwedenWorld('t');
  // the Borg's crown: a plateau height zone at BORG_H, with the rock's own collider under it
  var zone = heightZonesSweden.filter(function(z){ return z.type==='plateau'; })[0];
  if(!zone) throw new Error('Birka has no plateau zone to test against');
  var cx = (zone.x1+zone.x2)/2, cz = (zone.z1+zone.z2)/2;
  if(getTerrainHeight(cx, cz, undefined) < 1) throw new Error('the plateau is not actually raised');
  clearBots();
  var m = spawnBot(cx, cz, 0x808080, [cx,0,cz], [cx,0,cz], 'pistol', {skin:'hirdman', hp:100});
  var bd = m.userData.data;
  if(Math.abs(bd.groundY - zone.y) > 1e-6)
    throw new Error('spawned on the crown but groundY is '+bd.groundY+', expected '+zone.y);
  if(Math.abs(m.position.y - zone.y) > 1e-6)
    throw new Error('spawned on the crown but sits at y='+m.position.y.toFixed(2));
  // ...and it must STAY up there across frames rather than sinking once the per-frame rule runs
  for(var i=0;i<30;i++) animate();
  if(bd.groundY < zone.y - 0.2)
    throw new Error('the bot sank to '+bd.groundY.toFixed(2)+' after 30 frames');
  // a bot on flat ground is unaffected -- this must not have moved anything that already worked
  clearBots();
  var f = spawnBot(0, 24, 0x808080, [0,0,24], [0,0,24], 'knife', {skin:'draugr', hp:100});
  if(Math.abs(f.userData.data.groundY) > 1e-6) throw new Error('a bot on flat ground got groundY '+f.userData.data.groundY);
  clearBots();
  return 'plateau spawn holds '+zone.y.toFixed(1)+' across 30 frames; flat ground still 0';
"""))

# The same silhouette guard the Dane Axe carries, re-run for this weapon's own envelope. The box
# measure in bugcheck.py answers "is it on screen"; this answers "how big may it be", which is the
# question a two-hander actually has to keep answering -- the axe's own history is a tuning pass that
# shrank it because it measured a diagonal cylinder as a box and concluded it had no room left.
ok &= show("the Zhanmadao fills its frame and stays off the crosshair", run("""
  function applyM(M,x,y,z){ return {x:M[0]*x+M[4]*y+M[8]*z+M[12], y:M[1]*x+M[5]*y+M[9]*z+M[13], z:M[2]*x+M[6]*y+M[10]*z+M[14]}; }
  function silhouette(w, aspect){
    w.updateMatrixWorld(true);
    var p=w.userData.pos, s=w.scale.x;
    var tanV=Math.tan(75*Math.PI/180/2), tanH=tanV*aspect;
    var right=-9,left=9,top=-9,bottom=9,cross=9;
    function take(sx,sy,rad){
      right=Math.max(right,sx+rad); left=Math.min(left,sx-rad);
      top=Math.max(top,sy+rad); bottom=Math.min(bottom,sy-rad);
      cross=Math.min(cross, Math.max(0, Math.hypot(sx,sy)-rad));
    }
    w.traverse(function(m){
      if(!m.isMesh || !m.geometry) return;
      var g=m.geometry, M=m.matrixWorld;
      if(g.type==='CylinderGeometry'){
        var pr=g.parameters;
        for(var i=0;i<=24;i++){
          var f=i/24, q=applyM(M,0,(f-0.5)*pr.height,0);
          var r=pr.radiusBottom+(pr.radiusTop-pr.radiusBottom)*f;
          q.x+=p.x; q.y+=p.y; q.z+=p.z; if(q.z>-0.1) continue;
          take(q.x/(-q.z*tanH), q.y/(-q.z*tanV), (r*s)/(-q.z*tanV));
        }
      } else {
        var h=g._half||{x:0,y:0,z:0}, o=g._offset||{x:0,y:0,z:0};
        for(var a=-1;a<=1;a+=2) for(var b=-1;b<=1;b+=2) for(var c=-1;c<=1;c+=2){
          var q=applyM(M,o.x+a*h.x,o.y+b*h.y,o.z+c*h.z);
          q.x+=p.x; q.y+=p.y; q.z+=p.z; if(q.z>-0.1) continue;
          take(q.x/(-q.z*tanH), q.y/(-q.z*tanV), 0);
        }
      }
    });
    return {right:right,left:left,top:top,bottom:bottom,cross:cross};
  }
  var dao = chinaWeapons.filter(function(w){ return w.userData.name==='Zhanmadao'; })[0];
  if(!dao) throw new Error('no Zhanmadao in the China loadout');
  var m = silhouette(dao, 16/9);
  var swayX=(0.016+0.006+0.05)/(0.76*Math.tan(75*Math.PI/180/2)*(16/9));
  var riseY=(0.05+0.005)/(0.76*Math.tan(75*Math.PI/180/2));
  if(m.right > 0.93)        throw new Error('right edge at '+m.right.toFixed(2)+' -- it will clip the frame when it sways');
  if(m.right + swayX > 1.0) throw new Error('a hard flick takes it off the right of the frame');
  if(m.top   > 0.90)        throw new Error('the point is at '+m.top.toFixed(2)+' -- it clips the top');
  if(m.top + riseY > 1.0)   throw new Error('a hard flick takes the point off the top of the frame');
  if(m.left  < -0.02)       throw new Error('it has crossed to the left of the sight line');
  if(m.bottom > -1.35)      throw new Error('the grip ends at '+m.bottom.toFixed(2)+' -- inside the frame, so it hangs in mid-air');
  if(m.cross < 0.25)        throw new Error('only '+m.cross.toFixed(2)+' of clear screen around the crosshair');
  if(m.top < 0.70)          throw new Error('the point only reaches '+m.top.toFixed(2)+' -- the sabre has shrunk');
  return 'right '+m.right.toFixed(2)+' left '+m.left.toFixed(2)+' top '+m.top.toFixed(2)+
         ' bottom '+m.bottom.toFixed(2)+' crosshair '+m.cross.toFixed(2)+
         ' (worst-case sway: right '+(m.right+swayX).toFixed(2)+', top '+(m.top+riseY).toFixed(2)+')';
"""))

ok &= show("the China loadout is three weapons, each with a complete userData block", run("""
  if(typeof chinaWeapons === 'undefined') throw new Error('chinaWeapons is not defined');
  if(chinaWeapons.length !== 3) throw new Error('expected 3 weapons, got '+chinaWeapons.length);
  var names = chinaWeapons.map(function(w){ return w.userData.name; });
  ['Zhanmadao','Repeating Crossbow','Thunderclap Bomb'].forEach(function(n){
    if(names.indexOf(n) < 0) throw new Error(n+' is missing from chinaWeapons (have: '+names.join(', ')+')');
  });
  chinaWeapons.forEach(function(w){
    var u = w.userData;
    if(!u.pos || typeof u.pos.x !== 'number') throw new Error(u.name+': userData.pos is not a THREE.Vector3');
    if(typeof u.muzzleZ !== 'number') throw new Error(u.name+': no muzzleZ');
    if(typeof u.recoil !== 'number') throw new Error(u.name+': no recoil');
    if(!u.melee && !u.grenade && typeof u.magSize !== 'number')
      throw new Error(u.name+': a non-melee, non-grenade weapon needs a magSize');
  });
  // the Zhanmadao is the armour-answering melee weapon, the same role the Dane Axe plays
  var dao = chinaWeapons[0].userData;
  if(!dao.melee) throw new Error('the Zhanmadao is not melee');
  if(!dao.armourPierce || dao.armourPierce < 1.5) throw new Error('the Zhanmadao has no real armourPierce');
  // the crossbow is the rapid one: distinct from every single-shot bow/crossbow already in the game
  var xbow = chinaWeapons[1].userData;
  if(!xbow.auto) throw new Error('the Repeating Crossbow is not auto-fire');
  if(!(xbow.magSize >= 8)) throw new Error('the Repeating Crossbow magazine is only '+xbow.magSize+', too small to read as repeating');
  // the bomb is a grenade, the same mechanism the Naft Pot and Grenade Launcher already use
  var bomb = chinaWeapons[2].userData;
  if(!bomb.grenade) throw new Error('the Thunderclap Bomb does not use the grenade mechanic');
  if(!(bomb.splashRadius > 0)) throw new Error('the Thunderclap Bomb has no splashRadius');
  return names.join(', ')+' -- all present with complete userData';
"""))

ok &= show("Xiangyang is a real world: enterable, removable, reachable from /tp", run("""
  gameStarted = true;
  if(typeof xiangyangWorld === 'undefined') throw new Error('xiangyangWorld is not defined');
  if(typeof xiangyangColliders === 'undefined') throw new Error('xiangyangColliders is not defined');

  enterXiangyangWorld('test');
  if(!xiangyangWorld.parent) throw new Error('enterXiangyangWorld did not add the world to the scene');
  if(activeColliders !== xiangyangColliders) throw new Error('activeColliders was not swapped to Xiangyang');
  if(insideCollider(camera.position.x, camera.position.z, 0.45, 0))
    throw new Error('the player arrives inside geometry');
  if(weapons !== chinaWeapons) throw new Error('the China loadout was not equipped on entry');

  enterSwedenWorld('back');
  if(xiangyangWorld.parent) throw new Error('clearWorldGroups() does not remove xiangyangWorld');
  if(activeColliders !== swedenColliders) throw new Error('leaving did not restore Birka colliders');

  if(!adminTp(['xiangyang'])) throw new Error('/tp xiangyang did not work');
  if(!xiangyangWorld.parent) throw new Error('/tp xiangyang did not enter the world');
  return 'enter/leave/tp all clean, China loadout equipped';
"""))

# The rampart is the point of this map, and it only exists if a defender can actually stand on it.
ok &= show("the wall carries a real rampart, reachable by its own stair", run("""
  gameStarted = true;
  enterXiangyangWorld('t');
  // the walk itself: a plateau at the wall's height, over the wall's own footprint
  var walk = heightZonesXiangyang.filter(function(z){ return z.type==='plateau' && Math.abs(z.y-XY_WALL_H)<1e-6; });
  if(!walk.length) throw new Error('the wall has no rampart plateau at all');
  var onWalk = walk.filter(function(z){ return z.x1 < -8 && z.x2 > -12; })[0];
  if(!onWalk) throw new Error('no rampart bay covers x=-10, where the garrison is meant to stand');
  if(Math.abs(getTerrainHeight(-10, XY_WALL_Z, undefined) - XY_WALL_H) > 1e-6)
    throw new Error('terrain at x=-10 on the wall reads '+getTerrainHeight(-10,XY_WALL_Z,undefined));
  // a bot put up there stays up there -- the whole reason the engine fix exists
  clearBots();
  var m = spawnBot(-10, XY_WALL_Z, 0x808080, [-10,0,XY_WALL_Z], [-10,0,XY_WALL_Z], 'pistol',
                   {skin:'songcrossbowman', hp:100});
  if(Math.abs(m.userData.data.groundY - XY_WALL_H) > 1e-6)
    throw new Error('a crossbowman on the wall seeded groundY '+m.userData.data.groundY);
  // ...across a long run, with the player far away and out of his line, so he is on the WANDER branch
  // the whole time -- which is exactly the case that used to walk him off a 2.7-wide walk in under a
  // second. The leash in xiangyangTick() is what holds him.
  camera.position.set(0, 1.7, 26);
  for(var i=0;i<300;i++) animate();
  if(m.userData.data.groundY < XY_WALL_H - 0.3)
    throw new Error('he sank to '+m.userData.data.groundY.toFixed(2)+' after 300 frames of wandering');
  if(Math.abs(m.position.z - XY_WALL_Z) > XY_WALL_T)
    throw new Error('he wandered to z='+m.position.z.toFixed(2)+', off the wall entirely');
  clearBots();
  // the stair on the inside face: a ramp zone that actually reaches the walk
  var stair = heightZonesXiangyang.filter(function(z){ return z.type==='ramp' && z.axisX===false
                 && Math.max(z.y1,z.y2) >= XY_WALL_H-1e-6 && z.z2 < XY_WALL_Z; })[0];
  if(!stair) throw new Error('there is no stair up the inside of the wall');
  var lowZ = (stair.y1 > stair.y2) ? stair.z2 : stair.z1;
  if(Math.abs(getTerrainHeight((stair.x1+stair.x2)/2, lowZ, undefined)) > 0.2)
    throw new Error('the stair does not start at ground level');
  return 'rampart at '+XY_WALL_H+' over '+walk.length+' bays, a crossbowman holds it, and a stair reaches it';
"""))

# The breach: shut is a solid bay with no way through it; open is a climbable pile with no collider.
# Re-derivable state on the fjordSetPlank pattern, so entering, dying or /tp-ing can never disagree.
ok &= show("the breach is re-derivable state: solid bay, then a pile you climb", run("""
  gameStarted = true;
  enterXiangyangWorld('t');
  var bx = (XY_BREACH_X0+XY_BREACH_X1)/2;
  if(xiangyangBreached) throw new Error('the wall is already breached on a fresh entry');
  if(!xyBreachWall.visible) throw new Error('the intact bay is not visible while the wall is whole');
  if(xyBreachRubble.visible) throw new Error('the rubble is visible before anything has come down');
  if(!insideCollider(bx, XY_WALL_Z, 0.45, 0)) throw new Error('the intact bay does not block the gap');
  if(heightZonesXiangyang.indexOf(xyBreachZone[0]) >= 0) throw new Error('the rubble ramp exists before the breach');

  xiangyangSetBreach(true);
  if(xyBreachWall.visible) throw new Error('the intact bay is still visible after the breach');
  if(!xyBreachRubble.visible) throw new Error('no rubble after the breach');
  if(insideCollider(bx, XY_WALL_Z, 0.45, 0)) throw new Error('the breach is still solid');
  // and it must be CLIMBABLE from the outside: ground at the foot, rising to a crest on the wall line
  var foot = getTerrainHeight(bx, XY_WALL_Z+XY_WALL_T/2+2.0, undefined);
  var crest = getTerrainHeight(bx, XY_WALL_Z, undefined);
  if(crest <= foot + 1.5) throw new Error('the rubble does not rise: foot '+foot.toFixed(2)+' crest '+crest.toFixed(2));
  var inside = getTerrainHeight(bx, XY_WALL_Z-XY_WALL_T/2-2.0, undefined);
  if(inside > crest - 1.5) throw new Error('the rubble does not fall away on the city side');

  // re-entry always puts the wall back up, whatever the last visit left
  enterXiangyangWorld('t');
  if(xiangyangBreached) throw new Error('re-entering left the wall breached');
  if(!insideCollider(bx, XY_WALL_Z, 0.45, 0)) throw new Error('re-entering left the gap open');
  if(heightZonesXiangyang.indexOf(xyBreachZone[0]) >= 0) throw new Error('re-entering left the rubble ramp in place');
  // calling it twice is a no-op, not a second splice
  xiangyangSetBreach(true); xiangyangSetBreach(true);
  var n = heightZonesXiangyang.filter(function(z){ return z===xyBreachZone[0]; }).length;
  if(n !== 1) throw new Error('the rubble ramp is in the zone list '+n+' times');
  return 'solid bay blocks; breached it rises '+(crest-foot).toFixed(1)+' to a crest and falls away inside';
"""))

# The gate is its own switch, and the leg OPENS with it open -- the garrison has come out to fight.
ok &= show("the gate is a door on hinges: it swings, and what blocks you is what you can see", run("""
  gameStarted = true;
  enterXiangyangWorld('t');
  if(xyGateShut) throw new Error('the leg starts with the gate shut');
  if(xyGateSwing !== 1) throw new Error('entering did not snap the leaves open, swing is '+xyGateSwing);
  if(!xyGateDoor.visible) throw new Error('the leaves vanish instead of swinging');
  if(insideCollider(0, XY_WALL_Z, 0.45, 0)) throw new Error('the open gate is still solid');
  // thrown open the leaves stand across the road inside, and are solid there
  if(!insideCollider(XY_GATE_HW, XY_WALL_Z-3.0, 0.30, 0))
    throw new Error('the open leaves are not solid where they stand');
  xiangyangSetGate(true);
  if(xyGateSwing !== 1) throw new Error('shutting teleported the leaves rather than swinging them');
  // it takes real time: half a second in it is still moving, and not yet solid across the passage
  for(var i=0;i<30;i++) xiangyangGateTick(0.016);
  if(!(xyGateSwing > 0.4 && xyGateSwing < 0.9)) throw new Error('mid-swing reads '+xyGateSwing);
  for(var j=0;j<140;j++) xiangyangGateTick(0.016);
  if(xyGateSwing !== 0) throw new Error('it never finished shutting; swing '+xyGateSwing);
  if(!insideCollider(0, XY_WALL_Z, 0.45, 0)) throw new Error('the shut gate does not block the passage');
  if(insideCollider(XY_GATE_HW, XY_WALL_Z-3.0, 0.30, 0))
    throw new Error('the leaves are still solid across the road after shutting');
  // the pivots really turned; the leaves are not merely flagged
  if(Math.abs(xyGateLeaves[0].pivot.rotation.y) > 1e-6) throw new Error('the shut leaf is not square in the arch');
  xiangyangSetGate(false);
  for(var k=0;k<140;k++) xiangyangGateTick(0.016);
  if(Math.abs(Math.abs(xyGateLeaves[0].pivot.rotation.y) - XY_GATE_ARC) > 1e-6)
    throw new Error('the open leaf did not reach its stop');
  enterXiangyangWorld('t');
  if(xyGateShut) throw new Error('re-entering left the gate shut');
  return 'open on arrival, swings shut over ~1.6s, solid only where the timber actually is';
"""))

# The user asked for this by name: the door opens when the boss comes. It is derived from the stage,
# so it is open whether you walked into the boss or respawned into it.
ok &= show("the gate swings open for the boss, having been barred behind the sortie", run("""
  gameStarted = true;
  var d = {name:'China', legs:CHINA_LEGS};
  var want = [false, true, true];     // the sortie comes out through it; then it is barred
  var seen = [];
  for(var w=0; w<3; w++){             // tripWave is 0-based; 0..2 are the three waves
    jumpToDestStage(d, 0, w);
    for(var i=0;i<140;i++) xiangyangGateTick(0.016);
    seen.push('w'+(w+1)+(xyGateShut?':shut':':open'));
    if(xyGateShut !== want[w]) throw new Error('wave '+(w+1)+' gate reads '+(xyGateShut?'shut':'open'));
    if(insideCollider(0, XY_WALL_Z, 0.45, 0) !== want[w])
      throw new Error('wave '+(w+1)+' passage does not match the leaves');
  }
  jumpToDestStage(d, 0, 3);           // tripWave === waves.length is the boss stage
  if(!bossActive) throw new Error('stage 4 did not put the boss up');
  if(xyGateShut) throw new Error('the boss came and the gate stayed shut');
  for(var j=0;j<140;j++) xiangyangGateTick(0.016);
  if(xyGateSwing !== 1) throw new Error('the gate never finished opening for the boss');
  if(insideCollider(0, XY_WALL_Z, 0.45, 0)) throw new Error('the passage is still barred at the boss');
  // and the road THROUGH the arch is genuinely open its whole length, not just at the threshold
  var blocked = [];
  for(var z=8.0; z>=-6.0; z-=0.25){
    var hh = getTerrainHeight(0, z, 0);
    if(insideCollider(0, z, 0.42, hh)) blocked.push(z.toFixed(2));
  }
  if(blocked.length) throw new Error('the road in is still blocked at z='+blocked.slice(0,5).join(','));
  // with it shut, that same road is not passable -- so the sweep above is measuring the door
  jumpToDestStage(d, 0, 2); for(var m=0;m<140;m++) xiangyangGateTick(0.016);
  var anyBlocked = false;
  for(var z2=2.0; z2>=-2.0; z2-=0.25) if(insideCollider(0, z2, 0.42, getTerrainHeight(0,z2,0))) anyBlocked = true;
  if(!anyBlocked) throw new Error('the shut gate does not close that road at all');
  return seen.join(' ')+' -> boss: it grinds open and the road through the arch is clear end to end';
"""))

# The trebuchet is a machine, not a prop: it cycles, it looses, and a stone lands somewhere real.
ok &= show("the trebuchet winds, looses, and lands a stone where it was aimed", run("""
  gameStarted = true;
  enterXiangyangWorld('t');
  if(!xyTreb) throw new Error('there is no trebuchet');
  if(xyTreb.state !== 'wind') throw new Error('it does not start winding, it starts '+xyTreb.state);
  var landed = null;
  trebLooseAt(6.0, XY_WALL_Z, function(x,z){ landed = [x,z]; });
  // run it forward far enough to cover hold -> loose -> the stone's whole flight
  var seen = {};
  for(var i=0;i<400;i++){ xiangyangTrebTick(0.016, i*0.016); seen[xyTreb.state]=1; if(landed) break; }
  if(!landed) throw new Error('400 ticks and nothing landed; state is '+xyTreb.state);
  if(Math.abs(landed[0]-6.0) > 1e-6 || Math.abs(landed[1]-XY_WALL_Z) > 1e-6)
    throw new Error('it landed at '+landed+' rather than where it was aimed');
  if(!seen['loose']) throw new Error('it never passed through the loose state');
  if(!xyTreb.dust.visible) throw new Error('no dust where the stone hit');
  // and it recovers back to winding on its own, ready to fire again
  for(var j=0;j<600 && xyTreb.state!=='wind'; j++) xiangyangTrebTick(0.016, j*0.016);
  if(xyTreb.state !== 'wind') throw new Error('it never returned to winding; stuck in '+xyTreb.state);
  if(xyTreb.stone.parent !== xyTreb.sling) throw new Error('it did not reload the stone into its sling');
  return 'wind -> hold -> loose -> flight -> impact at the aim point -> reloaded and winding again';
"""))

# The ladder, and the thing that makes it a siege: each wave is fought at a different HEIGHT.
ok &= show("the three waves are fought in the field, on the wall, and in the breach", run("""
  gameStarted = true;
  var d = {name:'China', legs:CHINA_LEGS};

  // WAVE ONE -- the sortie. Gate open, infantry in the field, crossbowmen up on the wall.
  jumpToDestStage(d, 0, 0);
  if(xyGateShut) throw new Error('wave one has the gate shut, so nothing can have sortied');
  if(xiangyangBreached) throw new Error('wave one already has the wall down');
  var inf = bots.filter(function(b){ return b.skin==='songinfantry'; });
  var xb  = bots.filter(function(b){ return b.skin==='songcrossbowman'; });
  if(inf.length !== 3 || xb.length !== 2) throw new Error('wave one is '+inf.length+' infantry / '+xb.length+' crossbowmen');
  inf.forEach(function(b){
    if(b.groundY > 0.5) throw new Error('an infantryman spawned at height '+b.groundY.toFixed(2)+' -- he belongs in the field');
    if(b.mesh.position.z < XY_WALL_Z) throw new Error('an infantryman sortied to the wrong side of the wall');
  });
  xb.forEach(function(b){
    if(Math.abs(b.groundY - XY_WALL_H) > 1e-6)
      throw new Error('a crossbowman is at height '+b.groundY.toFixed(2)+', not up on the rampart at '+XY_WALL_H);
  });

  // WAVE TWO -- under the wall. The gate is shut and EVERY enemy is up on the walk: this wave cannot
  // be answered in melee at all, which is the whole reason it exists.
  jumpToDestStage(d, 0, 1);
  if(!xyGateShut) throw new Error('wave two left the gate open');
  if(xiangyangBreached) throw new Error('wave two already breached the wall');
  if(!bots.length) throw new Error('wave two spawned nothing');
  bots.forEach(function(b){
    if(Math.abs(b.groundY - XY_WALL_H) > 1e-6)
      throw new Error('wave two has a '+b.skin+' at height '+b.groundY.toFixed(2)+' -- it is meant to be fought entirely on the wall');
  });

  // WAVE THREE -- the breach. The wall is down and the armoured guard is standing in the gap.
  jumpToDestStage(d, 0, 2);
  if(!xiangyangBreached) throw new Error('wave three did not bring the wall down');
  var gd = bots.filter(function(b){ return b.skin==='songguard'; });
  if(gd.length !== 2) throw new Error('wave three has '+gd.length+' guards');
  gd.forEach(function(b){
    if(!b.armoured) throw new Error('the Song Guard is not armoured -- the Zhanmadao has nothing to answer');
    if(b.mesh.position.x < XY_BREACH_X0-2.5 || b.mesh.position.x > XY_BREACH_X1+2.5)
      throw new Error('a guard at x='+b.mesh.position.x.toFixed(1)+' is nowhere near the gap');
  });
  if(!bots.some(function(b){ return b.skin==='songfirelance' && Math.abs(b.groundY-XY_WALL_H)<1e-6; }))
    throw new Error('nobody is shooting into the breach from the wall above it');

  // ...and going back to wave one puts the wall and the gate back where wave one wants them
  jumpToDestStage(d, 0, 0);
  if(xiangyangBreached || xyGateShut) throw new Error('returning to wave one did not re-derive the map');
  return 'field sortie under covering fire; a wall that can only be shot at; then a breach held by armour';
"""))

# Every pool is checked on ITS OWN ground. The shared sweep in bugcheck.py tests west/east at curH 0,
# which is the right question for a field and the wrong one for a rampart -- a wall spawn point sits on
# top of a collider that is only passable to someone already at its height.
ok &= show("all three of Xiangyang's spawn grounds are clear, each at its own height", run("""
  gameStarted = true;
  var d = {name:'China', legs:CHINA_LEGS};
  jumpToDestStage(d, 0, 0);
  var bad = [];
  XIANGYANG_FIELD.forEach(function(p){
    if(insideCollider(p[0],p[1],0.6,0)) bad.push('field '+p);
    if(getTerrainHeight(p[0],p[1],undefined) > 0.2) bad.push('field '+p+' is not at ground level');
  });
  XIANGYANG_WALL.forEach(function(p){
    var h = getTerrainHeight(p[0],p[1],undefined);
    if(Math.abs(h-XY_WALL_H) > 1e-6) bad.push('wall '+p+' reads height '+h.toFixed(2));
    if(insideCollider(p[0],p[1],0.6,h)) bad.push('wall '+p+' is inside geometry even at rampart height');
  });
  // the breach points only have to be clear once there IS a breach
  jumpToDestStage(d, 0, 2);
  XIANGYANG_BREACH.forEach(function(p){
    if(insideCollider(p[0],p[1],0.6,getTerrainHeight(p[0],p[1],undefined))) bad.push('breach '+p);
  });
  if(bad.length) throw new Error(bad.join('; '));
  // no wall point may sit on the bay that comes down, or its man is left standing in mid-air
  var onDoomed = XIANGYANG_WALL.filter(function(p){ return p[0] > XY_BREACH_X0-0.8 && p[0] < XY_BREACH_X1+0.8; });
  if(onDoomed.length) throw new Error('wall spawns on the bay that collapses: '+JSON.stringify(onDoomed));
  var badRig = bots.filter(function(b){ return !b.mesh.userData.bodyMeshes || !b.mesh.userData.marker; });
  if(badRig.length) throw new Error(badRig.length+' actors are missing rig parts');
  return XIANGYANG_FIELD.length+' field, '+XIANGYANG_WALL.length+' wall, '+XIANGYANG_BREACH.length+' breach -- all clear';
"""))

ok &= show("the commander's strike is thrown by the real trebuchet, at the marked ground", run("""
  gameStarted = true; var wasGod = godMode; godMode = true;
  var d = {name:'China', legs:CHINA_LEGS};
  jumpToDestStage(d, 0, XIANGYANG_WAVES.length);
  var boss = bots.filter(function(b){ return b.boss; })[0];
  if(!boss) throw new Error('no boss on the boss stage');
  // stand still, in range, and let him call one down
  camera.position.set(XIANGYANG_BOSS.x + 5, 1.7, XIANGYANG_BOSS.z + 5);
  var fired = false;
  for(var i=0;i<900 && !fired;i++){
    camera.position.set(XIANGYANG_BOSS.x + 5, 1.7, XIANGYANG_BOSS.z + 5);
    animate();
    if(xyTreb.flight || xyTreb.state==='loose') fired = true;
  }
  if(!fired) throw new Error('the commander never signalled the trebuchet in 900 frames');
  // the stone has to be going where the player was marked, not at the wall's default bay
  for(var j=0;j<400 && !xyTreb.flight;j++) animate();
  if(!xyTreb.flight) throw new Error('it loosed but no stone is in flight');
  // within a stride of where the player was standing when he signalled -- the camera settles a little
  // inside the frame before the boss reads it, so this is aimed AT THE PLAYER rather than at a fixed
  // point, which is the property that matters
  var miss = Math.hypot(xyTreb.flight.x1 - camera.position.x, xyTreb.flight.z1 - camera.position.z);
  if(miss > 1.5)
    throw new Error('the stone is aimed at '+xyTreb.flight.x1.toFixed(1)+','+xyTreb.flight.z1.toFixed(1)+
                    ' -- '+miss.toFixed(1)+' from the player, so it is not aimed at them at all');
  // and it must NOT be the idle default, which throws at the wall bay far behind
  if(Math.abs(xyTreb.flight.z1 - XY_WALL_Z) < 0.5)
    throw new Error('it threw at the wall on its idle clock rather than at the marked ground');
  godMode = wasGod;
  return 'signalled, loosed, and the stone is on its way to the marked ground';
"""))

ok &= show("the Siege Commander is fought inside the city, past a wall that is already down", run("""
  gameStarted = true;
  var d = {name:'China', legs:CHINA_LEGS};
  jumpToDestStage(d, 0, XIANGYANG_WAVES.length);
  var boss = bots.filter(function(b){ return b.boss; })[0];
  if(!boss) throw new Error('no boss on the boss stage');
  if(boss.skin !== 'songcommander') throw new Error('Xiangyang ends on a '+boss.skin);
  if(!xiangyangBreached) throw new Error('the boss is fought with the wall still whole');
  // he stands INSIDE: north of the wall line, on open ground, clear of the yamen and the drum tower
  if(XIANGYANG_BOSS.z > XY_WALL_Z - 6)
    throw new Error('the boss at z='+XIANGYANG_BOSS.z+' is not properly inside the city');
  if(insideCollider(XIANGYANG_BOSS.x, XIANGYANG_BOSS.z, boss.radius, 0))
    throw new Error('the commander spawns inside the city geometry');
  if(Math.abs(getTerrainHeight(XIANGYANG_BOSS.x, XIANGYANG_BOSS.z, undefined)) > 0.01)
    throw new Error('the commander spawns on raised ground rather than the square');
  // and the player can actually walk to him from where a death puts them
  var R=0.45, step=0.5, seen={}, sp=usableSpawns()[0], stack=[[sp.x,sp.z]], best=1e9;
  seen[Math.round(sp.x/step)+','+Math.round(sp.z/step)]=1;
  var guard=0;
  while(stack.length && guard++ < 40000){
    var c=stack.pop();
    best=Math.min(best, Math.hypot(c[0]-XIANGYANG_BOSS.x, c[1]-XIANGYANG_BOSS.z));
    [[step,0],[-step,0],[0,step],[0,-step]].forEach(function(dv){
      var nx=c[0]+dv[0], nz=c[1]+dv[1], k=Math.round(nx/step)+','+Math.round(nz/step);
      if(seen[k]) return;
      if(Math.abs(nx)>28 || Math.abs(nz)>28) return;
      var h=getTerrainHeight(nx,nz,undefined);
      if(insideCollider(nx,nz,R,h)) return;
      seen[k]=1; stack.push([nx,nz]);
    });
  }
  if(best > 2.0) throw new Error('the closest reachable point to the commander is '+best.toFixed(2)+' away -- he is walled off');
  return 'fought at z='+XIANGYANG_BOSS.z+' inside a breached wall, reachable to within '+best.toFixed(2);
"""))


ok &= show("Yamen is a real world: enterable, removable, reachable from /tp, all hulls safe on entry", run("""
  gameStarted = true;
  if(typeof yamenWorld === 'undefined') throw new Error('yamenWorld is not defined');
  enterYamenWorld('test');
  if(!yamenWorld.parent) throw new Error('enterYamenWorld did not add the world to the scene');
  if(activeColliders !== yamenColliders) throw new Error('activeColliders was not swapped to Yamen');
  if(insideCollider(camera.position.x, camera.position.z, 0.45, 0))
    throw new Error('the player arrives inside geometry');
  if(yamenFire.some(function(f){return f;})) throw new Error('a hull is already on fire on a fresh entry');
  if(yamenDecks().length !== 3) throw new Error('not all three hulls are walkable on entry');
  if(weapons !== chinaWeapons) throw new Error('the China loadout was not equipped on entry');

  enterSwedenWorld('back');
  if(yamenWorld.parent) throw new Error('clearWorldGroups() does not remove yamenWorld');

  if(!adminTp(['yamen'])) throw new Error('/tp yamen did not work');
  if(!yamenWorld.parent) throw new Error('/tp yamen did not enter the world');
  return 'enter/leave/tp all clean, all three hulls safe, China loadout equipped';
"""))

# The premise of the whole leg, asserted: a CHAINED fleet is one surface. The first cut of this map had
# hulls 16 apart that were only 5.6 wide, so there were ten metres of open water between every pair of
# "chained" ships and no walk from one deck to the next -- and every test still passed, because they all
# only ever looked at one hull at a time.
ok &= show("the chained hulls are one continuous floor, walkable end to end", run("""
  gameStarted = true;
  enterYamenWorld('t');
  var rects = yamenDecks();
  if(rects.length !== YAMEN_HULLS.length) throw new Error('not every hull is walkable on a cold entry');
  // adjacent decks must share an edge exactly -- no gap, and no overlap either
  for(var i=0;i<rects.length-1;i++){
    var gap = rects[i+1].x1 - rects[i].x2;
    if(Math.abs(gap) > 1e-9)
      throw new Error('hull '+i+' and '+(i+1)+' are '+gap.toFixed(2)+' apart rather than flush');
    if(Math.abs(rects[i].z1-rects[i+1].z1) > 1e-9 || Math.abs(rects[i].z2-rects[i+1].z2) > 1e-9)
      throw new Error('hull '+i+' and '+(i+1)+' do not line up along their length');
  }
  // ...and the walkable rectangle has to match the deck that is actually DRAWN: walk the whole span and
  // confirm the clamp never moves you, from the outer hull's outboard rail across to the flagship's
  var x0 = rects[0].x1 + 0.3, x1 = rects[rects.length-1].x2 - 0.3;
  var moved = 0, steps = 0;
  for(var x=x0; x<=x1; x+=0.25){
    for(var z=-YAMEN_HULL_HL+0.4; z<=YAMEN_HULL_HL-0.4; z+=1.0){
      camera.position.set(x,1.7,z); steps++;
      yamenClampPlayer();
      if(Math.hypot(camera.position.x-x, camera.position.z-z) > 1e-8) moved++;
    }
  }
  if(moved) throw new Error(moved+' of '+steps+' points across the fleet are not actually walkable');
  return steps+' points from the outer rail to the flagship, all standable, decks flush at every seam';
"""))

ok &= show("the fire is re-derivable state: it spreads hull by hull and forces you off a burning deck", run("""
  gameStarted = true;
  enterYamenWorld('test');
  camera.position.set(YAMEN_HULLS[0].x, 1.7, 0);
  yamenTick(0.016, 1.0);
  if(Math.abs(camera.position.x - YAMEN_HULLS[0].x) > 1e-6)
    throw new Error('standing on a safe hull moved the player');

  yamenSetFire([true,false,false]);
  if(!yamenFire[0]) throw new Error('the rear hull did not catch');
  if(yamenDecks().length !== 2) throw new Error('the burning hull is still in the walkable list');
  camera.position.set(YAMEN_HULLS[0].x, 1.7, 0);
  yamenTick(0.016, 1.0);
  if(Math.abs(camera.position.x - YAMEN_HULLS[0].x) < 1e-6)
    throw new Error('the burning hull did not push the player off it');
  // The hulls are lashed beam to beam, so their rectangles SHARE an edge: a player clamped off a
  // burning deck lands exactly on that shared line, which is legitimately "on" both. What has to be
  // true is that they are standing on floor that is still in the walkable set, and no longer inside
  // the burning hull.
  if(yamenNearestDeck(camera.position.x, camera.position.z, yamenDecks())[2] > 1e-8)
    throw new Error('the player was pushed somewhere that is not walkable at all');
  var r0 = yamenDeckRect(0);
  if(camera.position.x < r0.x2 - 1e-6)
    throw new Error('the player is still inside the burning hull at x='+camera.position.x.toFixed(2));

  yamenSetFire([true,true,false]);
  if(yamenDecks().length !== 1) throw new Error('two hulls burning should leave exactly one deck');
  if(yamenDecks()[0].x1 !== yamenDeckRect(2).x1) throw new Error('the flagship is not the surviving deck');

  // re-entering the map must put every fire out, regardless of what the last visit left burning
  enterYamenWorld('test');
  if(yamenFire.some(function(f){return f;})) throw new Error('re-entering the map left a hull burning');

  // calling it with the same array twice must be a no-op, not a repeated banner/flip
  yamenSetFire([true,false,false]);
  var flameVisible = yamenFlames[0].group.visible;
  yamenSetFire([true,false,false]);
  if(yamenFlames[0].group.visible !== flameVisible) throw new Error('a repeated call flipped the flame state');
  return 'fire spreads hull by hull, forces retreat off a burning deck, always cold on entry';
"""))

# Yamen's roster is reused, not reinvented -- the same songinfantry/songcrossbowman skins Xiangyang
# fields, both drawn from the flagship pool so nothing ever spawns on a hull about to catch fire.
ok &= show("Yamen's three waves spawn the reused roster, always on the flagship", run("""
  gameStarted = true;
  var d = {name:'China', legs:CHINA_LEGS};
  for(var w=0; w<YAMEN_WAVES.length; w++){
    jumpToDestStage(d, 1, w);
    var want = YAMEN_WAVES[w], wantN = Object.keys(want).reduce(function(s,k){return s+want[k];},0);
    if(bots.length !== wantN) throw new Error('wave '+(w+1)+' spawned '+bots.length+', expected '+wantN);
    Object.keys(want).forEach(function(skin){
      var n = bots.filter(function(b){ return b.skin===skin; }).length;
      if(n !== want[skin]) throw new Error('wave '+(w+1)+': '+n+' of skin '+skin+', expected '+want[skin]);
    });
    // every one of them must be standing on the flagship, at every wave -- never on a burning hull
    var offFlagship = bots.filter(function(b){
      return yamenNearestDeck(b.mesh.position.x, b.mesh.position.z, [yamenDeckRect(2)])[2] > 1e-8;
    });
    if(offFlagship.length) throw new Error('wave '+(w+1)+': '+offFlagship.length+' enemies are not on the flagship');
  }
  // the fire matches the wave: cold at wave one, rear gone by wave two, rear+mid gone by wave three
  jumpToDestStage(d, 1, 0);
  if(yamenFire[0] || yamenFire[1]) throw new Error('wave one already has a hull burning');
  jumpToDestStage(d, 1, 1);
  if(!yamenFire[0] || yamenFire[1]) throw new Error('wave two does not match [rear burning, mid safe]');
  jumpToDestStage(d, 1, 2);
  if(!yamenFire[0] || !yamenFire[1]) throw new Error('wave three does not have both rear and mid burning');
  return YAMEN_WAVES.length+' waves, roster always on the flagship, fire matches every wave';
"""))

ok &= show("the Admiral stands on the flagship with rear and mid already burning", run("""
  gameStarted = true;
  var d = {name:'China', legs:CHINA_LEGS};
  jumpToDestStage(d, 1, YAMEN_WAVES.length);
  var boss = bots.filter(function(b){ return b.boss; })[0];
  if(!boss) throw new Error('no boss on the boss stage');
  if(boss.skin !== 'yamenadmiral') throw new Error('Yamen ends on a '+boss.skin);
  if(!yamenFire[0] || !yamenFire[1] || yamenFire[2]) throw new Error('the boss stage fire state is wrong');
  if(insideCollider(YAMEN_BOSS.x, YAMEN_BOSS.z, boss.radius, 0))
    throw new Error('the admiral spawns inside his own flagship');
  if(yamenNearestDeck(YAMEN_BOSS.x, YAMEN_BOSS.z, [yamenDeckRect(2)])[2] > 1e-8)
    throw new Error('the admiral is not standing on the flagship');
  return 'the admiral stands clear on the flagship, rear and mid already gone';
"""))

# The whole trip, start to finish: Xiangyang's three waves and the Commander hand on to Yamen (not home
# -- Xiangyang now carries a fellOn), and Yamen's three waves and the Admiral send the player home.
ok &= show("the Admiral burns the flagship out from under you, band by band", run("""
  gameStarted = true; var wasGod = godMode; godMode = true;
  var d = {name:'China', legs:CHINA_LEGS};
  jumpToDestStage(d, 1, YAMEN_WAVES.length);
  var boss = bots.filter(function(b){ return b.boss; })[0];
  if(!boss) throw new Error('no boss on the boss stage');
  if(yamenFlagCut !== 0) throw new Error('the flagship is already cut down at full health');
  var full = yamenDecks().filter(function(r){ return r.x2 > YAMEN_HULLS[2].x; })[0];
  var fullLen = full.z2 - full.z1;

  // two thirds of his health: the stern third goes
  boss.hp = boss.maxHp*0.60;
  for(var i=0;i<20;i++) animate();
  if(yamenFlagCut !== 1) throw new Error('at 60% health the stern has not gone (cut='+yamenFlagCut+')');
  var mid = yamenDecks().filter(function(r){ return r.x2 > YAMEN_HULLS[2].x; })[0];
  if(mid.z2 - mid.z1 >= fullLen - 0.01) throw new Error('the deck did not actually shrink');
  if(Math.abs(mid.z1 - (full.z1 + YAMEN_FLAG_BAND)) > 1e-6) throw new Error('the wrong end burned');

  // a third: the bow goes too, and the fight finishes in the waist
  boss.hp = boss.maxHp*0.20;
  for(var j=0;j<20;j++) animate();
  if(yamenFlagCut !== 2) throw new Error('at 20% health the bow has not gone');
  var waist = yamenDecks().filter(function(r){ return r.x2 > YAMEN_HULLS[2].x; })[0];
  if(waist.z2 - waist.z1 >= mid.z2 - mid.z1 - 0.01) throw new Error('the bow band did not come off');

  // the Admiral has to still be standing on what is left -- burning the boss off his own deck would
  // make the fight unwinnable
  if(yamenNearestDeck(YAMEN_BOSS.x, YAMEN_BOSS.z, [waist])[2] > 1e-8)
    throw new Error('the Admiral is standing on deck that has burned away');
  // ...and so does the player, who gets clamped forward as it goes
  camera.position.set(YAMEN_BOSS.x, 1.7, full.z1 + 0.5);
  yamenTick(0.016, 1.0);
  if(yamenNearestDeck(camera.position.x, camera.position.z, yamenDecks())[2] > 1e-8)
    throw new Error('the player was left standing on burned deck');

  // re-entering the map puts the whole deck back
  enterYamenWorld('t');
  if(yamenFlagCut !== 0) throw new Error('re-entering left the flagship cut down');
  godMode = wasGod;
  return 'full deck -> stern gone at 60% -> bow gone at 20%, boss and player both still on floor';
"""))

ok &= show("Yamen fields its own marines, not the wall garrison in a boat", run("""
  gameStarted = true;
  var d = {name:'China', legs:CHINA_LEGS};
  jumpToDestStage(d, 1, 0);
  if(!bots.length) throw new Error('wave one spawned nothing');
  if(bots.some(function(b){ return b.skin==='songinfantry'; }))
    throw new Error('the land infantry from Xiangyang are fighting on the fleet');
  if(!bots.every(function(b){ return b.skin==='songmarine'; }))
    throw new Error('wave one is not all marines');
  jumpToDestStage(d, 1, YAMEN_WAVES.length-1);
  if(!bots.some(function(b){ return b.skin==='songguard' && b.armoured; }))
    throw new Error('the last wave before the Admiral has no armoured elite in it');
  return 'marines on the decks, the armoured guard for the last wave';
"""))

ok &= show("the whole trip plays through: Xiangyang hands on to Yamen, and Yamen sends you home", run("""
  gameStarted = true; var wasGod = godMode; godMode = true;
  var d = {name:'China', legs:CHINA_LEGS};
  jumpToDestStage(d, 0, 0);
  for(var w=0; w<XIANGYANG_WAVES.length+1; w++){
    bots.forEach(function(b){ if(b.alive) damageBot(b, 1e6); });
    for(var i=0;i<600 && !bots.some(function(b){return b.alive;}); i++) animate();
  }
  if(bossActive) throw new Error('Xiangyang\\'s boss bar is still up after he fell');
  for(var i=0;i<900;i++) animate();
  if(inHub) throw new Error('clearing Xiangyang went home instead of on to Yamen');
  var leg = curLeg();
  if(!leg || leg.place !== 'Yamen') throw new Error('Xiangyang handed on to '+(leg ? leg.place : 'nowhere'));
  if(xiangyangWorld.parent) throw new Error('Xiangyang is still in the scene on the next leg');
  if(!yamenWorld.parent) throw new Error('the crossing did not land on Yamen');
  if(tripWave !== 0) throw new Error('Yamen started at wave '+(tripWave+1));

  for(var w2=0; w2<YAMEN_WAVES.length+1; w2++){
    bots.forEach(function(b){ if(b.alive) damageBot(b, 1e6); });
    for(var i=0;i<600 && !bots.some(function(b){return b.alive;}); i++) animate();
  }
  if(bossActive) throw new Error('the Admiral\\'s boss bar is still up after he fell');
  for(var i=0;i<900;i++) animate();
  if(!inHub) throw new Error('clearing the Admiral did not send the player home');
  if(tripDest) throw new Error('the trip did not end on the Admiral');
  godMode = wasGod;
  return 'Xiangyang -> Yamen -> home, the whole way through';
"""))

sys.exit(0 if ok else 1)
