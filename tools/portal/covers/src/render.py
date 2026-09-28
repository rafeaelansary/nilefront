#!/usr/bin/env python3
"""Render one cover scene from the game itself, in headless Chrome on the real GPU.

usage: render.py <scene cfg .js> <width> <height> <out.png>

The cfg names the cast (the game's own model builders), the camera and the lighting (look.js). The page is
index.html with the staging script injected after the SDK is ready, so it is the live game's own models,
maps and lights, posed. Render at twice the final size; make_covers.py scales down for clean edges.
"""
import sys, subprocess, re, html, base64, signal, os, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
CHROME = os.environ.get('CHROME', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
cfg, W, H, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
src = open(os.path.join(ROOT, 'index.html')).read()
anchor = "  startBtn.disabled = false;\n  refreshTitle();\n}"
assert src.count(anchor) == 1, 'index.html changed: update the injection anchor in render.py'
inject = ("\nCG.ready.then(()=>{\n" + open(os.path.join(HERE, 'look.js')).read() + "\n" + open(cfg).read()
          + "\nwindow.__CFG.W=%d; window.__CFG.H=%d;\n" % (W, H) + open(os.path.join(HERE, 'scene.js')).read() + "\n});")
page = os.path.join(tempfile.mkdtemp(), 'cover.html')
open(page, 'w').write(src.replace(anchor, anchor + inject))
p = subprocess.Popen([CHROME, '--headless=new', '--use-angle=metal', '--enable-gpu', '--force-device-scale-factor=1',
                      '--window-size=%d,%d' % (max(W, 800), max(H, 600)), '--virtual-time-budget=6000',
                      '--dump-dom', 'file://' + page], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
try: o, _ = p.communicate(timeout=180)
except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL); o, _ = p.communicate(); print('TIMEOUT')
d = o.decode('utf8', 'replace')
t = re.search(r'data-t="([^"]*)"', d); print(html.unescape(t.group(1)) if t else 'NO RESULT')
m = re.search(r'data-img="data:image/png;base64,([^"]*)"', d)
if m: open(out, 'wb').write(base64.b64decode(m.group(1))); print('wrote', out)
else: sys.exit(1)
