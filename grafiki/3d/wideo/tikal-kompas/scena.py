# -*- coding: utf-8 -*-
"""
Klip „tikal-kompas” do odcinka 2 „Wielki uskok…”.

Plan Tikal w 3D w stylu szkicu Leszka (zrodlo/webacja/02uskok/tikal.jpg): miętowe tło, czarne bryły
z białym obrysem, czerwone linie przerywane, granatowa strzałka „Pn”.
  1. budowle wyrastają z planu,
  2. gruba czerwona linia przerywana: dzisiejsza północ (jak na szkicu, przez Plac Główny),
  3. cieńsza czerwona linia przerywana: drugi kierunek ze szkicu, na wschód od północy,
  4. nad Świątynią I róża wiatrów; jej igła obraca się o 17° na północny wschód (kompas z cytatu Daenikena),
  5. trójkąt świątyń IV, I i V z cytatu Daenikena (kąt prosty przy Świątyni I).

Położenia budowli: wektorowy plan „Tikal map vector.svg” (Simon Burchell, Wikimedia Commons, CC BY-SA 3.0),
przeliczony na metry tak, by świątynie I–V i Mundo Perdido leżały tam, gdzie w klipie „tikal-przelot”
(te same współrzędne świątyń, z Wikipedii). Szczegóły i porównanie ze szkicem Leszka w README.md.

Uruchomienie:
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/tikal-kompas/scena.py
  ... -- --test 1,120,250,425
"""
import bpy, bmesh, math, os, sys, shutil, subprocess, time, glob, re
import numpy as np
from mathutils import Vector, Matrix

TU = os.path.dirname(os.path.abspath(__file__))
WIDEO = os.path.dirname(TU)
NAZWA = os.path.basename(TU)
FONT_DIR = r"C:\Windows\Fonts"
FPS = 25
KLATEK = 425  # 17 s
KAT = 17.0    # stopni: obrót igły kompasu (cytat Daenikena)
DRUGI = 45.0  # stopni: kierunek cieńszej linii na szkicu Leszka (zmierzony na tikal.jpg)
PRZEW = 1.4   # przewyższenie wysokości budowli (plan ma ok. 1,5 km, świątynie do 65 m)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TEST = [int(v) for v in argv[argv.index("--test") + 1].split(",")] if "--test" in argv else None


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c) + (1.0,)


def rgb255(r, g, b):
    return srgb("%02x%02x%02x" % (r, g, b))


# ---------------------------------------------------------------- dane planu (z Tikal_map_vector.svg, jednostki SVG)
SWIATYNIE = {  # metry (x = wschód, y = północ), jak w klipie tikal-przelot; wysokość całkowita [m], bok podstawy [m]
    "I": ((52, -1), 47, 32), "II": ((-54, 0), 38, 41), "III": ((-254, -15), 55, 42),
    "IV": ((-662, 163), 65, 64), "V": ((-6, -283), 57, 40),
}
SVG_SW = {"I": (9351.5, 12651.5), "II": (8061, 12541.5), "III": (5627, 13043), "IV": (578.6, 11273), "V": (8873, 15778.5)}
MP_SVG, MP_M = (4394, 15880), (-452, -241)   # Mundo Perdido 5C-54


def rect(x, y, w, h, m=None):
    pts = [(0, 0), (w, 0), (w, h), (0, h)]
    if m is None:
        return [(x + a, y + b) for a, b in pts]
    a, b, c, d, e, f = m
    return [(a * px + c * py + e, b * px + d * py + f) for px, py in pts]


def poly(s):
    v = [float(t) for t in re.split(r"[ ,]+", s.strip())]
    return list(zip(v[0::2], v[1::2]))


def path_outer(d):
    """Pierwszy (zewnętrzny) obrys ścieżki SVG z poleceniami M/l/z (współrzędne względne)."""
    tok = re.findall(r"[MmLlZz]|-?\d+\.?\d*", d)
    pts, cur, cmd, i = [], None, None, 0
    while i < len(tok):
        t = tok[i]
        if t in "MmLlZz":
            if t in "Zz":
                break
            cmd = t; i += 1; continue
        x, y = float(tok[i]), float(tok[i + 1]); i += 2
        if cmd == "M" or cur is None:
            cur = (x, y)
        else:
            cur = (cur[0] + x, cur[1] + y)
        pts.append(cur)
    return pts


