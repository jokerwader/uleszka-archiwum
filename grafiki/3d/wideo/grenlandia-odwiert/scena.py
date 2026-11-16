# -*- coding: utf-8 -*-
"""
Klip „grenlandia-odwiert” do odcinka 2 „Wielki uskok…”.

Przekrój lądolodu Grenlandii z warstwami lodu, wiertło schodzi do ok. 3000 m,
rdzeń lodowy wychodzi z otworu, kładzie się poziomo i z niego „wyrasta” wykres
średniej temperatury dokładnie taki jak na rysunku Leszka (zrodlo/webacja/02uskok/temperatura.jpg):
krzywa jest odczytywana piksel po pikselu z rysunku, podpisy i siatka leżą tam, gdzie na rysunku.

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/grenlandia-odwiert/scena.py
  ... -- --test 1,120,250,400     (tylko kadry próbne PNG do _klatki/test/)
"""
import bpy, bmesh, math, os, sys, shutil, subprocess, time
import numpy as np
from mathutils import Vector

TU = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(TU, "..", "..", "..", ".."))
WIDEO = os.path.dirname(TU)
NAZWA = os.path.basename(TU)
RYSUNEK = os.path.join(REPO, "zrodlo", "webacja", "02uskok", "temperatura.jpg")
FONT_DIR = r"C:\Windows\Fonts"
FPS = 25
KLATEK = 400  # 16 s

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TEST = None
if "--test" in argv:
    TEST = [int(v) for v in argv[argv.index("--test") + 1].split(",")]


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c) + (1.0,)


def rgb255(r, g, b):
    return srgb("%02x%02x%02x" % (r, g, b))


# ---------------------------------------------------------------- scena
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, KLATEK
sc.eevee.taa_render_samples = 48
try:
    sc.eevee.use_shadows = True
except Exception:
    pass
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
sc.render.film_transparent = False

col = sc.collection

# świat: granatowy gradient w kadrze, słabe światło otoczenia
world = bpy.data.worlds.new("Swiat")
sc.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()
out = wn.new("ShaderNodeOutputWorld")
tc = wn.new("ShaderNodeTexCoord")
sep = wn.new("ShaderNodeSeparateXYZ")
ramp = wn.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = srgb("#05070c")
ramp.color_ramp.elements[1].color = srgb("#1b2a4d")
ramp.color_ramp.elements[0].position = 0.0
ramp.color_ramp.elements[1].position = 1.0
bgc = wn.new("ShaderNodeBackground")
bga = wn.new("ShaderNodeBackground")
bga.inputs[0].default_value = srgb("#2a3550")
bga.inputs[1].default_value = 0.6
lp = wn.new("ShaderNodeLightPath")
mix = wn.new("ShaderNodeMixShader")
wl.new(tc.outputs["Window"], sep.inputs[0])
wl.new(sep.outputs["Y"], ramp.inputs[0])
wl.new(ramp.outputs[0], bgc.inputs[0])
wl.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
wl.new(bga.outputs[0], mix.inputs[1])
wl.new(bgc.outputs[0], mix.inputs[2])
wl.new(mix.outputs[0], out.inputs[0])

fonts = {
    "arial": bpy.data.fonts.load(os.path.join(FONT_DIR, "arial.ttf")),
    "arialb": bpy.data.fonts.load(os.path.join(FONT_DIR, "arialbd.ttf")) if os.path.exists(os.path.join(FONT_DIR, "arialbd.ttf")) else bpy.data.fonts.load(os.path.join(FONT_DIR, "arial.ttf")),
    "georgia": bpy.data.fonts.load(os.path.join(FONT_DIR, "georgia.ttf")),
}


