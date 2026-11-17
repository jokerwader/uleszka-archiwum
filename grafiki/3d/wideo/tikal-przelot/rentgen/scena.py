# -*- coding: utf-8 -*-
"""
Tikal „rentgen”: próba stylu cyfrowej rekonstrukcji (jak skan lidarowy i model w filmach dokumentalnych).

Uruchomienie (bez okna); bez argumentów pełny render do ../klip.mp4 (z blokadą .renderuje):
  S:\\Blender\\blender.exe -b --factory-startup --python grafiki/3d/wideo/tikal-przelot/rentgen/scena.py -- probne 1,45,150,270,400 blekit
  ... -- probne 45,400 zloto

Geometria budowli (położenia, wymiary, tarasy) pochodzi wprost z ../scena.py (funkcja miasto), więc jest taka sama
jak w zaakceptowanym klipie `tikal-przelot`. Tu zmienia się tylko sposób pokazania:
  * tło: granat filmu, bez nieba,
  * budowle: półprzezroczyste bryły (świecenie addytywne, jaśniejsze przy krawędziach brył) i świecące krawędzie
    o stałej grubości na ekranie (Geometry Nodes: krawędzie -> rurki skalowane odległością od kamery),
  * wnętrza: komory świątyń na szczytach, grobowiec pod Świątynią I, starsze budowle i grobowce w Akropolu Północnym,
  * dżungla i teren: chmura punktów jak ze skanu lidarowego (korony drzew i punkty gruntu),
  * linia skanu jedzie ze wschodu na zachód i odsłania budowle,
  * na końcu złoty trójkąt Świątyń IV, I i V (kąt przy Świątyni I ok. 91°).

Układ współrzędnych: x = wschód, y = północ, z = góra, metry. (0,0) = środek Placu Głównego.
"""
import bpy, math, os, sys, time, subprocess
import numpy as np
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

TU = os.path.dirname(os.path.abspath(__file__))
BAZA_DIR = os.path.dirname(TU)
sys.path.insert(0, os.path.join(BAZA_DIR, '..', '_wspolne'))
import globus as G
from wezly import Wezly

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
TRYB = ARGS[0] if ARGS else 'pelny'
KLATKI_PROBNE = [int(k) for k in (ARGS[1] if len(ARGS) > 1 else '1,45,150,270,400').split(',')]
WARIANT = ARGS[2] if len(ARGS) > 2 else 'blekit'      # 'blekit' (wybrany) albo 'zloto'
KLATKI = os.path.join(BAZA_DIR, '_klatki', 'rentgen')   # folder _klatki klipu jest ignorowany przez git
NKL = 400
RNG = np.random.default_rng(11)

# geometria z klipu bazowego: wykonujemy jego definicje bez wywołania main()
_zr = open(os.path.join(BAZA_DIR, 'scena.py'), encoding='utf-8').read()
_zr = _zr[:_zr.rindex('\nmain()')]
_argv = sys.argv; sys.argv = sys.argv[:1]               # baza czyta własne argumenty: nie przekazujemy naszych
B = {'__file__': os.path.join(BAZA_DIR, 'scena.py'), '__name__': 'tikal_baza'}
exec(compile(_zr, os.path.join(BAZA_DIR, 'scena.py'), 'exec'), B)
sys.argv = _argv
B['schody'].__defaults__ = (1.5, True)                  # w „rentgenie” stopnie schodów co 1,5 m (inaczej zlewają się w plamę)
B['piramida'].__defaults__ = (False, False)             # tarasy jako pojedyncze bryły, bez narożnych uskoków i gzymsów (czystszy rysunek)

# ---------------------------------------------------------------- kolory wariantów
ZLOTY = (240, 196, 111)
if WARIANT == 'zloto':
    KOL_BRYLA, KOL_KRAW, KOL_WNETRZE = (224, 170, 86), ZLOTY, (255, 244, 214)
else:
    KOL_BRYLA, KOL_KRAW, KOL_WNETRZE = (70, 150, 240), (128, 200, 255), ZLOTY
KOL_SKAN = (190, 240, 255)
KOL_KORONY = (56, 120, 170)
KOL_GRUNT = (88, 150, 215)

