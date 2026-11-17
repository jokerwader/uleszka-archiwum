# -*- coding: utf-8 -*-
"""
Klip „zacmienie-slonca” do odcinka 2 „Wielki uskok…” (rozdz. 12: „Skąd więc u Majów tak dokładne tabele zaćmień?”).

Całkowite zaćmienie Słońca z 16 lipca 790 r. (kalendarz juliański) – to, które Majowie zapisali na steli 3
w Santa Elena Poco Uinic. Wszystko, co się w klipie rusza, jest policzone z elementów Bessela NASA
(Fred Espenak, „Five Millennium Canon of Solar Eclipses”) wzorami z bessel.py:
  * położenie Księżyca i Słońca względem Ziemi (w skali), obrót Ziemi, kierunek światła,
  * półcień i cień na Ziemi (zakryta część tarczy Słońca liczona w shaderze dla każdego punktu elipsoidy),
  * granice pasa całkowitości,
  * widok z ziemi: tarcze Słońca i Księżyca, ich rozmiary i ruch, gwiazdy (HYG, z precesją) i planety (JPL Horizons).
Umowne są tylko: brak chmur, odblask w oceanie, wygląd korony (zdjęcie zaćmienia z 1999 r.) i kolory nieba.

Trzy ujęcia (18 s, 450 klatek):
  1. klatki 1–140: widok od strony Słońca z 1,5 mln km, teleobiektyw; Księżyc i Ziemia w prawdziwej skali,
  2. klatki 140–335: dolot nad Amerykę Środkową, cień sunie wzdłuż wybrzeża Pacyfiku, miasta Majów,
  3. klatki 336–450: widok z ziemi ze środka pasa (14,50°N, 91,74°W): ostatni błysk Słońca, korona, podpis o kodeksie.

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/zacmienie-slonca/scena.py
  ... -- --proba 1,75,150,180,230,300,340,372,400,450     (tylko kadry próbne PNG do _klatki/)
"""
import bpy, json, math, os, sys
import numpy as np
from mathutils import Vector, Matrix, Quaternion

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TU)
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
import niebo as N
import wezly
import bessel as BS

KLATEK = 450
F_C = 336                       # pierwsza klatka widoku z ziemi
opcje = G.argumenty()
sc = G.nowa_scena(KLATEK)
sc.eevee.taa_render_samples = int(os.environ.get("USKOK3D_PROBKI", "32"))

# ================================================================ rachunek zaćmienia
NASA = os.path.join(G.DANE, "zacmienie-0790", "nasa_SEsearchmap_07900716.html")
Z, _meta = BS.z_tablicy_nasa(NASA, "0790-07-16")
T_A, T_B = Z.zakres_osi()
LON_M = -91.739                                   # południk steli w Santa Elena Poco Uinic
T_M = Z.czas_nad_dlugoscia(LON_M, T_A + 0.03, T_B - 0.03)
LAT_M = Z.os_cienia(T_M)["lat"]                   # miejsce widoku z ziemi: środek pasa na tym południku
OK_M = Z.okolicznosci(LAT_M, LON_M)
C2, C3, T_MAX = OK_M["c2"], OK_M["c3"], OK_M["t_max"]
TRWANIE = (C3 - C2) * 3600.0
print("[zacmienie] miejsce %.3fN %.3fW, C2 %s UT, całkowite %.0f s, Słońce %.0f° nad horyzontem"
      % (LAT_M, -LON_M, BS.hms(Z.ut(C2)), TRWANIE, OK_M["wys"]))

# Słońce i planety: JPL Horizons (DE441), geocentrycznie, 16 VII 790, 20:29:30 TT (pliki w _dane/zacmienie-0790/horizons)
SLONCE_RA, SLONCE_RA_T, SLONCE_RA_NA_H = 118.963426, 20.4915565, 0.0424      # rektascensja pozorna [°], chwila [h TDT], zmiana [°/h]
PLANETY = [dict(nazwa="Merkury", ra=117.935912 / 15, dec=20.668324, mag=-0.59, ci=0.9),   # współrzędne ICRF (J2000)
           dict(nazwa="Wenus", ra=167.314933 / 15, dec=6.966829, mag=-3.91, ci=0.7)]
JD_M = 2009801.5 + T_M / 24.0


def geo(lat, lon, h=0.0):
    """Punkt na elipsoidzie Ziemi (szer. geodezyjna) w układzie ziemskim; h = wysokość w promieniach Ziemi."""
    fi, la = math.radians(lat), math.radians(lon)
    u = math.atan(BS.B_A * math.tan(fi))
    p = Vector((math.cos(u) * math.cos(la), math.cos(u) * math.sin(la), BS.B_A * math.sin(u)))
    n = Vector((math.cos(fi) * math.cos(la), math.cos(fi) * math.sin(la), math.sin(fi)))
    return p + n * h


def enu(lat, lon):
    """Wersory wschód, północ, zenit w miejscu (układ ziemski)."""
    fi, la = math.radians(lat), math.radians(lon)
    e = Vector((-math.sin(la), math.cos(la), 0.0))
    n = Vector((-math.sin(fi) * math.cos(la), -math.sin(fi) * math.sin(la), math.cos(fi)))
    u = Vector((math.cos(fi) * math.cos(la), math.cos(fi) * math.sin(la), math.sin(fi)))
    return e, n, u


def precesja_j2000(jd):
    """Macierz 3×3: współrzędne równikowe J2000 -> równik i równonoc daty (Meeus, „Astronomical Algorithms”, wzory 21.2–21.4)."""
    T = (jd - 2451545.0) / 36525.0
    s = math.radians(1 / 3600.0)
    zeta = (2306.2181 * T + 0.30188 * T * T + 0.017998 * T ** 3) * s
    zz = (2306.2181 * T + 1.09468 * T * T + 0.018203 * T ** 3) * s
    th = (2004.3109 * T - 0.42665 * T * T - 0.041833 * T ** 3) * s

    def f(v):
        a0, d0 = math.atan2(v[1], v[0]), math.asin(max(-1, min(1, v[2])))
        A = math.cos(d0) * math.sin(a0 + zeta)
        Bb = math.cos(th) * math.cos(d0) * math.cos(a0 + zeta) - math.sin(th) * math.sin(d0)
        C = math.sin(th) * math.cos(d0) * math.cos(a0 + zeta) + math.cos(th) * math.sin(d0)
        a, d = math.atan2(A, Bb) + zz, math.asin(max(-1, min(1, C)))
        return Vector((math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d)))
    return Matrix((f((1, 0, 0)), f((0, 1, 0)), f((0, 0, 1)))).transposed()


