"""Sets and lighting. Everything in u (10 cm)."""
from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector

import lib3d as L


def couch(dent_at=(0.0, 0.0), dent_r=2.2, dent_depth=0.35):
    """Rust couch in late-afternoon light, seat top at z=0, facing -Y."""
    fab = L.mat_fabric("couch", "#A4482A", scale=55, bump=0.6, alt="#B85A34")
    seat = L.rounded_box("seat", (8.0, 7.0, 2.0), 0.55, loc=(0, 0.6, -1.0), mat=fab, subdiv_cuts=40)
    tex = bpy.data.textures.new("dent", "BLEND")
    tex.progression = "SPHERICAL"
    ctrl = L.empty("dent_ctrl", (dent_at[0], dent_at[1], 0))
    ctrl.scale = (dent_r, dent_r * 1.2, dent_r)
    d = seat.modifiers.new("dent", "DISPLACE")
    d.texture = tex
    d.texture_coords = "OBJECT"
    d.texture_coords_object = ctrl
    d.direction = "Z"
    d.strength = -dent_depth
    d.mid_level = 0.0
    sub = seat.modifiers.new("smooth", "SUBSURF")
    sub.levels = sub.render_levels = 1
    # seam piping along the front edge
    L.cylinder("piping", 0.07, 8.0, loc=(0, -2.92, -0.06), mat=fab, segs=16).rotation_euler = (0, math.radians(90), 0)
    back = L.rounded_box("back", (8.4, 2.6, 5.0), 0.9, loc=(0, 5.0, 1.9), mat=fab)
    back.rotation_euler = (math.radians(-12), 0, 0)
    L.rounded_box("back2", (8.4, 2.6, 5.0), 0.9, loc=(8.6, 5.0, 1.9), mat=fab).rotation_euler = (math.radians(-12), 0, 0)
    L.rounded_box("seat2", (8.0, 7.0, 2.0), 0.55, loc=(8.2, 0.6, -1.0), mat=fab)
    L.rounded_box("seatL", (8.0, 7.0, 2.0), 0.55, loc=(-8.2, 0.6, -1.0), mat=fab)
    L.rounded_box("backL", (8.4, 2.6, 5.0), 0.9, loc=(-8.6, 5.0, 1.9), mat=fab).rotation_euler = (math.radians(-12), 0, 0)
    L.rounded_box("base", (26, 8, 3), 0.3, loc=(0, 0.8, -3.4), mat=fab)
    # knit pillows (left)
    knit1 = L.mat_stripes("knit1", ["#E7DCC6", "#E7DCC6", "#3C4660", "#E7DCC6", "#B8683A"], scale=3.0, knit_scale=70)
    p1 = L.rounded_box("pillow1", (4.4, 1.6, 4.4), 1.2, loc=(-5.6, 3.1, 2.0), mat=knit1)
    p1.rotation_euler = (math.radians(-14), math.radians(8), math.radians(-12))
    knit2 = L.mat_stripes("knit2", ["#8A4A26", "#DCC9A6", "#4F6B4A", "#DCC9A6"], scale=5.0, axis="X", knit_scale=70)
    p2 = L.rounded_box("pillow2", (3.8, 1.5, 3.6), 1.0, loc=(-6.4, 1.4, 1.3), mat=knit2)
    p2.rotation_euler = (math.radians(-22), math.radians(-6), math.radians(-18))
    # foreground knit throw (bottom-left, out of focus)
    throw = L.mat_stripes("throw", ["#DCCDB0", "#DCCDB0", "#5D6E54", "#B8683A"], scale=6.0, axis="X", knit_scale=50, bump=0.7)
    th = L.rounded_box("throw", (5.0, 3.0, 2.2), 1.0, loc=(-4.2, -6.2, -0.2), mat=throw)
    th.rotation_euler = (math.radians(10), 0, math.radians(30))
    room_back()
    return seat


