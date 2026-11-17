# -*- coding: utf-8 -*-
"""Klip „tsunami-2004”: fala tsunami z 26 grudnia 2004 r. rozchodzi się po oceanie Indyjskim.

Spokojny schemat na globusie. Czoło fali i linie co godzinę pochodzą z modelu czasu przejścia policzonego na
prawdziwej batymetrii ETOPO1 (NOAA): prędkość fali długiej v = sqrt(g·h), najkrótszy czas po wodzie (algorytm
Dijkstry na siatce 5 minut kątowych), źródło wzdłuż strefy zerwania uskoku. Model nie jest do niczego dopasowywany;
z pomiarami mareografów NOAA zgadza się do ok. pół godziny. Punkty na wybrzeżach zapalają się w zmierzonych
czasach dotarcia fali (baza NOAA NCEI, domena publiczna) – szczegóły w README.md.

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
# Źródło fali: strefa zerwania uskoku (ok. 1300 km, od ogniska na północ do ok. 14°N; Lay i in., Science 308, 2005).
# Oś rowu oceanicznego z granic płyt PB2002 (P. Bird 2003; odcinki BU/AU, BU/IN, IN\BU, IN-BU), z południa na północ.
# Dno podniosło się między rowem a łukiem wysp, dlatego źródło leży 0,8° na wschód od osi rowu.
ROW = [(1.34, 96.2), (1.49, 96.09), (1.88, 95.54), (2.1, 94.98), (2.46, 94.41), (3.05, 93.75), (3.72, 93.23), (4.38, 92.9),
       (5.01, 92.67), (5.7, 92.54), (6.33, 92.38), (6.95, 92.28), (7.66, 91.9), (8.16, 91.78), (8.66, 91.65), (9.13, 91.6),
       (9.6, 91.53), (10.06, 91.56), (10.51, 91.58), (11.3, 91.59), (11.79, 91.64), (12.28, 91.7), (13.15, 91.89),
       (13.71, 92.07), (14.38, 92.52)]
ROW_PRZES = 0.8                # stopni na wschód od osi rowu
V_PEKANIA = 2.5 * 60           # km/min: zerwanie biegło na północ ok. 2,5 km/s (ok. 9 min na całą długość)

# ---------------------------------------------------------------- model czasu przejścia (prawdziwa batymetria)
BATYMETRIA = os.path.join(G.DANE, "etopo", "etopo1_ocean_indyjski_5min.npz")   # ETOPO1 (NOAA), co 5 minut kątowych
W_SW, H_SW = 2160, 1080        # tekstura czasu dla całej kuli: 10 minut kątowych na piksel


def model_fali():
    """Czas dojścia czoła fali [min] na siatce batymetrii (5 minut kątowych): prędkość fali długiej v = sqrt(g·h)
    z głębokości ETOPO1, najkrótszy czas po wodzie (algorytm Dijkstry, 16 kierunków). Bez żadnego dopasowywania."""
    cp = os.path.join(G.CACHE, "tsunami2004_T_etopo1_v1.npz")
    if os.path.exists(cp):
        z = np.load(cp)
        return z["T"], z["lats"], z["lons"]
    t0 = time.time()
    z = np.load(BATYMETRIA)
    wys = z["wys"].astype(np.float32)
    krok = float(z["krok"])
    ny, nx = wys.shape
    lats = float(z["szer0"]) + np.arange(ny) * krok
    lons = float(z["dlug0"]) + np.arange(nx) * krok
    woda = wys < 0
    iv = 1.0 / (np.sqrt(9.81 * np.maximum(-wys, 10.0)) * 0.06)          # min/km
    coslat = np.cos(np.radians(lats))
    KM = 111.19 * krok
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1),
          (-1, -2), (-1, 2), (1, -2), (1, 2), (-2, -1), (-2, 1), (2, -1), (2, 1)]
    zr = {}
    for (a1, o1), (a2, o2) in zip(ROW[:-1], ROW[1:]):
        for u in np.linspace(0, 1, 8, endpoint=False):
            la, lo = a1 + (a2 - a1) * u, o1 + (o2 - o1) * u + ROW_PRZES
            if not 2.0 <= la <= 14.0:
                continue
            j, i = int(round((la - lats[0]) / krok)), int(round((lo - lons[0]) / krok))
            d = math.hypot((la - EPI[0]) * 111.19, (lo - EPI[1]) * 111.19 * math.cos(math.radians(la)))
            for r in range(8):
                c = [(j + a, i + b) for a in range(-r, r + 1) for b in range(-r, r + 1) if woda[j + a, i + b]]
                if c:
                    zr[c[0]] = min(zr.get(c[0], 1e9), d / V_PEKANIA)
                    break
    T = np.full((ny, nx), np.inf)
    h = []
    for (j, i), t in zr.items():
        T[j, i] = t
        h.append((t, j, i))
    heapq.heapify(h)
    while h:
        d, j, i = heapq.heappop(h)
        if d > T[j, i]:
            continue
        for dj, di in nb:
            jj, ii = j + dj, i + di
            if 0 <= jj < ny and 0 <= ii < nx and woda[jj, ii]:
                nd = d + math.hypot(di * KM * (coslat[j] + coslat[jj]) / 2, dj * KM) * 0.5 * (iv[j, i] + iv[jj, ii])
                if nd < T[jj, ii]:
                    T[jj, ii] = nd
                    heapq.heappush(h, (nd, jj, ii))
    T = T.astype(np.float32)
    os.makedirs(G.CACHE, exist_ok=True)
    np.savez_compressed(cp, T=T, lats=lats, lons=lons)
    print(f"[tsunami] model fali {time.time()-t0:.0f} s, siatka {ny}x{nx}")
    return T, lats, lons


def czas_modelu(T, lats, lons, la, lo):
    """Czas modelu [min] w komórce wody najbliższej punktowi (do ok. 30 km)."""
    krok = lats[1] - lats[0]
    j, i = int(round((la - lats[0]) / krok)), int(round((lo - lons[0]) / krok))
    best, bd = float("inf"), 1e9
    for a in range(-3, 4):
        for b in range(-3, 4):
            if 0 <= j + a < T.shape[0] and 0 <= i + b < T.shape[1] and np.isfinite(T[j + a, i + b]) and a * a + b * b < bd:
                bd, best = a * a + b * b, float(T[j + a, i + b])
    return best


def pole_czasu():
    """Tekstura czasu dla całej kuli (wiersz 0 = północ, 10 minut kątowych na piksel), minuty; poza modelem 9999.
    W komórkach lądu wpisany czas najbliższej wody, żeby przy brzegu czoło fali nie urywało się (ląd zakrywa maska)."""
    T, lats, lons = model_fali()
    for nazwa, la, lo, mn, _ in STACJE:
        m = czas_modelu(T, lats, lons, la, lo)
        print(f"[tsunami] {nazwa:18s} pomiar {mn // 60}:{mn % 60:02d}  model {int(m) // 60}:{int(m) % 60:02d}  ({m - mn:+.0f} min)")
    ny, nx = (T.shape[0] - 1) // 2, (T.shape[1] - 1) // 2
    t4 = np.where(np.isfinite(T[:ny * 2, :nx * 2]), T[:ny * 2, :nx * 2], np.nan).reshape(ny, 2, nx, 2)
    with np.errstate(all="ignore"):
        import warnings
        warnings.simplefilter("ignore")
        t2 = np.nanmean(t4, axis=(1, 3))                       # 10 minut kątowych, wiersz 0 = południe
    for _ in range(6):                                         # wypełnij ląd czasem sąsiedniej wody
        brak = np.isnan(t2)
        if not brak.any():
            break
        p = np.pad(t2, 1, constant_values=np.nan)
        ss = np.stack([p[1 + a:1 + a + ny, 1 + b:1 + b + nx] for a in (-1, 0, 1) for b in (-1, 0, 1)])
        with np.errstate(all="ignore"):
            sr = np.nanmean(ss, axis=0)
        t2 = np.where(brak, sr, t2)
    full = np.full((H_SW, W_SW), 9999.0, np.float32)
    r_pd = int(round((90.0 - lats[0]) * 6.0))                  # wiersz tekstury dla południowej krawędzi siatki
    c0 = int(round((lons[0] + 180.0) * 6.0))
    blok = np.where(np.isnan(t2), 9999.0, t2)[::-1]            # wiersz 0 = północ
    full[r_pd - ny:r_pd, c0:c0 + nx] = blok
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
