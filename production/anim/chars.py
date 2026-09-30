"""Character rigs: Crumb (cream dragon) and Pip (duck in raincoat). Pure functions of a pose dict."""
from __future__ import annotations

import math

from draw import Cv, hexc, lerp

CREAM, CREAM_LIGHT = hexc("#F1DFBC"), hexc("#FBF0D8")
HORN, WING = hexc("#C4611C"), hexc("#7E9C4B")
EYE = hexc("#22140E")


def _eye(cv, x, y, rx, ry, look, blink, lid, happy, glint=True, color=EYE, lidcol=CREAM):
    if happy > 0.5:                                      # closed happy arc  ^ ^
        cv.line([(x - rx * .8 + i * rx * .16, y + (-math.sin(math.pi * i / 10) * ry * .55)) for i in range(11)],
                EYE, max(5, rx * .28))
        return
    open_ = max(0.06, 1 - blink)
    cv.ellipse(x, y, rx, ry * open_, color)
    px, py = x + look[0] * rx * .35, y + look[1] * ry * .3
    if glint and open_ > .3:
        cv.ellipse(px - rx * .28, py - ry * .35 * open_, rx * .27, ry * .27 * open_, hexc("#FFFFFF"))
        cv.ellipse(px + rx * .3, py + ry * .3 * open_, rx * .12, ry * .12 * open_, hexc("#FFFFFF", 200))
    if lid > 0.02:                                       # heavy lid = smug / sleepy: cap of the eye ellipse
        ylid = y - ry * open_ + 2 * ry * open_ * lid
        pts = [(x + rx * 1.06 * math.cos(a), y + ry * open_ * 1.06 * math.sin(a))
               for a in [math.pi + i * math.pi / 24 for i in range(25)]]
        pts = [(px, min(py, ylid + (px - x) * 0.06 * lid)) for px, py in pts]
        cv.poly(pts, lidcol)
        cv.line([(pts[0][0], pts[0][1] + 1), (pts[-1][0], pts[-1][1] + 1)], hexc("#3A2418"), 3)


