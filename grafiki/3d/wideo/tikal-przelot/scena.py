# -*- coding: utf-8 -*-
"""
Tikal o świcie: przelot kamery nad Placem Głównym (rekonstrukcja).

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/tikal-przelot/scena.py -- probne 1,200,400
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/tikal-przelot/scena.py -- pelny

Układ współrzędnych: x = wschód, y = północ, z = góra, metry. (0,0) = środek Placu Głównego.
Położenia budowli: plan „Tikal map.JPG” (Simon Burchell, Wikimedia Commons, CC BY-SA 3.0),
przeskalowany według współrzędnych świątyń z Wikipedii (1 px planu = ok. 1,09 m). Szczegóły w README.md.
"""
import bpy, bmesh, math, os, sys, subprocess, time, random
import numpy as np
from mathutils import Vector, Matrix
from mathutils import noise as mnoise

DIR = os.path.dirname(os.path.abspath(__file__))
NAZWA = os.path.basename(DIR)
KLATKI = os.path.join(DIR, '_klatki')
BLOKADA = os.path.join(os.path.dirname(DIR), '.renderuje')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
TRYB = ARGS[0] if ARGS else 'pelny'
FPS = 25
NKL = 400          # 16 s
random.seed(7)
RNG = np.random.default_rng(7)

# ---------------------------------------------------------------- narzędzia
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

class Siatka:
    """Prosty zbieracz geometrii: wierzchołki, ściany, indeks materiału."""
    def __init__(s):
        s.v, s.f, s.m = [], [], []

    def box(s, x0, x1, y0, y1, z0, z1, ins=0.0, m=0):
        b = len(s.v)
        s.v += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                (x0 + ins, y0 + ins, z1), (x1 - ins, y0 + ins, z1), (x1 - ins, y1 - ins, z1), (x0 + ins, y1 - ins, z1)]
        s.f += [(b, b + 3, b + 2, b + 1), (b + 4, b + 5, b + 6, b + 7), (b, b + 1, b + 5, b + 4),
                (b + 1, b + 2, b + 6, b + 5), (b + 2, b + 3, b + 7, b + 6), (b + 3, b, b + 4, b + 7)]
        s.m += [m] * 6

    def pryzma_yz(s, prof, x0, x1, m=0):
        pole = sum(prof[i][0] * prof[(i + 1) % len(prof)][1] - prof[(i + 1) % len(prof)][0] * prof[i][1]
                   for i in range(len(prof)))
        if pole < 0:            # profil ma być przeciwny do ruchu wskazówek zegara (normalne na zewnątrz)
            prof = prof[::-1]
        n = len(prof); b = len(s.v)
        s.v += [(x0, y, z) for y, z in prof] + [(x1, y, z) for y, z in prof]
        s.f.append(tuple(b + i for i in reversed(range(n))))
        s.f.append(tuple(b + n + i for i in range(n)))
        s.m += [m, m]
        for i in range(n):
            j = (i + 1) % n
            s.f.append((b + i, b + j, b + n + j, b + n + i)); s.m.append(m)

    def walec(s, cx, cy, r, z0, z1, n=12, m=0):
        b = len(s.v)
        for z in (z0, z1):
            for i in range(n):
                a = 2 * math.pi * i / n
                s.v.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
        s.f.append(tuple(b + i for i in reversed(range(n)))); s.f.append(tuple(b + n + i for i in range(n)))
        s.m += [m, m]
        for i in range(n):
            j = (i + 1) % n
            s.f.append((b + i, b + j, b + n + j, b + n + i)); s.m.append(m)

    def przeksztalc_od(s, start, mat):
        for i in range(start, len(s.v)):
            s.v[i] = tuple(mat @ Vector(s.v[i]))

    def obiekt(s, nazwa, materialy, kol):
        me = bpy.data.meshes.new(nazwa)
        me.from_pydata(s.v, [], s.f)
        me.validate()
        for mt in materialy:
            me.materials.append(mt)
        if len(materialy) > 1:
            me.polygons.foreach_set('material_index', s.m)
        ob = bpy.data.objects.new(nazwa, me)
        kol.objects.link(ob)
        return ob

def obr_z(stopnie, x=0.0, y=0.0):
    return Matrix.Translation((x, y, 0)) @ Matrix.Rotation(math.radians(stopnie), 4, 'Z')

KIERUNEK = {'S': 0, 'W': -90, 'N': 180, 'E': 90}   # obrót tak, by front (lokalne -Y) patrzył w daną stronę

# ---------------------------------------------------------------- budowle
def schody(S, sw, y_front, y_top, H, krok=0.38, por=True):
    n = max(4, int(round(H / krok)))
    r = H / n; run = (y_top - y_front) / n
    y_back = y_top + 0.6
    pts = [(y_back, 0.0), (y_front, 0.0)]
    for i in range(1, n + 1):
        pts.append((y_front + (i - 1) * run, i * r))
        pts.append((y_front + i * run, i * r))
    pts.append((y_back, H))
    S.pryzma_yz(pts, -sw / 2, sw / 2)
    if por:  # boczne rampy (alfardy)
        for sx in (-1, 1):
            x0, x1 = (sw / 2, sw / 2 + 1.3) if sx > 0 else (-sw / 2 - 1.3, -sw / 2)
            S.pryzma_yz([(y_front - 0.3, 0.0), (y_back, 0.0), (y_back, H + 0.5), (y_top - 0.3, H + 0.5)], x0, x1)

def piramida(S, bw, bd, tw, td, h, n, naroznik=True, gzyms=True):
    dh = h / n
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        w0 = bw + (tw - bw) * t0; d0 = bd + (td - bd) * t0
        w1 = bw + (tw - bw) * t1
        z0, z1 = k * dh, (k + 1) * dh
        cof = (w0 - w1) / 2
        ins = min(0.45 * cof, 0.14 * dh) if k < n - 1 else 0.3 * cof
        c = min(1.4, 0.07 * min(w0, d0)) if naroznik else 0
        if c > 0:
            S.box(-w0 / 2, w0 / 2, -d0 / 2 + c, d0 / 2 - c, z0, z1, ins)
            S.box(-w0 / 2 + c, w0 / 2 - c, -d0 / 2, d0 / 2, z0, z1 - 0.012, ins)
        else:
            S.box(-w0 / 2, w0 / 2, -d0 / 2, d0 / 2, z0, z1, ins)
        if gzyms and dh > 2.0:
            a = min(0.9, 0.22 * dh)
            wt = w0 - 2 * ins * (1 - 0.2 / dh); dt = d0 - 2 * ins * (1 - 0.2 / dh)
            S.box(-wt / 2 - 0.25, wt / 2 + 0.25, -dt / 2 - 0.25 + c, dt / 2 + 0.25 - c, z1 - a - 0.25, z1 - 0.25)

