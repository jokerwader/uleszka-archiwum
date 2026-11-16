# -*- coding: utf-8 -*-
"""
Klip „slone-jeziora” do odcinka 2 „Wielki uskok…”.

Mapa świata jak na rysunku Leszka (zrodlo/webacja/02uskok/slonejeziora.jpg): zdjęcie satelitarne lądów,
szaroniebieskie morza, żółte trójkątne wskaźniki i białe podpisy. Ten sam wycinek świata co na rysunku
(odwzorowanie równoodległościowe, ok. 144°W–174°E, 80°N–50°S). Wskaźniki i podpisy stoją dokładnie tam,
gdzie na rysunku: ich położenia odczytano z pikseli rysunku (żółte trójkąty) i przeliczono na mapę.

Tekstura: NASA Blue Marble 2002 (domena publiczna), grafiki/3d/wideo/_dane/blue-marble/.

Uruchomienie:
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/slone-jeziora/scena.py
  ... -- --test 1,100,250,400
"""
import bpy, bmesh, math, os, sys, shutil, subprocess, time, glob
from mathutils import Vector, Matrix

TU = os.path.dirname(os.path.abspath(__file__))
WIDEO = os.path.dirname(TU)
NAZWA = os.path.basename(TU)
TEKSTURA = os.path.join(WIDEO, "_dane", "blue-marble", "blue-marble-2002-8192x4096.jpg")
FONT_DIR = r"C:\Windows\Fonts"
FPS = 25
KLATEK = 400  # 16 s

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TEST = [int(v) for v in argv[argv.index("--test") + 1].split(",")] if "--test" in argv else None


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c) + (1.0,)


def rgb255(r, g, b):
    return srgb("%02x%02x%02x" % (r, g, b))


# ---------------------------------------------------------------- odwzorowanie rysunku Leszka
# Rysunek 600×247 px. Dopasowanie (Salt Lake, Uyuni, M. Martwe): 1,8905 px na stopień długości,
# 1,899 px na stopień szerokości; lewa krawędź 143,8°W, górna 79,8°N.
RW, RH = 600, 247
LON0, DLON = -143.77, 1 / 1.8905
LAT0, DLAT = 79.83, 1 / 1.899
S = 0.0529       # jednostek Blendera na piksel rysunku (mapa 31,7 × 13,1)


def px2xy(px, py, z=0.0):
    return Vector(((px - RW / 2) * S, (RH / 2 - py) * S, z))


# Wskaźniki: grot i podstawa żółtego trójkąta (odczytane z pikseli rysunku), środek podpisu i jego tekst.
# Kolejność pojawiania się: najpierw obie Ameryki, potem Bliski Wschód i Azja.
JEZIORA = [
    # nazwa na rysunku,            grot,           podstawa,       środek podpisu,  klatka
    ("Salt Lake",                 (59.1, 73.6),  (79.3, 77.7),  (102.5, 81.5),   28),
    ("Wielka pustynia słona",     (58.2, 78.7),  (75.1, 91.6),  (85.0, 103.0),   52),
    ("Titicaca",                  (140.7, 174.9), (145.7, 156.9), (147.0, 150.5), 84),
    ("Salar del Uyuni",           (145.0, 190.0), (166.0, 189.1), (202.5, 189.0), 108),
    ("m. Martwe",                 (338.9, 85.1), (322.4, 75.4),  (310.0, 67.0),   182),
    ("m. Kaspijskie",             (363.0, 58.0), (351.0, 42.2),  (336.0, 33.5),   206),
    ("m. Aralskie",               (393.3, 56.2), (403.4, 38.1),  (419.5, 30.5),   230),
    ("jez. Bałchasz",             (423.8, 64.3), (441.2, 77.1),  (470.0, 87.5),   254),
    ("Wielka pustynia słona",     (381.3, 94.8), (390.9, 112.5), (405.5, 122.5),  278),
]

