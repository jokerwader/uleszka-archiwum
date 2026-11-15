"""
Piramida Chefrena: znane komory oraz struktury, które według F. Biondiego i C. Malangi (2025)
mają być w piramidzie i pod nią.

Model poglądowy do Atlasu Leszka (uleszka.net). Buduje całą scenę od zera w Blenderze
(testowane na Blenderze 5.3), zapisuje .blend, eksportuje .glb i renderuje kadry.

Uruchomienie (z katalogu repozytorium):

    blender -b --factory-startup --python grafiki/3d/chefren-sar/build_chefren_sar.py -- \
        --blend --glb --stills

    # klatki filmu obrotowego (potem sklejenie ffmpeg, patrz README.md):
    blender -b --factory-startup --python grafiki/3d/chefren-sar/build_chefren_sar.py -- \
        --frames <folder_na_klatki>

Układ współrzędnych: 1 jednostka = 1 metr, X = wschód, Y = północ, Z = góra,
Z = 0 to poziom skały pod piramidą, środek podstawy piramidy w (0, 0, 0).

KOLORY:
  piaskowy / złoty  = to, co potwierdzone (piramida, znane komory i korytarze),
  czerwono-różowy   = wyłącznie twierdzenia Malangi i Biondiego (bez recenzji naukowej).

Znane komory i korytarze: wg pomiarów Petriego (1883) oraz Maragioglia i Rinaldiego (1966).
Twierdzenia: liczby z konferencji prasowej 15.03.2025, układ z modelu 3D pokazanego przez autorów.
Wymiary i ich pochodzenie opisuje README.md. Wartości oznaczone "SZAC" to szacunki
autora modelu, bo źródła ich nie podają.
"""

import argparse
import math
import os
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

# ---------------------------------------------------------------- argumenty
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
ap.add_argument("--blend", action="store_true", help="zapisz chefren-sar.blend")
ap.add_argument("--glb", action="store_true", help="eksportuj chefren-sar.glb")
ap.add_argument("--stills", action="store_true", help="renderuj 5 kadrów PNG")
ap.add_argument("--only", default="", help="lista kadrów po przecinku, np. ogolny,opis")
ap.add_argument("--frames", default="", help="folder na klatki filmu obrotowego (PNG)")
ap.add_argument("--scale", type=int, default=100, help="procent rozdzielczości 1920x1080")
ap.add_argument("--samples", type=int, default=64)
ap.add_argument("--video-samples", type=int, default=32)
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--seconds", type=int, default=16)
args = ap.parse_args(argv)
OUT = os.path.abspath(args.out)
RES = (1920, 1080)

# ---------------------------------------------------------------- wymiary
# POTWIERDZONE. Źródła: W.M.F. Petrie, The Pyramids and Temples of Gizeh (1883), rozdz. 8–9;
# V. Maragioglio, C. Rinaldi, L'Architettura delle Piramidi Menfite, cz. V (1966) [dalej M&R].
PYR_BASE = 215.25          # bok podstawy [m] (Petrie: średnio 8474,9 cala)
PYR_HEIGHT = 143.5         # pierwotna wysokość [m] (kąt ścian ok. 53°10')
PASS_X = 12.45             # oś korytarzy: 12,45 m na wschód od osi piramidy (Petrie: 490,3 cala; M&R)
UPPER_ENTRANCE_Z = 11.54   # zachowany próg górnego wejścia; M&R rekonstruują pierwotny próg na 12,90 m
UPPER_ANGLE = 26.5         # korytarz zstępujący: 26°30'–26°46' (M&R)
PASS_W = 1.05              # szerokość korytarzy: 2 łokcie (Petrie: 41,29 cala)
UPPER_H = 1.20             # wysokość korytarza zstępującego (Petrie: 47,29 cala)
HORIZ_Z = -3.0             # posadzka korytarza poziomego: ok. 3 m poniżej bruku dziedzińca (M&R)
HORIZ_H = 1.80             # wysokość korytarza poziomego (Petrie: 71,06 cala)
PORTCULLIS_AFTER = 1.04    # zapadnia 1,04 m za końcem pochyłego stropu (Petrie)
PIT_T_AFTER = 7.0          # szyb T (połączenie z dolnym systemem) ok. 7 m na południe od zapadni (M&R)
BURIAL_X = (1.19, 15.36)   # komora grobowa: ściana zach. 1,19 m na wschód od osi N–S (Petrie); dł. 14,17 m
BURIAL_Y = (1.17, 6.14)    # ściana płd. 1,17 m na północ od osi W–E (Perring); szer. 4,97 m
BURIAL_WALL = 5.24         # wysokość ścian (Petrie: 206,4 cala)
BURIAL_APEX = 6.84         # wysokość do szczytu stropu dwuspadowego (Perring/Vandier)
SARC = (1.07, 2.63, 0.97)  # sarkofag: szer. W–E, dł. N–S, wys. (Petrie); 1,09 m od ściany zach., 1,08 m od płn.
LOWER_ENTRY_NORTH = 8.0    # dolne wejście w bruku "ponad 8 m" na północ od krawędzi podstawy (de.wikipedia)
LOWER_DESC_ANGLE = 22.67   # dolny korytarz zstępujący: ok. 22°40' (M&R)
LOWER_ASC_ANGLE = 21.67    # korytarz wstępujący do górnego systemu: średnio 21°40' (M&R)
LOWER_SLOPE_H = 1.32       # wysokość pionowa korytarzy pochyłych dolnego systemu: 1,30–1,34 m (M&R)
LOWER_H = 1.83             # wysokość dolnego odcinka poziomego (M&R)
SUBSID = (10.41, 3.12, 2.61)  # komora boczna: dł. W–E, szer. N–S (Petrie: 10,46 × 3,13 m), wys. (Wikipedia)

# SZAC w części potwierdzonej (źródła nie podają liczb)
LOWER_Z = -10.0            # SZAC: posadzka dolnego odcinka poziomego (z kątów wynika wtedy długość ok. 13 m)
RAMP_LEN = 6.0             # SZAC: długość rampy do komory bocznej (zachodnia ściana, połowa odcinka poziomego)
RAMP_DROP = 1.5            # SZAC: spadek rampy
SUBSID_WALL = 1.75         # SZAC: wysokość ścian komory bocznej (2,61 m przyjęto jako wysokość do szczytu stropu)

# TWIERDZENIA. Liczby: oficjalne streszczenie zespołu (F. Biondi, A. Mei, C. Malanga, marzec 2025;
# dalej "streszczenie") i C. Malanga na konferencji prasowej 15.03.2025 (transkrypcja J. Evatta).
# Układ: model 3D autorów ze slajdów konferencji (model autorów nie ma skali pionowej).
N_SHAFTS = 8               # streszczenie: 8 cylindrycznych struktur w dwóch równoległych rzędach z północy na południe
SHAFT_RADIUS = 5.5         # Malanga: "średnica ok. 10–12 metrów" -> 11 m
SHAFT_BOTTOM = -648.0      # streszczenie: "do głębokości 648 metrów"
CUBE_SIDE = 80.0           # streszczenie: "dwie duże struktury sześcienne o boku ok. 80 metrów"
N_CELLS = 5                # streszczenie: "5 struktur w środku piramidy, nad komorą Belzoniego", kształt "Zed"
CELL_LEVELS = 5            # streszczenie: "5 poziomów i skośny dach"
DEEP_ZONE_Z = -1200.0      # Malanga: "ok. 1200 metrów w głąb ... prawdziwe miasto, w cudzysłowie"
CLAIMED_MAX_DEPTH = -2000.0  # streszczenie: struktury pod trzema piramidami "ok. 2 km poniżej poziomu zero"

