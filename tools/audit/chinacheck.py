#!/usr/bin/env python3
"""China: the weapons loadout, then Xiangyang and Yamen as they land."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bugcheck import run, show

ok = True

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

# The gate is the one thing this map mutates. Re-derivable STATE, not an event -- forced shut on every
# entry (see enterXiangyangWorld()) and re-opened only by a caller that means it -- so a death or a /tp
# mid-siege can never leave the gate disagreeing with itself.
ok &= show("the gate is shut on every entry, and xiangyangSetBreach() is re-derivable state", run("""
  gameStarted = true;
  enterXiangyangWorld('test');
  if(xiangyangBreached) throw new Error('the gate is open on a fresh entry');
  if(!xyGateDoor.visible) throw new Error('the gate leaves are not visible while shut');
  if(xyGateRubble.visible) throw new Error('the rubble is visible before the gate ever opens');
  if(xiangyangColliders.indexOf(xyGateCollider) < 0) throw new Error('the shut gate has no collider');
  if(!insideCollider(0, XY_WALL_Z, 0.45, 0)) throw new Error('the shut gate does not actually block the gap');

  xiangyangSetBreach(true);
  if(!xiangyangBreached) throw new Error('xiangyangSetBreach(true) did not flip the flag');
  if(xyGateDoor.visible) throw new Error('the gate leaves are still visible after the breach');
  if(!xyGateRubble.visible) throw new Error('the rubble never appeared');
  if(xiangyangColliders.indexOf(xyGateCollider) >= 0) throw new Error('the breached gate still has a collider');
  if(insideCollider(0, XY_WALL_Z, 0.45, 0)) throw new Error('the breach does not actually open the gap');

  // re-entering the map must force it shut again, regardless of what the last visit left it as
  enterXiangyangWorld('test');
  if(xiangyangBreached) throw new Error('re-entering the map left the gate open');
  if(xiangyangColliders.indexOf(xyGateCollider) < 0) throw new Error('re-entering the map left the gap unguarded');

  // calling it twice with the same value must be a no-op, not a double-push onto the collider list
  xiangyangSetBreach(false); xiangyangSetBreach(false);
  var hits = xiangyangColliders.filter(function(c){ return c === xyGateCollider; }).length;
  if(hits !== 1) throw new Error('the gate collider appears '+hits+' times after calling shut twice');
  return 'shut by default, breach opens the gap and shows rubble, re-entry always forces it shut again';
"""))

# The wave ladder, fought entirely on the siege side -- the gate stays SHUT through every regular wave,
# because nothing north of it is reachable until the boss opens the breach. Each wave's roster is
# checked against XIANGYANG_WAVES directly, the same way fjordcheck.py checks FJORD_WAVES.
ok &= show("Xiangyang's three waves spawn the right roster, gate shut throughout", run("""
  gameStarted = true;
  var d = {name:'China', legs:CHINA_LEGS};
  for(var w=0; w<XIANGYANG_WAVES.length; w++){
    jumpToDestStage(d, 0, w);
    if(xiangyangBreached) throw new Error('wave '+(w+1)+' found the gate open');
    var want = XIANGYANG_WAVES[w], wantN = Object.keys(want).reduce(function(s,k){return s+want[k];},0);
    if(bots.length !== wantN) throw new Error('wave '+(w+1)+' spawned '+bots.length+', expected '+wantN);
    Object.keys(want).forEach(function(skin){
      var n = bots.filter(function(b){ return b.skin===skin; }).length;
      if(n !== want[skin]) throw new Error('wave '+(w+1)+': '+n+' of skin '+skin+', expected '+want[skin]);
    });
  }
  // the armoured elite only appears in wave three, and it is armoured
  var guard = bots.filter(function(b){ return b.skin==='songguard'; })[0];
  if(!guard) throw new Error('wave three has no songguard in it');
  if(!guard.armoured) throw new Error('the Song Guard is not armoured -- the Zhanmadao has nothing to answer');
  return XIANGYANG_WAVES.length+' waves, correct roster each time, gate shut throughout';
"""))

# The boss stage: the gate opens, the commander stands in the breach, and he is who the Zhanmadao's
# armourPierce answers next -- the same generic boss:true path the troll and every other boss use, so
# no new mechanic is required for that part.
ok &= show("the Siege Commander opens the breach and stands in it", run("""
  gameStarted = true;
  var d = {name:'China', legs:CHINA_LEGS};
  jumpToDestStage(d, 0, XIANGYANG_WAVES.length);
  var boss = bots.filter(function(b){ return b.boss; })[0];
  if(!boss) throw new Error('no boss on the boss stage');
  if(boss.skin !== 'songcommander') throw new Error('Xiangyang ends on a '+boss.skin);
  if(!xiangyangBreached) throw new Error('the boss stage did not open the breach');
  if(insideCollider(XIANGYANG_BOSS.x, XIANGYANG_BOSS.z, boss.radius, 0))
    throw new Error('the commander spawns inside the town geometry');
  // re-entering an earlier wave must shut the gate again
  jumpToDestStage(d, 0, 0);
  if(xiangyangBreached) throw new Error('returning to wave one left the breach open');
  return 'the commander stands clear in the breach, and leaving re-shuts the gate';
"""))

# The same "clear spawn points, real rig parts" check bugcheck.py runs for every DESTINATIONS entry --
# run by hand here since China is not wired into DESTINATIONS yet.
ok &= show("Xiangyang's own spawn pools are clear, and every actor has real rig parts", run("""
  gameStarted = true;
  var d = {name:'China', legs:CHINA_LEGS};
  jumpToDestStage(d, 0, 0);
  var blocked = XIANGYANG_WEST.concat(XIANGYANG_EAST).filter(function(p){
    return insideCollider(p[0],p[1],0.6,0);
  });
  if(blocked.length) throw new Error('blocked spawn points '+JSON.stringify(blocked));
  if(insideCollider(camera.position.x, camera.position.z, 0.45, 0))
    throw new Error('the arrival point is blocked');
  var bad = bots.filter(function(b){ return !b.mesh.userData.bodyMeshes || !b.mesh.userData.marker; });
  if(bad.length) throw new Error(bad.length+' actors are missing rig parts');
  return XIANGYANG_WEST.length+' west + '+XIANGYANG_EAST.length+' east points, all clear; arrival clear; every actor rigged';
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
  if(yamenNearestDeck(camera.position.x, camera.position.z, [yamenDeckRect(0)])[2] <= 1e-8)
    throw new Error('the player is still standing on the burning hull after the tick');

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