# ---------------------------------------------------------------- scena
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, KLATEK
sc.eevee.taa_render_samples = 48
sc.view_settings.view_transform = "Standard"
col = sc.collection


def link(ob):
    col.objects.link(ob)
    return ob


world = bpy.data.worlds.new("Swiat"); sc.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
wn.clear()
out = wn.new("ShaderNodeOutputWorld"); tc = wn.new("ShaderNodeTexCoord"); sep = wn.new("ShaderNodeSeparateXYZ")
ramp = wn.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = srgb("#05070c"); ramp.color_ramp.elements[1].color = srgb("#1b2a4d")
bgc = wn.new("ShaderNodeBackground"); bga = wn.new("ShaderNodeBackground")
bga.inputs[0].default_value = srgb("#3a4560"); bga.inputs[1].default_value = 0.5
lp = wn.new("ShaderNodeLightPath"); mix = wn.new("ShaderNodeMixShader")
wl.new(tc.outputs["Window"], sep.inputs[0]); wl.new(sep.outputs["Y"], ramp.inputs[0]); wl.new(ramp.outputs[0], bgc.inputs[0])
wl.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); wl.new(bga.outputs[0], mix.inputs[1]); wl.new(bgc.outputs[0], mix.inputs[2])
wl.new(mix.outputs[0], out.inputs[0])

f_arialb = bpy.data.fonts.load(os.path.join(FONT_DIR, "arialbd.ttf"))


