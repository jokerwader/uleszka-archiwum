# -*- coding: utf-8 -*-
"""
Domek z kart (zwiastun, odcinek 0 „Wstęp”).

Lektor: „…ale nasza najstarsza historia jest domkiem z kart i wyjęcie jednej karty, poruszenie jej
czy nawet delikatne dmuchnięcie grozi jego zawaleniem.”

Ilustracja porównania z tekstu Leszka (to jego ocena, nie fakt – stąd rodzaj „hipoteza”). Czteropiętrowy domek
z 26 kart; z dolnego piętra wysuwa się jedna karta i cała budowla się wali. Upadek liczy symulacja brył sztywnych
Blendera (nic nie jest animowane ręcznie poza wysunięciem karty). Karty mają same ozdobne ramki, bez figur.

Skala: karta 0,63 × 0,88 (dziesięć razy większa niż prawdziwa, żeby symulacja była stabilna i upadek płynny).

Uruchomienie:
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-domek-z-kart/scena.py -- --proba 1,70,95,120,160,350
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-domek-z-kart/scena.py
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, "..", "_wspolne"))
import globus as G, zwiastun as Z

opcje = G.argumenty()
NKL = 350  # 14 s
sc = Z.start(NKL, opcje, probki=48)
Z.swiat((3, 5, 10), (14, 21, 42), moc=0.8)
random.seed(5)

K_WYSUW = (52, 84)     # karta wysuwa się z dolnego piętra
K_PUSC = 60            # od tej klatki pozostałe karty podlegają fizyce

T, SZ, DL = 0.012, 0.63, 0.88          # grubość, szerokość, długość karty
KAT = math.radians(20.0)               # odchylenie kart od pionu
PIETRA = 4
WYS = DL * math.cos(KAT)               # wysokość daszka
DELTA = T / 2 / math.cos(KAT) + 0.004  # odsunięcie górnych krawędzi od osi daszka
PODZ = 2 * (DL * math.sin(KAT) + DELTA) + 0.05   # odstęp między daszkami


# ---------------------------------------------------------------- materiały kart
def mat_karty(nazwa, tlo, wzor, rewers):
    m = Z.pbr(nazwa, tlo, szorstkosc=0.42)
    nt = m.node_tree
    b = Z.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])

    def mat(op, x, y=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((x, y)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    ay = mat("DIVIDE", mat("ABSOLUTE", sep.outputs[1]), SZ / 2)
    az = mat("DIVIDE", mat("ABSOLUTE", sep.outputs[2]), DL / 2)
    mx = mat("MAXIMUM", mat("MULTIPLY", ay, 1.0), az)
    # ramka: pas między 0,84 a 0,89 „odległości” od środka
    ramka = mat("MULTIPLY", mat("GREATER_THAN", mx, 0.84), mat("LESS_THAN", mx, 0.89))
    if rewers:
        # kratka ukośna wewnątrz ramki
        u = mat("ADD", mat("MULTIPLY", sep.outputs[1], 14.0), mat("MULTIPLY", sep.outputs[2], 14.0))
        v = mat("SUBTRACT", mat("MULTIPLY", sep.outputs[1], 14.0), mat("MULTIPLY", sep.outputs[2], 14.0))
        l1 = mat("LESS_THAN", mat("ABSOLUTE", mat("SUBTRACT", mat("FRACT", u), 0.5)), 0.07)
        l2 = mat("LESS_THAN", mat("ABSOLUTE", mat("SUBTRACT", mat("FRACT", v), 0.5)), 0.07)
        srodek = mat("MULTIPLY", mat("MAXIMUM", l1, l2), mat("LESS_THAN", mx, 0.8))
    else:
        # romb pośrodku awersu
        romb = mat("ADD", mat("MULTIPLY", ay, 2.6), mat("MULTIPLY", az, 2.6))
        srodek = mat("MULTIPLY", mat("LESS_THAN", romb, 1.0), mat("GREATER_THAN", romb, 0.72))
    maska = mat("MAXIMUM", ramka, srodek)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = G.srgb(tlo)
    mix.inputs["B"].default_value = G.srgb(wzor)
    nt.links.new(maska, mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    nt.links.new(mat("MULTIPLY", maska, 0.9), b.inputs["Metallic"])
    nt.links.new(mat("SUBTRACT", 0.45, mat("MULTIPLY", maska, 0.2)), b.inputs["Roughness"])
    return m


M_AWERS = mat_karty("awers", (238, 230, 210), (212, 160, 60), False)
M_REWERS = mat_karty("rewers", (40, 70, 138), (236, 190, 96), True)
M_BRZEG = Z.pbr("brzeg_karty", (236, 228, 208), szorstkosc=0.6)

siatka_karty = None


def karta(nazwa, loc, rot):
    """Karta: grubość wzdłuż lokalnej osi x, szerokość y, długość z. Awers po stronie +x."""
    global siatka_karty
    if siatka_karty is None:
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(T, SZ, DL), verts=bm.verts)
        me = bpy.data.meshes.new("Karta")
        bm.to_mesh(me)
        bm.free()
        for mt in (M_BRZEG, M_AWERS, M_REWERS):
            me.materials.append(mt)
        for p in me.polygons:
            p.material_index = 1 if p.normal.x > 0.9 else (2 if p.normal.x < -0.9 else 0)
        siatka_karty = me
    ob = bpy.data.objects.new(nazwa, siatka_karty)
    sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


karty = []
dolne = {}
for k in range(PIETRA):
    n = PIETRA - k
    z0 = k * (WYS + T + 0.014) + 0.004
    for i in range(n):
        xs = (i - (n - 1) / 2) * PODZ
        lewa = karta(f"K{k}_{i}L", (xs - DELTA - DL / 2 * math.sin(KAT), random.uniform(-0.01, 0.01),
                                    z0 + DL / 2 * math.cos(KAT)), (0, KAT, 0))
        prawa = karta(f"K{k}_{i}P", (xs + DELTA + DL / 2 * math.sin(KAT), random.uniform(-0.01, 0.01),
                                     z0 + DL / 2 * math.cos(KAT)), (0, KAT, math.pi))
        karty += [lewa, prawa]
        if k == 0:
            dolne[i] = (lewa, prawa)
    for i in range(n - 1):
        xs = (i - (n - 2) / 2) * PODZ
        pozioma = karta(f"K{k}_{i}H", (xs, random.uniform(-0.01, 0.01), z0 + WYS + T / 2 + 0.007),
                        (0, math.pi / 2, 0))
        karty.append(pozioma)

wyjmowana = dolne[1][1]   # prawa karta drugiego daszka na dole

# ---------------------------------------------------------------- stół
M_STOL = Z.pbr("stol", (14, 22, 44), szorstkosc=0.36)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.25))
stol = bpy.context.active_object
stol.scale = (60, 60, 0.5)
stol.data.materials.append(M_STOL)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# ---------------------------------------------------------------- fizyka
bpy.ops.rigidbody.world_add()
rw = sc.rigidbody_world
rw.substeps_per_frame = 20
rw.use_split_impulse = True   # bez „wybuchu” przy starcie: odstępy między kartami są większe niż marginesy kolizji
rw.solver_iterations = 40
rw.time_scale = 0.46            # lekko zwolniony upadek
rw.point_cache.frame_start = 1
rw.point_cache.frame_end = NKL


def cialo(ob, typ="ACTIVE", masa=1.0):
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.rigidbody.object_add(type=typ)
    rb = ob.rigid_body
    rb.collision_shape = "BOX"
    rb.friction = 0.85
    rb.restitution = 0.05
    rb.use_margin = True
    rb.collision_margin = 0.001
    rb.mass = masa
    rb.linear_damping = 0.08
    rb.angular_damping = 0.25
    rb.use_deactivation = False
    return rb


cialo(stol, "PASSIVE").friction = 0.9
for ob in karty:
    rb = cialo(ob)
    rb.kinematic = True
    ob.keyframe_insert("rigid_body.kinematic", frame=1)
    puszcz = K_WYSUW[1] if ob is wyjmowana else K_PUSC
    ob.keyframe_insert("rigid_body.kinematic", frame=puszcz - 1)
    rb.kinematic = False
    ob.keyframe_insert("rigid_body.kinematic", frame=puszcz)

# wysunięcie karty: wzdłuż własnej płaszczyzny, w stronę kamery (-y), płynnie
y0 = wyjmowana.location.y
for f, dy in ((1, 0.0), (K_WYSUW[0], 0.0), (K_WYSUW[1], -0.95)):
    wyjmowana.location.y = y0 + dy
    wyjmowana.keyframe_insert("location", index=1, frame=f)
G.wygladz(wyjmowana)

# zapis symulacji (potrzebny, żeby kadry próbne z dowolnej klatki były takie jak w pełnym renderze)
with bpy.context.temp_override(scene=sc, point_cache=rw.point_cache):
    bpy.ops.ptcache.bake(bake=True)

# ---------------------------------------------------------------- kamera i światło
H_DOMKU = PIETRA * (WYS + T + 0.014)
cam = G.kamera((4.2, -7.5, 2.2), (0, 0, 1.6), lens=40)
cel = Z.pusty("Cel")
Z.lot_kamery(cam, cel, [
    (1, (3.2, -10.6, 2.4), (0.0, 0.0, 1.8)),
    (70, (2.7, -10.0, 2.3), (0.0, 0.0, 1.75)),
    (170, (1.7, -8.6, 2.1), (0.1, 0.0, 1.0)),
    (350, (-0.4, -7.4, 2.4), (0.3, -0.2, 0.35)),
])

Z.lampa((5.5, -6.5, 8.5), (0, 0, 1.4), moc=5200, kolor=(1.0, 0.86, 0.66), rozmiar=3.0)
for _l in (Z.lampa((-6.5, 2.5, 5.0), (0, 0, 1.2), moc=2400, kolor=(0.5, 0.66, 1.0), rozmiar=5.0, cien=False),
           Z.lampa((-3.0, -9.0, 1.4), (0, 0, 1.4), moc=900, kolor=(1.0, 0.9, 0.78), rozmiar=6.0, cien=False)):
    _l.data.specular_factor = 0.0     # bez odbicia lampy w blacie

G.renderuj(DIR, opcje, kadr_klatka=350)
