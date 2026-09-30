"""3D staging for the five videos. build(shot) creates the set; frame(shot, t) poses it at timeline time t."""
from __future__ import annotations

import math
import os

import bpy
from mathutils import Vector

import lib3d as L
import props3d as PR
import sets3d as S
from crumb3d import Crumb
from pip3d import Pip


def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def K(t, keys):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * smooth((t - t0) / max(1e-9, t1 - t0))
    return keys[-1][1]


def pulse(t, t0, dur, peak=1.0):
    u = (t - t0) / dur
    return peak * math.sin(math.pi * u) if 0 <= u <= 1 else 0.0


def blinks(t, seed=0.0):
    return pulse((t + seed) % 3.3, 3.0, 0.2)


def V(*a):
    return Vector(a)


class Base:
    def __init__(self, tl, talk):
        self.tl, self.A, self.talk = tl, tl.anchors, talk
        self.cam = None

    def focus_on(self, obj_or_point, loc, target, fstop, lens=None):
        L.aim_camera(self.cam, loc, target, fstop)
        if lens:
            self.cam.data.lens = lens
        bpy.context.view_layer.update()
        p = obj_or_point.matrix_world.translation if hasattr(obj_or_point, "matrix_world") else Vector(obj_or_point)
        self.cam.data.dof.focus_distance = (self.cam.location - p).length