def material(name, color, emis=0.0, rough=0.6, metal=0.0, alpha=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = color
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emis:
        p.inputs["Emission Color"].default_value = color
        p.inputs["Emission Strength"].default_value = emis
    if alpha is not None:
        p.inputs["Alpha"].default_value = alpha
    return m


def fader(m, keys):
    """Przezroczystość materiału animowana: keys = [(klatka, alfa), ...]."""
    p = m.node_tree.nodes["Principled BSDF"]
    try:
        m.surface_render_method = "DITHERED"
    except Exception:
        pass
    for f, a in keys:
        p.inputs["Alpha"].default_value = a
        p.inputs["Alpha"].keyframe_insert("default_value", frame=f)


def link(ob):
    col.objects.link(ob)
    return ob


def tekst(body, pos, size, mat, font="arialb", ax="CENTER", ay="CENTER", rot=(math.radians(90), 0, 0), ext=0.004, name=None):
    cu = bpy.data.curves.new(name or ("T_" + body[:12]), "FONT")
    cu.body = body
    cu.font = fonts[font]
    cu.size = size
    cu.align_x = ax
    cu.align_y = ay
    cu.extrude = ext
    ob = bpy.data.objects.new(cu.name, cu)
    ob.location = pos
    ob.rotation_euler = rot
    ob.data.materials.append(mat)
    return link(ob)


def box(name, size, loc, mat, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    me.materials.append(mat)
    if bevel:
        md = ob.modifiers.new("bev", "BEVEL"); md.width = bevel; md.segments = 2
    return link(ob)


def key(ob, path, frames_vals, interp="BEZIER"):
    for f, v in frames_vals:
        setattr(ob, path, v)
        ob.keyframe_insert(path, frame=f)
    if ob.animation_data and ob.animation_data.action:
        _set_interp(ob.animation_data.action, interp)


def _set_interp(action, interp):
    fcs = []
    try:
        fcs = list(action.fcurves)
    except Exception:
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    fcs.extend(cb.fcurves)
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = interp


def pop(ob, f0, dur=10, axis=None):
    """Pojawienie się przez skalowanie od zera (wygładzone)."""
    s1 = tuple(ob.scale)
    s0 = tuple(0.0001 if (axis is None or i in axis) else s1[i] for i in range(3))
    key(ob, "scale", [(1, s0), (f0, s0), (f0 + dur, s1)])


# ---------------------------------------------------------------- 1. przekrój lądolodu
L = 7.2          # połowa szerokości przekroju
H = 4.1          # grubość lodu w osi odwiertu (= ok. 3075 m)
M_NA_J = 3075.0 / H  # metrów na jednostkę w pionie


def z_pow(x):
    t = min(abs(x) / L, 1.0)
    return H * (1 - t ** (4 / 3)) ** (3 / 8)


def z_dno(x):
    return 0.18 * math.sin(x * 1.3) * (abs(x) / L) - 0.05 * math.cos(x * 3.1) * (abs(x) / L)


NX, NK = 160, 40
me = bpy.data.meshes.new("Lod")
bm = bmesh.new()
grid = []
for i in range(NX + 1):
    x = -L + 2 * L * i / NX
    zs, zb = z_pow(x), min(z_dno(x), z_pow(x))
    row = []
    for k in range(NK + 1):
        t = k / NK
        s = 1 - (1 - t) ** 1.8      # warstwy coraz cieńsze w głąb
        row.append(bm.verts.new((x, 0.0, zs - s * (zs - zb))))
    grid.append(row)
cl = bm.loops.layers.color.new("Col")
for i in range(NX):
    for k in range(NK):
        f = bm.faces.new((grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k]))
        t = k / NK
        base = np.array([0.93, 0.96, 1.0]) * (1 - t) + np.array([0.28, 0.48, 0.78]) * t
        if k % 2:
            base = base * 0.90
        if k in (NK - 1, NK - 2):
            base = np.array([0.42, 0.45, 0.52])  # lód z okruchami skalnymi przy dnie
        for lp_ in f.loops:
            lp_[cl] = (base[0], base[1], base[2], 1.0)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.normal_update()
bm.to_mesh(me); bm.free()
lod = bpy.data.objects.new("Lod", me)
link(lod)
sol = lod.modifiers.new("grub", "SOLIDIFY"); sol.thickness = 1.6; sol.offset = -1.0
m_lod = bpy.data.materials.new("lod")
m_lod.use_nodes = True
nt = m_lod.node_tree
p = nt.nodes["Principled BSDF"]
att = nt.nodes.new("ShaderNodeAttribute"); att.attribute_name = "Col"
nt.links.new(att.outputs["Color"], p.inputs["Base Color"])
nt.links.new(att.outputs["Color"], p.inputs["Emission Color"])
p.inputs["Emission Strength"].default_value = 0.25
p.inputs["Roughness"].default_value = 0.35
me.materials.append(m_lod)

# skała pod lodem
me2 = bpy.data.meshes.new("Skala")
bm = bmesh.new()
top, bot = [], []
for i in range(NX + 1):
    x = -L - 0.6 + (2 * L + 1.2) * i / NX
    zb = z_dno(max(-L, min(L, x))) if abs(x) <= L else 0.0
    top.append(bm.verts.new((x, 0, zb)))
    bot.append(bm.verts.new((x, 0, -1.3)))
for i in range(NX):
    bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
bm.to_mesh(me2); bm.free()
skala = bpy.data.objects.new("Skala", me2)
link(skala)
s2 = skala.modifiers.new("grub", "SOLIDIFY"); s2.thickness = 1.6; s2.offset = -1.0
m_sk = bpy.data.materials.new("skala"); m_sk.use_nodes = True
nt = m_sk.node_tree; p = nt.nodes["Principled BSDF"]
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0
rp = nt.nodes.new("ShaderNodeValToRGB")
rp.color_ramp.elements[0].color = srgb("#2b2622"); rp.color_ramp.elements[1].color = srgb("#5a4e44")
nt.links.new(nz.outputs["Fac"], rp.inputs[0]); nt.links.new(rp.outputs[0], p.inputs["Base Color"])
p.inputs["Roughness"].default_value = 0.9
me2.materials.append(m_sk)

# wieża wiertnicza na szczycie kopuły
m_ciem = material("wieza", srgb("#3a3f4a"), rough=0.5, metal=0.6)
m_zloto = material("zloto", srgb("#f0c46f"), emis=0.6, rough=0.3)
m_zloto_s = material("zloto_s", srgb("#f0c46f"), emis=0.35, rough=0.3)
for sx in (-1, 1):
    for sy in (-1, 1):
        a = box("noga", (0.025, 0.025, 1.0), (0, 0, 0), m_ciem)
        a.location = (sx * 0.17, -0.3 + sy * 0.17, H + 0.5)
        a.rotation_euler = (sy * -0.17, sx * 0.17, 0)
box("chatka", (0.55, 0.4, 0.22), (0.55, -0.3, H + 0.08), m_ciem)
box("szczyt", (0.12, 0.12, 0.06), (0, -0.3, H + 1.0), m_ciem)

# otwór i wiertło (przed ścianą przekroju)
import mathutils
otw = box("otwor", (0.07, 0.02, H), (0, 0, 0), material("otwor", srgb("#10161f"), rough=0.8))
otw.data.transform(mathutils.Matrix.Translation((0, 0, -H / 2)))   # początek u góry, rośnie w dół
otw.location = (0, -0.012, H)
key(otw, "scale", [(1, (1, 1, 0.0001)), (20, (1, 1, 0.0001)), (130, (1, 1, 0.985))])

wier = box("wiertlo", (0.022, 0.022, 1.0), (0, -0.05, 0), m_ciem)
wier.data.transform(mathutils.Matrix.Translation((0, 0, -0.5)))
wier.location = (0, -0.05, H + 1.0)
key(wier, "scale", [(1, (1, 1, 1.0)), (20, (1, 1, 1.0)), (130, (1, 1, H + 1.0 - 0.06))])
grot = bpy.data.meshes.new("grot")
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.0, radius2=0.06, depth=0.16)
bm.to_mesh(grot); bm.free()
grot_o = link(bpy.data.objects.new("grot", grot))
grot_o.data.materials.append(m_zloto)
key(grot_o, "location", [(1, (0, -0.05, H + 0.02)), (20, (0, -0.05, H + 0.02)), (130, (0, -0.05, 0.12))])
sw = bpy.data.lights.new("swiatlo_grotu", "POINT"); sw.energy = 2.5; sw.color = srgb("#f0c46f")[:3]; sw.shadow_soft_size = 0.1
swo = link(bpy.data.objects.new("swiatlo_grotu", sw)); swo.parent = grot_o; swo.location = (0, -0.25, 0)

