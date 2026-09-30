"""Props: human hand/face, glass, phone, mug, slipper, blanket, tissues, pencil, stamp, sign, sneakers."""
from __future__ import annotations

import math

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

import lib3d as L

_M = {}


def mats():
    if not _M:
        _M["skin"] = L.mat_plain("human_skin", "#E2A887", rough=0.5, sss=0.35, sss_radius=(1.0, 0.45, 0.25), sss_scale=0.08,
                                 spec=0.4)
        _M["sleeve"] = L.mat_stripes("sleeve", ["#556B4A", "#4C6142"], scale=1.0, knit_scale=40, bump=0.9)
        _M["lip"] = L.mat_plain("lip", "#C45E66", rough=0.35, sss=0.3, sss_scale=0.05, coat=0.3)
        _M["nail"] = L.mat_plain("nail", "#EAB8A6", rough=0.2, coat=0.6)
        _M["glass"] = L.mat_glass("glass", "#F4FAFF")
        _M["tea"] = L.mat_glass("tea", "#D89436", clarity=0.35)
        _M["phone"] = L.mat_plain("phone", "#15161B", rough=0.25, coat=0.7, coat_rough=0.05, metal=0.2)
        _M["screen_off"] = L.mat_plain("screen_off", "#08090C", rough=0.05, coat=1.0, coat_rough=0.0)
        _M["ceramic"] = L.mat_plain("ceramic", "#F2EDE3", rough=0.18, coat=0.8, coat_rough=0.05)
        _M["denim"] = L.mat_fabric("denim", "#3E5E8E", scale=90, bump=0.5, alt="#4A6FA3")
        _M["sneaker"] = L.mat_plain("sneaker", "#F4F4F1", rough=0.55, sheen=0.3)
        _M["rubber"] = L.mat_plain("rubber", "#DADAD4", rough=0.7)
    return _M


class Hand:
    """Stylised human hand (metaball fingers) + knit sleeve. Wrist at `wrist`; fingers point along `dir`."""

    def __init__(self, name="Hand", sleeve=True):
        m = mats()
        self.root = L.empty(name)
        self.mb = L.Meta(name + "Mb", m["skin"], parent=self.root, render_res=0.03)
        self.mb.add("palm", "ELLIPSOID", r=1.0, size=(0.42, 0.18, 0.46))
        self.mb.add("wrist", "ELLIPSOID", r=1.0, size=(0.34, 0.22, 0.4))
        self.sleeve = None
        if sleeve:
            self.sleeve = L.cylinder(name + "_sleeve", 0.52, 5.0, mat=m["sleeve"], parent=self.root, segs=32)
        self.nails = [L.uv_sphere(f"{name}_nail{i}", 0.07, scale=(1, .45, 1.2), mat=m["nail"], parent=self.root, segs=12, rings=8)
                      for i in range(5)]

    def pose(self, wrist, direction=(0, 0, 1), palm=(0, -1, 0), curl=0.0, point=False, spread=0.0, visible=True):
        """curl 0 open .. 1 fist; point keeps the index straight."""
        self.root.hide_render = not visible
        for ch in self.root.children:
            ch.hide_render = not visible
        if not visible:
            return
        W = Vector(wrist)
        up = Vector(direction).normalized()
        nrm = Vector(palm).normalized()
        side = up.cross(nrm).normalized()
        nrm = side.cross(up).normalized()
        R = Matrix((side, nrm, up)).transposed()           # local x=side, y=palm normal, z=finger direction

        def P(x, y, z):
            return W + R @ Vector((x, y, z))

        mb = self.mb
        mb.set("wrist", co=P(0, 0, 0.1), rot=R.to_quaternion())
        mb.set("palm", co=P(0, 0, 0.62), rot=R.to_quaternion())
        fingers = [(-0.3, 0.72), (-0.1, 0.8), (0.1, 0.76), (0.28, 0.6)]
        for i, (fx, ln) in enumerate(fingers):
            c = 0.0 if (point and i == 1) else curl
            base = P(fx * (1 + spread * .3), 0, 1.02)
            seg = ln / 3
            d = Vector((0, 0, 1))
            pts = [base]
            ang = 0.0
            for k in range(3):
                ang += c * 1.25
                d = Vector((0, -math.sin(ang), math.cos(ang)))
                pts.append(pts[-1] + R @ (d * seg))
            for k in range(3):
                mb.capsule(f"f{i}{k}", pts[k], pts[k + 1], 0.105 - 0.012 * k)
            self.nails[i].location = pts[-1] + R @ Vector((0, 0.06, -0.06))
            self.nails[i].rotation_mode = "QUATERNION"
            self.nails[i].rotation_quaternion = R.to_quaternion()
        tb = P(-0.4, -0.08, 0.35)
        td = R @ Vector((-0.5, -0.5 - curl * 0.6, 0.7)).normalized()
        t1 = tb + td * 0.3
        t2 = t1 + (R @ Vector((0.2 * curl, -0.4, 0.6)).normalized()) * 0.28
        mb.capsule("t0", tb, t1, 0.12)
        mb.capsule("t1", t1, t2, 0.105)
        self.nails[4].location = t2 + R @ Vector((0, 0.05, 0))
        if self.sleeve:
            self.sleeve.rotation_mode = "QUATERNION"
            self.sleeve.rotation_quaternion = up.to_track_quat("Z", "Y")
            self.sleeve.location = W - up * 2.55


