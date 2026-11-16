# -*- coding: utf-8 -*-
"""Klip „obliczenia-biegun”: ożywiony rysunek Leszka Klimka obliczenia.jpg i jego tabela z rozdziału
„Co wyszło z obliczeń?”.

Najpierw trójkąt sferyczny z rysunku: A = biegun poprzedni (Akpatok, 60°N 70°W wg tabeli),
B = biegun dzisiejszy, C = budowla (tu Teotihuacan); boki a = B–C, b = A–C, c = A–B, kąt C = odchylenie
„północy” budowli od dzisiejszej północy. Potem z kolejnych budowli z tabeli wychodzą łuki ich
„dawnej północy” i zbiegają się przy Akpatok. Przy nazwach: kąt zmierzony | kąt obliczony – liczby
z tabeli Leszka („?” tam, gdzie Leszek nie podał pomiaru).

Uruchomienie: S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/obliczenia-biegun/scena.py
              ... -- --proba 1,120,250,400
"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
from wezly import Wezly

OPCJE = G.argumenty()
KLATKI = 400  # 16 s

AKPATOK = (60.0, -70.0)  # tabela Leszka
# (nazwa, szer., dł. – położenie rzeczywiste do narysowania, kąt zmierzony, kąt obliczony – z tabeli Leszka)
MIEJSCA = [
    ("Teotihuacan", 19.692, -98.844, "18°", "19°"),
    ("Monte Alban", 17.044, -96.768, "?", "23°"),
    ("Palenque", 17.484, -92.046, "15°", "19°"),
    ("Tikal", 17.222, -89.623, "?", "15,5°"),
    ("Machu Picchu", -13.163, -72.545, "1,5°", "2°"),
    ("Tiahuanaco", -16.554, -68.673, "1,5°", "2°"),
    ("Giza", 29.979, 31.134, "20°", "24°"),
]
SRODEK = (33.0, -52.0)       # środek widoku
R_PX, CX, CY = 418.0, 960.0, 440.0
ZLOTY = G.ZLOTY

sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))

# ---------------------------------------------------------------- globus
glob = G.sfera_uv("Globus", 512, 256)
img = G.wczytaj_obraz(G.tekstura_ziemi(8192, G.ZIELEN_USKOK, G.MORZE_USKOK, "ziemia_uskok"))
mat = bpy.data.materials.new("Globus")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
W = Wezly(nt)
kol, _ = W.obraz(img, W.coord("UV"))
nrm = W.geometria("Normal")
sw_dir = (G.ll2xyz(SRODEK[0] + 25, SRODEK[1] - 30)).normalized()
sw = W.dot(nrm, tuple(sw_dir))
cien = W.add(0.62, W.mul(W.mx(sw, 0.0), 0.45))
kol = W.vmath("MULTIPLY", kol, W.vec(cien, cien, cien))
fres = W.math("POWER", W.sub(1.0, W.math("ABSOLUTE", W.dot(nrm, W.geometria("Incoming")))), 2.5)
kol = W.mix(W.mul(fres, 0.5), kol, G.srgb((150, 215, 255)))
W.emisja_wyjscie(kol)
glob.data.materials.append(mat)

# poświata
V = G.ll2xyz(*SRODEK)
bpy.ops.mesh.primitive_circle_add(vertices=128, radius=1.10, fill_type="TRIFAN", location=tuple(-V * 0.2))
pos = bpy.context.active_object
pos.rotation_euler = V.to_track_quat("Z", "Y").to_euler()
mp = bpy.data.materials.new("Poswiata")
mp.use_nodes = True
mp.node_tree.nodes.clear()
W2 = Wezly(mp.node_tree)
r2 = W2.vmath("LENGTH", W2.coord("Object"))
W2.emisja_wyjscie(G.srgb((60, 140, 225)), W2.mul(W2.sub(1.0, W2.smooth(0.9, 1.10, r2)), 0.5))
mp.surface_render_method = "BLENDED"
pos.data.materials.append(mp)

# kamera ortograficzna od strony środka widoku; 1 jednostka = R_PX pikseli
orto = 1920 / R_PX
cam = G.kamera(tuple(V * 12), (0, 0, 0), orto=orto)
cam.data.shift_y = -(540 - CY) / 1920
cam.data.ortho_scale = orto * 1.06
cam.data.keyframe_insert("ortho_scale", frame=1)
cam.data.ortho_scale = orto
cam.data.keyframe_insert("ortho_scale", frame=330)
G.wygladz(cam.data)
G.tlo_kamery(cam, odl=20)
bpy.context.view_layer.update()

# układ ekranu: prawo/góra kamery
Rc = cam.matrix_world.to_3x3()
PRAWO, GORA, KU_KAM = Rc.col[0].normalized(), Rc.col[1].normalized(), Rc.col[2].normalized()


def na_ekran(v):
    """punkt świata -> piksele kadru (dla końcowej skali kamery)"""
    return CX + v.dot(PRAWO) * R_PX, CY - v.dot(GORA) * R_PX


def z_ekranu(px, py, wys=1.3):
    """piksele -> punkt w płaszczyźnie przed globusem (napisy)"""
    return PRAWO * ((px - CX) / R_PX) + GORA * (-(py - CY) / R_PX) + KU_KAM * wys


# ---------------------------------------------------------------- linie na kuli (rosnące krzywe)
def krzywa(nazwa, pts, grub, kolor, f0, f1, r=1.004):
    cu = bpy.data.curves.new(nazwa, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = grub
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        q = p.normalized() * r
        sp.points[i].co = (q.x, q.y, q.z, 1)
    ob = bpy.data.objects.new(nazwa, cu)
    sc.collection.objects.link(ob)
    m = G.material_emisja(nazwa + "_mat", kolor)
    cu.materials.append(m)
    cu.bevel_factor_mapping_end = "SPLINE"
    cu.bevel_factor_end = 0.0
    cu.keyframe_insert("bevel_factor_end", frame=f0)
    cu.bevel_factor_end = 1.0
    cu.keyframe_insert("bevel_factor_end", frame=f1)
    G.wygladz(cu)
    G.animuj_alfa(m, [(f0, 0.0), (f0 + 3, 1.0)])
    return ob


def kropka(nazwa, lat, lon, rad, kolor, f0, obw=None):
    p = G.ll2xyz(lat, lon, 1.0)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=rad, location=tuple(p))
    ob = bpy.context.active_object
    ob.name = nazwa
    m = G.material_emisja(nazwa + "_mat", kolor)
    ob.data.materials.append(m)
    G.animuj_alfa(m, [(f0, 0.0), (f0 + 8, 1.0)])
    ob.scale = (0.01, 0.01, 0.01)
    ob.keyframe_insert("scale", frame=f0)
    ob.scale = (1, 1, 1)
    ob.keyframe_insert("scale", frame=f0 + 10)
    G.wygladz(ob)
    if obw:
        kropka(nazwa + "_obw", lat, lon, rad * 1.45, obw, f0)
    return ob


def plaski(nazwa, pts_px, faces, kolor, f0, wys=1.25):
    me = bpy.data.meshes.new(nazwa)
    me.from_pydata([tuple(z_ekranu(x, y, wys)) for x, y in pts_px], [], faces)
    ob = bpy.data.objects.new(nazwa, me)
    sc.collection.objects.link(ob)
    m = G.material_emisja(nazwa + "_mat", kolor)
    me.materials.append(m)
    G.animuj_alfa(m, [(f0, 0.0), (f0 + 12, 1.0)])
    return ob


def odcinek_px(nazwa, a, b, grub, kolor, f0):
    d = Vector((b[0] - a[0], b[1] - a[1])); L = d.length; d.normalize()
    n = Vector((-d.y, d.x)) * grub / 2
    pts = [(a[0] + n.x, a[1] + n.y), (b[0] + n.x, b[1] + n.y), (b[0] - n.x, b[1] - n.y), (a[0] - n.x, a[1] - n.y)]
    return plaski(nazwa, pts, [(0, 1, 2, 3)], kolor, f0)


def napis_px(nazwa, tekst, x, y, rozm_px, kolor, f0, kroj="arialb", wyr="LEFT", wys=1.3):
    ob = G.napis(tekst, rozm_px / R_PX, kolor, kroj, wyr, loc=tuple(z_ekranu(x, y, wys)), nazwa=nazwa, odstep=1.1)
    ob.rotation_euler = cam.rotation_euler
    G.alfa_napisu(ob, [(f0, 0.0), (f0 + 14, 1.0)])
    return ob


A = G.ll2xyz(*AKPATOK)
B = Vector((0, 0, 1))

# ---------------------------------------------------------------- trójkąt z rysunku (Teotihuacan)
nazwa0, la0, lo0, zm0, ob0 = MIEJSCA[0]
Cv = G.ll2xyz(la0, lo0)
kropka("Biegun_B", 90, 0, 0.014, (20, 20, 20), 8)
kropka("Akpatok_A", *AKPATOK, 0.016, (225, 30, 30), 8)
krzywa("Bok_c", G.luk(*AKPATOK, 90, 0, 80), 0.0035, (255, 255, 255), 20, 60)
krzywa("Bok_a", G.luk(la0, lo0, 90, 0, 120), 0.0035, (255, 255, 255), 30, 75)
for nm, la, lo, zm, ob_ in MIEJSCA:
    kropka("Miejsce_" + nm, la, lo, 0.011, (255, 214, 120), 14)

# łuki „dawnej północy” b: od budowli do Akpatok (najpierw Teotihuacan, potem pozostałe)
starty = {"Teotihuacan": 45, "Monte Alban": 120, "Palenque": 140, "Tikal": 160, "Machu Picchu": 190, "Tiahuanaco": 210,
          "Giza": 235}
for nm, la, lo, zm, ob_ in MIEJSCA:
    f0 = starty[nm]
    krzywa("Luk_" + nm, G.luk(la, lo, *AKPATOK, 160), 0.0045, ZLOTY, f0, f0 + 55)

# kąt C przy Teotihuacan: łuk między kierunkiem na B (północ) i na A
azA = math.radians(G.azymut(la0, lo0, *AKPATOK))
Nn = (B - Cv * Cv.z).normalized(); Ee = Nn.cross(Cv).normalized()
rk = math.radians(7.0)
klin = []
for i in range(25):
    t = azA * i / 24
    d = (Nn * math.cos(t) + Ee * math.sin(t))
    klin.append((Cv * math.cos(rk) + d * math.sin(rk)))
krzywa("Kat_C", klin, 0.0040, (255, 255, 255), 80, 100, r=1.006)

# litery jak na rysunku: A, B, C przy wierzchołkach, a, b, c przy bokach
def przy(v, dx, dy):
    x, y = na_ekran(v)
    return x + dx, y + dy


TL = 34
for txt, v, dx, dy, f0 in (("A", A, -30, -26, 20), ("B", B, 16, -30, 20), ("C", Cv, -44, -6, 30)):
    x, y = przy(v, dx, dy)
    napis_px("Lit_" + txt, txt, x, y, TL, (255, 255, 255), f0, wyr="CENTER")
mid_c = G.luk(*AKPATOK, 90, 0, 2)[1]
mid_a = G.luk(la0, lo0, 90, 0, 2)[1]
mid_b = G.luk(la0, lo0, *AKPATOK, 2)[1]
for txt, v, dx, dy, f0, kol_l in (("c", mid_c, -24, -8, 55, (255, 255, 255)), ("a", mid_a, -24, 4, 70, (255, 255, 255)),
                                  ("b", mid_b, 20, 14, 85, ZLOTY)):
    x, y = przy(v, dx, dy)
    napis_px("Lit_" + txt, txt, x, y, TL * 0.9, kol_l, f0, kroj="georgia", wyr="CENTER")

# podpisy biegunów
x, y = przy(A, 30, 12)
napis_px("Pod_A", "Akpatok", x, y, 30, (255, 255, 255), 24, wyr="LEFT")
x, y = przy(B, 40, -30)
napis_px("Pod_B", "biegun dzisiejszy", x, y, 30, (255, 255, 255), 24, wyr="LEFT")

# ---------------------------------------------------------------- nazwy budowli i kąty z tabeli
# rozkład podpisów (piksele kadru): kolumna z lewej dla Mezoameryki, Andy w dole, Giza z prawej
pozycje = {}
for nm, la, lo, zm, ob_ in MIEJSCA:
    pozycje[nm] = na_ekran(G.ll2xyz(la, lo))
print("[obl] piksele miejsc:", {k: (round(v[0]), round(v[1])) for k, v in pozycje.items()})
print("[obl] Akpatok", na_ekran(A), " biegun", na_ekran(B))
uklad = {"Teotihuacan": (300, 470), "Monte Alban": (300, 545), "Palenque": (300, 620), "Tikal": (300, 695),
         "Machu Picchu": (450, 770), "Tiahuanaco": (560, 840), "Giza": (1560, 470)}
for nm, la, lo, zm, ob_ in MIEJSCA:
    f0 = starty[nm] + (40 if nm == "Teotihuacan" else 20)
    tx, ty = uklad[nm]
    sx, sy = pozycje[nm]
    prawy = tx > sx
    wyr = "LEFT" if prawy else "RIGHT"
    napis_px("Naz_" + nm, nm, tx, ty - 15, 30, (255, 255, 255), f0, wyr=wyr)
    napis_px("Kat_" + nm, f"{zm}  |  {ob_}", tx, ty + 19, 27, ZLOTY, f0, kroj="arial", wyr=wyr)
    # linia odniesienia od podpisu do budowli
    kx = tx + (-12 if prawy else 12)
    odcinek_px("Odn_" + nm, (kx, ty), (sx, sy), 2.2, (230, 230, 230), f0)

# legenda (prawy górny róg)
napis_px("Leg1", "kąt zmierzony  |  kąt obliczony", 1880, 70, 28, ZLOTY, 250, kroj="arial", wyr="RIGHT")
napis_px("Leg2", "(tabela z artykułu Leszka)", 1880, 106, 24, (210, 210, 210), 250, kroj="arial", wyr="RIGHT")

G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
