# -*- coding: utf-8 -*-
"""
Kamienne olbrzymy w jednej skali (zwiastun, odcinek 0 „Wstęp”).

Lektor: „Oddzielmy budowle, które mógł zbudować człowiek od tych, których zbudować nie mógł,
bo nie miał ani siły ani techniki.”

Rekonstrukcja: prawdziwe kamienie z dawnych budowli i kamieniołomów ustawione w jednym szeregu, w tej samej skali
(1 jednostka = 1 m), od najlżejszego do najcięższego. Dla skali stoi obok zwykły samochód osobowy.
Wymiary i masy: patrz README.md (źródła). Klip niczego nie rozstrzyga – pokazuje same rozmiary.

Uruchomienie:
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-kamienne-olbrzymy/scena.py -- --proba 1,80,160,235,305,400
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-kamienne-olbrzymy/scena.py
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, noise

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, "..", "_wspolne"))
import globus as G, zwiastun as Z

opcje = G.argumenty()
NKL = 400  # 16 s
sc = Z.start(NKL, opcje, probki=40)
Z.swiat((5, 8, 16), (30, 46, 84), moc=1.0)

# ---------------------------------------------------------------- kamienie

def glaz(nazwa, wym, mat, komorka=0.4, r=0.25, amp=0.07, skala_szumu=0.5, ziarno=0.0, zwezenie=(1.0, 1.0),
         poduszka=0.0):
    """Zaokrąglony prostopadłościan z nierówną powierzchnią (szum). wym = (x, y, z) w metrach, podstawa na z = 0.
    zwezenie = (sx, sy): mnożnik wymiarów poziomych na górze (1 = bez zwężenia); poduszka = wybrzuszenie ścian."""
    h = np.array(wym, float) / 2
    n = [max(2, int(round(w / komorka))) for w in wym]
    idx, verts, faces = {}, [], []

    def v(p):
        k = tuple(np.round(p, 5))
        if k not in idx:
            idx[k] = len(verts)
            verts.append(np.array(p, float))
        return idx[k]

    for ax in range(3):
        a, b = [(1, 2), (2, 0), (0, 1)][ax]
        for sgn in (-1, 1):
            for i in range(n[a]):
                for j in range(n[b]):
                    q = []
                    for di, dj in ((0, 0), (1, 0), (1, 1), (0, 1)):
                        p = [0.0, 0.0, 0.0]
                        p[ax] = sgn * h[ax]
                        p[a] = -h[a] + 2 * h[a] * (i + di) / n[a]
                        p[b] = -h[b] + 2 * h[b] * (j + dj) / n[b]
                        q.append(v(p))
                    faces.append(q if sgn > 0 else q[::-1])
    P = np.array(verts)
    Q = np.clip(P, -(h - r), h - r)
    D = P - Q
    dl = np.linalg.norm(D, axis=1, keepdims=True)
    N = D / np.maximum(dl, 1e-9)
    P2 = Q + N * r
    out = []
    for p, nn in zip(P2, N):
        w = Vector(p * skala_szumu) + Vector((ziarno, ziarno * 1.7, ziarno * 0.3))
        s = noise.fractal(w, 1.0, 2.0, 5, noise_basis="PERLIN_ORIGINAL")
        s2 = noise.noise(w * 0.35)
        d = amp * (s * 0.7 + s2 * 1.6)
        # wyszczerbione krawędzie: tam, gdzie normalna nie jest równoległa do osi (krawędzie i naroża)
        kraw = 1.0 - float(np.max(np.abs(nn)))
        if kraw > 0.02:
            d -= r * 0.55 * min(1.0, kraw * 3.0) * (0.35 + abs(noise.noise(w * 2.3)))
        if poduszka:
            # wybrzuszenie środka ścian (kamienie „poduszkowe” z Sacsayhuamán)
            u = np.abs(p) / h
            d += poduszka * (1 - np.sort(u)[1] ** 2)
        q = p + nn * d
        t = (q[2] + h[2]) / (2 * h[2])
        q[0] *= 1 + (zwezenie[0] - 1) * t
        q[1] *= 1 + (zwezenie[1] - 1) * t
        q[2] += h[2]
        out.append(q)
    ob = Z.siatka(nazwa, out, faces, [mat], gladka=True)
    return ob


M_WAP_JASNY = Z.kamien("wapien_jasny", (214, 196, 156), (176, 156, 118), skala=4.0, wypuklosc=0.7, warstwy=0.6)
M_SARSEN = Z.kamien("sarsen", (150, 150, 146), (104, 106, 104), skala=1.6, wypuklosc=0.9, rysy=0.0)
M_SACSAY = Z.kamien("wapien_szary", (146, 140, 130), (100, 96, 90), skala=1.0, wypuklosc=0.8, rysy=0.0)
M_BAALBEK = Z.kamien("wapien_baalbek", (206, 180, 134), (150, 122, 84), skala=1.1, wypuklosc=1.0, warstwy=0.6)
M_GRANIT = Z.kamien("granit_asuan", (178, 112, 94), (120, 70, 62), skala=1.2, wypuklosc=0.7, plamy=0.8, rysy=0.0)

# położenia w szeregu (x = środek, metry)
X_AUTO, X_BLOK, X_SARSEN, X_SACSAY, X_TRYLIT, X_KCK, X_OBELISK = -5.0, 0.0, 4.0, 10.0, 25.5, 49.25, 85.0

blok = glaz("BlokPiramidy", (1.3, 1.3, 0.7), M_WAP_JASNY, komorka=0.08, r=0.05, amp=0.012, skala_szumu=2.5)
blok.location = (X_BLOK, 0, 0)

sarsen = glaz("Sarsen", (2.1, 1.1, 4.1), M_SARSEN, komorka=0.12, r=0.3, amp=0.07, skala_szumu=0.9, ziarno=3.1,
              zwezenie=(0.86, 0.9))
sarsen.location = (X_SARSEN, 0, 0)

sacsay = glaz("Sacsayhuaman", (4.0, 2.0, 8.5), M_SACSAY, komorka=0.2, r=0.55, amp=0.06, skala_szumu=0.5, ziarno=7.7,
              zwezenie=(0.82, 0.92), poduszka=0.22)
sacsay.location = (X_SACSAY, 0, 0)

trylit = glaz("BlokTrylitu", (19.0, 3.6, 4.2), M_BAALBEK, komorka=0.16, r=0.3, amp=0.1, skala_szumu=0.45, ziarno=11.0)
trylit.location = (X_TRYLIT, 0, 0)

kck = glaz("KamienCiezarnejKobiety", (20.5, 4.5, 4.3), M_BAALBEK, komorka=0.16, r=0.36, amp=0.13, skala_szumu=0.4,
           ziarno=19.0)
kck.location = (X_KCK, 0, 0)

# obelisk: leży wzdłuż osi x. Wymiary według R. Engelbacha, „The Aswân Obelisk” (1922): długość 41,75 m,
# podstawa 4,20 m, podstawa piramidionu 2,50 m, wysokość piramidionu 4,50 m (masa po ukończeniu: 1168 ton ang.)
def obelisk():
    L, a0, a1, lp = 41.75, 4.2, 2.5, 4.5
    nx, nb = 110, 10
    verts, faces = [], []
    pier = []
    for i in range(nx + 1):
        x = L * i / nx
        if x <= L - lp:
            a = a0 + (a1 - a0) * x / (L - lp)
        else:
            a = a1 * max(0.02, (L - x) / lp)
        ring = []
        for k in range(4 * nb):
            bok, j = divmod(k, nb)
            t = j / nb
            cor = [(-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)]
            y = (cor[bok][0] * (1 - t) + cor[bok + 1][0] * t) * a / 2
            z = (cor[bok][1] * (1 - t) + cor[bok + 1][1] * t) * a / 2
            w = Vector((x * 0.5, y * 0.6, z * 0.6))
            d = 0.05 * noise.fractal(w, 1.0, 2.0, 4, noise_basis="PERLIN_ORIGINAL")
            rr = math.hypot(y, z) or 1
            ring.append(len(verts))
            verts.append((x - L / 2, y * (1 + d / rr), z * (1 + d / rr) + a0 / 2))
        pier.append(ring)
    for i in range(nx):
        for k in range(4 * nb):
            k2 = (k + 1) % (4 * nb)
            faces.append((pier[i][k], pier[i][k2], pier[i + 1][k2], pier[i + 1][k]))
    faces.append(tuple(reversed(pier[0])))
    faces.append(tuple(pier[-1]))
    return Z.siatka("ObeliskAsuan", verts, faces, [M_GRANIT], gladka=False)


ob_obelisk = obelisk()
ob_obelisk.location = (X_OBELISK, 0, 0)

# ---------------------------------------------------------------- samochód dla skali (4,4 × 1,8 × 1,45 m)
M_LAK = Z.pbr("lakier", (190, 196, 205), szorstkosc=0.3, metal=0.6)
M_SZYBA = Z.pbr("szyba", (16, 22, 34), szorstkosc=0.08)
M_OPONA = Z.pbr("opona", (14, 14, 16), szorstkosc=0.8)


def samochod(x0):
    czesci = []
    # nadwozie: profil boczny (x, z) wyciągnięty na szerokość 1,8 m
    prof = [(-2.2, 0.32), (-2.2, 0.72), (-2.05, 0.86), (-1.25, 0.94), (-0.62, 1.42), (0.75, 1.45), (1.55, 0.98),
            (2.12, 0.9), (2.2, 0.7), (2.2, 0.32)]
    bm = bmesh.new()
    lewe = [bm.verts.new((x, -0.9, z)) for x, z in prof]
    prawe = [bm.verts.new((x, 0.9, z)) for x, z in prof]
    bm.faces.new(lewe[::-1])
    bm.faces.new(prawe)
    for i in range(len(prof)):
        j = (i + 1) % len(prof)
        bm.faces.new((lewe[i], lewe[j], prawe[j], prawe[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.07, segments=3, affect="EDGES")
    nad = Z.z_bmesh("Auto", bm, [M_LAK], gladka=True)
    czesci.append(nad)
    # szyby boczne: ciemne trapezy tuż przed blachą
    for sy in (-1, 1):
        okno = [(-1.12, 0.98), (-0.6, 1.36), (0.7, 1.39), (1.38, 1.0)]
        o = Z.siatka("Szyba", [(x, sy * 0.905, z) for x, z in okno], [(0, 1, 2, 3)], [M_SZYBA])
        czesci.append(o)
    for sx in (-1.38, 1.4):
        for sy in (-0.82, 0.82):
            bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.33, depth=0.24, location=(sx, sy, 0.33),
                                                rotation=(math.pi / 2, 0, 0))
            k = bpy.context.active_object
            k.data.materials.append(M_OPONA)
            czesci.append(k)
    root = Z.pusty("AutoRoot", (x0, 0, 0))
    for c in czesci:
        c.parent = root
    return root


samochod(X_AUTO)

# ---------------------------------------------------------------- podłoga i podziałka
M_PODLOGA = Z.pbr("podloga", (24, 33, 58), szorstkosc=0.3)
bpy.ops.mesh.primitive_plane_add(size=1200, location=(50, 0, 0))
bpy.context.active_object.data.materials.append(M_PODLOGA)

Y_MIARA = -3.6
Z.linia([(-8, Y_MIARA, 0.03), (108, Y_MIARA, 0.03)], 0.035, G.ZLOTY, "Miara")
for x in range(-5, 106, 5):
    dl = 0.7 if x % 10 == 0 else 0.35
    Z.linia([(x, Y_MIARA, 0.03), (x, Y_MIARA - dl, 0.03)], 0.03, G.ZLOTY, "Kreska")
for x in range(0, 101, 10):
    Z.napis_swiat(f"{x} m", 0.9 if x >= 20 else 0.45, (x, Y_MIARA - (1.6 if x >= 20 else 1.1), 0.03), G.ZLOTY, "arialb",
                  rot=(0, 0, 0))

# ---------------------------------------------------------------- podpisy (stoją nad kamieniami, czytane od strony kamery)
BIALY = (245, 240, 228)


def podpis(x, z, nazwa, masa, rozm, pojaw, znik=None, koniec=1.0):
    """Dwa wiersze nad kamieniem; koniec = powiększenie w ujęciu końcowym (klatki 300-400)."""
    root = Z.pusty("Podpis", (x, 0.0, z))
    a = Z.napis_swiat(nazwa, rozm, (0, 0, rozm * 2.0), BIALY, "georgia")
    b = Z.napis_swiat(masa, rozm * 1.5, (0, 0, rozm * 0.8), G.ZLOTY, "georgiab")
    for o in (a, b):
        o.parent = root
        kl = [(1, 0.0), (pojaw, 0.0), (pojaw + 14, 1.0)]
        if znik:
            kl += [(znik, 1.0), (znik + 16, 0.0)]
        G.alfa_napisu(o, kl)
    if koniec != 1.0:
        for f, v in ((300, 1.0), (392, koniec)):
            root.scale = (v, v, v)
            root.keyframe_insert("scale", frame=f)
        G.wygladz(root)
    return root


podpis(X_AUTO, 1.55, "samochód osobowy (dla skali)", "ok. 1,5 t", 0.26, 8, 318)
podpis(X_BLOK, 0.9, "blok Wielkiej Piramidy", "średnio ok. 2,5 t", 0.2, 22, 318)
podpis(X_SARSEN, 4.4, "Stonehenge, głaz sarsen", "ok. 25 t", 0.42, 62, 318)
podpis(X_SACSAY, 8.9, "Sacsayhuamán, największy głaz", "128–200 t (szacunki)", 0.62, 92, 318)
podpis(X_TRYLIT, 4.9, "Baalbek, blok trylitu", "ok. 800 t", 1.25, 135, koniec=1.55)
podpis(X_KCK, 5.0, "Kamień Ciężarnej Kobiety", "ok. 1000 t", 1.35, 205, koniec=1.45)
podpis(X_OBELISK, 5.2, "Asuan, niedokończony obelisk", "ok. 1100 t", 1.9, 270, koniec=1.25)
# w ujęciu końcowym małe podpisy są nieczytelne – zastępuje je jeden duży
Z.napis_swiat("od 1,5 t\ndo ponad 100 t", 2.3, (2.5, 0.0, 14.5), G.ZLOTY, "georgiab", pojaw=(338, 356))

# ---------------------------------------------------------------- kamera
cam = G.kamera((0, -10, 2), (0, 0, 1), lens=32)
cam.data.clip_end = 2000
cel = Z.pusty("Cel")
Z.lot_kamery(cam, cel, [
    (1, (-3.4, -8.6, 1.5), (-2.8, 0, 1.25)),
    (80, (5.0, -17.5, 3.2), (6.2, 0, 4.0)),
    (160, (23.5, -30.0, 5.5), (25.0, 0, 3.6)),
    (235, (47.0, -34.0, 7.0), (48.5, 0, 3.8)),
    (305, (82.0, -54.0, 12.0), (83.0, 0, 4.5)),
    (400, (60.0, -100.0, 30.0), (50.5, 0, 1.5)),
])

Z.napis_ekran(cam, "Kamienne olbrzymy w jednej skali", 960, 150, 62, G.ZLOTY, "georgiab", odl=1.0, pojaw=(345, 368))

# ---------------------------------------------------------------- światło
Z.slonce((0.55, 0.75, -0.62), moc=3.2, kolor=(1.0, 0.9, 0.76), kat=3.0)
sl2 = Z.slonce((-0.6, 0.5, -0.35), moc=0.7, kolor=(0.55, 0.68, 1.0), kat=20.0, cien=False)

G.renderuj(DIR, opcje, kadr_klatka=400)
