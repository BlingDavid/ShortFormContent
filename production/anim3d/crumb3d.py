"""Crumb, the palm-sized cream dragon, as a posable 3D rig.

pose() takes the same keys as the 2D rig (look, blink, lid, happy, mouth, smile, armL/armR,
head, tilt, lie, wing, t, armor) so the scene timing code carries over.
"""
from __future__ import annotations

import math

from mathutils import Euler, Matrix, Quaternion, Vector

import lib3d as L


def lerp(a, b, t):
    return a + (b - a) * t


def vlerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


# ------------------------------------------------------------------ sculpted head
HEAD_R = (0.6, 0.52, 0.5)
EYE_DIRS = [Vector((s * 0.52, -0.8, 0.12)).normalized() for s in (-1, 1)]
BUMPS = [  # (direction, amplitude, angular width)
    (Vector((0, -1, -0.5)).normalized(), 0.26, 0.4),           # muzzle
    (Vector((0, -1, -0.95)).normalized(), 0.06, 0.35),         # chin
    (Vector((-0.78, -0.55, -0.42)).normalized(), 0.07, 0.4),   # cheeks
    (Vector((0.78, -0.55, -0.42)).normalized(), 0.07, 0.4),
    (Vector((0, -0.55, 0.8)).normalized(), 0.03, 0.5),         # brow dome
] + [(d, -0.06, 0.24) for d in EYE_DIRS]                        # eye sockets


def head_radius(d):
    x, y, z = d
    rx, ry, rz = HEAD_R
    base = 1.0 / math.sqrt((x / rx) ** 2 + (y / ry) ** 2 + (z / rz) ** 2)
    for bd, amp, w in BUMPS:
        ang = math.acos(max(-1.0, min(1.0, d.dot(bd))))
        base += amp * math.exp(-(ang / w) ** 2)
    return base


def head_point(d, out=0.0):
    d = Vector(d).normalized()
    return d * (head_radius(d) + out)


