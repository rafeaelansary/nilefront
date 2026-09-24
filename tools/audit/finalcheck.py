#!/usr/bin/env python3
"""The endgame: the Gate of Ages, the Sum of Ages, and the Nile bank.

Drives the real functions, in order, the way chinacheck.py drives a trip:

    gate locked -> China walked -> the Yamen Admiral falls -> straight into the
    arena -> the boss is already there -> it falls -> the Nile bank -> nothing
    left to sell

    python3 tools/audit/finalcheck.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bugcheck import run, show  # noqa: E402

ok = True

# The unlock rule: China and nothing else. Mexico and Sweden are optional side-roads, so walking both of them
# must NOT open the gate, and walking China alone must.
ok &= show("the gate is gated on China alone", run("""
  gameStarted = true;
  var roads = DESTINATIONS.filter(function(d){ return d.legs; });
  var china = DESTINATIONS.find(function(d){ return d.name === FINAL_ROAD; });
  if(!china) throw new Error('no destination named ' + FINAL_ROAD);
  if(!china.legs) throw new Error(FINAL_ROAD + ' has no legs, so it cannot be the last road');
  roads.forEach(function(d){ d.done = false; });
  enterHub('t');
  if(agesUnlocked()) throw new Error('unlocked with nothing walked');
  if(gateHere())     throw new Error('the gate stands with nothing walked');
  // every OTHER road walked, and it must still be shut -- this is the assertion that pins the rule
  roads.forEach(function(d){ if(d !== china) d.done = true; });
  enterHub('t');
  if(agesUnlocked()) throw new Error('unlocked by the side-roads alone');
  if(gateHere())     throw new Error('the gate stands with ' + FINAL_ROAD + ' unwalked');
  // ...and China alone opens it, with the side-roads back to unwalked
  roads.forEach(function(d){ d.done = false; });
  china.done = true;
  if(!agesUnlocked()) throw new Error(FINAL_ROAD + ' walked and still locked');
  enterHub('t');
  if(!gateHere()) throw new Error(FINAL_ROAD + ' walked and no gate in Cairo');
  if(!agesGate.parent) throw new Error('unlocked but the gate was never attached to a map');
  return 'shut with the other ' + (roads.length-1) + ' walked; open on ' + FINAL_ROAD + ' alone';
"""))

# It has to be reachable from whichever hub the player finished in. Cairo only would strand anyone who
# walked Mexico last, because the Aztec Market's booth does not sell Egypt.
ok &= show("the gate stands in every hub, and leaves with the map", run("""
  gameStarted = true;
  DESTINATIONS.filter(function(d){ return d.legs; }).forEach(function(d){ d.done = true; });
  var seen = [];
  [[enterHub,'cairo'], [enterAztecMarketHub,'aztecMarket'], [enterLadogaMarketHub,'ladoga']].forEach(function(p){
    p[0]('t');
    if(currentHub !== p[1]) throw new Error('expected hub ' + p[1] + ', got ' + currentHub);
    if(!gateHere()) throw new Error('no gate in ' + p[1]);
    if(!agesGate.parent) throw new Error('gate not attached in ' + p[1]);
    // exactly one gate in the game: attaching it here must have detached it from the last hub
    var hosts = [islamicOverworld, aztecMarketOverworld, ladogaOverworld]
      .filter(function(g){ return g.children.indexOf(agesGate) >= 0; });
    if(hosts.length !== 1) throw new Error('the gate is parented to ' + hosts.length + ' maps at once');
    seen.push(p[1]);
  });
  return 'stands in ' + seen.join(', ') + ', one copy throughout';