# ============================================================ 1. The Heating Fee
class HeatingFee(Base):
    def build(self, shot):
        S.couch(dent_at=(0.2, -0.2), dent_r=2.4, dent_depth=0.4)
        S.light_couch()
        self.c = Crumb()
        self.c.root.location = (0.2, -0.2, -0.33)
        self.hand = PR.Hand()
        self.glass = PR.glass()
        self.glass.scale = (1.35, 1.35, 1.35)
        self.face = PR.Face()
        self.cam = L.camera((1, -9, 3), (0, 0, 1))

    def frame(self, shot, t):
        A, c = self.A, self.c
        sp = self.talk("crumb", t)
        base = dict(t=t, blink=blinks(t, .4), mouth=sp, lie=1.0, smile=0.45)
        self.face.pose((0, 0, 40), visible=False)
        if shot == "c1":
            c.pose(**dict(base, lid=K(t, [(0, .16), (.5, .06), (1.4, .0), (2.6, .12)]),
                          look=(K(t, [(0, -.2), (.35, -.2), (.8, .75)]), K(t, [(0, .1), (.6, -.55)])),
                          head=(K(t, [(0, 0), (.9, 14)]), K(t, [(0, -4), (.9, -18)])), smile=K(t, [(0, .3), (2.2, .7)])))
            gx = K(t, [(0.0, 5.0), (0.32, 1.35)])
            gz = K(t, [(0.0, 2.2), (0.32, 1.85), (0.45, 1.8)])
            self.glass.location = (gx, -3.0, gz)
            self.hand.pose((gx + 1.05, -3.45, gz + 0.85), direction=(-1, 0, 0.1), palm=(0, 1, 0), curl=0.55)
            self.focus_on(c.eyes[0], (0.9, -9.8, 3.1), (0.35, -0.2, 1.75), 0.22, lens=55)
        elif shot == "c2":
            c0 = A["c2.start"]
            up = K(t, [(c0, 0), (c0 + .5, 1)])
            c.pose(**dict(base, lid=.1, look=(.35 * up, -.8 * up), tilt=-3 * up, head=(10, -18 - 14 * up),
                          blink=max(base["blink"], pulse(t, c0 + 1.5, .5)), smile=0.35))
            self.glass.location = (0, 0, -40)
            poke = K(t, [(c0, 1.0), (c0 + .35, 0)]) + pulse(t, c0 + 1.0, .5, 0.25)
            tip = V(0.95, -1.1, 3.05) + V(0.9, -0.3, 0.9) * poke
            d = V(-0.55, 0.25, -0.8).normalized()
            self.hand.pose(tip - d * 1.95, direction=d, palm=(0.3, 0.2, 1), curl=0.95, point=True)
            self.focus_on(c.eyes[0], (1.0, -9.0, 3.5), (0.4, -0.3, 1.8), 0.22, lens=55)
        elif shot == "c3":
            c0 = A["c3.start"]
            c.pose(**dict(base, lie=0.85, lid=.05, look=(0, -.1), head=(0, -6), armR=K(t, [(c0 + .1, -70), (c0 + .55, 64)]),
                          blink=max(base["blink"], pulse(t, c0 + 1.25, .3)), smile=0.2))
            self.glass.location = (0, 0, -40)
            self.hand.pose((0, 0, 0), visible=False)
            push = K(t, [(c0 - .2, 0), (c0 + 2.0, 1)])
            self.focus_on(c.eyes[0], (0.6, -6.0 + 0.5 * push, 1.9), (0.25, -0.5, 1.15), 0.16, lens=55)
        else:                                               # c4: kiss, scoot, pat, "There."
            c0 = A["c4.start"]
            kiss = c0 + .75
            there = A["v5.start"]
            closed = kiss - .12 < t < kiss + .8
            scoot = K(t, [(c0 + 1.65, 0), (c0 + 1.95, -0.45)])
            hop = pulse(t, c0 + 1.65, .3, 0.12)
            pat = pulse(t, c0 + 2.35, .35) + pulse(t, c0 + 2.8, .35)
            c.root.location = (0.2 + scoot, -0.2, -0.33 + hop)
            c.pose(**dict(base, lid=.05, happy=1.0 if closed else 0.0, tilt=K(t, [(kiss - .3, 0), (kiss, 4), (kiss + .5, 0)]),
                          head=(K(t, [(c0 + 2.2, 0), (c0 + 2.5, 14), (c0 + 3.1, 14), (c0 + 3.3, 4)]),
                                -12 + 8 * pulse(t, kiss - .1, .5) - K(t, [(c0 + 2.9, 0), (c0 + 3.3, 14)])),
                          look=(K(t, [(c0 + 2.2, 0), (c0 + 2.4, .8), (c0 + 3.0, .8), (c0 + 3.2, .2)]),
                                K(t, [(c0 + 2.2, 0), (c0 + 2.4, .5), (c0 + 3.0, .5), (c0 + 3.2, -.7)])),
                          armR=-70 + 55 * min(1, pat), smile=K(t, [(c0 + 2.5, .4), (there, .95)]),
                          blink=0 if closed else base["blink"]))
            self.glass.location = (0, 0, -40)
            self.hand.pose((0, 0, 0), visible=False)
            bpy.context.view_layer.update()
            fh = c.head.matrix_world @ Vector((0, -0.2, 0.6))
            drop = K(t, [(kiss - .6, 3.0), (kiss - .02, 0.0)]) if t < kiss + .1 else K(t, [(kiss + .1, 0.0), (kiss + .75, 3.0)])
            self.face.pose(fh + V(0.12 + 0.7 * drop, -0.05, 0.05 + drop), pucker=0.7, visible=drop < 2.9)
            # tight on the kiss, then ease back out for the scoot and pat
            wide = K(t, [(kiss + .75, 0), (c0 + 1.6, 1)])
            cl = V(0.4, -5.0, 1.85).lerp(V(0.8, -8.8, 3.0), wide)
            tg = V(0.2, -0.3, 1.45).lerp(V(0.0, -0.2, 1.7), wide)
            self.focus_on(c.eyes[0], tuple(cl), tuple(tg), 0.2, lens=50)


