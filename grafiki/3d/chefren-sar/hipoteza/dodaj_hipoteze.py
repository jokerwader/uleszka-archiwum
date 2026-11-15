"""
Warstwa "hipoteza: obieg wodno-powietrzny" dla modelu Chefren SAR 3D.

To pomoc do zrozumienia zasady działania, NIE rekonstrukcja i NIE twierdzenie autorów (Biondi, Malanga, Mei).
Skrypt otwiera się na kopii projektu, niczego w niej nie zmienia poza dodaniem kolekcji HIPOTEZA_...,
obiektów Hipo_* i materiałów hipo_*, a potem zapisuje plik i eksportuje .glb z animacjami.

Uruchomienie (z katalogu repozytorium):

    blender -b grafiki/3d/chefren-sar/hipoteza/piramida-biondi-hipoteza.blend \
        --python grafiki/3d/chefren-sar/hipoteza/dodaj_hipoteze.py -- --save --glb

Trzy animacje (ścieżki NLA o tych nazwach, eksportowane jako osobne animacje glTF), 360 klatek, 30 kl./s:
  Wariant_A   zrzut wody, środkowy kanał otwarty, ciśnienie cały czas 1 bar
  Wariant_B1  tłok wodny, powrót wody: magazyn (powietrze z góry wypiera wodę do zbiornika na powierzchni)
  Wariant_B2  tłok wodny, powrót wody: przepływ (woda przechodzi dołem skrzyni i wraca drugim szybem)
Druga skrzynia (południowa) pracuje z przesunięciem o pół okresu.

Przez glTF przechodzą tylko przesunięcia, obroty i skale obiektów (animacje materiałów wymagają rozszerzenia
KHR_animation_pointer, którego three.js r147 nie obsługuje). Dlatego: poziomy wody to skala w pionie,
"znikanie" to skala bliska zera, a zmiana rodzaju powietrza (1 bar / sprężone) to dwa osobne obiekty.
Obiekty Hipo_B_*, Hipo_B1_*, Hipo_B2_* należą tylko do wskazanych wariantów; przeglądarka chowa je po nazwie.
"""

import argparse
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--save", action="store_true", help="zapisz plik .blend (ten, na którym uruchomiono skrypt)")
ap.add_argument("--glb", action="store_true", help="eksportuj chefren-sar-hipoteza.glb obok skryptu")
args = ap.parse_args(argv)
HERE = os.path.dirname(os.path.abspath(__file__))

FRAMES = 360
HIDE = 1e-4                 # skala "obiekt ukryty"
SPIRAL_PITCH = 8.0          # skok spirali z build_chefren_sar.py (z samej siatki nie da się go pewnie odczytać)

# ZAŁOŻENIA hipotezy (żadne nie pochodzi od autorów)
CHANNEL_DIP = 20.0          # wariant B: środkowy kanał wchodzi w skrzynię 20 m poniżej stropu
CHANNEL_R = 4.2             # promień słupa wody w środkowym kanale (szyb ma promień 5,5 m)
PIPE_R = 0.5                # wąski przewód sprężonego powietrza: średnica ok. 1 m
TANK = (300.0, 300.0, 6.0)  # B1: zbiornik na powierzchni
TANK_CENTER = (265.0, 0.0)  # położenie umowne: na wschód od piramidy
OUTLET_DROP = 4.0           # B2: wylot "kilka metrów" niżej niż wlot
F_FILL, F_COMP, F_PUSH = 96, 216, 264   # granice faz wariantu B (klatki)
A_FULL = 336                # wariant A: skrzynia pełna w tej klatce

scene = bpy.data.scenes.get("Chefren_SAR") or bpy.context.scene
if bpy.context.window:
    bpy.context.window.scene = scene

# kopia leży w innym folderze niż oryginał: napraw względne ścieżki czcionek systemowych (to nie zmienia obiektów)
for font in bpy.data.fonts:
    if font.filepath.startswith("//") and not os.path.exists(bpy.path.abspath(font.filepath)):
        cand = os.path.join("C:/Windows/Fonts", os.path.basename(font.filepath.replace("\\", "/")))
        if os.path.exists(cand):
            font.filepath = cand

for o in [o for o in bpy.data.objects if o.name.startswith("Hipo_")]:
    bpy.data.objects.remove(o, do_unlink=True)   # ponowne uruchomienie: usuń tylko własne obiekty