# (nazwa, wielokąt SVG, wysokość [m], rodzaj) — rodzaj: "bud" bryła, "plac" niski plac
PLAN = [
    ("Plac_Glowny", poly("8315,12956 8388,12078 9165,12171 9077,13017"), 1.0, "plac"),
    ("Akropol_Pn_1", poly("8554,11161 9308,11243 9259,11664 8505,11582"), 14, "bud"),
    ("Akropol_Pn_2", poly("8105,11527 9469,11691 9403,12200 8040,12036"), 9, "bud"),
    ("Akropol_Pn_3", rect(7158, 11161, 515, 295), 8, "bud"),
    ("Akropol_Centralny", poly("10480,13219 10480,13222 10480,13111 10801,13111 10801,13165 11486,13212 11469,13463 10866,13426 10866,13514 10947,13514 10947,13832 10900,13832 10873,14242 8735,14093 8767,13753 8394,13753 8394,13407 8025,13407 8025,13485 7636,13485 7636,13082 8025,13082 8025,13112 9065,13112 9065,13219"), 10, "bud"),
    ("Palac_Nietoperza", poly("3791,12939 4417,12997 4441,12699 3476,12597 3476,12879 3367,13712 3567,13753 4312,13753 4312,13492 3638,13492 3709,12984"), 8, "bud"),
    ("Grupa_N_1", rect(2303, 11981, 196, 305), 8, "bud"),
    ("Grupa_N_2", poly("1860,12458 2200,12521 2144,12824 1804,12762"), 8, "bud"),
    ("Grupa_N_3", poly("2581,12576 2862,12627 2813,12891 2532,12840"), 8, "bud"),
    ("Plac_Wsch_1", rect(10400, 12198, 224, 623), 7, "bud"),
    ("Plac_Wsch_2", rect(10702, 12414, 156, 376), 7, "bud"),
    ("Plac_Wsch_3", rect(0, 0, 678, 1037, (0.999086, 0.04274, -0.04274, 0.999086, 11045.8, 12088.7)), 3, "plac"),
    ("Plac_Wsch_4", rect(11528, 13488, 410, 407), 8, "bud"),
    ("Plac_Wsch_5", poly("12443,12604 12629,12604 12848,12604 12848,12823 12629,12823 12629,12929 12443,12929"), 7, "bud"),
    ("Plac_Wsch_6", poly("12873,12547 12389,12547 12389,12521 12094,12521 12094,12172 12389,12172 12389,12091 12870,12091 12870,12331 12416,12331 12416,12416 12873,12416"), 7, "bud"),
    ("Plac_male_1", rect(9147, 12923, 130, 215), 5, "bud"),
    ("Plac_male_2", rect(9358, 12948, 136, 219), 5, "bud"),
    ("Grupa_F", path_outer("M13406 11503l660 0 0 -27 161 -3 -22 -925 -108 3 0 -122 -749 0 0 268 -268 0 0 725 326 0 0 81z"), 8, "bud"),
    ("Grupa_G", path_outer("M12950 15230l701 0 0 183 -83 0 0 84 76 0 0 322 -132 0 0 107 29 0 0 135 242 0 0 429 -54 0 0 240 -29 0 0 163 246 0 0 188 -266 0 0 185 -161 0 0 -185 -744 0 0 -2 -144 0 0 -457 26 0 0 -400 0 -267 317 0 0 -488 139 0 0 459 210 0 0 -107 -48 0 0 -322 183 0 0 -84 -508 0 0 -183z"), 7, "bud"),
    ("Grupa_V_zach", rect(7314, 15152, 732, 942), 8, "bud"),
    ("Pd_wsch_1", rect(11312, 16602, 678, 291), 7, "bud"),
    ("Pd_wsch_2", poly("14395,16141 14632,16141 14632,16839 14686,16839 14686,17049 14225,17049 14225,16839 14395,16839"), 7, "bud"),
    ("Mundo_Perdido", poly("2949,16785 2949,15014 3136,15014 3136,15368 3508,15368 3508,14911 3239,14911 3239,14826 2861,14826 2861,14881 2760,14881 2760,16896 2844,16896 2844,16974 4877,16974 4877,17804 5070,17804 5070,17591 5358,17591 5358,17245 5070,17245 5070,16917 5473,16917 5690,16700 5636,16700 5636,16217 5727,16217 5727,15342 5873,15360 5927,14598 5704,14571 5666,15201 5443,15201 5443,15550 5307,15550 5307,15738 5443,15738 5443,15899 5311,15899 5311,16088 5443,16088 5443,16217 5443,16700 4826,16700 4826,16785"), 6, "bud"),
    ("Mundo_Perdido_5C54", rect(4069, 15477, 650, 806), 31, "piramida"),
    ("Mundo_Perdido_2", rect(4794, 14772, 495, 325), 10, "bud"),
    ("Siedem_Swiatyn", poly("6703,15501 6703,16649 6540,16649 6540,16700 5690,16700 5473,16917 5473,17645 5646,17645 5646,16917 5687,16917 5687,17184 5873,17184 5873,16917 6540,16917 6540,16971 6886,16971 6886,16951 6938,16951 6938,15501"), 6, "bud"),
    ("Siedem_Swiatyn_2", rect(6027, 15097, 169, 291), 9, "bud"),
    ("Siedem_Swiatyn_3", rect(6366, 15064, 176, 308), 9, "bud"),
]
# zespoły bliźniaczych piramid (na szkicu Leszka znak „krzyżyka” z czterech kwadratów)
for nm, rects in (("O", [(8821, 8366, 244, 244), (8445, 8071, 217, 190), (8076, 8230, 213, 295), (8340, 8637, 325, 132)]),
                  ("R", [(11494, 7295, 278, 291), (10797, 7987, 312, 274), (12165, 7959, 312, 305), (11413, 8610, 298, 156)]),
                  ("Q", [(12734, 7959, 291, 298), (13371, 7343, 333, 269), (13913, 7970, 278, 349), (13344, 8579, 407, 180)])):
    for i, r in enumerate(rects):
        PLAN.append(("Zespol_%s_%d" % (nm, i), rect(*r), 9 if i in (0, 2) else 5, "bud"))