# ============================================================ 2. The Phone Call
class PhoneCall(Base):
    CS = 0.42

    def build(self, shot):
        S.kitchen()
        if shot == "c4":
            self.phone = PR.phone(w=1.0, h=2.0)
            self.phone.location = (-1.8, -0.4, 0)
            self.phone.rotation_euler = (0, 0, math.radians(12))
            self.mug = PR.mug(color="#F4EFE6")
            ms = 1.8
            self.piv = L.empty("mugpiv", (0.8, 0.48 * ms, 0))
            self.mug.parent = self.piv
            self.mug.scale = (ms, ms, ms)
            self.mug.location = (0, -0.48 * ms, 1.0 * ms)
            self.mug.rotation_euler = (math.radians(180), 0, 0)
            self.c = Crumb()
            self.c.root.scale = (self.CS,) * 3
            self.c.root.location = (0.8, 0.12, 0.0)
        else:
            self.phone = PR.phone(w=1.0, h=2.0)
            self.c = Crumb()
            self.c.add_armor()
            self.c.root.scale = (self.CS,) * 3
            self.c.root.location = (0, 0.1, 0.085)
            self.hand = PR.Hand()
        self.cam = L.camera((0, -4, 1), (0, 0, 0.5))

    def frame(self, shot, t):
        A, c = self.A, self.c
        sp = self.talk("crumb", t)
        ring = [A["c3.start"] + .3, A["c3.start"] + 1.75, A["c3.start"] + 3.2]
        rp = max([pulse(t, r, .75) for r in ring] + [0])
        if shot == "c1":
            c0 = A["c1.start"]
            c.pose(t=t, lie=0, blink=0, look=(0, -.4), head=(0, -12), mouth=sp, armL=K(t, [(c0, -30), (c0 + .8, 60)]),
                   armR=K(t, [(c0, -30), (c0 + .8, 70)]), wing=1.1, smile=.7)
            self.hand.pose((0, 0, 0), visible=False)
            PR.set_phone_glow(self.phone, 0)
            push = K(t, [(c0, 0), (c0 + 3.5, 1)])
            self.focus_on(c.eyes[0], (0.35, -2.6 + 0.35 * push, 0.18), (0, 0.05, 0.62), 0.12, lens=28)
        elif shot == "c2":
            c0 = A["c2.start"]
            lk = K(t, [(c0, 1.0), (c0 + .4, 0), (c0 + .8, -.2)])
            c.pose(t=t, lie=0, blink=blinks(t), look=(lk * .9, K(t, [(c0, -.2), (c0 + .6, .7)])),
                   head=(8 * lk, K(t, [(c0, -12), (c0 + .7, 6)])), armL=K(t, [(c0, 60), (c0 + .7, -40)]),
                   armR=K(t, [(c0, 70), (c0 + .7, -40)]), wing=K(t, [(c0, 1.1), (c0 + .7, .2)]), smile=K(t, [(c0, .7), (c0 + .7, .1)]))
            hx = K(t, [(c0, 4.5), (c0 + .45, 1.75)])
            self.hand.pose((hx + 0.4, 0.1, 0.45), direction=(-1, 0.05, 0.15), palm=(0, -0.3, 1), curl=0.15, spread=0.5)
            PR.set_phone_glow(self.phone, 0)
            self.focus_on(c.eyes[0], (0.5, -3.6, 0.8), (0.2, 0.0, 0.55), 0.14, lens=32)
        elif shot == "c3":
            c0 = A["c3.start"]
            freeze = K(t, [(c0 + .25, 0), (c0 + .45, 1)])
            slump = K(t, [(c0 + 1.2, 0), (c0 + 3.4, 1)])
            j = 0.02 * rp * math.sin(t * 80)
            self.phone.location = (j, 0, 0)
            PR.set_phone_glow(self.phone, 4.0 * min(1, rp * 1.8))
            c.root.location = (j, 0.1, 0.085)
            c.pose(t=t if freeze < .5 else c0, lie=0, blink=0 if freeze > .5 else blinks(t), look=(0, .85),
                   head=(0, K(t, [(c0, 0), (c0 + 3.4, 20)])), mouth=sp,
                   armL=K(t, [(c0, -40), (c0 + .45, 45), (c0 + 3.4, -80)]), armR=K(t, [(c0, -40), (c0 + .45, 45), (c0 + 3.4, -80)]),
                   wing=K(t, [(c0, .2), (c0 + .45, 1.4), (c0 + 3.4, -1.5)]), smile=-.4 * slump, tilt=5 * slump)
            self.hand.pose((0, 0, 0), visible=False)
            self.focus_on(c.eyes[0], (0.3, -3.0, 0.75), (0, 0.05, 0.5), 0.14, lens=35)
        else:
            c0 = A["c4.start"]
            ang = K(t, [(c0 + .8, 0), (c0 + 1.2, 24), (c0 + 2.6, 24), (c0 + 3.0, 0)])
            ang += 1.2 * math.sin(t * 55) * (1 if c0 + .3 < t < c0 + .8 else 0)
            self.piv.rotation_euler = (math.radians(-ang), 0, 0)
            c.pose(t=t, lie=1, blink=blinks(t, 1.0), look=(-0.5, 0.1), head=(0, 4), smile=-.2, lid=0.1)
            PR.set_phone_glow(self.phone, 2.0 + 0.8 * math.sin(t * 6))
            self.focus_on(V(0.8, -0.3, 0.3), (0.6, -4.2, 0.55), (0.2, 0, 0.4), 0.14, lens=40)