class Face:
    """Lower half of a human face (chin, lips, nose tip) leaning in for the forehead kiss.

    Modelled facing -Y with +Z up, then tilted forward so the lips lead."""

    LIP = Vector((0, -0.52, 0.3))
    TILT = 38.0

    def __init__(self, name="Face"):
        m = mats()
        self.root = L.empty(name)
        self.root.rotation_euler = (math.radians(self.TILT), 0, math.radians(-90))
        self.mb = L.Meta(name + "Mb", m["skin"], parent=self.root, render_res=0.03)
        self.mb.add("mass", "ELLIPSOID", co=(0, 0.05, 0.95), r=1.0, size=(0.72, 0.5, 0.95))
        self.mb.add("chin", "ELLIPSOID", co=(0, -0.3, 0.05), r=1.0, size=(0.3, 0.26, 0.22))
        self.mb.add("muzzle", "ELLIPSOID", co=(0, -0.32, 0.42), r=1.0, size=(0.42, 0.26, 0.34))
        self.mb.add("nose", "ELLIPSOID", co=(0, -0.55, 0.92), r=1.0, size=(0.16, 0.18, 0.2))
        for s in (-1, 1):
            self.mb.add(f"cheek{s}", "ELLIPSOID", co=(s * 0.42, -0.2, 0.8), r=1.0, size=(0.26, 0.24, 0.26))
        self.lu = L.uv_sphere(name + "_lipU", 0.2, loc=(0, -0.53, 0.36), scale=(1.1, .5, .38), mat=m["lip"], parent=self.root)
        self.ll = L.uv_sphere(name + "_lipL", 0.19, loc=(0, -0.5, 0.22), scale=(1.0, .5, .42), mat=m["lip"], parent=self.root)

    def pose(self, lip_world, pucker=0.5, visible=True):
        R = self.root.rotation_euler.to_matrix()
        self.root.location = Vector(lip_world) - R @ self.LIP
        for o in [self.mb.obj, self.lu, self.ll]:
            o.hide_render = not visible
        s = 1 - 0.25 * pucker
        self.lu.scale = (1.1 * s, .5 + .15 * pucker, .38 + .1 * pucker)
        self.ll.scale = (1.0 * s, .5 + .15 * pucker, .42 + .1 * pucker)


def glass(name="Glass", parent=None):
    m = mats()
    g = L.empty(name, parent=parent)
    L.cylinder(name + "_outer", 0.36, 1.2, loc=(0, 0, 0.6), mat=m["glass"], parent=g, segs=48, r_top=0.4)
    L.cylinder(name + "_tea", 0.33, 0.8, loc=(0, 0, 0.42), mat=m["tea"], parent=g, segs=48, r_top=0.35)
    return g


def phone(name="Phone", w=0.75, h=1.55, screen="#0A0B10", glow=0.0, parent=None):
    """Smartphone lying on its back (screen up, +Z). Blank screen only; `glow` makes it emissive."""
    m = mats()
    g = L.empty(name, parent=parent)
    L.rounded_box(name + "_body", (w, h, 0.08), 0.035, loc=(0, 0, 0.04), mat=m["phone"], parent=g)
    scr = L.mat_plain(name + "_screen", screen, rough=0.04, coat=1.0, coat_rough=0.0, emit=screen, emit_str=0.0)
    s = L.rounded_box(name + "_scr", (w - 0.06, h - 0.06, 0.01), 0.05, loc=(0, 0, 0.083), mat=scr, parent=g)
    L.uv_sphere(name + "_cam", 0.018, loc=(0, h / 2 - 0.07, 0.086), mat=m["screen_off"], parent=g, segs=12, rings=6)
    g["screen_mat"] = scr.name
    return g


