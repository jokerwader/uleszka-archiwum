# -*- coding: utf-8 -*-
"""Klip „tsunami-2004”: fala tsunami z 26 grudnia 2004 r. rozchodzi się po oceanie Indyjskim.

Spokojny schemat na globusie. Czoło fali i linie co godzinę pochodzą z prostego modelu czasu przejścia
(prędkość fali na płytkiej wodzie v = sqrt(g·h), głębokość szacowana z odległości od brzegu, droga tylko
po wodzie – algorytm Dijkstry na siatce 0,25°). Model dopasowano do pomiarów mareografów z bazy NOAA NCEI
(średni błąd ok. 30 min). Punkty na wybrzeżach zapalają się w zmierzonych czasach dotarcia fali
(baza NOAA NCEI, domena publiczna) – szczegóły w README.md.

Uruchomienie (z katalogu repozytorium):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/tsunami-2004/scena.py
  ... -- --proba 60,200,420,500
"""
import bpy, math, os, sys, heapq, time
import numpy as np
from mathutils import Vector

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
from wezly import Wezly, animuj_wartosc

OPCJE = G.argumenty()
KLATKI = 500            # 20 s
T_KONIEC = 12.5 * 60    # minut po trzęsieniu na końcu animacji
F_START, F_STOP = 55, 440

# ---------------------------------------------------------------- dane NOAA (mareografy, czas od 00:58:53 UTC)
# Źródło: NOAA NCEI Global Historical Tsunami Database, zdarzenie 2439, pola travHours/travMins.
STACJE = [  # nazwa w filmie, szer., dł., minut, przesunięcie podpisu (px: x, y)
    ("Phuket", 7.83, 98.42, 116, (18, -2)),
    ("Ćennaj", 13.083, 80.30, 154, (-18, 0)),
    ("Kolombo", 6.948, 79.853, 170, (16, 14)),
    ("Male", 4.18, 73.52, 195, (-16, 14)),
    ("Perth (Hillarys)", -31.82, 115.73, 383, (-18, 0)),
    ("Port Louis", -20.157, 57.504, 407, (-18, 0)),
    ("Salala", 16.941, 54.008, 429, (-18, 0)),
    ("Lamu", -2.282, 40.909, 533, (18, 0)),
    ("Port Elizabeth", -33.967, 25.633, 733, (18, 0)),
]
EPI = (3.295, 95.982)   # ognisko (NOAA NCEI)
# pas zerwania uskoku (ok. 1300 km wzdłuż rowu Sundajskiego i Andamanów) – źródło fali
RUP = [(3.3 + k * (14.0 - 3.3) / 30, 95.9 + k * (92.9 - 95.9) / 30) for k in range(31)]

# ---------------------------------------------------------------- model czasu przejścia
RES = 0.25
LON0, LON1, LAT0, LAT1 = 15.0, 160.0, -75.0, 32.0