# skala głębokości przy otworze
m_bial = material("bialy", srgb("#e8edf5"), emis=1.0, rough=0.5)
for d, f in ((1000, 56), (2000, 92), (3000, 128)):
    z = H - d / M_NA_J
    kr = box("kreska%d" % d, (0.22, 0.01, 0.012), (0.2, -0.06, z), m_bial)
    t = tekst("%d m" % d, (0.42, -0.06, z), 0.24, m_bial, font="arialb", ax="LEFT")
    pop(kr, f, 8, axis=(0,)); pop(t, f, 8)
# złoty nawias 1000–3000 m (zakres wykresu)
z1, z3 = H - 1000 / M_NA_J, H - 3000 / M_NA_J
naw = box("nawias", (0.03, 0.012, (z1 - z3)), (-0.22, -0.06, (z1 + z3) / 2), m_zloto)
pop(naw, 132, 14, axis=(2,))
for z in (z1, z3):
    b = box("nawias_k", (0.14, 0.012, 0.03), (-0.16, -0.06, z), m_zloto); pop(b, 132, 14)

# cały przekrój zjeżdża w dół, gdy kamera przechodzi do wykresu
przekroj = link(bpy.data.objects.new("Przekroj", None))
for ob in list(col.objects):
    if ob is not przekroj and ob.parent is None:
        ob.parent = przekroj
