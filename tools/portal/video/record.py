#!/usr/bin/env python3
"""Record the two CrazyGames preview videos from the game itself.

    python3 tools/portal/build_portal.py          # the build this records
    python3 tools/portal/video/record.py          # -> tools/portal/video/preview_1920x1080.mp4
                                                  #    tools/portal/video/preview_1080x1620.mp4

CrazyGames asks for a 15-20 second clip in landscape (1080p, 16:9) and in portrait (1080p, 2:3), silent, with
no cursor, no black bars, no logo cards and no "Play now" text, opening on the cover so the thumbnail flows
into the preview. This plays the real portal build in headless Chrome on the real GPU and films it:

- Time is the recorder's, not the wall clock's. performance.now(), requestAnimationFrame and setTimeout are
  replaced before the page loads, and each frame advances the game exactly 1/30 s and is then captured. The
  capture is slower than real time, but the video is smooth and identical run to run.
- The player is a small aim script: it turns toward the nearest enemy it can see at a human rate, walks
  in, strafes a little, and fires once lined up. God mode and infinite ammo keep a clip from ending on a
  death or a reload; instant kills are on in the wave clips and off for the bosses, so a boss fight looks
  like one.
- Each segment is one place in the game, reached with the game's own /tp command, warmed up off camera so
  the arrival banner has cleared and the enemies have closed in, then filmed. Hard cuts between them.

Needs macOS Chrome, Pillow, websocket-client and an ffmpeg (imageio-ffmpeg's bundled binary is used if
there is none on PATH): pip3 install --user websocket-client imageio-ffmpeg
"""
import base64, http.server, io, itertools, json, os, shutil, signal, socketserver, subprocess, sys, tempfile, threading, time
import urllib.request

