# -*- coding: utf-8 -*-
"""
Wschód Słońca ze szczytu schodkowej piramidy i zielony promień (rozdział 11), wersja 2.

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/wschod-slonca-z-piramidy/scena.py -- probne 1,140,270,332,345,500
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/wschod-slonca-z-piramidy/scena.py -- pelny
  ... -- zloz      (tylko ponowne złożenie klip.mp4 i kadr.jpg z gotowych klatek w _klatki/)

Ujęcie: kamera nadlatuje od południowego zachodu nad dżunglą do szczytu piramidy i zatrzymuje się za świątynią
(grzebień dachowy na pierwszym planie), patrząc na wschód ponad lasem z mgłami; w lesie widać dwie dalsze piramidy.
Gdy zbliża się wschód, w prawym górnym rogu pojawia się okrągłe „okienko lunety”: ten sam wschód widziany
teleobiektywem z progu świątyni (pole widzenia 0,9°). W okienku widać zielony skrawek (zielony promień),
potem wschodzi pomarańczowa, spłaszczona tarcza z zieloną obwódką na górnym brzegu.

Klip powstaje z trzech przebiegów, składanych ffmpeg-iem:
  * główny (1920×1080, klatki _klatki/k_####.png),
  * luneta (430×430, klatki _klatki/lupa_####.png, tylko od klatki K_LUPA),
  * nakładki (pierścienie i linia: nakl_a.png, podpis „zielony promień”: nakl_b.png).

Fizyka: Słońce ma prawdziwą średnicę kątową (0,53°), jest spłaszczone przez refrakcję (ok. 0,86).
Zielony promień: obraz zielony leży nieco wyżej niż czerwony (rozszczepienie światła w atmosferze),
a niebieski jest rozproszony, więc jako pierwszy wychyla się nad horyzont zielony skrawek.
Przesunięcie zielonego obrazu jest powiększone (jak przy mirażu, który na zdjęciach z teleobiektywem
czyni błysk widocznym). Czas jest przyspieszony ok. 15×, sam błysk trwa ok. 1,4 s.

Układ: x = wschód, y = północ, z = góra, metry.
"""
import bpy, math, os, sys, subprocess, time, random, shutil
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

DIR = os.path.dirname(os.path.abspath(__file__))
NAZWA = os.path.basename(DIR)
KLATKI = os.path.join(DIR, '_klatki')
BLOKADA = os.path.join(os.path.dirname(DIR), '.renderuje')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
TRYB = ARGS[0] if ARGS else 'pelny'
FPS = 25
NKL = 500          # 20 s
KADR = 341
random.seed(3)

# oś czasu (klatki)
K_DOLOT = 270             # koniec dolotu kamery (potem tylko powolny najazd)
K_LUPA = 285              # pojawia się okienko lunety
K_BLYSK = 330             # zielony skrawek wychyla się nad horyzont
K_CZERWONY = 365          # wychyla się czerwono-pomarańczowa tarcza

# geometria
H_PLAT = 40.0             # wysokość podłogi świątyni na szczycie
OKO = 1.6
ZC = H_PLAT + OKO         # wysokość oka obserwatora na progu (kamera lunety)
D_SL = 45000.0            # odległość „ekranu” Słońca
R_ANG = math.radians(0.2665)   # promień kątowy Słońca
SPLASZCZ = 0.86
DELTA = 0.18              # przesunięcie obrazu zielonego (w promieniach Słońca), mocno powiększone
R_GRUNT = 30000.0         # zasięg płaskiej równiny lasu
Z_LAS = 22.0              # wysokość dachu lasu
Z_DALEKO = Z_LAS - 4.0    # wysokość dalekiej równiny
HORYZONT = -math.atan((ZC - Z_DALEKO) / (R_GRUNT + 800.0))   # kąt horyzontu z progu świątyni (ujemny)

# kamera główna
KAM_START = Vector((-132.0, -88.0, 67.0))
KAM_KONIEC = Vector((-47.0, -15.0, 50.6))
KAM_DRYF = Vector((0.026, 0.003, -0.0012))   # m na klatkę po dolocie
KAM_CEL0 = Vector((2.0, 2.0, 43.0))          # na początku kamera patrzy na szczyt piramidy
KAM_AZ1, KAM_POCH1 = 3.6, -2.2               # na końcu: azymut (° na północ od wschodu) i pochylenie
KAM_OB0, KAM_OB1 = 30.0, 42.0                # ogniskowa

# okienko lunety (piksele kadru 1920×1080)
LX, LY, RL = 1545, 248, 215
POLE_LUPY = 0.9           # pole widzenia lunety w stopniach
ZLOTY = (240, 196, 111)
ZIELONY = (150, 236, 120)


