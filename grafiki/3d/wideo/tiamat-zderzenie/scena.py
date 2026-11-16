# -*- coding: utf-8 -*-
"""
Klip „tiamat-zderzenie” do odcinka 2 „Wielki uskok…” (rozdz. 03 „Laik i trzęsienia ziemi”).

HIPOTEZA (Zecharia Sitchin, na niej Leszek opiera swój wywód; nauka jej nie przyjmuje):
praZiemia – Tiamat – krąży między Marsem a Jowiszem, cała pokryta wodą. Do układu wpada obce ciało – Marduk –
i uderza w nią. Tiamat traci część masy (widoczna utrata ponad 2/3 skorupy), gruz rozchodzi się po jej orbicie
w pas planetoid, a ona sama zostaje zepchnięta na dzisiejszą orbitę Ziemi.

Odległości i wielkości nie są w skali (orbity zagęszczone, planety powiększone), ruch planet spowolniony.

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/tiamat-zderzenie/scena.py
  ... -- --proba 1,200,232,300,450     (tylko kadry próbne PNG do _klatki/)
"""
import bpy, bmesh, math, os, sys, random
import numpy as np
from mathutils import Vector, Matrix

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G

KLATEK = 450  # 18 s
opcje = G.argumenty()
sc = G.nowa_scena(KLATEK)
sc.eevee.taa_render_samples = int(os.environ.get("USKOK3D_PROBKI", "24"))

F_UDERZENIE = 230
F_ZEPCHNIECIE0, F_ZEPCHNIECIE1 = 262, 380

# orbity (jednostki sceny, nie w skali): promień, wielkość planety, kąt początkowy, prędkość [obr. na klip]
def predkosc(au):
    return 0.16 * (2.8 / au) ** 0.8            # wolniej niż w naturze, ale wewnętrzne szybciej
PLANETY = {
    "Merkury": dict(r=1.55, rp=0.075, au=0.39, kolor=(150, 140, 130), k0=40),
    "Wenus":   dict(r=2.25, rp=0.13, au=0.72, kolor=(230, 205, 150), k0=200),
    "Mars":    dict(r=3.55, rp=0.10, au=1.52, kolor=(190, 90, 50), k0=120),
    "Jowisz":  dict(r=6.6,  rp=0.42, au=5.2, kolor=(205, 170, 130), k0=60),
}
R_TIAMAT, R_ZIEMIA = 4.8, 2.9
W_TIAMAT = predkosc(2.8)
KAT_UDERZENIA = math.radians(-58)            # Tiamat przy uderzeniu: z przodu po prawej
K0_TIAMAT = KAT_UDERZENIA - 2 * math.pi * W_TIAMAT * (F_UDERZENIE - 1) / KLATEK


def kat(k0, w, f):
    return k0 + 2 * math.pi * w * (f - 1) / KLATEK


# ---------------------------------------------------------------- materiały
def mat_planeta(nazwa, kolor, szorst=0.7):
    m = bpy.data.materials.new(nazwa)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = G.srgb(kolor)
    p.inputs["Roughness"].default_value = szorst
    return m


def kula(nazwa, r, mat, seg=64):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=seg // 2)
    ob = bpy.context.active_object
    ob.name = nazwa
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob


# Słońce
slonce = kula("Slonce", 0.55, G.material_emisja("Slonce_mat", (255, 214, 140)))
mat_s = bpy.data.materials["Slonce_mat"]
for n in mat_s.node_tree.nodes:
    if n.type == "EMISSION":
        n.inputs["Strength"].default_value = 4.0
