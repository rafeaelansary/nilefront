// Stages the cover scene. CFG (window.__CFG) drives it so it can be iterated without rewriting.
setTimeout(function(){ const r=[]; try{
  const CFG = window.__CFG;
  startGame(); clearBots(); gunGroup.visible=false; tutStep=-1;
  if(CFG.map) CFG.map();
  const put = (make, x, z, s, face) => { const m = make(); m.scale.setScalar(s); m.position.set(x, 0, z);
    m.rotation.y = Math.atan2(CFG.cam[0]-x, CFG.cam[2]-z) + (face ? Math.PI : 0) + (CFG.turn||0); if(m.userData.marker) m.userData.marker.visible=false; scene.add(m); m.updateMatrixWorld(true); return m; };
  for(const a of CFG.cast) put(eval(a[0]), a[1], a[2], a[3], a[4]);
  camera.position.set(CFG.cam[0], CFG.cam[1], CFG.cam[2]);
  camera.fov = CFG.fov || 50; camera.aspect = CFG.W/CFG.H; camera.updateProjectionMatrix();
  camera.lookAt(CFG.look[0], CFG.look[1], CFG.look[2]); camera.updateMatrixWorld(true);
  if(CFG.tweak) CFG.tweak();
  renderer.setPixelRatio(1); renderer.setSize(CFG.W, CFG.H);
  bakeDirty = true;
  renderer.render(scene, camera);
  document.body.setAttribute('data-img', renderer.domElement.toDataURL('image/png'));
  r.push('ok');
 }catch(e){ r.push('ERR '+e.message+' '+e.stack); } document.body.setAttribute('data-t', r.join(' ## '));
}, 300);