key(przekroj, "location", [(1, (0, 0, 0)), (225, (0, 0, 0)), (275, (0, 0, -4.0))])

# ---------------------------------------------------------------- 2. wykres (z rysunku Leszka)
W_PX, H_PX = 600, 280
K = 13.0 / W_PX            # jednostek na piksel rysunku
X0 = 0.0                   # środek wykresu w X
Z0 = 6.55                  # dolna krawędź wykresu
YF = -0.02                 # płaszczyzna przednia tablicy


def P(x, y, dy=0.0):
    return Vector(((x - W_PX / 2) * K + X0, YF - dy, Z0 + (H_PX - y) * K))


wykres = bpy.data.objects.new("Wykres", None)
link(wykres)
wykres.location = P(W_PX / 2, H_PX)  # punkt obrotu: dół tablicy
wykres.location.y = 0
bpy.context.view_layer.update()


def do_wykresu(ob):
    mw = ob.matrix_world.copy()
    ob.parent = wykres
    ob.matrix_parent_inverse = wykres.matrix_world.inverted()
    return ob


m_tab = material("tablica", rgb255(194, 194, 194), emis=0.12, rough=0.8)
m_siat = material("siatka", rgb255(92, 92, 92), emis=0.3, rough=0.7)
m_czar = material("czarny", rgb255(12, 12, 12), rough=0.6)
m_pas = material("pas", rgb255(226, 224, 236), emis=0.9, rough=0.6)
m_krz = material("krzywa", rgb255(38, 32, 128), emis=0.9, rough=0.4)
for m_ in (m_tab, m_siat, m_czar, m_pas):
    fader(m_, [(1, 0.0), (205, 0.0), (232, 1.0)])

c = P(300, 140)
tab = box("tablica", (W_PX * K + 0.1, 0.16, H_PX * K + 0.1), (c.x, 0.08, c.z), m_tab, bevel=0.04)
do_wykresu(tab)
# poziome linie siatki (co 1°C)
GY = [37, 53, 68, 84, 99, 114, 130, 145, 160, 176, 191, 207, 222]
for y in GY[1:]:
    a, b = P(35, y), P(565, y)
    do_wykresu(box("siatka_h", ((b.x - a.x), 0.01, 0.014), ((a + b) / 2), m_siat))
for (x1, x2) in ((35, 86), (521, 565)):     # górna linia przerwana tytułem
    a, b = P(x1, 37), P(x2, 37)
    do_wykresu(box("siatka_t", ((b.x - a.x), 0.01, 0.014), ((a + b) / 2), m_siat))
GX = {250: 35, 150: 66, 100: 106, 50: 193, 40: 228, 30: 270, 20: 321, 16: 352, 12: 395, 10: 429, 0: 565}
for v, x in GX.items():
    a, b = P(x, 37), P(x, 236)
    do_wykresu(box("siatka_v", (0.014, 0.01, (a.z - b.z)), ((a + b) / 2), m_siat))
    do_wykresu(tekst(str(v), P(x, 16, 0.01), 0.30, m_czar))