def pole_czasu():
    cp = os.path.join(G.CACHE, "tsunami2004_T.npy")
    if os.path.exists(cp):
        return np.load(cp)
    t0 = time.time()
    m = G.maska_ladu(1440, "50m")
    c0, c1 = int((LON0 + 180) / RES), int((LON1 + 180) / RES)
    r0, r1 = int((90 - LAT1) / RES), int((90 - LAT0) / RES)
    land = m[r0:r1, c0:c1] > 0.5
    ny, nx = land.shape
    lats = LAT1 - (np.arange(ny) + 0.5) * RES
    lons = LON0 + (np.arange(nx) + 0.5) * RES
    KM = 111.2 * RES
    coslat = np.cos(np.radians(lats))
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1),
          (-1, -2), (-1, 2), (1, -2), (1, 2), (-2, -1), (-2, 1), (2, -1), (2, 1)]

    def krok(j, i, jj, ii):
        return math.hypot((ii - i) * KM * (coslat[j] + coslat[jj]) / 2, (jj - j) * KM)

    def dijkstra(zrodla, wolne, koszt):
        dist = np.full((ny, nx), np.inf)
        h = []
        for j, i in zrodla:
            dist[j, i] = 0.0
            h.append((0.0, j, i))
        heapq.heapify(h)
        while h:
            d, j, i = heapq.heappop(h)
            if d > dist[j, i]:
                continue
            for dj, di in nb:
                jj, ii = j + dj, i + di
                if 0 <= jj < ny and 0 <= ii < nx and wolne[jj, ii]:
                    nd = d + koszt(j, i, jj, ii)
                    if nd < dist[jj, ii]:
                        dist[jj, ii] = nd
                        heapq.heappush(h, (nd, jj, ii))
        return dist

    # odległość od brzegu (km)
    wsz = np.ones_like(land)
    dbrzeg = dijkstra(list(zip(*np.nonzero(land))), wsz, krok)
    # głębokość: szelf 50 m przy brzegu, 4000 m od ok. 230 km; płytsze Morze Andamańskie i Zatoka Bengalska
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    cap = np.full((ny, nx), 4000.0)
    cap[(LA > 5) & (LA < 16) & (LO > 93.0) & (LO < 99.5)] = 700.0
    cap[(LA > 7) & (LO > 79) & (LO < 92.5)] = 2300.0
    h = np.minimum(50.0 + 3950.0 * np.clip((dbrzeg - 30.0) / 200.0, 0, 1), cap)
    v = np.sqrt(9.81 * h) * 3.6 / 60.0  # km/min
    woda = ~land

    def koszt(j, i, jj, ii):
        return krok(j, i, jj, ii) * 0.5 * (1 / v[j, i] + 1 / v[jj, ii])

    zr = []
    for la, lo in RUP:
        j, i = int((LAT1 - la) / RES), int((lo - LON0) / RES)
        for r in range(12):
            c = [(j + a, i + b) for a in range(-r, r + 1) for b in range(-r, r + 1) if woda[j + a, i + b]]
            if c:
                zr.append(c[0])
                break
    T = dijkstra(zr, woda, koszt)
    # do pełnej mapy świata (1440×720); ląd i obszar poza modelem = 9999
    full = np.full(m.shape, 9999.0, np.float32)
    Tm = np.where(np.isfinite(T), T, 9999.0)
    full[r0:r1, c0:c1] = Tm
    np.save(cp, full)
    print(f"[tsunami] pole czasu {time.time()-t0:.0f} s")
    return full


def obraz_float(nazwa, a):
    """H×W (wiersz 0 = północ) -> obraz float Blendera (spakowany, bez pliku)."""
    h, w = a.shape
    im = bpy.data.images.new(nazwa, w, h, alpha=False, float_buffer=True)
    im.colorspace_settings.name = "Non-Color"
    rgba = np.zeros((h, w, 4), np.float32)
    rgba[..., 0] = a
    rgba[..., 3] = 1
    im.pixels.foreach_set(np.ascontiguousarray(rgba[::-1]).ravel())
    im.pack()
    return im


# ---------------------------------------------------------------- scena
sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))
T = pole_czasu()
img_T = obraz_float("czas", T / 60.0)  # godziny
img_lad = G.wczytaj_obraz(G.tekstura_ziemi(8192, (255, 255, 255), (0, 0, 0), "maska_lad"), nieliniowy=False)

glob = G.sfera_uv("Ziemia", 512, 256)
mat = bpy.data.materials.new("Ziemia")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
W = Wezly(nt)
uv = W.coord("UV")
lad = W.sep(W.obraz(img_lad, uv)[0])[0]
th = W.sep(W.obraz(img_T, uv, interp="Linear", ext="EXTEND")[0])[0]   # godziny
t = W.wartosc(0.0, "czas_h")
o = W.coord("Object")
nrm = W.norm(o)
# morze i ląd w kolorach rysunków Leszka (jak uskok-globus), morze jaśniejsze w środku widoku
WIDOK = G.ll2xyz(-8.0, 80.0)
kat_w = W.dot(nrm, tuple(WIDOK))
morze = W.mix(W.smooth(0.55, 1.0, kat_w), G.srgb(G.MORZE_USKOK), G.srgb((120, 200, 240)))
kol = W.mix(lad, morze, G.srgb(G.ZIELEN_USKOK))
# obszar, do którego fala już dotarła: lekko jaśniejszy
dotarla = W.mul(W.sub(1.0, W.smooth(-0.02, 0.0, W.sub(th, t))), W.sub(1.0, lad))
kol = W.mix(W.mul(dotarla, 0.22), kol, G.srgb((205, 238, 255)))
# linie co godzinę (tylko te, które fala już minęła)
fr = W.math("FRACT", W.add(th, 0.5))
iso = W.linia(W.sub(fr, 0.5), 0.022, 0.012)
iso = W.mul(W.mul(iso, dotarla), W.smooth(0.3, 1.0, W.sub(t, th)))
kol = W.mix(W.mul(iso, 0.55), kol, G.srgb((25, 70, 140)))
# czoło fali: jasny pas za frontem
za = W.sub(t, th)  # ile godzin temu przeszła fala
front = W.mul(W.smooth(-0.015, 0.0, za), W.sub(1.0, W.smooth(0.0, 0.22, za)))
front = W.mul(W.mul(front, W.sub(1.0, lad)), W.wartosc(1.0, "alfa_frontu"))
kol = W.mix(W.mul(front, 0.95), kol, G.srgb((255, 255, 255)))
# ognisko: czerwona kropka
kk = W.math("ARCCOSINE", W.math("MINIMUM", W.dot(nrm, tuple(G.ll2xyz(*EPI))), 1.0))
ep = W.sub(1.0, W.smooth(0.010, 0.013, kk))
kol = W.mix(ep, kol, G.srgb((215, 30, 25)))
# cieniowanie kuli i jaśniejszy brzeg (jak uskok-globus)
sw = W.dot(nrm, tuple((WIDOK + Vector((0, 0, 0.6))).normalized()))
cien = W.add(0.78, W.mul(W.mx(sw, 0.0), 0.24))
kol = W.vmath("MULTIPLY", kol, W.vec(cien, cien, cien))
W.emisja_wyjscie(kol)
glob.data.materials.append(mat)

