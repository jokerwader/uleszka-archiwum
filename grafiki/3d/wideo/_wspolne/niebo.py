# -*- coding: utf-8 -*-
"""Gwiazdy (katalog HYG) i proste rachunki astronomiczne dla klipów z niebem.

Import w scena.py (po dodaniu _wspolne do sys.path):
    import globus as G
    import niebo as N

Układ horyzontalny scen: x = wschód, y = północ, z = zenit.
Układ równikowy: x = punkt Barana (rektascensja 0 h), z = biegun północny nieba.
Położenia gwiazd: epoka i równonoc J2000 (bez precesji i ruchów własnych).
Planety: średnie elementy orbit JPL (Standish, „Approximate Positions of the Planets”, ważne dla lat 1800–2050),
dokładność rzędu ułamka stopnia – do pokazania, gdzie planeta stoi na niebie, wystarcza.
"""
import bpy, math, os, csv
import numpy as np
from mathutils import Vector, Matrix
import globus as G

KATALOG = os.path.join(G.DANE, "hyg", "gwiazdy_mag6.csv")
OBLIQ = math.radians(23.43928)


# ---------------------------------------------------------------- rachunki
def jd(rok, mies, dzien, godz=0.0):
    """Dzień juliański (kalendarz gregoriański, czas uniwersalny)."""
    if mies <= 2:
        rok -= 1
        mies += 12
    a = rok // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (rok + 4716)) + math.floor(30.6001 * (mies + 1)) + dzien + b - 1524.5 + godz / 24.0


def czas_gwiazdowy(JD, dlug_wsch):
    """Miejscowy czas gwiazdowy w godzinach (długość geograficzna wschodnia w stopniach)."""
    T = (JD - 2451545.0) / 36525.0
    g = 280.46061837 + 360.98564736629 * (JD - 2451545.0) + 0.000387933 * T * T
    return ((g + dlug_wsch) % 360.0) / 15.0


_EL = {  # a, e, I, L, długość peryhelium, długość węzła; druga lista: zmiana na stulecie
    "merkury": ((0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593),
                (0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081)),
    "wenus": ((0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255),
              (0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418)),
    "ziemia": ((1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0),
               (0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0)),
    "mars": ((1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891),
             (0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343)),
    "jowisz": ((5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909),
               (-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106)),
    "saturn": ((9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448),
               (-0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794)),
}


def _helio(nazwa, T):
    e0, r = _EL[nazwa]
    a, e, I, L, w, O = [v + dv * T for v, dv in zip(e0, r)]
    om = math.radians(w - O)
    M = math.radians(((L - w) % 360 + 540) % 360 - 180)
    E = M
    for _ in range(30):
        E = M + e * math.sin(E)
    x, y = a * (math.cos(E) - e), a * math.sqrt(1 - e * e) * math.sin(E)
    O, I = math.radians(O), math.radians(I)
    co, so, cO, sO, cI, sI = math.cos(om), math.sin(om), math.cos(O), math.sin(O), math.cos(I), math.sin(I)
    return Vector(((co * cO - so * sO * cI) * x + (-so * cO - co * sO * cI) * y,
                   (co * sO + so * cO * cI) * x + (-so * sO + co * cO * cI) * y,
                   so * sI * x + co * sI * y))


def planeta(nazwa, JD):
    """Rektascensja [h] i deklinacja [°] planety widzianej z Ziemi; nazwa 'slonce' = Słońce."""
    T = (JD - 2451545.0) / 36525.0
    z = _helio("ziemia", T)
    v = -z if nazwa == "slonce" else _helio(nazwa, T) - z
    ce, se = math.cos(OBLIQ), math.sin(OBLIQ)
    x, y, zz = v.x, v.y * ce - v.z * se, v.y * se + v.z * ce
    return (math.degrees(math.atan2(y, x)) / 15.0) % 24.0, math.degrees(math.atan2(zz, math.hypot(x, y)))


def eq(ra_h, dec_deg, r=1.0):
    a, d = math.radians(ra_h * 15), math.radians(dec_deg)
    return Vector((math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d))) * r


def macierz_osi(szer_deg):
    """Macierz 3×3: układ równikowy przy czasie gwiazdowym 0 -> układ horyzontalny (x=E, y=N, z=zenit)."""
    f = math.radians(szer_deg)
    M = Vector((0, -math.sin(f), math.cos(f)))
    E = Vector((1, 0, 0))
    P = Vector((0, math.cos(f), math.sin(f)))
    return Matrix((M, E, P)).transposed()


