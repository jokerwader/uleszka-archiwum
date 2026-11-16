# -*- coding: utf-8 -*-
"""
Wschód Słońca ze szczytu schodkowej piramidy i zielony promień (rozdział 11).

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/wschod-slonca-z-piramidy/scena.py -- probne 1,200,320,500
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/wschod-slonca-z-piramidy/scena.py -- pelny

Kamera stoi we wnętrzu świątyni na szczycie piramidy (wys. ok. 40 m) i patrzy na wschód przez wejście.
Najpierw powoli podchodzi do progu, potem płynnie przybliża obraz (28 → 300 mm) na miejsce wschodu.
Słońce ma prawdziwą średnicę kątową (0,53°), jest spłaszczone przez refrakcję (ok. 0,86).
Zielony promień: obraz zielony leży nieco wyżej niż czerwony (rozszczepienie światła w atmosferze),
a niebieski jest rozproszony, więc jako pierwszy wychyla się nad horyzont zielony skrawek.
Przesunięcie zielonego obrazu jest powiększone (jak przy mirażu, który na zdjęciach z teleobiektywem
czyni błysk widocznym). Czas jest przyspieszony ok. 15×, sam błysk trwa ok. 1,2 s.

Układ: x = wschód, y = północ, z = góra, metry.
"""
import bpy, bmesh, math, os, sys, subprocess, time, random
import numpy as np
from mathutils import Vector, Matrix, Euler

DIR = os.path.dirname(os.path.abspath(__file__))
NAZWA = os.path.basename(DIR)
KLATKI = os.path.join(DIR, '_klatki')
BLOKADA = os.path.join(os.path.dirname(DIR), '.renderuje')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
TRYB = ARGS[0] if ARGS else 'pelny'
FPS = 25
NKL = 500          # 20 s
KADR = 470
RNG = np.random.default_rng(3)
random.seed(3)

# oś czasu (klatki)
K_DOJSCIE = (1, 125)      # podejście do progu
K_ZOOM = (125, 280)       # przybliżenie
K_BLYSK = 318             # zielony skrawek wychyla się nad horyzont
K_CZERWONY = 353          # wychyla się czerwono-pomarańczowa tarcza

# geometria
H_PLAT = 40.0             # wysokość podłogi świątyni na szczycie
OKO = 1.6
ZC = H_PLAT + OKO         # wysokość kamery
D_SL = 45000.0            # odległość „ekranu” Słońca
R_ANG = math.radians(0.2665)   # promień kątowy Słońca
SPLASZCZ = 0.86
DELTA = 0.10              # przesunięcie obrazu zielonego (w promieniach Słońca)
R_GRUNT = 30000.0         # zasięg płaskiej równiny lasu
Z_LAS = 22.0              # wysokość dachu lasu
HORYZONT = -math.atan((ZC - Z_LAS) / R_GRUNT)   # kąt horyzontu (ujemny)

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

