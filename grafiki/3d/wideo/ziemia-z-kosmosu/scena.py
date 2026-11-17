# -*- coding: utf-8 -*-
"""
Klip „ziemia-z-kosmosu” do odcinka 2 „Wielki uskok…” (rozdz. 13: „Jedynym rodzajem ratunku jest ucieczka w kosmos,
a takiej możliwości jeszcze długo mieć nie będziemy”).

ILUSTRACJA: Ziemia i Księżyc w prawdziwej skali rozmiarów i odległości. Kamera odsuwa się od Ziemi, aż w kadrze
mieści się orbita Księżyca (średnio 384 400 km = 60,3 promienia Ziemi; promień Księżyca 0,2727 promienia Ziemi).
Podpisy podają odległości: do Księżyca ok. 3 dni lotu (misje Apollo), do Marsa w najlepszym razie ok. 55 mln km,
czyli ponad 140 razy dalej (sondy lecą tam ok. 7 miesięcy).
Tekstura Ziemi: NASA Blue Marble (domena publiczna). Gwiazdy: katalog HYG (CC BY-SA 4.0). Księżyc: kula z szumem (bez zdjęcia).

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/ziemia-z-kosmosu/scena.py
  ... -- --proba 1,150,250,400     (tylko kadry próbne PNG do _klatki/)
"""
import bpy, math, os, sys
from mathutils import Vector

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
import niebo as N

KLATEK = 400  # 16 s
opcje = G.argumenty()
sc = G.nowa_scena(KLATEK)
sc.eevee.taa_render_samples = int(os.environ.get("USKOK3D_PROBKI", "24"))

D_KS = 60.27                  # odległość Księżyca w promieniach Ziemi (384 400 km / 6378 km)
R_KS = 0.2727
SLONCE = Vector((-0.62, -0.74, 0.26)).normalized()   # kierunek do Słońca (z lewej, zza kamery)
KS_POZ = Vector((D_KS, 0, 0))
LENS = 50.0
D0, D1 = 7.6, 118.0           # odległość kamery od osi Ziemia–Księżyc na początku i na końcu
F_A, F_B = 55, 300            # odjazd kamery


def nd(nt, typ, **kw):
    n = nt.nodes.new(typ)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def mat(nt, op, a, b=None):
    n = nd(nt, "ShaderNodeMath", operation=op)
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]