PREC = precesja_j2000(JD_M)
_s = PREC @ N.eq(136.254016869 / 15, 16.803470830)       # sprawdzenie: Słońce ICRF -> data; Horizons: 118,963° / 20,914°
print("[precesja] Słońce J2000 -> data: %.3f° %.3f° (Horizons, pozorne: 118.963° 20.914°)"
      % (math.degrees(math.atan2(_s.y, _s.x)) % 360, math.degrees(math.asin(_s.z))))


def czas_gwiazdowy(t):
    """Czas gwiazdowy Greenwich [°] w chwili t: kąt godzinny osi cienia + rektascensja Słońca."""
    return Z.kat_godzinny_osi(t) + SLONCE_RA + SLONCE_RA_NA_H * (t - SLONCE_RA_T)


def niebo_na_horyzont(t):
    """Macierz 3×3: równikowe J2000 -> układ horyzontalny miejsca widoku (x = wschód, y = północ, z = zenit)."""
    e, n, u = enu(LAT_M, LON_M)
    return Matrix((e, n, u)) @ Matrix.Rotation(-math.radians(czas_gwiazdowy(t)), 3, "Z") @ PREC


# ---------------------------------------------------------------- oś czasu klipu
def _odcinki(kl, f):
    for (f0, t0), (f1, t1) in zip(kl, kl[1:]):
        if f <= f1:
            return t0 + (t1 - t0) * (f - f0) / (f1 - f0)
    return kl[-1][1]


_KL = [(-30, 18.30 - 31 * 0.0087), (1, 18.30), (150, 19.60), (205, 19.95), (330, C2 - 90 / 3600.0), (335, C2 - 90 / 3600.0)]
_surowe = {f: _odcinki(_KL, f) for f in range(-30, 380)}


def czas(f):
    """Godzina TDT pokazywana w klatce f."""
    if f < F_C:
        w = range(max(-30, f - 10), min(335, f + 10) + 1)        # wygładzenie przejść między tempami
        return sum(_surowe[min(335, g)] for g in w) / len(w)
    if f <= 372:
        return C2 + (-90.0 + (f - F_C) / 36.0 * 92.0) / 3600.0
    s = (f - 372) / float(KLATEK - 372)
    return C2 + (2.0 + ((T_MAX - C2) * 3600.0 - 2.0) * (1 - (1 - s) ** 2)) / 3600.0


W = wezly.Wezly

# ================================================================ UJĘCIA 1–2: KOSMOS
# ---------------------------------------------------------------- puste obiekty: Słońce i oś cienia
e_slonce = bpy.data.objects.new("srodek_Slonca", None)
e_os = bpy.data.objects.new("os_cienia", None)          # początek w środku Księżyca, lokalne z = ku Słońcu
for o in (e_slonce, e_os):
    sc.collection.objects.link(o)


# ---------------------------------------------------------------- Ziemia (elipsoida)
def elipsoida(nazwa, nlon, nlat, skala=1.0):
    me = bpy.data.meshes.new(nazwa)
    verts, faces, uv = [], [], []
    for j in range(nlat + 1):
        lat = -90 + 180 * j / nlat
        for i in range(nlon + 1):
            verts.append(tuple(geo(lat, -180 + 360 * i / nlon) * skala))
    for j in range(nlat):
        for i in range(nlon):
            a = j * (nlon + 1) + i
            faces.append((a, a + 1, a + nlon + 2, a + nlon + 1))
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UV")
    for f in me.polygons:
        for li in f.loop_indices:
            j, i = divmod(me.loops[li].vertex_index, nlon + 1)
            uv.extend((i / nlon, j / nlat))
    uvl.data.foreach_set("uv", uv)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new(nazwa, me)
    sc.collection.objects.link(ob)
    return ob


ziemia = elipsoida("Ziemia", 720, 360)
mz = bpy.data.materials.new("Ziemia_mat"); mz.use_nodes = True
mz.node_tree.nodes.clear()
w = W(mz.node_tree)
uvn = w._node("ShaderNodeUVMap").outputs[0]
img_g = G.wczytaj_obraz(os.path.join(G.DANE, "blue-marble", "bmng-200407-8192x4096.jpg"))
img_r = G.wczytaj_obraz(os.path.join(G.DANE, "blue-marble", "bmng-200407-ameryka-srodkowa-114W-78W-4N-28N.jpg"))
kol_g, _ = w.obraz(img_g, uvn, ext="EXTEND")
u_, v_, _ = w.sep(uvn)
ur = w.sub(w.mul(u_, 10.0), 66.0 / 36.0)                       # wycinek 114°W–78°W, 4°N–28°N w większej rozdzielczości
vr = w.sub(w.mul(v_, 7.5), 94.0 / 24.0)
kol_r, _ = w.obraz(img_r, w.vec(ur, vr, 0.0), ext="EXTEND")
maska_r = w.mul(w.mul(w.smooth(0.0, 0.05, ur), w.smooth(0.0, 0.05, w.sub(1.0, ur))),
                w.mul(w.smooth(0.0, 0.05, vr), w.smooth(0.0, 0.05, w.sub(1.0, vr))))
kol = w.mix(maska_r, kol_g, kol_r)
nrm = w.geometria("Normal")
# światło: kierunek od punktu powierzchni do środka Słońca
tc_s = w._node("ShaderNodeTexCoord"); tc_s.object = e_slonce
L = w.scale(w.norm(tc_s.outputs["Object"]), -1.0)
cosl = w.dot(nrm, L)
dzien = w.math("POWER", w.math("MAXIMUM", cosl, 0.0), 0.5)
# zakryta część tarczy Słońca w tym punkcie Ziemi (te same wzory co bessel.zakrycie_tarcz)
tc_o = w._node("ShaderNodeTexCoord"); tc_o.object = e_os
qx, qy, qz = w.sep(tc_o.outputs["Object"])
delta = w.math("SQRT", w.add(w.mul(qx, qx), w.mul(qy, qy)))    # odległość od osi cienia
gl = w.mul(qz, -1.0)                                            # odległość od Księżyca wzdłuż osi
sec1, sec2 = math.sqrt(1 + Z.tan_f1 ** 2), math.sqrt(1 + Z.tan_f2 ** 2)
L1 = w.add(w.mul(gl, Z.tan_f1), Z.k1 * sec1)                    # promień półcienia na tej głębokości
L2 = w.sub(w.mul(gl, Z.tan_f2), Z.k2 * sec2)                    # promień cienia (ujemny = zaćmienie całkowite)
suma = w.add(L1, L2)
s_ = w.math("MAXIMUM", w.div(w.mul(delta, 2.0), suma), 1e-5)    # odstęp środków tarcz w promieniach Słońca
A_ = w.div(w.sub(L1, L2), suma)                                 # promień tarczy Księżyca w promieniach Słońca
ss, AA = w.mul(s_, s_), w.mul(A_, A_)
a1 = w.math("ARCCOSINE", w.math("MINIMUM", w.math("MAXIMUM", w.div(w.sub(w.add(ss, 1.0), AA), w.mul(s_, 2.0)), -1.0), 1.0))
a2 = w.math("ARCCOSINE", w.math("MINIMUM", w.math("MAXIMUM", w.div(w.sub(w.add(ss, AA), 1.0), w.mul(w.mul(s_, 2.0), A_)), -1.0), 1.0))
il = w.mul(w.mul(w.add(w.sub(1.0, s_), A_), w.sub(w.add(s_, 1.0), A_)),
           w.mul(w.add(w.sub(s_, 1.0), A_), w.add(w.add(s_, 1.0), A_)))
