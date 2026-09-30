"""3D building blocks for Blender (bpy): render setup, materials, mesh helpers.

Units: 1 Blender unit = 10 cm ("u"). Characters face -Y (toward a camera placed at -Y).
Metaball note: an isolated ball of `radius` r renders with visible radius ~r/2, so the
helpers below take *visible* sizes and double them.
"""
from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

# ----------------------------------------------------------------------------- scene


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def setup_render(width=720, height=1280, samples=6, fps=24):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = samples
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.03
    s.cycles.use_denoising = True
    s.cycles.denoiser = "OPENIMAGEDENOISE"
    s.cycles.max_bounces = 4
    s.cycles.diffuse_bounces = 2
    s.cycles.glossy_bounces = 2
    s.cycles.transmission_bounces = 4
    s.cycles.denoising_prefilter = "FAST"
    s.cycles.transparent_max_bounces = 6
    s.cycles.caustics_reflective = False
    s.cycles.caustics_refractive = False
    s.cycles.blur_glossy = 1.0
    s.render.resolution_x, s.render.resolution_y = width, height
    s.render.resolution_percentage = 100
    s.render.fps = fps
    s.render.use_persistent_data = True
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGB"
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = 0.0
    s.render.film_transparent = False
    return s


def world(color=(0.05, 0.035, 0.025), strength=1.0):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength
    return w


def link(obj, parent=None):
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None)
    o.location = loc
    return link(o, parent)


def camera(loc, target, lens=50, fstop=0.35, focus=None, name="Cam"):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cd.clip_start = 0.05
    cd.clip_end = 500
    cam = link(bpy.data.objects.new(name, cd))
    bpy.context.scene.camera = cam
    aim_camera(cam, loc, target, fstop, focus)
    return cam


def aim_camera(cam, loc, target, fstop=None, focus=None, roll=0.0):
    cam.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    q = d.to_track_quat("-Z", "Y")
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = q @ Quaternion((0, 0, 1), math.radians(roll))
    cd = cam.data
    if fstop is not None:
        cd.dof.use_dof = fstop > 0
        cd.dof.aperture_fstop = max(fstop, 0.01)
    cd.dof.focus_distance = focus if focus is not None else d.length


def light_area(name, loc, target, power, size=2.0, color=(1, 1, 1), shape="DISK", size_y=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = power
    ld.color = color
    ld.shape = shape
    ld.size = size
    if size_y is not None:
        ld.size_y = size_y
    o = link(bpy.data.objects.new(name, ld))
    o.location = loc
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y")
    return o


def light_sun(name, direction, strength, color=(1, .8, .6), angle=4.0):
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = strength
    ld.color = color
    ld.angle = math.radians(angle)
    o = link(bpy.data.objects.new(name, ld))
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector(direction).to_track_quat("-Z", "Y")
    return o


def light_point(name, loc, power, color=(1, .8, .6), radius=0.3):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = power
    ld.color = color
    ld.shadow_soft_size = radius
    o = link(bpy.data.objects.new(name, ld))
    o.location = loc
    return o


def kelvin(k):
    """Approximate blackbody RGB (linear-ish) for colour temperatures 1500-12000 K."""
    t = k / 100.0
    r = 255 if t <= 66 else 329.7 * (t - 60) ** -0.1332
    g = 99.47 * math.log(t) - 161.1 if t <= 66 else 288.1 * (t - 60) ** -0.0755
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5 * math.log(t - 10) - 305.0)
    c = [max(0, min(255, v)) / 255 for v in (r, g, b)]
    return tuple(v ** 2.2 for v in c)


# --------------------------------------------------------------------------- materials


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)


def _mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    return m, nt, p