# SZAC w części twierdzeń: odczyt z widoków modelu 3D autorów (dokładność rzędu 10 m)
AX = 8.3                   # oś układu: nad komorą grobową ("BELZONI + ZED" na slajdzie), ok. 8 m na wschód od osi
ROW_DX = 28.0              # rzędy szybów 28 m na zachód i na wschód od osi układu
SHAFT_Y = (-90.0, -30.0, 30.0, 90.0)  # cztery szyby w rzędzie, prawie na całej długości podstawy
SHAFT_TOP = 0.0            # streszczenie: szyby zaczynają się "poniżej poziomu zero głównej struktury"
SPIRAL_RADIUS = 9.0        # spirala wyraźnie wystaje poza rurę szybu, jak w modelu autorów
SPIRAL_PITCH = 8.0         # skok spirali: ok. 0,4 średnicy zewnętrznej, jak w modelu autorów
SPIRAL_TUBE = 1.0
CELL_SIZE = (20.0, 16.0)   # rzut "Zeda" (W–E, N–S): ok. 1/10 boku podstawy, jak w modelu autorów
CELL_Z = 4.5               # posadzka "Zedów": na ramie korytarzy, tuż nad stropem komory grobowej
CELL_LEVEL_H = 5.5         # pięć poziomów; razem z dachem ok. 38 m (ok. 1/4 wysokości piramidy, jak w modelu autorów)
CELL_GAP = 1.2
CELL_ROOF = 5.0
GRID_Z = 3.0               # poziom ramy korytarzy (tuż nad podstawą)
GRID_R = 1.5               # promień rur-korytarzy
RING = 98.0                # rama korytarzy biegnie tuż przy krawędziach podstawy
ROOM_BIG = ((-78.0, 76.0), (20.0, 28.0, 16.0))    # większa "skrzynia" przy narożniku płn.-zach.: środek, wymiary
ROOM_SMALL = ((-80.0, -80.0), (14.0, 18.0, 12.0))  # mniejsza przy narożniku płd.-zach.
HOOK_Y = (-50.0, -25.0, 0.0, 25.0, 50.0)  # pięć "haków" pod belką między skrzyniami
WATER_Z = -470.0           # woda: autorzy nie podali głębokości; ok. 73% długości szybów jak w ich modelu
DEEP_ZONE_H = 50.0

# Przekrój gruntu (warstwy schematyczne)
G_HALF = 350.0             # połowa szerokości bloku gruntu
G_BOTTOM = -2100.0
CUT_X = -130.0             # wycięcie: x > CUT_X i y < CUT_Y
CUT_Y = 130.0
LAYERS = [  # (nazwa, z_góra, z_dół, kolor)
    ("piasek_i_gruz", 0.0, -4.0, (0.80, 0.66, 0.45)),
    ("wapien_mokattam", -4.0, -120.0, (0.72, 0.63, 0.48)),
    ("starsze_wapienie_i_margle", -120.0, -700.0, (0.52, 0.46, 0.38)),
    ("glebsze_skaly_osadowe", -700.0, G_BOTTOM, (0.36, 0.33, 0.30)),
]

# ---------------------------------------------------------------- scena
scene = bpy.context.scene
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)

scene.unit_settings.system = "METRIC"
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.resolution_percentage = args.scale
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scene.render.engine = eng
        break
    except TypeError:
        continue
try:
    scene.eevee.taa_render_samples = args.samples
    scene.eevee.shadow_pool_size = "1024"
except (AttributeError, TypeError):
    pass
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.film_transparent = False


def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or scene.collection).children.link(c)
    return c


C_POTW = coll("POTWIERDZONE")
C_TWIERDZ = coll("TWIERDZENIA_MALANGA_BIONDI_2025")
C_TW_CUT = coll("TWIERDZENIA_plaszczyzny_do_przekroju", C_TWIERDZ)
C_TW_FULL = coll("TWIERDZENIA_plaszczyzny_pelne", C_TWIERDZ)
C_GRUNT = coll("GRUNT_PRZEKROJ")
C_GRUNT_GLB = coll("GRUNT_PRZEZROCZYSTY")
C_SKALA = coll("SKALA_GLEBOKOSCI")
C_SWIATLO = coll("SWIATLO_I_KAMERY")

# ---------------------------------------------------------------- materiały
FONT = FONT_B = None
for path, attr in (("C:/Windows/Fonts/arial.ttf", "FONT"), ("C:/Windows/Fonts/arialbd.ttf", "FONT_B")):
    if os.path.exists(path):
        globals()[attr] = bpy.data.fonts.load(path)


def principled(m):
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    p = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if p is None:
        nt.nodes.clear()
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        o = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(p.outputs[0], o.inputs[0])
    return p


def mat(name, color, alpha=1.0, emit=0.0, rough=0.7):
    m = bpy.data.materials.new(name)
    p = principled(m)
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Alpha"].default_value = alpha
    if emit:
        p.inputs["Emission Color"].default_value = (*color, 1)
        p.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = (*color, alpha)
    if alpha < 1:
        for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
        try:
            m.use_backface_culling = False
            m.use_transparency_overlap = True
        except Exception:
            pass
    return m


def flat_mat(name, color, alpha=1.0):
    """Materiał nakładek (napisy, panele): sama emisja, bez światła."""
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if alpha < 1:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = alpha
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs[0])
        for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
    else:
        nt.links.new(em.outputs[0], out.inputs[0])
    m.diffuse_color = (*color, alpha)
    return m


SAND = (0.86, 0.72, 0.50)
GOLD = (1.00, 0.80, 0.32)
CLAIM = (0.95, 0.18, 0.38)
CLAIM_LIGHT = (1.00, 0.55, 0.65)

M_PYR = mat("potw_piramida_przezroczysta", SAND, alpha=0.20, rough=0.8)
M_PYR_EDGE = mat("potw_piramida_krawedzie", (0.95, 0.82, 0.58), emit=0.6)
M_KNOWN = mat("potw_korytarze", GOLD, emit=1.2)
M_CHAMBER = mat("potw_komory", GOLD, alpha=0.55, emit=0.9)
M_GRANITE = mat("potw_granit", (0.62, 0.30, 0.24), emit=0.5)
M_SHAFT = mat("twierdz_szyby", CLAIM, alpha=0.55, emit=0.5)
M_SPIRAL = mat("twierdz_spirale", CLAIM, emit=1.0)
M_CUBE = mat("twierdz_szesciany", CLAIM, alpha=0.35, emit=0.4)
M_CUBE_EDGE = mat("twierdz_szesciany_krawedzie", CLAIM_LIGHT, emit=1.5)
M_UPPER = mat("twierdz_struktury_gorne", CLAIM, alpha=0.6, emit=0.6)
M_ZED_SLAB = mat("twierdz_zed_plyty", CLAIM_LIGHT, emit=0.9)
M_CUBE_HOLE = mat("twierdz_skrzynie_otwory", (0.25, 0.03, 0.09), alpha=0.75, emit=0.1)
M_DASH = mat("twierdz_zasieg_2km", CLAIM_LIGHT, alpha=0.7, emit=1.0)
M_WATER = mat("twierdz_woda", (0.20, 0.55, 1.00), alpha=0.22, emit=0.4)
M_ZONE = mat("twierdz_strefa_1200m", CLAIM, alpha=0.16, emit=0.5)
M_GHOST = mat("grunt_skala_przezroczysta", (0.70, 0.62, 0.50), alpha=0.05)
M_SURFACE = mat("grunt_powierzchnia", (0.80, 0.68, 0.48), alpha=0.18)
M_LAYER_PLANE = mat("grunt_granica_warstw", (0.75, 0.66, 0.52), alpha=0.10)
M_GEDGE = mat("grunt_krawedzie", (0.75, 0.68, 0.58), emit=0.3)
M_RULER = mat("skala", (0.92, 0.92, 0.92), emit=0.8)
M_RULER_RED = mat("skala_648", CLAIM_LIGHT, emit=1.2)
M_LAYERS = {n: mat("grunt_" + n, col, rough=0.95) for n, _, _, col in LAYERS}

