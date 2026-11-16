# -*- coding: utf-8 -*-
"""
Klip „wenus-pozycja” do odcinka 2 „Wielki uskok…” (rozdz. 13, cytat z B. J. Lenga).

HIPOTEZA (twierdzenie cytowanego autora): Wenus wraca na pozycję, jaką miała 27 lipca 9792 r. p.n.e.,
i zajmuje ją po 11 804 latach, 22–23 grudnia 2012 r.
Prosta animacja: Słońce, orbity Wenus i Ziemi, w tle kierunki gwiazdozbiorów Zodiaku. Licznik lat biegnie
od 9792 p.n.e. do 2012 r., Wenus okrąża Słońce (przy dużej prędkości widać tylko świecącą orbitę),
a na końcu zwalnia i staje w zaznaczonym miejscu. Położenie Wenus i Ziemi na końcu = 22 grudnia 2012
według średnich elementów orbit (J2000). Tego, że Wenus stała tam samo w 9792 p.n.e., ten sam rachunek
NIE potwierdza (patrz README) – to twierdzenie cytowanego autora.

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/wenus-pozycja/scena.py
  ... -- --proba 1,150,280,350     (tylko kadry próbne PNG do _klatki/)
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G

KLATEK = 350  # 14 s
opcje = G.argumenty()
sc = G.nowa_scena(KLATEK)
sc.eevee.taa_render_samples = int(os.environ.get("USKOK3D_PROBKI", "24"))

# ---------------------------------------------------------------- rachunek (średnie elementy orbit, J2000)
JD_2012 = 2456283.5                     # 22 grudnia 2012, 0h
T = (JD_2012 - 2451545.0) / 36525
L_WENUS = math.radians((181.97973 + 58517.81539 * T) % 360)   # ok. 213,7°
L_ZIEMIA = math.radians((100.46457 + 35999.37245 * T) % 360)  # ok. 90,8°
OKR_WENUS = 11804 * 365.25 / 224.701    # okrążeń Wenus w 11 804 latach

S_ = 4.2                                 # 1 au w jednostkach sceny
R_W, R_Z = 0.72333 * S_, 1.0 * S_

def xy(r, l, z=0.0):
    return Vector((r * math.cos(l), r * math.sin(l), z))

# ---------------------------------------------------------------- scena
sc.world.node_tree.nodes["Background"].inputs[0].default_value = G.srgb((24, 34, 62))
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.4

def kula(nazwa, r, mat, seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=seg // 2)
    ob = bpy.context.active_object; ob.name = nazwa
    bpy.ops.object.shade_smooth(); ob.data.materials.append(mat)
    ob.visible_shadow = False
    return ob

def mat_poswiata(nazwa, kolor, sila, potega):
    m = bpy.data.materials.new(nazwa); m.use_nodes = True
    nt_ = m.node_tree; nt_.nodes.clear()
    o = nt_.nodes.new("ShaderNodeOutputMaterial")
    e = nt_.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = G.srgb(kolor); e.inputs["Strength"].default_value = sila
    tr = nt_.nodes.new("ShaderNodeBsdfTransparent")
    lw = nt_.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    inv = nt_.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    nt_.links.new(lw.outputs["Facing"], inv.inputs[1])
    pw = nt_.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = potega
    nt_.links.new(inv.outputs[0], pw.inputs[0])
    al = nt_.nodes.new("ShaderNodeValue"); al.name = "alfa"; al.outputs[0].default_value = 1.0
    ml = nt_.nodes.new("ShaderNodeMath"); ml.operation = "MULTIPLY"
    nt_.links.new(pw.outputs[0], ml.inputs[0]); nt_.links.new(al.outputs[0], ml.inputs[1])
    mx = nt_.nodes.new("ShaderNodeMixShader")
    nt_.links.new(ml.outputs[0], mx.inputs[0]); nt_.links.new(tr.outputs[0], mx.inputs[1]); nt_.links.new(e.outputs[0], mx.inputs[2])
    nt_.links.new(mx.outputs[0], o.inputs[0])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m

slonce = kula("Slonce", 0.6, G.material_emisja("Slonce_mat", (255, 220, 150)))
for n in bpy.data.materials["Slonce_mat"].node_tree.nodes:
    if n.type == "EMISSION":
        n.inputs["Strength"].default_value = 4.0
kula("Korona", 1.1, mat_poswiata("Korona_mat", (255, 200, 110), 2.0, 2.5))
ld = bpy.data.lights.new("SwiatloSlonca", "POINT"); ld.energy = 900; ld.shadow_soft_size = 0.5; ld.use_shadow = False
lo = bpy.data.objects.new("SwiatloSlonca", ld); sc.collection.objects.link(lo)

def mat_planeta(nazwa, kolor, emisja=0.25):
    m = bpy.data.materials.new(nazwa); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = G.srgb(kolor); p.inputs["Roughness"].default_value = 0.6
    p.inputs["Emission Color"].default_value = G.srgb(kolor); p.inputs["Emission Strength"].default_value = emisja
    try:
        m.surface_render_method = "DITHERED"
    except Exception:
        pass
    return m
m_w = mat_planeta("Wenus_mat", (250, 232, 190), 0.35)
m_z = mat_planeta("Ziemia_mat", (70, 140, 220), 0.25)
wenus = kula("Wenus", 0.2, m_w)
ziemia = kula("Ziemia", 0.21, m_z)

def okrag(r, nazwa, kolor, alfa, grub=0.018, przerywany=False):
    cu = bpy.data.curves.new(nazwa, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = grub
    n = 256
    if przerywany:
        for i in range(0, n, 2):
            sp = cu.splines.new("POLY"); sp.points.add(1)
            for j, t in enumerate((i, i + 1)):
                sp.points[j].co = (*xy(r, 2 * math.pi * t / n), 1)
    else:
        sp = cu.splines.new("POLY"); sp.points.add(n - 1)
        for i in range(n):
            sp.points[i].co = (*xy(r, 2 * math.pi * i / n), 1)
        sp.use_cyclic_u = True
    ob = bpy.data.objects.new(nazwa, cu); sc.collection.objects.link(ob)
    m = G.material_emisja(nazwa + "_mat", kolor, alfa); cu.materials.append(m); ob["mat"] = m.name
    return ob, m

orb_w, m_ow = okrag(R_W, "orbita_Wenus", (250, 225, 170), 0.45)
orb_z, m_oz = okrag(R_Z, "orbita_Ziemi", (120, 170, 230), 0.4)
# świecąca orbita Wenus (gdy Wenus krąży za szybko, by ją zobaczyć)
bl_w, m_blw = okrag(R_W, "smuga_Wenus", (255, 236, 190), 0.0, 0.045)
for n in m_blw.node_tree.nodes:
    if n.type == "EMISSION":
        n.inputs["Strength"].default_value = 1.6
bl_z, m_blz = okrag(R_Z, "smuga_Ziemi", (140, 190, 255), 0.0, 0.04)

# Zodiak: kierunki gwiazdozbiorów (przybliżone środki na ekliptyce, długość ekliptyczna J2000)
ZODIAK = [("Ryby", 5), ("Baran", 35), ("Byk", 65), ("Bliźnięta", 95), ("Rak", 125), ("Lew", 150), ("Panna", 190),
          ("Waga", 225), ("Skorpion", 245), ("Strzelec", 275), ("Koziorożec", 305), ("Wodnik", 335)]
R_ZOD = 1.45 * S_
okrag(R_ZOD - 0.55, "zodiak", (240, 196, 111), 0.18, 0.012, przerywany=True)
for nazwa, lam in ZODIAK:
    ob = G.napis(nazwa.upper(), 0.36, (240, 196, 111), "georgiab", "CENTER", loc=xy(R_ZOD, math.radians(lam), 0.02),
                 rot=(0, 0, math.radians(lam) + (math.pi / 2 if math.sin(math.radians(lam)) < 0 else -math.pi / 2)),
                 nazwa="zod_" + nazwa, alfa=0.55)   # dolne napisy obrócone, by czytały się z widoku kamery

# znacznik pozycji Wenus (twierdzenie autora: ta sama w 9792 p.n.e. i 22–23 XII 2012)
zn = kula("Znacznik", 0.34, mat_poswiata("Znacznik_mat", G.ZLOTY, 3.0, 1.2))
zn.location = xy(R_W, L_WENUS)
bpy.ops.mesh.primitive_torus_add(major_radius=0.42, minor_radius=0.025, location=zn.location)
ring = bpy.context.active_object; ring.name = "ZnacznikPierscien"
m_ring = G.material_emisja("Pierscien_mat", G.ZLOTY, 1.0); ring.data.materials.append(m_ring)
kier = xy(1, L_WENUS)
linia_cu = bpy.data.curves.new("kierunek", "CURVE"); linia_cu.dimensions = "3D"; linia_cu.bevel_depth = 0.012
sp = linia_cu.splines.new("POLY"); sp.points.add(1)
sp.points[0].co = (*(kier * 0.75), 1); sp.points[1].co = (*(kier * (R_ZOD - 0.7)), 1)
linia_ob = bpy.data.objects.new("kierunek", linia_cu); sc.collection.objects.link(linia_ob)
m_lin = G.material_emisja("kierunek_mat", G.ZLOTY, 0.0); linia_cu.materials.append(m_lin)

# ---------------------------------------------------------------- kamera i napisy
CEL = Vector((0, 0.3, 0))
cam = G.kamera((0, -12, 22), CEL, lens=40)
G.tlo_kamery(cam, odl=120)
ODL = 10.0
px = G.skala_px(cam, ODL)
def napis_ekran(tekst, x, y, rozm_px, kolor, krój="georgiab", wyr="CENTER", nazwa="ekran"):
    pos = G.ekran_na_kamerze(cam, x, y, ODL)
    return G.napis(tekst, rozm_px * px, kolor, krój, wyr, rodzic=cam, loc=pos, nazwa=nazwa,
                   obrys=((5, 7, 12), 0.03 * rozm_px * px))
licznik = napis_ekran("27 lipca 9792 p.n.e.", 960, 70, 54, G.ZLOTY, nazwa="licznik")
podtyt = napis_ekran("pozycja Wenus według B. J. Lenga", 960, 124, 30, (220, 214, 200), "georgia", nazwa="podtytul")
po_drodze = napis_ekran("11 804 lata – ok. 19 200 okrążeń Wenus", 960, 124, 30, (220, 214, 200), "georgia", nazwa="po_drodze")
et_w = G.napis("Wenus", 0.4, (250, 232, 190), "arialb", "CENTER", nazwa="et_Wenus", obrys=((5, 7, 12), 0.02))
et_z = G.napis("Ziemia", 0.4, (140, 190, 255), "arialb", "CENTER", nazwa="et_Ziemia", obrys=((5, 7, 12), 0.02))
for ob in (et_w, et_z):
    c = ob.constraints.new("COPY_ROTATION"); c.target = cam

F_START, F_STOP = 85, 285      # bieg licznika
G.alfa_napisu(podtyt, [(1, 0), (10, 0), (35, 1), (F_START, 1), (F_START + 15, 0), (F_STOP, 0), (F_STOP + 25, 1)])
G.alfa_napisu(po_drodze, [(1, 0), (F_START + 15, 0), (F_START + 35, 1), (F_STOP - 30, 1), (F_STOP - 10, 0)])
G.alfa_napisu(licznik, [(1, 0), (5, 0), (25, 1)])
G.animuj_alfa(m_lin, [(1, 0), (20, 0), (45, 0.5)])
G.alfa_napisu(et_z, [(1, 0), (F_STOP - 40, 0), (F_STOP - 10, 1)])

# ---------------------------------------------------------------- ruch
def postep(f):
    """0..1 – ułamek drogi od 9792 p.n.e. do 2012 (szybko w środku, wolno na końcach)."""
    t = (f - F_START) / (F_STOP - F_START)
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return G.gladko5(t)

MIES = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca", "sierpnia", "września",
        "października", "listopada", "grudnia"]
def ustaw(scene, depsgraph=None):
    f = scene.frame_current
    p = postep(f)
    # liczba okrążeń, które Wenus ma jeszcze do zrobienia; na końcu staje w znaczniku
    zostalo = round(OKR_WENUS) * (1 - p)      # całkowita liczba okrążeń: start i koniec w tym samym miejscu (twierdzenie autora)
    lw = L_WENUS - 2 * math.pi * zostalo
    wenus.location = xy(R_W, lw)
    zostalo_z = 11804 * (1 - p)
    lz = L_ZIEMIA - 2 * math.pi * zostalo_z
    ziemia.location = xy(R_Z, lz)
    # prędkość (okrążeń na klatkę): przy dużej widać tylko świecącą smugę orbity
    dp = postep(f + 1) - postep(f - 1)
    v = OKR_WENUS * dp / 2
    smuga = max(0.0, min(1.0, (v - 0.04) / 0.25))
    for nd in m_blw.node_tree.nodes:
        if nd.type == "MIX_SHADER":
            nd.inputs[0].default_value = 0.75 * smuga
    vz = 11804 * dp / 2
    smz = max(0.0, min(1.0, (vz - 0.04) / 0.25))
    for nd in m_blz.node_tree.nodes:
        if nd.type == "MIX_SHADER":
            nd.inputs[0].default_value = 0.55 * smz
    pw_ = m_w.node_tree.nodes["Principled BSDF"].inputs["Alpha"]
    pw_.default_value = 1 - smuga
    m_z.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = (1 - smz) * (1.0 if f > F_STOP - 60 else 0.0)
    et_w.location = wenus.location + Vector((0, 0, 0.62))
    et_z.location = ziemia.location + Vector((0, 0, 0.62))
    for nd in bpy.data.materials["et_Wenus_mat"].node_tree.nodes:
        if nd.type == "MIX_SHADER":
            nd.inputs[0].default_value = 1 - smuga
    for nd in bpy.data.materials["et_Wenus_obrys_mat"].node_tree.nodes:
        if nd.type == "MIX_SHADER":
            nd.inputs[0].default_value = 1 - smuga
    # licznik lat
    rok_astr = -9791 + p * (2012 + 9791)
    if f >= F_STOP:
        tekst = "22 grudnia 2012"
    elif f <= F_START:
        tekst = "27 lipca 9792 p.n.e."
    else:
        r = int(round(rok_astr))
        tekst = f"{1 - r} p.n.e." if r <= 0 else f"{r} n.e."
    licznik.data.body = tekst
    if licznik.children:
        licznik.children[0].data.body = tekst
    # znacznik pulsuje lekko
    s = 1 + 0.08 * math.sin(f * 0.15)
    ring.scale = (s, s, s)
    # kamera: powolny obrót
    t = (f - 1) / (KLATEK - 1)
    az = math.radians(-90 + 25 * G.gladko(t))
    el = math.radians(58 - 6 * G.gladko(t))
    D = 30.0
    cam.location = CEL + Vector((D * math.cos(az) * math.cos(el), D * math.sin(az) * math.cos(el), D * math.sin(el)))
    G.patrz(cam, CEL)
bpy.app.handlers.frame_change_pre.append(ustaw)
ustaw(sc)
for ob in sc.objects:
    ob.visible_shadow = False

G.renderuj(TU, opcje, kadr_klatka=KLATEK)