old = bpy.data.collections.get("HIPOTEZA_OBIEG_WODNO_POWIETRZNY")
if old:
    bpy.data.collections.remove(old)
for a in [a for a in bpy.data.actions if a.name.startswith("Hipo_")]:
    bpy.data.actions.remove(a)
C_HIPO = bpy.data.collections.new("HIPOTEZA_OBIEG_WODNO_POWIETRZNY")
scene.collection.children.link(C_HIPO)


# ---------------------------------------------------------------- odczyt geometrii ze sceny
def bbox(ob):
    """Zakres obiektu w układzie sceny (obiekty modelu nie są obracane ani skalowane)."""
    cs = [Vector(c) + ob.location for c in ob.bound_box]
    return Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs))), \
        Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))


def spiral_phase(ob, top):
    """Kąt, pod którym spirala zaczyna się u góry szybu (ze środka ciężkości najwyższych wierzchołków)."""
    pts = [v.co for v in ob.data.vertices if v.co.z + ob.location.z > top - 0.6]
    c = sum(pts, Vector()) / max(len(pts), 1)
    return math.atan2(c.y, c.x)


CUBES = {}
for key, name in (("N", "Skrzynia_polnocna"), ("S", "Skrzynia_poludniowa")):
    lo, hi = bbox(bpy.data.objects[name])
    CUBES[key] = {"name": name, "lo": lo, "hi": hi, "cx": (lo.x + hi.x) / 2, "cy": (lo.y + hi.y) / 2,
                  "bottom": lo.z, "top": hi.z, "side": hi.x - lo.x, "shafts": []}
SHAFTS = []
for i in range(1, 9):
    ob = bpy.data.objects[f"Szyb_{i}"]
    lo, hi = bbox(ob)
    sp = bpy.data.objects[f"Spirala_{i}"]
    slo, shi = bbox(sp)
    s = {"i": i, "x": ob.location.x, "y": ob.location.y, "top": hi.z, "bottom": lo.z, "r": (hi.x - lo.x) / 2,
         "spiral_r": (shi.x - slo.x) / 2 - 1.0, "phase": spiral_phase(sp, shi.z)}
    for key, c in CUBES.items():
        if c["lo"].x <= s["x"] <= c["hi"].x and c["lo"].y <= s["y"] <= c["hi"].y:
            s["cube"] = key
            c["shafts"].append(s)
    SHAFTS.append(s)
assert all("cube" in s for s in SHAFTS), "szyb nie trafia w żadną skrzynię"
# Role szybów w fazie 5 (umowne): szyb powrotny = wschodni, bliżej środka piramidy; wlotowy = po przekątnej.
for c in CUBES.values():
    east = [s for s in c["shafts"] if s["x"] > c["cx"]]
    west = [s for s in c["shafts"] if s["x"] < c["cx"]]
    c["ret"] = min(east, key=lambda s: abs(s["y"]))
    c["inlet"] = max(west, key=lambda s: abs(s["y"]))
SIDE = CUBES["N"]["side"]
DEPTH = SHAFTS[0]["top"] - CUBES["N"]["top"]       # słup od stropu skrzyni do poziomu gruntu (648 m)
COLUMN = DEPTH + CHANNEL_DIP                        # pełny słup wody w kanale (668 m)
print("HIPO geometria: skrzynia %.0f m, strop %.0f, szyby %s, powrotne %s, wlotowe %s" % (
    SIDE, CUBES["N"]["top"], [(s["i"], s["cube"]) for s in SHAFTS],
    [c["ret"]["i"] for c in CUBES.values()], [c["inlet"]["i"] for c in CUBES.values()]))