def room_back(wall="#CFC2A8"):
    L.rounded_box("wall", (80, 1, 40), 0.1, loc=(0, 16, 10), mat=L.mat_plain("wall", wall, rough=0.9))
    wood = L.mat_wood("shelf", "#6B4428", "#4A2E1A", 2)
    L.rounded_box("shelf", (8, 3, 22), 0.1, loc=(3.5, 14, 6), mat=wood)
    cols = ["#6E4A30", "#4E5E70", "#8C6A40", "#6A3A2A", "#B89060", "#3E4A3C"]
    for r, z in enumerate((4.0, 9.5, 15.0)):
        L.rounded_box(f"sh{r}", (8, 3, 0.3), 0.05, loc=(3.5, 13.5, z - 0.8), mat=wood)
        x = 0.2
        k = 0
        while x < 7.0:
            w = 0.5 + ((k * 37) % 5) * 0.12
            h = 3.2 + ((k * 53) % 4) * 0.4
            L.rounded_box(f"bk{r}{k}", (w, 2.0, h), 0.05, loc=(x + w / 2, 13.3, z + h / 2 - 0.6),
                          mat=L.mat_plain(f"bk{r}{k}", cols[(k + r) % len(cols)], rough=0.6))
            x += w + 0.05
            k += 1
    frame = L.rounded_box("frame", (6, 0.4, 4.5), 0.1, loc=(12, 15.2, 12), mat=wood)
    L.rounded_box("art", (5.2, 0.45, 3.7), 0.05, loc=(12, 15.1, 12), mat=L.mat_plain("art", "#8FA08A", rough=0.8))
    win = L.mat_emit("window", "#FFD9A0", 6.0)
    L.rounded_box("window", (8, 0.3, 14), 0.1, loc=(-11, 15.4, 10), mat=win)
    leaf = L.mat_plain("leaf", "#4F6B35", rough=0.6, sss=0.3, sss_scale=0.3)
    import random
    rnd = random.Random(3)
    for i in range(40):
        L.uv_sphere(f"leaf{i}", 0.5, loc=(-5 + rnd.uniform(-2, 2), 13 + rnd.uniform(-1, 1), 4 + i * 0.3 + rnd.uniform(-.3, .3)),
                    scale=(1, .4, .7), mat=leaf, segs=12, rings=8)


def light_couch():
    sun = L.light_sun("sun", (0.55, 0.55, -0.35), 3.2, L.kelvin(3000), angle=6)
    L.light_area("fill", (6, -14, 8), (0, 0, 1), 900, size=10, color=L.kelvin(5200))
    L.light_area("rim", (-10, 12, 10), (0, 0, 1), 800, size=6, color=L.kelvin(2800))
    L.world((0.09, 0.055, 0.035), 1.0)
    return sun


def floor_contact(z=0.0):
    pass


def kitchen():
    wood = L.mat_wood("counter", "#C08A58", "#9A6A40", 1.2, rough=0.35)
    L.rounded_box("counter", (40, 20, 2), 0.1, loc=(0, 4, -1.0), mat=wood)
    tile = L.mat_fabric("tile", "#EDE6D6", scale=2.2, bump=1.2, alt="#F4EFE4")
    L.rounded_box("backsplash", (40, 1, 20), 0.05, loc=(0, 9, 10), mat=tile)
    L.rounded_box("wall_up", (40, 1, 20), 0.05, loc=(0, 9.2, 26), mat=L.mat_plain("kwall", "#E4D9C2", .9))
    L.rounded_box("kwin", (10, 0.3, 8), 0.1, loc=(9, 8.3, 9), mat=L.mat_emit("kwin", "#FFF1D6", 5.0))
    for i, (x, c) in enumerate([(-8, "#6E8F6A"), (-10.5, "#B8683A"), (12, "#D8C39A")]):
        L.cylinder(f"jar{i}", 1.1, 3.0, loc=(x, 6.5, 1.5), mat=L.mat_plain(f"jar{i}", c, 0.3, coat=0.5), segs=32)
    L.light_sun("ksun", (-0.6, -0.5, -0.6), 3.0, L.kelvin(4200), angle=8)
    L.light_area("kfill", (-4, -10, 6), (0, 0, 1), 400, size=8, color=L.kelvin(5600))
    L.light_area("kwinl", (9, 7, 9), (0, 0, 0.5), 1500, size=8, color=L.kelvin(5000))
    L.world((0.22, 0.2, 0.17), 1.0)


def bedroom():
    duvet = L.mat_fabric("duvet", "#8E97C4", scale=45, bump=0.4, alt="#A0A8D2")
    L.rounded_box("bed", (26, 20, 2.0), 0.9, loc=(-4, 2, -1.0), mat=duvet)
    for i in range(3):
        b = L.rounded_box(f"fold{i}", (26, 1.6, 0.9), 0.5, loc=(-4, -3 + i * 4.5, 0.05), mat=duvet)
        b.rotation_euler = (0, 0, math.radians(3 - i * 2))
    L.rounded_box("pillow", (10, 4, 2.6), 1.3, loc=(-6, 9, 1.2), mat=L.mat_fabric("pillow", "#E8E4F2", 45, 0.3))
    L.rounded_box("headboard", (28, 1, 14), 0.4, loc=(-4, 12.5, 6), mat=L.mat_wood("hb", "#6E4A30", "#4E321E", 2))
    ns = L.mat_wood("ns", "#8A5E3A", "#6A4228", 3)
    L.rounded_box("nightstand", (5, 5, 4.6), 0.2, loc=(12, 3, -1.9), mat=ns)
    L.cylinder("lamp_base", 0.5, 2.6, loc=(13, 4.2, 1.6), mat=L.mat_plain("lampb", "#C9A46A", 0.3, metal=0.6), segs=24)
    L.cylinder("shade", 1.6, 1.8, loc=(13, 4.2, 3.6), mat=L.mat_emit("shade", "#FFD9A0", 2.5), segs=32, r_top=1.1, cap=False)
    L.rounded_box("bwall", (60, 1, 40), 0.1, loc=(0, 14, 10), mat=L.mat_plain("bwall", "#4A4468", .9))
    L.rounded_box("tray", (1.6, 1.4, 0.62), 0.08, loc=(2.0, 1.2, 0.31), mat=L.mat_wood("tray", "#9A6A40", "#7A4E2C", 4))


