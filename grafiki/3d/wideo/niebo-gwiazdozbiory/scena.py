# -*- coding: utf-8 -*-
"""
Nocne niebo nad obserwatorium El Caracol w Chichén Itzá (rozdział 12).

Uruchomienie (bez okna):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/niebo-gwiazdozbiory/scena.py -- probne 1,200,330,420,500
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/niebo-gwiazdozbiory/scena.py -- pelny

Gwiazdy: katalog HYG v4.4 (D. Nash, astronexus, CC BY-SA 4.0), gwiazdy do 6 mag, wyciąg w _dane/hyg/.
Miejsce: szerokość 20,68° N (Chichén Itzá). Biegun niebieski stoi 20,7° nad północnym horyzontem.
Czas: przyspieszony; czas gwiazdowy od 1 h do 6 h (np. noc z końca listopada: od wieczora do świtu).
Najpierw widok na północ: gwiazdy krążą wokół bieguna (rysują się ślady), potem kamera obraca się na wschód,
gdzie wschodzą Lew, Rak i Bliźnięta; pojawiają się linie gwiazdozbiorów i ekliptyka (epoka J2000).

Układ: x = wschód, y = północ, z = góra. Obiekty nieba w układzie równikowym, obracane wokół osi świata.
"""
import bpy, bmesh, math, os, sys, subprocess, time, csv, random
import numpy as np
from mathutils import Vector, Matrix, Euler

DIR = os.path.dirname(os.path.abspath(__file__))
NAZWA = os.path.basename(DIR)
KLATKI = os.path.join(DIR, '_klatki')
BLOKADA = os.path.join(os.path.dirname(DIR), '.renderuje')
KATALOG = os.path.join(os.path.dirname(DIR), '_dane', 'hyg', 'gwiazdy_mag6.csv')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
TRYB = ARGS[0] if ARGS else 'pelny'
FPS = 25
NKL = 500          # 20 s
KADR = 480
FI = math.radians(20.68)
R_NIEBA = 5000.0
OKO = 1.7
OBLIQ = math.radians(23.4393)
LENS = 15.0
PX_M = R_NIEBA * 2 * math.tan(math.atan(18.0 / LENS)) / 1920   # metry na piksel na sferze nieba
FONT = r'C:\Windows\Fonts\georgia.ttf'
FONT_B = r'C:\Windows\Fonts\georgiab.ttf'

# oś czasu
K_SLADY = 230             # koniec szybkiego obrotu (ślady)
K_PAN = (230, 340)        # obrót kamery na wschód
L0, L1, L2 = 1.3, 5.3, 6.3     # czas gwiazdowy [h] w klatce 1, K_SLADY, NKL

def gladko(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

def czas_gwiazdowy(f):
    """Czas gwiazdowy [h]: szybko w pierwszej części (ślady), potem wolniej; płynne przejście."""
    # prędkość: v1 w części 1, v2 w części 2, gładka zmiana między klatkami 190 a 270
    n1 = K_SLADY - 1; n2 = NKL - K_SLADY
    # całkowanie prędkości: rozwiązanie numeryczne, normalizowane do L1 i L2
    return _TAB[int(round(f))]

def _tablica():
    v = np.ones(NKL + 2)
    for f in range(NKL + 2):
        t = gladko((f - 190) / 80.0)
        v[f] = 1.0 * (1 - t) + 0.22 * t
    c = np.concatenate([[0.0], np.cumsum(v[1:])])
    # dopasuj: c(1) -> L0, c(K_SLADY) -> L1 (w przybliżeniu), c(NKL) -> L2
    a = (L2 - L0) / (c[NKL] - c[1])
    return L0 + a * (c - c[1])
_TAB = _tablica()

def wyczysc():
    for kol in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                bpy.data.lights, bpy.data.curves, bpy.data.node_groups, bpy.data.worlds,
                bpy.data.collections, bpy.data.images, bpy.data.fonts):
        for b in list(kol):
            try:
                kol.remove(b)
            except Exception:
                pass

def wezel(nt, typ, loc=(0, 0), **wej):
    n = nt.nodes.new(typ); n.location = loc
    for k, v in wej.items():
        if k in ('operation', 'data_type', 'blend_type', 'attribute_type', 'attribute_name'):
            setattr(n, k, v)
        else:
            n.inputs[k].default_value = v
    return n

