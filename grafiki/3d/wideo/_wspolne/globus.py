# -*- coding: utf-8 -*-
"""Wspólny kod klipów 3D „Wielki uskok” (globusy).

Import w scena.py:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_wspolne"))
    import globus as G

Zawiera:
  * wczytanie Natural Earth (GeoJSON, domena publiczna) i rasteryzację lądów do mapy
    równoodległościowej (numpy, bez dodatkowych bibliotek),
  * geometrię sfery (szer./dł. geograficzna -> współrzędne Blendera),
  * pomocnicze funkcje sceny: tło, kamera, napisy, materiały „emisyjne” (płaskie kolory jak na rysunkach),
  * render: klatki próbne, blokada .renderuje, składanie mp4 ffmpeg-iem, kadr.jpg.

Układ współrzędnych globusa (promień 1, środek w 0):
  z = biegun północny, x = południk 0° na równiku, y = 90°E na równiku.
"""
import bpy, bmesh, json, math, os, sys, time, subprocess, shutil
import numpy as np
from mathutils import Vector, Matrix, Quaternion

WIDEO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REPO = os.path.normpath(os.path.join(WIDEO, "..", "..", ".."))
DANE = os.path.join(WIDEO, "_dane")
NE = os.path.join(DANE, "natural-earth")
RYSUNKI = os.path.join(REPO, "zrodlo", "webacja", "02uskok")
CACHE = os.path.join(os.environ.get("TEMP", "/tmp"), "uskok3d_cache")
os.makedirs(CACHE, exist_ok=True)

FONT_DIR = r"C:\Windows\Fonts"
FONTY = {"georgia": "georgia.ttf", "georgiab": "georgiab.ttf", "arial": "arial.ttf", "arialb": "arialbd.ttf"}

# Kolory Leszka (próbkowane z jego rysunków, sRGB 0-255)
ZIELEN_USKOK = (2, 143, 67)       # uskok.jpg – lądy
MORZE_USKOK = (0, 162, 233)       # uskok.jpg – morze (środek jaśniejszy)
MORZE_USKOK_JASNE = (120, 205, 245)
ZIELEN_TEKT = (128, 195, 37)      # tektonika.gif – lądy
MORZE_TEKT = (117, 195, 243)      # tektonika.gif – morze
GRANAT_TEKT = (5, 120, 195)       # tektonika.gif – nazwy oceanów
ZLOTY = (240, 196, 111)           # akcent filmu #f0c46f
TLO_GORA = (27, 42, 77)           # #1b2a4d
TLO_DOL = (5, 7, 12)              # #05070c
ZOLTY_LESZKA = (245, 200, 30)     # żółte podpisy / strzałki z uskok.jpg


