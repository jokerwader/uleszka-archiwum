# -*- coding: utf-8 -*-
"""Pomocnik scen-schematów (bryły oświetlone słońcem, podpisy zwrócone do kamery, rosnące linie, strzałki).

Uzupełnia globus.py (z niego: nowa_scena, kamera, tlo_kamery, napis, renderuj). Import w scena.py:
    sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
    import globus as G
    import schemat as S

Używają: obieg-wody, paski-magnetyczne, teotihuacan-aleja, titicaca-linia-brzegowa, odchylenie-17-globus.
"""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector, Matrix
import globus as G


def polacz(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def swiatlo(kat=(50, 0, -35), sila=3.2, otoczenie=(150, 165, 200), moc=0.6, cienie=True, miekkosc=6.0):
    """Słońce + rozproszone światło otoczenia (kolor świata; tło i tak zasłania płaszczyzna tlo_kamery)."""
    sc = bpy.context.scene
    bg = sc.world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = G.srgb(otoczenie)
    bg.inputs[1].default_value = moc
    L = bpy.data.lights.new("Slonce", "SUN")
    L.energy = sila
    L.angle = math.radians(miekkosc)
    L.use_shadow = cienie
    ob = polacz(bpy.data.objects.new("Slonce", L))
    ob.rotation_euler = tuple(math.radians(a) for a in kat)
    return ob


def mat(nazwa, kolor, szorstkosc=0.85, alfa=1.0, emisja=0.0, metal=0.0, przezroczysty=None):
    """Materiał Principled z płaskim kolorem (sRGB 0-255). m["bsdf"] = nazwa węzła."""
    m = bpy.data.materials.new(nazwa)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = G.srgb(kolor)
    b.inputs["Roughness"].default_value = szorstkosc
    b.inputs["Metallic"].default_value = metal
    b.inputs["Alpha"].default_value = alfa
    if emisja:
        b.inputs["Emission Color"].default_value = G.srgb(kolor)
        b.inputs["Emission Strength"].default_value = emisja
    if przezroczysty if przezroczysty is not None else alfa < 1.0:
        m.surface_render_method = "BLENDED"
    m["bsdf"] = b.name
    return m


def bsdf(m):
    return m.node_tree.nodes[m["bsdf"]]


def animuj_gniazdo(m, gniazdo, klucze, interp="BEZIER"):
    """Klucze (klatka, wartość) na wejściu węzła Principled, np. "Alpha", "Emission Strength"."""
    s = bsdf(m).inputs[gniazdo]
    for f, v in klucze:
        s.default_value = v
        s.keyframe_insert("default_value", frame=f)
    G.wygladz(m.node_tree, interp)


def klucze(ob, sciezka, lista, interp="BEZIER"):
    """lista: [(klatka, wartość), ...] dla właściwości obiektu/danych (np. "location", "scale", "bevel_factor_end")."""
    for f, v in lista:
        setattr(ob, sciezka, v)
        ob.keyframe_insert(sciezka, frame=f)
    G.wygladz(ob, interp)


def pojaw(ob, f0, dl=12, skala=(1, 1, 1), os_z=False):
    """Obiekt rośnie od zera (albo tylko w osi Z) między klatkami f0 i f0+dl."""
    s = Vector(skala)
    ob.scale = (s.x, s.y, 0.001) if os_z else (0.001, 0.001, 0.001)
    ob.keyframe_insert("scale", frame=max(1, f0))
    ob.scale = s
    ob.keyframe_insert("scale", frame=f0 + dl)
    G.wygladz(ob)


# ---------------------------------------------------------------- siatki

def siatka(nazwa, verts, faces, materialy=(), gladka=False, indeksy=None):
    me = bpy.data.meshes.new(nazwa)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    for m in materialy:
        me.materials.append(m)
    if indeksy is not None:
        me.polygons.foreach_set("material_index", indeksy)
    if gladka:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.update()
    return polacz(bpy.data.objects.new(nazwa, me))


def pudlo(nazwa, srodek, wymiary, material, obrot_z=0.0):
    """Prostopadłościan o środku podstawy w `srodek` (x, y, z dołu) i wymiarach (dx, dy, dz)."""
    dx, dy, dz = wymiary[0] / 2, wymiary[1] / 2, wymiary[2]
    v = [(-dx, -dy, 0), (dx, -dy, 0), (dx, dy, 0), (-dx, dy, 0), (-dx, -dy, dz), (dx, -dy, dz), (dx, dy, dz), (-dx, dy, dz)]
    f = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = siatka(nazwa, v, f, [material] if material else [])
    ob.location = srodek
    ob.rotation_euler = (0, 0, obrot_z)
    return ob


def teren(nazwa, fz, x0, x1, y0, y1, nx, ny, dno, mat_gora, mat_bok):
    """Bryła terenu: góra z = fz(X, Y) (tablice numpy), pionowe ściany do z = dno. Góra wygładzona, boki płaskie."""
    xs = np.linspace(x0, x1, nx)
    ys = np.linspace(y0, y1, ny)
    X, Y = np.meshgrid(xs, ys)
    Z = fz(X, Y)
    verts = [(float(X[j, i]), float(Y[j, i]), float(Z[j, i])) for j in range(ny) for i in range(nx)]
    faces, idx = [], []
    for j in range(ny - 1):
        for i in range(nx - 1):
            a = j * nx + i
            faces.append((a, a + 1, a + nx + 1, a + nx))
            idx.append(0)
    # obwód (przeciwnie do ruchu wskazówek, patrząc z góry)
    obw = [(0, i) for i in range(nx)] + [(j, nx - 1) for j in range(1, ny)] + \
          [(ny - 1, i) for i in range(nx - 2, -1, -1)] + [(j, 0) for j in range(ny - 2, 0, -1)]
    n0 = len(verts)
    for j, i in obw:
        verts.append((float(X[j, i]), float(Y[j, i]), float(Z[j, i])))
    n1 = len(verts)
    for j, i in obw:
        verts.append((float(X[j, i]), float(Y[j, i]), dno))
    L = len(obw)
    for k in range(L):
        k2 = (k + 1) % L
        faces.append((n0 + k, n1 + k, n1 + k2, n0 + k2))
        idx.append(1)
    ob = siatka(nazwa, verts, faces, [mat_gora, mat_bok], indeksy=idx)
    me = ob.data
    sm = [True] * ((nx - 1) * (ny - 1)) + [False] * L
    me.polygons.foreach_set("use_smooth", sm)
    ob["nx"], ob["ny"] = nx, ny
    return ob


def linia(nazwa, pts, grub, material, f0=None, f1=None, zamknieta=False, rozdz=4, plaska=None):
    """Krzywa 3D (łamana) o przekroju koła; z f0, f1 rośnie od początku do końca."""
    cu = bpy.data.curves.new(nazwa, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = grub
    cu.bevel_resolution = rozdz
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1)
    sp.use_cyclic_u = zamknieta
    ob = polacz(bpy.data.objects.new(nazwa, cu))
    cu.materials.append(material)
    if f0 is not None:
        cu.bevel_factor_mapping_end = "SPLINE"
        klucze(cu, "bevel_factor_end", [(f0, 0.0), (f1, 1.0)])
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=max(1, f0 - 1))
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=f0)
    return ob