def swiatynia(nazwa, cx, cy, strona, bw, bd, tw, td, h, n, plat, bud_w, bud_d, bud_h, grzebien_h,
              grzebien_w=None, sw=None, proj=3.0, kol=None, schody4=False, mat=None):
    """Piramida z kilku tarasów, schody z przodu, świątynia z grzebieniem dachowym na szczycie."""
    S = Siatka()
    piramida(S, bw, bd, tw, td, h, n)
    S.box(-tw / 2, tw / 2, -td / 2, td / 2, h, h + plat, 0.05)     # platforma szczytowa
    H = h + plat
    sw = sw or max(6.0, tw * 0.55)
    st = len(S.v)
    schody(S, sw, -bd / 2 - proj, -td / 2, H)
    if schody4:
        for ang in (90, 180, 270):
            st2 = len(S.v)
            schody(S, sw, -bd / 2 - proj, -td / 2, H)
            S.przeksztalc_od(st2, Matrix.Rotation(math.radians(ang), 4, 'Z'))
    if bud_h > 0:
        yb0 = -td / 2 + 1.0
        hb1 = bud_h * 0.55
        S.box(-bud_w / 2, bud_w / 2, yb0, yb0 + bud_d, H, H + hb1)
        S.box(-bud_w / 2 - 0.3, bud_w / 2 + 0.3, yb0 - 0.3, yb0 + bud_d + 0.3, H + hb1, H + hb1 + 0.5)
        S.box(-bud_w / 2 - 0.1, bud_w / 2 + 0.1, yb0 - 0.1, yb0 + bud_d + 0.1, H + hb1 + 0.5, H + bud_h, 0.55)
        dz = min(3.2, hb1 * 0.85)
        S.box(-1.15, 1.15, yb0 - 0.06, yb0 + 0.4, H, H + dz, m=1)       # ciemne wejście
        if grzebien_h > 0:
            gw = grzebien_w or bud_w * 0.92
            gd = bud_d * 0.55
            yc0 = yb0 + bud_d * 0.42
            z = H + bud_h
            tier = grzebien_h / 3
            for i, sk in enumerate((1.0, 0.88, 0.74)):
                S.box(-gw * sk / 2, gw * sk / 2, yc0 + 0.15 * i, yc0 + gd - 0.15 * i, z, z + tier, 0.12)
                z += tier
    ob = S.obiekt(nazwa, [mat['kamien'], mat['ciemny']], kol)
    ob.rotation_euler.z = math.radians(KIERUNEK[strona])
    ob.location = (cx, cy, 0)
    return ob

def palac(S, x0, x1, y0, y1, z0, h, drzwi='S', pietro=False):
    S.box(x0, x1, y0, y1, z0, z0 + h * 0.62)
    S.box(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, z0 + h * 0.62, z0 + h * 0.62 + 0.45)
    S.box(x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, z0 + h * 0.62 + 0.45, z0 + h, 0.45)
    dl = (x1 - x0) if drzwi in 'NS' else (y1 - y0)
    nd = max(1, int(dl / 5.5))
    for i in range(nd):
        t = (i + 0.5) / nd
        if drzwi == 'S':
            xc = x0 + t * (x1 - x0); S.box(xc - 0.9, xc + 0.9, y0 - 0.05, y0 + 0.4, z0, z0 + 2.4, m=1)
        elif drzwi == 'N':
            xc = x0 + t * (x1 - x0); S.box(xc - 0.9, xc + 0.9, y1 - 0.4, y1 + 0.05, z0, z0 + 2.4, m=1)
        elif drzwi == 'W':
            yc = y0 + t * (y1 - y0); S.box(x0 - 0.05, x0 + 0.4, yc - 0.9, yc + 0.9, z0, z0 + 2.4, m=1)
        else:
            yc = y0 + t * (y1 - y0); S.box(x1 - 0.4, x1 + 0.05, yc - 0.9, yc + 0.9, z0, z0 + 2.4, m=1)
    if pietro:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hx, hy = (x1 - x0) * 0.32, (y1 - y0) * 0.32
        palac(S, cx - hx, cx + hx, cy - hy, cy + hy, z0 + h, h * 0.8, drzwi, False)

# ---------------------------------------------------------------- teren
def wysokosc_terenu(x, y):
    """Łagodne wzgórza poza centrum (dla Tikal: grzbiety wapienne), płasko przy budowlach."""
    hx = (6.0 * np.sin(x / 260.0 + 0.7) * np.cos(y / 310.0 - 0.4) + 3.5 * np.sin((x + y) / 140.0 + 1.3)
          + 2.0 * np.cos((x - 2 * y) / 95.0))
    d = np.full_like(x, 1e9)
    for (px, py, r) in PLASKIE:
        d = np.minimum(d, np.hypot(x - px, y - py) - r)
    t = np.clip(d / 220.0, 0, 1)
    t = t * t * (3 - 2 * t)
    return hx * t

# miejsca, gdzie teren ma być płaski: (x, y, promień)
PLASKIE = [(60, -10, 230), (-254, -15, 60), (-662, 163, 80), (-6, -283, 60), (-452, -241, 90), (-380, 90, 60)]

