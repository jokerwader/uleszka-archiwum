# -*- coding: utf-8 -*-
"""
Klip „epoki-lodowcowe” do odcinka 2 „Wielki uskok…” (rozdz. 10: „Czy takich epok lodowcowych kończących się
z "wielkim hukiem" było na Ziemi kilka?”).

ILUSTRACJA (dane pomiarowe): temperatura nad Antarktydą z ostatnich 800 tys. lat odczytana z rdzenia lodowego
EPICA Dome C (Jouzel i in. 2007, PANGAEA doi:10.1594/PANGAEA.683655, CC BY 3.0; plik w _dane/epica/).
Wykres jako „grzbiet” w 3D: oś pozioma = czas (z lewej 800 tys. lat temu, z prawej dziś), wysokość = odchylenie
temperatury od średniej z ostatniego tysiąclecia. Kamera leci wzdłuż wykresu i liczy epoki lodowcowe (8 w 800 tys. lat),
na końcu pokazuje całość. Najzimniejsze punkty kolejnych epok lodowcowych wyszukuje skrypt w danych (wygładzonych
średnią z ok. 3 tys. lat). Klip nie rozstrzyga, jak kończyły się epoki lodowcowe – pokazuje tylko, że było ich wiele.

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/epoki-lodowcowe/scena.py
  ... -- --proba 1,120,250,330,425     (tylko kadry próbne PNG do _klatki/)
"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G

KLATEK = 425  # 17 s
opcje = G.argumenty()
sc = G.nowa_scena(KLATEK)
sc.eevee.taa_render_samples = int(os.environ.get("USKOK3D_PROBKI", "24"))

# ---------------------------------------------------------------- dane
def wczytaj():
    wiek, temp = [], []
    dane = False
    with open(os.path.join(G.DANE, "epica", "EPICA_DomeC_deuter_temperatura.tab"), encoding="utf-8") as f:
        for ln in f:
            if not dane:
                if ln.startswith("Depth ice/snow"):
                    dane = True
                continue
            p = ln.rstrip("\n").split("\t")
            if len(p) >= 4 and p[1] and p[3]:
                wiek.append(float(p[1])); temp.append(float(p[3]))
    return np.array(wiek), np.array(temp)


WIEK, TEMP = wczytaj()
KROK = 0.5                                           # tys. lat
OS_W = np.arange(0.0, 800.0 + KROK, KROK)            # 0 = dziś
T_SUR = np.interp(OS_W, WIEK, TEMP)


def srednia(a, okno):
    k = np.ones(okno) / okno
    return np.convolve(np.pad(a, (okno // 2, okno // 2), mode="edge"), k, mode="valid")[:len(a)]


T_W = srednia(T_SUR, 3)                               # wykres: lekkie wygładzenie (1,5 tys. lat)
T_G = srednia(T_SUR, 7)                               # do szukania minimów (3,5 tys. lat)

# okna, w których leżą kolejne epoki lodowcowe (zimne okresy między ociepleniami), od najstarszej
OKNA = [(700, 775), (622, 660), (525, 570), (427, 470), (338, 375), (245, 290), (132, 190), (15, 35)]
MINIMA = []
for a, b in OKNA:
    m = (OS_W >= a) & (OS_W <= b)
    i = np.argmin(np.where(m, T_G, 99))
    MINIMA.append((float(OS_W[i]), float(T_G[i])))
print("[epoki] minima (tys. lat, °C):", [(round(w), round(t, 1)) for w, t in MINIMA])
print("[epoki] zakres temperatur:", float(T_W.min()), float(T_W.max()))

# ---------------------------------------------------------------- układ wykresu
DL = 26.0                    # długość osi czasu w jednostkach sceny
SX = DL / 800.0              # jednostek na tys. lat
SZ = 0.42                    # jednostek na °C
T_DOL = -11.5                # podstawa wykresu [°C]
GR = 0.55                    # połowa grubości grzbietu (oś Y)


def X(wiek):                 # 800 tys. lat temu z lewej, dziś z prawej
    return DL / 2 - wiek * SX


def Z(t):
    return t * SZ


n = len(OS_W)
V, F = [], []
for i in range(n):
    x, z = X(OS_W[i]), Z(T_W[i])
    V += [(x, -GR, Z(T_DOL)), (x, -GR, z), (x, GR, z), (x, GR, Z(T_DOL))]
for i in range(n - 1):
    a, b = 4 * i, 4 * (i + 1)
    F += [(b, a, a + 1, b + 1), (b + 1, a + 1, a + 2, b + 2), (b + 2, a + 2, a + 3, b + 3)]
F += [(0, 3, 2, 1), (4 * (n - 1), 4 * (n - 1) + 1, 4 * (n - 1) + 2, 4 * (n - 1) + 3)]
me = bpy.data.meshes.new("grzbiet"); me.from_pydata(V, [], F); me.update()
grzbiet = bpy.data.objects.new("grzbiet", me); sc.collection.objects.link(grzbiet)

mg = bpy.data.materials.new("grzbiet_mat"); mg.use_nodes = True
nt = mg.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
geo = nt.nodes.new("ShaderNodeNewGeometry")
sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = Z(T_DOL); mr.inputs["From Max"].default_value = Z(5.0)
nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
ramp = nt.nodes.new("ShaderNodeValToRGB")
el = ramp.color_ramp.elements


def stop(t, kolor, i=None):
    pos = (t - T_DOL) / (5.0 - T_DOL)
    e = el[i] if i is not None else el.new(pos)
    e.position = pos; e.color = G.srgb(kolor)


stop(T_DOL, (10, 26, 70), 0)
stop(5.0, (255, 150, 70), 1)
stop(-9.0, (28, 70, 150))
stop(-6.0, (95, 160, 225))
stop(-3.0, (190, 222, 245))
stop(-1.0, (238, 236, 220))
stop(1.0, (240, 196, 111))
nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
sepn = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Normal"], sepn.inputs[0])
# wierzch jaśniejszy, ściana frontowa pełna, tylna ciemniejsza
jas = nt.nodes.new("ShaderNodeMapRange")
jas.inputs["From Min"].default_value = -1.0; jas.inputs["From Max"].default_value = 1.0
jas.inputs["To Min"].default_value = 0.78; jas.inputs["To Max"].default_value = 1.35
nt.links.new(sepn.outputs["Z"], jas.inputs["Value"])
em = nt.nodes.new("ShaderNodeEmission")
nt.links.new(ramp.outputs["Color"], em.inputs["Color"]); nt.links.new(jas.outputs["Result"], em.inputs["Strength"])
nt.links.new(em.outputs[0], out.inputs["Surface"])
me.materials.append(mg)

# podłoże: ciemna płyta z poprzecznymi kreskami co 100 tys. lat
bpy.ops.mesh.primitive_plane_add(size=1)
plyta = bpy.context.active_object; plyta.name = "plyta"
plyta.scale = (DL + 9.0, 7.0, 1); plyta.location = (0, 0.4, Z(T_DOL) - 0.01)
m_pl = G.material_emisja("plyta_mat", (11, 17, 34), 1.0); plyta.data.materials.append(m_pl)


def linia(nazwa, punkty, kolor, alfa, grub, przerywana=None):
    cu = bpy.data.curves.new(nazwa, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = grub
    if przerywana:
        a, b = Vector(punkty[0]), Vector(punkty[1])
        k = int((b - a).length / przerywana)
        for i in range(k):
            sp = cu.splines.new("POLY"); sp.points.add(1)
            sp.points[0].co = (*a.lerp(b, i / k), 1); sp.points[1].co = (*a.lerp(b, (i + 0.55) / k), 1)
    else:
        sp = cu.splines.new("POLY"); sp.points.add(len(punkty) - 1)
        for i, p in enumerate(punkty):
            sp.points[i].co = (*p, 1)
    ob = bpy.data.objects.new(nazwa, cu); sc.collection.objects.link(ob)
    m = G.material_emisja(nazwa + "_mat", kolor, alfa); cu.materials.append(m)
    return ob, m


Y_P = -GR - 0.02          # tuż przed frontem grzbietu
for w in range(0, 801, 100):
    linia(f"kreska{w}", [(X(w), -2.6, Z(T_DOL)), (X(w), 3.6, Z(T_DOL))], (70, 90, 140), 0.55, 0.012)
    tekst = "dziś" if w == 0 else f"{w}"
    t = G.napis(tekst, 0.5, G.ZLOTY, "georgiab", "CENTER", loc=(X(w), -1.55, Z(T_DOL) + 0.24),
                rot=(math.radians(62), 0, 0), nazwa=f"os{w}", obrys=((5, 7, 12), 0.012))
G.napis("tys. lat temu", 0.3, (200, 205, 220), "georgia", "CENTER", loc=(X(750), -2.35, Z(T_DOL) + 0.18),
        rot=(math.radians(62), 0, 0), nazwa="os_opis")
G.napis("tys. lat temu", 0.3, (200, 205, 220), "georgia", "CENTER", loc=(X(50), -2.35, Z(T_DOL) + 0.18),
        rot=(math.radians(62), 0, 0), nazwa="os_opis2")

# poziom dzisiejszy (0°C odchylenia) – linia przerywana przed grzbietem
linia("zero", [(X(800) - 0.6, Y_P, Z(0)), (X(0) + 0.6, Y_P, Z(0))], G.ZLOTY, 0.8, 0.014, przerywana=0.22)
et_zero = G.napis("temperatura\ndzisiejsza", 0.42, G.ZLOTY, "georgia", "LEFT", loc=(X(0) + 0.75, Y_P, Z(0)),
                  rot=(math.radians(90), 0, 0), nazwa="et_zero", odstep=0.9)
G.napis("o 9°C zimniej", 0.42, (150, 195, 245), "georgia", "LEFT", loc=(X(0) + 0.75, Y_P, Z(-9)),
        rot=(math.radians(90), 0, 0), nazwa="et_zimno")
linia("zimno", [(X(800) - 0.6, Y_P, Z(-9)), (X(0) + 0.6, Y_P, Z(-9))], (120, 170, 235), 0.45, 0.010, przerywana=0.22)

# numery epok lodowcowych nad najzimniejszymi punktami
numery = []
for i, (w, t) in enumerate(MINIMA):
    ob = G.napis(str(i + 1), 0.85, (215, 235, 255), "georgiab", "CENTER", loc=(X(w), Y_P - 0.02, Z(-5.2)),
                 rot=(math.radians(90), 0, 0), nazwa=f"nr{i+1}", obrys=((8, 20, 55), 0.03))
    numery.append((ob, w))

# ---------------------------------------------------------------- kamera
LENS = 35.0
F_LOT = 285                # koniec lotu wzdłuż wykresu
F_CALOSC = 345             # od tej klatki widok całości


def kam(f):
    # lot: kamera przesuwa się od 790 do 40 tys. lat temu
    u = G.gladko((f - 1) / float(F_LOT - 1))
    wiek_c = 770 - 720 * u
    p1 = Vector((X(wiek_c) - 1.5, -15.0, Z(T_DOL) + 7.0))
    c1 = Vector((X(wiek_c) + 0.8, 0.0, Z(-4.8)))
    p2 = Vector((1.3, -32.0, Z(T_DOL) + 9.5))
    c2 = Vector((1.3, 0.0, Z(-6.0)))
    t = G.gladko5((f - (F_LOT - 45)) / float(F_CALOSC - (F_LOT - 45)))
    return p1.lerp(p2, t), c1.lerp(c2, t), wiek_c


cam = G.kamera((0, -10, 2), (0, 0, 0), lens=LENS)
cam.data.clip_start, cam.data.clip_end = 0.05, 800
G.tlo_kamery(cam, odl=200)
ODL = 0.3
px = G.skala_px(cam, ODL)


def napis_ekran(tekst, x, y, rozm_px, kolor, kroj="georgiab", wyr="CENTER", nazwa="ekran"):
    pos = G.ekran_na_kamerze(cam, x, y, ODL)
    return G.napis(tekst, rozm_px * px, kolor, kroj, wyr, rodzic=cam, loc=pos, nazwa=nazwa,
                   obrys=((5, 7, 12), 0.03 * rozm_px * px))


tytul = napis_ekran("Temperatura z 800 tys. lat zapisana w lodzie", 1130, 78, 50, G.ZLOTY, nazwa="tytul")
zrodlo = napis_ekran("rdzeń lodowy EPICA Dome C, Antarktyda (Jouzel i in. 2007)", 1130, 130, 27, (205, 210, 225), "georgia", nazwa="zrodlo")
licznik = napis_ekran("epoki lodowcowe: 0", 1130, 196, 40, (215, 235, 255), "georgiab", nazwa="licznik")
wniosek = napis_ekran("8 epok lodowcowych; ostatnia skończyła się ok. 11,7 tys. lat temu", 960, 818, 36, (240, 232, 210),
                      "georgia", nazwa="wniosek")
G.alfa_napisu(tytul, [(1, 0), (6, 0), (28, 1)])
G.alfa_napisu(zrodlo, [(1, 0), (16, 0), (40, 1)])
G.alfa_napisu(licznik, [(1, 0), (30, 0), (50, 1)])
G.alfa_napisu(wniosek, [(1, 0), (F_CALOSC - 10, 0), (F_CALOSC + 20, 1)])

# klatka, w której kamera mija daną epokę (wtedy pojawia się numer i rośnie licznik)
def klatka_dla(wiek):
    for f in range(1, KLATEK + 1):
        if kam(f)[2] - 10 <= wiek:
            return f
    return F_LOT


KL_NR = []
for ob, w in numery:
    f0 = klatka_dla(w)
    KL_NR.append(f0)
    G.alfa_napisu(ob, [(1, 0), (f0 - 1, 0), (f0 + 14, 1)])
print("[epoki] klatki numerów:", KL_NR)


def ustaw(scene, depsgraph=None):
    f = scene.frame_current
    loc, cel, _ = kam(f)
    cam.location = loc
    G.patrz(cam, cel)
    ile = sum(1 for k in KL_NR if f >= k + 6)
    tekst = f"epoki lodowcowe: {ile}"
    licznik.data.body = tekst
    if licznik.children:
        licznik.children[0].data.body = tekst


bpy.app.handlers.frame_change_pre.append(ustaw)
ustaw(sc)
for ob in sc.objects:
    ob.visible_shadow = False

G.renderuj(TU, opcje, kadr_klatka=KLATEK)