def srgb(c, a=1.0):
    def lin(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (lin(c[0]), lin(c[1]), lin(c[2]), a)


def gladko(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def gladko5(t):
    t = max(0.0, min(1.0, t)); return t * t * t * (t * (6 * t - 15) + 10)


def wyczysc():
    for kol in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                bpy.data.lights, bpy.data.curves, bpy.data.node_groups, bpy.data.worlds,
                bpy.data.collections, bpy.data.images):
        for b in list(kol):
            try:
                kol.remove(b)
            except Exception:
                pass


def wezel(nt, typ, loc=(0, 0), **wej):
    n = nt.nodes.new(typ)
    n.location = loc
    for k, v in wej.items():
        if k in ('operation', 'data_type', 'blend_type'):
            setattr(n, k, v)
        else:
            n.inputs[k].default_value = v
    return n


def lacz(nt, a, b):
    nt.links.new(a, b)


class W:
    """Matematyka na gniazdach węzłów."""
    def __init__(s, nt):
        s.nt = nt
    def m(s, op, a, b=None, c=None):
        n = s.nt.nodes.new('ShaderNodeMath'); n.operation = op
        for i, x in enumerate((a, b, c)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                s.nt.links.new(x, n.inputs[i])
        return n.outputs[0]
    def clamp01(s, a):
        n = s.nt.nodes.new('ShaderNodeClamp'); s.nt.links.new(a, n.inputs['Value'])
        return n.outputs[0]
    def smooth(s, e0, e1, x):
        n = s.nt.nodes.new('ShaderNodeMapRange'); n.interpolation_type = 'SMOOTHSTEP'; n.clamp = True
        s.nt.links.new(x, n.inputs['Value'])
        n.inputs['From Min'].default_value = e0; n.inputs['From Max'].default_value = e1
        n.inputs['To Min'].default_value = 0.0; n.inputs['To Max'].default_value = 1.0
        return n.outputs['Result']


class Siatka:
    def __init__(s):
        s.v, s.f, s.m = [], [], []
    def box(s, x0, x1, y0, y1, z0, z1, ins=0.0, m=0):
        b = len(s.v)
        s.v += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                (x0 + ins, y0 + ins, z1), (x1 - ins, y0 + ins, z1), (x1 - ins, y1 - ins, z1), (x0 + ins, y1 - ins, z1)]
        s.f += [(b, b + 3, b + 2, b + 1), (b + 4, b + 5, b + 6, b + 7), (b, b + 1, b + 5, b + 4),
                (b + 1, b + 2, b + 6, b + 5), (b + 2, b + 3, b + 7, b + 6), (b + 3, b, b + 4, b + 7)]
        s.m += [m] * 6
    def pryzma_xz(s, prof, y0, y1, m=0):
        """Profil w płaszczyźnie (x, z) wyciągnięty wzdłuż y."""
        pole = sum(prof[i][0] * prof[(i + 1) % len(prof)][1] - prof[(i + 1) % len(prof)][0] * prof[i][1]
                   for i in range(len(prof)))
        if pole > 0:
            prof = prof[::-1]
        n = len(prof); b = len(s.v)
        s.v += [(x, y0, z) for x, z in prof] + [(x, y1, z) for x, z in prof]
        s.f.append(tuple(b + i for i in reversed(range(n))))
        s.f.append(tuple(b + n + i for i in range(n)))
        s.m += [m, m]
        for i in range(n):
            j = (i + 1) % n
            s.f.append((b + i, b + j, b + n + j, b + n + i)); s.m.append(m)
    def obiekt(s, nazwa, materialy, kol):
        me = bpy.data.meshes.new(nazwa)
        me.from_pydata(s.v, [], s.f); me.validate()
        for mt in materialy:
            me.materials.append(mt)
        if len(materialy) > 1:
            me.polygons.foreach_set('material_index', s.m)
        ob = bpy.data.objects.new(nazwa, me); kol.objects.link(ob)
        return ob


# ---------------------------------------------------------------- materiały
def niebo_wezel(nt, loc):
    sky = wezel(nt, 'ShaderNodeTexSky', loc)
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_disc = False
    sky.sun_rotation = math.radians(90.0)     # azymut 90° = wschód
    sky.air_density = 1.0; sky.aerosol_density = 2.5
    return sky


NIEBA = []   # węzły nieba do animacji wysokości Słońca
JASNOSC_NIEBA = 0.065


def niebo_w_kierunku_patrzenia(nt, w, loc, wys=0.02):
    """Kolor nieba tuż nad horyzontem w kierunku, w którym patrzy kamera (do mgiełki i mgły)."""
    geo = wezel(nt, 'ShaderNodeNewGeometry', (loc[0] - 600, loc[1]))
    sxyz = wezel(nt, 'ShaderNodeSeparateXYZ', (loc[0] - 400, loc[1])); lacz(nt, geo.outputs['Incoming'], sxyz.inputs[0])
    cxyz = wezel(nt, 'ShaderNodeCombineXYZ', (loc[0] - 200, loc[1]))
    lacz(nt, w.m('MULTIPLY', sxyz.outputs['X'], -1.0), cxyz.inputs['X'])
    lacz(nt, w.m('MULTIPLY', sxyz.outputs['Y'], -1.0), cxyz.inputs['Y'])
    cxyz.inputs['Z'].default_value = wys
    sky = niebo_wezel(nt, loc); NIEBA.append(sky)
    lacz(nt, cxyz.outputs[0], sky.inputs[0])
    return sky.outputs[0]


def material_kamien():
    """Wapień: plamy i zacieki (szum) + rzędy ciosów kamiennych na ścianach (tekstura cegieł w układzie x+y, z)."""
    mt = bpy.data.materials.new('kamien'); nt = mt.node_tree; nt.nodes.clear()
    w = W(nt)
    out = wezel(nt, 'ShaderNodeOutputMaterial', (600, 0))
    bs = wezel(nt, 'ShaderNodeBsdfPrincipled', (300, 0), Roughness=1.0)
    bs.inputs['Specular IOR Level'].default_value = 0.08
    tc = wezel(nt, 'ShaderNodeTexCoord', (-900, 0))
    no = wezel(nt, 'ShaderNodeTexNoise', (-650, 100), Scale=0.9, Detail=8.0, Roughness=0.62)
    lacz(nt, tc.outputs['Object'], no.inputs['Vector'])
    cr = wezel(nt, 'ShaderNodeValToRGB', (-380, 100))
    cr.color_ramp.elements[0].position = 0.30; cr.color_ramp.elements[0].color = (0.20, 0.19, 0.165, 1)
    cr.color_ramp.elements[1].position = 0.74; cr.color_ramp.elements[1].color = (0.47, 0.44, 0.375, 1)
    lacz(nt, no.outputs['Fac'], cr.inputs['Fac'])
    # ciosy: na ścianach pionowych; na powierzchniach poziomych gładko
    sep = wezel(nt, 'ShaderNodeSeparateXYZ', (-900, -300)); lacz(nt, tc.outputs['Object'], sep.inputs[0])
    cv = wezel(nt, 'ShaderNodeCombineXYZ', (-700, -300))
    lacz(nt, w.m('ADD', sep.outputs['X'], sep.outputs['Y']), cv.inputs['X']); lacz(nt, sep.outputs['Z'], cv.inputs['Y'])
    br = wezel(nt, 'ShaderNodeTexBrick', (-500, -300))
    lacz(nt, cv.outputs[0], br.inputs['Vector'])
    br.inputs['Color1'].default_value = (1, 1, 1, 1); br.inputs['Color2'].default_value = (0.80, 0.79, 0.76, 1)
    br.inputs['Mortar'].default_value = (0.38, 0.37, 0.35, 1)
    br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.035
    br.inputs['Brick Width'].default_value = 1.15; br.inputs['Row Height'].default_value = 0.56
    geo = wezel(nt, 'ShaderNodeNewGeometry', (-900, -600))
    sn = wezel(nt, 'ShaderNodeSeparateXYZ', (-700, -600)); lacz(nt, geo.outputs['Normal'], sn.inputs[0])
    sciana = w.m('SUBTRACT', 1.0, w.smooth(0.5, 0.9, w.m('ABSOLUTE', sn.outputs['Z'])))
    mx = wezel(nt, 'ShaderNodeMix', (0, 100), data_type='RGBA', blend_type='MULTIPLY')
    lacz(nt, sciana, mx.inputs['Factor']); lacz(nt, cr.outputs['Color'], mx.inputs[6]); lacz(nt, br.outputs['Color'], mx.inputs[7])
    lacz(nt, mx.outputs[2], bs.inputs['Base Color'])
    # chropowatość + spoiny
    no2 = wezel(nt, 'ShaderNodeTexNoise', (-650, -800), Scale=6.0, Detail=6.0)
    lacz(nt, tc.outputs['Object'], no2.inputs['Vector'])
    h = w.m('SUBTRACT', w.m('MULTIPLY', no2.outputs['Fac'], 0.3), w.m('MULTIPLY', w.m('MULTIPLY', br.outputs['Fac'], sciana), 0.6))
    bump = wezel(nt, 'ShaderNodeBump', (60, -200), Strength=0.5, Distance=0.05)
    lacz(nt, h, bump.inputs['Height'])
    lacz(nt, bump.outputs['Normal'], bs.inputs['Normal'])
    lacz(nt, bs.outputs[0], out.inputs['Surface'])
    return mt


def material_las(blisko):
    """Dach lasu + mgiełka w stronę koloru nieba (im dalej, tym jaśniej).
    blisko=True: korony są w geometrii, kolor zależy od wysokości (prześwity ciemne, wierzchołki jasne);
    blisko=False: korony udaje tekstura komórkowa."""
    mt = bpy.data.materials.new('las_blisko' if blisko else 'las_daleko'); nt = mt.node_tree; nt.nodes.clear()
    w = W(nt)
    out = wezel(nt, 'ShaderNodeOutputMaterial', (900, 0))
    bs = wezel(nt, 'ShaderNodeBsdfPrincipled', (400, 0), Roughness=0.85)
    bs.inputs['Specular IOR Level'].default_value = 0.2
    tc = wezel(nt, 'ShaderNodeTexCoord', (-900, 0))
    no = wezel(nt, 'ShaderNodeTexNoise', (-650, 100), Scale=0.004, Detail=8.0)
    lacz(nt, tc.outputs['Object'], no.inputs['Vector'])
    cr = wezel(nt, 'ShaderNodeValToRGB', (-400, 100))
    cr.color_ramp.elements[0].color = (0.022, 0.055, 0.02, 1); cr.color_ramp.elements[1].color = (0.085, 0.13, 0.045, 1)
    lacz(nt, no.outputs['Fac'], cr.inputs['Fac'])
    if blisko:
        sep = wezel(nt, 'ShaderNodeSeparateXYZ', (-650, -200)); lacz(nt, tc.outputs['Object'], sep.inputs[0])
        zf = w.smooth(Z_LAS - 7.0, Z_LAS + 6.0, sep.outputs['Z'])
        no3 = wezel(nt, 'ShaderNodeTexNoise', (-650, -400), Scale=0.13, Detail=2.0)
        lacz(nt, tc.outputs['Object'], no3.inputs['Vector'])
        sz = w.m('MULTIPLY', w.m('MULTIPLY_ADD', zf, 1.15, 0.12), w.m('MULTIPLY_ADD', no3.outputs['Fac'], 0.9, 0.55))
        no4 = wezel(nt, 'ShaderNodeTexNoise', (-650, -600), Scale=1.3, Detail=3.0)
        lacz(nt, tc.outputs['Object'], no4.inputs['Vector'])
        wys_b, sila_b, odl_b = no4.outputs['Fac'], 0.7, 0.5
    else:
        vo = wezel(nt, 'ShaderNodeTexVoronoi', (-650, -200), Scale=0.075, Randomness=0.9)
        lacz(nt, tc.outputs['Object'], vo.inputs['Vector'])
        kop = w.clamp01(w.m('SUBTRACT', 1.0, w.m('MULTIPLY', vo.outputs['Distance'], 1.35)))
        sz = w.m('MULTIPLY_ADD', kop, 0.9, 0.3)
        wys_b, sila_b, odl_b = kop, 1.0, 4.0
    mx = wezel(nt, 'ShaderNodeMix', (0, 100), data_type='RGBA', blend_type='MULTIPLY'); mx.inputs['Factor'].default_value = 1.0
    lacz(nt, cr.outputs['Color'], mx.inputs[6])
    cmb = wezel(nt, 'ShaderNodeCombineXYZ', (-100, 0))
    for k in 'XYZ':
        lacz(nt, sz, cmb.inputs[k])
    lacz(nt, cmb.outputs[0], mx.inputs[7])
    lacz(nt, mx.outputs[2], bs.inputs['Base Color'])
    bump = wezel(nt, 'ShaderNodeBump', (200, -300), Strength=sila_b, Distance=odl_b)
    lacz(nt, wys_b, bump.inputs['Height']); lacz(nt, bump.outputs['Normal'], bs.inputs['Normal'])
    # mgiełka powietrzna: kolor nieba przy horyzoncie w kierunku patrzenia
    kol_nieba = niebo_w_kierunku_patrzenia(nt, w, (200, 500))
    em = wezel(nt, 'ShaderNodeEmission', (450, 500), Strength=JASNOSC_NIEBA * 0.62)
    lacz(nt, kol_nieba, em.inputs['Color'])
    camd = wezel(nt, 'ShaderNodeCameraData', (-400, 800))
    d = w.m('MAXIMUM', w.m('SUBTRACT', camd.outputs['View Distance'], 150.0), 0.0)
    fog = w.m('MULTIPLY', w.m('SUBTRACT', 1.0, w.m('EXPONENT', w.m('DIVIDE', d, -4200.0))), 0.84)
    ms = wezel(nt, 'ShaderNodeMixShader', (700, 200))
    lacz(nt, fog, ms.inputs[0]); lacz(nt, bs.outputs[0], ms.inputs[1]); lacz(nt, em.outputs[0], ms.inputs[2])
    lacz(nt, ms.outputs[0], out.inputs['Surface'])
    return mt


N_MGIEL = 5


def material_mgla(nr):
    """Poranna mgła: stos cienkich, półprzezroczystych warstw w zagłębieniach lasu (im wyżej, tym mniejsze płaty),
    świecących kolorem nieba nad horyzontem. Wokół piramidy mgły nie ma."""
    mt = bpy.data.materials.new(f'mgla{nr}'); nt = mt.node_tree; nt.nodes.clear()
    w = W(nt)
    out = wezel(nt, 'ShaderNodeOutputMaterial', (900, 0))
    geo = wezel(nt, 'ShaderNodeNewGeometry', (-900, 0))
    no = wezel(nt, 'ShaderNodeTexNoise', (-550, 0), Scale=0.0042, Detail=5.0, Roughness=0.55)
    no.noise_dimensions = '4D'
    lacz(nt, geo.outputs['Position'], no.inputs['Vector'])
    for f, v in ((1, 0.0), (NKL, 0.2)):       # mgła powoli się przelewa
        no.inputs['W'].default_value = v; no.inputs['W'].keyframe_insert('default_value', frame=f)
    prog = 0.40 + 0.042 * nr
    plat = w.smooth(prog, prog + 0.2, no.outputs['Fac'])
    camd = wezel(nt, 'ShaderNodeCameraData', (-550, 300))
    d = camd.outputs['View Distance']
    zanik = w.m('MULTIPLY', w.smooth(40.0, 160.0, d), w.m('SUBTRACT', 1.0, w.smooth(1300.0, 3000.0, d)))
    sep = wezel(nt, 'ShaderNodeSeparateXYZ', (-700, -300)); lacz(nt, geo.outputs['Position'], sep.inputs[0])
    r = w.m('SQRT', w.m('ADD', w.m('MULTIPLY', sep.outputs['X'], sep.outputs['X']), w.m('MULTIPLY', sep.outputs['Y'], sep.outputs['Y'])))
    polana = w.smooth(50.0, 120.0, r)
    alfa = w.m('MULTIPLY', w.m('MULTIPLY', w.m('MULTIPLY', plat, zanik), polana), 0.45)
    kol_nieba = niebo_w_kierunku_patrzenia(nt, w, (200, 500), wys=0.09)
    em = wezel(nt, 'ShaderNodeEmission', (450, 500), Strength=JASNOSC_NIEBA * 0.95)
    lacz(nt, kol_nieba, em.inputs['Color'])
    tr = wezel(nt, 'ShaderNodeBsdfTransparent', (450, 200))
    ms = wezel(nt, 'ShaderNodeMixShader', (700, 200))
    lacz(nt, alfa, ms.inputs[0]); lacz(nt, tr.outputs[0], ms.inputs[1]); lacz(nt, em.outputs[0], ms.inputs[2])
    lacz(nt, ms.outputs[0], out.inputs['Surface'])
    mt.surface_render_method = 'BLENDED'
    return mt


def material_slonce():
    """Tarcza Słońca: trzy obrazy (czerwony, zielony, niebieski) przesunięte w pionie."""
    mt = bpy.data.materials.new('slonce'); nt = mt.node_tree; nt.nodes.clear()
    w = W(nt)
    out = wezel(nt, 'ShaderNodeOutputMaterial', (1400, 0))
    tc = wezel(nt, 'ShaderNodeTexCoord', (-1200, 0))
    sep = wezel(nt, 'ShaderNodeSeparateXYZ', (-1000, 0)); lacz(nt, tc.outputs['Object'], sep.inputs[0])
    sk = 1.4                                   # płaszczyzna ±1 = ±1,4 promienia
    px = w.m('MULTIPLY', sep.outputs['X'], sk)
    py = w.m('MULTIPLY', sep.outputs['Y'], sk)
    # „błysk”: chwilowe wzmocnienie zieleni (wartość animowana na węźle Value)
    blysk = wezel(nt, 'ShaderNodeValue', (-1000, -400)); blysk.label = 'blysk'; blysk.name = 'blysk'
    blysk.outputs[0].default_value = 1.0
    kanaly = []
    for off, jas in ((0.0, 2.3), (DELTA, 0.95), (DELTA, 0.04)):
        dy = w.m('DIVIDE', w.m('SUBTRACT', py, off), SPLASZCZ)
        r2 = w.m('ADD', w.m('MULTIPLY', px, px), w.m('MULTIPLY', dy, dy))
        r = w.m('SQRT', r2)
        maska = w.clamp01(w.m('DIVIDE', w.m('SUBTRACT', 1.0, r), 0.012))
        # pociemnienie brzegu tarczy
        mu = w.m('SQRT', w.m('MAXIMUM', w.m('SUBTRACT', 1.0, r2), 0.0))
        limb = w.m('MULTIPLY_ADD', mu, 0.3, 0.7)
        # niższa część tarczy przechodzi przez grubszą warstwę powietrza: bardziej czerwona
        grad = w.clamp01(w.m('MULTIPLY_ADD', py, 0.22, 0.78))
        v = w.m('MULTIPLY', w.m('MULTIPLY', maska, limb), jas)
        if off > 0:
            v = w.m('MULTIPLY', v, grad)
        kanaly.append(v)
    kanaly[1] = w.m('MULTIPLY', kanaly[1], blysk.outputs[0])
    cc = wezel(nt, 'ShaderNodeCombineColor', (900, 0))
    for i in range(3):
        lacz(nt, kanaly[i], cc.inputs[i])
    em = wezel(nt, 'ShaderNodeEmission', (1100, 0), Strength=1.0)
    lacz(nt, cc.outputs[0], em.inputs['Color'])
    # przezroczystość poza tarczą
    alfa = w.clamp01(w.m('ADD', w.m('ADD', kanaly[0], kanaly[1]), kanaly[2]))
    tr = wezel(nt, 'ShaderNodeBsdfTransparent', (1100, 200))
    ms = wezel(nt, 'ShaderNodeMixShader', (1250, 0))
    lacz(nt, alfa, ms.inputs[0]); lacz(nt, tr.outputs[0], ms.inputs[1]); lacz(nt, em.outputs[0], ms.inputs[2])
    lacz(nt, ms.outputs[0], out.inputs['Surface'])
    try:
        mt.surface_render_method = 'BLENDED'
    except Exception:
        pass
    return mt, blysk


# ---------------------------------------------------------------- budowle
def piramida_i_swiatynia(kol, M):
    """Schodkowa piramida w stylu Majów: front (schody) na wschód, świątynia z grzebieniem dachowym na szczycie."""
    S = Siatka()
    n = 8; bw = 46.0; tw = 14.0; h = H_PLAT - 0.8
    dh = h / n
    for k in range(n):
        w0 = bw + (tw - bw) * k / n; w1 = bw + (tw - bw) * (k + 1) / n
        cof = (w0 - w1) / 2
        ins = min(0.45 * cof, 0.14 * dh)
        c = 1.2
        S.box(-w0 / 2, w0 / 2, -w0 / 2 + c, w0 / 2 - c, k * dh, (k + 1) * dh, ins)
        S.box(-w0 / 2 + c, w0 / 2 - c, -w0 / 2, w0 / 2, k * dh, (k + 1) * dh - 0.012, ins)
        wt = w0 - 2 * ins
        S.box(-wt / 2 - 0.25, wt / 2 + 0.25, -wt / 2 - 0.25 + c, wt / 2 + 0.25 - c, (k + 1) * dh - 1.0, (k + 1) * dh - 0.3)
    S.box(-tw / 2, tw / 2, -tw / 2, tw / 2, h, H_PLAT, 0.05)
    # schody na wschód (+x): od podstawy do krawędzi platformy
    xf, xt = bw / 2 + 4.0, tw / 2
    ns = int(H_PLAT / 0.36); r = H_PLAT / ns; run = (xf - xt) / ns
    pts = [(xt - 0.6, 0.0), (xf, 0.0)]
    for i in range(1, ns + 1):
        pts.append((xf - (i - 1) * run, i * r)); pts.append((xf - i * run, i * r))
    pts.append((xt - 0.6, H_PLAT))
    sw = 8.0
    S.pryzma_xz(pts, -sw / 2, sw / 2)
    for sy in (-1, 1):
        y0, y1 = (sw / 2, sw / 2 + 1.3) if sy > 0 else (-sw / 2 - 1.3, -sw / 2)
        S.pryzma_xz([(xf + 0.3, 0.0), (xt - 0.6, 0.0), (xt - 0.6, H_PLAT + 0.45), (xt + 0.3, H_PLAT + 0.45)], y0, y1)
    ob_p = S.obiekt('piramida', [M['kamien']], kol)

    # świątynia: grube mury, wejście 2,2 × 2,9 m od wschodu, gzyms, pochyła strefa górna, grzebień dachowy
    T = Siatka()
    x_front = 1.2                 # lico ściany frontowej (wejście)
    gr = 1.5                      # grubość muru
    x0, x1 = x_front - gr - 3.0 - gr, x_front   # wnętrze: 3 m głębokości
    y0, y1 = -5.0, 5.0
    z0 = H_PLAT; zs = z0 + 3.4; zt = z0 + 6.2
    dw, dh_ = 1.1, 2.9
    # ściana frontowa z otworem
    T.box(x_front - gr, x_front, y0, -dw, z0, zs)
    T.box(x_front - gr, x_front, dw, y1, z0, zs)
    T.box(x_front - gr, x_front, -dw, dw, z0 + dh_, zs)            # nadproże
    # ściany boczne i tylna
    T.box(x0, x0 + gr, y0, y1, z0, zs)
    T.box(x0 + gr, x_front - gr, y0, y0 + gr, z0, zs)
    T.box(x0 + gr, x_front - gr, y1 - gr, y1, z0, zs)
    # gzyms środkowy, pochyła strefa górna (w środku sklepienie), gzyms górny
    T.box(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, zs, zs + 0.4)
    T.box(x0, x1, y0, y1, zs + 0.4, zt - 0.45, 0.42)
    T.box(x0 - 0.12, x1 + 0.12, y0 - 0.12, y1 + 0.12, zt - 0.45, zt)
    # grzebień dachowy (trzy zwężające się piętra) z pionowymi żebrami
    xa, xb = x0 + 0.4, x0 + 2.9
    T.box(xa, xb, -4.3, 4.3, zt, zt + 2.8, 0.2)
    T.box(xa + 0.2, xb - 0.2, -3.5, 3.5, zt + 2.8, zt + 5.2, 0.2)
    T.box(xa + 0.4, xb - 0.4, -2.5, 2.5, zt + 5.2, zt + 7.0, 0.25)
    for yy in (-3.2, -1.6, 0.0, 1.6, 3.2):
        T.box(xa - 0.14, xb + 0.14, yy - 0.28, yy + 0.28, zt + 0.35, zt + 2.45)
    for yy in (-2.2, 0.0, 2.2):
        T.box(xa + 0.08, xb - 0.08, yy - 0.26, yy + 0.26, zt + 3.1, zt + 4.9)
    T.box(x0 - 0.5, x_front + 0.5, y0 - 0.5, y1 + 0.5, z0 - 0.02, z0 + 0.25)   # próg / podłoga
    ob_t = T.obiekt('swiatynia', [M['kamien']], kol)
    return ob_p, ob_t


def dalsze_piramidy(kol, wzory):
    """Dwie dalsze piramidy wystające z lasu (zwrócone schodami ku naszej, jak świątynie I i II w Tikal)."""
    for i, (x, y, s) in enumerate(((425.0, 72.0, 0.86), (752.0, -88.0, 0.72))):
        for wz in wzory:
            ob = bpy.data.objects.new(f'{wz.name}_dal{i}', wz.data)
            ob.location = (x, y, 0.0); ob.scale = (s, s, s); ob.rotation_euler = (0, 0, math.radians(180.0))
            kol.objects.link(ob)


# ---------------------------------------------------------------- las
def _h01(a, b, k):
    n = (a * 374761393 + b * 668265263 + k * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n = n ^ (n >> 16)
    return (n & 0xFFFFFF).astype(np.float32) / float(0x1000000)


def fala_lasu(X, Y):
    """Łagodne pofałdowanie dachu lasu (w zagłębieniach zbiera się mgła)."""
    return Z_LAS + 2.0 * np.sin(X / 120.0 + np.cos(Y / 90.0)) * np.cos(Y / 140.0) + 1.0 * np.sin(X / 47.0 + 2.0 * np.sin(Y / 55.0))


def korony(X, Y, kom=9.0):
    """Wysokość koron drzew względem dachu lasu: kopuły o promieniu 5–8 m, czasem drzewo wyższe od innych."""
    ix = np.floor(X / kom).astype(np.int64); iy = np.floor(Y / kom).astype(np.int64)
    best = np.full(X.shape, -6.0, np.float32)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            ci, cj = ix + dx, iy + dy
            h0, h1, h2, h3 = (_h01(ci, cj, k) for k in range(4))
            px = (ci + 0.15 + 0.7 * h0) * kom; py = (cj + 0.15 + 0.7 * h1) * kom
            r = kom * (0.55 + 0.35 * h2)
            top = h3 ** 3 * 7.0 + h2 * 2.0
            d2 = (X - px) ** 2 + (Y - py) ** 2
            z = top - 0.85 * r + 0.85 * np.sqrt(np.maximum(r * r - d2, 0.0))
            best = np.maximum(best, np.where(d2 < r * r, z, -6.0).astype(np.float32))
    return best


def siatka_z_wysokosci(nazwa, xs, ys, Z, maska_scian, mat, kol):
    nx, ny = len(xs), len(ys)
    X, Y = np.meshgrid(xs, ys)
    V = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()]).astype(np.float32)
    ii, jj = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1))
    a = (jj * nx + ii).ravel()
    F = np.column_stack([a, a + 1, a + nx + 1, a + nx])
    if maska_scian is not None:
        F = F[maska_scian.ravel()]
    me = bpy.data.meshes.new(nazwa)
    me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(F.size); me.loops.foreach_set('vertex_index', F.ravel().astype(np.int32))
    me.polygons.add(len(F)); me.polygons.foreach_set('loop_start', (np.arange(len(F)) * 4).astype(np.int32))
    me.update(); me.validate(); me.materials.append(mat); me.shade_smooth()
    ob = bpy.data.objects.new(nazwa, me); kol.objects.link(ob)
    return ob