"""))

# "You arrive and it is there." A leg with waves:[] must go straight to its boss, which is the whole reason
# the empty array is safe: spawnTripStage() reads tripWave >= leg.waves.length, and 0 >= 0.
ok &= show("walking in starts the fight with no wave first", run("""
  gameStarted = true;
  DESTINATIONS.filter(function(d){ return d.legs; }).forEach(function(d){ d.done = true; });
  enterHub('t');
  if(FINAL_LEGS[0].waves.length !== 0) throw new Error('the final leg has waves; it is meant to have none');
  camera.position.set(AGES_GATE_POS.cairo.x, 1.7, AGES_GATE_POS.cairo.z);
  if(!nearGate()) throw new Error('standing on the gate and nearGate() is false');
  enterAgesGate();
  if(inHub) throw new Error('still in the hub after walking into the gate');
  if(!bossActive) throw new Error('arrived and no boss is active');
  var b = bots.filter(function(o){ return o.boss && o.alive; });
  if(b.length !== 1) throw new Error('expected exactly one boss, found ' + b.length);
  // `bots` holds the data objects themselves (each with .mesh/.alive/.boss), not the meshes -- which is what
  // the boss AI blocks read when they touch b.hp and b.mesh.position.
  var bd = b[0];
  if(bd.skin !== 'ages') throw new Error('the boss on this map is ' + bd.skin);
  if(bd.maxHp !== SUM_OF_AGES.hp) throw new Error('boss hp ' + bd.maxHp + ', expected ' + SUM_OF_AGES.hp);
  // and nothing else: the minions are its own to call, not a wave standing there on arrival
  var adds = bots.filter(function(o){ return !o.boss && o.alive; });
  if(adds.length) throw new Error(adds.length + ' non-boss enemies were standing there on arrival');
  return 'one boss, ' + bd.maxHp + ' hp, no adds, no waves';
"""))

# The fight has its own map now. It borrowed ifritArena for a while, which read as a leftover -- so this pins
# that the finale lands on agesArena, that the courtyard goes back to being unreachable, and that the two places
# the map has to keep clear actually are: where the boss stands and where the player walks in.
ok &= show("the fight is in its own arena, and both spawn points are clear", run("""
  gameStarted = true;
  DESTINATIONS.filter(function(d){ return d.legs; }).forEach(function(d){ d.done = true; });
  enterHub('t');
  camera.position.set(AGES_GATE_POS.cairo.x, 1.7, AGES_GATE_POS.cairo.z);
  enterAgesGate();
  if(agesArena.parent !== scene) throw new Error('the final fight is not on agesArena');
  if(ifritArena.parent) throw new Error('the orphaned Citadel courtyard is in the scene');
  if(activeColliders !== agesArenaColliders) throw new Error('the arena is up but its colliders are not active');
  function inside(x,z){
    return activeColliders.some(function(b){ return x > b.x1 && x < b.x2 && z > b.z1 && z < b.z2; });
  }
  if(inside(SUM_OF_AGES.x, SUM_OF_AGES.z))
    throw new Error('the boss spawns at (' + SUM_OF_AGES.x + ',' + SUM_OF_AGES.z + '), inside a collider');
  if(inside(camera.position.x, camera.position.z))
    throw new Error('the player walks in at (' + camera.position.x.toFixed(1) + ',' +
                    camera.position.z.toFixed(1) + '), inside a collider');
  // The ground the fight actually happens on has to be open. Not "no colliders inside the minions' clamp" --
  // every wave-bearing map in the game has cover inside its spawn area and resolveCollision is what deals with
  // a body that lands in it. What matters here is that the boss and the player are not fighting in a doorway.
  var CLEAR = 5;
  var near = activeColliders.filter(function(b){
    var dx = Math.max(b.x1 - SUM_OF_AGES.x, 0, SUM_OF_AGES.x - b.x2);
    var dz = Math.max(b.z1 - SUM_OF_AGES.z, 0, SUM_OF_AGES.z - b.z2);
    return Math.hypot(dx, dz) < CLEAR;
  });
  if(near.length)
    throw new Error(near.length + ' collider(s) stand within ' + CLEAR + ' of where the boss spawns');
  return 'agesArena up, ' + activeColliders.length + ' colliders, both spawns clear, ' +
         CLEAR + ' units open around the fight';
