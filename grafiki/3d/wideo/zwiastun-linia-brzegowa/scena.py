# -*- coding: utf-8 -*-
"""
Linia brzegowa po wielkim uskoku: pod wodą i pod ziemią (zwiastun, odcinek 0 „Wstęp”).

Lektor: „Jeśli jednak uwzględnić hipotezę Hapgooda o możliwości zaistnienia wielkiego uskoku skorupy ziemskiej
i przyjąć, że taki zaistniał w przeszłości i to niejednokrotnie, to zmiany w ukształtowaniu terenu mogą być bardzo
znaczne, a co za tym idzie, wiele „rzeczy” opisywanych przez starożytnych może znajdować się pod wodą,
a niektóre zniknęły pod ziemią naniesioną przez wielkie tsunami.”

HIPOTEZA z tekstu (nauka nie potwierdza gwałtownych przesunięć skorupy). Makieta wycinka wybrzeża:
1) brzeg z dwiema budowlami – jedna tuż nad morzem, druga w głębi lądu, złota linia = linia brzegowa;
2) uskok: ląd pochyla się ku morzu, woda wchodzi w głąb lądu, pierwsza budowla zostaje pod wodą;
3) wielka fala przechodzi przez nowy brzeg i zostawia warstwę ziemi, która przykrywa drugą budowlę.
Makieta jest umowna: nie przedstawia konkretnego miejsca, skala pionowa jest przesadzona.

Uruchomienie:
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-linia-brzegowa/scena.py -- --proba 30,130,230,330,450
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-linia-brzegowa/scena.py
"""
import bpy, bmesh, math, os, sys, random
import numpy as np
from mathutils import Vector, noise

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, "..", "_wspolne"))
import globus as G, zwiastun as Z

opcje = G.argumenty()
NKL = 450  # 18 s
sc = Z.start(NKL, opcje, probki=48)
Z.swiat((5, 7, 14), (30, 46, 84), moc=0.9)
random.seed(8)

# oś czasu (klatki)
K_USKOK = (62, 190)        # ląd pochyla się ku morzu
K_FALA = (268, 360)        # przejście wielkiej fali
K_NANOS = (312, 376)       # narastanie warstwy naniesionej ziemi

XL, XP, YP, DNO = -20.0, 20.0, 12.0, -7.0     # wymiary makiety
X_BRZEG = -6.0                                 # dawny brzeg
KAT_USKOKU = math.radians(5.0)                 # pochylenie lądu (oś obrotu przy prawej krawędzi makiety)
A_XY, B_XY = (-3.4, -2.5), (9.0, 1.5)          # budowla nad morzem i budowla w głębi lądu


def meander(y):
    return 1.2 * math.sin(y * 0.27) + 0.5 * math.sin(y * 0.71 + 1.0)


def wys(x, y):
    """Wysokość terenu przed uskokiem (0 = poziom morza)."""
    xx = x - meander(y)
    n = noise.noise(Vector((x * 0.16, y * 0.16, 0.3)))
    if xx < X_BRZEG:
        h = -0.24 * (X_BRZEG - xx) ** 1.08 + 0.05 * n
    else:
        h = 0.16 * (xx - X_BRZEG) + 0.10 * n
        w = max(0.0, min(1.0, (xx - 11.0) / 6.0))
        h += w * w * (3 - 2 * w) * (1.2 + 1.6 * abs(noise.noise(Vector((x * 0.2, y * 0.2, 4.0)))))
    for (ax, ay), r in ((A_XY, 2.0), (B_XY, 2.4)):          # wyrównane place pod budowlami
        d = math.hypot(x - ax, y - ay)
        if d < r:
            t = min(1.0, max(0.0, (r - d) / (r * 0.45)))
            h = h * (1 - t) + wys_placu(ax, ay) * t
    return h


def wys_placu(ax, ay):
    return 0.16 * (ax - meander(ay) - X_BRZEG)