BL = (-300.0, 660.0, -430.0, 430.0)     # zasięg bliskiego lasu z koronami (x0, x1, y0, y1)


def las(kol, M):
    """Bliski las z koronami drzew, dalszy pofałdowany dach lasu i daleka płaska równina po horyzont."""
    # blisko: siatka 1,5 m, korony w geometrii; wokół piramidy polana
    krok = 1.5
    xs = np.arange(BL[0], BL[1] + krok, krok); ys = np.arange(BL[2], BL[3] + krok, krok)
    X, Y = np.meshgrid(xs, ys)
    brzeg = np.clip(np.minimum(np.minimum(X - BL[0], BL[1] - X), np.minimum(Y - BL[2], BL[3] - Y)) / 40.0, 0.0, 1.0)
    Z = fala_lasu(X, Y) + korony(X, Y) * brzeg
    kat = np.arctan2(Y, X)
    rr = np.hypot(X, Y) * (1.0 + 0.10 * np.sin(3.0 * kat + 0.7) + 0.06 * np.sin(7.0 * kat))
    t = np.clip((rr - 31.0) / 9.0, 0.0, 1.0); pol = t * t * (3 - 2 * t)
    Z = Z * pol
    siatka_z_wysokosci('las_blisko', xs, ys, Z, None, M['las_blisko'], kol)
    # dalej: siatka 10 m, nieco niżej (zakładka pod bliskim lasem, bez szpar)
    krok = 10.0
    xs = np.arange(-2600, 4200 + krok, krok); ys = np.arange(-3100, 3100 + krok, krok)
    X, Y = np.meshgrid(xs, ys)
    Z = fala_lasu(X, Y) - 1.5 + 1.2 * np.sin(X / 11.0 + 2.0 * np.sin(Y / 13.0)) * np.cos(Y / 9.0 + np.sin(X / 7.0))
    cx = X[:-1, :-1] + krok / 2; cy = Y[:-1, :-1] + krok / 2
    zostaw = ~((cx > BL[0] + 25) & (cx < BL[1] - 25) & (cy > BL[2] + 25) & (cy < BL[3] - 25))
    siatka_z_wysokosci('las_dalej', xs, ys, Z, zostaw, M['las_daleko'], kol)
    # równina: pierścień do 30 km
    R = R_GRUNT; r = 2400.0
    v = [(-R, -R, 0), (R, -R, 0), (R, R, 0), (-R, R, 0), (-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0)]
    f = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me2 = bpy.data.meshes.new('las_daleko'); me2.from_pydata(v, [], f); me2.update(); me2.materials.append(M['las_daleko'])
    ob2 = bpy.data.objects.new('las_daleko', me2); ob2.location = (800, 0, Z_DALEKO); kol.objects.link(ob2)