def lacz(nt, a, b):
    nt.links.new(a, b)

def srgb(h):
    """'#rrggbb' -> liniowe RGB."""
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

ZLOTY = srgb('#f0c46f')

def eq(ra_h, dec_deg, r=R_NIEBA):
    a = math.radians(ra_h * 15); d = math.radians(dec_deg)
    return Vector((math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d))) * r

def macierz_osi():
    """Kolumny: obraz osi równikowych (przy czasie gwiazdowym 0) w układzie horyzontalnym."""
    M = Vector((0, -math.sin(FI), math.cos(FI)))   # punkt południka na równiku
    E = Vector((1, 0, 0))
    P = Vector((0, math.cos(FI), math.sin(FI)))    # biegun północny nieba
    m = Matrix((M, E, P)).transposed()
    return m.to_4x4()

# ---------------------------------------------------------------- materiały
def material_zanikajacy(nazwa, kolor, sila):
    """Emisja z przezroczystością sterowaną wartością 'widac' (0..1) – do płynnego pojawiania się."""
    mt = bpy.data.materials.new(nazwa); nt = mt.node_tree; nt.nodes.clear()
    out = wezel(nt, 'ShaderNodeOutputMaterial', (600, 0))
    em = wezel(nt, 'ShaderNodeEmission', (200, 0), Strength=sila); em.inputs['Color'].default_value = (*kolor, 1)
    tr = wezel(nt, 'ShaderNodeBsdfTransparent', (200, 150))
    val = nt.nodes.new('ShaderNodeValue'); val.name = 'widac'; val.outputs[0].default_value = 0.0
    ms = wezel(nt, 'ShaderNodeMixShader', (400, 0))
    lacz(nt, val.outputs[0], ms.inputs[0]); lacz(nt, tr.outputs[0], ms.inputs[1]); lacz(nt, em.outputs[0], ms.inputs[2])
    lacz(nt, ms.outputs[0], out.inputs['Surface'])
    try:
        mt.surface_render_method = 'BLENDED'
    except Exception:
        pass
    mt.use_backface_culling = False
    return mt

def animuj_widac(mt, klucze):
    v = mt.node_tree.nodes['widac'].outputs[0]
    for f, x in klucze:
        v.default_value = x; v.keyframe_insert('default_value', frame=f)

def material_gwiazd():
    mt = bpy.data.materials.new('gwiazdy'); nt = mt.node_tree; nt.nodes.clear()
    out = wezel(nt, 'ShaderNodeOutputMaterial', (900, 0))
    uv = wezel(nt, 'ShaderNodeUVMap', (-800, 0))
    sep = wezel(nt, 'ShaderNodeSeparateXYZ', (-600, 0)); lacz(nt, uv.outputs[0], sep.inputs[0])
    def m(op, a, b, loc):
        n = wezel(nt, 'ShaderNodeMath', loc, operation=op)
        for i, x in enumerate((a, b)):
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            elif x is not None:
                lacz(nt, x, n.inputs[i])
        return n.outputs[0]
    dx = m('SUBTRACT', sep.outputs['X'], 0.5, (-400, 50)); dy = m('SUBTRACT', sep.outputs['Y'], 0.5, (-400, -50))
    r2 = m('ADD', m('MULTIPLY', dx, dx, (-250, 50)), m('MULTIPLY', dy, dy, (-250, -50)), (-100, 0))
    # profil Gaussa: FWHM = połowa boku kwadratu
    g = m('EXPONENT', m('MULTIPLY', r2, -11.09, (50, 0)), None, (200, 0))
    jas = wezel(nt, 'ShaderNodeAttribute', (-100, -250), attribute_name='jas')
    kol = wezel(nt, 'ShaderNodeAttribute', (-100, -450), attribute_name='kolor')
    s = m('MULTIPLY', g, jas.outputs['Fac'], (350, 0))
    em = wezel(nt, 'ShaderNodeEmission', (550, 0))
    lacz(nt, kol.outputs['Color'], em.inputs['Color']); lacz(nt, s, em.inputs['Strength'])
    tr = wezel(nt, 'ShaderNodeBsdfTransparent', (550, 200))
    ad = wezel(nt, 'ShaderNodeAddShader', (750, 0))
    lacz(nt, tr.outputs[0], ad.inputs[0]); lacz(nt, em.outputs[0], ad.inputs[1])
    lacz(nt, ad.outputs[0], out.inputs['Surface'])
    try:
        mt.surface_render_method = 'BLENDED'
    except Exception:
        pass
    return mt

