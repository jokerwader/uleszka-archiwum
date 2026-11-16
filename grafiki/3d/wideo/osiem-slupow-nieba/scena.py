# -*- coding: utf-8 -*-
"""
Klip „osiem-slupow-nieba” do odcinka 2 „Wielki uskok…” (rozdz. 01, cytat z K'ü Jüana „Pytam niebiosa”).

Ilustracja MITU w duchu dawnej chińskiej kosmologii („niebo okrągłe, ziemia kwadratowa”):
kopuła nieba wsparta na ośmiu słupach stojących w ośmiu kierunkach. Słup na południowym wschodzie
łamie się i upada, ziemia (razem z niebem) kłoni się na południowy wschód, woda spływa w ten narożnik.

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/osiem-slupow-nieba/scena.py
  ... -- --proba 1,120,200,400     (tylko kadry próbne PNG do _klatki/)
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G

KLATEK = 400  # 16 s
opcje = G.argumenty()
sc = G.nowa_scena(KLATEK)
sc.eevee.taa_render_samples = int(os.environ.get("USKOK3D_PROBKI", "32"))

POL = 3.4         # połowa boku kwadratowej ziemi
RP = 2.8          # promień okręgu słupów
HP = 2.3          # wysokość słupa
RS = 0.13         # promień słupa
CZERWIEN = (168, 44, 36)
ZIEMIA = (196, 160, 92)      # żółta ziemia (kolor ziemi w chińskiej kosmologii)
WODA = (40, 110, 170)
NIEBO = (27, 42, 77)

# kierunki: x = wschód, y = północ
KIER = {"Wsch": 0, "Pn-Wsch": 45, "Pn": 90, "Pn-Zach": 135, "Zach": 180, "Pd-Zach": 225, "Pd": 270, "Pd-Wsch": 315}

kosmos = bpy.data.objects.new("Kosmos", None)
sc.collection.objects.link(kosmos)


def mat_pbr(nazwa, kolor, szorst=0.6, metal=0.0, emisja=0.0, alfa_anim=False):
    m = bpy.data.materials.new(nazwa)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = G.srgb(kolor)
    p.inputs["Roughness"].default_value = szorst
    p.inputs["Metallic"].default_value = metal
    if emisja:
        p.inputs["Emission Color"].default_value = G.srgb(kolor)
        p.inputs["Emission Strength"].default_value = emisja
    if alfa_anim:
        try:
            m.surface_render_method = "DITHERED"
        except Exception:
            pass
    return m


def dodaj(ob, rodzic=kosmos):
    ob.parent = rodzic
    return ob

# ---------------------------------------------------------------- ziemia
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.2))
ziemia = bpy.context.active_object
ziemia.name = "Ziemia"
ziemia.scale = (2 * POL, 2 * POL, 0.4)
bpy.ops.object.transform_apply(scale=True)
bev = ziemia.modifiers.new("faza", "BEVEL"); bev.width = 0.04; bev.segments = 3
dodaj(ziemia)
# materiał: ziemia, a tam gdzie powierzchnia (w świecie) leży poniżej poziomu wody – woda
mz = bpy.data.materials.new("Ziemia")
mz.use_nodes = True
nt = mz.node_tree
p = nt.nodes["Principled BSDF"]
p.inputs["Roughness"].default_value = 0.8
geo = nt.nodes.new("ShaderNodeNewGeometry")
sepz = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(geo.outputs["Position"], sepz.inputs[0])
poziom = nt.nodes.new("ShaderNodeValue"); poziom.name = poziom.label = "poziom_wody"
poziom.outputs[0].default_value = -0.03
roz = nt.nodes.new("ShaderNodeMath"); roz.operation = "SUBTRACT"
nt.links.new(poziom.outputs[0], roz.inputs[0]); nt.links.new(sepz.outputs[2], roz.inputs[1])
fac = nt.nodes.new("ShaderNodeMapRange")
fac.inputs["From Min"].default_value = 0.0; fac.inputs["From Max"].default_value = 0.025
nt.links.new(roz.outputs[0], fac.inputs["Value"])
# tylko górna ściana może być zalana (normalna w górę w układzie obiektu)
tc = nt.nodes.new("ShaderNodeTexCoord")
sepn = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Normal"], sepn.inputs[0])
gora = nt.nodes.new("ShaderNodeMath"); gora.operation = "GREATER_THAN"; gora.inputs[1].default_value = 0.9
nt.links.new(sepn.outputs[2], gora.inputs[0])
fw = nt.nodes.new("ShaderNodeMath"); fw.operation = "MULTIPLY"
nt.links.new(fac.outputs[0], fw.inputs[0]); nt.links.new(gora.outputs[0], fw.inputs[1])
# kolor ziemi z lekkim szumem
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0
rampa = nt.nodes.new("ShaderNodeValToRGB")
rampa.color_ramp.elements[0].color = G.srgb((176, 138, 74))
rampa.color_ramp.elements[1].color = G.srgb((214, 182, 112))
nt.links.new(nz.outputs[0], rampa.inputs[0])
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
nt.links.new(fw.outputs[0], mix.inputs["Factor"])
nt.links.new(rampa.outputs[0], mix.inputs["A"])
mix.inputs["B"].default_value = G.srgb(WODA)
nt.links.new(mix.outputs["Result"], p.inputs["Base Color"])
mr = nt.nodes.new("ShaderNodeMapRange")
mr.inputs["To Min"].default_value = 0.8; mr.inputs["To Max"].default_value = 0.12
nt.links.new(fw.outputs[0], mr.inputs["Value"])
nt.links.new(mr.outputs[0], p.inputs["Roughness"])
ziemia.data.materials.append(mz)

# złote linie na ziemi: obwódka i podział na dziewięć pól
def linia(punkty, nazwa, kolor=G.ZLOTY, grub=0.02, rodzic=kosmos, zamknieta=False, emisja=1.0):
    cu = bpy.data.curves.new(nazwa, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = grub
    cu.bevel_resolution = 2
    sp = cu.splines.new("POLY")
    sp.points.add(len(punkty) - 1)
    for pt, co in zip(sp.points, punkty):
        pt.co = (*co, 1)
    sp.use_cyclic_u = zamknieta
    ob = bpy.data.objects.new(nazwa, cu)
    sc.collection.objects.link(ob)
    m = mat_pbr(nazwa + "_mat", kolor, 0.35, 0.8, emisja)
    cu.materials.append(m)
    dodaj(ob, rodzic)
    return ob

z0 = 0.012
c = POL - 0.25
linia([(-c, -c, z0), (c, -c, z0), (c, c, z0), (-c, c, z0)], "obwodka", zamknieta=True, grub=0.025, emisja=0.6)
for t in (-1 / 3, 1 / 3):
    linia([(t * 2 * c, -c, z0), (t * 2 * c, c, z0)], "pole_x", grub=0.012, emisja=0.35)
    linia([(-c, t * 2 * c, z0), (c, t * 2 * c, z0)], "pole_y", grub=0.012, emisja=0.35)

# ---------------------------------------------------------------- słupy
m_slup = mat_pbr("Slup", CZERWIEN, 0.45)
m_zloto = mat_pbr("Zloto", G.ZLOTY, 0.3, 1.0, 0.15)
slupy = {}
for nazwa, kat in KIER.items():
    a = math.radians(kat)
    x, y = RP * math.cos(a), RP * math.sin(a)
    piv = bpy.data.objects.new("slup_" + nazwa, None)
    sc.collection.objects.link(piv)
    piv.location = (x, y, 0)
    dodaj(piv)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=RS, depth=HP, location=(0, 0, HP / 2))
    s = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    s.parent = piv
    s.data.materials.append(m_slup)
    for zz, rr, hh in ((0.09, RS * 1.7, 0.18), (HP - 0.08, RS * 1.6, 0.16), (HP - 0.2, RS * 1.25, 0.06), (0.24, RS * 1.3, 0.06)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=rr, depth=hh, location=(0, 0, zz))
        k = bpy.context.active_object
        bpy.ops.object.shade_smooth()
        k.parent = piv
        k.data.materials.append(m_zloto)
    slupy[nazwa] = piv

# słup południowo-wschodni ma własne materiały (znika po upadku)
m_slup_pw = mat_pbr("Slup_PW", CZERWIEN, 0.45, alfa_anim=True)
m_zloto_pw = mat_pbr("Zloto_PW", G.ZLOTY, 0.3, 1.0, 0.15, alfa_anim=True)
for ch in slupy["Pd-Wsch"].children:
    ch.data.materials[0] = m_slup_pw if ch.data.materials[0] == m_slup else m_zloto_pw

# ---------------------------------------------------------------- kopuła nieba
RK = RP + 0.12
bpy.ops.mesh.primitive_uv_sphere_add(radius=RK, segments=96, ring_count=48, location=(0, 0, HP))
kop = bpy.context.active_object
kop.name = "Kopula"
bpy.ops.object.shade_smooth()
bm = bmesh.new(); bm.from_mesh(kop.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context="VERTS")
bm.to_mesh(kop.data); bm.free()
dodaj(kop)
mk = bpy.data.materials.new("Kopula")
mk.use_nodes = True
ntk = mk.node_tree
pk = ntk.nodes["Principled BSDF"]
pk.inputs["Base Color"].default_value = G.srgb((30, 52, 100))
pk.inputs["Roughness"].default_value = 0.45
pk.inputs["Alpha"].default_value = 0.32
pk.inputs["Emission Color"].default_value = G.srgb((40, 70, 140))
pk.inputs["Emission Strength"].default_value = 0.25
try:
    mk.surface_render_method = "BLENDED"
    mk.use_backface_culling = False
except Exception:
    pass
kop.data.materials.append(mk)

# złote równoleżniki i południki (południki kończą się na słupach)
for latd in (0, 30, 60):
    la = math.radians(latd)
    r = RK * math.cos(la) * 1.002
    zz = HP + RK * math.sin(la) * 1.002
    linia([(r * math.cos(t), r * math.sin(t), zz) for t in [2 * math.pi * i / 160 for i in range(160)]],
          f"rownoleznik_{latd}", zamknieta=True, grub=0.018 if latd else 0.03, emisja=0.9)
for kat in KIER.values():
    a = math.radians(kat)
    pts = []
    for i in range(41):
        la = math.radians(90 * i / 40)
        pts.append((RK * 1.002 * math.cos(la) * math.cos(a), RK * 1.002 * math.cos(la) * math.sin(a), HP + RK * 1.002 * math.sin(la)))
    linia(pts, f"poludnik_{kat}", grub=0.014, emisja=0.9)

# gwiazdy na kopule
random.seed(7)
bm = bmesh.new()
for i in range(260):
    zf = random.random() ** 0.8
    t = random.random() * 2 * math.pi
    rr = math.sqrt(max(0.0, 1 - zf * zf))
    pos = Vector((rr * math.cos(t), rr * math.sin(t), zf)) * (RK * 0.995)
    pos.z += HP
    rad = 0.018 + 0.03 * random.random() ** 3
    res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rad)
    bmesh.ops.translate(bm, verts=res["verts"], vec=pos)
me = bpy.data.meshes.new("Gwiazdy"); bm.to_mesh(me); bm.free()
gw = bpy.data.objects.new("Gwiazdy", me); sc.collection.objects.link(gw); dodaj(gw)
gw.data.materials.append(G.material_emisja("Gwiazdy_mat", (255, 236, 190)))

# ---------------------------------------------------------------- napisy na ziemi (kierunki)
NAPISY_KIER = {"PÓŁNOC": (0, 1.95), "POŁUDNIE": (0, -1.95), "WSCHÓD": (1.95, 0), "ZACHÓD": (-1.95, 0)}
nap_kier = []
for txt, (x, y) in NAPISY_KIER.items():
    ob = G.napis(txt, 0.3, (100, 58, 16), "georgiab", "CENTER", rodzic=kosmos, loc=(x, y, 0.004), nazwa="kier_" + txt)
    nap_kier.append(ob)
pw_nap = G.napis("POŁUDNIOWY\nWSCHÓD", 0.24, (150, 40, 25), "georgiab", "CENTER", rodzic=kosmos,
                 loc=(1.55, -1.55, 0.004), rot=(0, 0, math.radians(45)), nazwa="kier_PW", odstep=0.95)

# ---------------------------------------------------------------- światło i kamera
def swiatlo(nazwa, typ, energia, kier, kolor=(1, 1, 1), kat=2.0):
    ld = bpy.data.lights.new(nazwa, typ)
    ld.energy = energia
    ld.color = kolor
    if typ == "SUN":
        ld.angle = math.radians(kat)
    ob = bpy.data.objects.new(nazwa, ld)
    sc.collection.objects.link(ob)
    ob.rotation_euler = (-Vector(kier)).to_track_quat("-Z", "Y").to_euler()
    return ob
swiatlo("Slonce", "SUN", 3.2, (-0.5, -0.9, 1.2), (1.0, 0.95, 0.86), 4)
swiatlo("Kontra", "SUN", 1.2, (0.6, 1.0, 0.5), (0.6, 0.7, 1.0), 10)
sc.world.node_tree.nodes["Background"].inputs[0].default_value = G.srgb((18, 26, 48))
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.8

CEL = Vector((0, 0, 1.75))
DK = 19.5
cam = G.kamera((0, -DK, 6), CEL, lens=32)
cam.data.shift_y = -0.034
tlo = G.tlo_kamery(cam, odl=80)
for f in range(1, KLATEK + 1):
    t = (f - 1) / (KLATEK - 1)
    s = G.gladko(t)
    az = math.radians(252 + 36 * s)          # z południowego zachodu ku południowi
    el = math.radians(24 - 4 * s)
    cam.location = CEL + Vector((DK * math.cos(az) * math.cos(el), DK * math.sin(az) * math.cos(el), DK * math.sin(el)))
    G.patrz(cam, CEL)
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
for fc in G._fcurves(cam.animation_data.action):
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"

# ---------------------------------------------------------------- animacja
F_PEK, F_UPADEK, F_ZNIK = 110, 150, 200
F_PRZECHYL0, F_PRZECHYL1 = 175, 290
pw = slupy["Pd-Wsch"]
a = math.radians(315)
os_upadku = Vector((-math.sin(a), math.cos(a), 0))     # pozioma, prostopadła do kierunku PW
# drżenie, potem upadek na zewnątrz (przyspieszenie jak spadanie)
for f in range(1, KLATEK + 1):
    if f < F_PEK:
        ang, drg = 0.0, 0.0
    elif f < F_UPADEK:
        u = (f - F_PEK) / (F_UPADEK - F_PEK)
        ang = math.radians(4) * u * u
        drg = math.radians(1.2) * math.sin(f * 2.3) * u
    else:
        u = min(1.0, (f - F_UPADEK) / 22)
        ang = math.radians(4) + math.radians(84) * u * u
        drg = 0.0
    q = Matrix.Rotation(-(ang + drg), 4, os_upadku)
    pw.rotation_euler = q.to_euler()
    pw.keyframe_insert("rotation_euler", frame=f)
for fc in G._fcurves(pw.animation_data.action):
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"
for mm in (m_slup_pw, m_zloto_pw):
    al = mm.node_tree.nodes["Principled BSDF"].inputs["Alpha"]
    for f, v in ((1, 1.0), (F_UPADEK + 22, 1.0), (F_ZNIK, 0.0)):
        al.default_value = v
        al.keyframe_insert("default_value", frame=f)

# przechył całej ziemi z niebem na południowy wschód (oś poziomo w kierunku Pn-Wsch)
os_przech = Vector((1, 1, 0)).normalized()
KAT_PRZECH = math.radians(8.5)
for f in range(1, KLATEK + 1):
    u = G.gladko((f - F_PRZECHYL0) / (F_PRZECHYL1 - F_PRZECHYL0))
    kosmos.rotation_euler = Matrix.Rotation(KAT_PRZECH * u, 4, os_przech).to_euler()
    kosmos.keyframe_insert("rotation_euler", frame=f)
for fc in G._fcurves(kosmos.animation_data.action):
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"
# woda: poziom w świecie stały (0,40 m pod powierzchnią ziemi), więc zalewa tylko narożnik PW, gdy ten opada
pv = poziom.outputs[0]
for f, v in ((1, -0.40), (KLATEK, -0.40)):
    pv.default_value = v
    pv.keyframe_insert("default_value", frame=f)
G.wygladz(nt)

# napisy na ziemi: kierunki od początku, „POŁUDNIOWY WSCHÓD” po upadku słupa
for ob in nap_kier:
    G.alfa_napisu(ob, [(1, 0.85), (KLATEK, 0.85)])
G.alfa_napisu(pw_nap, [(1, 0.0), (F_UPADEK + 10, 0.0), (F_ZNIK + 10, 1.0)])

# napisy ekranowe u góry (przypięte do kamery)
ODL = 6.0
px = G.skala_px(cam, ODL)
def napis_ekran(tekst, y, rozm_px, kolor, krój="georgiab", nazwa="ekran"):
    pos = G.ekran_na_kamerze(cam, 960, y, ODL)
    pos.y += cam.data.shift_y * 1920 * px    # poprawka na przesunięcie obiektywu
    return G.napis(tekst, rozm_px * px, kolor, krój, "CENTER", rodzic=cam, loc=pos, nazwa=nazwa,
                   obrys=((5, 7, 12), 0.03 * rozm_px * px))
t1 = napis_ekran("Osiem słupów podpiera niebo", 70, 52, G.ZLOTY, nazwa="tytul1")
t1b = napis_ekran("mit chiński", 122, 30, (220, 214, 200), "georgia", nazwa="tytul1b")
t2 = napis_ekran("Brak słupa na południowym wschodzie", 70, 50, G.ZLOTY, nazwa="tytul2")
t2b = napis_ekran("ziemia kłoni się w tę stronę", 122, 32, (220, 214, 200), "georgia", nazwa="tytul2b")
for ob in (t1, t1b):
    G.alfa_napisu(ob, [(1, 0.0), (15, 0.0), (40, 1.0), (F_PEK, 1.0), (F_PEK + 25, 0.0)])
for ob in (t2, t2b):
    G.alfa_napisu(ob, [(1, 0.0), (F_ZNIK, 0.0), (F_ZNIK + 30, 1.0)])

G.renderuj(TU, opcje, kadr_klatka=KLATEK)