MGLY = []


def mgly(kol):
    for nr in range(N_MGIEL):
        z = Z_LAS - 4.5 + nr * 1.6
        me = bpy.data.meshes.new(f'mgla{nr}')
        s = 3600.0
        me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
        me.materials.append(material_mgla(nr))
        ob = bpy.data.objects.new(f'mgla{nr}', me); ob.location = (600.0, 0.0, z)
        ob.visible_shadow = False
        kol.objects.link(ob); MGLY.append(ob)


# ---------------------------------------------------------------- Słońce i czas
def wysokosc_slonca(f):
    """Kąt wysokości środka tarczy (radiany) w klatce f; wolno wokół błysku, szybciej potem."""
    h_v = R_ANG * SPLASZCZ
    e_blysk = HORYZONT - h_v * (1 + DELTA)       # szczyt obrazu zielonego na horyzoncie
    e_czerw = HORYZONT - h_v                     # szczyt obrazu czerwonego na horyzoncie
    e_kon = HORYZONT + h_v * 0.55                # koniec: tarcza w ~3/4 nad horyzontem
    e_start = e_blysk - math.radians(0.33)
    pkt = [(1, e_start), (K_BLYSK - 60, e_blysk - math.radians(0.035)), (K_BLYSK, e_blysk), (K_CZERWONY, e_czerw), (NKL, e_kon)]
    # gładka interpolacja (monotoniczna, kubiczna Hermite'a)
    xs = [p[0] for p in pkt]; ys = [p[1] for p in pkt]
    n = len(pkt)
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [d[0]] + [0.5 * (d[i - 1] + d[i]) for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):
        if xs[i] <= f <= xs[i + 1]:
            t = (f - xs[i]) / (xs[i + 1] - xs[i]); hh = xs[i + 1] - xs[i]
            h00 = 2 * t ** 3 - 3 * t ** 2 + 1; h10 = t ** 3 - 2 * t ** 2 + t; h01 = -2 * t ** 3 + 3 * t ** 2; h11 = t ** 3 - t ** 2
            return h00 * ys[i] + h10 * hh * m[i] + h01 * ys[i + 1] + h11 * hh * m[i + 1]
    return ys[-1]


