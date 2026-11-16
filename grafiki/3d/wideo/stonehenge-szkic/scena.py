# -*- coding: utf-8 -*-
"""Klip „stonehenge-szkic”: ożywiony szkic Leszka Klimka „Naui Ollin i Stonehenge” (ollinstone.jpg).

Rysunek z rozdziału 12. Wszystkie elementy i położenia odczytane z pikseli rysunku (350×308 px):
zielone wały i kręgi (pod spodem wypukłe jak prawdziwe obwałowania), jasna figura w środku z kamieniami,
punkty A–F w czerwonych przerywanych okręgach, żółte linie od obserwatora w środku do gwiazd i planet
(Wega, Alamak, Spica, Jowisz, Wenus), niebieski pas Zodiaku ze znakami (Byk, Bliźnięta, Rak, Lew, Panna,
Waga), strzałka „Pn” i znak Ollin w lewym dolnym rogu. Kolejność pojawiania się jak w tekście:
A, C, E (wyróżnione obwałowaniem) -> D, F (na kręgu jam Aubreya) -> linia obserwator–B–A -> pozostałe linie.

Uruchomienie (z katalogu repozytorium):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/stonehenge-szkic/scena.py
  ... -- --proba 60,180,300,500
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G

OPCJE = G.argumenty()
KLATKI = 500  # 20 s
RYS = os.path.join(G.RYSUNKI, "ollinstone.jpg")
G.FONTY["sym"] = "seguisym.ttf"   # znaki Zodiaku (Segoe UI Symbol)

# ---------------------------------------------------------------- układ rysunku
RW, RH = 350, 308
U = 0.01                       # 1 px rysunku = 0,01 jednostki sceny
OX, OY = 175.0, 154.0          # środek tablicy


def P(x, y, z=0.0):
    return Vector(((x - OX) * U, -(y - OY) * U, z))


SRODEK = (176.0, 133.5)        # obserwator (przecięcie linii = środek pasa Zodiaku)
PUNKTY = {  # środek okręgu, promień okręgu (px), położenie litery (px)
    "A": ((275.0, 54.0), 12.0, (292.0, 49.0)),
    "B": ((233.0, 90.0), 6.5, (230.0, 77.0)),
    "C": ((158.0, 70.0), 12.0, (153.0, 52.0)),
    "D": ((117.0, 100.0), 6.5, (129.0, 96.0)),
    "E": ((194.0, 195.0), 12.0, (205.0, 211.0)),
    "F": ((237.0, 164.0), 6.5, (233.0, 151.0)),
}
GWIAZDY = {  # gwiazda (px), etykieta (środek px)
    "Wega": ((300.5, 35.2), (275.5, 24.3)),
    "Alamak": ((145.4, 22.6), (117.7, 32.3)),
    "Jowisz": ((75.4, 79.6), (55.8, 66.7)),
    "Wenus": ((278.3, 184.5), (297.1, 198.2)),
    "Spica": ((206.1, 239.6), (184.3, 252.2)),
}
# żółte linie z rysunku: (początek, koniec)
LINIE = {
    "AB": ((300.5, 35.2), (146.0, 156.0)),     # Wega – A – B – obserwator (i dalej)
    "CE": ((145.4, 22.6), (204.5, 229.0)),     # Alamak – C – obserwator – E – w stronę Spiki
    "DF": ((75.4, 79.6), (278.3, 184.5)),      # Jowisz – D – obserwator – F – Wenus
}
ZODIAK_R = (123.0, 149.0)       # pas Zodiaku: promienie (px) wokół SRODEK
ZODIAK_KATY = (134.0, 335.0)    # od lewej góry przez dół do prawej (stopnie, przeciwnie do zegara od osi X)
ZNAKI = [("♉", (47, 98)), ("♊", (47, 167)), ("♋", (77, 230)), ("♌", (140, 263)), ("♍", (220, 263)), ("♎", (283, 230))]
NAZWY_ZNAKOW = [("LEW", (135, 290)), ("PANNA", (227, 285)), ("WAGA", (307, 242))]

# kolory próbkowane z rysunku (sRGB)
TLO = (180, 220, 124)
ZIELEN = (14, 140, 62)
BLADY = (196, 226, 160)
NIEBIESKI = (112, 200, 240)
ZOLTY = (255, 236, 0)
CZERWONY = (232, 30, 30)
SZARY = (139, 130, 152)
CZARNY = (16, 16, 16)


# ---------------------------------------------------------------- maski z rysunku
def powieksz(a, f):
    """dwuliniowe powiększenie f razy (numpy)"""
    h, w = a.shape
    ys = (np.arange(h * f) + 0.5) / f - 0.5
    xs = (np.arange(w * f) + 0.5) / f - 0.5
    y0 = np.clip(np.floor(ys).astype(int), 0, h - 1); y1 = np.clip(y0 + 1, 0, h - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, w - 1); x1 = np.clip(x0 + 1, 0, w - 1)
    fy = np.clip(ys - y0, 0, 1)[:, None]; fx = np.clip(xs - x0, 0, 1)[None, :]
    return (a[y0][:, x0] * (1 - fy) * (1 - fx) + a[y0][:, x1] * (1 - fy) * fx
            + a[y1][:, x0] * fy * (1 - fx) + a[y1][:, x1] * fy * fx)


def prog(a, lo, hi):
    return np.clip((a - lo) / (hi - lo), 0, 1)


def maski():
    cp = os.path.join(G.CACHE, "stonehenge_maski_v2.npz")
    if os.path.exists(cp):
        z = np.load(cp)
        return z["wal"], z["wys"], z["blady"], z["czarny"], z["ollin"]
    d = G.obraz_numpy(RYS)[..., :3] * 255
    r, g, b = d[..., 0], d[..., 1], d[..., 2]
    H, W = r.shape
    yy, xx = np.mgrid[0:H, 0:W]
    # zielone wały: ciemna zieleń; bez okienek liter i znaku Ollin
    ziel = ((g > 95) & (r < 70) & (b < 120) & (g - r > 50)).astype(np.float32)
    # czerwone przerywane okręgi zasłaniają wał – uzupełnij tam, gdzie wokół jest zieleń
    czerw = (r > 170) & (g < 110) & (b < 110)
    zr = G.rozmyj(ziel, 2)
    ziel = np.maximum(ziel, (czerw & (zr > 0.18)).astype(np.float32))
    # żółte linie przecinają wały – też uzupełnij
    zolte = (r > 200) & (g > 190) & (b < 120)
    ziel = np.maximum(ziel, (zolte & (G.rozmyj(ziel, 1) > 0.3) & (np.hypot(xx - SRODEK[0], yy - SRODEK[1]) > 60)).astype(np.float32))
    ciemne = (r < 70) & (g < 70) & (b < 70)
    srodek = np.hypot(xx - SRODEK[0], yy - SRODEK[1])
    # jasna figura w środku (dawny plan kamieni) – jasna, bladozielona
    blady = (((r > 175) & (g > 205) & (b > 138) & (b - r > -45) & ((b > 145) | (g > 232))) & (srodek < 62)).astype(np.float32)
    blady = np.maximum(blady, ((ciemne | zolte) & (srodek < 50)).astype(np.float32) * (G.rozmyj(blady, 2) > 0.3))
    czarny = (ciemne & (srodek < 50)).astype(np.float32)
    # kropki w środkach okręgów C, E, A, B, D, F (czarne)
    for (cx, cy), rr, _ in PUNKTY.values():
        m = ciemne & (np.hypot(xx - cx, yy - cy) < rr * 0.7)
        czarny = np.maximum(czarny, m.astype(np.float32))
    ollin = (((r + g + b) / 3 < 95) & (xx < 125) & (yy > 215)).astype(np.float32)
    F = 4
    zw = powieksz(G.rozmyj(ziel, 1), F)
    wal = prog(zw, 0.30, 0.55)
    wys = G.rozmyj(wal, 3) * 0.6 + G.rozmyj(wal, 7) * 0.4
    bl = prog(G.rozmyj(powieksz(G.rozmyj(blady, 1), F), 3), 0.42, 0.58)
    cz = prog(powieksz(czarny, F), 0.30, 0.55)
    ol = prog(powieksz(ollin, F), 0.22, 0.5)
    np.savez_compressed(cp, wal=wal.astype(np.float32), wys=wys.astype(np.float32), blady=bl.astype(np.float32),
                        czarny=cz.astype(np.float32), ollin=ol.astype(np.float32))
    return wal, wys, bl, cz, ol


def obraz_rgba(nazwa, rgba):
    h, w = rgba.shape[:2]
    im = bpy.data.images.new(nazwa, w, h, alpha=True, float_buffer=False)
    im.colorspace_settings.name = "sRGB"
    im.pixels.foreach_set(np.ascontiguousarray(rgba[::-1].astype(np.float32)).ravel())
    im.pack()
    return im


# ---------------------------------------------------------------- scena
sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))
wal, wys, blady, czarny, ollin = maski()
HH, WW = wal.shape

# --- tablica z wałami (siatka z wysokością z maski)
NX, NY = 700, 616
jj, ii = np.mgrid[0:NY, 0:NX]
sy = (jj + 0.5) / NY * HH
sx = (ii + 0.5) / NX * WW
hz = wys[np.clip(sy.astype(int), 0, HH - 1), np.clip(sx.astype(int), 0, WW - 1)]
X = (ii / (NX - 1) * RW - OX) * U
Y = -(jj / (NY - 1) * RH - OY) * U
WYS_WALU = 0.055
me = bpy.data.meshes.new("Tablica")
verts = np.stack([X, Y, np.zeros_like(X)], -1).reshape(-1, 3)
faces = []
idx = np.arange(NX * NY).reshape(NY, NX)
a = idx[:-1, :-1].ravel(); b = idx[:-1, 1:].ravel(); c = idx[1:, 1:].ravel(); d_ = idx[1:, :-1].ravel()
me.vertices.add(len(verts))
me.vertices.foreach_set("co", verts.ravel())
nf = len(a)
me.loops.add(nf * 4)
me.loops.foreach_set("vertex_index", np.stack([a, d_, c, b], -1).ravel())
me.polygons.add(nf)
me.polygons.foreach_set("loop_start", np.arange(nf) * 4)
me.update()
uvl = me.uv_layers.new(name="UV")
vi = np.empty(nf * 4, np.int64); me.loops.foreach_get("vertex_index", vi)
uvx = (vi % NX) / (NX - 1); uvy = 1 - (vi // NX) / (NY - 1)
uvl.data.foreach_set("uv", np.stack([uvx, uvy], -1).ravel())
me.polygons.foreach_set("use_smooth", np.ones(nf, bool))
tab = bpy.data.objects.new("Tablica", me)
sc.collection.objects.link(tab)
# kształt „płaski” i „z wałami”
tab.shape_key_add(name="plaski")
sk = tab.shape_key_add(name="waly")
co = verts.copy(); co[:, 2] = hz.ravel() * WYS_WALU
sk.data.foreach_set("co", co.ravel())
sk.value = 0.0
sk.keyframe_insert("value", frame=20)
sk.value = 1.0
sk.keyframe_insert("value", frame=85)
G.wygladz(tab.data.shape_keys)

# tekstura koloru tablicy: tło + zieleń wałów; cieniowanie rzeźby wałów wyliczone z mapy wysokości
kol = np.zeros((HH, WW, 4), np.float32)
for k in range(3):
    kol[..., k] = (TLO[k] * (1 - wal) + ZIELEN[k] * wal) / 255.0
kol[..., 3] = 1
img_tab = obraz_rgba("tablica_kolor", kol)
px_sc = RW * U / WW                                   # jednostki sceny na piksel maski
gy, gx = np.gradient(wys * WYS_WALU, px_sc)
nx_, ny_, nz_ = -gx, gy, np.ones_like(gx)             # oś y obrazu w dół -> y sceny w górę
nl = np.sqrt(nx_ ** 2 + ny_ ** 2 + 1)
L = np.array([-0.55, 0.65, 0.9]); L = L / np.linalg.norm(L)
cien = (nx_ * L[0] + ny_ * L[1] + nz_ * L[2]) / nl / L[2]
cien = np.clip(0.55 + 0.45 * cien, 0.45, 1.25)
cr = np.zeros((HH, WW, 4), np.float32)
cr[..., 0] = cr[..., 1] = cr[..., 2] = cien / 1.25
cr[..., 3] = 1
img_cien = obraz_rgba("tablica_cien", cr)
img_cien.colorspace_settings.name = "Non-Color"
mt = bpy.data.materials.new("Tablica")
mt.use_nodes = True
nt = mt.node_tree
nt.nodes.clear()
from wezly import Wezly, animuj_wartosc
Wt = Wezly(nt)
uvt = Wt.coord("UV")
ct, _ = Wt.obraz(img_tab, uvt)
cs = Wt.sep(Wt.obraz(img_cien, uvt)[0])[0]
rzezba = Wt.wartosc(0.0, "rzezba")
mnoz = Wt.add(1.0, Wt.mul(Wt.sub(Wt.mul(cs, 1.25), 1.0), rzezba))
Wt.emisja_wyjscie(Wt.vmath("MULTIPLY", ct, Wt.vec(mnoz, mnoz, mnoz)))
me.materials.append(mt)
animuj_wartosc(nt, "rzezba", [(20, 0.0), (85, 1.0)])

# brzeg tablicy (cienka płyta pod spodem)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.036))
plyta = bpy.context.active_object
plyta.name = "Plyta"
plyta.scale = (RW * U, RH * U, 0.06)
mpl = G.material_emisja("Plyta_mat", (120, 160, 80))
plyta.data.materials.append(mpl)



# ---------------------------------------------------------------- warstwy płaskie (nad tablicą)
def plaszczyzna(nazwa, rgba_or_img, z, alfa_klucze):
    img = rgba_or_img
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, z))
    p = bpy.context.active_object
    p.name = nazwa
    p.scale = (RW * U, RH * U, 1)
    m = bpy.data.materials.new(nazwa)
    m.use_nodes = True
    t = m.node_tree
    t.nodes.clear()
    o = t.nodes.new("ShaderNodeOutputMaterial")
    em = t.nodes.new("ShaderNodeEmission")
    tr = t.nodes.new("ShaderNodeBsdfTransparent")
    mx = t.nodes.new("ShaderNodeMixShader")
    tx = t.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.interpolation = "Linear"; tx.extension = "CLIP"
    mul = t.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    val = t.nodes.new("ShaderNodeValue"); val.name = "alfa"
    t.links.new(tx.outputs["Color"], em.inputs["Color"])
    t.links.new(tx.outputs["Alpha"], mul.inputs[0])
    t.links.new(val.outputs[0], mul.inputs[1])
    t.links.new(mul.outputs[0], mx.inputs[0])
    t.links.new(tr.outputs[0], mx.inputs[1])
    t.links.new(em.outputs[0], mx.inputs[2])
    t.links.new(mx.outputs[0], o.inputs[0])
    m.surface_render_method = "BLENDED"
    p.data.materials.append(m)
    for f, v in alfa_klucze:
        val.outputs[0].default_value = v
        val.outputs[0].keyframe_insert("default_value", frame=f)
    G.wygladz(t)
    return p


def warstwa(maska, kolor):
    rgba = np.zeros(maska.shape + (4,), np.float32)
    for k in range(3):
        rgba[..., k] = kolor[k] / 255.0
    rgba[..., 3] = maska
    return rgba


# jasna figura w środku i czarne kamienie
img_bl = obraz_rgba("blady", warstwa(blady, BLADY))
img_cz = obraz_rgba("czarny", warstwa(czarny, CZARNY))
img_ol = obraz_rgba("ollin", warstwa(ollin, CZARNY))
plaszczyzna("Figura", img_bl, 0.004, [(1, 0.0), (60, 0.0), (95, 0.95)])
plaszczyzna("Kamienie", img_cz, 0.006, [(1, 0.0), (75, 0.0), (105, 1.0)])
plaszczyzna("Ollin", img_ol, 0.004, [(1, 0.0), (405, 0.0), (445, 1.0)])

Z = 0.075  # wysokość warstwy rysunku nad wałami


def mat_alfa(nazwa, kolor, klucze):
    m = G.material_emisja(nazwa, kolor)
    G.animuj_alfa(m, klucze)
    return m


def obiekt(nazwa, verts, faces, m):
    mesh = bpy.data.meshes.new(nazwa)
    mesh.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new(nazwa, mesh)
    sc.collection.objects.link(ob)
    mesh.materials.append(m)
    return ob


def okrag_przerywany(nazwa, srodek, r_px, grub_px, kreski, m, z=Z):
    """czerwony przerywany okrąg (kreski z przerwami), obiekt ze środkiem w punkcie"""
    verts, faces = [], []
    r0, r1 = (r_px - grub_px / 2) * U, (r_px + grub_px / 2) * U
    for k in range(kreski):
        a0 = 2 * math.pi * k / kreski
        a1 = a0 + 2 * math.pi / kreski * 0.62
        n = 8
        base = len(verts)
        for s in range(n + 1):
            a = a0 + (a1 - a0) * s / n
            verts += [(r0 * math.cos(a), r0 * math.sin(a), 0), (r1 * math.cos(a), r1 * math.sin(a), 0)]
        for s in range(n):
            q = base + 2 * s
            faces.append((q, q + 1, q + 3, q + 2))
    ob = obiekt(nazwa, verts, faces, m)
    ob.location = P(*srodek, z)
    return ob


def pasek(nazwa, a_px, b_px, grub_px, m, z=Z):
    """odcinek od a do b; początek w a, rośnie przez skalę X"""
    A, B = P(*a_px, z), P(*b_px, z)
    d = B - A
    L = d.length
    h = grub_px * U / 2
    ob = obiekt(nazwa, [(0, -h, 0), (L, -h, 0), (L, h, 0), (0, h, 0)], [(0, 1, 2, 3)], m)
    ob.location = A
    ob.rotation_euler = (0, 0, math.atan2(d.y, d.x))
    return ob


def rosnij(ob, f0, f1):
    ob.scale = (0.0001, 1, 1)
    ob.keyframe_insert("scale", frame=f0)
    ob.scale = (1, 1, 1)
    ob.keyframe_insert("scale", frame=f1)
    G.wygladz(ob)


def pojaw(ob, f0, dl=14, skala0=0.4):
    s = ob.scale.copy()
    ob.scale = s * skala0
    ob.keyframe_insert("scale", frame=f0)
    ob.scale = s
    ob.keyframe_insert("scale", frame=f0 + dl)
    G.wygladz(ob)


def litera(nazwa, tekst, poz_px, rozm_px, kolor, f0, kroj="arialb", z=Z + 0.002):
    ob = G.napis(tekst, rozm_px * U, kolor, kroj, "CENTER", loc=P(*poz_px, z), nazwa=nazwa)
    G.alfa_napisu(ob, [(1, 0.0), (f0, 0.0), (f0 + 12, 1.0)])
    return ob


# --- punkty A–F (czerwone przerywane okręgi) w kolejności z tekstu
POJAWIENIE = {"A": 112, "C": 124, "E": 136, "D": 172, "F": 184, "B": 222}
for nazwa, ((cx, cy), rr, lit) in PUNKTY.items():
    f0 = POJAWIENIE[nazwa]
    m = mat_alfa("Okrag_" + nazwa, CZERWONY, [(1, 0.0), (f0, 0.0), (f0 + 10, 1.0)])
    ob = okrag_przerywany("Okrag_" + nazwa, (cx, cy), rr, 2.2 if rr > 10 else 2.0, 10 if rr > 10 else 6, m)
    pojaw(ob, f0, 16, 1.8)
    ob.rotation_euler = (0, 0, 0)
    ob.keyframe_insert("rotation_euler", frame=f0)
    ob.rotation_euler = (0, 0, math.radians(-40))
    ob.keyframe_insert("rotation_euler", frame=f0 + 60)
    litera("Lit_" + nazwa, nazwa, lit, 12, CZARNY, f0 + 4)

# --- żółte linie: Wega–A–B–obserwator, potem C–E i D–F
mz = lambda n, f0: mat_alfa(n, ZOLTY, [(1, 0.0), (f0, 0.0), (f0 + 4, 1.0)])
GR = 1.6
l1 = pasek("Linia_AB", LINIE["AB"][1], LINIE["AB"][0], GR, mz("Linia_AB", 236))   # od obserwatora do Wegi
rosnij(l1, 236, 296)
l2a = pasek("Linia_C", SRODEK, LINIE["CE"][0], GR, mz("Linia_C", 300))
l2b = pasek("Linia_E", SRODEK, LINIE["CE"][1], GR, mz("Linia_E", 300))
l3a = pasek("Linia_D", SRODEK, LINIE["DF"][0], GR, mz("Linia_D", 318))
l3b = pasek("Linia_F", SRODEK, LINIE["DF"][1], GR, mz("Linia_F", 318))
for ob, f0 in ((l2a, 300), (l2b, 300), (l3a, 318), (l3b, 318)):
    rosnij(ob, f0, f0 + 45)
# obserwator: mała złota kropka w środku
mo = mat_alfa("Obserwator", (255, 255, 255), [(1, 0.0), (226, 0.0), (236, 1.0)])
bpy.ops.mesh.primitive_circle_add(vertices=24, radius=2.4 * U, fill_type="TRIFAN", location=P(*SRODEK, Z + 0.001))
obs = bpy.context.active_object
obs.data.materials.append(mo)


# --- gwiazdy (białe) i żółte etykiety
def etykieta(nazwa, tekst, poz_px, f0):
    sz = len(tekst) * 6.3 + 10
    w, h = sz * U / 2, 6.0 * U
    bpy.ops.mesh.primitive_plane_add(size=1, location=P(*poz_px, Z + 0.003))
    tlo = bpy.context.active_object
    tlo.name = "Etykieta_" + nazwa
    tlo.scale = (w * 2, h * 2, 1)
    bpy.ops.object.transform_apply(scale=True)
    bv = tlo.modifiers.new("zaokr", "BEVEL")
    bv.affect = "VERTICES"
    bv.width = h * 0.55
    bv.segments = 6
    m = mat_alfa("Etykieta_" + nazwa, ZOLTY, [(1, 0.0), (f0, 0.0), (f0 + 12, 1.0)])
    tlo.data.materials.append(m)
    pojaw(tlo, f0, 14, 0.5)
    t = litera("Napis_" + nazwa, tekst, (poz_px[0], poz_px[1] + 0.5), 11.5, CZARNY, f0 + 3, z=Z + 0.005)
    return tlo, t


KONIEC_LINII = {"Wega": 290, "Alamak": 338, "Spica": 338, "Jowisz": 356, "Wenus": 356}
for nazwa, (gw, et) in GWIAZDY.items():
    f0 = KONIEC_LINII[nazwa]
    m = mat_alfa("Gwiazda_" + nazwa, (255, 255, 255), [(1, 0.0), (f0, 0.0), (f0 + 6, 1.0)])
    verts = []
    for k in range(16):
        a = math.pi * 2 * k / 16
        rr = (3.6 if k % 2 == 0 else 1.5) * U
        verts.append((rr * math.cos(a), rr * math.sin(a), 0))
    verts.append((0, 0, 0))
    faces = [(16, k, (k + 1) % 16) for k in range(16)]
    g = obiekt("Gwiazda_" + nazwa, verts, faces, m)
    g.location = P(*gw, Z + 0.004)
    pojaw(g, f0, 12, 2.2)
    etykieta(nazwa, nazwa, et, f0 + 6)

# --- strzałka Pn (szara)
mpn = mat_alfa("Pn", SZARY, [(1, 0.0), (10, 0.0), (35, 1.0)])
pasek("Pn_trzon", (285.0, 150.0), (285.0, 112.0), 2.2, mpn)
grot = obiekt("Pn_grot", [(-4.5 * U, 0, 0), (4.5 * U, 0, 0), (0, 10 * U, 0)], [(0, 1, 2)], mpn)
grot.location = P(285.0, 113.0, Z)
pn = G.napis("Pn", 11 * U, CZARNY, "arialb", "CENTER", loc=P(285.0, 98.0, Z), nazwa="Pn_napis")
G.alfa_napisu(pn, [(1, 0.0), (10, 0.0), (35, 1.0)])

# --- pas Zodiaku (niebieski łuk), odsłaniany kątem
F_Z0, F_Z1 = 372, 432
mzod = bpy.data.materials.new("Zodiak")
mzod.use_nodes = True
tz = mzod.node_tree
tz.nodes.clear()
from wezly import Wezly, animuj_wartosc
Wz = Wezly(tz)
oz = Wz.coord("Object")
xz, yz, _ = Wz.sep(oz)
kat = Wz.math("ARCTAN2", yz, xz)                                  # -pi..pi
kat = Wz.math("WRAP", kat, math.radians(ZODIAK_KATY[0]), math.radians(ZODIAK_KATY[0]) + 2 * math.pi)
post = Wz.wartosc(0.0, "postep")
granica = Wz.add(math.radians(ZODIAK_KATY[0]), Wz.mul(post, math.radians(ZODIAK_KATY[1] - ZODIAK_KATY[0] + 360) % (2 * math.pi) or 0))
alfa_z = Wz.sub(1.0, Wz.smooth(-0.04, 0.04, Wz.sub(kat, granica)))
alfa_z = Wz.mul(alfa_z, Wz.smooth(0.0, 0.03, post))
Wz.emisja_wyjscie(G.srgb(NIEBIESKI), alfa_z)
mzod.surface_render_method = "BLENDED"
verts, faces = [], []
a0, a1 = math.radians(ZODIAK_KATY[0]), math.radians(ZODIAK_KATY[1] + 360 if ZODIAK_KATY[1] < ZODIAK_KATY[0] else ZODIAK_KATY[1])
n = 160
for s in range(n + 1):
    a = a0 + (a1 - a0) * s / n
    verts += [(ZODIAK_R[0] * U * math.cos(a), ZODIAK_R[0] * U * math.sin(a), 0),
              (ZODIAK_R[1] * U * math.cos(a), ZODIAK_R[1] * U * math.sin(a), 0)]
for s in range(n):
    q = 2 * s
    faces.append((q, q + 1, q + 3, q + 2))
zod = obiekt("Zodiak", verts, faces, mzod)
zod.location = P(*SRODEK, Z - 0.012)
animuj_wartosc(tz, "postep", [(F_Z0, 0.0), (F_Z1, 1.0)])

for k, (znak, poz) in enumerate(ZNAKI):
    f0 = F_Z0 + 8 + k * 9
    ob = G.napis(znak, 16 * U, (15, 20, 40), "sym", "CENTER", loc=P(*poz, Z - 0.008), nazwa=f"Znak_{k}")
    ob.data.offset = 0.2 * U
    G.alfa_napisu(ob, [(1, 0.0), (f0, 0.0), (f0 + 12, 1.0)])
for k, (nazwa, poz) in enumerate(NAZWY_ZNAKOW):
    f0 = F_Z0 + 30 + k * 9
    ob = G.napis(nazwa, 8.5 * U, (255, 255, 255), "arialb", "CENTER", loc=P(*poz, Z - 0.008), nazwa=f"Nazwa_{nazwa}")
    G.alfa_napisu(ob, [(1, 0.0), (f0, 0.0), (f0 + 12, 1.0)])

# ---------------------------------------------------------------- kamera
# Tablica 3,5 × 3,08 jednostki; w kadrze zajmuje górne ~860 px (dół 200 px wolny na podpis).
cam = G.kamera((0, 0, 10), (0, 0, 0), lens=85)
CEL = Vector((0.0, -0.02, 0.0))


def kamera_w(f):
    # od widoku z góry (jak rysunek) do lekkiego ujęcia z ukosa i z powrotem do niemal pionu na końcu
    s = G.gladko5(f / 300.0)
    s2 = G.gladko5((f - 330) / 150.0)
    pochyl = math.radians(4 + 26 * s - 12 * s2)
    obrot = math.radians(-6 + 12 * G.gladko5(f / 500.0))
    odl = 18.4 - 1.2 * s + 0.8 * s2
    kier = Vector((math.sin(pochyl) * math.sin(obrot), -math.sin(pochyl) * math.cos(obrot), math.cos(pochyl)))
    return CEL + kier * odl


for f in list(range(1, KLATKI + 1, 25)) + [KLATKI]:
    cam.location = kamera_w(f)
    G.patrz(cam, CEL)
    cam.data.shift_y = -0.055
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
cam.data.shift_y = -0.055
G.wygladz(cam)
G.tlo_kamery(cam, odl=30)

G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
