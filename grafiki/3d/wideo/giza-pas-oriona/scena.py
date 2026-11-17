# -*- coding: utf-8 -*-
"""
Klip „giza-pas-oriona” do odcinka 2 „Wielki uskok…” (rozdz. 13, „Piramidy w Gizie krzyczą o ruchach Oriona”).

HIPOTEZA (Robert Bauval, „korelacja Oriona”; sporna): trzy piramidy w Gizie ułożono jak trzy gwiazdy pasa Oriona.
Położenia piramid i gwiazd są prawdziwe:
  * piramidy: środki Cheopsa i Chefrena z pomiaru W. M. F. Petriego (1883, domena publiczna; odległości osiowe
    13 931 i 13 166 cali), Mykerinos: odległość N–S od Chefrena z Petriego, odległość E–W z Wikidata (CC0);
    boki i wysokości jak w opisach budowli (Petrie / Wikipedia),
  * gwiazdy: Alnitak, Alnilam, Mintaka z katalogu HYG v4.4 (CC BY-SA 4.0, `_dane/hyg/gwiazdy_mag6.csv`),
    rzut gnomoniczny wokół Alnilama, niebo „jak widziane z ziemi” (wschód po lewej).
Gwiazdy pojawiają się nad piramidami w takim układzie, jak na niebie (północ u góry), potem grupa obraca się
i skaluje do najlepszego dopasowania (metoda najmniejszych kwadratów: obrót, skala, przesunięcie, bez odbicia).

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/giza-pas-oriona/scena.py
  ... -- --proba 1,150,230,400     (tylko kadry próbne PNG do _klatki/)
"""
import bpy, bmesh, math, os, sys, csv, random
import numpy as np
from mathutils import Vector, Matrix

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TU, "..", "_wspolne"))
import globus as G

KLATEK = 400  # 16 s
opcje = G.argumenty()
sc = G.nowa_scena(KLATEK)
sc.eevee.taa_render_samples = int(os.environ.get("USKOK3D_PROBKI", "32"))
J = 0.1   # jednostka sceny = 10 m