def pozycja_slonca(f):
    return Vector((D_SL, 0.0, ZC + D_SL * math.tan(wysokosc_slonca(f))))


def slonce(kol):
    mt, blysk = material_slonce()
    R_m = D_SL * math.tan(R_ANG) * 1.4
    me = bpy.data.meshes.new('slonce')
    me.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
    me.materials.append(mt)
    ob = bpy.data.objects.new('slonce', me)
    ob.scale = (R_m, R_m, 1)
    ob.rotation_euler = (math.radians(90), 0, math.radians(90))   # płaszczyzna YZ, przodem do kamery (−x)
    ob.visible_shadow = False
    kol.objects.link(ob)
    # poświata wokół Słońca w ujęciu głównym (aureola w mgiełce i olśnienie obiektywu); w lunecie jej nie ma
    mp = bpy.data.materials.new('poswiata'); ntp = mp.node_tree; ntp.nodes.clear()
    wp = W(ntp)
    outp = wezel(ntp, 'ShaderNodeOutputMaterial', (600, 0))
    tcp = wezel(ntp, 'ShaderNodeTexCoord', (-600, 0))
    ln = ntp.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; lacz(ntp, tcp.outputs['Object'], ln.inputs[0])
    r = ln.outputs['Value']                      # 0 = środek, 1 = 4° od Słońca
    sila = wezel(ntp, 'ShaderNodeValue', (-600, -300)); sila.name = 'sila'
    jas = wp.m('MULTIPLY', wp.m('MULTIPLY', wp.m('EXPONENT', wp.m('MULTIPLY', r, -9.0)), wp.m('SUBTRACT', 1.0, wp.smooth(0.6, 1.0, r))), sila.outputs[0])
    emp = wezel(ntp, 'ShaderNodeEmission', (200, 0)); emp.inputs['Color'].default_value = (1.0, 0.5, 0.18, 1)
    lacz(ntp, jas, emp.inputs['Strength'])
    trp = wezel(ntp, 'ShaderNodeBsdfTransparent', (200, 200))
    addp = ntp.nodes.new('ShaderNodeAddShader'); lacz(ntp, trp.outputs[0], addp.inputs[0]); lacz(ntp, emp.outputs[0], addp.inputs[1])
    lacz(ntp, addp.outputs[0], outp.inputs['Surface'])
    mp.surface_render_method = 'BLENDED'
    mep = bpy.data.meshes.new('poswiata')
    mep.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
    mep.materials.append(mp)
    pos = bpy.data.objects.new('poswiata', mep)
    R_p = D_SL * math.tan(math.radians(4.0))
    pos.scale = (R_p, R_p, 1); pos.rotation_euler = ob.rotation_euler; pos.visible_shadow = False
    kol.objects.link(pos); MGLY.append(pos)      # lista obiektów ukrywanych w przebiegu lunety
    # światło słoneczne (pojawia się, gdy wyjdzie tarcza)
    ld = bpy.data.lights.new('swiatlo_slonca', 'SUN'); ld.angle = math.radians(0.53); ld.color = (1.0, 0.42, 0.18)
    try:
        ld.shadow_maximum_resolution = 0.25      # mniej stron cieni (duża scena)
    except Exception:
        pass
    lo = bpy.data.objects.new('swiatlo_slonca', ld); bpy.context.scene.collection.objects.link(lo)
    # słabe, chłodne światło wypełniające od zachodu (odbite od nieba), żeby bryła świątyni nie była czarną plamą
    fd = bpy.data.lights.new('wypelnienie', 'SUN'); fd.color = (0.55, 0.68, 1.0); fd.energy = 0.10; fd.angle = math.radians(40.0)
    fd.use_shadow = False
    fo = bpy.data.objects.new('wypelnienie', fd); bpy.context.scene.collection.objects.link(fo)
    fo.rotation_euler = Vector((-0.75, -0.45, 0.5)).normalized().to_track_quat('Z', 'Y').to_euler()
    for f in range(1, NKL + 1):
        e = wysokosc_slonca(f)
        ob.location = pozycja_slonca(f)
        ob.keyframe_insert('location', frame=f)
        for sky in NIEBA:
            sky.sun_elevation = e
            sky.keyframe_insert('sun_elevation', frame=f)
        d = Vector((math.cos(e), 0, math.sin(e)))
        lo.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); lo.keyframe_insert('rotation_euler', frame=f)
        wid = max(0.0, min(1.0, (e - (HORYZONT - R_ANG * SPLASZCZ)) / (2 * R_ANG * SPLASZCZ)))
        ld.energy = 3.0 * wid ** 1.5; ld.keyframe_insert('energy', frame=f)
        pos.location = ob.location - Vector((150.0, 0.0, 0.0)); pos.keyframe_insert('location', frame=f)
        sila.outputs[0].default_value = 0.05 + 2.0 * wid ** 1.2; sila.outputs[0].keyframe_insert('default_value', frame=f)
        # błysk: krótkie wzmocnienie zieleni, gdy nad horyzontem jest tylko zielony skrawek
        if K_BLYSK - 4 <= f <= K_CZERWONY + 12:
            t = (f - (K_BLYSK - 4)) / (K_CZERWONY + 16 - K_BLYSK)
            g = 1.0 + 1.1 * math.sin(math.pi * min(1.0, t)) ** 2
        else:
            g = 1.0
        blysk.outputs[0].default_value = g
        blysk.outputs[0].keyframe_insert('default_value', frame=f)


