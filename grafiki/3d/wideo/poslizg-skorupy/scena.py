# -*- coding: utf-8 -*-
"""Klip „poslizg-skorupy”: poślizg twardej litosfery po półpłynnym płaszczu (rozdział 03, hipoteza).

Tekst Leszka Klimka: „na pewnej głębokości skorupa Ziemi przechodzi stopniowo w półpłynny płaszcz i zapewne
gdzieś w tym miejscu, na głębokości 400-600 km, traci swą »przyczepność«. To w tym miejscu może dochodzić
do »poślizgu« twardej litosfery na półpłynnym płaszczu.”

Przekrój Ziemi z wyciętą ćwiartką, warstwy w skali (promień 6371 km; jądro zewnętrzne do 3480 km od środka,
wewnętrzne do 1220 km). Zewnętrzna powłoka do głębokości 500 km (środek strefy 400–600 km z tekstu)
obraca się wokół osi poziomej względem nieruchomego wnętrza: lądy na powierzchni i kreski na przekroju
skorupy przesuwają się, kreski płaszcza stoją. Geometria jest nieruchoma (kula obrócona wokół środka pokrywa
się sama ze sobą), obracają się tylko wzory – dlatego przekrój zostaje ciągły.

Uruchomienie (z katalogu repozytorium):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/poslizg-skorupy/scena.py
  ... -- --proba 60,200,330,500
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
from wezly import Wezly, animuj_wartosc

OPCJE = G.argumenty()
KLATKI = 500  # 20 s
RZ = 6371.0
R_POSL = 1 - 500 / RZ           # granica poślizgu (środek strefy)
R_400, R_600 = 1 - 400 / RZ, 1 - 600 / RZ
R_JZ, R_JW = 3480 / RZ, 1220 / RZ
OS = Vector((0, 1, 0))          # oś obrotu skorupy: prostopadła do przekroju y = 0

F_ZOOM0, F_ZOOM1 = 95, 185
F_RUCH = [(205, 0.0), (265, 2.4), (290, 2.4), (350, 5.6), (372, 5.6), (430, 8.0), (500, 12.0)]  # stopnie
F_WYJAZD0, F_WYJAZD1 = 405, 490

sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))


# ---------------------------------------------------------------- geometria
def kula(nazwa, r, seg=128):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r)
    ob = bpy.context.active_object
    ob.name = nazwa
    bpy.ops.object.shade_smooth()
    return ob


def odejmij(ob, narz):
    m = ob.modifiers.new("odejm", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.solver = "EXACT"
    m.object = narz
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)


# klin: ćwiartka x > 0, y > 0 (zwrócona do kamery)
bpy.ops.mesh.primitive_cube_add(size=1, location=(1.5, 1.5, 0))
klin = bpy.context.active_object
klin.scale = (3, 3, 3)
skor = kula("Skorupa", 1.0)
wew = kula("Wnetrze", R_POSL, 128)
srodek_kuli = kula("Pomoc", R_POSL - 1e-4, 128)
odejmij(skor, srodek_kuli)
odejmij(skor, klin)
odejmij(wew, klin)
for o in (klin, srodek_kuli):
    bpy.data.objects.remove(o, do_unlink=True)
for o in (skor, wew):
    o.data.materials.clear()
    for p in o.data.polygons:
        p.material_index = 0
        p.use_smooth = abs(p.normal.x) < 0.999 and abs(p.normal.y) < 0.999

img_lad = G.wczytaj_obraz(G.tekstura_ziemi(8192, (255, 255, 255), (0, 0, 0), "maska_lad"), nieliniowy=False)


def obrocony(W, wektor, nazwa_kata):
    kat = W.wartosc(0.0, nazwa_kata)
    return W.obrot(wektor, tuple(OS), W.mul(kat, -math.pi / 180)), kat


# --- materiał skorupy: powierzchnia (lądy, morze) + przekrój (skały z kreskami) – wzory obracają się
ms = bpy.data.materials.new("Skorupa")
ms.use_nodes = True
nts = ms.node_tree
nts.nodes.clear()
W = Wezly(nts)
o = W.coord("Object")
r = W.vmath("LENGTH", o)
po, _ = obrocony(W, o, "kat")
pn = W.norm(po)
px_, py_, pz_ = W.sep(pn)
lad = W.sep(W.srodowisko(img_lad, W.vec(px_, W.mul(py_, -1.0), pz_)))[0]
morze = W.mix(W.smooth(-0.2, 0.9, pz_), G.srgb(G.MORZE_USKOK), G.srgb((110, 196, 238)))
pow_kol = W.mix(lad, morze, G.srgb(G.ZIELEN_USKOK))
# siatka południków co 15° na powierzchni (obraca się ze skorupą) – pokazuje ruch
dl = W.math("ARCTAN2", py_, px_)
siatka = W.linia(W.sub(W.math("FRACT", W.add(W.div(dl, math.radians(15)), 0.5)), 0.5), 0.012, 0.01)
pow_kol = W.mix(W.mul(siatka, 0.25), pow_kol, G.srgb((255, 255, 255)))
# przekrój skorupy: brązowoszara skała, ciemne kreski co 1,5° kąta wokół osi obrotu
kat_os = W.math("ARCTAN2", px_, pz_)              # kąt w płaszczyźnie przekroju (wokół osi Y)
kres = W.linia(W.sub(W.math("FRACT", W.add(W.div(kat_os, math.radians(1.5)), 0.5)), 0.5), 0.06, 0.03)
glebia = W.smooth(R_POSL, 1.0, r)
skala = W.mix(glebia, G.srgb((118, 92, 74)), G.srgb((170, 140, 110)))
skala = W.mix(W.mul(kres, 0.75), skala, G.srgb((60, 44, 34)))
# powierzchnia czy przekrój? (powierzchnia ma r ≈ 1)
na_pow = W.smooth(0.9975, 0.9995, r)
kol = W.mix(na_pow, skala, pow_kol)
nrm = W.norm(W.geometria("Normal"))
sw = W.dot(nrm, tuple(Vector((0.35, 0.55, 0.75)).normalized()))
cien = W.add(0.74, W.mul(W.mx(sw, 0.0), 0.3))
kol = W.vmath("MULTIPLY", kol, W.vec(cien, cien, cien))
W.emisja_wyjscie(kol)
skor.data.materials.append(ms)

# --- materiał wnętrza: płaszcz (półpłynny, kreski nieruchome), jądro zewnętrzne i wewnętrzne
mw = bpy.data.materials.new("Wnetrze")
mw.use_nodes = True
ntw = mw.node_tree
ntw.nodes.clear()
W2 = Wezly(ntw)
o2 = W2.coord("Object")
r2 = W2.vmath("LENGTH", o2)
x2, y2, z2 = W2.sep(o2)
plaszcz = W2.mix(W2.smooth(R_JZ, R_POSL, r2), G.srgb((178, 52, 24)), G.srgb((240, 128, 50)))
k2 = W2.math("ARCTAN2", x2, z2)
kres2 = W2.linia(W2.sub(W2.math("FRACT", W2.add(W2.div(k2, math.radians(1.5)), 0.5)), 0.5), 0.06, 0.03)
kres2 = W2.mul(kres2, W2.smooth(R_POSL - 0.06, R_POSL - 0.01, r2))      # tylko tuż pod granicą
plaszcz = W2.mix(W2.mul(kres2, 0.55), plaszcz, G.srgb((120, 30, 10)))
jz = W2.mix(W2.smooth(R_JW, R_JZ, r2), G.srgb((250, 196, 70)), G.srgb((236, 150, 40)))
kol2 = W2.mix(W2.smooth(R_JZ - 0.004, R_JZ + 0.004, r2), jz, plaszcz)
kol2 = W2.mix(W2.smooth(R_JW - 0.004, R_JW + 0.004, r2), G.srgb((255, 236, 160)), kol2)
nrm2 = W2.norm(W2.geometria("Normal"))
sw2 = W2.dot(nrm2, tuple(Vector((0.35, 0.55, 0.75)).normalized()))
cien2 = W2.add(0.80, W2.mul(W2.mx(sw2, 0.0), 0.22))
kol2 = W2.vmath("MULTIPLY", kol2, W2.vec(cien2, cien2, cien2))
W2.emisja_wyjscie(kol2)
wew.data.materials.append(mw)

klucze = [(f, v) for f, v in F_RUCH]
animuj_wartosc(nts, "kat", klucze)


# --- strefa poślizgu 400–600 km na przekroju y = 0 (złota, półprzezroczysta) i linia granicy
def cwierc_pierscien(nazwa, r0, r1, y, mat, a0=-90.0, a1=90.0, n=256):
    """pierścień w płaszczyźnie y (x >= 0), kąty od osi X w stronę Z"""
    v, f = [], []
    for k in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * k / n)
        v += [(r0 * math.cos(a), y, r0 * math.sin(a)), (r1 * math.cos(a), y, r1 * math.sin(a))]
    for k in range(n):
        q = 2 * k
        f.append((q, q + 2, q + 3, q + 1))
    me = bpy.data.meshes.new(nazwa)
    me.from_pydata(v, [], f)
    ob = bpy.data.objects.new(nazwa, me)
    sc.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


m_strefa = G.material_emisja("Strefa", G.ZLOTY, 0.0)
G.animuj_alfa(m_strefa, [(1, 0.0), (F_ZOOM1 - 20, 0.0), (F_ZOOM1 + 10, 0.42)])
cwierc_pierscien("Strefa", R_600, R_400, 0.0015, m_strefa)
m_gran = G.material_emisja("Granica", (255, 236, 170), 0.0)
G.animuj_alfa(m_gran, [(1, 0.0), (F_ZOOM1 - 10, 0.0), (F_ZOOM1 + 20, 1.0)])
cwierc_pierscien("Granica", R_POSL - 0.0012, R_POSL + 0.0012, 0.002, m_gran)

# ---------------------------------------------------------------- kamera
CEL_CALY = Vector((0.0, 0.0, -0.02))
KIER_CALY = Vector((0.62, 1.0, 0.42)).normalized()
A_ZOOM = math.radians(8.0)                       # punkt na krawędzi przekroju (y = 0)
CEL_ZOOM = Vector((math.cos(A_ZOOM), 0, math.sin(A_ZOOM))) * 0.955
KIER_ZOOM = Vector((0.18, 1.0, 0.16)).normalized()
ODL_CALY, ODL_ZOOM = 6.8, 0.62
cam = G.kamera(CEL_CALY + KIER_CALY * ODL_CALY, CEL_CALY, lens=50)
PRZES = 0.04   # obraz nieco wyżej (dół 200 px na podpis)
GORA_ZOOM = CEL_ZOOM.normalized()     # w zbliżeniu „góra” kadru = na zewnątrz Ziemi
_poprz = [None]


def poza(f):
    if f <= F_WYJAZD0:
        s = G.gladko5((f - F_ZOOM0) / (F_ZOOM1 - F_ZOOM0))
    else:
        s = 1 - G.gladko5((f - F_WYJAZD0) / (F_WYJAZD1 - F_WYJAZD0))
    cel = CEL_CALY.lerp(CEL_ZOOM, s)
    kier = KIER_CALY.slerp(KIER_ZOOM, s) if hasattr(KIER_CALY, "slerp") else KIER_CALY.lerp(KIER_ZOOM, s).normalized()
    kier = kier.normalized()
    odl = math.exp(math.log(ODL_CALY) + (math.log(ODL_ZOOM) - math.log(ODL_CALY)) * s)
    # powolny obrót w widoku całości
    kat = math.radians(-6 + 12 * G.gladko5(f / KLATKI)) * (1 - s)
    kier = Matrix.Rotation(kat, 3, "Z") @ kier
    return cel, kier, odl, s


def ustaw(f):
    cel, kier, odl, s = poza(f)
    cam.location = cel + kier * odl
    gora = Vector((0, 0, 1)).lerp(GORA_ZOOM, s).normalized()
    g = (gora - kier * kier.dot(gora)).normalized()
    cel2 = cel - g * (0.025 * (1 - s) + 0.02 * s) * odl
    fwd = (cel2 - cam.location).normalized()
    prawo = fwd.cross(g).normalized()
    up = prawo.cross(fwd)
    M = Matrix((prawo, up, -fwd)).transposed()
    e = M.to_euler("XYZ", _poprz[0]) if _poprz[0] is not None else M.to_euler("XYZ")
    _poprz[0] = e
    cam.rotation_euler = e


for f in sorted(set([1, 40, 80] + list(range(F_ZOOM0, F_ZOOM1 + 1, 6)) + [F_ZOOM1, 250, 330, F_WYJAZD0]
                    + list(range(F_WYJAZD0, F_WYJAZD1 + 1, 6)) + [F_WYJAZD1, KLATKI])):
    ustaw(f)
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
G.wygladz(cam)
G.tlo_kamery(cam, odl=30)


def ekran(punkt, f):
    ustaw(f)
    bpy.context.view_layer.update()
    v = world_to_camera_view(sc, cam, Vector(punkt))
    return v.x * 1920, (1 - v.y) * 1080


# ---------------------------------------------------------------- napisy
# Napisy i kreski przypięte do kamery, bardzo blisko niej (w zbliżeniu kula jest ok. 0,6 jednostki od kamery).
ODL_N = 0.2
px_u = G.skala_px(cam, ODL_N)


def podpis(nazwa, tekst, x, y, rozm, kolor, klucze, wyr="LEFT", kroj="arialb", obrys=True):
    ob = G.napis(tekst, rozm * 1.4 * px_u, kolor, kroj, wyr, rodzic=cam, loc=G.ekran_na_kamerze(cam, x, y, ODL_N),
                 nazwa=nazwa, obrys=((8, 20, 45), 1.2 * px_u) if obrys else None, odstep=1.1)
    G.alfa_napisu(ob, klucze)
    return ob


def linia_ekranu(nazwa, a, b, kolor, klucze, grub=2.0):
    A = G.ekran_na_kamerze(cam, a[0], a[1], ODL_N + 0.0001)
    B = G.ekran_na_kamerze(cam, b[0], b[1], ODL_N + 0.0001)
    d = (B - A)
    n = Vector((-d.y, d.x, 0)).normalized() * grub * px_u / 2
    me = bpy.data.meshes.new(nazwa)
    me.from_pydata([A + n, B + n, B - n, A - n], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(nazwa, me)
    sc.collection.objects.link(ob)
    ob.parent = cam
    m = G.material_emisja(nazwa + "_mat", kolor)
    me.materials.append(m)
    G.animuj_alfa(m, klucze)
    return ob


def na_przekroju(kat_st, r):
    a = math.radians(kat_st)
    return Vector((math.cos(a) * r, 0, math.sin(a) * r))


# --- widok całości: warstwy na promieniu przekroju y = 0, podpisy w kolumnie po prawej
F_CALY = 40
WYG = [(F_ZOOM0 - 10, 1.0), (F_ZOOM0 + 15, 0.0)]
WARSTWY = [("skorupa", "twarda skorupa (litosfera)", 0.962, 12), ("plaszcz", "półpłynny płaszcz", 0.74, 24),
           ("jadro_z", "jądro zewnętrzne", 0.37, 36), ("jadro_w", "jądro wewnętrzne", 0.08, 48)]
pkt = [(n, t, ekran(na_przekroju(-28.0, r), F_CALY), f0) for n, t, r, f0 in WARSTWY]
srodek_px = ekran(Vector((0, 0, 0)), F_CALY)
kraw_px = ekran(Vector((0, 1, 0)), F_CALY)
X_KOL = srodek_px[0] + 2667 / ODL_CALY + 50
ys = sorted([p[1] for _, _, p, _ in pkt])
y_et = []
for _, _, p, _ in sorted(pkt, key=lambda q: q[2][1]):
    y = p[1]
    if y_et and y < y_et[-1] + 56:
        y = y_et[-1] + 56
    y_et.append(y)
for (n, t, p, f0), y in zip(sorted(pkt, key=lambda q: q[2][1]), y_et):
    kl = [(1, 0.0), (f0, 0.0), (f0 + 15, 1.0)] + WYG
    linia_ekranu("Kr_" + n, p, (X_KOL - 14, y), (235, 235, 235), kl, 1.8)
    bpy.ops.mesh.primitive_circle_add(vertices=16, radius=4 * px_u, fill_type="TRIFAN",
                                      location=G.ekran_na_kamerze(cam, p[0], p[1], ODL_N - 0.0001))
    kk = bpy.context.active_object
    kk.parent = cam
    mk = G.material_emisja("Kp_" + n, (255, 255, 255))
    kk.data.materials.append(mk)
    G.animuj_alfa(mk, kl)
    podpis("Et_" + n, t, X_KOL, y, 26, (255, 255, 255), kl)
print("[poslizg] warstwy px", [(n, [round(v) for v in p]) for n, _, p, _ in pkt])

# --- zbliżenie (powierzchnia u góry kadru, głębokość w dół): podziałka głębokości i opisy
F_POD = F_ZOOM1 - 5
FZ = F_ZOOM1 + 10
kl_pod = [(1, 0.0), (F_POD, 0.0), (F_POD + 18, 1.0), (F_WYJAZD0 + 5, 1.0), (F_WYJAZD0 + 25, 0.0)]
K_POD = 17.0     # kąt promienia z podziałką (lewa strona kadru)
for gl, et in ((0, "0 km"), (400, "400 km"), (600, "600 km")):
    p = ekran(na_przekroju(K_POD, 1 - gl / RZ), FZ)
    podpis("Gl_" + str(gl), et, p[0] - 22, p[1], 26, (255, 255, 255), kl_pod, wyr="RIGHT")
    linia_ekranu("Pk_" + str(gl), (p[0] - 12, p[1]), (p[0] + 12, p[1]), (255, 255, 255), kl_pod, 2.4)
p0 = ekran(na_przekroju(K_POD, 1.0), FZ)
p6 = ekran(na_przekroju(K_POD, R_600), FZ)
linia_ekranu("Podzialka", p0, p6, (255, 255, 255), kl_pod, 2.4)

pz = ekran(na_przekroju(0.0, R_POSL), FZ)
pz2 = ekran(na_przekroju(0.0, (1 + R_400) / 2), FZ)
pz3 = ekran(na_przekroju(0.0, 0.875), FZ)
print("[poslizg] zbliżenie: strefa px", pz, "skorupa px", pz2, "plaszcz px", pz3, "podzialka", p0, p6)
X_OP = max(pz[0], pz2[0], pz3[0]) + 30
podpis("Et_twarda", "twarda litosfera", X_OP, pz2[1], 30, (255, 255, 255), kl_pod)
podpis("Et_strefa", "strefa poślizgu 400–600 km", X_OP, pz[1] - 18, 30, (40, 26, 10), kl_pod, obrys=False)
podpis("Et_polplynny", "półpłynny płaszcz", X_OP, pz3[1], 30, (255, 255, 255), kl_pod)

# strzałka ruchu skorupy nad powierzchnią (skorupa przesuwa się w stronę malejącego kąta)
F_STRZ = 212
kl_s = [(1, 0.0), (F_STRZ, 0.0), (F_STRZ + 15, 1.0), (F_WYJAZD0 + 5, 1.0), (F_WYJAZD0 + 25, 0.0)]
sa = ekran(na_przekroju(13.0, 1.03), FZ)
sb = ekran(na_przekroju(4.0, 1.03), FZ)
linia_ekranu("Strz_trzon", sa, sb, G.ZLOTY, kl_s, 7.0)
d = Vector((sb[0] - sa[0], sb[1] - sa[1], 0)).normalized()
nn = Vector((-d.y, d.x, 0))
for k, znak in enumerate((1, -1)):
    linia_ekranu(f"Strz_grot{k}", (sb[0] + d.x * 3, sb[1] + d.y * 3),
                 (sb[0] - d.x * 30 + nn.x * 18 * znak, sb[1] - d.y * 30 + nn.y * 18 * znak), G.ZLOTY, kl_s, 7.0)
podpis("Et_ruch", "skorupa ślizga się po płaszczu", (sa[0] + sb[0]) / 2, min(sa[1], sb[1]) - 44, 30, G.ZLOTY, kl_s,
       wyr="CENTER")

ustaw(1)
G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