def w_polanie(x, y):
    """Maska polan (bez drzew): centrum, grobla Tozzera, otoczenie świątyń III, IV, V i Mundo Perdido."""
    m = (x > -98) & (x < 250) & (y > -145) & (y < 128)
    # grobla Tozzera: od Placu do Świątyni IV
    ax, ay, bx, by = -80.0, 38.0, -628.0, 150.0
    vx, vy = bx - ax, by - ay
    t = np.clip(((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy), 0, 1)
    dd = np.hypot(x - (ax + t * vx), y - (ay + t * vy))
    m |= dd < 13
    for (px, py, hx, hy) in [(-254, -15, 30, 30), (-662, 163, 42, 46), (-6, -283, 28, 30), (-452, -241, 45, 45)]:
        m |= (np.abs(x - px) < hx) & (np.abs(y - py) < hy)
    return m

# ---------------------------------------------------------------- materiały
def materialy():
    M = {}
    # kamień wapienny
    mt = bpy.data.materials.new('kamien'); nt = mt.node_tree
    nt.nodes.clear()
    out = wezel(nt, 'ShaderNodeOutputMaterial', (600, 0))
    bs = wezel(nt, 'ShaderNodeBsdfPrincipled', (300, 0), Roughness=0.92)
    tc = wezel(nt, 'ShaderNodeTexCoord', (-900, 0))
    no = wezel(nt, 'ShaderNodeTexNoise', (-650, 100), Scale=0.08, Detail=8.0, Roughness=0.62)
    lacz(nt, tc.outputs['Object'], no.inputs['Vector'])
    no2 = wezel(nt, 'ShaderNodeTexNoise', (-650, -150), Scale=1.3, Detail=6.0)
    lacz(nt, tc.outputs['Object'], no2.inputs['Vector'])
    cr = wezel(nt, 'ShaderNodeValToRGB', (-380, 100))
    cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[0].color = (0.075, 0.075, 0.07, 1)
    cr.color_ramp.elements[1].position = 0.72; cr.color_ramp.elements[1].color = (0.40, 0.39, 0.35, 1)
    e = cr.color_ramp.elements.new(0.55); e.color = (0.21, 0.21, 0.19, 1)
    lacz(nt, no.outputs['Fac'], cr.inputs['Fac'])
    # ciemne zacieki u dołu (wilgoć, porosty)
    sep = wezel(nt, 'ShaderNodeSeparateXYZ', (-650, -350))
    geo = wezel(nt, 'ShaderNodeNewGeometry', (-900, -350))
    lacz(nt, geo.outputs['Position'], sep.inputs['Vector'])
    mr = wezel(nt, 'ShaderNodeMapRange', (-420, -350))
    mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 14.0
    mr.inputs['To Min'].default_value = 0.55; mr.inputs['To Max'].default_value = 0.0
    lacz(nt, sep.outputs['Z'], mr.inputs['Value'])
    mix = wezel(nt, 'ShaderNodeMix', (-120, 50)); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    lacz(nt, mr.outputs['Result'], mix.inputs['Factor'])
    lacz(nt, cr.outputs['Color'], mix.inputs[6])
    mix.inputs[7].default_value = (0.30, 0.32, 0.26, 1)
    lacz(nt, mix.outputs[2], bs.inputs['Base Color'])
    bump = wezel(nt, 'ShaderNodeBump', (60, -200), Strength=0.35, Distance=0.3)
    lacz(nt, no2.outputs['Fac'], bump.inputs['Height'])
    lacz(nt, bump.outputs['Normal'], bs.inputs['Normal'])
    lacz(nt, bs.outputs[0], out.inputs['Surface'])
    M['kamien'] = mt

    mt = bpy.data.materials.new('ciemny'); nt = mt.node_tree
    bs = nt.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (0.004, 0.004, 0.004, 1); bs.inputs['Roughness'].default_value = 1.0; bs.inputs['Specular IOR Level'].default_value = 0.0
    M['ciemny'] = mt

    # trawa na placach
    mt = bpy.data.materials.new('trawa'); nt = mt.node_tree
    nt.nodes.clear()
    out = wezel(nt, 'ShaderNodeOutputMaterial', (600, 0))
    bs = wezel(nt, 'ShaderNodeBsdfPrincipled', (300, 0), Roughness=0.95)
    bs.inputs['Specular IOR Level'].default_value = 0.15
    tc = wezel(nt, 'ShaderNodeTexCoord', (-700, 0))
    no = wezel(nt, 'ShaderNodeTexNoise', (-500, 0), Scale=0.02, Detail=6.0)
    lacz(nt, tc.outputs['Object'], no.inputs['Vector'])
    cr = wezel(nt, 'ShaderNodeValToRGB', (-250, 0))
    cr.color_ramp.elements[0].color = (0.035, 0.07, 0.018, 1); cr.color_ramp.elements[1].color = (0.10, 0.16, 0.04, 1)
    lacz(nt, no.outputs['Fac'], cr.inputs['Fac'])
    lacz(nt, cr.outputs['Color'], bs.inputs['Base Color'])
    lacz(nt, bs.outputs[0], out.inputs['Surface'])
    M['trawa'] = mt

    # ścieżka / grobla (ubita ziemia, wapienny gruz)
    mt = bpy.data.materials.new('grobla'); bs = mt.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (0.13, 0.12, 0.075, 1); bs.inputs['Roughness'].default_value = 1.0
    M['grobla'] = mt

    # liście: kolor z atrybutu instancji „odcien”
    mt = bpy.data.materials.new('liscie'); nt = mt.node_tree
    nt.nodes.clear()
    out = wezel(nt, 'ShaderNodeOutputMaterial', (700, 0))
    bs = wezel(nt, 'ShaderNodeBsdfPrincipled', (400, 0), Roughness=0.75)
    bs.inputs['Subsurface Weight'].default_value = 0.0
    at = wezel(nt, 'ShaderNodeAttribute', (-700, 0)); at.attribute_type = 'INSTANCER'; at.attribute_name = 'odcien'
    cr = wezel(nt, 'ShaderNodeValToRGB', (-450, 0))
    cr.color_ramp.elements[0].color = (0.012, 0.032, 0.012, 1)
    cr.color_ramp.elements[1].color = (0.045, 0.08, 0.032, 1)
    e = cr.color_ramp.elements.new(0.5); e.color = (0.028, 0.06, 0.02, 1)
    lacz(nt, at.outputs['Fac'], cr.inputs['Fac'])
    tc = wezel(nt, 'ShaderNodeTexCoord', (-700, -250))
    no = wezel(nt, 'ShaderNodeTexNoise', (-450, -250), Scale=1.6, Detail=6.0)
    lacz(nt, tc.outputs['Object'], no.inputs['Vector'])
    mx = wezel(nt, 'ShaderNodeMix', (-150, 0)); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs['Factor'].default_value = 0.6
    lacz(nt, cr.outputs['Color'], mx.inputs[6])
    nm = wezel(nt, 'ShaderNodeMapRange', (-250, -250)); nm.inputs['To Min'].default_value = 0.55; nm.inputs['To Max'].default_value = 1.35
    lacz(nt, no.outputs['Fac'], nm.inputs['Value'])
    cmb = wezel(nt, 'ShaderNodeCombineXYZ', (-100, -250))
    for k in 'XYZ':
        lacz(nt, nm.outputs['Result'], cmb.inputs[k])
    lacz(nt, cmb.outputs[0], mx.inputs[7])
    lacz(nt, mx.outputs[2], bs.inputs['Base Color'])
    bump = wezel(nt, 'ShaderNodeBump', (150, -250), Strength=0.85, Distance=0.5)
    lacz(nt, no.outputs['Fac'], bump.inputs['Height'])
    lacz(nt, bump.outputs['Normal'], bs.inputs['Normal'])
    lacz(nt, bs.outputs[0], out.inputs['Surface'])
    M['liscie'] = mt

    # dywan koron drzew (daleki las): zieleń + mgiełka odległości
    mt = bpy.data.materials.new('korony_daleko'); nt = mt.node_tree
    nt.nodes.clear()
    out = wezel(nt, 'ShaderNodeOutputMaterial', (700, 0))
    bs = wezel(nt, 'ShaderNodeBsdfPrincipled', (400, 0), Roughness=0.85)
    tc = wezel(nt, 'ShaderNodeTexCoord', (-700, 0))
    no = wezel(nt, 'ShaderNodeTexNoise', (-450, 0), Scale=0.004, Detail=10.0, Roughness=0.7)
    lacz(nt, tc.outputs['Object'], no.inputs['Vector'])
    cr = wezel(nt, 'ShaderNodeValToRGB', (-200, 0))
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[0].color = (0.015, 0.04, 0.012, 1)
    cr.color_ramp.elements[1].position = 0.75; cr.color_ramp.elements[1].color = (0.07, 0.11, 0.03, 1)
    # korony: komórki Voronoi ~13 m (kopuły), ciemniejsze szczeliny między koronami
    vo = wezel(nt, 'ShaderNodeTexVoronoi', (-450, -300), Scale=0.075, Randomness=0.9)
    lacz(nt, tc.outputs['Object'], vo.inputs['Vector'])
    no2 = wezel(nt, 'ShaderNodeTexNoise', (-450, -550), Scale=0.6, Detail=5.0)
    lacz(nt, tc.outputs['Object'], no2.inputs['Vector'])
    kop = wezel(nt, 'ShaderNodeMapRange', (-200, -300))
    kop.inputs['From Min'].default_value = 0.0; kop.inputs['From Max'].default_value = 0.75
    kop.inputs['To Min'].default_value = 1.0; kop.inputs['To Max'].default_value = 0.0
    lacz(nt, vo.outputs['Distance'], kop.inputs['Value'])
    ciem = wezel(nt, 'ShaderNodeMapRange', (-200, -100))
    ciem.inputs['To Min'].default_value = 0.25; ciem.inputs['To Max'].default_value = 1.15
    lacz(nt, kop.outputs['Result'], ciem.inputs['Value'])
    mx1 = wezel(nt, 'ShaderNodeMix', (0, 0), data_type='RGBA', blend_type='MULTIPLY'); mx1.inputs['Factor'].default_value = 1.0
    lacz(nt, cr.outputs['Color'], mx1.inputs[6])
    cmb = wezel(nt, 'ShaderNodeCombineXYZ', (-50, -100))
    for k in 'XYZ':
        lacz(nt, ciem.outputs['Result'], cmb.inputs[k])
    lacz(nt, cmb.outputs[0], mx1.inputs[7])
    mx2 = wezel(nt, 'ShaderNodeMix', (200, 0), data_type='RGBA', blend_type='MIX'); mx2.inputs['Factor'].default_value = 0.0
    lacz(nt, mx1.outputs[2], mx2.inputs[6]); lacz(nt, vo.outputs['Color'], mx2.inputs[7])
    mx3 = wezel(nt, 'ShaderNodeMix', (300, 0), data_type='RGBA', blend_type='MULTIPLY'); mx3.inputs['Factor'].default_value = 1.0
    lacz(nt, mx2.outputs[2], mx3.inputs[6]); mx3.inputs[7].default_value = (0.85, 0.9, 0.8, 1)
    lacz(nt, mx3.outputs[2], bs.inputs['Base Color'])
    hsum = wezel(nt, 'ShaderNodeMath', (0, -450), operation='MULTIPLY_ADD')
    lacz(nt, no2.outputs['Fac'], hsum.inputs[0]); hsum.inputs[1].default_value = 0.35; lacz(nt, kop.outputs['Result'], hsum.inputs[2])
    bump = wezel(nt, 'ShaderNodeBump', (150, -350), Strength=1.0, Distance=4.0)
    lacz(nt, hsum.outputs[0], bump.inputs['Height'])
    lacz(nt, bump.outputs['Normal'], bs.inputs['Normal'])
    bs.inputs['Specular IOR Level'].default_value = 0.25
    # mgiełka powietrza w oddali: w stronę koloru nieba w tym samym kierunku
    geo = wezel(nt, 'ShaderNodeNewGeometry', (-200, 400))
    neg = wezel(nt, 'ShaderNodeVectorMath', (0, 400), operation='SCALE'); neg.inputs['Scale'].default_value = -1.0
    lacz(nt, geo.outputs['Incoming'], neg.inputs[0])
    sxyz = wezel(nt, 'ShaderNodeSeparateXYZ', (100, 500)); lacz(nt, neg.outputs[0], sxyz.inputs[0])
    zmx = wezel(nt, 'ShaderNodeMath', (200, 550), operation='MAXIMUM'); zmx.inputs[1].default_value = 0.10
    lacz(nt, sxyz.outputs['Z'], zmx.inputs[0])
    cxyz = wezel(nt, 'ShaderNodeCombineXYZ', (300, 500))
    lacz(nt, sxyz.outputs['X'], cxyz.inputs['X']); lacz(nt, sxyz.outputs['Y'], cxyz.inputs['Y']); lacz(nt, zmx.outputs[0], cxyz.inputs['Z'])
    sky = niebo_wezel(nt, (200, 400)); lacz(nt, cxyz.outputs[0], sky.inputs[0])
    em = wezel(nt, 'ShaderNodeEmission', (400, 400), Strength=1.0)
    em.inputs['Color'].default_value = (*MGIELKA, 1)   # stała mgiełka (kolor nieba przy horyzoncie po stronie przeciwnej do Słońca)
    camd = wezel(nt, 'ShaderNodeCameraData', (-200, 650))
    m1 = wezel(nt, 'ShaderNodeMath', (0, 650), operation='SUBTRACT'); m1.inputs[1].default_value = 500.0
    lacz(nt, camd.outputs['View Distance'], m1.inputs[0])
    m2 = wezel(nt, 'ShaderNodeMath', (150, 650), operation='MAXIMUM'); m2.inputs[1].default_value = 0.0
    lacz(nt, m1.outputs[0], m2.inputs[0])
    m3 = wezel(nt, 'ShaderNodeMath', (300, 650), operation='DIVIDE'); m3.inputs[1].default_value = -2600.0
    lacz(nt, m2.outputs[0], m3.inputs[0])
    m4 = wezel(nt, 'ShaderNodeMath', (450, 650), operation='EXPONENT'); lacz(nt, m3.outputs[0], m4.inputs[0])
    m5 = wezel(nt, 'ShaderNodeMath', (600, 650), operation='SUBTRACT'); m5.inputs[0].default_value = 1.0
    lacz(nt, m4.outputs[0], m5.inputs[1])
    ms = wezel(nt, 'ShaderNodeMixShader', (600, 200))
    lacz(nt, m5.outputs[0], ms.inputs['Fac']); lacz(nt, bs.outputs[0], ms.inputs[1]); lacz(nt, em.outputs[0], ms.inputs[2])
    lacz(nt, ms.outputs[0], out.inputs['Surface'])
    M['korony_daleko'] = mt

    mt = bpy.data.materials.new('pien'); bs = mt.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (0.08, 0.065, 0.05, 1); bs.inputs['Roughness'].default_value = 0.9
    M['pien'] = mt
    return M

def material_mgla():
    mt = bpy.data.materials.new('mgla'); nt = mt.node_tree
    nt.nodes.clear()
    out = wezel(nt, 'ShaderNodeOutputMaterial', (900, 0))
    vol = wezel(nt, 'ShaderNodeVolumePrincipled', (600, 0))
    vol.inputs['Color'].default_value = (0.92, 0.94, 1.0, 1)
    vol.inputs['Anisotropy'].default_value = 0.45
    geo = wezel(nt, 'ShaderNodeNewGeometry', (-900, 0))
    sep = wezel(nt, 'ShaderNodeSeparateXYZ', (-700, 0))
    lacz(nt, geo.outputs['Position'], sep.inputs['Vector'])
    # pas mgły nad koronami: max ok. 22–34 m, cieńsza przy ziemi, prawie nic powyżej 70 m
    def gauss(c, s, waga, y):
        a = wezel(nt, 'ShaderNodeMath', (-500, y), operation='SUBTRACT'); lacz(nt, sep.outputs['Z'], a.inputs[0]); a.inputs[1].default_value = c
        b = wezel(nt, 'ShaderNodeMath', (-350, y), operation='DIVIDE'); lacz(nt, a.outputs[0], b.inputs[0]); b.inputs[1].default_value = s
        c2 = wezel(nt, 'ShaderNodeMath', (-200, y), operation='MULTIPLY'); lacz(nt, b.outputs[0], c2.inputs[0]); lacz(nt, b.outputs[0], c2.inputs[1])
        d = wezel(nt, 'ShaderNodeMath', (-50, y), operation='MULTIPLY'); lacz(nt, c2.outputs[0], d.inputs[0]); d.inputs[1].default_value = -1.0
        e = wezel(nt, 'ShaderNodeMath', (100, y), operation='EXPONENT'); lacz(nt, d.outputs[0], e.inputs[0])
        f = wezel(nt, 'ShaderNodeMath', (250, y), operation='MULTIPLY'); lacz(nt, e.outputs[0], f.inputs[0]); f.inputs[1].default_value = waga
        return f
    g1 = gauss(28.0, 9.0, 0.0022, 200)
    g2 = gauss(0.0, 24.0, 0.00025, -100)
    s1 = wezel(nt, 'ShaderNodeMath', (400, 100), operation='ADD'); lacz(nt, g1.outputs[0], s1.inputs[0]); lacz(nt, g2.outputs[0], s1.inputs[1])
    # plamy mgły
    no = wezel(nt, 'ShaderNodeTexNoise', (-500, -400), Scale=0.0035, Detail=3.0, Roughness=0.5)
    lacz(nt, geo.outputs['Position'], no.inputs['Vector'])
    mr = wezel(nt, 'ShaderNodeMapRange', (-250, -400))
    mr.inputs['From Min'].default_value = 0.35; mr.inputs['From Max'].default_value = 0.65
    mr.inputs['To Min'].default_value = 0.25; mr.inputs['To Max'].default_value = 1.6
    lacz(nt, no.outputs['Fac'], mr.inputs['Value'])
    s2 = wezel(nt, 'ShaderNodeMath', (500, -100), operation='MULTIPLY'); lacz(nt, s1.outputs[0], s2.inputs[0]); lacz(nt, mr.outputs['Result'], s2.inputs[1])
    lacz(nt, s2.outputs[0], vol.inputs['Density'])
    lacz(nt, vol.outputs[0], out.inputs['Volume'])
    return mt

# ---------------------------------------------------------------- drzewa
def warianty_drzew(M):
    kol = bpy.data.collections.new('warianty_drzew')   # nie podpinamy do sceny
    obs = []
    for v in range(6):
        rnd = random.Random(100 + v)
        bm = bmesh.new()
        H = rnd.uniform(19, 28)
        bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=0.9, radius2=0.45, depth=H * 0.7,
                              matrix=Matrix.Translation((0, 0, H * 0.35)))
        for f in bm.faces:
            f.material_index = 1
        nk = rnd.randint(7, 10)
        R = rnd.uniform(7.5, 10.5)
        for k in range(nk):
            a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(R * 0.25, R * 0.7) if k else 0
            r = rnd.uniform(4.2, 6.5) * (1.2 if k == 0 else 1)
            z = H * rnd.uniform(0.72, 0.9) - 0.12 * d
            m = Matrix.Translation((d * math.cos(a), d * math.sin(a), z)) @ Matrix.Diagonal((1, 1, rnd.uniform(0.62, 0.8), 1))
            res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r, matrix=m)
            for vv in res['verts']:
                vv.co += (vv.co - m.translation).normalized() * (1.3 * mnoise.noise(vv.co * 0.32 + Vector((v * 17.0, 0, 0)))); vv.co.z += rnd.uniform(-0.25, 0.25)
        for k in range(4):   # podszyt: niższe krzewy i młode drzewa wokół pnia
            a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(2.0, 6.0)
            r = rnd.uniform(2.8, 4.2); z = rnd.uniform(2.5, H * 0.45)
            m = Matrix.Translation((d * math.cos(a), d * math.sin(a), z)) @ Matrix.Diagonal((1, 1, 0.8, 1))
            res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r, matrix=m)
            for vv in res['verts']:
                vv.co.x += rnd.uniform(-0.4, 0.4); vv.co.y += rnd.uniform(-0.4, 0.4); vv.co.z += rnd.uniform(-0.3, 0.3)
        me = bpy.data.meshes.new(f'drzewo_{v}')
        bm.to_mesh(me); bm.free()
        me.materials.append(M['liscie']); me.materials.append(M['pien'])
        for p in me.polygons:
            p.use_smooth = True
        ob = bpy.data.objects.new(f'drzewo_{v}', me)
        kol.objects.link(ob)
        obs.append(ob)
    return kol

