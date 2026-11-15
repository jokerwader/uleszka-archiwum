"""
Piramida Chefrena i domniemane struktury pod nią według C. Malangi i F. Biondiego (2025).

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
ap.add_argument("--stills", action="store_true", help="renderuj 4 kadry PNG")
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
# Potwierdzone (Wikipedia: Pyramid of Khafre; pomiary egiptologiczne)
PYR_BASE = 215.25          # bok podstawy [m]
PYR_HEIGHT = 143.5         # pierwotna wysokość [m]
UPPER_ENTRANCE_Z = 11.54   # górne wejście na ścianie północnej [m]
PASSAGE_EAST_OFFSET = 12.0  # korytarze przesunięte 12 m na wschód od osi
BURIAL = (14.15, 5.0, 6.83)  # komora grobowa: dł. W-E, szer., wys. do szczytu dwuspadowego stropu
SUBSID = (10.41, 3.12, 2.61)  # komora boczna (dł., szer., wys.) – wg literatury egiptologicznej

# Twierdzenia Malangi i Biondiego (konferencja, marzec 2025)
N_SHAFTS = 8               # podane wprost
SHAFT_BOTTOM = -648.0      # "ok. 2100 stóp" (JPost) = ok. 640–648 m; 648 m w wielu relacjach
CUBE_SIDE = 90.0           # NatGeo: 90 m; JPost: 80 m
N_UPPER = 5                # "pięć wielopoziomowych struktur połączonych korytarzami" – podane wprost
CLAIMED_MAX_DEPTH = -2000.0  # "ok. 2 km" – w części relacji (NatGeo, Retraction Watch)

# SZAC – nie podano w żadnym źródle
SHAFT_RADIUS = 5.0         # średnica ok. 10 m
SHAFT_TOP = -80.0
ROWS_X = (-25.0, 25.0)     # dwa równoległe rzędy wzdłuż osi północ–południe
SHAFT_Y = (-70.0, -20.0, 20.0, 70.0)
SPIRAL_RADIUS = 9.0
SPIRAL_PITCH = 25.0
SPIRAL_TUBE = 1.6
UPPER_Y = (-80.0, -40.0, 0.0, 40.0, 80.0)
UPPER_SIZE = 24.0
UPPER_LEVELS = 4
UPPER_TOP = -15.0

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
M_KNOWN = mat("potw_komory_korytarze", GOLD, emit=1.2)
M_SHAFT = mat("twierdz_szyby", CLAIM, alpha=0.55, emit=0.5)
M_SPIRAL = mat("twierdz_spirale", CLAIM, emit=1.0)
M_CUBE = mat("twierdz_szesciany", CLAIM, alpha=0.35, emit=0.4)
M_CUBE_EDGE = mat("twierdz_szesciany_krawedzie", CLAIM_LIGHT, emit=1.5)
M_UPPER = mat("twierdz_struktury_gorne", CLAIM, alpha=0.6, emit=0.6)
M_DASH = mat("twierdz_zasieg_2km", CLAIM_LIGHT, alpha=0.7, emit=1.0)
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
H_LINE_C = flat_mat("hud_linia_twierdzenie", (1.0, 0.45, 0.58))
H_LINE_G = flat_mat("hud_linia_potwierdzone", GOLD)
H_DARK = flat_mat("hud_ciemny", (0.10, 0.08, 0.06))

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


# ---- potwierdzone: piramida
h = PYR_BASE / 2
bm = bmesh.new()
vs = [bm.verts.new(p) for p in ((-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0), (0, 0, PYR_HEIGHT))]
bm.faces.new((vs[3], vs[2], vs[1], vs[0]))
for i in range(4):
    bm.faces.new((vs[i], vs[(i + 1) % 4], vs[4]))
pyr = mk("Piramida_Chefrena", bm, C_POTW, m=M_PYR)
wire_copy(pyr, "Piramida_Chefrena_krawedzie", M_PYR_EDGE, 1.5)

# ---- potwierdzone: komora grobowa (wykuta w skale, strop dwuspadowy)
bx, by, bz = BURIAL
wall_h = 4.6  # SZAC: wysokość ścian do początku stropu
cx = 6.0      # SZAC: środek komory 6 m na wschód od osi (korytarz wchodzi przy wschodnim końcu)
floor_z = -3.0  # SZAC: dno komory poniżej poziomu skały
bm = bmesh.new()
x0, x1, y0, y1 = -bx / 2, bx / 2, -by / 2, by / 2
p = [bm.verts.new(v) for v in (
    (x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0),
    (x0, y0, wall_h), (x1, y0, wall_h), (x1, y1, wall_h), (x0, y1, wall_h),
    (x0, 0, bz), (x1, 0, bz))]
for f in ((0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 9, 5), (3, 0, 4, 8, 7),
          (4, 5, 9, 8), (6, 7, 8, 9)):
    bm.faces.new([p[i] for i in f])
mk("Komora_grobowa_Belzoniego", bm, C_POTW, (cx, 0, floor_z), M_KNOWN)

# ---- potwierdzone: korytarze (przebieg schematyczny, przekrój ok. 1 x 1,2 m)
ex = PASSAGE_EAST_OFFSET
north_face_y = h - UPPER_ENTRANCE_Z / math.tan(math.atan(PYR_HEIGHT / h))
up_entry = (ex, north_face_y, UPPER_ENTRANCE_Z)
up_bottom = (ex, north_face_y - UPPER_ENTRANCE_Z / math.tan(math.radians(25.9)), 0.0)  # SZAC: kąt 25,9°
r_pass = 0.6
tube("Korytarz_gorny_zstepujacy", up_entry, up_bottom, r_pass, C_POTW, M_KNOWN)
tube("Korytarz_gorny_poziomy", up_bottom, (ex, by / 2, 0.0), r_pass, C_POTW, M_KNOWN)
low_entry = (ex, h + 4.0, 0.0)                 # SZAC: wejście dolne w bruku przed ścianą
low_bottom = (ex, h - 24.0, -11.0)             # SZAC
low_end = (ex, h - 38.0, -11.0)                # SZAC
tube("Korytarz_dolny_zstepujacy", low_entry, low_bottom, r_pass, C_POTW, M_KNOWN)
tube("Korytarz_dolny_poziomy", low_bottom, low_end, r_pass, C_POTW, M_KNOWN)
tube("Korytarz_dolny_wstepujacy", low_end, (ex, h - 62.0, 0.0), r_pass, C_POTW, M_KNOWN)
sx, sy, sz = SUBSID
box("Komora_boczna", (ex - 1.0 - sx / 2, h - 30.0, -11.0 + sz / 2), (sx, sy, sz), C_POTW, M_KNOWN)

# ---- twierdzenia: 5 wielopoziomowych struktur połączonych korytarzami
lvl_h, gap = 10.0, 3.0
for i, y in enumerate(UPPER_Y):
    for k in range(UPPER_LEVELS):
        zc = UPPER_TOP - lvl_h / 2 - k * (lvl_h + gap)
        box(f"Struktura_{i + 1}_poziom_{k + 1}", (0, y, zc), (UPPER_SIZE, UPPER_SIZE, lvl_h), C_TWIERDZ, M_UPPER)
    tube(f"Struktura_{i + 1}_trzon", (0, y, UPPER_TOP), (0, y, UPPER_TOP - UPPER_LEVELS * (lvl_h + gap)),
         3.0, C_TWIERDZ, M_SPIRAL)
mid_z = UPPER_TOP - 2 * (lvl_h + gap)
for a, b in zip(UPPER_Y, UPPER_Y[1:]):
    tube(f"Korytarz_struktur_{a:+.0f}_{b:+.0f}", (0, a + UPPER_SIZE / 2, mid_z), (0, b - UPPER_SIZE / 2, mid_z),
         2.0, C_TWIERDZ, M_SPIRAL)

# ---- twierdzenia: 8 szybów ze spiralami
shaft_len = SHAFT_TOP - SHAFT_BOTTOM
n = 0
for x in ROWS_X:
    for y in SHAFT_Y:
        n += 1
        cyl(f"Szyb_{n}", (x, y, (SHAFT_TOP + SHAFT_BOTTOM) / 2), SHAFT_RADIUS, shaft_len, C_TWIERDZ, M_SHAFT)
        cu = bpy.data.curves.new(f"Spirala_{n}_krzywa", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = SPIRAL_TUBE
        cu.bevel_resolution = 1
        cu.use_fill_caps = True
        sp = cu.splines.new("POLY")
        steps_per_turn = 28
        total = int(shaft_len / SPIRAL_PITCH * steps_per_turn)
        sp.points.add(total)
        phase = (n * 0.7) % (2 * math.pi)
        for i in range(total + 1):
            t = i / steps_per_turn * 2 * math.pi + phase
            z = SHAFT_TOP - i / total * shaft_len - (SHAFT_TOP + SHAFT_BOTTOM) / 2
            sp.points[i].co = (SPIRAL_RADIUS * math.cos(t), SPIRAL_RADIUS * math.sin(t), z, 1)
        cob = bpy.data.objects.new(f"Spirala_{n}_tmp", cu)
        cob.location = (x, y, (SHAFT_TOP + SHAFT_BOTTOM) / 2)
        C_TWIERDZ.objects.link(cob)
        curve_to_mesh(cob, f"Spirala_{n}", C_TWIERDZ, M_SPIRAL)
        bpy.data.curves.remove(cu)

# ---- twierdzenia: 2 struktury sześcienne pod szybami
for i, sgn in enumerate((-1, 1)):
    yc = sgn * (CUBE_SIDE / 2 + 2)
    cube = box(f"Szescian_{'poludniowy' if sgn < 0 else 'polnocny'}",
               (0, yc, SHAFT_BOTTOM - CUBE_SIDE / 2), (CUBE_SIDE,) * 3, C_TWIERDZ, M_CUBE)
    wire_copy(cube, cube.name + "_krawedzie", M_CUBE_EDGE, 1.6)
    # przerywana linia do ok. 2 km (zasięg podawany w części relacji)
    z = SHAFT_BOTTOM - CUBE_SIDE
    k = 0
    while z - 30 > CLAIMED_MAX_DEPTH:
        k += 1
        tube(f"Zasieg_2km_{i + 1}_{k:02d}", (0, yc, z - 10), (0, yc, z - 40), 2.2, C_TWIERDZ, M_DASH, segs=8)
        z -= 60
    cyl(f"Zasieg_2km_{i + 1}_znacznik", (0, yc, CLAIMED_MAX_DEPTH), 14.0, 3.0, C_TWIERDZ, M_DASH)

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
NO_SHADOW_MATS = {M_SPIRAL, M_PYR, M_GHOST, M_SURFACE, M_LAYER_PLANE, M_SHAFT, M_CUBE, M_UPPER, M_DASH, M_GEDGE, M_PYR_EDGE}
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
look_at(CAMS["szyby"], (360, -460, 120), (0, 0, -150))
CAMS["opis"] = make_cam("Kamera_04_opis", lens=35, shift_x=0.17)
look_at(CAMS["opis"], orbit((40, -40, -1000), (1, -1.2, 0.55), 5300), (40, -40, -1000))
CAMS["opis"].data.shift_y = 0.025

# kamera filmu obrotowego na osi obracającego się "uchwytu"
pivot = bpy.data.objects.new("Obrot_os", None)
pivot.location = (0, 0, -900)
C_SWIATLO.objects.link(pivot)
CAMS["obrot"] = make_cam("Kamera_05_obrot", lens=35)
CAMS["obrot"].parent = pivot
look_at(CAMS["obrot"], Vector((0, -3600, 1350)), Vector((0, 0, 0)))
FRAMES = args.fps * args.seconds
scene.frame_start, scene.frame_end = 1, FRAMES
scene.render.fps = args.fps
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert("rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, 2 * math.pi * FRAMES / (FRAMES + 0))  # pełny obrót
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


def hud_ctx(cam):
    D = 1.0
    if cam.data.type == "ORTHO":
        hw = cam.data.ortho_scale / 2
    else:
        hw = D * cam.data.sensor_width / (2 * cam.data.lens)
    return D, hw, hw * RES[1] / RES[0]


def hud_pt(cam, u, v, dz=0.0):
    D, hw, hh = hud_ctx(cam)
    su, sv = cam.data.shift_x, cam.data.shift_y
    if cam.data.type != "ORTHO":
        scale = (D + dz) / D
    else:
        scale = 1.0
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


def hud_text(cam, c, body, u, v, size_px, m, bold=False, align_x="LEFT", align_y="TOP", panel=False, pad_px=14):
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
                 ob.location.x + x1 + pad, ob.location.y + y1 + pad, H_PANEL, dz=0.002)
    return ob


def hud_rect(cam, c, x0, y0, x1, y1, m, dz=0.001):
    D = hud_ctx(cam)[0]
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


def hud_legend(cam, c, u=0.025, v=0.055):
    sw = px(cam, 22)
    for i, (m, txt) in enumerate(((H_GOLD, "potwierdzone: piramida, znane komory i korytarze"),
                                  (H_CLAIM, "twierdzenie Malangi i Biondiego (2025, bez recenzji)"))):
        vv = v + (1 - i) * 0.042
        p = hud_pt(cam, u, vv)
        hud_rect(cam, c, p.x, p.y - sw / 2, p.x + sw, p.y + sw / 2, m, dz=-0.0005)
        hud_text(cam, c, txt, u + 0.02, vv, 24, H_WHITE, align_y="CENTER")
    a = hud_pt(cam, u - 0.01, v - 0.03)
    b = hud_pt(cam, u + 0.36, v + 0.072)
    hud_rect(cam, c, a.x, a.y, b.x, b.y, H_PANEL, dz=0.002)


HUDS = {}


def new_hud(key):
    c = coll("NAKLADKA_" + key, C_SWIATLO)
    HUDS[key] = c
    return c


TAG = "Pod piramidą Chefrena \u2013 według Malangi i Biondiego (2025, bez recenzji)"
FOOT = "model poglądowy \u00b7 uleszka.net \u00b7 jokerwader"
for key in ("ogolny", "przekroj", "szyby"):
    cam, c = CAMS[key], new_hud(key)
    hud_text(cam, c, TAG, 0.025, 0.955, 30, H_WHITE, bold=True, panel=True)
    hud_legend(cam, c)
    hud_text(cam, c, FOOT, 0.975, 0.03, 20, H_GREY, align_x="RIGHT", align_y="BOTTOM")

# dodatkowe podpisy w przekroju
cam, c = CAMS["przekroj"], HUDS["przekroj"]
hud_text(cam, c, "przekrój północ\u2013południe, widok od południa; warstwy skały schematyczne",
         0.025, 0.905, 22, H_GREY)
for txt, x, z in (("wapień formacji\nMokattam (eocen)", CUT_X - 12, -60),
                  ("starsze wapienie i margle", CUT_X - 12, -400),
                  ("głębsze skały osadowe", G_HALF - 12, -770)):
    u, v = project(cam, (x, -G_HALF, z))
    hud_text(cam, c, txt, u, v, 20, H_DARK, align_x="RIGHT", align_y="CENTER")
u, v = project(cam, (-PYR_BASE / 2 - 8, -G_HALF, 40))
hud_text(cam, c, "Piramida Chefrena\n(potwierdzone)", u, v, 22, H_GOLD, align_x="RIGHT", align_y="CENTER")
u, v = project(cam, (75, -G_HALF, -300))
hud_text(cam, c, "8 szybów w dwóch rzędach\n(od południa widać 2 rzędy)\nwg Malangi i Biondiego", u, v, 22,
         H_CLAIM, align_y="CENTER", panel=True, pad_px=10)

# podpisy w zbliżeniu
cam, c = CAMS["szyby"], HUDS["szyby"]
hud_text(cam, c, "Piramida Chefrena i znane komory\n(potwierdzone)", 0.70, 0.86, 24, H_GOLD, panel=True, pad_px=10)
hud_leader(cam, c, 0.694, 0.835, (0, 0, 60), H_LINE_G)
hud_leader(cam, c, 0.694, 0.835, (6, 0, 2), H_LINE_G)
hud_text(cam, c, "5 struktur wielopoziomowych\npołączonych korytarzami\n(twierdzenie)", 0.70, 0.66, 24, H_CLAIM,
         panel=True, pad_px=10)
hud_leader(cam, c, 0.694, 0.625, (0, -80, -40), H_LINE_C)
hud_text(cam, c, "szyby otoczone spiralami,\nśrednica ok. 10 m – szacunek\n(twierdzenie)", 0.70, 0.44, 24, H_CLAIM,
         panel=True, pad_px=10)
hud_leader(cam, c, 0.694, 0.405, (25, -70, -250), H_LINE_C)

# kadr z opisami
cam, c = CAMS["opis"], new_hud("opis")
hud_text(cam, c, "Co według Malangi i Biondiego jest pod piramidą Chefrena?", 0.025, 0.955, 44, H_WHITE, bold=True)
hud_text(cam, c, "Ilustracja twierdzeń z konferencji prasowej (marzec 2025). Nie jest to potwierdzone odkrycie.",
         0.025, 0.895, 26, H_GREY)
LX = 0.60
hud_text(cam, c, "Potwierdzone", LX, 0.80, 28, H_GOLD, bold=True)
hud_text(cam, c, "Piramida Chefrena: wys. 143,5 m, bok 215 m", LX, 0.765, 24, H_WHITE)
hud_leader(cam, c, LX - 0.006, 0.752, (-30, -30, 45), H_LINE_G)
hud_text(cam, c, "Znane komory i korytarze, wykute w skale u podstawy", LX, 0.725, 24, H_WHITE)
hud_leader(cam, c, LX - 0.006, 0.712, (6, 0, 0), H_LINE_G)
hud_text(cam, c, "Według Malangi i Biondiego (2025, bez recenzji)", LX, 0.645, 28, H_CLAIM, bold=True)
CL = [
    ("5 wielopoziomowych struktur połączonych korytarzami", (0, -80, -40), 0.605),
    ("8 pionowych szybów w dwóch rzędach, otoczonych\nspiralami, do ok. 648 m w głąb", (25, -70, -380), 0.545),
    ("2 struktury sześcienne, bok ok. 90 m\n(w innych relacjach 80 m)", (45, -47, -690), 0.465),
    ("ok. 2 km \u2013 zasięg podawany w części relacji", (0, -47, CLAIMED_MAX_DEPTH), 0.395),
]
for txt, wp, vv in CL:
    hud_text(cam, c, txt, LX, vv, 24, H_WHITE)
    hud_leader(cam, c, LX - 0.006, vv - 0.013, wp, H_LINE_C)
hud_text(cam, c,
         "Zastrzeżenia: praca nie przeszła recenzji naukowej. Geofizycy (m.in. L. Conyers, S. Parcak)\n"
         "wskazują, że radar SAR nie przenika skały na setki metrów; Z. Hawass: brak dowodów.\n"
         "Wcześniejszy artykuł autorów o piramidzie Cheopsa (Remote Sensing, 2022) wycofano w 2026 r.",
         LX - 0.01, 0.255, 21, H_GREY, panel=True, pad_px=16)
hud_legend(cam, c)
hud_text(cam, c, "wymiary szybów i struktur częściowo szacunkowe \u00b7 " + FOOT, 0.975, 0.03, 20, H_GREY,
         align_x="RIGHT", align_y="BOTTOM")
# panel pod blokiem etykiet
a, b = hud_pt(cam, LX - 0.022, 0.37), hud_pt(cam, 0.985, 0.835)
hud_rect(cam, c, a.x, a.y, b.x, b.y, H_PANEL, dz=0.002)

# film obrotowy
cam, c = CAMS["obrot"], new_hud("obrot")
hud_text(cam, c, "Według Malangi i Biondiego (2025, bez recenzji)", 0.025, 0.955, 34, H_WHITE, bold=True, panel=True)
hud_legend(cam, c)
hud_text(cam, c, FOOT, 0.975, 0.03, 20, H_GREY, align_x="RIGHT", align_y="BOTTOM")

# ---------------------------------------------------------------- przełączanie widoków


def set_ground(mode):
    C_GRUNT.hide_render = mode != "przekroj"
    C_GRUNT_GLB.hide_render = mode == "przekroj"


def activate(key):
    for k, c in HUDS.items():
        c.hide_render = k != key
    scene.camera = CAMS[key]
    C_SKALA.hide_render = key == "szyby"  # w zbliżeniu skala byłaby tuż przed obiektywem
    set_ground("przezroczysty" if key == "obrot" else "przekroj")
    for t in RULER_TEXTS:
        for con in list(t.constraints):
            t.constraints.remove(con)
        if key == "obrot":
            con = t.constraints.new("COPY_ROTATION")
            con.target = CAMS[key]


activate("opis")
bpy.context.view_layer.update()

STILLS = [("ogolny", "render-01-widok-ogolny.png"), ("przekroj", "render-02-przekroj.png"),
          ("szyby", "render-03-szyby-zblizenie.png"), ("opis", "render-04-opis.png")]
only = [s for s in args.only.split(",") if s]

if args.blend:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "chefren-sar.blend"), compress=True)
    print("ZAPISANO .blend")

if args.glb:
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
    for c in (C_POTW, C_TWIERDZ, C_GRUNT_GLB, C_SKALA):
        for ob in c.objects:
            if ob.type == "MESH":
                ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "chefren-sar.glb"), export_format="GLB",
                              use_selection=True, export_apply=True, export_yup=True,
                              export_cameras=False, export_lights=False)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
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