# dopasowanie afiniczne SVG -> metry (świątynie I–V i 5C-54)
A_, B_ = [], []
for k, (xy_m, _, _) in SWIATYNIE.items():
    sx, sy = SVG_SW[k]; A_.append([sx, sy, 1]); B_.append(xy_m)
A_.append([MP_SVG[0], MP_SVG[1], 1]); B_.append(MP_M)
AFF, res, *_ = np.linalg.lstsq(np.array(A_, float), np.array(B_, float), rcond=None)
BLAD = np.sqrt(((np.array(A_) @ AFF - np.array(B_)) ** 2).sum(1))
print("DOPASOWANIE_BLAD_M", np.round(BLAD, 1))


def svg2m(p):
    v = np.array([p[0], p[1], 1.0]) @ AFF
    return (float(v[0]), float(v[1]))


# ---------------------------------------------------------------- scena
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, KLATEK
sc.eevee.taa_render_samples = 48
sc.view_settings.view_transform = "Standard"
sc.unit_settings.system = "METRIC"
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
bga.inputs[0].default_value = srgb("#4a5a70"); bga.inputs[1].default_value = 0.6
lp = wn.new("ShaderNodeLightPath"); mix = wn.new("ShaderNodeMixShader")
wl.new(tc.outputs["Window"], sep.inputs[0]); wl.new(sep.outputs["Y"], ramp.inputs[0]); wl.new(ramp.outputs[0], bgc.inputs[0])
wl.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); wl.new(bga.outputs[0], mix.inputs[1]); wl.new(bgc.outputs[0], mix.inputs[2])
wl.new(mix.outputs[0], out.inputs[0])

f_arialb = bpy.data.fonts.load(os.path.join(FONT_DIR, "arialbd.ttf"))
f_georgiab = bpy.data.fonts.load(os.path.join(FONT_DIR, "georgiab.ttf"))