# ---------------------------------------------------------------- materiały hipo_
def mat(name, color, alpha=1.0, emit=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = 0.6
    p.inputs["Alpha"].default_value = alpha
    p.inputs["Emission Color"].default_value = (*color, 1)
    p.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = (*color, alpha)
    if alpha < 1:
        for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
        m.use_backface_culling = False
    return m


M_WATER = mat("hipo_woda", (0.00, 0.72, 0.66), alpha=0.6, emit=0.5)
M_AIR = mat("hipo_powietrze_1bar", (0.72, 1.00, 0.94), alpha=0.2, emit=0.3)
M_AIR_HP = mat("hipo_powietrze_sprezone", (0.52, 0.34, 1.00), alpha=0.8, emit=0.9)
M_ARROW = mat("hipo_strzalki", (0.86, 1.00, 0.98), emit=1.0)
M_UNKNOWN = mat("hipo_nieznane", (0.60, 0.63, 0.70), alpha=0.45, emit=0.25)
M_ASSUMED = mat("hipo_zalozenie", (0.10, 0.52, 0.55), alpha=0.6, emit=0.4)


# ---------------------------------------------------------------- geometria pomocnicza
def new_obj(name, bm, loc, m):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    C_HIPO.objects.link(ob)
    try:
        ob.visible_shadow = False
    except AttributeError:
        pass
    return ob


def unit_box(name, sx, sy, loc, m, origin="bottom"):
    """Prostopadłościan o wysokości 1 m; skala Z = wysokość w metrach. origin: 'bottom' albo 'top'."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z + (0.5 if origin == "bottom" else -0.5)))
    return new_obj(name, bm, loc, m)


def unit_cyl(name, r, loc, m, segs=20):
    """Walec o wysokości 1 m z podstawą w początku układu; skala Z = wysokość w metrach."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=1.0)
    for v in bm.verts:
        v.co.z += 0.5
    return new_obj(name, bm, loc, m)


def tube(name, p0, p1, r, m, segs=12):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=d.length, matrix=rot)
    for v in bm.verts:
        v.co += (p0 + p1) / 2 - p0
    return new_obj(name, bm, p0, m)


def arrows(name, origin, items, length, radius, m):
    """Jeden obiekt z wielu strzałek-stożków. items: lista (pozycja względem origin, kierunek)."""
    bm = bmesh.new()
    for pos, direction in items:
        d = Vector(direction).normalized()
        rot = Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=radius, radius2=0.0, depth=length, matrix=rot)
        for v in res["verts"]:
            v.co += Vector(pos)
    return new_obj(name, bm, origin, m)