def crumb(cv: Cv, x, y, s=1.0, **p):
    """(x, y) = ground contact under the body centre. Height ~ 330*s sitting, ~200*s lying."""
    lie = p.get("lie", 0.0)
    flip = -1 if p.get("flip") else 1
    breathe = 1 + 0.018 * math.sin(p.get("t", 0) * 2.6)
    look = p.get("look", (0, 0))
    F = lambda dx: x + flip * dx * s                     # noqa: E731 mirror helper
    bw, bh = 150 * s, lerp(150, 105, lie) * s * breathe
    by = y - bh * 0.95
    hx, hy = p.get("head", (0, 0))
    # tail
    tw = p.get("tail", 0.0)
    cv.blob(F(-120 - 14 * tw), y - 40 * s, 62 * s, 26 * s, CREAM, rot=flip * (-18 + 20 * tw))
    # wings (behind the shoulders, peeking out beside the head)
    fl = p.get("wing", 0.0) + 0.10 * math.sin(p.get("t", 0) * 3.1)
    for sgn in (1, -1):
        wx, wy = x + flip * sgn * bw * .82, by - bh * .42
        cv.blob(wx, wy, 34 * s, 84 * s * (1 + .08 * fl), WING, rot=flip * sgn * (28 + 18 * fl), dark=.2)
    # feet
    for fx in (-52, 52):
        cv.blob(F(fx), y - 12 * s, 42 * s, 22 * s, CREAM, dark=.3)
        for c in (-14, 0, 14):
            cv.ellipse(F(fx + c * 1.1), y - 3 * s, 5 * s, 6 * s, hexc("#7A4A2A"))
    # body + belly
    cv.blob(x, by, bw, bh, CREAM, dark=.16)
    cv.blob(x + flip * 6 * s, by + bh * .22, bw * .62, bh * .66, CREAM_LIGHT, dark=.1, light=.1)
    if p.get("armor"):
        cardboard, tape = hexc("#B98B55"), hexc("#E8D9A8", 210)
        cv.rrect(x - bw * .55, by - bh * .32, x + bw * .55, by + bh * .68, 26 * s, cardboard, outline=hexc("#7C5630"), width=3)
        cv.rrect(x - bw * .3, by - bh * .55, x + bw * .3, by - bh * .3, 14 * s, cardboard, outline=hexc("#7C5630"), width=3)
        cv.rrect(x - bw * .12, by - bh * .32, x + bw * .12, by + bh * .68, 3, tape)
        cv.rrect(x - bw * .55, by + bh * .1, x + bw * .55, by + bh * .2, 3, tape)
    def draw_arms(raised):
        for side, key in ((-1, "armL"), (1, "armR")):
            ang = p.get(key, -55)
            if (ang > 25) != raised:
                continue
            ax, ay = x + flip * side * bw * .66, by + bh * .12
            L = 62 * s * (1 + .55 * max(0, ang) / 90)
            ex, ey = ax + flip * side * L * math.cos(math.radians(ang)), ay - L * math.sin(math.radians(ang))
            cv.capsule(ax, ay, ex, ey, 19 * s, CREAM)
            for k in (-1, 0, 1):                             # tiny claws
                cv.ellipse(ex + flip * side * 7 * s + k * 5 * s, ey + 8 * s + abs(k) * -2 * s + k * 2 * s, 4.5 * s, 8 * s,
                           hexc("#8B5A32"), rot=k * 25)

    draw_arms(False)
    # head
    hcx, hcy = x + flip * (hx + 6) * s, by - bh * .82 + hy * s + lie * 26 * s
    hr = 118 * s
    tilt = p.get("tilt", 0.0) * flip
    for sgn in (-1, 1):                                  # horns first (behind head shading)
        hxp = hcx + sgn * hr * .52
        cv.poly([(hxp - 20 * s, hcy - hr * .82), (hxp + 20 * s, hcy - hr * .82),
                 (hxp + sgn * 12 * s + tilt * 4, hcy - hr * 1.32)], HORN)
        cv.ellipse(hxp, hcy - hr * .84, 21 * s, 9 * s, hexc("#9E4A14"))
    cv.blob(hcx, hcy, hr * 1.06, hr, CREAM, rot=tilt, dark=.14)
    cv.blob(hcx, hcy + hr * .33, hr * .55, hr * .4, CREAM_LIGHT, dark=.05, light=.08, hi=(0, -.2))
    ex = hr * .43
    lidc = hexc('#E9D6AE')
    blink = p.get("blink", 0.0)
    for sgn in (-1, 1):
        _eye(cv, hcx + sgn * ex, hcy - hr * .04, hr * .19, hr * .25, look, blink, p.get("lid", 0.0), p.get("happy", 0.0),
             lidcol=lidc)
    for sgn in (-1, 1):                                  # cheeks
        cv.ellipse(hcx + sgn * hr * .68, hcy + hr * .3, hr * .13, hr * .08, hexc("#F0A58C", 120))
    cv.ellipse(hcx - hr * .06, hcy + hr * .26, 5 * s, 3.5 * s, hexc("#B98A66"))
    cv.ellipse(hcx + hr * .06, hcy + hr * .26, 5 * s, 3.5 * s, hexc("#B98A66"))
    draw_arms(True)                                      # raised arms in front of the head
    mo, sm = p.get("mouth", 0.0), p.get("smile", 0.0)
    my = hcy + hr * .5
    if mo > .08:
        cv.ellipse(hcx, my, hr * .12, hr * (.03 + .09 * mo), hexc("#5C2B1E"))
    else:
        cv.line([(hcx - hr * .14 + i * hr * .028, my - sm * hr * .04 * math.sin(math.pi * i / 10) * -1 + (0)) for i in range(11)],
                hexc("#7A4A36"), 4 * s)
    return (hcx, hcy, hr)


def mix_c(c, t):
    return tuple(int(v * (1 - t) + 200 * t) for v in c[:3]) + (255,)


# ------------------------------------------------------------------------------- Pip
DUCK, BILL = hexc("#F7D24A"), hexc("#F08A24")
COAT, COAT_D, BOOT = hexc("#2350C8"), hexc("#173A94"), hexc("#D5202C")


