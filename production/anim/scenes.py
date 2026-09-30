"""Per-video scene animation. Each scene is frame(shot_id, t_global) -> PIL image (1080x1920).

Beats are authored against the same timeline anchors the finishing tool uses (clip starts,
voice-line windows), so picture, voice, SFX and overlays stay locked together.
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFilter

import draw
import props as P
from draw import K, pulse, lerp, hexc, W, H


class Scene:
    def __init__(self, tl, talk):
        self.tl, self.A, self.talk = tl, tl.anchors, talk
        self.cache = {}

    def bg(self, key, fn, *a):
        if (key, a) not in self.cache:
            self.cache[(key, a)] = fn(*a)
        return self.cache[(key, a)].copy()

    def blink(self, t, times):
        return max([pulse(t, b, .22) for b in times] + [0])


def _blinks(t, seed=0.0):
    """Natural blink every ~3.3 s."""
    ph = (t + seed) % 3.3
    return pulse(ph, 3.0, .22)


# ================================================================== 1. The Heating Fee
class HeatingFee(Scene):
    def frame(self, shot, t):
        A, talk = self.A, self.talk
        f = self.bg("couch", P.bg_couch)
        speak = talk("crumb", t)
        base = dict(t=t, blink=_blinks(t, .4), mouth=speak, lie=1.0)
        cx, cy, s = 540, 1300, 1.9
        if shot == "c1":
            pose = dict(base, lid=K(t, [(0, .55), (.5, .3), (1.4, .1), (2.6, .35)]),
                        look=(K(t, [(0, -.2), (.3, -.2), (.8, .9)]), K(t, [(0, .1), (.6, -.5)])),
                        head=(K(t, [(0, 0), (.9, 12)]), K(t, [(0, 0), (.9, -22)])), armL=-70, armR=-70)
            P.crumb(f, cx, cy, s, **pose)
            hx = K(t, [(0.0, 1500), (.30, 0)])
            P.glass(f, 800 + hx, 820, 1.7, tilt=-6)
            P.hand(f, 1090 + hx, 930, deg=-88, pose="grip", s=1.7)
        elif shot == "c2":
            c0 = A["c2.start"]
            up = K(t, [(c0, 0), (c0 + .5, 1)])
            pose = dict(base, lid=.15, look=(.4 * up, -.85 * up), tilt=-3 * up,
                        head=(10, K(t, [(c0, -18), (c0 + .5, -34)])), armL=-70, armR=-70,
                        blink=max(base["blink"], pulse(t, c0 + 1.5, .5)), smile=0)
            P.crumb(f, cx, cy, s, **pose)
            poke = K(t, [(c0, 90), (c0 + .35, 0)]) + pulse(t, c0 + 1.0, .5, 30)
            P.hand(f, 1010 + poke * .7, 260 - poke * .25 + 60, deg=-138, pose="point", s=2.0)
        elif shot == "c3":
            c0 = A["c3.start"]
            raise_ = K(t, [(c0 + .1, -70), (c0 + .6, 58)])
            zoom = K(t, [(c0 - .3, 2.2), (c0 + 2, 2.35)])
            pose = dict(base, lie=.55, lid=.08, look=(0, -.15), head=(0, -10), armL=-70, armR=raise_,
                        blink=max(base["blink"], pulse(t, c0 + 1.25, .3)))
            P.crumb(f, 540, 1520, zoom, **pose)
        else:                                                 # c4: kiss, scoot, pat, "There."
            c0 = A["c4.start"]
            kiss = c0 + .75
            scoot = K(t, [(c0 + 1.65, 0), (c0 + 1.95, -140)])
            hop = pulse(t, c0 + 1.65, .3, 26)
            closed = kiss - .12 < t < kiss + .75
            there = A["v5.start"]
            pat = pulse(t, c0 + 2.35, .35) + pulse(t, c0 + 2.8, .35)
            armR = -78 + 68 * min(1, pat)
            if scoot < -10:                                    # the warm spot he left behind
                lay = Image.new("L", (W, H), 0)
                ImageDraw.Draw(lay).ellipse((cx - 220, cy - 120, cx + 250, cy + 40), fill=255)
                lay = lay.filter(ImageFilter.GaussianBlur(28))
                f.paste(Image.new("RGB", (W, H), (236, 150, 78)), (0, 0), lay.point(lambda v: int(v * K(t, [(c0 + 1.65, 0), (c0 + 2.3, .55)]))))
            pose = dict(base, lie=.9, lid=.1, happy=1.0 if closed else 0.0, tilt=K(t, [(kiss - .3, 0), (kiss, 4), (kiss + .5, 0)]),
                        head=(0, -14 + 10 * pulse(t, kiss - .1, .5)),
                        look=(K(t, [(c0 + 2.2, .0), (c0 + 2.4, .9), (c0 + 3.0, .9), (c0 + 3.2, .3)]), K(t, [(c0 + 2.2, .0), (c0 + 2.4, .6), (c0 + 3.0, .6), (c0 + 3.2, -.7)])),
                        armL=-70, armR=armR, smile=K(t, [(c0 + 2.5, 0), (there, 1)]), blink=0 if closed else base["blink"])
            P.crumb(f, cx + scoot, cy - hop, s, **pose)
            if t < kiss + .8:                                  # lower half of a face: chin + lips only
                drop = K(t, [(kiss - .6, -330), (kiss - .02, 690)]) if t < kiss + .1 else K(t, [(kiss + .1, 690), (kiss + .75, -330)])
                if drop > -300:
                    P.lips_face(f, 540, drop, 1.0, pucker=.6)
        return f


def jit(t, amp, freq=38.0):
    return amp * math.sin(t * freq) * math.sin(t * freq * .37)


def phone_flat(f, cx, cy, w, h, glow=0.0, shake=0.0):
    """Smartphone lying flat, seen from a low angle: top face + visible edge. Blank screen only."""
    cv = draw.Cv((max(0, int(cx - w)), max(0, int(cy - h)), min(W, int(cx + w)), min(H, int(cy + h))))
    cv.rrect(cx - w / 2, cy - h / 2 + 34, cx + w / 2, cy + h / 2 + 34, 46, hexc("#0E0F14"))         # edge
    cv.rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 46, hexc("#1A1B22"))
    scr = draw.mix((11, 12, 16), (196, 222, 255), glow)
    cv.rrect(cx - w / 2 + 16, cy - h / 2 + 16, cx + w / 2 - 16, cy + h / 2 - 16, 34, scr + (255,))
    cv.rrect(cx - w / 2 + 16, cy - h / 2 + 16, cx + w / 2 - 16, cy - h * .08, 34, draw.mix(scr, (255, 255, 255), .2) + (90,))
    cv.flush(f)
    if glow > .05:
        draw.radial_light(f, cx, cy - 40, w * .95, (170, 205, 255), .30 * glow)


# ================================================================== 2. The Phone Call
class PhoneCall(Scene):
    PH = dict(cx=540, cy=1670, w=1010, h=560)

    def phone(self, f, glow=0.0, dx=0.0):
        phone_flat(f, self.PH["cx"] + dx, self.PH["cy"], self.PH["w"], self.PH["h"], glow=glow)

    def frame(self, shot, t):
        A, talk = self.A, self.talk
        f = self.bg("kitchen", P.bg_kitchen)
        sp = talk("crumb", t)
        ring = [A["c3.start"] + .3, A["c3.start"] + 1.75, A["c3.start"] + 3.2]
        rp = max([pulse(t, r, .75) for r in ring] + [0])
        if shot == "c1":
            c0 = A["c1.start"]
            pose = dict(t=t, armor=True, blink=0, lid=0, look=(0, -.35), head=(0, -14), mouth=sp,
                        armL=K(t, [(c0, -10), (c0 + .8, 62)]), armR=K(t, [(c0, -10), (c0 + .8, 70)]), wing=1.0, smile=.6,
                        tilt=math.sin(t * 1.6) * 2)
            self.phone(f)
            P.crumb(f, 540, 1585, 1.62 + .02 * math.sin(t), **pose)
        elif shot == "c2":
            c0 = A["c2.start"]
            look = K(t, [(c0, 1.0), (c0 + .4, .0), (c0 + .8, -.2)])
            pose = dict(t=t, armor=True, blink=_blinks(t), lid=0, look=(look * .9, K(t, [(c0, -.2), (c0 + .6, .8)])),
                        head=(0, K(t, [(c0, -14), (c0 + .7, 2)])), armL=K(t, [(c0, 62), (c0 + .7, -20)]),
                        armR=K(t, [(c0, 70), (c0 + .7, -20)]), wing=K(t, [(c0, 1), (c0 + .7, .2)]),
                        smile=K(t, [(c0, .6), (c0 + .7, 0)]))
            self.phone(f)
            P.crumb(f, 540, 1585, 1.6, **pose)
            P.hand(f, K(t, [(c0, 1400), (c0 + .4, 1010)]), 1500, deg=-92, pose="open", s=1.7)
        elif shot == "c3":
            c0 = A["c3.start"]
            freeze = K(t, [(c0 + .25, 0), (c0 + .45, 1)])
            slump = K(t, [(c0 + 1.2, 0), (c0 + 3.4, 1)])
            self.phone(f, glow=min(1, rp * 1.6), dx=jit(t, 6 * rp))
            pose = dict(t=t if freeze < .5 else 0, armor=True, blink=0 if freeze > .5 else _blinks(t), lid=0.0,
                        look=(0, .9), head=(0, K(t, [(c0, 0), (c0 + 3.4, 26)])), mouth=sp,
                        armL=K(t, [(c0, -20), (c0 + .45, 40), (c0 + 3.4, -75)]),
                        armR=K(t, [(c0, -20), (c0 + .45, 40), (c0 + 3.4, -75)]),
                        wing=K(t, [(c0, .2), (c0 + .45, 1.2), (c0 + 3.4, -1.4)]), smile=-.5 * slump, tilt=6 * slump)
            P.crumb(f, 540, 1585, 1.6 - .2 * slump, **pose)
        else:
            c0 = A["c4.start"]
            phone_flat(f, 250, 1650, 640, 380, glow=.55 + .2 * math.sin(t * 6))
            lift = K(t, [(c0 + .8, 0), (c0 + 1.2, 74), (c0 + 2.6, 74), (c0 + 3.0, 0)]) + jit(t, 3, 55) * (1 if t > c0 + .3 else 0)
            P.mug_inverted(f, 760, 1640, 2.1, lift=max(0, lift), look=(-1, 0))
        return f


# ================================================================== 3. One More Video
class OneMoreVideo(Scene):
    def peek(self, f, y0, s_pip, cx, cy, pw, ph, t, **pose):
        P.pip(f, cx, y0, s_pip, t=t, tint=((110, 150, 255), .07), **pose)
        P.phone(f, cx, cy, pw, ph, deg=-2, screen=hexc("#9DBCFF"), glow=((110, 150, 255), .5))
        top = cy - ph / 2
        wc = draw.Cv((0, int(top - 60), W, int(top + 60)))
        for sg in (-1, 1):
            wc.ellipse(cx + sg * (pw / 2 - 40), top + 2, 34, 28, hexc("#F7D24A"))
        wc.flush(f)

    def frame(self, shot, t):
        A, talk = self.A, self.talk
        sp = talk("pip", t)
        f = self.bg("bed", P.bg_bedroom, 0.0) if shot in ("c1", "c2") else self.bg("bed_dark", P.bg_bedroom, 1.0)
        if shot == "c1":
            c0 = A["c1.start"]
            pulled = K(t, [(c0 + 1.4, 0), (c0 + 2.6, 1)])
            px = 700 - 280 * pulled
            walk_in = t < c0 + 1.0
            pxx = K(t, [(c0, -160), (c0 + 1.0, 300), (c0 + 1.4, 300), (c0 + 2.6, 90)])
            P.phone(f, px, 1330, 330, 610, deg=-4 + 8 * pulled, screen=hexc("#3A3F66"), glow=((150, 170, 255), .25))
            P.hand(f, 1070, 1400, deg=-90, pose="grip" if pulled < .2 else "open", s=1.9, mirror=True)
            grab = K(t, [(c0 + .9, 0), (c0 + 1.2, 1)])
            P.pip(f, pxx, 1640, 1.55, t=t, walk=(t - c0) * 2.4 % 2 if (walk_in or t > c0 + 1.4) else 0, brow=1.0, lid=.25,
                  look=(1, 0), mouth=sp, armL=K(t, [(c0 + .9, -50), (c0 + 1.25, 25)]), armR=K(t, [(c0 + .9, -50), (c0 + 1.25, 25)]),
                  head=(-6 * grab, 0))
        elif shot == "c2":
            c0 = A["c2.start"]
            nod = pulse(t, c0 + 1.35, .5, 16) + pulse(t, c0 + 1.8, .5, 12)
            xx = K(t, [(c0, 140), (c0 + .8, 640)])
            rise = K(t, [(c0 + .45, 0), (c0 + .8, 1)])
            place = K(t, [(c0 + .8, 0), (c0 + .95, 1)])
            phx = draw.lerp(xx + 250, 760, place)
            phy = draw.lerp(draw.lerp(1300, 900, rise), 752, place)
            deg = draw.lerp(0, 90, rise)
            P.pip(f, xx, 1640, 1.55, t=t, walk=((t - c0) * 2.4 % 2) if t < c0 + .8 else 0, brow=.8, lid=.25, look=(1, -.3 * rise),
                  armL=draw.lerp(35, 85, rise) if place < .5 else -50, armR=draw.lerp(35, 85, rise) if place < .5 else -50,
                  head=(0, nod), smile=.5 * place)
            P.phone(f, phx, phy, 330, 610, deg=deg, screen=hexc("#3A3F66"), glow=((150, 170, 255), .25 * place))
        elif shot == "c3":
            c0 = A["c3.start"]
            draw.radial_light(f, 560, 1250, 900, (70, 110, 255), .22)
            scan = math.sin((t - c0) * 5.2)
            swipe = pulse((t - c0) % .9, .0, .35, 28)
            self.peek(f, 1600, 1.7, 560, 1600, 640, 860, t, lid=.22, brow=0, look=(0, .45 + .5 * scan), head=(0, 6),
                      armR=-8 + swipe, armL=-45, blink=_blinks(t, 1.1), mouth=0)
        else:
            c0 = A["c4.start"]
            draw.radial_light(f, 540, 1400, 1300, (70, 110, 255), .28)
            flick = K(t, [(c0 + 1.5, 0), (c0 + 1.7, 1), (c0 + 2.3, 1), (c0 + 2.5, 0)])
            self.peek(f, 1960, 3.2, 540, 1900, 980, 940, t, lid=.15 * (1 - flick), brow=-.5 * flick, mouth=sp,
                      look=(1.3 * flick, .6 * (1 - flick) - .1 * flick), head=(0, 4), blink=max(pulse(t, c0 + 2.9, .25), 0),
                      shadow=False)
            if t > c0 + 1.9:
                sc = draw.Cv((700, 500, 900, 900))
                y0 = 640 + 40 * K(t, [(c0 + 1.9, 0), (c0 + 2.6, 1)])
                sc.ellipse(800, y0 + 30, 22, 30, hexc("#9FD0FF", 220))
                sc.poly([(800, y0 - 30), (778, y0 + 24), (822, y0 + 24)], hexc("#9FD0FF", 220))
                sc.flush(f)
        return f


# ================================================================== 4. Social Battery Inspection
class SocialBattery(Scene):
    def wide(self, f, t, jig=0.0, hand_in=0.0, tap=0.0):
        P.door(f, 540, 230, 640, 1350)
        P.door_handle(f, 820, 930, jig)
        P.sneakers(f, 1040, 1700, 1.15, tap=tap, gap=250)
        if hand_in > 0:
            P.hand(f, 1230 - 250 * hand_in, 700 + 20 * hand_in, deg=-125, pose="grip", s=1.5)
        P.cardboard_sign(f, 290, 1640, 500, 800, deg=-2)

    def frame(self, shot, t):
        A, talk = self.A, self.talk
        sp = talk("pip", t)
        f = self.bg("entry", P.bg_entry)
        if shot in ("c1", "c2"):
            jig, hand_in, tap = 0.0, 0.0, 0.0
            if shot == "c1":
                c0 = A["c1.start"]
                jig = max(pulse(t, c0 + .2 + k * .16, .12, 1) for k in range(6))
                hand_in = K(t, [(c0 + .05, 0), (c0 + .25, 1), (c0 + 1.2, 1), (c0 + 1.5, 0)])
                tap = max(0, math.sin(t * 7))
            self.wide(f, t, jig, hand_in, tap)
            nod = pulse(t, A["c2.start"] + 1.5, .45, 14) if shot == "c2" else 0
            P.pip(f, 620, 1650, 1.5, t=t, brow=1.0, lid=.1, look=(.2, -.4), mouth=sp, armL=-25, armR=-25, head=(0, nod),
                  blink=_blinks(t, .6))
        elif shot == "c3":
            c0 = A["c3.start"]
            tap = pulse(t, c0 + 1.0, .5)
            heel = pulse(t, c0 + .3, .5) * .6
            P.sneakers(f, 540, 1500, 2.0, tap=max(tap, heel), gap=250)
            P.pip(f, 1010, 1830, 1.45, t=t, flip=True, brow=.6, look=(-1, -.2), armL=-40, armR=-40)
        elif shot == "c4":
            c0 = A["c4.start"]
            stamp_t = A["v4.end"] + .12
            press = K(t, [(stamp_t - .25, 0), (stamp_t, 1)]) if t < stamp_t + .05 else K(t, [(stamp_t + .05, 1), (stamp_t + .5, 0)])
            scr = K(t, [(c0 + .1, 0), (c0 + 1.2, 1)])
            P.pip(f, 540, 1720, 2.3, t=t, brow=1.0, lid=.15, look=(0, .9), mouth=sp, armL=-60, armR=-60, head=(0, 8), shadow=False)
            P.clipboard(f, 540, 1530, 600, 780, deg=-3, scribble=scr if t < stamp_t else 1.0)
            wob = math.sin(t * 22) * 20 * (1 if c0 + .1 < t < c0 + 1.2 else 0)
            P.pencil(f, 470 + wob + 40 * scr, 1510 - wob * .3, 630 + wob + 40 * scr, 1360)
            if stamp_t - .3 < t < stamp_t + .6:
                P.stamp(f, 610, 1530, 1.6, press=press)
            wc = draw.Cv((0, 1050, W, 1290))
            for sg in (-1, 1):
                wc.ellipse(540 + sg * 250, 1165, 40, 34, hexc("#F7D24A"))
            wc.flush(f)
        else:
            c0 = A["c5.start"]
            bx = K(t, [(c0 + .3, -300), (c0 + 1.6, 620)])
            P.sneakers(f, 720, 990, 1.35, gap=230)
            P.blanket(f, bx, 1500, 620, 250, color="#3E8E8A", stripe="#2B6C68")
            push = K(t, [(c0 + .1, 0), (c0 + .6, 1), (c0 + 1.5, 0)])
            nod = pulse(t, c0 + 2.0, .5, 16)
            P.pip(f, 190, 1750, 1.55, t=t, brow=.6, lid=.2, look=(1, .3), armL=10 * push, armR=10 * push, lean=.5 * push,
                  head=(0, nod), smile=.4)
        return f


# ================================================================== 5. The Comfort Hoard
class ComfortHoard(Scene):
    def pile(self, f, t, blur=0.0):
        lay = f.copy()
        P.tissues(lay, 990, 1500, 1.0)
        P.blanket(lay, 700, 1500, 540, 210)
        P.mug(lay, 860, 1385, 1.05, steam=1.0, t=t)
        if blur:
            reg = lay.crop((380, 1000, W, 1720)).filter(ImageFilter.GaussianBlur(blur))
            lay.paste(reg, (380, 1000))
        f.paste(lay)

    def frame(self, shot, t):
        A, talk = self.A, self.talk
        f = self.bg("living", P.bg_livingroom)
        sp = talk("crumb", t)
        SL = .85
        if shot == "c1":
            c0 = A["c1.start"]
            self.pile(f, t, blur=16)
            heave = [c0 + .35, c0 + .85, c0 + 1.4, c0 + 1.95, c0 + 2.45]
            prog = sum(K(t, [(h - .05, 0), (h + .3, 1)]) for h in heave) / 5
            sx = 260 + 250 * prog
            hv = max([pulse(t, h, .32) for h in heave] + [0])
            P.slipper(f, sx, 1640, SL)
            P.crumb(f, sx + 400 + 26 * hv, 1660, 1.45, t=t, armL=-8 + 22 * hv, armR=-70, lid=.45 + .2 * hv,
                    mouth=.7 * hv, tilt=-7 * hv, look=(-.8, .4), head=(-8 * hv, 4), smile=-.6, wing=-.3,
                    blink=0.4 * hv)
            if hv > .3:                                        # effort sweat drop
                sc = draw.Cv((sx + 380, 1200, sx + 640, 1400))
                sc.ellipse(sx + 560, 1290 + 30 * hv, 12, 17, hexc("#BFE3FF", 220))
                sc.flush(f)
        elif shot == "c2":
            c0 = A["c2.start"]
            self.pile(f, t)
            lift = K(t, [(c0 + 1.0, 0), (c0 + 1.9, 1)])
            sx = K(t, [(c0, 510), (c0 + 1.0, 540), (c0 + 1.9, 590)])
            sy = 1640 - 300 * lift
            hop = pulse(t, c0 + 1.1, .7, 60)
            P.slipper(f, sx, sy, SL, deg=-6 * lift)
            P.crumb(f, 250 + 120 * lift, 1665 - hop, 1.45, t=t, armL=K(t, [(c0 + .8, -15), (c0 + 1.9, 55)]), armR=-70,
                    lid=.2, mouth=sp, look=(.9, -.2), head=(0, 0), smile=K(t, [(c0 + 2.2, 0), (c0 + 3.0, .8)]), flip=True)
        else:
            f = self.bg("living_b", P.bg_livingroom, 10)
            c0 = A[shot + ".start"]
            P.blanket(f, 560, 1600, 1000, 380)
            P.mug(f, 150, 1600, 1.5, steam=1.0, t=t)
            P.tissues(f, 330, 1610, 1.3)
            if shot == "c3":
                pat = pulse(t, c0 + .7, .35) + pulse(t, c0 + 1.05, .35)
                P.crumb(f, 560, 1520, 2.15, t=t, armR=-40 + 45 * min(1, pat), armL=-70, lid=.1, mouth=sp, smile=.5,
                        look=(K(t, [(c0 + .6, .8), (c0 + 1.4, 0)]), K(t, [(c0 + .6, .5), (c0 + 1.4, -.3)])), head=(0, -4),
                        blink=_blinks(t, .2))
            else:
                hx = K(t, [(c0 + .2, 1350), (c0 + 1.6, 900)])
                lean = K(t, [(c0 + 1.7, 0), (c0 + 2.4, 1)])
                P.crumb(f, 560 + 30 * lean, 1520, 2.15, t=t, armR=-40, armL=-70, lid=.1, happy=lean, smile=.9, tilt=5 * lean,
                        look=(.8, .3), head=(14 * lean, 0), blink=0)
                P.hand(f, hx, 1560, deg=-88, pose="open", s=1.8)
        return f