# kamera: patrzy na ocean Indyjski, powoli się oddala
K0, K1 = G.ll2xyz(1.0, 89.0), G.ll2xyz(-9.0, 72.0)
D0, D1 = 4.6, 7.0
cam = G.kamera(K1 * D1, (0, 0, 0), lens=50)


def ustaw_kamere(f):
    s = G.gladko5((f - 15) / (F_STOP - 15.0))
    k = K0.slerp(K1, s) if hasattr(K0, "slerp") else K0.lerp(K1, s).normalized()
    k = k.normalized()
    d = D0 + (D1 - D0) * s
    cam.location = k * d
    gora = (Vector((0, 0, 1)) - k * k.z).normalized()
    # globus nieco powyżej środka kadru (dół 200 px na podpis): patrz trochę poniżej środka kuli
    G.patrz(cam, -gora * 0.037 * d)


for f in list(range(1, F_STOP + 1, 20)) + [F_STOP]:
    ustaw_kamere(f)
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
G.wygladz(cam)
ustaw_kamere(F_STOP)
KIER = K1
G.tlo_kamery(cam, odl=30)

# poświata wokół globusa (dysk za kulą, zwrócony do kamery)
bpy.ops.mesh.primitive_circle_add(vertices=128, radius=1.14, fill_type="TRIFAN")
pos = bpy.context.active_object
pos.name = "Poswiata"
con = pos.constraints.new("TRACK_TO")
con.target = cam
con.track_axis = "TRACK_Z"
con.up_axis = "UP_Y"
mp = bpy.data.materials.new("Poswiata")
mp.use_nodes = True
mp.node_tree.nodes.clear()
W2 = Wezly(mp.node_tree)
r2 = W2.vmath("LENGTH", W2.coord("Object"))
W2.emisja_wyjscie(G.srgb((70, 150, 230)), W2.mul(W2.sub(1.0, W2.smooth(0.98, 1.14, r2)), 0.55))
mp.surface_render_method = "BLENDED"
pos.data.materials.append(mp)

# czas w modelu: przyspiesza łagodnie (pierwsze godziny wolniej)
def czas_min(f):
    s = max(0.0, min(1.0, (f - F_START) / (F_STOP - F_START)))
    s = G.gladko(s) * 0.25 + s * 0.75
    return T_KONIEC * s ** 1.45


klucze = [(f, czas_min(f) / 60.0) for f in range(1, KLATKI + 1, 5)]
animuj_wartosc(nt, "czas_h", klucze, interp="LINEAR")

# ---------------------------------------------------------------- napisy
# orientacja kamery w końcowym ujęciu (podpisy zwrócone do niej)
_g = (Vector((0, 0, 1)) - K1 * K1.z).normalized()
KAM_KON = K1 * D1
rot_cam = (-_g * 0.037 * D1 - KAM_KON).to_track_quat("-Z", "Y")
ROT_E = rot_cam.to_euler()
DO_KAM = (rot_cam @ Vector((0, 0, 1))).normalized()
PRAWO = rot_cam @ Vector((1, 0, 0))
GORA = rot_cam @ Vector((0, 1, 0))