# ---------------------------------------------------------------- materiały
def mat_teren():
    m = Z.pbr("teren", (112, 132, 76), szorstkosc=0.9)
    nt = m.node_tree
    b = Z.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, G.srgb((150, 136, 104))      # dno morza
    el[1].position, el[1].color = 1.0, G.srgb((150, 150, 132))      # wzgórza
    for pos, kol in ((0.46, (196, 180, 134)), (0.52, (214, 198, 150)), (0.58, (130, 150, 82)), (0.8, (96, 124, 66))):
        e = el.new(pos)
        e.color = G.srgb(kol)
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[1].default_value = -4.0
    mr.inputs[2].default_value = 4.0
    nt.links.new(sep.outputs[2], mr.inputs[0])
    nt.links.new(mr.outputs[0], ramp.inputs[0])
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 1.6
    n.inputs["Detail"].default_value = 8.0
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    mm = nt.nodes.new("ShaderNodeMapRange")
    mm.inputs[3].default_value = 0.78
    mm.inputs[4].default_value = 1.15
    nt.links.new(n.outputs[0], mm.inputs[0])
    nt.links.new(mm.outputs[0], hsv.inputs["Value"])
    nt.links.new(ramp.outputs[0], hsv.inputs["Color"])
    nt.links.new(hsv.outputs[0], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.2
    nt.links.new(n.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], b.inputs["Normal"])
    return m


