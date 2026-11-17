# -*- coding: utf-8 -*-
"""Zaćmienie Słońca z elementów Bessela – czysty Python (math), bez Blendera.

Dane wejściowe: wielomianowe elementy Bessela NASA (Fred Espenak, „Five Millennium Canon of Solar Eclipses”):
x, y (położenie osi cienia na płaszczyźnie podstawowej, w promieniach równikowych Ziemi), d (deklinacja osi),
mu (kąt godzinny osi w Greenwich, w czasie efemeryd), l1, l2 (promień półcienia i cienia na płaszczyźnie
podstawowej), tan f1, tan f2 (kąty stożków), t0 (godzina TDT, od której liczy się t), ΔT.

Wzory: Jean Meeus, „Elements of Solar Eclipses 1951–2200” (Willmann-Bell 1989), rozdz. o linii środkowej,
i „Explanatory Supplement to the Astronomical Almanac” (1992), rozdz. 8 – te same, których używa NASA.
Elipsoida Ziemi: spłaszczenie 1/298,257 (e² = 0,00669438), promień równikowy 6378,14 km.

Układ „ziemski” (taki jak w _wspolne/globus.py): środek Ziemi w 0, z = biegun północny, x = południk 0°
na równiku, y = 90°E na równiku; jednostka = promień równikowy Ziemi.
"""
import math, re

E2 = 0.00669438            # kwadrat mimośrodu elipsoidy
B_A = 0.99664719           # b/a = 1 - f
R_KM = 6378.14             # promień równikowy [km]
OBR = 0.00417807           # stopnie obrotu Ziemi na sekundę czasu (15°/h * 1,002738 / 3600)
R_SLONCA = 696000.0 / R_KM  # promień Słońca w promieniach Ziemi (109,12)


def _wiel(c, t):
    return sum(a * t ** i for i, a in enumerate(c))


def _poch(c, t):
    return sum(i * a * t ** (i - 1) for i, a in enumerate(c) if i > 0)


def _zloty(f, a, b, tol=1e-7):
    """Minimum funkcji jednej zmiennej metodą złotego podziału."""
    g = (math.sqrt(5) - 1) / 2
    c, d = b - g * (b - a), a + g * (b - a)
    fc, fd = f(c), f(d)
    while abs(b - a) > tol:
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - g * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a)
            fd = f(d)
    return (a + b) / 2