class Crumb:
    def __init__(self, name="Crumb", mats=None):
        m = mats or {}
        self.skin = m.get("skin") or L.mat_skin_scaly("crumb_skin")
        self.belly = m.get("belly") or L.mat_skin_scaly("crumb_belly", color="#F6F0D8", back="#EDE6C4", scale=22, sss=0.3)
        self.horn = L.mat_ridged("crumb_horn", "#B8561F", ridges=34)
        self.wingm = L.mat_membrane("crumb_wing", "#7F8C4B")
        self.spike = L.mat_plain("crumb_spike", "#7A8A48", rough=0.5, sss=0.2, sss_radius=(.5, 1, .3), sss_scale=0.02)
        self.claw = L.mat_plain("crumb_claw", "#3A2418", rough=0.3, coat=0.5)
        self.eye = L.mat_eye("crumb_eye")
        self.dark = L.mat_plain("crumb_mouth", "#4A2016", rough=0.6)
        self.glint = L.mat_emit("crumb_glint", "#FFFFFF", 6.0)
        self.blush = L.mat_plain("crumb_blush", "#F2A48C", rough=0.6, sss=0.4, sss_scale=0.02)
        self.cardboard = L.mat_plain("cardboard", "#B98B55", rough=0.85)
        self.tape = L.mat_plain("tape", "#E6D7A6", rough=0.3, coat=0.3)

        self.root = L.empty(name)
        self.body = L.Meta(name + "Bd", self.skin, parent=self.root, render_res=0.02)
        self.head = L.empty(name + "_head", parent=self.root)
        self.headmesh = self._head_mesh(name + "_skull")
        b = self.body
        for k in ("torso", "belly", "chest", "hipL", "hipR", "footL", "footR", "pawL", "pawR"):
            b.add(k, "ELLIPSOID", r=0.3)
        for i in range(9):
            b.add(f"tail{i}", r=0.2)
        # ear frills (pointing back/out) and horns
        self.ears, self.horns = [], []
        for s in (-1, 1):
            e = L.uv_sphere(f"{name}_ear{s}", 1.0, mat=self.skin, parent=self.head, segs=24, rings=12)
            e.location = head_point((s * 1, 0.25, 0.25), -0.05)
            e.scale = (0.2, 0.08, 0.1)
            e.rotation_euler = (0, math.radians(s * 20), math.radians(s * 35))
            self.ears.append(e)
            base = head_point((s * 0.5, 0.1, 0.85), -0.04)
            pts = L.catmull([base, base + Vector((s * .05, .04, .14)), base + Vector((s * .1, .18, .24)),
                             base + Vector((s * .13, .34, .2)), base + Vector((s * .12, .4, .06)),
                             base + Vector((s * .1, .33, -.02))], 7)
            radii = [0.13 * (1 - 0.86 * i / (len(pts) - 1)) + 0.01 for i in range(len(pts))]
            hn = L.sweep(f"{name}_horn{s}", pts, radii, self.horn, ring=18, parent=self.head)
            self.horns.append(hn)
        # eyes (gaze = local -Y), catchlights, lids
        self.eyes, self.lids, self.glints = [], [], []
        self.eye_r = 0.17
        for s in (-1, 1):
            d = EYE_DIRS[(s + 1) // 2]
            piv = L.empty(f"{name}_eyepiv{s}", head_point(d, -0.55 * self.eye_r), parent=self.head)
            piv.rotation_mode = "QUATERNION"
            piv.rotation_quaternion = (-d).to_track_quat("Y", "Z")
            ey = L.uv_sphere(f"{name}_eye{s}", self.eye_r, mat=self.eye, parent=piv)
            ey.rotation_mode = "XYZ"
            gl = L.uv_sphere(f"{name}_gl{s}", 0.03, loc=(-0.05 * s + 0.04, -self.eye_r * 0.93, 0.07), mat=self.glint,
                             parent=piv, segs=12, rings=8)
            gl.visible_shadow = False
            lid = self._lid(f"{name}_lid{s}", piv)
            r = self.eye_r
            arc = [(r * 0.85 * u, -r * 1.12 + 0.02 * r * u * u, r * (0.28 * (1 - u * u) - 0.05)) for u in [i / 10 - 1 for i in range(21)]]
            cr = L.sweep(f"{name}_crease{s}", arc, [0.012] + [0.022] * 19 + [0.012], self.claw, ring=8, parent=piv)
            self.creases = getattr(self, "creases", []) + [cr]
            self.eyes.append(ey)
            self.glints.append(gl)
            self.lids.append(lid)
        # nostrils, blush, mouth
        for s in (-1, 1):
            L.uv_sphere(f"{name}_nos{s}", 0.02, loc=head_point((s * 0.11, -1, -0.26), -0.006), scale=(1.2, .7, .8),
                        mat=self.dark, parent=self.head, segs=12, rings=8)
            bd = Vector((s * 0.72, -0.62, -0.3)).normalized()
            bl = L.uv_sphere(f"{name}_blush{s}", 0.09, loc=head_point(bd, -0.012), scale=(1.1, 1.1, .7), mat=self.blush,
                             parent=self.head, segs=16, rings=8)
            bl.rotation_mode = "QUATERNION"
            bl.rotation_quaternion = bd.to_track_quat("Y", "Z")
            bl.scale = (1.2, 0.25, 0.75)
        self.mouth = L.mesh_obj(f"{name}_mouth", [(0, 0, 0)], [], self.dark, parent=self.head)
        self.mouth_open = L.uv_sphere(f"{name}_mopen", 0.08, loc=head_point((0, -1, -0.7), -0.03), scale=(1.2, .5, 0.01), mat=self.dark,
                                      parent=self.head, segs=16, rings=8)
        # wings
        self.wings = []
        for s in (-1, 1):
            piv = L.empty(f"{name}_wpiv{s}", parent=self.root)
            w = self._wing(f"{name}_wing{s}", s, piv)
            self.wings.append((piv, w))
        # spikes along back ridge + tail, claws
        self.spikes = [L.sweep(f"{name}_sp{i}", [(0, 0, 0), (0, 0.02, 0.06), (0, 0.05, 0.1)], [0.045, 0.028, 0.005],
                               self.spike, ring=10, parent=self.root) for i in range(11)]
        self.claws = [L.sweep(f"{name}_cl{i}", [(0, 0, 0), (0, -0.03, -0.01), (0, -0.05, -0.04)], [0.022, 0.015, 0.003],
                              self.claw, ring=8, parent=self.root) for i in range(12)]
        self.armor = None

    # -------------------------------------------------------------------- parts
    def _head_mesh(self, name, seg=96, rings=64):
        verts, faces = [], []
        for i in range(rings + 1):
            th = math.pi * i / rings
            for k in range(seg):
                a = 2 * math.pi * k / seg
                d = Vector((math.sin(th) * math.cos(a), math.sin(th) * math.sin(a), math.cos(th)))
                verts.append(head_point(d))
        for i in range(rings):
            for k in range(seg):
                a, b = i * seg + k, i * seg + (k + 1) % seg
                faces.append((a, b, b + seg, a + seg))
        o = L.mesh_obj(name, verts, faces, self.skin, parent=self.head)
        sub = o.modifiers.new("sub", "SUBSURF")
        sub.levels, sub.render_levels = 0, 1
        return o

    def _lid(self, name, piv):
        r = self.eye_r * 1.07
        verts, faces = [], []
        seg, rings = 28, 10
        for i in range(rings + 1):
            th = math.pi / 2 * i / rings                 # hemisphere: +Z pole to equator
            for k in range(seg):
                a = 2 * math.pi * k / seg
                verts.append((r * math.sin(th) * math.cos(a), r * math.sin(th) * math.sin(a), r * math.cos(th)))
        for i in range(rings):
            for k in range(seg):
                a, b = i * seg + k, i * seg + (k + 1) % seg
                faces.append((a, b, b + seg, a + seg))
        o = L.mesh_obj(name, verts, faces, self.skin, parent=piv)
        o.rotation_mode = "XYZ"
        sol = o.modifiers.new("sol", "SOLIDIFY")
        sol.thickness = 0.012
        arc = [(r * 1.02 * math.cos(a), r * 1.02 * math.sin(a), 0.0)
               for a in [math.pi * (1.05 + 0.9 * i / 20) for i in range(21)]]
        L.sweep(name + "_lash", arc, [0.008] + [0.024] * 19 + [0.008], self.claw, ring=8, parent=o)
        return o

    def _wing(self, name, s, piv):
        """Flat bat wing in the XZ plane: arm bone up-out, three finger tips, scalloped trailing edge."""
        tips = [(0.55, 0.62), (0.78, 0.36), (0.74, 0.08)]
        pts = [(0.0, 0.0), (0.12, 0.3), (0.3, 0.52)]
        pts += [tips[0]]
        for a, b in zip(tips, tips[1:] + [(0.18, -0.08)]):
            mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            pts.append((mx - 0.08, mz - 0.02))
            pts.append(b)
        verts = [(s * x, 0.0, z) for x, z in pts]
        faces = [tuple(range(len(verts)))]
        o = L.mesh_obj(name, verts, faces, self.wingm, parent=piv, smooth=True)
        sol = o.modifiers.new("sol", "SOLIDIFY")
        sol.thickness = 0.018
        sub = o.modifiers.new("sub", "SUBSURF")
        sub.levels = sub.render_levels = 2
        for tx, tz in tips:                               # finger bones
            L.sweep(name + f"_b{tx}", [(0, 0, 0), (s * tx * 0.5, 0.004, tz * 0.55 + 0.05), (s * tx, 0.004, tz)],
                    [0.018, 0.013, 0.006], self.wingm, ring=10, parent=piv)
        return o

    def _mouth_mesh(self, smile, width=0.16):
        pts = []
        n = 14
        for i in range(n + 1):
            u = i / n * 2 - 1
            d = Vector((u * width * 1.6, -1, -0.62 + smile * 0.09 * (u * u) - smile * 0.03))
            pts.append(head_point(d, -0.004))
        return pts

    def add_armor(self):
        a = L.empty("armor", parent=self.root)
        plate = L.rounded_box("armor_plate", (0.72, 0.16, 0.6), 0.06, mat=self.cardboard, parent=a)
        L.rounded_box("armor_tape1", (0.12, 0.17, 0.62), 0.02, mat=self.tape, parent=a)
        L.rounded_box("armor_tape2", (0.74, 0.17, 0.1), 0.02, loc=(0, 0, 0.1), mat=self.tape, parent=a)
        for sx in (-1, 1):
            L.rounded_box(f"armor_pad{sx}", (0.28, 0.24, 0.12), 0.05, loc=(sx * 0.42, 0.06, 0.3), mat=self.cardboard, parent=a)
        self.armor = a
        return a

    # --------------------------------------------------------------------- pose
    def pose(self, **p):
        t = p.get("t", 0.0)
        lie = p.get("lie", 0.0)
        br = 1 + 0.015 * math.sin(t * 2.6)
        b = self.body
        # torso: lying loaf (lie=1) vs upright sitting (lie=0)
        b.set("torso", co=vlerp((0, 0.05, 0.68), (0, 0.1, 0.42), lie), r=1.0,
              size=(lerp(.55, .56, lie) * br, lerp(.5, .78, lie), lerp(.72, .42, lie) * br),
              rot=(lerp(-8, 0, lie), 0, 0))
        b.set("belly", co=vlerp((0, -0.14, 0.55), (0, -0.2, 0.34), lie), r=1.0, size=(.44 * br, .36, .44 * br))
        b.set("chest", co=vlerp((0, -0.18, 1.02), (0, -0.46, 0.62), lie), r=1.0, size=(.4, .34, .36))
        for s, k in ((-1, "hipL"), (1, "hipR")):
            b.set(k, co=vlerp((s * 0.36, 0.12, 0.34), (s * 0.4, 0.45, 0.3), lie), r=1.0, size=(.28, .36, .3))
        for s, k in ((-1, "footL"), (1, "footR")):
            b.set(k, co=vlerp((s * 0.33, -0.3, 0.09), (s * 0.5, 0.2, 0.09), lie), r=1.0, size=(.15, .22, .1))
        # arms / front paws: angle >0 raises the paw (degrees), default rests forward on the ground
        paws = {}
        for s, key, pk in ((-1, "armL", "pawL"), (1, "armR", "pawR")):
            ang = p.get(key, -70)
            sh = vlerp((s * 0.36, -0.28, 0.9), (s * 0.3, -0.52, 0.48), lie)
            reach = 0.5 + 0.25 * max(0, ang) / 90
            a = math.radians(ang)
            fwd = Vector((s * 0.12, -math.cos(a) * 0.55 - 0.45 * max(0, math.sin(a)) * 0.2, math.sin(a)))
            end = sh + fwd.normalized() * reach
            end.z = max(end.z, 0.08)
            b.capsule("arm" + pk, sh, end, 0.1)
            b.set(pk, co=end, r=1.0, size=(.15, .19, .11))
            paws[pk] = (end, fwd.normalized())
        # tail: curls around the front-left (viewer's left = -X)
        tw = p.get("tail", 0.0) + 0.06 * math.sin(t * 1.3)
        if lie > 0.5:
            ctrl = [(0.15, 0.75, 0.3), (-0.45, 0.75, 0.2), (-0.78, 0.3, 0.13), (-0.72, -0.3, 0.1), (-0.4, -0.72 + tw * .1, 0.09)]
        else:
            ctrl = [(0.1, 0.45, 0.25), (-0.4, 0.55, 0.14), (-0.75, 0.2, 0.1), (-0.72, -0.3, 0.09), (-0.45, -0.6 + tw * .1, 0.08)]
        tail = L.catmull(ctrl, 3)
        idx = [round(i * (len(tail) - 1) / 8) for i in range(9)]
        for i, j in enumerate(idx):
            b.set(f"tail{i}", co=tail[j], r=0.06)
            if i:
                b.capsule(f"tseg{i}", tail[idx[i - 1]], tail[j], 0.19 - 0.13 * i / 8)
        # head transform
        hx, hy = p.get("head", (0, 0))
        neck = vlerp((0, -0.2, 1.3), (0, -0.62, 0.86), lie)
        yaw = math.radians(-hx * 1.2)
        pitch = math.radians(hy * 1.1)
        roll = math.radians(p.get("tilt", 0.0) * 2.2)
        M = Matrix.Translation(neck) @ Euler((pitch, roll, yaw), "YXZ").to_matrix().to_4x4() @ Matrix.Translation((0, -0.06, 0.34))
        self.head.matrix_basis = M
        # spikes: back ridge + tail
        ridge = L.catmull([neck + Vector((0, 0.18, 0.1)), vlerp((0, 0.22, 1.1), (0, 0.05, 0.84), lie),
                           vlerp((0, 0.42, 0.78), (0, 0.5, 0.74), lie), vlerp((0, 0.5, 0.45), (0, 0.8, 0.46), lie)], 3)
        spots = [ridge[round(i * (len(ridge) - 1) / 5)] for i in range(1, 6)] + [tail[j] for j in idx[1:7]]
        for sp, pos in zip(self.spikes, spots):
            sp.location = pos + Vector((0, 0, 0.08 if sp is not self.spikes[0] else 0.1))
            sc = 1.3 if sp in self.spikes[:5] else 1.0 - 0.1 * self.spikes.index(sp) / 11
            sp.scale = (sc, sc, sc)
            sp.rotation_euler = (math.radians(-25), 0, 0)
        # claws on feet + paws
        spots = []
        for s, k in ((-1, "footL"), (1, "footR")):
            c = b.el[k].co
            spots += [Vector((c.x + d * 0.08, c.y - 0.25, 0.05)) for d in (-1, 0, 1)]
        for pk in ("pawL", "pawR"):
            e, f = paws[pk]
            side = f.cross(Vector((0, 0, 1)))
            side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
            spots += [e + f * 0.17 + side * d * 0.07 + Vector((0, 0, -0.03)) for d in (-1, 0, 1)]
        for cl, pos in zip(self.claws, spots):
            cl.location = pos
        # wings: behind the shoulders, spread slightly; `wing` in [-1.5, 1.5] folds/flares
        fl = p.get("wing", 0.0) + 0.12 * math.sin(t * 3.1)
        for s, (piv, w) in zip((-1, 1), self.wings):
            piv.location = vlerp((s * 0.3, 0.25, 1.0), (s * 0.28, 0.22, 0.74), lie)
            piv.rotation_euler = (math.radians(-18), math.radians(s * (-8 - 14 * fl)), math.radians(s * (28 + 12 * fl)))
            sc = 1.25
            piv.scale = (sc, sc, sc)
        # face
        look = p.get("look", (0.0, 0.0))
        blink = p.get("blink", 0.0)
        lid = p.get("lid", 0.0)
        happy = p.get("happy", 0.0)
        for s, ey, ld in zip((-1, 1), self.eyes, self.lids):
            ey.rotation_euler = (math.radians(look[1] * -24), 0, math.radians(-look[0] * 24))
            close = max(lid, blink, happy)
            ld.rotation_euler = (math.radians(lerp(-96, 86, close)), 0, 0)
            ld.scale = (1, 1, 1)
        shut = max(blink, happy) > 0.6
        for gl in self.glints:
            gl.hide_render = shut
        for cr in self.creases:
            cr.hide_render = not shut
        mo = p.get("mouth", 0.0)
        sm = p.get("smile", 0.35) if happy < 0.5 else 0.9
        pts = self._mouth_mesh(sm)
        verts, faces = [], []
        ring = 8
        for i, c in enumerate(pts):
            for k in range(ring):
                a = 2 * math.pi * k / ring
                verts.append(c + Vector((0, math.cos(a) * 0.01, math.sin(a) * 0.012)))
        for i in range(len(pts) - 1):
            for k in range(ring):
                aa, bb = i * ring + k, i * ring + (k + 1) % ring
                faces.append((aa, bb, bb + ring, aa + ring))
        L.replace_mesh(self.mouth, verts, faces)
        self.mouth_open.scale = (1.2 + 0.2 * mo, .5, max(0.01, 1.0 * mo))
        self.mouth_open.hide_render = mo < 0.08
        if self.armor is not None:
            self.armor.location = vlerp((0, -0.74, 0.74), (0, -0.8, 0.5), lie)
            self.armor.rotation_euler = (math.radians(lerp(-8, 10, lie)), 0, 0)
