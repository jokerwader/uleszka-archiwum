# -*- coding: utf-8 -*-
"""Klip „odchylenie-17-globus”: ożywiony rysunek Leszka Klimka 17std3.jpg (rozdz. „Siedemnaście stopni Daenikena”).

Treść rysunku: globus (jasnoniebieskie morze, zielone lądy), zielony południk „70” przez Titicaca, Akpatok i biegun,
czarne punkty „Akpatok” (biegun poprzedni) i „Pn” (biegun dzisiejszy), gruba czerwona strzałka od Akpatok do Pn,
żółte kwadraty „Jukatan” i „Egipt”, od każdego żółta linia przerywana do Akpatok (dawna północ) i ciągła do Pn
(dzisiejsza północ), małe czerwone strzałki kąta i podpisy „Odchylenie od północy na północny wschód / zachód”.

Kolejność: południk 70 i Akpatok -> kwadraty i linie przerywane -> czerwona strzałka do Pn -> linie ciągłe ->
czerwone strzałki kąta i podpisy. Kamera przesuwa się znad Ameryki nad Atlantyk (jak na rysunku) i staje.

Uruchomienie: S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/odchylenie-17-globus/scena.py
              ... -- --proba 1,120,250,400
"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
import schemat as S
from wezly import Wezly

OPCJE = G.argumenty()
KLATKI = 400  # 16 s

# kolory próbkowane z 17std3.jpg
MORZE = (117, 195, 243)
LAD = (128, 195, 38)
ZIELONA = (16, 142, 78)       # południk 70
ZOLTA = (255, 240, 0)         # linie do biegunów
ZOLTY_KWADRAT = (226, 236, 70)
CZERWONA = (232, 26, 30)
FIOLET = (190, 110, 140)      # wypełnienie czerwonej strzałki
CZARNY = (16, 16, 20)
GRANAT_TXT = (14, 18, 40)
NIEBIESKI = (8, 137, 255)     # punkt Titicaca

AKPATOK = (60.0, -70.0)       # biegun poprzedni według Leszka (tabela w rozdz. „Co wyszło z obliczeń?”)
JUKATAN = (19.5, -89.5)
EGIPT = (27.5, 31.0)
TITICACA = (-15.8, -69.4)
KONIEC_WIDOKU = (37.0, -43.0)     # środek widoku jak na rysunku
START_WIDOKU = (24.0, -92.0)
R_PX, CX, CY = 436.0, 960.0, 452.0

sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))

# ---------------------------------------------------------------- globus
glob = G.sfera_uv("Globus", 512, 256)
img = G.wczytaj_obraz(G.tekstura_ziemi(8192, LAD, MORZE, "ziemia_17std3"))
mat = bpy.data.materials.new("Globus")
mat.use_nodes = True
mat.node_tree.nodes.clear()
W = Wezly(mat.node_tree)
kol, _ = W.obraz(img, W.coord("UV"))
nrm = W.geometria("Normal")
sw = W.dot(nrm, tuple(G.ll2xyz(55, -95).normalized()))
cien = W.add(0.70, W.mul(W.mx(sw, 0.0), 0.36))
kol = W.vmath("MULTIPLY", kol, W.vec(cien, cien, cien))
fres = W.math("POWER", W.sub(1.0, W.math("ABSOLUTE", W.dot(nrm, W.geometria("Incoming")))), 2.5)
kol = W.mix(W.mul(fres, 0.45), kol, G.srgb((190, 230, 255)))
W.emisja_wyjscie(kol)
glob.data.materials.append(mat)

# kamera ortograficzna: jedzie po łuku od widoku na Amerykę do widoku z rysunku i staje (klatka 215)
orto = 1920 / R_PX
cam = G.kamera((12, 0, 0), (0, 0, 0), orto=orto)
cam.data.shift_y = -(540 - CY) / 1920
F_STOP = 215


def tor(f):
    t = S.rampa(f, 70, F_STOP)
    return (START_WIDOKU[1] + (KONIEC_WIDOKU[1] - START_WIDOKU[1]) * t,
            START_WIDOKU[0] + (KONIEC_WIDOKU[0] - START_WIDOKU[0]) * t, 12.0)


S.orbita_f(cam, (0, 0, 0), tor, KLATKI, krok=5)
G.tlo_kamery(cam, odl=20)

# poświata wokół globusa (zwrócona do kamery)
bpy.ops.mesh.primitive_circle_add(vertices=128, radius=1.10, fill_type="TRIFAN", location=(0, 0, 0))
pos = bpy.context.active_object
pos.parent = cam
pos.location = (0, 0, -12.6)
mp = bpy.data.materials.new("Poswiata")
mp.use_nodes = True
mp.node_tree.nodes.clear()
W2 = Wezly(mp.node_tree)
r2 = W2.vmath("LENGTH", W2.coord("Object"))
W2.emisja_wyjscie(G.srgb((60, 140, 225)), W2.mul(W2.sub(1.0, W2.smooth(0.9, 1.10, r2)), 0.5))
mp.surface_render_method = "BLENDED"
pos.data.materials.append(mp)

# układ ekranu dla końcowego położenia kamery (podpisy pojawiają się głównie po zatrzymaniu)
KU_KAM = G.ll2xyz(*KONIEC_WIDOKU).normalized()
PRAWO = Vector((0, 0, 1)).cross(KU_KAM).normalized()
GORA = KU_KAM.cross(PRAWO).normalized()


def na_ekran(v):
    return CX + v.dot(PRAWO) * R_PX, CY - v.dot(GORA) * R_PX


def z_ekranu(px, py, wys=1.35):
    return PRAWO * ((px - CX) / R_PX) + GORA * (-(py - CY) / R_PX) + KU_KAM * wys


# ---------------------------------------------------------------- rysowanie na kuli
def uklad(lat, lon, az):
    """Lokalny układ w punkcie kuli: P, oś „w przód” o azymucie az (stopnie od północy), oś „w prawo”."""
    P = G.ll2xyz(lat, lon)
    Nn = (Vector((0, 0, 1)) - P * P.z)
    Nn = Nn.normalized() if Nn.length > 1e-6 else Vector((-1, 0, 0))
    Ee = Nn.cross(P).normalized()
    a = math.radians(az)
    przod = Nn * math.cos(a) + Ee * math.sin(a)
    prawo = przod.cross(P).normalized()
    return P, przod, prawo


def pkt(ukl, x, y, r=1.0):
    """Punkt kuli odległy od P o (x w prawo, y w przód) stopni."""
    P, przod, prawo = ukl
    d = prawo * x + przod * y
    rho = math.radians(d.length)
    if rho < 1e-9:
        return P * r
    return (P * math.cos(rho) + d.normalized() * math.sin(rho)) * r


def mat_odkrywany(nazwa, kolor, A, omega, kreska=None, alfa=1.0):
    """Emisja odkrywana od punktu A (wektor jednostkowy) do kąta omega [rad] wartością „postep” 0..1.
    kreska=(długość, wypełnienie) w radianach: wzór linii przerywanej liczony od A."""
    m = bpy.data.materials.new(nazwa)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    Wm = Wezly(m.node_tree)
    p = Wm.norm(Wm.geometria("Position"))
    ang = Wm.math("ARCCOSINE", Wm.math("MINIMUM", Wm.math("MAXIMUM", Wm.dot(p, tuple(A)), -1.0), 1.0))
    postep = Wm.wartosc(0.0, "postep")
    a = Wm.math("LESS_THAN", ang, Wm.mul(postep, omega * 1.02 + 0.002))
    if kreska:
        fr = Wm.math("FRACT", Wm.div(Wm.add(ang, kreska[0] * 0.3), kreska[0]))
        a = Wm.mul(a, Wm.math("LESS_THAN", fr, kreska[1]))
    if alfa < 1.0:
        a = Wm.mul(a, alfa)
        m.surface_render_method = "BLENDED"
    Wm.emisja_wyjscie(G.srgb(kolor), a)
    return m


def postep(m, f0, f1):
    from wezly import animuj_wartosc
    animuj_wartosc(m.node_tree, "postep", [(max(1, f0 - 1), 0.0), (f0, 0.0), (f1, 1.0)])


def rura(nazwa, pts, grub, m, r=1.004, zamknieta=False):
    return S.linia(nazwa, [p.normalized() * r for p in pts], grub, m, zamknieta=zamknieta)


def luk_od(nazwa, skad, dokad, kolor, grub, f0, f1, kreska=None, r=1.004, skroc=0.0):
    A = G.ll2xyz(*skad)
    pts = G.luk(*skad, *dokad, 160)
    if skroc:
        pts = pts[: int(len(pts) * (1 - skroc))]
    om = A.angle(pts[-1])
    m = mat_odkrywany(nazwa + "_mat", kolor, A, om, kreska)
    postep(m, f0, f1)
    return rura(nazwa, pts, grub, m, r)


def plat(nazwa, ukl, punkty, trojkaty, m, r=1.010):
    return S.siatka(nazwa, [pkt(ukl, x, y, r) for x, y in punkty], trojkaty, [m])


def kropka(nazwa, ll, rad, kolor, f0, r=1.0):
    ob = S.kula(nazwa, G.ll2xyz(*ll, r), rad, G.material_emisja(nazwa + "_mat", kolor))
    S.pojaw(ob, f0, 10)
    return ob


def napis_przy(nazwa, tekst, ll, dx, dy, rozm_px, kolor, f0, wyr="LEFT", obrys=((255, 255, 255), 0.045), kroj="arialb"):
    """Podpis przy punkcie kuli, odsunięty o (dx, dy) pikseli w układzie końcowego kadru; zwrócony do kamery."""
    p = G.ll2xyz(*ll) * 1.03 + PRAWO * (dx / R_PX) + GORA * (-dy / R_PX) + KU_KAM * 0.25
    return S.podpis(tekst, rozm_px / R_PX, kolor, p, cam, f0, kroj=kroj, wyr=wyr, obrys=obrys, nazwa=nazwa)


# ---------------------------------------------------------------- południk 70, Titicaca, Akpatok
mer = [G.ll2xyz(la, -70.0) for la in np.linspace(-66, 90, 157)] + [G.ll2xyz(la, 110.0) for la in np.linspace(89, 62, 28)]
m_zielona = G.material_emisja("Zielona", ZIELONA)
poludnik = S.linia("Poludnik_70", [p * 1.003 for p in mer], 0.0048, m_zielona, 8, 62)

# żółte kółko „70” na południku
u70 = uklad(21.0, -70.0, 0.0)
n_k = 40
kolo = [(0.0, 0.0)] + [(5.4 * math.cos(2 * math.pi * k / n_k), 5.4 * math.sin(2 * math.pi * k / n_k)) for k in range(n_k)]
znak70 = plat("Znak_70", u70, kolo, [(0, 1 + k, 1 + (k + 1) % n_k) for k in range(n_k)], G.material_emisja("Zolty70", (255, 232, 0)), r=1.012)
G.animuj_alfa(znak70.data.materials[0], [(39, 0.0), (40, 0.0), (52, 1.0)])
S.podpis("70", 38 / R_PX, CZARNY, G.ll2xyz(21.0, -70.0) * 1.03, cam, 42, obrys=None, nazwa="Napis_70")

kropka("Titicaca", TITICACA, 0.013, NIEBIESKI, 24, r=1.004)
napis_przy("Pod_Titicaca", "Titicaca", TITICACA, 18, 0, 27, GRANAT_TXT, 28)
kropka("Akpatok", AKPATOK, 0.016, CZARNY, 52, r=1.006)
napis_przy("Pod_Akpatok", "Akpatok", AKPATOK, 16, 30, 28, GRANAT_TXT, 58)

# ---------------------------------------------------------------- kwadraty Jukatan i Egipt + linie przerywane do Akpatok
KRESKA = (math.radians(3.6), 0.58)
for nazwa, ll, f_kw, f0, f1, dxy in (("Jukatan", JUKATAN, 60, 78, 128, (-124, 60)), ("Egipt", EGIPT, 168, 176, 236, (-40, 86))):
    az = G.azymut(*ll, *AKPATOK)
    ukl = uklad(*ll, az)
    b = 3.7
    kw = plat("Kwadrat_" + nazwa, ukl, [(-b, -b), (b, -b), (b, b), (-b, b)], [(0, 1, 2, 3)],
              G.material_emisja("Kwadrat_" + nazwa + "_mat", ZOLTY_KWADRAT, 0.72), r=1.008)
    G.animuj_alfa(kw.data.materials[0], [(f_kw - 1, 0.0), (f_kw, 0.0), (f_kw + 14, 0.72)])
    napis_przy("Pod_" + nazwa, nazwa, ll, dxy[0], dxy[1], 30, GRANAT_TXT, f_kw + 6)
    luk_od("Dawna_polnoc_" + nazwa, ll, AKPATOK, ZOLTA, 0.0046, f0, f1, kreska=KRESKA, r=1.005)
    print("[17] %s: azymut do Akpatok %.1f°" % (nazwa, az if az < 180 else az - 360))

# ---------------------------------------------------------------- gruba czerwona strzałka Akpatok -> Pn
uA = uklad(*AKPATOK, 0.0)
DL = 90.0 - AKPATOK[0] - 1.2          # grot kończy się tuż przed punktem Pn
SZ, GR, GL = 2.0, 5.6, 9.5            # półszerokość trzonu, półszerokość grotu, długość grotu [stopnie]
ny = 8
pts2 = []
for k in range(ny + 1):
    y = (DL - GL) * k / ny
    pts2 += [(-SZ, y), (SZ, y)]
tri = []
for k in range(ny):
    a = 2 * k
    tri.append((a, a + 1, a + 3, a + 2))
n0 = len(pts2)
pts2 += [(-GR, DL - GL), (GR, DL - GL), (0.0, DL)]
tri += [(n0, 2 * ny, n0 + 2), (2 * ny, 2 * ny + 1, n0 + 2), (2 * ny + 1, n0 + 1, n0 + 2)]
A_vec = G.ll2xyz(*AKPATOK)
om_s = math.radians(DL)
m_wyp = mat_odkrywany("Strzalka_wyp", FIOLET, A_vec, om_s, alfa=0.62)
m_obw = mat_odkrywany("Strzalka_obw", CZERWONA, A_vec, om_s)
F_S0, F_S1 = 232, 278
postep(m_wyp, F_S0, F_S1)
postep(m_obw, F_S0, F_S1)
plat("Strzalka_bieguna", uA, pts2, tri, m_wyp, r=1.011)
obrys = [(-SZ, 0), (SZ, 0)] + [(SZ, (DL - GL) * k / ny) for k in range(1, ny + 1)] + [(GR, DL - GL), (0, DL), (-GR, DL - GL)] + \
        [(-SZ, (DL - GL) * k / ny) for k in range(ny, 0, -1)]
rura("Strzalka_obrys", [pkt(uA, x, y) for x, y in obrys], 0.0055, m_obw, r=1.012, zamknieta=True)

kropka("Pn", (90.0, 0.0), 0.016, CZARNY, 268, r=1.008)
napis_przy("Pod_Pn", "Pn", (90.0, 0.0), -62, -26, 32, GRANAT_TXT, 272)

# ---------------------------------------------------------------- żółte linie ciągłe do Pn z grotami
for nazwa, ll, f0, f1 in (("Jukatan", JUKATAN, 284, 322), ("Egipt", EGIPT, 290, 328)):
    luk_od("Dzis_polnoc_" + nazwa, ll, (90.0, 0.0), ZOLTA, 0.0050, f0, f1, r=1.006, skroc=0.045)
    # grot przy biegunie: trójkąt w układzie bieguna, skierowany wzdłuż nadchodzącej linii
    kon = G.luk(*ll, 90.0, 0.0, 100)[94]
    la, lo = G.xyz2ll(kon)
    ug = uklad(la, lo, 0.0)
    gr = plat("Grot_" + nazwa, ug, [(-1.5, 0.0), (1.5, 0.0), (0.0, 4.6)], [(0, 1, 2)], G.material_emisja("Grot_" + nazwa + "_mat", ZOLTA), r=1.009)
    G.animuj_alfa(gr.data.materials[0], [(f1 - 7, 0.0), (f1 - 6, 0.0), (f1, 1.0)])

# ---------------------------------------------------------------- małe czerwone strzałki kąta + podpisy
OPISY = {"Jukatan": ("Odchylenie od północy\nna północny wschód", (300, 388), "RIGHT"),
         "Egipt": ("Odchylenie od północy\nna północny zachód", (1500, 300), "LEFT")}
m_czer = G.material_emisja("Czerwona", CZERWONA)
m_linia = G.material_emisja("Odnosnik", (245, 245, 245))
for nazwa, ll, rk, f0 in (("Jukatan", JUKATAN, 21.0, 330), ("Egipt", EGIPT, 17.0, 338)):
    az = G.azymut(*ll, *AKPATOK)
    az = az if az < 180 else az - 360
    u0 = uklad(*ll, 0.0)
    kat = [math.radians(a) for a in np.linspace(0.0, az, 24)]
    lk = [pkt(u0, rk * math.sin(a), rk * math.cos(a)) for a in kat]
    ob = S.linia("Kat_" + nazwa, [p * 1.008 for p in lk[:-3]], 0.0042, m_czer, f0, f0 + 16)
    # grot: w punkcie końcowym, wzdłuż łuku
    la, lo = G.xyz2ll(lk[-4])
    kier = G.azymut(la, lo, *G.xyz2ll(lk[-1]))
    ug = uklad(la, lo, kier)
    gr = plat("KatGrot_" + nazwa, ug, [(-1.3, 0.0), (1.3, 0.0), (0.0, 3.4)], [(0, 1, 2)], G.material_emisja("KatGrot_" + nazwa + "_mat", CZERWONA), r=1.010)
    G.animuj_alfa(gr.data.materials[0], [(f0 + 11, 0.0), (f0 + 12, 0.0), (f0 + 18, 1.0)])
    # podpis z rysunku + odnośnik do środka łuku
    tekst, (tx, ty), wyr = OPISY[nazwa]
    t = G.napis(tekst, 31 / R_PX, (255, 255, 255), "arialb", wyr, loc=tuple(z_ekranu(tx, ty)), nazwa="Opis_" + nazwa, odstep=1.08)
    c = t.constraints.new("COPY_ROTATION")
    c.target = cam
    G.alfa_napisu(t, [(f0 + 5, 0.0), (f0 + 6, 0.0), (f0 + 22, 1.0)])
    sx, sy = na_ekran(lk[len(lk) // 2])
    kx = tx + (16 if wyr == "RIGHT" else -16)
    a3, b3 = z_ekranu(kx, ty, 1.3), z_ekranu(sx, sy, 1.3)
    S.linia("Odn_" + nazwa, [a3, b3], 0.0022, m_linia, f0 + 8, f0 + 24)
    print("[17] %s: opis %s, środek łuku na ekranie (%.0f, %.0f)" % (nazwa, (tx, ty), sx, sy))

for nm, ll in (("Akpatok", AKPATOK), ("Pn", (90, 0)), ("Jukatan", JUKATAN), ("Egipt", EGIPT), ("Titicaca", TITICACA)):
    print("[17] ekran", nm, tuple(round(v) for v in na_ekran(G.ll2xyz(*ll))))

G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