def material_kamien():
    mt = bpy.data.materials.new('kamien'); nt = mt.node_tree; nt.nodes.clear()
    out = wezel(nt, 'ShaderNodeOutputMaterial', (600, 0))
    bs = wezel(nt, 'ShaderNodeBsdfPrincipled', (300, 0), Roughness=0.92)
    tc = wezel(nt, 'ShaderNodeTexCoord', (-900, 0))
    no = wezel(nt, 'ShaderNodeTexNoise', (-650, 100), Scale=0.35, Detail=8.0, Roughness=0.62)
    lacz(nt, tc.outputs['Object'], no.inputs['Vector'])
    vo = wezel(nt, 'ShaderNodeTexVoronoi', (-650, -150), Scale=1.6)
    lacz(nt, tc.outputs['Object'], vo.inputs['Vector'])
    cr = wezel(nt, 'ShaderNodeValToRGB', (-380, 100))
    cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[0].color = (0.07, 0.07, 0.065, 1)
    cr.color_ramp.elements[1].position = 0.72; cr.color_ramp.elements[1].color = (0.36, 0.35, 0.31, 1)
    lacz(nt, no.outputs['Fac'], cr.inputs['Fac'])
    lacz(nt, cr.outputs['Color'], bs.inputs['Base Color'])
    # spoiny między kamieniami (Voronoi) + chropowatość
    no2 = wezel(nt, 'ShaderNodeTexNoise', (-650, -350), Scale=6.0, Detail=6.0)
    lacz(nt, tc.outputs['Object'], no2.inputs['Vector'])
    w = W(nt)
    h = w.m('MULTIPLY_ADD', no2.outputs['Fac'], 0.3, w.clamp01(w.m('MULTIPLY', vo.outputs['Distance'], 3.0)))
    bump = wezel(nt, 'ShaderNodeBump', (60, -200), Strength=0.5, Distance=0.05)
    lacz(nt, h, bump.inputs['Height'])
    lacz(nt, bump.outputs['Normal'], bs.inputs['Normal'])
    lacz(nt, bs.outputs[0], out.inputs['Surface'])
    return mt

def material_las():
    """Dach lasu: komórki koron + mgiełka w stronę koloru nieba (im dalej, tym jaśniej)."""
    mt = bpy.data.materials.new('las'); nt = mt.node_tree; nt.nodes.clear()
    w = W(nt)
    out = wezel(nt, 'ShaderNodeOutputMaterial', (900, 0))
    bs = wezel(nt, 'ShaderNodeBsdfPrincipled', (400, 0), Roughness=0.85)
    bs.inputs['Specular IOR Level'].default_value = 0.2
    tc = wezel(nt, 'ShaderNodeTexCoord', (-900, 0))
    vo = wezel(nt, 'ShaderNodeTexVoronoi', (-650, -200), Scale=0.075, Randomness=0.9)
    lacz(nt, tc.outputs['Object'], vo.inputs['Vector'])
    no = wezel(nt, 'ShaderNodeTexNoise', (-650, 100), Scale=0.004, Detail=8.0)
    lacz(nt, tc.outputs['Object'], no.inputs['Vector'])
    cr = wezel(nt, 'ShaderNodeValToRGB', (-400, 100))
    cr.color_ramp.elements[0].color = (0.012, 0.03, 0.012, 1); cr.color_ramp.elements[1].color = (0.045, 0.075, 0.03, 1)
    lacz(nt, no.outputs['Fac'], cr.inputs['Fac'])
    kop = w.clamp01(w.m('SUBTRACT', 1.0, w.m('MULTIPLY', vo.outputs['Distance'], 1.35)))
    mx = wezel(nt, 'ShaderNodeMix', (0, 100), data_type='RGBA', blend_type='MULTIPLY'); mx.inputs['Factor'].default_value = 1.0
    lacz(nt, cr.outputs['Color'], mx.inputs[6])
    sz = w.m('MULTIPLY_ADD', kop, 0.9, 0.3)
    cmb = wezel(nt, 'ShaderNodeCombineXYZ', (-100, 0))
    for k in 'XYZ':
        lacz(nt, sz, cmb.inputs[k])
    lacz(nt, cmb.outputs[0], mx.inputs[7])
    lacz(nt, mx.outputs[2], bs.inputs['Base Color'])
    bump = wezel(nt, 'ShaderNodeBump', (200, -300), Strength=1.0, Distance=4.0)
    lacz(nt, kop, bump.inputs['Height']); lacz(nt, bump.outputs['Normal'], bs.inputs['Normal'])
    # mgiełka
    geo = wezel(nt, 'ShaderNodeNewGeometry', (-400, 500))
    sxyz = wezel(nt, 'ShaderNodeSeparateXYZ', (-200, 500)); lacz(nt, geo.outputs['Incoming'], sxyz.inputs[0])
    cxyz = wezel(nt, 'ShaderNodeCombineXYZ', (0, 500))
    lacz(nt, w.m('MULTIPLY', sxyz.outputs['X'], -1.0), cxyz.inputs['X'])
    lacz(nt, w.m('MULTIPLY', sxyz.outputs['Y'], -1.0), cxyz.inputs['Y'])
    cxyz.inputs['Z'].default_value = 0.02
    sky = niebo_wezel(nt, (200, 500)); NIEBA.append(sky)
    lacz(nt, cxyz.outputs[0], sky.inputs[0])
    em = wezel(nt, 'ShaderNodeEmission', (450, 500), Strength=0.038)
    lacz(nt, sky.outputs[0], em.inputs['Color'])
    camd = wezel(nt, 'ShaderNodeCameraData', (-400, 800))
    d = w.m('MAXIMUM', w.m('SUBTRACT', camd.outputs['View Distance'], 300.0), 0.0)
    fog = w.m('MULTIPLY', w.m('SUBTRACT', 1.0, w.m('EXPONENT', w.m('DIVIDE', d, -5500.0))), 0.8)
    ms = wezel(nt, 'ShaderNodeMixShader', (700, 200))
    lacz(nt, fog, ms.inputs[0]); lacz(nt, bs.outputs[0], ms.inputs[1]); lacz(nt, em.outputs[0], ms.inputs[2])
    lacz(nt, ms.outputs[0], out.inputs['Surface'])
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
    """Schodkowa piramida w stylu Majów: front (schody) na wschód, świątynia na szczycie."""
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
    S.obiekt('piramida', [M['kamien']], kol)

    # świątynia: grube mury, wejście 2,2 × 2,9 m od wschodu, sklepienie wspornikowe
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
    # sklepienie wspornikowe (stopnie do środka) i dach
    for i in range(6):
        t = i / 6
        T.box(x0 + gr + 1.5 * t, x_front - gr - 1.5 * t, y0, y1, zs + i * 0.4, zs + (i + 1) * 0.4)
    T.box(x0 - 0.2, x_front + 0.2, y0 - 0.2, y1 + 0.2, zt - 0.6, zt)
    T.box(x0 + 0.5, x0 + 2.8, y0 + 0.8, y1 - 0.8, zt, zt + 7.0, 0.3)   # grzebień dachowy z tyłu
    T.box(x0 - 0.5, x_front + 0.5, y0 - 0.5, y1 + 0.5, z0 - 0.02, z0 + 0.25)   # próg / podłoga
    T.obiekt('swiatynia', [M['kamien']], kol)