def light_bedroom(lamp=1.0, moon=0.0):
    lp = L.light_point("lamp", (13, 4.2, 3.4), 400 * lamp, L.kelvin(2700), radius=1.0)
    L.light_area("bfill", (-3, -12, 7), (0, 0, 1), 1400 * lamp + 30, size=10, color=L.kelvin(4200 if lamp else 9000))
    if lamp:
        L.light_area("bkey", (8, -4, 6), (0, 0, 0.5), 1200 * lamp, size=4, color=L.kelvin(2900))
    if moon:
        L.light_area("moon", (-12, -4, 10), (0, 0, 0), 220 * moon, size=12, color=(0.5, 0.6, 1.0))
    L.world((0.03, 0.03, 0.05) if lamp < 0.5 else (0.08, 0.06, 0.07), 1.0)
    return lp


def entry():
    floor = L.mat_wood("efloor", "#9A6A42", "#744A2A", 0.8, rough=0.4)
    L.rounded_box("efloor", (60, 40, 1), 0.05, loc=(0, 4, -0.5), mat=floor)
    wall = L.mat_plain("ewall", "#E6DCC8", .9)
    L.rounded_box("ewall", (60, 1, 40), 0.05, loc=(0, 5.5, 20), mat=wall)
    L.rounded_box("base", (60, 0.6, 1.2), 0.1, loc=(0, 5.0, 0.6), mat=L.mat_plain("eskirt", "#F4EFE6", .5))
    door = L.mat_plain("door", "#6E8F7A", 0.45, coat=0.2)
    L.rounded_box("door", (8.6, 0.5, 20.5), 0.12, loc=(0, 5.2, 10.25), mat=door)
    for z in (5.0, 15.0):
        L.rounded_box(f"panel{z}", (6.4, 0.6, 8.0), 0.3, loc=(0, 5.0, z), mat=L.mat_plain(f"pn{z}", "#62826E", 0.5))
    L.rounded_box("frame", (10.2, 0.4, 21.5), 0.1, loc=(0, 5.4, 10.6), mat=L.mat_plain("dframe", "#F4EFE6", .5))
    knob = L.mat_plain("knob", "#C9A24A", 0.2, metal=1.0)
    L.uv_sphere("rose", 0.5, loc=(3.2, 4.7, 9.6), scale=(1, .3, 1), mat=knob)
    lever = L.empty("lever_piv", (3.2, 4.45, 9.6))
    L.rounded_box("lever", (1.8, 0.35, 0.35), 0.15, loc=(-0.8, 0, 0), mat=knob, parent=lever)
    L.light_area("ekey", (-10, -8, 16), (0, 3, 3), 3000, size=10, color=L.kelvin(4300))
    L.light_area("efill", (8, -12, 6), (0, 0, 3), 900, size=10, color=L.kelvin(6000))
    L.world((0.18, 0.16, 0.14), 1.0)
    return lever


def living():
    floor = L.mat_wood("lfloor", "#8A5A36", "#643E22", 0.7, rough=0.4)
    L.rounded_box("lfloor", (80, 50, 1), 0.05, loc=(0, 10, -0.5), mat=floor)
    sofa = L.mat_fabric("lsofa", "#5A3A4A", 60, 0.4)
    L.rounded_box("lsofa", (26, 8, 6), 1.2, loc=(-6, 16, 3), mat=sofa)
    L.rounded_box("lsofab", (26, 3, 9), 1.2, loc=(-6, 20, 7), mat=sofa)
    L.rounded_box("lwall", (80, 1, 40), 0.05, loc=(0, 24, 18), mat=L.mat_plain("lwall", "#5A4440", .9))
    L.cylinder("llamp_pole", 0.2, 14, loc=(12, 18, 7), mat=L.mat_plain("pole", "#2A2A2A", 0.4, metal=0.8), segs=12)
    L.cylinder("llamp_shade", 2.0, 2.4, loc=(12, 18, 14.5), mat=L.mat_emit("lshade", "#FFCB88", 3.0), segs=32, r_top=1.4, cap=False)
    L.light_point("llamp", (12, 17, 14), 3000, L.kelvin(2700), radius=1.5)
    L.light_area("lkey", (-6, -8, 9), (2, 0, 1), 1600, size=8, color=L.kelvin(3900))
    L.light_area("lfill", (6, -10, 4), (2, 0, 1), 600, size=10, color=L.kelvin(5600))
    L.light_area("lrim", (10, 10, 6), (2, 0, 1), 700, size=6, color=L.kelvin(2800))
    L.world((0.06, 0.04, 0.035), 1.0)