# ---------------------------------------------------------------- kamery
def kierunek(az, poch):
    """Wektor patrzenia: az = stopnie na północ od wschodu, poch = stopnie w górę."""
    a, p = math.radians(az), math.radians(poch)
    return Vector((math.cos(a) * math.cos(p), math.sin(a) * math.cos(p), math.sin(p)))


def kamery(sc):
    # główna: dolot po łuku, potem powolny najazd bez obrotu (Słońce stoi w tym samym miejscu kadru)
    cd = bpy.data.cameras.new('kamera'); cd.clip_start = 0.5; cd.clip_end = 80000; cd.sensor_width = 36
    co = bpy.data.objects.new('kamera', cd); sc.collection.objects.link(co)
    d0 = (KAM_CEL0 - KAM_START).normalized()
    az0 = math.degrees(math.atan2(d0.y, d0.x)); poch0 = math.degrees(math.asin(d0.z))
    for f in range(1, NKL + 1):
        e = gladko5((f - 1) / (K_DOLOT - 1))
        # dryf: prędkość rośnie płynnie od zera (klatki 200–270), potem stała
        t = (f - 200) / 70.0
        g = 0.0 if t <= 0 else (70.0 * (t ** 3 - t ** 4 / 2) if t < 1 else 35.0 + (f - 270))
        luk = Vector((0.0, -1.0, 0.0)) * 14.0 * math.sin(math.pi * e)     # lekki łuk od południa
        co.location = KAM_START + (KAM_KONIEC - KAM_START) * e + luk + KAM_DRYF * g
        co.keyframe_insert('location', frame=f)
        er = gladko5((f - 1) / (K_DOLOT - 16))
        d = kierunek(az0 + (KAM_AZ1 - az0) * er, poch0 + (KAM_POCH1 - poch0) * er)
        co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); co.keyframe_insert('rotation_euler', frame=f)
        cd.lens = KAM_OB0 + (KAM_OB1 - KAM_OB0) * e; cd.keyframe_insert('lens', frame=f)
    # luneta: stoi na progu świątyni, patrzy na miejsce wschodu
    ld = bpy.data.cameras.new('luneta'); ld.clip_start = 0.5; ld.clip_end = 80000; ld.sensor_width = 36
    ld.lens = 18.0 / math.tan(math.radians(POLE_LUPY / 2))
    lo = bpy.data.objects.new('luneta', ld); sc.collection.objects.link(lo)
    lo.location = (2.0, 0.0, ZC)
    lo.rotation_euler = kierunek(0.0, math.degrees(HORYZONT) + 0.16).to_track_quat('-Z', 'Y').to_euler()
    return co, lo


def swiat(sc):
    w = bpy.data.worlds.new('niebo'); sc.world = w
    nt = w.node_tree; bg = nt.nodes.get('Background')
    sky = niebo_wezel(nt, (-300, 0)); NIEBA.append(sky)
    lacz(nt, sky.outputs[0], bg.inputs['Color']); bg.inputs['Strength'].default_value = JASNOSC_NIEBA


