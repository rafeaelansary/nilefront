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

sys.exit(0 if ok else 1)