def set_phone_glow(g, strength, color=(0.72, 0.84, 1.0)):
    mat = bpy.data.materials[g["screen_mat"]]
    p = mat.node_tree.nodes["Principled BSDF"]
    p.inputs["Emission Color"].default_value = (*color, 1)
    p.inputs["Emission Strength"].default_value = strength


def mug(name="Mug", parent=None, color=None):
    m = mats()
    mat = m["ceramic"] if color is None else L.mat_plain(name + "_mat", color, rough=0.18, coat=0.8, coat_rough=0.05)
    g = L.empty(name, parent=parent)
    outer = L.cylinder(name + "_o", 0.48, 1.0, loc=(0, 0, 0.5), mat=mat, parent=g, segs=48)
    sol = outer.modifiers.new("bev", "BEVEL")
    sol.width, sol.segments, sol.limit_method = 0.05, 4, "ANGLE"
    L.cylinder(name + "_in", 0.42, 0.02, loc=(0, 0, 0.97), mat=L.mat_plain(name + "_rim", "#E2DBCF", 0.3), parent=g, segs=48)
    L.sweep(name + "_h", [(0.46, 0, 0.8), (0.72, 0, 0.72), (0.76, 0, 0.45), (0.62, 0, 0.26), (0.46, 0, 0.24)],
            [0.06] * 5, mat, ring=14, parent=g, cap_tip=False)
    return g


def tea_in(g, name="MugTea"):
    L.cylinder(name, 0.42, 0.02, loc=(0, 0, 0.9), mat=L.mat_plain(name + "_m", "#6E3A14", 0.05, coat=1.0), parent=g, segs=48)


def slipper(name="Slipper", parent=None):
    fuzz = L.mat_plain("slipper_fuzz", "#8FAFD6", rough=0.9, sheen=1.0, sheen_rough=0.3, sheen_tint="#DDEBFF")
    sole = L.mat_plain("slipper_sole", "#E6DAC4", rough=0.7)
    g = L.empty(name, parent=parent)
    mb = L.Meta(name + "Mb", fuzz, parent=g, render_res=0.04)
    mb.add("toe", "ELLIPSOID", co=(0, -0.7, 0.35), r=1.0, size=(0.55, 0.75, 0.38))
    mb.add("mid", "ELLIPSOID", co=(0, 0.2, 0.22), r=1.0, size=(0.52, 0.8, 0.24))
    mb.add("heel", "ELLIPSOID", co=(0, 0.95, 0.28), r=1.0, size=(0.48, 0.4, 0.3))
    mb.add("hole", "ELLIPSOID", co=(0, 0.45, 0.52), r=1.0, size=(0.4, 0.55, 0.2), neg=True)
    L.rounded_box(name + "_sole", (1.1, 2.7, 0.16), 0.08, loc=(0, 0.1, 0.08), mat=sole, parent=g)
    return g


def blanket(name="Blanket", size=(3.2, 2.2, 0.7), colors=("#E0A23A", "#E0A23A", "#C97F22"), parent=None):
    m = L.mat_stripes(name + "_knit", list(colors), scale=2.0, axis="X", knit_scale=45, bump=0.8)
    g = L.empty(name, parent=parent)
    sx, sy, sz = size
    for i in range(3):
        L.rounded_box(f"{name}_{i}", (sx, sy, sz / 3 + 0.02), 0.12, loc=(0, 0, sz / 6 + i * sz / 3.2), mat=m, parent=g)
    return g


def tissues(name="Tissues", parent=None):
    box = L.mat_plain("tissue_box", "#8FC0E4", rough=0.5)
    paper = L.mat_plain("tissue", "#FFFFFF", rough=0.9, sss=0.3, sss_scale=0.05)
    g = L.empty(name, parent=parent)
    L.rounded_box(name + "_box", (1.3, 1.3, 1.1), 0.08, loc=(0, 0, 0.55), mat=box, parent=g)
    L.rounded_box(name + "_slot", (0.7, 0.2, 0.05), 0.04, loc=(0, 0, 1.1), mat=L.mat_plain("slot", "#2E5F86", 0.6), parent=g)
    t = L.uv_sphere(name + "_t", 0.3, loc=(0, 0, 1.35), scale=(1.3, .25, 1.1), mat=paper, parent=g)
    t.rotation_euler = (0, math.radians(15), 0)
    return g


