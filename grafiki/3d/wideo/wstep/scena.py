# -*- coding: utf-8 -*-
"""
Wstęp odcinka podcastu „Uwierz we własny rozum – teksty Leszka Klimka” (30 s, 750 klatek, 25 kl./s, bez dźwięku).

Animacja pod zapowiedź, którą lektor czyta na tle muzyki w pierwszych 30 s każdego nagrania. Jest wspólna
dla wszystkich odcinków: tytuł konkretnego odcinka nakłada `scripts/wideo.ts` w pustym środku kadru (14,3–25 s).

    0–163  z ciemności złoty błysk i tytuł „Uwierz we własny rozum”; od kl. 47 tytuł odsuwa się w górę,
           w ciepłym świetle pojawia się „w hołdzie śp. Leszkowi Wiktorowi Klimkowi”
  163–358  przelot wśród rysunków Leszka w złotych ramkach, napis „uleszka.net · 2004–2007”;
           od kl. 318 („czytane bez zmian”) rysunki układają się w równe rzędy
  358–625  Ziemia widziana z orbity nisko nad krawędzią, gwiazdy; środek kadru pusty na tytuł odcinka;
           na kl. 425 Słońce wychodzi zza krawędzi, od kl. 500 mały napis o lektorze
  625–750  kamera odpływa: Ziemia maleje, wokół niej rysuje się złoty krąg zodiaku; ostatnia klatka nie jest czarna

Momenty są w słowniku T na górze pliku (numery klatek filmu od 0), więc łatwo je przestawić.

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/wstep/scena.py
  ... -- --proba 30,120,250,340,450,749 [--skala 50]   tylko kadry próbne PNG do _klatki/
  ... -- --od 358 --do 749                              render części klatek (bez składania mp4)
  ... -- --czekaj                                       czeka, aż zniknie blokada .renderuje
  ... -- --zloz                                         tylko składa klip.mp4 i kadr.jpg z gotowych klatek
"""
import bpy, bmesh, math, os, sys, csv, time, subprocess, random
import numpy as np
from mathutils import Vector, Matrix, Quaternion, noise

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G
from wezly import Wezly

KLATKI_DIR = os.path.join(TU, "_klatki")
NAZWA = "wstep"
KLATEK, FPS = 750, 25

# ---------------------------------------------------------------- CZAS (klatki filmu, od 0)
# Zapowiedź lektora z nagrania odcinka 2 (w innych odcinkach czasy są prawie takie same) i akcenty muzyki.
T = dict(
    blysk=4,        # 0,0 s „Uwierz we własny rozum.” – złoty błysk i wejście tytułu
    hold=47,        # 1,9 s „Podcast w hołdzie świętej pamięci Leszkowi Wiktorowi Klimkowi.”
    rysunki=163,    # 6,5 s „Jego teksty ze strony uleszka.net z lat 2004–2007,” (cięcie przez przyciemnienie)
    adres=190,      # napis „uleszka.net · 2004–2007”
    uklad=318,      # 12,7 s „czytane bez zmian.” – rysunki układają się w rzędy (akcent muzyki ok. 13 s)
    ziemia=358,     # 14,3 s „Odcinek …” (cięcie); stąd do `odplyw` środek kadru jest pusty na tytuł odcinka
    slonce=425,     # 17 s akcent muzyki – Słońce wychodzi zza krawędzi Ziemi
    lektor=500,     # 20,0 s „Czyta lektor wygenerowany przez sztuczną inteligencję.” (akcent muzyki ok. 20,5 s)
    odplyw=625,     # 25 s koniec mowy, muzyka wygasa – kamera odpływa
)
KADR = 40           # klatka na kadr.jpg (tytuł)

ZLOTO = G.srgb(G.ZLOTY)[:3]                    # #f0c46f liniowo
ZLOTO_J = G.srgb((255, 246, 224))[:3]          # #fff6e0
ZLOTO_C = G.srgb((180, 122, 34))[:3]           # #b47a22
KREM = (243, 234, 216)


def argumenty():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = {"proba": None, "skala": 100, "od": 0, "do": KLATEK - 1, "czekaj": False, "zloz": False, "bez_blokady": False}
    i = 0
    while i < len(a):
        if a[i] == "--proba":
            o["proba"] = [int(x) for x in a[i + 1].split(",")]; i += 2
        elif a[i] in ("--skala", "--od", "--do"):
            o[a[i][2:]] = int(a[i + 1]); i += 2
        elif a[i] in ("--czekaj", "--zloz"):
            o[a[i][2:]] = True; i += 1
        elif a[i] == "--bez-blokady":
            o["bez_blokady"] = True; i += 1
        else:
            i += 1
    return o


opcje = argumenty()
random.seed(7)
rng = np.random.default_rng(7)

# ================================================================ scena i pomocnicze
sc = G.nowa_scena(KLATEK)
sc.frame_start, sc.frame_end = 0, KLATEK - 1
sc.render.fps = FPS
sc.render.resolution_percentage = opcje["skala"]
sc.eevee.taa_render_samples = int(os.environ.get("USKOK3D_PROBKI", "24" if opcje["proba"] else "56"))
for k, v in (("use_shadows", True), ("use_volumetric_shadows", True), ("volumetric_end", 600.0),
             ("volumetric_samples", 96), ("shadow_pool_size", "1024"), ("bokeh_max_size", 60.0)):
    try:
        setattr(sc.eevee, k, v)
    except Exception as e:
        print("[eevee]", k, e)
try:
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.4
    sc.render.motion_blur_position = "START"     # rozmycie nie sięga za cięcie (kamera z poprzedniego ujęcia)
except Exception as e:
    print("[rozmycie]", e)
try:
    sc.view_settings.view_transform = "Khronos PBR Neutral"    # barwy jak w „Standard”, ale łagodne przejście w biel
except Exception as e:
    print("[widok]", e)
bg = sc.world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.0035, 0.005, 0.011, 1)
bg.inputs[1].default_value = 1.0

WIDOK = {}        # nazwa obiektu -> lista zakresów klatek [a, b), w których obiekt jest renderowany


class Zestaw:
    """Wszystko, co powstanie wewnątrz `with`, jest widoczne tylko w podanych zakresach klatek."""
    def __init__(self, zakresy):
        self.zakresy = zakresy

    def __enter__(self):
        self.przed = {o.name for o in bpy.data.objects}
        return self

    def __exit__(self, *a):
        for o in bpy.data.objects:
            if o.name not in self.przed and o.name not in WIDOK:
                WIDOK[o.name] = self.zakresy


def widok(ob, zakresy):
    WIDOK[ob.name] = zakresy
    return ob


def animuj(obj, prop, klucze, interp="BEZIER", index=-1):
    """klucze: [(klatka, wartość[, interpolacja])]. Interpolacja dotyczy odcinka za kluczem."""
    for k in klucze:
        if index >= 0:
            getattr(obj, prop)[index] = k[1]
        else:
            setattr(obj, prop, k[1])
        obj.keyframe_insert(prop, frame=k[0], index=index)
    tryby = {k[0]: (k[2] if len(k) > 2 else interp) for k in klucze}
    path = obj.path_from_id(prop)
    for fc in G._fcurves(obj.id_data.animation_data.action):
        if fc.data_path == path and (index < 0 or fc.array_index == index):
            for kp in fc.keyframe_points:
                t = tryby.get(int(round(kp.co[0])), interp)
                if t == "GLADKO":
                    kp.interpolation = "BEZIER"; kp.handle_left_type = kp.handle_right_type = "AUTO"
                elif t == "BEZIER":
                    kp.interpolation = "BEZIER"; kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
                else:
                    kp.interpolation = t
            fc.update()


