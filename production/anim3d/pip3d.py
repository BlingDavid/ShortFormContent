"""Pip, the small round duck in a cobalt raincoat and red boots, as a posable 3D rig.

Pose keys mirror the 2D rig: look, blink, lid, happy, mouth, brow, armL/armR (deg, +up),
head (dx, dy), tilt, walk (0..2 cycle), lean, t, smile.
"""
from __future__ import annotations

import math

from mathutils import Euler, Matrix, Vector

import lib3d as L


def lerp(a, b, t):
    return a + (b - a) * t


class Pip:
    def __init__(self, name="Pip"):
        self.fluff = L.mat_plain("pip_fluff", "#F4CF4A", rough=0.7, sheen=0.9, sheen_rough=0.35, sheen_tint="#FFF3B0",
                                 sss=0.2, sss_radius=(1, .8, .3), sss_scale=0.03)
        self.bill = L.mat_plain("pip_bill", "#F08A24", rough=0.35, coat=0.3, sss=0.2, sss_scale=0.02)
        self.coat = L.mat_plain("pip_coat", "#1E4FC8", rough=0.28, coat=0.6, coat_rough=0.12, spec=0.6)
        self.boot = L.mat_plain("pip_boot", "#D0161E", rough=0.2, coat=0.8, coat_rough=0.05, spec=0.6)
        self.sole = L.mat_plain("pip_sole", "#2A1414", rough=0.6)
        self.button = L.mat_plain("pip_button", "#F5D15A", rough=0.3, coat=0.5)
        self.eye = L.mat_eye("pip_eye", iris="#1A120C", pupil="#050303", ring="#0A0604", mid="#3A2A1E")
        self.glint = L.mat_emit("pip_glint", "#FFFFFF", 6.0)
        self.dark = L.mat_plain("pip_dark", "#5A3A10", rough=0.6)
        self.mouthm = L.mat_plain("pip_mouth", "#6A2210", rough=0.6)
        self.blush = L.mat_plain("pip_blush", "#F29A6A", rough=0.6)
        self.wood = L.mat_wood("clip_wood", "#C08A55", "#9A6A3C", 6)
        self.paper = L.mat_plain("paper", "#FBFAF4", rough=0.8)
        self.metal = L.mat_plain("metal", "#B8BCC4", rough=0.25, metal=1.0)

        self.root = L.empty(name)
        self.coatm = L.Meta(name + "Ct", self.coat, parent=self.root, render_res=0.02)
        c = self.coatm
        c.add("body", "ELLIPSOID", r=1.0, size=(.7, .62, .74))
        c.add("hem", "ELLIPSOID", r=1.0, size=(.74, .66, .3))
        self.bootm = L.Meta(name + "Bt", self.boot, parent=self.root, render_res=0.015)
        for s in ("L", "R"):
            self.bootm.add("shaft" + s, "ELLIPSOID", r=1.0, size=(.22, .22, .34))
            self.bootm.add("toe" + s, "ELLIPSOID", r=1.0, size=(.24, .34, .17))
        self.soles = [L.rounded_box(f"{name}_sole{s}", (0.42, 0.62, 0.05), 0.02, mat=self.sole, parent=self.root) for s in "LR"]
        self.buttons = [L.uv_sphere(f"{name}_btn{i}", 0.055, scale=(1, .5, 1), mat=self.button, parent=self.root, segs=16, rings=8)
                        for i in range(3)]
        self.collar = L.sweep(f"{name}_collar", [(0.6 * math.cos(a), 0.55 * math.sin(a), 0) for a in
                                                 [2 * math.pi * i / 32 for i in range(33)]],
                              [0.09] * 33, self.coat, ring=12, parent=self.root, cap_tip=False)
        self.hands = [L.uv_sphere(f"{name}_hand{s}", 0.16, scale=(1, .8, .9), mat=self.fluff, parent=self.root, segs=24, rings=12)
                      for s in "LR"]
        # head
        self.head = L.empty(name + "_head", parent=self.root)
        L.uv_sphere(name + "_skull", 0.62, scale=(1.05, 0.98, 0.95), mat=self.fluff, parent=self.head)
        for k, (x, z, rz) in enumerate([(0, .6, 0), (.07, .58, -25), (-.07, .58, 25)]):
            f = L.sweep(f"{name}_tuft{k}", [(0, 0, 0), (0, 0, 0.12), (x * .6, 0, 0.22)], [0.07, 0.05, 0.01], self.fluff,
                        ring=10, parent=self.head)
            f.location = (x, 0.02, z)
            f.rotation_euler = (0, math.radians(rz), 0)
        self.upper = L.uv_sphere(name + "_billU", 0.3, loc=(0, -0.62, -0.1), scale=(1.15, 0.72, 0.36), mat=self.bill,
                                 parent=self.head)
        self.lower = L.uv_sphere(name + "_billL", 0.26, loc=(0, -0.56, -0.2), scale=(1.05, 0.66, 0.26), mat=self.bill,
                                 parent=self.head)
        self.mouth_in = L.uv_sphere(name + "_mouthin", 0.22, loc=(0, -0.55, -0.16), scale=(1, .6, .2), mat=self.mouthm,
                                    parent=self.head, segs=20, rings=10)
        for s in (-1, 1):
            L.uv_sphere(f"{name}_nos{s}", 0.022, loc=(s * 0.09, -0.86, -0.02), scale=(1.2, .6, .6), mat=self.dark,
                        parent=self.head, segs=10, rings=6)
            b = L.uv_sphere(f"{name}_blush{s}", 0.1, loc=(s * 0.45, -0.38, -0.12), scale=(1, .3, .6), mat=self.blush,
                            parent=self.head, segs=16, rings=8)
            b.rotation_euler = (0, 0, math.radians(-s * 42))
        self.eyes, self.lids, self.glints, self.brows = [], [], [], []
        er = 0.15
        self.eye_r = er
        for s in (-1, 1):
            d = Vector((s * 0.46, -0.84, 0.2)).normalized()
            piv = L.empty(f"{name}_eyepiv{s}", d * (0.6 - 0.45 * er), parent=self.head)
            piv.rotation_mode = "QUATERNION"
            piv.rotation_quaternion = (-d).to_track_quat("Y", "Z")
            ey = L.uv_sphere(f"{name}_eye{s}", er, mat=self.eye, parent=piv)
            ey.rotation_mode = "XYZ"
            gl = L.uv_sphere(f"{name}_gl{s}", 0.028, loc=(-0.04 * s + 0.04, -er * 0.93, 0.06), mat=self.glint, parent=piv,
                             segs=12, rings=8)
            gl.visible_shadow = False
            lid = self._lid(f"{name}_lid{s}", piv, er)
            brow = L.sweep(f"{name}_brow{s}", [(-0.09, 0, 0), (0, 0, 0.012), (0.09, 0, 0)], [0.022, 0.026, 0.02], self.dark,
                           ring=10, parent=self.head)
            brow.location = (s * 0.3, -0.56, 0.36)
            brow.rotation_mode = "XYZ"
            self.eyes.append(ey)
            self.glints.append(gl)
            self.lids.append(lid)
            self.brows.append(brow)
        self.clip = None

    def _lid(self, name, piv, er):
        r = er * 1.08
        verts, faces = [], []
        seg, rings = 28, 10
        for i in range(rings + 1):
            th = math.pi / 2 * i / rings
            for k in range(seg):
                a = 2 * math.pi * k / seg
                verts.append((r * math.sin(th) * math.cos(a), r * math.sin(th) * math.sin(a), r * math.cos(th)))
        for i in range(rings):
            for k in range(seg):
                a, b = i * seg + k, i * seg + (k + 1) % seg
                faces.append((a, b, b + seg, a + seg))
        o = L.mesh_obj(name, verts, faces, self.fluff, parent=piv)
        o.rotation_mode = "XYZ"
        o.modifiers.new("sol", "SOLIDIFY").thickness = 0.012
        return o

    def add_clipboard(self):
        g = L.empty("clipboard", parent=self.root)
        L.rounded_box("clip_board", (0.9, 0.05, 1.2), 0.04, mat=self.wood, parent=g)
        L.rounded_box("clip_paper", (0.78, 0.06, 1.0), 0.005, loc=(0, -0.01, -0.06), mat=self.paper, parent=g)
        L.rounded_box("clip_clip", (0.36, 0.1, 0.16), 0.03, loc=(0, -0.03, 0.56), mat=self.metal, parent=g)
        self.clip = g
        return g

    def pose(self, **p):
        t = p.get("t", 0.0)
        walk = p.get("walk", 0.0)
        lean = p.get("lean", 0.0)
        br = 1 + 0.012 * math.sin(t * 2.4)
        bob = abs(math.sin(walk * math.pi)) * 0.08
        c = self.coatm
        base = Vector((0, lean * 0.15, 0.62 + bob))
        c.set("body", co=base + Vector((0, 0, 0.62)), size=(.7 * br, .62, .74 * br), rot=(-lean * 10, 0, 0))
        c.set("hem", co=base + Vector((0, 0, 0.12)), size=(.74, .66, .3))
        for i, bt in enumerate(self.buttons):
            bt.location = base + Vector((0, -0.66 - 0.02 * i, 1.0 - 0.28 * i))
            bt.rotation_euler = (math.radians(-10 * i), 0, 0)
        self.collar.location = base + Vector((0, -0.02, 1.3))
        for k, s in enumerate(("L", "R")):
            sx = -1 if s == "L" else 1
            lift = max(0, math.sin(walk * math.pi + (0 if s == "L" else math.pi))) * 0.18
            fx = sx * 0.3
            self.bootm.set("shaft" + s, co=(fx, 0.02, 0.38 + lift))
            self.bootm.set("toe" + s, co=(fx, -0.18, 0.15 + lift))
            self.soles[k].location = (fx, -0.1, 0.02 + lift)
        for side, key, hand in ((-1, "armL", self.hands[0]), (1, "armR", self.hands[1])):
            ang = math.radians(p.get(key, -55))
            sh = base + Vector((side * 0.6, -0.05, 1.05))
            fwd = Vector((side * math.cos(ang) * 0.55, -0.45 - 0.2 * max(0, math.sin(ang)), math.sin(ang)))
            end = sh + fwd.normalized() * 0.62
            c.capsule("sleeve" + key, sh, end, 0.15)
            hand.location = end + fwd.normalized() * 0.12
        hx, hy = p.get("head", (0, 0))
        M = (Matrix.Translation(base + Vector((0, -0.02, 1.62))) @
             Euler((math.radians(hy * 1.1), math.radians(p.get("tilt", 0) * 2.2), math.radians(-hx * 1.2)), "YXZ").to_matrix().to_4x4()
             @ Matrix.Translation((0, 0, 0.3)))
        self.head.matrix_basis = M
        look = p.get("look", (0, 0))
        close = max(p.get("lid", 0.0), p.get("blink", 0.0), p.get("happy", 0.0))
        for ey, ld in zip(self.eyes, self.lids):
            ey.rotation_euler = (math.radians(look[1] * -24), 0, math.radians(-look[0] * 24))
            ld.rotation_euler = (math.radians(lerp(-96, 86, close)), 0, 0)
        for gl in self.glints:
            gl.hide_render = max(p.get("blink", 0), p.get("happy", 0)) > 0.6
        brow = p.get("brow", 0.0)          # +1 stern (inner ends down), -1 worried
        for s, bw in zip((-1, 1), self.brows):
            bw.rotation_euler = (0, math.radians(-s * 22 * brow), 0)
            bw.location = (s * 0.3, -0.57, 0.38 + 0.03 * (1 - abs(brow)) - 0.02 * max(0, brow))
        mo = p.get("mouth", 0.0)
        self.lower.location = (0, -0.56, -0.2 - 0.1 * mo)
        self.lower.rotation_euler = (math.radians(12 * mo), 0, 0)
        self.mouth_in.hide_render = mo < 0.08
        if self.clip is not None:
            self.clip.location = base + Vector((0, -0.85, 0.85))
            self.clip.rotation_euler = (math.radians(-8), 0, 0)