def _set(p, **kw):
    names = {"base": "Base Color", "rough": "Roughness", "metal": "Metallic", "sss": "Subsurface Weight",
             "sss_radius": "Subsurface Radius", "sss_scale": "Subsurface Scale", "sheen": "Sheen Weight",
             "sheen_rough": "Sheen Roughness", "sheen_tint": "Sheen Tint", "coat": "Coat Weight",
             "coat_rough": "Coat Roughness", "trans": "Transmission Weight", "ior": "IOR", "emit": "Emission Color",
             "emit_str": "Emission Strength", "spec": "Specular IOR Level", "alpha": "Alpha"}
    for k, v in kw.items():
        inp = p.inputs[names[k]]
        if isinstance(v, str):
            v = srgb(v)
        if isinstance(v, tuple) and len(v) == 3 and inp.type == "RGBA":
            v = (*v, 1.0)
        inp.default_value = v


def _bump(nt, p, height_socket, strength=0.3, distance=0.02):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    nt.links.new(height_socket, b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    return b


def _coord(nt, kind="Object"):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    return tc.outputs[kind]


def mat_plain(name, color, rough=0.5, **kw):
    m, nt, p = _mat(name)
    _set(p, base=color, rough=rough, **kw)
    return m


def mat_skin_scaly(name, color="#E9EBC6", back="#D0D29E", scale=62.0, sss=0.25):
    """Creamy dragon skin: soft SSS, fine sheen fuzz, voronoi scales in bump, slightly greener on top."""
    m, nt, p = _mat(name)
    _set(p, rough=0.62, sss=sss, sss_radius=(0.8, 0.65, 0.4), sss_scale=0.03, sheen=0.35, sheen_rough=0.4,
         sheen_tint="#FFF8E6", spec=0.35)
    co = _coord(nt)
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "SMOOTH_F1" if hasattr(vor, "feature") else vor.feature
    vor.inputs["Scale"].default_value = scale
    nt.links.new(co, vor.inputs["Vector"])
    vor2 = nt.nodes.new("ShaderNodeTexVoronoi")
    vor2.feature = "DISTANCE_TO_EDGE"
    vor2.inputs["Scale"].default_value = scale
    nt.links.new(co, vor2.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].position = 0.12
    nt.links.new(vor2.outputs["Distance"], ramp.inputs["Fac"])
    _bump(nt, p, ramp.outputs["Color"], strength=0.14, distance=0.01)
    # colour: cream, a touch greener/darker toward the top and in scale creases
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(co, sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.3
    mr.inputs["From Max"].default_value = 1.6
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*srgb(color), 1)
    mix.inputs["B"].default_value = (*srgb(back), 1)
    nt.links.new(mr.outputs["Result"], mix.inputs["Factor"])
    mix2 = nt.nodes.new("ShaderNodeMix")
    mix2.data_type = "RGBA"
    mix2.inputs["Factor"].default_value = 0.0
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "MULTIPLY"
    inv.inputs[1].default_value = 0.25
    one = nt.nodes.new("ShaderNodeMath")
    one.operation = "SUBTRACT"
    one.inputs[0].default_value = 1.0
    nt.links.new(ramp.outputs["Color"], one.inputs[1])
    nt.links.new(one.outputs[0], inv.inputs[0])
    nt.links.new(inv.outputs[0], mix2.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], mix2.inputs["A"])
    mix2.inputs["B"].default_value = (*srgb("#A99E6A"), 1)
    nt.links.new(mix2.outputs["Result"], p.inputs["Base Color"])
    return m