def mat_poswiata(nazwa, kolor, sila, potega):
    """Miękka poświata: przezroczystość rośnie ku brzegom kuli (jak blask)."""
    m = bpy.data.materials.new(nazwa)
    m.use_nodes = True
    nt_ = m.node_tree
    nt_.nodes.clear()
    o = nt_.nodes.new("ShaderNodeOutputMaterial")
    e = nt_.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = G.srgb(kolor)
    e.inputs["Strength"].default_value = sila
    tr = nt_.nodes.new("ShaderNodeBsdfTransparent")
    lw = nt_.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    inv = nt_.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    nt_.links.new(lw.outputs["Facing"], inv.inputs[1])
    pw = nt_.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = potega
    nt_.links.new(inv.outputs[0], pw.inputs[0])
    al = nt_.nodes.new("ShaderNodeValue"); al.name = "alfa"; al.outputs[0].default_value = 1.0
    ml = nt_.nodes.new("ShaderNodeMath"); ml.operation = "MULTIPLY"
    nt_.links.new(pw.outputs[0], ml.inputs[0]); nt_.links.new(al.outputs[0], ml.inputs[1])
    mx = nt_.nodes.new("ShaderNodeMixShader")
    nt_.links.new(ml.outputs[0], mx.inputs[0]); nt_.links.new(tr.outputs[0], mx.inputs[1]); nt_.links.new(e.outputs[0], mx.inputs[2])
    nt_.links.new(mx.outputs[0], o.inputs[0])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m
korona = kula("Korona", 1.0, mat_poswiata("Korona_mat", (255, 200, 110), 2.0, 2.5))
ld = bpy.data.lights.new("SwiatloSlonca", "POINT")
ld.energy = 1400
ld.shadow_soft_size = 0.5
ld.color = (1.0, 0.93, 0.8)
lo = bpy.data.objects.new("SwiatloSlonca", ld)
sc.collection.objects.link(lo)
sc.world.node_tree.nodes["Background"].inputs[0].default_value = G.srgb((30, 40, 70))
# słabe światło od strony widza, żeby nocne strony planet nie były czarne
ldf = bpy.data.lights.new("Wypelnienie", "SUN"); ldf.energy = 0.7; ldf.color = (0.75, 0.82, 1.0); ldf.use_shadow = False
lof = bpy.data.objects.new("Wypelnienie", ldf); sc.collection.objects.link(lof)
lof.rotation_euler = (math.radians(50), 0, 0)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.35

planety = {}
for n, d in PLANETY.items():
    planety[n] = kula(n, d["rp"], mat_planeta(n + "_mat", d["kolor"]))