def las(M, kol_sceny):
    kol_w = warianty_drzew(M)
    # punkty: siatka z rozrzutem w pasie bliskim kamerze
    krok = 9.5
    xs = np.arange(-950, 420, krok); ys = np.arange(-520, 470, krok)
    X, Y = np.meshgrid(xs, ys)
    X = X + RNG.uniform(-4.2, 4.2, X.shape); Y = Y + RNG.uniform(-4.2, 4.2, Y.shape)
    X = X.ravel(); Y = Y.ravel()
    ok = ~w_polanie(X, Y) & (RNG.random(X.shape) > 0.07)
    X, Y = X[ok], Y[ok]
    Z = wysokosc_terenu(X, Y)
    n = len(X)
    me = bpy.data.meshes.new('punkty_drzew')
    me.vertices.add(n)
    me.vertices.foreach_set('co', np.column_stack([X, Y, Z]).astype(np.float32).ravel())
    var = RNG.integers(0, 6, n).astype(np.int32)
    sc = RNG.uniform(0.75, 1.25, n).astype(np.float32)
    rz = RNG.uniform(0, 2 * math.pi, n).astype(np.float32)
    od = RNG.random(n).astype(np.float32)
    for nm, typ, dane in (('war', 'INT', var), ('skala', 'FLOAT', sc), ('obrot', 'FLOAT', rz), ('odcien', 'FLOAT', od)):
        a = me.attributes.new(nm, typ, 'POINT'); a.data.foreach_set('value', dane)
    ob = bpy.data.objects.new('las_blisko', me)
    kol_sceny.objects.link(ob)
    # geometry nodes: instancje drzew na punktach
    ng = bpy.data.node_groups.new('drzewa_GN', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput'); go = ng.nodes.new('NodeGroupOutput')
    ci = ng.nodes.new('GeometryNodeCollectionInfo'); ci.inputs['Collection'].default_value = kol_w
    ci.inputs['Separate Children'].default_value = True; ci.inputs['Reset Children'].default_value = True
    iop = ng.nodes.new('GeometryNodeInstanceOnPoints')
    iop.inputs['Pick Instance'].default_value = True
    a_war = ng.nodes.new('GeometryNodeInputNamedAttribute'); a_war.data_type = 'INT'; a_war.inputs['Name'].default_value = 'war'
    a_sc = ng.nodes.new('GeometryNodeInputNamedAttribute'); a_sc.data_type = 'FLOAT'; a_sc.inputs['Name'].default_value = 'skala'
    a_rz = ng.nodes.new('GeometryNodeInputNamedAttribute'); a_rz.data_type = 'FLOAT'; a_rz.inputs['Name'].default_value = 'obrot'
    cmb = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(a_rz.outputs['Attribute'], cmb.inputs['Z'])
    e2r = ng.nodes.new('FunctionNodeEulerToRotation')
    ng.links.new(cmb.outputs[0], e2r.inputs[0])
    ng.links.new(gi.outputs[0], iop.inputs['Points'])
    ng.links.new(ci.outputs[0], iop.inputs['Instance'])
    ng.links.new(a_war.outputs['Attribute'], iop.inputs['Instance Index'])
    ng.links.new(e2r.outputs[0], iop.inputs['Rotation'])
    ng.links.new(a_sc.outputs['Attribute'], iop.inputs['Scale'])
    ng.links.new(iop.outputs[0], go.inputs[0])
    mod = ob.modifiers.new('drzewa', 'NODES'); mod.node_group = ng
    print('DRZEW', n)
    return ob

def dywan_koron(M, kol):
    """Daleki las jako pofałdowana powierzchnia koron (z dziurami na polany)."""
    krok = 12.0
    xs = np.arange(-2600, 2600 + krok, krok); ys = np.arange(-2600, 2600 + krok, krok)
    nx, ny = len(xs), len(ys)
    X, Y = np.meshgrid(xs, ys)
    Z = (wysokosc_terenu(X, Y) + 20.5 + 3.0 * np.sin(X / 37.0 + np.cos(Y / 23.0)) * np.cos(Y / 41.0 + 0.5 * np.sin(X / 19.0))
         + RNG.uniform(-2.2, 2.2, X.shape))
    V = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()]).astype(np.float32)
    ii, jj = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1))
    a = (jj * nx + ii).ravel()
    F = np.column_stack([a, a + 1, a + nx + 1, a + nx])
    cxs = (X[:-1, :-1] + krok / 2).ravel(); cys = (Y[:-1, :-1] + krok / 2).ravel()
    keep = ~(w_polanie(cxs, cys) | w_polanie(cxs + 10, cys) | w_polanie(cxs - 10, cys)
             | w_polanie(cxs, cys + 10) | w_polanie(cxs, cys - 10))
    # tam, gdzie stoją bliskie drzewa, dywan schodzi niżej (żeby nie przebijał koron)
    F = F[keep]
    me = bpy.data.meshes.new('korony_daleko')
    me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(F.size); me.loops.foreach_set('vertex_index', F.ravel().astype(np.int32))
    me.polygons.add(len(F)); me.polygons.foreach_set('loop_start', (np.arange(len(F)) * 4).astype(np.int32))
    me.update(); me.validate()
    me.materials.append(M['korony_daleko'])
    me.shade_smooth()
    ob = bpy.data.objects.new('korony_daleko', me); kol.objects.link(ob)
    # bardzo daleka równina koron po horyzont
    R, r = 30000.0, 2500.0   # pierścień z dziurą w środku, żeby nie przykrył placów
    v = [(-R, -R, 0), (R, -R, 0), (R, R, 0), (-R, R, 0), (-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0)]
    f = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me2 = bpy.data.meshes.new('las_horyzont'); me2.from_pydata(v, [], f); me2.update()
    me2.materials.append(M['korony_daleko'])
    ob2 = bpy.data.objects.new('las_horyzont', me2); ob2.location.z = 18.0; kol.objects.link(ob2)

