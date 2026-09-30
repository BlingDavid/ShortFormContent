"""Props and scene backgrounds. Every prop draws itself onto `frame` through a tight Cv."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import chars
import draw
from draw import Cv, W, H, hexc, lerp, mix, soft_shadow

SKIN, SKIN_D = hexc("#E3A985"), hexc("#B87A58")


def box_around(cx, cy, rx, ry):
    x0, y0, x1, y1 = max(0, int(cx - rx)), max(0, int(cy - ry)), min(W, int(cx + rx)), min(H, int(cy + ry))
    if x1 <= x0 or y1 <= y0:                       # fully off-screen: draw nothing
        return (0, 0, 1, 1)
    return (x0, y0, x1, y1)


def crumb(frame, x, y, s=1.0, shadow=True, **pose):
    if shadow:
        soft_shadow(frame, x, y + 4 * s, 190 * s, 26 * s, .42, 16)
    cv = Cv(box_around(x, y - 230 * s, 400 * s, 330 * s))
    r = chars.crumb(cv, x, y, s, **pose)
    cv.flush(frame)
    return r


def pip(frame, x, y, s=1.0, shadow=True, **pose):
    if shadow:
        soft_shadow(frame, x, y + 4 * s, 180 * s, 24 * s, .42, 16)
    cv = Cv(box_around(x, y - 230 * s, 400 * s, 340 * s))
    r = chars.pip(cv, x, y, s, **pose)
    cv.flush(frame)
    return r


def hand(frame, wx, wy, deg=0.0, pose="open", s=1.0, sleeve=hexc("#3B4A6B"), shadow=True, mirror=False):
    """Hand with wrist at (wx,wy); fingers point along `deg` (0 = up, 90 = right, -90 = left).

    Drawn through a coordinate transform (no rotated canvas), so it never clips at the frame edge.
    """
    cv = Cv(box_around(wx, wy, 560 * s, 560 * s), ss=2)
    d = math.radians(deg)
    cs, sn = math.cos(d), math.sin(d)

    mx = -1 if mirror else 1

    def T(lx, ly):
        lx *= mx
        return (wx + (lx * cs - ly * sn) * s, wy + (lx * sn + ly * cs) * s)

    def cap(a, b, r, col):
        (x0, y0), (x1, y1) = T(*a), T(*b)
        cv.capsule(x0, y0, x1, y1, r * s, col)

    cap((0, 330), (0, 50), 52, sleeve)                                   # sleeve + forearm
    cap((0, 70), (0, -5), 44, SKIN)
    px, py = T(0, -60)
    cv.blob(px, py, 64 * s, 74 * s, SKIN, rot=deg, dark=.22)              # palm
    cap((-46, -30), (-84, -88), 21, SKIN)                                 # thumb
    for i, (dx, ln) in enumerate([(-33, 100), (-10, 112), (13, 104), (36, 86)]):
        by = -108
        if pose == "point":
            ln = 170 if i == 0 else 26
        elif pose == "grip":
            ln = 40
        cap((dx, by), (dx, by - ln), 18, SKIN)
        if pose == "point" and i == 0:
            tx, ty = T(dx, by - ln)
            cv.ellipse(tx, ty, 16 * s, 13 * s, mix(SKIN[:3], (255, 220, 200), .3) + (255,), rot=deg)
    cv.flush(frame)


def glass(frame, cx, cy, s=1.0, tilt=0.0):
    cv = Cv(box_around(cx, cy, 160 * s, 200 * s))
    top, bot, h = 78 * s, 60 * s, 250 * s

    def paint(c):
        pts = [(cx - top, cy - h / 2), (cx + top, cy - h / 2), (cx + bot, cy + h / 2), (cx - bot, cy + h / 2)]
        c.poly(pts, hexc("#DDEBF2", 90))
        c.poly([(cx - top * .93, cy - h * .18), (cx + top * .93, cy - h * .18), (cx + bot * .95, cy + h / 2 - 6),
                (cx - bot * .95, cy + h / 2 - 6)], hexc("#F3B65B", 150))
        c.rrect(cx - top * .8, cy - h * .48, cx - top * .55, cy + h * .4, 8, hexc("#FFFFFF", 150))
        c.ellipse(cx, cy - h / 2, top, 14 * s, hexc("#FFFFFF", 120))
        c.ellipse(cx, cy + h / 2 - 3, bot, 10 * s, hexc("#A9C4D0", 200))

    cv.rotated(paint, cx, cy, tilt)
    cv.flush(frame)


def phone(frame, cx, cy, w=300, h=560, deg=0.0, screen=None, glow=None, s=1.0, shadow=True):
    """Smartphone (blank screen, never any UI). `glow` = (rgb, strength) light cast on surroundings."""
    w, h = w * s, h * s
    if glow:
        lay = Image.new("L", (int(w * 3), int(h * 2)), 0)
        ImageDraw.Draw(lay).ellipse((w * .5, h * .35, w * 2.5, h * 1.65), fill=int(255 * glow[1]))
        lay = lay.filter(ImageFilter.GaussianBlur(70))
        frame.paste(Image.new("RGB", lay.size, glow[0]), (int(cx - w * 1.5), int(cy - h)), lay)
    if shadow:
        soft_shadow(frame, cx + 10, cy + h * .46 + 10, w * .55, 22, .35, 14)
    cv = Cv(box_around(cx, cy, max(w, h) * .75, max(w, h) * .75))

    def paint(c):
        c.rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 44 * s, hexc("#16171D"))
        c.rrect(cx - w / 2 + 5 * s, cy - h / 2 + 5 * s, cx + w / 2 - 5 * s, cy + h / 2 - 5 * s, 40 * s, hexc("#2A2C36"))
        col = screen or hexc("#0B0C10")
        c.rrect(cx - w / 2 + 16 * s, cy - h / 2 + 16 * s, cx + w / 2 - 16 * s, cy + h / 2 - 16 * s, 32 * s, col)
        if screen:
            c.rrect(cx - w / 2 + 16 * s, cy - h / 2 + 16 * s, cx + w / 2 - 16 * s, cy - h * .05, 32 * s, mix(col[:3], (255, 255, 255), .10) + (255,))
        c.ellipse(cx, cy - h / 2 + 34 * s, 9 * s, 9 * s, hexc("#08080B"))

    cv.rotated(paint, cx, cy, deg)
    cv.flush(frame)


def mug(frame, cx, cy, s=1.0, inverted=False, lift=0.0, steam=0.0, t=0.0, color="#F4EFE6"):
    """(cx,cy) = centre of the base contact point. inverted = upside-down over something."""
    soft_shadow(frame, cx, cy + 6, 120 * s, 20 * s, .4, 14)
    cv = Cv(box_around(cx, cy - 100 * s - lift, 260 * s, 260 * s + lift))
    w, h = 108 * s, 170 * s
    base = hexc(color)
    cy2 = cy - lift
    if not inverted:
        cv.line([(cx + w + 6 * s + 36 * s * math.cos(a / 24 * 2 * math.pi), cy2 - h * .5 + 48 * s * math.sin(a / 24 * 2 * math.pi))
                 for a in range(25)], hexc("#D9CFBF"), 15 * s)
    cv.blob(cx, cy2 - h * .5, w, h * .5, base, dark=.2)
    cv.rrect(cx - w, cy2 - h * .92, cx + w, cy2 - 8 * s, 30 * s, base)
    cv.blob(cx, cy2 - h * .52, w * .98, h * .48, base, dark=.14)
    if inverted:
        cv.ellipse(cx, cy2 - 6 * s, w, 20 * s, hexc("#CFC5B4"))
        cv.ellipse(cx + w + 8 * s, cy2 - h * .5, 40 * s, 52 * s, hexc("#D9CFBF"))
        cv.ellipse(cx + w + 8 * s, cy2 - h * .5, 22 * s, 32 * s, hexc("#00000000"))
        cv.blob(cx, cy2 - h * .52, w * .98, h * .48, base, dark=.14)
    else:
        cv.ellipse(cx, cy2 - h * .9, w, 22 * s, hexc("#E7DFD0"))
        cv.ellipse(cx, cy2 - h * .9, w * .86, 16 * s, hexc("#8A4A22"))
    cv.flush(frame)
    if steam > 0 and not inverted:
        for k in range(3):
            pts = [(cx + (k - 1) * 38 * s + 18 * s * math.sin(t * 2 + k + i * .7), cy2 - h - i * 22 * s) for i in range(9)]
            lay = Cv(box_around(cx, cy2 - h - 100 * s, 200 * s, 160 * s))
            lay.line(pts, hexc("#FFFFFF", int(110 * steam)), 10 * s)
            lay.im = lay.im.filter(ImageFilter.GaussianBlur(4 * lay.ss))
            lay.flush(frame)


def slipper(frame, cx, cy, s=1.0, deg=0.0, flip=False):
    """Fuzzy mule slipper, side view. (cx,cy) = centre of the sole underside."""
    soft_shadow(frame, cx, cy + 6 * s, 320 * s, 30 * s, .42, 18)
    cv = Cv(box_around(cx, cy - 110 * s, 480 * s, 260 * s))
    f = -1 if flip else 1
    X = lambda dx: cx + f * dx * s                       # noqa: E731

    def paint(c):
        c.rrect(min(X(-330), X(330)), cy - 44 * s, max(X(-330), X(330)), cy, 30 * s, hexc("#E7DCC6"))          # sole
        c.rrect(min(X(-330), X(330)), cy - 12 * s, max(X(-330), X(330)), cy, 14 * s, hexc("#B8AB92"))
        c.blob(X(60), cy - 118 * s, 285 * s, 118 * s, hexc("#8FB0D6"), dark=.3)                               # toe dome
        c.blob(X(-215), cy - 98 * s, 120 * s, 84 * s, hexc("#86A6CC"), dark=.32)                              # heel cup
        c.ellipse(X(-130), cy - 172 * s, 135 * s, 40 * s, hexc("#2E2C3A"), rot=-f * 10)                       # foot opening
        c.ellipse(X(-130), cy - 164 * s, 118 * s, 28 * s, hexc("#4A4760"), rot=-f * 10)
        for i in range(30):                                                                                    # fuzzy rim
            a = 2 * math.pi * i / 30
            c.ellipse(X(-130 + 138 * math.cos(a)), cy - 172 * s + 44 * s * math.sin(a), 15 * s, 11 * s,
                      hexc("#C4D6EA"), rot=math.degrees(a))
        c.line([(X(150), cy - 200 * s), (X(210), cy - 120 * s), (X(230), cy - 50 * s)], hexc("#6C8DB5", 200), 5 * s)   # toe seam
        c.ellipse(X(250), cy - 96 * s, 46 * s, 34 * s, hexc("#B4CBE6"))

    cv.rotated(paint, cx, cy, deg)
    cv.flush(frame)


def blanket(frame, cx, cy, w=520, h=190, s=1.0, color="#E0A23A", stripe="#C97F22", fold=0.0):
    soft_shadow(frame, cx, cy + h * .45, w * .55, 26, .4, 18)
    cv = Cv(box_around(cx, cy - h * .3, w * .7, h * 1.1))
    base = hexc(color)
    cv.blob(cx, cy - h * .35, w / 2, h * .62, base, dark=.22)
    cv.blob(cx - w * .04, cy - h * .68, w * .46, h * .32, mix(base[:3], (255, 255, 255), .12) + (255,), dark=.1)
    for i in range(4):
        y = cy - h * (.75 - .2 * i)
        cv.line([(cx - w * .42, y), (cx + w * .42, y + 6)], hexc(stripe, 130), 9)
    for i in range(-2, 3):
        cv.line([(cx + i * w * .16, cy - h * .95), (cx + i * w * .16 + 8, cy + h * .1)], hexc(stripe, 70), 7)
    cv.flush(frame)


def tissues(frame, cx, cy, s=1.0):
    soft_shadow(frame, cx, cy + 6, 120 * s, 16 * s, .38, 12)
    cv = Cv(box_around(cx, cy - 80 * s, 200 * s, 160 * s))
    cv.rrect(cx - 105 * s, cy - 130 * s, cx + 105 * s, cy, 18 * s, hexc("#9CC7E6"))
    cv.rrect(cx - 105 * s, cy - 130 * s, cx + 105 * s, cy - 100 * s, 14 * s, hexc("#7DB0D6"))
    cv.ellipse(cx, cy - 132 * s, 62 * s, 14 * s, hexc("#2E5F86"))
    cv.poly([(cx - 40 * s, cy - 134 * s), (cx - 12 * s, cy - 205 * s), (cx + 14 * s, cy - 150 * s), (cx + 38 * s, cy - 190 * s),
             (cx + 50 * s, cy - 134 * s)], hexc("#FFFFFF"))
    cv.flush(frame)


def sneakers(frame, cx, cy, s=1.0, tap=0.0, gap=210, jeans="#3F5F8F"):
    """Two sneakers seen from the front-above with jeans cuffs going up out of frame."""
    for side in (-1, 1):
        x = cx + side * gap / 2 * s
        soft_shadow(frame, x, cy + 8 * s, 110 * s, 18 * s, .4, 12)
        cv = Cv((max(0, int(x - 200 * s)), 0, min(W, int(x + 200 * s)), min(H, int(cy + 60 * s))))
        lift = tap * 26 * s if side > 0 else 0
        cv.rrect(x - 82 * s, cy - 2400 * s, x + 82 * s, cy - 120 * s - lift, 20 * s, hexc(jeans))
        cv.rrect(x - 34 * s, cy - 2400 * s, x + 24 * s, cy - 140 * s - lift, 10 * s, mix(hexc(jeans)[:3], (255, 255, 255), .10) + (255,))
        cv.rrect(x + 52 * s, cy - 2400 * s, x + 82 * s, cy - 120 * s - lift, 10 * s, mix(hexc(jeans)[:3], (0, 0, 0), .25) + (255,))
        for k in range(3):
            cv.line([(x - 70 * s, cy - (250 + 60 * k) * s - lift), (x + 20 * s, cy - (230 + 60 * k) * s - lift)], mix(hexc(jeans)[:3], (0, 0, 0), .2) + (150,), 4 * s)
        cv.rrect(x - 82 * s, cy - 190 * s - lift, x + 82 * s, cy - 130 * s - lift, 12 * s, hexc("#2E4970"))
        cv.blob(x, cy - 70 * s - lift, 96 * s, 78 * s, hexc("#F3F3F1"), dark=.15)
        cv.blob(x, cy - 34 * s - lift, 100 * s, 44 * s, hexc("#FFFFFF"), dark=.1)
        cv.ellipse(x, cy - 6 * s - lift, 104 * s, 14 * s, hexc("#2A2A30"))
        cv.line([(x - 40 * s, cy - 110 * s - lift), (x + 40 * s, cy - 110 * s - lift)], hexc("#C9C9C6"), 6 * s)
        cv.flush(frame)


def cardboard_sign(frame, cx, cy, w=380, h=430, s=1.0, deg=0.0):
    """Blank white cardboard sign on a stick. (cx,cy) = bottom of the stick."""
    cv = Cv(box_around(cx, cy - h * .6, w * .8, h * .8))

    def paint(c):
        c.rrect(cx - 10 * s, cy - h * .6, cx + 10 * s, cy, 6, hexc("#B98A55"))
        c.rrect(cx - w / 2, cy - h - 20, cx + w / 2, cy - h * .3, 14, hexc("#F4F1EA"), outline=hexc("#BFB59F"), width=5)
        c.rrect(cx - w / 2 + 14, cy - h - 6, cx + w / 2 - 14, cy - h * .32, 10, hexc("#FBF9F4"))

    cv.rotated(paint, cx, cy, deg)
    cv.flush(frame)


def clipboard(frame, cx, cy, w=330, h=440, deg=0.0, scribble=0.0, s=1.0):
    cv = Cv(box_around(cx, cy, max(w, h) * .8, max(w, h) * .8))

    def paint(c):
        c.rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 22, hexc("#B98A55"), outline=hexc("#7C5630"), width=5)
        c.rrect(cx - w / 2 + 26, cy - h / 2 + 46, cx + w / 2 - 26, cy + h / 2 - 26, 6, hexc("#FBFAF6"))
        c.rrect(cx - 62, cy - h / 2 - 8, cx + 62, cy - h / 2 + 56, 12, hexc("#8C8F98"), outline=hexc("#5C5F68"), width=4)
        for i in range(5):                                       # faint ruled lines, no words
            c.line([(cx - w / 2 + 48, cy - h / 2 + 130 + i * 52), (cx + w / 2 - 48, cy - h / 2 + 130 + i * 52)], hexc("#D6DDE8"), 4)
        if scribble > 0:
            n = int(28 * scribble)
            pts = [(cx - 100 + (i * 7.3) % 200, cy - 20 + 22 * math.sin(i * 1.9) + (i // 9) * 36) for i in range(n)]
            if len(pts) > 1:
                c.line(pts, hexc("#3A3A48", 230), 5)

    cv.rotated(paint, cx, cy, deg)
    cv.flush(frame)


def pencil(frame, x0, y0, x1, y1):
    cv = Cv(box_around((x0 + x1) / 2, (y0 + y1) / 2, 260, 260))
    cv.capsule(x0, y0, x1, y1, 11, hexc("#F2C230"))
    ang = math.atan2(y1 - y0, x1 - x0)
    cv.capsule(x0 - 30 * math.cos(ang), y0 - 30 * math.sin(ang), x0, y0, 11, hexc("#E88A8A"))
    cv.ellipse(x1 + 8 * math.cos(ang), y1 + 8 * math.sin(ang), 8, 8, hexc("#3A3A48"))
    cv.flush(frame)


def stamp(frame, cx, cy, s=1.0, press=0.0):
    """Rubber stamp; press 0 (raised) .. 1 (down)."""
    cy = cy - (1 - press) * 90 * s
    cv = Cv(box_around(cx, cy, 200 * s, 260 * s))
    cv.rrect(cx - 26 * s, cy - 190 * s, cx + 26 * s, cy - 40 * s, 20 * s, hexc("#9B6A3A"))
    cv.blob(cx, cy - 200 * s, 44 * s, 32 * s, hexc("#B98A55"))
    cv.rrect(cx - 78 * s, cy - 50 * s, cx + 78 * s, cy, 10 * s, hexc("#7B5230"))
    cv.rrect(cx - 70 * s, cy - 6 * s, cx + 70 * s, cy + 14 * s, 6 * s, hexc("#C0392B"))
    cv.flush(frame)


def door(frame, cx, top, w=620, h=1150, open_=0.0):
    cv = Cv(box_around(cx, top + h / 2, w, h * .6))
    cv.rrect(cx - w / 2 - 26, top - 26, cx + w / 2 + 26, top + h, 8, hexc("#E9E1D2"))
    cv.rrect(cx - w / 2, top, cx + w / 2, top + h, 6, hexc("#6C8B78"))
    for (a, b, c_, d) in [(.12, .07, .88, .44), (.12, .5, .88, .93)]:
        cv.rrect(cx - w / 2 + w * a, top + h * b, cx - w / 2 + w * c_, top + h * d, 10, hexc("#5C7967"), outline=hexc("#48604F"), width=4)
        cv.rrect(cx - w / 2 + w * a + 12, top + h * b + 12, cx - w / 2 + w * c_ - 12, top + h * d - 12, 8, hexc("#6C8B78"))
    cv.flush(frame)


def door_handle(frame, x, y, jiggle=0.0):
    cv = Cv(box_around(x, y, 130, 130))
    cv.ellipse(x, y, 40, 40, hexc("#C9A24A"))
    cv.capsule(x, y, x - 90, y + 8 + jiggle * 12, 15, hexc("#D9B45A"))
    cv.ellipse(x - 90, y + 8 + jiggle * 12, 17, 17, hexc("#E5C670"))
    cv.flush(frame)


# ------------------------------------------------------------------------- backgrounds

def _finish(img, light=None, vig=.32, grain_amt=4, seed=1):
    if light:
        draw.radial_light(img, *light)
    draw.vignette(img, vig)
    draw.grain(img, grain_amt, seed)
    return img


def bg_couch(dent=True):
    img = draw.vgrad((120, 58, 34), (168, 82, 46))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 520), fill=(112, 52, 30))                                # couch back
    cv = Cv((0, 300, W, H))
    cv.rrect(-40, 470, W + 40, 1500, 90, hexc("#B5552B"))                          # seat cushion
    cv.rrect(-40, 430, W + 40, 560, 60, hexc("#9B4523"))
    cv.flush(img)
    arr = np.asarray(img, np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    weave = 6 * np.sin(xx * .55) * np.sin(yy * .55)
    arr += weave[..., None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if dent:
        lay = Image.new("L", (W, H), 0)
        ImageDraw.Draw(lay).ellipse((110, 800, 970, 1380), fill=255)
        lay = lay.filter(ImageFilter.GaussianBlur(50))
        img.paste(Image.new("RGB", (W, H), (78, 30, 14)), (0, 0), lay.point(lambda v: int(v * .55)))
        lay2 = Image.new("L", (W, H), 0)
        ImageDraw.Draw(lay2).ellipse((150, 830, 930, 1300), fill=255)
        img.paste(Image.new("RGB", (W, H), (140, 66, 34)), (0, 0), lay2.filter(ImageFilter.GaussianBlur(70)).point(lambda v: int(v * .5)))
    return _finish(img, (180, 300, 1100, (255, 205, 130), .38), .42)


def bg_kitchen():
    img = draw.vgrad((226, 214, 190), (204, 188, 160))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 120):
        for y in range(0, 900, 120):
            d.rectangle((x + 3, y + 3, x + 117, y + 117), fill=(236 - (x // 120 + y // 120) % 2 * 6, 228, 208), outline=(206, 196, 176))
    img = img.filter(ImageFilter.GaussianBlur(9))
    d = ImageDraw.Draw(img)
    cv = Cv((0, 900, W, H))
    cv.rrect(-40, 1010, W + 40, 2000, 20, hexc("#B98A5A"))
    cv.rrect(-40, 990, W + 40, 1040, 10, hexc("#D2A574"))
    cv.flush(img)
    arr = np.asarray(img, np.float32)
    grainw = 5 * np.sin(np.mgrid[0:H, 0:W][1] * .03 + np.sin(np.mgrid[0:H, 0:W][0] * .02) * 4)
    mask = (np.mgrid[0:H, 0:W][0] > 1030)[..., None]
    arr += grainw[..., None] * mask
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return _finish(img, (860, 330, 900, (255, 236, 190), .5), .36)


def bg_bedroom(dark=0.0):
    top, bot = mix((46, 40, 74), (16, 18, 34), dark), mix((84, 66, 92), (24, 24, 44), dark)
    img = draw.vgrad(top, bot)
    d = ImageDraw.Draw(img)
    cv = Cv((0, 1000, W, H))
    cv.rrect(-60, 1120, W + 60, 2100, 120, hexc(mix((122, 132, 176), (36, 44, 78), dark) and "#7A84B0" if dark < .5 else "#2A3060"))
    cv.rrect(-60, 1120, W + 60, 1260, 80, hexc("#9099C4" if dark < .5 else "#343C78"))
    cv.flush(img)
    if dark < .5:
        cv = Cv((0, 700, W, 1150))                                                    # nightstand + lamp
        cv.rrect(560, 930, 1140, 1180, 14, hexc("#7A5334"))
        cv.rrect(560, 915, 1140, 950, 10, hexc("#946842"))
        cv.flush(img)
        img.paste(Image.new("RGB", (W, H), (255, 200, 120)), (0, 0), _pool(200, 700, 520).point(lambda v: int(v * .45)))
        d = ImageDraw.Draw(img)
        cv = Cv((0, 400, 460, 900))
        cv.poly([(140, 560), (300, 560), (340, 720), (100, 720)], hexc("#FFE1A8"))
        cv.rrect(210, 720, 230, 850, 8, hexc("#6B4A2B"))
        cv.ellipse(220, 860, 70, 16, hexc("#6B4A2B"))
        cv.flush(img)
    return _finish(img, None, .5 if dark > .5 else .38)


def _pool(cx, cy, r):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    m = np.clip(1 - np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r, 0, 1) ** 1.5
    return Image.fromarray((m * 255).astype(np.uint8))


def bg_entry():
    img = draw.vgrad((232, 220, 200), (214, 200, 178))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 1560, W, H), fill=(150, 108, 70))
    for i in range(0, W, 110):
        d.line([(i, 1560), (i - 90, H)], fill=(128, 90, 58), width=4)
    d.rectangle((0, 1500, W, 1568), fill=(244, 238, 226))
    arr = np.asarray(img, np.float32)
    arr[1568:] += (5 * np.sin(np.mgrid[0:H - 1568, 0:W][1] * .05))[..., None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return _finish(img, (560, 500, 1100, (255, 240, 205), .3), .34)


def bg_livingroom(blur=0.0):
    img = draw.vgrad((70, 46, 54), (120, 78, 60))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 1180, W, H), fill=(126, 84, 52))
    for i in range(-2, 14):
        d.line([(i * 100, 1180), (i * 100 - 240, H)], fill=(104, 68, 42), width=4)
    cv = Cv((0, 300, W, 1250))                                                        # sofa silhouette + lamp
    cv.rrect(-60, 700, 640, 1220, 60, hexc("#5A3A46"))
    cv.rrect(-60, 640, 640, 800, 50, hexc("#6A4652"))
    cv.flush(img)
    img.paste(Image.new("RGB", (W, H), (255, 190, 110)), (0, 0), _pool(880, 420, 640).point(lambda v: int(v * .5)))
    d = ImageDraw.Draw(img)
    d.ellipse((820, 300, 940, 380), fill=(255, 226, 168))
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    return _finish(img, None, .45)


def lips_face(frame, cx, drop, s=1.0, pucker=0.0):
    """Lower half of a face (chin + lips) hanging from the top edge, softly out of focus. drop = lip y."""
    cv = Cv((0, 0, W, int(drop + 330)))
    cv.blob(cx, drop - 330 * s, 360 * s, 470 * s, SKIN, dark=.22)                 # jaw/chin mass
    cv.blob(cx, drop - 250 * s, 70 * s, 55 * s, mix(SKIN[:3], (255, 215, 190), .25) + (255,), dark=.12)      # nose tip
    cv.ellipse(cx - 26 * s, drop - 232 * s, 12 * s, 8 * s, hexc("#6A3A2C"))
    cv.ellipse(cx + 26 * s, drop - 232 * s, 12 * s, 8 * s, hexc("#6A3A2C"))
    cv.ellipse(cx, drop + 92 * s, 34 * s, 16 * s, mix(SKIN[:3], (150, 90, 80), .25) + (255,))     # chin dimple
    w = 128 * s * (1 - .22 * pucker)
    cv.ellipse(cx, drop + 18 * s, w, 36 * s, hexc("#B8535F"))                     # lower lip
    cv.ellipse(cx - w * .38, drop - 8 * s, w * .62, 30 * s, hexc("#C4636E"), rot=-8)   # upper lip halves
    cv.ellipse(cx + w * .38, drop - 8 * s, w * .62, 30 * s, hexc("#C4636E"), rot=8)
    cv.ellipse(cx, drop + 22 * s, w * .55, 11 * s, hexc("#E08A94", 200))          # gloss
    cv.line([(cx - w * .95, drop + 4 * s), (cx, drop + 8 * s), (cx + w * .95, drop + 4 * s)], hexc("#7A2F3A"), 5 * s)
    cv.im = cv.im.filter(ImageFilter.GaussianBlur(2.2 * cv.ss))
    cv.flush(frame)


def mug_inverted(frame, cx, cy, s=1.0, lift=0.0, look=(0.0, 0.0)):
    """Mug upside-down on the counter; lift opens a gap under the rim with two eyes peeking out."""
    soft_shadow(frame, cx, cy + 4, 140 * s, 18 * s, .45, 14)
    w, h = 105 * s, 165 * s
    top = cy - lift - h
    cv = Cv(box_around(cx, cy - h / 2, 240 * s, 220 * s + lift))
    white = hexc("#F4EFE6")
    cv.rrect(cx - w, top, cx + w, cy - lift, 30 * s, white)
    cv.rrect(cx + w * .45, top + 8, cx + w - 2, cy - lift - 4, 24 * s, hexc("#D9D0C0"))
    cv.rrect(cx - w * .8, top + 14 * s, cx - w * .55, cy - lift - 20 * s, 10 * s, hexc("#FFFFFF", 170))
    cv.ellipse(cx, top + 8 * s, w - 10 * s, 20 * s, hexc("#FFFFFF"))
    hx, hy = cx + w + 20 * s, top + h * .45
    cv.line([(hx + 42 * s * math.cos(a / 24 * 2 * math.pi), hy + 54 * s * math.sin(a / 24 * 2 * math.pi)) for a in range(25)],
            hexc("#E6DECF"), 17 * s)
    if lift > 2:                                            # dark gap under the rim, eyes inside it
        cv.rrect(cx - w + 4 * s, cy - lift, cx + w - 4 * s, cy + 2, 4, hexc("#1A0D08"))
        eh = min(22 * s, lift * .40)
        for sg in (-1, 1):
            ex, ey = cx + sg * 40 * s + look[0] * 6 * s, cy - lift * .5
            cv.ellipse(ex, ey, 15 * s, eh, hexc("#F1DFBC"))
            cv.ellipse(ex + look[0] * 3 * s, ey, 10 * s, eh * .8, hexc("#22140E"))
            cv.ellipse(ex - 3 * s, ey - eh * .3, 4 * s, min(4 * s, eh * .4), hexc("#FFFFFF"))
    else:
        cv.ellipse(cx, cy - 2, w, 12 * s, hexc("#CFC5B4"))
    cv.flush(frame)
