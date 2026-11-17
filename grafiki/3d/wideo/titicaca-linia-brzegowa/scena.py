# -*- coding: utf-8 -*-
"""Klip „titicaca-linia-brzegowa”: dawna linia brzegowa jeziora Titicaca nachylona do dzisiejszego lustra wody.

Rozdz. „Jak to wygląda w praktyce?” (Tiahuanaco): „Odnaleziono tu poprzednią linię brzegową nachyloną w stosunku
do dzisiejszej. Gdyby jezioro wysychało w niezmiennych warunkach, to stara linia brzegowa byłaby równoległa
do dzisiejszego lustra wody, a nie jest.”

Schemat (nie mapa): górska kotlina z jeziorem. 1) jezioro stoi wyżej; 2) woda opada, na zboczach zostaje biała
przerywana linia dawnego brzegu – równoległa do lustra wody (tak byłoby, „gdyby jezioro wysychało w niezmiennych
warunkach”); 3) złota linia – dawny brzeg według tekstu – odchyla się od białej: z jednej strony jeziora leży wyżej,
z drugiej niżej. Nachylenie jest mocno przesadzone, żeby było je widać.

Uruchomienie: S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/titicaca-linia-brzegowa/scena.py
              ... -- --proba 1,120,250,400
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
KLATKI = 400                      # 16 s
XB, YB, DNO = 6.2, 3.4, -0.95      # połowy wymiarów bloku, spód
H_DAWNY, H_DZIS = 0.62, 0.0       # poziom wody dawniej i dziś
K_MAX = 0.085                     # nachylenie złotej linii (przyrost wysokości na jednostkę długości) – przesadzone
F_OPAD0, F_OPAD1 = 45, 150        # woda opada
F_NACH0, F_NACH1 = 205, 300       # złota linia się nachyla
ZLOTY = G.ZLOTY
SHIFT = 0.06

rng = np.random.default_rng(7)
FALE = [(rng.uniform(0.5, 2.6), rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi)) for _ in range(26)]


def szum(X, Y):
    s = np.zeros_like(X)
    for k, kier, faza in FALE:
        s += np.sin(k * (X * math.cos(kier) + Y * math.sin(kier)) + faza) / k
    return s / 10.0


def wys(X, Y):
    """kotlina: dno jeziora pośrodku, góry dookoła (im wyżej, tym bardziej poszarpane)"""
    r = np.sqrt((X / 5.3) ** 2 + (Y / 2.75) ** 2)
    baza = -0.95 + 2.2 * np.clip(r, 0, 1.2) ** 2.3
    gory = np.clip((r - 0.72) / 0.4, 0, 1)
    gory = gory * gory * (3 - 2 * gory)
    z = baza + szum(X, Y) * (0.12 + 1.1 * gory) + 1.6 * gory * np.abs(szum(X * 1.9 + 3.1, Y * 1.9 - 1.7))
    # od strony kamery (y < 0) góry są niższe, żeby było widać jezioro; z tyłu wyższe
    przod = np.clip(-Y / YB, 0, 1)
    tyl = np.clip(Y / YB, 0, 1)
    prog = 1.12
    z = np.where(z > prog, prog + (z - prog) * (1.0 - 0.8 * przod + 0.1 * tyl), z)
    return np.where(z > 1.8, 1.8 + 0.55 * np.tanh((z - 1.8) / 0.55), z)      # łagodne ścięcie najwyższych szczytów


sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))
S.swiatlo(kat=(55, 0, 40), sila=3.0, otoczenie=(160, 180, 220), moc=0.55)


def principled(Wm, kolor, emis_kolor=None, emis_sila=None, szorst=0.85):
    out = Wm._node("ShaderNodeOutputMaterial")
    b = Wm._node("ShaderNodeBsdfPrincipled")
    Wm._in(b.inputs["Base Color"], kolor)
    b.inputs["Roughness"].default_value = szorst
    if emis_kolor is not None:
        Wm._in(b.inputs["Emission Color"], emis_kolor)
        Wm._in(b.inputs["Emission Strength"], emis_sila)
    Wm.nt.links.new(b.outputs[0], out.inputs["Surface"])


# ---------------------------------------------------------------- teren
m_ter = bpy.data.materials.new("Teren")
m_ter.use_nodes = True
m_ter.node_tree.nodes.clear()
W = Wezly(m_ter.node_tree)
x, y, z = W.sep(W.geometria("Position"))
nz = W._node("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 3.0
nz.inputs["Detail"].default_value = 6.0
W.nt.links.new(W.geometria("Position"), nz.inputs["Vector"])
zz = W.add(z, W.mul(W.sub(nz.outputs[0], 0.5), 0.35))
kol = W.mix(W.smooth(0.3, 1.3, zz), G.srgb((186, 164, 110)), G.srgb((124, 100, 78)))      # altiplano -> skała
kol = W.mix(W.smooth(1.6, 2.0, zz), kol, G.srgb((244, 247, 252)))                        # śnieg na szczytach
dawne_dno = W.sub(1.0, W.smooth(H_DAWNY - 0.02, H_DAWNY + 0.02, z))
kol = W.mix(W.mul(dawne_dno, 0.75), kol, G.srgb((212, 204, 172)))                          # odsłonięte dno dawnego jeziora
# biała przerywana linia: dawny brzeg równoległy do lustra wody
biala = W.wartosc(0.0, "biala")
pas1 = W.math("LESS_THAN", W.math("ABSOLUTE", W.sub(z, H_DAWNY)), 0.032)
kreska = W.math("LESS_THAN", W.math("FRACT", W.mul(W.math("ARCTAN2", y, x), 46 / (2 * math.pi))), 0.6)
f1 = W.mul(W.mul(pas1, kreska), biala)
# złota linia: dawny brzeg nachylony (z = H_DAWNY + K * x)
zlota = W.wartosc(0.0, "zlota")
K = W.wartosc(0.0, "K")
pas2 = W.math("LESS_THAN", W.math("ABSOLUTE", W.sub(z, W.add(H_DAWNY, W.mul(K, x)))), 0.04)
f2 = W.mul(pas2, zlota)
kol = W.mix(f1, kol, G.srgb((255, 255, 255)))
kol = W.mix(f2, kol, G.srgb(ZLOTY))
emis = W.mix(f2, G.srgb((255, 255, 255)), G.srgb(ZLOTY))
principled(W, kol, emis, W.mx(W.mul(f1, 0.9), W.mul(f2, 1.2)), 0.9)
animuj_wartosc(m_ter.node_tree, "biala", [(F_OPAD0 + 8, 0.0), (F_OPAD0 + 30, 1.0)])
animuj_wartosc(m_ter.node_tree, "zlota", [(F_NACH0 - 30, 0.0), (F_NACH0 - 8, 1.0)])
animuj_wartosc(m_ter.node_tree, "K", [(F_NACH0, 0.0), (F_NACH1, K_MAX)])

m_bok = S.mat("Bok", (74, 58, 48), 0.95)
teren = S.teren("Kotlina", wys, -XB, XB, -YB, YB, 311, 171, DNO, m_ter, m_bok)

# ---------------------------------------------------------------- woda
m_woda = S.mat("Woda", (34, 104, 170), 0.12, alfa=0.86)
S.bsdf(m_woda).inputs["Emission Color"].default_value = G.srgb((30, 96, 160))
S.bsdf(m_woda).inputs["Emission Strength"].default_value = 0.25
woda = S.siatka("Woda", [(-XB + 0.3, -YB + 0.3, 0), (XB - 0.3, -YB + 0.3, 0), (XB - 0.3, YB - 0.3, 0), (-XB + 0.3, YB - 0.3, 0)],
                [(0, 1, 2, 3)], [m_woda])
woda.visible_shadow = False
S.klucze(woda, "location", [(1, (0, 0, H_DAWNY)), (F_OPAD0, (0, 0, H_DAWNY)), (F_OPAD1, (0, 0, H_DZIS))])

# złota półprzezroczysta płaszczyzna dawnego lustra wody – nachyla się razem ze złotą linią
m_pl = G.material_emisja("Plaszczyzna_dawna", ZLOTY, 0.0)
pl = S.siatka("Dawne_lustro", [(-XB + 0.3, -YB + 0.3, 0), (XB - 0.3, -YB + 0.3, 0), (XB - 0.3, YB - 0.3, 0), (-XB + 0.3, YB - 0.3, 0)],
              [(0, 1, 2, 3)], [m_pl])
pl.visible_shadow = False
pl.location = (0, 0, H_DAWNY)
G.animuj_alfa(m_pl, [(F_NACH0 - 30, 0.0), (F_NACH0 - 8, 0.11)])
S.klucze(pl, "rotation_euler", [(F_NACH0, (0, 0, 0)), (F_NACH1, (0, -math.atan(K_MAX), 0))])

# ---------------------------------------------------------------- kamera
cam = G.kamera((0, -20, 9), (0, 0, 0), lens=50)
cam.data.shift_y = -SHIFT
cam.data.clip_start, cam.data.clip_end = 2.0, 200.0


def tor(f):
    d = (f - 1) / (KLATKI - 1)
    t = G.gladko(d)
    return (-104 + 26 * t, 30 - 7 * t, 28.5 - 2.0 * t)


S.orbita_f(cam, (0.0, 0.1, 1.0), tor, KLATKI)
G.tlo_kamery(cam, odl=120)

# ---------------------------------------------------------------- podpisy
OBR = ((8, 12, 24), 0.05)
S.podpis("jezioro Titicaca", 0.5, (255, 255, 255), (0.2, 0.9, 1.5), cam, 10, obrys=OBR, nazwa="Pod_jezioro")
t = S.podpis("dawny poziom wody", 0.4, (255, 255, 255), (-0.2, -0.6, 0.95), cam, None, obrys=OBR, nazwa="Pod_dawny")
G.alfa_napisu(t, [(1, 1.0), (F_OPAD0 + 10, 1.0), (F_OPAD0 + 30, 0.0)])
S.podpis("dzisiejsze lustro wody", 0.4, (190, 225, 255), (-0.1, 0.5, 0.3), cam, F_OPAD1 - 12, obrys=OBR, nazwa="Pod_dzis")

# objaśnienia przypięte do kamery (prawa górna część kadru), słowa z tekstu Leszka
ODL = 7.0
px1 = G.skala_px(cam, ODL)
m_b = G.material_emisja("Leg_biala", (255, 255, 255))
m_z = G.material_emisja("Leg_zlota", ZLOTY)


def objasnienie(nazwa, tekst, y_px, kolor, mat_, f0, przerywana):
    y = y_px + SHIFT * 1920
    x0 = 1010
    for k in range(3 if przerywana else 1):
        a = x0 + (k * 26 if przerywana else 0)
        dl = 16 if przerywana else 68
        p = G.ekran_na_kamerze(cam, a + dl / 2, y, ODL)
        kr = S.siatka(f"{nazwa}_kr{k}", [(-dl / 2 * px1, -3 * px1, 0), (dl / 2 * px1, -3 * px1, 0), (dl / 2 * px1, 3 * px1, 0), (-dl / 2 * px1, 3 * px1, 0)],
                      [(0, 1, 2, 3)], [mat_])
        kr.parent = cam
        kr.location = p
    tx = G.napis(tekst, 29 * px1, kolor, "arialb", "LEFT", rodzic=cam, loc=tuple(G.ekran_na_kamerze(cam, x0 + 88, y, ODL)),
                 nazwa=nazwa, odstep=1.12)
    G.alfa_napisu(tx, [(f0 - 1, 0.0), (f0, 0.0), (f0 + 16, 1.0)])
    return tx


# ciemne tło pod objaśnieniami (góry w tle są jasne)
m_panel = G.material_emisja("Leg_panel", (10, 16, 34), 0.0)
pa, pb = G.ekran_na_kamerze(cam, 985, 52 + SHIFT * 1920, ODL + 0.05), G.ekran_na_kamerze(cam, 1575, 232 + SHIFT * 1920, ODL + 0.05)
panel = S.siatka("Leg_panel", [(pa.x, pb.y, pa.z), (pb.x, pb.y, pa.z), (pb.x, pa.y, pa.z), (pa.x, pa.y, pa.z)], [(0, 1, 2, 3)], [m_panel])
panel.parent = cam
G.animuj_alfa(m_panel, [(F_OPAD0 + 14, 0.0), (F_OPAD0 + 30, 0.78)])
G.animuj_alfa(m_b, [(F_OPAD0 + 20, 0.0), (F_OPAD0 + 36, 1.0)])
G.animuj_alfa(m_z, [(F_NACH0 - 22, 0.0), (F_NACH0 - 6, 1.0)])
objasnienie("Obj_biala", "gdyby jezioro tylko wysychało, stara linia" + chr(10) + "brzegowa byłaby równoległa do lustra wody",
            92, (255, 255, 255), m_b, F_OPAD0 + 20, True)
objasnienie("Obj_zlota", "odnaleziona stara linia brzegowa" + chr(10) + "jest nachylona do dzisiejszej",
            188, ZLOTY, m_z, F_NACH0 - 22, False)
tx = G.napis("nachylenie pokazane z dużą przesadą", 23 * px1, (170, 180, 200), "arial", "RIGHT", rodzic=cam,
             loc=tuple(G.ekran_na_kamerze(cam, 1880, 852 + SHIFT * 1920, ODL)), nazwa="Uwaga")
G.alfa_napisu(tx, [(F_NACH1 - 20, 0.0), (F_NACH1, 1.0)])

G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
