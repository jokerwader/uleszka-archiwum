# -*- coding: utf-8 -*-
"""
Klip „stonehenge-swit-2012” do odcinka 2 „Wielki uskok…” (rozdz. 12, scena z druidem: „Około 6.00 Wega zacznie
nasuwać się nad Heel Stone (kamień "A"), Spica nad ognisko "E", a Alamak (gamma Andromedy) nad "C"…”).

Niebo nad Stonehenge (51,179°N, 1,826°W) 22 grudnia 2012 r. od 6:00 do 6:23 czasu uniwersalnego, policzone:
gwiazdy z katalogu HYG (J2000), planety ze średnich elementów orbit (JPL). Kamera wisi 10 m nad środkiem kręgu
i obraca się: północny zachód (Jowisz, Alamak) -> północny wschód (Wega) -> południowy wschód (Spica, Wenus).
Złote linie to kierunki od środka kręgu przez punkty A–F ze szkicu Leszka (ollinstone.jpg; azymuty odczytane
z pikseli szkicu: A 51°, B 53°, C 344°, D 300°, E 164°, F 117°). W dołach E i C płoną ogniska, jak w tekście.
Bez ludzi. Model kręgu uproszczony (stan dzisiejszy: stojące sarseny, nadproża, trylity), odległości punktów
od środka według planu: A (Heel Stone) 77 m, pozostałe ok. 43 m.

Wynik rachunku (patrz README): gwiazdy i planety stoją blisko linii, ale nie dokładnie na nich (różnice 1–8°),
Wenus wschodzi ok. 6:16–6:20, Jowisz zachodzi ok. 6:24 – zgodnie z opisem w tekście.

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/stonehenge-swit-2012/scena.py
  ... -- --proba 40,140,230,320,420,500     (tylko kadry próbne PNG do _klatki/)
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
import niebo as N

KLATEK = 500  # 20 s
opcje = G.argumenty()
sc = G.nowa_scena(KLATEK)
sc.eevee.taa_render_samples = int(os.environ.get("USKOK3D_PROBKI", "32"))

SZER, DLUG = 51.1789, -1.8262
JD0 = N.jd(2012, 12, 22, 6.0)
MIN_KONIEC, F_KONIEC = 23.0, 470        # zegar: 6:00 w klatce 1, 6:23 w klatce 470
LENS = 12.0
OKO = Vector((0, 0, 10.0))
R_N = 6000.0
KAT_PX = (36.0 / LENS) / 1920.0
AZ_OSI = 51.2
PUNKTY = {"A": (51.2, 77.0, 3.2), "B": (52.6, 43.0, 1.5), "C": (344.2, 43.0, 3.2), "D": (299.6, 43.3, 1.5),
          "E": (163.7, 43.0, 3.2), "F": (116.6, 43.3, 1.5)}       # azymut [°], odległość [m], promień znacznika [m]
# widoki kamery: (klatka, azymut, wysokość)
WIDOKI = [(1, 322.0, 6.0), (95, 322.0, 6.0), (185, 412.0, 6.5), (270, 412.0, 6.5), (360, 500.0, 6.0), (500, 503.0, 6.0)]


def az_xy(az, r, z=0.0):
    a = math.radians(az)
    return Vector((r * math.sin(a), r * math.cos(a), z))


def minuty(f):
    return MIN_KONIEC * max(0.0, min(1.0, (f - 1) / float(F_KONIEC - 1)))


def lst_dla(f):
    return N.czas_gwiazdowy(JD0 + minuty(f) / 1440.0, DLUG)


# ---------------------------------------------------------------- świat
ramp = N.swiat_noc(horyzont=(24, 37, 70), zenit=(4, 6, 11), wykladnik=0.55, zasieg=0.6)
wnt = sc.world.node_tree
bg = wnt.nodes["Background"]
# łuna przedświtu na południowym wschodzie (Słońce 19–15° pod horyzontem, azymut ok. 106°) – bardzo słaba
tc = wnt.nodes.new("ShaderNodeTexCoord")
nr = wnt.nodes.new("ShaderNodeVectorMath"); nr.operation = "NORMALIZE"; wnt.links.new(tc.outputs["Generated"], nr.inputs[0])
dt = wnt.nodes.new("ShaderNodeVectorMath"); dt.operation = "DOT_PRODUCT"
wnt.links.new(nr.outputs[0], dt.inputs[0]); dt.inputs[1].default_value = N.z_wys_az(-6.0, 112.0)
mx = wnt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"; wnt.links.new(dt.outputs["Value"], mx.inputs[0]); mx.inputs[1].default_value = 0.0
pw = wnt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; wnt.links.new(mx.outputs[0], pw.inputs[0]); pw.inputs[1].default_value = 7.0
swit = wnt.nodes.new("ShaderNodeValue"); swit.name = "swit"; swit.outputs[0].default_value = 0.0
ml = wnt.nodes.new("ShaderNodeMath"); ml.operation = "MULTIPLY"; wnt.links.new(pw.outputs[0], ml.inputs[0]); wnt.links.new(swit.outputs[0], ml.inputs[1])
sk = wnt.nodes.new("ShaderNodeVectorMath"); sk.operation = "SCALE"; sk.inputs[0].default_value = tuple(G.srgb((120, 110, 150))[:3])
wnt.links.new(ml.outputs[0], sk.inputs["Scale"])
ad = wnt.nodes.new("ShaderNodeVectorMath"); ad.operation = "ADD"
wnt.links.new(ramp.outputs["Color"], ad.inputs[0]); wnt.links.new(sk.outputs[0], ad.inputs[1])
wnt.links.new(ad.outputs[0], bg.inputs["Color"])

# ---------------------------------------------------------------- materiały
def mat_lity(nazwa, kolor, emisja=0.0, szorstkosc=0.95):
    m = bpy.data.materials.new(nazwa); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = G.srgb(kolor); p.inputs["Roughness"].default_value = szorstkosc
    p.inputs["Emission Color"].default_value = G.srgb(kolor); p.inputs["Emission Strength"].default_value = emisja
    return m


m_trawa = mat_lity("trawa", (26, 40, 28), 0.012)
m_wal = mat_lity("wal", (40, 56, 40), 0.016)
m_kamien = mat_lity("kamien", (120, 124, 132), 0.012)
m_kreda = mat_lity("kreda", (190, 190, 180), 0.03)

# ---------------------------------------------------------------- teren
bpy.ops.mesh.primitive_circle_add(vertices=128, radius=9000, fill_type="NGON")
teren = bpy.context.active_object; teren.name = "teren"; teren.data.materials.append(m_trawa)


def pierscien(nazwa, r0, r1, z, material, seg=180):
    V, F = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        V += [(r0 * math.sin(a), r0 * math.cos(a), z), (r1 * math.sin(a), r1 * math.cos(a), z)]
    for i in range(seg):
        j = (i + 1) % seg
        F.append((2 * i, 2 * i + 1, 2 * j + 1, 2 * j))
    me = bpy.data.meshes.new(nazwa); me.from_pydata(V, [], F)
    ob = bpy.data.objects.new(nazwa, me); sc.collection.objects.link(ob); me.materials.append(material)
    return ob


pierscien("wal", 45.0, 49.5, 0.04, m_wal)            # wał wewnątrz rowu
pierscien("row", 50.0, 54.0, 0.03, mat_lity("row", (14, 22, 16), 0.006))
# jamy Aubreya: 56 jasnych znaczników na okręgu o promieniu 43,3 m
bm = bmesh.new()
for i in range(56):
    p = az_xy(AZ_OSI + 3.2 + i * 360.0 / 56, 43.3, 0.05)
    bmesh.ops.create_circle(bm, cap_ends=True, segments=16, radius=0.45, matrix=Matrix.Translation(p))
me = bpy.data.meshes.new("jamy_Aubreya"); bm.to_mesh(me); bm.free(); me.materials.append(m_kreda)
sc.collection.objects.link(bpy.data.objects.new("jamy_Aubreya", me))

# ---------------------------------------------------------------- kamienie
rnd = random.Random(2012)
bm = bmesh.new()


def blok(az, r, szer, grub, wys, z0=0.0, obrot_dod=0.0, pochyl=0.0):
    """Prostopadłościan: szer wzdłuż okręgu, grub wzdłuż promienia, lekko nieregularny."""
    p = az_xy(az, r, z0 + wys / 2)
    M = (Matrix.Translation(p) @ Matrix.Rotation(-math.radians(az) + obrot_dod, 4, "Z") @ Matrix.Rotation(pochyl, 4, "X")
         @ Matrix.Diagonal((szer, grub, wys, 1.0)))
    g = bmesh.ops.create_cube(bm, size=1.0, matrix=M)
    for v in g["verts"]:
        v.co += Vector((rnd.uniform(-0.07, 0.07), rnd.uniform(-0.07, 0.07), rnd.uniform(-0.05, 0.05)))
        if v.co.z > z0 + wys * 0.6:                     # zwężenie ku górze
            c = Vector((p.x, p.y, v.co.z))
            v.co = c + (v.co - c) * 0.9


R_S = 15.6
STOJACE = {1, 2, 3, 4, 5, 6, 7, 10, 11, 16, 21, 22, 23, 27, 28, 29, 30}
def az_s(n):
    return AZ_OSI + 6.0 + 12.0 * (n - 1)
for n_ in sorted(STOJACE):
    blok(az_s(n_), R_S, 2.1, 1.1, 2.4 if n_ == 11 else 4.1 + rnd.uniform(-0.1, 0.1))
for a_, b_ in [(29, 30), (30, 1), (1, 2), (4, 5), (6, 7), (21, 22)]:
    blok((az_s(a_) + (az_s(b_) if b_ > a_ else az_s(b_) + 360)) / 2.0, R_S * math.cos(math.radians(6)), 3.3, 1.05, 0.8, z0=4.1)
# leżące sarseny (kilka)
for n_ in (8, 9, 12, 14, 19, 25, 26):
    blok(az_s(n_) + rnd.uniform(-3, 3), R_S + rnd.uniform(-1.5, 2.5), 4.0, 1.9, 0.9, obrot_dod=rnd.uniform(-0.6, 0.6))
# trylity (podkowa otwarta ku północnemu wschodowi)
R_T = 7.6
for kat_, wys_, lewy, prawy, nadproze in [(70, 6.0, True, True, True), (125, 6.2, True, True, True),
                                         (180, 7.2, False, True, False), (235, 6.2, True, True, True), (290, 6.0, False, True, False)]:
    az = AZ_OSI + kat_
    d = math.degrees(1.45 / R_T)
    if lewy:
        blok(az - d, R_T, 2.3, 1.2, wys_)
    else:
        blok(az - d - 14, R_T - 3.0, 6.0, 2.2, 1.0, obrot_dod=0.5)       # przewrócony
    if prawy:
        blok(az + d, R_T, 2.3, 1.2, wys_)
    if nadproze:
        blok(az, R_T, 4.9, 1.25, 1.0, z0=wys_)
# błękitne kamienie (małe) na okręgu
for i in range(22):
    blok(AZ_OSI + 9 + i * 360.0 / 22 + rnd.uniform(-4, 4), 11.8 + rnd.uniform(-0.3, 0.3), 0.8, 0.6, rnd.uniform(0.8, 1.9))
# Heel Stone (A), Slaughter Stone (B, leżący), kamienie stacyjne D i F
blok(PUNKTY["A"][0], PUNKTY["A"][1], 2.4, 2.0, 4.7, pochyl=0.12)
blok(PUNKTY["B"][0], PUNKTY["B"][1], 2.1, 6.4, 0.6)
blok(PUNKTY["D"][0], PUNKTY["D"][1], 1.3, 0.9, 1.2)
blok(PUNKTY["F"][0], PUNKTY["F"][1], 1.5, 1.0, 2.7, pochyl=-0.25)
bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.14, segments=2, affect="EDGES")
me = bpy.data.meshes.new("kamienie"); bm.to_mesh(me); bm.free(); me.materials.append(m_kamien)
kamienie = bpy.data.objects.new("kamienie", me); sc.collection.objects.link(kamienie)

# kopce C i E: niski wałek wokół dołu
for lit in ("C", "E"):
    az, r, _ = PUNKTY[lit]
    bpy.ops.mesh.primitive_torus_add(major_radius=5.2, minor_radius=0.9, major_segments=64, minor_segments=10,
                                     location=az_xy(az, r, -0.3))
    t = bpy.context.active_object; t.name = "kopiec_" + lit; t.scale = (1, 1, 0.75); t.data.materials.append(m_wal)
    bpy.ops.object.shade_smooth()

# ---------------------------------------------------------------- ogniska w C i E
m_ogien = G.material_emisja("ogien", (255, 150, 50), 1.0)
for n_ in m_ogien.node_tree.nodes:
    if n_.type == "EMISSION":
        n_.inputs["Strength"].default_value = 9.0
m_zar = G.material_emisja("zar", (255, 90, 20), 1.0)
for n_ in m_zar.node_tree.nodes:
    if n_.type == "EMISSION":
        n_.inputs["Strength"].default_value = 4.0
plomienie, swiatla = [], []
for lit in ("C", "E"):
    az, r, _ = PUNKTY[lit]
    p0 = az_xy(az, r, 0.0)
    for k in range(7):
        dx, dy = rnd.uniform(-0.7, 0.7), rnd.uniform(-0.7, 0.7)
        bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=rnd.uniform(0.35, 0.6), depth=1.0, location=p0 + Vector((dx, dy, 0.6)))
        c = bpy.context.active_object; c.name = f"plomien_{lit}{k}"; c.data.materials.append(m_ogien if k < 5 else m_zar)
        plomienie.append((c, rnd.uniform(1.4, 2.8), rnd.uniform(0, 6.28), rnd.uniform(0.35, 0.6), p0 + Vector((dx, dy, 0))))
    ld = bpy.data.lights.new("swiatlo_" + lit, "POINT"); ld.energy = 5000; ld.color = (1.0, 0.5, 0.2)
    ld.shadow_soft_size = 1.0; ld.use_shadow = False
    lo = bpy.data.objects.new("swiatlo_" + lit, ld); lo.location = p0 + Vector((0, 0, 2.2)); sc.collection.objects.link(lo)
    swiatla.append(ld)
# światło gwiazd: bardzo słabe, chłodne, bez cieni
sd = bpy.data.lights.new("gwiazdy_swiatlo", "SUN"); sd.energy = 0.95; sd.color = (0.5, 0.64, 1.0); sd.use_shadow = False
so = bpy.data.objects.new("gwiazdy_swiatlo", sd); so.rotation_euler = (math.radians(35), 0, math.radians(200)); sc.collection.objects.link(so)

# ---------------------------------------------------------------- niebo: gwiazdy i planety
osie, obrot = N.niebo_obrotowe(SZER, OKO)
gw = N.wczytaj(6.0)
JD_SR = JD0 + 12.0 / 1440.0
PLANETY = {"Wenus": ("wenus", -2.6, 0.7), "Jowisz": ("jowisz", -2.0, 0.8), "Saturn": ("saturn", 0.6, 1.0), "Merkury": ("merkury", -0.5, 0.9)}
planety = {}
for nazwa, (klucz, mag, ci) in PLANETY.items():
    ra, dec = N.planeta(klucz, JD_SR)
    planety[nazwa] = dict(ra=ra, dec=dec, mag=mag, ci=ci)
    gw.append(dict(ra=ra, dec=dec, mag=mag, ci=ci, bayer="", con="", nazwa=nazwa))
gwiazdy = N.siatka_gwiazd(gw, R_N, KAT_PX, wzmocnienie=1.0, rozmiar=1.0)
gwiazdy.parent = obrot
OBIEKTY = {"Wega": N.znajdz(gw, "Vega"), "Spica": N.znajdz(gw, "Spica"), "Alamak": N.znajdz(gw, "Almach"),
           "Jowisz": planety["Jowisz"], "Wenus": planety["Wenus"]}
for nazwa, s in OBIEKTY.items():
    for mm_ in (0.0, 12.0, 23.0):
        wys, az = N.wys_az(N.kierunek(s["ra"], s["dec"], N.czas_gwiazdowy(JD0 + mm_ / 1440.0, DLUG), SZER))
        print(f"[niebo] {nazwa:7s} 6:{int(mm_):02d}  wysokość {wys:5.1f}°  azymut {az:5.1f}°")

# ---------------------------------------------------------------- linie kierunków i znaczniki punktów
def krzywa(nazwa, odcinki, kolor, alfa, grub):
    cu = bpy.data.curves.new(nazwa, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = grub
    for pts in odcinki:
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (*p, 1)
    ob = bpy.data.objects.new(nazwa, cu); sc.collection.objects.link(ob)
    m = G.material_emisja(nazwa + "_mat", kolor, alfa); cu.materials.append(m)
    return ob, m


mat_linii = {}
for lit, (az, r, rz) in PUNKTY.items():
    if lit == "B":
        continue
    # na ziemi: od środka kręgu do punktu; na niebie: przerywany łuk stałego azymutu od horyzontu do 34°
    ob, m = krzywa(f"linia_ziemia_{lit}", [[az_xy(az, 17.5, 0.08), az_xy(az, r - rz, 0.08)]], G.ZLOTY, 0.0, 0.07)
    odc = []
    for k in range(17):
        a0, a1 = 0.4 + k * 2.0, 0.4 + k * 2.0 + 1.1
        odc.append([OKO + N.z_wys_az(a0, az, R_N * 0.98), OKO + N.z_wys_az(a1, az, R_N * 0.98)])
    ob2, m2 = krzywa(f"linia_niebo_{lit}", odc, G.ZLOTY, 0.0, R_N * KAT_PX * 1.0)
    mat_linii[lit] = (m, m2)
znaczniki = {}
for lit, (az, r, rz) in PUNKTY.items():
    bpy.ops.mesh.primitive_torus_add(major_radius=rz, minor_radius=0.11, major_segments=64, minor_segments=8, location=az_xy(az, r, 0.12))
    t = bpy.context.active_object; t.name = "znacznik_" + lit
    m = G.material_emisja(f"znacznik_{lit}_mat", (232, 60, 40), 0.0); t.data.materials.append(m)
    znaczniki[lit] = m

# strony świata na horyzoncie
for az, tekst in [(0, "PÓŁNOC"), (45, "PN.-WSCH."), (90, "WSCHÓD"), (135, "PD.-WSCH."), (180, "POŁUDNIE"), (225, "PD.-ZACH."),
                  (270, "ZACHÓD"), (315, "PN.-ZACH.")]:
    p = OKO + N.z_wys_az(1.9, az, 800.0)
    G.napis(tekst, 20.0, (120, 140, 185), "arialb", "CENTER", loc=p, rot=(math.radians(90), 0, math.radians(-az)),
            nazwa=f"strona_{az}", alfa=0.75)

# ---------------------------------------------------------------- kamera i podpisy
cam = G.kamera(OKO, OKO + Vector((0, 1, 0)), lens=LENS)
cam.data.clip_start, cam.data.clip_end = 0.05, 20000
ODL = 0.3
px = G.skala_px(cam, ODL)


def napis_ekran(tekst, x, y, rozm_px, kolor, kroj="georgiab", wyr="CENTER", nazwa="ekran"):
    pos = G.ekran_na_kamerze(cam, x, y, ODL)
    return G.napis(tekst, rozm_px * px, kolor, kroj, wyr, rodzic=cam, loc=pos, nazwa=nazwa,
                   obrys=((5, 7, 12), 0.03 * rozm_px * px))


def etykieta(tekst, rozm_px, kolor, nazwa, kroj="arialb", wyr="CENTER"):
    return G.napis(tekst, rozm_px * px, kolor, kroj, wyr, rodzic=cam, nazwa=nazwa, obrys=((5, 7, 12), 0.04 * rozm_px * px))


def na_ekran(p, dx=0.0, dy=0.0):
    q = cam.matrix_world.inverted() @ Vector(p)
    if q.z > -1e-6:
        return Vector((0, 0, 10.0))          # za kamerą: poza kadrem
    q = q * (ODL / -q.z)
    return Vector((q.x + dx * px, q.y + dy * px, -ODL - 0.0005))


tytul = napis_ekran("Stonehenge, 22 grudnia 2012", 1160, 80, 50, G.ZLOTY, nazwa="tytul")
zegar = napis_ekran("godz. 6:00", 1160, 140, 42, (235, 232, 220), "georgiab", nazwa="zegar")
objasn = napis_ekran("złote linie: kierunki od środka kręgu przez punkty ze szkicu Leszka", 1160, 192, 27, (200, 205, 220),
                     "georgia", nazwa="objasnienie")
G.alfa_napisu(tytul, [(1, 0), (6, 0), (26, 1)])
G.alfa_napisu(zegar, [(1, 0), (12, 0), (32, 1)])
G.alfa_napisu(objasn, [(1, 0), (40, 0), (65, 1)])

et_gw = {}
for nazwa in OBIEKTY:
    et_gw[nazwa] = etykieta(nazwa, 40, (235, 240, 255), "et_" + nazwa, wyr="LEFT")
et_pkt = {}
for lit in PUNKTY:
    et_pkt[lit] = etykieta(lit, 44, G.ZOLTY_LESZKA, "et_pkt_" + lit, "georgiab")
et_ogn = {lit: etykieta("ognisko", 24, (255, 190, 130), "et_ognisko_" + lit, "georgia") for lit in ("C", "E")}

# pojawianie się: wszystko, co dotyczy danego widoku, tuż przed nim
OKNA = {"D": 12, "C": 12, "Jowisz": 30, "Alamak": 30, "A": 120, "B": 120, "Wega": 150, "E": 300, "F": 300, "Spica": 330, "Wenus": 425}
for lit, (m, m2) in mat_linii.items():
    f0 = OKNA[lit]
    G.animuj_alfa(m, [(1, 0), (f0, 0), (f0 + 25, 0.75)])
    G.animuj_alfa(m2, [(1, 0), (f0 + 10, 0), (f0 + 35, 0.65)])
for lit, m in znaczniki.items():
    f0 = OKNA[lit]
    G.animuj_alfa(m, [(1, 0), (f0, 0), (f0 + 25, 0.95)])
    G.alfa_napisu(et_pkt[lit], [(1, 0), (f0, 0), (f0 + 25, 1)])
for lit in ("C", "E"):
    G.alfa_napisu(et_ogn[lit], [(1, 0), (OKNA[lit] + 10, 0), (OKNA[lit] + 35, 0.9)])
for nazwa, ob in et_gw.items():
    f0 = OKNA[nazwa]
    G.alfa_napisu(ob, [(1, 0), (f0, 0), (f0 + 25, 1)])
wenus_info = napis_ekran("6:23 – Wenus wschodzi, Jowisz po drugiej stronie nieba zachodzi", 700, 330, 32, (240, 232, 210), "georgia", nazwa="wenus_info")
G.alfa_napisu(wenus_info, [(1, 0), (440, 0), (465, 1)])


def kam_kier(f):
    for (f0, a0, w0), (f1, a1, w1) in zip(WIDOKI, WIDOKI[1:]):
        if f <= f1:
            t = G.gladko5((f - f0) / float(f1 - f0)) if a0 != a1 and f1 - f0 < 120 else (f - f0) / float(f1 - f0)
            return a0 + (a1 - a0) * t, w0 + (w1 - w0) * t
    return WIDOKI[-1][1], WIDOKI[-1][2]


def ustaw(scene, depsgraph=None):
    f = scene.frame_current
    az, wys = kam_kier(f)
    cam.rotation_euler = (math.radians(90 + wys), 0, math.radians(-az))
    lst = lst_dla(f)
    N.ustaw_czas(obrot, lst)
    mn = minuty(f)
    swit.outputs[0].default_value = 0.10 + 0.30 * mn / MIN_KONIEC
    tekst = f"godz. 6:{int(mn):02d}"
    zegar.data.body = tekst
    if zegar.children:
        zegar.children[0].data.body = tekst
    for i, (c, wys_p, faza, r_p, p0) in enumerate(plomienie):
        h = wys_p * (0.75 + 0.25 * math.sin(f * 0.9 + faza) + 0.12 * math.sin(f * 2.3 + faza * 2))
        c.scale = (1, 1, h)
        c.location = p0 + Vector((0.08 * math.sin(f * 0.7 + faza), 0.08 * math.cos(f * 0.5 + faza), h / 2))
    for i, ld in enumerate(swiatla):
        ld.energy = 5000 * (0.85 + 0.15 * math.sin(f * 0.8 + i * 2.0) + 0.08 * math.sin(f * 2.1 + i))
    bpy.context.view_layer.update()
    for nazwa, s in OBIEKTY.items():
        p = OKO + N.kierunek(s["ra"], s["dec"], lst, SZER) * R_N
        et_gw[nazwa].location = na_ekran(p, 26, 30 if nazwa != "Wenus" else 44)
    for lit, (a_, r_, rz_) in PUNKTY.items():
        dx = {"A": 44, "B": -40}.get(lit, 0)
        et_pkt[lit].location = na_ekran(az_xy(a_, r_, 0.0), dx, 52 if lit != "B" else -44)
    for lit in ("C", "E"):
        a_, r_, _ = PUNKTY[lit]
        et_ogn[lit].location = na_ekran(az_xy(a_, r_, 0.0), 120, -22)


bpy.app.handlers.frame_change_pre.append(ustaw)
ustaw(sc)
for ob in sc.objects:
    ob.visible_shadow = False
N.poswiata(sc, 0.9, 0.45, 0.45)

G.renderuj(TU, opcje, kadr_klatka=KLATEK)