# biały pas 12–10 tys. lat (na rysunku jasny prostokąt)
a, b = P(418, 44), P(428, 235)
pas = do_wykresu(box("pas", (b.x - a.x, 0.008, a.z - b.z), ((a + b) / 2) + Vector((0, 0.003, 0)), m_pas))
fader_pas = material("pas2", rgb255(222, 220, 232), emis=0.2)
pas.data.materials[0] = fader_pas
fader(fader_pas, [(1, 0.0), (340, 0.0), (358, 1.0)])
# oś dolna i podziałka głębokości
a, b = P(35, 250), P(565, 250)
do_wykresu(box("os", (b.x - a.x, 0.01, 0.022), (a + b) / 2, m_czar))
for v, x in ((3000, 35), (2500, 168), (2000, 300), (1500, 433), (1000, 563)):
    a, b = P(x, 250), P(x, 256)
    do_wykresu(box("tick", (0.018, 0.01, a.z - b.z), (a + b) / 2, m_czar))
    do_wykresu(tekst(str(v), P(x, 266, 0.01), 0.30, m_czar))
do_wykresu(tekst("PRZYBLIŻONY WIEK PRÓBKI, DLA KTÓREJ OKREŚLONO ŚREDNIĄ TEMPERATURĘ (w tys. lat)", P(303.5, 35, 0.01), 0.178, m_czar))
do_wykresu(tekst("GŁĘBOKOŚĆ ODWIERTU, Z KTÓREJ POBRANO PRÓBKĘ LĄDOLODU (w m.)", P(309, 243.5, 0.01), 0.178, m_czar))
t = do_wykresu(tekst("ZMIANA TEMPERATURY O 1 STOPIEŃ CELSJUSZA", P(578, 131, 0.01), 0.170, m_czar))
t.rotation_euler = (mathutils.Matrix.Rotation(math.radians(90), 4, "X") @ mathutils.Matrix.Rotation(math.radians(90), 4, "Z")).to_euler()

# --- krzywa: odczyt z rysunku
im = bpy.data.images.load(RYSUNEK)
w, h = im.size
px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1] * 255
r_, g_, b_ = px[..., 0], px[..., 1], px[..., 2]
nieb = (b_ - r_ > 25) & (b_ - g_ > 20) & (r_ < 170)
nieb[:40, :] = False
nieb[240:, :] = False
kol = []
for x in range(36, 565):
    ys = np.nonzero(nieb[:, x])[0]
    kol.append((x, ys.min(), ys.max()) if len(ys) else None)
# uzupełnij luki liniowo między sąsiednimi kolumnami
luki = [i for i, k_ in enumerate(kol) if k_ is None]
print("LUKI_W_KRZYWEJ", len(luki), luki[:40])
znane = [i for i, k_ in enumerate(kol) if k_ is not None]
for i in luki:
    a_ = max([j for j in znane if j < i], default=None); b2 = min([j for j in znane if j > i], default=None)
    if a_ is None: a_ = b2
    if b2 is None: b2 = a_
    t_ = 0 if b2 == a_ else (i - a_) / (b2 - a_)
    ym = (kol[a_][1] + kol[a_][2]) / 2 * (1 - t_) + (kol[b2][1] + kol[b2][2]) / 2 * t_
    kol[i] = (36 + i, ym, ym)
punkty = []
prev = kol[0][1]
for (x, y0, y1) in kol:
    if abs(prev - y0) <= abs(prev - y1):
        seq = (y0, y1)
    else:
        seq = (y1, y0)
    punkty.append((x - 0.25, seq[0] + 0.5)); punkty.append((x + 0.25, seq[1] + 0.5))
    prev = seq[1]
cu = bpy.data.curves.new("krzywa", "CURVE")
cu.dimensions = "3D"
sp = cu.splines.new("POLY")
sp.points.add(len(punkty) - 1)
for i, (x, y) in enumerate(punkty):
    v = P(x, y, 0.03)
    sp.points[i].co = (v.x, v.y, v.z, 1)
cu.bevel_depth = 0.019
cu.bevel_resolution = 2
krz = link(bpy.data.objects.new("krzywa", cu))
krz.data.materials.append(m_krz)
do_wykresu(krz)