def podpis_na_kuli(nazwa, tekst, lat, lon, dx, dy, rozm_px=30, kolor=(255, 255, 255), wyr=None, krój="arialb"):
    p = G.ll2xyz(lat, lon, 1.0) + DO_KAM * 0.35   # przed kulą, żeby jej nie przecinał
    s = (p - KAM_KON).length * cam.data.sensor_width / cam.data.lens / 1920  # jednostki sceny na piksel
    loc = p + PRAWO * dx * s + GORA * (-dy) * s
    if wyr is None:
        wyr = "LEFT" if dx >= 0 else "RIGHT"
    ob = G.napis(tekst, rozm_px * s, kolor, krój, wyr, loc=loc, nazwa=nazwa, obrys=((10, 25, 50), 0.0025))
    ob.rotation_euler = ROT_E
    return ob


def kropka(nazwa, lat, lon, kolor, r=0.011):
    bpy.ops.mesh.primitive_circle_add(vertices=32, radius=r, fill_type="TRIFAN")
    k = bpy.context.active_object
    k.name = nazwa
    n = G.ll2xyz(lat, lon)
    k.location = n * 1.004
    k.rotation_euler = n.to_track_quat("Z", "Y").to_euler()
    m = G.material_emisja(nazwa + "_mat", kolor)
    k.data.materials.append(m)
    k["mat"] = m.name
    # biała obwódka
    bpy.ops.mesh.primitive_circle_add(vertices=32, radius=r * 1.45, fill_type="TRIFAN")
    o2 = bpy.context.active_object
    o2.name = nazwa + "_obw"
    o2.location = n * 1.003
    o2.rotation_euler = k.rotation_euler
    m2 = G.material_emisja(nazwa + "_obw_mat", (255, 255, 255))
    o2.data.materials.append(m2)
    o2["mat"] = m2.name
    return [k, o2]


def klatka_dla_czasu(minuty):
    for f in range(1, KLATKI + 1):
        if czas_min(f) >= minuty:
            return f
    return KLATKI


# ognisko
ep_nap = podpis_na_kuli("Et_ognisko", "Ognisko trzęsienia\n26.12.2004, 00:58 UTC", EPI[0], EPI[1], 22, 34,
                        rozm_px=30, kolor=G.ZLOTY)
G.alfa_napisu(ep_nap, [(1, 0.0), (10, 0.0), (35, 1.0), (F_START + 60, 1.0), (F_START + 90, 0.0)])

for nazwa, la, lo, mins, (dx, dy) in STACJE:
    f0 = klatka_dla_czasu(mins)
    obs = kropka("K_" + nazwa, la, lo, G.ZLOTY)
    for ob in obs:
        G.animuj_alfa(bpy.data.materials[ob["mat"]], [(1, 0.0), (f0 - 1, 0.0), (f0 + 8, 1.0)])
    h, m = divmod(mins, 60)
    et = podpis_na_kuli("Et_" + nazwa, f"{nazwa}  {h}:{m:02d}", la, lo, dx, dy, rozm_px=28)
    G.alfa_napisu(et, [(1, 0.0), (f0 - 1, 0.0), (f0 + 12, 1.0)])

# zegar w prawym górnym rogu (przypięty do kamery)
ODL_Z = 4.0
zeg = G.napis("+0 h 00 min", 0.13, (255, 255, 255), "arialb", "RIGHT", rodzic=cam,
              loc=G.ekran_na_kamerze(cam, 1840, 88, ODL_Z) + Vector((0, 0.0, 0)), nazwa="Zegar")
zeg.data.size = G.skala_px(cam, ODL_Z) * 58
zeg2 = G.napis("od trzęsienia ziemi", 0.05, G.ZLOTY, "arial", "RIGHT", rodzic=cam,
               loc=G.ekran_na_kamerze(cam, 1840, 142, ODL_Z), nazwa="Zegar_opis")
zeg2.data.size = G.skala_px(cam, ODL_Z) * 30
leg = G.napis("Punkty: zmierzony czas dotarcia fali (mareografy, NOAA)\nLinie: co godzinę (model)", 0.05,
              (200, 220, 240), "arial", "RIGHT", rodzic=cam, loc=G.ekran_na_kamerze(cam, 1840, 830, ODL_Z),
              nazwa="Legenda")
leg.data.size = G.skala_px(cam, ODL_Z) * 24
for ob in (zeg, zeg2, leg):
    G.alfa_napisu(ob, [(1, 0.0), (F_START - 25, 0.0), (F_START, 1.0)])


def aktualizuj_zegar(scena, *a):
    mins = int(round(czas_min(scena.frame_current)))
    h, m = divmod(mins, 60)
    zeg.data.body = f"+{h} h {m:02d} min"


bpy.app.handlers.frame_change_pre.append(aktualizuj_zegar)

G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