# ============================================================ 3. One More Video
class OneMoreVideo(Base):
    PS = 0.55

    def build(self, shot):
        S.bedroom()
        dark = shot in ("c3", "c4")
        S.light_bedroom(lamp=0.0 if dark else 1.0, moon=1.0 if dark else 0.0)
        self.p = Pip()
        self.p.root.scale = (self.PS,) * 3
        self.phone = PR.phone(w=0.8, h=1.6)
        if not dark:
            self.hand = PR.Hand()
        else:
            L.light_area("glow", (0, -1.2, 0.9), (0, 0.4, 0.9), 0.0, size=0.8, color=(0.6, 0.72, 1.0))
            self.glow = bpy.data.objects["glow"]
        self.cam = L.camera((0, -5, 3), (0, 0, 0.5))

    def frame(self, shot, t):
        A, p = self.A, self.p
        sp = self.talk("pip", t)
        if shot == "c1":
            c0 = A["c1.start"]
            pulled = K(t, [(c0 + 1.4, 0), (c0 + 2.6, 1)])
            px = K(t, [(c0, -2.8), (c0 + 1.0, 0.0), (c0 + 1.4, 0.0), (c0 + 2.6, -0.9)])
            walking = t < c0 + 1.0 or c0 + 1.4 < t < c0 + 2.6
            p.root.location = (px, 0, 0.02)
            p.root.rotation_euler = (0, 0, math.radians(-35 if t < c0 + 1.0 else -20))
            p.pose(t=t, walk=((t - c0) * 2.6) % 2 if walking else 0, brow=1.0, lid=.25, look=(.8, .1), mouth=sp,
                   armL=K(t, [(c0 + .9, -50), (c0 + 1.2, 5)]), armR=K(t, [(c0 + .9, -50), (c0 + 1.2, 5)]), lean=.3 * pulled)
            self.phone.location = (1.25 - 1.1 * pulled, -0.2, 0.0)
            self.phone.rotation_euler = (0, 0, math.radians(80 + 12 * pulled))
            self.hand.pose((2.5, 0.1, 0.25), direction=(-1, -0.05, 0.02), palm=(0, 0, -1), curl=0.25 if pulled < .3 else 0.05)
            self.focus_on(p.head, (0.3, -5.6, 2.6), (0.2, 0, 0.55), 0.2, lens=36)
        elif shot == "c2":
            c0 = A["c2.start"]
            xx = K(t, [(c0, -0.9), (c0 + .9, 1.0)])
            place = K(t, [(c0 + .85, 0), (c0 + 1.0, 1)])
            nod = pulse(t, c0 + 1.35, .5, 14) + pulse(t, c0 + 1.8, .5, 10)
            p.root.location = (xx, 0, 0.02)
            p.root.rotation_euler = (0, 0, math.radians(-40 * (1 - place)))
            p.pose(t=t, walk=((t - c0) * 2.6) % 2 if t < c0 + .9 else 0, brow=.8, lid=.25, look=(.6, -.2), smile=.5 * place,
                   armL=80 if place < .5 else -50, armR=80 if place < .5 else -50, head=(0, nod))
            bpy.context.view_layer.update()
            top = p.head.matrix_world.translation + V(0, 0, 0.55)
            dest = V(2.0, 1.2, 0.63)
            pos = top.lerp(dest, place)
            self.phone.location = pos
            self.phone.rotation_euler = (0, 0, math.radians(90))
            self.hand.pose((0, 0, 0), visible=False)
            self.focus_on(p.head, (0.6, -5.8, 2.4), (0.7, 0.3, 0.9), 0.2, lens=34)
        elif shot == "c3":
            c0 = A["c3.start"]
            scan = math.sin((t - c0) * 5.2)
            swipe = pulse((t - c0) % .9, 0, .35, 25)
            p.root.location = (0, 0.4, 0.02)
            p.root.rotation_euler = (0, 0, 0)
            p.pose(t=t, lid=.25, brow=0, look=(0, .45 + .45 * scan), head=(0, 8), armR=-5 + swipe, armL=-10,
                   blink=blinks(t, 1.1))
            self.phone.location = (0, -0.35, 0.5)
            self.phone.rotation_euler = (math.radians(-80), 0, 0)
            PR.set_phone_glow(self.phone, 3.0)
            self.glow.data.energy = 60
            self.glow.location = (0, -0.28, 0.95)
            self.focus_on(p.head, (0.5, -4.2, 1.55), (0, 0.2, 1.0), 0.16, lens=45)
        else:
            c0 = A["c4.start"]
            flick = K(t, [(c0 + 1.5, 0), (c0 + 1.7, 1), (c0 + 2.3, 1), (c0 + 2.5, 0)])
            p.root.location = (0, 0.4, 0.02)
            p.pose(t=t, lid=.15 * (1 - flick), brow=-.8 * flick, mouth=self.talk("pip", t), head=(-6 * flick, 8 - 6 * flick),
                   look=(-1.6 * flick, .6 * (1 - flick) - .15 * flick), armR=-5, armL=-10, blink=pulse(t, c0 + 2.9, .25))
            if not hasattr(self, "drop"):
                self.drop = L.uv_sphere("sweat", 0.035, scale=(1, 1, 1.4), mat=PR.mats()["glass"], segs=16, rings=10)
            bpy.context.view_layer.update()
            dy = K(t, [(c0 + 1.9, 0), (c0 + 2.7, 1)])
            self.drop.hide_render = t < c0 + 1.8
            self.drop.location = p.head.matrix_world @ Vector((0.5, -0.45, 0.35 - 0.25 * dy))
            self.phone.location = (0, -0.35, 0.5)
            self.phone.rotation_euler = (math.radians(-80), 0, 0)
            PR.set_phone_glow(self.phone, 3.0)
            self.glow.data.energy = 60
            self.glow.location = (0, -0.28, 0.95)
            self.focus_on(p.eyes[0], (0.15, -2.2, 1.35), (0, 0.3, 1.2), 0.3, lens=55)