def pip(cv: Cv, x, y, s=1.0, **p):
    """Small round duck. (x,y) = ground under the boots. Height ~ 360*s."""
    t = p.get("t", 0)
    flip = -1 if p.get("flip") else 1
    breathe = 1 + 0.015 * math.sin(t * 2.4)
    walk = p.get("walk", 0.0)
    look = p.get("look", (0, 0))
    tint = p.get("tint")                                  # (rgb, strength) light colour, e.g. phone glow
    lean = p.get("lean", 0.0)
    F = lambda dx: x + flip * dx * s                      # noqa: E731
    bob = abs(math.sin(walk * math.pi)) * 8 * s
    y = y - bob
    ry = 168 * s * breathe
    by = y - 52 * s - ry * .9
    bxp = x + flip * lean * 24 * s
    cv.blob(bxp, by, 150 * s, ry, DUCK)
    cv.blob(bxp, by + 16 * s, 150 * s, ry * .98, COAT)                       # raincoat
    cv.blob(bxp, by + ry * .46, 136 * s, ry * .42, COAT_D, dark=.15, light=.05, hi=(0, .1))
    for k in range(3):
        cv.ellipse(bxp, by + (8 + 38 * k) * s, 8 * s, 8 * s, hexc("#F5D15A"))
    cv.rrect(bxp - 112 * s, by - 20 * s, bxp + 112 * s, by - 4 * s, 6, hexc("#1B3FA6"))
    bh = ry
    for sgn in (-1, 1):                                    # boots (in front of the coat hem)
        lift = max(0, math.sin(walk * math.pi + (0 if sgn < 0 else math.pi))) * 22 * s
        bx = F(sgn * 58 + lean * 10)
        cv.blob(bx, y - 44 * s - lift, 44 * s, 42 * s, BOOT, dark=.3)
        cv.blob(bx + flip * 26 * s, y - 20 * s - lift, 58 * s, 24 * s, BOOT, dark=.35)
        cv.ellipse(bx + flip * 26 * s, y - 3 * s - lift, 60 * s, 5 * s, hexc("#3A0A0E"))
    # arms / wings in sleeves
    for side, key in ((-1, "armL"), (1, "armR")):
        ang = p.get(key, -50)
        ax, ay = bxp + flip * side * 122 * s, by + 4 * s
        L = 66 * s
        ex, ey = ax + flip * side * L * math.cos(math.radians(ang)), ay - L * math.sin(math.radians(ang))
        cv.capsule(ax, ay, ex, ey, 24 * s, COAT)
        cv.ellipse(ex, ey + 6 * s, 22 * s, 19 * s, DUCK)
    # head
    hx, hy = p.get("head", (0, 0))
    hcx, hcy, hr = bxp + flip * (hx + lean * 10) * s, by - bh * .86 + hy * s, 124 * s
    cv.blob(hcx, hcy, hr * 1.12, hr, DUCK)
    cv.ellipse(hcx + flip * 8 * s, hcy - hr * .95, 16 * s, 26 * s, DUCK, rot=flip * 12)   # head tuft
    cv.ellipse(hcx - 6 * s * flip, hcy - hr * .98, 12 * s, 22 * s, DUCK, rot=-flip * 20)
    ex = hr * .44
    lidc = hexc("#E6BE3C")
    for sgn in (-1, 1):
        _eye(cv, hcx + sgn * ex + flip * look[0] * 6 * s, hcy - hr * .06, hr * .17, hr * .23, look, p.get("blink", 0.0),
             p.get("lid", 0.0), p.get("happy", 0.0), lidcol=lidc)
    brow = p.get("brow", 0.0)                             # >0 stern (inner ends down), <0 worried
    if abs(brow) > .02:
        for sgn in (-1, 1):
            yy = hcy - hr * .34
            cv.line([(hcx + sgn * (ex + hr * .2), yy - brow * -hr * .06 * -1 - brow * hr * .1),
                     (hcx + sgn * (ex - hr * .2), yy + brow * hr * .08)], hexc("#7A5A10"), 7 * s)
    mo = p.get("mouth", 0.0)
    bx, by2 = hcx + flip * look[0] * 8 * s, hcy + hr * .3
    cv.blob(bx, by2 + mo * 10 * s, hr * .5, hr * (.2 + .06 * mo), BILL, dark=.25, hi=(0, -.3))
    if mo > .1:
        cv.ellipse(bx, by2 + 4 * s + mo * 16 * s, hr * .34, hr * .05 * mo, hexc("#7A2E10"))
    cv.ellipse(bx - hr * .12, by2 - 2 * s, 5 * s, 3 * s, hexc("#B65E14"))
    cv.ellipse(bx + hr * .12, by2 - 2 * s, 5 * s, 3 * s, hexc("#B65E14"))
    for sgn in (-1, 1):
        cv.ellipse(hcx + sgn * hr * .72, hcy + hr * .3, hr * .13, hr * .08, hexc("#F29A6A", 110))
    if tint:                                               # colour cast over the whole character layer
        col, st = tint
        lay = cv.im
        a = lay.getchannel("A")
        from PIL import Image
        wash = Image.new("RGBA", lay.size, col + (int(255 * st),))
        wash.putalpha(a.point(lambda v: int(v * st)))
        lay.alpha_composite(wash)
    return (hcx, hcy, hr)