# Tiamat: ocean, po uderzeniu rana (odsłonięty gorący płaszcz) i chmury pary
mt = bpy.data.materials.new("Tiamat_mat")
mt.use_nodes = True
nt = mt.node_tree
p = nt.nodes["Principled BSDF"]
p.inputs["Roughness"].default_value = 0.35
tc = nt.nodes.new("ShaderNodeTexCoord")
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.5; nz.inputs["Detail"].default_value = 6
nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
ocean = nt.nodes.new("ShaderNodeValToRGB")
ocean.color_ramp.elements[0].color = G.srgb((14, 60, 130))
ocean.color_ramp.elements[1].color = G.srgb((60, 140, 210))
nt.links.new(nz.outputs[0], ocean.inputs[0])
# maska rany: czasza od strony uderzenia (w układzie obiektu kierunek +x), poszarpana szumem
dotn = nt.nodes.new("ShaderNodeVectorMath"); dotn.operation = "DOT_PRODUCT"
dotn.inputs[1].default_value = (1, 0, 0)
nt.links.new(tc.outputs["Normal"], dotn.inputs[0])
nz2 = nt.nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 6
nt.links.new(tc.outputs["Object"], nz2.inputs["Vector"])
add = nt.nodes.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"
nt.links.new(nz2.outputs[0], add.inputs[0]); add.inputs[1].default_value = 0.5
nt.links.new(dotn.outputs["Value"], add.inputs[2])
czasza = nt.nodes.new("ShaderNodeMapRange")
czasza.inputs["From Min"].default_value = 0.05; czasza.inputs["From Max"].default_value = 0.25
nt.links.new(add.outputs[0], czasza.inputs["Value"])
v_rana = nt.nodes.new("ShaderNodeValue"); v_rana.name = v_rana.label = "rana"
mr = nt.nodes.new("ShaderNodeMath"); mr.operation = "MULTIPLY"
nt.links.new(czasza.outputs[0], mr.inputs[0]); nt.links.new(v_rana.outputs[0], mr.inputs[1])
plaszcz = nt.nodes.new("ShaderNodeValToRGB")
plaszcz.color_ramp.elements[0].color = G.srgb((60, 20, 10))
plaszcz.color_ramp.elements[1].color = G.srgb((255, 120, 30))
nt.links.new(nz2.outputs[0], plaszcz.inputs[0])
mixr = nt.nodes.new("ShaderNodeMix"); mixr.data_type = "RGBA"
nt.links.new(mr.outputs[0], mixr.inputs["Factor"])
nt.links.new(ocean.outputs[0], mixr.inputs["A"]); nt.links.new(plaszcz.outputs[0], mixr.inputs["B"])
# chmury pary
v_chm = nt.nodes.new("ShaderNodeValue"); v_chm.name = v_chm.label = "chmury"
nz3 = nt.nodes.new("ShaderNodeTexNoise"); nz3.inputs["Scale"].default_value = 4.5; nz3.inputs["Detail"].default_value = 8
nt.links.new(tc.outputs["Object"], nz3.inputs["Vector"])
chm = nt.nodes.new("ShaderNodeMapRange")
chm.inputs["From Min"].default_value = 0.5; chm.inputs["From Max"].default_value = 0.68
nt.links.new(nz3.outputs[0], chm.inputs["Value"])
mc = nt.nodes.new("ShaderNodeMath"); mc.operation = "MULTIPLY"
nt.links.new(chm.outputs[0], mc.inputs[0]); nt.links.new(v_chm.outputs[0], mc.inputs[1])
mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"
nt.links.new(mc.outputs[0], mixc.inputs["Factor"])
nt.links.new(mixr.outputs["Result"], mixc.inputs["A"]); mixc.inputs["B"].default_value = (0.92, 0.92, 0.95, 1)
nt.links.new(mixc.outputs["Result"], p.inputs["Base Color"])
p.inputs["Emission Color"].default_value = G.srgb((255, 110, 30))
em = nt.nodes.new("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = 3.0
nt.links.new(mr.outputs[0], em.inputs[0])
nt.links.new(em.outputs[0], p.inputs["Emission Strength"])
tiamat = kula("Tiamat", 0.27, mt, 96)

def klucze_wartosc(node, pary):
    for f, v in pary:
        node.outputs[0].default_value = v
        node.outputs[0].keyframe_insert("default_value", frame=f)
klucze_wartosc(v_rana, [(1, 0), (F_UDERZENIE, 0), (F_UDERZENIE + 4, 1), (F_UDERZENIE + 60, 1), (F_ZEPCHNIECIE1, 0.25), (KLATEK - 30, 0.0)])
klucze_wartosc(v_chm, [(1, 0), (F_UDERZENIE + 20, 0), (F_UDERZENIE + 120, 0.8), (KLATEK, 0.9)])
G.wygladz(nt)

# Marduk
mm = mat_planeta("Marduk_mat", (120, 50, 40), 0.8)
mm.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = G.srgb((200, 70, 30))
mm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.4
marduk = kula("Marduk", 0.24, mm)

# ---------------------------------------------------------------- orbity
def okrag(r, nazwa, kolor=(200, 200, 215), alfa=0.35, grub=0.012, przerywany=False):
    cu = bpy.data.curves.new(nazwa, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = grub
    n = 256
    if przerywany:
        for i in range(0, n, 2):
            sp = cu.splines.new("POLY"); sp.points.add(1)
            for j, t in enumerate((i, i + 1)):
                a = 2 * math.pi * t / n
                sp.points[j].co = (r * math.cos(a), r * math.sin(a), 0, 1)
    else:
        sp = cu.splines.new("POLY"); sp.points.add(n - 1)
        for i in range(n):
            a = 2 * math.pi * i / n
            sp.points[i].co = (r * math.cos(a), r * math.sin(a), 0, 1)
        sp.use_cyclic_u = True
    ob = bpy.data.objects.new(nazwa, cu)
    sc.collection.objects.link(ob)
    m = G.material_emisja(nazwa + "_mat", kolor, alfa)
    cu.materials.append(m)
    ob["mat"] = m.name
    return ob

for n, d in PLANETY.items():
    okrag(d["r"], "orbita_" + n)
orb_t = okrag(R_TIAMAT, "orbita_Tiamat", (110, 170, 240), 0.55, 0.016)
orb_z = okrag(R_ZIEMIA, "orbita_Ziemi", G.ZLOTY, 0.0, 0.016, przerywany=True)
G.animuj_alfa(bpy.data.materials[orb_t["mat"]], [(1, 0.55), (F_UDERZENIE, 0.55), (F_UDERZENIE + 60, 0.0)])
G.animuj_alfa(bpy.data.materials[orb_z["mat"]], [(1, 0.0), (F_ZEPCHNIECIE0 - 20, 0.0), (F_ZEPCHNIECIE0 + 10, 0.8)])

# gwiazdy w tle (losowe punkty, tylko tło)
random.seed(3)
bm = bmesh.new()
for i in range(700):
    v = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized() * 90
    res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.05 + 0.12 * random.random() ** 4)
    bmesh.ops.translate(bm, verts=res["verts"], vec=v)
me = bpy.data.meshes.new("Gwiazdy"); bm.to_mesh(me); bm.free()
gw = bpy.data.objects.new("Gwiazdy", me); sc.collection.objects.link(gw)
gw.data.materials.append(G.material_emisja("Gwiazdy_mat", (230, 230, 255), 0.8))

# ---------------------------------------------------------------- gruz (jedna siatka, ustawiana co klatkę)
NG = 650
rng = np.random.default_rng(11)
ico = bmesh.new()
bmesh.ops.create_icosphere(ico, subdivisions=1, radius=1.0)
ico_v = np.array([v.co[:] for v in ico.verts], np.float32)
ico_f = [[v.index for v in f.verts] for f in ico.faces]
ico.free()
nv = len(ico_v)
gr_skala = (0.012 + 0.05 * rng.random(NG) ** 3).astype(np.float32)
gr_deform = (0.6 + 0.8 * rng.random((NG, 3))).astype(np.float32)       # nieregularne bryłki
gr_delta = rng.uniform(-math.pi, math.pi, NG)                           # końcowe rozproszenie po orbicie
gr_dr = rng.normal(0, 0.28, NG)                                         # szerokość pasa
gr_dz = rng.normal(0, 0.07, NG)
gr_wyb = rng.normal(0, 1, (NG, 3)) * np.array([1.0, 1.0, 0.4])          # rozrzut tuż po wybuchu
gr_wyb /= np.maximum(np.linalg.norm(gr_wyb, axis=1, keepdims=True), 1e-6)
gr_v0 = 0.6 + 0.9 * rng.random(NG)
faces = [[i * nv + k for k in f] for i in range(NG) for f in ico_f]
me = bpy.data.meshes.new("Gruz")
me.from_pydata(np.zeros((NG * nv, 3)).tolist(), [], faces)
me.update()
gruz = bpy.data.objects.new("Gruz", me)
sc.collection.objects.link(gruz)
mg = mat_planeta("Gruz_mat", (120, 108, 96), 0.9)
gruz.data.materials.append(mg)
lok = (ico_v[None, :, :] * gr_deform[:, None, :] * gr_skala[:, None, None])   # NG×nv×3

# błysk uderzenia
blysk = kula("Blysk", 0.3, mat_poswiata("Blysk_mat", (255, 220, 160), 5.0, 1.5), 32)
_al = bpy.data.materials["Blysk_mat"].node_tree.nodes["alfa"].outputs[0]
for f, v in ((F_UDERZENIE - 1, 0.0), (F_UDERZENIE + 1, 1.0), (F_UDERZENIE + 16, 0.0)):
    _al.default_value = v; _al.keyframe_insert("default_value", frame=f)
lb = bpy.data.lights.new("BlyskSw", "POINT"); lb.energy = 0; lb.color = (1, 0.8, 0.5)
lbo = bpy.data.objects.new("BlyskSw", lb); sc.collection.objects.link(lbo)
for f, e in ((F_UDERZENIE - 1, 0), (F_UDERZENIE + 1, 700), (F_UDERZENIE + 18, 0)):
    lb.energy = e; lb.keyframe_insert("energy", frame=f)

# ślad Marduka: krzywa toru, rysowana stopniowo
def tor_marduka(t):
    """t: 0..1 przed uderzeniem (przylot), >1 dalej po uderzeniu (odlot)."""
    pi_ = Vector((R_TIAMAT * math.cos(KAT_UDERZENIA), R_TIAMAT * math.sin(KAT_UDERZENIA), 0))
    p0 = Vector((14.0, 9.0, 2.2))
    c1 = Vector((9.0, -4.0, 1.2))
    # kwadratowa krzywa Béziera od p0 przez c1 do punktu uderzenia; po uderzeniu prosto dalej (odbity tor)
    if t <= 1:
        return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * c1 + t * t * pi_
    kier = (pi_ - c1).normalized()
    kier = Vector((kier.x * 0.6 - 0.5, kier.y * 0.6 - 0.2, -0.05)).normalized()
    return pi_ + kier * (t - 1) * 9.0
F_PRZYLOT0 = 110
def t_marduka(f):
    if f < F_UDERZENIE:
        return max(0.0, (f - F_PRZYLOT0) / (F_UDERZENIE - F_PRZYLOT0)) ** 0.9
    return 1.0 + (f - F_UDERZENIE) / 160.0
cu = bpy.data.curves.new("SladMarduka", "CURVE")
cu.dimensions = "3D"
cu.bevel_depth = 0.035
cu.use_fill_caps = False
sp = cu.splines.new("POLY")
TORP = [tor_marduka(i / 120) for i in range(121)]
sp.points.add(len(TORP) - 1)
for pt, co in zip(sp.points, TORP):
    pt.co = (*co, 1)
slad = bpy.data.objects.new("SladMarduka", cu)
sc.collection.objects.link(slad)
ms = G.material_emisja("Slad_mat", (230, 110, 60), 0.0)
cu.materials.append(ms)
G.animuj_alfa(ms, [(1, 0.0), (F_PRZYLOT0, 0.0), (F_PRZYLOT0 + 20, 0.55), (F_UDERZENIE, 0.55), (F_UDERZENIE + 60, 0.0)])

# ---------------------------------------------------------------- napisy (zawsze przodem do kamery)
cam = G.kamera((0, -18, 14), (0, 0, 0), lens=31)
tlo = G.tlo_kamery(cam, odl=120)
napisy = []
def etykieta(tekst, cel_fn, rozm=0.27, kolor=(235, 230, 215), krój="arialb", dz=0.45, nazwa="et"):
    ob = G.napis(tekst, rozm, kolor, krój, "CENTER", nazwa=nazwa, obrys=((5, 7, 12), 0.02))
    c = ob.constraints.new("COPY_ROTATION")
    c.target = cam
    napisy.append((ob, cel_fn, dz))
    return ob

def poz_planety(n, f):
    d = PLANETY[n]
    a = kat(math.radians(d["k0"]), predkosc(d["au"]), f)
    return Vector((d["r"] * math.cos(a), d["r"] * math.sin(a), 0))

def r_tiamat(f):
    u = G.gladko((f - F_ZEPCHNIECIE0) / (F_ZEPCHNIECIE1 - F_ZEPCHNIECIE0))
    return R_TIAMAT + (R_ZIEMIA - R_TIAMAT) * u

def kat_tiamat(f):
    # po uderzeniu chwilowe wyhamowanie, potem szybciej (bliżej Słońca)
    a = kat(K0_TIAMAT, W_TIAMAT, f)
    if f > F_UDERZENIE:
        u = G.gladko((f - F_ZEPCHNIECIE0) / (F_ZEPCHNIECIE1 - F_ZEPCHNIECIE0))
        a += 2 * math.pi * 0.05 * u * (f - F_ZEPCHNIECIE0) / 100 if f > F_ZEPCHNIECIE0 else 0.0
    return a

def poz_tiamat(f):
    a = kat_tiamat(f)
    r = r_tiamat(f)
    return Vector((r * math.cos(a), r * math.sin(a), 0))

for n in PLANETY:
    etykieta(n, (lambda n: lambda f: poz_planety(n, f))(n), dz=PLANETY[n]["rp"] + 0.32, nazwa="et_" + n)
etykieta("Słońce", lambda f: Vector((0, 0, 0)), dz=1.05, kolor=G.ZLOTY, nazwa="et_Slonce")
et_t = etykieta("Tiamat (praZiemia)", poz_tiamat, rozm=0.32, kolor=(140, 200, 255), dz=0.62, nazwa="et_Tiamat")
et_z = etykieta("Ziemia", poz_tiamat, rozm=0.32, kolor=(140, 200, 255), dz=0.62, nazwa="et_Ziemia")
et_m = etykieta("Marduk", lambda f: tor_marduka(t_marduka(f)), rozm=0.32, kolor=(240, 140, 90), dz=0.65, nazwa="et_Marduk")
KAT_PAS = math.radians(186)
et_p = etykieta("pas planetoid", lambda f: Vector((R_TIAMAT * 1.07 * math.cos(KAT_PAS), R_TIAMAT * 1.07 * math.sin(KAT_PAS), 0)),
                rozm=0.3, kolor=(215, 205, 190), dz=-0.55, nazwa="et_pas")
KAT_ORBZ = math.radians(-128)
et_oz = etykieta("dzisiejsza orbita Ziemi", lambda f: Vector((R_ZIEMIA * math.cos(KAT_ORBZ), R_ZIEMIA * math.sin(KAT_ORBZ), 0)),
                 rozm=0.24, kolor=G.ZLOTY, dz=-0.4, nazwa="et_orbz")
G.alfa_napisu(et_t, [(1, 1), (F_UDERZENIE - 8, 1), (F_UDERZENIE, 0), (F_UDERZENIE + 30, 0), (F_UDERZENIE + 50, 1), (F_ZEPCHNIECIE1 - 30, 1), (F_ZEPCHNIECIE1, 0)])
G.alfa_napisu(et_z, [(1, 0), (F_ZEPCHNIECIE1 - 30, 0), (F_ZEPCHNIECIE1, 1)])
G.alfa_napisu(et_m, [(1, 0), (F_PRZYLOT0 + 10, 0), (F_PRZYLOT0 + 35, 1), (F_UDERZENIE - 25, 1), (F_UDERZENIE - 8, 0)])
G.alfa_napisu(et_p, [(1, 0), (F_UDERZENIE + 110, 0), (F_UDERZENIE + 150, 1)])
G.alfa_napisu(et_oz, [(1, 0), (F_ZEPCHNIECIE0 - 10, 0), (F_ZEPCHNIECIE0 + 25, 1)])

# tytuł u góry (przypięty do kamery)
ODL = 8.0
px = G.skala_px(cam, ODL)
def napis_ekran(tekst, y, rozm_px, kolor, krój="georgiab", nazwa="ekran"):
    pos = G.ekran_na_kamerze(cam, 960, y, ODL)
    return G.napis(tekst, rozm_px * px, kolor, krój, "CENTER", rodzic=cam, loc=pos, nazwa=nazwa,
                   obrys=((5, 7, 12), 0.03 * rozm_px * px))
ty = napis_ekran("Tiamat i Marduk według Z. Sitchina", 66, 48, G.ZLOTY, nazwa="tytul")
G.alfa_napisu(ty, [(1, 0), (12, 0), (40, 1), (F_PRZYLOT0 + 10, 1), (F_PRZYLOT0 + 40, 0)])
ty2 = napis_ekran("praZiemia zepchnięta na dzisiejszą orbitę", 66, 46, G.ZLOTY, nazwa="tytul2")
G.alfa_napisu(ty2, [(1, 0), (F_ZEPCHNIECIE0, 0), (F_ZEPCHNIECIE0 + 30, 1)])

# ---------------------------------------------------------------- ruch: wszystko liczone dla klatki
CEL = Vector((0, -0.6, 0))
def ustaw(scene, depsgraph=None):
    f = scene.frame_current
    # kamera: powolny obrót i lekkie zbliżenie
    t = (f - 1) / (KLATEK - 1)
    s = G.gladko(t)
    az = math.radians(-90 + 18 * s)
    el = math.radians(47 - 5 * s)
    D = 19.5 - 1.2 * s
    cam.location = CEL + Vector((D * math.cos(az) * math.cos(el), D * math.sin(az) * math.cos(el), D * math.sin(el)))
    G.patrz(cam, CEL)
    for n, ob in planety.items():
        ob.location = poz_planety(n, f)
    tiamat.location = poz_tiamat(f)
    # Tiamat po uderzeniu mniejsza (utrata masy), rana zwrócona ku miejscu uderzenia
    u = G.gladko((f - F_UDERZENIE) / 12)
    tiamat.scale = [1 - 0.22 * u] * 3
    kier = tor_marduka(0.9) - tor_marduka(1.0)          # skąd nadleciał Marduk: tam zwrócona rana
    tiamat.rotation_euler = (0, 0, math.atan2(kier.y, kier.x))
    marduk.location = tor_marduka(t_marduka(f))
    marduk.hide_render = f < F_PRZYLOT0
    cu.bevel_factor_end = min(1.0, t_marduka(f)) if f < F_UDERZENIE + 60 else 1.0
    cu.bevel_factor_start = max(0.0, min(1.0, t_marduka(f)) - 0.45)
    pu = tor_marduka(1.0)
    blysk.location = pu
    blysk.scale = [1 + 2.2 * max(0.0, min(1.0, (f - F_UDERZENIE) / 16)) ** 0.6] * 3
    lbo.location = pu + Vector((0, 0, 0.3))
    # gruz
    if f < F_UDERZENIE:
        gruz.hide_render = True
    else:
        gruz.hide_render = False
        dt = f - F_UDERZENIE
        wyb = 1 - math.exp(-dt / 10.0)                      # szybki rozrzut
        roz = G.gladko(dt / 170.0)                          # rozejście się po orbicie
        a_imp = KAT_UDERZENIA + 2 * math.pi * W_TIAMAT * dt / KLATEK
        a = a_imp + gr_delta * roz
        r = R_TIAMAT + gr_dr * (0.3 + 0.7 * roz)
        c = np.stack([r * np.cos(a), r * np.sin(a), gr_dz * (0.4 + 0.6 * roz)], axis=1)
        c += gr_wyb * (gr_v0 * 0.9 * wyb * (1 - roz))[:, None]
        v = (lok + c[:, None, :]).reshape(-1, 3).astype(np.float32)
        gruz.data.vertices.foreach_set("co", v.ravel())
        gruz.data.update()
    for ob, fn, dz in napisy:
        ob.location = fn(f) + Vector((0, 0, dz))
# cieni nie rzucają: Słońce, poświaty, orbity, napisy, tło (inaczej zasłaniają światło w środku Słońca)
for ob in sc.objects:
    if ob.name not in set(planety) | {"Tiamat", "Marduk", "Gruz"}:
        ob.visible_shadow = False
bpy.app.handlers.frame_change_pre.append(ustaw)
ustaw(sc)

G.renderuj(TU, opcje, kadr_klatka=KLATEK)