def kierunek(ra_h, dec_deg, lst_h, szer_deg):
    """Wektor jednostkowy w układzie horyzontalnym dla gwiazdy o danych współrzędnych i czasie gwiazdowym."""
    return macierz_osi(szer_deg) @ (Matrix.Rotation(-math.radians(lst_h * 15), 3, "Z") @ eq(ra_h, dec_deg))


def wys_az(v):
    """Wysokość i azymut (stopnie, azymut od północy przez wschód) wektora w układzie horyzontalnym."""
    v = Vector(v).normalized()
    return math.degrees(math.asin(max(-1, min(1, v.z)))), math.degrees(math.atan2(v.x, v.y)) % 360


def z_wys_az(wys, az, r=1.0):
    a, z = math.radians(wys), math.radians(az)
    return Vector((math.cos(a) * math.sin(z), math.cos(a) * math.cos(z), math.sin(a))) * r


# ---------------------------------------------------------------- katalog
def wczytaj(mag_max=6.0):
    gw = []
    with open(KATALOG, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            m = float(r["mag"])
            if m > mag_max:
                continue
            try:
                ci = float(r["ci"])
            except ValueError:
                ci = 0.6
            gw.append(dict(ra=float(r["ra_h"]), dec=float(r["dec_deg"]), mag=m, ci=ci,
                           bayer=r["bayer"].split("-")[0], con=r["con"], nazwa=r["proper"]))
    return gw


def znajdz(gw, nazwa):
    for s in gw:
        if s["nazwa"] == nazwa:
            return s
    raise KeyError(nazwa)


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


# ---------------------------------------------------------------- obiekty
def material_gwiazd(nazwa="gwiazdy"):
    """Punkt o profilu Gaussa na kwadracie; jasność i kolor z atrybutów 'jas' i 'kolor'; węzeł 'widac' mnoży jasność."""
    mt = bpy.data.materials.new(nazwa)
    mt.use_nodes = True
    nt = mt.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    uv = nt.nodes.new("ShaderNodeUVMap")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs[0], sep.inputs[0])

    def m(op, a, b=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, x in enumerate((a, b)):
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            elif x is not None:
                nt.links.new(x, n.inputs[i])
        return n.outputs[0]
    dx, dy = m("SUBTRACT", sep.outputs["X"], 0.5), m("SUBTRACT", sep.outputs["Y"], 0.5)
    r2 = m("ADD", m("MULTIPLY", dx, dx), m("MULTIPLY", dy, dy))
    g = m("EXPONENT", m("MULTIPLY", r2, -11.09))
    okno = nt.nodes.new("ShaderNodeMapRange"); okno.interpolation_type = "SMOOTHSTEP"     # wygaszenie przy brzegu kwadratu
    okno.inputs["From Min"].default_value = 0.25; okno.inputs["From Max"].default_value = 0.10
    nt.links.new(r2, okno.inputs["Value"])
    g = m("MULTIPLY", g, okno.outputs["Result"])
    jas = nt.nodes.new("ShaderNodeAttribute"); jas.attribute_name = "jas"
    kol = nt.nodes.new("ShaderNodeAttribute"); kol.attribute_name = "kolor"
    wid = nt.nodes.new("ShaderNodeValue"); wid.name = "widac"; wid.outputs[0].default_value = 1.0
    s = m("MULTIPLY", m("MULTIPLY", g, jas.outputs["Fac"]), wid.outputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(kol.outputs["Color"], em.inputs["Color"])
    nt.links.new(s, em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    ad = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], ad.inputs[0])
    nt.links.new(em.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs["Surface"])
    try:
        mt.surface_render_method = "BLENDED"
    except Exception:
        pass
    return mt


def siatka_gwiazd(gw, R, kat_px, nazwa="gwiazdy", wzmocnienie=1.0, rozmiar=1.0, material=None):
    """Kwadraty-gwiazdy na sferze o promieniu R w układzie równikowym.
    kat_px: kąt (radiany) przypadający na piksel obrazu – od niego zależy rozmiar plamki.
    gw: lista słowników z ra [h], dec [°], mag, ci. Zwraca obiekt (bez rodzica)."""
    mt = material or material_gwiazd(nazwa)
    V, F, UV, J, K = [], [], [], [], []
    for s in gw:
        p = eq(s["ra"], s["dec"], R)
        n = p.normalized()
        u = n.cross(Vector((0, 0, 1)))
        if u.length < 1e-6:
            u = Vector((1, 0, 0))
        u.normalize()
        v = n.cross(u)
        mag = s["mag"]
        fwhm = (1.7 + 0.85 * max(0.0, 6.0 - mag)) * rozmiar
        h = fwhm * R * kat_px
        szczyt = wzmocnienie * 1.4 * (10 ** (-0.4 * (mag - 1.0))) ** 0.5
        b = len(V)
        for a, c in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            V.append(p + u * (a * h) + v * (c * h))
        UV += [(0, 0), (1, 0), (1, 1), (0, 1)]
        F.append((b, b + 1, b + 2, b + 3))
        J += [szczyt] * 4
        K += [(*kolor_bv(s.get("ci", 0.6)), 1.0)] * 4
    me = bpy.data.meshes.new(nazwa)
    me.from_pydata([tuple(x) for x in V], [], F)
    uvl = me.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", np.array([UV[l.vertex_index] for l in me.loops], dtype=np.float32).ravel())
    a = me.attributes.new("jas", "FLOAT", "POINT")
    a.data.foreach_set("value", J)
    c = me.attributes.new("kolor", "FLOAT_COLOR", "POINT")
    c.data.foreach_set("color", np.array(K, dtype=np.float32).ravel())
    me.materials.append(mt)
    ob = bpy.data.objects.new(nazwa, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.visible_shadow = False
    return ob


def niebo_obrotowe(szer_deg, srodek=(0, 0, 0)):
    """Dwa puste obiekty: 'osie' (układ równikowy przy czasie gwiazdowym 0) i 'obrot' (dziecko, obracane o czas gwiazdowy).
    Gwiazdy przypinaj do 'obrot'; ustaw_czas(obrot, lst_h) obraca niebo."""
    sc = bpy.context.scene
    osie = bpy.data.objects.new("osie_rownikowe", None)
    sc.collection.objects.link(osie)
    osie.matrix_world = Matrix.Translation(Vector(srodek)) @ macierz_osi(szer_deg).to_4x4()
    obrot = bpy.data.objects.new("obrot_nieba", None)
    obrot.parent = osie
    sc.collection.objects.link(obrot)
    return osie, obrot


def ustaw_czas(obrot, lst_h):
    obrot.rotation_euler = (0, 0, -math.radians(lst_h * 15))


def swiat_noc(horyzont=(27, 42, 77), zenit=(5, 7, 12), wykladnik=0.6, zasieg=0.55):
    """Tło świata: granat filmu, jaśniejszy przy horyzoncie. Zwraca węzeł ColorRamp (kolory można animować)."""
    sc = bpy.context.scene
    w = sc.world
    nt = w.node_tree
    bg = nt.nodes.get("Background")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nrm = nt.nodes.new("ShaderNodeVectorMath"); nrm.operation = "NORMALIZE"
    nt.links.new(tc.outputs["Generated"], nrm.inputs[0])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(nrm.outputs[0], sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = zasieg
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = wykladnik
    nt.links.new(mr.outputs["Result"], pw.inputs[0])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = G.srgb(horyzont)
    cr.color_ramp.elements[1].color = G.srgb(zenit)
    nt.links.new(pw.outputs[0], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    return cr


def poswiata(sc, prog=0.9, sila=0.45, rozmiar=0.45):
    """Delikatna poświata (bloom) w kompozytorze – jak w klipie niebo-gwiazdozbiory."""
    tree = bpy.data.node_groups.new("kompozycja", "CompositorNodeTree")
    sc.compositing_node_group = tree
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers")
    gl = tree.nodes.new("CompositorNodeGlare")
    gl.inputs["Type"].default_value = "Bloom"
    gl.inputs["Threshold"].default_value = prog
    gl.inputs["Strength"].default_value = sila
    gl.inputs["Size"].default_value = rozmiar
    out = tree.nodes.new("NodeGroupOutput")
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"])
    tree.links.new(gl.outputs["Image"], out.inputs[0])
    return gl