def ustawienia(sc):
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = NKL
    ee = sc.eevee
    ee.taa_render_samples = 48
    ee.use_shadows = True
    try:
        ee.shadow_pool_size = '1024'
    except Exception:
        pass
    try:
        ee.use_fast_gi = True
    except Exception:
        pass
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    tree = bpy.data.node_groups.new('kompozycja', 'CompositorNodeTree')
    sc.compositing_node_group = tree
    tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = tree.nodes.new('CompositorNodeRLayers')
    gl = tree.nodes.new('CompositorNodeGlare')
    gl.inputs['Type'].default_value = 'Bloom'
    gl.inputs['Threshold'].default_value = 0.8
    gl.inputs['Strength'].default_value = 0.9
    gl.inputs['Size'].default_value = 0.85
    out = tree.nodes.new('NodeGroupOutput')
    tree.links.new(rl.outputs['Image'], gl.inputs['Image']); tree.links.new(gl.outputs['Image'], out.inputs[0])


def interp(pkt, f):
    for (f0, v0), (f1, v1) in zip(pkt, pkt[1:]):
        if f0 <= f <= f1:
            return v0 + (v1 - v0) * gladko((f - f0) / (f1 - f0))
    return pkt[0][1] if f < pkt[0][0] else pkt[-1][1]


EV_GLOWNY = [(1, 2.9), (K_DOLOT, 2.5), (K_BLYSK, 2.3), (NKL, 2.0)]     # ekspozycja jak w aparacie: ciemniej, gdy wschodzi Słońce
EV_LUPA = [(K_LUPA, -0.7), (K_BLYSK, -1.0), (NKL, -1.4)]


def przebieg(sc, ktory, f, KAM):
    """Ustawia scenę do renderu klatki f w przebiegu 'glowny' albo 'lupa'."""
    glowny = ktory == 'glowny'
    sc.camera = KAM[0] if glowny else KAM[1]
    sc.render.resolution_x, sc.render.resolution_y = (1920, 1080) if glowny else (2 * RL, 2 * RL)
    for ob in MGLY:
        ob.hide_render = not glowny
    vs = sc.view_settings
    if glowny:
        vs.view_transform = 'AgX'
        try:
            vs.look = 'AgX - Medium High Contrast'
        except Exception:
            pass
    else:
        vs.look = 'None'
        vs.view_transform = 'Standard'
    sc.frame_set(f)
    vs.exposure = interp(EV_GLOWNY if glowny else EV_LUPA, f)


# ---------------------------------------------------------------- nakładki (pierścienie, linia, podpis)
def punkt_wschodu_px(sc, KAM):
    """Piksel kadru, w którym wschodzi Słońce (po zakończeniu dolotu kamera już się nie obraca)."""
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.camera = KAM[0]
    sc.frame_set(K_BLYSK); bpy.context.view_layer.update()
    p = Vector((D_SL, 0.0, ZC + D_SL * math.tan(HORYZONT + math.radians(0.10))))
    c = world_to_camera_view(sc, KAM[0], p)
    return c.x * 1920.0, (1.0 - c.y) * 1080.0


def nakladki(sx, sy):
    """Renderuje dwie przezroczyste nakładki 1920×1080: nakl_a.png (pierścienie i linia), nakl_b.png (podpis)."""
    scn = bpy.data.scenes.new('nakladka')
    scn.render.engine = 'BLENDER_EEVEE'
    scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = True
    scn.render.image_settings.file_format = 'PNG'; scn.render.image_settings.color_mode = 'RGBA'
    scn.view_settings.view_transform = 'Standard'; scn.view_settings.look = 'None'
    scn.eevee.taa_render_samples = 32
    cd = bpy.data.cameras.new('kam_nakl'); cd.type = 'ORTHO'; cd.ortho_scale = 1920.0; cd.clip_end = 100
    co = bpy.data.objects.new('kam_nakl', cd); co.location = (0, 0, 50); scn.collection.objects.link(co); scn.camera = co
    A = bpy.data.collections.new('nakl_a'); B = bpy.data.collections.new('nakl_b')
    scn.collection.children.link(A); scn.collection.children.link(B)

    def P(x, y, z=0.0):
        return Vector((x - 960.0, 540.0 - y, z))

    def mat(nazwa, kolor):
        m = bpy.data.materials.new(nazwa); nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = srgb(kolor); nt.links.new(em.outputs[0], out.inputs['Surface'])
        return m

    m_zl, m_ciemny, m_ziel, m_jasny = mat('zloty', ZLOTY), mat('ciemny', (6, 9, 18)), mat('zielony', ZIELONY), mat('jasny', (236, 238, 244))

    def pierscien(nazwa, cx, cy, r0, r1, m, z=0.0, n=160):
        v, f = [], []
        for i in range(n):
            a = 2 * math.pi * i / n
            v += [tuple(P(cx + r0 * math.cos(a), cy + r0 * math.sin(a), z)), tuple(P(cx + r1 * math.cos(a), cy + r1 * math.sin(a), z))]
        for i in range(n):
            j = (i + 1) % n
            f.append((2 * i, 2 * i + 1, 2 * j + 1, 2 * j))
        me = bpy.data.meshes.new(nazwa); me.from_pydata(v, [], f); me.materials.append(m)
        A.objects.link(bpy.data.objects.new(nazwa, me))

    def linia(nazwa, x0, y0, x1, y1, gr, m, z=0.0):
        d = Vector((x1 - x0, y1 - y0)); n = Vector((-d.y, d.x)).normalized() * gr / 2
        v = [tuple(P(x0 + n.x, y0 + n.y, z)), tuple(P(x1 + n.x, y1 + n.y, z)), tuple(P(x1 - n.x, y1 - n.y, z)), tuple(P(x0 - n.x, y0 - n.y, z))]
        me = bpy.data.meshes.new(nazwa); me.from_pydata(v, [], [(0, 1, 2, 3)]); me.materials.append(m)
        A.objects.link(bpy.data.objects.new(nazwa, me))

    def napis(tekst, x, y, rozm, plik, m, wyr='RIGHT'):
        cu = bpy.data.curves.new('napis', 'FONT'); cu.body = tekst
        cu.font = bpy.data.fonts.load(os.path.join(r'C:\Windows\Fonts', plik), check_existing=True)
        cu.size = rozm; cu.align_x = wyr; cu.align_y = 'CENTER'
        cu.materials.append(m)
        ob = bpy.data.objects.new('napis', cu); ob.location = P(x, y, 1.0); B.objects.link(ob)
        cu2 = cu.copy(); cu2.offset = rozm * 0.045; cu2.materials.clear(); cu2.materials.append(m_ciemny)   # ciemny obrys
        ob2 = bpy.data.objects.new('napis_obrys', cu2); ob2.location = P(x + rozm * 0.03, y + rozm * 0.03, 0.5); B.objects.link(ob2)

    # duży pierścień okienka, mały pierścień wokół miejsca wschodu i linia między nimi
    RM = 42.0
    pierscien('pierscien_cien', LX, LY, RL - 1, RL + 7, m_ciemny, 0.0)
    pierscien('pierscien', LX, LY, RL - 1, RL + 4, m_zl, 0.5)
    pierscien('maly_cien', sx, sy, RM - 1.5, RM + 4.5, m_ciemny, 0.0)
    pierscien('maly', sx, sy, RM, RM + 3, m_zl, 0.5, n=96)
    k = Vector((LX - sx, LY - sy)).normalized()
    a0 = (sx + k.x * (RM + 3), sy + k.y * (RM + 3)); a1 = (LX - k.x * (RL + 4), LY - k.y * (RL + 4))
    linia('linia_cien', *a0, *a1, 6.0, m_ciemny, 0.0)
    linia('linia', *a0, *a1, 3.0, m_zl, 0.5)
    # podpis po lewej stronie okienka
    xt = LX - RL - 44
    napis('zielony promień', xt, LY - 26, 66, 'georgiab.ttf', m_ziel)
    napis('trwa około sekundy', xt, LY + 34, 36, 'arial.ttf', m_jasny)

    for plik, pokaz, ukryj in (('nakl_a.png', A, B), ('nakl_b.png', B, A)):
        pokaz.hide_render = False; ukryj.hide_render = True
        scn.render.filepath = os.path.join(KLATKI, plik)
        bpy.ops.render.render(write_still=True, scene=scn.name)
    # maska okienka (koło z miękkim brzegiem)
    n = 2 * RL
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - RL, yy + 0.5 - RL)
    a = np.clip((RL - 0.5) - r, 0.0, 1.0).astype(np.float32)
    px = np.empty((n, n, 4), np.float32); px[..., 0] = px[..., 1] = px[..., 2] = a; px[..., 3] = 1.0
    im = bpy.data.images.new('maska', n, n, alpha=False); im.colorspace_settings.name = 'Non-Color'
    im.pixels.foreach_set(px.ravel()); im.filepath_raw = os.path.join(KLATKI, 'maska.png'); im.file_format = 'PNG'; im.save()