"""))

# Four ages, and every minion name in them has to resolve to a real model. A typo here would not throw --
# makeVoxelBot falls through to the default grunt -- so the Old Kingdom would quietly send soldiers.
ok &= show("all four ages carry a hazard and minions that resolve", run("""
  if(AGES_PHASES.length !== 4) throw new Error(AGES_PHASES.length + ' ages, expected 4');
  var dflt = 0;
  (function(){ var g = makeVoxelBot(0x808080,'knife',null); g.traverse(function(o){ if(o.isMesh) dflt++; }); })();
  var lines = [];
  AGES_PHASES.forEach(function(A, i){
    ['wake','cry','call'].forEach(function(k){
      if(!A[k]) throw new Error('age ' + i + ' has no ' + k + ' line');
    });
    if(!A.hazard || !A.hazard.damage) throw new Error('age ' + i + ' has no hazard damage');
    if(!(A.every > 0) || !(A.callEvery > 0)) throw new Error('age ' + i + ' has a non-positive cooldown');
    if(!A.minions || !A.minions.length) throw new Error('age ' + i + ' calls nobody');
    A.minions.forEach(function(mn){
      if(mn.wt !== 'knife' && mn.wt !== 'pistol' && mn.wt !== 'javelin')
        throw new Error(mn.skin + ' carries an unknown weapon ' + mn.wt);
      var n = 0, g = makeVoxelBot(0x808080, mn.wt, mn.skin);
      g.traverse(function(o){ if(o.isMesh) n++; });
      // resolves either through a SKINS config or through makeVoxelBot's own dispatch to a builder
      if(!SKINS[mn.skin] && n === dflt)
        throw new Error('minion skin "' + mn.skin + '" resolves to the default grunt');
    });
    lines.push(A.minions.map(function(m){ return m.skin; }).join('+'));
  });
  // the hazard must get harder as the ages fall, or the ladder is decoration
  for(var i=1;i<4;i++){
    if(!(AGES_PHASES[i].every <= AGES_PHASES[i-1].every))
      throw new Error('age ' + i + ' fires no faster than age ' + (i-1));
  }
  return lines.join('  ->  ');
"""))

# The express route. Clearing the road that completes the set must go straight into the arena rather than home
# to a hub -- and clearing a road while others are still unwalked must still go home, or the finale fires early.
ok &= show("killing the Yamen Admiral goes straight to the final boss", run("""
  gameStarted = true;
  var roads = DESTINATIONS.filter(function(d){ return d.legs; });
  var china = DESTINATIONS.find(function(d){ return d.name === FINAL_ROAD; });
  roads.forEach(function(d){ d.done = false; });
  campaignComplete = false;
  // standing on China's last leg, the Admiral just down -- which is what advanceTripLeg() is called for
  tripDest = {name:china.name, legs:china.legs};
  tripLeg = china.legs.length - 1; tripCleared = false;
  advanceTripLeg();
  if(pending !== 'agesgate')
    throw new Error('the Admiral fell and it armed "' + pending + '", expected agesgate');
  travelTo(FINAL_TRIP);
  if(!bossActive) throw new Error('the express route did not start the fight');
  if(bots.filter(function(o){ return o.boss && o.alive; })[0].skin !== 'ages')
    throw new Error('the express route led to the wrong boss');
  // A SIDE-ROAD MUST NOT DO THIS. Finishing Mexico with China unwalked goes home to a hub as it always did.
  roads.forEach(function(d){ d.done = false; });
  var side = roads.filter(function(d){ return d !== china; })[0];
  campaignComplete = false;
  tripDest = {name:side.name, legs:side.legs, homeHub:side.homeHub, homeBanner:side.homeBanner};
  tripLeg = side.legs.length - 1; tripCleared = false;
  advanceTripLeg();
  if(pending !== 'triphome')
    throw new Error('finishing ' + side.name + ' armed "' + pending + '" instead of going home');
  // ...and neither must a side-road finished after the game is already beaten
  china.done = true; campaignComplete = true;
  tripDest = {name:side.name, legs:side.legs, homeHub:side.homeHub, homeBanner:side.homeBanner};
  tripLeg = side.legs.length - 1; tripCleared = false;
  advanceTripLeg();
  if(pending !== 'triphome')
    throw new Error('a side-road after the ending armed "' + pending + '" and hauled the player back in');
  campaignComplete = false;
  return 'Admiral -> agesgate -> the fight; ' + side.name + ' -> triphome, before and after the ending';