def sneakers_and_legs(name="Legs", parent=None):
    m = mats()
    g = L.empty(name, parent=parent)
    legs = []
    for s in (-1, 1):
        leg = L.empty(f"{name}_{s}", parent=g)
        L.cylinder(f"{name}_jean{s}", 0.62, 24.0, loc=(0, 0.15, 12.5), mat=m["denim"], parent=leg, segs=32, r_top=0.8)
        L.cylinder(f"{name}_cuff{s}", 0.66, 0.35, loc=(0, 0.15, 0.62), mat=m["denim"], parent=leg, segs=32)
        mb = L.Meta(f"{name}Shoe{s}", m["sneaker"], parent=leg, render_res=0.04)
        mb.add("toe", "ELLIPSOID", co=(0, -0.9, 0.3), r=1.0, size=(0.55, 0.75, 0.32))
        mb.add("heel", "ELLIPSOID", co=(0, 0.3, 0.42), r=1.0, size=(0.55, 0.62, 0.45))
        L.rounded_box(f"{name}_sole{s}", (1.12, 2.5, 0.2), 0.08, loc=(0, -0.3, 0.1), mat=m["rubber"], parent=leg)
        legs.append(leg)
    return g, legs


def sign_texture(path, text="CLOSED", size=(1024, 1152)):
    from PIL import Image, ImageDraw, ImageFont
    import os
    font = os.path.join(os.path.dirname(__file__), "..", "fonts", "LilitaOne-Regular.ttf")
    im = Image.new("RGB", size, (246, 243, 236))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(font, 260)
    w = d.textlength(text, font=f)
    d.text(((size[0] - w) / 2, size[1] / 2 - 170), text, font=f, fill=(206, 32, 38))
    d.rounded_rectangle((30, 30, size[0] - 30, size[1] - 30), radius=30, outline=(200, 192, 176), width=10)
    im.save(path)
    return path


def sign(name, tex_path, w=2.4, h=2.7, parent=None):
    img = bpy.data.images.load(tex_path)
    m = bpy.data.materials.new(name + "_mat")
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.85
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    nt.links.new(tx.outputs["Color"], p.inputs["Base Color"])
    g = L.empty(name, parent=parent)
    verts = [(-w / 2, 0, 0), (w / 2, 0, 0), (w / 2, 0, h), (-w / 2, 0, h)]
    board = L.mesh_obj(name + "_board", verts, [(0, 1, 2, 3)], m, parent=g, smooth=False)
    board.location = (0, 0, 1.4)
    uv = board.data.uv_layers.new(name="UVMap")
    for loop, co in zip(board.data.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[loop.index].uv = co
    board.modifiers.new("sol", "SOLIDIFY").thickness = 0.06
    L.cylinder(name + "_stick", 0.07, 1.6, loc=(0, 0.08, 0.8), mat=L.mat_wood("stick", "#B98A55", "#8A5E34", 8), parent=g, segs=12)
    return g


def pencil(name="Pencil", parent=None):
    g = L.empty(name, parent=parent)
    L.cylinder(name + "_b", 0.06, 1.2, loc=(0, 0, 0.6), mat=L.mat_plain("pencil_y", "#F2C230", 0.4), parent=g, segs=6)
    L.cylinder(name + "_tip", 0.06, 0.2, loc=(0, 0, -0.1), mat=L.mat_wood("pwood", "#E6C08A", "#D2A870", 20), parent=g,
               segs=12, r_top=0.06).scale = (1, 1, 1)
    L.cylinder(name + "_er", 0.062, 0.16, loc=(0, 0, 1.28), mat=L.mat_plain("eraser", "#E88A8A", 0.7), parent=g, segs=12)
    return g


def rubber_stamp(name="Stamp", parent=None):
    g = L.empty(name, parent=parent)
    L.cylinder(name + "_h", 0.14, 0.9, loc=(0, 0, 0.75), mat=L.mat_wood("sh", "#9B6A3A", "#7A5028", 10), parent=g, segs=24)
    L.uv_sphere(name + "_k", 0.22, loc=(0, 0, 1.25), scale=(1, 1, .8), mat=L.mat_wood("sk", "#B98A55", "#8A5E34", 10), parent=g)
    L.rounded_box(name + "_base", (0.8, 0.5, 0.25), 0.04, loc=(0, 0, 0.25), mat=L.mat_wood("sb", "#7B5230", "#5A3A20", 10),
                  parent=g)
    L.rounded_box(name + "_ink", (0.76, 0.46, 0.08), 0.02, loc=(0, 0, 0.06), mat=L.mat_plain("ink", "#C0392B", 0.5), parent=g)
    return g
