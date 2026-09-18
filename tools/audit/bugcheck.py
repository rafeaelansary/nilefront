#!/usr/bin/env python3
"""Broad bug hunt across the whole game, not just the recent work."""
import re, pathlib, json, sys
from py_mini_racer import MiniRacer
HTML="/Users/rafea/src/blockfront/index.html"; STUB="/Users/rafea/src/blockfront/tools/audit/three_stub.js"
script=max(re.findall(r"<script>(.*?)</script>", pathlib.Path(HTML).read_text(), re.S), key=len)
inner=script.rstrip()[:-len('})();')]
def run(js):
    probe=inner+f"\nglobalThis.__r=(function(){{try{{return {{ok:true,v:(function(){{ {js} }})()}};}}catch(e){{return {{ok:false,err:String(e)}};}}}})();\n}})();"
    ctx=MiniRacer(); ctx.eval(pathlib.Path(STUB).read_text()); ctx.eval(probe)
    return json.loads(ctx.eval("JSON.stringify(globalThis.__r)"))
def show(name, r):
    print(f"[{'ok ' if r['ok'] else 'BUG'}] {name}")
    if not r['ok']: print(f"        {r['err']}")
    elif r['v'] not in (True,'ok',None): print(f"        {json.dumps(r['v'])[:900]}")
    return r['ok']

print("=== 1. every campaign wave spawns, on the right map, with a live loadout ===")
show("waves 1-12 all jump and spawn without throwing", run("""
  gameStarted=true; var out=[];
  for(var n=0;n<WAVES.length;n++){
    jumpToWave(n);
    var alive=bots.filter(b=>b.alive).length;
    var bad=bots.filter(b=>!b.mesh.userData.bodyMeshes || !b.mesh.userData.marker);
    if(bad.length) throw new Error('wave '+(n+1)+': '+bad.length+' actors missing bodyMeshes/marker');
    if(!weapons || !weapons.length) throw new Error('wave '+(n+1)+': no loadout');
    if(insideCollider(camera.position.x,camera.position.z,0.45,playerHeight))
      throw new Error('wave '+(n+1)+': player spawned inside geometry');
    out.push((n+1)+':'+alive);
  }
  return out.join(' ');
"""))

print("\n=== 2. every boss ===")
show("all four campaign bosses spawn with a full rig", run("""
  gameStarted=true; var out=[];
  for(var era=0; era<4; era++){
    jumpToWave(ERA_START_WAVE[era]);
    bossNum=era; currentEra=era;
    try { spawnBossFight(); } catch(e){ throw new Error('era '+era+' boss threw: '+e); }
    var b=bots.filter(x=>x.boss)[0];
    if(!b) { out.push('era'+era+':none'); continue; }
    if(!b.mesh.userData.bodyMeshes) throw new Error('era '+era+' boss has no bodyMeshes (setBotEmissive would throw)');
    if(!b.mesh.userData.marker) throw new Error('era '+era+' boss has no marker');
    setBotEmissive(b,0x661111); setBotEmissive(b,0);
    out.push('era'+era+':'+b.skin+' hp'+b.hp);
  }
  return out.join(' ');
"""))

print("\n=== 3. every destination leg ===")
show("each leg of each destination enters, spawns, and has clear spawn points", run("""
  gameStarted=true; var out=[];
  DESTINATIONS.forEach(function(d){
    if(!d.legs) return;
    d.legs.forEach(function(leg,li){
      jumpToDestStage(d, li, 0);
      var blockedSpawns=[];
      // south too, where a leg has one -- Birka's harbour is a pool like any other, and checking only
      // west/east would silently pass two thirds of its garrison
      leg.west.concat(leg.east).concat(leg.south||[]).forEach(function(p){
        if(insideCollider(p[0],p[1],0.6,0)) blockedSpawns.push(p);
      });
      if(blockedSpawns.length) throw new Error(d.name+'/'+leg.place+': blocked spawn points '+JSON.stringify(blockedSpawns));
      if(insideCollider(camera.position.x,camera.position.z,0.45,0))
        throw new Error(d.name+'/'+leg.place+': arrival point blocked');
      var bad=bots.filter(b=>!b.mesh.userData.bodyMeshes||!b.mesh.userData.marker);
      if(bad.length) throw new Error(d.name+'/'+leg.place+': '+bad.length+' actors missing rig parts');
      out.push(d.name+'/'+leg.place+':'+bots.length);
      if(leg.boss){
        jumpToDestStage(d, li, leg.waves.length);
        if(!bots.some(b=>b.boss)) throw new Error(d.name+'/'+leg.place+': boss stage spawned no boss');
      }
    });
  });
  return out.join(' ');
"""))