H_WHITE = flat_mat("hud_bialy", (1, 1, 1))
H_GREY = flat_mat("hud_szary", (0.78, 0.78, 0.78))
H_CLAIM = flat_mat("hud_twierdzenie", (1.0, 0.45, 0.58))
H_GOLD = flat_mat("hud_potwierdzone", GOLD)
H_PANEL = flat_mat("hud_panel", (0.02, 0.025, 0.035), alpha=0.72)
H_PANEL2 = flat_mat("hud_panel_mocny", (0.018, 0.022, 0.032), alpha=0.94)
H_LINE_C = flat_mat("hud_linia_twierdzenie", (1.0, 0.45, 0.58))
H_LINE_G = flat_mat("hud_linia_potwierdzone", GOLD)
H_DARK = flat_mat("hud_ciemny", (0.10, 0.08, 0.06))
H_WATER = flat_mat("hud_woda", (0.02, 0.07, 0.28))

# ---------------------------------------------------------------- geometria


def mk(name, bm, c, loc=(0, 0, 0), m=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    c.objects.link(ob)
    if m:
        me.materials.append(m)
    return ob


def box(name, center, size, c, m):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    return mk(name, bm, c, center, m)


def cyl(name, center, r, depth, c, m, segs=32):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r, radius2=r, depth=depth)
    return mk(name, bm, c, center, m)


def tube(name, p0, p1, r, c, m, segs=12):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bm = bmesh.new()
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r, radius2=r, depth=d.length, matrix=rot)
    return mk(name, bm, c, (p0 + p1) / 2, m)


def wire_copy(ob, name, m, thick):
    w = bpy.data.objects.new(name, ob.data.copy())
    w.location = ob.location
    w.data.materials.clear()
    w.data.materials.append(m)
    mod = w.modifiers.new("krawedzie", "WIREFRAME")
    mod.thickness = thick
    mod.use_replace = True
    mod.use_even_offset = True
    for c in ob.users_collection:
        c.objects.link(w)
    return w


def curve_to_mesh(cob, name, c, m):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(cob.evaluated_get(dg))
    me.name = name
    ob = bpy.data.objects.new(name, me)
    ob.location = cob.location
    c.objects.link(ob)
    me.materials.clear()
    me.materials.append(m)
    bpy.data.objects.remove(cob, do_unlink=True)
    return ob


def passage(name, a, b, w, hgt, c, m):
    """Korytarz o przekroju prostokątnym: a, b = końce osi posadzki, hgt = wysokość pionowa."""
    a, b = Vector(a), Vector(b)
    d = b - a
    side = Vector((-d.y, d.x, 0))
    if side.length < 1e-6:
        side = Vector((1, 0, 0))
    side = side.normalized() * (w / 2)
    up = Vector((0, 0, hgt))
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in (a - side, a + side, a + side + up, a - side + up,
                                    b - side, b + side, b + side + up, b - side + up)]
    for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mk(name, bm, c, (0, 0, 0), m)