# krzywa odsłaniana maską (X obiektu < wartość), w tym samym tempie co skaner
x_a, x_b = P(36, 0).x, P(564, 0).x
nt = m_krz.node_tree
pk = nt.nodes["Principled BSDF"]
tck = nt.nodes.new("ShaderNodeTexCoord"); sxk = nt.nodes.new("ShaderNodeSeparateXYZ")
odk = nt.nodes.new("ShaderNodeValue"); odk.name = "odkrycie"
lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"
nt.links.new(tck.outputs["Object"], sxk.inputs[0]); nt.links.new(sxk.outputs["X"], lt.inputs[0])
nt.links.new(odk.outputs[0], lt.inputs[1]); nt.links.new(lt.outputs[0], pk.inputs["Alpha"])
m_krz.surface_render_method = "DITHERED"
for f, v in ((1, x_a - 0.2), (248, x_a - 0.2), (345, x_b + 0.2)):
    odk.outputs[0].default_value = v
    odk.outputs[0].keyframe_insert("default_value", frame=f)
_set_interp(nt.animation_data.action, "LINEAR")

# skaner: pionowa złota linia od rdzenia do krzywej, idzie razem z rysowaniem
x_a, x_b = P(36, 0).x, P(564, 0).x
z_lo, z_hi = Z0 - 0.12, P(0, 40).z
sk = box("skaner", (0.022, 0.01, z_hi - z_lo), (x_a, YF - 0.05, (z_lo + z_hi) / 2), m_zloto_s)
zc_sk = (z_lo + z_hi) / 2
key(sk, "location", [(1, (x_a, YF - 0.05, zc_sk)), (248, (x_a, YF - 0.05, zc_sk)), (345, (x_b, YF - 0.05, zc_sk))], interp="LINEAR")
key(sk, "scale", [(1, (0, 0, 0)), (246, (0, 0, 0)), (250, (1, 1, 1)), (343, (1, 1, 1)), (350, (0, 0, 0))])

# klamra „ok. 7°C” (z tekstu Leszka: wzrost o ok. 7°C między 12 a 10 tys. lat)
m_zl2 = material("zloto_klamra", srgb("#e0a640"), emis=0.45)
fader(m_zl2, [(1, 0.0), (350, 0.0), (368, 1.0)])
ya, yb = 98, 193
for (x1, x2, y) in ((392, 452, yb), (428, 452, ya)):
    a, b = P(x1, y, 0.04), P(x2, y, 0.04)
    do_wykresu(box("klamra_h", (b.x - a.x, 0.01, 0.016), (a + b) / 2, m_zl2))
a, b = P(450, ya, 0.04), P(450, yb, 0.04)
do_wykresu(box("klamra_v", (0.03, 0.01, a.z - b.z), (a + b) / 2, m_zl2))
do_wykresu(tekst("ok. 7°C", P(458, 146, 0.04), 0.36, m_zl2, ax="LEFT"))

# wykres wyrasta od dołu
key(wykres, "scale", [(1, (1, 1, 0.0001)), (205, (1, 1, 0.0001)), (240, (1, 1, 1))])

# ---------------------------------------------------------------- 3. rdzeń lodowy
m_rdz = bpy.data.materials.new("rdzen"); m_rdz.use_nodes = True
nt = m_rdz.node_tree; p = nt.nodes["Principled BSDF"]
tcn = nt.nodes.new("ShaderNodeTexCoord")
sepn = nt.nodes.new("ShaderNodeSeparateXYZ")
wave = nt.nodes.new("ShaderNodeTexWave"); wave.inputs["Scale"].default_value = 3.0
wave.bands_direction = "Z"; wave.inputs["Distortion"].default_value = 1.5
rp = nt.nodes.new("ShaderNodeValToRGB")
rp.color_ramp.elements[0].color = (0.55, 0.72, 0.95, 1); rp.color_ramp.elements[1].color = (0.92, 0.96, 1.0, 1)
nt.links.new(tcn.outputs["Object"], wave.inputs["Vector"])
nt.links.new(wave.outputs["Fac"], rp.inputs[0])
nt.links.new(rp.outputs[0], p.inputs["Base Color"])
nt.links.new(rp.outputs[0], p.inputs["Emission Color"])
p.inputs["Emission Strength"].default_value = 0.15
p.inputs["Roughness"].default_value = 0.15
p.inputs["Coat Weight"].default_value = 0.6
LR = (3000 - 1000) / M_NA_J   # długość rdzenia (1000–3000 m)
rme = bpy.data.meshes.new("rdzen")
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.11, radius2=0.11, depth=1.0)
bm.to_mesh(rme); bm.free()
rdz = link(bpy.data.objects.new("rdzen", rme))
rdz.data.materials.append(m_rdz)
zc0 = H - 2000 / M_NA_J
x_mid = (P(35, 0).x + P(565, 0).x) / 2
L_os = P(565, 0).x - P(35, 0).x
ZR = Z0 - 0.22
key(rdz, "location", [(1, (0, -0.25, zc0)), (160, (0, -0.25, zc0)), (200, (0, -0.6, H + LR / 2 + 0.6)),
                      (240, (x_mid, -0.6, ZR))])
