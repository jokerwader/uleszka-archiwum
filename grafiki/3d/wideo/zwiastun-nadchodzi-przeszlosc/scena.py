# -*- coding: utf-8 -*-
"""
„Nadchodzi przeszłość ...” – ożywiona ilustracja ze wstępu Leszka (zwiastun, odcinek 0 „Wstęp”).

Źródło: zrodlo/webacja/tsunami.jpg (obrazek we wstępie do „Cywilizacji Bogów”, podpis Leszka „Nadchodzi przeszłość ...”):
ogromna zielononiebieska fala z załamującym się grzbietem, a przed nią, w prawym dolnym rogu, Statua Wolności.
Klip zachowuje tę treść: fala rośnie i nadciąga nad posąg, kadr końcowy odpowiada obrazkowi (chwila przed uderzeniem).

HIPOTEZA: takiej fali nikt nie zaobserwował; to obraz ostrzeżenia z tekstu, nie rekonstrukcja zdarzenia.
Posąg jest uproszczoną bryłą (pomnik, nie człowiek); w kadrze nie ma ludzi.

Skala: 1 jednostka = 10 m. Posąg z cokołem 93 m (9,3 j.), fala w kadrze końcowym ok. 300 m – ok. trzy razy wyższa
od posągu, tak jak na obrazku.

Uruchomienie:
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-nadchodzi-przeszlosc/scena.py -- --proba 1,130,260,400
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-nadchodzi-przeszlosc/scena.py
"""
import bpy, bmesh, math, os, sys, random
import numpy as np
from mathutils import Vector, noise

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, "..", "_wspolne"))
import globus as G, zwiastun as Z

opcje = G.argumenty()
NKL = 400  # 16 s
sc = Z.start(NKL, opcje, probki=48, ekspozycja=0.0)
Z.swiat((52, 84, 110), (206, 222, 226), moc=1.0)
random.seed(4)
RNG = np.random.default_rng(4)

H_FALI = 30.0     # wysokość fali w kadrze końcowym (300 m)