def teren(M, kol):
    krok = 8.0
    xs = np.arange(-1000, 520 + krok, krok); ys = np.arange(-560, 520 + krok, krok)
    nx, ny = len(xs), len(ys)
    X, Y = np.meshgrid(xs, ys)
    Z = wysokosc_terenu(X, Y) - 0.02
    V = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()]).astype(np.float32)
    ii, jj = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1))
    a = (jj * nx + ii).ravel()
    F = np.column_stack([a, a + 1, a + nx + 1, a + nx])
    me = bpy.data.meshes.new('teren')
    me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(F.size); me.loops.foreach_set('vertex_index', F.ravel().astype(np.int32))
    me.polygons.add(len(F)); me.polygons.foreach_set('loop_start', (np.arange(len(F)) * 4).astype(np.int32))
    me.update(); me.validate()
    me.materials.append(M['trawa'])
    ob = bpy.data.objects.new('teren', me); kol.objects.link(ob)
    # grobla Tozzera: pas ubitej ziemi
    S = Siatka()
    ax, ay, bx, by = -80.0, 38.0, -628.0, 150.0
    L = math.hypot(bx - ax, by - ay)
    S.box(0, L, -9, 9, -0.3, 0.25)
    S.przeksztalc_od(0, Matrix.Translation((ax, ay, 0)) @ Matrix.Rotation(math.atan2(by - ay, bx - ax), 4, 'Z'))
    S.obiekt('grobla_Tozzera', [M['grobla']], kol)