def las(kol, M):
    """Bliski dach lasu (pofałdowany) i daleka płaska równina po horyzont."""
    krok = 8.0
    xs = np.arange(-2500, 4000 + krok, krok); ys = np.arange(-3000, 3000 + krok, krok)
    nx, ny = len(xs), len(ys)
    X, Y = np.meshgrid(xs, ys)
    Z = Z_LAS + 2.5 * np.sin(X / 33.0 + np.cos(Y / 21.0)) * np.cos(Y / 37.0) + 1.2 * np.sin(X / 11.0 + 2.0 * np.sin(Y / 13.0)) * np.cos(Y / 9.0 + np.sin(X / 7.0))
    V = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()]).astype(np.float32)
    ii, jj = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1))
    a = (jj * nx + ii).ravel()
    F = np.column_stack([a, a + 1, a + nx + 1, a + nx])
    cx = (X[:-1, :-1] + krok / 2).ravel(); cy = (Y[:-1, :-1] + krok / 2).ravel()
    F = F[(np.abs(cx) > 32) | (np.abs(cy) > 32)]
    me = bpy.data.meshes.new('las_blisko')
    me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(F.size); me.loops.foreach_set('vertex_index', F.ravel().astype(np.int32))
    me.polygons.add(len(F)); me.polygons.foreach_set('loop_start', (np.arange(len(F)) * 4).astype(np.int32))
    me.update(); me.validate(); me.materials.append(M['las']); me.shade_smooth()
    ob = bpy.data.objects.new('las_blisko', me); kol.objects.link(ob)
    # równina: pierścień do 30 km
    R = R_GRUNT; r = 2400.0
    v = [(-R, -R, 0), (R, -R, 0), (R, R, 0), (-R, R, 0), (-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0)]
    f = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me2 = bpy.data.meshes.new('las_daleko'); me2.from_pydata(v, [], f); me2.update(); me2.materials.append(M['las'])
    ob2 = bpy.data.objects.new('las_daleko', me2); ob2.location = (800, 0, Z_LAS - 1.5); kol.objects.link(ob2)
    # grunt pod piramidą (plac)
    me3 = bpy.data.meshes.new('plac'); me3.from_pydata([(-40, -40, 0.01), (40, -40, 0.01), (40, 40, 0.01), (-40, 40, 0.01)], [], [(0, 1, 2, 3)])
    me3.materials.append(M['kamien'])
    kol.objects.link(bpy.data.objects.new('plac', me3))

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
    # światło słoneczne (pojawia się, gdy wyjdzie tarcza)
    ld = bpy.data.lights.new('swiatlo_slonca', 'SUN'); ld.angle = math.radians(0.53); ld.color = (1.0, 0.42, 0.18)
    lo = bpy.data.objects.new('swiatlo_slonca', ld); bpy.context.scene.collection.objects.link(lo)
    for f in range(1, NKL + 1):
        e = wysokosc_slonca(f)
        ob.location = (D_SL, 0.0, ZC + D_SL * math.tan(e))
        ob.keyframe_insert('location', frame=f)
        for sky in NIEBA:
            sky.sun_elevation = e
            sky.keyframe_insert('sun_elevation', frame=f)
        d = Vector((math.cos(e), 0, math.sin(e)))
        lo.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); lo.keyframe_insert('rotation_euler', frame=f)
        wid = max(0.0, min(1.0, (e - (HORYZONT - R_ANG * SPLASZCZ)) / (2 * R_ANG * SPLASZCZ)))
        ld.energy = 3.0 * wid ** 1.5; ld.keyframe_insert('energy', frame=f)
        # błysk: krótkie wzmocnienie zieleni, gdy nad horyzontem jest tylko zielony skrawek
        if K_BLYSK - 4 <= f <= K_CZERWONY + 12:
            t = (f - (K_BLYSK - 4)) / (K_CZERWONY + 16 - K_BLYSK)
            g = 1.0 + 1.1 * math.sin(math.pi * min(1.0, t)) ** 2
        else:
            g = 1.0
        blysk.outputs[0].default_value = g
        blysk.outputs[0].keyframe_insert('default_value', frame=f)