class Zacmienie:
    def __init__(self, x, y, d, mu, l1, l2, tan_f1, tan_f2, t0, delta_t, k1=0.272488, k2=0.272281, nazwa=""):
        self.cx, self.cy, self.cd, self.cmu, self.cl1, self.cl2 = x, y, d, mu, l1, l2
        self.tan_f1, self.tan_f2, self.t0, self.dt, self.k1, self.k2, self.nazwa = tan_f1, tan_f2, t0, delta_t, k1, k2, nazwa

    # ------------------------------------------------------------ elementy w chwili t (godziny TDT)
    def el(self, t):
        s = t - self.t0
        return dict(x=_wiel(self.cx, s), y=_wiel(self.cy, s), d=math.radians(_wiel(self.cd, s)), mu=_wiel(self.cmu, s),
                    l1=_wiel(self.cl1, s), l2=_wiel(self.cl2, s), dx=_poch(self.cx, s), dy=_poch(self.cy, s),
                    dmu=math.radians(_poch(self.cmu, s)), dd=math.radians(_poch(self.cd, s)))

    def ut(self, t):
        """Czas uniwersalny (godziny) dla godziny TDT."""
        return t - self.dt / 3600.0

    def kat_godzinny_osi(self, t):
        """Kąt godzinny osi cienia w Greenwich [°] po poprawce na ΔT (rzeczywisty obrót Ziemi)."""
        return self.el(t)["mu"] - OBR * self.dt

    # ------------------------------------------------------------ układ podstawowy -> ziemski
    def osie(self, t):
        """Wersory układu podstawowego (i = wschód, j = północ, k = ku Słońcu) w układzie ziemskim."""
        e = self.el(t)
        m, d = math.radians(self.kat_godzinny_osi(t)), e["d"]
        i = (math.sin(m), math.cos(m), 0.0)
        j = (-math.sin(d) * math.cos(m), math.sin(d) * math.sin(m), math.cos(d))
        k = (math.cos(d) * math.cos(m), -math.cos(d) * math.sin(m), math.sin(d))
        return i, j, k

    def na_ziemski(self, t, xi, eta, zeta):
        i, j, k = self.osie(t)
        return tuple(xi * i[n] + eta * j[n] + zeta * k[n] for n in range(3))

    def punkt_podsloneczny(self, t):
        """Szerokość i długość (wsch.) punktu, nad którym Słońce stoi w zenicie [°]."""
        e = self.el(t)
        lon = (-self.kat_godzinny_osi(t) + 180.0) % 360.0 - 180.0
        return math.degrees(e["d"]), lon

    def ksiezyc(self, t):
        """Środek Księżyca w układzie ziemskim [promienie Ziemi] i jego odległość od płaszczyzny podstawowej."""
        e = self.el(t)
        sin_f1 = self.tan_f1 / math.sqrt(1 + self.tan_f1 ** 2)
        zm = e["l1"] / self.tan_f1 - self.k1 / sin_f1        # wierzchołek stożka półcienia leży k1/sin f1 za Księżycem
        return self.na_ziemski(t, e["x"], e["y"], zm), zm

    def slonce(self, t):
        """Środek Słońca w układzie ziemskim [promienie Ziemi] (na osi cienia, za Księżycem)."""
        m, zm = self.ksiezyc(t)
        sin_f1 = self.tan_f1 / math.sqrt(1 + self.tan_f1 ** 2)
        g = (R_SLONCA + self.k1) / sin_f1                    # odległość Słońce–Księżyc
        k = self.osie(t)[2]
        return tuple(m[n] + g * k[n] for n in range(3))

    # ------------------------------------------------------------ linia środkowa (Meeus)
    def os_cienia(self, t):
        """Punkt, w którym oś cienia przebija powierzchnię Ziemi w chwili t. None, gdy oś mija Ziemię."""
        e = self.el(t)
        x, y, d = e["x"], e["y"], e["d"]
        om = 1.0 / math.sqrt(1.0 - E2 * math.cos(d) ** 2)
        p = e["dmu"]
        b = e["dy"] - p * x * math.sin(d)
        c = e["dx"] + p * y * math.sin(d)
        y1 = om * y
        b1 = om * math.sin(d)
        b2 = B_A * om * math.cos(d)
        B2 = 1.0 - x * x - y1 * y1
        if B2 < 0:
            return None
        B = math.sqrt(B2)
        fi1 = math.asin(B * b1 + y1 * b2)
        H = math.atan2(x, B * b2 - y1 * b1)
        fi = math.atan(1.00336409 * math.tan(fi1))
        lon = (math.degrees(H) - self.kat_godzinny_osi(t) + 180.0) % 360.0 - 180.0
        L1 = e["l1"] - B * self.tan_f1
        L2 = e["l2"] - B * self.tan_f2
        a = c - p * B * math.cos(d)
        n = math.hypot(a, b)
        trwanie = 7200.0 * abs(L2) / n
        sin_h = math.sin(d) * math.sin(fi) + math.cos(d) * math.cos(fi) * math.cos(H)
        K = math.sqrt(B * B + ((x * a + y * b) / n) ** 2)
        szer = 2 * R_KM * abs(L2) / K
        az = math.degrees(math.atan2(-math.cos(d) * math.sin(H),
                                     math.sin(d) * math.cos(fi) - math.cos(d) * math.cos(H) * math.sin(fi))) % 360.0
        return dict(lat=math.degrees(fi), lon=lon, wys=math.degrees(math.asin(sin_h)), az=az, szer_km=szer,
                    trwanie_s=trwanie, stosunek=(L1 - L2) / (L1 + L2), L1=L1, L2=L2, B=B, predkosc=n)

    # ------------------------------------------------------------ obserwator
    def obserwator(self, t, lat, lon, wys_m=0.0):
        """Okoliczności w miejscu (szer., dł. wsch. w stopniach) w chwili t."""
        e = self.el(t)
        d = e["d"]
        fi = math.radians(lat)
        u1 = math.atan(B_A * math.tan(fi))
        rs = B_A * math.sin(u1) + wys_m / (R_KM * 1000.0) * math.sin(fi)
        rc = math.cos(u1) + wys_m / (R_KM * 1000.0) * math.cos(fi)
        H = math.radians(self.kat_godzinny_osi(t) + lon)
        xi = rc * math.sin(H)
        eta = rs * math.cos(d) - rc * math.cos(H) * math.sin(d)
        zeta = rs * math.sin(d) + rc * math.cos(H) * math.cos(d)
        u, v = e["x"] - xi, e["y"] - eta
        L1 = e["l1"] - zeta * self.tan_f1
        L2 = e["l2"] - zeta * self.tan_f2
        D = math.hypot(u, v)
        faza = (L1 - D) / (L1 + L2)                 # wielkość zaćmienia (część średnicy Słońca)
        sin_h = math.sin(d) * math.sin(fi) + math.cos(d) * math.cos(fi) * math.cos(H)
        az = math.degrees(math.atan2(-math.cos(d) * math.sin(H),
                                     math.sin(d) * math.cos(fi) - math.cos(d) * math.cos(H) * math.sin(fi))) % 360.0
        return dict(u=u, v=v, D=D, L1=L1, L2=L2, faza=faza, stosunek=(L1 - L2) / (L1 + L2), zeta=zeta,
                    wys=math.degrees(math.asin(sin_h)), az=az, H=math.degrees(H), xyz=(xi, eta, zeta))

    def zakrycie(self, t, lat, lon):
        """Zakryta część tarczy Słońca (pole), 0..1."""
        o = self.obserwator(t, lat, lon)
        return zakrycie_tarcz(2 * o["D"] / (o["L1"] + o["L2"]), o["stosunek"])

    def okolicznosci(self, lat, lon, t_a=None, t_b=None):
        """Maksimum i kontakty zaćmienia całkowitego w miejscu: t_max, faza, C2, C3 (godziny TDT) albo None."""
        t_a = self.t0 - 3 if t_a is None else t_a
        t_b = self.t0 + 3 if t_b is None else t_b
        f = lambda t: self.obserwator(t, lat, lon)["D"]
        tm = min((t_a + (t_b - t_a) * i / 200 for i in range(201)), key=f)
        tm = _zloty(f, tm - 0.05, tm + 0.05, 1e-8)
        o = self.obserwator(tm, lat, lon)
        wyn = dict(t_max=tm, faza=o["faza"], wys=o["wys"], az=o["az"], c2=None, c3=None)
        g = lambda t: (lambda q: q["D"] - abs(q["L2"]))(self.obserwator(t, lat, lon))
        if g(tm) < 0:
            for znak, klucz in ((-1, "c2"), (1, "c3")):
                a, b = tm, tm + znak * 0.2
                for _ in range(60):
                    m = (a + b) / 2
                    if g(m) < 0:
                        a = m
                    else:
                        b = m
                wyn[klucz] = (a + b) / 2
        return wyn

    # ------------------------------------------------------------ największe zaćmienie
    def maksimum(self):
        f = lambda t: math.hypot(self.el(t)["x"], self.el(t)["y"])
        t = _zloty(f, self.t0 - 2, self.t0 + 2, 1e-9)
        e = self.el(t)
        return t, math.copysign(f(t), e["y"])

    def zakres_osi(self):
        """Godziny TDT, w których oś cienia przebija Ziemię (początek i koniec linii środkowej)."""
        tm, _ = self.maksimum()
        wyn = []
        for znak in (-1, 1):
            a, b = tm, tm + znak * 3.0
            for _ in range(60):
                m = (a + b) / 2
                if self.os_cienia(m) is not None:
                    a = m
                else:
                    b = m
            wyn.append(a)
        return tuple(wyn)

    # ------------------------------------------------------------ granice pasa całkowitości
    def czas_nad_dlugoscia(self, lon, t_a, t_b):
        """Chwila, w której linia środkowa przecina południk lon (bisekcja; długość rośnie z czasem w środku toru)."""
        def r(t):
            return (self.os_cienia(t)["lon"] - lon + 180.0) % 360.0 - 180.0
        a, b = t_a, t_b
        if r(a) * r(b) > 0:
            return None
        for _ in range(60):
            m = (a + b) / 2
            if r(a) * r(m) <= 0:
                b = m
            else:
                a = m
        return (a + b) / 2

    def _min_odstep(self, lat, lon, tc):
        """Najmniejsza w czasie różnica: odległość miejsca od osi minus promień cienia (ujemna = zaćmienie całkowite)."""
        g = lambda t: (lambda q: q["D"] - abs(q["L2"]))(self.obserwator(t, lat, lon))
        t = _zloty(g, tc - 0.25, tc + 0.25, 1e-7)
        return g(t)

    def granica(self, lon, strona, t_a, t_b):
        """Szerokość północnej (strona=+1) lub południowej (-1) granicy pasa całkowitości na południku lon."""
        tc = self.czas_nad_dlugoscia(lon, t_a, t_b)
        if tc is None:
            return None
        lat_c = self.os_cienia(tc)["lat"]
        a, b = lat_c, lat_c + strona * 4.0
        if self._min_odstep(b, lon, tc) < 0:
            return None
        for _ in range(40):
            m = (a + b) / 2
            if self._min_odstep(m, lon, tc) < 0:
                a = m
            else:
                b = m
        return (a + b) / 2