def text_mesh(name, body, size, loc, rot, m):
    cu = bpy.data.curves.new(name + "_krzywa", "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = size * 0.06
    cu.align_x = "CENTER"
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    C_HIPO.objects.link(tmp)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.curves.remove(cu)
    me.name = name
    me.materials.clear()
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = rot
    C_HIPO.objects.link(ob)
    return ob


# ---------------------------------------------------------------- model fizyczny (wspólny z przeglądarką)
P_MAX = None


def pressure(d):
    """Ciśnienie poduszki [bar abs.] gdy lustro wody w kanale jest d metrów nad stropem skrzyni (d od -20).
    Poduszka: wysokość 20/p; słup wody nad lustrem w skrzyni: d + 20/p; p = 1 + słup/10."""
    return ((10 + d) + math.sqrt((10 + d) ** 2 + 800)) / 20


P_MAX = pressure(DEPTH)


def state(variant, f):
    """Stan jednej skrzyni w klatce f (1..360) dla wariantu 'A', 'B1', 'B2'. Wysokości w metrach."""
    f = ((f - 1) % FRAMES) + 1
    st = {"water": 0.0, "air": 0.0, "cushion": 0.0, "column": 0.0, "column_ret": 0.0, "p": 1.0, "phase": 1}
    if variant == "A":
        st["water"] = SIDE * min(1.0, (f - 1) / (A_FULL - 1))
        st["air"] = SIDE - st["water"]
        st["phase"] = 1 if f < A_FULL else 2
        return st
    fill = SIDE - CHANNEL_DIP
    if f < F_FILL:
        st["water"] = fill * (f - 1) / (F_FILL - 1)
        st["air"] = SIDE - st["water"]
    elif f < F_COMP:
        d = -CHANNEL_DIP + COLUMN * (f - F_FILL) / (F_COMP - F_FILL)
        st["p"] = pressure(d)
        st["cushion"] = CHANNEL_DIP / st["p"]
        st["water"] = SIDE - st["cushion"]
        st["column"] = st["column_ret"] = d + CHANNEL_DIP
        st["phase"] = 3
    elif f < F_PUSH:
        k = (f - F_COMP) / (F_PUSH - F_COMP)
        st["p"] = P_MAX
        st["cushion"] = (CHANNEL_DIP / P_MAX) * (1 - k) + 0.02 * k    # powietrze odpływa przy stałym ciśnieniu
        st["water"] = SIDE - st["cushion"]
        st["column"] = st["column_ret"] = COLUMN
        st["phase"] = 4
    else:
        k = (f - F_PUSH) / (FRAMES + 1 - F_PUSH)
        st["phase"] = 5
        st["p"] = P_MAX
        if variant == "B1":      # magazyn: powietrze z góry wypiera wodę drugim szybem do zbiornika
            st["water"] = SIDE * (1 - k)
            st["cushion"] = SIDE - st["water"]
            st["column"] = COLUMN * (1 - k)
            st["column_ret"] = COLUMN
        else:                    # przepływ: skrzynia zostaje pełna, woda płynie dołem do drugiego szybu
            st["water"] = SIDE
            st["column"] = COLUMN
            st["column_ret"] = COLUMN - OUTLET_DROP
    return st


def cube_frame(key, f):
    """Skrzynia południowa pracuje z przesunięciem o pół okresu."""
    return f if key == "N" else f + FRAMES // 2


# ---------------------------------------------------------------- animacje: akcje i ścieżki NLA
VARIANTS = ("A", "B1", "B2")
TRACKS = {v: "Wariant_" + v for v in VARIANTS}
ANIMATED = []


def add_track(ob, variant, channels):
    """channels: {(ścieżka, indeks): funkcja(klatka) -> wartość}. Klucze co klatkę, 1..361, liniowo."""
    ad = ob.animation_data or ob.animation_data_create()
    act = bpy.data.actions.new(f"{ob.name}_{variant}")
    slot = act.slots.new(id_type="OBJECT", name=ob.name)
    layer = act.layers.new("Warstwa")
    strip = layer.strips.new(type="KEYFRAME")
    bag = strip.channelbag(slot, ensure=True)
    for (path, idx), fn in channels.items():
        fc = bag.fcurves.new(path, index=idx)
        n = FRAMES + 1
        fc.keyframe_points.add(n)
        co = []
        for f in range(1, n + 1):
            co.extend((float(f), float(fn(f))))
        fc.keyframe_points.foreach_set("co", co)
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
        fc.update()
    tr = ad.nla_tracks.new()
    tr.name = TRACKS[variant]
    st = tr.strips.new(TRACKS[variant], 1, act)
    try:
        st.action_slot = slot
    except Exception as e:
        print("Uwaga: nie przypisano slotu akcji:", e)
    if ob not in ANIMATED:
        ANIMATED.append(ob)


def scale_channels(height_fn, visible_fn=None):
    """Skala: wysokość w osi Z; gdy obiekt ma być niewidoczny, wszystkie osie bliskie zera."""
    def vis(f):
        h = height_fn(f)
        return h > 1e-3 and (visible_fn(f) if visible_fn else True)
    return {("scale", 0): lambda f: 1.0 if vis(f) else HIDE,
            ("scale", 1): lambda f: 1.0 if vis(f) else HIDE,
            ("scale", 2): lambda f: max(height_fn(f), HIDE) if vis(f) else HIDE}


def gate_channels(on_fn):
    return {("scale", i): (lambda f: 1.0 if on_fn(f) else HIDE) for i in range(3)}


def ramp(total):
    """Liniowy ruch przez cały cykl: po 360 klatkach wzór strzałek pokrywa się z początkowym."""
    return lambda f: total * (f - 1) / FRAMES


def in_phase(variant, key, test):
    return lambda f: test(state(variant, cube_frame(key, f)), ((cube_frame(key, f) - 1) % FRAMES) + 1)


# ---------------------------------------------------------------- obiekty: skrzynie
for key, c in CUBES.items():
    nm = "polnocna" if key == "N" else "poludniowa"
    inner = SIDE - 2.0
    # woda w skrzyni (oba warianty)
    w = unit_box(f"Hipo_Woda_skrzynia_{nm}", inner, inner, (c["cx"], c["cy"], c["bottom"]), M_WATER, "bottom")
    # powietrze 1 bar nad wodą (oba warianty)
    a = unit_box(f"Hipo_Powietrze_skrzynia_{nm}", inner, inner, (c["cx"], c["cy"], c["top"]), M_AIR, "top")
    # poduszka sprężonego powietrza (B)
    p = unit_box(f"Hipo_B_Poduszka_{nm}", inner, inner, (c["cx"], c["cy"], c["top"]), M_AIR_HP, "top")
    for v in VARIANTS:
        add_track(w, v, scale_channels(lambda f, v=v, key=key: state(v, cube_frame(key, f))["water"]))
        add_track(a, v, scale_channels(lambda f, v=v, key=key: state(v, cube_frame(key, f))["air"]))
        add_track(p, v, scale_channels(lambda f, v=v, key=key: state(v, cube_frame(key, f))["cushion"]))

    # wąski przewód sprężonego powietrza i zawór w stropie (B) – położenie w środku skrzyni jest założeniem
    tube(f"Hipo_B_Przewod_sprezonego_{nm}", (c["cx"], c["cy"], c["top"]), (c["cx"], c["cy"], c["top"] + DEPTH), PIPE_R,
         M_ASSUMED)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=3.0, radius2=3.0, depth=0.6)
    valve = new_obj(f"Hipo_B_Zawor_{nm}", bm, (c["cx"], c["cy"], c["top"] + 0.6), M_ASSUMED)

    def valve_angle(variant, key=key):
        def fn(f):
            ff = ((cube_frame(key, f) - 1) % FRAMES) + 1
            open_until = FRAMES + 1 if variant == "B1" else F_PUSH
            if variant == "A" or ff < F_COMP:
                return 0.0
            if ff < F_COMP + 6:
                return math.pi / 2 * (ff - F_COMP) / 6
            if ff < open_until - 6:
                return math.pi / 2
            if ff < open_until:
                return math.pi / 2 * (open_until - ff) / 6
            return 0.0
        return fn
    for v in VARIANTS:
        add_track(valve, v, {("rotation_euler", 0): valve_angle(v)})

    # strzałki w wąskim przewodzie: w górę podczas tłoczenia (B), w dół przy wtłaczaniu powietrza (B1, faza 5)
    n_ar = int(DEPTH // 24)
    up = arrows(f"Hipo_B_Strzalki_sprezone_{nm}", (c["cx"], c["cy"], c["top"]),
                [((0, 0, 12 + 24 * k), (0, 0, 1)) for k in range(n_ar - 4)], 9.0, 2.2, M_ARROW)
    down = arrows(f"Hipo_B1_Strzalki_wtlaczanie_{nm}", (c["cx"], c["cy"], c["top"]),
                  [((0, 0, 108 + 24 * k), (0, 0, -1)) for k in range(n_ar - 4)], 9.0, 2.2, M_ARROW)
    for v in VARIANTS:
        ch = gate_channels(in_phase(v, key, lambda st, ff: st["phase"] == 4 and v != "A"))
        ch[("location", 2)] = lambda f, z0=c["top"]: z0 + ramp(96.0)(f)
        add_track(up, v, ch)
        ch = gate_channels(in_phase(v, key, lambda st, ff, v=v: st["phase"] == 5 and v == "B1"))
        ch[("location", 2)] = lambda f, z0=c["top"]: z0 - ramp(96.0)(f)
        add_track(down, v, ch)

    # szyb powrotny: strzałki w górę w fazie 5 (B1 i B2)
    r = c["ret"]
    n_ret = int(COLUMN // 24)
    ret = arrows(f"Hipo_B_Strzalki_powrot_{nm}", (r["x"], r["y"], c["top"] - CHANNEL_DIP),
                 [((0, 0, 12 + 24 * k), (0, 0, 1)) for k in range(n_ret - 2)], 10.0, 2.8, M_ARROW)
    for v in VARIANTS:
        ch = gate_channels(in_phase(v, key, lambda st, ff, v=v: st["phase"] == 5 and v != "A"))
        ch[("location", 2)] = lambda f, z0=c["top"] - CHANNEL_DIP: z0 + ramp(48.0)(f)
        add_track(ret, v, ch)

    # B1: przewód od szybu powrotnego do zbiornika na powierzchni (położenie umowne)
    tank_edge_x = TANK_CENTER[0] - TANK[0] / 2
    tube(f"Hipo_B1_Przewod_do_zbiornika_{nm}", (r["x"], r["y"], r["top"] + 1.0), (tank_edge_x, r["y"], r["top"] + 1.0),
         2.0, M_UNKNOWN)

    # B2: przepływ dołem skrzyni od szybu wlotowego do powrotnego; wlot i wylot na powierzchni
    i_ = c["inlet"]
    a0 = Vector((i_["x"], i_["y"], c["bottom"] + 6.0))
    b0 = Vector((r["x"], r["y"], c["bottom"] + 6.0))
    d = (b0 - a0)
    n_b = int((d.length - 24) // 12)
    floor_ar = arrows(f"Hipo_B2_Strzalki_dno_{nm}", a0, [(d.normalized() * (6 + 12 * k), d) for k in range(n_b)],
                      8.0, 2.6, M_ARROW)
    dn = d.normalized() * 24.0
    for v in VARIANTS:
        ch = gate_channels(in_phase(v, key, lambda st, ff, v=v: st["phase"] == 5 and v == "B2"))
        ch[("location", 0)] = lambda f, x0=a0.x, dx=dn.x: x0 + dx * (f - 1) / FRAMES
        ch[("location", 1)] = lambda f, y0=a0.y, dy=dn.y: y0 + dy * (f - 1) / FRAMES
        add_track(floor_ar, v, ch)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=i_["r"] + 4.5, radius2=i_["r"] + 4.5, depth=2.0)
    new_obj(f"Hipo_B2_Wlot_{nm}", bm, (i_["x"], i_["y"], i_["top"]), M_ASSUMED)
    tube(f"Hipo_B2_Wylot_{nm}", (r["x"], r["y"], r["top"] - OUTLET_DROP), (r["x"] + 26.0, r["y"], r["top"] - OUTLET_DROP),
         2.5, M_UNKNOWN)

# ---------------------------------------------------------------- obiekty: szyby
for s in SHAFTS:
    c = CUBES[s["cube"]]
    key, i = s["cube"], s["i"]
    is_ret = s is c["ret"]
    is_inlet = s is c["inlet"]
    # woda schodząca po spirali: strzałki na spirali, co 1,5 zwoju; ruch po linii śrubowej
    P, R = SPIRAL_PITCH, s["spiral_r"]
    items = []
    turns = (s["top"] - s["bottom"]) / P
    k = 0
    while k * 1.5 < turns - 0.5:
        th = s["phase"] + (k * 1.5 + 0.5) * 2 * math.pi
        z = -(k * 1.5 + 0.5) * P + 2.4          # tuż nad rurą spirali
        items.append(((R * math.cos(th), R * math.sin(th), z), (-R * math.sin(th), R * math.cos(th), -P / (2 * math.pi))))
        k += 1
    wa = arrows(f"Hipo_Strzalki_woda_{i}", (s["x"], s["y"], s["top"]), items, 8.0, 2.3, M_ARROW)
    for v in VARIANTS:
        def water_on(st, ff, v=v, is_inlet=is_inlet):
            if v == "A":
                return st["phase"] == 1
            return st["phase"] in (1, 3) or (v == "B2" and st["phase"] == 5 and is_inlet)
        ch = gate_channels(in_phase(v, key, water_on))
        ch[("location", 2)] = lambda f, z0=s["top"]: z0 - ramp(3 * P)(f)        # 3 zwoje w dół na cykl
        ch[("rotation_euler", 2)] = ramp(3 * 2 * math.pi)
        add_track(wa, v, ch)

    # powietrze 1 bar uchodzące środkiem szybu
    n_air = int((s["top"] - s["bottom"]) // 24) - 2
    aa = arrows(f"Hipo_Strzalki_powietrze_{i}", (s["x"], s["y"], s["bottom"]),
                [((0, 0, -12 + 24 * k), (0, 0, 1)) for k in range(n_air)], 10.0, 2.8, M_ARROW)
    for v in VARIANTS:
        ch = gate_channels(in_phase(v, key, lambda st, ff: st["phase"] == 1))
        ch[("location", 2)] = lambda f, z0=s["bottom"]: z0 + ramp(48.0)(f)
        add_track(aa, v, ch)

    # wariant B: zanurzony koniec środkowego kanału (założenie) i słup wody w kanale
    tube(f"Hipo_B_Kanal_zanurzony_{i}", (s["x"], s["y"], c["top"] - CHANNEL_DIP), (s["x"], s["y"], c["top"]), s["r"],
         M_ASSUMED, segs=20)
    col = unit_cyl(f"Hipo_B_Woda_szyb_{i}", CHANNEL_R, (s["x"], s["y"], c["top"] - CHANNEL_DIP), M_WATER)
    for v in VARIANTS:
        add_track(col, v, scale_channels(
            lambda f, v=v, key=key, is_ret=is_ret: state(v, cube_frame(key, f))["column_ret" if is_ret else "column"]))

# ---------------------------------------------------------------- obiekty: zbiornik na powierzchni (B1)
tz = SHAFTS[0]["top"]
unit_box("Hipo_B1_Zbiornik", TANK[0], TANK[1], (TANK_CENTER[0], TANK_CENTER[1], tz), M_UNKNOWN, "bottom").scale.z = TANK[2]
tank_w = unit_box("Hipo_B1_Zbiornik_woda", TANK[0] - 4, TANK[1] - 4, (TANK_CENTER[0], TANK_CENTER[1], tz + 0.1), M_WATER,
                  "bottom")


def tank_level(variant):
    def fn(f):
        if variant != "B1":
            return 0.0
        missing = 2 * SIDE - state("B1", f)["water"] - state("B1", f + FRAMES // 2)["water"]
        return min(TANK[2], missing * SIDE * SIDE / ((TANK[0] - 4) * (TANK[1] - 4)))
    return fn


for v in VARIANTS:
    add_track(tank_w, v, scale_channels(tank_level(v)))
text_mesh("Hipo_B1_Zbiornik_znak_zapytania", "?", 90.0, (TANK_CENTER[0], TANK_CENTER[1], tz + TANK[2] + 8.0),
          (math.radians(90), 0, 0), M_UNKNOWN)

# ---------------------------------------------------------------- scena, zapis, eksport
scene.frame_start, scene.frame_end = 1, FRAMES
scene.render.fps = 30
HIPO_OBJECTS = sorted(o.name for o in C_HIPO.objects)
print("HIPO obiekty (%d):" % len(HIPO_OBJECTS), ", ".join(HIPO_OBJECTS))
print("HIPO materialy:", ", ".join(sorted(m.name for m in bpy.data.materials if m.name.startswith("hipo_"))))
print("HIPO p_max = %.1f bar, poduszka na koncu sprezania = %.2f m, zbiornik: %.2f..%.2f m" % (
    P_MAX, CHANNEL_DIP / P_MAX, min(tank_level("B1")(f) for f in range(1, 361)),
    max(tank_level("B1")(f) for f in range(1, 361))))

if args.glb:
    names = ("POTWIERDZONE", "TWIERDZENIA_MALANGA_BIONDI_2025", "TWIERDZENIA_plaszczyzny_pelne",
             "TWIERDZENIA_plaszczyzny_do_przekroju", "GRUNT_PRZEKROJ", "GRUNT_PRZEZROCZYSTY", "SKALA_GLEBOKOSCI")
    saved = {n: (bpy.data.collections[n].hide_viewport, bpy.data.collections[n].hide_render) for n in names}
    for n in names:
        bpy.data.collections[n].hide_viewport = False
    bpy.context.view_layer.update()
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    tmp = []
    dg = bpy.context.evaluated_depsgraph_get()
    C_SKALA = bpy.data.collections["SKALA_GLEBOKOSCI"]
    for t in [o for o in C_SKALA.objects if o.type == "FONT"]:   # napisy skali jako siatki (glTF nie ma tekstów)
        me = bpy.data.meshes.new_from_object(t.evaluated_get(dg))
        o = bpy.data.objects.new(t.name + "_siatka", me)
        o.matrix_world = t.matrix_world
        C_SKALA.objects.link(o)
        tmp.append(o)
    for n in ("POTWIERDZONE", "TWIERDZENIA_MALANGA_BIONDI_2025", "TWIERDZENIA_plaszczyzny_pelne", "GRUNT_PRZEZROCZYSTY",
              "SKALA_GLEBOKOSCI", C_HIPO.name):
        for ob in bpy.data.collections[n].objects:
            if ob.type == "MESH":
                ob.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(HERE, "chefren-sar-hipoteza.glb"), export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_cameras=False, export_lights=False,
        export_animations=True, export_animation_mode="NLA_TRACKS", export_nla_strips=True,
        export_force_sampling=True, export_frame_range=False, export_anim_slide_to_zero=True,
        export_optimize_animation_size=True)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
    for n, (hv, hr) in saved.items():
        bpy.data.collections[n].hide_viewport = hv
        bpy.data.collections[n].hide_render = hr
    print("ZAPISANO .glb")

# w Blenderze domyślnie widać wariant B1 (pozostałe ścieżki wyciszone); eksport robi się przed wyciszeniem
for ob in ANIMATED:
    for tr in ob.animation_data.nla_tracks:
        tr.mute = tr.name != TRACKS["B1"]

if args.save:
    bpy.ops.wm.save_mainfile(compress=True)
    print("ZAPISANO .blend")