import websocket
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
BUILD = os.path.join(ROOT, 'tools', 'portal', 'build')
COVERS = os.path.join(ROOT, 'tools', 'portal', 'covers')
CHROME = os.environ.get('CHROME', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
FPS = 30

# Each segment: how to get there (the game's own /tp), where to stand and which way to face (None keeps the
# map's own spawn), off-camera warm-up frames, filmed frames, instant kills (off for bosses, so the fight
# lasts), the weapon slot, whether the player walks in, and whether to stage the enemies: move the ones
# still alive onto open ground in an arc ahead, so the clip is the fight and not the walk to it.
SEGMENTS = [
    dict(name='giza',         go="chatRun('/tp 2')",              at=(0, 12),   yaw=0,    warm=20, frames=90, insta=False, weapon=0, walk=False, stage=True),
    dict(name='nile',         go="chatRun('/tp nile')",           at=(0, -3.4), yaw=None, warm=60, frames=72, insta=True,  weapon=0, walk=False, stage=False, face='nearest'),
    dict(name='colosseum',    go="chatRun('/tp 6'); bots.forEach(b=>{ if(b.alive) damageBot(b,1e9,b.mesh.position); })",
                                                                  at=None,      yaw=None, warm=150, frames=75, insta=False, weapon=0, walk=False, stage=False, standoff=True),
    dict(name='tenochtitlan', go="chatRun('/tp mexico 2 1')",     at=None,      yaw=None, warm=20, frames=72, insta=True,  weapon=0, walk=False, stage=True),
    dict(name='birka',        go="chatRun('/tp sweden 1 1')",     at=None,      yaw=None, warm=20, frames=72, insta=True,  weapon=0, walk=True,  stage=True),
    dict(name='xiangyang',    go="chatRun('/tp china 1 1')",      at=None,      yaw=None, warm=40, frames=72, insta=True,  weapon=0, walk=True,  stage=False),
    dict(name='fjord',        go="chatRun('/tp sweden 2 boss')",  at=None,      yaw=None, warm=80, frames=72, insta=False, weapon=2, walk=False, stage=False, standoff=True),
]

LOCK_SHIM = r"""(()=>{ let el=null;
Object.defineProperty(Document.prototype,'pointerLockElement',{get(){return el}, configurable:true});
Element.prototype.requestPointerLock=function(){ el=this; setTimeout(()=>document.dispatchEvent(new Event('pointerlockchange')),0); return Promise.resolve(); };
Document.prototype.exitPointerLock=function(){ if(!el) return; el=null; setTimeout(()=>document.dispatchEvent(new Event('pointerlockchange')),0); };
})();"""

TIME_SHIM = r"""(()=>{
  const realNow = performance.now.bind(performance), realRAF = window.requestAnimationFrame.bind(window);
  const realST = window.setTimeout.bind(window), realCT = window.clearTimeout.bind(window);
  let virt = false, vt = 0, q = [], timers = [], tid = 1e7;
  performance.now = () => virt ? vt : realNow();
  window.requestAnimationFrame = cb => { if(virt){ q.push(cb); return 1; } return realRAF(cb); };
  window.setTimeout = (fn, d, ...a) => { if(!virt) return realST(fn, d, ...a); const id = ++tid;
    timers.push({id, at: vt + (+d || 0), fn, a}); return id; };
  window.clearTimeout = id => { const i = timers.findIndex(t => t.id === id); if(i >= 0) timers.splice(i, 1); else realCT(id); };
  window.__virt = () => { vt = realNow(); virt = true; };
  window.__step = ms => {
    vt += ms;
    for(;;){ timers.sort((a,b) => a.at - b.at); if(!timers.length || timers[0].at > vt) break;
      const t = timers.shift(); try { if(typeof t.fn === 'function') t.fn(...t.a); } catch(e){ console.error(String(e && e.stack || e)); } }
    const cbs = q; q = []; cbs.forEach(cb => { try { cb(vt); } catch(e){ console.error(String(e && e.stack || e)); } });
  };
})();"""

# Runs inside the game's closure (through the hook), so it can see bots, camera, fire() and the rest.
# The aim only takes targets it can see within a cone ahead, turns at a human rate, and keeps the view near
# level, so the camera never whips round or stares at the sky; with nothing to shoot it drifts slowly.
AIM = r"""window.__aimStep = function(walk, strafe){
  if(!player.alive) return;
  const angTo = (x, z) => Math.atan2(-(x - camera.position.x), -(z - camera.position.z));
  const wrap = a => ((a + Math.PI) % (2*Math.PI) + 2*Math.PI) % (2*Math.PI) - Math.PI;
  let tgt = null, best = 1e9;
  for(const b of bots){
    if(!b.alive) continue;
    const p = b.mesh.position, s = b.scale || 1;
    const off = Math.abs(wrap(angTo(p.x, p.z) - targetYaw));
    if(off > 1.2) continue;
    // the chest if it can be seen, else the head: a rail or a crate can hide one and not the other
    let chest = null;
    for(const hy of (b.boss ? [1.8, 2.6, 3.4, 1.2] : [1.05, 1.5, 0.7])){
      const c = new THREE.Vector3(p.x, (b.groundY || 0) + hy * s, p.z);
      const dir = c.clone().sub(camera.position), dist = dir.length(); dir.normalize();
      const h = firstHit(camera.position, dir, dist + 1);
      if(h && h.bot === b){ chest = c; break; }
    }
    if(!chest) continue;
    const d = Math.hypot(p.x - camera.position.x, p.z - camera.position.z);
    const score = d + off * 12;
    if(score < best){ best = score; tgt = {chest, d}; }
  }
  const w = weapons[currentWeapon].userData;
  keys['KeyA'] = keys['KeyD'] = false;
  if(!tgt){ keys['KeyW'] = false; firing = false; targetYaw += 0.12 / 30; targetPitch += (0 - targetPitch) * 0.1; return; }
  const dx = tgt.chest.x - camera.position.x, dz = tgt.chest.z - camera.position.z;
  const dy = wrap(Math.atan2(-dx, -dz) - targetYaw);
  const wantPitch = Math.max(-0.22, Math.min(0.4, Math.atan2(tgt.chest.y - camera.position.y, Math.hypot(dx, dz))));
  const turn = 2.4 / 30;
  targetYaw += Math.max(-turn, Math.min(turn, dy));
  targetPitch += Math.max(-turn, Math.min(turn, wantPitch - targetPitch));
  keys['KeyW'] = walk && tgt.d > (w.melee ? 1.8 : 12);
  if(strafe && !keys['KeyW']){ const side = Math.floor(performance.now() / 1400) % 2 === 0; keys['KeyA'] = side; keys['KeyD'] = !side; }
  const aligned = Math.abs(dy) < 0.06 && Math.abs(wantPitch - targetPitch) < 0.1 && (!w.melee || tgt.d < 2.6);
  firing = aligned && !!w.auto;
  if(aligned) fire();
};
// Turn to face the boss, or the nearest enemy, at once (a cut, not a pan: it happens off camera).
window.__face = function(which){
  const live = bots.filter(b => b.alive && (which !== 'boss' || b.boss));
  if(!live.length) return;
  live.sort((p, q) => p.mesh.position.distanceTo(camera.position) - q.mesh.position.distanceTo(camera.position));
  const p = live[0].mesh.position;
  yaw = targetYaw = Math.atan2(-(p.x - camera.position.x), -(p.z - camera.position.z)); pitch = targetPitch = 0;
};
// Stand somewhere with a clear shot at the boss: try points on rings around it, keep the first that is open
// ground inside the play area with an unbroken line of sight, preferring the side the player is already on.
window.__standOff = function(){
  const boss = bots.find(b => b.alive && b.boss); if(!boss) return;
  const bp = boss.mesh.position, s = boss.scale || 1;
  const chest = new THREE.Vector3(bp.x, (boss.groundY || 0) + 1.8 * s, bp.z);
  const home = Math.atan2(camera.position.x - bp.x, camera.position.z - bp.z);
  for(const r of [12, 14, 10, 16]) for(let k = 0; k < 24; k++){
    const a = home + (k % 2 ? 1 : -1) * Math.ceil(k / 2) * (Math.PI / 12);
    const x = bp.x + Math.sin(a) * r, z = bp.z + Math.cos(a) * r;
    if(Math.abs(x) > playClamp - 1 || Math.abs(z) > playClamp - 1 || insideCollider(x, z, 0.6, 0)) continue;
    const eye = new THREE.Vector3(x, getTerrainHeight(x, z, undefined) + 1.7, z);
    const dir = chest.clone().sub(eye), d = dir.length(); dir.normalize();
    const h = firstHit(eye, dir, d + 2);
    if(!(h && h.bot === boss)) continue;
    placePlayerAt(new THREE.Vector3(x, 1.7, z));
    yaw = targetYaw = Math.atan2(-(bp.x - x), -(bp.z - z)); pitch = targetPitch = 0;
    return true;
  }
  return false;
};
// Put the living enemies on open ground in an arc 9-17 units ahead, facing the player.
window.__stage = function(){
  const live = bots.filter(b => b.alive && !b.boss).slice(0, 5);
  live.forEach((b, i) => {
    const a = targetYaw + (i - (live.length - 1) / 2) * 0.28, d = 9 + (i % 3) * 3.5;
    let x = camera.position.x - Math.sin(a) * d, z = camera.position.z - Math.cos(a) * d;
    const R = b.radius !== undefined ? b.radius : 0.55 * (b.scale || 1);
    [x, z] = nearestFreeSpot(x, z, R, 0);
    b.mesh.position.x = x; b.mesh.position.z = z;
  });
};"""


class Page:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=180, suppress_origin=True)
        self.ids = itertools.count(1)
        self.errors = []

    def call(self, method, **params):
        i = next(self.ids)
        self.ws.send(json.dumps({'id': i, 'method': method, 'params': params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get('id') == i:
                if 'error' in m:
                    raise RuntimeError('%s: %s' % (method, m['error']))
                return m.get('result', {})
            if m.get('method') == 'Runtime.exceptionThrown':
                self.errors.append(m['params']['exceptionDetails'].get('exception', {}).get('description', '?'))
            elif m.get('method') == 'Runtime.consoleAPICalled' and m['params']['type'] == 'error':
                self.errors.append(' '.join(str(a.get('value', '')) for a in m['params']['args']))

    def js(self, expr):
        r = self.call('Runtime.evaluate', expression=expr, returnByValue=True)
        if 'exceptionDetails' in r:
            raise RuntimeError('JS: ' + json.dumps(r['exceptionDetails'])[:1500])
        return r['result'].get('value')

    def game(self, code):
        return self.js('window.__g(' + json.dumps(code) + ')')


def serve(directory):
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=directory, **k)
    http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
    srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def ffmpeg():
    exe = shutil.which('ffmpeg')
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def record(W, H, cover, out_mp4):
    site = tempfile.mkdtemp()
    src = open(os.path.join(BUILD, 'index.html'), encoding='utf-8').read()
    anchor = "  startBtn.disabled = false;\n  refreshTitle();\n}"
    assert src.count(anchor) == 1, 'index.html changed: update the hook anchor in record.py'
    open(os.path.join(site, 'index.html'), 'w', encoding='utf-8').write(
        src.replace(anchor, anchor + "\nwindow.__g = function(s){ return eval(s); };\n"))
    shutil.copy(os.path.join(BUILD, 'three.min.js'), site)
    srv = serve(site)
    port = 9400 + (W % 97)
    prof = tempfile.mkdtemp()
    chrome = subprocess.Popen([CHROME, '--headless=new', '--remote-debugging-port=%d' % port, '--user-data-dir=' + prof,
                               '--window-size=%d,%d' % (W, H), '--force-device-scale-factor=1', '--hide-scrollbars',
                               '--mute-audio', '--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist',
                               '--no-first-run', 'about:blank'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    frames = tempfile.mkdtemp()
    try:
        for _ in range(100):
            try:
                tabs = json.load(urllib.request.urlopen('http://127.0.0.1:%d/json' % port))
                break
            except Exception:
                time.sleep(0.1)
        p = Page([t for t in tabs if t['type'] == 'page'][0]['webSocketDebuggerUrl'])
        p.call('Runtime.enable'); p.call('Page.enable')
        p.call('Emulation.setDeviceMetricsOverride', width=W, height=H, deviceScaleFactor=1, mobile=False)
        p.call('Page.addScriptToEvaluateOnNewDocument', source=LOCK_SHIM + TIME_SHIM)
        p.call('Page.navigate', url='http://127.0.0.1:%d/index.html' % srv.server_address[1])
        for _ in range(300):
            try:
                if p.js("!!window.__g && !document.getElementById('startbtn').disabled"):
                    break
            except Exception:
                pass
            time.sleep(0.1)
        x, y = p.js("(()=>{const r=document.getElementById('startbtn').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
        for kind in ('mousePressed', 'mouseReleased'):
            p.call('Input.dispatchMouseEvent', type=kind, x=x, y=y, button='left', clickCount=1)
        time.sleep(1.5)
        p.js('window.__virt()')
        p.game("rsTick = function(){}; renderer.setPixelRatio(1); renderer.setSize(innerWidth, innerHeight); 0")
        p.game(AIM)
        p.js("(()=>{const s=document.createElement('style'); s.textContent='#pausebtn,#tip{display:none!important}'; document.head.appendChild(s);})()")
        step = 'window.__step(%f)' % (1000.0 / FPS)
        n = 0
        for sg in SEGMENTS:
            p.game("%s; closeChat(); godMode = true; gk7q.a = true; gk7q.b = %s; tutStep = -1; tipEl.classList.remove('on'); selectWeapon(%d); 0"
                   % (sg['go'], 'true' if sg['insta'] else 'false', sg['weapon']))
            if sg['at']:
                p.game("placePlayerAt(new THREE.Vector3(%f, 1.7, %f)); 0" % sg['at'])
            if sg['yaw'] is not None:
                p.game("yaw = targetYaw = %f; pitch = targetPitch = 0; 0" % (sg['yaw'] * 3.14159265 / 180))
            if sg['stage']:
                p.game('__stage(); 0')
            walk = 'true' if sg['walk'] else 'false'
            for i in range(sg['warm']):
                if sg.get('face') and i in (0, sg['warm'] - 25):
                    p.game("__face('%s'); 0" % sg['face'])
                if sg.get('standoff') and i == sg['warm'] - 20:
                    print('    stand-off found:', p.game("__standOff()"))
                p.game('__aimStep(%s, false)' % walk); p.js(step)
            p.game("setBanner(''); 0")
            count = 1 if STILLS else sg['frames']
            for i in range(count):
                p.game('__aimStep(%s, %s)' % (walk, 'true' if (i // 45) % 2 == 1 else 'false'))
                p.js(step)
                shot = p.call('Page.captureScreenshot', format='png')
                open(os.path.join(STILLS or frames, ('%s.png' % sg['name']) if STILLS else ('g%05d.png' % n)), 'wb').write(base64.b64decode(shot['data']))
                n += 1
            print('  %-13s %d frames' % (sg['name'], count))
        if p.errors:
            print('  page errors:', p.errors[:5])
    finally:
        try: os.killpg(chrome.pid, signal.SIGKILL)
        except Exception: pass
        srv.shutdown()

    if STILLS:
        return
    # the cover opens the clip (0.5 s), then crossfades into the first gameplay frames (0.3 s)
    seq = tempfile.mkdtemp()
    cov = Image.open(cover).convert('RGB')
    if cov.size != (W, H):
        cov = cov.resize((W, H), Image.LANCZOS)
    k = 0
    def put(im):
        nonlocal k
        im.save(os.path.join(seq, '%05d.png' % k)); k += 1
    for _ in range(15):
        put(cov)
    for i in range(n):
        g = Image.open(os.path.join(frames, 'g%05d.png' % i)).convert('RGB')
        if i < 9:
            g = Image.blend(cov, g, (i + 1) / 10.0)
        put(g)
    subprocess.run([ffmpeg(), '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(seq, '%05d.png'),
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                    '-an', out_mp4], check=True)
    shutil.rmtree(frames, ignore_errors=True); shutil.rmtree(seq, ignore_errors=True); shutil.rmtree(site, ignore_errors=True)
    print('wrote %s (%.1f s, %.1f MB)' % (os.path.relpath(out_mp4, ROOT), k / FPS, os.path.getsize(out_mp4) / 1e6))


STILLS = None   # --stills DIR: one frame per segment, to check the framing before filming it all

if __name__ == '__main__':
    if not os.path.exists(os.path.join(BUILD, 'index.html')):
        sys.exit('Build the portal copy first: python3 tools/portal/build_portal.py')
    args = sys.argv[1:]
    if '--stills' in args:
        i = args.index('--stills'); STILLS = os.path.abspath(args[i + 1]); del args[i:i + 2]
        os.makedirs(STILLS, exist_ok=True)
    which = args or ['landscape', 'portrait']
    if 'landscape' in which:
        record(1920, 1080, os.path.join(COVERS, 'cover_1920x1080.png'), os.path.join(HERE, 'preview_1920x1080.mp4'))
    if 'portrait' in which:
        record(1080, 1620, os.path.join(HERE, 'opening_1080x1620.png'), os.path.join(HERE, 'preview_1080x1620.mp4'))