"""))

# The ending itself. Driven through the same two functions the trip machinery uses, rather than simulated
# combat: advanceTripLeg() is what a boss's death calls, and returnToHub() is what `pending` fires.
ok &= show("the boss falling lands the player on the Nile bank, for good", run("""
  gameStarted = true;
  DESTINATIONS.filter(function(d){ return d.legs; }).forEach(function(d){ d.done = true; });
  enterHub('t');
  camera.position.set(AGES_GATE_POS.cairo.x, 1.7, AGES_GATE_POS.cairo.z);
  enterAgesGate();
  campaignComplete = false;
  advanceTripLeg();
  if(pending !== 'triphome') throw new Error('after the last leg, pending is ' + pending);
  returnToHub();
  if(currentHub !== 'nilebank') throw new Error('came home to ' + currentHub);
  if(!campaignComplete) throw new Error('on the bank and the campaign is not marked complete');
  if(gameWon) throw new Error('gameWon was set -- that disables firing and makes a click restart the run');
  if(!inHub) throw new Error('the bank is meant to be hub-shaped and inHub is false');
  if(nileBankWorld.parent !== scene) throw new Error('the bank map is not in the scene');
  if(bots.filter(function(o){ return o.alive; }).length) throw new Error('something followed the player home');
  // nothing to sell, and no gate to walk back into
  if(hubHasBooth()) throw new Error('the bank claims to have a booth');
  camera.position.set(BOOTH_POS.x, 1.7, BOOTH_POS.z);
  if(nearBooth()) throw new Error('a booth is reachable on the bank');
  if(gateHere()) throw new Error('the gate still stands after the campaign is finished');
  // the stele reads, and names every boss the game has
  camera.position.set(STELE_POS.x, 1.7, STELE_POS.z + 2);
  if(!nearStele()) throw new Error('standing at the stele and nearStele() is false');
  var roll = agesRoll();
  if(roll.indexOf(SUM_OF_AGES.name) < 0) throw new Error('the roll does not name the final boss');
  var missing = [];
  DESTINATIONS.forEach(function(d){
    if(!d.legs) return;
    d.legs.forEach(function(L){ if(L.boss && roll.indexOf(L.boss.name) < 0) missing.push(L.boss.name); });
  });
  if(missing.length) throw new Error('the roll leaves out ' + missing.join(', '));
  return 'bank reached, ' + (roll.split('·').length) + ' names on the stele, no booth, no gate';
"""))

# THE NILE IS BLUE. Aldeigjuborg learned this once already and the note is in its enter function: a warm
# hemisphere repaints every cool colour under it, and this map's first pass (0xffd0a0 hemi over a 0xffc98a
# ambient) turned the river olive-green. The sunset belongs to the sky, the fog and the tint; the light that
# lands on the water stays near-neutral. Asserted rather than eyeballed, because it has now regressed twice.
ok &= show("the river is blue, and nothing warm is lighting it", run("""
  gameStarted = true;
  enterNileBankHub('t');
  var w = nileBankWorld.userData.water;
  if(!w) throw new Error('the bank has no water registered on it');
  // The stub wraps `color` in a Color object but leaves other colour fields as the raw hex they were passed,
  // so take either shape rather than assuming one.
  function hexOf(v){ return (v && typeof v.getHex === 'function') ? v.getHex() : v; }
  function ch(v){ var hex = hexOf(v); return {r:(hex>>16)&255, g:(hex>>8)&255, b:hex&255}; }
  var c = ch(w.material.color);
  if(!(c.b > c.g + 30) || !(c.b > c.r + 60))
    throw new Error('the water is rgb(' + c.r + ',' + c.g + ',' + c.b + '), which is not blue-dominant');
  var e = ch(w.material.emissive);
  if(!(e.b > e.g))  throw new Error('the water emissive is warmer than it is blue');
  // the lights that fall on it
  var h = ch(hemi.color);
  if(h.b < h.r) throw new Error('the hemisphere is warm-dominant (' + h.r + ',' + h.g + ',' + h.b + ') -- this is what turned the river green');
  var f = ch(fill.color);
  if(f.b < f.r) throw new Error('the fill light is warm-dominant, which will turn the river green');
  var amb = null;
  nileBankWorld.traverse(function(o){ if(o.isAmbientLight || (o.type === 'AmbientLight')) amb = o; });
  if(amb){
    var a = ch(amb.color);
    if(a.b < a.r) throw new Error('the map ambient is warm-dominant (' + a.r + ',' + a.g + ',' + a.b + ')');
  }
  return 'water rgb(' + c.r + ',' + c.g + ',' + c.b + '), hemi/fill/ambient all cool-side';