key(rdz, "rotation_euler", [(1, (0, 0, 0)), (185, (0, 0, 0)), (235, (0, math.radians(90), 0))])
key(rdz, "scale", [(1, (0.0001, 0.0001, LR)), (150, (0.0001, 0.0001, LR)), (162, (1, 1, LR)), (200, (1, 1, LR)),
                   (240, (1, 1, L_os))])
# podpisy końców rdzenia nie są potrzebne: oś wykresu ma liczby Leszka

# ---------------------------------------------------------------- światło i kamera
sun = bpy.data.lights.new("slonce", "SUN"); sun.energy = 2.2; sun.angle = math.radians(8)
so = link(bpy.data.objects.new("slonce", sun)); so.rotation_euler = (math.radians(55), math.radians(-25), math.radians(-20))
fill = bpy.data.lights.new("wypelnienie", "AREA"); fill.energy = 1500; fill.size = 14
fo = link(bpy.data.objects.new("wypelnienie", fill)); fo.location = (-4, -14, 9); fo.rotation_euler = (math.radians(70), 0, math.radians(-15))

cam = bpy.data.cameras.new("kamera"); cam.lens = 40; cam.clip_end = 300
co = link(bpy.data.objects.new("kamera", cam)); sc.camera = co
cel = link(bpy.data.objects.new("cel", None))
tr = co.constraints.new("TRACK_TO"); tr.target = cel; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
key(co, "location", [(1, (-2.4, -19.5, 3.4)), (140, (-0.8, -17.0, 2.9)), (200, (0.3, -16.0, 6.5)), (250, (-1.2, -18.4, 7.65)), (KLATEK, (-0.4, -18.0, 7.75))])
key(cel, "location", [(1, (0, 0, 2.0)), (140, (0, 0, 1.9)), (200, (0, 0, 6.5)), (250, (0.35, 0, 8.65)), (KLATEK, (0.4, 0, 8.7))])

# ---------------------------------------------------------------- render
KLATKI = os.path.join(TU, "_klatki")
os.makedirs(KLATKI, exist_ok=True)
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"


def ffmpeg():
    f = shutil.which("ffmpeg")
    if f:
        return f
    import glob
    g = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe"))
    return g[0]


if TEST:
    os.makedirs(os.path.join(KLATKI, "test"), exist_ok=True)
    for f in TEST:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(KLATKI, "test", "t%04d.png" % f)
        bpy.ops.render.render(write_still=True)
else:
    blok = os.path.join(WIDEO, ".renderuje")
    if os.path.exists(blok):
        print("BLOKADA: istnieje", blok, open(blok, encoding="utf-8").read())
        sys.exit(2)
    with open(blok, "w", encoding="utf-8") as fh:
        fh.write(NAZWA)
    try:
        t0 = time.time()
        sc.render.filepath = os.path.join(KLATKI, "k")
        bpy.ops.render.render(animation=True)
        print("CZAS_RENDERU_S", round(time.time() - t0))
    finally:
        os.remove(blok)
    ff = ffmpeg()
    subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(KLATKI, "k%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-an", os.path.join(TU, "klip.mp4")], check=True)
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", os.path.join(KLATKI, "k%04d.png" % KLATEK), "-vf", "scale=1600:-2",
                    "-q:v", "2", os.path.join(TU, "kadr.jpg")], check=True)
    print("GOTOWE", os.path.join(TU, "klip.mp4"))