def zakrycie_tarcz(s, A):
    """Pole tarczy Słońca (promień 1) zakryte przez tarczę Księżyca (promień A), gdy środki dzieli odległość s.
    Wynik jako ułamek pola tarczy Słońca."""
    if s >= 1 + A:
        return 0.0
    if s <= abs(A - 1):
        return 1.0 if A >= 1 else A * A
    a1 = math.acos(max(-1.0, min(1.0, (s * s + 1 - A * A) / (2 * s))))
    a2 = math.acos(max(-1.0, min(1.0, (s * s + A * A - 1) / (2 * s * A))))
    pole = a1 + A * A * a2 - 0.5 * math.sqrt(max(0.0, (-s + 1 + A) * (s + 1 - A) * (s - 1 + A) * (s + 1 + A)))
    return pole / math.pi


# ---------------------------------------------------------------- wczytanie danych NASA
def z_tablicy_nasa(sciezka_html, nazwa=""):
    """Elementy z archiwalnej strony NASA „SEsearchmap.php” (tablica JavaScript `elements`):
    JD, t0, tmin, tmax, ΔT, x0..x3, y0..y3, d0..d2, mu0..mu2, l1_0..2, l2_0..2, tan f1, tan f2."""
    with open(sciezka_html, encoding="utf-8", errors="replace") as f:
        s = f.read()
    m = re.search(r"var elements = new Array\(([^)]*)\)", s)
    v = [float(a) for a in m.group(1).split(",")]
    return Zacmienie(x=v[5:9], y=v[9:13], d=v[13:16], mu=v[16:19], l1=v[19:22], l2=v[22:25], tan_f1=v[25], tan_f2=v[26],
                     t0=v[1], delta_t=v[4], nazwa=nazwa), dict(jd=v[0], tmin=v[2], tmax=v[3])


