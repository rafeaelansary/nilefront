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

sys.exit(0 if ok else 1)