def material(name, color, emis=0.0, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = color; p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emis:
        p.inputs["Emission Color"].default_value = color; p.inputs["Emission Strength"].default_value = emis
    return m


def _fcurves(action):
    try:
        return list(action.fcurves)
    except Exception:
        o = []
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    o.extend(cb.fcurves)
        return o


def key(ob, path, fv, interp=None):
    for f, v in fv:
        setattr(ob, path, v); ob.keyframe_insert(path, frame=f)
    if interp and ob.animation_data:
        for fc in _fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = interp


def fader(m, keys):
    p = m.node_tree.nodes["Principled BSDF"]
    m.surface_render_method = "DITHERED"
    for f, a in keys:
        p.inputs["Alpha"].default_value = a
        p.inputs["Alpha"].keyframe_insert("default_value", frame=f)


def odslona(m, keys, os_="X"):
    """Maska odsłaniania: widoczne tylko tam, gdzie współrzędna obiektu < wartość (keyframes w metrach)."""
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tcn = nt.nodes.new("ShaderNodeTexCoord"); sx = nt.nodes.new("ShaderNodeSeparateXYZ")
    val = nt.nodes.new("ShaderNodeValue"); lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"
    nt.links.new(tcn.outputs["Object"], sx.inputs[0]); nt.links.new(sx.outputs[os_], lt.inputs[0])
    nt.links.new(val.outputs[0], lt.inputs[1]); nt.links.new(lt.outputs[0], p.inputs["Alpha"])
    m.surface_render_method = "DITHERED"
    for f, v in keys:
        val.outputs[0].default_value = v
        val.outputs[0].keyframe_insert("default_value", frame=f)


def extrude(name, pts, h, mat, z0=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((x, y, z0)) for x, y in pts]
    try:
        f = bm.faces.new(vs)
    except ValueError:
        bm.free(); return None
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
    bm.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]:
        v.co.z += h
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new(name, me)); me.materials.append(mat)
    return ob


def offset_poly(pts, d):
    """Wielokąt odsunięty o d metrów (przybliżenie: skalowanie od środka)."""
    c = np.mean(np.array(pts), 0)
    out_ = []
    for p in pts:
        v = np.array(p) - c
        n = np.linalg.norm(v) + 1e-9
        out_.append(tuple(c + v * (n + d) / n))
    return out_


# ---------------------------------------------------------------- teren i budowle
M_TLO = material("teren", rgb255(160, 219, 189), emis=0.35, rough=0.95)       # miętowe tło szkicu
M_CZ = material("bryla", rgb255(28, 28, 32), emis=0.0, rough=0.55)
M_BIA = material("obrys", rgb255(250, 250, 250), emis=0.6, rough=0.7)
M_PLAC = material("plac", rgb255(205, 236, 220), emis=0.35, rough=0.9)

teren = extrude("teren", [(-2600, -2000), (2600, -2000), (2600, 2400), (-2600, 2400)], 6.0, M_TLO, z0=-6.0)
mod = teren.modifiers.new("bev", "BEVEL"); mod.width = 4.0; mod.segments = 3


def rosnij(ob, f0, dur=18):
    """Budowla wyłania się spod terenu (teren jest nieprzezroczystą płytą)."""
    x, y, z = ob.location
    key(ob, "location", [(1, (x, y, z - 140)), (f0, (x, y, z - 140)), (f0 + dur, (x, y, z))])


def budowla(name, pts_m, h, rodzaj, f0):
    cx, cy = np.mean(np.array(pts_m), 0)
    loc = [(x - cx, y - cy) for x, y in pts_m]
    if rodzaj == "plac":      # place nie są zaznaczone na szkicu Leszka
        return
    ob_o = extrude(name + "_obrys", offset_poly(loc, 3.0), 0.8, M_BIA)
    if ob_o: ob_o.location = (cx, cy, 0); rosnij(ob_o, f0, 8)
    ob = extrude(name, loc, h * PRZEW, M_CZ, z0=0.0)
    if ob:
        ob.location = (cx, cy, 0)
        bv = ob.modifiers.new("bev", "BEVEL"); bv.width = 0.6; bv.segments = 1
        rosnij(ob, f0 + 3)


def piramida_schodkowa(name, cx, cy, bok, h, n, f0, swiatynka=True):
    hp = h * PRZEW * (0.72 if swiatynka else 1.0)
    grp = link(bpy.data.objects.new(name, None)); grp.location = (cx, cy, 0)
    ob_o = extrude(name + "_obrys", [(-bok / 2 - 4, -bok / 2 - 4), (bok / 2 + 4, -bok / 2 - 4), (bok / 2 + 4, bok / 2 + 4), (-bok / 2 - 4, bok / 2 + 4)], 0.8, M_BIA)
    ob_o.parent = grp
    for i in range(n):
        s = bok * (1 - 0.62 * i / n)
        t = extrude("%s_t%d" % (name, i), [(-s / 2, -s / 2), (s / 2, -s / 2), (s / 2, s / 2), (-s / 2, s / 2)], hp / n, M_CZ, z0=hp * i / n)
        t.parent = grp
    if swiatynka:
        s = bok * 0.3
        t = extrude(name + "_swiatynka", [(-s / 2, -s / 3), (s / 2, -s / 3), (s / 2, s / 3), (-s / 2, s / 3)], h * PRZEW * 0.28, M_CZ, z0=hp)
        t.parent = grp
    rosnij(grp, f0, 22)
    return grp