def kamera(nazwa, start, klucze, lens=35, fstop=None, interp="LINEAR", ostrosc=None):
    """klucze: [(klatka, położenie, cel[, ogniskowa])]. Kamera patrzy na pusty obiekt-cel; znacznik włącza ją od `start`."""
    cd = bpy.data.cameras.new(nazwa)
    cd.lens = lens
    cd.clip_start, cd.clip_end = 0.03, 4000
    ob = bpy.data.objects.new(nazwa, cd)
    sc.collection.objects.link(ob)
    cel = bpy.data.objects.new(nazwa + "_cel", None)
    sc.collection.objects.link(cel)
    con = ob.constraints.new("TRACK_TO")
    con.target = cel
    con.track_axis, con.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    animuj(ob, "location", [(k[0], tuple(k[1])) for k in klucze], interp)
    animuj(cel, "location", [(k[0], tuple(k[2])) for k in klucze], interp)
    if len(klucze[0]) > 3:
        animuj(cd, "lens", [(k[0], k[3]) for k in klucze], interp)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.focus_object = ostrosc or cel
        cd.dof.aperture_fstop = fstop
    m = sc.timeline_markers.new(nazwa, frame=start)
    m.camera = ob
    if start == 0:
        sc.camera = ob
    return ob, cel


def mat_nowy(nazwa, przezroczysty=False):
    m = bpy.data.materials.new(nazwa)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    if przezroczysty:
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            m.blend_method = "BLEND"
    return m, nt, Wezly(nt)


def wyjscie(nt, shader, objetosc=False):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(shader, out.inputs["Volume" if objetosc else "Surface"])


def emisja(W, kolor, sila=1.0, alfa=None):
    """Zwraca gniazdo shadera: emisja (ew. zmieszana z przezroczystością wg alfa)."""
    em = W._node("ShaderNodeEmission")
    W._in(em.inputs["Color"], kolor if isinstance(kolor, bpy.types.NodeSocket) else (*kolor[:3], 1))
    W._in(em.inputs["Strength"], sila)
    if alfa is None:
        return em.outputs[0], em
    tr = W._node("ShaderNodeBsdfTransparent")
    mix = W._node("ShaderNodeMixShader")
    W._in(mix.inputs[0], alfa)
    W.nt.links.new(tr.outputs[0], mix.inputs[1])
    W.nt.links.new(em.outputs[0], mix.inputs[2])
    return mix.outputs[0], em


def mat_swiatlo(nazwa, kolor, sila=1.0):
    m, nt, W = mat_nowy(nazwa)
    sh, em = emisja(W, kolor, sila)
    wyjscie(nt, sh)
    m["em"] = em.name
    return m


def sila_emisji(mat):
    return mat.node_tree.nodes[mat["em"]].inputs["Strength"]


def czas_s(W):
    """Węzeł wartości = czas w sekundach (klucze liniowe)."""
    v = W._node("ShaderNodeValue")
    animuj(v.outputs[0], "default_value", [(0, 0.0), (KLATEK, KLATEK / FPS)], "LINEAR")
    return v.outputs[0]


def mat_pryncypialny(nazwa, kolor, szorstkosc=0.8, metal=0.0, wypuklosc=None):
    """wypuklosc: (skala szumu, siła)"""
    m, nt, W = mat_nowy(nazwa)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = (*kolor[:3], 1)
    bs.inputs["Roughness"].default_value = szorstkosc
    bs.inputs["Metallic"].default_value = metal
    if wypuklosc:
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = wypuklosc[0]
        nz.inputs["Detail"].default_value = 8
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = wypuklosc[1]
        nt.links.new(nz.outputs[0], bp.inputs["Height"])
        nt.links.new(bp.outputs[0], bs.inputs["Normal"])
    wyjscie(nt, bs.outputs[0])
    m["bsdf"] = bs.name
    return m


def linia3d(nazwa, punkty, grubosc, mat, cykl=False, rodzic=None):
    cu = bpy.data.curves.new(nazwa, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(punkty) - 1)
    for p, v in zip(sp.points, punkty):
        p.co = (v[0], v[1], v[2], 1)
    sp.use_cyclic_u = cykl
    cu.bevel_depth = grubosc
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    cu.materials.append(mat)
    ob = bpy.data.objects.new(nazwa, cu)
    sc.collection.objects.link(ob)
    if rodzic:
        ob.parent = rodzic
    return ob


def okrag_pkt(r, n=360, faza=0.0, u=Vector((1, 0, 0)), v=Vector((0, 1, 0)), srodek=Vector((0, 0, 0))):
    return [srodek + r * (math.cos(faza + 2 * math.pi * i / n) * u + math.sin(faza + 2 * math.pi * i / n) * v) for i in range(n)]