def mat(nt, op, x, y=None, z=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, v in enumerate((x, y, z)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def gladki(nt, a, b, x):
    """Płynne przejście 0 -> 1, gdy x rośnie od a do b (a, b, x: liczby albo gniazda)."""
    n = nt.nodes.new("ShaderNodeMapRange")
    n.interpolation_type = "SMOOTHSTEP"
    for i, v in ((0, x), (1, a), (2, b)):
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


# ---------------------------------------------------------------- mgiełka (głębia powietrza i pył wodny)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 100, 40))
mg = bpy.context.active_object
mg.name = "Mgla"
mg.scale = (1600, 1200, 82)
mm = bpy.data.materials.new("mgla")
mm.use_nodes = True
mm.node_tree.nodes.clear()
vo = mm.node_tree.nodes.new("ShaderNodeOutputMaterial")
vs = mm.node_tree.nodes.new("ShaderNodeVolumeScatter")
vs.inputs["Density"].default_value = 0.0016
vs.inputs["Anisotropy"].default_value = 0.3
vs.inputs["Color"].default_value = (0.86, 0.95, 1.0, 1)
mm.node_tree.links.new(vs.outputs[0], vo.inputs["Volume"])
mg.data.materials.append(mm)
mg.visible_shadow = False
for k, v in (("volumetric_end", 900.0), ("volumetric_samples", 96), ("volumetric_tile_size", "4"),
             ("use_volumetric_shadows", False)):
    try:
        setattr(sc.eevee, k, v)
    except Exception as e:
        print("[eevee]", k, e)

# ---------------------------------------------------------------- morze
M_MORZE = Z.pbr("morze", (8, 92, 104), szorstkosc=0.18)
nt = M_MORZE.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord")
mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (0.05, 0.11, 1.0)
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
ns = nt.nodes.new("ShaderNodeTexNoise")
ns.noise_dimensions = "4D"
ns.inputs["Scale"].default_value = 5.0
ns.inputs["Detail"].default_value = 8.0
ns.inputs["Roughness"].default_value = 0.6
nt.links.new(mp.outputs[0], ns.inputs["Vector"])
for f, w in ((1, 0.0), (NKL, 1.3)):
    ns.inputs["W"].default_value = w
    ns.inputs["W"].keyframe_insert("default_value", frame=f)
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.55
bump.inputs["Distance"].default_value = 0.6
nt.links.new(ns.outputs[0], bump.inputs["Height"])
nt.links.new(bump.outputs[0], Z.bsdf(M_MORZE).inputs["Normal"])
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[0].color = G.srgb((5, 70, 86))
ramp.color_ramp.elements[1].position = 0.75
ramp.color_ramp.elements[1].color = G.srgb((24, 138, 140))
nt.links.new(ns.outputs[0], ramp.inputs[0])
nt.links.new(ramp.outputs[0], Z.bsdf(M_MORZE).inputs["Base Color"])
for fc in G._fcurves(nt.animation_data.action):
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"
bpy.ops.mesh.primitive_plane_add(size=6000, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(M_MORZE)


# ---------------------------------------------------------------- fala
def profil(n=96):
    """Przekrój załamującej się fali (y, z) dla wysokości 1: y < 0 to strona, w którą fala idzie (ku kamerze)."""
    P = [(-1.9, 0.0), (-1.6, 0.012), (-1.3, 0.05), (-1.0, 0.14), (-0.62, 0.31), (-0.32, 0.5), (-0.12, 0.7),
         (-0.03, 0.86), (-0.05, 0.98), (-0.17, 1.06), (-0.36, 1.08), (-0.56, 1.03), (-0.72, 0.93), (-0.82, 0.8),
         (-0.86, 0.68)]
    pts = []
    m = len(P)
    for i in range(n + 1):          # krzywa Catmulla-Roma przez punkty
        t = i / n * (m - 1)
        k = min(int(t), m - 2)
        u = t - k
        p0, p1, p2, p3 = P[max(k - 1, 0)], P[k], P[k + 1], P[min(k + 2, m - 1)]
        c = []
        for a in (0, 1):
            c.append(0.5 * ((2 * p1[a]) + (-p0[a] + p2[a]) * u + (2 * p0[a] - 5 * p1[a] + 4 * p2[a] - p3[a]) * u * u
                            + (-p0[a] + 3 * p1[a] - 3 * p2[a] + p3[a]) * u ** 3))
        pts.append(c)
    return pts


def wys_grzbietu(x):
    return 1.0 + 0.16 * noise.noise(Vector((x * 0.011, 3.3, 0))) + 0.05 * noise.noise(Vector((x * 0.05, 9.1, 0)))


def wygiecie(x):
    """Grzbiet nie biegnie po prostej: łagodne wygięcia linii fali (w jednostkach sceny)."""
    return 9.0 * noise.noise(Vector((x * 0.006, 1.7, 0))) + 2.5 * noise.noise(Vector((x * 0.02, 5.2, 0)))


def fala():
    DLUG, NX = 560.0, 420
    pr = profil()
    ns_ = len(pr)
    verts, faces, uvs = [], [], []
    for i in range(NX + 1):
        x = -DLUG / 2 + DLUG * i / NX
        # grzbiet nie jest równy: wysokość i wysunięcie wargi zmieniają się wzdłuż fali
        hh = wys_grzbietu(x)
        ww = 1.0 + 0.30 * noise.noise(Vector((x * 0.017, 7.7, 0)))
        wyg = wygiecie(x)
        for j, (y, z) in enumerate(pr):
            s = j / (ns_ - 1)
            lip = max(0.0, (s - 0.62) / 0.38)            # część „warga”
            yy = y * (1 + (ww - 1) * lip)
            d = 0.012 * noise.fractal(Vector((x * 0.09, s * 6.0, 1.0)), 1.0, 2.0, 4) * (0.3 + s)
            verts.append((x, (yy + d) * H_FALI + wyg, max(0.0, z * hh + d * 0.6) * H_FALI))
            uvs.append((x / 60.0, s))
    for i in range(NX):
        for j in range(ns_ - 1):
            a = i * ns_ + j
            faces.append((a, a + ns_, a + ns_ + 1, a + 1))
    ob = Z.siatka("Fala", verts, faces, [], gladka=True)
    uvl = ob.data.uv_layers.new(name="UV")
    uvl.data.foreach_set("uv", [c for l in ob.data.loops for c in uvs[l.vertex_index]])
    return ob


M_FALA = Z.pbr("fala", (10, 120, 130), szorstkosc=0.2)
nt = M_FALA.node_tree
b = Z.bsdf(M_FALA)
uv = nt.nodes.new("ShaderNodeUVMap")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(uv.outputs[0], sep.inputs[0])
v = sep.outputs[1]
# smugi piany ciągnięte w górę po ścianie fali (szum rozciągnięty wzdłuż przekroju, przesuwany w czasie)
mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (26.0, 2.2, 1.0)
nt.links.new(uv.outputs[0], mp.inputs["Vector"])
for f, off in ((1, 0.0), (NKL, -1.7)):
    mp.inputs["Location"].default_value = (0.0, off, 0.0)
    mp.inputs["Location"].keyframe_insert("default_value", frame=f)
for fc in G._fcurves(nt.animation_data.action):
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"
sm = nt.nodes.new("ShaderNodeTexNoise")
sm.inputs["Scale"].default_value = 1.0
sm.inputs["Detail"].default_value = 9.0
sm.inputs["Roughness"].default_value = 0.68
nt.links.new(mp.outputs[0], sm.inputs["Vector"])
rampa = nt.nodes.new("ShaderNodeValToRGB")
el = rampa.color_ramp.elements
el[0].position, el[0].color = 0.0, G.srgb((5, 76, 92))
el[1].position, el[1].color = 1.0, G.srgb((210, 246, 240))
for pos, kol in ((0.3, (8, 112, 122)), (0.6, (20, 160, 158)), (0.86, (96, 220, 204))):
    e = el.new(pos)
    e.color = G.srgb(kol)
nt.links.new(v, rampa.inputs[0])
# piana: biała warga + smugi, których przybywa ku górze
prog = mat(nt, "SUBTRACT", 0.78, mat(nt, "MULTIPLY", v, 0.3))
smugi = gladki(nt, prog, mat(nt, "ADD", prog, 0.1), sm.outputs[0])
warga = gladki(nt, 0.9, 1.0, mat(nt, "ADD", v, mat(nt, "MULTIPLY", mat(nt, "SUBTRACT", sm.outputs[0], 0.5), 0.3)))
piana = mat(nt, "MINIMUM", mat(nt, "ADD", mat(nt, "MULTIPLY", smugi, mat(nt, "ADD", mat(nt, "MULTIPLY", v, 0.8), 0.15)), warga), 1.0)
mix = nt.nodes.new("ShaderNodeMix")
mix.data_type = "RGBA"
mix.inputs["B"].default_value = (0.95, 1.0, 1.0, 1)
nt.links.new(rampa.outputs[0], mix.inputs["A"])
nt.links.new(piana, mix.inputs["Factor"])
nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
nt.links.new(mat(nt, "ADD", 0.16, mat(nt, "MULTIPLY", piana, 0.6)), b.inputs["Roughness"])
# światło przechodzące przez cienki grzbiet: lekkie świecenie turkusem, rosnące ku górze
nt.links.new(rampa.outputs[0], b.inputs["Emission Color"])
nt.links.new(mat(nt, "ADD", 0.25, mat(nt, "MULTIPLY", mat(nt, "POWER", v, 1.6), 0.7)), b.inputs["Emission Strength"])
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.5
bump.inputs["Distance"].default_value = 1.0
nt.links.new(sm.outputs[0], bump.inputs["Height"])
nt.links.new(bump.outputs[0], b.inputs["Normal"])

ob_fala = fala()
ob_fala.data.materials.append(M_FALA)

# pył wodny zrywany z grzbietu: drobne białe bryłki nad wargą i za nią
def pyl(n=26000):
    pr = profil()
    verts, faces = [], []
    wz = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    tr = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
    for _ in range(n):
        x = random.uniform(-280, 280)
        j = random.randint(int(len(pr) * 0.6), len(pr) - 1)
        y, z = pr[j]
        hh = wys_grzbietu(x)
        g = abs(random.gauss(0, 1))
        cx, cy, cz = x, (y + random.uniform(-0.04, 0.2) + g * 0.08) * H_FALI + wygiecie(x), (z * hh + g * 0.05 + 0.01) * H_FALI
        r = random.uniform(0.02, 0.09) * (1 + g)
        b0 = len(verts)
        verts += [(cx + a * r, cy + b_ * r, cz + c * r) for a, b_, c in wz]
        faces += [(b0 + a, b0 + b_, b0 + c) for a, b_, c in tr]
    return Z.siatka("PylWodny", verts, faces, [], gladka=True)


M_PYL = Z.pbr("pyl", (240, 250, 250), szorstkosc=0.9, emisja=(230, 246, 248), moc_emisji=0.55)
ob_pyl = pyl()
ob_pyl.data.materials.append(M_PYL)
ob_pyl.visible_shadow = False

# fala i pył jadą razem: obrót wokół osi z ustawia grzbiet skośnie do kamery (bliżej z lewej, jak na obrazku)
root = Z.pusty("FalaRoot")
ob_fala.parent = root
ob_pyl.parent = root
root.rotation_euler = (0, 0, math.radians(-24))
KIER = Vector((math.sin(math.radians(-24)), -math.cos(math.radians(-24)), 0))    # dokąd idzie fala
P_KONIEC = Vector((6.0, 56.0, 0.0))
for f, odl, sz in ((1, 150.0, 0.42), (140, 92.0, 0.62), (290, 34.0, 0.9), (400, 0.0, 1.0)):
    p = P_KONIEC - KIER * odl
    root.location = p
    root.keyframe_insert("location", frame=f)
    root.scale = (1, 0.75 + 0.25 * sz, sz)
    root.keyframe_insert("scale", frame=f)
G.wygladz(root)

# ---------------------------------------------------------------- wyspa i posąg
M_WYSPA = Z.kamien("wyspa", (92, 108, 84), (70, 84, 66), skala=0.6, wypuklosc=0.3)
M_FORT = Z.kamien("fort", (176, 164, 142), (136, 124, 104), skala=1.4, wypuklosc=0.5)
M_COKOL = Z.kamien("cokol", (196, 182, 156), (150, 138, 114), skala=2.2, wypuklosc=0.5)
M_MIEDZ = Z.kamien("patyna", (104, 168, 148), (70, 128, 112), skala=5.0, wypuklosc=0.4, szorstkosc=0.6)
M_OGIEN = Z.pbr("plomien", (255, 200, 80), szorstkosc=0.3, metal=1.0, emisja=(255, 190, 70), moc_emisji=2.5)
PX, PY = 17.0, 0.0     # miejsce posągu


def bryla_obrotowa(nazwa, prof, mat_, seg=48, loc=(0, 0, 0), skala_y=1.0):
    verts, faces = [], []
    for r, z in prof:
        for k in range(seg):
            a = 2 * math.pi * k / seg
            verts.append((r * math.cos(a), r * math.sin(a) * skala_y, z))
    for i in range(len(prof) - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    faces.append(tuple(range(seg - 1, -1, -1)))
    faces.append(tuple(range((len(prof) - 1) * seg, len(prof) * seg)))
    ob = Z.siatka(nazwa, verts, faces, [mat_], gladka=True)
    ob.location = loc
    return ob


# wyspa (niska, owalna) i gwiaździsty fort pod cokołem
bryla_obrotowa("Wyspa", [(19.0, -0.5), (18.0, 0.25), (16.0, 0.4), (0.01, 0.45)], M_WYSPA, 64, (PX, PY, 0), 0.62)
gw_v, gw_f = [], []
NG = 11
for hz in (0.4, 1.9):
    for k in range(2 * NG):
        a = math.pi * k / NG + 0.2
        r = 5.6 if k % 2 == 0 else 3.9
        gw_v.append((PX + r * math.cos(a), PY + r * math.sin(a), hz))
for k in range(2 * NG):
    k2 = (k + 1) % (2 * NG)
    gw_f.append((k, k2, 2 * NG + k2, 2 * NG + k))
gw_f.append(tuple(range(2 * NG, 4 * NG)))
Z.siatka("FortGwiazda", gw_v, gw_f, [M_FORT])

# cokół: ścięty słup z gzymsami (od 1,9 do 4,7 j.)
def slup(nazwa, a0, a1, z0, z1, mat_):
    v = []
    for a, z in ((a0, z0), (a1, z1)):
        v += [(PX - a, PY - a, z), (PX + a, PY - a, z), (PX + a, PY + a, z), (PX - a, PY + a, z)]
    f = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]
    return Z.siatka(nazwa, v, f, [mat_])


slup("Cokol1", 1.55, 1.45, 1.9, 2.4, M_COKOL)
slup("Cokol2", 1.15, 0.95, 2.4, 4.3, M_COKOL)
slup("Cokol3", 1.1, 1.1, 4.3, 4.5, M_COKOL)
slup("Cokol4", 0.85, 0.8, 4.5, 4.7, M_COKOL)

# posąg (4,6 j. od stóp do płomienia): szata, głowa, korona z siedmioma promieniami, ręka z pochodnią, tablica
Z0 = 4.7
ROT = math.radians(110)       # posąg zwrócony frontem ku kamerze (na południowy wschód)
posag = Z.pusty("Posag", (PX, PY, Z0))
posag.rotation_euler = (0, 0, ROT)


def do_posagu(ob):
    ob.parent = posag
    return ob


do_posagu(bryla_obrotowa("Szata", [(0.6, 0.0), (0.56, 0.5), (0.48, 1.2), (0.42, 1.9), (0.45, 2.35), (0.5, 2.62),
                                   (0.4, 2.82), (0.17, 2.95), (0.13, 3.05)], M_MIEDZ, 32, (0, 0, 0), 0.72))
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.2, location=(0, 0, 3.2))
glowa = bpy.context.active_object
glowa.scale = (0.9, 0.95, 1.12)
glowa.data.materials.append(M_MIEDZ)
bpy.ops.object.shade_smooth()
do_posagu(glowa)
for i in range(7):                       # korona: siedem promieni
    a = math.radians(-78 + 26 * i)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.035, radius2=0.0, depth=0.34,
                                    location=(0.0 + 0.3 * math.sin(a), 0.0, 3.34 + 0.3 * math.cos(a)))
    pr_ = bpy.context.active_object
    pr_.rotation_euler = (0, a, 0)
    pr_.data.materials.append(M_MIEDZ)
    do_posagu(pr_)


def walec(nazwa, p0, p1, r, mat_):
    p0, p1 = Vector(p0), Vector(p1)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=(p1 - p0).length, location=(p0 + p1) / 2)
    ob = bpy.context.active_object
    ob.name = nazwa
    ob.rotation_euler = (p1 - p0).to_track_quat("Z", "Y").to_euler()
    ob.data.materials.append(mat_)
    bpy.ops.object.shade_smooth()
    return do_posagu(ob)