def mat_przekroj():
    """Ściany makiety: warstwy ziemi i skał (pasy według wysokości, lekko pofalowane)."""
    m = Z.pbr("przekroj", (120, 96, 70), szorstkosc=0.85)
    nt = m.node_tree
    b = Z.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 0.25
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    ad = nt.nodes.new("ShaderNodeMath")
    ad.operation = "MULTIPLY_ADD"
    ad.inputs[1].default_value = 1.6
    nt.links.new(n.outputs[0], ad.inputs[0])
    nt.links.new(sep.outputs[2], ad.inputs[2])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[1].default_value = DNO
    mr.inputs[2].default_value = 5.0
    nt.links.new(ad.outputs[0], mr.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, G.srgb((78, 70, 68))
    el[1].position, el[1].color = 0.92, G.srgb((120, 96, 66))
    for pos, kol in ((0.2, (98, 84, 74)), (0.36, (126, 104, 82)), (0.5, (104, 86, 70)), (0.64, (146, 120, 88)),
                     (0.78, (116, 94, 70))):
        e = el.new(pos)
        e.color = G.srgb(kol)
    nt.links.new(mr.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
    return m


M_TEREN, M_PRZEKROJ = mat_teren(), mat_przekroj()
M_WODA = Z.pbr("woda", (20, 96, 150), szorstkosc=0.08, alfa=0.62)
M_KAMIEN = Z.kamien("kamien_budowli", (226, 214, 186), (180, 166, 136), skala=3.0, wypuklosc=0.4)
M_NANOS = Z.kamien("nanos", (134, 100, 64), (96, 72, 48), skala=1.2, wypuklosc=0.6)
M_NANOS.surface_render_method = "BLENDED"
Z.bsdf(M_NANOS).inputs["Alpha"].default_value = 0.8
M_FALA = Z.pbr("fala", (36, 122, 172), szorstkosc=0.15, alfa=0.9)
_nt = M_FALA.node_tree
_tc = _nt.nodes.new("ShaderNodeTexCoord")
_sp = _nt.nodes.new("ShaderNodeSeparateXYZ")
_nt.links.new(_tc.outputs["Object"], _sp.inputs[0])
_ns = _nt.nodes.new("ShaderNodeTexNoise")
_ns.inputs["Scale"].default_value = 2.5
_nt.links.new(_tc.outputs["Object"], _ns.inputs["Vector"])
_ad = _nt.nodes.new("ShaderNodeMath")
_ad.operation = "MULTIPLY_ADD"
_ad.inputs[1].default_value = 0.5
_nt.links.new(_ns.outputs[0], _ad.inputs[0])
_nt.links.new(_sp.outputs[2], _ad.inputs[2])
_rp = _nt.nodes.new("ShaderNodeValToRGB")
_rp.color_ramp.elements[0].position = 0.78
_rp.color_ramp.elements[0].color = G.srgb((36, 122, 172))
_rp.color_ramp.elements[1].position = 1.12
_rp.color_ramp.elements[1].color = (1, 1, 1, 1)
_nt.links.new(_ad.outputs[0], _rp.inputs[0])
_nt.links.new(_rp.outputs[0], Z.bsdf(M_FALA).inputs["Base Color"])
_nt.links.new(_rp.outputs[0], Z.bsdf(M_FALA).inputs["Emission Color"])
Z.bsdf(M_FALA).inputs["Emission Strength"].default_value = 0.3
# nanos widać tylko za czołem fali (wartość „czoło” jest animowana) i zanika przy krawędziach płata
_nt = M_NANOS.node_tree
_tc = _nt.nodes.new("ShaderNodeTexCoord")
_sp = _nt.nodes.new("ShaderNodeSeparateXYZ")
_nt.links.new(_tc.outputs["Object"], _sp.inputs[0])
CZOLO = _nt.nodes.new("ShaderNodeValue")
CZOLO.label = "czolo"


def _zakres(x, a, b_, c, d):
    n = _nt.nodes.new("ShaderNodeMapRange")
    n.interpolation_type = "SMOOTHSTEP"
    for i, v in ((0, x), (1, a), (2, b_), (3, c), (4, d)):
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            _nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def _mnoz(a, b_):
    n = _nt.nodes.new("ShaderNodeMath")
    n.operation = "MULTIPLY"
    for i, v in ((0, a), (1, b_)):
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            _nt.links.new(v, n.inputs[i])
    return n.outputs[0]


_roz = _nt.nodes.new("ShaderNodeMath")
_roz.operation = "SUBTRACT"
_nt.links.new(CZOLO.outputs[0], _roz.inputs[0])
_nt.links.new(_sp.outputs[0], _roz.inputs[1])
_alfa = _mnoz(_mnoz(_zakres(_roz.outputs[0], -0.6, 0.8, 0.0, 0.86), _zakres(_sp.outputs[0], 1.5, 4.5, 0.0, 1.0)),
              _zakres(_sp.outputs[0], 15.5, 17.5, 1.0, 0.0))
_nt.links.new(_alfa, Z.bsdf(M_NANOS).inputs["Alpha"])

# ---------------------------------------------------------------- teren (z bocznymi ścianami)
teren_root = Z.pusty("Lad", (XP, 0, 0))       # oś pochylenia: prawa krawędź makiety


def do_ladu(ob):
    """Przypina obiekt do lądu (współrzędne obiektu są podane w układzie makiety)."""
    ob.parent = teren_root
    ob.location = Vector(ob.location) - Vector((XP, 0, 0))
    return ob


KROK = 0.25
NXX, NYY = int((XP - XL) / KROK), int(2 * YP / KROK)
H = np.zeros((NXX + 1, NYY + 1))
for i in range(NXX + 1):
    for j in range(NYY + 1):
        H[i, j] = wys(XL + i * KROK, -YP + j * KROK)
verts, faces, idx = [], [], []
for i in range(NXX + 1):
    for j in range(NYY + 1):
        verts.append((XL + i * KROK, -YP + j * KROK, H[i, j]))
vi = lambda i, j: i * (NYY + 1) + j
for i in range(NXX):
    for j in range(NYY):
        faces.append((vi(i, j), vi(i + 1, j), vi(i + 1, j + 1), vi(i, j + 1)))
        idx.append(0)


def sciana(lista):
    """Ściana boczna pod łamaną wierzchołków powierzchni (indeksy w kolejności obiegu)."""
    b0 = len(verts)
    for k in lista:
        x, y, _ = verts[k]
        verts.append((x, y, DNO))
    for a in range(len(lista) - 1):
        faces.append((lista[a + 1], lista[a], b0 + a, b0 + a + 1))
        idx.append(1)


sciana([vi(i, 0) for i in range(NXX, -1, -1)])            # przód (y = -YP)
sciana([vi(i, NYY) for i in range(NXX + 1)])              # tył
sciana([vi(0, j) for j in range(NYY + 1)])                # od morza
sciana([vi(NXX, j) for j in range(NYY, -1, -1)])          # od lądu
teren = Z.siatka("Teren", verts, faces, [M_TEREN, M_PRZEKROJ], idx, gladka=True)
do_ladu(teren)

# ---------------------------------------------------------------- woda: bryła o stałym poziomie (z = 0)
woda = Z.prostopadloscian("Woda", (XP - XL - 0.04, 2 * YP - 0.04, -DNO - 0.02), (0, 0, DNO / 2 - 0.01), M_WODA)
woda.visible_shadow = False

# ---------------------------------------------------------------- budowle
def megality(x, y, z):
    """Budowla nad morzem: platforma i krąg słupów z nadprożami."""
    cz = [Z.prostopadloscian("Platforma", (2.6, 1.8, 0.16), (x, y, z + 0.08), M_KAMIEN, faza=0.02)]
    for sx in (-1.0, -0.33, 0.33, 1.0):
        for sy in (-0.62, 0.62):
            cz.append(Z.prostopadloscian("Slup", (0.24, 0.24, 0.8), (x + sx, y + sy, z + 0.56), M_KAMIEN, faza=0.02))
    for sy in (-0.62, 0.62):
        cz.append(Z.prostopadloscian("Nadproze", (2.4, 0.28, 0.16), (x, y + sy, z + 1.04), M_KAMIEN, faza=0.02))
    return cz


def piramida(x, y, z):
    """Budowla w głębi lądu: piramida schodkowa."""
    cz = []
    for k, a in enumerate((2.6, 2.05, 1.5, 0.95)):
        cz.append(Z.prostopadloscian("Stopien", (a, a, 0.3), (x, y, z + 0.15 + 0.3 * k), M_KAMIEN, faza=0.02))
    cz.append(Z.prostopadloscian("Swiatynia", (0.5, 0.5, 0.26), (x, y, z + 1.33), M_KAMIEN, faza=0.02))
    return cz


ZA, ZB = wys_placu(*A_XY), wys_placu(*B_XY)
for ob in megality(A_XY[0], A_XY[1], ZA) + piramida(B_XY[0], B_XY[1], ZB):
    do_ladu(ob)

# ---------------------------------------------------------------- złota linia dawnego brzegu (leży na terenie)
pts = []
for j in range(0, NYY + 1, 2):
    y = -YP + j * KROK
    pts.append((X_BRZEG + meander(y), y, 0.06))
do_ladu(Z.linia(pts, 0.07, G.ZLOTY, "DawnyBrzeg"))

# ---------------------------------------------------------------- warstwa naniesiona przez falę (rośnie kluczem kształtu)
def nanos():
    i0, i1 = int((1.5 - XL) / KROK), int((17.5 - XL) / KROK)
    v, f = [], []
    gr = []
    for i in range(i0, i1 + 1):
        for j in range(NYY + 1):
            x, y = XL + i * KROK, -YP + j * KROK
            v.append((x, y, H[i, j] + 0.02))
            t = (i - i0) / (i1 - i0)
            brz = min(1.0, t / 0.2) * min(1.0, (1 - t) / 0.25)
            brz = brz * brz * (3 - 2 * brz)
            # grubość: najwięcej w obniżeniach, do ok. 1,9 nad placem piramidy
            g = brz * (1.75 + 0.35 * noise.noise(Vector((x * 0.3, y * 0.3, 2.0))))
            cel_z = max(H[i, j] + 0.02, ZB + g * (1.0 - 0.45 * max(0.0, H[i, j] - ZB - 0.6)))
            gr.append(cel_z)
    n = NYY + 1
    for a in range(i1 - i0):
        for j in range(NYY):
            f.append((a * n + j, (a + 1) * n + j, (a + 1) * n + j + 1, a * n + j + 1))
    b0 = len(v)
    for a in range(i1 - i0 + 1):                 # dolna krawędź fartucha: zostaje na terenie
        v.append((v[a * n][0], v[a * n][1], v[a * n][2] - 0.02))
        gr.append(v[a * n][2] - 0.02)
    for a in range(i1 - i0):
        f.append((b0 + a, b0 + a + 1, (a + 1) * n, a * n))
    ob = Z.siatka("Nanos", v, f, [M_NANOS], gladka=True)
    ob.shape_key_add(name="Baza")
    sk = ob.shape_key_add(name="Gruba")
    for k, z in enumerate(gr):
        sk.data[k].co.z = z
    return ob, sk


ob_nanos, sk_nanos = nanos()
do_ladu(ob_nanos)
ob_nanos.visible_shadow = False
for f_, w in ((1, 0.0), (K_NANOS[0], 0.0), (K_NANOS[1], 1.0)):
    sk_nanos.value = w
    sk_nanos.keyframe_insert("value", frame=f_)
G.wygladz(ob_nanos.data.shape_keys)
for f_, x_ in ((1, 0.0), (K_FALA[0] + 48, 0.5), (K_FALA[0] + 72, 9.5), (K_FALA[1], 16.5), (K_FALA[1] + 14, 19.5)):
    CZOLO.outputs[0].default_value = x_
    CZOLO.outputs[0].keyframe_insert("default_value", frame=f_)
G.wygladz(M_NANOS.node_tree)

# ---------------------------------------------------------------- uskok: pochylenie lądu ku morzu
for f_, a in ((1, 0.0), (K_USKOK[0], 0.0), (K_USKOK[1], -KAT_USKOKU)):
    teren_root.rotation_euler = (0, a, 0)
    teren_root.keyframe_insert("rotation_euler", frame=f_)
G.wygladz(teren_root)

# ---------------------------------------------------------------- wielka fala: wał wody idący od morza w głąb lądu
def wal():
    v, f = [], []
    NP, NY = 28, 48
    for j in range(NY + 1):
        y = -YP + 0.05 + (2 * YP - 0.1) * j / NY
        przes = 0.7 * math.sin(y * 0.3) + 0.4 * noise.noise(Vector((y * 0.4, 0, 0)))
        for k in range(NP + 1):
            t = k / NP
            x = -4.2 + 6.0 * t                      # łagodny grzbiet z tyłu, strome czoło z przodu
            z = math.exp(-((x - 0.6) / (1.7 if x < 0.6 else 0.55)) ** 2)
            v.append((x + przes, y, z))
    for j in range(NY):
        for k in range(NP):
            a = j * (NP + 1) + k
            f.append((a, a + 1, a + NP + 2, a + NP + 1))
    return Z.siatka("WielkaFala", v, f, [M_FALA], gladka=True)


fala = wal()
fala.visible_shadow = False
for f_, x, z, s in ((K_FALA[0], -19.0, 0.0, 0.5), (K_FALA[0] + 30, -8.0, 0.0, 1.7), (K_FALA[0] + 52, 2.0, 0.05, 1.9),
                    (K_FALA[0] + 72, 9.0, 1.2, 1.4), (K_FALA[1], 15.5, 2.9, 0.25)):
    fala.location = (x, 0, z)
    fala.scale = (1, 1, s)
    fala.keyframe_insert("location", frame=f_)
    fala.keyframe_insert("scale", frame=f_)
G.wygladz(fala)
fala.hide_render = True
fala.keyframe_insert("hide_render", frame=1)
fala.hide_render = False
fala.keyframe_insert("hide_render", frame=K_FALA[0])
fala.hide_render = True
fala.keyframe_insert("hide_render", frame=K_FALA[1] + 1)

# ---------------------------------------------------------------- kamera (z lekkim drżeniem podczas uskoku)
cam = G.kamera((-8, -48, 24), (0, 0, -1), lens=34)
cel = Z.pusty("Cel")
Z.lot_kamery(cam, cel, [
    (1, (-13.0, -47.0, 21.0), (-1.0, 0.0, -4.4)),
    (200, (-6.0, -48.5, 22.5), (0.0, 0.0, -4.6)),
    (450, (4.0, -48.0, 23.5), (0.8, 0.0, -4.8)),
])
drz = Z.pusty("Drzenie")
cel.parent = drz
for f_ in range(K_USKOK[0], K_USKOK[1] + 14, 2):
    t = (f_ - K_USKOK[0]) / (K_USKOK[1] - K_USKOK[0])
    amp = 0.16 * math.sin(math.pi * min(1.0, t)) ** 0.7 if t <= 1 else 0.0
    drz.location = (random.uniform(-amp, amp), 0, random.uniform(-amp, amp))
    drz.keyframe_insert("location", frame=f_)


# ---------------------------------------------------------------- podpisy (przodem do kamery)
def tablica(tekst, rozm, loc, kolor=G.ZLOTY, kroj="georgiab", pojaw=None, znik=None):
    ob = G.napis(tekst, rozm, kolor, kroj, "CENTER", loc=loc, obrys=((6, 9, 18), rozm * 0.05))
    ob.constraints.new("COPY_ROTATION").target = cam
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
tablica("linia brzegowa", 1.25, (X_BRZEG - 1.5, 3.0, 4.2), pojaw=10, znik=118)
Z.linia([(X_BRZEG - 1.0, 3.0, 3.3), (X_BRZEG + meander(3.0), 3.0, 0.2)], 0.035, G.ZLOTY, "Odn1", pojaw=(10, 26), alfa=1.0)
G.animuj_alfa(bpy.data.materials["Odn1_mat"], [(1, 0.0), (10, 0.0), (26, 1.0), (118, 1.0), (134, 0.0)])
tablica("wielki uskok skorupy ziemskiej", 1.6, (0.0, 8.0, 8.2), BIALY, "georgia", pojaw=72, znik=188)
tablica("dawna linia brzegowa", 0.9, (X_BRZEG - 5.8, -5.0, 2.6), G.ZLOTY, "georgia", pojaw=206)
Z.linia([(X_BRZEG - 4.6, -5.0, 2.0), (X_BRZEG - 0.9, -5.0, -2.2)], 0.03, G.ZLOTY, "Odn2", pojaw=(206, 222), alfa=0.9)
tablica("pod wodą", 1.45, (A_XY[0] - 0.5, A_XY[1], 4.6), pojaw=258)
Z.linia([(A_XY[0] - 0.4, A_XY[1], 3.6), (A_XY[0], A_XY[1], -0.4)], 0.04, G.ZLOTY, "Odn3", pojaw=(258, 274))
tablica("pod ziemią naniesioną\nprzez wielkie tsunami", 1.3, (B_XY[0] + 1.0, B_XY[1], 8.0), pojaw=372)
Z.linia([(B_XY[0] + 0.6, B_XY[1], 6.2), (B_XY[0], B_XY[1], 2.9)], 0.04, G.ZLOTY, "Odn4", pojaw=(372, 388))

# ---------------------------------------------------------------- światło
Z.slonce((0.5, 0.62, -0.6), moc=3.6, kolor=(1.0, 0.93, 0.82), kat=4.0)
Z.slonce((-0.6, 0.2, -0.5), moc=0.8, kolor=(0.6, 0.72, 1.0), kat=30.0, cien=False)

G.renderuj(DIR, opcje, kadr_klatka=450)
