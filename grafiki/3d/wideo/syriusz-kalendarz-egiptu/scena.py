# -*- coding: utf-8 -*-
"""
Klip „syriusz-kalendarz-egiptu” do odcinka 2 „Wielki uskok…” (rozdz. 12: „…kolejni faraonowie wstępujący na tron
w starożytnym Egipcie składali przysięgę iż w żadnym wypadku nie zmienią kalendarza…”).

ILUSTRACJA zjawiska potwierdzonego: kalendarz cywilny Egiptu miał 365 dni (12 miesięcy po 30 dni i 5 dni dodatkowych)
i nie znał roku przestępnego. Dlatego wschód Syriusza przed świtem (tzw. wschód heliakalny, zapowiedź wylewu Nilu)
co 4 lata wypadał o 1 dzień później w kalendarzu i wracał do Nowego Roku po ok. 1460 latach (cykl sotisowy).

Lewa część kadru: niebo przed świtem nad Memfis (29,85°N), widok na wschód-południowy wschód, policzone na świt
19 lipca 1322 r. p.n.e. (kalendarz juliański) – początek cyklu sotisowego, który skończył się w 139 r. n.e.
Gwiazdy z katalogu HYG przeliczone na tę datę (ruch własny i precesja, `_wspolne/epoka.py`); Słońce pod horyzontem
policzone (łuna świtu świeci z jego kierunku). Syriusz wschodzi w azymucie ok. 111°, nad nim stoi Orion. Prawa część: koło roku egipskiego ze znacznikiem dnia
wschodu Syriusza, który obiega koło w 1460 lat.
O samej przysiędze faraonów mówi tekst Leszka; klip jej nie pokazuje, pokazuje tylko, co dawał niezmieniany kalendarz.

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/syriusz-kalendarz-egiptu/scena.py
  ... -- --proba 1,120,220,330,425     (tylko kadry próbne PNG do _klatki/)
"""
import bpy, math, os, sys
from mathutils import Vector

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
import niebo as N
import epoka as E

KLATEK = 425  # 17 s
opcje = G.argumenty()
sc = G.nowa_scena(KLATEK)
sc.eevee.taa_render_samples = int(os.environ.get("USKOK3D_PROBKI", "32"))

SZER = 29.85                     # Memfis (Mit Rahina)
JD_NIEBA = E.jd_jul(-1321, 7, 19)    # 19 lipca 1322 r. p.n.e. (rok astronomiczny -1321), kalendarz juliański
gw = E.wczytaj(JD_NIEBA, 6.0)        # gwiazdy na tę datę: ruch własny + precesja
SYR = N.znajdz(gw, "Sirius")
# czas gwiazdowy [h]: Syriusz od 1° pod horyzontem do 6° nad nim
LST0 = E.lst_dla_wysokosci(SYR["ra"], SYR["dec"], SZER, -1.0)
LST1 = E.lst_dla_wysokosci(SYR["ra"], SYR["dec"], SZER, 6.0)
if LST1 < LST0:
    LST1 += 24.0
SL_RA, SL_DEC, SL_DLUG = E.slonce(JD_NIEBA)
for _l in (LST0, (LST0 + LST1) / 2, LST1):
    print("[syriusz] LST %.3f h: Syriusz wys %.1f° az %.1f°; Słońce wys %.1f° az %.1f°" % (
        _l % 24, *E.wys_az(SYR["ra"], SYR["dec"], _l, SZER), *E.wys_az(SL_RA, SL_DEC, _l, SZER)))
LENS = 18.0
AZ_K, WYS_K = 120.0, 16.0        # kierunek kamery
OKO = Vector((0, 0, 25.0))       # krawędź pustynnego płaskowyżu nad doliną
R_N = 6000.0
F_KOLO = (150, 195)              # pojawianie się koła kalendarza
F_LATA = (205, 385)              # bieg licznika lat 0 -> 1460

# ---------------------------------------------------------------- świat: granat i łuna świtu
w = sc.world
nt = w.node_tree
bg = nt.nodes["Background"]


def vm(op, a=None, b=None, skala=None):
    n = nt.nodes.new("ShaderNodeVectorMath"); n.operation = op
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (tuple, list, Vector)):
            n.inputs[i].default_value = tuple(x)[:3]
        else:
            nt.links.new(x, n.inputs[i])
    if skala is not None:
        if isinstance(skala, (int, float)):
            n.inputs["Scale"].default_value = skala
        else:
            nt.links.new(skala, n.inputs["Scale"])
    return n


def mm(op, a, b=None):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]