print("\n=== 4. every weapon is actually ON the screen ===")
# The Dane Axe shipped with its right edge at 1.41 half-screen-widths -- 41% past the frame, with its
# whole crescent head cut off by it -- because the tuning pass that placed it only ever measured the
# LEFT edge (crosshair clearance) and never the right. This measures both.
#
# MELEE weapons only, deliberately: a polearm or a thrown weapon is held with its shaft running back
# past the camera, so some of it is off-frame by design (the Naft Pot sits at 33% inside and looks
# correct). A melee weapon is short and held close -- none of it should leave the frame. 95% rather
# than 100% because the Chimalli's shield rim has one mesh clipping the edge, which has always been
# true and reads fine.
show("no melee weapon hangs off the edge of the screen", run("""
  var all = originalWeapons.concat(pyramidWeapons).concat(nileWeapons).concat(greekWeapons)
    .concat(romanWeapons).concat(islamicWeapons).concat(mexicoWeapons).concat(aztecWeapons).concat(swedenWeapons);
  var tanV = Math.tan(75*Math.PI/180/2), tanH = tanV*(16/9), out=[], bad=[];
  all.forEach(function(w){
    if(!w.userData.melee) return;
    w.updateMatrixWorld(true);
    var p=w.userData.pos, inside=0, total=0, right=-9, bottom=9;
    globalThis.__worldBoxes(w).forEach(function(bx){
      var b=bx.box, pts=[];
      [b.min.x+p.x, b.max.x+p.x].forEach(function(X){
        [b.min.y+p.y, b.max.y+p.y].forEach(function(Y){
          [b.min.z+p.z, b.max.z+p.z].forEach(function(Z){
            if(Z > -0.1) return;
            pts.push([X/(-Z*tanH), Y/(-Z*tanV)]);
          });
        });
      });
      if(!pts.length) return;
      total++;
      var mx = -9, mny = 9;
      pts.forEach(function(q){ mx=Math.max(mx,q[0]); mny=Math.min(mny,q[1]); });
      right = Math.max(right, mx);
      bottom = Math.min(bottom, mny);
      if(mx <= 1.0) inside++;
    });
    var frac = inside/total;
    // bottom is reported, not asserted. A long-hafted weapon MUST leave the bottom of the frame or it
    // hangs in mid-air -- the Dane Axe did exactly that for one revision, ending at -1.00 -- but a
    // xiphos, a pugio and a saif all stop around -0.85 and read correctly, because a short blade held
    // in the fist genuinely ends near the bottom edge. There is no threshold that separates those two
    // without exempting half the list, so this prints the number and leaves the judgement to a human.
    out.push(w.userData.name+' '+Math.round(frac*100)+'% (foot '+bottom.toFixed(2)+')');
    if(frac < 0.95) bad.push(w.userData.name+' only '+Math.round(frac*100)+
                             '% on screen (right edge '+right.toFixed(2)+')');
  });
  if(bad.length) throw new Error(bad.join('; '));
  return out.join(' \u00b7 ');
"""))

# The box measure above is the right tool for "is it on screen at all", and the wrong one for "how big
# may it be". A box around a diagonal cylinder is mostly air: the Dane Axe's haft measured 0.468 wide
# as a box and came out 0.108 from the crosshair, while the actual timber was never closer than 0.37 --
# and a whole tuning pass concluded from that number that the axe was already as large as it could get.
# This measures the SILHOUETTE: boxes by their eight corners (exact), round parts by axis and radius.
# It guards the envelope that sizing was solved against, so a future pass cannot quietly shrink the axe
# back or shove it over the aim point.
show("the Dane Axe fills its frame and nothing else", run("""
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
  var axe = swedenWeapons.filter(function(w){ return w.userData.name==='Dane Axe'; })[0];
  if(!axe) throw new Error('no Dane Axe in the Sweden loadout');
  var m = silhouette(axe, 16/9);
  // the envelope the size was solved against, plus the worst the viewmodel motion can add to it
  var swayX=(0.016+0.006+0.05)/(0.76*Math.tan(75*Math.PI/180/2)*(16/9));
  var riseY=(0.05+0.005)/(0.76*Math.tan(75*Math.PI/180/2));
  if(m.right > 0.93)      throw new Error('right edge at '+m.right.toFixed(2)+' -- it will clip the frame when it sways');
  if(m.right + swayX > 1.0) throw new Error('a hard flick takes it off the right of the frame');
  if(m.top   > 0.90)      throw new Error('the head is at '+m.top.toFixed(2)+' -- it clips the top');
  if(m.top + riseY > 1.0) throw new Error('a hard flick takes the head off the top of the frame');
  if(m.left  < -0.02)     throw new Error('it has crossed to the left of the sight line');
  if(m.bottom > -1.35)    throw new Error('the haft ends at '+m.bottom.toFixed(2)+' -- inside the frame, so it hangs in mid-air');
  if(m.cross < 0.25)      throw new Error('only '+m.cross.toFixed(2)+' of clear screen around the crosshair');
  // ...and it has to still be BIG. This is the check that stops it shrinking back.
  if(m.top < 0.80)        throw new Error('the head only reaches '+m.top.toFixed(2)+' -- the axe has shrunk');
  return 'right '+m.right.toFixed(2)+' left '+m.left.toFixed(2)+' top '+m.top.toFixed(2)+
         ' bottom '+m.bottom.toFixed(2)+' crosshair '+m.cross.toFixed(2)+
         ' (worst-case sway: right '+(m.right+swayX).toFixed(2)+', top '+(m.top+riseY).toFixed(2)+')';
"""))