walec("RekaPrawa", (0.36, 0.0, 2.72), (0.56, 0.0, 3.98), 0.1, M_MIEDZ)          # uniesiona ręka
walec("Pochodnia", (0.56, 0.0, 3.92), (0.58, 0.0, 4.3), 0.045, M_MIEDZ)
walec("Misa", (0.58, 0.0, 4.28), (0.58, 0.0, 4.34), 0.13, M_MIEDZ)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.1, location=(0.58, 0, 4.47))
pl = bpy.context.active_object
pl.scale = (0.9, 0.9, 1.5)
pl.data.materials.append(M_OGIEN)
do_posagu(pl)
walec("RekaLewa", (-0.36, 0.0, 2.7), (-0.42, -0.26, 2.2), 0.1, M_MIEDZ)
tab = Z.prostopadloscian("Tablica", (0.3, 0.08, 0.52), (-0.46, -0.34, 2.36), M_MIEDZ, rot=(math.radians(-12), 0, math.radians(10)))
do_posagu(tab)
# posąg stał dotąd w początku układu – przenieś dzieci pod pusty obiekt bez zmiany ich lokalnych współrzędnych
# (współrzędne powyżej są podane w układzie posągu)

# ---------------------------------------------------------------- kamera
cam = G.kamera((-14, -78, 5), (10, 0, 12), lens=30)
cam.data.clip_start, cam.data.clip_end = 0.1, 5000
cel = Z.pusty("Cel")
Z.lot_kamery(cam, cel, [
    (1, (-6.0, -62.0, 6.5), (14.0, 0.0, 6.0)),
    (200, (-1.0, -44.0, 4.2), (13.5, 2.0, 8.5)),
    (400, (3.0, -30.0, 2.6), (13.0, 6.0, 9.6)),
])

Z.napis_ekran(cam, "Nadchodzi przeszłość ...", 560, 185, 66, (250, 246, 236), "georgiab", odl=1.0, pojaw=(24, 54))

# ---------------------------------------------------------------- światło: słońce z przodu, z lewej, zza kamery
Z.slonce((0.45, 0.72, -0.5), moc=4.0, kolor=(1.0, 0.96, 0.9), kat=2.0)
Z.slonce((-0.6, -0.3, -0.5), moc=0.8, kolor=(0.7, 0.9, 1.0), kat=30.0, cien=False)

G.renderuj(DIR, opcje, kadr_klatka=400)