pole = w.sub(w.add(a1, w.mul(AA, a2)), w.mul(w.math("SQRT", w.math("MAXIMUM", il, 0.0)), 0.5))
zakr = w.math("MINIMUM", w.math("MAXIMUM", w.div(pole, math.pi), 0.0), 1.0)
slonca = w.math("POWER", w.sub(1.0, zakr), 0.7)                 # odsłonięta część tarczy; wykładnik 0,7 = krzywa tonalna (mapa czytelna w półcieniu)
jasn = w.add(w.mul(w.mul(dzien, slonca), 1.30), 0.004)
# odblask Słońca w oceanie (umowny, model Blinna–Phonga) i mgiełka atmosfery przy brzegu tarczy
V = w.geometria("Incoming")
sepc = w._node("ShaderNodeSeparateColor")
mz.node_tree.links.new(kol, sepc.inputs[0])
r_, g_, b_ = sepc.outputs[0], sepc.outputs[1], sepc.outputs[2]
woda = w.smooth(0.01, 0.06, w.sub(b_, w.math("MAXIMUM", r_, g_)))
polw = w.norm(w.vadd(L, V))
odbl = w.mul(w.mul(w.math("POWER", w.math("MAXIMUM", w.dot(nrm, polw), 0.0), 90.0), woda), 0.16)
brzeg = w.math("POWER", w.sub(1.0, w.math("MAXIMUM", w.dot(nrm, V), 0.0)), 3.0)
swiatlo = w._node("ShaderNodeCombineColor")
for i in range(3):
    mz.node_tree.links.new(jasn, swiatlo.inputs[i])
k1_ = w._node("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY"); k1_.inputs["Factor"].default_value = 1.0
mz.node_tree.links.new(kol, k1_.inputs[6]); mz.node_tree.links.new(swiatlo.outputs[0], k1_.inputs[7])
dod = w.mul(w.mul(dzien, slonca), 1.0)
mgla = w.vmath("SCALE", w.rgb((0.30, 0.52, 1.0, 1.0)), scale=w.mul(w.mul(brzeg, dod), 0.55))
bl = w.vmath("SCALE", w.rgb((1.0, 0.97, 0.90, 1.0)), scale=w.mul(odbl, dod))
# złoty obrys cienia: punkty, w których odległość od osi równa się promieniowi cienia (granica zaćmienia całkowitego)
pierscien = w.wartosc(0.0, "pierscien")
obr = w.mul(w.linia(w.add(delta, L2), 0.00042, 0.00016), pierscien)
kon = w.mix(obr, w.vadd(w.vadd(k1_.outputs[2], mgla), bl), w.rgb(G.srgb(G.ZLOTY)))
w.emisja_wyjscie(kon)
ziemia.data.materials.append(mz)


def mat_poswiata(nazwa, kolor, sila, potega):
    m = bpy.data.materials.new(nazwa); m.use_nodes = True
    t = m.node_tree; t.nodes.clear()
    o = t.nodes.new("ShaderNodeOutputMaterial")
    e = t.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = G.srgb(kolor); e.inputs["Strength"].default_value = sila
    tr = t.nodes.new("ShaderNodeBsdfTransparent")
    lw = t.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    pw = t.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = potega
    t.links.new(lw.outputs["Facing"], pw.inputs[0])
    mx = t.nodes.new("ShaderNodeMixShader")
    t.links.new(pw.outputs[0], mx.inputs[0]); t.links.new(tr.outputs[0], mx.inputs[1]); t.links.new(e.outputs[0], mx.inputs[2])
    t.links.new(mx.outputs[0], o.inputs[0])
    m.surface_render_method = "BLENDED"
    return m


atm = elipsoida("Atmosfera", 180, 90, 1.012)
atm.data.materials.append(mat_poswiata("Atmosfera_mat", (110, 170, 255), 1.3, 3.2))

# ---------------------------------------------------------------- Księżyc (mapa LRO, w skali)
ksiezyc = G.sfera_uv("Ksiezyc", 256, 128, r=Z.k1)
mk = bpy.data.materials.new("Ksiezyc_mat"); mk.use_nodes = True
mk.node_tree.nodes.clear()
w = W(mk.node_tree)
img_k = G.wczytaj_obraz(os.path.join(G.DANE, "ksiezyc", "lroc_color_poles_4k.jpg"))
kk, _ = w.obraz(img_k, w._node("ShaderNodeUVMap").outputs[0], ext="EXTEND")
tc_s = w._node("ShaderNodeTexCoord"); tc_s.object = e_slonce
Lk = w.scale(w.norm(tc_s.outputs["Object"]), -1.0)
ck = w.dot(w.geometria("Normal"), Lk)
jk = w.mul(w.smooth(-0.02, 0.22, ck), 0.86)        # grunt księżycowy przy pełnym oświetleniu świeci prawie równo aż po brzeg
w.emisja_wyjscie(w.vmath("SCALE", kk, scale=jk))
ksiezyc.data.materials.append(mk)

# ---------------------------------------------------------------- pas całkowitości (granice policzone co 0,25° długości)
LON0, LON1, DLON = -126.0, -80.0, 0.25
PAS = []
lo = LON0
while lo <= LON1 + 1e-9:
    tc = Z.czas_nad_dlugoscia(lo, T_A + 0.03, T_B - 0.03)
    PAS.append((lo, tc, Z.os_cienia(tc)["lat"], Z.granica(lo, +1, T_A + 0.03, T_B - 0.03), Z.granica(lo, -1, T_A + 0.03, T_B - 0.03)))
    lo += DLON
