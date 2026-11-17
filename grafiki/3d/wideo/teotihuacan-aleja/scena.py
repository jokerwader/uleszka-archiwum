# -*- coding: utf-8 -*-
"""Klip „teotihuacan-aleja”: ożywiony szkic Leszka Klimka teotihuacan.jpg (rozdz. „Jak to wygląda w praktyce?”).

Szkic leży jak plansza: miętowe tło, czarne budowle z białym środkiem, biała aleja, czerwona linia przerywana wzdłuż
alei i granatowa strzałka „Pn” (na szkicu północ jest po prawej). Budowle są odczytane z pikseli szkicu
(plamy czarnych pikseli -> kwadraty ustawione równolegle do alei) i wyrastają z planu. Potem rośnie czerwona linia,
strzałka północy i złoty łuk kąta między północą a aleją z podpisem „ok. 18°” (liczba z tekstu Leszka).

Uruchomienie: S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/teotihuacan-aleja/scena.py
              ... -- --proba 1,120,250,400
"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
import schemat as S

OPCJE = G.argumenty()
KLATKI = 400  # 16 s
SK = 0.1      # 1 piksel szkicu = 0,1 jednostki sceny
MIETA = (160, 214, 186)     # tło szkicu
CZERN = (26, 26, 26)
BIEL = (250, 250, 250)
CZERWIEN = (226, 30, 40)    # linia przerywana
GRANAT = (36, 36, 128)      # strzałka Pn
ZLOTY = G.ZLOTY

sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))
S.swiatlo(kat=(46, 0, -32), sila=2.3, otoczenie=(205, 215, 235), moc=0.5)

# ---------------------------------------------------------------- szkic -> dane
img = G.obraz_numpy(os.path.join(G.RYSUNKI, "teotihuacan.jpg"))
HH, WW = img.shape[:2]
rgb = img[..., :3]
jas = rgb.sum(2)

# czerwona linia alei: dopasowanie prostej j = m*i + c do czerwonych pikseli
czer = (rgb[..., 0] > 0.66) & (rgb[..., 1] < 0.43) & (rgb[..., 2] < 0.43)
jj, ii = np.nonzero(czer)
M_, C_ = np.linalg.lstsq(np.vstack([ii, np.ones(len(ii))]).T, jj, rcond=None)[0]
KAT_ALEI = math.atan(M_)                     # w układzie obrazu (oś j w dół)
print("[teo] linia alei: j = %.4f*i + %.2f, kąt do krawędzi szkicu %.2f°" % (M_, C_, math.degrees(KAT_ALEI)))


def px(i, j, z=0.0):
    """piksel szkicu -> scena (x w prawo, y w górę kartki)"""
    return Vector(((i - WW / 2) * SK, (HH / 2 - j) * SK, z))


def na_alei(i):
    return (i, M_ * i + C_)


U = Vector((math.cos(KAT_ALEI), -math.sin(KAT_ALEI), 0))   # kierunek alei w scenie
V = Vector((-U.y, U.x, 0))                                  # prostopadły (w górę kartki)
ROT = math.atan2(U.y, U.x)

# plamy czarnych pikseli (budowle), bez strzałki „Pn” i bez Cytadeli (ta jest opisana ręcznie niżej)
ciemne = jas < 0.85
ciemne[20:36, 24:106] = False
ciemne[56:75, 131:151] = False             # trzy zlane platformy przy alei – opisane ręcznie niżej
CYT = (30.9, 56.9)                           # środek Cytadeli [px]
CYT_U, CYT_V = 33.4, 28.9                    # wymiary wzdłuż alei i w poprzek [px]
for j in range(HH):
    for i in range(WW):
        if ciemne[j, i]:
            d = Vector(((i - CYT[0]), -(j - CYT[1]), 0))
            if abs(d.dot(U)) < CYT_U / 2 + 2 and abs(d.dot(V)) < CYT_V / 2 + 2:
                ciemne[j, i] = False
etyk = np.zeros((HH, WW), np.int32)
plamy = []
for j0 in range(HH):
    for i0 in range(WW):
        if ciemne[j0, i0] and not etyk[j0, i0]:
            nr = len(plamy) + 1
            stos, pts = [(j0, i0)], []
            etyk[j0, i0] = nr
            while stos:
                j, i = stos.pop()
                pts.append((i, j))
                for dj in (-1, 0, 1):
                    for di in (-1, 0, 1):
                        a, b = j + dj, i + di
                        if 0 <= a < HH and 0 <= b < WW and ciemne[a, b] and not etyk[a, b]:
                            etyk[a, b] = nr
                            stos.append((a, b))
            plamy.append(pts)

BUDOWLE = []   # (środek_i, środek_j, bok_u, bok_v, biały_środek)
for pts in plamy:
    if len(pts) < 3:
        continue
    P = np.array(pts, float)
    pu = P[:, 0] * U.x - P[:, 1] * U.y
    pv = P[:, 0] * V.x - P[:, 1] * V.y
    bu, bv = pu.max() - pu.min() + 1.0, pv.max() - pv.min() + 1.0
    cu_, cv_ = (pu.max() + pu.min()) / 2, (pv.max() + pv.min()) / 2
    ci = cu_ * U.x + cv_ * V.x
    cj = -(cu_ * U.y + cv_ * V.y)
    if not (2 < ci < WW - 2 and 2 < cj < HH - 2):
        continue
    bialy = jas[int(round(cj)), int(round(ci))] > 2.3 and min(bu, bv) > 4
    BUDOWLE.append((ci, cj, bu, bv, bialy))
print("[teo] budowli ze szkicu:", len(BUDOWLE), " największe:",
      sorted([(round(b[2], 1), round(b[0]), round(b[1])) for b in BUDOWLE], reverse=True)[:4])

# ---------------------------------------------------------------- materiały
m_mieta = S.mat("Mieta", MIETA, 0.95)
m_czern = S.mat("Czern", CZERN, 0.55)
m_biel = S.mat("Biel", BIEL, 0.9)
m_czerw = S.mat("Czerwien", CZERWIEN, 0.6, emisja=0.35)
m_granat = S.mat("Granat", GRANAT, 0.6, emisja=0.25)
m_zloty = G.material_emisja("Zloty", ZLOTY)

# plansza szkicu
plansza = S.pudlo("Plansza", (0, 0, -0.3), (WW * SK, HH * SK, 0.3), m_mieta)


def bryla(nazwa, ci, cj, bu, bv, wys, stopnie, bialy, f0):
    """Budowla schodkowa: `stopnie` pięter coraz mniejszych, biała podstawa-obrys i (opcjonalnie) biały szczyt."""
    c = px(ci, cj)
    verts, faces, idx = [], [], []

    def klocek(du, dv, z0, z1, mi):
        n = len(verts)
        for z in (z0, z1):
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = U * (su * du / 2 * SK) + V * (sv * dv / 2 * SK)
                verts.append((p.x, p.y, z))
        for f in ((3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            faces.append(tuple(n + k for k in f))
            idx.append(mi)

    klocek(bu + 0.9, bv + 0.9, 0.0, 0.012, 1)                      # biały obrys przy ziemi
    for s in range(stopnie):
        k = 1.0 - 0.62 * s / stopnie
        klocek(bu * k, bv * k, wys * s / stopnie, wys * (s + 1) / stopnie, 0)
    if bialy:
        k = 1.0 - 0.62 * (stopnie - 1) / stopnie
        klocek(bu * k * 0.82, bv * k * 0.82, wys, wys + 0.03, 1)   # biały środek ze szkicu
    ob = S.siatka(nazwa, verts, faces, [m_czern, m_biel], indeksy=idx)
    ob.location = c
    ob.scale = (1, 1, 0.08)
    ob.keyframe_insert("scale", frame=f0)
    ob.scale = (1, 1, 1)
    ob.keyframe_insert("scale", frame=f0 + 34)
    G.wygladz(ob)
    return ob


def start_budowli(ci):
    return int(8 + 70 * ci / WW)


SLONCE = KSIEZYC = None
for n, (ci, cj, bu, bv, bialy) in enumerate(BUDOWLE):
    bok = max(bu, bv)
    if bok >= 9:                       # piramidy Słońca i Księżyca
        b_ = bryla(f"Piramida_{n}", ci, cj, bu, bv, 0.55 * bok * SK, 5, True, start_budowli(ci))
        if bok > 17:
            SLONCE = (ci, cj, 0.55 * bok * SK)
        else:
            KSIEZYC = (ci, cj, 0.55 * bok * SK)
    elif bialy:                        # mniejsze platformy z białym środkiem
        bryla(f"Platforma_{n}", ci, cj, bu, bv, 0.5 * bok * SK, 3, True, start_budowli(ci))
    else:                              # małe budowle (kropki na szkicu)
        bryla(f"Budowla_{n}", ci, cj, max(bu, 2.0), max(bv, 2.0), (0.7 * bok + 0.8) * SK, 1, False, start_budowli(ci))

# grupa trzech platform przy alei (na szkicu stykają się rogami, więc zlewały się w jedną plamę)
for k, (ci, cj) in enumerate(((143.1, 60.6), (136.3, 64.0), (145.6, 67.9))):
    bryla(f"Platforma_grupa_{k}", ci, cj, 6.0, 6.0, 0.3, 3, True, start_budowli(ci))
for k, (ci, cj) in enumerate(((134.8, 68.1), (143.8, 71.6))):
    bryla(f"Budowla_grupa_{k}", ci, cj, 2.2, 2.2, 0.23, 1, False, start_budowli(ci))

# Cytadela: obrys zewnętrzny i wewnętrzny (cienkie linie szkicu = niskie mury), dwie platformy świątyni, rzędy małych budowli
def mur(nazwa, srodek, du, dv, grub, wys, f0):
    c = px(*srodek)
    for k, (su, sv, lu, lv) in enumerate(((0, 1, du, grub), (0, -1, du, grub), (1, 0, grub, dv), (-1, 0, grub, dv))):
        p = c + U * (su * du / 2 * SK) + V * (sv * dv / 2 * SK)
        ob = S.pudlo(f"{nazwa}_{k}", (p.x, p.y, 0), (lu * SK + (grub * SK if su == 0 else 0), lv * SK, wys), m_czern, ROT)
        S.pojaw(ob, f0, 30, os_z=True)


mur("Cytadela_zewn", CYT, CYT_U, CYT_V, 0.55, 0.09, 10)
mur("Cytadela_wewn", (31.4, 57.4), 22.5, 21.0, 0.45, 0.06, 14)
QUETZ = (30.6, 56.9)
bryla("Swiatynia_Quetzalcoatla", *QUETZ, 6.6, 6.6, 0.36, 3, True, 18)
bryla("Platforma_przy_swiatyni", 28.1, 64.6, 6.6, 6.6, 0.33, 3, True, 20)
for k, (i8, j8) in enumerate(((170, 352), (160, 380), (148, 407), (140, 435), (377, 425), (367, 455), (355, 485), (343, 512))):
    bryla(f"Cytadela_mala_{k}", i8 / 8, j8 / 8, 2.0, 2.0, 0.2, 1, False, 16 + k)

# aleja: biały pas (szeroki przy Cytadeli, dalej wąski) i biały plac przed Piramidą Księżyca
def pas(nazwa, i0, i1, szer, przes=0.0, wys=0.010):
    a, b = px(*na_alei(i0)), px(*na_alei(i1))
    c = (a + b) / 2 - V * (przes * SK)
    return S.pudlo(nazwa, (c.x, c.y, 0), ((b - a).length, szer * SK, wys), m_biel, ROT)


pas("Aleja_szeroka", 11, 53, 3.4, przes=1.9)
pas("Aleja_waska", 53, 158, 1.3, przes=0.4, wys=0.008)
pas("Plac_Ksiezyca", 157, 170, 7.0, przes=0.3, wys=0.009)

# czerwona linia przerywana wzdłuż alei (jak na szkicu: przez całą planszę)
A0, A1 = px(*na_alei(5), 0.014), px(*na_alei(191), 0.014)
S.kreski("Linia_alei", A0, A1, 0.075, 0.02, m_czerw, dl=0.23, przerwa=0.15, f0=90, f1=170)

# granatowa strzałka „Pn” (na szkicu północ jest po prawej)
P0, P1 = px(26.5, 28.5, 0.014), px(88.0, 28.5, 0.014)
L = (P1 - P0).length
gr, sz, gl = 0.19, 0.055, 0.5
verts = [(0, -sz, 0), (L - gl, -sz, 0), (L - gl, -gr, 0), (L, 0, 0), (L - gl, gr, 0), (L - gl, sz, 0), (0, sz, 0)]
verts += [(x, y, 0.03) for x, y, z in verts]
faces = [tuple(range(6, -1, -1)), tuple(range(7, 14))] + [(k, (k + 1) % 7, 7 + (k + 1) % 7, 7 + k) for k in range(7)]
strz = S.siatka("Strzalka_Pn", verts, faces, [m_granat])
strz.location = P0
strz.scale = (0.001, 1, 1)
strz.keyframe_insert("scale", frame=150)
strz.scale = (1, 1, 1)
strz.keyframe_insert("scale", frame=185)
G.wygladz(strz)
S.podpis("Pn", 0.72, (16, 16, 70), px(99.5, 28.3, 0.03), f0=182, rot=(0, 0, 0), obrys=None, nazwa="Pn")

# złoty łuk kąta między północą a aleją; wierzchołek = przecięcie linii strzałki z linią alei
iw = (28.5 - C_) / M_
W0 = px(iw, 28.5, 0.03)
R_LUK = 4.6
luk = [W0 + Vector((math.cos(-t), math.sin(-t), 0)) * R_LUK for t in np.linspace(0.0, KAT_ALEI, 40)]
S.linia("Luk_kata", luk, 0.045, m_zloty, 200, 245)
sr = W0 + Vector((math.cos(-KAT_ALEI / 2), math.sin(-KAT_ALEI / 2), 0)) * (R_LUK + 1.25)

# ---------------------------------------------------------------- kamera
cam = G.kamera((0, -3, 34), (0, 0, 0), lens=50)
cam.data.shift_y = -0.055
cam.data.clip_start, cam.data.clip_end = 6.0, 300.0


def tor(f):
    t = S.rampa(f, 55, 335)
    d = (f - 1) / (KLATKI - 1)
    return (-90 + 8 * t + 2.0 * d, 80 - 38 * t, 42.0 - 6.0 * t)


S.orbita_f(cam, (0.3, 0.4, 0), tor, KLATKI)
G.tlo_kamery(cam, odl=120)

# podpisy (zwrócone do kamery): liczba z tekstu na złoto, nazwy na biało
S.podpis("ok. 18°", 0.62, ZLOTY, (sr.x, sr.y, 0.35), cam, 238, obrys=((10, 14, 28), 0.05), nazwa="Kat18")
am = px(*na_alei(84))
S.podpis("Aleja Zmarłych", 0.56, (255, 255, 255), (am.x + V.x * 0.48, am.y + V.y * 0.48, 0.03), f0=172,
         rot=(0, 0, ROT), obrys=((10, 14, 28), 0.05), nazwa="Aleja")
if SLONCE:
    p = px(SLONCE[0], SLONCE[1])
    S.podpis("Piramida Słońca", 0.55, (255, 255, 255), (p.x, p.y, SLONCE[2] + 0.9), cam, 262, obrys=((10, 14, 28), 0.05))
if KSIEZYC:
    p = px(KSIEZYC[0], KSIEZYC[1])
    S.podpis("Piramida Księżyca", 0.55, (255, 255, 255), (p.x - 0.6, p.y, KSIEZYC[2] + 0.9), cam, 278,
             obrys=((10, 14, 28), 0.05))
p = px(*QUETZ)
pq = p - V * 2.35
S.podpis("Świątynia Quetzalcoatla", 0.55, (255, 255, 255), (pq.x, pq.y, 0.3), cam, 294, obrys=((10, 14, 28), 0.05))

G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
