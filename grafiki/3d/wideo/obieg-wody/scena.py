# -*- coding: utf-8 -*-
"""Klip „obieg-wody”: obieg wody w przyrodzie według opisu Leszka Klimka (rozdz. „Czy woda może być śladem?”).

Blok krajobrazu w przekroju: słony ocean – niziny – góry – kotlina bez odpływu. Kolejność jak w tekście:
parowanie wody z oceanu -> chmury („latające cysterny” słodkiej wody) niesione nad ląd -> deszcz, śnieg, grad ->
woda wsiąka w ziemię i zbiera się w warstwie wodonośnej -> źródło i rzeka spływająca do morza -> część wody
zatrzymuje się na warstwie nieprzepuszczalnej (glina, skała) w zbiorniku śródlądowym bez ujścia.
Schemat, nie mapa: krajobraz jest wymyślony, proporcje umowne.

Uruchomienie: S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/obieg-wody/scena.py
              ... -- --proba 1,150,300,450
"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
import schemat as S
from wezly import Wezly, animuj_wartosc

OPCJE = G.argumenty()
KLATKI = 450                       # 18 s
XB, YB, DNO = 7.0, 2.4, -1.6
JEZ = (4.9, 0.1)                   # środek kotliny bez odpływu
H_JEZ0, H_JEZ1 = 0.14, 0.32        # poziom jeziora przed deszczem i po nim
# czasy (klatki)
F_PAR = 12                         # parowanie
F_CHM0, F_CHM1 = 105, 232          # chmury płyną nad ląd
F_DESZCZ0, F_DESZCZ1 = 236, 338    # deszcz w górach
F_WSIAK = 258                      # woda wsiąka
F_RZEKA0, F_RZEKA1 = 300, 392      # rzeka od źródła do morza
F_JEZ0, F_JEZ1 = 350, 430          # deszcz nad kotliną, jezioro przybiera
ZLOTY = G.ZLOTY
SHIFT = 0.06

rng = np.random.default_rng(11)
FALE = [(rng.uniform(0.8, 4.0), rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi)) for _ in range(30)]


def szum(X, Y):
    s = np.zeros_like(np.asarray(X, float))
    for k, kier, faza in FALE:
        s = s + np.sin(k * (X * math.cos(kier) + Y * math.sin(kier)) + faza) / k
    return s / 6.0


def gl(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


# rzeka: od źródła na zboczu do wybrzeża; potok z gór do jeziora w kotlinie
def gladka_lamana(P, n=120):
    P = np.array(P, float)
    t = np.linspace(0, len(P) - 1, n)
    out = []
    for u in t:
        i = min(int(u), len(P) - 2)
        f = u - i
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3))
    return np.array(out)


RZEKA = gladka_lamana([(1.75, -0.15), (1.2, 0.3), (0.5, -0.15), (-0.3, 0.45), (-1.1, 0.1), (-1.9, 0.55), (-2.75, 0.4)])
POTOK = gladka_lamana([(3.45, 0.35), (3.85, 0.05), (4.3, 0.2)], 40)


def odl_od(X, Y, L):
    d = np.full(np.shape(X), 1e9)
    for (ax, ay), (bx, by) in zip(L[:-1], L[1:]):
        vx, vy = bx - ax, by - ay
        t = np.clip(((X - ax) * vx + (Y - ay) * vy) / (vx * vx + vy * vy + 1e-12), 0, 1)
        d = np.minimum(d, np.hypot(X - ax - t * vx, Y - ay - t * vy))
    return d


def wys(X, Y, koryta=True):
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    z = -0.9 + 1.3 * gl((X + 3.7) / 2.3)                                         # dno oceanu -> niziny
    z = z + 1.6 * np.exp(-((X - 2.6) / 1.4) ** 2) * (0.8 + 0.2 * np.cos(1.9 * Y + 0.5))   # góry
    z = z + 0.75 * gl((X - 5.7) / 1.3)                                           # próg za kotliną
    z = z - 0.45 * np.exp(-(((X - JEZ[0]) / 0.85) ** 2 + ((Y - JEZ[1]) / 1.25) ** 2))          # kotlina bez odpływu
    lad = gl((X + 2.6) / 1.2)
    gory = np.exp(-((X - 2.6) / 1.5) ** 2)
    z = z + szum(X, Y) * (0.03 + 0.05 * lad + 0.42 * gory) + 1.1 * gory * np.abs(szum(X * 1.7 + 2.0, Y * 1.7))
    if koryta:
        z = z - 0.07 * np.exp(-(odl_od(X, Y, RZEKA) / 0.16) ** 2) - 0.05 * np.exp(-(odl_od(X, Y, POTOK) / 0.14) ** 2)
    return z


sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))
S.swiatlo(kat=(52, 0, 35), sila=3.0, otoczenie=(165, 185, 225), moc=0.6)

# ---------------------------------------------------------------- teren
m_ter = bpy.data.materials.new("Teren")
m_ter.use_nodes = True
m_ter.node_tree.nodes.clear()
W = Wezly(m_ter.node_tree)
x, y, z = W.sep(W.geometria("Position"))
nz = W._node("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 3.5
nz.inputs["Detail"].default_value = 6.0
W.nt.links.new(W.geometria("Position"), nz.inputs["Vector"])
zz = W.add(z, W.mul(W.sub(nz.outputs[0], 0.5), 0.3))
kol = W.mix(W.smooth(-0.05, 0.1, z), G.srgb((196, 180, 130)), G.srgb((112, 158, 72)))     # piasek -> zieleń nizin
kol = W.mix(W.smooth(0.7, 1.3, zz), kol, G.srgb((128, 110, 92)))                            # skała
kol = W.mix(W.smooth(1.7, 2.0, zz), kol, G.srgb((244, 247, 252)))                         # śnieg
out = W._node("ShaderNodeOutputMaterial")
bs = W._node("ShaderNodeBsdfPrincipled")
W._in(bs.inputs["Base Color"], kol)
bs.inputs["Roughness"].default_value = 0.9
W.nt.links.new(bs.outputs[0], out.inputs["Surface"])
m_bok = S.mat("Bok", (96, 78, 62), 0.95)
teren = S.teren("Krajobraz", wys, -XB, XB, -YB, YB, 421, 145, DNO, m_ter, m_bok)

# przekrój od frontu: gleba, warstwa wodonośna, warstwa nieprzepuszczalna
xs = np.linspace(-XB, XB, 281)
pow_ = wys(xs, np.full_like(xs, -YB))
pow_gl = wys(xs, np.full_like(xs, -YB), koryta=False) - szum(xs, np.full_like(xs, -YB)) * 0.3
zA = np.minimum(pow_ - 0.12, 0.55 * pow_gl - 0.3)                 # strop warstwy wodonośnej
zB = zA - 0.45                                                     # strop warstwy nieprzepuszczalnej
g = np.exp(-((xs - JEZ[0]) / 1.1) ** 2)                            # pod kotliną glina podchodzi pod powierzchnię
zA = zA + (pow_ - 0.1 - zA) * g
zB = zB + (zA - 0.04 - zB) * g
zB = np.maximum(zB, DNO + 0.25)


def pas_przekroju(nazwa, dol, gora, kolor):
    v = [(float(a), -YB - 0.004, float(b)) for a, b in zip(xs, dol)] + [(float(a), -YB - 0.004, float(b)) for a, b in zip(xs, gora)]
    n = len(xs)
    f = [(k, k + 1, n + k + 1, n + k) for k in range(n - 1)]
    ob = S.siatka(nazwa, v, f, [S.mat(nazwa + "_mat", kolor, 0.95)])
    ob.visible_shadow = False
    return ob


pas_przekroju("Gleba", zA, pow_, (128, 96, 66))
pas_przekroju("Warstwa_wodonosna", zB, zA, (120, 168, 214))
pas_przekroju("Warstwa_nieprzepuszczalna", np.full_like(xs, DNO), zB, (104, 106, 114))


def w_przekroju(xv, z_tab):
    return float(np.interp(xv, xs, z_tab))


# ---------------------------------------------------------------- wody
m_ocean = S.mat("Ocean", (30, 104, 176), 0.12, alfa=0.9)
ocean = S.pudlo("Ocean", (-XB + (XB - 1.55) / 2 - 0.0, 0, -0.93), (XB - 1.55, 2 * YB - 0.002, 0.93), m_ocean)
ocean.location.x = (-XB + -1.55) / 2
ocean.visible_shadow = False

m_rzeka = S.mat("Rzeka", (52, 132, 214), 0.25, emisja=0.35)


def ciek(nazwa, L, f0, f1, grub):
    pts = [(float(a), float(b), float(wys(a, b)) + 0.012) for a, b in L]
    ob = S.linia(nazwa, pts, grub, m_rzeka, f0, f1)
    ob.visible_shadow = False
    return ob


ciek("Rzeka", RZEKA, F_RZEKA0, F_RZEKA1, 0.055)
ciek("Potok_do_jeziora", POTOK, F_JEZ0 - 12, F_JEZ0 + 30, 0.042)

m_jez = S.mat("Jezioro", (40, 116, 190), 0.12, alfa=0.92, emisja=0.2)
n_j = 48
jez = S.siatka("Jezioro", [(0, 0, 0)] + [(1.6 * math.cos(2 * math.pi * k / n_j), 2.1 * math.sin(2 * math.pi * k / n_j), 0) for k in range(n_j)],
               [(0, 1 + k, 1 + (k + 1) % n_j) for k in range(n_j)], [m_jez])
jez.visible_shadow = False
S.klucze(jez, "location", [(1, (JEZ[0], JEZ[1], H_JEZ0)), (F_JEZ0 + 8, (JEZ[0], JEZ[1], H_JEZ0)), (F_JEZ1, (JEZ[0], JEZ[1], H_JEZ1))])

# ---------------------------------------------------------------- parowanie: faliste smugi unoszące się znad oceanu
m_para = G.material_emisja("Para", (215, 235, 255), 0.5)
for seria, f_s in enumerate((F_PAR, F_PAR + 62)):
    for k in range(8):
        x0 = -6.4 + k * 0.5 + rng.uniform(-0.1, 0.1)
        y0 = rng.uniform(-1.6, 1.6)
        faza = rng.uniform(0, 6.28)
        pts = [(x0 + 0.13 * math.sin(4.2 * t + faza) + 0.25 * t, y0, 0.06 + 2.0 * t) for t in np.linspace(0, 1, 40)]
        ob = S.linia(f"Para_{seria}_{k}", pts, 0.042, m_para)
        ob.visible_shadow = False
        cu = ob.data
        cu.bevel_factor_mapping_start = cu.bevel_factor_mapping_end = "SPLINE"
        f0 = f_s + k * 3
        S.klucze(cu, "bevel_factor_end", [(f0, 0.0), (f0 + 44, 1.0)])
        S.klucze(cu, "bevel_factor_start", [(f0 + 22, 0.0), (f0 + 70, 1.0)])
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=f0)
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=f0 + 70)

# ---------------------------------------------------------------- chmury
m_chm = S.mat("Chmura", (250, 251, 255), 0.95, emisja=0.25)
S.animuj_gniazdo(m_chm, "Base Color", [(F_CHM1 - 20, G.srgb((250, 251, 255))), (F_CHM1 + 8, G.srgb((176, 184, 198))),
                                       (F_JEZ1 - 10, G.srgb((176, 184, 198))), (KLATKI, G.srgb((236, 240, 248)))])
S.animuj_gniazdo(m_chm, "Emission Strength", [(F_CHM1 - 20, 0.25), (F_CHM1 + 8, 0.08)])
CHMURY = [  # (start nad oceanem, cel nad górami, skala, opóźnienie)
    ((-5.1, 0.35, 2.75), (1.2, 0.5, 3.0), 0.85, 0),
    ((-3.9, -1.0, 2.55), (2.6, -0.9, 3.05), 0.75, 10),
    ((-4.5, 1.25, 2.9), (3.6, 1.0, 3.1), 0.75, 18),
]
chmury = []
for n, (a, b, sk, op) in enumerate(CHMURY):
    e = S.polacz(bpy.data.objects.new(f"Chmura_{n}", None))
    for k in range(9):
        r = rng.uniform(0.3, 0.52)
        p = (rng.uniform(-0.75, 0.75), rng.uniform(-0.4, 0.4), rng.uniform(-0.08, 0.22) + (0.12 if abs(k - 4) < 2 else 0))
        kl = S.kula(f"Chmura_{n}_{k}", p, r, m_chm, seg=20)
        kl.scale = (1.15, 1.0, 0.72)
        kl.parent = e
        kl.visible_shadow = False
    kl_loc = [(1, a), (F_CHM0 + op, a), (F_CHM1 + op // 2, b)]
    if n == 2:   # trzecia chmura płynie dalej, nad kotlinę
        kl_loc += [(F_DESZCZ1 - 30, b), (F_JEZ0 - 6, (JEZ[0] + 0.1, JEZ[1] + 0.2, 2.5))]
    S.klucze(e, "location", kl_loc)
    S.klucze(e, "scale", [(1, (0.12 * sk,) * 3), (22 + op, (0.12 * sk,) * 3), (F_CHM0 + op, (sk, sk, sk))])
    chmury.append(e)

# ---------------------------------------------------------------- deszcz (kreski opadające w pętli)
def deszcz(nazwa, x0, x1, y0, y1, z_gora, f0, f1, ile=90, okres=1.2, klatek=13):
    m = bpy.data.materials.new(nazwa + "_mat")
    m.use_nodes = True
    m.node_tree.nodes.clear()
    Wd = Wezly(m.node_tree)
    _, _, zw = Wd.sep(Wd.geometria("Position"))
    moc = Wd.wartosc(0.0, "moc")
    a = Wd.mul(Wd.mul(Wd.math("LESS_THAN", zw, z_gora), moc), 0.8)
    Wd.emisja_wyjscie(G.srgb((196, 224, 255)), a)
    m.surface_render_method = "BLENDED"
    animuj_wartosc(m.node_tree, "moc", [(f0 - 1, 0.0), (f0 + 10, 1.0), (f1 - 12, 1.0), (f1, 0.0)])
    v, f = [], []
    for _ in range(ile):
        px, py, pz = rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(0, okres)
        for kz in range(-1, int(z_gora / okres) + 2):
            zb = pz + kz * okres
            n = len(v)
            for dx, dy in ((0.014, 0), (0, 0.014)):
                n = len(v)
                v += [(px - dx, py - dy, zb), (px + dx, py + dy, zb), (px + dx, py + dy, zb + 0.17), (px - dx, py - dy, zb + 0.17)]
                f.append((n, n + 1, n + 2, n + 3))
    ob = S.siatka(nazwa, v, f, [m])
    ob.visible_shadow = False
    ob.location = (0, 0, 0)
    ob.keyframe_insert("location", frame=f0)
    ob.location = (0, 0, -okres)
    ob.keyframe_insert("location", frame=f0 + klatek)
    for fc in G._fcurves(ob.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
        fc.modifiers.new("CYCLES")
    return ob


deszcz("Deszcz_gory", 0.6, 4.1, -1.55, 1.6, 2.85, F_DESZCZ0, F_DESZCZ1, ile=240)
deszcz("Deszcz_kotlina", JEZ[0] - 0.8, JEZ[0] + 0.8, JEZ[1] - 0.6, JEZ[1] + 0.7, 2.4, F_JEZ0, F_JEZ1, ile=70)

# ---------------------------------------------------------------- woda wsiąka (strzałki na przekroju) i płynie warstwą wodonośną
m_wsiak = S.mat("Wsiakanie", (36, 110, 220), 0.4, emisja=0.9)


def ukryj_do(ob, f0):
    """przed klatką f0 obiektu nie ma w kadrze (spłaszczona strzałka byłaby widoczna jako kreska)"""
    ob.hide_render = True
    ob.keyframe_insert("hide_render", frame=1)
    ob.hide_render = False
    ob.keyframe_insert("hide_render", frame=f0)


for k, xv in enumerate((1.0, 1.55, 2.1, 2.65, 3.2)):
    a = Vector((xv, -YB - 0.03, w_przekroju(xv, pow_) - 0.06))
    b = Vector((xv - 0.12, -YB - 0.03, w_przekroju(xv, zA) - 0.2))
    st = S.strzalka(f"Wsiak_{k}", a, b, 0.022, m_wsiak, grot=0.07)
    st.visible_shadow = False
    S.pojaw(st, F_WSIAK + k * 6, 26, os_z=True)
    ukryj_do(st, F_WSIAK + k * 6)
a = Vector((1.7, -YB - 0.03, w_przekroju(1.7, zA) - 0.24))
b = Vector((-0.6, -YB - 0.03, w_przekroju(-0.6, zA) - 0.22))
st = S.strzalka("Przeplyw_podziemny", a, b, 0.024, m_wsiak, grot=0.08)
st.visible_shadow = False
S.pojaw(st, F_WSIAK + 36, 30, os_z=True)
ukryj_do(st, F_WSIAK + 36)

# ---------------------------------------------------------------- kamera
cam = G.kamera((0, -30, 14), (0, 0, 0), lens=50)
cam.data.shift_y = -SHIFT
cam.data.clip_start, cam.data.clip_end = 3.0, 250.0


def tor(f):
    d = (f - 1) / (KLATKI - 1)
    t = G.gladko(d)
    return (-102 + 22 * t, 23 + 5 * t, 30.5 - 2.0 * t)


S.orbita_f(cam, (0.0, 0.0, 0.9), tor, KLATKI)
G.tlo_kamery(cam, odl=160)

# ---------------------------------------------------------------- podpisy (kolejność jak w tekście)
OBR = ((8, 12, 24), 0.05)
BIALY = (255, 255, 255)
R = 0.4
S.podpis("słony ocean", R, (190, 225, 255), (-5.2, -1.2, 0.3), cam, 6, obrys=OBR)
S.podpis("parowanie", R, BIALY, (-6.2, 0.2, 1.45), cam, F_PAR + 8, obrys=OBR)
t = S.podpis("„latające cysterny”" + chr(10) + "słodkiej wody", R, BIALY, (0, 0, 1.05), cam, F_CHM0 - 28, obrys=OBR, nazwa="Pod_cysterny")
t.parent = chmury[0]
t.scale = (1, 1, 1)
S.podpis("deszcz, śnieg, grad", R, BIALY, (-0.5, -0.6, 2.3), cam, F_DESZCZ0 + 6, obrys=OBR)
S.podpis("woda wsiąka w ziemię", R * 0.92, BIALY, (3.9, -YB - 0.9, 0.55), cam, F_WSIAK + 6, obrys=OBR)
S.podpis("warstwa wodonośna", R * 0.92, (190, 225, 255), (-1.2, -YB - 0.9, w_przekroju(-1.2, zA) - 0.2), cam, F_WSIAK + 40, obrys=OBR)
S.podpis("warstwa nieprzepuszczalna (glina, skała)", R * 0.92, (226, 228, 235), (2.6, -YB - 0.9, DNO + 0.42), cam, F_WSIAK + 52, obrys=OBR)
zr = RZEKA[0]
S.podpis("źródło", R, BIALY, (zr[0] - 0.35, zr[1] - 0.2, float(wys(zr[0], zr[1])) + 0.45), cam, F_RZEKA0 + 4, obrys=OBR)
rz = RZEKA[len(RZEKA) * 2 // 3]
S.podpis("rzeka", R, BIALY, (rz[0], rz[1] - 0.5, float(wys(rz[0], rz[1])) + 0.42), cam, F_RZEKA0 + 50, obrys=OBR)
S.podpis("jezioro bez odpływu", R, ZLOTY, (JEZ[0] + 0.1, JEZ[1] - 2.2, 1.3), cam, F_JEZ0 + 30, obrys=OBR)

G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