def mat_eye(name, iris="#5C2E10", pupil="#0E0605", ring="#2A1208", mid="#9A5424"):
    """Glossy cartoon eye; gaze is the object's local -Y axis."""
    m, nt, p = _mat(name)
    _set(p, rough=0.25, coat=1.0, coat_rough=0.02, spec=0.6)
    co = _coord(nt)
    nrm = nt.nodes.new("ShaderNodeVectorMath")
    nrm.operation = "NORMALIZE"
    nt.links.new(co, nrm.inputs[0])
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = (0, -1, 0)
    nt.links.new(nrm.outputs[0], dot.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position, cr.elements[0].color = 0.0, (*srgb(ring), 1)
    cr.elements[1].position, cr.elements[1].color = 0.45, (*srgb(ring), 1)
    for pos, col in [(0.56, iris), (0.72, mid), (0.78, pupil), (1.0, pupil)]:
        e = cr.elements.new(pos)
        e.color = (*srgb(col), 1)
    nt.links.new(dot.outputs["Value"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    return m


def mat_emit(name, color, strength=5.0):
    m, nt, p = _mat(name)
    _set(p, base=color, emit=color, emit_str=strength, rough=0.4)
    return m


def mat_fabric(name, color, scale=60.0, bump=0.35, alt=None, weave=True):
    """Upholstery / knit: two crossed wave bands for weave, noise for colour variation."""
    m, nt, p = _mat(name)
    _set(p, rough=0.85, sheen=0.6, sheen_rough=0.5, spec=0.2)
    co = _coord(nt)
    w1 = nt.nodes.new("ShaderNodeTexWave")
    w1.wave_type = "BANDS"
    w1.bands_direction = "X"
    w1.inputs["Scale"].default_value = scale
    w1.inputs["Distortion"].default_value = 1.5
    w2 = nt.nodes.new("ShaderNodeTexWave")
    w2.wave_type = "BANDS"
    w2.bands_direction = "Z" if weave else "Y"
    w2.inputs["Scale"].default_value = scale
    w2.inputs["Distortion"].default_value = 1.5
    for w in (w1, w2):
        nt.links.new(co, w.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "MULTIPLY"
    nt.links.new(w1.outputs["Fac"], add.inputs[0])
    nt.links.new(w2.outputs["Fac"], add.inputs[1])
    _bump(nt, p, add.outputs[0], strength=bump, distance=0.03)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6
    nt.links.new(co, noise.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    c = srgb(color)
    mix.inputs["A"].default_value = (*[v * 0.8 for v in c], 1)
    mix.inputs["B"].default_value = (*(srgb(alt) if alt else c), 1)
    fac = nt.nodes.new("ShaderNodeMath")
    fac.operation = "MULTIPLY_ADD"
    fac.inputs[1].default_value = 0.5
    fac.inputs[2].default_value = 0.35
    nt.links.new(noise.outputs["Fac"], fac.inputs[0])
    fac2 = nt.nodes.new("ShaderNodeMath")
    fac2.operation = "ADD"
    nt.links.new(fac.outputs[0], fac2.inputs[0])
    nt.links.new(add.outputs[0], fac2.inputs[1])
    nt.links.new(fac2.outputs[0], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], p.inputs["Base Color"])
    return m


def mat_stripes(name, colors, scale=4.0, axis="Z", bump=0.5, knit_scale=90):
    """Chunky knit with colour stripes (pillows, throws, blankets)."""
    m, nt, p = _mat(name)
    _set(p, rough=0.9, sheen=0.8, sheen_rough=0.6, spec=0.15)
    co = _coord(nt)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(co, sep.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = scale
    nt.links.new(sep.outputs[axis], mul.inputs[0])
    fr = nt.nodes.new("ShaderNodeMath")
    fr.operation = "FRACT"
    nt.links.new(mul.outputs[0], fr.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "CONSTANT"
    n = len(colors)
    cr.elements[0].color = (*srgb(colors[0]), 1)
    cr.elements[1].position = 1 / n
    cr.elements[1].color = (*srgb(colors[1 % n]), 1)
    for i in range(2, n):
        e = cr.elements.new(i / n)
        e.color = (*srgb(colors[i]), 1)
    nt.links.new(fr.outputs[0], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    w = nt.nodes.new("ShaderNodeTexWave")
    w.wave_type = "RINGS" if False else "BANDS"
    w.inputs["Scale"].default_value = knit_scale
    w.inputs["Distortion"].default_value = 4
    w.inputs["Detail"].default_value = 3
    nt.links.new(co, w.inputs["Vector"])
    _bump(nt, p, w.outputs["Fac"], strength=bump, distance=0.05)
    return m


def mat_glass(name, tint="#FFFFFF", rough=0.02, clarity=0.88):
    """Cheap bright glass: mostly transparent + a glossy sheen (no refraction bounce cost)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    p = nt.nodes["Principled BSDF"]
    _set(p, base=tint, rough=rough, spec=1.0, coat=1.0, coat_rough=0.02)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = 1 - clarity
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(p.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def mat_wood(name, color="#8A5A34", dark="#5C3A20", scale=3.0, rough=0.45):
    m, nt, p = _mat(name)
    _set(p, rough=rough, spec=0.4, coat=0.2, coat_rough=0.2)
    co = _coord(nt)
    w = nt.nodes.new("ShaderNodeTexWave")
    w.wave_type = "BANDS"
    w.bands_direction = "X"
    w.inputs["Scale"].default_value = scale
    w.inputs["Distortion"].default_value = 8
    w.inputs["Detail"].default_value = 4
    nt.links.new(co, w.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*srgb(color), 1)
    mix.inputs["B"].default_value = (*srgb(dark), 1)
    nt.links.new(w.outputs["Fac"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], p.inputs["Base Color"])
    _bump(nt, p, w.outputs["Fac"], strength=0.08, distance=0.01)
    return m


def mat_ridged(name, color, ridges=30.0, rough=0.35):
    """Horn keratin: glossy with rings along the object's local Z."""
    m, nt, p = _mat(name)
    _set(p, base=color, rough=rough, coat=0.4, coat_rough=0.25, sss=0.15, sss_radius=(1, .4, .2), sss_scale=0.02)
    co = _coord(nt, "UV")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(co, sep.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = ridges
    nt.links.new(sep.outputs["Y"], mul.inputs[0])
    sn = nt.nodes.new("ShaderNodeMath")
    sn.operation = "SINE"
    nt.links.new(mul.outputs[0], sn.inputs[0])
    _bump(nt, p, sn.outputs[0], strength=0.35, distance=0.01)
    # darker toward the base, lighter at the tips
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*[v * 0.55 for v in srgb(color)], 1)
    ramp.color_ramp.elements[1].color = (*srgb("#E8A070"), 1)
    nt.links.new(sep.outputs["Y"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    return m


def mat_membrane(name, color="#7C8C4A"):
    m, nt, p = _mat(name)
    _set(p, base=color, rough=0.55, sss=0.4, sss_radius=(0.6, 1.0, 0.3), sss_scale=0.05, sheen=0.3,
         sheen_tint="#DDE8B0")
    return m


def assign(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    return obj


# ------------------------------------------------------------------------------ meshes


def mesh_obj(name, verts, faces, mat=None, smooth=True, parent=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    o = link(bpy.data.objects.new(name, me), parent)
    if smooth:
        for poly in me.polygons:
            poly.use_smooth = True
    if mat:
        assign(o, mat)
    return o


def uv_sphere(name, radius=1.0, loc=(0, 0, 0), scale=(1, 1, 1), mat=None, segs=48, rings=24, parent=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=radius)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    o = link(bpy.data.objects.new(name, me), parent)
    o.location = loc
    o.scale = scale
    if mat:
        assign(o, mat)
    return o


def rounded_box(name, size, bevel=0.2, loc=(0, 0, 0), mat=None, segments=6, parent=None, subdiv_cuts=0):
    sx, sy, sz = size
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    if subdiv_cuts:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=subdiv_cuts, use_grid_fill=True)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me), parent)
    o.location = loc
    mod = o.modifiers.new("bevel", "BEVEL")
    mod.width = bevel
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.harden_normals = False
    for poly in me.polygons:
        poly.use_smooth = True
    if mat:
        assign(o, mat)
    return o


def cylinder(name, r, h, loc=(0, 0, 0), mat=None, segs=48, parent=None, cap=True, bevel=0.0, r_top=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, segments=segs, radius1=r, radius2=r if r_top is None else r_top, depth=h)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me), parent)
    o.location = loc
    for poly in me.polygons:
        poly.use_smooth = True
    if bevel:
        mod = o.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 4
        mod.limit_method = "ANGLE"
    if mat:
        assign(o, mat)
    return o


def sweep(name, path, radii, mat=None, ring=20, parent=None, cap_tip=True, uv=True):
    """Tube swept along `path` points with per-point radius (horns, spikes, tails, straps)."""
    P = [Vector(p) for p in path]
    verts, faces, uvs = [], [], []
    n = len(P)
    up = Vector((0, 0, 1))
    prev_side = None
    for i, p in enumerate(P):
        t = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized()
        side = t.cross(up)
        if side.length < 1e-4:
            side = t.cross(Vector((1, 0, 0)))
        side.normalize()
        if prev_side is not None and side.dot(prev_side) < 0:
            side = -side
        prev_side = side
        up2 = side.cross(t).normalized()
        for k in range(ring):
            a = 2 * math.pi * k / ring
            verts.append(p + (side * math.cos(a) + up2 * math.sin(a)) * radii[i])
    for i in range(n - 1):
        for k in range(ring):
            a, b = i * ring + k, i * ring + (k + 1) % ring
            faces.append((a, b, b + ring, a + ring))
    if cap_tip:
        verts.append(P[-1] + (P[-1] - P[-2]).normalized() * radii[-1] * 0.6)
        tip = len(verts) - 1
        base = (n - 1) * ring
        for k in range(ring):
            faces.append((base + k, base + (k + 1) % ring, tip))
    verts.append(P[0] - (P[1] - P[0]).normalized() * radii[0] * 0.3)
    root = len(verts) - 1
    for k in range(ring):
        faces.append(((k + 1) % ring, k, root))
    o = mesh_obj(name, verts, faces, mat, parent=parent)
    if uv:
        me = o.data
        uvl = me.uv_layers.new(name="UVMap")
        per_vert_v = []
        for i in range(n):
            per_vert_v += [i / (n - 1)] * ring
        per_vert_v += [1.0, 0.0]
        for loop in me.loops:
            uvl.data[loop.index].uv = (0.0, per_vert_v[loop.vertex_index])
    return o


def catmull(points, samples=8):
    """Catmull-Rom spline through points -> dense list."""
    P = [Vector(p) for p in points]
    P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return out


def replace_mesh(obj, verts, faces):
    me = obj.data
    me.clear_geometry()
    me.from_pydata([tuple(v) for v in verts], [], faces)
    for poly in me.polygons:
        poly.use_smooth = True
    me.update()


# ------------------------------------------------------------------------- metaballs


class Meta:
    """A metaball family. add() takes VISIBLE radii; elements can be re-posed every frame."""

    def __init__(self, name, mat, parent=None, res=0.02, render_res=0.012, threshold=0.6):
        self.mb = bpy.data.metaballs.new(name)
        self.mb.resolution = res
        self.mb.render_resolution = render_res
        self.mb.threshold = threshold
        self.obj = link(bpy.data.objects.new(name, self.mb), parent)
        assign(self.obj, mat)
        self.el = {}

    def add(self, key, kind="BALL", co=(0, 0, 0), r=0.5, size=(1, 1, 1), rot=(0, 0, 0), stiff=2.0, neg=False):
        e = self.mb.elements.new(type=kind)
        e.stiffness = stiff
        e.use_negative = neg
        self.el[key] = e
        self.set(key, co, r, size, rot)
        return e

    def set(self, key, co=None, r=None, size=None, rot=None):
        e = self.el[key]
        if co is not None:
            e.co = Vector(co)
        if r is not None:
            e.radius = 2.0 * r
        if size is not None and e.type in ("ELLIPSOID", "CAPSULE", "CUBE", "PLANE"):
            e.size_x, e.size_y, e.size_z = size
        if rot is not None:
            if isinstance(rot, Quaternion):
                e.rotation = rot
            else:
                e.rotation = Euler([math.radians(a) for a in rot]).to_quaternion()

    def capsule(self, key, a, b, r, stiff=2.0):
        """Capsule element from point a to point b with visible radius r."""
        a, b = Vector(a), Vector(b)
        d = b - a
        L = max(d.length, 1e-4)
        if key not in self.el:
            self.add(key, "CAPSULE", r=r, stiff=stiff)
        e = self.el[key]
        e.co = (a + b) / 2
        e.radius = 2.0 * r
        e.size_x = L / 2 / (2.0 * r) * 2.0 * r if False else L / 2
        e.rotation = d.to_track_quat("X", "Z")