# ---------------------------------------------------------------- składanie
T_LUPA = (K_LUPA - 1) / FPS
T_PODPIS = (K_BLYSK - 3) / FPS
D_LUPA, D_PODPIS = 0.8, 0.5


def zloz_klatke(f, glowny, lupa, wynik):
    """Składa jedną klatkę (kadry próbne)."""
    t = (f - 1) / FPS
    al = max(0.0, min(1.0, (t - T_LUPA) / D_LUPA)); ap = max(0.0, min(1.0, (t - T_PODPIS) / D_PODPIS))
    if al <= 0 or not os.path.exists(lupa):
        shutil.copyfile(glowny, wynik); return
    fc = (f"[2]format=gray[m];[1][m]alphamerge,colorchannelmixer=aa={al:.3f}[l];[0][l]overlay={LX - RL}:{LY - RL}[a];"
          f"[3]colorchannelmixer=aa={al:.3f}[na];[a][na]overlay=0:0[b];[4]colorchannelmixer=aa={ap:.3f}[nb];[b][nb]overlay=0:0")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', glowny, '-i', lupa, '-i', os.path.join(KLATKI, 'maska.png'),
                    '-i', os.path.join(KLATKI, 'nakl_a.png'), '-i', os.path.join(KLATKI, 'nakl_b.png'),
                    '-filter_complex', fc, '-frames:v', '1', wynik], check=True)


def zloz_film():
    # przed pojawieniem się okienka klatki lunety nie są renderowane: wypełnij kopiami pierwszej (i tak są przezroczyste)
    pierwsza = os.path.join(KLATKI, f'lupa_{K_LUPA:04d}.png')
    for f in range(1, K_LUPA):
        p = os.path.join(KLATKI, f'lupa_{f:04d}.png')
        if not os.path.exists(p):
            shutil.copyfile(pierwsza, p)
    mp4 = os.path.join(DIR, 'klip.mp4')
    fc = (f"[2]format=gray[m];[1][m]alphamerge,fade=t=in:st={T_LUPA:.3f}:d={D_LUPA}:alpha=1[l];[0][l]overlay={LX - RL}:{LY - RL}[a];"
          f"[3]format=rgba,fade=t=in:st={T_LUPA:.3f}:d={D_LUPA}:alpha=1[na];[a][na]overlay=0:0[b];"
          f"[4]format=rgba,fade=t=in:st={T_PODPIS:.3f}:d={D_PODPIS}:alpha=1[nb];[b][nb]overlay=0:0,format=yuv420p[v]")
    still = ['-loop', '1', '-framerate', str(FPS)]
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(KLATKI, 'k_%04d.png'),
                    '-framerate', str(FPS), '-i', os.path.join(KLATKI, 'lupa_%04d.png'),
                    *still, '-i', os.path.join(KLATKI, 'maska.png'), *still, '-i', os.path.join(KLATKI, 'nakl_a.png'),
                    *still, '-i', os.path.join(KLATKI, 'nakl_b.png'),
                    '-filter_complex', fc, '-map', '[v]', '-frames:v', str(NKL), '-an',
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp4, '-vf', f'select=eq(n\\,{KADR - 1}),scale=1600:-2',
                    '-frames:v', '1', '-q:v', '2', os.path.join(DIR, 'kadr.jpg')], check=True)
    print('GOTOWE', mp4)


def renderuj(sc, KAM):
    os.makedirs(KLATKI, exist_ok=True)
    if TRYB == 'test':
        return
    if TRYB == 'zloz':
        zloz_film(); return
    sx, sy = punkt_wschodu_px(sc, KAM)
    print(f'PUNKT WSCHODU {sx:.1f} {sy:.1f}')
    nakladki(sx, sy)

    def klatka(ktory, f, plik):
        przebieg(sc, ktory, f, KAM)
        sc.render.filepath = plik
        bpy.ops.render.render(write_still=True, scene=sc.name)

    if TRYB == 'probne':
        for f in [int(k) for k in (ARGS[1] if len(ARGS) > 1 else '1,140,270,332,345,500').split(',')]:
            t = time.time()
            g = os.path.join(KLATKI, f'probna_g_{f:04d}.png'); l = os.path.join(KLATKI, f'probna_l_{f:04d}.png')
            klatka('glowny', f, g)
            if f >= K_LUPA:
                klatka('lupa', f, l)
            zloz_klatke(f, g, l, os.path.join(KLATKI, f'probna_{f:04d}.png'))
            print(f'PROBNA {f} {time.time() - t:.1f}s')
        return
    if os.path.exists(BLOKADA) and open(BLOKADA, encoding="utf-8").read().strip() != NAZWA:   # blokadę z własną nazwą mogła założyć kolejka
        print('BLOKADA: inna sesja renderuje:', open(BLOKADA, encoding='utf-8').read()); return
    with open(BLOKADA, 'w', encoding='utf-8') as fh:
        fh.write(NAZWA)
    try:
        t = time.time()
        for p in os.listdir(KLATKI):
            if (p.startswith('k_') or p.startswith('lupa_')) and p.endswith('.png'):
                os.remove(os.path.join(KLATKI, p))
        for f in range(K_LUPA, NKL + 1):
            klatka('lupa', f, os.path.join(KLATKI, f'lupa_{f:04d}.png'))
        print(f'RENDER LUNETY {time.time() - t:.0f}s')
        for f in range(1, NKL + 1):
            klatka('glowny', f, os.path.join(KLATKI, f'k_{f:04d}.png'))
        dt = time.time() - t
        print(f'RENDER {dt:.0f}s')
        with open(os.path.join(KLATKI, 'czas_renderu.txt'), 'w', encoding='utf-8') as fh:
            fh.write(f'render {dt:.0f} s, klatek {NKL} + luneta {NKL - K_LUPA + 1}\n')
    finally:
        os.remove(BLOKADA)
    zloz_film()


def main():
    wyczysc()
    sc = bpy.context.scene
    kol = bpy.data.collections.new('Wschod'); sc.collection.children.link(kol)
    M = {'kamien': material_kamien(), 'las_blisko': material_las(True), 'las_daleko': material_las(False)}
    wzory = piramida_i_swiatynia(kol, M)
    dalsze_piramidy(kol, wzory)
    las(kol, M)
    mgly(kol)
    swiat(sc)
    slonce(kol)
    KAM = kamery(sc)
    ustawienia(sc)
    renderuj(sc, KAM)


main()