def kamera(sc):
    cd = bpy.data.cameras.new('kamera'); cd.clip_start = 0.1; cd.clip_end = 80000; cd.sensor_width = 36
    co = bpy.data.objects.new('kamera', cd); sc.collection.objects.link(co); sc.camera = co
    def gladko(t):
        t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
    for f in range(1, NKL + 1):
        t1 = gladko((f - K_DOJSCIE[0]) / (K_DOJSCIE[1] - K_DOJSCIE[0]))
        x = -3.0 + 3.6 * t1                       # od środka komory do progu
        t2 = gladko((f - K_ZOOM[0]) / (K_ZOOM[1] - K_ZOOM[0]))
        lens = math.exp(math.log(24.0) + (math.log(300.0) - math.log(24.0)) * t2)
        pitch_szer = math.radians(-2.5)
        pitch_tele = HORYZONT + math.radians(0.62)
        pitch = pitch_szer + (pitch_tele - pitch_szer) * t2
        co.location = (x, 0.0, ZC); co.keyframe_insert('location', frame=f)
        co.rotation_euler = (math.radians(90) + pitch, 0, math.radians(-90)); co.keyframe_insert('rotation_euler', frame=f)
        cd.lens = lens; cd.keyframe_insert('lens', frame=f)
    return co

def swiat(sc):
    w = bpy.data.worlds.new('niebo'); sc.world = w
    nt = w.node_tree; bg = nt.nodes.get('Background')
    sky = niebo_wezel(nt, (-300, 0)); NIEBA.append(sky)
    lacz(nt, sky.outputs[0], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.065

def ustawienia(sc):
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 1920; sc.render.resolution_y = 1080; sc.render.resolution_percentage = 100
    sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = NKL
    ee = sc.eevee
    ee.taa_render_samples = 64
    ee.use_shadows = True
    try:
        ee.use_fast_gi = True
    except Exception:
        pass
    sc.view_settings.view_transform = 'Standard'
    for look in ('None',):
        try:
            sc.view_settings.look = look; break
        except Exception:
            pass
    for f, ev in ((1, 1.2), (K_ZOOM[0], 1.2), (K_ZOOM[1], -1.0), (K_BLYSK, -1.0), (NKL, -1.4)):
        sc.view_settings.exposure = ev; sc.view_settings.keyframe_insert("exposure", frame=f)
    sc.render.image_settings.file_format = 'PNG'
    tree = bpy.data.node_groups.new('kompozycja', 'CompositorNodeTree')
    sc.compositing_node_group = tree
    tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = tree.nodes.new('CompositorNodeRLayers')
    gl = tree.nodes.new('CompositorNodeGlare')
    gl.inputs['Type'].default_value = 'Bloom'
    gl.inputs['Threshold'].default_value = 0.8
    gl.inputs['Strength'].default_value = 0.35
    gl.inputs['Size'].default_value = 0.7
    out = tree.nodes.new('NodeGroupOutput')
    tree.links.new(rl.outputs['Image'], gl.inputs['Image']); tree.links.new(gl.outputs['Image'], out.inputs[0])

def renderuj(sc):
    os.makedirs(KLATKI, exist_ok=True)
    if TRYB == 'test':
        return
    if TRYB == 'probne':
        for f in [int(k) for k in (ARGS[1] if len(ARGS) > 1 else '1,200,330,500').split(',')]:
            sc.frame_set(f)
            sc.render.filepath = os.path.join(KLATKI, f'probna_{f:04d}.png')
            t = time.time(); bpy.ops.render.render(write_still=True); print(f'PROBNA {f} {time.time() - t:.1f}s')
        return
    if os.path.exists(BLOKADA) and open(BLOKADA, encoding="utf-8").read().strip() != NAZWA:   # blokadę z własną nazwą mogła założyć kolejka
        print('BLOKADA: inna sesja renderuje:', open(BLOKADA, encoding='utf-8').read()); return
    with open(BLOKADA, 'w', encoding='utf-8') as fh:
        fh.write(NAZWA)
    try:
        t = time.time()
        sc.render.filepath = os.path.join(KLATKI, 'k_')
        bpy.ops.render.render(animation=True)
        print(f'RENDER {time.time() - t:.0f}s')
    finally:
        os.remove(BLOKADA)
    mp4 = os.path.join(DIR, 'klip.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(KLATKI, 'k_%04d.png'),
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(KLATKI, f'k_{KADR:04d}.png'),
                    '-vf', 'scale=1600:-2', '-q:v', '3', os.path.join(DIR, 'kadr.jpg')], check=True)
    print('GOTOWE', mp4)

def main():
    wyczysc()
    sc = bpy.context.scene
    kol = bpy.data.collections.new('Wschod'); sc.collection.children.link(kol)
    M = {'kamien': material_kamien(), 'las': material_las()}
    piramida_i_swiatynia(kol, M)
    las(kol, M)
    swiat(sc)
    slonce(kol)
    kamera(sc)
    ustawienia(sc)
    renderuj(sc)

main()