def srgb(c, a=1.0):
    """(r,g,b) 0-255 sRGB -> liniowe RGBA 0-1 (Blender przechowuje kolory liniowo)."""
    def lin(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (lin(c[0]), lin(c[1]), lin(c[2]), a)


# ---------------------------------------------------------------- geografia

def ll2xyz(lat, lon, r=1.0):
    la, lo = math.radians(lat), math.radians(lon)
    return Vector((r * math.cos(la) * math.cos(lo), r * math.cos(la) * math.sin(lo), r * math.sin(la)))


def xyz2ll(v):
    v = Vector(v).normalized()
    return math.degrees(math.asin(max(-1, min(1, v.z)))), math.degrees(math.atan2(v.y, v.x))


def odleglosc_katowa(lat1, lon1, lat2, lon2):
    a, b = ll2xyz(lat1, lon1), ll2xyz(lat2, lon2)
    return math.degrees(a.angle(b))


def azymut(lat1, lon1, lat2, lon2):
    """Azymut (stopnie od północy, zgodnie z ruchem wskazówek) z punktu 1 do punktu 2 po kole wielkim."""
    f1, f2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(f2)
    x = math.cos(f1) * math.sin(f2) - math.sin(f1) * math.cos(f2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def luk(lat1, lon1, lat2, lon2, n=64, r=1.0):
    """Punkty łuku koła wielkiego (lista Vector)."""
    a, b = ll2xyz(lat1, lon1), ll2xyz(lat2, lon2)
    om = a.angle(b)
    pts = []
    for i in range(n + 1):
        t = i / n
        if om < 1e-6:
            p = a
        else:
            p = (math.sin((1 - t) * om) * a + math.sin(t * om) * b) / math.sin(om)
        pts.append(p.normalized() * r)
    return pts


# ---------------------------------------------------------------- Natural Earth -> raster

def _pierscienie(geojson_path, filtr=None):
    with open(geojson_path, "r", encoding="utf-8") as f:
        d = json.load(f)
    rings = []
    for ft in d["features"]:
        if filtr and not filtr(ft["properties"]):
            continue
        g = ft["geometry"]
        if g is None:
            continue
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            for ring in poly:
                a = np.asarray(ring, dtype=np.float64)[:, :2]
                if len(a) >= 3:
                    rings.append(a)
    return rings


def rasteryzuj(rings, W, H, lon0=-180.0, lat0=90.0, dlon=360.0, dlat=180.0):
    """Wypełnia pierścienie (lon,lat) regułą parzysto-nieparzystą do tablicy H×W (uint8 0/1).
    Piksel (j,i) ma środek w lon = lon0 + (i+0.5)/W*dlon, lat = lat0 - (j+0.5)/H*dlat."""
    rows_all, xs_all = [], []
    for r in rings:
        fx = (r[:, 0] - lon0) / dlon * W - 0.5
        fy = (lat0 - r[:, 1]) / dlat * H - 0.5
        x0, y0 = fx, fy
        x1, y1 = np.roll(fx, -1), np.roll(fy, -1)
        ymin, ymax = np.minimum(y0, y1), np.maximum(y0, y1)
        j0 = np.ceil(ymin).astype(np.int64)
        j1 = np.ceil(ymax).astype(np.int64)  # rzędy j0..j1-1
        cnt = np.clip(j1 - j0, 0, None)
        m = cnt > 0
        if not m.any():
            continue
        x0, y0, x1, y1, j0, cnt = x0[m], y0[m], x1[m], y1[m], j0[m], cnt[m]
        idx = np.repeat(np.arange(len(cnt)), cnt)
        off = np.arange(cnt.sum()) - np.repeat(np.cumsum(cnt) - cnt, cnt)
        jj = j0[idx] + off
        t = (jj - y0[idx]) / (y1[idx] - y0[idx])
        xx = x0[idx] + t * (x1[idx] - x0[idx])
        rows_all.append(jj)
        xs_all.append(xx)
    out = np.zeros((H, W + 1), np.int32)
    if not rows_all:
        return out[:, :W].astype(np.uint8)
    jj = np.concatenate(rows_all)
    xx = np.concatenate(xs_all)
    ok = (jj >= 0) & (jj < H)
    jj, xx = jj[ok], xx[ok]
    order = np.lexsort((xx, jj))
    jj, xx = jj[order], xx[order]
    # pary w każdym rzędzie
    n = len(jj)
    # pozycja w rzędzie
    start = np.r_[0, np.nonzero(np.diff(jj))[0] + 1]
    rank = np.arange(n) - np.repeat(start, np.diff(np.r_[start, n]))
    a = rank % 2 == 0
    ia = np.nonzero(a)[0]
    ia = ia[ia + 1 < n]
    ia = ia[jj[ia] == jj[ia + 1]]
    s = np.clip(np.ceil(xx[ia]).astype(np.int64), 0, W)
    e = np.clip(np.ceil(xx[ia + 1]).astype(np.int64), 0, W)
    np.add.at(out, (jj[ia], s), 1)
    np.add.at(out, (jj[ia], e), -1)
    out = np.cumsum(out, axis=1)[:, :W]
    return (out > 0).astype(np.uint8)


def maska_ladu(W=8192, rozdz="10m", jeziora=True):
    """Maska lądu (H×W, float32 0/1), wiersz 0 = 90°N, kolumna 0 = 180°W. Cache w %TEMP%."""
    H = W // 2
    cp = os.path.join(CACHE, f"lad_{rozdz}_{W}_{int(jeziora)}.npy")
    if os.path.exists(cp):
        return np.load(cp)
    t = time.time()
    rings = _pierscienie(os.path.join(NE, f"ne_{rozdz}_land.geojson"))
    m = rasteryzuj(rings, W, H)
    if jeziora:
        lr = _pierscienie(os.path.join(NE, f"ne_{rozdz}_lakes.geojson"), lambda p: (p.get("scalerank") or 9) <= 3)
        m = m & (1 - rasteryzuj(lr, W, H))
    m = m.astype(np.float32)
    np.save(cp, m)
    print(f"[globus] maska lądu {W}x{H} w {time.time()-t:.1f} s")
    return m


def rozmyj(a, r=1):
    """Szybkie rozmycie pudełkowe (numpy), r w pikselach, zawijanie w poziomie."""
    out = a.astype(np.float32)
    for ax in (0, 1):
        acc = np.zeros_like(out)
        for k in range(-r, r + 1):
            if ax == 1:
                acc += np.roll(out, k, axis=1)
            else:
                acc += np.pad(out, ((r, r), (0, 0)), mode="edge")[r + k: r + k + out.shape[0]]
        out = acc / (2 * r + 1)
    return out


def zmniejsz(a, f):
    h, w = a.shape[:2]
    return a.reshape(h // f, f, w // f, f, *a.shape[2:]).mean(axis=(1, 3))


def zapisz_png(rgba, path, nazwa=None):
    """rgba: H×W×4 float 0-1 (sRGB, wiersz 0 = góra). Zapis PNG przez Blendera."""
    h, w = rgba.shape[:2]
    nazwa = nazwa or os.path.basename(path)
    im = bpy.data.images.new(nazwa, w, h, alpha=True)
    im.colorspace_settings.name = "sRGB"
    px = np.ascontiguousarray(rgba[::-1].astype(np.float32)).ravel()
    im.pixels.foreach_set(px)
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    return im


def wczytaj_obraz(path, nieliniowy=True):
    im = bpy.data.images.load(path, check_existing=True)
    if not nieliniowy:
        im.colorspace_settings.name = "Non-Color"
    return im


def obraz_numpy(path):
    """Wczytuje obraz (np. rysunek Leszka) jako H×W×4 float, wiersz 0 = góra, wartości sRGB."""
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(h, w, 4)[::-1].copy()


def tekstura_ziemi(W, kolor_lad, kolor_morze, nazwa, rozdz="10m", aa=True):
    """Płaska tekstura równoodległościowa (PNG w cache): lądy jednym kolorem, morze drugim."""
    path = os.path.join(CACHE, f"{nazwa}_{W}.png")
    if os.path.exists(path):
        return path
    m = maska_ladu(W * 2 if aa else W, rozdz)
    if aa:
        m = zmniejsz(m, 2)
    a = np.empty(m.shape + (4,), np.float32)
    for c in range(3):
        a[..., c] = (kolor_morze[c] * (1 - m) + kolor_lad[c] * m) / 255.0
    a[..., 3] = 1
    zapisz_png(a, path)
    return path


# ---------------------------------------------------------------- scena

def nowa_scena(klatki, fps=25, res=(1920, 1080), proba=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.fps = fps
    sc.frame_start, sc.frame_end = 1, klatki
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.film_transparent = False
    try:
        # sceny są płaskie (emisja), więc 12 próbek wystarcza na wygładzenie krawędzi
        sc.eevee.taa_render_samples = int(os.environ.get("USKOK3D_PROBKI", "16" if proba else "32"))
    except Exception:
        pass
    if os.environ.get("USKOK3D_SILNIK", "").upper() == "CYCLES":
        # zapas, gdy karta jest zajęta: Cycles na procesorze, same materiały emisyjne -> bez odbić
        sc.render.engine = "CYCLES"
        sc.cycles.device = "CPU"
        sc.cycles.samples = int(os.environ.get("USKOK3D_PROBKI", "12"))
        sc.cycles.use_adaptive_sampling = False
        sc.cycles.use_denoising = False
        sc.cycles.max_bounces = 0
        sc.cycles.transparent_max_bounces = 8
        sc.cycles.pixel_filter_type = "BLACKMAN_HARRIS"
        sc.render.use_persistent_data = os.environ.get("USKOK3D_PERSIST", "1") == "1"
    w = bpy.data.worlds.new("Swiat")
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = srgb(TLO_DOL)
    bg.inputs[1].default_value = 1.0
    sc.world = w
    return sc


def material_emisja(nazwa, kolor=None, alfa=1.0):
    """Materiał świecący płaskim kolorem (jak rysunek). Zwraca (mat, nodes, links, wyjście_emisji)."""
    m = bpy.data.materials.new(nazwa)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    if kolor is not None:
        em.inputs["Color"].default_value = srgb(kolor) if max(kolor) > 1.0 else (*kolor[:3], 1)
    em.inputs["Strength"].default_value = 1.0
    if alfa < 1.0 or True:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = alfa
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        m["mix"] = mix.name
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    try:
        m.blend_method = "BLEND"
    except Exception:
        pass
    return m


def ustaw_alfa(mat, wartosc, klatka=None):
    mix = mat.node_tree.nodes[mat["mix"]]
    mix.inputs[0].default_value = wartosc
    if klatka is not None:
        mix.inputs[0].keyframe_insert("default_value", frame=klatka)


def animuj_alfa(mat, klucze):
    """klucze: [(klatka, alfa), ...]"""
    for f, v in klucze:
        ustaw_alfa(mat, v, f)
    wygladz(mat.node_tree)


def wygladz(id_data, interp="BEZIER"):
    ad = getattr(id_data, "animation_data", None)
    if not ad or not ad.action:
        return
    for fc in _fcurves(ad.action):
        for k in fc.keyframe_points:
            k.interpolation = interp
            if interp == "BEZIER":
                k.easing = "AUTO"
                k.handle_left_type = k.handle_right_type = "AUTO_CLAMPED"


def _fcurves(action):
    if hasattr(action, "fcurves") and action.fcurves is not None:
        try:
            return list(action.fcurves)
        except Exception:
            pass
    res = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                res.extend(cb.fcurves)
    return res


def kamera(loc, cel, lens=50, orto=None):
    cd = bpy.data.cameras.new("Kamera")
    if orto:
        cd.type = "ORTHO"
        cd.ortho_scale = orto
    else:
        cd.lens = lens
    cd.clip_start, cd.clip_end = 0.01, 500
    ob = bpy.data.objects.new("Kamera", cd)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    ob.location = loc
    patrz(ob, cel)
    return ob


def patrz(ob, cel, gora=(0, 0, 1)):
    d = Vector(cel) - Vector(ob.location)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def tlo_kamery(cam, odl=60.0):
    """Płaszczyzna za sceną z promienistym gradientem granatu (#1b2a4d -> #05070c), przypięta do kamery."""
    sc = bpy.context.scene
    cd = cam.data
    ar = sc.render.resolution_x / sc.render.resolution_y
    if cd.type == "ORTHO":
        w = cd.ortho_scale * 1.05
    else:
        w = 2 * odl * math.tan(cd.angle / 2) * 1.05 * (1 if ar >= 1 else 1 / ar) * (36 / cd.sensor_width if False else 1)
        w = 2 * odl * (cd.sensor_width / 2) / cd.lens * 1.05
    bpy.ops.mesh.primitive_plane_add(size=1)
    p = bpy.context.active_object
    p.name = "Tlo"
    w *= 1.3  # zapas na przesunięcie obiektywu (shift)
    p.scale = (w, w / ar, 1)
    p.parent = cam
    p.location = (0, 0, -odl)
    p.rotation_euler = (0, 0, 0)
    m = bpy.data.materials.new("Tlo")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], sep.inputs[0])
    # odległość od punktu (0.5, 0.62) z poprawką proporcji
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "SUBTRACT"; m1.inputs[1].default_value = 0.5
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "SUBTRACT"; m2.inputs[1].default_value = 0.6
    m3 = nt.nodes.new("ShaderNodeMath"); m3.operation = "MULTIPLY"; m3.inputs[1].default_value = ar
    nt.links.new(sep.outputs[0], m1.inputs[0]); nt.links.new(m1.outputs[0], m3.inputs[0])
    nt.links.new(sep.outputs[1], m2.inputs[0])
    cx = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(m3.outputs[0], cx.inputs[0]); nt.links.new(m2.outputs[0], cx.inputs[1])
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    nt.links.new(cx.outputs[0], ln.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = srgb(TLO_GORA)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = srgb(TLO_DOL)
    nt.links.new(ln.outputs[1], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], out.inputs[0])
    p.data.materials.append(m)
    return p


_fonty = {}


def font(nazwa):
    if nazwa not in _fonty:
        _fonty[nazwa] = bpy.data.fonts.load(os.path.join(FONT_DIR, FONTY[nazwa]))
    return _fonty[nazwa]


def napis(tekst, rozmiar, kolor, krój="arialb", wyrownanie="CENTER", rodzic=None, loc=(0, 0, 0),
          rot=(0, 0, 0), nazwa="Napis", alfa=1.0, obrys=None, odstep=1.0):
    cu = bpy.data.curves.new(nazwa, "FONT")
    cu.body = tekst
    cu.font = font(krój)
    cu.size = rozmiar
    cu.align_x = wyrownanie
    cu.align_y = "CENTER"
    cu.space_line = odstep
    ob = bpy.data.objects.new(nazwa, cu)
    bpy.context.scene.collection.objects.link(ob)
    if rodzic:
        ob.parent = rodzic
    ob.location = loc
    ob.rotation_euler = rot
    m = material_emisja(nazwa + "_mat", kolor, alfa)
    cu.materials.append(m)
    if obrys:
        # cień/obrys: kopia tekstu lekko z tyłu, ciemna i pogrubiona
        cu2 = cu.copy()
        cu2.offset = obrys[1]
        ob2 = bpy.data.objects.new(nazwa + "_obrys", cu2)
        bpy.context.scene.collection.objects.link(ob2)
        ob2.parent = ob
        ob2.location = (0, 0, -0.001)
        m2 = material_emisja(nazwa + "_obrys_mat", obrys[0], alfa)
        cu2.materials.clear()
        cu2.materials.append(m2)
        ob["obrys_mat"] = m2.name
    ob["mat"] = m.name
    return ob


def alfa_napisu(ob, klucze):
    animuj_alfa(bpy.data.materials[ob["mat"]], klucze)
    if "obrys_mat" in ob:
        animuj_alfa(bpy.data.materials[ob["obrys_mat"]], klucze)


def ekran_na_kamerze(cam, x, y, odl):
    """Pozycja w układzie kamery dla punktu ekranu (x,y w pikselach 1920×1080, 0,0 = lewy górny) na głębokości odl."""
    sc = bpy.context.scene
    W, H = sc.render.resolution_x, sc.render.resolution_y
    cd = cam.data
    if cd.type == "ORTHO":
        sw = cd.ortho_scale
    else:
        sw = odl * cd.sensor_width / cd.lens
    sh = sw * H / W
    return Vector(((x / W - 0.5) * sw, (0.5 - y / H) * sh, -odl))


def skala_px(cam, odl):
    sc = bpy.context.scene
    cd = cam.data
    sw = cd.ortho_scale if cd.type == "ORTHO" else odl * cd.sensor_width / cd.lens
    return sw / sc.render.resolution_x


def gladko(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def gladko5(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (6 * t - 15) + 10)


# ---------------------------------------------------------------- sfera

def sfera_uv(nazwa="Ziemia", nlon=512, nlat=256, r=1.0):
    """Sfera z dokładną mapą UV równoodległościową (u = (lon+180)/360, v = (lat+90)/180)."""
    me = bpy.data.meshes.new(nazwa)
    verts, faces, uvs = [], [], []
    for j in range(nlat + 1):
        lat = -90 + 180 * j / nlat
        for i in range(nlon + 1):
            lon = -180 + 360 * i / nlon
            verts.append(tuple(ll2xyz(lat, lon, r)))
    for j in range(nlat):
        for i in range(nlon):
            a = j * (nlon + 1) + i
            faces.append((a, a + 1, a + nlon + 2, a + nlon + 1))
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UV")
    loops_uv = []
    for f in me.polygons:
        for li in f.loop_indices:
            vi = me.loops[li].vertex_index
            j, i = divmod(vi, nlon + 1)
            loops_uv.extend((i / nlon, j / nlat))
    uvl.data.foreach_set("uv", loops_uv)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(nazwa, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ---------------------------------------------------------------- render

def argumenty():
    """Argumenty po '--': --proba 1,100,200 (tylko kadry PNG), --koniec N, --bez-blokady."""
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opcje = {"proba": None, "bez_blokady": False}
    i = 0
    while i < len(a):
        if a[i] == "--proba":
            opcje["proba"] = [int(x) for x in a[i + 1].split(",")]
            i += 2
        elif a[i] == "--bez-blokady":
            opcje["bez_blokady"] = True
            i += 1
        else:
            i += 1
    return opcje


def ffmpeg_exe():
    p = shutil.which("ffmpeg")
    if p:
        return p
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages")
    for root, dirs, files in os.walk(base):
        if "ffmpeg.exe" in files:
            return os.path.join(root, "ffmpeg.exe")
    raise RuntimeError("brak ffmpeg")


def renderuj(folder, opcje, kadr_klatka=None):
    """Render klatek do folder/_klatki, potem klip.mp4 i kadr.jpg. Z --proba tylko PNG wskazanych klatek."""
    sc = bpy.context.scene
    kl = os.path.join(folder, "_klatki")
    os.makedirs(kl, exist_ok=True)
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    if opcje.get("proba"):
        for f in opcje["proba"]:
            sc.frame_set(f)
            sc.render.filepath = os.path.join(kl, f"proba_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
            print("[proba]", sc.render.filepath)
        return
    blok = os.path.join(WIDEO, ".renderuje")
    nazwa = os.path.basename(os.path.normpath(folder))
    if not opcje.get("bez_blokady"):
        if os.path.exists(blok):
            with open(blok, encoding="utf-8", errors="replace") as f:
                kto = f.read().strip()
            raise SystemExit(f"[render] karta zajęta: {blok} ({kto}) – spróbuj później")
        with open(blok, "w", encoding="utf-8") as f:
            f.write(nazwa + "\n")
    t0 = time.time()
    try:
        for p in os.listdir(kl):
            if p.startswith("k_") and p.endswith(".png"):
                os.remove(os.path.join(kl, p))
        sc.render.filepath = os.path.join(kl, "k_")
        bpy.ops.render.render(animation=True)
    finally:
        if not opcje.get("bez_blokady") and os.path.exists(blok):
            os.remove(blok)
    t1 = time.time()
    ff = ffmpeg_exe()
    mp4 = os.path.join(folder, "klip.mp4")
    subprocess.run([ff, "-loglevel", "error", "-y", "-framerate", str(sc.render.fps), "-start_number", str(sc.frame_start),
                    "-i", os.path.join(kl, "k_%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-preset", "slow", "-an", "-movflags", "+faststart", mp4], check=True)
    kf = kadr_klatka or sc.frame_end
    subprocess.run([ff, "-loglevel", "error", "-y", "-i", os.path.join(kl, f"k_{kf:04d}.png"), "-vf", "scale=1600:-2",
                    "-q:v", "2", os.path.join(folder, "kadr.jpg")], check=True)
    with open(os.path.join(folder, "_klatki", "czas_renderu.txt"), "w", encoding="utf-8") as f:
        f.write(f"render {t1-t0:.0f} s, klatek {sc.frame_end-sc.frame_start+1}\n")
    print(f"[render] {nazwa}: {t1-t0:.0f} s render, mp4: {mp4}")
