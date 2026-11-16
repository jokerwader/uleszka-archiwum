# -*- coding: utf-8 -*-
"""Klip „tektonika-globus”: ożywiona mapa Leszka Klimka tektonika.gif.

Podpis Leszka pod mapą: „Przypuszczalne granice płyt tektonicznych pokrywające się z rejonami
sejsmicznymi i tzw. gorące plamy”. Na mapie: białe linie = granice płyt, czerwone punkty = gorące plamy,
pomarańczowe strzałki przy Grzbiecie Atlantyckim = rozszerzanie się Atlantyku od grzbietu na zachód
i wschód (tekst rozdziału 03).

Przebieg: płaska mapa w owalu (jak u Leszka) -> po kolei granice, punkty i strzałki -> mapa zwija się
w globus -> globus obraca się do Atlantyku. Położenia linii, punktów i strzałek odczytano z pikseli
rysunku (rzut Mollweidego dopasowany do lądów, południk środkowy 8°E) i przeniesiono na kulę.

Uruchomienie: S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/tektonika-globus/scena.py
              ... -- --proba 1,120,240,400
"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector, Matrix, Quaternion

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
from wezly import Wezly, animuj_wartosc

OPCJE = G.argumenty()
KLATKI = 400  # 16 s

# rzut rysunku (dopasowanie lądów Natural Earth do zieleni rysunku, IoU 0,83)
M_CX, M_CY, M_A, M_B, L0 = 298.0, 153.0, 289.0, 142.0, 8.0
# płaska mapa w scenie: półosie owalu (jednostki sceny); globus ma promień 1
FA, FB = 1.86, 0.93


def moll_theta(lat_rad):
    t = np.asarray(lat_rad, dtype=np.float64).copy()
    for _ in range(30):
        f = 2 * t + np.sin(2 * t) - np.pi * np.sin(lat_rad)
        t = t - f / (2 + 2 * np.cos(2 * t) + 1e-12)
    return t


def moll(lat, lon):
    """(lat, lon) stopnie -> (X, Y) w [-1,1] owalu (X w poziomie, Y w pionie)"""
    th = moll_theta(np.radians(lat))
    dl = (np.asarray(lon) - L0 + 180) % 360 - 180
    return np.radians(dl) / np.pi * np.cos(th), np.sin(th)


def moll_odwr(X, Y):
    th = np.arcsin(np.clip(Y, -1, 1))
    lat = np.degrees(np.arcsin(np.clip((2 * th + np.sin(2 * th)) / np.pi, -1, 1)))
    lon = L0 + np.degrees(np.pi * X / np.maximum(np.cos(th), 1e-6))
    return lat, (lon + 180) % 360 - 180


def rys_ll(px, py):
    return moll_odwr((px - M_CX) / M_A, (M_CY - py) / M_B)


def ll_rys(lat, lon):
    X, Y = moll(lat, lon)
    return M_CX + X * M_A, M_CY - Y * M_B


# ---------------------------------------------------------------- odczyt rysunku
def skladowe(mask):
    """spójne składowe (8-sąsiedztwo) – lista tablic (y, x)"""
    from collections import deque
    H, W = mask.shape
    seen = np.zeros_like(mask, bool)
    out = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        q = deque([(y0, x0)]); seen[y0, x0] = True; pts = []
        while q:
            y, x = q.popleft(); pts.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True; q.append((yy, xx))
        out.append(np.array(pts))
    return out


def scienianie(img):
    """szkieletyzacja Zhang–Suen (numpy)"""
    img = img.copy().astype(bool)
    while True:
        zm = False
        for krok in (0, 1):
            P = np.pad(img, 1).astype(np.int32)
            p2, p3, p4 = P[:-2, 1:-1], P[:-2, 2:], P[1:-1, 2:]
            p5, p6, p7 = P[2:, 2:], P[2:, 1:-1], P[2:, :-2]
            p8, p9 = P[1:-1, :-2], P[:-2, :-2]
            B = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            s = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
            A = sum(((s[i] == 0) & (s[i + 1] == 1)).astype(np.int32) for i in range(8))
            if krok == 0:
                c = (p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)
            else:
                c = (p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0)
            m = img & (B >= 2) & (B <= 6) & (A == 1) & c
            if m.any():
                img[m] = False; zm = True
        if not zm:
            return img


def odczytaj_rysunek():
    d = G.obraz_numpy(os.path.join(G.RYSUNKI, "tektonika.gif")) * 255
    r, g, b, a = d[..., 0], d[..., 1], d[..., 2], d[..., 3]
    H, W = r.shape
    yy, xx = np.mgrid[0:H, 0:W]
    wew = (((xx - M_CX) / (M_A - 3)) ** 2 + ((yy - M_CY) / (M_B - 3)) ** 2) < 1
    bialy = (r > 225) & (g > 225) & (b > 225) & (a > 0) & wew
    czerw = (r > 190) & (g < 90) & (b < 90) & wew
    pom = (r > 220) & (g > 80) & (g < 185) & (b < 90) & wew & ~czerw
    nieb = (b > 150) & (r < 60) & (g < 150) & wew
    kropki = []
    for k in skladowe(czerw):
        if len(k) < 12:
            continue
        cy, cx = k[:, 0].mean() + 0.5, k[:, 1].mean() + 0.5
        kropki.append(rys_ll(cx, cy))
    strzalki = []
    for k in skladowe(pom):
        if len(k) < 6:
            continue
        cy, cx = k[:, 0].mean() + 0.5, k[:, 1].mean() + 0.5
        dd = (k[:, 0] + 0.5 - cy) ** 2 + (k[:, 1] + 0.5 - cx) ** 2
        ty, tx = k[np.argmax(dd)] + 0.5
        strzalki.append((rys_ll(cx, cy), rys_ll(tx, ty)))
    # napisy (nazwy oceanów): grupy niebieskich pikseli
    napisy = []
    for k in skladowe(G.rozmyj(nieb.astype(np.float32), 3) > 0.05):
        if len(k) < 60:
            continue
        cy, cx = (k[:, 0].min() + k[:, 0].max() + 1) / 2, (k[:, 1].min() + k[:, 1].max() + 1) / 2
        napisy.append((cx, cy, k[:, 1].max() - k[:, 1].min()))
    szk = scienianie(bialy)
    return bialy, szk, kropki, strzalki, napisy


def pole_odleglosci(szk, S=4, R=10):
    """odległość (w pikselach rysunku) od szkieletu, na siatce S× gęstszej"""
    H, W = szk.shape
    gest = np.zeros((H * S, W * S), bool)
    ys, xs = np.nonzero(szk)
    pts = set(zip(ys.tolist(), xs.tolist()))
    for (y, x) in pts:
        for dy, dx in ((0, 1), (1, -1), (1, 0), (1, 1)):
            if (y + dy, x + dx) in pts:
                for t in np.linspace(0, 1, S * 2 + 1):
                    gest[int((y + dy * t + 0.5) * S), int((x + dx * t + 0.5) * S)] = True
        gest[int((y + 0.5) * S), int((x + 0.5) * S)] = True
    odl = np.full(gest.shape, 99.0, np.float32)
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            dd = math.hypot(dx, dy)
            if dd > R:
                continue
            sh = np.roll(np.roll(gest, dy, 0), dx, 1)
            odl = np.where(sh & (dd < odl), dd, odl)
    return odl / S


def tekstury():
    pliki = [os.path.join(G.CACHE, f"tekt_{n}.png") for n in ("baza", "linie", "znaki")]
    if all(os.path.exists(p) for p in pliki) and os.path.exists(os.path.join(G.CACHE, "tekt_dane.npy")):
        dane = np.load(os.path.join(G.CACHE, "tekt_dane.npy"), allow_pickle=True).item()
        return pliki, dane
    bialy, szk, kropki, strzalki, napisy = odczytaj_rysunek()
    print(f"[tekt] kropek {len(kropki)}, strzałek {len(strzalki)}, napisów {len(napisy)}, szkielet {szk.sum()} px")
    odl = pole_odleglosci(szk)
    S = 4
    Wt, Ht = 4096, 2048
    jj, ii = np.mgrid[0:Ht, 0:Wt]
    lon = (ii + 0.5) / Wt * 360 - 180
    lat = 90 - (jj + 0.5) / Ht * 180
    PX, PY = ll_rys(lat, lon)
    # wygładzenie schodków szkieletu i próbkowanie dwuliniowe
    odl = G.rozmyj(np.minimum(odl, 4.0), 3)
    fy = np.clip(PY * S - 0.5, 0, odl.shape[0] - 1.001)
    fx = np.clip(PX * S - 0.5, 0, odl.shape[1] - 1.001)
    y0, x0 = fy.astype(int), fx.astype(int)
    ty, tx = fy - y0, fx - x0
    dl = (odl[y0, x0] * (1 - tx) * (1 - ty) + odl[y0, x0 + 1] * tx * (1 - ty)
          + odl[y0 + 1, x0] * (1 - tx) * ty + odl[y0 + 1, x0 + 1] * tx * ty)
    wewn = (((PX - M_CX) / (M_A - 4)) ** 2 + ((PY - M_CY) / (M_B - 4)) ** 2) < 1
    lin = np.clip((1.15 - dl) / 0.45 + 0.5, 0, 1) * wewn
    # kolejność rysowania linii: od Atlantyku na boki (w poziomie mapy)
    kol = np.clip(np.abs(PX - 262) / 300, 0, 1)
    a = np.zeros((Ht, Wt, 4), np.float32)
    a[..., 0] = lin; a[..., 1] = kol; a[..., 3] = 1
    G.zapisz_png(a, pliki[1])
    # baza: ląd/morze w kolorach rysunku
    m = G.zmniejsz(G.maska_ladu(8192, "10m"), 2)
    b = np.zeros((Ht, Wt, 4), np.float32)
    for c in range(3):
        b[..., c] = (G.MORZE_TEKT[c] * (1 - m) + G.ZIELEN_TEKT[c] * m) / 255
    b[..., 3] = 1
    G.zapisz_png(b, pliki[0])
    # znaki: R = kropki (alfa), G = kolejność kropek, B = strzałki
    P = np.stack([np.cos(np.radians(lat)) * np.cos(np.radians(lon)), np.cos(np.radians(lat)) * np.sin(np.radians(lon)),
                  np.sin(np.radians(lat))], -1)
    z = np.zeros((Ht, Wt, 4), np.float32); z[..., 3] = 1
    kropki_s = sorted(kropki, key=lambda k: k[1])
    RK = 1.55  # promień kropki (stopnie)
    for n, (la, lo) in enumerate(kropki_s):
        c = np.array(G.ll2xyz(la, lo))
        ang = np.degrees(np.arccos(np.clip(P @ c, -1, 1)))
        al = np.clip((RK - ang) / 0.25 + 0.5, 0, 1)
        z[..., 0] = np.maximum(z[..., 0], al)
        z[..., 1] = np.where(al > 0.01, (n + 0.5) / len(kropki_s), z[..., 1])
    for (la, lo), (tla, tlo) in strzalki:
        c = G.ll2xyz(la, lo)
        az = math.radians(G.azymut(la, lo, tla, tlo))
        Nn = (Vector((0, 0, 1)) - c * c.z).normalized()
        Ee = Nn.cross(c).normalized()
        kier = (Nn * math.cos(az) + Ee * math.sin(az))
        bok = c.cross(kier).normalized()
        cn = np.array(c); kn = np.array(kier); bn = np.array(bok)
        dz = P @ cn
        u = (P @ kn) / np.maximum(dz, 1e-3)
        v = (P @ bn) / np.maximum(dz, 1e-3)
        Ls = math.radians(2.6)  # pół długości trójkąta
        Ws = math.radians(2.1)
        # trójkąt: grot w u=+Ls, podstawa w u=-Ls o szerokości ±Ws
        t = (u + Ls) / (2 * Ls)
        inside = (dz > 0.9) & (t >= 0) & (t <= 1) & (np.abs(v) <= Ws * (1 - t))
        z[..., 2] = np.maximum(z[..., 2], inside.astype(np.float32))
    z[..., 2] = G.rozmyj(z[..., 2], 1)
    G.zapisz_png(z, pliki[2])
    dane = {"napisy": [(rys_ll(cx, cy), w) for (cx, cy, w) in napisy], "kropki": kropki_s, "strzalki": strzalki}
    np.save(os.path.join(G.CACHE, "tekt_dane.npy"), dane, allow_pickle=True)
    return pliki, dane


# ---------------------------------------------------------------- scena
sc = G.nowa_scena(KLATKI, proba=bool(OPCJE["proba"]))
pliki, dane = tekstury()
img_baza = G.wczytaj_obraz(pliki[0])
img_lin = G.wczytaj_obraz(pliki[1], nieliniowy=False)
img_zn = G.wczytaj_obraz(pliki[2], nieliniowy=False)
print("[tekt] napisy:", dane["napisy"])


def pozycja_kuli(lat, lon):
    """kula: środek mapy (L0) zwrócony do kamery (-Y), biegun w +Z"""
    f, l = math.radians(lat), math.radians(lon - L0)
    return Vector((math.cos(f) * math.sin(l), -math.cos(f) * math.cos(l), math.sin(f)))


def pozycja_mapy(lat, lon):
    X, Y = moll(lat, lon)
    return Vector((float(X) * FA, -1.0, float(Y) * FB))


# siatka globusa/mapy: dł. geogr. od L0-180 do L0+180 (brzegi mapy = szew)
NLON, NLAT = 360, 180
me = bpy.data.meshes.new("Globus")
verts_f, verts_k, faces, uv = [], [], [], []
for j in range(NLAT + 1):
    lat = -90 + 180 * j / NLAT
    for i in range(NLON + 1):
        lon = L0 - 180 + 360 * i / NLON
        verts_f.append(pozycja_mapy(lat, lon))
        verts_k.append(pozycja_kuli(lat, lon))
for j in range(NLAT):
    for i in range(NLON):
        a = j * (NLON + 1) + i
        faces.append((a, a + 1, a + NLON + 2, a + NLON + 1))
me.from_pydata([tuple(v) for v in verts_f], [], faces)
uvl = me.uv_layers.new(name="UV")
luv = []
for f in me.polygons:
    for li in f.loop_indices:
        vi = me.loops[li].vertex_index
        j, i = divmod(vi, NLON + 1)
        lon = L0 - 180 + 360 * i / NLON
        luv.extend(((lon + 180) / 360, j / NLAT))
uvl.data.foreach_set("uv", luv)
for p in me.polygons:
    p.use_smooth = True
glob = bpy.data.objects.new("Globus", me)
sc.collection.objects.link(glob)
glob.shape_key_add(name="Mapa")
kk = glob.shape_key_add(name="Kula")
for i, v in enumerate(verts_k):
    kk.data[i].co = v
kk.value = 0.0

mat = bpy.data.materials.new("Globus")
nt = mat.node_tree if mat.node_tree else None
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
W = Wezly(nt)
uvc = W.coord("UV")
baza, _ = W.obraz(img_baza, uvc)
lin, _ = W.obraz(img_lin, uvc)
zn, _ = W.obraz(img_zn, uvc)
l_a, l_k, _ = W.sep(lin)
z_k, z_o, z_s = W.sep(zn)
p_lin = W.wartosc(-0.1, "postep_linii")
p_kr = W.wartosc(0.0, "postep_kropek")
a_st = W.wartosc(0.0, "alfa_strzalek")
odk_l = W.sub(1.0, W.smooth(-0.04, 0.04, W.sub(l_k, p_lin)))
kol = W.mix(W.mul(l_a, odk_l), baza, G.srgb((255, 255, 255)))
odk_k = W.sub(1.0, W.smooth(-0.002, 0.002, W.sub(z_o, p_kr)))
kol = W.mix(W.mul(z_k, odk_k), kol, G.srgb((228, 32, 36)))
kol = W.mix(W.mul(z_s, a_st), kol, G.srgb((244, 128, 44)))
# cieniowanie (płasko na mapie, kuliście na globusie)
nrm = W.geometria("Normal")
sw = W.dot(nrm, tuple(Vector((-0.45, -0.75, 0.5)).normalized()))
cien = W.add(0.78, W.mul(W.mx(sw, 0.0), 0.26))
kol = W.vmath("MULTIPLY", kol, W.vec(cien, cien, cien))
widok = W.geometria("Incoming")
fres = W.math("POWER", W.sub(1.0, W.math("ABSOLUTE", W.dot(nrm, widok))), 3.0)
kol = W.mix(W.mul(fres, 0.35), kol, G.srgb((190, 230, 255)))
alfa_glob = W.wartosc(0.0, "alfa_globusa")
W.emisja_wyjscie(kol, alfa_glob)
mat.surface_render_method = "BLENDED"
mat.use_backface_culling = True
me.materials.append(mat)

# szara obwódka owalu jak na rysunku (znika przy zwijaniu)
bpy.ops.mesh.primitive_circle_add(vertices=180, radius=1.0, fill_type="NOTHING")
ob_o = bpy.context.active_object
ob_o.name = "Obwodka"
ob_o.rotation_euler = (math.radians(90), 0, 0)
ob_o.location = (0, -0.995, 0)
ob_o.scale = (FA + 0.022, FB + 0.022, 1)
bm_o = ob_o.data
import bmesh
bm = bmesh.new(); bm.from_mesh(bm_o)
ext = bmesh.ops.extrude_edge_only(bm, edges=bm.edges[:])
for v in [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]:
    v.co.x *= (FA + 0.05) / (FA + 0.022)
    v.co.y *= (FB + 0.05) / (FB + 0.022)
bm.to_mesh(bm_o); bm.free()
m_o = G.material_emisja("Obwodka", (198, 194, 190), 0.0)
bm_o.materials.append(m_o)
G.animuj_alfa(m_o, [(1, 0.0), (18, 1.0), (190, 1.0), (215, 0.0)])

# nazwy oceanów (niebieskie, pogrubione) – na powierzchni mapy/globusa
napisy = []
for (la, lo), w in dane["napisy"]:
    nm = "PACYFIK"
    if 230 < ll_rys(la, lo)[0] < 300:
        nm = "ATLANTYK"
    elif 360 < ll_rys(la, lo)[0] < 450:
        nm = "INDYJSKI"
    ob = G.napis(nm, 0.085, G.GRANAT_TEKT, "arialb", "CENTER", nazwa="Ocean_" + nm)
    ob.parent = glob
    ob.rotation_mode = "QUATERNION"
    napisy.append((ob, la, lo))

# kamera
cam = G.kamera((0, -7.4, 0.0), (0, 0, 0), lens=50)
cam.data.shift_y = -0.035
G.tlo_kamery(cam, odl=40)


def k_zwijania(f):
    return G.gladko5((f - 190) / 105)


def obrot_globusa(f):
    t = G.gladko((f - 255) / 145)
    return Euler_zxy(math.radians(36) * t, math.radians(9) * t)


def Euler_zxy(spin, tilt):
    return (Matrix.Rotation(tilt, 4, "X") @ Matrix.Rotation(spin, 4, "Z"))


# klucze: kształt, obrót globusa, napisy (pozycja na zwijającej się powierzchni)
for f in range(1, KLATKI + 1):
    k = k_zwijania(f)
    kk.value = k
    kk.keyframe_insert("value", frame=f)
    glob.matrix_world = obrot_globusa(f)
    glob.keyframe_insert("rotation_euler", frame=f)
    for ob, la, lo in napisy:
        pf, pk = pozycja_mapy(la, lo), pozycja_kuli(la, lo)
        p = pf.lerp(pk, k)
        # styczny układ: na mapie (X w prawo, Z w górę, normalna -Y); na kuli wschód/północ/na zewnątrz
        nk = pk.normalized()
        ek = Vector((0, 0, 1)).cross(nk).normalized() if abs(nk.z) < 0.999 else Vector((1, 0, 0))
        ek = -ek if ek.x * math.cos(0) < -2 else ek
        northk = nk.cross(ek).normalized()
        e = Vector((1, 0, 0)).lerp(ek, k).normalized()
        nrm_ = Vector((0, -1, 0)).lerp(nk, k).normalized()
        up = nrm_.cross(e).normalized()
        e = up.cross(nrm_).normalized()
        R = Matrix((e, up, nrm_)).transposed().to_4x4()
        # tekst leży w płaszczyźnie XY obiektu, patrzy w +Z
        ob.matrix_basis = Matrix.Translation(p + nrm_ * 0.012) @ R
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_quaternion", frame=f)
        # napis gaśnie, gdy schodzi na brzeg kuli (płaski napis wystawałby poza obrys)
        Mw = obrot_globusa(f)
        pw = Mw @ (p + nrm_ * 0.012)
        nw = (Mw.to_3x3() @ nrm_).normalized()
        widz = (cam.location - pw).normalized()
        alfa = min(G.gladko((f - 1) / 17), G.gladko((nw.dot(widz) - 0.45) / 0.25))
        if ob.name.startswith("Ocean_PACYFIK"):
            # oba napisy PACYFIK leżą na brzegach mapy i przy zwijaniu wchodziłyby w kulę – gasną przed zwijaniem
            alfa = min(alfa, 1 - G.gladko((f - 182) / 14))
        G.ustaw_alfa(bpy.data.materials[ob["mat"]], alfa, f)

for ob in [glob] + [n[0] for n in napisy]:
    if ob.animation_data and ob.animation_data.action:
        for fc in G._fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
if me.shape_keys.animation_data:
    for fc in G._fcurves(me.shape_keys.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

animuj_wartosc(nt, "alfa_globusa", [(1, 0.0), (18, 1.0)])
animuj_wartosc(nt, "postep_linii", [(22, -0.06), (95, 1.06)])
animuj_wartosc(nt, "postep_kropek", [(100, 0.0), (160, 1.0)], interp="LINEAR")
animuj_wartosc(nt, "alfa_strzalek", [(160, 0.0), (180, 1.0)])

G.renderuj(TU, OPCJE, kadr_klatka=KLATKI)