"""))

# The flicker. distantGround is a 700-unit plane pinned at y=-0.04 and the ripple sweep bobs every water
# surface +/-0.03, so this river's surface crosses that plane twice a cycle no matter where it rests -- the
# green/blue alternation that was reported. Two things keep it invisible, and both are asserted here because
# the geometry audit cannot see either: distantGround lives on the scene, not in the map group.
ok &= show("the river cannot flicker against the far plane or the shore", run("""
  gameStarted = true;
  enterNileBankHub('t');
  var w = nileBankWorld.userData.water;
  function hexOf(v){ return (v && typeof v.getHex === 'function') ? v.getHex() : v; }
  // 1. the plane it crosses is the same colour, so whichever wins the depth test looks identical
  if(hexOf(distantGround.material.color) !== hexOf(w.material.color))
    throw new Error('the far plane is #' + hexOf(distantGround.material.color).toString(16) +
                    ' but the river is #' + hexOf(w.material.color).toString(16) + ' -- it will flicker');
  // 2. the whole bob stays under the bank's top face, so it can never fight the sand at the shore
  var RIPPLE = 0.03, halfH = 0.6;   // the sweep's amplitude, and half the water box's height
  var base = w.userData.baseY;
  if(base === undefined) throw new Error('the river has no baseY, so the ripple sweep will bob it from 0.22');
  var top = base + halfH;
  if(!(top + RIPPLE < 0))
    throw new Error('the river tops out at ' + (top+RIPPLE).toFixed(3) + ', at or above the bank at 0');
  return 'far plane matches the river; surface rides ' + (top-RIPPLE).toFixed(3) +
         ' to ' + (top+RIPPLE).toFixed(3) + ', all of it under the bank';
"""))

# Two presses, not one. The first reads; only the second starts over. A single-keypress restart on the
# reward screen would be the same trap gameWon is.
ok &= show("the stele needs a second press to start a new run", run("""
  gameStarted = true;
  DESTINATIONS.filter(function(d){ return d.legs; }).forEach(function(d){ d.done = true; });
  enterNileBankHub('t');
  camera.position.set(STELE_POS.x, 1.7, STELE_POS.z + 2);
  steleRead = false;
  readStele();
  if(!steleRead) throw new Error('the first press did not read the stele');
  if(!campaignComplete) throw new Error('the first press restarted the run');
  if(currentHub !== 'nilebank') throw new Error('the first press moved the player to ' + currentHub);
  // walking away forgets it, so the second press is never a leftover from an earlier visit
  camera.position.set(STELE_POS.x, 1.7, STELE_POS.z + 12);
  updateInteract();
  if(steleRead) throw new Error('walking away did not clear the read state');
  camera.position.set(STELE_POS.x, 1.7, STELE_POS.z + 2);
  readStele(); readStele();
  if(campaignComplete) throw new Error('two presses did not begin a new run');
  if(!gameStarted) throw new Error('the new run did not start');
  return 'first press reads, walking away forgets, second press starts over';
"""))

print()
print("ALL OK" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