print("[pas] %d przekrojów, szerokość na 92°W: %.0f km" % (len(PAS), Z.os_cienia(Z.czas_nad_dlugoscia(-92, T_A + .03, T_B - .03))["szer_km"]))


def krzywa(nazwa, punkty, grub, kolor, alfa):
    cu = bpy.data.curves.new(nazwa, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = grub; cu.bevel_resolution = 2
    sp = cu.splines.new("POLY"); sp.points.add(len(punkty) - 1)
    for i, p in enumerate(punkty):
        sp.points[i].co = (*p, 1)
    ob = bpy.data.objects.new(nazwa, cu); sc.collection.objects.link(ob)
    m = G.material_emisja(nazwa + "_mat", kolor, alfa); cu.materials.append(m)
    cu.bevel_factor_end = 0.0
    return ob, m


gr_n, m_gn = krzywa("granica_N", [geo(p[3], p[0], 0.0010) for p in PAS], 0.00030, G.ZLOTY, 0.0)
gr_s, m_gs = krzywa("granica_S", [geo(p[4], p[0], 0.0010) for p in PAS], 0.00030, G.ZLOTY, 0.0)
# wstęga między granicami: pojawia się za cieniem (atrybut „czas” = chwila przejścia osi cienia)
me = bpy.data.meshes.new("pas")
vv = []
for p in PAS:
    vv += [tuple(geo(p[3], p[0], 0.0007)), tuple(geo(p[4], p[0], 0.0007))]
me.from_pydata(vv, [], [(2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1) for i in range(len(PAS) - 1)])
at = me.attributes.new("czas", "FLOAT", "POINT")
at.data.foreach_set("value", [p[1] for p in PAS for _ in (0, 1)])
pas = bpy.data.objects.new("pas", me); sc.collection.objects.link(pas)
mp = bpy.data.materials.new("pas_mat"); mp.use_nodes = True; mp.node_tree.nodes.clear()
w = W(mp.node_tree)
an = w._node("ShaderNodeAttribute"); an.attribute_name = "czas"
teraz = w.wartosc(0.0, "teraz")
widac_pas = w.wartosc(0.0, "widac")
al = w.mul(w.mul(w.sub(1.0, w.smooth(-0.075, -0.012, w.sub(an.outputs["Fac"], teraz))), widac_pas), 0.13)
w.emisja_wyjscie(w.rgb(G.srgb(G.ZLOTY)), al)
mp.surface_render_method = "BLENDED"
me.materials.append(mp)

# ---------------------------------------------------------------- miejsca Majów
MIEJSCA = [("Palenque", 17.4842, -92.0464, -18, 8, "RIGHT"), ("Tikal", 17.2221, -89.6236, 18, 8, "LEFT"),
           ("Copán", 14.838, -89.1424, 18, 8, "LEFT"), ("Calakmul", 18.105, -89.8106, 18, 8, "LEFT"),
           ("Chichén Itzá", 20.6831, -88.5686, 18, 8, "LEFT")]
STELA = (16.5875, -91.7390)


def kropka(nazwa, lat, lon, r, kolor, pierscien=False):
    n = 32
    p0 = geo(lat, lon, 0.0016)
    e, nn, u = enu(lat, lon)
    V = [tuple(p0 + (e * math.cos(2 * math.pi * i / n) + nn * math.sin(2 * math.pi * i / n)) * r) for i in range(n)]
    if pierscien:
        V += [tuple(p0 + (e * math.cos(2 * math.pi * i / n) + nn * math.sin(2 * math.pi * i / n)) * r * 0.62) for i in range(n)]
        F = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    else:
        F = [tuple(range(n))]
    me = bpy.data.meshes.new(nazwa); me.from_pydata(V, [], F)
    ob = bpy.data.objects.new(nazwa, me); sc.collection.objects.link(ob)
    m = G.material_emisja(nazwa + "_mat", kolor, 0.0); me.materials.append(m)
    return ob, m


KROPKI = []
for nazwa, la, lon_, dx, dy, wyr in MIEJSCA:
    KROPKI.append(kropka("kropka_" + nazwa, la, lon_, 0.0014, (255, 244, 214))[1])
KROPKI.append(kropka("kropka_stela", STELA[0], STELA[1], 0.0017, G.ZLOTY)[1])
KROPKI.append(kropka("kropka_widok", LAT_M, LON_M, 0.0026, (255, 255, 255), pierscien=True)[1])


# ---------------------------------------------------------------- kamera 1 (kosmos)
D_A, LENS_A = 235.0, 1256.0                   # 235 promieni Ziemi = 1,5 mln km (okolice punktu L1, gdzie pracuje sonda DSCOVR)
CAM_A = (-0.5, -4.0, D_A)                     # położenie w układzie podstawowym: 1° od linii Słońce–Ziemia
B0_KAM, B0_CEL, B0_WYS = (10.0, -95.6), (16.3, -96.0), 0.56
B1_KAM, B1_CEL, B1_WYS = (11.4, -92.1), (15.05, -91.9), 0.33
LENS_B = 50.0

cam = G.kamera((0, -9, 0), (0, 0, 0), lens=LENS_A)
cam.data.clip_start, cam.data.clip_end = 0.05, 6000
tlo = G.tlo_kamery(cam, odl=1500)
TLO_SK = tuple(tlo.scale)


def kam1(f):
    """Położenie, cel i ogniskowa kamery 1 w klatce f (układ ziemski)."""
    t = czas(f)
    pa = Vector(Z.na_ziemski(t, *CAM_A))
    ca = Vector(Z.na_ziemski(t, 0.0, 0.07, 0.0))
    if f <= 140:
        return pa, ca, LENS_A
    s2 = G.gladko((f - 200) / 130.0)
    kb = geo(B0_KAM[0] + (B1_KAM[0] - B0_KAM[0]) * s2, B0_KAM[1] + (B1_KAM[1] - B0_KAM[1]) * s2).normalized()
    wys = B0_WYS + (B1_WYS - B0_WYS) * s2
    pb = kb * (1.0 + wys)
    cb = geo(B0_CEL[0] + (B1_CEL[0] - B0_CEL[0]) * s2, B0_CEL[1] + (B1_CEL[1] - B0_CEL[1]) * s2)
    s = G.gladko5((f - 140) / 72.0)
    if s >= 1.0:
        return pb, cb, LENS_B
    kier = pa.normalized().slerp(pb.normalized(), s)
    # wysokość nad Ziemią i ogniskowa zmieniają się wykładniczo – przelot wygląda jak jednostajne zbliżanie
    odl = 1.0 + math.exp(math.log(pa.length - 1.0) + (math.log(pb.length - 1.0) - math.log(pa.length - 1.0)) * s)
    lens = math.exp(math.log(LENS_A) + (math.log(LENS_B) - math.log(LENS_A)) * s)
    return kier * odl, ca.lerp(cb, s), lens


# ================================================================ UJĘCIE 3: WIDOK Z ZIEMI
for o in sc.objects:
    o["ujecie"] = 1

R_NIEBA, R_SL, R_KS, R_KOR = 90.0, 50.0, 49.0, 51.0
LENS_C0, LENS_C1 = 300.0, 600.0
SLONCE_Y = 385.0                                # wysokość środka Słońca w kadrze [px od góry]

# niebo: kolor zależy od tego, jaka część tarczy Słońca jeszcze świeci
bpy.ops.mesh.primitive_uv_sphere_add(radius=R_NIEBA, segments=48, ring_count=24)
niebo = bpy.context.active_object; niebo.name = "niebo"
mn = bpy.data.materials.new("niebo_mat"); mn.use_nodes = True; mn.node_tree.nodes.clear()
w = W(mn.node_tree)
jasnosc = w.wartosc(0.0, "jasnosc")
w.emisja_wyjscie(w.mix(jasnosc, w.rgb(G.srgb((11, 17, 36))), w.rgb(G.srgb((70, 118, 190)))))
niebo.data.materials.append(mn)


def tarcza(nazwa, n=128):
    V = [(0.0, 0.0, 0.0)] + [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n), 0.0) for i in range(n)]
    F = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    me = bpy.data.meshes.new(nazwa); me.from_pydata(V, [], F)
    ob = bpy.data.objects.new(nazwa, me); sc.collection.objects.link(ob)
    return ob