def kolor_bv(ci):
    tab = [(-0.4, (0.60, 0.70, 1.0)), (0.0, (0.80, 0.87, 1.0)), (0.4, (0.97, 0.97, 1.0)), (0.65, (1.0, 0.95, 0.86)),
           (1.0, (1.0, 0.86, 0.68)), (1.4, (1.0, 0.76, 0.52)), (2.0, (1.0, 0.64, 0.38))]
    if ci <= tab[0][0]:
        return tab[0][1]
    for (a, ca), (b, cb) in zip(tab, tab[1:]):
        if ci <= b:
            t = (ci - a) / (b - a)
            return tuple(ca[i] + (cb[i] - ca[i]) * t for i in range(3))
    return tab[-1][1]

# ---------------------------------------------------------------- gwiazdy
def wczytaj():
    gw = []
    with open(KATALOG, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            try:
                ci = float(r['ci'])
            except ValueError:
                ci = 0.6
            gw.append(dict(ra=float(r['ra_h']), dec=float(r['dec_deg']), mag=float(r['mag']), ci=ci,
                           bayer=r['bayer'].split('-')[0], con=r['con'], nazwa=r['proper']))
    return gw

def gwiazdy(gw, rodzic):
    mt = material_gwiazd()
    V, F, UV, J, K = [], [], [], [], []
    for s in gw:
        p = eq(s['ra'], s['dec'])
        n = p.normalized()
        u = n.cross(Vector((0, 0, 1)))
        if u.length < 1e-6:
            u = Vector((1, 0, 0))
        u.normalize(); v = n.cross(u)
        m = s['mag']
        fwhm = 1.7 + 0.85 * max(0.0, 6.0 - m)                 # piksele
        h = fwhm * PX_M                                        # połowa boku = FWHM
        szczyt = 1.4 * (10 ** (-0.4 * (m - 1.0))) ** 0.5
        b = len(V)
        for a, c in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            V.append(p + u * (a * h) + v * (c * h))
        UV += [(0, 0), (1, 0), (1, 1), (0, 1)]
        F.append((b, b + 1, b + 2, b + 3))
        J += [szczyt] * 4
        kk = kolor_bv(s['ci'])
        K += [(*kk, 1.0)] * 4
    me = bpy.data.meshes.new('gwiazdy'); me.from_pydata([tuple(x) for x in V], [], F)
    uvl = me.uv_layers.new(name='UVMap')
    uvl.data.foreach_set('uv', np.array([UV[li] for li in [l.vertex_index for l in me.loops]]).ravel())
    a = me.attributes.new('jas', 'FLOAT', 'POINT'); a.data.foreach_set('value', J)
    c = me.attributes.new('kolor', 'FLOAT_COLOR', 'POINT'); c.data.foreach_set('color', np.array(K).ravel())
    me.materials.append(mt)
    ob = bpy.data.objects.new('gwiazdy', me); ob.parent = rodzic
    bpy.context.scene.collection.objects.link(ob)
    print('GWIAZD', len(gw))
    return ob

def krzywa(nazwa, punkty, grubosc, mt, rodzic, kol):
    cu = bpy.data.curves.new(nazwa, 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = grubosc; cu.bevel_resolution = 2
    cu.bevel_factor_mapping_end = 'SPLINE'
    sp = cu.splines.new('POLY'); sp.points.add(len(punkty) - 1)
    for i, p in enumerate(punkty):
        sp.points[i].co = (p.x, p.y, p.z, 1)
    cu.materials.append(mt)
    ob = bpy.data.objects.new(nazwa, cu); ob.parent = rodzic; kol.objects.link(ob)
    return ob

def slady(gw, osie, kol):
    """Ślady gwiazd wokół bieguna: łuki rysowane w układzie z chwili początkowej."""
    obrot0 = bpy.data.objects.new('slady_uklad', None); obrot0.parent = osie
    obrot0.rotation_euler = (0, 0, -math.radians(L0 * 15)); kol.objects.link(obrot0)
    dL = (_TAB[K_SLADY] - L0) * 15
    wyb = [s for s in gw if s['dec'] > 18 and s['mag'] < 4.7]
    mats = {}
    obs = []
    for i, s in enumerate(wyb):
        kk = kolor_bv(s['ci'])
        key = tuple(round(x, 1) for x in kk) + (round(min(1.0, 1.5 * 10 ** (-0.4 * (s['mag'] - 1.5))), 1),)
        if key not in mats:
            mats[key] = material_zanikajacy(f'slad_{len(mats)}', kk, 0.25 + 1.3 * key[3])
        pkt = [eq(s['ra'] - (dL * t / 60) / 15 * 1.0, s['dec'], R_NIEBA * 0.995) for t in np.linspace(0, 60, 61)]
        ob = krzywa(f'slad_{i}', pkt, PX_M * (0.45 + 0.35 * key[3]), mats[key], obrot0, kol)
        obs.append(ob)
    # wzrost śladu zgodnie z obrotem nieba
    for f in range(1, NKL + 1, 2):
        t = min(1.0, (_TAB[f] - L0) * 15 / dL)
        for ob in obs:
            ob.data.bevel_factor_end = max(0.0005, t)
        for ob in obs:
            ob.data.keyframe_insert('bevel_factor_end', frame=f)
    for mt in mats.values():
        animuj_widac(mt, [(1, 0.0), (12, 1.0), (K_SLADY - 10, 1.0), (K_SLADY + 60, 0.0)])
    print('SLADOW', len(obs))

# figury gwiazdozbiorów (oznaczenia Bayera w HYG): łamane
FIGURY = {
    'Leo': ('Lew', [['Eps', 'Mu', 'Zet', 'Gam', 'Eta', 'Alp'], ['Gam', 'Del', 'Bet', 'The', 'Alp'], ['Del', 'The']]),
    'Cnc': ('Rak', [['Iot', 'Gam', 'Del', 'Bet'], ['Del', 'Alp']]),
    'Gem': ('Bliźnięta', [['Alp', 'Tau', 'Eps', 'Mu', 'Eta'], ['Tau', 'Iot', 'Ups', 'Bet'], ['Ups', 'Del', 'Zet', 'Gam'], ['Del', 'Lam']]),
    'Vir': ('Panna', [['Bet', 'Eta', 'Gam', 'Alp'], ['Gam', 'Del', 'Eps'], ['Del', 'Zet', 'Alp']]),
    'Tau': ('Byk', [['Zet', 'Alp', 'The', 'Gam', 'Del', 'Eps', 'Bet']]),
}
KOLEJNOSC = [('Leo', 345), ('Cnc', 365), ('Gem', 385), ('Vir', 400), ('Tau', 400)]
# przesunięcie podpisu względem środka figury (stopnie RA, Dec)
PODPIS = {'Leo': (0.0, -8.0), 'Cnc': (0.0, -6.5), 'Gem': (0.5, -8.5), 'Vir': (0.0, 9.0), 'Tau': (0.0, 9.0)}

def gwiazdozbiory(gw, obrot, kol):
    idx = {}
    for s in gw:
        if s['bayer']:
            k = (s['con'], s['bayer'])
            if k not in idx or s['mag'] < idx[k]['mag']:
                idx[k] = s
    for con, start in KOLEJNOSC:
        nazwa, linie = FIGURY[con]
        mt = material_zanikajacy(f'linie_{con}', ZLOTY, 1.6)
        pts_all = []
        for j, ln in enumerate(linie):
            pk = [idx[(con, b)] for b in ln if (con, b) in idx]
            if len(pk) != len(ln):
                print('BRAK GWIAZDY', con, ln)
            pts = []
            for a, b in zip(pk, pk[1:]):
                pa, pb = eq(a['ra'], a['dec']).normalized(), eq(b['ra'], b['dec']).normalized()
                for t in np.linspace(0, 1, 12):        # odcinek po wielkim kole
                    pts.append(pa.slerp(pb, t) * R_NIEBA * 0.99 if hasattr(pa, 'slerp') else (pa * (1 - t) + pb * t).normalized() * R_NIEBA * 0.99)
            krzywa(f'linia_{con}_{j}', pts, PX_M * 0.9, mt, obrot, kol)
            pts_all += pk
        animuj_widac(mt, [(1, 0.0), (start, 0.0), (start + 25, 0.85)])
        # podpis
        ra = sum(s['ra'] for s in pts_all) / len(pts_all); de = sum(s['dec'] for s in pts_all) / len(pts_all)
        dra, dde = PODPIS[con]
        napis(nazwa, eq(ra + dra / 15, de + dde, R_NIEBA * 0.985), obrot, kol, start + 8)

KAM_CEL = None

def napis(tekst, poz, rodzic, kol, start, rozmiar=34, font=FONT):
    cu = bpy.data.curves.new('napis_' + tekst, 'FONT'); cu.body = tekst
    cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.size = rozmiar * PX_M; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    mt = material_zanikajacy('napis_' + tekst, ZLOTY, 1.3)
    cu.materials.append(mt)
    ob = bpy.data.objects.new('napis_' + tekst, cu); ob.parent = rodzic; ob.location = poz
    kol.objects.link(ob)
    tr = ob.constraints.new('TRACK_TO'); tr.target = KAM_CEL; tr.track_axis = 'TRACK_Z'; tr.up_axis = 'UP_Y'
    animuj_widac(mt, [(1, 0.0), (start, 0.0), (start + 25, 1.0)])
    return ob, mt

def ekliptyka(obrot, kol):
    mt = material_zanikajacy('ekliptyka', ZLOTY, 0.9)
    pts = []
    for lam in np.linspace(0, 2 * math.pi, 361):
        v = Vector((math.cos(lam), math.sin(lam) * math.cos(OBLIQ), math.sin(lam) * math.sin(OBLIQ))) * R_NIEBA * 0.992
        pts.append(v)
    ob = krzywa('ekliptyka', pts, PX_M * 0.7, mt, obrot, kol)
    animuj_widac(mt, [(1, 0.0), (318, 0.0), (350, 0.75)])
    # podpis „ekliptyka” przy Lambda ok. 75° (między Bykiem a Bliźniętami, nad nią)
    lam = math.radians(127)
    v = Vector((math.cos(lam), math.sin(lam) * math.cos(OBLIQ), math.sin(lam) * math.sin(OBLIQ)))
    ra = math.degrees(math.atan2(v.y, v.x)) / 15; de = math.degrees(math.asin(v.z))
    napis('ekliptyka', eq(ra + 0.5, de + 3.0, R_NIEBA * 0.985), obrot, kol, 330, rozmiar=26)

def biegun(obrot, kol):
    mt = material_zanikajacy('biegun', ZLOTY, 1.0)
    pts = [eq(h, 89.0, R_NIEBA * 0.99) for h in np.linspace(0, 24, 49)]
    krzywa('biegun_krag', pts, PX_M * 0.6, mt, obrot, kol)
    animuj_widac(mt, [(1, 0.0), (40, 0.0), (70, 0.8), (K_SLADY - 10, 0.8), (K_SLADY + 40, 0.0)])
    ob, m2 = napis('biegun niebieski', eq(0, 84.2, R_NIEBA * 0.985), obrot, kol, 45, rozmiar=26)
    animuj_widac(m2, [(1, 0.0), (45, 0.0), (70, 1.0), (K_SLADY - 10, 1.0), (K_SLADY + 40, 0.0)])

# ---------------------------------------------------------------- krajobraz
def sylwetki(kol):
    mt = bpy.data.materials.new('sylwetka'); bs = mt.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (0.004, 0.005, 0.008, 1); bs.inputs['Roughness'].default_value = 1.0
    bs.inputs['Specular IOR Level'].default_value = 0.0
    def box(bm, x0, x1, y0, y1, z0, z1):
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)))
    def walec(bm, cx, cy, r, z0, z1, seg=48):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=z1 - z0,
                              matrix=Matrix.Translation((cx, cy, (z0 + z1) / 2)))
    # El Caracol: dolna platforma 67 × 52 m, taras 26 × 30 m, okrągła wieża (16 m u podstawy), razem ok. 22,5 m
    cx, cy = 0.0, 118.0
    bm = bmesh.new()
    box(bm, cx - 33.5, cx + 33.5, cy - 26, cy + 26, 0, 6.0)
    box(bm, cx - 13, cx + 13, cy - 15, cy + 15, 6.0, 10.5)
    # schody od zachodu (bok sylwetki)
    for i in range(10):
        box(bm, cx - 33.5 - 6 + i * 0.6, cx - 33.5, cy - 10, cy + 10, 0, 0.6 * (i + 1))
    walec(bm, cx, cy, 8.0, 10.5, 13.8)             # okrągły cokół
    walec(bm, cx, cy, 8.4, 13.8, 14.3)             # gzyms
    walec(bm, cx, cy, 5.6, 14.3, 18.6)             # wieża
    walec(bm, cx, cy, 6.0, 18.6, 19.1)             # gzyms
    me = bpy.data.meshes.new('El_Caracol'); bm.to_mesh(me); bm.free()
    me.materials.append(mt)
    kol.objects.link(bpy.data.objects.new('El_Caracol', me))
    # górna komora obserwacyjna: zachowana tylko od zachodu i południa, szczyt skośnie urwany (do ok. 22,5 m)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=3.9, radius2=3.6, depth=3.8,
                          matrix=Matrix.Translation((cx, cy, 19.1 + 1.9)))
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(cx + 0.4, cy, 21.2), plane_no=(0.55, 0.35, 0.76), clear_outer=True)
    bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=0)
    me = bpy.data.meshes.new('El_Caracol_ruina'); bm.to_mesh(me); bm.free(); me.materials.append(mt)
    kol.objects.link(bpy.data.objects.new('El_Caracol_ruina', me))

    # El Castillo (Kukulkan): podstawa 55 m, 9 tarasów, 24 m + świątynia 6 m; ok. 410 m na NNE od Caracola
    kx, ky = cx + 156.0, cy + 376.0
    bm = bmesh.new()
    for k in range(9):
        w0 = 55.3 - k * (55.3 - 19.5) / 9
        box(bm, kx - w0 / 2, kx + w0 / 2, ky - w0 / 2, ky + w0 / 2, k * 24.0 / 9, (k + 1) * 24.0 / 9)
    box(bm, kx - 6.5, kx + 6.5, ky - 6.5, ky + 6.5, 24.0, 30.0)
    me = bpy.data.meshes.new('El_Castillo'); bm.to_mesh(me); bm.free(); me.materials.append(mt)
    kol.objects.link(bpy.data.objects.new('El_Castillo', me))

    # grunt i linia lasu na horyzoncie (niski las Jukatanu, 10–16 m)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6000)
    me = bpy.data.meshes.new('grunt'); bm.to_mesh(me); bm.free(); me.materials.append(mt)
    kol.objects.link(bpy.data.objects.new('grunt', me))
    rnd = random.Random(5)
    bm = bmesh.new()
    for i in range(1400):
        a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(420, 1400)
        x, y = d * math.sin(a), d * math.cos(a)
        if abs(x - kx) < 60 and abs(y - ky) < 60:
            continue
        r = rnd.uniform(5, 9)
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r,
                                   matrix=Matrix.Translation((x, y, rnd.uniform(6, 11))) @ Matrix.Diagonal((1, 1, 0.75, 1)))
    for i in range(160):     # bliższe drzewa przy placu
        a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(150, 400)
        x, y = d * math.sin(a), d * math.cos(a)
        if abs(x - kx) < 60 and abs(y - ky) < 60:
            continue
        if abs(a) < 0.5 or abs(a - 2 * math.pi) < 0.5:
            continue
        r = rnd.uniform(4, 7)
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r,
                                   matrix=Matrix.Translation((x, y, rnd.uniform(5, 9))) @ Matrix.Diagonal((1, 1, 0.8, 1)))
    me = bpy.data.meshes.new('las'); bm.to_mesh(me); bm.free(); me.materials.append(mt)
    kol.objects.link(bpy.data.objects.new('las', me))

