# -*- coding: utf-8 -*-
"""Klip „kalendarz-majow-2012”: koła kalendarza Majów i data Długiej Rachuby 13.0.0.0.0 (rozdział 13).

Trzy koła zazębione jak tryby, każde przesuwa się o jeden ząb na dzień:
  * koło 13 liczb Tzolk'in (liczby zapisane cyframi Majów: kropka = 1, kreska = 5),
  * koło 20 nazw dni Tzolk'in (Imix … Ajaw),
  * koło 365 dni Haab' (18 miesięcy po 20 dni i 5 dni Wayeb'), widać tylko jego brzeg.
Promienie kół są w proporcji liczby zębów (13 : 20 : 365), więc zęby naprawdę do siebie pasują.
Koła kręcą się dzień po dniu, a licznik Długiej Rachuby po prawej dochodzi do 13.0.0.0.0 – dnia
4 Ajaw 3 K'ank'in (21 grudnia 2012 r. według najczęściej używanego przelicznika GMT 584283,
23 grudnia według przelicznika 584285 – tę datę podaje tekst).

Nazwy dni i miesięcy w nowej pisowni (Guatemalan Academy of Mayan Languages), bez glifów –
glify zastępują napisy, liczby są zapisane cyframi Majów.

Uruchomienie (z katalogu repozytorium):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/kalendarz-majow-2012/scena.py
  ... -- --proba 40,200,330,500
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, Matrix

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G

OPCJE = G.argumenty()
KLATKI = 500  # 20 s

DNI = ["Imix", "Ik'", "Ak'b'al", "K'an", "Chikchan", "Kimi", "Manik'", "Lamat", "Muluk", "Ok", "Chuwen", "Eb'",
       "B'en", "Ix", "Men", "K'ib'", "Kab'an", "Etz'nab'", "Kawak", "Ajaw"]
MIESIACE = ["Pop", "Wo'", "Sip", "Sotz'", "Sek", "Xul", "Yaxk'in", "Mol", "Ch'en", "Yax", "Sak'", "Keh", "Mak",
            "K'ank'in", "Muwan", "Pax", "K'ayab", "Kumk'u", "Wayeb'"]
# stan końcowy: 13.0.0.0.0 = 4 Ajaw 3 K'ank'in
LICZBA0 = 4          # 1..13
DZIEN0 = 19          # Ajaw
HAAB0 = 13 * 20 + 3  # 3 K'ank'in (pozycja 0..364)
D_START = -60        # dni przed 13.0.0.0.0 na początku klipu (12.19.19.15.0)
F_RUCH0, F_RUCH1 = 30, 345

# ---------------------------------------------------------------- geometria kół
PODZ = 2 * math.pi * 1.0 / 20       # podziałka (łuk na ząb) przy promieniu koła 20 = 1
R20 = 1.0
R13 = 13 * PODZ / (2 * math.pi)
R365 = 365 * PODZ / (2 * math.pi)
H = 0.30 * PODZ                     # wysokość zęba nad / pod okręgiem podziałowym
C20 = Vector((-0.30, 0.18, 0))
C13 = C20 + Vector((-(R13 + R20), 0, 0))
C365 = C20 + Vector((R20 + R365, 0, 0))

KAMIEN = (216, 186, 136)
KAMIEN_BOK = (150, 118, 80)
NAPIS = (72, 44, 22)
ZLOTY = G.ZLOTY

sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))


def kolo_zebate(nazwa, n, r, przes_kata=0.0, r_wew=None, grub=0.07, seg_zab=6):
    """Płaskie koło zębate (n zębów, okrąg podziałowy r); ząb nr k na kącie przes + k·2π/n.
    r_wew: jeśli podany, koło jest pierścieniem."""
    w = 2 * math.pi / n
    bm = bmesh.new()
    zew = []
    for k in range(n):
        c = przes_kata + k * w
        for frac, rr in ((-0.5, r - H), (-0.27, r - H), (-0.17, r + H), (0.17, r + H), (0.27, r - H)):
            a = c + frac * w
            zew.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), 0)))
    krawedzie = [bm.edges.new((zew[i], zew[(i + 1) % len(zew)])) for i in range(len(zew))]
    if r_wew is not None:
        m = max(64, n * 2)
        wew = [bm.verts.new((r_wew * math.cos(2 * math.pi * j / m + przes_kata), r_wew * math.sin(2 * math.pi * j / m + przes_kata), 0))
               for j in range(m)]
        krawedzie += [bm.edges.new((wew[i], wew[(i + 1) % m])) for i in range(m)]
    # wypełnienie (wewnętrzna pętla = otwór)
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=krawedzie, normal=(0, 0, 1))
    me = bpy.data.meshes.new(nazwa)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(nazwa, me)
    sc.collection.objects.link(ob)
    so = ob.modifiers.new("grubosc", "SOLIDIFY")
    so.thickness = grub
    so.offset = -1.0
    return ob


def material_kamien(nazwa, kolor=KAMIEN, bok=KAMIEN_BOK):
    m = bpy.data.materials.new(nazwa)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    from wezly import Wezly
    W = Wezly(nt)
    n = W.geometria("Normal")
    _, _, nz = W.sep(n)
    o = W.coord("Object")
    r = W.vmath("LENGTH", o)
    # delikatne słoje „kamienia” i ciemniejszy bok
    szum = W._node("ShaderNodeTexNoise")
    szum.inputs["Scale"].default_value = 9.0
    szum.inputs["Detail"].default_value = 4.0
    W._in(szum.inputs["Vector"], W.coord("Object"))
    plam = W.smooth(0.35, 0.75, szum.outputs["Fac"])
    gora = W.mix(W.mul(plam, 0.35), G.srgb(kolor), G.srgb((190, 158, 110)))
    kol = W.mix(W.smooth(0.5, 0.9, nz), G.srgb(bok), gora)
    W.emisja_wyjscie(kol)
    return m


def mat_tekst(nazwa, kolor=NAPIS):
    return G.material_emisja(nazwa, kolor)


k13 = kolo_zebate("Kolo13", 13, R13)
k20 = kolo_zebate("Kolo20", 20, R20, przes_kata=math.pi / 20)
# koło Haab': tylko pierścień (ze środka daleko poza kadrem)
k365 = kolo_zebate("Kolo365", 365, R365, r_wew=R365 - 0.50, grub=0.07)
mk = material_kamien("Kamien")
for k in (k13, k20, k365):
    k.data.materials.append(mk)
k13.location, k20.location, k365.location = C13, C20, C365

# piasty i ozdobne okręgi
def pierscien(nazwa, r0, r1, rodzic, z, kolor, n=128):
    v, f = [], []
    for j in range(n):
        a = 2 * math.pi * j / n
        v += [(r0 * math.cos(a), r0 * math.sin(a), 0), (r1 * math.cos(a), r1 * math.sin(a), 0)]
        q = 2 * j
        f.append((q, (q + 2) % (2 * n), (q + 3) % (2 * n), q + 1))
    ob = bpy.data.objects.new(nazwa, bpy.data.meshes.new(nazwa))
    ob.data.from_pydata(v, [], f)
    sc.collection.objects.link(ob)
    ob.parent = rodzic
    ob.location = (0, 0, z)
    m = G.material_emisja(nazwa + "_m", kolor)
    ob.data.materials.append(m)
    return ob


pierscien("Ozd13", R13 - 0.30, R13 - 0.285, k13, 0.002, NAPIS)
pierscien("Ozd20", R20 - 0.36, R20 - 0.345, k20, 0.002, NAPIS)
pierscien("Ozd20b", 0.20, 0.215, k20, 0.002, NAPIS)
pierscien("Ozd13b", 0.12, 0.135, k13, 0.002, NAPIS)
for k, rr in ((k13, 0.07), (k20, 0.09)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=rr, depth=0.05, location=(0, 0, 0.02))
    p = bpy.context.active_object
    p.parent = k
    p.data.materials.append(G.material_emisja("Piasta", (120, 92, 60)))


# ---------------------------------------------------------------- cyfry Majów (kropka = 1, kreska = 5, muszla = 0)
def cyfra_maja(nazwa, n, s, kolor, rodzic=None):
    """Obiekt z cyfrą Majów n (0..19), wysokość ok. s; oś Y = „do góry” cyfry."""
    v, f = [], []

    def prost(cx, cy, w, h):
        b = len(v)
        v.extend([(cx - w / 2, cy - h / 2, 0), (cx + w / 2, cy - h / 2, 0), (cx + w / 2, cy + h / 2, 0), (cx - w / 2, cy + h / 2, 0)])
        f.append((b, b + 1, b + 2, b + 3))

    def kolo(cx, cy, r, m=14):
        b = len(v)
        v.append((cx, cy, 0))
        for j in range(m):
            a = 2 * math.pi * j / m
            v.append((cx + r * math.cos(a), cy + r * math.sin(a), 0))
        for j in range(m):
            f.append((b, b + 1 + j, b + 1 + (j + 1) % m))

    def elipsa_pier(cx, cy, a, b_, t, m=28, a0=0.0, a1=2 * math.pi):
        b = len(v)
        for j in range(m + 1):
            al = a0 + (a1 - a0) * j / m
            v.append((cx + a * math.cos(al), cy + b_ * math.sin(al), 0))
            v.append((cx + (a - t) * math.cos(al), cy + (b_ - t) * math.sin(al), 0))
        for j in range(m):
            q = b + 2 * j
            f.append((q, q + 2, q + 3, q + 1))

    if n == 0:
        # uproszczona muszla: owal z dwiema wewnętrznymi liniami
        elipsa_pier(0, 0, 0.62 * s, 0.36 * s, 0.07 * s)
        elipsa_pier(0, -0.05 * s, 0.40 * s, 0.17 * s, 0.05 * s, m=16, a0=0.15, a1=math.pi - 0.15)
        elipsa_pier(0, -0.16 * s, 0.30 * s, 0.10 * s, 0.05 * s, m=12, a0=0.2, a1=math.pi - 0.2)
    else:
        kreski, kropki = n // 5, n % 5
        hb, gap = 0.16 * s, 0.07 * s
        wys = kreski * hb + max(0, kreski - 1) * gap + (0.2 * s + gap if kropki else 0)
        y = -wys / 2
        for _ in range(kreski):
            prost(0, y + hb / 2, 0.9 * s, hb)
            y += hb + gap
        if kropki:
            r = 0.09 * s
            for j in range(kropki):
                prost_x = (j - (kropki - 1) / 2) * 0.24 * s
                kolo(prost_x, y + r, r)
    me = bpy.data.meshes.new(nazwa)
    me.from_pydata(v, [], f)
    ob = bpy.data.objects.new(nazwa, me)
    sc.collection.objects.link(ob)
    if rodzic:
        ob.parent = rodzic
    m = G.material_emisja(nazwa + "_m", kolor) if isinstance(kolor, tuple) else kolor
    me.materials.append(m)
    return ob


def na_kole(ob, rodzic, kat, r, z=0.003, obrot_tekstu=-math.pi / 2):
    """umieść obiekt na kole: na kącie kat, promieniu r, „góra” obiektu na zewnątrz koła"""
    ob.parent = rodzic
    ob.location = (r * math.cos(kat), r * math.sin(kat), z)
    ob.rotation_euler = (0, 0, kat - math.pi / 2)


mt = mat_tekst("Napis_kola")
# koło 13: liczby 1..13 na zębach (ząb i = liczba i+1, na kącie i·2π/13)
for i in range(13):
    c = cyfra_maja(f"L13_{i+1}", i + 1, 0.15, mt)
    na_kole(c, k13, i * 2 * math.pi / 13, R13 - 0.13)
# koło 20: nazwy dni w przerwach między zębami, zgodnie z ruchem wskazówek zegara (nazwa j na kącie -j·2π/20)
for j, nazwa in enumerate(DNI):
    t = G.napis(nazwa, 0.085, NAPIS, "georgiab", "CENTER", nazwa=f"D20_{j}")
    t.data.materials.clear()
    t.data.materials.append(mt)
    na_kole(t, k20, -j * 2 * math.pi / 20, R20 - 0.17)
# koło 365: numery dni (0..19, Wayeb' 0..4) na zębach i nazwy miesięcy – tylko te, które pojawią się w kadrze
for kpos in range(HAAB0 + D_START - 14, HAAB0 + 16):
    kk = kpos % 365
    mies, dzien = divmod(kk, 20)
    kat = kk * 2 * math.pi / 365
    t = G.napis(str(dzien), 0.085, NAPIS, "arialb", "CENTER", nazwa=f"H_{kk}")
    t.data.materials.clear()
    t.data.materials.append(mt)
    na_kole(t, k365, kat, R365 - 0.115)
    if dzien in (1, 6, 11, 16) or (mies == 18 and dzien == 2):
        tm = G.napis(MIESIACE[mies], 0.095, NAPIS, "georgiab", "CENTER", nazwa=f"M_{mies}_{dzien}")
        tm.data.materials.clear()
        tm.data.materials.append(mt)
        kat_m = (kk + 0.5) * 2 * math.pi / 365
        na_kole(tm, k365, kat_m, R365 - 0.33)
        tm.rotation_euler = (0, 0, kat_m)   # nazwa miesiąca wzdłuż pierścienia
    if dzien == 0 and kpos != HAAB0 + D_START - 14:
        # kreska oddzielająca miesiące
        kr = bpy.data.objects.new(f"Gr_{kk}", bpy.data.meshes.new(f"Gr_{kk}"))
        kr.data.from_pydata([(-0.007, -0.30, 0), (0.007, -0.30, 0), (0.007, 0.0, 0), (-0.007, 0.0, 0)], [], [(0, 1, 2, 3)])
        sc.collection.objects.link(kr)
        kr.data.materials.append(mt)
        na_kole(kr, k365, (kk - 0.5) * 2 * math.pi / 365, R365 - 0.2)


# ---------------------------------------------------------------- obrót kół (dzień po dniu)
def dni(f):
    """liczba dni od 13.0.0.0.0 (ujemna), z „tyknięciem” przy każdym dniu"""
    s = G.gladko((f - F_RUCH0) / (F_RUCH1 - F_RUCH0))
    s = 0.5 * s + 0.5 * G.gladko5((f - F_RUCH0) / (F_RUCH1 - F_RUCH0))
    dc = D_START * (1 - s)
    n = math.floor(dc)
    fr = dc - n
    # przy szybkim ruchu tyknięcia zlewają się w płynny obrót
    tyk = G.gladko5(min(1.0, fr * 1.6))
    return n + tyk


def katy(d):
    t13 = -(LICZBA0 - 1 + d) * 2 * math.pi / 13
    t20 = math.pi + (DZIEN0 + d) * 2 * math.pi / 20
    t365 = math.pi - (HAAB0 + d) * 2 * math.pi / 365
    return t13, t20, t365


for f in range(1, KLATKI + 1):
    d = dni(f)
    a, b, c = katy(d)
    for ob, kat in ((k13, a), (k20, b), (k365, c)):
        ob.rotation_euler = (0, 0, kat)
        ob.keyframe_insert("rotation_euler", index=2, frame=f)
for ob in (k13, k20, k365):
    for fc in G._fcurves(ob.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

# znaczniki: złote trójkąty przy zazębieniach (miejsca odczytu)
def trojkat(nazwa, poz, kat, s=0.11):
    v = [(0, 0, 0), (-s * 0.6, s, 0), (s * 0.6, s, 0)]
    ob = bpy.data.objects.new(nazwa, bpy.data.meshes.new(nazwa))
    ob.data.from_pydata(v, [], [(0, 1, 2)])
    sc.collection.objects.link(ob)
    ob.location = poz
    ob.rotation_euler = (0, 0, kat)
    ob.data.materials.append(G.material_emisja(nazwa + "_m", ZLOTY))
    return ob


Z = 0.09
trojkat("Znacznik_Tzolkin", (C20.x - R20, C20.y + R13 * 0.25 + 0.16, Z), math.pi)
trojkat("Znacznik_Haab", (C20.x + R20, C20.y + 0.30, Z), math.pi)

# ---------------------------------------------------------------- kamera i napisy
cam = G.kamera((0, 0, 10), (0, 0, 0), lens=60)
CEL = Vector((0.42, -0.2, 0))


def kam(f):
    s = f / KLATKI
    pochyl = math.radians(13 - 5 * s)
    obr = math.radians(-4 + 6 * s)
    odl = 11.2 - 0.6 * G.gladko5(s)
    kier = Vector((math.sin(pochyl) * math.sin(obr), -math.sin(pochyl) * math.cos(obr), math.cos(pochyl)))
    return CEL + kier * odl


for f in list(range(1, KLATKI + 1, 50)) + [KLATKI]:
    cam.location = kam(f)
    G.patrz(cam, CEL)
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
G.wygladz(cam)
G.tlo_kamery(cam, odl=30)

ODL_N = 2.0
pxu = G.skala_px(cam, ODL_N)


def tekst_ekranu(nazwa, tekst, x, y, rozm, kolor, kroj="arialb", wyr="CENTER", klucze=None):
    ob = G.napis(tekst, rozm * 1.4 * pxu, kolor, kroj, wyr, rodzic=cam, loc=G.ekran_na_kamerze(cam, x, y, ODL_N),
                 nazwa=nazwa, odstep=1.1)
    if klucze:
        G.alfa_napisu(ob, klucze)
    return ob


# odczyt kół i licznik Długiej Rachuby (prawa strona kadru)
XP = 1600
tekst_ekranu("Tyt_tzolkin", "Tzolk'in", XP - 130, 150, 24, (200, 210, 230), "arial")
tekst_ekranu("Tyt_haab", "Haab'", XP + 140, 150, 24, (200, 210, 230), "arial")
od_tz = tekst_ekranu("Odczyt_tzolkin", "4 Ajaw", XP - 130, 205, 46, (255, 255, 255))
od_hb = tekst_ekranu("Odczyt_haab", "3 K'ank'in", XP + 140, 205, 46, (255, 255, 255))
tekst_ekranu("Tyt_lc", "Długa Rachuba", XP, 300, 24, (200, 210, 230), "arial")
od_lc = tekst_ekranu("Odczyt_lc", "13.0.0.0.0", XP, 365, 62, ZLOTY)


def dlugia_rachuba(dd):
    # 13.0.0.0.0 + dd dni (dd <= 0)
    tot = 13 * 144000 + dd
    b, r = divmod(tot, 144000)
    k, r = divmod(r, 7200)
    t, r = divmod(r, 360)
    w, i = divmod(r, 20)
    return f"{b}.{k}.{t}.{w}.{i}"


def odczyt(scena, *a):
    dd = int(round(dni(scena.frame_current)))
    lic = (LICZBA0 - 1 + dd) % 13 + 1
    dz = (DZIEN0 + dd) % 20
    hb = (HAAB0 + dd) % 365
    m, dn = divmod(hb, 20)
    od_tz.data.body = f"{lic} {DNI[dz]}"
    od_hb.data.body = f"{dn} {MIESIACE[m]}"
    od_lc.data.body = dlugia_rachuba(dd)


bpy.app.handlers.frame_change_pre.append(odczyt)

# finał: data zapisana cyframi Majów (13.0.0.0.0) i odpowiednik w naszym kalendarzu
F_FIN = 365
kl_fin = [(1, 0.0), (F_FIN, 0.0), (F_FIN + 20, 1.0)]
mz = G.material_emisja("Cyfry_fin", ZLOTY)
G.animuj_alfa(mz, kl_fin)
POZ = ["b'ak'tun", "k'atun", "tun", "winal", "k'in"]
for i, (n, nazwa) in enumerate(zip((13, 0, 0, 0, 0), POZ)):
    x = XP - 240 + i * 120
    loc = G.ekran_na_kamerze(cam, x, 480, ODL_N)
    c = cyfra_maja(f"Fin_{i}", n, 84 * pxu, mz, rodzic=cam)
    c.location = loc
    tekst_ekranu(f"Fin_et_{i}", nazwa, x, 556, 21, (200, 210, 230), "arial", klucze=kl_fin)
tekst_ekranu("Fin_data", "21–23 grudnia 2012", XP, 650, 40, (255, 255, 255), klucze=[(1, 0.0), (F_FIN + 25, 0.0), (F_FIN + 45, 1.0)])
tekst_ekranu("Fin_uwaga", "zależnie od przyjętego przelicznika", XP, 704, 23, (200, 210, 230), "arial",
             klucze=[(1, 0.0), (F_FIN + 25, 0.0), (F_FIN + 45, 1.0)])

G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