# ---------------------------------------------------------------- dane
CAL = 0.0254
# środki piramid w metrach (x = wschód, y = północ), początek w środku Cheopsa.
# W. M. F. Petrie, „The Pyramids and Temples of Gizeh” (1883), §92, odległości środków w calach (północ–południe, wschód–zachód):
#   I–II: 13931,6 i 13165,8;  I–III: 29102,0 i 22616,0;  II–III: 15170,4 i 9450,2
dx_ch, dy_ch = -13165.8 * CAL, -13931.6 * CAL            # Chefren względem Cheopsa
dx_my, dy_my = -22616.0 * CAL, -29102.0 * CAL            # Mykerinos względem Cheopsa
PIRAMIDY = [
    # nazwa, (x, y) [m], bok E–W, bok N–S, wysokość [m]
    ("Cheops", (0.0, 0.0), 230.33, 230.33, 146.6),
    ("Chefren", (dx_ch, dy_ch), 215.25, 215.25, 143.5),
    ("Mykerinos", (dx_my, dy_my), 104.6, 102.2, 65.5),
]
GWIAZDY = ["Alnitak", "Alnilam", "Mintaka"]              # Alnitak ↔ Cheops, Alnilam ↔ Chefren, Mintaka ↔ Mykerinos
gw = {}
with open(os.path.join(G.DANE, "hyg", "gwiazdy_mag6.csv"), encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["proper"] in GWIAZDY:
            gw[row["proper"]] = (float(row["ra_h"]) * 15, float(row["dec_deg"]), float(row["mag"]))
ra0, de0 = math.radians(gw["Alnilam"][0]), math.radians(gw["Alnilam"][1])
S = []
for n in GWIAZDY:
    ra, de = math.radians(gw[n][0]), math.radians(gw[n][1])
    c = math.sin(de0) * math.sin(de) + math.cos(de0) * math.cos(de) * math.cos(ra - ra0)
    xi = math.cos(de) * math.sin(ra - ra0) / c
    eta = (math.cos(de0) * math.sin(de) - math.sin(de0) * math.cos(de) * math.cos(ra - ra0)) / c
    S.append((-math.degrees(xi), math.degrees(eta)))     # wschód w lewo: niebo widziane z ziemi
S = np.array(S)
P = np.array([p[1] for p in PIRAMIDY])
# dopasowanie podobieństwa (liczby zespolone): P ≈ k·S + t
cS, cP = S.mean(0), P.mean(0)
zs = (S - cS) @ [1, 1j]
zp = (P - cP) @ [1, 1j]
k = (np.conj(zs) @ zp) / (np.conj(zs) @ zs)
KAT = float(np.angle(k))
SKALA = float(abs(k))                                    # m na stopień
RES = np.abs(zp - k * zs)
print(f"[dopasowanie] obrót {math.degrees(KAT):.1f}°, skala {SKALA:.1f} m/°, odchyłki {', '.join(f'{r:.1f}' for r in RES)} m")

# ---------------------------------------------------------------- scena
sc.world.node_tree.nodes["Background"].inputs[0].default_value = G.srgb((16, 24, 46))
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.9

# pustynia
bpy.ops.mesh.primitive_plane_add(size=600, location=(cP[0] * J, cP[1] * J, 0))
pus = bpy.context.active_object
pus.name = "Pustynia"
mp = bpy.data.materials.new("Pustynia"); mp.use_nodes = True
ntp = mp.node_tree; pp = ntp.nodes["Principled BSDF"]
pp.inputs["Roughness"].default_value = 0.95
nz = ntp.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.05; nz.inputs["Detail"].default_value = 8
rp = ntp.nodes.new("ShaderNodeValToRGB")
rp.color_ramp.elements[0].color = G.srgb((128, 104, 74)); rp.color_ramp.elements[1].color = G.srgb((168, 138, 98))
ntp.links.new(nz.outputs[0], rp.inputs[0]); ntp.links.new(rp.outputs[0], pp.inputs["Base Color"])
# zanik pustyni ku brzegom (w granat tła)
tc = ntp.nodes.new("ShaderNodeTexCoord")
gr = ntp.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"
mpg = ntp.nodes.new("ShaderNodeMapping"); mpg.inputs["Scale"].default_value = (2.2, 2.2, 1)
mpg.inputs["Location"].default_value = (0, 0, 0)
ntp.links.new(tc.outputs["Object"], mpg.inputs[0])
sp_ = ntp.nodes.new("ShaderNodeVectorMath"); sp_.operation = "SCALE"; sp_.inputs["Scale"].default_value = 1 / 300 * 2.0
ntp.links.new(tc.outputs["Object"], sp_.inputs[0])
ntp.links.new(sp_.outputs[0], gr.inputs[0])
mixk = ntp.nodes.new("ShaderNodeMix"); mixk.data_type = "RGBA"
ntp.links.new(gr.outputs["Fac"], mixk.inputs["Factor"])
mixk.inputs["A"].default_value = G.srgb((14, 20, 38))
ntp.links.new(rp.outputs[0], mixk.inputs["B"])
ntp.links.new(mixk.outputs["Result"], pp.inputs["Base Color"])
pus.data.materials.append(mp)

mpir = bpy.data.materials.new("Piramida"); mpir.use_nodes = True
pb = mpir.node_tree.nodes["Principled BSDF"]
pb.inputs["Base Color"].default_value = G.srgb((196, 168, 122)); pb.inputs["Roughness"].default_value = 0.85
nzp = mpir.node_tree.nodes.new("ShaderNodeTexNoise"); nzp.inputs["Scale"].default_value = 4
bmp = mpir.node_tree.nodes.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.25
mpir.node_tree.links.new(nzp.outputs[0], bmp.inputs["Height"]); mpir.node_tree.links.new(bmp.outputs[0], pb.inputs["Normal"])

wierzcholki = []
for nazwa, (x, y), a, b, h in PIRAMIDY:
    me = bpy.data.meshes.new(nazwa)
    bm = bmesh.new()
    vs = [bm.verts.new((sx * a / 2 * J, sy * b / 2 * J, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    top = bm.verts.new((0, 0, h * J))
    for i in range(4):
        bm.faces.new((vs[i], vs[(i + 1) % 4], top))
    bm.faces.new(list(reversed(vs)))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(nazwa, me)
    sc.collection.objects.link(ob)
    ob.location = (x * J, y * J, 0)
    ob.data.materials.append(mpir)
    wierzcholki.append(Vector((x * J, y * J, h * J)))

# światło: księżycowe z południowego wschodu, nisko, i słabe z nieba
def swiatlo(nazwa, energia, kier, kolor, kat=1.0, cien=True):
    ld = bpy.data.lights.new(nazwa, "SUN"); ld.energy = energia; ld.color = kolor; ld.angle = math.radians(kat)
    ld.use_shadow = cien
    ob = bpy.data.objects.new(nazwa, ld); sc.collection.objects.link(ob)
    ob.rotation_euler = (-Vector(kier)).to_track_quat("-Z", "Y").to_euler()
swiatlo("Ksiezyc", 4.2, (0.7, -0.6, 0.45), (0.92, 0.93, 1.0), 1.0)
swiatlo("Wypelnienie", 0.35, (-0.5, 0.6, 0.8), (0.6, 0.7, 1.0), 10, False)

# ---------------------------------------------------------------- gwiazdy
ZG = 18.0                                   # wysokość płaszczyzny gwiazd (nad szczytami)
def mat_poswiata(nazwa, kolor, sila, potega):
    m = bpy.data.materials.new(nazwa); m.use_nodes = True
    nt_ = m.node_tree; nt_.nodes.clear()
    o = nt_.nodes.new("ShaderNodeOutputMaterial")
    e = nt_.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = G.srgb(kolor); e.inputs["Strength"].default_value = sila
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

def klucze_alfa(mat, pary):
    al = mat.node_tree.nodes["alfa"].outputs[0]
    for f, v in pary:
        al.default_value = v; al.keyframe_insert("default_value", frame=f)

F_GW0, F_GW1 = 165, 200          # gwiazdy się pojawiają
F_OBR0, F_OBR1 = 215, 300        # obrót i dopasowanie
m_gw = mat_poswiata("Gwiazda_rdzen", (235, 242, 255), 12.0, 0.6)
m_bl = mat_poswiata("Gwiazda_blask", (170, 200, 255), 3.0, 3.0)
klucze_alfa(m_gw, [(1, 0), (F_GW0, 0), (F_GW1, 1)])
klucze_alfa(m_bl, [(1, 0), (F_GW0, 0), (F_GW1, 0.9)])
gwiazdy_ob = []
for i, n in enumerate(GWIAZDY):
    mag = gw[n][2]
    r = 0.9 * 10 ** (-0.12 * mag)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=32, ring_count=16)
    rd = bpy.context.active_object; rd.name = "gw_" + n; rd.data.materials.append(m_gw)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 5.5, segments=32, ring_count=16)
    bl = bpy.context.active_object; bl.name = "blask_" + n; bl.data.materials.append(m_bl)
    bl.parent = rd
    gwiazdy_ob.append(rd)

# linia pasa (łączy gwiazdy) i pionowe promienie do szczytów po dopasowaniu
def linia(punkty, nazwa, kolor=G.ZLOTY, grub=0.08):
    cu = bpy.data.curves.new(nazwa, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = grub
    sp = cu.splines.new("POLY"); sp.points.add(len(punkty) - 1)
    for pt, co in zip(sp.points, punkty):
        pt.co = (*co, 1)
    ob = bpy.data.objects.new(nazwa, cu); sc.collection.objects.link(ob)
    m = G.material_emisja(nazwa + "_mat", kolor, 0.0); cu.materials.append(m); ob["mat"] = m.name
    return ob, cu
pas, pas_cu = linia([(0, 0, ZG)] * 3, "pas", (190, 210, 255), 0.07)
G.animuj_alfa(bpy.data.materials[pas["mat"]], [(1, 0), (F_GW1 - 10, 0), (F_GW1 + 10, 0.45)])
promienie = []
for i, v in enumerate(wierzcholki):
    ob, cu_ = linia([tuple(v), (v.x, v.y, ZG)], f"promien_{i}", G.ZLOTY, 0.06)
    G.animuj_alfa(bpy.data.materials[ob["mat"]], [(1, 0), (F_OBR1, 0), (F_OBR1 + 30, 0.7)])
    promienie.append(ob)

# ---------------------------------------------------------------- napisy
KREM = (240, 232, 214)
et_pir = []
for (nazwa, (x, y), a, b, h), v in zip(PIRAMIDY, wierzcholki):
    ob = G.napis(nazwa, 3.4, KREM, "georgiab", "LEFT", loc=(x * J + a / 2 * J + 2.5, y * J - 1.2, 0.05), nazwa="et_" + nazwa,
                 obrys=((20, 16, 12), 0.06))
    et_pir.append(ob)
    G.alfa_napisu(ob, [(1, 0), (25, 0), (55, 1)])
et_gw = []
for n in GWIAZDY:
    ob = G.napis(n, 3.0, (175, 205, 255), "arialb", "RIGHT", nazwa="et_" + n, obrys=((5, 7, 12), 0.06))
    et_gw.append(ob)
    G.alfa_napisu(ob, [(1, 0), (F_GW0 + 10, 0), (F_GW1 + 10, 1)])

# ---------------------------------------------------------------- kamera
CEL0 = Vector((cP[0] * J, cP[1] * J, 4.0))
CEL1 = CEL0 + Vector((0, -6.5, 0))          # w widoku z góry treść nieco wyżej (miejsce na podpis u dołu)
CEL = CEL0
cam = G.kamera((0, -100, 100), CEL, lens=85)
cam.data.clip_end = 3000
tlo = G.tlo_kamery(cam, odl=1500)
ODL = 50.0
px = G.skala_px(cam, ODL)
def napis_ekran(tekst, y, rozm_px, kolor, krój="georgiab", nazwa="ekran"):
    pos = G.ekran_na_kamerze(cam, 960, y, ODL)
    return G.napis(tekst, rozm_px * px, kolor, krój, "CENTER", rodzic=cam, loc=pos, nazwa=nazwa,
                   obrys=((5, 7, 12), 0.03 * rozm_px * px))
t1 = napis_ekran("Pas Oriona nad piramidami w Gizie", 66, 50, G.ZLOTY, nazwa="tytul")
t2 = napis_ekran(f"mapa nieba obrócona o {abs(math.degrees(KAT)):.0f}° (południe u góry), odchyłki do {RES.max():.0f} m",
                 116, 28, (215, 210, 198), "georgia", nazwa="tytul2")
G.alfa_napisu(t1, [(1, 0), (F_GW0 - 20, 0), (F_GW0 + 10, 1)])
G.alfa_napisu(t2, [(1, 0), (F_OBR1, 0), (F_OBR1 + 30, 1)])

def patrz_gora(ob, cel, gora):
    f = (Vector(cel) - ob.location).normalized()
    r = f.cross(gora).normalized()
    u = r.cross(f)
    m = Matrix((r, u, -f)).transposed()
    ob.rotation_euler = m.to_euler()

D0, D1 = 420.0, 640.0
def ustaw(scene, depsgraph=None):
    fr = scene.frame_current
    # kamera: z południowego wschodu, ukośnie, potem nad głowę (północ u góry)
    s1 = G.gladko5((fr - 1) / 160)
    s2 = G.gladko5((fr - 90) / 130)
    az = math.radians(-50 - 40 * s1)
    el = math.radians(27 + 62.9 * s2)
    D = D0 + (D1 - D0) * G.gladko5((fr - 40) / 200)
    CEL = CEL0.lerp(CEL1, s2)
    pos = CEL + Vector((D * math.cos(az) * math.cos(el), D * math.sin(az) * math.cos(el), D * math.sin(el)))
    cam.location = pos
    gora = Vector((0, 0, 1)).lerp(Vector((0, 1, 0)), s2).normalized()
    patrz_gora(cam, CEL, gora)
    # gwiazdy: najpierw jak na niebie (skala dopasowania, środek nad środkiem piramid), potem obrót do dopasowania
    u = G.gladko5((fr - F_OBR0) / (F_OBR1 - F_OBR0))
    kk = SKALA * complex(math.cos(KAT * u), math.sin(KAT * u))
    for i, ob in enumerate(gwiazdy_ob):
        z = complex(*(S[i] - cS)) * kk
        x, y = (cP[0] + z.real) * J, (cP[1] + z.imag) * J
        ob.location = (x, y, ZG)
        et_gw[i].location = (x - 2.8, y + 0.4, ZG + 0.5)
    pts = pas_cu.splines[0].points
    for i, ob in enumerate(gwiazdy_ob):
        pts[i].co = (*ob.location, 1)
bpy.app.handlers.frame_change_pre.append(ustaw)
ustaw(sc)
for ob in sc.objects:
    if ob.name not in {"Cheops", "Chefren", "Mykerinos", "Pustynia"}:
        ob.visible_shadow = False

G.renderuj(TU, opcje, kadr_klatka=KLATEK)
