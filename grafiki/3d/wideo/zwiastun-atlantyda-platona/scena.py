# -*- coding: utf-8 -*-
"""
Stolica Atlantydy według opisu Platona (zwiastun, odcinek 0 „Wstęp”).

Lektor: „Atlantyda istniała naprawdę, ale nikt nie kwapi się z jej odszukaniem…”

HIPOTEZA. Nikt nie znalazł Atlantydy; klip odtwarza wyłącznie to, co Platon zapisał w dialogu „Kritias” (113c–117e):
wyspa środkowa o średnicy 5 stadiów, wokół niej na przemian pierścienie wody (1, 2 i 3 stadia) i lądu (2 i 3 stadia),
kanał do morza długi na 50 stadiów i szeroki na 3 pletry, mosty szerokie na pletr, mury kryte mosiądzem, cyną
i orichalkiem, świątynia Posejdona długa na stadion i szeroka na 3 pletry, tor wyścigów konnych szeroki na stadion
na większym pierścieniu lądu, mur miejski w odległości 50 stadiów od największego pierścienia.
Układ domów, kolory pól, wysokości i kształty budowli są umowne (Platon ich nie podaje).

Skala: 1 jednostka = 1 stadion (ok. 180 m, tak jak przelicza Leszek). Morze leży na południu (-Y).

Uruchomienie:
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-atlantyda-platona/scena.py -- --proba 1,150,300,450
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-atlantyda-platona/scena.py
"""
import bpy, bmesh, math, os, sys, random
import numpy as np
from mathutils import Vector

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, "..", "_wspolne"))
import globus as G, zwiastun as Z

opcje = G.argumenty()
NKL = 450  # 18 s
sc = Z.start(NKL, opcje, probki=40, ekspozycja=0.0)
Z.swiat((52, 92, 160), (244, 206, 168), moc=1.0)
# lekka mgiełka powietrza: dal blednie ku barwie nieba (bryła mgły nad ziemią, nie objętość świata –
# objętość świata gasi słońce i tło)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 22))
_mg = bpy.context.active_object
_mg.name = "Mgla"
_mg.scale = (1500, 1500, 44)
_mm = bpy.data.materials.new("mgla")
_mm.use_nodes = True
_mm.node_tree.nodes.clear()
_vo = _mm.node_tree.nodes.new("ShaderNodeOutputMaterial")
_vs = _mm.node_tree.nodes.new("ShaderNodeVolumeScatter")
_vs.inputs["Density"].default_value = 0.0022
_vs.inputs["Anisotropy"].default_value = 0.4
_vs.inputs["Color"].default_value = (1.0, 0.92, 0.84, 1)
_mm.node_tree.links.new(_vs.outputs[0], _vo.inputs["Volume"])
_mg.data.materials.append(_mm)
_mg.visible_shadow = False
for _k, _v in (("volumetric_end", 700.0), ("volumetric_samples", 96), ("volumetric_tile_size", "4"),
               ("use_volumetric_shadows", False)):
    try:
        setattr(sc.eevee, _k, _v)
    except Exception as e:
        print("[eevee]", _k, e)
random.seed(11)
RNG = np.random.default_rng(11)

# promienie według Platona (stadia)
R_WYSPA = 2.5
R_W1, R_L1, R_W2, R_L2, R_W3 = 3.5, 5.5, 7.5, 10.5, 13.5
D_KANAL, S_KANAL = 50.0, 0.5          # długość kanału i szerokość (3 pletry = pół stadionu)
R_MUR = R_W3 + D_KANAL                # mur miejski 50 stadiów od największego pierścienia
PLETR = 1.0 / 6.0
H_ROWNINA, H_PIERSC, H_WYSPA = 0.07, 0.10, 0.13
X_MOST = 0.0                          # droga i mosty biegną w osi kanału


def brzeg(x):
    """Linia brzegu morza (y w funkcji x): styczna do muru miejskiego przy ujściu kanału."""
    return -R_MUR - 0.0016 * x * x


# ---------------------------------------------------------------- materiały
def mat_woda():
    m = Z.pbr("woda", (14, 74, 122), szorstkosc=0.16)
    nt = m.node_tree
    b = Z.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 2.2
    n.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(n.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], b.inputs["Normal"])
    return m