f = 4
for name, pts, h, rodzaj in PLAN:
    pm = [svg2m(p) for p in pts]
    if rodzaj == "piramida":
        cx, cy = np.mean(np.array(pm), 0)
        piramida_schodkowa(name, cx, cy, 58, h, 5, f, swiatynka=False)
    else:
        budowla(name, pm, h, rodzaj, f)
    f = 4 + (len(bpy.data.objects) * 7) % 40

SW_OB = {}
for i, (k, ((x, y), h, bok)) in enumerate(SWIATYNIE.items()):
    SW_OB[k] = piramida_schodkowa("Swiatynia_" + k, x, y, bok, h, 7 if k != "II" else 3, 10 + i * 6)

# ---------------------------------------------------------------- napisy (obrócone do kamery)
cam = bpy.data.cameras.new("kamera"); cam.lens = 38; cam.clip_start = 5; cam.clip_end = 20000
co = link(bpy.data.objects.new("kamera", cam)); sc.camera = co


def napis(body, pos, size, mat, f0, font=None, name=None, ax="CENTER"):
    cu = bpy.data.curves.new(name or ("T_" + body), "FONT")
    cu.body = body; cu.font = font or f_arialb; cu.size = size
    cu.align_x = ax; cu.align_y = "CENTER"; cu.extrude = size * 0.04
    ob = link(bpy.data.objects.new(cu.name, cu)); ob.location = pos
    cu.materials.append(mat)
    c = ob.constraints.new("COPY_ROTATION"); c.target = co   # napis równoległy do kadru, bez przechyłu
    key(ob, "scale", [(1, (0.001,) * 3), (f0, (0.001,) * 3), (f0 + 10, (1, 1, 1))])
    return ob


M_NAP = material("napis_bialy", rgb255(255, 255, 255), emis=1.0)
for i, (k, ((x, y), h, bok)) in enumerate(SWIATYNIE.items()):
    napis(k, (x, y - bok * 0.2, h * PRZEW + 44), 54, M_NAP, 34 + i * 4, font=f_georgiab, name="nr_" + k)

# ---------------------------------------------------------------- linie przerywane ze szkicu
M_CZER = material("czerwony", rgb255(226, 32, 40), emis=0.8, rough=0.5)
M_CZER2 = material("czerwony_cienki", rgb255(214, 92, 104), emis=0.8, rough=0.5)
Z_LIN = 2.5


