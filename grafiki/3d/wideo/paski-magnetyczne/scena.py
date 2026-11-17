# -*- coding: utf-8 -*-
"""Klip „paski-magnetyczne”: zastygła lawa grzbietu atlantyckiego zapisuje kierunek pola magnetycznego Ziemi.

Rozdz. „Siedemnaście stopni Daenikena”: „…o badaniach warstw lawy wypływającej z grzbietu atlantyckiego i odkryciu,
że w zastygłych pokładach zachował się układ linii ówczesnego pola magnetycznego”.

Blok dna oceanu w przekroju: pod grzbietem unosi się magma, w szczelinie świeci lawa, dno rozsuwa się na boki.
Stygnąca lawa przyjmuje kolor aktualnego kierunku pola (jak dziś / odwrócone); igła nad grzbietem pokazuje ten
kierunek i co jakiś czas się odwraca. Po obu stronach grzbietu powstają takie same pasy (lustrzane odbicie).
Kolejność i względna szerokość pasów według prawdziwej skali odwróceń pola z ostatnich 5,3 mln lat
(S. C. Cande, D. V. Kent 1995); klip biegnie od 2,3 mln lat temu do dziś. Stała prędkość rozsuwania, blok jest schematem.

Uruchomienie: S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/paski-magnetyczne/scena.py
              ... -- --proba 1,130,260,400
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
KLATKI = 400            # 16 s
XB, YB, DNO = 6.0, 2.3, -1.9          # połowa szerokości bloku, połowa długości (wzdłuż grzbietu), spód
GR = 0.42                              # grubość zastygłej skorupy w przekroju
T_KON = 4.6                            # o tyle jednostek dno odsuwa się od grzbietu w czasie klipu
MLN = 0.5                              # mln lat na jednostkę długości (i czasu T)
# Okresy pola „jak dziś” (polarność normalna), wiek w mln lat. Skala: S. C. Cande, D. V. Kent, „Revised calibration of
# the geomagnetic polarity timescale for the Late Cretaceous and Cenozoic”, J. Geophys. Res. 100 (B4), 1995, s. 6093–6095.
# Brunhes; Jaramillo; Olduvai; Gauss (trzy części, między nimi Kaena i Mammoth); Cochiti; Nunivak; Sidufjall; Thvera.
# Pominięty epizod Réunion (2,14–2,15 mln lat): trwał 10 tys. lat, pas byłby cieńszy niż piksel.
NORMALNE = [(-9.0, 0.780), (0.990, 1.070), (1.770, 1.950), (2.581, 3.040), (3.110, 3.220), (3.330, 3.580),
            (4.180, 4.290), (4.480, 4.620), (4.800, 4.890), (4.980, 5.230)]
KOL_DZIS = (226, 150, 58)              # pole jak dziś
KOL_ODWR = (62, 98, 164)               # pole odwrócone
LAWA = (255, 120, 24)
ZLOTY = G.ZLOTY


def wys(x):
    """profil dna: wyniesienie grzbietu z doliną ryftową pośrodku"""
    return 0.44 * np.exp(-(x / 1.7) ** 2) - 0.17 * np.exp(-(x / 0.24) ** 2)


def wiek(tb):
    """Wiek [mln lat] lawy zastygłej w chwili tb (koniec klipu, T = T_KON, to dziś)."""
    return (T_KON - tb) * MLN


def pole(tb):
    """> 0: pole jak dziś, < 0: odwrócone (dla lawy zastygłej w chwili tb)"""
    w = wiek(tb)
    return 1.0 if any(a <= w < b for a, b in NORMALNE) else -1.0


def T_klatki(f):
    return T_KON * (f - 1) / (KLATKI - 1)


sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))
S.swiatlo(kat=(52, 0, 28), sila=2.6, otoczenie=(150, 170, 215), moc=0.55)


# ---------------------------------------------------------------- materiały (pasy liczone w shaderze)
def pasy(Wm):
    """Wspólna część: kolor pasa i „żar” świeżej lawy w funkcji |x| i czasu T. Zwraca (kolor, żar, x, z, T)."""
    x, y, z = Wm.sep(Wm.geometria("Position"))
    ax = Wm.math("ABSOLUTE", x)
    T = Wm.wartosc(0.0, "T")
    tb = Wm.sub(T, ax)
    w = Wm.mul(Wm.sub(T_KON, tb), MLN)                 # wiek lawy [mln lat]
    dzis = None
    for a, b in NORMALNE:
        o = Wm.mul(Wm.math("GREATER_THAN", w, a), Wm.math("LESS_THAN", w, b))
        dzis = o if dzis is None else Wm.add(dzis, o)
    kol = Wm.mix(dzis, G.srgb(KOL_ODWR), G.srgb(KOL_DZIS))
    # faktura bazaltu jadąca razem z dnem
    nz = Wm._node("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.6
    nz.inputs["Detail"].default_value = 5.0
    Wm.nt.links.new(Wm.vec(Wm.sub(ax, T), y, 0.0), nz.inputs["Vector"])
    cien = Wm.add(0.62, Wm.mul(nz.outputs[0], 0.62))
    kol = Wm.vmath("MULTIPLY", kol, Wm.vec(cien, cien, cien))
    zar = Wm.math("EXPONENT", Wm.mul(ax, -1.0 / 0.21))
    return kol, zar, x, z, T, ax


def principled(Wm, kolor, emis_kolor, emis_sila, szorst=0.8):
    out = Wm._node("ShaderNodeOutputMaterial")
    b = Wm._node("ShaderNodeBsdfPrincipled")
    Wm._in(b.inputs["Base Color"], kolor)
    b.inputs["Roughness"].default_value = szorst
    Wm._in(b.inputs["Emission Color"], emis_kolor)
    Wm._in(b.inputs["Emission Strength"], emis_sila)
    Wm.nt.links.new(b.outputs[0], out.inputs["Surface"])


m_gora = bpy.data.materials.new("Dno")
m_gora.use_nodes = True
m_gora.node_tree.nodes.clear()
Wg = Wezly(m_gora.node_tree)
kol, zar, x_, z_, T_, ax_ = pasy(Wg)
kol = Wg.mix(Wg.mn(Wg.mul(zar, 1.5), 1.0), kol, G.srgb((60, 22, 12)))
principled(Wg, kol, G.srgb(LAWA), Wg.mul(zar, 5.0))

m_bok = bpy.data.materials.new("Przekroj")
m_bok.use_nodes = True
m_bok.node_tree.nodes.clear()
Wb = Wezly(m_bok.node_tree)
kol, zar, x_, z_, T_, ax_ = pasy(Wb)
h = Wb.sub(Wb.mul(Wb.math("EXPONENT", Wb.mul(Wb.math("POWER", Wb.div(ax_, 1.7), 2.0), -1.0)), 0.44),
           Wb.mul(Wb.math("EXPONENT", Wb.mul(Wb.math("POWER", Wb.div(ax_, 0.24), 2.0), -1.0)), 0.17))
gleb = Wb.sub(h, z_)
skorupa = Wb.math("LESS_THAN", gleb, GR)
g01 = Wb.math("MINIMUM", Wb.math("MAXIMUM", Wb.div(Wb.sub(gleb, GR), -DNO - GR), 0.0), 1.0)
plaszcz = Wb.mix(g01, G.srgb((168, 62, 30)), G.srgb((92, 24, 22)))
szer = Wb.add(0.30, Wb.mul(g01, 0.75))
nz2 = Wb._node("ShaderNodeTexNoise")
nz2.inputs["Scale"].default_value = 2.2
nz2.inputs["Detail"].default_value = 3.0
Wb.nt.links.new(Wb.vec(x_, Wb.sub(z_, Wb.mul(T_, 0.55)), 0.0), nz2.inputs["Vector"])
smuga = Wb.mul(Wb.math("EXPONENT", Wb.mul(Wb.math("POWER", Wb.div(x_, szer), 2.0), -1.0)), Wb.add(0.55, Wb.mul(nz2.outputs[0], 0.8)))
smuga = Wb.mn(smuga, 1.0)
plaszcz = Wb.mix(smuga, plaszcz, G.srgb((255, 176, 56)))
kol_sk = Wb.vmath("MULTIPLY", kol, (0.66, 0.66, 0.66))
kol_sk = Wb.mix(Wb.mn(Wb.mul(zar, 1.6), 1.0), kol_sk, G.srgb(LAWA))
kolor = Wb.mix(skorupa, plaszcz, kol_sk)
sila = Wb.add(Wb.mul(Wb.mul(Wb.sub(1.0, skorupa), smuga), 2.2), Wb.mul(Wb.mul(skorupa, zar), 3.0))
principled(Wb, kolor, G.srgb((255, 150, 40)), sila, 0.9)

for m in (m_gora, m_bok):
    animuj_wartosc(m.node_tree, "T", [(1, 0.0), (KLATKI, T_KON)], interp="LINEAR")

blok = S.teren("Dno_oceanu", lambda X, Y: wys(X), -XB, XB, -YB, YB, 361, 9, DNO, m_gora, m_bok)

# ---------------------------------------------------------------- strzałki namagnesowania jadące z dnem
# chwile odwróceń pola (zera funkcji pole) w przedziale obejmującym całe dno widoczne w klipie
ts = np.linspace(-XB - 0.5, T_KON + 0.2, 6000)
ps = np.array([pole(t) for t in ts])
zera = [float(ts[i]) for i in range(1, len(ts)) if (ps[i - 1] > 0) != (ps[i] > 0)]
granice = [float(ts[0])] + zera + [float(ts[-1])]
print("[paski] odwrócenia pola w klipie (klatki):", [int(round(1 + z / T_KON * (KLATKI - 1))) for z in zera if 0 < z < T_KON])

m_strz = S.mat("Strzalka_pola", (250, 250, 250), 0.6, emisja=0.55)
DLS, SZS, GRS, GLS = 0.74, 0.05, 0.15, 0.26


def siatka_strzalki(nazwa):
    v = [(-SZS, -DLS / 2, 0), (SZS, -DLS / 2, 0), (SZS, DLS / 2 - GLS, 0), (GRS, DLS / 2 - GLS, 0), (0, DLS / 2, 0),
         (-GRS, DLS / 2 - GLS, 0), (-SZS, DLS / 2 - GLS, 0)]
    v += [(x, y, 0.035) for x, y, z in v]
    f = [tuple(range(6, -1, -1)), tuple(range(7, 14))] + [(k, (k + 1) % 7, 7 + (k + 1) % 7, 7 + k) for k in range(7)]
    me = bpy.data.meshes.new(nazwa)
    me.from_pydata(v, [], f)
    me.materials.append(m_strz)
    return me


me_strz = siatka_strzalki("Strzalka_pola")
X_OD, X_DO = 0.34, XB - 0.3
ile = 0
for k in range(len(granice) - 1):
    t0, t1 = granice[k], granice[k + 1]
    if t1 - t0 < 0.42:
        continue
    tb = (t0 + t1) / 2
    dzis = pole(tb) > 0
    for strona in (-1, 1):
        for yy in (-1.45, 0.0, 1.45):
            # klatki, w których strzałka jest na bloku: |x| = T - tb w (X_OD, X_DO)
            f_od = 1 + (tb + X_OD) / T_KON * (KLATKI - 1)
            f_do = 1 + (tb + X_DO) / T_KON * (KLATKI - 1)
            if f_do < 2 or f_od > KLATKI:
                continue
            ob = S.polacz(bpy.data.objects.new(f"Namagn_{k}_{strona}_{int(yy * 10)}", me_strz))
            ob.rotation_euler = (0, 0, 0.0 if dzis else math.pi)
            ob.visible_shadow = False
            fa, fb = max(1, int(math.floor(f_od))), min(KLATKI, int(math.ceil(f_do)))
            for f in sorted(set(list(range(fa, fb + 1, 10)) + [fb])):
                xx = strona * max(0.0, T_klatki(f) - tb)
                ob.location = (xx, yy, float(wys(xx)) + 0.045)
                ob.keyframe_insert("location", frame=f)
            G.wygladz(ob, "LINEAR")
            # pojawia się przy grzbiecie, znika przy krawędzi bloku
            if f_od >= 1:
                ob.scale = (0.001, 0.001, 0.001); ob.keyframe_insert("scale", frame=fa)
                ob.scale = (1, 1, 1); ob.keyframe_insert("scale", frame=fa + 12)
            if f_do <= KLATKI:
                ob.scale = (1, 1, 1); ob.keyframe_insert("scale", frame=max(fa + 13, fb - 10))
                ob.scale = (0.001, 0.001, 0.001); ob.keyframe_insert("scale", frame=max(fa + 14, fb))
            ile += 1
print("[paski] strzałek namagnesowania:", ile)

# ---------------------------------------------------------------- igła pola nad grzbietem
IGLA = Vector((-4.3, 1.2, 1.95))
m_czer = S.mat("Igla_N", (226, 40, 40), 0.5, emisja=0.5)
m_bial = S.mat("Igla_S", (245, 245, 245), 0.5, emisja=0.5)
m_ciem = S.mat("Igla_os", (30, 36, 60), 0.5)
Li, Wi, Hi = 1.15, 0.24, 0.07
v = [(-Wi, 0, 0), (0, 0, Hi), (Wi, 0, 0), (0, 0, -Hi), (0, Li, 0), (0, -Li, 0)]
f = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (1, 0, 5), (2, 1, 5), (3, 2, 5), (0, 3, 5)]
igla = S.siatka("Igla", v, f, [m_czer, m_bial], indeksy=[0, 0, 0, 0, 1, 1, 1, 1])
igla.location = IGLA
S.kula("Igla_os", IGLA, 0.11, m_ciem)
pier = S.linia("Igla_pierscien", [IGLA + Vector((math.cos(a), math.sin(a), 0)) * 1.32 for a in np.linspace(0, 2 * math.pi, 73)[:-1]],
               0.022, G.material_emisja("Pierscien", ZLOTY), zamknieta=True)
dzis0 = pole(0.0) > 0
kat = 0.0 if dzis0 else math.pi
igla.rotation_euler = (0, 0, kat)
igla.keyframe_insert("rotation_euler", frame=1)
stany = [(1, dzis0)]
fzs = [int(round(1 + z / T_KON * (KLATKI - 1))) for z in zera if 0 < z < T_KON]
print("[paski] odwrócenia: wiek [mln lat] i klatka:", [(round(wiek(z), 3), int(round(1 + z / T_KON * (KLATKI - 1)))) for z in zera if 0 < z < T_KON])
for i, fz in enumerate(fzs):
    odst = min([abs(fz - g) for j, g in enumerate(fzs) if j != i] + [99])
    pol = max(3, min(9, odst // 2 - 1))               # połowa czasu obrotu igły [klatki]
    igla.rotation_euler = (0, 0, kat)
    igla.keyframe_insert("rotation_euler", frame=fz - pol)
    kat += math.pi
    igla.rotation_euler = (0, 0, kat)
    igla.keyframe_insert("rotation_euler", frame=fz + pol)
    stany.append((fz, not stany[-1][1]))
G.wygladz(igla)

# ---------------------------------------------------------------- kamera
cam = G.kamera((6, -17, 9), (0, 0, 0), lens=50)
cam.data.shift_y = -0.075
SHIFT_PX = 0.075 * 1920
cam.data.clip_start, cam.data.clip_end = 2.0, 200.0


def tor(f):
    d = (f - 1) / (KLATKI - 1)
    t = G.gladko(d)
    return (-74 + 16 * t, 27 + 5 * t, 32.0 - 1.5 * t)


S.orbita_f(cam, (-0.2, 0.0, 0.3), tor, KLATKI)
G.tlo_kamery(cam, odl=120)

# ---------------------------------------------------------------- podpisy
OBR = ((8, 12, 24), 0.05)
S.podpis("kierunek pola" + chr(10) + "magnetycznego Ziemi", 0.4, (255, 255, 255), IGLA + Vector((0, 0, 1.38)), cam, 12, obrys=OBR, nazwa="Pod_pole")
# stan pola przy igle (zmienia się razem z igłą)
for k, (fz, dzis) in enumerate(stany):
    f_kon = stany[k + 1][0] if k + 1 < len(stany) else None
    if f_kon and f_kon - fz < 30:
        continue                                       # epizod krótszy niż sekunda: igła obraca się bez podpisu
    t = S.podpis("jak dziś" if dzis else "odwrócone", 0.46, KOL_DZIS if dzis else (130, 170, 240), IGLA + Vector((0, 0, 0.66)), cam,
                 None, obrys=OBR, nazwa=f"Stan_{k}")
    kl = [(max(1, fz + 2), 0.0), (fz + 12, 1.0)] if k else [(1, 1.0)]
    if f_kon:
        kl += [(f_kon - 10, 1.0), (f_kon - 2, 0.0)]
    G.alfa_napisu(t, kl)

S.podpis("Grzbiet Atlantycki", 0.5, (255, 255, 255), (0.3, YB + 0.2, 1.15), cam, 30, obrys=OBR, nazwa="Pod_grzbiet")
S.podpis("magma", 0.42, (255, 240, 200), (0.0, -YB - 0.9, -1.0), cam, 50, obrys=OBR, nazwa="Pod_magma")
S.podpis("zastygła lawa", 0.42, (255, 255, 255), (-3.6, -YB - 1.0, -0.85), cam, 70, obrys=OBR, nazwa="Pod_lawa")
odn = S.linia("Odn_lawa", [(-3.6, -YB - 0.95, -0.55), (-3.6, -YB - 0.02, float(wys(-3.6)) - GR / 2)], 0.012, G.material_emisja("Odn", (245, 245, 245)), 74, 88)

# złote strzałki: dno rozsuwa się na boki
m_zl = S.mat("Zlota", ZLOTY, 0.5, emisja=0.8)
for strona in (-1, 1):
    a = Vector((strona * 0.75, -YB + 0.25, 0.95))
    b = Vector((strona * 2.75, -YB + 0.25, 0.7))
    st = S.strzalka(f"Rozsuw_{strona}", a, b, 0.045, m_zl, grot=0.14)
    st.visible_shadow = False
    S.pojaw(st, 100, 24)
S.podpis("dno oceanu rozsuwa się", 0.42, ZLOTY, (0.0, -YB + 0.25, 1.75), cam, 112, obrys=OBR, nazwa="Pod_rozsuw")

# legenda (przypięta do kamery, prawy górny róg)
ODL = 7.0
px1 = G.skala_px(cam, ODL)
for k, (kolor, tekst) in enumerate(((KOL_DZIS, "lawa zastygła przy polu jak dziś"), (KOL_ODWR, "lawa zastygła przy polu odwróconym"))):
    y = 150 + k * 46 + 0.075 * 1920      # poprawka na przesunięcie obiektywu (shift_y)
    p = G.ekran_na_kamerze(cam, 1340, y, ODL)
    kw = S.siatka(f"Leg_kw_{k}", [(-14 * px1, -14 * px1, 0), (14 * px1, -14 * px1, 0), (14 * px1, 14 * px1, 0), (-14 * px1, 14 * px1, 0)],
                  [(0, 1, 2, 3)], [G.material_emisja(f"Leg_kw_{k}_mat", kolor)])
    kw.parent = cam
    kw.location = p
    G.animuj_alfa(kw.data.materials[0], [(150, 0.0), (170, 1.0)])
    t = G.napis(tekst, 27 * px1, (235, 238, 245), "arial", "LEFT", rodzic=cam, loc=tuple(p + Vector((28 * px1, 0, 0))), nazwa=f"Leg_{k}")
    G.alfa_napisu(t, [(150, 0.0), (170, 1.0)])

# źródło skali i licznik czasu (pod legendą)
p = G.ekran_na_kamerze(cam, 1326, 150 + 2 * 46 + 6 + 0.075 * 1920, ODL)
zr = G.napis("pasy według skali odwróceń pola (Cande i Kent 1995)", 22 * px1, (175, 185, 210), "arial", "LEFT", rodzic=cam,
             loc=tuple(p), nazwa="Zrodlo_skali")
G.alfa_napisu(zr, [(150, 0.0), (170, 1.0)])
p = G.ekran_na_kamerze(cam, 1326, 150 + 3 * 46 + 12 + 0.075 * 1920, ODL)
czas_n = G.napis("2,3 mln lat temu", 34 * px1, ZLOTY, "arialb", "LEFT", rodzic=cam, loc=tuple(p), nazwa="Czas")
G.alfa_napisu(czas_n, [(1, 0.0), (10, 0.0), (30, 1.0)])


def ustaw_czas(scene, depsgraph=None):
    w = wiek(T_klatki(scene.frame_current))
    tekst = "dziś" if w < 0.005 else (f"{w:.1f}".replace(".", ",") + " mln lat temu")
    czas_n.data.body = tekst
    for d in czas_n.children:
        if d.type == "FONT":
            d.data.body = tekst


bpy.app.handlers.frame_change_pre.append(ustaw_czas)
ustaw_czas(sc)

G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