# ---------------------------------------------------------------- budowa miasta
def miasto(M, kol):
    # Świątynia I (Wielkiego Jaguara): 47 m, 9 tarasów, front na zachód
    swiatynia('Swiatynia_I', 52, -1, 'W', bw=32, bd=30, tw=14, td=12, h=30.0, n=9, plat=0.8,
              bud_w=12, bud_d=8.5, bud_h=7.0, grzebien_h=9.2, sw=8.0, proj=3.5, kol=kol, mat=M)
    # Świątynia II (Masek): ok. 38 m, podstawa 37,6 × 41 m, 3 tarasy, front na wschód
    swiatynia('Swiatynia_II', -54, 0, 'E', bw=41, bd=37.6, tw=20, td=15, h=20.0, n=3, plat=1.0,
              bud_w=16, bud_d=8.5, bud_h=7.5, grzebien_h=9.5, grzebien_w=14.5, sw=10.0, proj=3.0, kol=kol, mat=M)
    # Świątynia III: ok. 55 m
    swiatynia('Swiatynia_III', -254, -15, 'E', bw=42, bd=40, tw=15, td=13, h=36.0, n=9, plat=1.0,
              bud_w=12, bud_d=8, bud_h=8.0, grzebien_h=10.0, sw=9.0, proj=3.5, kol=kol, mat=M)
    # Świątynia IV: ok. 65 m (najwyższa), front na wschód
    swiatynia('Swiatynia_IV', -662, 163, 'E', bw=68, bd=58, tw=24, td=17, h=44.0, n=7, plat=2.0,
              bud_w=18, bud_d=10, bud_h=9.0, grzebien_h=10.0, grzebien_w=15, sw=12.0, proj=4.0, kol=kol, mat=M)
    # Świątynia V: ok. 57 m, front na północ
    swiatynia('Swiatynia_V', -6, -283, 'N', bw=40, bd=38, tw=12, td=9, h=38.0, n=7, plat=1.0,
              bud_w=9.5, bud_d=5.5, bud_h=6.0, grzebien_h=12.0, sw=8.0, proj=4.0, kol=kol, mat=M)
    # Mundo Perdido, Wielka Piramida 5C-54: ok. 31 m, schody z czterech stron
    swiatynia('Mundo_Perdido_5C54', -452, -241, 'E', bw=60, bd=60, tw=18, td=18, h=30.0, n=5, plat=1.0,
              bud_w=0, bud_d=0, bud_h=0, grzebien_h=0, sw=10.0, proj=4.0, kol=kol, schody4=True, mat=M)

    # Akropol Północny: platforma dwustopniowa z kilkunastoma świątyniami
    S = Siatka()
    S.box(-54, 60, 44, 117, 0, 4.2, 0.6)
    S.box(-47, 54, 51, 112, 4.2, 9.0, 0.6)
    st = len(S.v)
    schody(S, 40, 40.0, 44.6, 4.2, por=False)
    S.przeksztalc_od(st, Matrix.Translation((3, 0, 0)))
    st = len(S.v)
    schody(S, 26, 44.4, 51.5, 9.0, por=False)
    S.przeksztalc_od(st, Matrix.Translation((3, 0, 0)))
    S.obiekt('Akropol_Polnocny_platforma', [M['kamien'], M['ciemny']], kol)
    for nz, x, y, bw, h, n, bh, gh in [('5D-33', 3, 64, 19, 12, 4, 5.5, 6.0), ('5D-32', -22, 64, 13, 8, 3, 4.5, 3.0),
                                       ('5D-34', 28, 64, 13, 8, 3, 4.5, 3.0), ('5D-22', 3, 94, 21, 11, 4, 5.5, 4.0),
                                       ('5D-23', 30, 97, 14, 9, 3, 4.5, 3.0), ('5D-24', -24, 97, 14, 9, 3, 4.5, 3.0),
                                       ('5D-35', -40, 66, 8, 4, 2, 3.5, 0), ('5D-31', 45, 66, 8, 4, 2, 3.5, 0)]:
        ob = swiatynia('Akropol_Polnocny_' + nz, x, y, 'S', bw=bw, bd=bw * 0.95, tw=bw * 0.5, td=bw * 0.42, h=h, n=n,
                       plat=0.6, bud_w=bw * 0.42, bud_d=bw * 0.3, bud_h=bh, grzebien_h=gh, sw=bw * 0.32, proj=1.5, kol=kol, mat=M)
        ob.location.z = 9.0

    # stele i ołtarze przed Akropolem Północnym
    S = Siatka()
    for i, x in enumerate(np.linspace(-44, 50, 17)):
        S.box(x - 0.6, x + 0.6, 39.5, 40.0, 0, 3.0 + 0.4 * math.sin(i * 1.7), 0.05)
        S.walec(x, 37.6, 0.85, 0, 0.6, n=14)
    S.obiekt('stele_i_oltarze', [M['kamien']], kol)

    # Akropol Centralny: pałace wokół dziedzińców
    S = Siatka()
    S.box(-87, 226, -131, -38, 0, 3.5, 0.5)
    st = len(S.v)
    schody(S, 30, -34.5, -38.6, 3.5, por=False)       # schody od strony placu (front na północ)
    S.przeksztalc_od(st, Matrix.Translation((5, 0, 0)) @ Matrix.Rotation(math.pi, 4, 'Z'))
    rnd = random.Random(11)
    for cxk in (-55, -2, 52, 108, 165, 205):
        cyk = -84 + rnd.uniform(-6, 6)
        r = 19 if cxk != 205 else 13
        for strona in 'NSEW':
            h = rnd.uniform(6.0, 9.5)
            pt = rnd.random() < 0.3
            if strona == 'N':
                palac(S, cxk - r, cxk + r, cyk + r - 7, cyk + r, 3.5, h, 'S', pt)
            elif strona == 'S':
                palac(S, cxk - r, cxk + r, cyk - r, cyk - r + 7, 3.5, h + rnd.uniform(0, 3), 'N', pt)
            elif strona == 'E':
                palac(S, cxk + r - 7, cxk + r, cyk - r + 7.4, cyk + r - 7.4, 3.5, h * 0.9, 'W', False)
            else:
                palac(S, cxk - r, cxk - r + 7, cyk - r + 7.4, cyk + r - 7.4, 3.5, h * 0.9, 'E', False)
    # Pałac Pięciopiętrowy (Maler) od południa: 5 kondygnacji
    for i in range(5):
        palac(S, 60 + 2.5 * i, 96 - 2.5 * i, -130 + 1.6 * i, -117 - 0.4 * i, 3.5 + i * 4.6, 4.6, 'S', False)
    S.obiekt('Akropol_Centralny', [M['kamien'], M['ciemny']], kol)

    # boisko do gry w piłkę (5D-74) na południe od Świątyni I
    S = Siatka()
    S.box(37, 46, -44, -25, 0, 5.0, 1.8)
    S.box(53, 62, -44, -25, 0, 5.0, 1.8)
    # budowle Placu Wschodniego
    palac(S, 138, 152, -11, 33, 0, 6.5, 'E')
    palac(S, 159, 173, -11, 33, 0, 6.5, 'W')
    S.box(186, 242, -40, 40, 0, 6.0, 1.0)
    palac(S, 196, 232, -12, 12, 6.0, 7.0, 'W', True)
    S.obiekt('Plac_Wschodni', [M['kamien'], M['ciemny']], kol)