# linia skanu: położenie x (m) w klatkach; na wschód od linii wszystko jest już „zeskanowane”
SKAN = [(1, -38.0), (45, -84.0), (150, -300.0), (262, -770.0), (NKL, -1300.0)]
KAMERA = [  # klatka, położenie kamery, punkt, na który patrzy
    (1,   (24, -16, 5.5),     (-54, 2, 21)),
    (140, (62, -64, 30),      (-112, 32, 20)),
    (255, (128, -118, 44),    (10, 2, 6)),          # niski przelot obok Świątyni I: grobowiec widać pod piramidą
    (NKL, (330, -520, 330),   (-180, -90, -25)),
]
KADR = 258
T_I, T_IV, T_V = (52.0, -1.0), (-662.0, 163.0), (-6.0, -283.0)   # trójkąt z cytatu


def interp(pkt, f):
    for (f0, v0), (f1, v1) in zip(pkt, pkt[1:]):
        if f0 <= f <= f1:
            return v0 + (v1 - v0) * (f - f0) / (f1 - f0)
    return pkt[0][1] if f < pkt[0][0] else pkt[-1][1]


# ---------------------------------------------------------------- materiały (wszystkie świecą addytywnie)
MAT_SKAN = []     # materiały z węzłem 'skan' (położenie linii skanu)


def _dodaj(nt, W, kolor_sila):
    """Wyjście: Transparent + suma emisji [(kolor, siła), ...] (addytywnie, kolejność rysowania nie ma znaczenia)."""
    out = W._node('ShaderNodeOutputMaterial')
    suma = W._node('ShaderNodeBsdfTransparent').outputs[0]
    for kolor, sila in kolor_sila:
        em = W._node('ShaderNodeEmission')
        em.inputs['Color'].default_value = G.srgb(kolor)
        W._in(em.inputs['Strength'], sila)
        ad = W._node('ShaderNodeAddShader')
        nt.links.new(suma, ad.inputs[0]); nt.links.new(em.outputs[0], ad.inputs[1])
        suma = ad.outputs[0]
    nt.links.new(suma, out.inputs['Surface'])


def _skan(W):
    """(odsłonięcie 0..1, pasek linii skanu 0..1) z położenia punktu w świecie."""
    x, _, _ = W.sep(W.geometria('Position'))
    dx = W.sub(x, W.wartosc(1e5, 'skan'))
    return W.smooth(0.0, 14.0, dx), W.sub(1.0, W.smooth(0.0, 5.0, W.math('ABSOLUTE', dx)))