def przerywana(name, p0, kat_od_pn, dl, szer, kreska, przerwa, mat, f0, f1, z=Z_LIN, wys=1.5):
    """Linia przerywana od punktu p0 w kierunku azymutu kat_od_pn (stopnie), długość dl; odsłaniana f0–f1."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    s = 0.0
    while s < dl:
        e = min(s + kreska, dl)
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            v.co.x = s + (v.co.x + 0.5) * (e - s)
            v.co.y *= szer
            v.co.z = v.co.z * wys
        s = e + przerwa
    bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new(name, me))
    m = mat.copy(); me.materials.append(m)
    ob.location = (p0[0], p0[1], z)
    ob.rotation_euler = (0, 0, math.radians(90 - kat_od_pn))
    odslona(m, [(1, -1.0), (f0, -1.0), (f1, dl + 1.0)])
    return ob


# gruba czerwona: dzisiejsza północ przez Plac Główny (na szkicu od dolnego rzędu budowli po zespół na północy)
PG = svg2m((8735, 12550))
przerywana("linia_polnoc", (PG[0], PG[1] - 380), 0.0, 1090, 7.0, 22, 12, M_CZER, 62, 102)
# cieńsza: drugi kierunek ze szkicu (ok. 45° na wschód), z Placu Głównego ku zespołowi bliźniaczych piramid
L2 = 1000
p0 = (PG[0] - 260 * math.sin(math.radians(DRUGI)), PG[1] - 260 * math.cos(math.radians(DRUGI)))
przerywana("linia_druga", p0, DRUGI, L2, 3.2, 14, 9, M_CZER2, 108, 148)

# granatowa strzałka „Pn” jak na szkicu (na lewo od linii)
M_GRAN = material("granat", rgb255(26, 27, 92), emis=0.6)
ax_, ay_ = PG[0] - 175, PG[1] + 160
st = extrude("strzalka_trzon", [(-3, 0), (3, 0), (3, 150), (-3, 150)], 2.0, M_GRAN)
gr = extrude("strzalka_grot", [(-13, 150), (13, 150), (0, 185)], 2.0, M_GRAN)
for o in (st, gr):
    o.location = (ax_, ay_, 1.0); key(o, "scale", [(1, (1, 0.001, 1)), (78, (1, 0.001, 1)), (92, (1, 1, 1))])
napis("Pn", (ax_, ay_ + 230, 16), 56, material("granat_napis", rgb255(26, 27, 92), emis=0.8), 88, name="Pn_szkic")

# ---------------------------------------------------------------- róża wiatrów nad Świątynią I
M_ZL = material("zloto", srgb("#f0c46f"), emis=0.7, rough=0.3, metal=0.3)
M_ZL_J = material("zloto_jasne", srgb("#f0c46f"), emis=1.1, rough=0.3)
SI = SWIATYNIE["I"][0]
ZR = 30.0          # nad niskimi budowlami, środek w osi Świątyni I
R = 130.0
roza = link(bpy.data.objects.new("roza", None)); roza.location = (SI[0], SI[1], ZR)
# obręcz (torus)
tor = bpy.data.meshes.new("obrecz"); bm = bmesh.new()
NS, NR, rr = 128, 8, 2.4
vv = []
for i in range(NS):
    a = 2 * math.pi * i / NS
    vv.append([bm.verts.new(((R + rr * math.cos(2 * math.pi * j / NR)) * math.cos(a), (R + rr * math.cos(2 * math.pi * j / NR)) * math.sin(a),
                             rr * math.sin(2 * math.pi * j / NR))) for j in range(NR)])
for i in range(NS):
    for j in range(NR):
        bm.faces.new((vv[i][j], vv[(i + 1) % NS][j], vv[(i + 1) % NS][(j + 1) % NR], vv[i][(j + 1) % NR]))
bm.to_mesh(tor); bm.free()
obr = link(bpy.data.objects.new("obrecz", tor)); obr.parent = roza; obr.data.materials.append(M_ZL)
# podziałka co 10° (stała tarcza: dzisiejsze kierunki), dłuższe kreski co 90°
tik = bpy.data.meshes.new("podzialka"); bm = bmesh.new()
for i in range(36):
    a = math.radians(i * 10)
    l = 20 if i % 9 == 0 else 9
    w = 3.0 if i % 9 == 0 else 1.8
    r_ = bmesh.ops.create_cube(bm, size=1.0)
    for v in r_["verts"]:
        x = R - 3 - (v.co.x + 0.5) * l; y = v.co.y * w; z = v.co.z * 1.5
        v.co.x = x * math.sin(a) + y * math.cos(a)
        v.co.y = x * math.cos(a) - y * math.sin(a)
        v.co.z = z
bm.to_mesh(tik); bm.free()
tk = link(bpy.data.objects.new("podzialka", tik)); tk.parent = roza; tk.data.materials.append(M_ZL)
napis("Pn", (SI[0], SI[1] + R + 40, ZR + 4), 40, M_ZL_J, 160, font=f_georgiab, name="roza_Pn")
# igła = długa złota oś przerywana przez środek róży (obraca się razem z igłą), z grotem na północy
igla = link(bpy.data.objects.new("igla", None)); igla.parent = roza
me = bpy.data.meshes.new("os_igly"); bm = bmesh.new()
s_ = -330.0
while s_ < 400.0:
    e_ = min(s_ + 18, 400.0)
    if not (-14 < s_ < 14 or -14 < e_ < 14):
        r_ = bmesh.ops.create_cube(bm, size=1.0)
        for v in r_["verts"]:
            v.co.y = s_ + (v.co.y + 0.5) * (e_ - s_); v.co.x *= 4.0; v.co.z *= 2.0
    s_ = e_ + 10
bm.to_mesh(me); bm.free()
osi = link(bpy.data.objects.new("os_igly", me)); osi.parent = igla
m_os = M_ZL_J.copy(); me.materials.append(m_os)
odslona(m_os, [(1, -331.0), (172, -331.0), (198, 401.0)], os_="Y")
gro = extrude("grot_igly", [(-11, R + 6), (11, R + 6), (0, R + 40)], 3.0, M_ZL_J); gro.parent = igla
srod = extrude("srodek_igly", [(-7, -7), (7, -7), (7, 7), (-7, 7)], 4.0, M_ZL); srod.parent = igla
key(roza, "scale", [(1, (0.001,) * 3), (152, (0.001,) * 3), (174, (1, 1, 1))])
key(gro, "scale", [(1, (0.001,) * 3), (192, (0.001,) * 3), (200, (1, 1, 1))])
# obrót igły o 17° na północny wschód (zgodnie z ruchem wskazówek zegara)
key(igla, "rotation_euler", [(1, (0, 0, 0)), (205, (0, 0, 0)), (262, (0, 0, -math.radians(KAT)))])
# łuk między północą a 17°
luk = bpy.data.curves.new("luk", "CURVE"); luk.dimensions = "3D"
spl = luk.splines.new("POLY"); NA = 24; spl.points.add(NA)
RL = R * 0.62
for i in range(NA + 1):
    a = math.radians(KAT * i / NA)
    spl.points[i].co = (RL * math.sin(a), RL * math.cos(a), 3.0, 1)
luk.bevel_depth = 2.2
lo = link(bpy.data.objects.new("luk", luk)); lo.parent = roza; luk.materials.append(M_ZL_J)
for f_, v in ((1, 0.0), (205, 0.0), (262, 1.0)):
    luk.bevel_factor_end = v; luk.keyframe_insert("bevel_factor_end", frame=f_)
a = math.radians(KAT / 2)
# napis z prośby sesji głównej: jasne, że 17° jest z cytatu Daenikena, a nie ze szkicu Leszka
napis("kompas Daenikena\n(17°)",(SI[0] + 218, SI[1] + 52, ZR + 40), 30, M_ZL_J, 258, font=f_georgiab, name="kat17")

for o in [roza] + list(roza.children_recursive):
    o.visible_shadow = False

# ---------------------------------------------------------------- trójkąt świątyń IV, I i V
M_TR = material("trojkat", srgb("#f0c46f"), emis=1.0, rough=0.3)


def odcinek(name, a, b, f0, f1, szer=4.0, z=27.0):
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
    v = b - a; L = v.length
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    r = bmesh.ops.create_cube(bm, size=1.0)
    for vv_ in r["verts"]:
        vv_.co.x = (vv_.co.x + 0.5) * L; vv_.co.y *= szer; vv_.co.z *= 2.5
    bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new(name, me)); m = M_TR.copy(); me.materials.append(m)
    ob.location = (a.x, a.y, z); ob.rotation_euler = (0, 0, math.atan2(v.y, v.x))
    odslona(m, [(1, -1.0), (f0, -1.0), (f1, L + 1.0)])
    return ob


P1, P4, P5 = SWIATYNIE["I"][0], SWIATYNIE["IV"][0], SWIATYNIE["V"][0]
odcinek("tr_I_IV", P1, P4, 292, 322, szer=5.5)
odcinek("tr_I_V", P1, P5, 318, 338, szer=5.5)
odcinek("tr_IV_V", P4, P5, 334, 362, szer=5.5)
# znak kąta prostego przy Świątyni I
u4 = Vector((P4[0] - P1[0], P4[1] - P1[1], 0)).normalized()
u5 = Vector((P5[0] - P1[0], P5[1] - P1[1], 0)).normalized()
d = 46
q0 = Vector((P1[0], P1[1], 0)) + u4 * d; q1 = q0 + u5 * d; q2 = Vector((P1[0], P1[1], 0)) + u5 * d
k1 = odcinek("kat_prosty_1", (q0.x, q0.y), (q1.x, q1.y), 362, 368, szer=3.0, z=28)
k2 = odcinek("kat_prosty_2", (q1.x, q1.y), (q2.x, q2.y), 366, 372, szer=3.0, z=28)
kat_I4 = math.degrees(math.acos(max(-1, min(1, u4.dot(u5)))))
print("KAT_PRZY_SWIATYNI_I", round(kat_I4, 1))
az_IV = (math.degrees(math.atan2(P4[0] - P1[0], P4[1] - P1[1])) + 360) % 360
az_V = (math.degrees(math.atan2(P5[0] - P1[0], P5[1] - P1[1])) + 360) % 360
print("AZYMUT_I_IV", round(az_IV, 1), "AZYMUT_I_V", round(az_V, 1))

# ---------------------------------------------------------------- światło i kamera
sun = bpy.data.lights.new("slonce", "SUN"); sun.energy = 2.6; sun.angle = math.radians(4)
so = link(bpy.data.objects.new("slonce", sun)); so.rotation_euler = (math.radians(48), math.radians(-18), math.radians(-35))
cel = link(bpy.data.objects.new("cel", None))
tr = co.constraints.new("TRACK_TO"); tr.target = cel; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
C0 = Vector((-60, 10, 0))        # środek kadru końcowego
D, TILT = 2450.0, math.radians(30)
off = Vector((0, -D * math.sin(TILT), D * math.cos(TILT)))
key(cel, "location", [(1, C0 + Vector((40, 40, 0))), (200, C0 + Vector((0, 10, 0))), (KLATEK, C0)])
key(co, "location", [(1, C0 + Vector((380, 0, 0)) + off * 1.12), (200, C0 + Vector((60, 0, 0)) + off * 1.03), (300, C0 + off), (KLATEK, C0 + off * 0.97)])
cam.lens = 50

# napisy, linie i trójkąt nie rzucają cieni (na szkicu ich nie ma, a cień myliłby się z linią)
def bez_cienia(m):
    """Materiał przezroczysty dla promieni cienia (alfa * (1 - Is Shadow Ray))."""
    if m.get("bez_cienia"):
        return
    m["bez_cienia"] = True
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    lpn = nt.nodes.new("ShaderNodeLightPath")
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    nt.links.new(lpn.outputs["Is Shadow Ray"], inv.inputs[1])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    a_in = p.inputs["Alpha"]
    if a_in.is_linked:
        nt.links.new(a_in.links[0].from_socket, mul.inputs[0])
    else:
        mul.inputs[0].default_value = a_in.default_value
    nt.links.new(inv.outputs[0], mul.inputs[1]); nt.links.new(mul.outputs[0], a_in)
    m.surface_render_method = "DITHERED"
    try:
        m.use_transparent_shadow = True
    except Exception:
        pass


for o in sc.objects:
    if o.type == "FONT" or o.name.startswith(("linia_", "tr_", "kat_prosty", "strzalka", "os_igly", "grot_igly", "srodek_igly", "obrecz", "podzialka", "luk")):
        o.visible_shadow = False
        for ms in o.material_slots:
            if ms.material:
                bez_cienia(ms.material)
        if o.type in ("FONT", "CURVE"):
            for m in o.data.materials:
                if m: bez_cienia(m)

# kontrola kadru: położenie świątyń w pikselach w ostatniej klatce
from bpy_extras.object_utils import world_to_camera_view
sc.frame_set(KLATEK)
for k, ((x, y), h, b) in SWIATYNIE.items():
    v = world_to_camera_view(sc, co, Vector((x, y, 0)))
    print("KADR", k, round(v.x * 1920), round((1 - v.y) * 1080))
for nm, pt in (("PnKoniec", (PG[0], PG[1] + 710)), ("Q", svg2m((13700, 8050)))):
    v = world_to_camera_view(sc, co, Vector((pt[0], pt[1], 0)))
    print("KADR", nm, round(v.x * 1920), round((1 - v.y) * 1080))

# ---------------------------------------------------------------- render
KLATKI = os.path.join(TU, "_klatki"); os.makedirs(KLATKI, exist_ok=True)
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGB"


def ffmpeg():
    return shutil.which("ffmpeg") or glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe"))[0]


if TEST:
    os.makedirs(os.path.join(KLATKI, "test"), exist_ok=True)
    for f_ in TEST:
        sc.frame_set(f_); sc.render.filepath = os.path.join(KLATKI, "test", "t%04d.png" % f_)
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