def kreski(nazwa, a, b, grub, wys, material, dl=3.0, przerwa=2.0, f0=None, f1=None):
    """Linia przerywana z płaskich klocków od a do b (Vector); z f0, f1 kreski pojawiają się po kolei."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    d.normalize()
    kat = math.atan2(d.y, d.x)
    n = max(1, int((L + przerwa) / (dl + przerwa)))
    obs = []
    for i in range(n):
        s = i * (dl + przerwa)
        e = min(L, s + dl)
        c = a + d * ((s + e) / 2)
        ob = pudlo(f"{nazwa}_{i:03d}", (c.x, c.y, c.z), (e - s, grub, wys), material, kat)
        if f0 is not None:
            fa = f0 + (f1 - f0) * i / n
            pojaw(ob, int(round(fa)), 5)
        obs.append(ob)
    return obs


def strzalka(nazwa, a, b, grub, material, grot=None, dl_grotu=None, n=20):
    """Strzałka 3D (walec + stożek) od a do b; obiekt ma początek w a i oś +Z skierowaną do b (skalowanie Z = wzrost)."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    grot = grot or grub * 2.6
    dg = min(dl_grotu or grot * 2.2, L * 0.6)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=grub, radius2=grub, depth=L - dg,
                          matrix=Matrix.Translation((0, 0, (L - dg) / 2)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=grot, radius2=0.0, depth=dg,
                          matrix=Matrix.Translation((0, 0, L - dg / 2)))
    me = bpy.data.meshes.new(nazwa)
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.materials.append(material)
    ob = polacz(bpy.data.objects.new(nazwa, me))
    ob.location = a
    ob.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return ob


