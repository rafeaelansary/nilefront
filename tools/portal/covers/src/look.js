// shared cover look: golden-hour key light from the camera side, dusk sky, warm haze
window.__LOOK = function(C){
  const tgt = new THREE.Vector3(C.center[0], 0, C.center[1]);
  sun.target.position.copy(tgt); scene.add(sun.target);
  sun.position.set(tgt.x + C.sunOff[0], C.sunOff[1], tgt.z + C.sunOff[2]);
  sun.color.setHex(0xffd2a0); sun.intensity = 1.35;
  sun.shadow.mapSize.set(4096, 4096); if(sun.shadow.map){ sun.shadow.map.dispose(); sun.shadow.map = null; }
  const sc = sun.shadow.camera; sc.left=-40; sc.right=40; sc.top=40; sc.bottom=-40; sc.far=260; sc.updateProjectionMatrix();
  hemi.color.setHex(0xffd9b8); hemi.groundColor.setHex(0x6a4a30); hemi.intensity = 0.62;
  fill.intensity = 0.18;
  // dusk sky: deep violet overhead, through rose, to a hot gold at the horizon
  const c = document.createElement('canvas'); c.width = 8; c.height = 512; const x = c.getContext('2d');
  const g = x.createLinearGradient(0,0,0,512);
  g.addColorStop(0.00,'#2a1f5c'); g.addColorStop(0.35,'#7a3e7a'); g.addColorStop(0.62,'#e0735a');
  g.addColorStop(0.82,'#ffb45a'); g.addColorStop(1.00,'#ffe0a0');
  x.fillStyle = g; x.fillRect(0,0,8,512);
  const tex = new THREE.CanvasTexture(c); sky.visible = false; scene.background = tex;
  scene.fog.color.setRGB(1.0*0.95, 0.78*0.95, 0.55*0.95); scene.fog.near = 60; scene.fog.far = 320;
  if(typeof horizonHaze !== 'undefined') horizonHaze.visible = false;
};