def material(name, color, emis=0.0, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = color; p.inputs["Roughness"].default_value = rough
    if emis:
        p.inputs["Emission Color"].default_value = color; p.inputs["Emission Strength"].default_value = emis
    return m


def _fcurves(action):
    try:
        return list(action.fcurves)
    except Exception:
        out_ = []
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out_.extend(cb.fcurves)
        return out_


def key(ob, path, fv):
    for f, v in fv:
        setattr(ob, path, v); ob.keyframe_insert(path, frame=f)


# ---------------------------------------------------------------- mapa
W, H = RW * S, RH * S
me = bpy.data.meshes.new("mapa")
NXm, NYm = 120, 50
bm = bmesh.new()
uv = bm.loops.layers.uv.new("UV")
vs = [[bm.verts.new(((i / NXm - 0.5) * W, (0.5 - j / NYm) * H, 0)) for i in range(NXm + 1)] for j in range(NYm + 1)]
for j in range(NYm):
    for i in range(NXm):
        f = bm.faces.new((vs[j][i], vs[j + 1][i], vs[j + 1][i + 1], vs[j][i + 1]))
        for l, (ii, jj) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
            px, py = ii / NXm * RW, jj / NYm * RH
            lon, lat = LON0 + px * DLON, LAT0 - py * DLAT
            l[uv].uv = ((lon + 180) / 360, (lat + 90) / 180)
bm.normal_update(); bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
mapa = link(bpy.data.objects.new("mapa", me))
sol = mapa.modifiers.new("grub", "SOLIDIFY"); sol.thickness = 0.35; sol.offset = -1.0
sol.material_offset = 1

m_map = bpy.data.materials.new("mapa"); m_map.use_nodes = True
nt = m_map.node_tree; N, Lk = nt.nodes, nt.links
pr = N["Principled BSDF"]
img = N.new("ShaderNodeTexImage"); img.image = bpy.data.images.load(TEKSTURA); img.interpolation = "Cubic"
uvn = N.new("ShaderNodeUVMap"); uvn.uv_map = "UV"
Lk.new(uvn.outputs[0], img.inputs[0])
# maska morza: kolor wyraźnie niebieski (b > r, g) -> kolor morza z rysunku Leszka
sp = N.new("ShaderNodeSeparateColor")
Lk.new(img.outputs["Color"], sp.inputs[0])
mx = N.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
Lk.new(sp.outputs[0], mx.inputs[0]); Lk.new(sp.outputs[1], mx.inputs[1])
d = N.new("ShaderNodeMath"); d.operation = "SUBTRACT"
Lk.new(sp.outputs[2], d.inputs[0]); Lk.new(mx.outputs[0], d.inputs[1])
mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.015; mr.inputs["From Max"].default_value = 0.05
Lk.new(d.outputs[0], mr.inputs["Value"])
mixc = N.new("ShaderNodeMix"); mixc.data_type = "RGBA"
Lk.new(mr.outputs[0], mixc.inputs["Factor"])
# ląd lekko rozjaśniony jak na rysunku
bc = N.new("ShaderNodeBrightContrast"); bc.inputs["Bright"].default_value = 0.03; bc.inputs["Contrast"].default_value = 0.05
Lk.new(img.outputs["Color"], bc.inputs["Color"])
Lk.new(bc.outputs[0], mixc.inputs[6])
mixc.inputs[7].default_value = rgb255(80, 84, 118)
Lk.new(mixc.outputs[2], pr.inputs["Base Color"])
Lk.new(mixc.outputs[2], pr.inputs["Emission Color"])
pr.inputs["Emission Strength"].default_value = 0.55
pr.inputs["Roughness"].default_value = 0.75
# delikatna rzeźba lądów z jasności zdjęcia (tylko na lądzie)
inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
Lk.new(mr.outputs[0], inv.inputs[1])
bw = N.new("ShaderNodeRGBToBW"); Lk.new(img.outputs["Color"], bw.inputs[0])
mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
Lk.new(bw.outputs[0], mul.inputs[0]); Lk.new(inv.outputs[0], mul.inputs[1])
bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25; bump.inputs["Distance"].default_value = 0.02
Lk.new(mul.outputs[0], bump.inputs["Height"]); Lk.new(bump.outputs[0], pr.inputs["Normal"])
me.materials.append(m_map)
me.materials.append(material("bok_mapy", srgb("#0e1424"), rough=0.5))

# ---------------------------------------------------------------- wskaźniki i podpisy
m_zol = material("zolty", rgb255(255, 236, 0), emis=0.9, rough=0.4)
m_bia = material("bialy", rgb255(255, 255, 255), emis=1.0, rough=0.5)
m_cien = material("cien", rgb255(10, 12, 20), rough=0.9)
for m_ in (m_bia, m_cien):
    m_.surface_render_method = "DITHERED"


def klin(tip, base, f0, name):
    """Żółty trójkąt: grot w jeziorze, podstawa od strony podpisu. Wyrasta od grotu."""
    t, b = px2xy(*tip), px2xy(*base)
    v = b - t
    L = v.length
    # na rysunku podstawa ma ok. 6 px szerokości
    half = 3.2 * S
    me_ = bpy.data.meshes.new(name); bm_ = bmesh.new()
    a0 = bm_.verts.new((0, 0, 0)); a1 = bm_.verts.new((L, half, 0)); a2 = bm_.verts.new((L, -half, 0))
    bm_.faces.new((a0, a1, a2))
    bm_.to_mesh(me_); bm_.free()
    ob = link(bpy.data.objects.new(name, me_))
    sol_ = ob.modifiers.new("g", "SOLIDIFY"); sol_.thickness = 0.06; sol_.offset = 1.0
    me_.materials.append(m_zol)
    ob.location = (t.x, t.y, 0.02)
    ob.rotation_euler = (0, 0, math.atan2(v.y, v.x))
    key(ob, "scale", [(1, (0.0001, 0.0001, 1)), (f0, (0.0001, 0.0001, 1)), (f0 + 9, (1.0, 1.0, 1))])
    return ob


def podpis(txt, c, f0, name):
    pos = px2xy(*c)
    obs = []
    for (dx, dy, dz, m_, nm) in ((0.035, -0.035, 0.05, m_cien, "_cien"), (0, 0, 0.07, m_bia, "")):
        cu = bpy.data.curves.new(name + nm, "FONT")
        cu.body = txt; cu.font = f_arialb; cu.size = 0.56; cu.align_x = "CENTER"; cu.align_y = "CENTER"
        cu.extrude = 0.012
        ob = link(bpy.data.objects.new(name + nm, cu))
        ob.location = (pos.x + dx, pos.y + dy, dz)
        cu.materials.append(m_.copy())
        mm = cu.materials[0]
        mm.surface_render_method = "DITHERED"
        p = mm.node_tree.nodes["Principled BSDF"]
        for f, a in ((1, 0.0), (f0 + 4, 0.0), (f0 + 14, 0.85 if nm else 1.0)):
            p.inputs["Alpha"].default_value = a
            p.inputs["Alpha"].keyframe_insert("default_value", frame=f)
        key(ob, "scale", [(1, (0.85, 0.85, 1)), (f0 + 4, (0.85, 0.85, 1)), (f0 + 14, (1, 1, 1))])
        obs.append(ob)
    return obs


for i, (txt, tip, base, c, f0) in enumerate(JEZIORA):
    klin(tip, base, f0, "klin_%d" % i)
    podpis(txt, c, f0, "podpis_%d" % i)
    # krótki błysk w miejscu jeziora
    ls = bpy.data.lights.new("blysk_%d" % i, "POINT"); ls.color = (1, 0.93, 0.5); ls.shadow_soft_size = 0.05
    lo = link(bpy.data.objects.new("blysk_%d" % i, ls)); lo.location = px2xy(*tip, 0.35)
    for f, e in ((1, 0), (f0, 0), (f0 + 5, 6.0), (f0 + 22, 0.0)):
        ls.energy = e; ls.keyframe_insert("energy", frame=f)

# ---------------------------------------------------------------- światło i kamera
sun = bpy.data.lights.new("slonce", "SUN"); sun.energy = 1.6; sun.angle = math.radians(3)
so = link(bpy.data.objects.new("slonce", sun)); so.rotation_euler = (math.radians(35), math.radians(20), math.radians(-30))

cam = bpy.data.cameras.new("kamera"); cam.lens = 40; cam.clip_end = 400
co = link(bpy.data.objects.new("kamera", cam)); sc.camera = co
cel = link(bpy.data.objects.new("cel", None))
tr = co.constraints.new("TRACK_TO"); tr.target = cel; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"

am = px2xy(132, 150)     # obie Ameryki (z podpisem Salar del Uyuni)
az = px2xy(385, 75)      # Bliski Wschód i Azja Środkowa
cal = px2xy(300, 140.5)    # cała mapa (podniesiona, bo dół kadru jest na podpis filmu)
key(cel, "location", [(1, am + Vector((-0.5, 1.6, 0))), (140, am + Vector((0, 0, 0))), (205, az), (285, az + Vector((0.4, 0.1, 0))),
                      (345, cal), (KLATEK, cal + Vector((0.15, 0, 0)))])
key(co, "location", [(1, am + Vector((-2.0, -9.0, 12.0))), (140, am + Vector((0.0, -10.2, 12.6))), (205, az + Vector((-1.0, -9.5, 10.5))),
                     (285, az + Vector((0.2, -9.0, 10.2))), (345, cal + Vector((0, -12.5, 38.5))), (KLATEK, cal + Vector((0.3, -12.2, 38.0)))])

# ---------------------------------------------------------------- render
KLATKI = os.path.join(TU, "_klatki"); os.makedirs(KLATKI, exist_ok=True)
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGB"


def ffmpeg():
    return shutil.which("ffmpeg") or glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe"))[0]


if TEST:
    os.makedirs(os.path.join(KLATKI, "test"), exist_ok=True)
    for f in TEST:
        sc.frame_set(f); sc.render.filepath = os.path.join(KLATKI, "test", "t%04d.png" % f)
        bpy.ops.render.render(write_still=True)
else:
    blok = os.path.join(WIDEO, ".renderuje")
    if os.path.exists(blok):
        print("BLOKADA: istnieje", blok); sys.exit(2)
    open(blok, "w", encoding="utf-8").write(NAZWA)
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