# ============================================================ 4. Social Battery Inspection
class SocialBattery(Base):
    def build(self, shot):
        self.lever = S.entry()
        self.p = Pip()
        self.p.add_clipboard() if shot == "c4" else None
        tex = os.path.join(os.environ.get("SIGN_DIR", "/tmp"), "closed_sign.png")
        PR.sign_texture(tex)
        self.sign = PR.sign("sign", tex, w=2.4, h=2.7)
        self.sign.location = (-1.75, -0.4, 0)
        self.legs, self.legl = PR.sneakers_and_legs()
        self.legs.location = (3.4, -0.8, 0)
        for i, lg in enumerate(self.legl):
            lg.location = ((-0.9 if i == 0 else 0.9), 0, 0)
        self.hand = PR.Hand()
        self.blanket = PR.blanket(size=(3.0, 2.0, 0.7), colors=("#3E8E8A", "#3E8E8A", "#2B6C68", "#E8DCC0"))
        self.blanket.location = (0, 0, -30)
        self.stamp = PR.rubber_stamp()
        self.stamp.location = (0, 0, -30)
        self.pencil = PR.pencil()
        self.pencil.location = (0, 0, -30)
        self.cam = L.camera((0, -10, 4), (0, 0, 3))

    def frame(self, shot, t):
        A, p = self.A, self.p
        sp = self.talk("pip", t)
        self.hand.pose((0, 0, 0), visible=False)
        if shot in ("c1", "c2"):
            c0 = A[shot + ".start"]
            p.root.location = (0.3, -0.6, 0)
            nod = pulse(t, A["c2.start"] + 1.5, .45, 14) if shot == "c2" else 0
            p.pose(t=t, brow=1.0, lid=.1, look=(.25, -.45), mouth=sp, armL=-25, armR=-25, head=(0, nod), blink=blinks(t, .6))
            if shot == "c1":
                jig = max(pulse(t, c0 + .2 + k * .16, .12, 1) for k in range(6))
                hin = K(t, [(c0 + .05, 0), (c0 + .25, 1), (c0 + 1.2, 1), (c0 + 1.5, 0)])
                self.lever.rotation_euler = (0, math.radians(-14 * jig), 0)
                if hin > 0.02:
                    self.hand.pose((4.2 + 1.8 * (1 - hin), 3.6, 9.2 + 0.2 * jig), direction=(-1, 0.3, 0.3), palm=(0, 0.6, -1), curl=0.6)
                for i, lg in enumerate(self.legl):
                    lg.location = ((-0.9 if i == 0 else 0.9), 0, max(0, math.sin(t * 7)) * 0.3 if i == 1 else 0)
            self.focus_on(p.head, (0.7, -11.0, 4.4), (0.7, 0, 4.0), 0.3, lens=30)
        elif shot == "c3":
            c0 = A["c3.start"]
            heel = pulse(t, c0 + .3, .5) * .6
            tap = pulse(t, c0 + 1.0, .5)
            for i, lg in enumerate(self.legl):
                lg.location = ((-0.9 if i == 0 else 0.9), K(t, [(c0, 0), (c0 + .6, -0.3)]) * (1 if i == 0 else 0),
                               (heel if i == 0 else tap) * 0.35)
            p.root.location = (1.9, -2.8, 0)
            p.root.rotation_euler = (0, 0, math.radians(-120))
            p.pose(t=t, brow=.6, look=(-.2, -.4), armL=-40, armR=-40)
            self.focus_on(V(3.4, -0.8, 1.0), (1.2, -8.5, 1.4), (3.0, 0, 1.6), 0.25, lens=40)
        elif shot == "c4":
            c0 = A["c4.start"]
            stamp_t = A["v4.end"] + .12
            p.root.location = (0, -0.6, 0)
            p.root.rotation_euler = (0, 0, 0)
            p.pose(t=t, brow=1.0, lid=.12, look=(0, .75), mouth=sp, armL=-30, armR=-30, head=(0, 16))
            scr = K(t, [(c0 + .1, 0), (c0 + 1.2, 1)])
            wob = math.sin(t * 22) * 0.12 * (1 if c0 + .1 < t < c0 + 1.2 else 0)
            bpy.context.view_layer.update()
            cb = p.clip.matrix_world.translation
            self.pencil.location = cb + V(0.2 + wob + 0.3 * scr, -0.25, 0.1)
            self.pencil.rotation_euler = (math.radians(-60), math.radians(25), 0)
            self.pencil.hide_render = t > stamp_t - 0.3
            if stamp_t - .35 < t < stamp_t + .6:
                press = K(t, [(stamp_t - .25, 0), (stamp_t, 1)]) if t < stamp_t + .05 else K(t, [(stamp_t + .05, 1), (stamp_t + .5, 0)])
                self.stamp.location = cb + V(0.1, -0.55 - 0.02, 0.0) + V(0, -0.9 * (1 - press), 0.2)
                self.stamp.rotation_euler = (math.radians(90 + 8), 0, 0)
            else:
                self.stamp.location = (0, 0, -30)
            self.focus_on(p.eyes[0], (0.2, -4.6, 2.9), (0, -0.6, 2.2), 0.2, lens=40)
        else:
            c0 = A["c5.start"]
            bx = K(t, [(c0 + .3, -3.0), (c0 + 1.6, 1.4)])
            self.blanket.location = (bx, -1.4, 0)
            self.blanket.rotation_euler = (0, 0, math.radians(8 * math.sin(t * 3)))
            push = K(t, [(c0 + .1, 0), (c0 + .6, 1), (c0 + 1.5, 0)])
            nod = pulse(t, c0 + 2.0, .5, 14)
            p.root.location = (K(t, [(c0 + .3, -5.8), (c0 + 1.6, -2.1)]), -1.4, 0)
            p.root.rotation_euler = (0, 0, math.radians(-70))
            p.pose(t=t, walk=((t - c0) * 2.6) % 2 if c0 + .3 < t < c0 + 1.6 else 0, brow=.6, lid=.2, look=(-.3, .2),
                   armL=10 * push - 20, armR=10 * push - 20, lean=.5 * push, head=(0, nod), smile=.4)
            self.focus_on(self.blanket, (0.6, -10.5, 3.2), (1.0, 0, 1.6), 0.3, lens=32)