def kula(nazwa, srodek, r, material, seg=24):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    me = bpy.data.meshes.new(nazwa)
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.materials.append(material)
    ob = polacz(bpy.data.objects.new(nazwa, me))
    ob.location = srodek
    return ob


# ---------------------------------------------------------------- podpisy

def podpis(tekst, rozmiar, kolor, loc, cam=None, f0=None, kroj="arialb", wyr="CENTER", obrys=((8, 12, 24), 0.0),
           nazwa=None, rot=None, odstep=1.05, dl=14):
    """Napis w świecie. Z cam: zawsze zwrócony do kamery (billboard). Z rot: leży jak na mapie.
    obrys: (kolor, grubość jako ułamek rozmiaru) – ciemna obwódka dla czytelności na jasnym tle; None = bez."""
    ob_ = (obrys[0], rozmiar * obrys[1]) if obrys and obrys[1] > 0 else None
    ob = G.napis(tekst, rozmiar, kolor, kroj, wyr, loc=tuple(loc), nazwa=nazwa or ("Podpis_" + tekst[:12]), obrys=ob_,
                 odstep=odstep)
    for o in [ob] + list(ob.children):
        o.visible_shadow = False
    if cam is not None:
        c = ob.constraints.new("COPY_ROTATION")
        c.target = cam
    elif rot is not None:
        ob.rotation_euler = rot
    if f0 is not None:
        G.alfa_napisu(ob, [(max(1, f0 - 1), 0.0), (f0, 0.0), (f0 + dl, 1.0)])
    return ob


def orbita(cam, cel, klucze_, gora_z=True):
    """Kamera patrzy na `cel` (pusty obiekt) i jedzie po kluczach [(klatka, azymut°, wysokość°, odległość), ...].
    Azymut liczony od osi +X przeciwnie do wskazówek (kamera stoi po tej stronie), wysokość nad poziomem."""
    e = polacz(bpy.data.objects.new("Cel", None))
    e.location = cel
    c = cam.constraints.new("TRACK_TO")
    c.target = e
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    for f, az, wys, odl in klucze_:
        a, h = math.radians(az), math.radians(wys)
        cam.location = Vector(cel) + Vector((math.cos(h) * math.cos(a), math.cos(h) * math.sin(a), math.sin(h))) * odl
        cam.keyframe_insert("location", frame=f)
    G.wygladz(cam)
    return e


def orbita_f(cam, cel, fn, klatki, krok=8):
    """Jak orbita, ale z funkcji fn(klatka) -> (azymut°, wysokość°, odległość); gęste klucze = płynny łuk."""
    fs = list(range(1, klatki + 1, krok))
    if fs[-1] != klatki:
        fs.append(klatki)
    return orbita(cam, cel, [(f, *fn(f)) for f in fs])


def rampa(f, f0, f1):
    """Wygładzone 0..1 między klatkami f0 i f1."""
    return G.gladko((f - f0) / float(f1 - f0))
