# -*- coding: utf-8 -*-
"""Pomocnicze funkcje klipów „zwiastun-*” (sceny oświetlone, nie płaskie jak globusy).

Import w scena.py:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_wspolne"))
    import globus as G, zwiastun as Z

Korzysta z globus.py (kolory, napisy, kamera, render z blokadą `.renderuje`), niczego w nim nie zmienia.
"""
import bpy, bmesh, math, os
import numpy as np
from mathutils import Vector
import globus as G


def start(klatki, opcje, probki=48, widok="Khronos PBR Neutral", ekspozycja=0.0):
    """Nowa scena EEVEE z cieniami i śledzeniem promieni w przestrzeni ekranu."""
    sc = G.nowa_scena(klatki, proba=bool(opcje.get("proba")))
    ee = sc.eevee
    ee.taa_render_samples = int(os.environ.get("USKOK3D_PROBKI", str(probki // 2 if opcje.get("proba") else probki)))
    for k, v in (("use_shadows", True), ("use_raytracing", True), ("shadow_ray_count", 2), ("shadow_step_count", 6),
                 ("use_fast_gi", True), ("fast_gi_distance", 0.0), ("shadow_pool_size", "1024")):
        try:
            setattr(ee, k, v)
        except Exception as e:
            print("[eevee]", k, e)
    try:
        ee.ray_tracing_options.resolution_scale = "2"
        ee.ray_tracing_options.trace_max_roughness = 0.5
    except Exception as e:
        print("[eevee] rt", e)
    try:
        sc.view_settings.view_transform = widok
    except Exception:
        sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = ekspozycja
    return sc


def swiat(gora, dol, moc=1.0, os_z=True):
    """Tło świata: gradient od koloru `dol` (horyzont i niżej) do `gora` (zenit). Kolory sRGB 0-255."""
    w = bpy.context.scene.world
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    mp = nt.nodes.new("ShaderNodeMapRange")
    mp.inputs[1].default_value = -0.05
    mp.inputs[2].default_value = 0.7
    nt.links.new(sep.outputs[2], mp.inputs[0])
    nt.links.new(mp.outputs[0], ramp.inputs[0])
    ramp.color_ramp.elements[0].color = G.srgb(dol)
    ramp.color_ramp.elements[1].color = G.srgb(gora)
    nt.links.new(ramp.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = moc
    nt.links.new(bg.outputs[0], out.inputs[0])
    return bg, ramp


def pbr(nazwa, kolor, szorstkosc=0.6, metal=0.0, emisja=None, moc_emisji=1.0, alfa=1.0, transmisja=0.0, ior=None):
    """Materiał Principled; kolor sRGB 0-255. Zwraca materiał (m["bsdf"] = nazwa węzła)."""
    m = bpy.data.materials.new(nazwa)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = G.srgb(kolor)
    b.inputs["Roughness"].default_value = szorstkosc
    b.inputs["Metallic"].default_value = metal
    if emisja is not None:
        b.inputs["Emission Color"].default_value = G.srgb(emisja)
        b.inputs["Emission Strength"].default_value = moc_emisji
    if transmisja:
        b.inputs["Transmission Weight"].default_value = transmisja
        m.use_raytrace_refraction = True
    if ior:
        b.inputs["IOR"].default_value = ior
    if alfa < 1.0:
        b.inputs["Alpha"].default_value = alfa
        m.surface_render_method = "BLENDED"
    m["bsdf"] = b.name
    return m


def bsdf(m):
    return m.node_tree.nodes[m["bsdf"]]


def kamien(nazwa, kolor, kolor2=None, skala=6.0, szorstkosc=0.85, wypuklosc=0.35, plamy=0.5, rysy=0.5):
    """Proceduralny kamień: dwa odcienie mieszane szumem, drobne ziarno, wypukłości (bump) i rysy/pęknięcia (Voronoi).
    Współrzędne obiektu, więc wzór nie pływa przy ruchu kamery."""
    m = pbr(nazwa, kolor, szorstkosc)
    nt = m.node_tree
    b = bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")

    def szum(sk, detal=8.0, rough=0.62):
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = sk
        n.inputs["Detail"].default_value = detal
        n.inputs["Roughness"].default_value = rough
        nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
        return n

    def mat(op, x, y):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((x, y)):
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    n1 = szum(skala, 10.0, 0.7)          # nierówności średnie
    n2 = szum(skala * 0.23, 4.0)         # duże plamy barwy
    n3 = szum(skala * 9.0, 6.0, 0.8)     # ziarno
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = skala * 0.55
    nw = nt.nodes.new("ShaderNodeVectorMath")
    nw.operation = "ADD"
    sk = nt.nodes.new("ShaderNodeVectorMath")
    sk.operation = "SCALE"
    sk.inputs["Scale"].default_value = 0.35
    nt.links.new(n2.outputs["Color"], sk.inputs[0])
    nt.links.new(tc.outputs["Object"], nw.inputs[0])
    nt.links.new(sk.outputs[0], nw.inputs[1])
    nt.links.new(nw.outputs[0], vor.inputs["Vector"])
    # rysa: 1 przy krawędzi komórki Voronoi, 0 dalej
    rysa = nt.nodes.new("ShaderNodeMapRange")
    rysa.inputs[1].default_value = 0.0
    rysa.inputs[2].default_value = 0.035
    rysa.inputs[3].default_value = 1.0
    rysa.inputs[4].default_value = 0.0
    nt.links.new(vor.outputs["Distance"], rysa.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    k2 = kolor2 or tuple(max(0, c * 0.62) for c in kolor)
    mix.inputs["A"].default_value = G.srgb(kolor)
    mix.inputs["B"].default_value = G.srgb(k2)
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[1].default_value = 0.5 - plamy * 0.5
    mr.inputs[2].default_value = 0.5 + plamy * 0.5
    nt.links.new(n2.outputs[0], mr.inputs[0])
    nt.links.new(mr.outputs[0], mix.inputs["Factor"])
    # ziarno i rysy przyciemniają barwę
    ciem = mat("MULTIPLY", mat("ADD", mat("MULTIPLY", n3.outputs[0], 0.5), 0.75),
               mat("SUBTRACT", 1.0, mat("MULTIPLY", rysa.outputs[0], 0.45 * rysy)))
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    nt.links.new(mix.outputs["Result"], hsv.inputs["Color"])
    nt.links.new(ciem, hsv.inputs["Value"])
    nt.links.new(hsv.outputs[0], b.inputs["Base Color"])
    wys = mat("SUBTRACT", mat("ADD", n1.outputs[0], mat("MULTIPLY", n3.outputs[0], 0.35)),
              mat("MULTIPLY", rysa.outputs[0], 0.9 * rysy))
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = wypuklosc
    bump.inputs["Distance"].default_value = 0.08
    nt.links.new(wys, bump.inputs["Height"])
    nt.links.new(bump.outputs[0], b.inputs["Normal"])
    return m


def siatka(nazwa, verts, faces, materialy=(), indeksy=None, gladka=False):
    me = bpy.data.meshes.new(nazwa)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate()
    for mt in materialy:
        me.materials.append(mt)
    if indeksy is not None:
        me.polygons.foreach_set("material_index", indeksy)
    if gladka:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.update()
    ob = bpy.data.objects.new(nazwa, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def z_bmesh(nazwa, bm, materialy=(), gladka=False):
    me = bpy.data.meshes.new(nazwa)
    bm.to_mesh(me)
    bm.free()
    for mt in materialy:
        me.materials.append(mt)
    if gladka:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new(nazwa, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def prostopadloscian(nazwa, wym, loc=(0, 0, 0), mat=None, faza=0.0, rot=(0, 0, 0)):
    """Prostopadłościan o wymiarach wym=(x,y,z), środek w loc; faza = zaokrąglenie krawędzi (bevel)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=wym, verts=bm.verts)
    if faza > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=faza, segments=2, affect="EDGES", profile=0.6)
    ob = z_bmesh(nazwa, bm, [mat] if mat else [], gladka=False)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def slonce(kierunek, moc=3.0, kolor=(1.0, 0.95, 0.88), kat=2.0, cien=True):
    """Światło SUN świecące w stronę wektora `kierunek` (dokąd pada światło)."""
    ld = bpy.data.lights.new("Slonce", "SUN")
    ld.energy = moc
    ld.color = kolor
    ld.angle = math.radians(kat)
    ld.use_shadow = cien
    ob = bpy.data.objects.new("Slonce", ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = Vector(kierunek).normalized().to_track_quat("-Z", "Y").to_euler()
    return ob


def lampa(loc, cel, moc=500.0, kolor=(1, 1, 1), rozmiar=4.0, typ="AREA", cien=True, stozek=50.0):
    ld = bpy.data.lights.new("Lampa", typ)
    ld.energy = moc
    ld.color = kolor
    if typ == "AREA":
        ld.size = rozmiar
    else:
        ld.shadow_soft_size = rozmiar
    if typ == "SPOT":
        ld.spot_size = math.radians(stozek)
        ld.spot_blend = 0.6
    ld.use_shadow = cien
    ob = bpy.data.objects.new("Lampa", ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(cel) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


def klucze(ob, sciezka, pary, indeks=-1, gladko=True):
    """pary: [(klatka, wartość), ...] dla właściwości `sciezka` obiektu (lub dowolnego ID / struktury)."""
    for f, v in pary:
        if indeks >= 0:
            cur = getattr(ob, sciezka)
            cur[indeks] = v
        else:
            setattr(ob, sciezka, v)
        ob.keyframe_insert(sciezka, index=indeks, frame=f)
    if gladko:
        G.wygladz(ob.id_data)


def lot_kamery(cam, cel_ob, punkty):
    """Kamera patrzy na pusty obiekt `cel_ob`; punkty: [(klatka, (x,y,z) kamery, (x,y,z) celu), ...]."""
    con = cam.constraints.new("TRACK_TO")
    con.target = cel_ob
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    for f, pk, pc in punkty:
        cam.location = pk
        cam.keyframe_insert("location", frame=f)
        cel_ob.location = pc
        cel_ob.keyframe_insert("location", frame=f)
    G.wygladz(cam)
    G.wygladz(cel_ob)


def pusty(nazwa="Cel", loc=(0, 0, 0)):
    ob = bpy.data.objects.new(nazwa, None)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    return ob


def napis_ekran(cam, tekst, x, y, px, kolor=G.ZLOTY, kroj="georgiab", wyr="CENTER", odl=1.0, pojaw=None, obrys=True,
                odstep=1.0):
    """Napis przypięty do kamery w punkcie ekranu (x, y w pikselach 1920×1080), wysokość liter ok. `px` pikseli.
    pojaw = (klatka_start, klatka_pełna) – płynne pojawienie się; None = widoczny od początku."""
    s = G.skala_px(cam, odl)
    ob = G.napis(tekst, px * s, kolor, kroj, wyr, rodzic=cam, loc=G.ekran_na_kamerze(cam, x, y, odl),
                 obrys=((8, 12, 22), px * s * 0.035) if obrys else None, odstep=odstep)
    ob.visible_shadow = False
    for ch in ob.children:
        ch.visible_shadow = False
    if pojaw:
        G.alfa_napisu(ob, [(1, 0.0), (pojaw[0], 0.0), (pojaw[1], 1.0)])
    return ob


def napis_swiat(tekst, rozmiar, loc, kolor=G.ZLOTY, kroj="georgiab", wyr="CENTER", rot=(math.pi / 2, 0, 0), pojaw=None,
                obrys=None):
    """Napis stojący w scenie (domyślnie pionowo, czytany z -Y)."""
    ob = G.napis(tekst, rozmiar, kolor, kroj, wyr, loc=loc, rot=rot, obrys=obrys)
    ob.visible_shadow = False
    for ch in ob.children:
        ch.visible_shadow = False
    if pojaw:
        G.alfa_napisu(ob, [(1, 0.0), (pojaw[0], 0.0), (pojaw[1], 1.0)])
    return ob


def linia(punkty, grubosc, kolor=G.ZLOTY, nazwa="Linia", pojaw=None, alfa=1.0):
    """Łamana 3D jako krzywa z okrągłym przekrojem, materiał świecący."""
    cu = bpy.data.curves.new(nazwa, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(punkty) - 1)
    for p, v in zip(sp.points, punkty):
        p.co = (*v, 1.0)
    cu.bevel_depth = grubosc
    cu.bevel_resolution = 2
    ob = bpy.data.objects.new(nazwa, cu)
    bpy.context.scene.collection.objects.link(ob)
    m = G.material_emisja(nazwa + "_mat", kolor, alfa)
    cu.materials.append(m)
    ob.visible_shadow = False
    ob["mat"] = m.name
    if pojaw:
        G.animuj_alfa(m, [(1, 0.0), (pojaw[0], 0.0), (pojaw[1], alfa)])
    return ob