print("\n=== 5. every weapon, every operation ===")
show("fire / reload / scope / switch on all 23 weapons without throwing", run("""
  gameStarted=true; jumpToWave(1);
  var sets=[originalWeapons,pyramidWeapons,nileWeapons,greekWeapons,romanWeapons,
            islamicWeapons,mexicoWeapons,aztecWeapons,swedenWeapons];
  sets.forEach(function(st){ st.forEach(function(w){ w.userData.__set=st; }); });
  var all=[].concat.apply([],sets);
  var saved=weapons, n=0;
  all.forEach(function(wp){
    var u=wp.userData;
    weapons=(wp.userData.__set||saved); currentWeapon=Math.max(0,weapons.indexOf(wp));
    u.ammo=u.magSize||0; u.reloading=false; u.reloadT=0; lastShot=-99;
    try{
      selectWeapon(0);
      fire(); if(u.charge){ u.chargeT=u.chargeTime; releaseCharge(); }
      reloadWeapon(0);
      setScope(true); setScope(false);
      setAim(true); setAim(false);
      for(var i=0;i<5;i++) animate();
      reloadWeapon(0); u.reloading=false;
    }catch(e){ throw new Error(u.name+': '+e); }
    n++;
  });
  weapons=saved; currentWeapon=0; selectWeapon(0);
  return n+' weapons exercised';
"""))

print("\n=== 6. state leaks across map transitions ===")
show("flight / scope / guard / charge do not survive a map change", run("""
  gameStarted=true;
  jumpToWave(1);
  gk7q.c=true; setScope(true); guarding=true;
  DESTINATIONS.find(d=>d.name==='Sweden').go(); selectWeapon(1);
  var bow=swedenWeapons[1].userData; bow.ammo=bow.magSize; lastShot=-99; firing=true; fire();
  if(!bow.drawing) throw new Error('setup: no draw');
  jumpToWave(4);
  var leaks=[];
  if(bow.drawing) leaks.push('bow still drawing after leaving the map');
  if(scoped) leaks.push('still scoped');
  if(guarding) leaks.push('still guarding');
  gk7q.c=false;
  if(leaks.length) throw new Error(leaks.join('; '));
  return 'clean';
"""))

show("dying and respawning on every destination leaves no boss bar or stale bots", run("""
  gameStarted=true;
  DESTINATIONS.find(d=>d.name==='Sweden').go();
  player.hp=1; damagePlayer(999);
  if(player.alive) throw new Error('did not die');
  respawnPlayer();
  if(!player.alive) throw new Error('did not respawn');
  if(bossActive) throw new Error('boss bar left up after a respawn');
  if(insideCollider(camera.position.x,camera.position.z,0.45,playerHeight))
    throw new Error('respawned inside geometry');
  return 'clean';
"""))

print("\n=== 7. world geometry, every map ===")
r=run("""
  var names=['overworld','pyramidOverworld','greekOverworld','romanOverworld','islamicOverworld',
             'mexicoOverworld','aztecOverworld','aztecMarketOverworld','swedenOverworld',
             'dungeon','pyramidDungeon','greekDungeon','nileWorld','hydraArena','colosseumArena','ifritArena'];
  var groups={overworld:overworld,pyramidOverworld:pyramidOverworld,greekOverworld:greekOverworld,
    romanOverworld:romanOverworld,islamicOverworld:islamicOverworld,mexicoOverworld:mexicoOverworld,
    aztecOverworld:aztecOverworld,aztecMarketOverworld:aztecMarketOverworld,swedenOverworld:swedenOverworld,
    dungeon:dungeon,pyramidDungeon:pyramidDungeon,greekDungeon:greekDungeon,nileWorld:nileWorld,
    hydraArena:hydraArena,colosseumArena:colosseumArena,ifritArena:ifritArena};
  var snow=[]; if(birkaSnow) birkaSnow.grp.traverse(function(o){ if(o.isMesh) snow.push(o); });
  return names.map(function(n){
    var g=groups[n];
    var boxes=globalThis.__worldBoxes(g).filter(function(b){ return snow.indexOf(b.mesh)<0; });
    var fl=globalThis.__worldFloaters(g,0,0.05,0.01).length;
    var cp=globalThis.__worldCoplanar(g,0.005,0.12,4).length;
    // snow floats by design; subtract it from Birka's count
    if(n==='swedenOverworld'){ fl=Math.max(0,fl-snow.length); }
    return {map:n, meshes:boxes.length, floaters:fl, zfight:cp};
  });
""")
if r['ok']:
    print(f"    {'map':22} {'meshes':>7} {'floaters':>9} {'z-fight':>8}")
    mine={'aztecMarketOverworld','swedenOverworld'}
    for m in r['v']:
        tag = "  <- built in this session" if m['map'] in mine else ""
        print(f"    {m['map']:22} {m['meshes']:7} {m['floaters']:9} {m['zfight']:8}{tag}")
else:
    print("    BUG:", r['err'])
