# -*- coding: utf-8 -*-
"""Klip „uskok-globus”: ożywiony rysunek Leszka Klimka uskok.jpg.

Globus widziany od strony bieguna północnego, w tym samym rzucie co rysunek (rzut azymutalny
równoodległy o środku ok. 48°N 34°E, dopasowany do rysunku). Skorupa przesuwa się w kierunku
czerwonej strzałki: wyspa Akpatok (biegun sprzed ok. 12 000 lat, 60°N 70°W według tabeli Leszka)
odjeżdża z osi obrotu, a na oś wjeżdża dzisiejszy biegun. Równik sprzed 12 000 lat jedzie razem
ze skorupą, równik dzisiejszy zostaje w miejscu. Ostatnia klatka = rysunek Leszka.

Uruchomienie (z katalogu repozytorium):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/uskok-globus/scena.py
  ... -- --proba 1,150,375     (tylko kadry próbne PNG w _klatki/)
"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector, Matrix

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
from wezly import Wezly, animuj_wartosc

OPCJE = G.argumenty()
KLATKI = 375  # 15 s

# ---------------------------------------------------------------- rzut rysunku
# Dopasowanie (najmniejsze kwadraty, 5 punktów kontrolnych: oba bieguny, Przylądek Igielny,
# południe Madagaskaru, południe Indii) rzutu azymutalnego równoodległego do uskok.jpg (350×352 px).
C_LAT, C_LON, TETA, CMAX = 48.0, 34.0, 34.0, 104.0   # środek, obrót obrazu, kąt na brzegu tarczy
RYS_CX, RYS_CY, RYS_R = 173.0, 186.0, 157.0          # tarcza na rysunku (px)
AKPATOK = (60.0, -70.0)                               # tabela Leszka: Akpatok 60,00°N 70,00°W

# Kadr: tarcza o promieniu 400 px, środek w (960, 460) – dół 200 px i lewy górny róg wolne.
RPX, CX, CY = 400.0, 960.0, 460.0


def rzut(lat, lon):
    """(lat, lon) -> (x, y) tarczy w jednostkach promienia (y w górę), dla stanu końcowego."""
    f0, l0 = math.radians(C_LAT), math.radians(C_LON)
    f, l = math.radians(lat), math.radians(lon)
    cc = math.sin(f0) * math.sin(f) + math.cos(f0) * math.cos(f) * math.cos(l - l0)
    c = math.degrees(math.acos(max(-1, min(1, cc))))
    y = math.sin(l - l0) * math.cos(f)
    x = math.cos(f0) * math.sin(f) - math.sin(f0) * math.cos(f) * math.cos(l - l0)
    az = math.atan2(y, x) + math.radians(TETA)
    r = c / CMAX
    return r * math.sin(az), r * math.cos(az)


def rzut_wektor(v):
    lat, lon = G.xyz2ll(v)
    return rzut(lat, lon)


def px(x, y):
    """jednostki tarczy -> piksele kadru"""
    return CX + x * RPX, CY - y * RPX


def swiat(pxx, pxy, z=1.4):
    return Vector(((pxx - CX) / RPX, -(pxy - CY) / RPX, z))


def rys_na_tarcze(x, y):
    """piksel rysunku Leszka -> jednostki tarczy"""
    return (x - RYS_CX) / RYS_R, -(y - RYS_CY) / RYS_R


# ---------------------------------------------------------------- maski z rysunku
def maski_z_rysunku():
    """Czerwona strzałka (w układzie tarczy) i czapa lodowa (geograficznie) odczytane z uskok.jpg."""
    p_strz = os.path.join(G.CACHE, "uskok_strzalka.png")
    p_lod = os.path.join(G.CACHE, "uskok_lod.png")
    if os.path.exists(p_strz) and os.path.exists(p_lod):
        return p_strz, p_lod
    d = G.obraz_numpy(os.path.join(G.RYSUNKI, "uskok.jpg")) * 255
    r, g, b = d[..., 0], d[..., 1], d[..., 2]
    H, W = r.shape
    yy, xx = np.mgrid[0:H, 0:W]
    wew = np.hypot(xx - RYS_CX, yy - RYS_CY) < 154
    czerw = ((r > 120) & (r - g > 50) & (r - b > 35) & wew).astype(np.float32)
    bialy = (r > 215) & (g > 235) & (b > 235)
    jasnoziel = (g > 195) & (r > 120) & (r < 215) & (g - b > 4)
    lod = ((bialy | jasnoziel) & wew).astype(np.float32)
    # jasne morze przy lewym górnym brzegu (odblask na rysunku) to nie lód
    lod[(xx < 140) & (yy < 92)] = 0
    # domknięcie dziur i wygładzenie
    lod = (G.rozmyj(lod, 2) > 0.35).astype(np.float32)
    lod = (G.rozmyj(lod, 2) > 0.6).astype(np.float32)
    # zostaw tylko duży obszar wokół starego bieguna (wypełnianie od punktu startowego)
    from collections import deque
    sx, sy = 175, 120
    seen = np.zeros_like(lod, bool)
    q = deque([(sy, sx)])
    seen[sy, sx] = True
    while q:
        y0, x0 = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            y1, x1 = y0 + dy, x0 + dx
            if 0 <= y1 < H and 0 <= x1 < W and not seen[y1, x1] and lod[y1, x1] > 0.5:
                seen[y1, x1] = True
                q.append((y1, x1))
    lod = seen.astype(np.float32)
    # pod strzałką rysunek nie pokazuje lodu – uzupełnij lód tam, gdzie strzałka go zakrywa (wypukła otoczka w pionie)
    pod = czerw > 0.5
    for x0 in range(W):
        col = np.nonzero(lod[:, x0] > 0.5)[0]
        if len(col):
            y_lo, y_hi = col.min(), col.max()
            m = pod[:, x0].copy(); m[:y_lo] = False; m[y_hi + 1:] = False
            lod[m, x0] = 1.0
    # domknięcie: wypełnia dziury po czarnym napisie leżącym na strzałce
    czerw = (G.rozmyj(czerw, 3) > 0.25).astype(np.float32)
    czerw = (G.rozmyj(czerw, 3) > 0.75).astype(np.float32)
    czerw = (G.rozmyj(czerw, 1) > 0.5).astype(np.float32)
    # usuń drobne czerwone punkty (kropka bieguna, groty strzałek żółtych)
    cz2 = G.rozmyj(czerw, 3)
    czerw = czerw * (cz2 > 0.45)

    def probka(mask, X, Y):
        """dwuliniowe próbkowanie maski rysunku w pikselach (X, Y)"""
        X = np.clip(X, 0, W - 1.001); Y = np.clip(Y, 0, H - 1.001)
        x0 = np.floor(X).astype(int); y0 = np.floor(Y).astype(int)
        fx = X - x0; fy = Y - y0
        return (mask[y0, x0] * (1 - fx) * (1 - fy) + mask[y0, x0 + 1] * fx * (1 - fy)
                + mask[y0 + 1, x0] * (1 - fx) * fy + mask[y0 + 1, x0 + 1] * fx * fy)

    # strzałka: obraz 1024² w układzie tarczy [-1,1]²; kanał R = maska, G = postęp od ogona do grotu
    N = 1024
    jj, ii = np.mgrid[0:N, 0:N]
    X = (ii + 0.5) / N * 2 - 1
    Y = 1 - (jj + 0.5) / N * 2
    m = probka(G.rozmyj(czerw, 1), RYS_CX + X * RYS_R, RYS_CY - Y * RYS_R)
    m = np.clip((m - 0.5) * 3 + 0.5, 0, 1)
    ogon = np.array(rys_na_tarcze(262, 160)); grot = np.array(rys_na_tarcze(118, 55))
    kier = grot - ogon
    s = ((X - ogon[0]) * kier[0] + (Y - ogon[1]) * kier[1]) / (kier @ kier)
    out = np.zeros((N, N, 4), np.float32)
    out[..., 0] = m
    out[..., 1] = np.clip(s, 0, 1)
    out[..., 3] = 1
    G.zapisz_png(out, p_strz)
    # lód: mapa równoodległościowa 2048×1024 (geograficznie), z rysunku przez rzut odwrotny
    Wl, Hl = 2048, 1024
    jj, ii = np.mgrid[0:Hl, 0:Wl]
    lon = (ii + 0.5) / Wl * 360 - 180
    lat = 90 - (jj + 0.5) / Hl * 180
    f0, l0 = math.radians(C_LAT), math.radians(C_LON)
    f, l = np.radians(lat), np.radians(lon)
    cc = np.clip(np.sin(f0) * np.sin(f) + np.cos(f0) * np.cos(f) * np.cos(l - l0), -1, 1)
    c = np.degrees(np.arccos(cc))
    yv = np.sin(l - l0) * np.cos(f)
    xv = np.cos(f0) * np.sin(f) - np.sin(f0) * np.cos(f) * np.cos(l - l0)
    az = np.arctan2(yv, xv) + math.radians(TETA)
    rr = c / CMAX
    PX = RYS_CX + rr * np.sin(az) * RYS_R
    PY = RYS_CY - rr * np.cos(az) * RYS_R
    ml = probka(G.rozmyj(lod, 1), PX, PY) * (rr < 0.97)
    out = np.zeros((Hl, Wl, 4), np.float32)
    out[..., 0] = out[..., 1] = out[..., 2] = np.clip((ml - 0.5) * 4 + 0.5, 0, 1)
    out[..., 3] = 1
    G.zapisz_png(out, p_lod)
    return p_strz, p_lod


# ---------------------------------------------------------------- scena
sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))
p_strz, p_lod = maski_z_rysunku()
img_lad = G.wczytaj_obraz(G.tekstura_ziemi(8192, (255, 255, 255), (0, 0, 0), "maska_lad"), nieliniowy=False)
img_lod = G.wczytaj_obraz(p_lod, nieliniowy=False)
img_strz = G.wczytaj_obraz(p_strz, nieliniowy=False)

# wektory geograficzne (stan końcowy = dzisiejszy układ współrzędnych)
U = G.ll2xyz(C_LAT, C_LON)
NP = Vector((0, 0, 1))
Nv = (NP - U * U.dot(NP)).normalized()          # północ w środku rzutu
Ev = Nv.cross(U).normalized()                    # wschód w środku rzutu
AKP = G.ll2xyz(*AKPATOK)
OS_PRZES = AKP.cross(NP).normalized()            # oś obrotu skorupy (leży w płaszczyźnie równika)
ALFA = AKP.angle(NP)                             # 30°: Akpatok -> oś obrotu
E1 = OS_PRZES.copy()                             # baza wokół Akpatok (do kresek okręgów)
E2 = AKP.cross(E1).normalized()

# kopuła (półkula) – na niej rysunek w rzucie azymutalnym
bpy.ops.mesh.primitive_uv_sphere_add(segments=256, ring_count=128, radius=1.0)
kop = bpy.context.active_object
kop.name = "Globus"
bm_del = [v for v in kop.data.vertices if v.co.z < -1e-4]
import bmesh
bm = bmesh.new(); bm.from_mesh(kop.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context="VERTS")
bm.to_mesh(kop.data); bm.free()
bpy.ops.object.shade_smooth()

mat = bpy.data.materials.new("Globus")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
W = Wezly(nt)
o = W.coord("Object")
x, y, _ = W.sep(o)
v2 = W.vec(x, y, 0.0)
rr = W.vmath("LENGTH", v2)
vr = W.obrot(v2, (0, 0, 1), math.radians(TETA))
xr, yr, _ = W.sep(vr)
c = W.mul(rr, math.radians(CMAX))
s = W.div(W.math("SINE", c), W.mx(rr, 1e-4))
d = W.vadd(W.vadd(W.scale(tuple(U), W.math("COSINE", c)), W.scale(tuple(Nv), W.mul(yr, s))), W.scale(tuple(Ev), W.mul(xr, s)))
kat = W.wartosc(-ALFA, "kat_skorupy")
p = W.obrot(d, tuple(OS_PRZES), kat)            # punkt skorupy widoczny w kierunku d
pxv, pyv, pzv = W.sep(p)
kier_tex = W.vec(pxv, W.mul(pyv, -1.0), pzv)    # konwencja tekstury środowiska Blendera
lad = W.srodowisko(img_lad, kier_tex)
lad = W.sep(lad)[0]
lod = W.sep(W.srodowisko(img_lod, kier_tex))[0]
a_lod = W.wartosc(1.0, "alfa_lodu")
lod = W.mul(lod, a_lod)

# morze: jaśniejsze w środku jak na rysunku
hl = W.vmath("DISTANCE", v2, (-0.12, 0.28, 0.0))
morze = W.mix(W.smooth(0.0, 1.05, hl), G.srgb((150, 218, 247)), G.srgb(G.MORZE_USKOK))
kol = W.mix(lad, morze, G.srgb(G.ZIELEN_USKOK))
lod_kol = W.mix(lad, G.srgb((236, 249, 255)), G.srgb((172, 222, 196)))
kol = W.mix(W.mul(lod, 0.97), kol, lod_kol)

# siatka sprzed 12 000 lat (porusza się ze skorupą): okręgi wokół Akpatok, kreskowane
a1 = W.dot(p, tuple(AKP))
kol_akp = W.math("ARCCOSINE", W.math("MINIMUM", W.math("MAXIMUM", a1, -1.0), 1.0))  # rad
fi = W.math("ARCTAN2", W.dot(p, tuple(E2)), W.dot(p, tuple(E1)))
a_stara = W.wartosc(1.0, "alfa_starej_siatki")


def kreski(fi_sock, ile):
    f = W.math("FRACT", W.mul(fi_sock, ile / (2 * math.pi)))
    return W.mul(W.smooth(0.08, 0.16, f), W.sub(1.0, W.smooth(0.52, 0.60, f)))


for stopnie, ile, grub, kolor_l, alfa_l in ((30, 60, 0.0028, (95, 95, 110), 0.75), (60, 104, 0.0028, (95, 95, 110), 0.75),
                                            (90, 120, 0.0042, (150, 85, 60), 0.95)):
    ln = W.linia(W.sub(kol_akp, math.radians(stopnie)), grub, 0.0016)
    ln = W.mul(W.mul(ln, kreski(fi, ile)), W.mul(a_stara, alfa_l))
    kol = W.mix(ln, kol, G.srgb(kolor_l))

# siatka dzisiejsza (stała w przestrzeni, oś obrotu się nie zmienia): ciągłe cienkie okręgi
_, _, dz = W.sep(d)
kol_np = W.math("ARCCOSINE", W.math("MINIMUM", W.math("MAXIMUM", dz, -1.0), 1.0))
a_dzis = W.wartosc(0.0, "alfa_dzisiejszej_siatki")
for stopnie, grub, alfa_l in ((30, 0.0022, 0.6), (60, 0.0022, 0.6), (90, 0.0030, 0.8)):
    ln = W.linia(W.sub(kol_np, math.radians(stopnie)), grub, 0.0014)
    ln = W.mul(ln, W.mul(a_dzis, alfa_l))
    kol = W.mix(ln, kol, G.srgb((45, 55, 70)))

# czerwona strzałka „Kierunek przesunięcia skorupy ziemskiej” (w układzie tarczy, nie jedzie ze skorupą)
uv_s = W.vec(W.add(W.mul(x, 0.5), 0.5), W.add(W.mul(y, 0.5), 0.5), 0.0)
st_col, _ = W.obraz(img_strz, uv_s, ext="CLIP")
st_m, st_s, _ = W.sep(st_col)
postep = W.wartosc(0.0, "postep_strzalki")
odkryte = W.sub(1.0, W.smooth(-0.03, 0.03, W.sub(st_s, postep)))
a_strz = W.mul(W.mul(st_m, odkryte), 0.93)
st_kol = W.mix(lad, G.srgb((210, 98, 90)), G.srgb((158, 66, 52)))
kol = W.mix(a_strz, kol, st_kol)

# bieguny: czerwona kropka = Akpatok (biegun poprzedni), czarna = dzisiejszy biegun (punkty skorupy)
for wek, kolor_k, nazwa in ((AKP, (200, 20, 20), "alfa_kropki_akp"), (NP, (10, 10, 10), "alfa_kropki_np")):
    kk = W.math("ARCCOSINE", W.math("MINIMUM", W.dot(p, tuple(wek)), 1.0))
    obw = W.sub(1.0, W.smooth(0.020, 0.024, kk))
    srd = W.sub(1.0, W.smooth(0.013, 0.017, kk))
    ak = W.wartosc(1.0, nazwa)
    kol = W.mix(W.mul(obw, ak), kol, G.srgb((255, 255, 255)))
    kol = W.mix(W.mul(srd, ak), kol, G.srgb(kolor_k))

# cieniowanie kuli (miękkie światło z lewej góry, jaśniejszy brzeg jak atmosfera)
nrm = W.norm(o)
sw = W.dot(nrm, tuple(Vector((-0.35, 0.45, 0.82)).normalized()))
cien = W.add(0.80, W.mul(W.mx(sw, 0.0), 0.24))
kol = W.vmath("MULTIPLY", kol, W.vec(cien, cien, cien))
_, _, nz = W.sep(nrm)
brzeg = W.math("POWER", W.sub(1.0, W.mx(nz, 0.0)), 3.0)
kol = W.mix(W.mul(brzeg, 0.45), kol, G.srgb((170, 225, 255)))
W.emisja_wyjscie(kol)
kop.data.materials.append(mat)

# poświata wokół globusa
bpy.ops.mesh.primitive_circle_add(vertices=128, radius=1.12, fill_type="TRIFAN", location=(0, 0, -0.02))
pos = bpy.context.active_object
pos.name = "Poswiata"
mp = bpy.data.materials.new("Poswiata")
mp.use_nodes = True
nt2 = mp.node_tree
nt2.nodes.clear()
W2 = Wezly(nt2)
o2 = W2.coord("Object")
r2 = W2.vmath("LENGTH", o2)
alfa2 = W2.mul(W2.sub(1.0, W2.smooth(0.98, 1.12, r2)), 0.55)
W2.emisja_wyjscie(G.srgb((70, 150, 230)), alfa2)
mp.surface_render_method = "BLENDED"
pos.data.materials.append(mp)

# kamera ortograficzna z góry; tarcza 400 px = 1 jednostka
cam = G.kamera((0, -(540 - CY) / RPX, 10), (0, -(540 - CY) / RPX, 0), orto=1920 / RPX)
cam.data.ortho_scale = 1920 / RPX * 1.035
cam.data.keyframe_insert("ortho_scale", frame=1)
cam.data.ortho_scale = 1920 / RPX
cam.data.keyframe_insert("ortho_scale", frame=300)
G.wygladz(cam.data)
G.tlo_kamery(cam, odl=20)

# ---------------------------------------------------------------- napisy (jak na rysunku)
ZOL = G.ZOLTY_LESZKA
p_np = px(*rzut(90, 0))
p_akp = px(*rzut(*AKPATOK))
print("[uskok] biegun dzisiejszy px", p_np, " Akpatok px", p_akp)
TS = 0.08  # wielkość liter (jednostki tarczy) ~ 32 px


def plaski(nazwa, verts, faces, kolor, z=1.35):
    me = bpy.data.meshes.new(nazwa)
    me.from_pydata([(vx, vy, z) for vx, vy in verts], [], faces)
    ob = bpy.data.objects.new(nazwa, me)
    sc.collection.objects.link(ob)
    m = G.material_emisja(nazwa + "_mat", kolor)
    me.materials.append(m)
    ob["mat"] = m.name
    return ob


def odcinek(nazwa, a, b, grub, kolor, grot=None):
    """Pasek od a do b (piksele) o grubości grub px; opcjonalnie grot strzałki w b."""
    A, B = swiat(*a), swiat(*b)
    d = (B - A); L = d.length; d.normalize()
    n = Vector((-d.y, d.x, 0)) * (grub / RPX / 2)
    koniec = B - d * (grot / RPX * 1.2 if grot else 0)
    verts = [(A + n).xy, (koniec + n).xy, (koniec - n).xy, (A - n).xy]
    faces = [(0, 1, 2, 3)]
    if grot:
        g = grot / RPX
        nn = Vector((-d.y, d.x, 0))
        verts += [(koniec + nn * g * 0.6).xy, B.xy, (koniec - nn * g * 0.6).xy]
        faces.append((4, 5, 6))
    return plaski(nazwa, [tuple(v) for v in verts], faces, kolor)


def etykieta(nazwa, tekst, poz, kolor, rozm=TS, wyr="LEFT", obrot=0.0, obrys=None):
    ob = G.napis(tekst, rozm, kolor, "arialb", wyr, loc=swiat(*poz, z=1.4), rot=(0, 0, math.radians(obrot)),
                 nazwa=nazwa, obrys=obrys, odstep=1.05)
    return ob


elementy = []  # (lista obiektów, klatka pojawienia się)

# „Położenie poprzedniego bieguna północnego” – lewa góra, podkreślenie i żółta strzałka do Akpatok
L1 = etykieta("Et_poprz", "Położenie poprzedniego\nbieguna północnego", (440, 92), (255, 255, 255))
l1a = odcinek("Pk_poprz", (440, 142), (735, 142), 4, ZOL)
l1b = odcinek("St_poprz", (735, 142), (p_akp[0] - 8, p_akp[1] - 6), 5, ZOL, grot=22)
elementy.append(([L1, l1a, l1b], 262))
# „Położenie dzisiejszego bieguna północnego” – prawa góra
L2 = etykieta("Et_dzis", "Położenie dzisiejszego\nbieguna północnego", (1480, 92), (255, 255, 255), wyr="RIGHT")
l2a = odcinek("Pk_dzis", (1480, 142), (1215, 142), 4, ZOL)
l2b = odcinek("St_dzis", (1215, 142), (p_np[0] + 7, p_np[1] - 8), 5, ZOL, grot=22)
elementy.append(([L2, l2a, l2b], 276))


# równiki: podpis wzdłuż linii (punkt linii najbliższy miejscu podpisu na rysunku)
def podpis_linii(nazwa, tekst, punkty_px, cel_px, kolor, przes=14, obrys=None):
    pts = [p for p in punkty_px if (p[0] - CX) ** 2 + (p[1] - CY) ** 2 < (0.93 * RPX) ** 2]
    i = min(range(1, len(pts) - 1), key=lambda k: (pts[k][0] - cel_px[0]) ** 2 + (pts[k][1] - cel_px[1]) ** 2)
    a, b = pts[i - 1], pts[i + 1]
    ang = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))
    if ang > 90: ang -= 180
    if ang < -90: ang += 180
    nx, ny = -math.sin(math.radians(ang)), -math.cos(math.radians(ang))  # w górę od linii (piksele)
    poz = (pts[i][0] + nx * przes, pts[i][1] + ny * przes)
    return etykieta(nazwa, tekst, poz, kolor, rozm=TS * 0.95, wyr="CENTER", obrot=ang, obrys=obrys)


rownik_dzis = [px(*rzut(0, lo)) for lo in np.linspace(-180, 180, 721)]
# równik sprzed 12 000 lat: okrąg 90° od Akpatok (stan końcowy)
rownik_stary = []
for k in range(721):
    t = 2 * math.pi * k / 720
    v = (E1 * math.cos(t) + E2 * math.sin(t)).normalized()
    rownik_stary.append(px(*rzut_wektor(v)))
cel_dzis = px(*rys_na_tarcze(128, 258))
cel_stary = px(*rys_na_tarcze(210, 228))
L3 = podpis_linii("Et_rownik_dzis", "Równik dzisiejszy", rownik_dzis, cel_dzis, (255, 255, 255))
L4 = podpis_linii("Et_rownik_stary", "Równik sprzed 12000 lat", rownik_stary, cel_stary, ZOL)
elementy.append(([L4], 236))
elementy.append(([L3], 250))
# „Kierunek przesunięcia skorupy ziemskiej” – czarny podpis przy strzałce (jak na rysunku)
kx, ky = px(*rys_na_tarcze(282, 113))
L5 = etykieta("Et_kierunek", "Kierunek przesunięcia\nskorupy ziemskiej", (1228, 352), (12, 12, 12), wyr="CENTER")
elementy.append(([L5], 120))

for obs, f0 in elementy:
    for ob in obs:
        if "mat" in ob:
            klucze = [(1, 0.0), (f0, 0.0), (f0 + 18, 1.0)]
            if ob.type == "FONT":
                G.alfa_napisu(ob, klucze)
            else:
                G.animuj_alfa(bpy.data.materials[ob["mat"]], klucze)

# ---------------------------------------------------------------- animacja skorupy
# 1–45: stan sprzed 12 000 lat (Akpatok na osi), 30–110: strzałka rośnie od ogona do grotu,
# 70–250: skorupa przesuwa się (wygładzony ruch), 110–200: pojawia się dzisiejsza siatka.
animuj_wartosc(nt, "postep_strzalki", [(30, -0.05), (110, 1.05)])
animuj_wartosc(nt, "kat_skorupy", [(70, -ALFA), (250, 0.0)])
animuj_wartosc(nt, "alfa_dzisiejszej_siatki", [(110, 0.0), (200, 1.0)])
animuj_wartosc(nt, "alfa_kropki_np", [(60, 0.0), (90, 1.0)])

G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
