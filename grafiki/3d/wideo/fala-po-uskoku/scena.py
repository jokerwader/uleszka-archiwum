# -*- coding: utf-8 -*-
"""Klip „fala-po-uskoku”: schemat ogólnoświatowej fali po „wielkim uskoku” (hipoteza z tekstu).

Według tekstu odcinka (rozdz. 02 i 05–07): gdy skorupa się zatrzymała, wody „najpierw bezwładnie
przesunęły się w kierunku południowym, a następnie gigantycznym tsunami ruszyły z powrotem”;
fala przetaczała się przez lądy (Jukatan, Andy), zostawiając wodę uwięzioną w środku lądów.
To ilustracja hipotezy, nie symulacja: pasy fal biegną po oceanach na południe, potem wraca
jasny grzbiet fali na północ i zalewa pas wybrzeży (zasięg zależny od odległości od brzegu,
z lekkim szumem), na koniec woda częściowo spływa. Styl płaski jak na rysunkach Leszka
(zielone lądy, niebieskie morze), lądy z Natural Earth.

Uruchomienie: S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/fala-po-uskoku/scena.py
              ... -- --proba 30,110,200,260,400
"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector, Matrix

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
from wezly import Wezly, animuj_wartosc

OPCJE = G.argumenty()
KLATKI = 400  # 16 s


def odleglosc_od_brzegu():
    """Odległość w głąb lądu (stopnie łuku na równiku), mapa 4096×2048; 0 na morzu."""
    p = os.path.join(G.CACHE, "odl_brzeg_4096.png")
    if os.path.exists(p):
        return p
    m = G.zmniejsz(G.maska_ladu(8192, "10m"), 2) > 0.5
    H, W = m.shape
    d = np.zeros(m.shape, np.float32)
    cur = m.copy()
    for k in range(1, 141):
        # erozja na przemian 4- i 8-sąsiedztwem (odległość ośmiokątna, bez „kwadratów”), zawijanie w poziomie
        n = cur.copy()
        sas = ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (1, -1), (-1, 1), (-1, -1)) if k % 2 else ())
        for dy, dx in sas:
            sh = np.roll(cur, dx, 1)
            sh = np.roll(sh, dy, 0)
            n &= sh
        d[cur & ~n] = k
        cur = n
        if not cur.any():
            break
    d[cur] = 141
    d = G.rozmyj(G.rozmyj(d, 2), 2)
    deg = d * (360.0 / W)            # piksele -> stopnie
    a = np.zeros((H, W, 4), np.float32)
    a[..., 0] = np.clip(deg / 12.0, 0, 1)  # 0..12° w kanale R
    a[..., 1] = m.astype(np.float32)
    a[..., 3] = 1
    G.zapisz_png(a, p)
    return p


sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))
img_kol = G.wczytaj_obraz(G.tekstura_ziemi(8192, G.ZIELEN_USKOK, G.MORZE_USKOK, "ziemia_uskok"))
img_odl = G.wczytaj_obraz(odleglosc_od_brzegu(), nieliniowy=False)

glob = G.sfera_uv("Globus", 512, 256)
mat = bpy.data.materials.new("Globus")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
W = Wezly(nt)
uv = W.coord("UV")
kol, _ = W.obraz(img_kol, uv)
od, _ = W.obraz(img_odl, uv)
odl_r, lad, _ = W.sep(od)
odl_deg = W.mul(odl_r, 12.0)
o = W.norm(W.coord("Object"))
ox, oy, oz = W.sep(o)
lat = W.mul(W.math("ARCSINE", oz), 180 / math.pi)
lon = W.mul(W.math("ARCTAN2", oy, ox), 180 / math.pi)
morze = W.sub(1.0, lad)

# faza 1: woda bezwładnie na południe – jasne pasy przesuwające się na południe
f1 = W.wartosc(0.0, "faza1")          # siła faz 1 (0..1)
przes1 = W.wartosc(0.0, "przes1")     # przesunięcie pasów (stopnie)
pas = W.math("SINE", W.mul(W.add(lat, przes1), 2 * math.pi / 14.0))
pas = W.smooth(0.55, 0.95, pas)
kol = W.mix(W.mul(W.mul(pas, f1), W.mul(morze, 0.45)), kol, G.srgb((150, 215, 250)))


def szewrony(lat_s, lon_s, przes, na_polnoc, rozmiar=11.0):
    cu = W.math("FRACT", W.div(lon_s, rozmiar * 1.6))
    cv = W.math("FRACT", W.div(W.add(lat_s, przes), rozmiar))
    du = W.math("ABSOLUTE", W.sub(cu, 0.5))
    if na_polnoc:
        v = W.add(W.sub(cv, 0.55), W.mul(du, 0.75))
    else:
        v = W.sub(W.sub(cv, 0.45), W.mul(du, 0.75))
    m = W.sub(1.0, W.smooth(0.035, 0.06, W.math("ABSOLUTE", v)))
    return W.mul(m, W.sub(1.0, W.smooth(0.24, 0.27, du)))


sz1 = szewrony(lat, lon, przes1, False)
kol = W.mix(W.mul(W.mul(sz1, f1), W.mul(morze, 0.9)), kol, G.srgb((255, 255, 255)))

# faza 2: grzbiet tsunami wraca na północ (szerokość czoła fali = front)
front = W.wartosc(-80.0, "front")
za = W.sub(front, lat)                         # >0: fala już przeszła
grzbiet = W.mul(W.smooth(-3.0, 0.0, za), W.sub(1.0, W.smooth(0.0, 2.2, za)))
spieniona = W.mul(W.smooth(0.0, 1.0, za), W.sub(1.0, W.smooth(2.0, 22.0, za)))
a_f2 = W.wartosc(0.0, "faza2")
kol = W.mix(W.mul(W.mul(spieniona, a_f2), W.mul(morze, 0.55)), kol, G.srgb((140, 212, 248)))
sz2 = szewrony(lat, lon, W.mul(front, -1.0), True)
pas_sz = W.mul(W.smooth(1.0, 4.0, za), W.sub(1.0, W.smooth(9.0, 14.0, za)))
kol = W.mix(W.mul(W.mul(sz2, pas_sz), W.mul(morze, W.mul(a_f2, 0.9))), kol, G.srgb((255, 255, 255)))
grzbiet_woda = W.mul(grzbiet, W.mx(morze, W.mul(lad, W.smooth(0.0, 0.6, W.sub(2.0, odl_deg)))))
kol = W.mix(W.mul(grzbiet_woda, a_f2), kol, G.srgb((250, 253, 255)))

# zalanie lądu: zasięg rośnie, gdy fala przeszła, potem woda częściowo spływa
szum = W._node("ShaderNodeTexNoise")
szum.inputs["Scale"].default_value = 3.2
szum.inputs["Detail"].default_value = 4.0
W.nt.links.new(o, szum.inputs["Vector"])
zasieg_max = W.add(3.4, W.mul(W.sub(szum.outputs["Fac"], 0.5), 6.0))   # stopnie w głąb lądu
narost = W.smooth(0.0, 14.0, za)
splyw = W.wartosc(1.0, "zostaje")             # 1 -> 0.45 pod koniec
zasieg = W.mul(W.mul(zasieg_max, narost), splyw)
zalanie = W.mul(lad, W.sub(1.0, W.smooth(-0.25, 0.25, W.sub(odl_deg, zasieg))))
zalanie = W.mul(zalanie, a_f2)
kol = W.mix(W.mul(zalanie, 0.88), kol, G.srgb((95, 185, 238)))
# czoło fali na lądzie: jaśniejsza linia przy granicy zalania
brzeg_fali = W.mul(W.mul(lad, W.sub(1.0, W.smooth(0.0, 0.6, W.math("ABSOLUTE", W.sub(odl_deg, zasieg))))),
                   W.mul(W.smooth(0.3, 1.0, zasieg), a_f2))
kol = W.mix(W.mul(brzeg_fali, 0.45), kol, G.srgb((235, 248, 255)))

# cieniowanie
nrm = W.geometria("Normal")
sw = W.dot(nrm, tuple(Vector((-0.5, -0.7, 0.55)).normalized()))
cien = W.add(0.66, W.mul(W.mx(sw, 0.0), 0.42))
kol = W.vmath("MULTIPLY", kol, W.vec(cien, cien, cien))
fres = W.math("POWER", W.sub(1.0, W.math("ABSOLUTE", W.dot(nrm, W.geometria("Incoming")))), 2.5)
kol = W.mix(W.mul(fres, 0.5), kol, G.srgb((150, 215, 255)))
W.emisja_wyjscie(kol)
glob.data.materials.append(mat)

# poświata za globusem
bpy.ops.mesh.primitive_circle_add(vertices=128, radius=1.12, fill_type="TRIFAN", location=(0, 0.3, 0),
                                  rotation=(math.radians(90), 0, 0))
mp = bpy.data.materials.new("Poswiata")
mp.use_nodes = True
mp.node_tree.nodes.clear()
W2 = Wezly(mp.node_tree)
r2 = W2.vmath("LENGTH", W2.coord("Object"))
W2.emisja_wyjscie(G.srgb((60, 140, 225)), W2.mul(W2.sub(1.0, W2.smooth(0.9, 1.12, r2)), 0.5))
mp.surface_render_method = "BLENDED"
bpy.context.active_object.data.materials.append(mp)

# kamera z przodu (-Y); globus obraca się tak, by widok przeszedł z obu Ameryk na Atlantyk
cam = G.kamera((0, -7.2, 0), (0, 0, 0), lens=50)
cam.data.shift_y = -0.04
G.tlo_kamery(cam, odl=40)


def orientacja(lon_c, lat_c):
    """obrót globusa: punkt (lat_c, lon_c) zwrócony do kamery (-Y), północ w górę"""
    return Matrix.Rotation(math.radians(lat_c), 4, "X") @ Matrix.Rotation(math.radians(-90 - lon_c), 4, "Z")


for f in range(1, KLATKI + 1):
    t = G.gladko((f - 1) / (KLATKI - 1))
    glob.matrix_world = orientacja(-82 + 40 * t, 14 + 4 * t)
    glob.keyframe_insert("rotation_euler", frame=f)
for fc in G._fcurves(glob.animation_data.action):
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"

# przebieg
animuj_wartosc(nt, "faza1", [(35, 0.0), (60, 1.0), (125, 1.0), (150, 0.0)])
animuj_wartosc(nt, "przes1", [(35, 0.0), (150, 40.0)], interp="LINEAR")
animuj_wartosc(nt, "faza2", [(140, 0.0), (150, 1.0)])
animuj_wartosc(nt, "front", [(145, -75.0), (315, 88.0)], interp="LINEAR")
animuj_wartosc(nt, "zostaje", [(300, 1.0), (380, 0.5)])

G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