def tor_nasa(sciezka_html):
    """Punkty toru z tej samej strony NASA: słownik {'N': [(lat, lon), ...], 'S': [...], 'C': [...]}."""
    with open(sciezka_html, encoding="utf-8", errors="replace") as f:
        s = f.read()
    wyn = {}
    for lit in "NSC":
        m = re.search(r"var polyline%s = new GPolyline\(\[(.*?)\]" % lit, s, re.S)
        wyn[lit] = [(float(a), float(b)) for a, b in re.findall(r"GLatLng\(\s*([-\d.]+),\s*([-\d.]+)\)", m.group(1))]
    return wyn


def z_tabeli_bessela(sciezka_html, nazwa=""):
    """Elementy ze statycznej strony NASA „SE....beselm.html” (zaćmienia z lat 1901–2100)."""
    with open(sciezka_html, encoding="utf-8", errors="replace") as f:
        s = re.sub(r"<[^>]*>", "", f.read())
    w = {}
    for n in range(4):
        m = re.search(r"^\s*%d((?:\s+-?\d+\.\d+)+)\s*$" % n, s, re.M)
        w[n] = [float(a) for a in m.group(1).split()]
    t0 = float(re.search(r"(\d+):00:00\.0 TDT\s+\(=t0\)", s).group(1))
    dt = float(re.search(r"T =\s+([\d.]+) s", s).group(1))
    tf = re.search(r"Tan[^=]*1 = ([\d.]+)\s+Tan[^=]*2 = ([\d.]+)", s)
    return Zacmienie(x=[w[0][0], w[1][0], w[2][0], w[3][0]], y=[w[0][1], w[1][1], w[2][1], w[3][1]],
                     d=[w[0][2], w[1][2], w[2][2]], l1=[w[0][3], w[1][3], w[2][3]], l2=[w[0][4], w[1][4], w[2][4]],
                     mu=[w[0][5], w[1][5]], tan_f1=float(tf.group(1)), tan_f2=float(tf.group(2)), t0=t0, delta_t=dt,
                     nazwa=nazwa)


def tabela_toru_nasa(sciezka_html):
    """Wiersze statycznej tabeli toru NASA „SE....path.html”: UT [h], granica N, granica S, linia środkowa
    (szer., dł. wsch.), stosunek średnic, wysokość Słońca, szerokość pasa [km], czas trwania [s]."""
    with open(sciezka_html, encoding="utf-8", errors="replace") as f:
        s = re.sub(r"<[^>]*>", "", f.read())

    def kat(st, mi, lit):
        v = int(st) + float(mi) / 60.0
        return -v if lit in "SW" else v
    wz = re.compile(r"^\s*(\d\d):(\d\d)\s+" + r"\s+".join([r"(\d+) ([\d.]+)([NS])\s+(\d+) ([\d.]+)([EW])"] * 3)
                    + r"\s+([\d.]+)\s+(\d+)\s+(\S+)\s+(\d+)\s+(\d+)m([\d.]+)s", re.M)
    wyn = []
    for m in wz.finditer(s):
        g = m.groups()
        p = [(kat(*g[2 + 6 * i:5 + 6 * i]), kat(*g[5 + 6 * i:8 + 6 * i])) for i in range(3)]
        wyn.append(dict(ut=int(g[0]) + int(g[1]) / 60.0, N=p[0], S=p[1], C=p[2], stosunek=float(g[20]), wys=int(g[21]),
                        szer_km=int(g[23]), trwanie_s=int(g[24]) * 60 + float(g[25])))
    return wyn


def hms(godz):
    s = int(round(godz * 3600))
    return "%02d:%02d:%02d" % (s // 3600 % 24, s // 60 % 60, s % 60)
