# -*- coding: utf-8 -*-
"""Klip „lod-przy-biegunie”: ilustracja słów Einsteina cytowanych w rozdziale 02 (hipoteza Hapgooda).

„W strefie polarnej trwa nieustanne nawarstwianie się lodu, występujące nierównomiernie wokół bieguna.
Rotacja Ziemi oddziałuje na tę masę lodu, wytwarzając moment odśrodkowy, który przenosi się na twardą
skorupę naszej planety. Siła ta, osiągnąwszy pewną wartość, powoduje przesuwanie skorupy ziemskiej”.

Globus ustawiony jak przed uskokiem: oś obrotu (N–S) przechodzi przez wyspę Akpatok (60°N 70°W wg
Leszka). Lód narasta nierównomiernie wokół bieguna – do zasięgu z mapy „największego zasięgu
zlodowaceń” (lodowiec.gif), przeliczonej z odwzorowania Robinsona na kulę. Czerwone strzałki (jak na
rysunkach masy1.jpg i masy3.jpg) pokazują siłę odśrodkową działającą na masy lodu i jej wypadkową;
na końcu skorupa razem z lodem zaczyna się przesuwać względem nieruchomej osi.

Uruchomienie: S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/lod-przy-biegunie/scena.py
              ... -- --proba 40,150,250,330,400
"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector, Matrix, Quaternion

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
from wezly import Wezly, animuj_wartosc

OPCJE = G.argumenty()
KLATKI = 400  # 16 s
AKPATOK = (60.0, -70.0)
# lodowiec.gif: odwzorowanie Robinsona, dopasowane do lądów (środek 250,127 px, R = 93 px, południk 0°)
R_CX, R_CY, R_R = 250.0, 127.0, 93.0
ROB = np.array([[0, 1.0, 0.0], [5, .9986, .0620], [10, .9954, .1240], [15, .9900, .1860], [20, .9822, .2480],
                [25, .9730, .3100], [30, .9600, .3720], [35, .9427, .4340], [40, .9216, .4958], [45, .8962, .5571],
                [50, .8679, .6176], [55, .8350, .6769], [60, .7986, .7346], [65, .7597, .7903], [70, .7186, .8435],
                [75, .6732, .8936], [80, .6213, .9394], [85, .5722, .9761], [90, .5322, 1.0]])
CZERWONY = (222, 44, 40)


def robinson(lat, lon):
    a = np.abs(lat)
    X = np.interp(a, ROB[:, 0], ROB[:, 1]); Y = np.interp(a, ROB[:, 0], ROB[:, 2]) * np.sign(lat)
    return R_CX + 0.8487 * X * np.radians(lon) * R_R, R_CY - 1.3523 * Y * R_R


def tekstury_lodu():
    p = os.path.join(G.CACHE, "lod_lgm.png")
    pn = os.path.join(G.CACHE, "lod_lgm.npy")
    if os.path.exists(p) and os.path.exists(pn):
        return p, np.load(pn)
    d = G.obraz_numpy(os.path.join(G.RYSUNKI, "lodowiec.gif")) * 255
    r, g, b = d[..., 0], d[..., 1], d[..., 2]
    lod = ((b > 200) & (b - r > 45) & (r > 130) & (r < 185)).astype(np.float32)
    lod = (G.rozmyj(lod, 2) > 0.3).astype(np.float32)   # domknięcie przerw po liniach siatki i napisach
    lod = (G.rozmyj(lod, 2) > 0.6).astype(np.float32)
    H, W = lod.shape
    Wt, Ht = 4096, 2048
    jj, ii = np.mgrid[0:Ht, 0:Wt]
    lon = (ii + 0.5) / Wt * 360 - 180
    lat = 90 - (jj + 0.5) / Ht * 180
    PX, PY = robinson(lat, lon)
    X = np.clip(PX, 0, W - 1.001); Y = np.clip(PY, 0, H - 1.001)
    x0, y0 = X.astype(int), Y.astype(int); fx, fy = X - x0, Y - y0
    lm = G.rozmyj(lod, 1)
    m = (lm[y0, x0] * (1 - fx) * (1 - fy) + lm[y0, x0 + 1] * fx * (1 - fy) + lm[y0 + 1, x0] * (1 - fx) * fy
         + lm[y0 + 1, x0 + 1] * fx * fy)
    m = np.clip((m - 0.5) * 3 + 0.5, 0, 1) * (lat > 35)
    # grubość: rozmyta maska (gładkie kopuły lodu opadające do zera na brzegach),
    # grubsza po stronie, w którą według tekstu ruszyła skorupa (nierównomierność wokół bieguna)
    A = np.array(G.ll2xyz(*AKPATOK))
    P = np.stack([np.cos(np.radians(lat)) * np.cos(np.radians(lon)), np.cos(np.radians(lat)) * np.sin(np.radians(lon)),
                  np.sin(np.radians(lat))], -1)
    gr = G.zmniejsz(m, 4)
    for _ in range(4):
        gr = G.rozmyj(gr, 5)
    gr = np.repeat(np.repeat(gr, 4, 0), 4, 1)
    Q0n = np.array(Q0.to_3x3())
    Pq = P @ Q0n.T
    rh = np.hypot(Pq[..., 0], Pq[..., 1])
    strona = (Pq[..., 0] * H_TEKST.x + Pq[..., 1] * H_TEKST.y) / np.maximum(rh, 1e-6)
    gr = gr * (0.55 + 0.45 * np.clip(strona, -1, 1) * np.clip(rh / 0.4, 0, 1))
    gr = gr / max(gr.max(), 1e-6)
    odl = np.degrees(np.arccos(np.clip(P @ A, -1, 1)))
    rng = np.random.default_rng(7)
    sz = rng.random((64, 128)).astype(np.float32)
    sz = G.rozmyj(np.repeat(np.repeat(sz, 32, 0), 32, 1), 24)
    kol = np.clip(odl / 48.0 + (sz - 0.5) * 0.35, 0, 1)
    a = np.zeros((Ht, Wt, 4), np.float32)
    a[..., 0] = m; a[..., 1] = kol; a[..., 2] = gr; a[..., 3] = 1
    G.zapisz_png(a, p)
    # środek masy lodu (wektor), ważony grubością i polem (cos szerokości)
    w = (gr * np.cos(np.radians(lat)))[..., None]
    sm = (P * w).sum((0, 1)) / w.sum()
    np.save(pn, sm)
    return p, sm


# orientacja skorupy przed uskokiem: Akpatok na osi (+Z)
A = G.ll2xyz(*AKPATOK)
Q0 = A.rotation_difference(Vector((0, 0, 1))).to_matrix().to_4x4()
# kierunek wypadkowej i przesuwania: tak jak w tekście – skorupa ruszyła na południe wzdłuż 70°W,
# czyli Akpatok odjeżdża od osi w stronę przeciwną do dzisiejszego bieguna
npq = Q0 @ Vector((0, 0, 1))
H_TEKST = -Vector((npq.x, npq.y, 0)).normalized()

sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))
p_lod, srodek_masy = tekstury_lodu()
img_lod = G.wczytaj_obraz(p_lod, nieliniowy=False)
img_ziemia = G.wczytaj_obraz(G.tekstura_ziemi(8192, G.ZIELEN_USKOK, G.MORZE_USKOK, "ziemia_uskok"))
h = H_TEKST
print("[lod] środek masy lodu (ważony):", G.xyz2ll(Vector(srodek_masy)), " kierunek wypadkowej:", tuple(round(c, 3) for c in h))

# hierarchia: Obrot (wirowanie wokół osi Z) -> Skorupa (przesuwanie) -> globus i lód
obrot = bpy.data.objects.new("Obrot", None); sc.collection.objects.link(obrot)
skorupa = bpy.data.objects.new("Skorupa", None); sc.collection.objects.link(skorupa)
skorupa.parent = obrot

ziemia = G.sfera_uv("Ziemia", 512, 256)
ziemia.parent = skorupa
ziemia.matrix_parent_inverse = Matrix.Identity(4)
ziemia.matrix_basis = Q0
mz = bpy.data.materials.new("Ziemia")
mz.use_nodes = True
mz.node_tree.nodes.clear()
W = Wezly(mz.node_tree)
kol, _ = W.obraz(img_ziemia, W.coord("UV"))
nrm = W.geometria("Normal")
SW = Vector((-0.55, -0.6, 0.6)).normalized()
sw = W.dot(nrm, tuple(SW))
cien = W.add(0.6, W.mul(W.mx(sw, 0.0), 0.48))
kol = W.vmath("MULTIPLY", kol, W.vec(cien, cien, cien))
fres = W.math("POWER", W.sub(1.0, W.math("ABSOLUTE", W.dot(nrm, W.geometria("Incoming")))), 2.5)
kol = W.mix(W.mul(fres, 0.5), kol, G.srgb((150, 215, 255)))
W.emisja_wyjscie(kol)
ziemia.data.materials.append(mz)

# skorupa lodu: osobna kula z wypukłością (grubość z tekstury), przezroczysta poza lodem
lodo = G.sfera_uv("Lod", 512, 256, r=1.003)
lodo.parent = skorupa
lodo.matrix_parent_inverse = Matrix.Identity(4)
lodo.matrix_basis = Q0
tx = bpy.data.textures.new("grubosc", "IMAGE")
tx.image = img_lod
tx.use_alpha = False
dsp = lodo.modifiers.new("Grubosc", "DISPLACE")
dsp.texture = tx
dsp.texture_coords = "UV"
dsp.uv_layer = "UV"
dsp.direction = "NORMAL"
dsp.mid_level = 0.0
dsp.strength = 0.0
dsp.keyframe_insert("strength", frame=20)
dsp.strength = 0.045
dsp.keyframe_insert("strength", frame=215)
ml = bpy.data.materials.new("Lod")
ml.use_nodes = True
ml.node_tree.nodes.clear()
W3 = Wezly(ml.node_tree)
lc, _ = W3.obraz(img_lod, W3.coord("UV"))
l_m, l_k, l_g = W3.sep(lc)
narost = W3.wartosc(0.0, "narost")
widoczny = W3.mul(l_m, W3.sub(1.0, W3.smooth(-0.04, 0.0, W3.sub(l_k, narost))))
n3 = W3.geometria("Normal")
s3 = W3.dot(n3, tuple(SW))
c3 = W3.add(0.72, W3.mul(W3.mx(s3, 0.0), 0.34))
kl = W3.mix(W3.mul(l_g, 0.6), G.srgb((214, 232, 246)), G.srgb((250, 253, 255)))
kl = W3.vmath("MULTIPLY", kl, W3.vec(c3, c3, c3))
W3.emisja_wyjscie(kl, W3.smooth(0.25, 0.6, widoczny))
ml.surface_render_method = "DITHERED"
lodo.data.materials.append(ml)
animuj_wartosc(ml.node_tree, "narost", [(20, 0.0), (215, 1.0)])

# kropka Akpatok (dawny biegun) na skorupie
bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, radius=0.022, location=(0, 0, 1.0))
kr = bpy.context.active_object
kr.parent = skorupa
kr.matrix_parent_inverse = Matrix.Identity(4)
kr.location = (0, 0, 1.0 + 0.05)
kr.data.materials.append(G.material_emisja("Akp", (200, 25, 25)))

# oś obrotu N–S (nieruchoma)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.009, depth=3.5, location=(0, 0, -0.25))
os_ = bpy.context.active_object
os_.name = "Os"
os_.data.materials.append(G.material_emisja("Os", (235, 235, 235)))

# kamera
EL = math.radians(52)
cam = G.kamera((0, -9.6 * math.cos(EL), 9.6 * math.sin(EL)), (0, 0, 0.0), lens=50)
cam.data.shift_y = -0.035
G.tlo_kamery(cam, odl=40)
bpy.context.view_layer.update()
PRAWO = cam.matrix_world.to_3x3().col[0].normalized()
for txt, z in (("N", 1.72), ("S", -2.22)):
    t = G.napis(txt, 0.16, (255, 255, 255), "arialb", "CENTER", loc=(0.0, 0, z), nazwa="Lit_" + txt)
    t.rotation_euler = cam.rotation_euler

# wirowanie: na końcu wypadkowa ma wskazywać w prawo kadru
fi_h = math.atan2(h.y, h.x)
fi_cel = math.atan2(PRAWO.y, PRAWO.x) - math.radians(18)
FI_KON = fi_cel - fi_h
FI_POC = FI_KON - math.radians(80)


def fi(f):
    return FI_POC + (FI_KON - FI_POC) * G.gladko((f - 1) / (KLATKI - 40))


for f in range(1, KLATKI + 1):
    obrot.rotation_euler = (0, 0, fi(f))
    obrot.keyframe_insert("rotation_euler", frame=f)
for fc in G._fcurves(obrot.animation_data.action):
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"

# przesuwanie skorupy: obrót wokół osi poziomej prostopadłej do wypadkowej (masa lodu odjeżdża od osi)
k_os = Vector((0, 0, 1)).cross(h).normalized()
BETA = math.radians(8)
skorupa.rotation_mode = "QUATERNION"
for f, b in ((285, 0.0), (385, BETA)):
    skorupa.rotation_quaternion = Quaternion(k_os, b)
    skorupa.keyframe_insert("rotation_quaternion", frame=f)
G.wygladz(skorupa)


# ---------------------------------------------------------------- strzałki
def strzalka(nazwa, dlug, grub, kolor, rodzic, baza, kierunek, f0, f1, alfa_kon=1.0):
    """strzałka 3D (walec + stożek) od punktu baza w kierunku kierunek; rośnie od f0 do f1"""
    m = G.material_emisja(nazwa + "_mat", kolor)
    me_c = bpy.data.meshes.new(nazwa)
    import bmesh
    bm = bmesh.new()
    gl = dlug * 0.32
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=grub, radius2=grub, depth=dlug - gl,
                          matrix=Matrix.Translation((0, 0, (dlug - gl) / 2)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=grub * 2.6, radius2=0.0, depth=gl,
                          matrix=Matrix.Translation((0, 0, dlug - gl / 2)))
    bm.to_mesh(me_c); bm.free()
    ob = bpy.data.objects.new(nazwa, me_c)
    sc.collection.objects.link(ob)
    ob.parent = rodzic
    ob.matrix_parent_inverse = Matrix.Identity(4)
    me_c.materials.append(m)
    ob.location = baza
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(kierunek)
    ob.scale = (1, 1, 0.001)
    ob.keyframe_insert("scale", frame=f0)
    ob.scale = (1, 1, 1)
    ob.keyframe_insert("scale", frame=f1)
    G.wygladz(ob)
    G.animuj_alfa(m, [(f0, 0.0), (f0 + 6, alfa_kon)])
    return ob


# punkty na masach lodu (tylko tam, gdzie mapa pokazuje lód); długość ~ odległość od osi × grubość
img_px = None
lod_np = np.load(os.path.join(G.CACHE, "lod_lgm.npy"))  # tylko dla pewności, że cache istnieje
d = np.empty(img_lod.size[0] * img_lod.size[1] * 4, np.float32)
img_lod.pixels.foreach_get(d)
d = d.reshape(img_lod.size[1], img_lod.size[0], 4)[::-1]


def probka_lodu(lat, lon):
    j = int((90 - lat) / 180 * d.shape[0]); i = int((lon + 180) / 360 * d.shape[1])
    return d[min(j, d.shape[0] - 1), min(i, d.shape[1] - 1)]


MASY = [(58, -92), (72, -40), (62, 16), (60, -128), (52, -75), (66, 40)]
n = 0
for la, lo in MASY:
    s = probka_lodu(la, lo)
    if s[0] < 0.5:
        continue
    pb = Q0 @ G.ll2xyz(la, lo)                   # punkt w układzie skorupy (oś = Z)
    poz = Vector((pb.x, pb.y, 0))
    rh = poz.length
    dl = 0.16 + 0.42 * rh * (0.4 + 0.6 * float(s[2]))
    baza = pb * (1.0 + 0.045 * float(s[2]) + 0.012)
    strzalka(f"Sila_{n}", dl, 0.013, CZERWONY, obrot, baza, poz.normalized(), 200 + n * 8, 230 + n * 8)
    n += 1
print("[lod] strzałek sił:", n)
# wypadkowa: gruba strzałka od osi nad biegunem w stronę przesunięcia masy (jak na masy1.jpg)
wyp = strzalka("Wypadkowa", 0.95, 0.03, (235, 60, 50), obrot, Vector((0, 0, 1.1)), h, 245, 285)

# podpisy (słowa z cytatu Einsteina) – przy strzałkach, zwrócone do kamery
def podpis(nazwa, tekst, poz, f0, rodzic=None, rozm=0.11, kolor=(255, 255, 255)):
    t = G.napis(tekst, rozm, kolor, "arialb", "CENTER", loc=poz, nazwa=nazwa)
    if rodzic:
        t.parent = rodzic
        t.matrix_parent_inverse = Matrix.Identity(4)
        t.location = poz
    c = t.constraints.new("TRACK_TO")
    c.target = cam
    c.track_axis = "TRACK_Z"
    c.up_axis = "UP_Y"
    G.alfa_napisu(t, [(1, 0.0), (f0, 0.0), (f0 + 16, 1.0)])
    return t


podpis("Pod_moment", "moment odśrodkowy", Vector((0, 0, 1.1)) + h * 0.6 + Vector((0, 0, 0.15)), 270, rodzic=obrot,
       kolor=(255, 225, 160))
podpis("Pod_skorupa", "przesuwanie skorupy ziemskiej", PRAWO * 1.95 + Vector((0, 0, 0.25)), 300, kolor=(150, 200, 255))

# znak przesuwania skorupy: łuk ze strzałką przy brzegu kuli (jak niebieski łuk na masy3.jpg)
cu = bpy.data.curves.new("Luk_przes", "CURVE")
cu.dimensions = "3D"
cu.bevel_depth = 0.014
sp = cu.splines.new("POLY")
pts = []
for i in range(41):
    t = math.radians(64 - 54 * i / 40)    # od góry ku równikowi – w stronę, w którą odjeżdża masa lodu
    pts.append(Vector((math.cos(t) * 1.2, 0, math.sin(t) * 1.2)))
sp.points.add(len(pts) - 1)
for i, p in enumerate(pts):
    sp.points[i].co = (p.x, p.y, p.z, 1)
lk = bpy.data.objects.new("Luk_przes", cu)
sc.collection.objects.link(lk)
mlk = G.material_emisja("Luk_przes", (40, 110, 220))
cu.materials.append(mlk)
cu.bevel_factor_mapping_end = "SPLINE"
cu.bevel_factor_end = 0.0
cu.keyframe_insert("bevel_factor_end", frame=290)
cu.bevel_factor_end = 1.0
cu.keyframe_insert("bevel_factor_end", frame=360)
G.wygladz(cu)
G.animuj_alfa(mlk, [(288, 0.0), (292, 1.0)])
# łuk leży w płaszczyźnie (kamera-prawo, Z) po prawej stronie kuli; obrót do płaszczyzny ekranu
lk.rotation_euler = (0, 0, math.atan2(PRAWO.y, PRAWO.x))
# grot łuku
t_k = math.radians(10)
kon = Vector((math.cos(t_k) * 1.2, 0, math.sin(t_k) * 1.2))
styczna = Vector((math.sin(t_k), 0, -math.cos(t_k)))
grot = strzalka("Grot_przes", 0.16, 0.014, (40, 110, 220), lk, kon - styczna * 0.02, styczna, 354, 362)

G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
