# -*- coding: utf-8 -*-
"""
Wstęp odcinka, WERSJA B: sceny i dynamika dawnej czołówki dopasowane do zapowiedzi lektora
(30 s, 750 klatek, 25 kl./s, bez dźwięku). Wersja A to `../scena.py` i `../klip.mp4`.

    0–172  z ciemności złoty błysk i tytuł „Uwierz we własny rozum”; od kl. 47 spokojny kadr hołdu:
           „w hołdzie śp. Leszkowi Wiktorowi Klimkowi” w ciepłej poświacie
  172–358  montaż cięty pod akcenty basu w nagraniu (6,86 / 9,14 / 10,95 / 12,88 s):
           Ziemia ze złotymi równikami (dzisiejszym i dawnym) → Giza z pasem Oriona → Tikal → Kamień Słońca
  358–625  Stonehenge o wschodzie Słońca: kamienie nisko w kadrze, środek pusty na tytuł odcinka
           (nakłada go `scripts/wideo.ts`); na kl. 422 (akcent 16,9 s) Słońce wchodzi w szczelinę wielkiego trylitu
  625–750  kamera odpływa w górę i w tył; ostatnia klatka: krąg z lotu ptaka, Słońce nad horyzontem, gwiazdy

Małe napisy („uleszka.net · 2004–2007” i „lektor: głos wygenerowany przez AI”) dokłada ffmpeg przy składaniu klipu,
bo kamery montażu mają głębię ostrości. Momenty są w słowniku T na górze pliku (numery klatek filmu od 0).

Uruchomienie (bez okna), z katalogu repozytorium:
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/wstep/wersja-b/scena.py
  ... -- --proba 40,110,200,250,300,340,450,749 [--skala 50]   tylko kadry próbne PNG do _klatki/
  ... -- --od 358 --do 749                 render części klatek (bez składania mp4)
  ... -- --czekaj                          czeka, aż zniknie blokada .renderuje
  ... -- --zloz                            tylko składa klip.mp4 i kadr.jpg z gotowych klatek
  ... -- --podglad <nagranie.mp3>          podglad.mp4: klip + pierwsze 30 s nagrania + przykładowy tytuł odcinka
"""
import bpy, bmesh, math, os, sys, csv, time, subprocess, random
import numpy as np
from mathutils import Vector, Matrix, Quaternion, noise

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "..", "_wspolne"))
import globus as G
from wezly import Wezly

KLATKI_DIR = os.path.join(TU, "_klatki")
NAZWA = "wstep-b"
KLATEK, FPS = 750, 25

# ---------------------------------------------------------------- CZAS (klatki filmu, od 0)
# Mowa: zapowiedź odcinka 2 (`../PLAN.md`). Muzyka: skoki basu (<90 Hz) zmierzone na pierwszych 30 s nagrania
# odcinka 2: 6,86 / 9,14 / 10,34 / 10,95 / 11,38 / 12,88 / 13,51 / 16,89 / 18,24 / 19,13 / 20,36 / 25,47 s.
T = dict(
    blysk=4,        # 0,0 s „Uwierz we własny rozum.” – złoty błysk i wejście tytułu
    hold=47,        # 1,9 s „Podcast w hołdzie świętej pamięci Leszkowi Wiktorowi Klimkowi.”
    montaz=172,     # 6,86 s akcent basu (mowa „Jego teksty ze strony uleszka.net…” od 6,5 s): Ziemia ze złotymi równikami
    adres=196,      # napis „uleszka.net · 2004–2007”
    giza=229,       # 9,14 s akcent: Giza i pas Oriona
    tikal=274,      # 10,95 s akcent: Tikal
    kamien=322,     # 12,88 s akcent („czytane bez zmian.” od 12,7 s): Kamień Słońca
    stone=358,      # 14,3 s „Odcinek …”: Stonehenge; do `odplyw` środek kadru pusty na tytuł odcinka
    slonce=422,     # 16,89 s akcent: Słońce wchodzi w szczelinę
    lektor=500,     # 20,0 s „Czyta lektor wygenerowany przez sztuczną inteligencję.” (akcent 20,36 s)
    odplyw=625,     # 25 s koniec mowy, muzyka wygasa – kamera odpływa
)
C = dict(giza=T["giza"], tikal=T["tikal"], kamien=T["kamien"], stone=T["stone"])
# Przejście Kamień Słońca → Stonehenge: od PRZ0 kamera najeżdża na twarz Słońca i rozlewa się z niej złote światło,
# na cięciu wypełnia kadr, do PRZ1 zbiega się do łuny nad horyzontem Stonehenge.
PRZ0, PRZ1 = T["stone"] - 12, T["stone"] + 22
PRZ_MIEKKOSC = 0.5          # rozmycie brzegu światła jako ułamek jego średnicy
PRZ_HORYZONT = 0.23         # wysokość łuny w Stonehenge jako ułamek wysokości kadru, liczona od dołu
KADR = 250          # klatka na kadr.jpg (Giza)

ZLOTO = G.srgb(G.ZLOTY)[:3]                    # #f0c46f liniowo
ZLOTO_J = G.srgb((255, 246, 224))[:3]          # #fff6e0
ZLOTO_C = G.srgb((180, 122, 34))[:3]           # #b47a22
KREM = (243, 234, 216)