# ---------------------------------------------------------------- świat, światło, kamera
SLONCE_AZ = 82.0     # azymut od północy (wschód = 90°)
SLONCE_EL = 5.0

def kierunek_slonca():
    a, e = math.radians(SLONCE_AZ), math.radians(SLONCE_EL)
    return Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))

SWIAT_SILA = 0.35
MGIELKA = (0.70, 0.645, 0.70)

def niebo_wezel(nt, loc):
    sky = wezel(nt, 'ShaderNodeTexSky', loc)
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation = math.radians(SLONCE_EL)
    sky.sun_rotation = math.radians(SLONCE_AZ)    # w Blenderze 5.3: azymut od północy zgodnie z zegarem
    sky.air_density = 1.2; sky.aerosol_density = 3.0
    sky.sun_size = math.radians(1.0)
    return sky

def swiat(sc):
    w = bpy.data.worlds.new('niebo'); sc.world = w
    nt = w.node_tree
    bg = nt.nodes.get('Background')
    sky = niebo_wezel(nt, (-300, 0))
    lacz(nt, sky.outputs[0], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = SWIAT_SILA
    ld = bpy.data.lights.new('slonce', 'SUN')
    ld.energy = 3.2
    ld.color = (1.0, 0.8, 0.64)
    ld.angle = math.radians(0.8)
    lo = bpy.data.objects.new('slonce', ld)
    lo.rotation_euler = kierunek_slonca().to_track_quat('Z', 'Y').to_euler()
    sc.collection.objects.link(lo)

def kamera(sc):
    cd = bpy.data.cameras.new('kamera'); cd.lens = 30; cd.clip_start = 1.0; cd.clip_end = 40000
    co = bpy.data.objects.new('kamera', cd); sc.collection.objects.link(co); sc.camera = co
    cel = bpy.data.objects.new('cel', None); sc.collection.objects.link(cel)
    tr = co.constraints.new('TRACK_TO'); tr.target = cel; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
    klucze = [  # klatka, położenie kamery, punkt, na który patrzy
        (1,   (24, -16, 5.5),    (-54, 2, 21)),
        (160, (62, -64, 30),     (-112, 32, 20)),
        (300, (142, -182, 86),   (-152, 80, 6)),
        (NKL, (200, -250, 120),  (-168, 88, 0)),
    ]
    for f, p, c in klucze:
        co.location = p; co.keyframe_insert('location', frame=f)
        cel.location = c; cel.keyframe_insert('location', frame=f)
    return co

def mgla(kol):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    me = bpy.data.meshes.new('mgla'); bm.to_mesh(me); bm.free()
    me.materials.append(material_mgla())
    ob = bpy.data.objects.new('mgla', me)
    ob.scale = (3600, 3600, 90); ob.location = (-200, 0, 45)
    kol.objects.link(ob)

def ustawienia(sc):
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 1920; sc.render.resolution_y = 1080; sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.frame_start = 1; sc.frame_end = NKL
    ee = sc.eevee
    ee.taa_render_samples = 48
    ee.volumetric_start = 1.0; ee.volumetric_end = 2800.0
    ee.volumetric_tile_size = '4'; ee.volumetric_samples = 96; ee.volumetric_sample_distribution = 0.9
    ee.use_volumetric_shadows = True; ee.volumetric_shadow_samples = 32
    ee.use_shadows = True
    try:
        ee.shadow_resolution_scale = 1.0
        ee.use_fast_gi = True
    except Exception:
        pass
    sc.view_settings.view_transform = 'AgX'
    for look in ('AgX - Medium High Contrast', 'Medium High Contrast'):
        try:
            sc.view_settings.look = look; break
        except Exception:
            pass
    sc.view_settings.exposure = -0.4
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '8'
    # kompozycja: delikatna poświata
    tree = bpy.data.node_groups.new('kompozycja', 'CompositorNodeTree')
    sc.compositing_node_group = tree
    tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = tree.nodes.new('CompositorNodeRLayers')
    gl = tree.nodes.new('CompositorNodeGlare')
    gl.inputs['Type'].default_value = 'Bloom'
    gl.inputs['Threshold'].default_value = 1.2
    gl.inputs['Strength'].default_value = 0.25
    gl.inputs['Size'].default_value = 0.6
    out = tree.nodes.new('NodeGroupOutput')
    tree.links.new(rl.outputs['Image'], gl.inputs['Image'])
    tree.links.new(gl.outputs['Image'], out.inputs[0])

# ---------------------------------------------------------------- render
def renderuj(sc):
    os.makedirs(KLATKI, exist_ok=True)
    if TRYB == "test":
        for o in bpy.data.objects:
            if o.type == "MESH": print("OB", o.name, len(o.data.polygons), tuple(round(c) for c in o.location), tuple(round(c) for c in o.dimensions), o.data.polygons[0].vertices[:] if len(o.data.polygons) else None, len(o.data.loops))
        return
    if TRYB == "probne":
        klatki = [int(k) for k in (ARGS[1] if len(ARGS) > 1 else '1,200,400').split(',')]
        for f in klatki:
            sc.frame_set(f)
            sc.render.resolution_percentage = int(os.environ.get("PROC", "100"))
            sc.render.filepath = os.path.join(KLATKI, f"probna_{f:04d}.png")
            t = time.time()
            bpy.ops.render.render(write_still=True)
            print(f'PROBNA {f} {time.time() - t:.1f}s')
        return
    if os.path.exists(BLOKADA) and open(BLOKADA, encoding="utf-8").read().strip() != NAZWA:   # blokadę z własną nazwą mogła założyć kolejka
        print('BLOKADA: inna sesja renderuje:', open(BLOKADA, encoding='utf-8').read())
        return
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

KADR = 330

def main():
    t0 = time.time()
    wyczysc()
    sc = bpy.context.scene
    kol = bpy.data.collections.new('Tikal'); sc.collection.children.link(kol)
    M = materialy()
    teren(M, kol)
    miasto(M, kol)
    las(M, kol)
    dywan_koron(M, kol)
    mgla(kol)
    swiat(sc)
    kamera(sc)
    ustawienia(sc)
    print(f'SCENA {time.time() - t0:.1f}s')
    renderuj(sc)

main()
