# -*- coding: utf-8 -*-
"""Niebo w dowolnej epoce: ruch własny gwiazd, precesja, położenie Słońca. Bez bpy – działa też poza Blenderem.

Import w scena.py (po dodaniu _wspolne do sys.path):
    import epoka as E
    JD = E.jd_jul(-1321, 7, 19)                # 19 lipca 1322 r. p.n.e. (rok astronomiczny -1321), kalendarz juliański
    gw = E.wczytaj(JD)                         # jak niebo.wczytaj(), ale położenia na datę JD (równonoc i epoka daty)

Wzory:
- precesja: kąty ζ, z, θ według IAU 1976 (J. Meeus, „Astronomical Algorithms”, wyd. 2, wzory 21.2–21.4);
  dla dat odległych o 2–4 tys. lat błąd jest rzędu minut kątowych,
- ruch własny: przesunięcie wektora kierunku o μ·t (μ z katalogu Hipparcos przez HYG), bez prędkości radialnej;
  dla Syriusza po 3300 latach daje to 1,2°,
- Słońce: wzory niskiej dokładności Meeusa (rozdz. 25): średnia długość, równanie środka, nachylenie ekliptyki daty.
Kontrola (16.11.2026): z tych wzorów wschód heliakalny Syriusza w Memfis w 139 r. n.e. wypada 20–21 lipca,
czyli tak, jak podaje Cenzoryn („De die natali”, 238 r.); patrz AUDYT.md.
"""
import math, os, csv

DANE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_dane")
KATALOG = os.path.join(DANE, "hyg", "gwiazdy_mag6_ruch.csv")
J2000 = 2451545.0
MAS = math.radians(1.0 / 3600000.0)


def jd_greg(rok, mies, dzien, godz=0.0):
    """Dzień juliański dla daty kalendarza gregoriańskiego."""
    if mies <= 2:
        rok -= 1
        mies += 12
    a = rok // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (rok + 4716)) + math.floor(30.6001 * (mies + 1)) + dzien + b - 1524.5 + godz / 24.0


def jd_jul(rok, mies, dzien, godz=0.0):
    """Dzień juliański dla daty kalendarza juliańskiego (rok astronomiczny: 1 r. p.n.e. = 0, 1322 r. p.n.e. = -1321)."""
    if mies <= 2:
        rok -= 1
        mies += 12
    return math.floor(365.25 * (rok + 4716)) + math.floor(30.6001 * (mies + 1)) + dzien - 1524.5 + godz / 24.0


def precesja(ra_h, dec_deg, JD):
    """Współrzędne J2000 -> równonoc daty JD. Zwraca (ra [h], dec [°])."""
    T = (JD - J2000) / 36525.0
    zeta = math.radians((2306.2181 * T + 0.30188 * T * T + 0.017998 * T ** 3) / 3600.0)
    z = math.radians((2306.2181 * T + 1.09468 * T * T + 0.018203 * T ** 3) / 3600.0)
    th = math.radians((2004.3109 * T - 0.42665 * T * T - 0.041833 * T ** 3) / 3600.0)
    a, d = math.radians(ra_h * 15.0), math.radians(dec_deg)
    A = math.cos(d) * math.sin(a + zeta)
    B = math.cos(th) * math.cos(d) * math.cos(a + zeta) - math.sin(th) * math.sin(d)
    C = math.sin(th) * math.cos(d) * math.cos(a + zeta) + math.cos(th) * math.sin(d)
    return (math.degrees(math.atan2(A, B) + z) % 360.0) / 15.0, math.degrees(math.asin(max(-1.0, min(1.0, C))))


def ruch_wlasny(ra_h, dec_deg, pmra_mas, pmdec_mas, lat):
    """Położenie J2000 po `lat` latach od epoki 2000.0 (ujemne = przeszłość). pmra zawiera już cos(dec)."""
    a, d = math.radians(ra_h * 15.0), math.radians(dec_deg)
    p = (math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d))
    e = (-math.sin(a), math.cos(a), 0.0)                                       # jednostkowy na wschód
    n = (-math.sin(d) * math.cos(a), -math.sin(d) * math.sin(a), math.cos(d))  # jednostkowy na północ
    ma, md = pmra_mas * MAS * lat, pmdec_mas * MAS * lat
    x, y, z = (p[i] + e[i] * ma + n[i] * md for i in range(3))
    return (math.degrees(math.atan2(y, x)) % 360.0) / 15.0, math.degrees(math.atan2(z, math.hypot(x, y)))


def na_date(ra_h, dec_deg, pmra_mas, pmdec_mas, JD):
    """Położenie katalogowe (J2000, epoka 2000.0) -> równonoc i epoka daty JD."""
    lat = (JD - J2000) / 365.25
    return precesja(*ruch_wlasny(ra_h, dec_deg, pmra_mas, pmdec_mas, lat), JD)


def wczytaj(JD, mag_max=6.0):
    """Lista gwiazd jak w niebo.wczytaj(), z położeniami przeliczonymi na datę JD."""
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
            ra, dec = na_date(float(r["ra_h"]), float(r["dec_deg"]), float(r["pmra_mas"] or 0), float(r["pmdec_mas"] or 0), JD)
            gw.append(dict(ra=ra, dec=dec, mag=m, ci=ci, bayer=r["bayer"].split("-")[0], con=r["con"], nazwa=r["proper"]))
    return gw


def slonce(JD):
    """Słońce: (ra [h], dec [°], długość ekliptyczna [°]) dla równonocy daty (Meeus, rozdz. 25, niska dokładność)."""
    T = (JD - J2000) / 36525.0
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    M = math.radians(357.52911 + 35999.05029 * T - 0.0001537 * T * T)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M) + (0.019993 - 0.000101 * T) * math.sin(2 * M)
         + 0.000289 * math.sin(3 * M))
    lam = math.radians((L0 + C) % 360.0)
    eps = math.radians(23.4392911 - (46.8150 * T + 0.00059 * T * T - 0.001813 * T ** 3) / 3600.0)
    ra = math.degrees(math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))) % 360.0
    return ra / 15.0, math.degrees(math.asin(math.sin(eps) * math.sin(lam))), math.degrees(lam)


def wys_az(ra_h, dec_deg, lst_h, szer_deg):
    """Wysokość i azymut (od północy przez wschód) w stopniach, bez refrakcji."""
    H = math.radians((lst_h - ra_h) * 15.0)
    d, f = math.radians(dec_deg), math.radians(szer_deg)
    wys = math.asin(math.sin(f) * math.sin(d) + math.cos(f) * math.cos(d) * math.cos(H))
    az = math.atan2(-math.cos(d) * math.sin(H), math.sin(d) * math.cos(f) - math.cos(d) * math.cos(H) * math.sin(f))
    return math.degrees(wys), math.degrees(az) % 360.0


def lst_dla_wysokosci(ra_h, dec_deg, szer_deg, wys_deg, wschod=True):
    """Czas gwiazdowy [h], w którym ciało ma daną wysokość po wschodniej (wschod=True) albo zachodniej stronie nieba."""
    d, f, a = math.radians(dec_deg), math.radians(szer_deg), math.radians(wys_deg)
    cH = (math.sin(a) - math.sin(f) * math.sin(d)) / (math.cos(f) * math.cos(d))
    H = math.degrees(math.acos(max(-1.0, min(1.0, cH)))) / 15.0
    return (ra_h - H) % 24.0 if wschod else (ra_h + H) % 24.0