def argumenty():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = {"proba": None, "skala": 100, "od": 0, "do": KLATEK - 1, "czekaj": False, "zloz": False, "bez_blokady": False,
         "podglad": None}
    i = 0
    while i < len(a):
        if a[i] == "--proba":
            o["proba"] = [int(x) for x in a[i + 1].split(",")]; i += 2
        elif a[i] in ("--skala", "--od", "--do"):
            o[a[i][2:]] = int(a[i + 1]); i += 2
        elif a[i] == "--podglad":
            o["podglad"] = a[i + 1]; i += 2
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
with Zestaw([(0, T["montaz"])]):
    kamT, _ = kamera("K1_tytul", 0, [(0, O_TYT + Vector((0, -11.5, 0.30)), O_TYT + Vector((0, 0, 0.50))),
                                      (H0, O_TYT + Vector((0, -11.0, 0.34)), O_TYT + Vector((0, 0, 0.50))),
                                      (T["montaz"], O_TYT + Vector((0, -10.1, 0.42)), O_TYT + Vector((0, 0, 0.46)))],
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
    animuj(v_p.outputs[0], "default_value", [(H0 - 6, 0.0), (H0 + 46, 0.50), (T["montaz"], 0.55)], "BEZIER")
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
    animuj(sila_emisji(M_ZT), "default_value", [(B0, 2.2), (B0 + 36, 0.42), (T["montaz"], 0.30)], "BEZIER")
    krag_zodiaku("ZodiakT", 5.0, M_ZT, zodT)
    animuj(zodT, "rotation_euler", [(0, 0.0), (T["montaz"], math.radians(-12))], "LINEAR", index=2)
    # drobiny: fala od błysku (za napisem), potem unoszą się powoli jak iskry
    M_FALA = mat_punkty("Fala_m", ZLOTO, 1.0, migot=0.4)
    animuj(M_FALA.node_tree.nodes[M_FALA["sila"]].outputs[0], "default_value",
           [(B0, 22.0), (B0 + 28, 6.0), (H0 + 4, 3.0), (H0 + 34, 1.1), (T["montaz"], 0.9)], "BEZIER")
    nf = 2600
    a_ = rng.uniform(0, 2 * math.pi, nf)
    r_ = 0.05 + 0.25 * rng.random(nf)
    pts = np.stack([r_ * np.cos(a_) * 2.2, 0.25 + np.abs(rng.normal(0, 0.30, nf)), r_ * np.sin(a_) * 0.7 + 0.03], axis=1)
    chmura("Fala", pts, rng.uniform(0.005, 0.016, nf) * (0.6 + 1.4 * rng.random(nf) ** 3), 0.2 + 1.8 * rng.random(nf) ** 2, M_FALA,
           loc=O_TYT + Vector((0, 0, 0.45)), szyb=1.2 + 8.5 * rng.random(nf) ** 1.4,
           ruch=dict(amp=0.10, skala=0.5, tempo=0.25, wybuch=dict(t0=B0 / FPS, k=1.9, g=-0.05)))
    pyl("PylTytul", 800, w_pudle(O_TYT + Vector((0, -1.5, 0.2)), (15, 15, 11)), mat_punkty("PylTytul_m", ZLOTO, 3.2, migot=0.4),
        prom=(0.005, 0.016), ruch=dict(v=(0.008, 0.0, 0.07), amp=0.09, skala=0.45, tempo=0.25))

# ================================================================ 2. ZIEMIA ZE ZŁOTYMI RÓWNIKAMI (172–229)
E0, E1 = T["montaz"], T["giza"]
AKPATOK = G.ll2xyz(60.0, -70.0)          # biegun sprzed ok. 12 000 lat według tabeli Leszka (wyspa Akpatok)
EKL = math.radians(23.44)
R_GW = 600.0
LAT_K, LON_K, PHI_K = 16.0, -42.0, 80.0


def kier_kam(phi):
    return G.ll2xyz(LAT_K, LON_K + (PHI_K - phi))


def odl_kam(f):
    return 5.3 - 1.2 * (f - E0) / (E1 - E0)


_sep = math.asin(1.0 / odl_kam(E0 + 3))                          # Słońce staje na krawędzi tarczy 3 klatki po cięciu
PHI_S = math.degrees(2 * math.asin(math.sin(_sep / 2) / math.cos(math.radians(LAT_K))))


def phi_kam(f):
    x = (f - E0) / (E1 - E0)
    return PHI_S - 0.9 + (52.0 - PHI_S) * (0.35 * x + 0.65 * x * x)


S_A = -kier_kam(0.0)                                             # kierunek ku Słońcu: dokładnie za Ziemią na początku toru

with Zestaw([(E0, E1)]):
    ziemia = G.sfera_uv("Ziemia", 256, 128, 1.0)
    m, nt, W = mat_nowy("Ziemia")
    uv = W._node("ShaderNodeUVMap").outputs[0]
    tk, _ = W.obraz(G.wczytaj_obraz(os.path.join(G.DANE, "blue-marble", "blue-marble-2002-8192x4096.jpg")), uv, "Cubic")
    nrm = W._node("ShaderNodeNewGeometry").outputs["Normal"]
    ns = W.dot(nrm, tuple(S_A))
    dzien = W.smooth(-0.10, 0.45, ns)
    zmierzch = W.mul(W.smooth(-0.30, 0.02, ns), W.sub(1.0, W.smooth(0.02, 0.40, ns)))
    noc = W.scale(W.vmath("MULTIPLY", tk, (0.55, 0.75, 1.25)), 0.085)       # poświata: nocna strona widoczna na ok. 8%
    kol = W.vadd(W.vadd(noc, W.scale(tk, W.mul(dzien, 1.22))),
                 W.scale(W.vmath("MULTIPLY", tk, (1.0, 0.45, 0.12)), W.mul(zmierzch, 0.9)))
    sh, _ = emisja(W, kol, 1.0)
    wyjscie(nt, sh)
    ziemia.data.materials.append(m)
    animuj(ziemia, "rotation_euler", [(E0, math.radians(-3)), (E1, 0.0)], "LINEAR", index=2)

    m, nt, W = mat_nowy("Atmosfera", przezroczysty=True)
    lw = W._node("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    fc = lw.outputs["Facing"]
    F0 = 1 - math.sqrt(1 - (1 / 1.06) ** 2)
    obw = W.mul(W.smooth(F0 * 0.35, F0, fc), W.sub(1.0, W.smooth(F0, 0.98, fc)))
    nrm = W._node("ShaderNodeNewGeometry").outputs["Normal"]
    ns = W.dot(nrm, tuple(S_A))
    dz = W.smooth(-0.42, 0.22, ns)
    zm = W.mul(W.smooth(-0.45, -0.05, ns), W.sub(1.0, W.smooth(-0.05, 0.40, ns)))
    kol = W.mixv(zm, (0.30, 0.55, 1.0), (1.0, 0.55, 0.22))
    alfa = W.math("MINIMUM", W.mul(W.math("POWER", obw, 2.0), W.mul(dz, 0.95)), 1.0)
    sh, _ = emisja(W, kol, 2.0, alfa)
    wyjscie(nt, sh)
    kula("Atmosfera", 1.06, (0, 0, 0), m, seg=96, cien=False)

    # dwa równiki na skorupie: dzisiejszy i dawny (90° od Akpatok), rozbłyskują zaraz po cięciu
    M_ROW = mat_swiatlo("Rownik", ZLOTO, 4.0)
    M_ROW2 = mat_swiatlo("RownikDawny", (1.0, 0.86, 0.60), 4.0)
    rownik = linia3d("Rownik", okrag_pkt(1.004, 360, math.radians(-60)), 0.0042, M_ROW, True, ziemia)
    u_ = AKPATOK.cross(Vector((0, 0, 1))).normalized()
    v_ = AKPATOK.cross(u_).normalized()
    rownik_d = linia3d("RownikDawny", okrag_pkt(1.004, 360, math.radians(150), u_, v_), 0.0034, M_ROW2, True, ziemia)
    for ob_, f0 in ((rownik, E0 + 4), (rownik_d, E0 + 9)):
        animuj(ob_.data, "bevel_factor_end", [(f0, 0.004), (f0 + 24, 1.0)], "BEZIER")
        widok(ob_, [(f0, E1)])
    for mm in (M_ROW, M_ROW2):
        animuj(sila_emisji(mm), "default_value", [(E0 + 4, 16.0), (E0 + 32, 4.5), (E1, 4.0)], "BEZIER")
    for nz, p_ in (("BiegunDawny", AKPATOK), ("BiegunDzis", Vector((0, 0, 1)))):
        a_ = p_.orthogonal().normalized()
        b_ = p_.cross(a_).normalized()
        o_ = linia3d(nz, okrag_pkt(0.035, 48, 0, a_, b_, p_ * 1.004), 0.003, M_ROW2 if "Dawny" in nz else M_ROW, True, ziemia)
        animuj(o_.data, "bevel_factor_end", [(E0 + 18, 0.01), (E0 + 32, 1.0)], "BEZIER")
        widok(o_, [(E0 + 18, E1)])

    kula("Slonce", 3.2, S_A * 500.0, mat_swiatlo("Slonce", (1.0, 0.86, 0.62), 260.0), cien=False)
    zod = bpy.data.objects.new("Zodiak", None)
    sc.collection.objects.link(zod)
    zod.rotation_euler = (-EKL, 0, 0)
    krag_zodiaku("Zodiak", 8.0, mat_swiatlo("ZodiakLinia", ZLOTO, 3.0), zod, grub=0.012, n=720)
    animuj(zod, "rotation_euler", [(E0, 0.0), (E1, math.radians(5))], "LINEAR", index=2)

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
        return v * rng.uniform(1.6, 7.5, n)[:, None]
    pyl("PylKosmos", 520, _powloka, mat_punkty("PylKosmos", ZLOTO, 3.5, migot=0.35), prom=(0.002, 0.006))

    ostrosc0 = bpy.data.objects.new("Ostrosc0", None)
    sc.collection.objects.link(ostrosc0)
    kl = [(f, kier_kam(phi_kam(f)) * odl_kam(f), (0, 0, 0.04)) for f in sorted(set(list(range(E0, E1, 3)) + [E1]))]
    kamera("K2_ziemia", E0, kl, lens=35, fstop=2.8, interp="GLADKO", ostrosc=ostrosc0)

# ================================================================ 3. GIZA, jednostka = 10 m
O_GIZA = Vector((3000, 0, 0))
with Zestaw([(C["giza"], C["tikal"])]):
    J = 0.1
    CAL = 0.0254
    dx_ch, dy_ch = -13165.7 * CAL, -13931.5 * CAL                      # Chefren względem Cheopsa (Petrie 1883)
    dy_my = dy_ch - 15170.4 * CAL                                      # Mykerinos N–S (Petrie)
    dx_my = dx_ch + (31.128333 - 31.130972) * 111320 * math.cos(math.radians(29.975))   # E–W z Wikidata (CC0)
    PIR = [("Cheops", (0.0, 0.0), 230.33, 146.6), ("Chefren", (dx_ch, dy_ch), 215.25, 143.5), ("Mykerinos", (dx_my, dy_my), 104.6, 65.5)]
    cP = np.mean([p[1] for p in PIR], axis=0)
    S_G = Vector((-0.80, 0.52, 0.16)).normalized()
    kopula("NieboGiza", O_GIZA, 1300, (0.060, 0.045, 0.050), (0.006, 0.010, 0.026), S_G, sila_slonca=1.6, wykl=60)
    gwiazdy_kopuly("GwiazdyGiza", O_GIZA, 1250, 2200, mat_punkty("GwiazdyGiza_m", (0.9, 0.93, 1.0), 1.6, migot=0.3))
    kula("SlonceGiza", 14, O_GIZA + S_G * 1200, mat_swiatlo("SlonceGiza", (1.0, 0.75, 0.45), 60.0), cien=False)
    slonce_lampa("LampaGiza", S_G, 3.2, kat=2.0)
    lampa("WypelnienieGiza", "AREA", O_GIZA + Vector((80, -120, 60)), O_GIZA, 4.5e4, (0.50, 0.60, 1.0), 120)
    m_piasek = mat_pryncypialny("Piasek", (0.30, 0.19, 0.10), 0.95, wypuklosc=(0.6, 0.5))
    bm = bmesh.new()
    pudlo(bm, (0, 0, -1), (2400, 2400, 1))
    siatka("Pustynia", bm, m_piasek, loc=O_GIZA)
    m_pir = mat_pryncypialny("Piramida", (0.60, 0.42, 0.24), 0.85, wypuklosc=(9.0, 0.35))
    M_KONTUR = mat_swiatlo("KonturGiza", ZLOTO, 0.0)
    animuj(sila_emisji(M_KONTUR), "default_value", [(C["giza"], 14.0), (C["giza"] + 16, 3.4)], "BEZIER")
    M_PROMIEN = mat_nowy("PromienGiza", przezroczysty=True)
    sh, _ = emisja(M_PROMIEN[2], ZLOTO_J, 2.0, 0.22)
    wyjscie(M_PROMIEN[1], sh)
    M_ORION = mat_swiatlo("Orion", (0.80, 0.90, 1.0), 0.0)
    animuj(sila_emisji(M_ORION), "default_value", [(C["giza"], 240.0), (C["giza"] + 14, 70.0)], "BEZIER")
    for nazwa, (x, y), a, h in PIR:
        px, py = (x - cP[0]) * J, (y - cP[1]) * J
        r, hh = a / 2 * J, h * J
        bm = bmesh.new()
        vs = [bm.verts.new((sx * r, sy * r, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        top = bm.verts.new((0, 0, hh))
        for i in range(4):
            bm.faces.new((vs[i], vs[(i + 1) % 4], top))
        loc = O_GIZA + Vector((px, py, 0))
        siatka(nazwa, bm, m_pir, loc=loc)
        naroza = [Vector((sx * r, sy * r, 0.02)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        wierz = Vector((0, 0, hh + 0.02))
        for i in range(4):
            linia3d(f"{nazwa}_k{i}", [naroza[i], wierz], 0.045, M_KONTUR).location = loc
        linia3d(f"{nazwa}_kp", naroza, 0.04, M_KONTUR, True).location = loc
        gw = loc + Vector((0, 0, 30.0))
        kula(f"{nazwa}_gwiazda", 0.38, gw, M_ORION, seg=16, cien=False)
        linia3d(f"{nazwa}_promien", [loc + wierz, gw], 0.035, M_PROMIEN[0])
    mgla("MglaGiza", O_GIZA + Vector((0, 0, 45)), (700, 700, 92), 0.00062, (1.0, 0.78, 0.52), 0.7)
    pyl("PylGiza", 2600, w_pudle(O_GIZA + Vector((30, -45, 9)), (90, 90, 22)), mat_punkty("PylGiza_m", ZLOTO, 5.0, migot=0.35),
        prom=(0.012, 0.045), ruch=dict(v=(0.10, 0.05, 0.02), amp=0.3, skala=0.1, tempo=0.2))
    kamera("K2_giza", C["giza"], [(C["giza"], O_GIZA + Vector((64, -84, 3.2)), O_GIZA + Vector((2, -4, 10.5))),
                                   (C["tikal"], O_GIZA + Vector((50, -72, 8.0)), O_GIZA + Vector((0, 0, 11.5)))], lens=28, fstop=4.0)

# ================================================================ 4. TIKAL, metry
O_TIKAL = Vector((6000, 0, 0))


def swiatynia(bm, kontury, x0, wys_tarasu=3.35, n=9, baza=(34.0, 30.0), wciecie=1.45, przod=1, skala=1.0):
    """Piramida schodkowa Majów: n tarasów o pochyłych ścianach, schody od frontu (+x·przod), świątynia i grzebień."""
    z = 0.0
    sx, sy = baza[0] * skala, baza[1] * skala
    ht = wys_tarasu * skala
    for i in range(n):
        k = 1 - 0.55 * skala / sx * 2, 1 - 0.55 * skala / sy * 2
        pudlo(bm, (x0, 0, z), (sx, sy, ht), zwez=k)
        z += ht
        gx, gy = sx * k[0] / 2, sy * k[1] / 2
        kontury.append([(x0 + a * gx, b * gy, z + 0.03) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        sx -= 2 * wciecie * skala
        sy -= 2 * wciecie * skala
    # schody: klin od ziemi do szczytu
    w = 8.5 * skala
    xa, xb = x0 + przod * (baza[0] * skala / 2 + 3.0 * skala), x0 + przod * (sx / 2 + wciecie * skala)
    vs = [bm.verts.new(p) for p in ((xa, -w / 2, 0), (xa, w / 2, 0), (xb, w / 2, z), (xb, -w / 2, z),
                                     (xb, -w / 2, 0), (xb, w / 2, 0))]
    for f in ((0, 1, 2, 3), (0, 3, 4), (1, 5, 2), (0, 4, 5, 1), (4, 3, 2, 5)):
        bm.faces.new([vs[i] for i in f])
    # świątynia na szczycie i grzebień dachowy
    pudlo(bm, (x0, 0, z), (sx * 0.9, sy * 0.86, 5.6 * skala), zwez=(0.94, 0.94))
    kontury.append([(x0 + a * sx * 0.45 * 0.94, b * sy * 0.43 * 0.94, z + 5.63 * skala) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    z2 = z + 5.6 * skala
    pudlo(bm, (x0 - przod * sx * 0.12, 0, z2), (sx * 0.5, sy * 0.72, 5.2 * skala), zwez=(0.8, 0.9))
    pudlo(bm, (x0 - przod * sx * 0.12, 0, z2 + 5.2 * skala), (sx * 0.4, sy * 0.6, 3.4 * skala), zwez=(0.7, 0.85))
    return z2 + 8.6 * skala


with Zestaw([(C["tikal"], C["kamien"])]):
    S_T = Vector((0.45, 0.86, 0.20)).normalized()
    kopula("NieboTikal", O_TIKAL, 1400, (0.075, 0.050, 0.040), (0.006, 0.011, 0.028), S_T, sila_slonca=1.5, wykl=50)
    gwiazdy_kopuly("GwiazdyTikal", O_TIKAL, 1350, 2200, mat_punkty("GwiazdyTikal_m", (0.9, 0.93, 1.0), 1.5, migot=0.3))
    kula("SlonceTikal", 15, O_TIKAL + S_T * 1300, mat_swiatlo("SlonceTikal", (1.0, 0.75, 0.45), 60.0), cien=False)
    slonce_lampa("LampaTikal", S_T, 3.5, kat=2.0)
    lampa("WypelnienieTikal", "AREA", O_TIKAL + Vector((120, -160, 90)), O_TIKAL + Vector((0, 0, 20)), 1.1e5, (0.55, 0.62, 1.0), 150)
    m, nt, W = mat_nowy("Wapien")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = (0.60, 0.44, 0.27, 1)
    bs.inputs["Roughness"].default_value = 0.9
    oc = W.coord("Object")
    wv = W._node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z")
    wv.inputs["Scale"].default_value = 2.6
    wv.inputs["Distortion"].default_value = 0.6
    W._in(wv.inputs["Vector"], oc)
    nz = W._node("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.3
    nz.inputs["Detail"].default_value = 8
    W._in(nz.inputs["Vector"], oc)
    bp = W._node("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.6
    bp.inputs["Distance"].default_value = 0.25
    W._in(bp.inputs["Height"], W.add(W.mul(wv.outputs["Fac"], 0.5), nz.outputs[0]))
    nt.links.new(bp.outputs[0], bs.inputs["Normal"])
    wyjscie(nt, bs.outputs[0])
    m_wap = m
    M_KONT_T = mat_swiatlo("KonturTikal", ZLOTO, 0.0)
    animuj(sila_emisji(M_KONT_T), "default_value", [(C["tikal"], 12.0), (C["tikal"] + 16, 2.8)], "BEZIER")
    kont = []
    bm = bmesh.new()
    swiatynia(bm, kont, 0.0, przod=-1)                          # Świątynia I (ok. 47 m), front ku placowi
    k2 = []
    swiatynia(bm, k2, -98.0, wys_tarasu=3.6, n=6, baza=(36.0, 34.0), wciecie=1.9, przod=1, skala=0.95)   # Świątynia II naprzeciw
    siatka("Swiatynie", bm, m_wap, loc=O_TIKAL)
    for i, kk in enumerate(kont + k2):
        linia3d(f"KonturT{i}", kk, 0.075, M_KONT_T, True).location = O_TIKAL
    bm = bmesh.new()
    pudlo(bm, (0, 0, -1), (2600, 2600, 1))
    siatka("ZiemiaTikal", bm, mat_pryncypialny("ZiemiaTikal_m", (0.030, 0.040, 0.020), 1.0, wypuklosc=(0.3, 0.4)), loc=O_TIKAL)
    # dżungla: korony drzew wokół placu (jedna siatka: wzorzec kuli powielony w numpy)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    bm.verts.ensure_lookup_table()
    wz_v = np.array([v_.co[:] for v_ in bm.verts], np.float32)
    wz_f = np.array([[v_.index for v_ in f_.verts] for f_ in bm.faces], np.int32)
    bm.free()
    drzewa = []
    while len(drzewa) < 1900:
        a_ = rng.uniform(0, 2 * math.pi)
        d_ = 50 + 640 * rng.random() ** 1.3
        x, y = -49 + d_ * math.cos(a_), d_ * math.sin(a_)
        if (abs(y) < 40 and -130 < x < 34) or math.hypot(x + 57, y + 59) < 105 or math.hypot(x + 20, y + 20) < 70:
            continue
        r = rng.uniform(3.8, 7.5)
        drzewa.append((x, y, rng.uniform(12, 20) + (9 if rng.random() < 0.06 else 0), r))
    drzewa = np.array(drzewa, np.float32)
    co = (wz_v[None] * drzewa[:, None, 3:4] * np.array([1, 1, 0.85], np.float32) + drzewa[:, None, :3]).reshape(-1, 3)
    for cz, amp in ((0.45, 1.3), (1.3, 0.8)):                         # guzowate korony: dwie oktawy „szumu” z sinusów
        q = co * cz
        co = co + amp * np.stack([np.sin(q[:, 1] * 1.7 + q[:, 2] * 1.3 + 1.0) * np.cos(q[:, 0] * 0.9),
                                  np.sin(q[:, 2] * 1.9 + q[:, 0] * 1.1 + 2.0) * np.cos(q[:, 1] * 0.8),
                                  np.sin(q[:, 0] * 1.5 + q[:, 1] * 1.2 + 3.0) * np.cos(q[:, 2] * 1.1)], axis=1)
    fa = (wz_f[None] + (np.arange(len(drzewa), dtype=np.int32) * len(wz_v))[:, None, None]).reshape(-1, 3)
    me = bpy.data.meshes.new("Dzungla")
    me.vertices.add(len(co))
    me.vertices.foreach_set("co", co.astype(np.float32).ravel())
    me.loops.add(fa.size)
    me.loops.foreach_set("vertex_index", fa.ravel())
    me.polygons.add(len(fa))
    me.polygons.foreach_set("loop_start", np.arange(0, fa.size, 3, dtype=np.int32))
    me.polygons.foreach_set("use_smooth", np.ones(len(fa), bool))
    me.update(calc_edges=True)
    me.materials.append(mat_pryncypialny("Dzungla_m", (0.022, 0.050, 0.016), 1.0, wypuklosc=(1.5, 0.8)))
    dz_ob = bpy.data.objects.new("Dzungla", me)
    dz_ob.location = O_TIKAL
    sc.collection.objects.link(dz_ob)
    mgla("MglaTikal", O_TIKAL + Vector((0, 0, 60)), (1200, 1200, 124), 0.00055, (1.0, 0.80, 0.55), 0.7)
    pyl("PylTikal", 2600, w_pudle(O_TIKAL + Vector((-45, -40, 26)), (130, 130, 60)), mat_punkty("PylTikal_m", ZLOTO, 5.0, migot=0.35),
        prom=(0.03, 0.10), ruch=dict(v=(0.2, 0.1, 0.06), amp=0.6, skala=0.05, tempo=0.2))
    kamera("K3_tikal", C["tikal"], [(C["tikal"], O_TIKAL + Vector((-66, -52, 4.0)), O_TIKAL + Vector((0, 0, 24))),
                                     (C["kamien"], O_TIKAL + Vector((-48, -66, 30.0)), O_TIKAL + Vector((0, 0, 27)))], lens=26, fstop=4.0)

# ================================================================ 5. KAMIEŃ SŁOŃCA, metry
O_KAM = Vector((12000, 0, 0))
FOTO = os.path.join(G.DANE, "kamien-slonca", "Piedra_del_Sol_en_MNA.jpg")
K_KOLOR = os.path.join(G.CACHE, "kamien_kolor_v1.png")
K_WYS = os.path.join(G.CACHE, "kamien_wys_v1.npy")
NT = 2048


def kamien_tekstury():
    """Jak w klipie kamien-slonca-4-ollin: zdjęcie wyprostowane do koła i mapa wysokości z jasności."""
    if os.path.exists(K_KOLOR) and os.path.exists(K_WYS):
        return
    a = G.obraz_numpy(FOTO)[..., :3]
    H0, W0 = a.shape[:2]
    f = W0 / 1000.0
    cx, cy, rx, top, bot, kx = 548.5, 392.0, 436.0, 22.0, 822.0, 0.03
    A = ((bot - cy) + (cy - top)) / 2
    B = ((bot - cy) - (cy - top)) / 2
    g = (np.arange(NT) + 0.5) / NT * 2 - 1
    X, Y = np.meshgrid(g, g)
    xs = (cx + X * rx * (1 + kx * Y)) * f
    ys = (cy + Y * (A + B * Y)) * f
    x0 = np.clip(np.floor(xs).astype(int), 0, W0 - 2)
    y0 = np.clip(np.floor(ys).astype(int), 0, H0 - 2)
    fx = np.clip(xs - x0, 0, 1)[..., None]
    fy = np.clip(ys - y0, 0, 1)[..., None]
    o = (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy) + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy)
    G.zapisz_png(np.concatenate([o, np.ones(o.shape[:2] + (1,), np.float32)], axis=2), K_KOLOR, "kamien_kolor")
    L = o[..., 0] * 0.3 + o[..., 1] * 0.55 + o[..., 2] * 0.15
    duze = np.repeat(np.repeat(G.rozmyj(G.zmniejsz(L, 4), 6), 4, 0), 4, 1)
    hp = G.rozmyj(L - duze, 1)
    lo, hi = np.percentile(hp, 2), np.percentile(hp, 98)
    np.save(K_WYS, np.clip((hp - lo) / (hi - lo), 0, 1).astype(np.float32))


with Zestaw([(C["kamien"], C["stone"])]):
    kamien_tekstury()
    R_TARCZY, RM, GLEB = 0.985, 1.79, 0.075
    Sk = RM / R_TARCZY
    h = np.load(K_WYS)
    NR, NS = 380, 1100
    rs = np.linspace(0, 1, NR + 1)[1:]
    ts = np.linspace(0, 2 * math.pi, NS, endpoint=False)
    RR, TT = np.meshgrid(rs, ts, indexing="ij")
    uu = np.concatenate([[0.0], (RR * np.cos(TT)).ravel() * R_TARCZY])
    vv = np.concatenate([[0.0], (RR * np.sin(TT)).ravel() * R_TARCZY])
    px = np.clip(((uu + 1) / 2 * NT).astype(int), 0, NT - 1)
    py = np.clip(((1 - vv) / 2 * NT).astype(int), 0, NT - 1)
    hh = h[py, px] * np.clip((1 - np.hypot(uu, vv) / R_TARCZY) / 0.01, 0, 1)
    verts = np.stack([uu * Sk, -hh * GLEB, vv * Sk], axis=1)
    faces = [(0, 1 + j, 1 + (j + 1) % NS) for j in range(NS)]
    idx = lambda i, j: 1 + i * NS + (j % NS)
    for i in range(NR - 1):
        for j in range(NS):
            faces.append((idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)))
    me = bpy.data.meshes.new("Tarcza")
    me.from_pydata(verts.tolist(), [], faces)
    uvl = me.uv_layers.new(name="UV")
    lv = np.empty(len(me.loops), np.int32)
    me.loops.foreach_get("vertex_index", lv)
    uvl.data.foreach_set("uv", np.stack([(uu[lv] + 1) / 2, (vv[lv] + 1) / 2], axis=1).astype(np.float32).ravel())
    me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
    me.update()
    os_k = bpy.data.objects.new("KamienOs", None)
    os_k.location = O_KAM
    sc.collection.objects.link(os_k)
    tarcza = bpy.data.objects.new("Tarcza", me)
    sc.collection.objects.link(tarcza)
    tarcza.parent = os_k
    # materiał: kamień „w złocie” – barwa zdjęcia przesunięta ku złotu, lekko metaliczna
    m, nt, W = mat_nowy("KamienZloty")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    uv = W._node("ShaderNodeUVMap").outputs[0]
    tk, _ = W.obraz(G.wczytaj_obraz(K_KOLOR), uv, "Cubic")
    bw = W._node("ShaderNodeRGBToBW")
    W._in(bw.inputs[0], tk)
    jasn = W.smooth(0.02, 0.55, bw.outputs[0])
    zl = W.mixv(jasn, (0.20, 0.10, 0.025), (1.0, 0.68, 0.26))
    W._in(bs.inputs["Base Color"], W.mixv(0.72, tk, zl))
    bs.inputs["Metallic"].default_value = 0.6
    bs.inputs["Roughness"].default_value = 0.42
    wyjscie(nt, bs.outputs[0])
    me.materials.append(m)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=256, radius1=RM, radius2=RM, depth=0.5,
                          matrix=Matrix.Translation((0, 0.252, 0)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    bok = siatka("KamienBok", bm, mat_pryncypialny("KamienBok_m", (0.30, 0.19, 0.07), 0.5, metal=0.6, wypuklosc=(6.0, 0.5)))
    bok.parent = os_k
    animuj(os_k, "rotation_euler", [(C["kamien"], math.radians(-26)), (C["stone"], math.radians(12))], "LINEAR", index=1)
    animuj(os_k, "rotation_euler", [(C["kamien"], math.radians(-24)), (C["stone"], math.radians(-6))], "LINEAR", index=2)
    # światło ślizgowe wędruje z lewej ku górze, kontra z prawej
    kl_ = lampa("KamienKlucz", "AREA", (0, 0, 0), (0, 0, 1), 900.0, (1.0, 0.74, 0.42), 1.6)
    kon = kl_.constraints.new("TRACK_TO")
    kon.target = os_k
    kon.track_axis, kon.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    kl_.rotation_euler = (0, 0, 0)
    kk = []
    for f in range(C["kamien"], C["stone"] + 1, 4):
        a_ = math.radians(200 - 115 * (f - C["kamien"]) / (C["stone"] - C["kamien"]))
        kk.append((f, tuple(O_KAM + Vector((math.cos(a_) * 4.2, -1.15, math.sin(a_) * 4.2)))))
    animuj(kl_, "location", kk, "GLADKO")
    lampa("KamienKontra", "AREA", O_KAM + Vector((4.5, -1.6, -2.0)), O_KAM, 320.0, (0.45, 0.60, 1.0), 3.0)
    lampa("KamienPrzod", "AREA", O_KAM + Vector((0, -7, 1.5)), O_KAM, 140.0, (1.0, 0.85, 0.65), 5.0)
    pyl("PylKamien", 1500, w_pudle(O_KAM + Vector((0, -3.5, 0)), (9, 8, 6)), mat_punkty("PylKamien_m", ZLOTO, 6.0, migot=0.35),
        prom=(0.004, 0.013), ruch=dict(v=(0.03, 0.0, 0.05), amp=0.08, skala=0.6, tempo=0.3))
    # kamera: jak dotąd płynie po prostej; od PRZ0 przyspiesza ku twarzy Słońca w środku kamienia (przejście do Stonehenge)
    _A, _B = O_KAM + Vector((-1.5, -8.6, -0.5)), O_KAM + Vector((0.5, -5.3, 0.25))
    _N = O_KAM + Vector((0.20, -2.7, 0.12))
    _c0, _c1 = O_KAM + Vector((0.1, 0, 0.0)), O_KAM + Vector((0, 0, 0.05))
    klk = [(C["kamien"], _A, _c0)]
    for f in range(PRZ0, C["stone"] + 1):
        x = (f - C["kamien"]) / (C["stone"] - C["kamien"])
        e = ((f - PRZ0) / (C["stone"] - PRZ0)) ** 2.2
        klk.append((f, _A.lerp(_B, x) + (_N - _B) * e, _c0.lerp(_c1, x)))
    kam5, _ = kamera("K5_kamien", C["kamien"], klk, lens=50, fstop=2.8)
    G.tlo_kamery(kam5, odl=60.0)

# ================================================================ 6. STONEHENGE: TŁO POD TYTUŁ ODCINKA I ODPŁYNIĘCIE (358–750), metry
O_STONE = Vector((9000, 0, 0))
ST0, P0 = T["stone"], T["odplyw"]
KONIEC = KLATEK - 1
with Zestaw([(ST0, KLATEK)]):
    AZ = math.radians(50.0)                                           # oś ku wschodowi Słońca w przesilenie letnie
    OS = Vector((math.sin(AZ), math.cos(AZ), 0))
    BOK = Vector((OS.y, -OS.x, 0))
    S_S = (OS + Vector((0, 0, 0.066))).normalized()                   # Słońce 3,8° nad horyzontem, dokładnie w osi
    kopula("NieboStone", O_STONE, 1400, (0.060, 0.040, 0.036), (0.006, 0.011, 0.030), S_S, sila_slonca=0.5, wykl=120)
    gwiazdy_kopuly("GwiazdyStone", O_STONE, 1350, 2600, mat_punkty("GwiazdyStone_m", (0.9, 0.93, 1.0), 1.7, migot=0.3), zmin=0.10)
    kula("SlonceStone", 9.0, O_STONE + S_S * 1300, mat_swiatlo("SlonceStone", (1.0, 0.80, 0.50), 150.0), cien=False)
    slonce_lampa("LampaStone", S_S, 4.5, kolor=(1.0, 0.70, 0.38), kat=1.0)
    lampa("WypelnienieStone", "AREA", O_STONE - OS * 60 + Vector((0, 0, 45)), O_STONE, 1.6e4, (0.62, 0.66, 1.0), 60)
    bm = bmesh.new()
    a0 = math.atan2(OS.y, OS.x)
    # krąg sarsenowy: 30 głazów i ciągły pierścień nadproży (szczeliny wypadają w osi)
    for i in range(30):
        a_ = a0 + 2 * math.pi * (i + 0.5) / 30
        p_ = Vector((math.cos(a_), math.sin(a_), 0)) * 15.6
        pudlo(bm, p_, (1.1 * rng.uniform(0.9, 1.1), 2.1 * rng.uniform(0.88, 1.08), 4.1), obrot=a_, zwez=(0.86, 0.9))
        a2 = a0 + 2 * math.pi * (i + 1.0) / 30
        pudlo(bm, (15.6 * math.cos(a2), 15.6 * math.sin(a2), 4.1), (1.0, 3.2, 0.78), obrot=a2)
    # podkowa pięciu trylitów, otwarta ku osi
    for da, hh in ((180, 7.3), (118, 6.5), (-118, 6.5), (62, 6.1), (-62, 6.1)):
        a_ = a0 + math.radians(da)
        c_ = Vector((math.cos(a_), math.sin(a_), 0)) * 7.4
        t_ = Vector((-math.sin(a_), math.cos(a_), 0))
        for s_ in (-1, 1):
            pudlo(bm, c_ + t_ * 1.55 * s_, (1.25, 2.2, hh), obrot=a_, zwez=(0.84, 0.86))
        pudlo(bm, c_ + Vector((0, 0, hh)), (1.3, 4.9, 1.05), obrot=a_, zwez=(1.0, 1.04))
    # krąg i podkowa z „błękitnych kamieni”
    for i in range(56):
        a_ = a0 + 2 * math.pi * (i + 0.5) / 56
        pudlo(bm, Vector((math.cos(a_), math.sin(a_), 0)) * 11.6, (0.55, 0.9, rng.uniform(1.5, 2.0)), obrot=a_, zwez=(0.75, 0.8))
    for i in range(14):
        a_ = a0 + math.radians(65 + 230 * (i + 0.5) / 14)
        pudlo(bm, Vector((math.cos(a_), math.sin(a_), 0)) * 5.3, (0.5, 0.7, rng.uniform(2.0, 2.6)), obrot=a_, zwez=(0.7, 0.75))
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=4, use_grid_fill=True)
    for v_ in bm.verts:
        v_.co += noise.noise_vector(v_.co * 0.55) * 0.16 + noise.noise_vector(v_.co * 2.1) * 0.04
    siatka("Kamienie", bm, mat_pryncypialny("Sarsen", (0.36, 0.33, 0.30), 0.85, wypuklosc=(3.0, 0.7)), gladka=True, loc=O_STONE)
    bm = bmesh.new()
    pudlo(bm, (0, 0, -1), (2700, 2700, 1))
    siatka("Laka", bm, mat_pryncypialny("Laka_m", (0.060, 0.065, 0.030), 0.95, wypuklosc=(2.0, 0.6)), loc=O_STONE)
    mgla("MglaStone", O_STONE + Vector((0, 0, 7)), (1100, 1100, 14.2), 0.0044, (1.0, 0.80, 0.55), 0.6)      # niska mgła przy ziemi: niebo zostaje granatowe
    pyl("PylStone", 3600, w_pudle(O_STONE + Vector((0, 0, 9)) - OS * 38, (70, 110, 20)), mat_punkty("PylStone_m", ZLOTO, 5.0, migot=0.35),
        prom=(0.006, 0.022), ruch=dict(v=(0.05, 0.03, 0.03), amp=0.15, skala=0.3, tempo=0.3))

    # kamera: stoi w osi, powoli przesuwa się w bok (Słońce wchodzi w szczelinę na klatce `slonce`), potem odpływa
    D_KAM, WYS_KAM, NACH = 48.0, 1.6, math.radians(17.0)        # NACH: o ile kamera patrzy ponad horyzont (kamienie nisko w kadrze)

    def _lin(f, pkt):
        for (f0, v0), (f1, v1) in zip(pkt, pkt[1:]):
            if f <= f1:
                return v0 + (v1 - v0) * (f - f0) / (f1 - f0)
        return pkt[-1][1]

    kl = []
    for f in sorted(set(list(range(ST0, KONIEC, 3)) + [KONIEC])):
        w = G.gladko5((f - P0) / (KONIEC - P0))
        b = _lin(f, [(ST0, -1.42), (T["slonce"], -0.70), (T["lektor"], -0.12), (P0, 0.22), (KONIEC, 0.0)])
        poz = O_STONE - OS * (D_KAM + 16.0 * w) + BOK * b + Vector((0, 0, WYS_KAM + 9.5 * w))
        cel_a = poz + OS * 100.0 + Vector((0, 0, 100.0 * math.tan(NACH)))
        cel_b = O_STONE + OS * 20.0 + Vector((0, 0, 9.0))
        kl.append((f, poz, cel_a.lerp(cel_b, w)))
    ostr = bpy.data.objects.new("OstroscStone", None)
    ostr.location = O_STONE
    sc.collection.objects.link(ostr)
    kamera("K6_stone", ST0, kl, lens=24, fstop=5.6, interp="GLADKO", ostrosc=ostr)

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

# ================================================================ kompozycja: poświata, smugi, winieta, błysk, rozjaśnienia na cięciach
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
# przejście Kamień Słońca → Stonehenge: złote światło rozlewa się z twarzy Słońca w środku kamienia, wypełnia kadr,
# a po cięciu zbiega się do łuny nad horyzontem, tam gdzie potem wzejdzie Słońce
el2 = ng.nodes.new("CompositorNodeEllipseMask")
bl2 = ng.nodes.new("CompositorNodeBlur")
ng.links.new(el2.outputs[0], bl2.inputs["Image"])
sila = ng.nodes.new("ShaderNodeMath")
sila.operation = "MULTIPLY_ADD"                       # maska × siła + równa poświata na cały kadr
sila.use_clamp = True
ng.links.new(bl2.outputs[0], sila.inputs[0])
sila.inputs[1].default_value = 0.0
sila.inputs[2].default_value = 0.0
przej = ng.nodes.new("ShaderNodeMix")
przej.data_type = "RGBA"
pot = ng.nodes.new("ShaderNodeMath")                  # barwa światła: na brzegu głębokie złoto, w środku jasny krem
pot.operation = "POWER"
ng.links.new(sila.outputs[0], pot.inputs[0])
pot.inputs[1].default_value = 2.0
barwa = ng.nodes.new("ShaderNodeMix")
barwa.data_type = "RGBA"
barwa.inputs["A"].default_value = (1.0, 0.52, 0.15, 1)
barwa.inputs["B"].default_value = (2.0, 1.45, 0.75, 1)
ng.links.new(pot.outputs[0], barwa.inputs["Factor"])
ng.links.new(barwa.outputs["Result"], przej.inputs["B"])
ng.links.new(sila.outputs[0], przej.inputs["Factor"])
ng.links.new(blysk_k.outputs["Result"], przej.inputs["A"])
fade = ng.nodes.new("ShaderNodeMix")
fade.data_type = "RGBA"
fade.inputs["A"].default_value = (0, 0, 0, 1)
ng.links.new(przej.outputs["Result"], fade.inputs["B"])
out = ng.nodes.new("NodeGroupOutput")
ng.links.new(fade.outputs["Result"], out.inputs[0])
sc.compositing_node_group = ng
sc.render.use_compositing = True
try:
    sc.render.compositor_device = "GPU"
except Exception:
    pass

ek = [(0, 0.0), (B0 - 1, 1.2), (B0 + 1, 1.8), (B0 + 5, 1.0), (B0 + 12, 0.4), (B0 + 26, 0.0)]
for c in (T["montaz"], T["giza"], T["tikal"], T["kamien"], T["stone"]):      # krótkie rozjaśnienie na każdym cięciu montażu
    ek += [(c - 1, 0.0), (c, 0.9), (c + 7, 0.0)]
ek += [(KONIEC, 0.0)]
animuj(n_eksp.inputs["Exposure"], "default_value", sorted(ek), "LINEAR")
animuj(blysk_k.inputs["Factor"], "default_value", [(0, 0.0), (B0 - 2, 0.0), (B0 + 1, 0.85), (B0 + 4, 0.42), (B0 + 9, 0.0),
                                                   (KONIEC, 0.0)], "LINEAR")
animuj(fade.inputs["Factor"], "default_value", [(0, 0.0), (max(1, B0 - 3), 0.0), (B0 + 2, 1.0), (KONIEC, 1.0)], "LINEAR")
_S = T["stone"]
# średnica światła jako ułamek szerokości kadru; rozmycie rośnie razem z nią, więc to zawsze miękka poświata, nie tarcza
_sr = [(0, 0.02), (PRZ0 - 2, 0.02), (PRZ0 + 4, 0.10), (_S - 4, 0.26), (_S - 2, 0.55), (_S - 1, 1.1),
       (_S, 1.0), (_S + 2, 0.6), (_S + 6, 0.36), (_S + 14, 0.22), (PRZ1, 0.14), (KONIEC, 0.14)]
_px = 1920 * opcje["skala"] / 100 * PRZ_MIEKKOSC
animuj(el2.inputs["Size"], "default_value", [(f, (v, v)) for f, v in _sr], "LINEAR")
animuj(bl2.inputs["Size"], "default_value", [(f, (v * _px, v * _px)) for f, v in _sr], "LINEAR")
animuj(el2.inputs["Position"], "default_value", [(0, (0.5, 0.5)), (_S - 1, (0.5, 0.5)), (_S, (0.5, PRZ_HORYZONT)),
                                                 (KONIEC, (0.5, PRZ_HORYZONT))], "CONSTANT")
animuj(sila.inputs[1], "default_value", [(0, 0.0), (PRZ0 - 2, 0.0), (PRZ0 + 1, 1.3), (_S - 1, 1.5), (_S, 1.5), (_S + 6, 1.1),
                                         (PRZ1, 0.0), (KONIEC, 0.0)], "LINEAR")
animuj(sila.inputs[2], "default_value", [(0, 0.0), (_S - 3, 0.0), (_S - 1, 0.8), (_S, 0.55), (_S + 2, 0.1), (_S + 4, 0.0),
                                         (KONIEC, 0.0)], "LINEAR")


# ================================================================ render, składanie, podgląd
def ffmpeg(*a, cwd=None):
    subprocess.run([G.ffmpeg_exe(), "-loglevel", "error", "-y", *a], check=True, cwd=cwd)


def napis_ff(plik, tekst, font, px, kolor, y, od, do, wej=0.8, wyj=0.4, x="(w-text_w)/2"):
    """Filtr drawtext z łagodnym wejściem i zejściem (czasy w sekundach). Tekst idzie z pliku UTF-8 w _klatki/."""
    with open(os.path.join(KLATKI_DIR, plik), "w", encoding="utf-8") as f:
        f.write(tekst)
    return (f"drawtext=fontfile=/Windows/Fonts/{font}:textfile={plik}:fontsize={px}:fontcolor={kolor}:x={x}:y={y}"
            f":borderw=2:bordercolor=0x05070c@0.55:shadowcolor=0x05070c@0.6:shadowx=2:shadowy=2"
            f":alpha='clip((t-{od:.3f})/{wej},0,1)*clip(({do:.3f}-t)/{wyj},0,1)'")


def zloz():
    brak = [f for f in range(KLATEK) if not os.path.exists(os.path.join(KLATKI_DIR, f"k_{f:04d}.png"))]
    if brak:
        raise SystemExit(f"[zloz] brakuje {len(brak)} klatek, np. {brak[:5]}")
    napisy = ",".join([
        napis_ff("napis_adres.txt", "uleszka.net  ·  2004–2007", "georgia.ttf", 54, "0xf0c46f", 958, T["adres"] / FPS, (T["kamien"] - 2) / FPS, 0.9, 0.3),
        napis_ff("napis_lektor.txt", "lektor: głos wygenerowany przez AI", "georgia.ttf", 38, "0xf0e8d6", 990, T["lektor"] / FPS, (P0 + 22) / FPS, 0.7, 1.0),
    ])
    ffmpeg("-framerate", str(FPS), "-start_number", "0", "-i", "k_%04d.png", "-vf", napisy,
           "-frames:v", str(KLATEK), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           "-preset", "slow", "-an", "-movflags", "+faststart", os.path.join(TU, "klip.mp4"), cwd=KLATKI_DIR)
    ffmpeg("-i", os.path.join(TU, "klip.mp4"), "-vf", f"select='eq(n,{KADR})',scale=1600:-2", "-frames:v", "1", "-q:v", "2",
           os.path.join(TU, "kadr.jpg"))
    print("[zloz]", os.path.join(TU, "klip.mp4"))


def podglad(mp3):
    """klip + pierwsze 30 s nagrania + przykładowy tytuł odcinka, położony tak jak w wideo.ts (14,3–24,5 s)."""
    tyt = ",".join([
        napis_ff("pod_etykieta.txt", "O D C I N E K   2", "arialbd.ttf", 34, "0xe2a93f", 414, 14.3, 24.5, 0.6, 0.6),
        napis_ff("pod_tytul.txt", "Wielki uskok…", "georgiab.ttf", 104, "0xf0c46f", 484, 14.3, 24.5, 0.6, 0.6),
    ])
    ffmpeg("-i", os.path.join(TU, "klip.mp4"), "-t", str(KLATEK / FPS), "-i", mp3, "-map", "0:v", "-map", "1:a", "-vf", tyt,
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
           "-t", str(KLATEK / FPS), "-movflags", "+faststart", os.path.join(TU, "podglad.mp4"), cwd=KLATKI_DIR)
    print("[podglad]", os.path.join(TU, "podglad.mp4"))


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
if opcje["podglad"]:
    podglad(opcje["podglad"])
elif opcje["zloz"]:
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
