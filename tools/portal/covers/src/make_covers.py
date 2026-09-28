from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
"""Build the three CrazyGames covers (1920x1080, 800x1200, 800x800) from the game's own renders.

usage: python3 tools/portal/covers/src/make_covers.py   (macOS: needs Chrome, Pillow, Georgia Bold)

Renders each scene at 2x with render.py, scales it down, grades it (contrast, warmth, vignette), darkens the
ground under the logo, and sets NILEFRONT in the title screen's own lettering: Georgia Bold, NILE gold and
FRONT teal on a navy outline. CrazyGames allows the game's name and nothing else as text on a cover.
"""
import sys, os, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
S = tempfile.mkdtemp()
for name, w, h in (('landscape', 3840, 2160), ('portrait', 1600, 2400), ('square', 1600, 1600)):
    subprocess.run([sys.executable, os.path.join(HERE, 'render.py'), os.path.join(HERE, name + '.js'), str(w), str(h),
                    os.path.join(S, name + '_raw.png')], check=True)
FONT='/System/Library/Fonts/Supplemental/Georgia Bold.ttf'
GOLD=(255,213,74); TEAL=(62,198,217); NAVY=(14,41,66)

def grade(im):
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Color(im).enhance(1.10)
    W,H = im.size
    # vignette: darken corners
    v = Image.new('L',(W,H),0); d = ImageDraw.Draw(v)
    d.ellipse((-W*0.25,-H*0.2,W*1.25,H*1.25), fill=255)
    v = v.filter(ImageFilter.GaussianBlur(min(W,H)*0.12))
    dark = Image.new('RGB',(W,H),(20,10,25))
    im = Image.composite(im, Image.blend(im, dark, 0.55), v)
    return im

def ground_fade(im, start):
    W,H = im.size
    g = Image.new('L',(1,H),0)
    for y in range(H):
        t = max(0.0, (y/H - start)/(1-start))
        g.putpixel((0,y), int(255*min(1,t*t*0.9)))
    g = g.resize((W,H))
    return Image.composite(Image.new('RGB',(W,H),(18,10,20)), im, g)

def logo(im, width_frac, center_y_frac):
    W,H = im.size
    target = W*width_frac
    size = 200
    f = ImageFont.truetype(FONT, size)
    tw = f.getlength('NILEFRONT') * 1.08   # tracking below
    size = int(size * target / tw); f = ImageFont.truetype(FONT, size)
    track = int(size*0.08)
    parts = [(ch, GOLD if i < 4 else TEAL) for i,ch in enumerate('NILEFRONT')]
    total = sum(f.getlength(c) for c,_ in parts) + track*(len(parts)-1)
    x0 = (W - total)/2
    asc, desc = f.getmetrics()
    y0 = H*center_y_frac - asc/2
    layer = Image.new('RGBA',(W,H),(0,0,0,0))
    # glow
    glow = Image.new('RGBA',(W,H),(0,0,0,0)); gd = ImageDraw.Draw(glow)
    x = x0
    for c,col in parts:
        gd.text((x,y0), c, font=f, fill=(255,190,90,200)); x += f.getlength(c)+track
    glow = glow.filter(ImageFilter.GaussianBlur(size*0.22))
    # drop shadow
    sh = Image.new('RGBA',(W,H),(0,0,0,0)); sd = ImageDraw.Draw(sh)
    x = x0; off = size*0.07
    for c,col in parts:
        sd.text((x,y0+off), c, font=f, fill=NAVY+(255,), stroke_width=int(size*0.06), stroke_fill=NAVY+(255,)); x += f.getlength(c)+track
    sh = sh.filter(ImageFilter.GaussianBlur(size*0.02))
    # letters with a dark outline
    tx = Image.new('RGBA',(W,H),(0,0,0,0)); td = ImageDraw.Draw(tx)
    x = x0
    for c,col in parts:
        td.text((x,y0), c, font=f, fill=col+(255,), stroke_width=int(size*0.045), stroke_fill=NAVY+(255,)); x += f.getlength(c)+track
    # a light top-to-bottom sheen on the letters
    sheen = Image.new('L',(1,H),0)
    for y in range(H):
        t = (y - y0)/max(1,asc)
        sheen.putpixel((0,y), int(max(0,min(255, 70*(1-t)))) if 0<=t<=1 else 0)
    sheen = sheen.resize((W,H))
    hl = Image.new('RGBA',(W,H),(255,255,255,0)); hl.putalpha(ImageChops.multiply(sheen, tx.getchannel('A')))
    out = im.convert('RGBA')
    for L in (glow, sh, tx, hl): out = Image.alpha_composite(out, L)
    return out.convert('RGB')

def make(raw, size, width_frac, logo_y, fade_start, out):
    im = Image.open(raw).convert('RGB').resize(size, Image.LANCZOS)
    im = grade(im)
    im = ground_fade(im, fade_start)
    im = logo(im, width_frac, logo_y)
    im.save(out, optimize=True)
    return out

make(S+'/landscape_raw.png', (1920,1080), 0.58, 0.845, 0.55, OUT+'/cover_1920x1080.png')
make(S+'/portrait_raw.png', (800,1200), 0.90, 0.855, 0.58, OUT+'/cover_800x1200.png')
make(S+'/square_raw.png',   (800,800),  0.84, 0.845, 0.56, OUT+'/cover_800x800.png')
print('ok')