def swiat(sc):
    """Tło nieba: granat jak plansze filmu (#05070c w zenicie, #1b2a4d przy horyzoncie)."""
    w = bpy.data.worlds.new('noc'); sc.world = w
    nt = w.node_tree; bg = nt.nodes.get('Background')
    tc = wezel(nt, 'ShaderNodeTexCoord', (-900, 0))
    sep = wezel(nt, 'ShaderNodeSeparateXYZ', (-700, 0)); lacz(nt, tc.outputs['Generated'], sep.inputs[0])
    nrm = wezel(nt, 'ShaderNodeVectorMath', (-700, -200), operation='NORMALIZE'); lacz(nt, tc.outputs['Generated'], nrm.inputs[0])
    sep2 = wezel(nt, 'ShaderNodeSeparateXYZ', (-500, -200)); lacz(nt, nrm.outputs[0], sep2.inputs[0])
    mr = wezel(nt, 'ShaderNodeMapRange', (-300, -200)); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.55
    lacz(nt, sep2.outputs['Z'], mr.inputs['Value'])
    pw = wezel(nt, 'ShaderNodeMath', (-150, -200), operation='POWER'); pw.inputs[1].default_value = 0.6
    lacz(nt, mr.outputs['Result'], pw.inputs[0])
    cr = wezel(nt, 'ShaderNodeValToRGB', (0, -200))
    cr.color_ramp.elements[0].color = (*srgb('#1b2a4d'), 1); cr.color_ramp.elements[1].color = (*srgb('#05070c'), 1)
    lacz(nt, pw.outputs[0], cr.inputs['Fac'])
    lacz(nt, cr.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.0

def kamera(sc):
    cd = bpy.data.cameras.new('kamera'); cd.lens = LENS; cd.clip_start = 0.5; cd.clip_end = 20000
    co = bpy.data.objects.new('kamera', cd); sc.collection.objects.link(co); sc.camera = co
    co.location = (0, 0, OKO)
    az0, alt0 = 0.0, 24.0
    az1, alt1 = 86.0, 47.0
    for f in range(1, NKL + 1):
        t = gladko((f - K_PAN[0]) / (K_PAN[1] - K_PAN[0]))
        az = az0 + (az1 - az0) * t; alt = alt0 + (alt1 - alt0) * t
        co.rotation_euler = (math.radians(90 + alt), 0, math.radians(-az)); co.keyframe_insert('rotation_euler', frame=f)
    return co

def ustawienia(sc):
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 1920; sc.render.resolution_y = 1080; sc.render.resolution_percentage = 100
    sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = NKL
    sc.eevee.taa_render_samples = 32
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.exposure = 0.0
    sc.render.image_settings.file_format = 'PNG'
    tree = bpy.data.node_groups.new('kompozycja', 'CompositorNodeTree')
    sc.compositing_node_group = tree
    tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = tree.nodes.new('CompositorNodeRLayers')
    gl = tree.nodes.new('CompositorNodeGlare')
    gl.inputs['Type'].default_value = 'Bloom'
    gl.inputs['Threshold'].default_value = 0.9
    gl.inputs['Strength'].default_value = 0.45
    gl.inputs['Size'].default_value = 0.45
    out = tree.nodes.new('NodeGroupOutput')
    tree.links.new(rl.outputs['Image'], gl.inputs['Image']); tree.links.new(gl.outputs['Image'], out.inputs[0])

def renderuj(sc):
    os.makedirs(KLATKI, exist_ok=True)
    if TRYB == 'test':
        return
    if TRYB == 'probne':
        for f in [int(k) for k in (ARGS[1] if len(ARGS) > 1 else '1,200,330,420,500').split(',')]:
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
    global KAM_CEL
    wyczysc()
    sc = bpy.context.scene
    kol = bpy.data.collections.new('Niebo'); sc.collection.children.link(kol)
    KAM_CEL = bpy.data.objects.new('oko', None); KAM_CEL.location = (0, 0, OKO); kol.objects.link(KAM_CEL)
    osie = bpy.data.objects.new('osie_rownikowe', None); kol.objects.link(osie)
    osie.matrix_world = Matrix.Translation((0, 0, OKO)) @ macierz_osi()
    obrot = bpy.data.objects.new('obrot_nieba', None); obrot.parent = osie; kol.objects.link(obrot)
    for f in range(1, NKL + 1):
        obrot.rotation_euler = (0, 0, -math.radians(_TAB[f] * 15)); obrot.keyframe_insert('rotation_euler', frame=f)
    gw = wczytaj()
    gwiazdy(gw, obrot)
    slady(gw, osie, kol)
    gwiazdozbiory(gw, obrot, kol)
    ekliptyka(obrot, kol)
    biegun(obrot, kol)
    sylwetki(kol)
    swiat(sc)
    kamera(sc)
    ustawienia(sc)
    renderuj(sc)

main()
