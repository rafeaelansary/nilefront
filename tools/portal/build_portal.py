#!/usr/bin/env python3
"""The portal build, for a machine without Node: the same swaps and checks as build-portal.js, byte for byte.

    python3 tools/portal/build_portal.py

Writes tools/portal/build/ (index.html + three.min.js, the two files CrazyGames' uploader takes) and
tools/portal/dist/NILEFRONT-vX.Y.Z-crazygames.zip (for portals that want a zip). build-portal.js stays the
reference and says why each step exists; this mirrors it, so a change to one belongs in the other.
"""
import base64, hashlib, os, re, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SRC_HTML = os.path.join(ROOT, 'index.html')
OUT_DIR = os.path.join(HERE, 'build')
DIST_DIR = os.path.join(HERE, 'dist')
VENDOR_SRC = os.path.join(ROOT, 'electron', 'vendor', 'three.min.js')

CDN_TAG = '''<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
        integrity="sha512-dLxUelApnYxpLt6K2iomGngnHO83iUvZytA3YjDUCjT0HDOHKXnVYdf3hU4JjM8uEhxf9nD1/ey98U3t2vZ0qQ=="
        crossorigin="anonymous" referrerpolicy="no-referrer"></script>'''
SDK_TAG = '<script src="https://sdk.crazygames.com/crazygames-sdk-v3.js"></script>'
LOCAL_TAG = SDK_TAG + '\n<script src="three.min.js"></script>'
CDN_ERROR_MSG = '''\'The game pulls its 3D library from cdnjs.cloudflare.com on first run. Check the connection, '
      + 'or whether something on this network blocks that host, and reload.');'''
LOCAL_ERROR_MSG = '''\'three.min.js failed to load from this bundle. The zip may be corrupt or incomplete -- '
      + 'redownload it and reload.');'''
EXPECTED_SHA512 = re.search(r'integrity="sha512-([^"]+)"', CDN_TAG).group(1)
VER_RE = re.compile(r'<div id="ver">v([0-9]+\.[0-9]+\.[0-9]+)</div>')


def fail(msg):
    sys.exit('\nbuild_portal.py: ' + msg + '\n')


def main():
    if not os.path.exists(VENDOR_SRC):
        fail('Missing electron/vendor/three.min.js -- vendor three.js r128 once (see build-portal.js).')
    html = open(SRC_HTML, encoding='utf-8').read()
    if CDN_TAG not in html:
        fail("index.html's three.js <script> tag has changed; update CDN_TAG here and in build-portal.js.")
    actual = base64.b64encode(hashlib.sha512(open(VENDOR_SRC, 'rb').read()).digest()).decode()
    if actual != EXPECTED_SHA512:
        fail('electron/vendor/three.min.js does not match the integrity hash on index.html\'s own <script> tag.')
    if CDN_ERROR_MSG not in html:
        fail('The three.js failure message in index.html has changed; update CDN_ERROR_MSG/LOCAL_ERROR_MSG.')
    m = VER_RE.search(html)
    ver = m.group(1) if m else '0.0.0'

    patched = html.replace(CDN_TAG, LOCAL_TAG).replace(CDN_ERROR_MSG, LOCAL_ERROR_MSG)
    shutil.rmtree(OUT_DIR, ignore_errors=True)
    os.makedirs(OUT_DIR)
    os.makedirs(DIST_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(patched)
    shutil.copyfile(VENDOR_SRC, os.path.join(OUT_DIR, 'three.min.js'))
    print('Built tools/portal/build/index.html (%d KiB) -- three.js loads from a local file; the CrazyGames SDK tag is added.'
          % (len(patched.encode('utf-8')) // 1024))

    # index.html at the ARCHIVE ROOT, next to three.min.js -- not one folder down.
    zip_path = os.path.join(DIST_DIR, 'NILEFRONT-v%s-crazygames.zip' % ver)
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in ('index.html', 'three.min.js'):
            z.write(os.path.join(OUT_DIR, name), name)
    print('Zipped %s (%d KiB)' % (os.path.relpath(zip_path, ROOT), os.path.getsize(zip_path) // 1024))


if __name__ == '__main__':
    main()