def siatka(nazwa, bm, mat, gladka=False, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(nazwa)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    if gladka:
        me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
    me.materials.append(mat)
    ob = bpy.data.objects.new(nazwa, me)
    ob.location = loc
    sc.collection.objects.link(ob)
    return ob


def pudlo(bm, podstawa, wym, obrot=0.0, zwez=(1.0, 1.0)):
    """Prostopadłościan (ew. zwężony ku górze) o środku podstawy `podstawa`, obrócony wokół osi z."""
    sx, sy, h = wym
    co, si = math.cos(obrot), math.sin(obrot)
    vs = []
    for z, kx, ky in ((0, 1, 1), (h, zwez[0], zwez[1])):
        for ax, ay in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            x, y = ax * sx / 2 * kx, ay * sy / 2 * ky
            vs.append(bm.verts.new((podstawa[0] + x * co - y * si, podstawa[1] + x * si + y * co, podstawa[2] + z)))
    for f in ((3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([vs[i] for i in f])
    return vs


def kula(nazwa, r, loc, mat, seg=32, cien=True):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    ob = siatka(nazwa, bm, mat, gladka=True, loc=loc)
    ob.visible_shadow = cien
    return ob


def chmura(nazwa, pts, prom, jas, mat, kol=None, ruch=None, loc=(0, 0, 0), szyb=None):
    """Chmura punktów (Geometry Nodes: siatka -> punkty) z atrybutami prom (promień), jas (jasność), los, kol.
    ruch: dict(v=(x,y,z) dryf m/s, amp=, skala=, tempo= falowanie; wybuch=dict(t0=, k=, g=) rozlot od środka)."""
    n = len(pts)
    me = bpy.data.meshes.new(nazwa)
    me.vertices.add(n)
    me.vertices.foreach_set("co", np.asarray(pts, np.float32).ravel())
    for nz, arr in (("prom", prom), ("jas", jas), ("los", rng.random(n)), ("szyb", szyb)):
        if arr is not None:
            a = me.attributes.new(nz, "FLOAT", "POINT")
            a.data.foreach_set("value", np.asarray(arr, np.float32))
    if kol is not None:
        a = me.attributes.new("kol", "FLOAT_COLOR", "POINT")
        a.data.foreach_set("color", np.asarray(kol, np.float32).ravel())
    ob = bpy.data.objects.new(nazwa, me)
    ob.location = loc
    sc.collection.objects.link(ob)
    ng = bpy.data.node_groups.new(nazwa + "_gn", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi, go = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
    W = Wezly(ng)

    def atr(nz):
        a = W._node("GeometryNodeInputNamedAttribute", data_type="FLOAT")
        a.inputs["Name"].default_value = nz
        return a.outputs[0]
    geo = gi.outputs[0]
    if ruch:
        czas = W._node("GeometryNodeInputSceneTime").outputs["Seconds"]
        pos = W._node("GeometryNodeInputPosition").outputs[0]
        off = None
        if "v" in ruch:
            off = W.scale(W.vec(tuple(ruch["v"])), W.mul(czas, W.add(0.5, atr("los"))))
        if ruch.get("amp"):
            nzn = W._node("ShaderNodeTexNoise")
            nzn.inputs["Scale"].default_value = 1.0
            nzn.inputs["Detail"].default_value = 1.0
            W._in(nzn.inputs["Vector"], W.vadd(W.scale(pos, ruch.get("skala", 0.5)),
                                               W.vec(0.0, 0.0, W.mul(czas, ruch.get("tempo", 0.3)))))
            fal = W.scale(W.vmath("SUBTRACT", nzn.outputs["Color"], (0.5, 0.5, 0.5)), 2.0 * ruch["amp"])
            off = fal if off is None else W.vadd(off, fal)
        if "wybuch" in ruch:
            wb = ruch["wybuch"]
            tt = W.mx(W.sub(czas, wb["t0"]), 0.0)
            droga = W.mul(atr("szyb"), W.sub(1.0, W.math("POWER", math.e, W.mul(tt, -wb["k"]))))
            o2 = W.vadd(W.scale(W.norm(pos), droga), W.vec(0.0, 0.0, W.mul(tt, -wb.get("g", 0.0))))
            off = o2 if off is None else W.vadd(off, o2)
        sp = W._node("GeometryNodeSetPosition")
        ng.links.new(geo, sp.inputs["Geometry"])
        ng.links.new(off, sp.inputs["Offset"])
        geo = sp.outputs[0]
    mp = W._node("GeometryNodeMeshToPoints")
    ng.links.new(geo, mp.inputs["Mesh"])
    ng.links.new(atr("prom"), mp.inputs["Radius"])
    sm = W._node("GeometryNodeSetMaterial")
    ng.links.new(mp.outputs[0], sm.inputs["Geometry"])
    sm.inputs["Material"].default_value = mat
    ng.links.new(sm.outputs[0], go.inputs[0])
    md = ob.modifiers.new("gn", "NODES")
    md.node_group = ng
    me.materials.append(mat)
    ob.visible_shadow = False
    return ob


def mat_punkty(nazwa, kolor=None, sila=1.0, migot=0.0):
    """Materiał punktów: emisja = (kolor albo atrybut kol) × sila × atrybut jas × migotanie."""
    m, nt, W = mat_nowy(nazwa)
    a = W._node("ShaderNodeAttribute", attribute_name="jas")
    s = W._node("ShaderNodeValue")
    s.outputs[0].default_value = sila
    st = W.mul(a.outputs["Fac"], s.outputs[0])
    if migot:
        nz = W._node("ShaderNodeTexNoise", noise_dimensions="4D")
        nz.inputs["Scale"].default_value = 3.0
        W._in(nz.inputs["Vector"], W._node("ShaderNodeNewGeometry").outputs["Position"])
        W._in(nz.inputs["W"], W.mul(czas_s(W), 0.9))
        st = W.mul(st, W.add(1.0 - migot, W.mul(nz.outputs[0], 2.0 * migot)))
    if kolor is None:
        kolor = W._node("ShaderNodeAttribute", attribute_name="kol").outputs["Color"]
    sh, em = emisja(W, kolor, st)
    wyjscie(nt, sh)
    m["sila"] = s.name
    return m


def pyl(nazwa, n, losuj, mat, prom=(0.004, 0.014), loc=(0, 0, 0), ruch=None):
    pts = losuj(n)
    p = rng.uniform(prom[0], prom[1], n) * (0.6 + 1.2 * rng.random(n) ** 3)
    jas = 0.25 + 1.6 * rng.random(n) ** 2
    return chmura(nazwa, pts, p, jas, mat, loc=loc,
                  ruch=ruch or dict(v=(0.01, 0.006, -0.012), amp=0.05, skala=0.4, tempo=0.25))


def w_pudle(srodek, wym):
    return lambda n: np.asarray(srodek) + (rng.random((n, 3)) - 0.5) * np.asarray(wym)


def kopula(nazwa, srodek, R, kol_dol, kol_gora, slonce=None, kol_slonca=(1.0, 0.62, 0.25), sila_slonca=1.2, wykl=30.0):
    """Kopuła nieba: gradient od horyzontu ku zenitowi i łuna wokół kierunku Słońca. Nie rzuca cienia."""
    m, nt, W = mat_nowy(nazwa)
    kier = W.norm(W.coord("Object"))
    z = W.sep(kier)[2]
    t = W.smooth(-0.02, 0.55, z)
    kol = W.mixv(t, kol_dol, kol_gora)
    if slonce is not None:
        d = W.mx(W.dot(kier, tuple(Vector(slonce).normalized())), 0.0)
        luna = W.add(W.mul(W.math("POWER", d, wykl), sila_slonca), W.mul(W.math("POWER", d, 4.0), sila_slonca * 0.18))
        kol = W.vadd(kol, W.scale(W.vec(tuple(kol_slonca)), luna))
    sh, _ = emisja(W, kol, 1.0)
    wyjscie(nt, sh)
    ob = kula(nazwa, R, srodek, m, seg=48, cien=False)
    return ob


def gwiazdy_kopuly(nazwa, srodek, R, n, mat, zmin=0.05):
    v = rng.normal(size=(n * 3, 3))
    v /= np.linalg.norm(v, axis=1)[:, None]
    v = v[v[:, 2] > zmin][:n]
    k = len(v)
    jas = 0.4 + 3.0 * rng.random(k) ** 6
    return chmura(nazwa, v * R, R * (0.0007 + 0.0009 * rng.random(k)), jas, mat, loc=srodek)


def slonce_lampa(nazwa, kier, sila, kolor=(1.0, 0.72, 0.42), kat=1.5):
    ld = bpy.data.lights.new(nazwa, "SUN")
    ld.energy = sila
    ld.color = kolor
    ld.angle = math.radians(kat)
    ob = bpy.data.objects.new(nazwa, ld)
    ob.rotation_euler = (-Vector(kier)).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(ob)
    return ob


def lampa(nazwa, typ, loc, cel, moc, kolor=(1, 1, 1), rozmiar=1.0, kat=None):
    ld = bpy.data.lights.new(nazwa, typ)
    ld.energy = moc
    ld.color = kolor
    if typ == "AREA":
        ld.size = rozmiar
    else:
        ld.shadow_soft_size = rozmiar
    if kat:
        ld.spot_size = math.radians(kat)
        ld.spot_blend = 0.6
    ob = bpy.data.objects.new(nazwa, ld)
    ob.location = loc
    ob.rotation_euler = (Vector(cel) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(ob)
    return ob


def mgla(nazwa, srodek, wym, gestosc, kolor=(1.0, 0.85, 0.65), anizo=0.6):
    m, nt, W = mat_nowy(nazwa)
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (*kolor, 1)
    pv.inputs["Density"].default_value = gestosc
    pv.inputs["Anisotropy"].default_value = anizo
    wyjscie(nt, pv.outputs[0], objetosc=True)
    bm = bmesh.new()
    pudlo(bm, (0, 0, -wym[2] / 2), wym)
    ob = siatka(nazwa, bm, m, loc=srodek)
    ob.visible_shadow = False
    return ob


M_ZLOTO = {}


def zloto(sila):
    """Złota emisja o danej sile (materiały współdzielone)."""
    if sila not in M_ZLOTO:
        M_ZLOTO[sila] = mat_swiatlo(f"Zloto_{sila}", ZLOTO, sila)
    return M_ZLOTO[sila]


def napis_ekran(cam, nazwa, tekst, x, y, px, kolor, kroj="georgia", odl=1.5):
    """Napis przypięty do kamery: (x, y) w pikselach kadru 1920×1080, px = wysokość pisma w pikselach."""
    s = G.skala_px(cam, odl)
    return G.napis(tekst, px * s, kolor, kroj, rodzic=cam, loc=G.ekran_na_kamerze(cam, x, y, odl), nazwa=nazwa, alfa=0.0,
                   obrys=((5, 7, 12), px * s * 0.035))


def krag_zodiaku(nazwa, R, mat, rodzic, grub=0.008, n=480):
    """Dwa cienkie okręgi i 12 + 60 kresek w płaszczyźnie XY obiektu `rodzic`. Zwraca (okrąg1, okrąg2, kreski)."""
    o1 = linia3d(nazwa + "1", okrag_pkt(R, n, math.radians(150)), grub, mat, True, rodzic)
    o2 = linia3d(nazwa + "2", okrag_pkt(R * 1.075, n, math.radians(330)), grub * 0.6, mat, True, rodzic)
    bm = bmesh.new()
    for i in range(72):
        a_ = 2 * math.pi * i / 72
        duza = i % 6 == 0
        r0, r1, w_ = R, R * (1.075 if duza else 1.028), grub * (2.2 if duza else 1.0)
        d_ = Vector((math.cos(a_), math.sin(a_), 0))
        t_ = Vector((-math.sin(a_), math.cos(a_), 0))
        bm.faces.new([bm.verts.new(d_ * r + t_ * s) for r, s in ((r0, -w_), (r1, -w_), (r1, w_), (r0, w_))])
    kr = siatka(nazwa + "Kreski", bm, mat)
    kr.parent = rodzic
    return o1, o2, kr


# ================================================================ 1. TYTUŁ I HOŁD (0–163)
O_TYT = Vector((18000, 0, 0))
B0, H0 = T["blysk"], T["hold"]
with Zestaw([(0, T["rysunki"])]):
    kamT, _ = kamera("K1_tytul", 0, [(0, O_TYT + Vector((0, -11.5, 0.30)), O_TYT + Vector((0, 0, 0.50))),
                                      (H0, O_TYT + Vector((0, -11.0, 0.34)), O_TYT + Vector((0, 0, 0.50))),
                                      (T["rysunki"], O_TYT + Vector((0, -10.1, 0.42)), O_TYT + Vector((0, 0, 0.46)))],
                      lens=50, fstop=2.0, interp="GLADKO")
    G.tlo_kamery(kamT, odl=70.0)
    # tytuł: przód świeci złotym gradientem (#fff6e0 → #f0c46f → #b47a22), fazy i boki to metaliczne złoto
    m, nt, W = mat_nowy("Tytul")
    gy = W.sep(W.coord("Generated"))[1]
    ramp = W._node("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.10, (*ZLOTO_C, 1)
    e[1].position, e[1].color = 0.92, (*ZLOTO_J, 1)
    e.new(0.52).color = (*ZLOTO, 1)
    W._in(ramp.inputs[0], gy)
    ox, oy, _ = W.sep(W.coord("Object"))
    blysk = W._node("ShaderNodeValue")
    blysk.name = "blysk"
    animuj(blysk.outputs[0], "default_value", [(B0 + 4, -4.4, "LINEAR"), (B0 + 40, 4.6, "CONSTANT"),
                                               (H0 + 44, -4.4, "LINEAR"), (H0 + 104, 4.6, "LINEAR")])
    pas = W.sub(1.0, W.smooth(0.0, 0.42, W.math("ABSOLUTE", W.sub(W.add(ox, W.mul(oy, 0.55)), blysk.outputs[0]))))
    kol = W.vadd(ramp.outputs[0], W.scale(W.vec(1.0, 0.92, 0.75), W.mul(pas, 1.3)))
    em = W._node("ShaderNodeEmission")
    W._in(em.inputs["Color"], kol)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = (*ZLOTO, 1)
    bs.inputs["Metallic"].default_value = 1.0
    bs.inputs["Roughness"].default_value = 0.28
    vt = W._node("ShaderNodeVectorTransform", vector_type="NORMAL", convert_from="WORLD", convert_to="OBJECT")
    W._in(vt.inputs[0], W._node("ShaderNodeNewGeometry").outputs["Normal"])
    przod = W.smooth(0.90, 0.985, W.sep(vt.outputs[0])[2])
    mx_ = W._node("ShaderNodeMixShader")
    W._in(mx_.inputs[0], przod)
    nt.links.new(bs.outputs[0], mx_.inputs[1])
    nt.links.new(em.outputs[0], mx_.inputs[2])
    wyjscie(nt, mx_.outputs[0])
    cu = bpy.data.curves.new("Tytul", "FONT")
    cu.body = "Uwierz we własny rozum"
    cu.font = G.font("georgiab")
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.size = 1.0
    tyt = bpy.data.objects.new("Tytul", cu)
    sc.collection.objects.link(tyt)
    bpy.context.view_layer.update()
    cu.size = 6.0 / tyt.dimensions.x
    cu.extrude = 0.035
    cu.bevel_depth = 0.010
    cu.bevel_resolution = 3
    cu.materials.append(m)
    tyt.rotation_euler = (math.pi / 2, 0, 0)
    animuj(tyt, "scale", [(B0 - 2, (1.14,) * 3), (B0 + 20, (1.0,) * 3), (H0, (1.0,) * 3), (H0 + 34, (0.60,) * 3)], "BEZIER")
    animuj(tyt, "location", [(H0, tuple(O_TYT + Vector((0, 0, 0.52)))), (H0 + 34, tuple(O_TYT + Vector((0, 0, 1.40))))], "BEZIER")
    lampa("TytulGora", "AREA", O_TYT + Vector((-2.5, -5.5, 5.0)), O_TYT, 2600.0, (1.0, 0.85, 0.6), 6.0)
    lampa("TytulDol", "AREA", O_TYT + Vector((3.5, -4.0, -3.5)), O_TYT, 900.0, (0.6, 0.72, 1.0), 5.0)

    # hołd: dwie linijki i złota kreska, w ciepłej poświacie
    def napis_tyt(nazwa, tekst, szer, kolor, z, a, b, kroj="georgia"):
        ob = G.napis(tekst, 1.0, kolor, kroj, loc=O_TYT + Vector((0, 0, z)), rot=(math.pi / 2, 0, 0), nazwa=nazwa, alfa=0.0)
        bpy.context.view_layer.update()
        ob.data.size = szer / ob.dimensions.x
        G.alfa_napisu(ob, [(a, 0.0), (b, 1.0)])
        animuj(ob, "location", [(a, tuple(O_TYT + Vector((0, 0, z - 0.08)))), (b + 14, tuple(O_TYT + Vector((0, 0, z))))], "BEZIER")
        return ob
    napis_tyt("Hold1", "w hołdzie śp.", 1.95, (250, 222, 160), 0.46, H0 + 8, H0 + 26)
    napis_tyt("Hold2", "Leszkowi Wiktorowi Klimkowi", 5.5, KREM, -0.16, H0 + 16, H0 + 38)
    bm = bmesh.new()
    pudlo(bm, (0, 0, -0.004), (1.0, 0.004, 0.008))
    kre = siatka("Kreska", bm, mat_swiatlo("Kreska_m", ZLOTO, 1.6), loc=O_TYT + Vector((0, 0, 0.92)))
    animuj(kre, "scale", [(H0 + 2, (0.0, 1, 1)), (H0 + 40, (3.0, 1, 1))], "BEZIER")
    # ciepła poświata za napisami
    m, nt, W = mat_nowy("Poswiata", przezroczysty=True)
    px_, _, pz_ = W.sep(W.coord("Object"))
    odl_ = W.math("SQRT", W.add(W.math("POWER", W.div(px_, 7.4), 2.0), W.math("POWER", W.div(pz_, 4.2), 2.0)))
    v_p = W._node("ShaderNodeValue")
    animuj(v_p.outputs[0], "default_value", [(H0 - 6, 0.0), (H0 + 46, 0.50), (T["rysunki"], 0.55)], "BEZIER")
    sh, _ = emisja(W, (1.0, 0.50, 0.17), 1.0, W.mul(W.math("POWER", W.sub(1.0, W.smooth(0.0, 1.0, odl_)), 2.6), v_p.outputs[0]))
    wyjscie(nt, sh)
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(p) for p in ((-7.6, 0, -4.4), (7.6, 0, -4.4), (7.6, 0, 4.4), (-7.6, 0, 4.4))])
    siatka("Poswiata", bm, m, loc=O_TYT + Vector((0, 1.6, 0.25))).visible_shadow = False
    # krąg zodiaku w tle
    zodT = bpy.data.objects.new("ZodiakT", None)
    zodT.location = O_TYT + Vector((0, 6.0, 0.45))
    zodT.rotation_euler = (math.radians(90 - 14), 0, 0)
    sc.collection.objects.link(zodT)
    M_ZT = mat_swiatlo("ZodiakT_m", ZLOTO, 0.0)
    animuj(sila_emisji(M_ZT), "default_value", [(B0, 2.2), (B0 + 36, 0.42), (T["rysunki"], 0.30)], "BEZIER")
    krag_zodiaku("ZodiakT", 5.0, M_ZT, zodT)
    animuj(zodT, "rotation_euler", [(0, 0.0), (T["rysunki"], math.radians(-12))], "LINEAR", index=2)
    # drobiny: fala od błysku (za napisem), potem unoszą się powoli jak iskry
    M_FALA = mat_punkty("Fala_m", ZLOTO, 1.0, migot=0.4)
    animuj(M_FALA.node_tree.nodes[M_FALA["sila"]].outputs[0], "default_value",
           [(B0, 22.0), (B0 + 28, 6.0), (H0 + 4, 3.0), (H0 + 34, 1.1), (T["rysunki"], 0.9)], "BEZIER")
    nf = 2600
    a_ = rng.uniform(0, 2 * math.pi, nf)
    r_ = 0.05 + 0.25 * rng.random(nf)
    pts = np.stack([r_ * np.cos(a_) * 2.2, 0.25 + np.abs(rng.normal(0, 0.30, nf)), r_ * np.sin(a_) * 0.7 + 0.03], axis=1)
    chmura("Fala", pts, rng.uniform(0.005, 0.016, nf) * (0.6 + 1.4 * rng.random(nf) ** 3), 0.2 + 1.8 * rng.random(nf) ** 2, M_FALA,
           loc=O_TYT + Vector((0, 0, 0.45)), szyb=1.2 + 8.5 * rng.random(nf) ** 1.4,
           ruch=dict(amp=0.10, skala=0.5, tempo=0.25, wybuch=dict(t0=B0 / FPS, k=1.9, g=-0.05)))
    pyl("PylTytul", 800, w_pudle(O_TYT + Vector((0, -1.5, 0.2)), (15, 15, 11)), mat_punkty("PylTytul_m", ZLOTO, 3.2, migot=0.4),
        prom=(0.005, 0.016), ruch=dict(v=(0.008, 0.0, 0.07), amp=0.09, skala=0.45, tempo=0.25))

# ================================================================ 2. RYSUNKI LESZKA (163–358)
O_RYS = Vector((12000, 0, 0))
RZEDY = [["tektonika.gif", "uskok.jpg", "17std3.jpg", "obliczenia.jpg"],
         ["masy1.jpg", "masy2.jpg", "masy3.jpg", "ollinstone.jpg", "ollin.gif"],
         ["temperatura.jpg", "stonehenge.jpg", "tikal.jpg", "absyda.jpg"]]
R0, U0 = T["rysunki"], T["uklad"]
with Zestaw([(R0, T["ziemia"])]):
    WYS, ODST = 1.5, 0.30                       # wysokość rysunku i odstęp w układzie końcowym
    Y_KAM, ODL_SIATKI = 1.2, 12.6
    Y_SIATKI = Y_KAM + ODL_SIATKI
    kamR, celR = kamera("K2_rysunki", R0, [(R0, O_RYS + Vector((0.5, -10.5, 0.25)), O_RYS + Vector((0.0, 2.0, 0.2))),
                                            ((R0 + U0) // 2, O_RYS + Vector((-0.35, -4.9, 0.05)), O_RYS + Vector((0.0, 8.0, 0.1))),
                                            (U0, O_RYS + Vector((0.0, 0.1, 0.0)), O_RYS + Vector((0, Y_SIATKI, 0.0))),
                                            (T["ziemia"], O_RYS + Vector((0, Y_KAM, 0.0)), O_RYS + Vector((0, Y_SIATKI, 0.0)))],
                           lens=35, interp="GLADKO")
    G.tlo_kamery(kamR, odl=80.0)
    M_RAMA = mat_swiatlo("Rama", ZLOTO, 1.25)
    panele = []
    for wiersz in RZEDY:
        for plik in wiersz:
            png = os.path.join(G.CACHE, "wstep2_" + os.path.splitext(plik)[0] + ".png")
            if not os.path.exists(png):      # trzykrotne powiększenie (lanczos), żeby małe rysunki nie były kanciaste
                subprocess.run([G.ffmpeg_exe(), "-loglevel", "error", "-y", "-i", os.path.join(G.RYSUNKI, plik), "-frames:v", "1",
                                "-filter_complex", "[0]scale=iw*3:ih*3:flags=lanczos,format=rgba[i];color=white:s=16x16[c];"
                                "[c][i]scale2ref[c2][i2];[c2][i2]overlay=shortest=1,format=rgb24", png], check=True)
            im = G.wczytaj_obraz(png)
            asp = im.size[0] / im.size[1]
            os_ = bpy.data.objects.new("Rys_" + plik, None)
            sc.collection.objects.link(os_)
            m, nt, W = mat_nowy("Rys_" + plik)
            tk, _ = W.obraz(im, W._node("ShaderNodeUVMap").outputs[0], "Cubic", "EXTEND")
            gl = W._node("ShaderNodeCameraData").outputs["View Z Depth"]
            sh, _ = emisja(W, tk, W.mul(0.86, W.sub(1.0, W.mul(W.smooth(9.0, 26.0, gl), 0.6))))
            wyjscie(nt, sh)
            bm = bmesh.new()
            uvl = bm.loops.layers.uv.new("UV")
            f_ = bm.faces.new([bm.verts.new((sx * asp * WYS / 2, sy * WYS / 2, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
            for lp, uv_ in zip(f_.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                lp[uvl].uv = uv_
            siatka("Obraz_" + plik, bm, m).parent = os_
            bm = bmesh.new()
            g_ = 0.055
            bm.faces.new([bm.verts.new((sx * (asp * WYS / 2 + g_), sy * (WYS / 2 + g_), -0.012)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
            siatka("Rama_" + plik, bm, M_RAMA).parent = os_
            panele.append((os_, asp))
    # układ końcowy: trzy wyśrodkowane rzędy
    cele, k = [], 0
    for j, wiersz in enumerate(RZEDY):
        szer = [panele[k + i][1] * WYS for i in range(len(wiersz))]
        x = -(sum(szer) + ODST * (len(wiersz) - 1)) / 2
        for i in range(len(wiersz)):
            cele.append(Vector((x + szer[i] / 2, Y_SIATKI, 0.42 + (1 - j) * (WYS + ODST))))
            x += szer[i] + ODST
        k += len(wiersz)
    # położenia w locie: rozsiane wzdłuż toru kamery, na przemian po lewej i prawej
    n_p = len(panele)
    kolej = rng.permutation(n_p)
    for nr, idx in enumerate(kolej):
        os_, asp = panele[idx]
        strona = -1 if nr % 2 == 0 else 1
        y = -6.5 + 19.0 * nr / (n_p - 1)
        x = strona * rng.uniform(1.9, 4.2) * (0.8 + 0.5 * (y + 6.5) / 19.0)
        z = rng.uniform(-1.9, 2.1)
        p0 = Vector((x, y, z))
        r0 = Vector((math.pi / 2 + math.radians(rng.uniform(-9, 9)), math.radians(rng.uniform(-7, 7)),
                     -strona * math.radians(rng.uniform(10, 32))))
        p1 = p0 + Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.2, 0.5), rng.uniform(-0.3, 0.3)))
        r1 = r0 + Vector((math.radians(rng.uniform(-5, 5)), math.radians(rng.uniform(-4, 4)), math.radians(rng.uniform(-7, 7))))
        ta = U0 - 14 + int(14 * nr / (n_p - 1))             # kolejne rysunki ruszają na miejsce co ok. 1 klatkę
        tb = ta + 24
        animuj(os_, "location", [(R0, tuple(O_RYS + p0), "LINEAR"), (ta, tuple(O_RYS + p0.lerp(p1, (ta - R0) / (U0 - R0))), "BEZIER"),
                                 (tb, tuple(O_RYS + cele[idx]), "BEZIER")])
        animuj(os_, "rotation_euler", [(R0, tuple(r0), "LINEAR"), (ta, tuple(r0.lerp(r1, (ta - R0) / (U0 - R0))), "BEZIER"),
                                       (tb, (math.pi / 2, 0, 0), "BEZIER")])
    adr = napis_ekran(kamR, "AdresRys", "uleszka.net  ·  2004–2007", 960, 985, 54, G.ZLOTY)
    G.alfa_napisu(adr, [(T["adres"], 0.0), (T["adres"] + 22, 1.0)])
    pyl("PylRys", 2200, w_pudle(O_RYS + Vector((0, 4, 0)), (22, 34, 12)), mat_punkty("PylRys_m", ZLOTO, 3.4, migot=0.4),
        prom=(0.005, 0.016), ruch=dict(v=(0.01, 0.0, 0.03), amp=0.10, skala=0.4, tempo=0.25))

# ================================================================ 3. ZIEMIA Z ORBITY I ODPŁYNIĘCIE (358–750)
Z0, P0 = T["ziemia"], T["odplyw"]
KONIEC = KLATEK - 1
R_GW = 600.0
OS_Z = Vector((0, 0, 1))


def podnies(a, h, kat):
    """Obraca wektor a wokół poziomej osi h o kąt `kat` tak, żeby poszedł w górę."""
    v = Matrix.Rotation(kat, 3, h) @ a
    return v if v.z > a.z else Matrix.Rotation(-kat, 3, h) @ a


def odl_kam(f):
    if f <= P0:
        return 1.95 + 0.10 * (f - Z0) / (P0 - Z0)
    return 2.05 + (6.3 - 2.05) * G.gladko5((f - P0) / (KONIEC - P0))


def rho(f):
    return math.asin(1.0 / odl_kam(f))


def _lin(f, pkt):
    for (f0, v0), (f1, v1) in zip(pkt, pkt[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * (f - f0) / (f1 - f0)
    return pkt[-1][1]


# kamera wisi nad szerokością 52°N; Słońce stoi tuż za krawędzią tarczy, na lewo od środka kadru
U_REF = Vector((math.cos(math.radians(52)), 0, math.sin(math.radians(52))))
A_REF = -U_REF
H_REF = A_REF.cross(OS_Z).normalized()
_b = podnies(A_REF, H_REF, rho(T["slonce"]))
_widok = podnies(A_REF, H_REF, rho(T["slonce"]) + math.radians(7.5))
_prawo = _widok.cross(OS_Z).normalized()
S_W = Matrix.Rotation(math.radians(26), 3, A_REF) @ _b
if S_W.dot(_prawo) > 0:
    S_W = Matrix.Rotation(math.radians(-26), 3, A_REF) @ _b
N_OBR = A_REF.cross(S_W).normalized()


def theta(f):
    """Odstęp kątowy Słońca od środka Ziemi widziany z kamery: do `odplyw` Słońce powoli wschodzi nad krawędź."""
    if f <= P0:
        return rho(f) + math.radians(_lin(f, [(Z0, -1.0), (T["slonce"], 0.0), (T["lektor"], 1.0), (P0, 2.1)]))
    return rho(P0) + math.radians(2.1 + 9.0 * (f - P0) / (KONIEC - P0))


def kier_kam(f):
    d = theta(f) - rho(T["slonce"])
    u = Matrix.Rotation(d, 3, N_OBR) @ U_REF
    if abs((-u).angle(S_W) - theta(f)) > 1e-4:
        u = Matrix.Rotation(-d, 3, N_OBR) @ U_REF
    return u


def psi(f):
    """Kąt, o jaki kamera patrzy ponad środek Ziemi: najpierw krawędź nisko w kadrze, na końcu Ziemia prawie w środku."""
    w = G.gladko5((f - P0) / (KONIEC - P0))
    return rho(f) + math.radians(7.5) - w * (rho(f) + math.radians(6.2))


with Zestaw([(Z0, KLATEK)]):
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.0045, 0.0075, 0.020, 1)
    ziemia = G.sfera_uv("Ziemia", 256, 128, 1.0)
    m, nt, W = mat_nowy("Ziemia")
    uv = W._node("ShaderNodeUVMap").outputs[0]
    tk, _ = W.obraz(G.wczytaj_obraz(os.path.join(G.DANE, "blue-marble", "blue-marble-2002-8192x4096.jpg")), uv, "Cubic")
    nrm = W._node("ShaderNodeNewGeometry").outputs["Normal"]
    ns = W.dot(nrm, tuple(S_W))
    dzien = W.smooth(-0.10, 0.45, ns)
    zmierzch = W.mul(W.smooth(-0.30, 0.02, ns), W.sub(1.0, W.smooth(0.02, 0.40, ns)))
    noc = W.scale(W.vmath("MULTIPLY", tk, (0.55, 0.75, 1.25)), 0.085)       # poświata: nocna strona widoczna na ok. 8%
    kol = W.vadd(W.vadd(noc, W.scale(tk, W.mul(dzien, 1.22))),
                 W.scale(W.vmath("MULTIPLY", tk, (1.0, 0.45, 0.12)), W.mul(zmierzch, 0.9)))
    sh, _ = emisja(W, kol, 1.0)
    wyjscie(nt, sh)
    ziemia.data.materials.append(m)
    ziemia.rotation_mode = "QUATERNION"
    q_poch = Quaternion((0, 1, 0), math.radians(-28))
    animuj(ziemia, "rotation_quaternion", [(Z0, tuple(q_poch @ Quaternion((0, 0, 1), math.radians(-20)))),
                                           (KONIEC, tuple(q_poch @ Quaternion((0, 0, 1), math.radians(-8))))], "LINEAR")

    # atmosfera: powłoka świecąca przy krawędzi tarczy, po stronie dziennej i w pasie zmierzchu
    m, nt, W = mat_nowy("Atmosfera", przezroczysty=True)
    lw = W._node("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    fc = lw.outputs["Facing"]
    F0 = 1 - math.sqrt(1 - (1 / 1.06) ** 2)
    obw = W.mul(W.smooth(F0 * 0.35, F0, fc), W.sub(1.0, W.smooth(F0, 0.98, fc)))
    nrm = W._node("ShaderNodeNewGeometry").outputs["Normal"]
    ns = W.dot(nrm, tuple(S_W))
    dz = W.smooth(-0.42, 0.22, ns)
    zm = W.mul(W.smooth(-0.45, -0.05, ns), W.sub(1.0, W.smooth(-0.05, 0.40, ns)))
    kol = W.mixv(zm, (0.30, 0.55, 1.0), (1.0, 0.55, 0.22))
    alfa = W.math("MINIMUM", W.mul(W.math("POWER", obw, 2.0), W.mul(dz, 0.95)), 1.0)
    sh, _ = emisja(W, kol, 2.0, alfa)
    wyjscie(nt, sh)
    kula("Atmosfera", 1.06, (0, 0, 0), m, seg=128, cien=False)

    kula("Slonce", 3.2, S_W * 500.0, mat_swiatlo("Slonce", (1.0, 0.86, 0.62), 260.0), cien=False)

    # gwiazdy z katalogu HYG (do 6 mag) + słabsze tło
    P, R_, J_, K_ = [], [], [], []
    with open(os.path.join(G.DANE, "hyg", "gwiazdy_mag6.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ra, de, mag = math.radians(float(row["ra_h"]) * 15), math.radians(float(row["dec_deg"])), float(row["mag"])
            ci = float(row["ci"]) if row["ci"] else 0.6
            P.append((math.cos(de) * math.cos(ra), math.cos(de) * math.sin(ra), math.sin(de)))
            R_.append(0.45 + 0.42 * max(0.0, 4.5 - mag))
            J_.append(min(22.0, 2.2 * 2.512 ** (0.62 * (4.6 - mag))))
            t_ = min(1.0, max(0.0, (ci + 0.3) / 1.9))
            K_.append((0.72 + 0.28 * min(1, 2 * t_), 0.82 + 0.18 * (1 - abs(2 * t_ - 1)), 1.0 - 0.52 * max(0, 2 * t_ - 1), 1))
    nt_ = 9000
    v = rng.normal(size=(nt_, 3))
    v /= np.linalg.norm(v, axis=1)[:, None]
    P = np.vstack([np.asarray(P), v]) * R_GW
    R_ = np.r_[R_, rng.uniform(0.24, 0.40, nt_)]
    J_ = np.r_[J_, 0.5 + 1.4 * rng.random(nt_) ** 3]
    K_ = np.vstack([np.asarray(K_), np.tile((0.85, 0.9, 1.0, 1.0), (nt_, 1))])
    chmura("Gwiazdy", P, R_, J_, mat_punkty("Gwiazdy", None, 1.0, migot=0.25), kol=K_)

    def _powloka(n):
        v = rng.normal(size=(n, 3))
        v /= np.linalg.norm(v, axis=1)[:, None]
        return v * rng.uniform(2.6, 9.0, n)[:, None]
    pyl("PylKosmos", 420, _powloka, mat_punkty("PylKosmos", ZLOTO, 3.2, migot=0.35), prom=(0.002, 0.006))

    # kamera: klucze co 3 klatki z toru policzonego wyżej
    kl = []
    for f in sorted(set(list(range(Z0, KONIEC, 3)) + [KONIEC])):
        u = kier_kam(f)
        a = -u
        h = a.cross(OS_Z).normalized()
        c = u * odl_kam(f)
        kl.append((f, c, c + podnies(a, h, psi(f)) * 10.0))
    kamZ, _ = kamera("K3_ziemia", Z0, kl, lens=35, interp="GLADKO")

    # złoty krąg zodiaku wokół Ziemi rysuje się, gdy kamera odpływa
    u_k = kier_kam(KONIEC)
    h_k = (-u_k).cross(OS_Z).normalized()
    n_r = Matrix.Rotation(math.radians(16), 3, u_k) @ (Matrix.Rotation(math.radians(66), 3, h_k) @ u_k)
    zodZ = bpy.data.objects.new("ZodiakZ", None)
    sc.collection.objects.link(zodZ)
    zodZ.rotation_mode = "QUATERNION"
    zodZ.rotation_quaternion = OS_Z.rotation_difference(n_r)
    M_ZZ = mat_swiatlo("ZodiakZ_m", ZLOTO, 3.0)
    M_ZZK = mat_swiatlo("ZodiakZK_m", ZLOTO, 0.0)
    z1, z2, _kr = krag_zodiaku("ZodiakZ", 1.62, M_ZZ, zodZ, grub=0.0042, n=600)
    _kr.data.materials[0] = M_ZZK
    for o_, a_, b_ in ((z1, P0 + 4, P0 + 74), (z2, P0 + 14, P0 + 84)):
        animuj(o_.data, "bevel_factor_end", [(a_, 0.003), (b_, 1.0)], "BEZIER")
        widok(o_, [(a_, KLATEK)])
    widok(_kr, [(P0 + 30, KLATEK)])
    animuj(sila_emisji(M_ZZK), "default_value", [(P0 + 30, 0.0), (P0 + 95, 2.4)], "BEZIER")

    lek = napis_ekran(kamZ, "Lektor", "lektor: głos wygenerowany przez AI", 960, 1010, 38, (240, 232, 214), odl=0.4)
    G.alfa_napisu(lek, [(T["lektor"], 0.0), (T["lektor"] + 18, 1.0), (P0 - 4, 1.0), (P0 + 22, 0.0)])

# ================================================================ widoczność obiektów w ujęciach
for nazwa, zakresy in WIDOK.items():
    ob = bpy.data.objects[nazwa]
    if ob.type == "CAMERA" or ob.type == "EMPTY":
        continue
    d = {0: True}
    for a, b in zakresy:
        d[a] = False
    for a, b in zakresy:
        if b < KLATEK and b not in [z[0] for z in zakresy]:
            d[b] = True
    animuj(ob, "hide_render", sorted(d.items()), "CONSTANT")

# ================================================================ kompozycja: poświata, smugi, winieta, błysk, przyciemnienia na cięciach
ng = bpy.data.node_groups.new("Kompozycja", "CompositorNodeTree")
ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = ng.nodes.new("CompositorNodeRLayers")
rl.scene = sc


def kn(typ, obraz, **gniazda):
    n = ng.nodes.new(typ)
    ng.links.new(obraz, n.inputs["Image"])
    for k, v in gniazda.items():
        n.inputs[k.replace("_", " ")].default_value = v
    return n


n_bloom = kn("CompositorNodeGlare", rl.outputs["Image"], Type="Bloom", Quality="High", Threshold=1.0, Smoothness=0.6,
             Strength=0.55, Saturation=1.0, Size=0.62)
n_smugi = kn("CompositorNodeGlare", n_bloom.outputs["Image"], Type="Streaks", Quality="Medium", Threshold=22.0, Smoothness=0.2,
             Strength=0.3, Streaks=6, Streaks_Angle=math.radians(12), Iterations=4, Fade=0.95, Color_Modulation=0.2)
n_lens = kn("CompositorNodeLensdist", n_smugi.outputs["Image"], Dispersion=0.012)
el = ng.nodes.new("CompositorNodeEllipseMask")
el.inputs["Size"].default_value = (0.92, 0.86)
bl = ng.nodes.new("CompositorNodeBlur")
ng.links.new(el.outputs[0], bl.inputs["Image"])
bl.inputs["Size"].default_value = (260.0 * opcje["skala"] / 100, 260.0 * opcje["skala"] / 100)
mr = ng.nodes.new("ShaderNodeMapRange")
ng.links.new(bl.outputs[0], mr.inputs[0])
mr.inputs[3].default_value, mr.inputs[4].default_value = 0.42, 1.0
win = ng.nodes.new("ShaderNodeMix")
win.data_type, win.blend_type = "RGBA", "MULTIPLY"
win.inputs["Factor"].default_value = 1.0
ng.links.new(n_lens.outputs["Image"], win.inputs["A"])
ng.links.new(mr.outputs[0], win.inputs["B"])
n_eksp = kn("CompositorNodeExposure", win.outputs["Result"], Exposure=0.0)
blysk_k = ng.nodes.new("ShaderNodeMix")
blysk_k.data_type, blysk_k.blend_type = "RGBA", "ADD"
blysk_k.inputs["Factor"].default_value = 0.0
blysk_k.inputs["B"].default_value = (1.0, 0.84, 0.55, 1)
ng.links.new(n_eksp.outputs["Image"], blysk_k.inputs["A"])
fade = ng.nodes.new("ShaderNodeMix")
fade.data_type = "RGBA"
fade.inputs["A"].default_value = (0, 0, 0, 1)
ng.links.new(blysk_k.outputs["Result"], fade.inputs["B"])
out = ng.nodes.new("NodeGroupOutput")
ng.links.new(fade.outputs["Result"], out.inputs[0])
sc.compositing_node_group = ng
sc.render.use_compositing = True
try:
    sc.render.compositor_device = "GPU"
except Exception:
    pass

animuj(n_eksp.inputs["Exposure"], "default_value", [(0, 0.0), (B0 - 1, 1.2), (B0 + 1, 1.8), (B0 + 5, 1.0), (B0 + 12, 0.4),
                                                    (B0 + 26, 0.0), (KONIEC, 0.0)], "LINEAR")
animuj(blysk_k.inputs["Factor"], "default_value", [(0, 0.0), (B0 - 2, 0.0), (B0 + 1, 0.85), (B0 + 4, 0.42), (B0 + 9, 0.0),
                                                   (KONIEC, 0.0)], "LINEAR")
fk = [(0, 0.0), (max(1, B0 - 3), 0.0), (B0 + 2, 1.0)]
for c, po in ((R0, 12), (Z0, 16)):                 # cięcia przez krótkie przyciemnienie
    fk += [(c - 9, 1.0), (c - 1, 0.03), (c, 0.03), (c + po, 1.0)]
fk += [(KONIEC, 1.0)]
animuj(fade.inputs["Factor"], "default_value", fk, "LINEAR")


# ================================================================ render
def ffmpeg(*a):
    subprocess.run([G.ffmpeg_exe(), "-loglevel", "error", "-y", *a], check=True)


def zloz():
    brak = [f for f in range(KLATEK) if not os.path.exists(os.path.join(KLATKI_DIR, f"k_{f:04d}.png"))]
    if brak:
        raise SystemExit(f"[zloz] brakuje {len(brak)} klatek, np. {brak[:5]}")
    mp4 = os.path.join(TU, "klip.mp4")
    ffmpeg("-framerate", str(FPS), "-start_number", "0", "-i", os.path.join(KLATKI_DIR, "k_%04d.png"),
           "-frames:v", str(KLATEK), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           "-preset", "slow", "-an", "-movflags", "+faststart", mp4)
    ffmpeg("-i", os.path.join(KLATKI_DIR, f"k_{KADR:04d}.png"), "-vf", "scale=1600:-2", "-q:v", "2", os.path.join(TU, "kadr.jpg"))
    print("[zloz]", mp4)


def blokada_zajmij():
    blok = os.path.join(G.WIDEO, ".renderuje")
    while True:
        try:
            fd = os.open(blok, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, (NAZWA + "\n").encode())
            os.close(fd)
            return blok
        except FileExistsError:
            try:
                kto = open(blok, encoding="utf-8", errors="replace").read().strip()
            except OSError:
                kto = "?"
            if kto == NAZWA:
                return blok
            if not opcje["czekaj"]:
                raise SystemExit(f"[render] karta zajęta: {blok} ({kto}) – spróbuj później albo dodaj --czekaj")
            print(f"[render] czekam na kartę ({kto})", flush=True)
            time.sleep(20)


os.makedirs(KLATKI_DIR, exist_ok=True)
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
if opcje["zloz"]:
    zloz()
elif opcje["proba"]:
    for f in opcje["proba"]:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(KLATKI_DIR, f"proba_{f:04d}.png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"[proba] {f} kamera {sc.camera.name} {time.time() - t0:.1f} s", flush=True)
else:
    blok = None if opcje["bez_blokady"] else blokada_zajmij()
    t0 = time.time()
    try:
        sc.frame_start, sc.frame_end = opcje["od"], opcje["do"]
        sc.render.filepath = os.path.join(KLATKI_DIR, "k_")
        bpy.ops.render.render(animation=True)
    finally:
        if blok and os.path.exists(blok):
            os.remove(blok)
    with open(os.path.join(KLATKI_DIR, "czas_renderu.txt"), "a", encoding="utf-8") as f:
        f.write(f"render klatek {opcje['od']}-{opcje['do']}: {time.time() - t0:.0f} s\n")
    print(f"[render] {time.time() - t0:.0f} s", flush=True)
    if opcje["od"] == 0 and opcje["do"] == KLATEK - 1:
        zloz()
