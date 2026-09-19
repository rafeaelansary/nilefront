#!/usr/bin/env python3
"""Draws NILEFRONT's app icon and writes build/icon-1024.png.

Not a placeholder: the palette is lifted directly from the game's own title screen
(index.html's #lock/#title CSS) — the same dark navy backdrop, the same gold/cyan
title-text split — so the icon in the Dock reads as the same thing as the game's own
logo, not a generic Electron-app square with a name on it.

The mark itself is a pyramid over a river, which is the one image that spans the whole
game rather than any single era: PY_TOP/pyramidOverworld's Giza plateau anchors the
campaign's first act, and the water battles (the Nile Wave, the Fjord) are the throughline
after it. A pyramid alone would just be "Egypt"; the river band underneath it is what
makes the mark say NILEFRONT specifically.

Run this, then scripts/build-icns.sh to turn the PNG into build/icon.icns.
"""
import math
from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024
OUT = "build/icon-1024.png"

# ---- palette, taken from index.html's own title screen ----
BG_TOP    = (22, 49, 80)      # #lock's radial gradient, inner stop
BG_MID    = (10, 26, 44)      # ...middle stop
BG_OUTER  = (6, 15, 26)       # ...outer stop
GOLD      = (255, 213, 74)    # #title's own colour (#ffd54a)
GOLD_DK   = (176, 132, 24)    # a shaded gold for the pyramid's far face
CYAN      = (62, 198, 217)    # #title span's colour (#3ec6d9) — the Nile
CYAN_DK   = (32, 138, 158)
NAVY_LINE = (14, 41, 66)      # #0e2942 — the title's drop-shadow colour, used as outline


def radial_bg():
    """The same three-stop radial gradient #lock uses, centred a little above middle
    the way the title screen's is (50% 30%)."""
    img = Image.new("RGB", (SIZE, SIZE))
    px = img.load()
    cx, cy = SIZE * 0.5, SIZE * 0.34
    max_r = math.hypot(max(cx, SIZE - cx), max(cy, SIZE - cy))
    for y in range(SIZE):
        for x in range(SIZE):
            d = math.hypot(x - cx, y - cy) / max_r
            if d < 0.55:
                t = d / 0.55
                c = tuple(int(BG_TOP[i] + (BG_MID[i] - BG_TOP[i]) * t) for i in range(3))
            else:
                t = min(1.0, (d - 0.55) / 0.45)
                c = tuple(int(BG_MID[i] + (BG_OUTER[i] - BG_MID[i]) * t) for i in range(3))
            px[x, y] = c
    return img


def main():
    base = radial_bg()
    draw = ImageDraw.Draw(base, "RGBA")

    # ---- the river: two bands. A polygon that reaches the canvas bottom always paints
    # OVER whatever was under it, so layering three of them (the first attempt at this)
    # just hid two of the three colours entirely — only the last, frontmost polygon was
    # ever visible. Two bands avoids that: the dark one is drawn first as the full water
    # area, and the light crest is a second, narrower band riding along its top edge, so
    # both stay visible instead of one erasing the other. Amplitude is large enough to
    # read at 128px (a Dock-sized render), not just at 1024.
    river_top = SIZE * 0.680
    amp, phase = 34, 1.1

    def wave_y(x):
        return river_top + math.sin(x / SIZE * math.pi * 2.2 + phase) * amp

    dark = [(0, SIZE), (0, wave_y(0))]
    crest = [(0, wave_y(0) - 26)]
    for x in range(0, SIZE + 1, 6):
        y = wave_y(x)
        dark.append((x, y))
        crest.append((x, y - 26))
    dark += [(SIZE, wave_y(SIZE)), (SIZE, SIZE)]
    crest += [(x, wave_y(x)) for x in range(SIZE, -1, -6)]
    draw.polygon(dark, fill=CYAN_DK + (255,))
    draw.polygon(crest, fill=CYAN + (255,))

    # ---- the pyramid: three lit/shaded faces (left face brighter, right face darker,
    # a thin capstone), the same "light from upper-left" rule every model in the game
    # itself follows. Base sits ON the nearest river band, not floating above it. ----
    apex   = (SIZE * 0.5, SIZE * 0.225)
    base_l = (SIZE * 0.175, river_top + 24)
    base_r = (SIZE * 0.825, river_top + 24)
    ridge  = (SIZE * 0.5, river_top + 24)  # where the near and far faces meet at the base

    # soft gold glow behind the apex — echoes the title text's own glow
    # (0 0 34px rgba(70,170,210,0.55)), but warm instead of cool since this is the sun
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gr = SIZE * 0.16
    gd.ellipse([apex[0] - gr, apex[1] - gr * 0.7, apex[0] + gr, apex[1] + gr * 1.3],
               fill=GOLD + (140,))
    glow = glow.filter(ImageFilter.GaussianBlur(SIZE * 0.045))
    base.paste(Image.alpha_composite(base.convert("RGBA"), glow).convert("RGB"), (0, 0))
    draw = ImageDraw.Draw(base, "RGBA")

    # left (lit) face, right (shaded) face — deliberately just two flat triangles with
    # one seam down the ridge, no masonry-course lines. The first attempt had three per
    # face, which read as intended at 1024px but turns to mush at a 32 or 16px Dock/menu
    # render (macOS's own HIG explicitly warns against fine detail for exactly this
    # reason). A silhouette this simple is what stays legible at every size .icns needs.
    draw.polygon([apex, base_l, ridge], fill=GOLD + (255,))
    draw.polygon([apex, ridge, base_r], fill=GOLD_DK + (255,))
    draw.line([apex, base_l], fill=NAVY_LINE + (255,), width=10)
    draw.line([apex, base_r], fill=NAVY_LINE + (255,), width=10)
    draw.line([apex, ridge], fill=NAVY_LINE + (160,), width=6)
    draw.line([base_l, base_r], fill=NAVY_LINE + (200,), width=8)

    # No pre-rounded corners: Apple's own guidance is to hand over a full-bleed square
    # and let the OS apply its squircle mask (and drop shadow) at render time. Rounding
    # it here as well double-masks it — the two curves don't match, so the icon sits
    # inside a second, slightly-wrong-radius rounded shape instead of filling the one
    # every other Dock icon uses.
    base.convert("RGB").save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
