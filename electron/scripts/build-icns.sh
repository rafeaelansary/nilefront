#!/bin/sh
# Turns build/icon-1024.png (see generate-icon.py) into build/icon.icns — the file
# electron-builder picks up automatically for macOS packaging (its default is exactly
# build/icon.icns; no config needed). macOS-only: sips and iconutil are both part of the
# OS, not something to install.
set -e
cd "$(dirname "$0")/.."

SRC=build/icon-1024.png
ICONSET=build/icon.iconset

if [ ! -f "$SRC" ]; then
  echo "Missing $SRC — run 'python3 scripts/generate-icon.py' first." >&2
  exit 1
fi

rm -rf "$ICONSET"
mkdir -p "$ICONSET"

# Apple's required set for a full-quality .icns: every size from 16pt to 512pt, each at
# 1x and 2x (Retina) resolution.
for spec in "16 icon_16x16.png" "32 icon_16x16@2x.png" \
            "32 icon_32x32.png" "64 icon_32x32@2x.png" \
            "128 icon_128x128.png" "256 icon_128x128@2x.png" \
            "256 icon_256x256.png" "512 icon_256x256@2x.png" \
            "512 icon_512x512.png" "1024 icon_512x512@2x.png"; do
  set -- $spec
  sips -z "$1" "$1" "$SRC" --out "$ICONSET/$2" >/dev/null
done

iconutil -c icns "$ICONSET" -o build/icon.icns
rm -rf "$ICONSET"
echo "wrote build/icon.icns"