# ============================================================ 5. The Comfort Hoard
class ComfortHoard(Base):
    CS = 0.55

    def build(self, shot):
        S.living()
        self.c = Crumb()
        self.c.root.scale = (self.CS,) * 3
        self.pile = L.empty("pile", (3.8, 0.4, 0))
        PR.blanket("pblanket", size=(3.2, 2.4, 0.9)).parent = self.pile
        m = PR.mug("pmug")
        PR.tea_in(m)
        m.parent = self.pile
        m.location = (0.8, 1.9, 0)
        m.scale = (0.9, 0.9, 0.9)
        tb = PR.tissues()
        tb.parent = self.pile
        tb.location = (-1.1, 1.9, 0)
        tb.scale = (0.9, 0.9, 0.9)
        self.slipper = PR.slipper()
        self.hand = PR.Hand()
        self.cam = L.camera((0, -7, 1.5), (0, 0, 0.6))

    def frame(self, shot, t):
        A, c = self.A, self.c
        sp = self.talk("crumb", t)
        self.hand.pose((0, 0, 0), visible=False)
        if shot == "c1":
            c0 = A["c1.start"]
            heave = [c0 + .35, c0 + .85, c0 + 1.4, c0 + 1.95, c0 + 2.45]
            prog = sum(K(t, [(h - .05, 0), (h + .3, 1)]) for h in heave) / 5
            hv = max([pulse(t, h, .32) for h in heave] + [0])
            sx = -2.2 + 1.2 * prog
            self.slipper.location = (sx, -0.6, 0)
            self.slipper.rotation_euler = (0, 0, math.radians(90))
            c.root.location = (sx + 1.9 + 0.08 * hv, -0.6, 0)
            c.root.rotation_euler = (0, 0, math.radians(-60))
            c.pose(t=t, lie=0.15, armL=5 + 25 * hv, armR=5 + 25 * hv, lid=.4 + .25 * hv, mouth=.6 * hv, tilt=-6 * hv,
                   look=(-.3, .2), head=(-6 * hv, 6), smile=-.5, wing=-.4, blink=.4 * hv)
            self.focus_on(c.eyes[0], (0.2, -7.8, 1.6), (0.3, 0, 0.8), 0.18, lens=45)
        elif shot == "c2":
            c0 = A["c2.start"]
            lift = K(t, [(c0 + 1.0, 0), (c0 + 1.9, 1)])
            hop = pulse(t, c0 + 1.1, .7, 0.4)
            sx = K(t, [(c0, 1.3), (c0 + 1.0, 1.9), (c0 + 1.9, 3.7)])
            self.slipper.location = (sx, 0.2, 0.9 * lift)
            self.slipper.rotation_euler = (0, math.radians(-8 * (1 - lift)), math.radians(90))
            c.root.location = (K(t, [(c0, 2.9), (c0 + 1.9, 2.3)]), -1.2, hop)
            c.root.rotation_euler = (0, 0, math.radians(20))
            c.pose(t=t, lie=0.1, armL=K(t, [(c0 + .8, -10), (c0 + 1.9, 60)]), armR=K(t, [(c0 + .8, -10), (c0 + 1.9, 60)]), lid=.15,
                   mouth=sp, look=(.3, -.4), head=(6, 0), smile=K(t, [(c0 + 2.2, 0), (c0 + 3.0, .8)]))
            self.focus_on(c.eyes[0], (1.8, -7.6, 2.4), (3.3, 0.2, 1.0), 0.2, lens=40)
        else:
            c0 = A[shot + ".start"]
            self.slipper.location = (3.7, 0.2, 0.9)
            self.slipper.rotation_euler = (0, 0, math.radians(90))
            c.root.location = (3.1, -0.2, 0.9)
            c.root.rotation_euler = (0, 0, math.radians(-10))
            if shot == "c3":
                pat = pulse(t, c0 + .7, .35) + pulse(t, c0 + 1.05, .35)
                c.pose(t=t, lie=0.0, armR=-60 + 50 * min(1, pat), armL=-60, lid=.08, mouth=sp, smile=.45,
                       look=(K(t, [(c0 + .6, .6), (c0 + 1.4, 0)]), K(t, [(c0 + .6, .4), (c0 + 1.4, -.45)])), head=(0, -8),
                       blink=blinks(t, .2))
            else:
                lean = K(t, [(c0 + 1.7, 0), (c0 + 2.4, 1)])
                c.pose(t=t, lie=0.0, armR=-60, armL=-60, lid=.05, happy=lean, smile=.9, tilt=6 * lean, look=(.5, -.2),
                       head=(12 * lean, 0), blink=0)
                hx = K(t, [(c0 + .2, 7.5), (c0 + 1.6, 3.0)])
                self.hand.pose((hx + 1.9, -0.25, 1.05), direction=(-1, 0.02, 0.0), palm=(0, 0, -1), curl=0.08)
            self.focus_on(c.eyes[0], (2.4, -4.4, 2.2), (3.2, 0, 1.45), 0.14, lens=45)


SCENES = {"01-heating-fee": HeatingFee, "02-phone-call": PhoneCall, "03-one-more-video": OneMoreVideo,
          "04-social-battery-inspection": SocialBattery, "05-comfort-hoard": ComfortHoard}