tc = nt.nodes.new("ShaderNodeTexCoord")
kier = vm("NORMALIZE", tc.outputs["Generated"]).outputs[0]
sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(kier, sep.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 0.6
nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = G.srgb((27, 42, 77)); ramp.color_ramp.elements[1].color = G.srgb((5, 7, 12))
nt.links.new(mm("POWER", mr.outputs["Result"], 0.6), ramp.inputs["Fac"])
# Słońce pod horyzontem na północnym wschodzie: kierunek policzony (w każdej klatce ustawia go funkcja ustaw)
SLONCE_KIER = N.z_wys_az(*E.wys_az(SL_RA, SL_DEC, (LST0 + LST1) / 2, SZER))
ds_wezel = vm("DOT_PRODUCT", kier, SLONCE_KIER)
ds = ds_wezel.outputs["Value"]
dsp = mm("MAXIMUM", ds, 0.0)
swit = nt.nodes.new("ShaderNodeValue"); swit.name = "swit"; swit.outputs[0].default_value = 0.3
g_waska = mm("MULTIPLY", mm("POWER", dsp, 9.0), swit.outputs[0])
g_szeroka = mm("MULTIPLY", mm("POWER", dsp, 2.2), swit.outputs[0])
k1 = vm("SCALE", tuple(G.srgb((255, 140, 55))[:3]), skala=g_waska).outputs[0]
k2 = vm("SCALE", tuple(G.srgb((38, 66, 125))[:3]), skala=g_szeroka).outputs[0]
suma = vm("ADD", vm("ADD", ramp.outputs["Color"], k1).outputs[0], k2).outputs[0]
nt.links.new(suma, bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0

# ---------------------------------------------------------------- ziemia: dolina, rzeka, wzgórza na horyzoncie
def plaska(nazwa, V, kolor, sila=1.0):
    me = bpy.data.meshes.new(nazwa); me.from_pydata(V, [], [tuple(range(len(V)))])
    ob = bpy.data.objects.new(nazwa, me); sc.collection.objects.link(ob)
    m = G.material_emisja(nazwa + "_mat", kolor, 1.0); me.materials.append(m)
    return ob, m


plaska("dolina", [(-9000, -9000, 0), (9000, -9000, 0), (9000, 9000, 0), (-9000, 9000, 0)], (6, 9, 15))
# Nil płynie z południa na północ; patrzymy z zachodniego brzegu na wschód-południowy wschód
brzeg_z, brzeg_w = [], []
for i in range(81):
    y = -6000 + 150 * i
    x0 = 650 + 110 * math.sin(y / 900.0) + 60 * math.sin(y / 370.0 + 1.0)
    szer = 330 + 70 * math.sin(y / 1300.0 + 0.5)
    brzeg_z.append((x0, y, 0.2)); brzeg_w.append((x0 + szer, y, 0.2))
rzeka, m_rzeka = plaska("Nil", brzeg_z + brzeg_w[::-1], (44, 66, 112))
# wzgórza pustyni wschodniej na horyzoncie
V, F = [], []
n_w = 720
for i in range(n_w + 1):
    az = 2 * math.pi * i / n_w
    wys = 55 + 26 * math.sin(az * 7 + 1.3) + 16 * math.sin(az * 19 + 0.4) + 9 * math.sin(az * 43) + 5 * math.sin(az * 97 + 2)
    r = 5200.0
    V += [(r * math.sin(az), r * math.cos(az), -30.0), (r * math.sin(az), r * math.cos(az), 25.0 + max(4.0, wys))]
for i in range(n_w):
    F.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
me = bpy.data.meshes.new("wzgorza"); me.from_pydata(V, [], F)
wzg = bpy.data.objects.new("wzgorza", me); sc.collection.objects.link(wzg)
m_wzg = G.material_emisja("wzgorza_mat", (4, 6, 11), 1.0); m_wzg.use_backface_culling = False; me.materials.append(m_wzg)

# ---------------------------------------------------------------- niebo
osie, obrot = N.niebo_obrotowe(SZER, OKO)
KAT_PX = (36.0 / LENS) / 1920.0
gwiazdy = N.siatka_gwiazd(gw, R_N, KAT_PX, wzmocnienie=1.15, rozmiar=1.15)
gwiazdy.parent = obrot
m_gw = gwiazdy.data.materials[0]

# linie Oriona
ORION = [("Betelgeuse", "Bellatrix"), ("Betelgeuse", "Alnitak"), ("Bellatrix", "Mintaka"), ("Alnitak", "Alnilam"),
         ("Alnilam", "Mintaka"), ("Alnitak", "Saiph"), ("Mintaka", "Rigel"), ("Saiph", "Rigel")]
cu = bpy.data.curves.new("orion", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = R_N * KAT_PX * 0.9
for a, b in ORION:
    sa, sb = N.znajdz(gw, a), N.znajdz(gw, b)
    pa, pb = N.eq(sa["ra"], sa["dec"], R_N * 0.999), N.eq(sb["ra"], sb["dec"], R_N * 0.999)
    sp = cu.splines.new("POLY"); sp.points.add(1)
    sp.points[0].co = (*pa.lerp(pb, 0.12), 1); sp.points[1].co = (*pa.lerp(pb, 0.88), 1)
orion_ob = bpy.data.objects.new("orion", cu); sc.collection.objects.link(orion_ob); orion_ob.parent = obrot
m_orion = G.material_emisja("orion_mat", (150, 180, 235), 0.0); cu.materials.append(m_orion)
G.animuj_alfa(m_orion, [(1, 0), (40, 0), (75, 0.5)])

# ---------------------------------------------------------------- kamera
cam = G.kamera(OKO, OKO + N.z_wys_az(WYS_K, AZ_K), lens=LENS)
cam.data.clip_start, cam.data.clip_end = 0.05, 20000
cam.rotation_euler = (math.radians(90 + WYS_K), 0, math.radians(-AZ_K))
ODL = 0.3
px = G.skala_px(cam, ODL)


def napis_ekran(tekst, x, y, rozm_px, kolor, kroj="georgiab", wyr="CENTER", nazwa="ekran", obrot_z=0.0):
    pos = G.ekran_na_kamerze(cam, x, y, ODL)
    return G.napis(tekst, rozm_px * px, kolor, kroj, wyr, rodzic=cam, loc=pos, rot=(0, 0, obrot_z), nazwa=nazwa,
                   obrys=((5, 7, 12), 0.03 * rozm_px * px))


def na_ekran(p, dx=0.0, dy=0.0):
    q = cam.matrix_world.inverted() @ Vector(p)
    q = q * (ODL / -q.z)
    return Vector((q.x + dx * px, q.y + dy * px, -ODL - 0.0005))


tytul = napis_ekran("Wschód Syriusza przed świtem", 760, 84, 50, G.ZLOTY, nazwa="tytul")
podtyt = napis_ekran("w Egipcie zapowiadał wylew Nilu", 760, 136, 30, (225, 220, 205), "georgia", nazwa="podtytul")
G.alfa_napisu(tytul, [(1, 0), (8, 0), (30, 1)])
G.alfa_napisu(podtyt, [(1, 0), (20, 0), (45, 1)])
data_n = napis_ekran("niebo obliczone: Memfis, świt 19 lipca 1322 r. p.n.e.", 760, 180, 23, (165, 180, 215), "georgia", nazwa="data_nieba")
G.alfa_napisu(data_n, [(1, 0), (32, 0), (58, 0.9)])
et_syr = G.napis("Syriusz", 40 * px, (235, 240, 255), "arialb", "LEFT", rodzic=cam, nazwa="et_syriusz", obrys=((5, 7, 12), 1.4 * px))
et_ori = G.napis("Orion", 36 * px, (170, 195, 240), "arialb", "CENTER", rodzic=cam, nazwa="et_orion", obrys=((5, 7, 12), 1.3 * px))
et_nil = G.napis("Nil", 30 * px, (150, 180, 230), "georgia", "CENTER", rodzic=cam, nazwa="et_nil", obrys=((5, 7, 12), 1.1 * px))
G.alfa_napisu(et_syr, [(1, 0), (55, 0), (85, 1)])
G.alfa_napisu(et_ori, [(1, 0), (40, 0), (75, 0.9)])
G.alfa_napisu(et_nil, [(1, 0), (30, 0), (60, 0.8)])

# ---------------------------------------------------------------- koło kalendarza (w przestrzeni ekranu)
KX, KY, KR = 1455, 455, 235        # środek i promień zewnętrzny koła (piksele)
SRODEK_K = G.ekran_na_kamerze(cam, KX, KY, ODL)
mat_kola = []


def kat(dzien):
    """Kąt na kole dla dnia roku (0..365): początek u góry, zgodnie z ruchem wskazówek zegara."""
    return math.radians(90.0 - 360.0 * dzien / 365.0)


def wycinek(nazwa, r0, r1, d0, d1, kolor, alfa, glebia=0.0):
    k = max(2, int((d1 - d0) * 1.5))
    V = []
    for i in range(k + 1):
        a = kat(d0 + (d1 - d0) * i / k)
        V.append((r0 * px * math.cos(a), r0 * px * math.sin(a), 0))
    for i in range(k, -1, -1):
        a = kat(d0 + (d1 - d0) * i / k)
        V.append((r1 * px * math.cos(a), r1 * px * math.sin(a), 0))
    me = bpy.data.meshes.new(nazwa); me.from_pydata(V, [], [tuple(range(len(V)))])
    ob = bpy.data.objects.new(nazwa, me); sc.collection.objects.link(ob)
    ob.parent = cam; ob.location = SRODEK_K + Vector((0, 0, glebia))
    m = G.material_emisja(nazwa + "_mat", kolor, 0.0); me.materials.append(m)
    mat_kola.append((m, alfa))
    return ob


# tło koła (lekko przyciemnia niebo pod spodem)
wycinek("kolo_tlo", 0, KR + 62, 0, 365, (8, 12, 24), 0.72, -0.0006)
PORY = [("ACHET", "wylew", (70, 130, 215)), ("PERET", "zasiewy", (80, 160, 95)), ("SZEMU", "żniwa", (215, 165, 70))]
MIESIACE = ["Thot", "Paofi", "Athyr", "Choiak", "Tybi", "Mechir", "Famenot", "Farmuti", "Pachons", "Pauni", "Epifi", "Mesore"]
teksty_kola = []
for i, (nazwa, opis, kolor) in enumerate(PORY):
    wycinek(f"pora{i}", KR - 78, KR - 34, i * 120 + 0.6, (i + 1) * 120 - 0.6, kolor, 0.85)
    a = kat(i * 120 + 60)
    for tekst, dy, rozm, kroj, kol in ((nazwa, 12, 23, "georgiab", kolor), (opis, -13, 19, "georgia", (215, 215, 215))):
        t = G.napis(tekst, rozm * px, kol, kroj, "CENTER", rodzic=cam, nazwa=f"pora_t{i}_{tekst}",
                    loc=SRODEK_K + Vector((108 * px * math.cos(a), (108 * math.sin(a) + dy) * px, 0.0003)))
        teksty_kola.append(t)
for i, nazwa in enumerate(MIESIACE):
    wycinek(f"mies{i}", KR - 30, KR, i * 30 + 0.5, (i + 1) * 30 - 0.5, (236, 226, 200) if i % 2 == 0 else (196, 184, 158), 0.9)
    a = kat(i * 30 + 15)
    obr = a - math.pi / 2 if math.sin(a) >= 0 else a + math.pi / 2
    t = G.napis(nazwa, 19 * px, (232, 226, 210), "georgia", "CENTER", rodzic=cam, nazwa=f"mies_t{i}", rot=(0, 0, obr),
                loc=SRODEK_K + Vector(((KR + 20) * px * math.cos(a), (KR + 20) * px * math.sin(a), 0.0003)))
    teksty_kola.append(t)
wycinek("epagomenalne", KR - 30, KR, 360.4, 364.6, (225, 80, 60), 0.95)
t = G.napis("5 dni\ndodatkowych", 17 * px, (240, 150, 130), "georgia", "RIGHT", rodzic=cam, nazwa="epag_t", odstep=0.9,
            loc=SRODEK_K + Vector((-16 * px, (KR + 38) * px, 0.0003)))
teksty_kola.append(t)
t = G.napis("Nowy\nRok", 17 * px, G.ZLOTY, "georgiab", "LEFT", rodzic=cam, nazwa="nowyrok_t", odstep=0.9,
            loc=SRODEK_K + Vector((12 * px, (KR + 38) * px, 0.0003)))
teksty_kola.append(t)
# środek koła: licznik lat i opis
licznik = G.napis("rok 0", 40 * px, G.ZLOTY, "georgiab", "CENTER", rodzic=cam, nazwa="licznik",
                  loc=SRODEK_K + Vector((0, 4 * px, 0.0003)))
opis_k = G.napis("rok ma 365 dni,\nbez dnia przestępnego", 19 * px, (225, 222, 210), "georgia", "CENTER", rodzic=cam, nazwa="opis_kola",
                 odstep=0.95, loc=SRODEK_K + Vector((0, -42 * px, 0.0003)))
teksty_kola += [licznik, opis_k]
# znacznik dnia wschodu Syriusza
bpy.ops.mesh.primitive_circle_add(vertices=32, radius=11 * px, fill_type="NGON")
znacznik = bpy.context.active_object; znacznik.name = "znacznik"; znacznik.parent = cam
m_zn = G.material_emisja("znacznik_mat", (255, 255, 255), 0.0); znacznik.data.materials.append(m_zn)
for n_ in m_zn.node_tree.nodes:
    if n_.type == "EMISSION":
        n_.inputs["Strength"].default_value = 3.0
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=19 * px, fill_type="NGON")
znacznik2 = bpy.context.active_object; znacznik2.name = "znacznik_otok"; znacznik2.parent = cam
m_zn2 = G.material_emisja("znacznik2_mat", (120, 170, 255), 0.0); znacznik2.data.materials.append(m_zn2)
# ślad za znacznikiem (łuk pokazujący, o ile dni przesunął się wschód)
slad_cu = bpy.data.curves.new("slad", "CURVE"); slad_cu.dimensions = "3D"; slad_cu.bevel_depth = 2.4 * px
sp = slad_cu.splines.new("POLY"); sp.points.add(365)
for i in range(366):
    a = kat(i)
    sp.points[i].co = ((KR + 6) * px * math.cos(a), (KR + 6) * px * math.sin(a), 0, 1)
slad = bpy.data.objects.new("slad", slad_cu); sc.collection.objects.link(slad); slad.parent = cam
slad.location = SRODEK_K + Vector((0, 0, 0.0004))
m_slad = G.material_emisja("slad_mat", (150, 195, 255), 0.0); slad_cu.materials.append(m_slad)
slad_cu.bevel_factor_end = 0.0
legenda = napis_ekran("●  dzień wschodu Syriusza: co 4 lata o 1 dzień później", 1455, 772, 26, (190, 215, 255), "georgia", nazwa="legenda")
wniosek = napis_ekran("po 1460 latach znów w Nowy Rok (cykl sotisowy)", 1455, 818, 30, G.ZLOTY, "georgiab", nazwa="wniosek")

f0, f1 = F_KOLO
for m, a in mat_kola:
    G.animuj_alfa(m, [(1, 0), (f0, 0), (f1, a)])
for t in teksty_kola:
    G.alfa_napisu(t, [(1, 0), (f0 + 10, 0), (f1 + 10, 1)])
for m in (m_zn, m_slad):
    G.animuj_alfa(m, [(1, 0), (f1 - 10, 0), (f1 + 15, 1)])
G.animuj_alfa(m_zn2, [(1, 0), (f1 - 10, 0), (f1 + 15, 0.45)])
G.alfa_napisu(legenda, [(1, 0), (f1, 0), (f1 + 25, 1)])
G.alfa_napisu(wniosek, [(1, 0), (F_LATA[1] - 25, 0), (F_LATA[1] + 5, 1)])

ALN = N.znajdz(gw, "Alnilam")
BET = N.znajdz(gw, "Betelgeuse")


def ustaw(scene, depsgraph=None):
    f = scene.frame_current
    t = (f - 1) / (KLATEK - 1)
    lst = LST0 + (LST1 - LST0) * (0.72 * G.gladko(min(1.0, (f - 1) / 190.0)) + 0.28 * t)
    N.ustaw_czas(obrot, lst)
    ds_wezel.inputs[1].default_value = tuple(N.z_wys_az(*E.wys_az(SL_RA, SL_DEC, lst, SZER)))
    swit.outputs[0].default_value = 0.22 + 0.5 * t
    m_gw.node_tree.nodes["widac"].outputs[0].default_value = 1.0 - 0.22 * t
    bpy.context.view_layer.update()
    ps = OKO + N.kierunek(SYR["ra"], SYR["dec"], lst, SZER) * R_N
    et_syr.location = na_ekran(ps, 26, 6)
    po = OKO + (N.kierunek(BET["ra"], BET["dec"], lst, SZER) * 0.5 + N.kierunek(ALN["ra"], ALN["dec"], lst, SZER) * 0.5).normalized() * R_N
    et_ori.location = na_ekran(po, -150, 40)
    et_nil.location = na_ekran((800, 900, 0), 0, 4)
    # licznik lat i znacznik
    u = G.gladko((f - F_LATA[0]) / float(F_LATA[1] - F_LATA[0]))
    lata = int(round(1460 * u / 4.0)) * 4
    dzien = lata / 4.0
    a = kat(dzien)
    for ob, dz in ((znacznik, 0.0006), (znacznik2, 0.0005)):
        ob.location = SRODEK_K + Vector(((KR + 6) * px * math.cos(a), (KR + 6) * px * math.sin(a), dz))
    slad_cu.bevel_factor_end = min(1.0, dzien / 365.0)
    tekst = f"rok {lata}"
    licznik.data.body = tekst
    if licznik.children:
        licznik.children[0].data.body = tekst


bpy.app.handlers.frame_change_pre.append(ustaw)
ustaw(sc)
for ob in sc.objects:
    ob.visible_shadow = False
N.poswiata(sc, 0.9, 0.4, 0.4)

G.renderuj(TU, opcje, kadr_klatka=KLATEK)
