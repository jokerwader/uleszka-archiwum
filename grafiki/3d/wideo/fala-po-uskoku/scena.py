# -*- coding: utf-8 -*-
"""Klip „fala-po-uskoku”: ogólnoświatowe tsunami po „wielkim uskoku” (hipoteza z tekstu), wersja 2.

Według tekstu odcinka (rozdz. 02 i 06): gdy skorupa się przesunęła, wody „najpierw bezwładnie
przesunęły się w kierunku południowym, a następnie gigantycznym tsunami ruszyły z powrotem”;
fala „przetaczając się przez ląd (…) niosła z sobą olbrzymie ilości osadów i wypłukanej ziemi”.

Co widać: duży globus w stylu rysunków Leszka (zielone lądy, niebieskie morze, jak w `uskok-globus`)
po prawej, po lewej lista trzech etapów. Kamera przybliża globus (z 420 do 620 px promienia).
  1. Oceany przesuwają się na południe: drobne fale i białe strzałki suną na południe.
  2. Gigantyczna fala wraca na północ: biały grzbiet z cieniowanym wałem wody, za nim spieniona
     woda i słabsze grzbiety; fala wchodzi na lądy i zalewa wybrzeża.
  3. Woda spływa z lądów, zostają osady: zalany pas się kurczy, zostaje brązowy pas mułu.
To ilustracja hipotezy, nie symulacja: zasięg zalania zależy tylko od odległości od brzegu
(z szumem), wysokość terenu nie jest brana pod uwagę, kształt i prędkość fali są umowne.

Uruchomienie: S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/fala-po-uskoku/scena.py
              ... -- --proba 20,60,130,180,232,270,330,400
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
KADR = 232

# oś czasu (klatki)
K_ETAP1 = 12      # woda rusza na południe
K_ETAP2 = 85      # fala wraca
K_FALA = (88, 290)    # czoło fali: od 66°S do 86°N
K_ETAP3 = 284     # woda spływa
PX = 400.0        # 1 jednostka sceny = 400 px (kamera ortograficzna)


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


def swiat(x, y, glebia=0.0):
    """piksel kadru (0,0 = lewy górny) -> punkt sceny; kamera patrzy wzdłuż +Y"""
    return Vector(((x - 960) / PX, glebia, (540 - y) / PX))


sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))
img_kol = G.wczytaj_obraz(G.tekstura_ziemi(8192, G.ZIELEN_USKOK, G.MORZE_USKOK, "ziemia_uskok"))
img_odl = G.wczytaj_obraz(odleglosc_od_brzegu(), nieliniowy=False)

korzen = bpy.data.objects.new("Korzen", None)
sc.collection.objects.link(korzen)
glob = G.sfera_uv("Globus", 512, 256)
glob.parent = korzen

# ---------------------------------------------------------------- materiał globusa
mat = bpy.data.materials.new("Globus")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
W = Wezly(nt)
BIALY = G.srgb((252, 254, 255))


def szum(wektor, skala, detal=2.0):
    n = W._node("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = skala
    n.inputs["Detail"].default_value = detal
    W._in(n.inputs["Vector"], wektor)
    return n.outputs["Fac"]


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
n_duzy = szum(o, 2.2, 2.0)

# etap 1: woda bezwładnie na południe – drobne fale sunące na południe (strzałki to osobne siatki, niżej)
f1 = W.wartosc(0.0, "faza1")
przes1 = W.wartosc(0.0, "przes1")
fale1 = W.smooth(0.25, 0.95, W.math("SINE", W.mul(W.add(W.add(lat, przes1), W.mul(szum(o, 13.0, 2.0), 3.2)), 2 * math.pi / 3.4)))
plamy = W.smooth(0.40, 0.62, szum(o, 6.0, 2.0))
kol = W.mix(W.mul(W.mul(fale1, plamy), W.mul(morze, W.mul(f1, 0.34))), kol, G.srgb((175, 228, 252)))

# etap 2: czoło tsunami wraca na północ; linia czoła faluje (szum), żeby nie była równoleżnikiem
front = W.wartosc(-80.0, "front")
a_f2 = W.wartosc(0.0, "faza2")
falowanie = W.add(W.mul(W.sub(n_duzy, 0.5), 14.0), W.mul(W.sub(szum(o, 9.0, 2.0), 0.5), 4.0))
za = W.sub(W.add(front, falowanie), lat)          # > 0: fala już przeszła (stopnie)

# dolina przed falą: ciemniejsza woda (kontrast dla grzbietu)
dolina = W.mul(W.smooth(-8.0, -1.0, za), W.sub(1.0, W.smooth(-1.0, 0.2, za)))
kol = W.mix(W.mul(W.mul(dolina, a_f2), W.mul(morze, 0.5)), kol, G.srgb((0, 92, 168)))
# wał wody za grzbietem: jaśniejsza, wzburzona woda
cialo = W.mul(W.smooth(0.0, 1.5, za), W.sub(1.0, W.smooth(4.0, 28.0, za)))
kol = W.mix(W.mul(W.mul(cialo, a_f2), W.mul(morze, 0.55)), kol, G.srgb((118, 204, 245)))
# piana: smugi równoległe do grzbietu, jadą razem z falą
piana = W.smooth(0.50, 0.70, szum(W.vec(W.div(lon, 7.0), W.div(za, 1.1), 0.0), 1.0, 3.0))
zas_piany = W.mul(W.smooth(0.5, 2.5, za), W.sub(1.0, W.smooth(5.0, 30.0, za)))
kol = W.mix(W.mul(W.mul(piana, zas_piany), W.mul(morze, W.mul(a_f2, 0.75))), kol, G.srgb((236, 247, 255)))
# słabsze grzbiety za główną falą
wys_wt = None
for z_i, a_i in ((9.0, 0.62), (17.5, 0.42), (27.0, 0.26)):
    g = W.sub(1.0, W.smooth(0.25, 1.1, W.math("ABSOLUTE", W.sub(za, z_i))))
    kol = W.mix(W.mul(W.mul(g, a_i), W.mul(morze, a_f2)), kol, BIALY)
    h = W.mul(W.sub(1.0, W.smooth(0.0, 1.8, W.math("ABSOLUTE", W.sub(za, z_i)))), a_i * 0.5)
    wys_wt = h if wys_wt is None else W.add(wys_wt, h)
# główny grzbiet: biały pas; na lądzie słabszy i tylko w pasie do kilkunastu stopni od brzegu
grzbiet = W.mul(W.smooth(-0.9, 0.1, za), W.sub(1.0, W.smooth(1.2, 4.2, za)))
na_ladzie = W.mul(lad, W.mul(W.sub(1.0, W.smooth(5.0, 13.0, odl_deg)), 0.55))
kol = W.mix(W.mul(W.mul(grzbiet, W.mx(morze, na_ladzie)), a_f2), kol, BIALY)

# zalanie lądu: zasięg rośnie, gdy fala przeszła, potem woda spływa i zostają osady
zasieg_max = W.mx(W.add(3.7, W.add(W.mul(W.sub(szum(o, 3.2, 4.0), 0.5), 10.0), W.mul(W.sub(szum(o, 14.0, 3.0), 0.5), 5.0))), 0.35)   # stopnie w głąb lądu
narost = W.smooth(0.0, 12.0, za)
zostaje = W.wartosc(1.0, "zostaje")
zasieg_szczyt = W.mul(zasieg_max, narost)
zasieg = W.mul(zasieg_szczyt, zostaje)
zal_szczyt = W.mul(W.mul(lad, W.sub(1.0, W.smooth(-0.25, 0.25, W.sub(odl_deg, zasieg_szczyt)))), a_f2)
zalanie = W.mul(W.mul(lad, W.sub(1.0, W.smooth(-0.25, 0.25, W.sub(odl_deg, zasieg)))), a_f2)
osady = W.mx(W.sub(zal_szczyt, zalanie), 0.0)
kol_mulu = W.mix(szum(o, 60.0, 3.0), G.srgb((150, 122, 80)), G.srgb((190, 164, 116)))
kol = W.mix(W.mul(osady, 0.88), kol, kol_mulu)
kol = W.mix(W.mul(zalanie, 0.9), kol, G.srgb((92, 184, 238)))
# czoło wody na lądzie: jasna linia na granicy zalania
brzeg_fali = W.mul(W.mul(lad, W.sub(1.0, W.smooth(0.0, 0.55, W.math("ABSOLUTE", W.sub(odl_deg, zasieg))))),
                   W.mul(W.smooth(0.3, 1.0, zasieg), a_f2))
kol = W.mix(W.mul(brzeg_fali, 0.6), kol, G.srgb((238, 249, 255)))

# cieniowanie kuli (miękkie światło z lewej góry, jaśniejszy brzeg jak atmosfera) – jak w uskok-globus
SWIATLO = tuple(Vector((-0.45, -0.62, 0.64)).normalized())
nrm = W.geometria("Normal")
d0 = W.dot(nrm, SWIATLO)
cien = W.add(0.80, W.mul(W.mx(d0, 0.0), 0.24))
kol = W.vmath("MULTIPLY", kol, W.vec(cien, cien, cien))
# relief fali: wysokość -> wypukłość (Bump) -> jaśniejsze czoło, ciemniejszy tył wału
wys = W.add(W.mul(W.smooth(-2.5, 0.6, za), W.sub(1.0, W.smooth(0.6, 9.0, za))), wys_wt)
wys = W.mul(wys, a_f2)
bump = W._node("ShaderNodeBump")
bump.inputs["Strength"].default_value = 1.0
bump.inputs["Distance"].default_value = 0.03
W._in(bump.inputs["Height"], wys)
relief = W.sub(W.dot(bump.outputs["Normal"], SWIATLO), d0)
rel = W.math("MINIMUM", W.math("MAXIMUM", W.add(1.0, W.mul(relief, 1.15)), 0.5), 1.7)
kol = W.vmath("MULTIPLY", kol, W.vec(rel, rel, rel))
fres = W.math("POWER", W.sub(1.0, W.math("ABSOLUTE", W.dot(nrm, W.geometria("Incoming")))), 3.0)
kol = W.mix(W.mul(fres, 0.45), kol, G.srgb((170, 225, 255)))
W.emisja_wyjscie(kol)
glob.data.materials.append(mat)

# poświata wokół globusa
bpy.ops.mesh.primitive_circle_add(vertices=128, radius=1.12, fill_type="TRIFAN", location=(0, 0.3, 0),
                                  rotation=(math.radians(90), 0, 0))
pos = bpy.context.active_object
pos.name = "Poswiata"
pos.parent = korzen
mp = bpy.data.materials.new("Poswiata")
mp.use_nodes = True
mp.node_tree.nodes.clear()
W2 = Wezly(mp.node_tree)
r2 = W2.vmath("LENGTH", W2.coord("Object"))
W2.emisja_wyjscie(G.srgb((70, 150, 230)), W2.mul(W2.sub(1.0, W2.smooth(0.98, 1.12, r2)), 0.55))
mp.surface_render_method = "BLENDED"
pos.data.materials.append(mp)


# ---------------------------------------------------------------- strzałki etapu 1 (siatki na kuli)
def strzalka(nazwa, lon_s, lat_ogon, lat_grot, pol_szer=1.25, grot_dl=7.5, grot_pol=4.2, r=1.007):
    """Biała strzałka wzdłuż południka, przyklejona do globusa; zwraca (obiekt, materiał)."""
    kier = 1.0 if lat_grot > lat_ogon else -1.0
    dl = abs(lat_grot - lat_ogon)
    n = 24
    v, f = [], []
    for i in range(n + 1):
        la = lat_ogon + kier * (dl - grot_dl) * i / n
        w = pol_szer / math.cos(math.radians(la))
        v += [tuple(G.ll2xyz(la, lon_s - w, r)), tuple(G.ll2xyz(la, lon_s + w, r))]
    for i in range(n):
        f.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    lb = lat_ogon + kier * (dl - grot_dl)
    wb = grot_pol / math.cos(math.radians(lb))
    b = len(v)
    v += [tuple(G.ll2xyz(lb, lon_s - wb, r)), tuple(G.ll2xyz(lb, lon_s, r)), tuple(G.ll2xyz(lb, lon_s + wb, r)),
          tuple(G.ll2xyz(lat_grot, lon_s, r))]
    f += [(b, b + 1, b + 3), (b + 1, b + 2, b + 3)]
    me = bpy.data.meshes.new(nazwa)
    me.from_pydata(v, [], f)
    ob = bpy.data.objects.new(nazwa, me)
    sc.collection.objects.link(ob)
    ob.parent = glob
    m = G.material_emisja(nazwa + "_mat", (255, 255, 255), 0.0)
    me.materials.append(m)
    # ruch na południe = obrót wokół osi poziomej prostopadłej do południka
    ob.rotation_mode = "AXIS_ANGLE"
    os_ = (-math.sin(math.radians(lon_s)), math.cos(math.radians(lon_s)), 0.0)
    for kl, kat in ((K_ETAP1, 0.0), (K_ETAP2 + 12, 13.0)):
        ob.rotation_axis_angle = (math.radians(kat), *os_)
        ob.keyframe_insert("rotation_axis_angle", frame=kl)
    for fc in G._fcurves(ob.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    G.animuj_alfa(m, [(K_ETAP1, 0.0), (K_ETAP1 + 20, 0.92), (K_ETAP2 - 8, 0.92), (K_ETAP2 + 10, 0.0)])
    return ob


for i, (lo, la0, la1) in enumerate(((-44.0, 47.0, 22.0), (-19.0, 6.0, -19.0), (-126.0, 38.0, 13.0), (-103.0, 0.0, -25.0),
                                    (-150.0, 12.0, -13.0), (-28.0, -28.0, -50.0))):
    strzalka(f"Strzalka{i}", lo, la0, la1)

# ---------------------------------------------------------------- kamera, tło, napisy
cam = G.kamera((0, -10, 0), (0, 0, 0), orto=1920 / PX)
G.tlo_kamery(cam, odl=40)

ETAPY = (("1", "Oceany przesuwają się\nna południe", K_ETAP1, K_ETAP2),
         ("2", "Gigantyczna fala\nwraca na północ", K_ETAP2, K_ETAP3),
         ("3", "Woda spływa z lądów,\nzostają osady", K_ETAP3, None))
ROT = (math.radians(90), 0, 0)
for i, (nr, tekst, k0, k1) in enumerate(ETAPY):
    y = 322 + i * 158
    klucze = [(max(1, k0 - 14), 0.34), (k0 + 6, 1.0)]
    if k1:
        klucze += [(k1 - 14, 1.0), (k1 + 6, 0.55)]
    ob_n = G.napis(nr, 108 / PX, G.ZLOTY, "georgiab", "LEFT", loc=swiat(78, y, -3), rot=ROT, nazwa=f"Nr{nr}")
    ob_t = G.napis(tekst, 45 / PX, (238, 241, 247), "arialb", "LEFT", loc=swiat(158, y, -3), rot=ROT,
                   nazwa=f"Etap{nr}", odstep=1.12)
    G.alfa_napisu(ob_n, klucze)
    G.alfa_napisu(ob_t, klucze)
    # złota kreska pod aktywnym etapem
    bpy.ops.mesh.primitive_plane_add(size=1)
    kr = bpy.context.active_object
    kr.name = f"Kreska{nr}"
    kr.rotation_euler = ROT
    kr.scale = (500 / PX, 3 / PX, 1)
    kr.location = swiat(158 + 250, y + 66, -3)
    mk = G.material_emisja(f"Kreska{nr}_mat", G.ZLOTY, 0.0)
    kr.data.materials.append(mk)
    G.animuj_alfa(mk, [(max(1, k0 - 14), 0.0), (k0 + 6, 0.95)] + ([(k1 - 14, 0.95), (k1 + 6, 0.0)] if k1 else []))


# ---------------------------------------------------------------- ruch globusa
def orientacja(lon_c, lat_c):
    """obrót globusa: punkt (lat_c, lon_c) zwrócony do kamery (-Y), północ w górę"""
    return Matrix.Rotation(math.radians(lat_c), 4, "X") @ Matrix.Rotation(math.radians(-90 - lon_c), 4, "Z")


for f in range(1, KLATKI + 1):
    tz = G.gladko5((f - 1) / 150)                       # przybliżenie
    r_px = 420 + (620 - 420) * tz
    cx, cy = 1235 + (1312 - 1235) * tz, 452 + (470 - 452) * tz
    korzen.location = swiat(cx, cy)
    s = r_px / PX
    korzen.scale = (s, s, s)
    korzen.keyframe_insert("location", frame=f)
    korzen.keyframe_insert("scale", frame=f)
    tl = G.gladko((f - 85) / (320 - 85))                # widok idzie za falą na północ
    tt = G.gladko((f - 1) / (KLATKI - 1))
    glob.rotation_euler = orientacja(-66 + 22 * tt, 3 + 23 * tl).to_euler()
    glob.keyframe_insert("rotation_euler", frame=f)
for ob in (korzen, glob):
    for fc in G._fcurves(ob.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

# ---------------------------------------------------------------- przebieg
animuj_wartosc(nt, "faza1", [(K_ETAP1, 0.0), (K_ETAP1 + 20, 1.0), (K_ETAP2 - 8, 1.0), (K_ETAP2 + 12, 0.0)])
animuj_wartosc(nt, "przes1", [(K_ETAP1, 0.0), (K_ETAP2 + 12, 26.0)], interp="LINEAR")
animuj_wartosc(nt, "faza2", [(K_ETAP2 - 2, 0.0), (K_ETAP2 + 10, 1.0)])
animuj_wartosc(nt, "zostaje", [(K_ETAP3 + 6, 1.0), (388, 0.42)])
# ostatnie wywołanie ustawia interpolację wszystkich krzywych materiału: liniowa (stała prędkość fali)
animuj_wartosc(nt, "front", [(K_FALA[0], -66.0), (K_FALA[1], 86.0)], interp="LINEAR")

G.renderuj(TU, OPCJE, kadr_klatka=KADR)
