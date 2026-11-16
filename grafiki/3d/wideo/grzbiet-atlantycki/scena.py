# -*- coding: utf-8 -*-
"""Klip „grzbiet-atlantycki”: Grzbiet Śródatlantycki jako „główny winowajca” (rozdział 03).

Fakt naukowy: dno Atlantyku rozsuwa się od grzbietu na zachód i wschód (nowe dno tworzy wypływająca magma),
a Pacyfik się kurczy. Hipoteza Leszka Klimka: to grzbiet jest głównym „rozpychającym się łokciami”
i główną przyczyną trzęsień Ziemi.

Przebieg: globus od strony Atlantyku -> rysuje się grzbiet (z północy na południe) -> świeci magma ->
pasy dna odsuwają się od grzbietu na obie strony, złote strzałki na zachód i wschód -> globus obraca się
na Pacyfik, strzałki przy jego brzegach wskazują, że ocean się zwęża.

Uruchomienie (z katalogu repozytorium):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/grzbiet-atlantycki/scena.py
  ... -- --proba 100,250,380,500
"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector, Quaternion
from bpy_extras.object_utils import world_to_camera_view

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
from wezly import Wezly, animuj_wartosc

OPCJE = G.argumenty()
KLATKI = 500  # 20 s

# Oś Grzbietu Śródatlantyckiego (przybliżona, z map batymetrycznych; szer., dł.) – z północy na południe
GRZBIET = [(72.0, -2.0), (70.5, -8.0), (68.0, -17.5), (66.5, -18.5), (64.0, -19.5), (63.0, -23.5), (60.0, -29.0),
           (57.0, -33.0), (54.0, -35.0), (52.6, -32.0), (50.0, -29.0), (45.0, -28.0), (40.0, -29.5), (37.5, -32.5),
           (35.0, -35.0), (30.0, -42.0), (25.0, -45.0), (20.0, -45.5), (15.0, -46.0), (12.0, -44.0), (10.0, -41.0),
           (7.5, -37.0), (4.5, -32.0), (1.5, -29.0), (0.5, -24.0), (-0.8, -16.0), (-3.0, -12.5), (-7.0, -12.5),
           (-11.0, -13.5), (-15.0, -14.0), (-20.0, -12.5), (-25.0, -13.5), (-30.0, -13.5), (-35.0, -16.5),
           (-40.0, -16.5), (-45.0, -13.5), (-50.0, -8.0), (-54.0, 1.0)]

F_GRZB0, F_GRZB1 = 25, 110       # rysowanie grzbietu
F_MAGMA = 95                     # świecenie magmy
F_DNO0, F_DNO1 = 130, 300        # rozsuwanie dna
F_OBR0, F_OBR1 = 300, 395        # obrót na Pacyfik
F_PAC = 385                      # strzałki Pacyfiku
WIDOK_ATL = (14.0, -32.0)
WIDOK_PAC = (8.0, -152.0)
ODL = 6.6


# ---------------------------------------------------------------- tekstury pomocnicze
def zageszczony():
    pts = []
    for (a1, o1), (a2, o2) in zip(GRZBIET[:-1], GRZBIET[1:]):
        n = max(2, int(G.odleglosc_katowa(a1, o1, a2, o2) / 0.25))
        pts += G.luk(a1, o1, a2, o2, n)[:-1]
    pts.append(G.ll2xyz(*GRZBIET[-1]))
    return pts


def mapy():
    cp = os.path.join(G.CACHE, "grzbiet_mapy_v2.npy")
    if os.path.exists(cp):
        return np.load(cp)
    Wt, Ht = 2048, 1024
    jj, ii = np.mgrid[0:Ht, 0:Wt]
    lon = (ii + 0.5) / Wt * 360 - 180
    lat = 90 - (jj + 0.5) / Ht * 180
    la, lo = np.radians(lat), np.radians(lon)
    P = np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1).reshape(-1, 3)
    R = np.array([tuple(v) for v in zageszczony()])
    best = np.full(len(P), -1.0)
    for k in range(0, len(R), 64):
        best = np.maximum(best, (P @ R[k:k + 64].T).max(axis=1))
    dist = np.degrees(np.arccos(np.clip(best, -1, 1))).reshape(Ht, Wt)
    # Atlantyk (bez Pacyfiku, Morza Śródziemnego, Bałtyku, Zatoki Hudsona i Oceanu Indyjskiego)
    m = G.zmniejsz(G.maska_ladu(4096, "50m"), 2)
    atl = (lon > -100) & (lon < 20) & (lat > -58) & (lat < 75) & (m < 0.5)
    atl &= ~((lat < 8.5) & (lon < -77.5))
    atl &= ~((lat < 16.3) & (lon < -83.5))
    atl &= ~(lon < -98)
    atl &= ~((lat < -40) & (lon < -66))
    atl &= ~((lon < -65) & (lat > 50))
    atl &= ~((lat < 46) & (lat > 30) & (lon > 0))
    atl &= ~((lat < 37) & (lat > 30) & (lon > -5.6))
    atl &= ~((lon > 10) & (lat > 53))
    atl &= ~((lat > 72))
    atl &= ~((lat < 18.5) & (lat > 8) & (lon < -61.5))      # Morze Karaibskie
    atl &= ~((lat > 18) & (lat < 31) & (lon < -81.5))       # Zatoka Meksykańska
    out = np.stack([dist.astype(np.float32), G.rozmyj(atl.astype(np.float32), 1)], -1)
    np.save(cp, out)
    return out


def obraz_float(nazwa, a2):
    h, w, _ = a2.shape
    im = bpy.data.images.new(nazwa, w, h, alpha=False, float_buffer=True)
    im.colorspace_settings.name = "Non-Color"
    rgba = np.zeros((h, w, 4), np.float32)
    rgba[..., 0] = a2[..., 0]
    rgba[..., 1] = a2[..., 1]
    rgba[..., 3] = 1
    im.pixels.foreach_set(np.ascontiguousarray(rgba[::-1]).ravel())
    im.pack()
    return im


# ---------------------------------------------------------------- scena
sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))
img_lad = G.wczytaj_obraz(G.tekstura_ziemi(8192, (255, 255, 255), (0, 0, 0), "maska_lad"), nieliniowy=False)
img_m = obraz_float("grzbiet_mapy", mapy())

glob = G.sfera_uv("Ziemia", 512, 256)
mat = bpy.data.materials.new("Ziemia")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
W = Wezly(nt)
uv = W.coord("UV")
lad = W.sep(W.obraz(img_lad, uv)[0])[0]
mc = W.obraz(img_m, uv)[0]
odl, atl, _ = W.sep(mc)                    # odległość od grzbietu (stopnie), maska Atlantyku
o = W.coord("Object")
nrm = W.norm(o)
kam = W.wartosc(0.0, "kam_x")   # nieużywane (zostawione dla czytelności drzewa)
morze_jasne = G.srgb((120, 200, 240))
kol = W.mix(lad, G.srgb(G.MORZE_USKOK), G.srgb(G.ZIELEN_USKOK))
# pasy dna: nowe dno rodzi się przy grzbiecie i odsuwa na obie strony
zasieg = W.wartosc(0.0, "zasieg")         # do ilu stopni od grzbietu widać pasy
przes = W.wartosc(0.0, "przesuniecie")    # przesunięcie pasów (stopnie)
OKRES = 4.0
faza = W.math("FRACT", W.div(W.sub(odl, przes), OKRES))
pas = W.mul(W.smooth(0.08, 0.16, faza), W.sub(1.0, W.smooth(0.50, 0.58, faza)))
widac = W.mul(W.mul(atl, W.sub(1.0, lad)), W.sub(1.0, W.smooth(W.sub(zasieg, 2.0), zasieg, odl)))
mlode = W.sub(1.0, W.smooth(0.0, 30.0, odl))     # młodsze dno przy grzbiecie jaśniejsze
kol_pas = W.mix(mlode, G.srgb((30, 120, 200)), G.srgb((150, 215, 245)))
kol = W.mix(W.mul(W.mul(pas, widac), 0.36), kol, kol_pas)
kol = W.mix(W.mul(widac, W.mul(mlode, 0.18)), kol, G.srgb((190, 232, 252)))
# magma: pomarańczowa poświata przy osi grzbietu (pulsuje)
a_mag = W.wartosc(0.0, "magma")
pul = W.wartosc(1.0, "puls")
mag = W.mul(W.sub(1.0, W.smooth(0.0, 1.6, odl)), W.mul(a_mag, pul))
mag = W.mul(mag, W.sub(1.0, W.mul(lad, 0.6)))
kol = W.mix(mag, kol, G.srgb((255, 120, 30)))
# cieniowanie kuli
sw = W.dot(nrm, tuple(Vector((-0.3, -0.6, 0.75)).normalized()))
cien = W.add(0.80, W.mul(W.mx(sw, 0.0), 0.22))
kol = W.vmath("MULTIPLY", kol, W.vec(cien, cien, cien))
W.emisja_wyjscie(kol)
glob.data.materials.append(mat)

animuj_wartosc(nt, "magma", [(F_MAGMA, 0.0), (F_MAGMA + 35, 1.0)])
animuj_wartosc(nt, "zasieg", [(F_DNO0, 0.0), (F_DNO1, 40.0)])
animuj_wartosc(nt, "przesuniecie", [(F_DNO0, 0.0), (KLATKI, 4.0 * 3.0)], interp="LINEAR")
animuj_wartosc(nt, "puls", [(f, 0.85 + 0.15 * math.sin(f / 9.0)) for f in range(1, KLATKI + 1, 6)])

# grzbiet: krzywa na kuli rysowana z północy na południe
cu = bpy.data.curves.new("Grzbiet", "CURVE")
cu.dimensions = "3D"
cu.bevel_depth = 0.0042
cu.bevel_resolution = 2
pts = zageszczony()
sp = cu.splines.new("POLY")
sp.points.add(len(pts) - 1)
for p, v in zip(sp.points, pts):
    q = v * 1.002
    p.co = (q.x, q.y, q.z, 1)
grz = bpy.data.objects.new("Grzbiet", cu)
sc.collection.objects.link(grz)
mg = G.material_emisja("Grzbiet_mat", (255, 205, 120))
cu.materials.append(mg)
cu.bevel_factor_end = 0.0
cu.keyframe_insert("bevel_factor_end", frame=F_GRZB0)
cu.bevel_factor_end = 1.0
cu.keyframe_insert("bevel_factor_end", frame=F_GRZB1)
G.wygladz(cu)

# poświata
bpy.ops.mesh.primitive_circle_add(vertices=128, radius=1.14, fill_type="TRIFAN")
pos = bpy.context.active_object
pos.name = "Poswiata"
mp = bpy.data.materials.new("Poswiata")
mp.use_nodes = True
mp.node_tree.nodes.clear()
W2 = Wezly(mp.node_tree)
r2 = W2.vmath("LENGTH", W2.coord("Object"))
W2.emisja_wyjscie(G.srgb((70, 150, 230)), W2.mul(W2.sub(1.0, W2.smooth(0.98, 1.14, r2)), 0.55))
mp.surface_render_method = "BLENDED"
pos.data.materials.append(mp)


# ---------------------------------------------------------------- kamera
def kier_kamery(lat, lon):
    return G.ll2xyz(lat, lon)


cam = G.kamera(kier_kamery(*WIDOK_ATL) * ODL, (0, 0, 0), lens=50)
con = pos.constraints.new("TRACK_TO")
con.target = cam
con.track_axis = "TRACK_Z"
con.up_axis = "UP_Y"
PRZES_W_GORE = 0.245   # globus nieco wyżej (dół 200 px na podpis)


def ustaw_kamere(f):
    s = G.gladko5((f - F_OBR0) / (F_OBR1 - F_OBR0))
    lat = WIDOK_ATL[0] + (WIDOK_PAC[0] - WIDOK_ATL[0]) * s
    lon = WIDOK_ATL[1] + (WIDOK_PAC[1] - WIDOK_ATL[1]) * s
    k = kier_kamery(lat, lon)
    d = ODL + 0.35 * math.sin(math.pi * s)        # lekkie oddalenie w trakcie obrotu
    g = (Vector((0, 0, 1)) - k * k.z).normalized()
    cam.location = k * d
    G.patrz(cam, -g * PRZES_W_GORE)


for f in [1, F_OBR0] + list(range(F_OBR0 + 5, F_OBR1, 5)) + [F_OBR1, KLATKI]:
    ustaw_kamere(f)
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
G.wygladz(cam)
G.tlo_kamery(cam, odl=30)


def ekran(punkt, f):
    """piksele (x, y od góry) punktu świata przy kamerze z klatki f"""
    ustaw_kamere(f)
    bpy.context.view_layer.update()
    v = world_to_camera_view(sc, cam, Vector(punkt))
    return v.x * 1920, (1 - v.y) * 1080


# ---------------------------------------------------------------- strzałki na kuli
def strzalka_mesh(nazwa, dl, szer, kolor):
    """płaska strzałka wzdłuż +X (od 0 do dl), w płaszczyźnie XY"""
    g = szer * 1.9
    gd = dl * 0.36
    v = [(0, -szer / 2, 0), (dl - gd, -szer / 2, 0), (dl - gd, -g / 2, 0), (dl, 0, 0), (dl - gd, g / 2, 0),
         (dl - gd, szer / 2, 0), (0, szer / 2, 0)]
    f = [(0, 1, 5, 6), (2, 3, 4)]
    me = bpy.data.meshes.new(nazwa)
    me.from_pydata(v, [], f)
    ob = bpy.data.objects.new(nazwa, me)
    sc.collection.objects.link(ob)
    m = G.material_emisja(nazwa + "_mat", kolor)
    me.materials.append(m)
    ob["mat"] = m.name
    return ob


def ustaw_na_kuli(ob, p, kier, r=1.006):
    """obiekt płaski (oś X = kierunek strzałki) stycznie do kuli w punkcie p"""
    n = p.normalized()
    x = (kier - n * kier.dot(n)).normalized()
    y = n.cross(x)
    from mathutils import Matrix
    M = Matrix((x, y, n)).transposed()
    ob.rotation_euler = M.to_euler()
    ob.location = n * r


def przesun_po_kole(p, kier, kat):
    """punkt p przesunięty o kąt (rad) po kole wielkim w kierunku kier"""
    n = p.normalized()
    t = (kier - n * kier.dot(n)).normalized()
    return (n * math.cos(kat) + t * math.sin(kat)).normalized(), (t * math.cos(kat) - n * math.sin(kat)).normalized()


pts = zageszczony()
ZLOTY = G.ZLOTY
for i_lat, lat0 in enumerate((46.0, 25.0, 5.5, -16.0, -36.0)):
    # punkt grzbietu na danej szerokości; dno odsuwa się mniej więcej wzdłuż równoleżników (na zachód i wschód)
    k = min(range(1, len(pts) - 1), key=lambda i: abs(G.xyz2ll(pts[i])[0] - lat0))
    p = pts[k]
    wschod = Vector((0, 0, 1)).cross(p).normalized()
    for strona, znak in (("E", 1.0), ("W", -1.0)):
        kier0 = wschod * znak
        f0 = F_DNO0 + 20 + i_lat * 8
        ob = strzalka_mesh(f"Strz_{i_lat}_{strona}", 0.15, 0.04, ZLOTY)
        # przesuwa się od 2,5° do 7° od grzbietu
        for f, kat in ((f0, 2.8), (F_DNO1 + 20, 8.0)):
            q, t = przesun_po_kole(p, kier0, math.radians(kat))
            ustaw_na_kuli(ob, q, t)
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("rotation_euler", frame=f)
        G.wygladz(ob)
        G.animuj_alfa(bpy.data.materials[ob["mat"]], [(1, 0.0), (f0, 0.0), (f0 + 15, 1.0), (F_OBR0 + 25, 1.0),
                                                      (F_OBR0 + 50, 0.0)])

# Pacyfik: przy brzegach strzałki do środka oceanu (ocean się zwęża)
PAC = [((-14.0, -96.0), -1), ((4.0, -102.0), -1), ((22.0, -122.0), -1), ((42.0, -138.0), -1),
       ((40.0, 156.0), 1), ((20.0, 140.0), 1), ((2.0, 143.0), 1), ((-22.0, 170.0), 1)]
for i, ((la, lo), znak) in enumerate(PAC):
    p = G.ll2xyz(la, lo)
    wsch = Vector((0, 0, 1)).cross(p).normalized()
    kier0 = wsch * znak
    f0 = F_PAC + i * 5
    ob = strzalka_mesh(f"StrzP_{i}", 0.18, 0.048, ZLOTY)
    for f, kat in ((f0, 0.0), (KLATKI, 5.0)):
        q, t = przesun_po_kole(p, kier0, math.radians(kat))
        ustaw_na_kuli(ob, q, t)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
    G.wygladz(ob)
    G.animuj_alfa(bpy.data.materials[ob["mat"]], [(1, 0.0), (f0, 0.0), (f0 + 15, 1.0)])

# ---------------------------------------------------------------- napisy (przypięte do kamery)
ODL_N = 2.0
px_u = G.skala_px(cam, ODL_N)


def podpis(nazwa, tekst, x, y, rozm, kolor, klucze, wyr="LEFT", kroj="arialb"):
    ob = G.napis(tekst, rozm * 1.4 * px_u, kolor, kroj, wyr, rodzic=cam, loc=G.ekran_na_kamerze(cam, x, y, ODL_N),
                 nazwa=nazwa, obrys=((8, 20, 45), 0.0012), odstep=1.08)
    G.alfa_napisu(ob, klucze)
    return ob


px_grz = ekran(G.ll2xyz(40.0, -29.5), 60)
px_pac = ekran(G.ll2xyz(4.0, -152.0), KLATKI)
px_mag = ekran(G.ll2xyz(-10.0, -13.5), 140)
print("[grzbiet] grzbiet px", px_grz, "magma px", px_mag)
wyg_atl = (F_OBR0 - 5, 1.0), (F_OBR0 + 25, 0.0)
podpis("Et_grzbiet", "Grzbiet Śródatlantycki", px_grz[0] - 40, px_grz[1] + 10, 34, (255, 255, 255),
       [(1, 0.0), (F_GRZB0 + 40, 0.0), (F_GRZB0 + 60, 1.0), *wyg_atl], wyr="RIGHT")
podpis("Et_magma", "wypływ magmy\nz wnętrza Ziemi", px_mag[0] + 30, px_mag[1], 28, (255, 214, 160),
       [(1, 0.0), (F_MAGMA + 20, 0.0), (F_MAGMA + 40, 1.0), *wyg_atl])
podpis("Et_atl", "Atlantyk rozszerza się\nna zachód i wschód", 1560, 250, 34, G.ZLOTY,
       [(1, 0.0), (F_DNO0 + 40, 0.0), (F_DNO0 + 62, 1.0), *wyg_atl], wyr="CENTER")
podpis("Et_pac", "Pacyfik kurczy się", px_pac[0], px_pac[1], 38, G.ZLOTY,
       [(1, 0.0), (F_PAC + 25, 0.0), (F_PAC + 45, 1.0)], wyr="CENTER")

ustaw_kamere(1)
G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
