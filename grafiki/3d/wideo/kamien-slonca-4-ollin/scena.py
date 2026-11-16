# -*- coding: utf-8 -*-
"""
Klip „kamien-slonca-4-ollin” do odcinka 2 „Wielki uskok…” (rozdz. 01).

Aztecki Kamień Słońca w 3D. Płaskorzeźba powstaje z fotografii kamienia z Wikimedia Commons
(„Piedra del Sol en MNA.jpg”, Juan Carlos Fonseca Mata, CC BY-SA 4.0): zdjęcie jest prostowane do koła
(fotografia zrobiona lekko od dołu), z jasności powstaje mapa wysokości, a z niej siatka 3D.
Kamera powoli krąży, kolejno świecą cztery poprzednie Słońca (kwadraty znaku Ollin: 4 Jaguar, 4 Wiatr,
4 Deszcz, 4 Woda), na końcu cały znak 4-Ollin – piąte Słońce, „Słońce Ruchu”.
Układ znaku taki jak na rysunku Leszka zrodlo/webacja/02uskok/ollin.gif („Aztecki znak Ollin – trzęsienie”).

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/kamien-slonca-4-ollin/scena.py
  ... -- --proba 1,120,300,400     (tylko kadry próbne PNG do _klatki/)
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G

FOTO = os.path.join(G.DANE, "kamien-slonca", "Piedra_del_Sol_en_MNA.jpg")
KLATEK = 400  # 16 s
opcje = G.argumenty()

# ---------------------------------------------------------------- tekstury (numpy, cache w %TEMP%)
N = 2048
KOLOR = os.path.join(G.CACHE, "kamien_kolor_v1.png")
WYS = os.path.join(G.CACHE, "kamien_wys_v1.npy")
MASKI = os.path.join(G.CACHE, "kamien_maski_v1.png")
MASKA_OLLIN = os.path.join(G.CACHE, "kamien_ollin_v1.png")

# Środki czterech kwadratów (poprzednich Słońc) na wyprostowanym zdjęciu, w promieniach tarczy (u w prawo, v w górę).
# Odczytane z siatki na zdjęciu; układ zgodny z rysunkiem Leszka ollin.gif.
KWADRATY = {
    "jaguar": (0.222, 0.267),   # prawy górny: 4 Jaguar (Nahui Ocelotl) – I Słońce
    "wiatr": (-0.217, 0.278),   # lewy górny: 4 Wiatr (Nahui Ehecatl) – II Słońce
    "deszcz": (-0.228, -0.222), # lewy dolny: 4 Deszcz ognia (Nahui Quiahuitl) – III Słońce
    "woda": (0.233, -0.233),    # prawy dolny: 4 Woda (Nahui Atl) – IV Słońce
}
R_TWARZ = 0.21                  # krąg twarzy w środku znaku
R_TARCZY = 0.985                # krawędź tarczy na wyprostowanym zdjęciu


def przygotuj_tekstury():
    if all(os.path.exists(p) for p in (KOLOR, WYS, MASKI, MASKA_OLLIN)):
        return
    a = G.obraz_numpy(FOTO)[..., :3]          # H×W×3, sRGB 0–1, wiersz 0 = góra
    H0, W0 = a.shape[:2]
    f = W0 / 1000.0
    # prostowanie: punkty dobrane na podglądzie 1000 px (środek twarzy, krawędzie tarczy)
    cx, cy, rx, top, bot, kx = 548.5, 392.0, 436.0, 22.0, 822.0, 0.03
    A = ((bot - cy) + (cy - top)) / 2
    B = ((bot - cy) - (cy - top)) / 2
    g = (np.arange(N) + 0.5) / N * 2 - 1
    X, Y = np.meshgrid(g, g)                   # Y w dół
    xs = (cx + X * rx * (1 + kx * Y)) * f
    ys = (cy + Y * (A + B * Y)) * f
    x0 = np.clip(np.floor(xs).astype(int), 0, W0 - 2)
    y0 = np.clip(np.floor(ys).astype(int), 0, H0 - 2)
    fx = np.clip(xs - x0, 0, 1)[..., None]
    fy = np.clip(ys - y0, 0, 1)[..., None]
    o = (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy)
         + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy)
    rgba = np.concatenate([o, np.ones(o.shape[:2] + (1,), np.float32)], axis=2)
    G.zapisz_png(rgba, KOLOR, "kamien_kolor")
    # wysokość: jasność bez dużych plam światła (filtr górnoprzepustowy), lekko wygładzona
    L = o[..., 0] * 0.3 + o[..., 1] * 0.55 + o[..., 2] * 0.15
    duze = G.rozmyj(G.zmniejsz(L, 4), 6)
    duze = np.repeat(np.repeat(duze, 4, 0), 4, 1)
    hp = G.rozmyj(L - duze, 1)
    lo, hi = np.percentile(hp, 2), np.percentile(hp, 98)
    h = np.clip((hp - lo) / (hi - lo), 0, 1)
    np.save(WYS, h.astype(np.float32))
    # maski: R,G,B,A = cztery kwadraty; osobno cały znak Ollin (kwadraty + twarz)
    U, V = np.meshgrid(g, -g)
    def blob(cu, cv):
        e = np.maximum(np.abs(U - cu), np.abs(V - cv)) / 0.105
        d = (np.abs(U - cu) + np.abs(V - cv)) / 0.15
        k = np.maximum(e, d)
        return np.clip((1.12 - k) / 0.2, 0, 1)
    m = np.zeros((N, N, 4), np.float32)
    for i, key in enumerate(("jaguar", "wiatr", "deszcz", "woda")):
        m[..., i] = blob(*KWADRATY[key])
    G.zapisz_png(m, MASKI, "kamien_maski")
    r = np.hypot(U, V)
    tw = np.clip((R_TWARZ + 0.015 - r) / 0.03, 0, 1)
    ol = np.maximum(m.max(axis=2), tw)
    G.zapisz_png(np.dstack([ol, ol, ol, np.ones_like(ol)]), MASKA_OLLIN, "kamien_ollin")


przygotuj_tekstury()

# ---------------------------------------------------------------- scena
sc = G.nowa_scena(KLATEK)
sc.eevee.taa_render_samples = int(os.environ.get("USKOK3D_PROBKI", "32"))
try:
    sc.eevee.use_shadows = True
except Exception:
    pass

RM = 1.79                 # promień tarczy w metrach (średnica kamienia 3,58 m)
S = RM / R_TARCZY         # metry na jednostkę u/v zdjęcia
GLEB = 0.055              # głębokość płaskorzeźby (m)

# siatka biegunowa tarczy, wysokość próbkowana z mapy
h = np.load(WYS)
NR, NS = 520, 1400
me = bpy.data.meshes.new("Tarcza")
rs = np.linspace(0, 1, NR + 1)[1:]
ts = np.linspace(0, 2 * math.pi, NS, endpoint=False)
RR, TT = np.meshgrid(rs, ts, indexing="ij")
uu = (RR * np.cos(TT)).ravel() * R_TARCZY
vv = (RR * np.sin(TT)).ravel() * R_TARCZY
uu = np.concatenate([[0.0], uu]); vv = np.concatenate([[0.0], vv])
px = np.clip(((uu + 1) / 2 * N).astype(int), 0, N - 1)
py = np.clip(((1 - vv) / 2 * N).astype(int), 0, N - 1)
hh = h[py, px]
rr = np.hypot(uu, vv) / R_TARCZY
hh = hh * np.clip((1 - rr) / 0.01, 0, 1)            # krawędź tarczy płaska
verts = np.stack([uu * S, -hh * GLEB, vv * S], axis=1)
faces = []
for j in range(NS):                                   # środek
    faces.append((0, 1 + j, 1 + (j + 1) % NS))
idx = lambda i, j: 1 + i * NS + (j % NS)
for i in range(NR - 1):
    for j in range(NS):
        faces.append((idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)))
me.from_pydata(verts.tolist(), [], faces)
uv = me.uv_layers.new(name="UV")
loop_v = np.empty(len(me.loops), np.int32)
me.loops.foreach_get("vertex_index", loop_v)
uvco = np.stack([(uu[loop_v] + 1) / 2, (vv[loop_v] + 1) / 2], axis=1).astype(np.float32)
uv.data.foreach_set("uv", uvco.ravel())
me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
me.update()
tarcza = bpy.data.objects.new("Tarcza", me)
sc.collection.objects.link(tarcza)

# boki i tył kamienia (walec)
bpy.ops.mesh.primitive_cylinder_add(vertices=256, radius=RM, depth=0.9, location=(0, 0.45 + 0.002, 0),
                                    rotation=(math.pi / 2, 0, 0))
bok = bpy.context.active_object
bok.name = "Bok"
bpy.ops.object.shade_smooth()

# materiał tarczy: zdjęcie + świecenie wybranych pól
m = bpy.data.materials.new("Kamien")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
bs.inputs["Roughness"].default_value = 0.88
nt.links.new(bs.outputs[0], out.inputs[0])
uvn = nt.nodes.new("ShaderNodeUVMap")
def tex(path, nonc=False, packed=False):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path)
    if nonc:
        t.image.colorspace_settings.name = "Non-Color"
    if packed:
        t.image.alpha_mode = "CHANNEL_PACKED"
    t.interpolation = "Cubic"
    nt.links.new(uvn.outputs[0], t.inputs[0])
    return t
t_kol = tex(KOLOR)
t_m = tex(MASKI, True, True)
t_o = tex(MASKA_OLLIN, True)
sep = nt.nodes.new("ShaderNodeSeparateColor")
nt.links.new(t_m.outputs["Color"], sep.inputs[0])
wartosci = {}
def wartosc(nazwa):
    v = nt.nodes.new("ShaderNodeValue")
    v.name = v.label = nazwa
    v.outputs[0].default_value = 0.0
    wartosci[nazwa] = v
    return v
def mnoz(a, b):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = "MULTIPLY"
    nt.links.new(a, n.inputs[0]); nt.links.new(b, n.inputs[1]); return n.outputs[0]
def maks(a, b):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = "MAXIMUM"
    nt.links.new(a, n.inputs[0]); nt.links.new(b, n.inputs[1]); return n.outputs[0]
kan = {"jaguar": sep.outputs[0], "wiatr": sep.outputs[1], "deszcz": sep.outputs[2], "woda": t_m.outputs["Alpha"]}
sw = None
for k in ("jaguar", "wiatr", "deszcz", "woda"):
    s = mnoz(kan[k], wartosc(k).outputs[0])
    sw = s if sw is None else maks(sw, s)
sw = maks(sw, mnoz(t_o.outputs["Color"], wartosc("ollin").outputs[0]))
# przyciemnienie reszty: 1 - 0.55*przyc*(1-sw)
jeden_minus = nt.nodes.new("ShaderNodeMath"); jeden_minus.operation = "SUBTRACT"
jeden_minus.inputs[0].default_value = 1.0; nt.links.new(sw, jeden_minus.inputs[1])
pc = mnoz(jeden_minus.outputs[0], wartosc("przyciemnienie").outputs[0])
pc2 = nt.nodes.new("ShaderNodeMath"); pc2.operation = "MULTIPLY_ADD"
nt.links.new(pc, pc2.inputs[0]); pc2.inputs[1].default_value = -0.42; pc2.inputs[2].default_value = 1.0
mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"; mixc.blend_type = "MULTIPLY"
mixc.inputs["Factor"].default_value = 1.0
nt.links.new(t_kol.outputs["Color"], mixc.inputs["A"])
cmb = nt.nodes.new("ShaderNodeCombineColor")
for i in range(3):
    nt.links.new(pc2.outputs[0], cmb.inputs[i])
nt.links.new(cmb.outputs[0], mixc.inputs["B"])
nt.links.new(mixc.outputs["Result"], bs.inputs["Base Color"])
# złote świecenie z zachowaniem rysunku płaskorzeźby (mnożone przez jasność zdjęcia)
bw = nt.nodes.new("ShaderNodeRGBToBW")
nt.links.new(t_kol.outputs["Color"], bw.inputs[0])
sila = mnoz(mnoz(bw.outputs[0], sw), wartosc("blask").outputs[0])
bs.inputs["Emission Color"].default_value = G.srgb(G.ZLOTY)
nt.links.new(sila, bs.inputs["Emission Strength"])
tarcza.data.materials.append(m)

mb = bpy.data.materials.new("KamienBok")
mb.use_nodes = True
pb = mb.node_tree.nodes["Principled BSDF"]
pb.inputs["Base Color"].default_value = G.srgb((150, 132, 112))
pb.inputs["Roughness"].default_value = 0.95
nz = mb.node_tree.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40
bump = mb.node_tree.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.4
mb.node_tree.links.new(nz.outputs[0], bump.inputs["Height"])
mb.node_tree.links.new(bump.outputs[0], pb.inputs["Normal"])
bok.data.materials.append(mb)

# światło: ślizgowe z lewej góry, żeby wydobyć płaskorzeźbę, i słabe wypełnienie
def swiatlo(nazwa, typ, energia, kier, kolor=(1, 1, 1), kat=2.0):
    ld = bpy.data.lights.new(nazwa, typ)
    ld.energy = energia
    ld.color = kolor
    if typ == "SUN":
        ld.angle = math.radians(kat)
    ob = bpy.data.objects.new(nazwa, ld)
    sc.collection.objects.link(ob)
    ob.rotation_euler = (-Vector(kier)).to_track_quat("-Z", "Y").to_euler()
    return ob
swiatlo("Slonce", "SUN", 4.6, (-0.9, -0.75, 1.05), (1.0, 0.95, 0.86), 3)
swiatlo("Wypelnienie", "SUN", 0.9, (0.8, -1.0, -0.25), (0.75, 0.82, 1.0), 20)
sc.world.node_tree.nodes["Background"].inputs[0].default_value = G.srgb((14, 20, 38))
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.6

# ---------------------------------------------------------------- kamera (wolne krążenie)
D = 18.0
cam = G.kamera((0, -D, 0), (0, 0, 0), lens=70)
cam.data.shift_y = -0.026          # środek kamienia ok. 490 px od góry: miejsce na tytuł u góry i podpis u dołu
cam.data.clip_end = 200
tlo = G.tlo_kamery(cam, odl=60)
for f in range(1, KLATEK + 1):
    t = (f - 1) / (KLATEK - 1)
    s = G.gladko(t)
    yaw = math.radians(-17 + 29 * s)
    el = math.radians(5 - 6 * s)
    cam.location = (D * math.sin(yaw) * math.cos(el), -D * math.cos(yaw) * math.cos(el), D * math.sin(el))
    G.patrz(cam, (0, 0, 0))
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
for fc in G._fcurves(cam.animation_data.action):
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"

# ---------------------------------------------------------------- animacja świecenia
def klucze(nazwa, pary):
    v = wartosci[nazwa].outputs[0]
    for f, x in pary:
        v.default_value = x
        v.keyframe_insert("default_value", frame=f)
F = {"jaguar": 60, "wiatr": 110, "deszcz": 160, "woda": 210}
for k, f0 in F.items():
    klucze(k, [(f0, 0.0), (f0 + 18, 1.0), (f0 + 45, 1.0), (f0 + 62, 0.45), (270, 0.45), (300, 0.0)])
klucze("ollin", [(1, 0.0), (270, 0.0), (305, 1.0), (KLATEK, 1.0)])
klucze("przyciemnienie", [(1, 0.0), (45, 0.0), (75, 1.0), (KLATEK, 1.0)])
klucze("blask", [(1, 0.6), (KLATEK, 0.6)])
G.wygladz(nt)

# ---------------------------------------------------------------- napisy i linie
ROT = (math.pi / 2, 0, 0)           # tekst w płaszczyźnie kamienia, przodem do kamery
YN = -0.12                          # napisy przed płaskorzeźbą
KREM = (246, 236, 214)

def linia(punkty, nazwa, kolor=G.ZLOTY, grub=0.012):
    cu = bpy.data.curves.new(nazwa, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = grub
    cu.bevel_resolution = 2
    sp = cu.splines.new("POLY")
    sp.points.add(len(punkty) - 1)
    for p, (x, z) in zip(sp.points, punkty):
        p.co = (x, YN + 0.02, z, 1)
    ob = bpy.data.objects.new(nazwa, cu)
    sc.collection.objects.link(ob)
    mat = G.material_emisja(nazwa + "_mat", kolor)
    cu.materials.append(mat)
    ob["mat"] = mat.name
    return ob

def kropka(x, z, nazwa, r=0.045):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x, YN, z), segments=24, ring_count=12)
    ob = bpy.context.active_object
    ob.name = nazwa
    mat = G.material_emisja(nazwa + "_mat", G.ZLOTY)
    ob.data.materials.append(mat)
    ob["mat"] = mat.name
    return ob

OPIS = {
    # klucz: (numer Słońca, nazwa PL, nazwa nahuatl, strona)
    "jaguar": ("I Słońce", "4 Jaguar", "Nahui Ocelotl", 1),
    "wiatr": ("II Słońce", "4 Wiatr", "Nahui Ehecatl", -1),
    "deszcz": ("III Słońce", "4 Deszcz ognia", "Nahui Quiahuitl", -1),
    "woda": ("IV Słońce", "4 Woda", "Nahui Atl", 1),
}
XL = 2.18
for k, (nr, pl, nah, strona) in OPIS.items():
    cu_, cv_ = KWADRATY[k]
    zl = 1.02 if cv_ > 0 else -0.98
    wyr = "LEFT" if strona > 0 else "RIGHT"
    x = XL * strona
    t1 = G.napis(nr, 0.15, G.ZLOTY, "arialb", wyr, loc=(x, YN, zl + 0.27), rot=ROT, nazwa=f"nr_{k}")
    t2 = G.napis(pl, 0.25, KREM, "georgiab", wyr, loc=(x, YN, zl), rot=ROT, nazwa=f"pl_{k}")
    t3 = G.napis(nah, 0.13, (200, 196, 186), "georgia", wyr, loc=(x, YN, zl - 0.24), rot=ROT, nazwa=f"nah_{k}")
    # linia od napisu do kwadratu (do jego zewnętrznego narożnika)
    kx_, kz_ = cu_ * S, cv_ * S
    rog = (kx_ + math.copysign(0.17, cu_), kz_ + math.copysign(0.17, cv_))
    ln = linia([(x - 0.08 * strona, zl), (1.92 * strona, zl), rog], f"linia_{k}")
    kr = kropka(rog[0], rog[1], f"kropka_{k}")
    f0 = F[k]
    for ob in (t1, t2, t3):
        G.alfa_napisu(ob, [(1, 0.0), (f0 + 4, 0.0), (f0 + 22, 1.0)])
    for ob in (ln, kr):
        G.animuj_alfa(bpy.data.materials[ob["mat"]], [(1, 0.0), (f0, 0.0), (f0 + 16, 0.9), (f0 + 60, 0.9), (275, 0.55)])

# tytuł: piąte Słońce, 4-Ollin
tyt = G.napis("V Słońce · 4-Ollin – Słońce Ruchu", 0.27, G.ZLOTY, "georgiab", "CENTER",
              loc=(0, YN, 2.08), rot=ROT, nazwa="tytul", obrys=((5, 7, 12), 0.012))
G.alfa_napisu(tyt, [(1, 0.0), (280, 0.0), (310, 1.0)])

G.renderuj(TU, opcje, kadr_klatka=KLATEK)