def gable(name, x0, x1, y0, y1, z0, wall_h, apex_h, c, m):
    """Komora ze stropem dwuspadowym; kalenica wzdłuż osi X (wschód–zachód)."""
    ym = (y0 + y1) / 2
    bm = bmesh.new()
    p = [bm.verts.new(v) for v in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z0 + wall_h), (x1, y0, z0 + wall_h), (x1, y1, z0 + wall_h), (x0, y1, z0 + wall_h),
        (x0, ym, z0 + apex_h), (x1, ym, z0 + apex_h))]
    for f in ((0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 9, 5), (3, 0, 4, 8, 7),
              (4, 5, 9, 8), (6, 7, 8, 9)):
        bm.faces.new([p[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mk(name, bm, c, (0, 0, 0), m)


# ---- potwierdzone: piramida
h = PYR_BASE / 2
FACE_TAN = PYR_HEIGHT / h
bm = bmesh.new()
vs = [bm.verts.new(p) for p in ((-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0), (0, 0, PYR_HEIGHT))]
bm.faces.new((vs[3], vs[2], vs[1], vs[0]))
for i in range(4):
    bm.faces.new((vs[i], vs[(i + 1) % 4], vs[4]))
pyr = mk("Piramida_Chefrena", bm, C_POTW, m=M_PYR)
wire_copy(pyr, "Piramida_Chefrena_krawedzie", M_PYR_EDGE, 1.5)

# ---- potwierdzone: górny system (wejście w ścianie północnej, korytarz zstępujący w granicie, zapadnia)
ex = PASS_X
up_y = h - UPPER_ENTRANCE_Z / FACE_TAN
UP_ENTRY = Vector((ex, up_y, UPPER_ENTRANCE_Z))
up_run = (UPPER_ENTRANCE_Z - HORIZ_Z) / math.tan(math.radians(UPPER_ANGLE))
UP_BOTTOM = Vector((ex, up_y - up_run, HORIZ_Z))
PORT_Y = UP_BOTTOM.y - PORTCULLIS_AFTER
PIT_Y = PORT_Y - PIT_T_AFTER
passage("Korytarz_gorny_zstepujacy", UP_ENTRY, UP_BOTTOM, PASS_W, UPPER_H, C_POTW, M_KNOWN)
passage("Korytarz_gorny_poziomy", UP_BOTTOM, (ex, BURIAL_Y[1], HORIZ_Z), PASS_W, HORIZ_H, C_POTW, M_KNOWN)
box("Zapadnia_granitowa", (ex, PORT_Y, HORIZ_Z + 0.95), (PASS_W + 0.5, 0.37, 1.9), C_POTW, M_GRANITE)

# ---- potwierdzone: komora grobowa (wykuta w skale, strop dwuspadowy z belek wapiennych) i sarkofag
gable("Komora_grobowa_Belzoniego", BURIAL_X[0], BURIAL_X[1], BURIAL_Y[0], BURIAL_Y[1], HORIZ_Z,
      BURIAL_WALL, BURIAL_APEX, C_POTW, M_CHAMBER)
BURIAL_C = Vector(((BURIAL_X[0] + BURIAL_X[1]) / 2, (BURIAL_Y[0] + BURIAL_Y[1]) / 2, HORIZ_Z + BURIAL_APEX / 2))
sx0 = BURIAL_X[0] + 1.09
sy1 = BURIAL_Y[1] - 1.08
box("Sarkofag", (sx0 + SARC[0] / 2, sy1 - SARC[1] / 2, HORIZ_Z - SARC[2] / 2 + 0.25), SARC, C_POTW, M_GRANITE)

# ---- potwierdzone: dolny system (wejście w bruku, zejście, odcinek poziomy, podejście do górnego korytarza)
LOW_ENTRY = Vector((ex, h + LOWER_ENTRY_NORTH, 0.0))
low_run = -LOWER_Z / math.tan(math.radians(LOWER_DESC_ANGLE))
LOW_BOTTOM = Vector((ex, LOW_ENTRY.y - low_run, LOWER_Z))
asc_run = (HORIZ_Z - LOWER_Z) / math.tan(math.radians(LOWER_ASC_ANGLE))
LOW_END = Vector((ex, PIT_Y + asc_run, LOWER_Z))
JUNCTION = Vector((ex, PIT_Y, HORIZ_Z))
passage("Korytarz_dolny_zstepujacy", LOW_ENTRY, LOW_BOTTOM, PASS_W, LOWER_SLOPE_H, C_POTW, M_KNOWN)
passage("Korytarz_dolny_poziomy", LOW_BOTTOM, LOW_END, PASS_W, LOWER_H, C_POTW, M_KNOWN)
passage("Korytarz_dolny_wstepujacy", LOW_END, JUNCTION, PASS_W, LOWER_SLOPE_H, C_POTW, M_KNOWN)
print("DOLNY ODCINEK POZIOMY: dlugosc %.1f m" % (LOW_BOTTOM.y - LOW_END.y))
# komora boczna: po zachodniej stronie, wejście pośrodku jej wschodniej ściany, rampa w połowie odcinka poziomego
ramp_y = (LOW_BOTTOM.y + LOW_END.y) / 2
RAMP_A = Vector((ex - PASS_W / 2, ramp_y, LOWER_Z))
RAMP_B = Vector((ex - PASS_W / 2 - RAMP_LEN, ramp_y, LOWER_Z - RAMP_DROP))
passage("Rampa_do_komory_bocznej", RAMP_A, RAMP_B, 1.04, 1.2, C_POTW, M_KNOWN)
gable("Komora_boczna", RAMP_B.x - SUBSID[0], RAMP_B.x, ramp_y - SUBSID[1] / 2, ramp_y + SUBSID[1] / 2,
      RAMP_B.z, SUBSID_WALL, SUBSID[2], C_POTW, M_CHAMBER)
SUBSID_C = Vector((RAMP_B.x - SUBSID[0] / 2, ramp_y, RAMP_B.z + 1.3))

# ---- twierdzenia: 5 struktur "Zed" w środku piramidy, nad komorą Belzoniego: 2 z przodu, 2 z tyłu, 1 w środku
CELLS = [(AX - ROW_DX, SHAFT_Y[1]), (AX - ROW_DX, SHAFT_Y[2]), (AX + ROW_DX, SHAFT_Y[1]),
         (AX + ROW_DX, SHAFT_Y[2]), (AX, BURIAL_C.y)]
CELL_TOP = CELL_Z + CELL_LEVELS * CELL_LEVEL_H + (CELL_LEVELS - 1) * CELL_GAP
for i, (x, y) in enumerate(CELLS):
    for k in range(CELL_LEVELS):
        z0 = CELL_Z + k * (CELL_LEVEL_H + CELL_GAP)
        box(f"Zed_{i + 1}_poziom_{k + 1}", (x, y, z0 + CELL_LEVEL_H / 2), (CELL_SIZE[0], CELL_SIZE[1], CELL_LEVEL_H),
            C_TWIERDZ, M_UPPER)
        # wystająca płyta nad każdym poziomem (jak stropy komór odciążających w "Zedzie" Cheopsa)
        box(f"Zed_{i + 1}_plyta_{k + 1}", (x, y, z0 + CELL_LEVEL_H + CELL_GAP / 2),
            (CELL_SIZE[0] + 3.0, CELL_SIZE[1] + 2.0, CELL_GAP), C_TWIERDZ, M_ZED_SLAB)
    gable(f"Zed_{i + 1}_dach", x - CELL_SIZE[0] / 2, x + CELL_SIZE[0] / 2, y - CELL_SIZE[1] / 2,
          y + CELL_SIZE[1] / 2, CELL_TOP + CELL_GAP, 0.5, CELL_ROOF, C_TWIERDZ, M_UPPER)
ZED_TOP = CELL_TOP + CELL_GAP + CELL_ROOF

# ---- twierdzenia: rama korytarzy przy krawędziach podstawy i krata łącząca "Zedy" (wg modelu autorów)
xw, xe, ys, yn = AX - ROW_DX, AX + ROW_DX, SHAFT_Y[1], SHAFT_Y[2]
R = RING
LINKS = [((-R, -R), (R, -R)), ((R, -R), (R, R)), ((R, R), (-R, R)), ((-R, R), (-R, -R)),   # rama
         ((xw, -R), (xw, R)), ((xe, -R), (xe, R)),                                       # dwie rury północ–południe
         ((-R, ys), (R, ys)), ((-R, yn), (R, yn)),                                       # dwie rury zachód–wschód
         ((xw, BURIAL_C.y), (xe, BURIAL_C.y))]                                           # dojście do środkowego "Zeda"
for i, (a, b) in enumerate(LINKS):
    tube(f"Korytarz_ramy_{i + 1:02d}", (a[0], a[1], GRID_Z), (b[0], b[1], GRID_Z), GRID_R, C_TWIERDZ, M_SPIRAL, segs=10)
# dwie "skrzynie" przy zachodnim boku, belka między nimi i pięć "haków"
for nm, (cxy, size) in (("Skrzynia_zachodnia_wieksza", ROOM_BIG), ("Skrzynia_zachodnia_mniejsza", ROOM_SMALL)):
    box(nm, (cxy[0], cxy[1], GRID_Z + size[2] / 2), size, C_TWIERDZ, M_UPPER)
beam_x = ROOM_BIG[0][0]
beam_z = GRID_Z + 4.0
tube("Belka_zachodnia", (beam_x, ROOM_SMALL[0][1], beam_z), (beam_x, ROOM_BIG[0][1], beam_z), 1.2, C_TWIERDZ, M_SPIRAL,
     segs=10)
for i, y in enumerate(HOOK_Y):
    tube(f"Hak_{i + 1}_a", (beam_x, y, beam_z), (beam_x, y, beam_z - 8), 0.8, C_TWIERDZ, M_SPIRAL, segs=8)
    tube(f"Hak_{i + 1}_b", (beam_x, y, beam_z - 8), (beam_x - 5, y, beam_z - 8), 0.8, C_TWIERDZ, M_SPIRAL, segs=8)
    tube(f"Hak_{i + 1}_c", (beam_x - 5, y, beam_z - 8), (beam_x - 5, y, beam_z - 4), 0.8, C_TWIERDZ, M_SPIRAL, segs=8)

# ---- twierdzenia: 8 szybów (rur) ze spiralą, w dwóch rzędach północ–południe
shaft_len = SHAFT_TOP - SHAFT_BOTTOM
zmid = (SHAFT_TOP + SHAFT_BOTTOM) / 2
SHAFTS = []
n = 0
for x in (AX - ROW_DX, AX + ROW_DX):
    for y in SHAFT_Y:
        n += 1
        SHAFTS.append((x, y))
        cyl(f"Szyb_{n}", (x, y, zmid), SHAFT_RADIUS, shaft_len, C_TWIERDZ, M_SHAFT)
        cu = bpy.data.curves.new(f"Spirala_{n}_krzywa", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = SPIRAL_TUBE
        cu.bevel_resolution = 1
        cu.use_fill_caps = True
        sp = cu.splines.new("POLY")
        steps_per_turn = 16
        total = int(shaft_len / SPIRAL_PITCH * steps_per_turn)
        sp.points.add(total)
        phase = (n * 0.7) % (2 * math.pi)
        for i in range(total + 1):
            t = i / steps_per_turn * 2 * math.pi + phase
            z = SHAFT_TOP - i / total * shaft_len - zmid
            sp.points[i].co = (SPIRAL_RADIUS * math.cos(t), SPIRAL_RADIUS * math.sin(t), z, 1)
        cob = bpy.data.objects.new(f"Spirala_{n}_tmp", cu)
        cob.location = (x, y, zmid)
        C_TWIERDZ.objects.link(cob)
        curve_to_mesh(cob, f"Spirala_{n}", C_TWIERDZ, M_SPIRAL)
        bpy.data.curves.remove(cu)

# ---- twierdzenia: 2 "skrzynie" 80 m; do każdej wchodzą 4 szyby
CUBE_Y = ((SHAFT_Y[0] + SHAFT_Y[1]) / 2, (SHAFT_Y[2] + SHAFT_Y[3]) / 2)
for i, yc in enumerate(CUBE_Y):
    cube = box(f"Skrzynia_{'poludniowa' if yc < 0 else 'polnocna'}",
               (AX, yc, SHAFT_BOTTOM - CUBE_SIDE / 2), (CUBE_SIDE,) * 3, C_TWIERDZ, M_CUBE)
    wire_copy(cube, cube.name + "_krawedzie", M_CUBE_EDGE, 1.6)
    # kwadratowe otwory w ścianach, jak w modelu autorów
    zc = SHAFT_BOTTOM - CUBE_SIDE / 2
    win = CUBE_SIDE * 0.5
    for j, (dx, dy, sx_, sy_) in enumerate(((CUBE_SIDE / 2, 0, 0.6, win), (-CUBE_SIDE / 2, 0, 0.6, win),
                                            (0, CUBE_SIDE / 2, win, 0.6), (0, -CUBE_SIDE / 2, win, 0.6))):
        wbox = box(f"{cube.name}_otwor_{j + 1}", (AX + dx, yc + dy, zc), (sx_, sy_, win), C_TWIERDZ, M_CUBE_HOLE)
        wire_copy(wbox, wbox.name + "_krawedzie", M_CUBE_EDGE, 1.0)
    # przerywana linia do ok. 2 km (zasięg ze streszczenia zespołu i relacji prasowych)
    z = SHAFT_BOTTOM - CUBE_SIDE
    k = 0
    while z - 30 > CLAIMED_MAX_DEPTH:
        k += 1
        tube(f"Zasieg_2km_{i + 1}_{k:02d}", (AX, yc, z - 10), (AX, yc, z - 40), 2.2, C_TWIERDZ, M_DASH, segs=8)
        z -= 60
    cyl(f"Zasieg_2km_{i + 1}_znacznik", (AX, yc, CLAIMED_MAX_DEPTH), 14.0, 3.0, C_TWIERDZ, M_DASH)

# ---- twierdzenia: woda i strefa "miasta" ok. 1200 m (dwie wersje zasięgu: do kadrów z wycięciem i pełna)
cut_c = ((CUT_X + G_HALF) / 2, (CUT_Y - G_HALF) / 2)
cut_s = (G_HALF - CUT_X, G_HALF + CUT_Y)
for c, cxy, sxy, suf in ((C_TW_CUT, cut_c, cut_s, "_przekroj"), (C_TW_FULL, (0, 0), (2 * G_HALF, 2 * G_HALF), "")):
    box("Woda_wg_modelu_autorow" + suf, (cxy[0], cxy[1], WATER_Z), (sxy[0], sxy[1], 1.5), c, M_WATER)
    box("Strefa_1200m_miasto" + suf, (cxy[0], cxy[1], DEEP_ZONE_Z), (sxy[0], sxy[1], DEEP_ZONE_H), c, M_ZONE)

# ---- grunt: przekrój w kształcie litery L (do kadrów)
for name, zt, zb, _ in LAYERS:
    zc, hz = (zt + zb) / 2, zt - zb
    box(f"Grunt_zachod_{name}", ((-G_HALF + CUT_X) / 2, 0, zc), (CUT_X + G_HALF, 2 * G_HALF, hz), C_GRUNT, M_LAYERS[name])
    box(f"Grunt_polnoc_{name}", ((CUT_X + G_HALF) / 2, (CUT_Y + G_HALF) / 2, zc),
        (G_HALF - CUT_X, G_HALF - CUT_Y, hz), C_GRUNT, M_LAYERS[name])
box("Grunt_wyciecie_skala_przezroczysta", ((CUT_X + G_HALF) / 2, (CUT_Y - G_HALF) / 2, G_BOTTOM / 2),
    (G_HALF - CUT_X, G_HALF + CUT_Y, -G_BOTTOM), C_GRUNT, M_GHOST)
box("Grunt_wyciecie_powierzchnia", ((CUT_X + G_HALF) / 2, (CUT_Y - G_HALF) / 2, -0.6),
    (G_HALF - CUT_X, G_HALF + CUT_Y, 1.0), C_GRUNT, M_SURFACE)

# ---- grunt: wersja przezroczysta (film obrotowy i .glb)
gb = box("Grunt_blok_przezroczysty", (0, 0, G_BOTTOM / 2), (2 * G_HALF, 2 * G_HALF, -G_BOTTOM), C_GRUNT_GLB, M_GHOST)
wire_copy(gb, "Grunt_blok_krawedzie", M_GEDGE, 2.0)
box("Grunt_powierzchnia", (0, 0, -0.6), (2 * G_HALF, 2 * G_HALF, 1.0), C_GRUNT_GLB, M_SURFACE)
for name, zt, zb, _ in LAYERS[1:]:
    box(f"Granica_warstw_{name}", (0, 0, zt), (2 * G_HALF, 2 * G_HALF, 0.5), C_GRUNT_GLB, M_LAYER_PLANE)

# ---- skala głębokości
RX, RY = CUT_X + 6, -G_HALF + 30
tube("Skala_pion", (RX, RY, 0), (RX, RY, CLAIMED_MAX_DEPTH), 1.8, C_SKALA, M_RULER, segs=8)
diag = Vector((1, 1, 0)).normalized()
labels = []
for d in range(0, 2001, 100):
    major = d % 500 == 0
    ln = 30 if major else 14
    p0 = Vector((RX, RY, -d))
    tube(f"Skala_kreska_{d:04d}", p0, p0 + diag * ln, 1.4 if major else 0.9, C_SKALA, M_RULER, segs=6)
    if major:
        labels.append((d, f"{d} m" if d else "0 m", M_RULER))
labels.append((648, "648 m", M_RULER_RED))
tube("Skala_kreska_648", Vector((RX, RY, -648)), Vector((RX, RY, -648)) + diag * 34, 1.8, C_SKALA, M_RULER_RED, segs=6)

RULER_TEXTS = []
for d, body, m in labels:
    cu = bpy.data.curves.new(f"Skala_napis_{d}", "FONT")
    cu.body = body if d == 0 else "\u2212" + body
    if FONT:
        cu.font = FONT
    cu.size = 34
    cu.align_y = "CENTER"
    ob = bpy.data.objects.new(f"Skala_napis_{d}", cu)
    ob.location = Vector((RX, RY, -d)) + diag * 42
    ob.rotation_euler = (math.radians(90), 0, math.radians(45))
    C_SKALA.objects.link(ob)
    cu.materials.append(m)
    RULER_TEXTS.append(ob)

# obiekty półprzezroczyste nie rzucają cieni (inaczej EEVEE daje ziarniste cienie na "szklanej" skale)
NO_SHADOW_MATS = {M_SPIRAL, M_PYR, M_GHOST, M_SURFACE, M_LAYER_PLANE, M_SHAFT, M_CUBE, M_UPPER, M_DASH, M_GEDGE, M_PYR_EDGE,
                  M_CHAMBER, M_WATER, M_ZONE, M_ZED_SLAB, M_CUBE_HOLE}
for ob in bpy.data.objects:
    mats = set(ob.data.materials) if ob.type in ("MESH", "FONT") else set()
    if mats & NO_SHADOW_MATS or ob.users_collection[0] == C_SKALA:
        try:
            ob.visible_shadow = False
        except AttributeError:
            pass

# ---------------------------------------------------------------- światło i tło
world = bpy.data.worlds.new("Tlo")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.018, 0.022, 0.032, 1)
bg.inputs["Strength"].default_value = 1.0
# delikatne światło otoczenia przez osobny obiekt-światło (tło zostaje ciemne)
sun = bpy.data.objects.new("Slonce", bpy.data.lights.new("Slonce", "SUN"))
sun.data.energy = 3.2
sun.data.angle = math.radians(2)
sun.data.use_shadow = False  # cienie tylko zaciemniały czytelność schematu
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
C_SWIATLO.objects.link(sun)
fill = bpy.data.objects.new("Swiatlo_wypelniajace", bpy.data.lights.new("Swiatlo_wypelniajace", "SUN"))
fill.data.energy = 1.0
fill.data.use_shadow = False
fill.rotation_euler = (math.radians(-60), math.radians(0), math.radians(-150))
C_SWIATLO.objects.link(fill)

# ---------------------------------------------------------------- kamery


def make_cam(name, lens=35, ortho=None, shift_x=0.0):
    cd = bpy.data.cameras.new(name)
    cd.clip_start = 0.05
    cd.clip_end = 30000
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    cd.shift_x = shift_x
    cam = bpy.data.objects.new(name, cd)
    C_SWIATLO.objects.link(cam)
    return cam


def look_at(cam, loc, target):
    cam.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def orbit(target, direction, dist):
    d = Vector(direction).normalized()
    return Vector(target) + d * dist


CAMS = {}
CAMS["ogolny"] = make_cam("Kamera_01_ogolny", lens=35)
look_at(CAMS["ogolny"], orbit((40, -40, -930), (1, -1.15, 0.62), 4200), (40, -40, -930))
CAMS["przekroj"] = make_cam("Kamera_02_przekroj", ortho=1800)
CAMS["przekroj"].location = (60, -3000, -335)
CAMS["przekroj"].rotation_euler = (math.radians(90), 0, 0)
CAMS["szyby"] = make_cam("Kamera_03_szyby", lens=26)
look_at(CAMS["szyby"], (310, -400, 150), (0, 0, -70))
CAMS["opis"] = make_cam("Kamera_04_opis", lens=35, shift_x=0.17)
look_at(CAMS["opis"], orbit((40, -40, -1000), (1, -1.2, 0.55), 5300), (40, -40, -1000))
CAMS["opis"].data.shift_y = 0.025
KOM_T = (PASS_X, 55, 1)
KOM_W = 175.0  # szerokość kadru w metrach na głębokości korytarzy
# teleobiektyw z daleka (prawie rzut prostokątny); w kamerze ORTHO o dowolnym obrocie nakładki gubiły głębię
CAMS["komory"] = make_cam("Kamera_05_komory", lens=600)
look_at(CAMS["komory"], orbit(KOM_T, (1, 0.22, 0.30), KOM_W * 600 / 36), KOM_T)
CAMS["komory"]["hud_d"] = 50.0

# kamera filmu obrotowego na osi obracającego się "uchwytu"
pivot = bpy.data.objects.new("Obrot_os", None)
pivot.location = (0, 0, -900)
C_SWIATLO.objects.link(pivot)
CAMS["obrot"] = make_cam("Kamera_06_obrot", lens=35)
CAMS["obrot"].parent = pivot
look_at(CAMS["obrot"], Vector((0, -3600, 1350)), Vector((0, 0, 0)))
FRAMES = args.fps * args.seconds
scene.frame_start, scene.frame_end = 1, FRAMES
scene.render.fps = args.fps
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert("rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, 2 * math.pi)  # pełny obrót
pivot.keyframe_insert("rotation_euler", index=2, frame=FRAMES + 1)
try:
    for fc in pivot.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
except Exception:
    # Blender 5: kanały w warstwach akcji
    try:
        for layer in pivot.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "LINEAR"
    except Exception as e:
        print("Uwaga: nie ustawiono interpolacji liniowej:", e)

# ---------------------------------------------------------------- nakładki (napisy w kadrze)


ORTHO_DZ = 200.0


def hud_ctx(cam):
    D = cam.get("hud_d", 1.0)  # odległość nakładki od kamery; większa dla teleobiektywu
    if cam.data.type == "ORTHO":
        hw = cam.data.ortho_scale / 2
    else:
        hw = D * cam.data.sensor_width / (2 * cam.data.lens)
    return D, hw, hw * RES[1] / RES[0]


def hud_pt(cam, u, v, dz=0.0):
    D, hw, hh = hud_ctx(cam)
    su, sv = cam.data.shift_x, cam.data.shift_y
    if cam.data.type != "ORTHO":
        dz *= D
        scale = (D + dz) / D
    else:
        scale = 1.0
        dz *= ORTHO_DZ  # w rzucie prostokątnym głębia jest liniowa: warstwy napisów trzeba rozsunąć
    return Vector((((u - 0.5) * 2 * hw + su * 2 * hw) * scale, ((v - 0.5) * 2 * hh + sv * 2 * hw) * scale, -(D + dz)))


def px(cam, p):
    return p * 2 * hud_ctx(cam)[1] / RES[0]


def hud_obj(cam, c, ob):
    c.objects.link(ob)
    ob.parent = cam
    for attr in ("visible_shadow",):
        try:
            setattr(ob, attr, False)
        except Exception:
            pass
    return ob


def hud_text(cam, c, body, u, v, size_px, m, bold=False, align_x="LEFT", align_y="TOP", panel=False, pad_px=14,
             panel_m=None):
    cu = bpy.data.curves.new("hud_tekst", "FONT")
    cu.body = body
    f = FONT_B if bold else FONT
    if f:
        cu.font = f
    cu.size = px(cam, size_px)
    cu.space_line = 1.15
    cu.align_x = align_x
    cu.align_y = align_y
    ob = bpy.data.objects.new("hud_tekst", cu)
    ob.location = hud_pt(cam, u, v)
    cu.materials.append(m)
    hud_obj(cam, c, ob)
    if panel:
        bpy.context.view_layer.update()
        bb = [Vector(b) for b in ob.bound_box]
        x0, x1 = min(b.x for b in bb), max(b.x for b in bb)
        y0, y1 = min(b.y for b in bb), max(b.y for b in bb)
        pad = px(cam, pad_px)
        hud_rect(cam, c, ob.location.x + x0 - pad, ob.location.y + y0 - pad,
                 ob.location.x + x1 + pad, ob.location.y + y1 + pad, panel_m or H_PANEL, dz=0.002)
    return ob


def hud_rect(cam, c, x0, y0, x1, y1, m, dz=0.001):
    D = hud_ctx(cam)[0]
    dz *= ORTHO_DZ if cam.data.type == "ORTHO" else D
    s = (D + dz) / D if cam.data.type != "ORTHO" else 1.0
    bm = bmesh.new()
    vs = [bm.verts.new((x * s, y * s, -(D + dz))) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    bm.faces.new(vs)
    return hud_obj(cam, c, mk_nolink("hud_panel", bm, m))


def mk_nolink(name, bm, m):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    return bpy.data.objects.new(name, me)


def project(cam, world_pt):
    bpy.context.view_layer.update()
    co = world_to_camera_view(scene, cam, Vector(world_pt))
    return co.x, co.y


def hud_leader(cam, c, u0, v0, world_pt, m, width_px=2.4, dot_px=7):
    u1, v1 = project(cam, world_pt)
    a, b = hud_pt(cam, u0, v0, -0.0005), hud_pt(cam, u1, v1, -0.0005)
    d = (b - a)
    nrm = Vector((-d.y, d.x, 0)).normalized() * px(cam, width_px) / 2
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in (a - nrm, b - nrm, b + nrm, a + nrm)]
    bm.faces.new(vs)
    hud_obj(cam, c, mk_nolink("hud_linia", bm, m))
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=20, radius=px(cam, dot_px))
    dot = mk_nolink("hud_punkt", bm, m)
    dot.location = b
    hud_obj(cam, c, dot)


def hud_callout(cam, c, txt, u, v, world_pt, m_txt, m_line, size=22, above=True, du=0.012):
    """Podpis w ramce z linią do punktu; above=True, gdy podpis leży nad wskazywanym miejscem."""
    lines = txt.count("\n") + 1
    hud_text(cam, c, txt, u, v, size, m_txt, panel=True, pad_px=9, panel_m=H_PANEL2)
    lh = size * 1.15 / RES[1]
    v0 = v - lines * lh - 0.012 if above else v + 0.012
    hud_leader(cam, c, u + du, v0, world_pt, m_line, width_px=2.0, dot_px=5)


def hud_legend(cam, c, u=0.025, v=0.055, only_confirmed=False):
    sw = px(cam, 22)
    rows = [(H_GOLD, "potwierdzone: piramida, znane komory i korytarze")]
    if not only_confirmed:
        rows.append((H_CLAIM, "twierdzenie Malangi i Biondiego (2025, bez recenzji)"))
    for i, (m, txt) in enumerate(rows):
        vv = v + (len(rows) - 1 - i) * 0.042
        p = hud_pt(cam, u, vv)
        hud_rect(cam, c, p.x, p.y - sw / 2, p.x + sw, p.y + sw / 2, m, dz=-0.0005)
        hud_text(cam, c, txt, u + 0.02, vv, 24, H_WHITE, align_y="CENTER")
    a = hud_pt(cam, u - 0.01, v - 0.03)
    b = hud_pt(cam, u + 0.36, v + 0.03 + (len(rows) - 1) * 0.042)
    hud_rect(cam, c, a.x, a.y, b.x, b.y, H_PANEL, dz=0.002)


HUDS = {}


def new_hud(key):
    c = coll("NAKLADKA_" + key, C_SWIATLO)
    HUDS[key] = c
    return c


TAG = "Pod piramidą Chefrena – według Malangi i Biondiego (2025, bez recenzji)"
FOOT = "model poglądowy · uleszka.net · jokerwader"
for key in ("ogolny", "przekroj", "szyby"):
    cam, c = CAMS[key], new_hud(key)
    hud_text(cam, c, TAG, 0.025, 0.955, 30, H_WHITE, bold=True, panel=True)
    hud_legend(cam, c)
    hud_text(cam, c, FOOT, 0.975, 0.03, 20, H_GREY, align_x="RIGHT", align_y="BOTTOM")

XE, XW = AX + ROW_DX, AX - ROW_DX

# dodatkowe podpisy w przekroju
cam, c = CAMS["przekroj"], HUDS["przekroj"]
hud_text(cam, c, "przekrój zachód–wschód, widok od południa; warstwy skały schematyczne",
         0.025, 0.905, 22, H_GREY)
for txt, x, z in (("wapień formacji\nMokattam (eocen)", CUT_X - 12, -60),
                  ("starsze wapienie i margle", CUT_X - 12, -400),
                  ("głębsze skały osadowe", G_HALF - 12, -790)):
    u, v = project(cam, (x, -G_HALF, z))
    hud_text(cam, c, txt, u, v, 20, H_DARK, align_x="RIGHT", align_y="CENTER")
u, v = project(cam, (-PYR_BASE / 2 - 8, -G_HALF, 60))
hud_text(cam, c, "Piramida Chefrena\n(potwierdzone)", u, v, 22, H_GOLD, align_x="RIGHT", align_y="CENTER")
u, v = project(cam, (PYR_BASE / 2 + 6, -G_HALF, 34))
hud_text(cam, c, "5 struktur „Zed” w środku\npiramidy (twierdzenie)", u, v, 22, H_CLAIM, align_y="CENTER")
u, v = project(cam, (XE + 40, -G_HALF, -250))
hud_text(cam, c, "8 szybów w dwóch rzędach,\nśrednica 10–12 m, do 648 m\n(od południa widać 2 rzędy)", u, v, 22,
         H_CLAIM, align_y="CENTER", panel=True, pad_px=10)
u, v = project(cam, (G_HALF - 12, -G_HALF, WATER_Z + 18))
hud_text(cam, c, "woda wg modelu autorów (głębokość nie podana)", u, v, 22, H_WATER, bold=True, align_x="RIGHT",
         align_y="CENTER")
u, v = project(cam, (AX + CUBE_SIDE / 2 + 16, -G_HALF, SHAFT_BOTTOM - 40))
hud_text(cam, c, "2 „skrzynie” o boku 80 m\n(od południa widać jedną)", u, v, 22, H_CLAIM, align_y="CENTER",
         panel=True, pad_px=10)

# podpisy w zbliżeniu
cam, c = CAMS["szyby"], HUDS["szyby"]
RX0 = 0.70
hud_text(cam, c, "Piramida Chefrena, znane komory\ni korytarze (potwierdzone)", RX0, 0.90, 24, H_GOLD, panel=True,
         pad_px=10)
hud_leader(cam, c, RX0 - 0.006, 0.875, (20, -20, 70), H_LINE_G)
hud_leader(cam, c, RX0 - 0.006, 0.875, BURIAL_C, H_LINE_G)
hud_text(cam, c, "5 struktur „Zed” nad komorą Belzoniego:\n5 poziomów i skośny dach, 2 z przodu,\n2 z tyłu, 1 w środku (twierdzenie)",
         RX0, 0.745, 24, H_CLAIM, panel=True, pad_px=10)
hud_leader(cam, c, RX0 - 0.006, 0.705, (XE, SHAFT_Y[1], ZED_TOP - 4), H_LINE_C)
hud_text(cam, c, "rama korytarzy przy podstawie i 2 skrzynie\nprzy zachodnim boku (twierdzenie)", RX0, 0.575, 24, H_CLAIM,
         panel=True, pad_px=10)
hud_leader(cam, c, RX0 - 0.006, 0.55, (RING, -RING + 40, GRID_Z), H_LINE_C)
hud_text(cam, c, "8 szybów (rur) o średnicy 10–12 m,\notoczonych spiralą, od podstawy\ndo 648 m w głąb (twierdzenie)",
         RX0, 0.435, 24, H_CLAIM, panel=True, pad_px=10)
hud_leader(cam, c, RX0 - 0.006, 0.395, (XE, SHAFT_Y[0], -230), H_LINE_C)

# kadr z opisami
cam, c = CAMS["opis"], new_hud("opis")
hud_text(cam, c, "Co według Malangi i Biondiego jest pod piramidą Chefrena?", 0.025, 0.955, 44, H_WHITE, bold=True)
hud_text(cam, c, "Ilustracja twierdzeń ze streszczenia i konferencji (marzec 2025). Nie jest to potwierdzone odkrycie.",
         0.025, 0.895, 26, H_GREY)
LX = 0.60
hud_text(cam, c, "Potwierdzone", LX, 0.80, 28, H_GOLD, bold=True)
hud_text(cam, c, "Piramida Chefrena: wys. 143,5 m, bok 215 m", LX, 0.765, 24, H_WHITE)
hud_leader(cam, c, LX - 0.006, 0.752, (-30, -30, 45), H_LINE_G)
hud_text(cam, c, "Znane komory i korytarze, wykute w skale u podstawy", LX, 0.725, 24, H_WHITE)
hud_leader(cam, c, LX - 0.006, 0.712, BURIAL_C, H_LINE_G)
hud_text(cam, c, "Według Malangi i Biondiego (2025, bez recenzji)", LX, 0.655, 28, H_CLAIM, bold=True)
CL = [
    ("5 struktur „Zed” w środku piramidy, nad komorą Belzoniego\n(5 poziomów, skośny dach), połączonych korytarzami",
     (XE, SHAFT_Y[1], ZED_TOP - 4), 0.615),
    ("8 pionowych szybów w dwóch rzędach, średnica 10–12 m,\notoczonych spiralą, do 648 m w głąb",
     (XE, SHAFT_Y[0], -330), 0.550),
    ("woda poniżej pewnego poziomu (głębokość nie podana)", (250, -250, WATER_Z), 0.485),
    ("2 „skrzynie” o boku ok. 80 m; do każdej wchodzą 4 szyby",
     (AX + CUBE_SIDE / 2, CUBE_Y[0] - 10, SHAFT_BOTTOM - 45), 0.445),
    ("ok. 1200 m: jasne plamy opisane jako „miasto”", (250, -250, DEEP_ZONE_Z), 0.405),
    ("do ok. 2 km – struktury pod trzema piramidami (streszczenie)", (AX, CUBE_Y[0], CLAIMED_MAX_DEPTH), 0.365),
]
for txt, wp, vv in CL:
    hud_text(cam, c, txt, LX, vv, 24, H_WHITE)
    hud_leader(cam, c, LX - 0.006, vv - 0.013, wp, H_LINE_C)
hud_text(cam, c,
         "Zastrzeżenia: praca nie przeszła recenzji naukowej. Geofizycy (m.in. L. Conyers, S. Parcak)\n"
         "wskazują, że radar SAR nie przenika skały na setki metrów; Z. Hawass: brak dowodów.\n"
         "Wcześniejszy artykuł autorów o piramidzie Cheopsa (Remote Sensing, 2022) wycofano w 2026 r.",
         LX - 0.01, 0.275, 21, H_GREY, panel=True, pad_px=16)
hud_legend(cam, c)
hud_text(cam, c, "liczby z konferencji, układ wg modelu 3D autorów, reszta szacunkowa · " + FOOT, 0.975, 0.03, 20,
         H_GREY, align_x="RIGHT", align_y="BOTTOM")
# panel pod blokiem etykiet
a, b = hud_pt(cam, LX - 0.022, 0.325), hud_pt(cam, 0.985, 0.835)
hud_rect(cam, c, a.x, a.y, b.x, b.y, H_PANEL, dz=0.002)

# kadr: znane komory i korytarze (tylko potwierdzone)
cam, c = CAMS["komory"], new_hud("komory")
hud_text(cam, c, "Znane komory i korytarze piramidy Chefrena (potwierdzone)", 0.025, 0.955, 38, H_WHITE, bold=True)
hud_text(cam, c, "Widok od wschodu, północ po prawej. Wymiary wg pomiarów W.M.F. Petriego (1883) oraz V. Maragioglia"
                 " i C. Rinaldiego (1966).", 0.025, 0.9, 22, H_GREY, panel=True, pad_px=8, panel_m=H_PANEL2)
MID_DESC = (UP_ENTRY + UP_BOTTOM) / 2 + Vector((0, 0, UPPER_H))
MID_LOW = (LOW_BOTTOM + LOW_END) / 2
KOM = [
    ("Komora grobowa (Belzoniego)\n14,15 × 5 m, wys. 6,84 m, wykuta\nw skale, strop dwuspadowy;\nsarkofag przy ścianie zachodniej",
     0.04, 0.80, BURIAL_C + Vector((0, 0, 3)), True),
    ("Korytarz poziomy\nok. 3 m poniżej poziomu\ndziedzińca, wys. 1,80 m", 0.30, 0.80,
     Vector((PASS_X, 35, HORIZ_Z + HORIZ_H)), True),
    ("Korytarz zstępujący\nok. 26°30′, 1,05 × 1,20 m,\nwyłożony granitem", 0.50, 0.80, MID_DESC, True),
    ("Wejście górne\n11,54 m nad podstawą,\n12,45 m na wschód od osi", 0.71, 0.80,
     UP_ENTRY + Vector((0, 0, UPPER_H)), True),
    ("Zapadnia granitowa", 0.36, 0.33, Vector((PASS_X, PORT_Y, HORIZ_Z)), False),
    ("Dolny korytarz\nzejście ok. 22°40′, odcinek\npoziomy, podejście ok. 21°40′", 0.50, 0.27,
     MID_LOW, False),
    ("Komora boczna\n10,41 × 3,12 × 2,61 m,\npo zachodniej stronie", 0.705, 0.24, SUBSID_C + Vector((5, 0, -1.3)), False),
    ("Wejście dolne\nw bruku, ponad 8 m\nna północ od podstawy", 0.85, 0.42, LOW_ENTRY, True),
]
for txt, u, v, wp, above in KOM:
    hud_callout(cam, c, txt, u, v, wp, H_WHITE, H_LINE_G, above=above)
hud_legend(cam, c, only_confirmed=True)
# linia poziomu dziedzińca (obiekt w scenie, widoczny tylko w tym kadrze)
tube("Poziom_dziedzinca_linia", (PASS_X, h, 0), (PASS_X, h + 34, 0), 0.12, c, H_GREY, segs=6)
u, v = project(cam, (PASS_X, h + 34, 0))
hud_text(cam, c, "poziom dziedzińca", u - 0.004, v + 0.012, 20, H_GREY, align_x="RIGHT", align_y="BOTTOM")
# podziałka 10 m
bar_u = 10.0 / KOM_W
a, b = hud_pt(cam, 0.45, 0.062), hud_pt(cam, 0.45 + bar_u, 0.068)
hud_rect(cam, c, a.x, a.y, b.x, b.y, H_WHITE, dz=-0.0005)
hud_text(cam, c, "10 m", 0.45 + bar_u / 2, 0.058, 20, H_WHITE, align_x="CENTER")
hud_text(cam, c, "głębokość dolnego korytarza i rampa do komory bocznej – szacunek · " + FOOT, 0.975, 0.03, 20,
         H_GREY, align_x="RIGHT", align_y="BOTTOM")

# film obrotowy
cam, c = CAMS["obrot"], new_hud("obrot")
hud_text(cam, c, "Według Malangi i Biondiego (2025, bez recenzji)", 0.025, 0.955, 34, H_WHITE, bold=True, panel=True)
hud_legend(cam, c)
hud_text(cam, c, FOOT, 0.975, 0.03, 20, H_GREY, align_x="RIGHT", align_y="BOTTOM")

# ---------------------------------------------------------------- przełączanie widoków


def hide(c, state):
    c.hide_render = state
    c.hide_viewport = state


def activate(key):
    """Ustawia kamerę, napisy i wersję gruntu dla wybranego kadru (także w oknie Blendera)."""
    for k, c in HUDS.items():
        hide(c, k != key)
    scene.camera = CAMS[key]
    hide(C_SKALA, key in ("szyby", "komory"))  # w zbliżeniach skala byłaby tuż przed obiektywem
    hide(C_TWIERDZ, key == "komory")           # kadr "komory" pokazuje tylko to, co potwierdzone
    pyr.hide_render = key == "komory"          # tam z piramidy zostają same krawędzie
    full = key in ("obrot", "komory")
    hide(C_GRUNT, full)
    hide(C_GRUNT_GLB, key != "obrot")  # kadr "komory" jest bez gruntu, na ciemnym tle
    hide(C_TW_FULL, key != "obrot")
    hide(C_TW_CUT, key == "obrot")
    for t in RULER_TEXTS:
        for con in list(t.constraints):
            t.constraints.remove(con)
        if key == "obrot":
            con = t.constraints.new("COPY_ROTATION")
            con.target = CAMS[key]


def show_all():
    for c in (C_POTW, C_TWIERDZ, C_TW_FULL, C_TW_CUT, C_GRUNT, C_GRUNT_GLB, C_SKALA):
        c.hide_viewport = False


activate("opis")
bpy.context.view_layer.update()

STILLS = [("ogolny", "render-01-widok-ogolny.png"), ("przekroj", "render-02-przekroj.png"),
          ("szyby", "render-03-szyby-zblizenie.png"), ("opis", "render-04-opis.png"),
          ("komory", "render-05-znane-komory.png")]
only = [s for s in args.only.split(",") if s]

if args.blend:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "chefren-sar.blend"), compress=True)
    print("ZAPISANO .blend")

if args.glb:
    show_all()
    bpy.context.view_layer.update()
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    # napisy skali jako siatki (glTF nie obsługuje obiektów tekstowych)
    tmp = []
    dg = bpy.context.evaluated_depsgraph_get()
    for t in RULER_TEXTS:
        me = bpy.data.meshes.new_from_object(t.evaluated_get(dg))
        o = bpy.data.objects.new(t.name + "_siatka", me)
        o.matrix_world = t.matrix_world
        C_SKALA.objects.link(o)
        tmp.append(o)
    for c in (C_POTW, C_TWIERDZ, C_TW_FULL, C_GRUNT_GLB, C_SKALA):
        for ob in c.objects:
            if ob.type == "MESH":
                ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "chefren-sar.glb"), export_format="GLB",
                              use_selection=True, export_apply=True, export_yup=True,
                              export_cameras=False, export_lights=False)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
    activate("opis")
    print("ZAPISANO .glb")

if args.stills:
    scene.eevee.taa_render_samples = args.samples
    scene.render.image_settings.file_format = "PNG"
    for key, fname in STILLS:
        if only and key not in only:
            continue
        activate(key)
        scene.render.filepath = os.path.join(OUT, fname)
        bpy.ops.render.render(write_still=True)
        print("RENDER", fname)

if args.stills and "obrot" in only:  # podgląd dwóch klatek filmu
    activate("obrot")
    for f in (1, FRAMES // 3):
        scene.frame_set(f)
        scene.render.filepath = os.path.join(OUT, f"test-obrot-{f:03d}.png")
        bpy.ops.render.render(write_still=True)
    scene.frame_set(1)

if args.frames:
    activate("obrot")
    scene.eevee.taa_render_samples = args.video_samples
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = os.path.join(os.path.abspath(args.frames), "klatka_")
    bpy.ops.render.render(animation=True)
    print("KLATKI GOTOWE")

activate("opis")