def material(nazwa, kolor, lico, brzeg, pasek=0.5, potega=2.0):
    """Bryła „rentgenowska”: słabe świecenie lica + mocniejsze tam, gdzie powierzchnia jest widziana pod ostrym kątem."""
    m = bpy.data.materials.new(nazwa); nt = m.node_tree; nt.nodes.clear()
    W = Wezly(nt)
    ods, pas = _skan(W)
    lw = W._node('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    sila = W.mul(W.add(lico, W.mul(W.math('POWER', lw.outputs['Facing'], potega), brzeg)), ods)
    _dodaj(nt, W, [(kolor, sila), (KOL_SKAN, W.mul(pas, pasek))])
    m.surface_render_method = 'BLENDED'
    MAT_SKAN.append(m)
    return m


def material_punktow(nazwa, kolor, przed, po, pasek):
    """Punkty skanu: jasność z atrybutu 'jas'; 'przed' i 'po' = jasność przed przejściem linii skanu i po nim."""
    m = bpy.data.materials.new(nazwa); nt = m.node_tree; nt.nodes.clear()
    W = Wezly(nt)
    ods, pas = _skan(W)
    at = W._node('ShaderNodeAttribute'); at.attribute_name = 'jas'
    jas = at.outputs['Factor']
    sila = W.mul(jas, W.add(przed, W.mul(ods, po - przed)))
    _dodaj(nt, W, [(kolor, sila), (KOL_SKAN, W.mul(W.mul(pas, pasek), jas))])
    m.surface_render_method = 'BLENDED'
    MAT_SKAN.append(m)
    return m


def material_linii(nazwa, kolor, sila=1.25):
    """Linia rysująca się od początku do końca: 'postep' 0..1 wzdłuż osi X obiektu (współrzędne Generated)."""
    m = bpy.data.materials.new(nazwa); nt = m.node_tree; nt.nodes.clear()
    W = Wezly(nt)
    gx, _, _ = W.sep(W.coord('Generated'))
    wid = W.sub(1.0, W.smooth(-0.004, 0.004, W.sub(gx, W.wartosc(0.0, 'postep'))))
    _dodaj(nt, W, [(kolor, W.mul(wid, sila))])
    m.surface_render_method = 'BLENDED'
    return m


# ---------------------------------------------------------------- Geometry Nodes
def grupa_krawedzi(mat, px=1.0, rmin=0.012, rmax=1.5):
    """Krawędzie siatki -> rurki o promieniu ok. px pikseli (skalowane odległością od kamery, ogniskowa 30 mm)."""
    ng = bpy.data.node_groups.new('krawedzie_' + mat.name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes.new; L = ng.links.new
    gi, go = N('NodeGroupInput'), N('NodeGroupOutput')
    m2c = N('GeometryNodeMeshToCurve')
    kam = N('GeometryNodeInputActiveCamera'); oi = N('GeometryNodeObjectInfo'); oi.transform_space = 'RELATIVE'
    L(kam.outputs[0], oi.inputs['Object'])
    odl = N('ShaderNodeVectorMath'); odl.operation = 'DISTANCE'
    L(N('GeometryNodeInputPosition').outputs[0], odl.inputs[0]); L(oi.outputs['Location'], odl.inputs[1])
    mn = N('ShaderNodeMath'); mn.operation = 'MULTIPLY'; mn.inputs[1].default_value = px / 1600.0
    L(odl.outputs['Value'], mn.inputs[0])
    cl = N('ShaderNodeClamp'); cl.inputs['Min'].default_value = rmin; cl.inputs['Max'].default_value = rmax
    L(mn.outputs[0], cl.inputs['Value'])
    okr = N('GeometryNodeCurvePrimitiveCircle'); okr.inputs['Resolution'].default_value = 4; okr.inputs['Radius'].default_value = 1.0
    c2m = N('GeometryNodeCurveToMesh')
    L(gi.outputs[0], m2c.inputs['Mesh']); L(m2c.outputs[0], c2m.inputs['Curve'])
    L(okr.outputs['Curve'], c2m.inputs['Profile Curve']); L(cl.outputs[0], c2m.inputs['Scale'])
    sm = N('GeometryNodeSetMaterial'); sm.inputs['Material'].default_value = mat
    L(c2m.outputs[0], sm.inputs['Geometry']); L(sm.outputs[0], go.inputs[0])
    return ng


def grupa_punktow(mat, px=0.9, rmin=0.05, rmax=1.6):
    """Wierzchołki siatki -> punkty o promieniu ok. px pikseli."""
    ng = bpy.data.node_groups.new('punkty_' + mat.name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes.new; L = ng.links.new
    gi, go = N('NodeGroupInput'), N('NodeGroupOutput')
    kam = N('GeometryNodeInputActiveCamera'); oi = N('GeometryNodeObjectInfo'); oi.transform_space = 'RELATIVE'
    L(kam.outputs[0], oi.inputs['Object'])
    odl = N('ShaderNodeVectorMath'); odl.operation = 'DISTANCE'
    L(N('GeometryNodeInputPosition').outputs[0], odl.inputs[0]); L(oi.outputs['Location'], odl.inputs[1])
    mn = N('ShaderNodeMath'); mn.operation = 'MULTIPLY'; mn.inputs[1].default_value = px / 1600.0
    L(odl.outputs['Value'], mn.inputs[0])
    cl = N('ShaderNodeClamp'); cl.inputs['Min'].default_value = rmin; cl.inputs['Max'].default_value = rmax
    L(mn.outputs[0], cl.inputs['Value'])
    m2p = N('GeometryNodeMeshToPoints')
    L(gi.outputs[0], m2p.inputs['Mesh']); L(cl.outputs[0], m2p.inputs['Radius'])
    sm = N('GeometryNodeSetMaterial'); sm.inputs['Material'].default_value = mat
    L(m2p.outputs[0], sm.inputs['Geometry']); L(sm.outputs[0], go.inputs[0])
    return ng


def dodaj_krawedzie(ob, grupa, kol):
    """Kopia obiektu (ta sama siatka) pokazująca tylko świecące krawędzie."""
    k = bpy.data.objects.new(ob.name + '_kraw', ob.data)
    k.matrix_world = ob.matrix_world.copy()
    k.location, k.rotation_euler, k.scale = ob.location, ob.rotation_euler, ob.scale
    kol.objects.link(k)
    mod = k.modifiers.new('krawedzie', 'NODES'); mod.node_group = grupa
    return k


# ---------------------------------------------------------------- wnętrza
def macierz(nazwa):
    ob = bpy.data.objects[nazwa]
    return Matrix.Translation(ob.location) @ Matrix.Rotation(ob.rotation_euler.z, 4, 'Z')


def wnetrza(kol, M):
    """Komory świątyń na szczytach, grobowiec pod Świątynią I, starsze budowle i grobowce Akropolu Północnego.
    Rozmiary komór są przybliżone, położenia grobowców schematyczne (patrz README)."""
    S = B['Siatka']()

    def komory(nazwa, yb0, H, ile, szer, gleb=1.1, wys=4.2):
        st = len(S.v)
        for i in range(ile):
            y0 = yb0 + 1.3 + i * (gleb + 1.25)
            w = szer * (1.0 - 0.16 * i)
            S.box(-w / 2, w / 2, y0, y0 + gleb, H + 0.35 * i, H + 0.35 * i + wys, 0.3)     # zwężenie ku górze = sklepienie pozorne
        S.przeksztalc_od(st, macierz(nazwa))

    # (nazwa obiektu, przód budynku w układzie świątyni, wysokość podłogi, liczba komór, szerokość pierwszej komory)
    komory('Swiatynia_I', -5.0, 30.8, 3, 6.2)
    komory('Swiatynia_II', -6.5, 21.0, 3, 7.5)
    komory('Swiatynia_III', -5.5, 37.0, 2, 6.0)
    komory('Swiatynia_IV', -7.5, 46.0, 3, 8.5)
    komory('Swiatynia_V', -3.5, 39.0, 1, 3.95, gleb=0.9, wys=4.4)     # jedna komora: 3,95 m szer., 0,9 m głęb., 4,4 m wys.
    # grobowiec Jasaw Chan K'awiila I (Pochówek 116): sklepiona komora w głębi piramidy, poniżej poziomu placu
    st = len(S.v)
    S.box(-2.3, 2.3, -1.3, 1.3, -6.8, -2.6, 0.45)
    S.przeksztalc_od(st, macierz('Swiatynia_I'))
    # Akropol Północny: grobowce pod świątyniami 33 (Pochówek 48), 34 (Pochówek 10), 32 (Pochówek 195) i 26 (Pochówek 85)
    for x, y in ((3.0, 63.0), (28.0, 63.0), (-22.0, 63.0), (3.0, 80.0)):
        S.box(x - 1.6, x + 1.6, y - 1.1, y + 1.1, -2.8, -0.5, 0.3)
    ob = S.obiekt('wnetrza_komory', [M['wnetrze']], kol)
    # Świątynia I: linia pionu od komór na szczycie do grobowca i tunel archeologów (1962) od stóp schodów do stropu grobowca
    S3 = B['Siatka']()
    S3.box(-0.2, 0.2, -0.2, 0.2, -2.6, 30.8)
    S3.pryzma_yz([(-18.5, 0.0), (-18.5, -0.7), (-1.3, -3.3), (-1.3, -2.6)], -0.35, 0.35)
    S3.przeksztalc_od(0, macierz('Swiatynia_I'))
    ob3 = S3.obiekt('wnetrza_linie', [M['starsze']], kol)

    # starsze, mniejsze budowle zamknięte w środku późniejszych (Akropol Północny rozbudowywano ok. 1300 lat)
    S2 = B['Siatka']()
    S2.box(-40, 46, 53, 108, 0, 6.4, 0.5)
    S2.box(-27, 33, 62, 100, 0, 3.6, 0.5)
    for bw, h, n in ((13.0, 8.0, 3), (8.0, 4.6, 2)):          # dwie wcześniejsze wersje świątyni 5D-33
        st = len(S2.v)
        B['piramida'](S2, bw, bw * 0.95, bw * 0.5, bw * 0.42, h, n, naroznik=False, gzyms=False)
        S2.przeksztalc_od(st, Matrix.Translation((3.0, 64.5, 9.0)))
    ob2 = S2.obiekt('wnetrza_starsze', [M['starsze']], kol)
    return ob, ob2, ob3


# ---------------------------------------------------------------- chmura punktów (dżungla i grunt)
def chmura(kol, M):
    wys, polana = B['wysokosc_terenu'], B['w_polanie']

    def obiekt(nazwa, P, jas, mat, px):
        me = bpy.data.meshes.new(nazwa)
        me.vertices.add(len(P)); me.vertices.foreach_set('co', P.astype(np.float32).ravel())
        a = me.attributes.new('jas', 'FLOAT', 'POINT'); a.data.foreach_set('value', jas.astype(np.float32))
        ob = bpy.data.objects.new(nazwa, me); kol.objects.link(ob)
        mod = ob.modifiers.new('punkty', 'NODES'); mod.node_group = grupa_punktow(mat, px=px)
        return ob

    def zanik(X, Y):
        """Jasność maleje ku brzegom zeskanowanego pasa (jak pas lotu samolotu ze skanerem)."""
        d = np.minimum(np.minimum(X + 1000, 520 - X), np.minimum(Y + 560, 520 - Y))
        return np.clip(d / 160.0, 0.0, 1.0)

    # korony drzew: siatka z rozrzutem, bez polan; na każde drzewo kilkanaście punktów na kopule korony i kilka na pniu
    krok = 9.0
    X, Y = np.meshgrid(np.arange(-1000, 520, krok), np.arange(-560, 520, krok))
    X = (X + RNG.uniform(-4, 4, X.shape)).ravel(); Y = (Y + RNG.uniform(-4, 4, Y.shape)).ravel()
    ok = ~polana(X, Y) & (RNG.random(X.shape) > 0.06)
    X, Y = X[ok], Y[ok]
    n = len(X); k = 13
    Z0 = wys(X, Y)
    H = RNG.uniform(19, 30, n) + (RNG.random(n) ** 6) * 14          # wysokość drzewa, czasem olbrzym
    R = RNG.uniform(3.8, 7.0, n)
    az = RNG.uniform(0, 2 * math.pi, (n, k)); u = RNG.uniform(0.0, 1.0, (n, k))
    el = np.arcsin(u)                                               # równomiernie na półkuli
    PX = X[:, None] + R[:, None] * np.cos(el) * np.cos(az)
    PY = Y[:, None] + R[:, None] * np.cos(el) * np.sin(az)
    PZ = (Z0 + H)[:, None] - R[:, None] * 0.9 + R[:, None] * 0.9 * np.sin(el)
    P = np.column_stack([PX.ravel(), PY.ravel(), PZ.ravel()])
    jas = (RNG.uniform(0.45, 1.0, n * k) * np.repeat(zanik(X, Y), k))
    obiekt('chmura_korony', P, jas, M['korony'], 1.0)
    print('DRZEW', n, 'PUNKTOW KORON', len(P))

    # grunt: gęsto na polanach (plac, akropole), rzadko pod lasem (mało impulsów dociera do ziemi)
    czesci = []
    for krok, obszar, rzadko in ((4.5, (-1000, 520, -560, 520), 0.45), (2.0, (-110, 260, -150, 130), 1.0)):
        X, Y = np.meshgrid(np.arange(obszar[0], obszar[1], krok), np.arange(obszar[2], obszar[3], krok))
        X = (X + RNG.uniform(-0.3, 0.3, X.shape) * krok).ravel(); Y = (Y + RNG.uniform(-0.3, 0.3, Y.shape) * krok).ravel()
        pol = polana(X, Y)
        ok = pol | (RNG.random(X.shape) < rzadko)
        if krok > 3:
            ok &= ~((X > -110) & (X < 260) & (Y > -150) & (Y < 130))
        X, Y, pol = X[ok], Y[ok], pol[ok]
        czesci.append((X, Y, pol))
    X = np.concatenate([c[0] for c in czesci]); Y = np.concatenate([c[1] for c in czesci]); pol = np.concatenate([c[2] for c in czesci])
    P = np.column_stack([X, Y, wys(X, Y)])
    jas = np.where(pol, 1.0, 0.6) * RNG.uniform(0.6, 1.0, len(X)) * zanik(X, Y)
    obiekt('chmura_grunt', P, jas, M['grunt'], 1.0)
    print('PUNKTOW GRUNTU', len(P))


# ---------------------------------------------------------------- linia skanu, trójkąt, napisy
def kurtyna_skanu(kol):
    """Pionowa, ledwo widoczna płaszczyzna skanu z jasną linią przy ziemi."""
    me = bpy.data.meshes.new('kurtyna')
    me.from_pydata([(0, -620, 0), (0, 560, 0), (0, 560, 110), (0, -620, 110)], [], [(0, 1, 2, 3)])
    m = bpy.data.materials.new('kurtyna'); nt = m.node_tree; nt.nodes.clear()
    W = Wezly(nt)
    _, _, z = W.sep(W.coord('Object'))
    prazki = W.smooth(0.55, 1.0, W.math('SINE', W.mul(z, 2 * math.pi / 3.0)))
    sila = W.add(W.mul(W.sub(1.0, W.smooth(0.0, 110.0, z)), 0.010),
                 W.mul(W.sub(1.0, W.smooth(0.0, 1.6, z)), 0.9))
    _dodaj(nt, W, [(KOL_SKAN, sila)])
    m.surface_render_method = 'BLENDED'
    me.materials.append(m)
    ob = bpy.data.objects.new('kurtyna', me); kol.objects.link(ob)
    for f in range(1, NKL + 1):
        ob.location = (interp(SKAN, f), 0, 0); ob.keyframe_insert('location', frame=f)
    return ob


def wstega(nazwa, a, b, szer, mat, kol, z=1.2):
    """Płaska wstęga na ziemi od punktu a do b (lokalna oś X wzdłuż linii)."""
    a, b = Vector((a[0], a[1], z)), Vector((b[0], b[1], z))
    dl = (b - a).length
    me = bpy.data.meshes.new(nazwa)
    me.from_pydata([(0, -szer / 2, 0), (dl, -szer / 2, 0), (dl, szer / 2, 0), (0, szer / 2, 0)], [], [(0, 1, 2, 3)])
    me.materials.append(mat)
    ob = bpy.data.objects.new(nazwa, me); kol.objects.link(ob)
    ob.location = a; ob.rotation_euler = (0, 0, math.atan2(b.y - a.y, b.x - a.x))
    return ob


def animuj(mat, nazwa, klucze):
    nd = mat.node_tree.nodes[nazwa]
    for f, v in klucze:
        nd.outputs[0].default_value = v; nd.outputs[0].keyframe_insert('default_value', frame=f)
    for fc in G._fcurves(mat.node_tree.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'


def trojkat(kol):
    """Złoty trójkąt Świątyń IV, I i V ze znakiem kąta prostego przy Świątyni I; rysuje się w klatkach 300–372."""
    I, IV, V = Vector(T_I), Vector(T_IV), Vector(T_V)
    for nazwa, a, b, k0, k1 in (('linia_I_IV', I, IV, 300, 338), ('linia_I_V', I, V, 318, 346), ('linia_IV_V', IV, V, 340, 372)):
        m = material_linii(nazwa + '_mat', ZLOTY)
        wstega(nazwa, a, b, 2.2, m, kol)
        animuj(m, 'postep', [(k0, 0.0), (k1, 1.0)])
    # znak kąta prostego: mały kwadrat przy Świątyni I
    e1, e2 = (IV - I).normalized(), (V - I).normalized()
    r = 30.0
    m = material_linii('kat_mat', ZLOTY)
    wstega('kat_1', I + e1 * r, I + e1 * r + e2 * r, 1.5, m, kol)
    wstega('kat_2', I + e2 * r, I + e2 * r + e1 * r, 1.5, m, kol)
    animuj(m, 'postep', [(346, 0.0), (358, 1.0)])


def napis(tekst, punkt, rozmiar, kolor, klucze, cam, kroj='georgiab', wyr='CENTER'):
    """Napis zwrócony zawsze do kamery; klucze = [(klatka, alfa), ...]."""
    ob = G.napis(tekst, rozmiar, kolor, kroj, wyr, loc=punkt, nazwa='napis_' + tekst[:12], alfa=0.0,
                 obrys=((4, 7, 16), rozmiar * 0.035), odstep=1.15)
    c = ob.constraints.new('COPY_ROTATION'); c.target = cam
    G.alfa_napisu(ob, klucze)
    return ob


# ---------------------------------------------------------------- scena
def kompozycja(sc):
    tree = bpy.data.node_groups.new('kompozycja', 'CompositorNodeTree')
    sc.compositing_node_group = tree
    tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = tree.nodes.new('CompositorNodeRLayers')
    gl = tree.nodes.new('CompositorNodeGlare')
    gl.inputs['Type'].default_value = 'Bloom'
    gl.inputs['Threshold'].default_value = 0.7
    gl.inputs['Strength'].default_value = 0.4
    gl.inputs['Size'].default_value = 0.55
    out = tree.nodes.new('NodeGroupOutput')
    tree.links.new(rl.outputs['Image'], gl.inputs['Image']); tree.links.new(gl.outputs['Image'], out.inputs[0])


def main():
    t0 = time.time()
    sc = G.nowa_scena(NKL, proba=True)
    kol = bpy.data.collections.new('Tikal_rentgen'); sc.collection.children.link(kol)
    M = {
        'kamien': material('bryla', KOL_BRYLA, 0.005, 0.05, pasek=0.05),
        'ciemny': material('wejscia', KOL_KRAW, 0.22, 0.25, pasek=0.2),
        'grobla': material('grobla', KOL_BRYLA, 0.03, 0.0, pasek=0.1),
        'krawedz': material('krawedz', KOL_KRAW, 0.55, 0.0, pasek=0.9),
        'krawedz_slaba': material('krawedz_slaba', KOL_BRYLA, 0.30, 0.0, pasek=0.6),
        'wnetrze': material('wnetrze', KOL_WNETRZE, 0.42, 0.5, pasek=0.3),
        'wnetrze_kraw': material('wnetrze_kraw', KOL_WNETRZE, 1.0, 0.0, pasek=0.3),
        'starsze': material('starsze', KOL_WNETRZE, 0.022, 0.10, pasek=0.2),
        'starsze_kraw': material('starsze_kraw', KOL_WNETRZE, 0.42, 0.0, pasek=0.2),
        'korony': material_punktow('korony', KOL_KORONY, 0.55, 0.30, 0.9),
        'grunt': material_punktow('grunt', KOL_GRUNT, 0.0, 0.95, 1.0),
    }
    # budowle z klipu bazowego (te same położenia i wymiary), w materiałach „rentgenowskich”
    B['miasto'](M, kol)
    budowle = list(kol.objects)
    ob_k, ob_s, ob_l = wnetrza(kol, M)
    # grobla Tozzera (droga od Placu do Świątyni IV): sam obrys
    S = B['Siatka']()
    ax, ay, bx, by = -80.0, 38.0, -628.0, 150.0
    S.box(0, math.hypot(bx - ax, by - ay), -9, 9, 0.0, 0.3)
    S.przeksztalc_od(0, Matrix.Translation((ax, ay, 0)) @ Matrix.Rotation(math.atan2(by - ay, bx - ax), 4, 'Z'))
    grobla = S.obiekt('grobla_Tozzera', [M['grobla']], kol)

    g_kraw, g_slaba = grupa_krawedzi(M['krawedz']), grupa_krawedzi(M['krawedz_slaba'], px=0.8)
    g_wn, g_st = grupa_krawedzi(M['wnetrze_kraw'], px=1.1), grupa_krawedzi(M['starsze_kraw'], px=0.8)
    for ob in budowle:
        dodaj_krawedzie(ob, g_kraw, kol)
    dodaj_krawedzie(ob_k, g_wn, kol)
    dodaj_krawedzie(ob_s, g_st, kol)
    dodaj_krawedzie(ob_l, g_wn, kol)
    dodaj_krawedzie(grobla, g_slaba, kol)
    chmura(kol, M)
    kurtyna_skanu(kol)
    trojkat(kol)

    # kamera jak w klipie bazowym, z wyższym zakończeniem (żeby zmieścił się trójkąt IV–I–V)
    cd = bpy.data.cameras.new('kamera'); cd.lens = 30; cd.clip_start = 1.0; cd.clip_end = 40000
    cam = bpy.data.objects.new('kamera', cd); sc.collection.objects.link(cam); sc.camera = cam
    cel = bpy.data.objects.new('cel', None); sc.collection.objects.link(cel)
    tr = cam.constraints.new('TRACK_TO'); tr.target = cel; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
    for f, p, c in KAMERA:
        cam.location = p; cam.keyframe_insert('location', frame=f)
        cel.location = c; cel.keyframe_insert('location', frame=f)
    G.tlo_kamery(cam, odl=20000)

    # linia skanu w materiałach
    for m in MAT_SKAN:
        nd = m.node_tree.nodes['skan']
        for f in range(1, NKL + 1):
            nd.outputs[0].default_value = interp(SKAN, f); nd.outputs[0].keyframe_insert('default_value', frame=f)

    # napisy (zawsze przodem do kamery, z ciemnym obrysem; wysoko nad budowlami, żeby nie ginęły w liniach)
    bialy = (232, 238, 248)
    # położenia i czasy dobrane tak, żeby napis był cały w kadrze przez cały czas widoczności (kamera jest w ruchu)
    napis('Świątynia II', (-54, 0, 46.0), 4.6, bialy, [(4, 0.0), (20, 1.0), (178, 1.0), (196, 0.0)], cam, 'arialb')
    napis('trzy komory na szczycie', (-54, 0, 41.8), 3.0, ZLOTY, [(36, 0.0), (52, 1.0), (178, 1.0), (196, 0.0)], cam, 'arialb')
    napis('Akropol Północny', (-20, 62, 40), 6.0, bialy, [(112, 0.0), (128, 1.0), (198, 1.0), (212, 0.0)], cam, 'arialb', 'RIGHT')
    napis('w środku starsze budowle\ni grobowce władców', (-20, 62, 31.5), 3.7, ZLOTY, [(118, 0.0), (134, 1.0), (198, 1.0), (212, 0.0)],
          cam, 'arialb', 'RIGHT')
    napis('Świątynia I', (73, 20, 31), 6.4, bialy, [(246, 0.0), (258, 1.0), (286, 1.0), (298, 0.0)], cam, 'arialb')
    napis('grobowiec władcy,\nodkryty tunelem w 1962 r.', (76, 23, -10), 4.2, ZLOTY,
          [(254, 0.0), (266, 1.0), (286, 1.0), (298, 0.0)], cam, 'arialb')
    for tekst, (x, y), z, r in (('I', (T_I[0] + 52, T_I[1] + 60), 34, 40), ('IV', (T_IV[0] - 70, T_IV[1] - 84), 40, 66),
                                ('V', (T_V[0] - 46, T_V[1] - 54), 32, 31)):
        napis(tekst, (x, y, z), r, ZLOTY, [(338, 0.0), (358, 1.0)], cam)
    e = ((Vector(T_IV) - Vector(T_I)).normalized() + (Vector(T_V) - Vector(T_I)).normalized()).normalized() * 78.0
    napis('90°', (T_I[0] + e.x, T_I[1] + e.y, 70), 30, ZLOTY, [(352, 0.0), (368, 1.0)], cam, 'arialb')
    # napis ekranowy na początku: uczciwie, że to rekonstrukcja, a nie prawdziwy skan
    odl = 12.0
    s = G.skala_px(cam, odl)
    ob = G.napis('rekonstrukcja 3D w stylu skanu lidarowego', 34 * s, (150, 205, 240), 'arial', 'RIGHT', rodzic=cam,
                 loc=G.ekran_na_kamerze(cam, 1850, 70, odl), nazwa='napis_skan', alfa=0.0)
    G.alfa_napisu(ob, [(1, 0.9), (95, 0.9), (120, 0.0)])

    kompozycja(sc)
    print(f'SCENA {time.time() - t0:.1f}s')
    os.makedirs(KLATKI, exist_ok=True)
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
    if TRYB == 'probne':
        for f in KLATKI_PROBNE:
            t = time.time()
            sc.frame_set(f)
            if f == KLATKI_PROBNE[-1]:
                bpy.context.view_layer.update()
                for nazwa, (x, y) in (('I', T_I), ('IV', T_IV), ('V', T_V)):
                    c = world_to_camera_view(sc, cam, Vector((x, y, 0)))
                    print(f'EKRAN {nazwa} klatka {f}: {c.x * 1920:.0f} {(1 - c.y) * 1080:.0f}')
            sc.render.filepath = os.path.join(KLATKI, f'proba_{WARIANT}_{f:04d}.png')
            bpy.ops.render.render(write_still=True)
            print(f'PROBNA {WARIANT} {f} {time.time() - t:.1f}s')
        return
    # pełny render: klatki do ../_klatki/rentgen, wynik jako ../klip.mp4 i ../kadr.jpg (rentgen zastępuje wersję realistyczną)
    blok = os.path.join(G.WIDEO, '.renderuje')
    if os.path.exists(blok):
        raise SystemExit(f'[render] karta zajęta: {open(blok, encoding="utf-8", errors="replace").read().strip()}')
    with open(blok, 'w', encoding='utf-8') as fh:
        fh.write('tikal-przelot\n')
    t = time.time()
    try:
        for p in os.listdir(KLATKI):
            if p.startswith('k_') and p.endswith('.png'):
                os.remove(os.path.join(KLATKI, p))
        sc.eevee.taa_render_samples = 32
        sc.render.filepath = os.path.join(KLATKI, 'k_')
        bpy.ops.render.render(animation=True)
    finally:
        if os.path.exists(blok):
            os.remove(blok)
    dt = time.time() - t
    ff = G.ffmpeg_exe()
    mp4 = os.path.join(BAZA_DIR, 'klip.mp4')
    subprocess.run([ff, '-loglevel', 'error', '-y', '-framerate', '25', '-start_number', '1', '-i', os.path.join(KLATKI, 'k_%04d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow', '-an', '-movflags', '+faststart', mp4], check=True)
    subprocess.run([ff, '-loglevel', 'error', '-y', '-i', os.path.join(KLATKI, f'k_{KADR:04d}.png'), '-vf', 'scale=1600:-2',
                    '-q:v', '2', os.path.join(BAZA_DIR, 'kadr.jpg')], check=True)
    with open(os.path.join(KLATKI, 'czas_renderu.txt'), 'w', encoding='utf-8') as fh:
        fh.write(f'render {dt:.0f} s, klatek {NKL}\n')
    print(f'[render] tikal-przelot (rentgen): {dt:.0f} s, mp4: {mp4}')


main()