def smooth(nt, e0, e1, x):
    n = nd(nt, "ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
    n.inputs["From Min"].default_value = e0; n.inputs["From Max"].default_value = e1
    nt.links.new(x, n.inputs["Value"])
    return n.outputs["Result"]


def dzien_wezel(nt, e0, e1):
    geo = nd(nt, "ShaderNodeNewGeometry")
    dot = nd(nt, "ShaderNodeVectorMath", operation="DOT_PRODUCT")
    nt.links.new(geo.outputs["Normal"], dot.inputs[0]); dot.inputs[1].default_value = SLONCE
    return smooth(nt, e0, e1, dot.outputs["Value"])


def kula(nazwa, r, material, seg=64):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=seg // 2)
    ob = bpy.context.active_object; ob.name = nazwa
    bpy.ops.object.shade_smooth(); ob.data.materials.append(material)
    return ob


# ---------------------------------------------------------------- Ziemia
os_ziemi = bpy.data.objects.new("os_Ziemi", None); sc.collection.objects.link(os_ziemi)
os_ziemi.rotation_euler = (math.radians(-20), math.radians(8), 0)      # północ lekko ku kamerze
ziemia = G.sfera_uv("Ziemia", 256, 128)
ziemia.parent = os_ziemi
mz = bpy.data.materials.new("Ziemia_mat"); mz.use_nodes = True
nt = mz.node_tree; nt.nodes.clear()
out = nd(nt, "ShaderNodeOutputMaterial")
tex = nd(nt, "ShaderNodeTexImage")
tex.image = G.wczytaj_obraz(os.path.join(G.DANE, "blue-marble", "blue-marble-2002-8192x4096.jpg"))
tex.extension = "EXTEND"
dz = dzien_wezel(nt, -0.12, 0.30)
jas = mat(nt, "MULTIPLY", mat(nt, "ADD", dz, 0.03), 1.3)
gam = nd(nt, "ShaderNodeCombineColor")
for i in range(3):
    nt.links.new(jas, gam.inputs[i])
kol = nd(nt, "ShaderNodeMixRGB", blend_type="MULTIPLY"); kol.inputs[0].default_value = 1.0
nt.links.new(tex.outputs["Color"], kol.inputs[1]); nt.links.new(gam.outputs[0], kol.inputs[2])
em = nd(nt, "ShaderNodeEmission"); nt.links.new(kol.outputs[0], em.inputs["Color"])
nt.links.new(em.outputs[0], out.inputs["Surface"])
ziemia.data.materials.append(mz)

# atmosfera
ma = bpy.data.materials.new("Atmosfera_mat"); ma.use_nodes = True
nt = ma.node_tree; nt.nodes.clear()
out = nd(nt, "ShaderNodeOutputMaterial")
e = nd(nt, "ShaderNodeEmission"); e.inputs["Color"].default_value = G.srgb((110, 170, 255)); e.inputs["Strength"].default_value = 1.6
tr = nd(nt, "ShaderNodeBsdfTransparent")
lw = nd(nt, "ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
w = mat(nt, "MULTIPLY", mat(nt, "POWER", lw.outputs["Facing"], 3.0), dzien_wezel(nt, -0.25, 0.35))
mx = nd(nt, "ShaderNodeMixShader")
nt.links.new(w, mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], out.inputs[0])
ma.surface_render_method = "BLENDED"
kula("Atmosfera", 1.018, ma, 96)

# ---------------------------------------------------------------- Księżyc
mk = bpy.data.materials.new("Ksiezyc_mat"); mk.use_nodes = True
nt = mk.node_tree; nt.nodes.clear()
out = nd(nt, "ShaderNodeOutputMaterial")
dz = dzien_wezel(nt, -0.05, 0.35)
tco = nd(nt, "ShaderNodeTexCoord")
sz = nd(nt, "ShaderNodeTexNoise"); sz.inputs["Scale"].default_value = 3.2; sz.inputs["Detail"].default_value = 6.0
nt.links.new(tco.outputs["Object"], sz.inputs["Vector"])
plamy = smooth(nt, 0.42, 0.62, sz.outputs[0])
jas = mat(nt, "MULTIPLY", mat(nt, "ADD", mat(nt, "MULTIPLY", dz, 1.05), 0.03), mat(nt, "ADD", mat(nt, "MULTIPLY", plamy, 0.38), 0.55))
cc = nd(nt, "ShaderNodeCombineColor")
nt.links.new(jas, cc.inputs[0]); nt.links.new(mat(nt, "MULTIPLY", jas, 0.97), cc.inputs[1]); nt.links.new(mat(nt, "MULTIPLY", jas, 0.92), cc.inputs[2])
em = nd(nt, "ShaderNodeEmission"); nt.links.new(cc.outputs[0], em.inputs["Color"])
nt.links.new(em.outputs[0], out.inputs["Surface"])
ksiezyc = kula("Ksiezyc", R_KS, mk)
ksiezyc.location = KS_POZ

# ---------------------------------------------------------------- kamera, tło, gwiazdy
cam = G.kamera((0, -D0, 0), (0, 0, 0), lens=LENS)
cam.data.clip_start, cam.data.clip_end = 0.05, 30000
cam.data.shift_y = 0.0
G.tlo_kamery(cam, odl=12000)
gw = N.wczytaj(6.0)
gwiazdy = N.siatka_gwiazd(gw, 8000.0, (36.0 / LENS) / 1920.0, wzmocnienie=0.95)
gwiazdy.rotation_euler = (math.radians(63), 0, math.radians(40))   # pas Drogi Mlecznej poza środkiem kadru

ODL = 0.3
px = G.skala_px(cam, ODL)


def napis_ekran(tekst, x, y, rozm_px, kolor, kroj="georgiab", wyr="CENTER", nazwa="ekran"):
    pos = G.ekran_na_kamerze(cam, x, y, ODL)
    pos.y += cam.data.shift_y * 0  # shift przesuwa obraz, nie napisy przypięte do kamery
    return G.napis(tekst, rozm_px * px, kolor, kroj, wyr, rodzic=cam, loc=pos, nazwa=nazwa,
                   obrys=((5, 7, 12), 0.03 * rozm_px * px))


def etykieta(tekst, rozm_px, kolor, nazwa, kroj="arialb"):
    return G.napis(tekst, rozm_px * px, kolor, kroj, "CENTER", rodzic=cam, nazwa=nazwa,
                   obrys=((5, 7, 12), 0.035 * rozm_px * px))


def na_ekran(p, dx=0.0, dy=0.0):
    q = cam.matrix_world.inverted() @ Vector(p)
    q = q * (ODL / -q.z)
    return Vector((q.x + dx * px, q.y + dy * px, -ODL - 0.0005))


# linia Ziemia–Księżyc (pojawia się pod koniec), grubość w skali końcowego kadru
PX_KONIEC = D1 * (36.0 / LENS) / 1920.0        # promieni Ziemi na piksel w końcowym kadrze
linia_cu = bpy.data.curves.new("odleglosc", "CURVE"); linia_cu.dimensions = "3D"; linia_cu.bevel_depth = PX_KONIEC * 1.1
n_kresek = 46
for i in range(n_kresek):
    a = 1.6 + (D_KS - 2.4) * i / n_kresek
    b = a + (D_KS - 2.4) / n_kresek * 0.55
    sp = linia_cu.splines.new("POLY"); sp.points.add(1)
    sp.points[0].co = (a, 0, 0, 1); sp.points[1].co = (b, 0, 0, 1)
linia_ob = bpy.data.objects.new("odleglosc", linia_cu); sc.collection.objects.link(linia_ob)
m_lin = G.material_emisja("odleglosc_mat", G.ZLOTY, 0.0); linia_cu.materials.append(m_lin)
G.animuj_alfa(m_lin, [(1, 0), (250, 0), (290, 0.9)])

tytul = napis_ekran("Ziemia i Księżyc w prawdziwej skali", 1130, 80, 52, G.ZLOTY, nazwa="tytul")
G.alfa_napisu(tytul, [(1, 0), (150, 0), (185, 1)])
et_zm = etykieta("Ziemia", 42, (150, 195, 255), "et_ziemia")
et_ks = etykieta("Księżyc", 42, (228, 228, 232), "et_ksiezyc")
et_odl = etykieta("384 400 km  ·  3 dni lotu", 38, G.ZLOTY, "et_odl", "georgiab")
et_mars = napis_ekran("Do Marsa w najlepszym razie 55 mln km:\nponad 140 razy dalej, ok. 7 miesięcy lotu", 960, 770, 36,
                      (240, 232, 210), "georgia", nazwa="et_mars")
G.alfa_napisu(et_zm, [(1, 0), (230, 0), (265, 1)])
G.alfa_napisu(et_ks, [(1, 0), (240, 0), (275, 1)])
G.alfa_napisu(et_odl, [(1, 0), (270, 0), (305, 1)])
G.alfa_napisu(et_mars, [(1, 0), (315, 0), (350, 1)])


def ustaw(scene, depsgraph=None):
    f = scene.frame_current
    t = G.gladko5((f - F_A) / float(F_B - F_A))
    d = D0 * (D1 / D0) ** t                          # odjazd wykładniczy: stałe tempo „zmniejszania się” Ziemi
    cx = (D_KS / 2) * G.gladko5((f - F_A - 60) / float(F_B - F_A - 60))   # cel: od Ziemi do środka odcinka Ziemia–Księżyc
    cam.location = Vector((cx, -d, 0.0))
    G.patrz(cam, Vector((cx, 0, 0)))
    ziemia.rotation_euler = (0, 0, math.radians(-112 + 14 * (f - 1) / (KLATEK - 1)))   # Europa i Afryka ku kamerze
    bpy.context.view_layer.update()
    et_zm.location = na_ekran((0, 0, 0), 0, -70)
    et_ks.location = na_ekran(KS_POZ, 0, -58)
    et_odl.location = na_ekran((D_KS / 2, 0, 0), 0, 44)


bpy.app.handlers.frame_change_pre.append(ustaw)
ustaw(sc)
for ob in sc.objects:
    ob.visible_shadow = False

G.renderuj(TU, opcje, kadr_klatka=KLATEK)