def mat_pola(nazwa, kolory, skala, szorstkosc=0.9):
    """Szachownica pól: komórki Voronoi w losowych odcieniach z listy `kolory`."""
    m = Z.pbr(nazwa, kolory[0], szorstkosc)
    nt = m.node_tree
    b = Z.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = skala
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(vor.outputs["Color"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    el = ramp.color_ramp.elements
    el[0].position = 0.0
    el[0].color = G.srgb(kolory[0])
    el[1].position = 1.0 / len(kolory)
    el[1].color = G.srgb(kolory[1])
    for i, k in enumerate(kolory[2:], start=2):
        e = el.new(i / len(kolory))
        e.color = G.srgb(k)
    nt.links.new(sep.outputs[0], ramp.inputs[0])
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = skala * 6
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    mm = nt.nodes.new("ShaderNodeMapRange")
    mm.inputs[3].default_value = 0.82
    mm.inputs[4].default_value = 1.12
    nt.links.new(n.outputs[0], mm.inputs[0])
    nt.links.new(mm.outputs[0], hsv.inputs["Value"])
    nt.links.new(ramp.outputs[0], hsv.inputs["Color"])
    nt.links.new(hsv.outputs[0], b.inputs["Base Color"])
    return m


M_WODA = mat_woda()
M_ROWNINA = mat_pola("rownina", [(158, 146, 112), (150, 140, 104), (166, 152, 118), (146, 138, 108)], 0.5)
M_DALEKO = mat_pola("lad_daleki", [(104, 124, 70), (122, 136, 78), (160, 152, 96), (94, 114, 66), (138, 142, 86)], 0.22)
M_PIERSC = mat_pola("pierscien", [(134, 146, 92), (116, 134, 80), (164, 154, 116), (108, 126, 76)], 2.0)
M_SKALA = Z.kamien("skala_brzegu", (168, 150, 122), (116, 96, 76), skala=2.0, wypuklosc=0.6)
M_TOR = Z.pbr("tor", (196, 168, 120), szorstkosc=0.95)
M_DROGA = Z.pbr("droga", (214, 204, 182), szorstkosc=0.9)
M_BIALY = Z.pbr("kamien_bialy", (232, 226, 212), szorstkosc=0.8)
M_CZARNY = Z.pbr("kamien_czarny", (52, 50, 54), szorstkosc=0.75)
M_CZERWONY = Z.pbr("kamien_czerwony", (160, 92, 70), szorstkosc=0.8)
M_MOSIADZ = Z.pbr("mosiadz", (214, 172, 72), szorstkosc=0.28, metal=1.0)
M_CYNA = Z.pbr("cyna", (206, 212, 218), szorstkosc=0.3, metal=1.0)
M_ORICHALK = Z.pbr("orichalk", (236, 120, 62), szorstkosc=0.25, metal=1.0, emisja=(255, 96, 40), moc_emisji=0.25)
M_SREBRO = Z.pbr("srebro", (226, 230, 236), szorstkosc=0.22, metal=1.0)
M_ZLOTO = Z.pbr("zloto", (255, 200, 80), szorstkosc=0.22, metal=1.0, emisja=(255, 190, 70), moc_emisji=0.15)
M_MUR = Z.pbr("mur_miejski", (206, 196, 176), szorstkosc=0.85)
M_DREWNO = Z.pbr("okret", (98, 62, 38), szorstkosc=0.7)

# ---------------------------------------------------------------- woda
bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(M_WODA)


# ---------------------------------------------------------------- bryły obrotowe
def pierscien(nazwa, r0, r1, z0, z1, mats, seg=360, kopula=0.0, mat_bok=None):
    """Pierścień lądu (r0 = 0 daje dysk): wierzch + ściana zewnętrzna + wewnętrzna. mats = [wierzch, bok]."""
    nr = max(2, int((r1 - r0) / 0.25))
    verts, faces, idx = [], [], []
    rs = [r0 + (r1 - r0) * i / nr for i in range(nr + 1)]
    for r in rs:
        for k in range(seg):
            a = 2 * math.pi * k / seg
            z = z1 + kopula * (1 - (r / r1) ** 2)
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(nr):
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
            idx.append(0)
    b0 = len(verts)
    for r in (r0, r1):
        for k in range(seg):
            a = 2 * math.pi * k / seg
            verts.append((r * math.cos(a), r * math.sin(a), z0))
    for k in range(seg):
        k2 = (k + 1) % seg
        faces.append((nr * seg + k, nr * seg + k2, b0 + seg + k2, b0 + seg + k))  # ściana zewnętrzna
        idx.append(1)
        if r0 > 0:
            faces.append((k2, k, b0 + k, b0 + k2))                              # ściana wewnętrzna
            idx.append(1)
    return Z.siatka(nazwa, verts, faces, mats, idx, gladka=True)


pierscien("WyspaSrodkowa", 0.0, R_WYSPA, -0.3, H_WYSPA, [M_PIERSC, M_SKALA], kopula=0.06)
pierscien("PierscienLadu1", R_W1, R_L1, -0.3, H_PIERSC, [M_PIERSC, M_SKALA])
pierscien("PierscienLadu2", R_W2, R_L2, -0.3, H_PIERSC, [M_PIERSC, M_SKALA])
# tor wyścigów konnych: szeroki na stadion, dookoła większego pierścienia
pierscien("TorWyscigow", 8.5, 9.5, H_PIERSC - 0.01, H_PIERSC + 0.004, [M_TOR, M_TOR])


# równina wokół pierścieni z wyciętym kanałem (kanał ma proste, równoległe brzegi x = ±S_KANAL/2)
def rownina():
    seg = 720
    rs = [R_W3, 14, 15, 16.5, 18.5, 21, 24, 28, 33, 39, 46, 53, 59, R_MUR]
    verts, faces, idx = [], [], []
    for r in rs:
        d = math.asin(S_KANAL / 2 / r)
        for k in range(seg + 1):
            a = -math.pi / 2 + d + (2 * math.pi - 2 * d) * k / seg
            verts.append((r * math.cos(a), r * math.sin(a), H_ROWNINA))
    n = seg + 1
    for i in range(len(rs) - 1):
        for k in range(seg):
            faces.append((i * n + k, i * n + k + 1, (i + 1) * n + k + 1, (i + 1) * n + k))
            idx.append(0)
    b0 = len(verts)
    for k in range(seg + 1):       # ściana od strony zewnętrznego pierścienia wody
        x, y, _ = verts[k]
        verts.append((x, y, -0.3))
    for k in range(seg):
        faces.append((k + 1, k, b0 + k, b0 + k + 1))
        idx.append(1)
    for kk in (0, seg):            # brzegi kanału
        b1 = len(verts)
        for i in range(len(rs)):
            x, y, _ = verts[i * n + kk]
            verts.append((x, y, -0.3))
        for i in range(len(rs) - 1):
            q = (i * n + kk, (i + 1) * n + kk, b1 + i + 1, b1 + i)
            faces.append(q if kk == seg else q[::-1])
            idx.append(1)
    return Z.siatka("Rownina", verts, faces, [M_ROWNINA, M_SKALA], idx)


rownina()


# ląd poza murem miejskim (do brzegu morza), w pasach co 1 stadion
def lad_daleki():
    verts, faces = [], []
    XMAX, YMAX = 520, 520

    def pas(x0, x1, f_dol, f_gora):
        b = len(verts)
        verts.extend([(x0, f_dol(x0), H_ROWNINA), (x1, f_dol(x1), H_ROWNINA), (x1, f_gora(x1), H_ROWNINA),
                      (x0, f_gora(x0), H_ROWNINA)])
        faces.append((b, b + 1, b + 2, b + 3))

    okr = lambda x: math.sqrt(max(0.0, R_MUR * R_MUR - x * x))
    x = -XMAX
    while x < XMAX:
        krok = 1.0 if abs(x) < R_MUR + 2 else 8.0
        x1 = min(XMAX, x + krok)
        if abs(x) >= R_MUR and abs(x1) >= R_MUR and x * x1 > 0:
            pas(x, x1, brzeg, lambda t: YMAX)
        else:
            a, b_ = max(-R_MUR, x), min(R_MUR, x1)
            pas(a, b_, brzeg, lambda t: -okr(t))
            pas(a, b_, okr, lambda t: YMAX)
        x = x1
    return Z.siatka("LadDaleki", verts, faces, [M_DALEKO])


lad_daleki()

# ---------------------------------------------------------------- mury
pierscien("MurMosiadz", R_L2 - 0.1, R_L2 - 0.02, H_PIERSC, H_PIERSC + 0.13, [M_MOSIADZ, M_MOSIADZ])
pierscien("MurCyna", R_L1 - 0.1, R_L1 - 0.02, H_PIERSC, H_PIERSC + 0.13, [M_CYNA, M_CYNA])
pierscien("MurOrichalk", R_WYSPA - 0.1, R_WYSPA - 0.02, H_WYSPA, H_WYSPA + 0.15, [M_ORICHALK, M_ORICHALK])
pierscien("MurMiejski", R_MUR - 0.3, R_MUR, H_ROWNINA, H_ROWNINA + 0.3, [M_MUR, M_MUR], seg=720)
# złote ogrodzenie świętego miejsca pośrodku wyspy
pierscien("OgrodzenieZlote", 0.24, 0.28, H_WYSPA + 0.05, H_WYSPA + 0.14, [M_ZLOTO, M_ZLOTO], seg=64)


# ---------------------------------------------------------------- pudełka (domy, wieże, mosty) w jednej siatce
class Pudelka:
    def __init__(s):
        s.v, s.f = [], []

    def dodaj(s, x, y, z0, sx, sy, sz, rot=0.0, dach=0.0):
        c, si = math.cos(rot), math.sin(rot)
        b = len(s.v)
        for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            px, py = dx * sx / 2, dy * sy / 2
            s.v.append((x + px * c - py * si, y + px * si + py * c, z0))
        for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            px, py = dx * sx / 2, dy * sy / 2
            s.v.append((x + px * c - py * si, y + px * si + py * c, z0 + sz))
        s.f += [(b + 4, b + 5, b + 6, b + 7), (b, b + 1, b + 5, b + 4), (b + 1, b + 2, b + 6, b + 5),
                (b + 2, b + 3, b + 7, b + 6), (b + 3, b, b + 4, b + 7)]
        if dach:   # dach dwuspadowy wzdłuż osi x
            g = len(s.v)
            for dx in (-1, 1):
                px = dx * sx / 2
                s.v.append((x + px * c, y + px * si, z0 + sz + dach))
            s.f += [(b + 4, b + 5, g + 1, g), (b + 6, b + 7, g, g + 1), (b + 5, b + 6, g + 1), (b + 7, b + 4, g)]

    def obiekt(s, nazwa, mat):
        return Z.siatka(nazwa, s.v, s.f, [mat])


domy = {"b": Pudelka(), "c": Pudelka(), "r": Pudelka()}


def los_dom():
    return domy[random.choices("bcr", weights=(62, 10, 28))[0]]


def w_drodze(x, y, pol=0.5):
    """Czy punkt leży w pasie drogi/kanału (oś y, strona południowa i północna)."""
    return abs(x - X_MOST) < pol


# miasto między zewnętrznym pierścieniem wody a murem: gęsta zabudowa, promieniste ulice
r = R_W3 + 0.7
while r < R_MUR - 1.0:
    krok = 0.44 + 0.009 * (r - R_W3)
    nk = int(2 * math.pi * r / krok)
    for k in range(nk):
        a = 2 * math.pi * (k + random.uniform(-0.2, 0.2)) / nk
        if k % 16 == 0 or random.random() < 0.2:   # ulice promieniste i wolne place
            continue
        rr = r + random.uniform(-0.12, 0.12)
        x, y = rr * math.cos(a), rr * math.sin(a)
        if abs(x) < 0.9 and y < 0:      # kanał z nabrzeżami
            continue
        los_dom().dodaj(x, y, H_ROWNINA, krok * random.uniform(0.45, 0.72), krok * random.uniform(0.4, 0.62),
                        random.uniform(0.04, 0.09), rot=a + math.pi / 2, dach=random.choice((0, 0, 0.02)))
    r += krok * 1.08

# pierścienie lądu: świątynie, ogrody, koszary – domy luźniej (poza torem wyścigów)
for r0, r1 in ((R_W1 + 0.25, R_L1 - 0.3), (R_W2 + 0.25, 8.35), (9.65, R_L2 - 0.3)):
    r = r0
    while r < r1:
        nk = int(2 * math.pi * r / 0.42)
        for k in range(nk):
            a = 2 * math.pi * (k + random.uniform(-0.2, 0.2)) / nk
            x, y = r * math.cos(a), r * math.sin(a)
            if random.random() < 0.45 or (abs(x - X_MOST) < 0.28):
                continue
            los_dom().dodaj(x, y, H_PIERSC, random.uniform(0.16, 0.3), random.uniform(0.12, 0.2),
                            random.uniform(0.04, 0.09), rot=a + math.pi / 2, dach=random.choice((0, 0.02)))
        r += 0.36

# wyspa środkowa: pałac królewski (kilka większych gmachów)
for (x, y, sx, sy, sz, rot) in ((-1.25, 0.55, 0.8, 0.4, 0.14, 0.2), (-1.1, -0.75, 0.6, 0.45, 0.12, -0.3),
                                 (1.3, 0.9, 0.7, 0.35, 0.12, 0.5), (1.35, -0.7, 0.55, 0.5, 0.13, 0.1),
                                 (0.2, 1.6, 0.9, 0.3, 0.1, 0.0), (-0.3, -1.65, 0.8, 0.3, 0.1, 0.0)):
    domy["b"].dodaj(x, y, H_WYSPA + 0.02, sx, sy, sz, rot=rot, dach=0.04)

domy["b"].obiekt("DomyBiale", M_BIALY)
domy["c"].obiekt("DomyCzarne", M_CZARNY)
domy["r"].obiekt("DomyCzerwone", M_CZERWONY)

# świątynia Posejdona: długa na stadion, szeroka na 3 pletry; ściany srebrne, szczyty złote
sw = Pudelka()
sw.dodaj(0.0, 0.62, H_WYSPA + 0.055, 1.0, 0.5, 0.26, rot=0.0, dach=0.0)
sw.obiekt("SwiatyniaPosejdona", M_SREBRO)
dach = Pudelka()
dach.dodaj(0.0, 0.62, H_WYSPA + 0.055 + 0.26, 1.06, 0.56, 0.02, dach=0.12)
dach.obiekt("SwiatyniaDach", M_ZLOTO)
schody = Pudelka()
schody.dodaj(0.0, 0.62, H_WYSPA + 0.03, 1.16, 0.66, 0.03)
schody.obiekt("SwiatyniaStopnie", M_BIALY)

# ---------------------------------------------------------------- droga, mosty, bramy z wieżami
mosty, wieze, droga = Pudelka(), Pudelka(), Pudelka()
SZER_MOSTU = PLETR
for (ra, rb, za, zb) in ((R_WYSPA, R_W1, H_WYSPA, H_PIERSC), (R_L1, R_W2, H_PIERSC, H_PIERSC),
                         (R_L2, R_W3, H_PIERSC, H_ROWNINA)):
    ym = -(ra + rb) / 2
    # pomost i filary; pod mostem zostaje przepływ dla okrętów
    mosty.dodaj(X_MOST, ym, max(za, zb) + 0.02, SZER_MOSTU, (rb - ra) + 0.3, 0.03, rot=0.0)
    for t in (0.25, 0.5, 0.75):
        mosty.dodaj(X_MOST, -(ra + (rb - ra) * t), -0.2, SZER_MOSTU * 0.9, 0.06, max(za, zb) + 0.22)
    for rr, zz in ((ra - 0.12, za), (rb + 0.12, zb)):   # bramy z dwiema wieżami na każdym końcu mostu
        for sx in (-1, 1):
            wieze.dodaj(X_MOST + sx * 0.16, -rr, zz, 0.12, 0.14, 0.3)
mosty.obiekt("Mosty", M_BIALY)
wieze.obiekt("WiezeBram", M_CZERWONY)
# droga od świątyni przez pierścienie
for (ya, yb, zz) in ((-R_WYSPA, 0.3, H_WYSPA + 0.062), (-R_L1, -R_W1, H_PIERSC), (-R_L2, -R_W2, H_PIERSC)):
    droga.dodaj(X_MOST, (ya + yb) / 2, zz, SZER_MOSTU, abs(yb - ya), 0.012)
droga.obiekt("Droga", M_DROGA)
# wieże przy ujściu kanału do morza
uj = Pudelka()
for sx in (-1, 1):
    uj.dodaj(sx * 0.75, -R_MUR + 0.2, H_ROWNINA, 0.5, 0.5, 0.7)
uj.obiekt("WiezeUjscia", M_MUR)

# okręty w kanale i w portach (bez ludzi – same kadłuby)
okr = Pudelka()
for i in range(26):
    y = -R_W3 - 2 - i * 1.8 + random.uniform(-0.5, 0.5)
    okr.dodaj(random.choice((-0.11, 0.11)), y, 0.0, 0.035, 0.2, 0.03)
for i in range(60):
    rr = random.choice((random.uniform(R_L2 + 0.4, R_W3 - 0.4), random.uniform(R_L1 + 0.3, R_W2 - 0.3)))
    a = random.uniform(0, 2 * math.pi)
    okr.dodaj(rr * math.cos(a), rr * math.sin(a), 0.0, 0.2, 0.035, 0.03, rot=a + math.pi / 2)
okr.obiekt("Okrety", M_DREWNO)

# ---------------------------------------------------------------- kamera
cam = G.kamera((0, -100, 30), (0, 0, 0), lens=35)
cam.data.clip_start, cam.data.clip_end = 0.1, 4000
cel = Z.pusty("Cel")
Z.lot_kamery(cam, cel, [
    (1, (16.0, -118.0, 22.0), (0.0, -30.0, 0.0)),
    (150, (17.0, -64.0, 19.0), (0.0, -8.0, 0.0)),
    (300, (24.0, -30.0, 16.0), (0.5, -0.5, 0.0)),
    (450, (30.0, -17.0, 14.0), (0.8, -0.8, 0.0)),
])


# ---------------------------------------------------------------- podpisy (zawsze przodem do kamery)
def tablica(tekst, rozm, loc, kolor=G.ZLOTY, kroj="georgiab", pojaw=None, znik=None):
    ob = G.napis(tekst, rozm, kolor, kroj, "CENTER", loc=loc, obrys=((8, 12, 22), rozm * 0.04))
    con = ob.constraints.new("COPY_ROTATION")
    con.target = cam
    for o in [ob] + list(ob.children):
        o.visible_shadow = False
    kl = []
    if pojaw:
        kl += [(1, 0.0), (pojaw, 0.0), (pojaw + 16, 1.0)]
    if znik:
        kl += [(znik, 1.0), (znik + 16, 0.0)]
    if kl:
        G.alfa_napisu(ob, kl)
    return ob


BIALY = (246, 242, 232)
tablica("kanał do morza: 50 stadiów (ok. 9 km)", 2.3, (-10.0, -46.0, 5.0), pojaw=18, znik=100)
tablica("mur miejski", 1.7, (22.0, -60.0, 3.0), BIALY, "georgia", pojaw=30, znik=95)

# miarka wzdłuż promienia (na wschód): szerokości kolejnych pierścieni w stadiach
Z_M = 0.75
granice = [0.0, R_WYSPA, R_W1, R_L1, R_W2, R_L2, R_W3]
Z.linia([(-R_WYSPA, 0, Z_M), (R_W3, 0, Z_M)], 0.03, G.ZLOTY, "Miarka", pojaw=(232, 250))
for x in [-R_WYSPA] + granice[1:]:
    Z.linia([(x, 0, Z_M + 0.22), (x, 0, 0.16)], 0.02, G.ZLOTY, "MiarkaKreska", pojaw=(232, 250), alfa=0.85)
for xs, t in ((0.0, "5"), (3.0, "1"), (4.5, "2"), (6.5, "2"), (9.0, "3"), (12.0, "3")):
    tablica(t, 1.0, (xs, 0, Z_M + 0.85), G.ZLOTY, "georgiab", pojaw=240)
tablica("szerokości w stadiach\n(1 stadion to ok. 180 m)", 1.15, (-4.5, 17.5, 4.2), BIALY, "georgia", pojaw=252)
tablica("woda", 0.62, (3.0, 0, Z_M + 1.95), (150, 205, 255), "arialb", pojaw=262)
tablica("ląd", 0.62, (4.5, 0, Z_M + 1.95), (190, 220, 140), "arialb", pojaw=262)
tablica("woda", 0.62, (6.5, 0, Z_M + 1.95), (150, 205, 255), "arialb", pojaw=262)
tablica("ląd", 0.62, (9.0, 0, Z_M + 1.95), (190, 220, 140), "arialb", pojaw=262)
tablica("woda", 0.62, (12.0, 0, Z_M + 1.95), (150, 205, 255), "arialb", pojaw=262)
tablica("świątynia Posejdona", 0.8, (-3.4, 3.2, 4.4), BIALY, "georgia", pojaw=330)
Z.linia([(-3.0, 2.9, 3.85), (0.0, 0.62, 0.6)], 0.02, BIALY, "Odnosnik", pojaw=(330, 346), alfa=0.9)

# ---------------------------------------------------------------- światło: niskie słońce z południowego zachodu
Z.slonce((0.8, 0.5, -0.36), moc=5.0, kolor=(1.0, 0.84, 0.64), kat=1.5)
Z.slonce((-0.5, 0.5, -0.6), moc=0.6, kolor=(0.6, 0.72, 1.0), kat=30.0, cien=False)

G.renderuj(DIR, opcje, kadr_klatka=450)