t_sl = tarcza("tarcza_Slonca")
ms = bpy.data.materials.new("Slonce_mat"); ms.use_nodes = True; ms.node_tree.nodes.clear()
w = W(ms.node_tree)
ox, oy, _oz = w.sep(w.coord("Object"))
r2 = w.math("MINIMUM", w.add(w.mul(ox, ox), w.mul(oy, oy)), 1.0)
pociemn = w.sub(1.0, w.mul(w.sub(1.0, w.math("SQRT", w.sub(1.0, r2))), 0.6))      # pociemnienie brzegowe tarczy (u = 0,6)
o_ = w._node("ShaderNodeOutputMaterial"); em = w._node("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.95, 0.86, 1.0)
ms.node_tree.links.new(w.mul(pociemn, 1500.0), em.inputs["Strength"])   # tarcza Słońca jest wielokrotnie jaśniejsza od korony: nawet cienki sierp oślepia
ms.node_tree.links.new(em.outputs[0], o_.inputs["Surface"])
t_sl.data.materials.append(ms)
t_ks = tarcza("tarcza_Ksiezyca")
t_ks.data.materials.append(mn)                 # tarcza Księżyca ma kolor nieba: widać ją tylko na tle Słońca i korony


# korona: zdjęcie zaćmienia z 11 VIII 1999 (Luc Viatour, CC BY-SA 3.0); skala według tarczy Księżyca na zdjęciu
def tarcza_na_zdjeciu(sciezka):
    """Środek i promień ciemnej tarczy Księżyca na zdjęciu korony (piksele; y od góry). Wynik w pamięci podręcznej."""
    cp = os.path.join(G.CACHE, "korona_tarcza.json")
    if os.path.exists(cp):
        with open(cp) as f:
            return json.load(f)
    a = G.obraz_numpy(sciezka)[..., :3].mean(axis=2)
    h, wd = a.shape
    cx, cy = wd / 2.0, h / 2.0
    for _ in range(4):
        px, py = [], []
        for k in range(360):
            c, s = math.cos(math.radians(k)), math.sin(math.radians(k))
            rr = np.arange(200, min(wd, h) // 2 - 5)
            pr = a[np.clip((cy + rr * s).astype(int), 0, h - 1), np.clip((cx + rr * c).astype(int), 0, wd - 1)]
            j = int(np.argmax(pr > 0.35))
            if pr[j] > 0.35:
                px.append(cx + rr[j] * c); py.append(cy + rr[j] * s)
        px, py = np.array(px), np.array(py)
        M = np.c_[2 * px, 2 * py, np.ones(len(px))]
        sol = np.linalg.lstsq(M, px ** 2 + py ** 2, rcond=None)[0]
        cx, cy = float(sol[0]), float(sol[1])
        r = float(math.sqrt(sol[2] + cx * cx + cy * cy))
    wyn = dict(cx=cx, cy=cy, r=r, w=wd, h=h)
    with open(cp, "w") as f:
        json.dump(wyn, f)
    return wyn


ZDJ = os.path.join(G.DANE, "korona", "Solar_eclipse_1999_4.jpg")
TZ = tarcza_na_zdjeciu(ZDJ)
print("[korona] tarcza Księżyca na zdjęciu: środek (%.0f, %.0f), promień %.0f px z %d×%d" % (TZ["cx"], TZ["cy"], TZ["r"], TZ["w"], TZ["h"]))
bpy.ops.mesh.primitive_plane_add(size=1)
korona = bpy.context.active_object; korona.name = "korona"
mkr = bpy.data.materials.new("korona_mat"); mkr.use_nodes = True; mkr.node_tree.nodes.clear()
w = W(mkr.node_tree)
uvk = w._node("ShaderNodeUVMap").outputs[0]
kz, _ = w.obraz(G.wczytaj_obraz(ZDJ), uvk, ext="EXTEND")
uu, vv_, _ = w.sep(uvk)
rk = w.math("SQRT", w.add(w.math("POWER", w.sub(uu, 0.5), 2.0), w.math("POWER", w.sub(vv_, 0.5), 2.0)))
widac_kor = w.wartosc(0.0, "widac")
sila_k = w.mul(w.mul(w.sub(1.0, w.smooth(0.455, 0.50, rk)), widac_kor), 1.9)
kz2 = w.vmath("MAXIMUM", w.vmath("SUBTRACT", kz, (0.006, 0.006, 0.006)), (0.0, 0.0, 0.0))
o_ = w._node("ShaderNodeOutputMaterial"); em = w._node("ShaderNodeEmission"); tr = w._node("ShaderNodeBsdfTransparent")
ad = w._node("ShaderNodeAddShader")
mkr.node_tree.links.new(kz2, em.inputs["Color"]); mkr.node_tree.links.new(sila_k, em.inputs["Strength"])
mkr.node_tree.links.new(tr.outputs[0], ad.inputs[0]); mkr.node_tree.links.new(em.outputs[0], ad.inputs[1])
mkr.node_tree.links.new(ad.outputs[0], o_.inputs["Surface"])
mkr.surface_render_method = "BLENDED"
korona.data.materials.append(mkr)

# gwiazdy (HYG, J2000) i planety (Horizons, ICRF) – obracane co klatkę macierzą precesji i czasu gwiazdowego
cam2 = G.kamera((0, 0, 0), (0, 1, 0), lens=LENS_C0)
cam2.name = "Kamera_ziemia"
cam2.data.clip_start, cam2.data.clip_end = 0.05, 300
KAT_PX = (36.0 / 330.0) / 1920.0
gwiazdy_l = [g for g in N.wczytaj(4.6)]
m_gw = N.material_gwiazd("gwiazdy_mat")
gwiazdy = N.siatka_gwiazd(gwiazdy_l, 80.0, KAT_PX, nazwa="gwiazdy", wzmocnienie=0.6, material=m_gw)
planety = N.siatka_gwiazd(PLANETY, 79.0, KAT_PX, nazwa="planety", wzmocnienie=0.75, rozmiar=0.75, material=m_gw)

for o in sc.objects:
    if "ujecie" not in o:
        o["ujecie"] = 2

# ================================================================ NAPISY (przypięte do kamer, przeliczane co klatkę)
ODL, PX0 = 0.3, 1e-4            # ODL: odległość napisów od kamery 2; dla kamery 1 liczona co klatkę (patrz ustaw)
NAPISY = []


def napis(kam, tekst, rozm, kolor, kroj="georgiab", wyr="CENTER", ekran=None, punkt=None, dx=0.0, dy=0.0, klucze=None,
          nazwa="napis", odstep=1.0):
    """Napis przypięty do kamery. ekran=(x, y) w pikselach kadru albo punkt = funkcja klatki -> punkt sceny (+ dx, dy w px)."""
    ob = G.napis(tekst, rozm * PX0, kolor, kroj, wyr, rodzic=kam, nazwa=nazwa, obrys=((4, 6, 11), 0.035 * rozm * PX0), odstep=odstep)
    NAPISY.append(dict(ob=ob, kam=kam, ekran=ekran, punkt=punkt, dx=dx, dy=dy))
    if klucze:
        G.alfa_napisu(ob, klucze)
    return ob


ZLOTY, BIALY, SZARY = G.ZLOTY, (236, 232, 220), (168, 176, 198)
# --- ujęcie 1
napis(cam, "Zaćmienie Słońca 16 lipca 790 r.", 54, ZLOTY, ekran=(1385, 82), klucze=[(1, 0), (6, 0), (26, 1), (186, 1), (204, 0)], nazwa="tytul")
napis(cam, "cień Księżyca policzony z danych NASA", 30, BIALY, "georgia", ekran=(1385, 138),
      klucze=[(1, 0), (16, 0), (38, 1), (186, 1), (204, 0)], nazwa="podtytul")
zegar = napis(cam, "00:00 czasu uniwersalnego", 28, SZARY, "arial", ekran=(1385, 186),
              klucze=[(1, 0), (16, 0), (38, 1), (186, 1), (204, 0)], nazwa="zegar")
zegar2 = napis(cam, "00:00 czasu uniwersalnego", 28, BIALY, "arial", "RIGHT", ekran=(1890, 62),
               klucze=[(1, 0), (200, 0), (218, 1), (318, 1), (332, 0)], nazwa="zegar2")
napis(cam, "rozmiary i odległości w skali\nwidok od strony Słońca, z 1,5 mln km", 24, SZARY, "arial", ekran=(1385, 250),
      klucze=[(1, 0), (30, 0), (52, 1), (128, 1), (146, 0)], nazwa="skala", odstep=1.15)
napis(cam, "Księżyc", 40, BIALY, "arialb", "RIGHT", punkt=lambda f: STAN["ksiezyc"], dx=-128, dy=6,
      klucze=[(1, 0), (20, 0), (42, 1), (132, 1), (150, 0)], nazwa="et_ksiezyc")
napis(cam, "strona niewidoczna z Ziemi", 22, SZARY, "arial", "RIGHT", punkt=lambda f: STAN["ksiezyc"], dx=-128, dy=-30,
      klucze=[(1, 0), (20, 0), (42, 1), (132, 1), (150, 0)], nazwa="et_ksiezyc2")
napis(cam, "półcień: zaćmienie częściowe", 28, BIALY, "arialb", punkt=lambda f: STAN["cien"], dx=-30, dy=-196,
      klucze=[(1, 0), (40, 0), (62, 1), (132, 1), (150, 0)], nazwa="et_polcien")
napis(cam, "cień: zaćmienie całkowite", 26, ZLOTY, "arialb", "LEFT", punkt=lambda f: STAN["cien"], dx=16, dy=-2,
      klucze=[(1, 0), (55, 0), (77, 1), (132, 1), (150, 0)], nazwa="et_cien")
# --- ujęcie 2
K2 = [(1, 0), (196, 0), (216, 1), (316, 1), (330, 0)]
for nazwa, la, lon_, dx, dy, wyr in MIEJSCA:
    napis(cam, nazwa, 25, BIALY, "arialb", wyr, punkt=(lambda p: (lambda f: p))(geo(la, lon_, 0.002)), dx=dx, dy=dy - 8, klucze=K2,
          nazwa="et_" + nazwa)
napis(cam, "Santa Elena Poco Uinic", 25, ZLOTY, "arialb", "RIGHT", punkt=lambda f: P_STELA, dx=-20, dy=2, klucze=K2, nazwa="et_stela")
napis(cam, "stela z zapisem tego zaćmienia\ntu Księżyc zakrył 95% tarczy", 20, BIALY, "arial", "RIGHT", punkt=lambda f: P_STELA,
      dx=-20, dy=-38, klucze=K2, nazwa="et_stela2", odstep=1.1)
napis(cam, "kraj Majów", 46, (255, 240, 205), "georgia", punkt=lambda f: P_KRAJ, klucze=[(1, 0), (190, 0), (212, 0.55), (300, 0.55), (322, 0)],
      nazwa="et_kraj")
napis(cam, "złoty pas: tu zaćmienie było całkowite (szerokość ok. 100 km)", 26, ZLOTY, "arialb", "LEFT", ekran=(60, 800),
      klucze=[(1, 0), (226, 0), (246, 1), (316, 1), (330, 0)], nazwa="et_pas")
napis(cam, "stąd widok z ziemi", 22, BIALY, "arialb", "LEFT", punkt=lambda f: P_WIDOK, dx=30, dy=-2,
      klucze=[(1, 0), (262, 0), (280, 1), (316, 1), (330, 0)], nazwa="et_widok")
napis(cam, "położenie pasa zależy od dawnego tempa obrotu Ziemi (ΔT): niepewność rzędu 40 km", 20, SZARY, "arial", "RIGHT",
      ekran=(1890, 858), klucze=[(1, 0), (214, 0), (234, 1), (314, 1), (328, 0)], nazwa="uwaga_dt")
# --- ujęcie 3
K3 = [(1, 0), (338, 0), (350, 1), (392, 1), (408, 0)]
napis(cam2, "Widok z ziemi, ze środka pasa", 46, ZLOTY, ekran=(1400, 82), klucze=K3, nazwa="c_tytul")
napis(cam2, "wybrzeże Pacyfiku w dzisiejszej Gwatemali, ok. 13:30", 27, BIALY, "georgia", ekran=(1400, 134), klucze=K3, nazwa="c_gdzie")
napis(cam2, "Słońce zakryte przez %d min %d s" % (TRWANIE // 60, round(TRWANIE % 60)), 27, BIALY, "georgia", ekran=(1400, 178),
      klucze=[(1, 0), (372, 0), (382, 1), (392, 1), (408, 0)], nazwa="c_trwa")
napis(cam2, "korona: zdjęcie zaćmienia z 1999 r., Luc Viatour, CC BY-SA 3.0", 19, SZARY, "arial", "RIGHT", ekran=(1892, 862),
      klucze=[(1, 0), (396, 0), (416, 1)], nazwa="c_zdjecie")
napis(cam2, "Tablica zaćmień w Kodeksie drezdeńskim Majów:", 38, BIALY, "georgia", ekran=(960, 764), klucze=[(1, 0), (398, 0), (422, 1)],
      nazwa="kodeks1")
napis(cam2, "405 lunacji = 11 960 dni, niecałe 33 lata", 44, ZLOTY, ekran=(960, 822), klucze=[(1, 0), (404, 0), (428, 1)], nazwa="kodeks2")
P_STELA = geo(STELA[0], STELA[1], 0.002)
P_KRAJ = geo(18.9, -89.3, 0.002)
P_WIDOK = geo(LAT_M, LON_M, 0.002)
_tp = Z.czas_nad_dlugoscia(-98.6, T_A + 0.03, T_B - 0.03)
P_PAS = geo(Z.granica(-98.6, -1, T_A + 0.03, T_B - 0.03), -98.6, 0.002)

# przyciemnienia między ujęciami
for kam, klucze, nazwa in ((cam, [(1, 0), (320, 0), (335, 1)], "zaslona1"), (cam2, [(1, 1), (F_C, 1), (F_C + 9, 0)], "zaslona2")):
    bpy.ops.mesh.primitive_plane_add(size=2)
    z_ = bpy.context.active_object; z_.name = nazwa; z_.parent = kam; z_.location = (0, 0, -0.08)
    z_["ujecie"] = 1 if kam is cam else 2
    mzs = G.material_emisja(nazwa + "_mat", (3, 4, 8), 0.0); z_.data.materials.append(mzs)
    G.animuj_alfa(mzs, klucze)

for o in sc.objects:
    if "ujecie" not in o:
        k = o
        while k.parent is not None:
            k = k.parent
        o["ujecie"] = 1 if k is cam else 2
# widoczność obiektów w renderze: ujęcia 1–2 do klatki 335, ujęcie 3 od 336
for o in sc.objects:
    if o.type in ("CAMERA", "EMPTY"):
        continue
    for f, ukryty in ((1, o["ujecie"] == 2), (F_C, o["ujecie"] == 1)):
        o.hide_render = ukryty
        o.keyframe_insert("hide_render", frame=f)
sc.timeline_markers.new("kosmos", frame=1).camera = cam
sc.timeline_markers.new("ziemia", frame=F_C).camera = cam2

# ---------------------------------------------------------------- wartości animowane kluczami (co klatkę)
kl_pas, kl_teraz, kl_kropki, kl_gran = [], [], [], []
kl_niebo, kl_kor, kl_gw = [], [], []
P_BLYSK = None
for f in range(1, KLATEK + 1):
    t = czas(f)
    kl_teraz.append((f, t))
    if f >= F_C - 1:
        o = Z.obserwator(t, LAT_M, LON_M)
        zak = BS.zakrycie_tarcz(2 * o["D"] / (o["L1"] + o["L2"]), o["stosunek"])
        p = max(0.0, 1.0 - zak)                               # świecąca część tarczy Słońca
        j = max(0.0, min(1.0, (math.log10(max(p, 1e-4)) + 4.0) / 4.0)) ** 1.6
        kl_niebo.append((f, j))
        kl_kor.append((f, 1.0 - G.gladko(p / 0.0012)))
        kl_gw.append((f, 1.0 - G.gladko(p / 0.004)))
for nt, nazwa, kl in ((mp.node_tree, "teraz", kl_teraz), (mn.node_tree, "jasnosc", kl_niebo), (mkr.node_tree, "widac", kl_kor),
                      (m_gw.node_tree, "widac", kl_gw)):
    wezly.animuj_wartosc(nt, nazwa, kl, "LINEAR")
wezly.animuj_wartosc(mp.node_tree, "widac", [(1, 0), (165, 0), (200, 1), (318, 1), (332, 0)])
for m in (m_gn, m_gs):
    G.animuj_alfa(m, [(1, 0), (165, 0), (200, 0.9), (318, 0.9), (332, 0)])
wezly.animuj_wartosc(mz.node_tree, "pierscien", [(1, 0), (160, 0), (200, 1), (335, 1)])
for m in KROPKI:
    G.animuj_alfa(m, [(1, 0), (190, 0), (212, 1), (318, 1), (332, 0)])

STAN = dict(ksiezyc=Vector((0, 0, 60)), cien=Vector((0, 0, 1)), nh=Matrix.Identity(3))


def _macierz_kamery(poz, cel, pochyl=0.0):
    q = (Vector(cel) - Vector(poz)).to_track_quat("-Z", "Y")
    if pochyl:
        q = q @ Quaternion((1, 0, 0), pochyl)
    return Matrix.LocRotScale(Vector(poz), q, None), q


def ustaw(scene, depsgraph=None):
    f = scene.frame_current
    t = czas(f)
    kamera_teraz = cam if f < F_C else cam2
    if scene.camera is not kamera_teraz:
        scene.camera = kamera_teraz
    # --- geometria Słońce–Księżyc–Ziemia z elementów Bessela
    i, j, k = (Vector(v) for v in Z.osie(t))
    mk_, _zm = Z.ksiezyc(t)
    mk_ = Vector(mk_)
    sl = Vector(Z.slonce(t))
    e_slonce.location = sl
    e_os.matrix_world = Matrix.Translation(mk_) @ Matrix((i, j, k)).transposed().to_4x4()
    # Księżyc: południk 0° ku Ziemi (bez libracji), biegun ku północy ekliptyki
    gst = math.radians(czas_gwiazdowy(t))
    eps = math.radians(23.5966)
    bieg = Matrix.Rotation(-gst, 3, "Z") @ Vector((0.0, -math.sin(eps), math.cos(eps)))
    xk = (-mk_).normalized()
    zk = (bieg - xk * bieg.dot(xk)).normalized()
    ksiezyc.matrix_world = Matrix.Translation(mk_) @ Matrix((xk, zk.cross(xk), zk)).transposed().to_4x4()
    oc = Z.os_cienia(t)
    if oc:
        STAN["cien"] = geo(oc["lat"], oc["lon"], 0.001)
        ulamek = (oc["lon"] - 0.55 - LON0) / (LON1 - LON0)       # linie kończą się tuż za cieniem
    else:
        ulamek = 0.0
    STAN["ksiezyc"] = mk_
    for c in (gr_n, gr_s):
        c.data.bevel_factor_end = max(0.0, min(1.0, ulamek))
    # --- kamera 1
    poz, cel, lens = kam1(min(f, F_C - 1))
    M1, q1 = _macierz_kamery(poz, cel)
    cam.location, cam.rotation_euler, cam.data.lens = poz, q1.to_euler(), lens
    tlo.scale = (TLO_SK[0] * LENS_A / lens, TLO_SK[1] * LENS_A / lens, 1.0)
    # --- widok z ziemi: wszystko w układzie horyzontalnym miejsca (x = wschód, y = północ, z = zenit)
    e, n, u = enu(LAT_M, LON_M)
    H = Matrix((e, n, u))
    obs = geo(LAT_M, LON_M)
    ds, dk = sl - obs, mk_ - obs
    ks, kk_ = (H @ ds).normalized(), (H @ dk).normalized()
    r_s = math.asin(BS.R_SLONCA / ds.length)
    r_k = math.asin(Z.k2 / dk.length)
    for ob, kier, odl, r in ((t_sl, ks, R_SL, r_s), (t_ks, kk_, R_KS, r_k)):
        ob.matrix_world = Matrix.LocRotScale(kier * odl, kier.to_track_quat("Z", "Y"), Vector((1, 1, 1)) * odl * math.tan(r))
    bok = R_KOR * math.tan(r_k) * TZ["w"] / TZ["r"]                       # bok zdjęcia: tarcza Księżyca na zdjęciu = tarcza w kadrze
    qk = ks.to_track_quat("Z", "Y")
    # płaszczyznę widać od tyłu, więc oś X ma skalę ujemną (zdjęcie nie jest odbite w lustrze)
    przes = qk @ Vector(((TZ["cx"] / TZ["w"] - 0.5) * bok, (TZ["cy"] / TZ["h"] - 0.5) * bok * TZ["h"] / TZ["w"], 0.0))
    korona.matrix_world = Matrix.LocRotScale(ks * R_KOR + przes, qk, Vector((-bok, bok * TZ["h"] / TZ["w"], 1.0)))
    nh = niebo_na_horyzont(t)
    STAN["nh"] = nh
    gwiazdy.matrix_world = nh.to_4x4()
    planety.matrix_world = nh.to_4x4()
    sz = G.gladko((f - 346) / 84.0)
    lens2 = math.exp(math.log(LENS_C0) + (math.log(LENS_C1) - math.log(LENS_C0)) * sz)
    pochyl = -(540.0 - SLONCE_Y) * 36.0 / lens2 / 1920.0                  # Słońce powyżej środka kadru (dół kadru zostaje na podpis)
    M2, q2 = _macierz_kamery((0, 0, 0), ks, pochyl)
    cam2.location, cam2.rotation_euler, cam2.data.lens = (0, 0, 0), q2.to_euler(), lens2
    # --- zegar
    ut = Z.ut(t)
    tekst = "%s czasu uniwersalnego" % BS.hms(ut)[:5]
    for o in (zegar, *zegar.children, zegar2, *zegar2.children):
        if o.data.body != tekst:
            o.data.body = tekst
    # --- napisy
    for d in NAPISY:
        kam = d["kam"]
        M = M1 if kam is cam else M2
        # daleko od Ziemi napisy stoją dalej od kamery: przy 235 promieniach Ziemi liczby 32-bitowe mają krok 0,00002
        odl = max(0.12, min(12.0, 0.05 * (poz.length - 1.0))) if kam is cam else ODL
        sw = odl * 36.0 / kam.data.lens
        px = sw / 1920.0
        d["ob"].scale = (px / PX0,) * 3
        for dz in d["ob"].children:                      # obrys tuż za napisem
            dz.location = (0, 0, -0.002 * odl * PX0 / px)
        if d["ekran"]:
            x, y = d["ekran"]
            d["ob"].location = ((x / 1920.0 - 0.5) * sw, (0.5 - y / 1080.0) * sw * 1080.0 / 1920.0, -odl)
        else:
            q = M.inverted() @ Vector(d["punkt"](f))
            if q.z > -1e-6:
                d["ob"].location = (0, 0, 10.0)
                continue
            q = q * (odl / -q.z)
            d["ob"].location = (q.x + d["dx"] * px, q.y + d["dy"] * px, -odl * 1.0015)


bpy.app.handlers.frame_change_pre.append(ustaw)
ustaw(sc)
for ob in sc.objects:
    ob.visible_shadow = False
N.poswiata(sc, prog=1.6, sila=0.9, rozmiar=0.7)

if os.environ.get("ZACMIENIE_INFO"):
    for f in (1, 75, 140, 180, 205, 260, 330, 336, 360, 372, 400, 450):
        t = czas(f)
        oc = Z.os_cienia(t)
        print("[klatka %3d] %s UT, cień %.2fN %.2fW" % (f, BS.hms(Z.ut(t)), oc["lat"], -oc["lon"]))

G.renderuj(TU, opcje, kadr_klatka=KLATEK)
