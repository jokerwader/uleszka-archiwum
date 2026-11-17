# -*- coding: utf-8 -*-
"""Sprawdzenie obliczeń z bessel.py na danych NASA. Wynik: sprawdzenie.txt obok skryptu.

Uruchomienie (Python Blendera, bo w systemie nie ma innego):
  S:\\Blender\\5.3\\python\\bin\\python.exe grafiki/3d/wideo/zacmienie-slonca/sprawdz.py

1. Zaćmienie 11 VII 1991: NASA podaje i elementy Bessela, i gotową tabelę toru co minutę – porównujemy
   nasz rachunek z tabelą (linia środkowa, granice, szerokość pasa, czas trwania, wysokość Słońca).
2. Zaćmienie 16 VII 790 (to z klipu): porównujemy z punktami toru i okolicznościami największego zaćmienia,
   które NASA podaje na stronie tego zaćmienia.
"""
import math, os, sys

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TU)
import bessel as B

DANE = os.path.normpath(os.path.join(TU, "..", "_dane"))
wy = []


def pisz(s=""):
    wy.append(s)
    print(s)


def km(lat1, lon1, lat2, lon2):
    f1, f2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    a = math.sin((f2 - f1) / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


# ---------------------------------------------------------------- 1. rok 1991
z = B.z_tabeli_bessela(os.path.join(DANE, "zacmienie-1991", "nasa_SE1991Jul11Tbeselm.html"), "1991-07-11")
tab = B.tabela_toru_nasa(os.path.join(DANE, "zacmienie-1991", "nasa_SE1991Jul11Tpath.html"))
pisz("1. ZAĆMIENIE 11 LIPCA 1991 – nasz rachunek a tabela toru NASA (%d wierszy co minutę)" % len(tab))
tm, gam = z.maksimum()
pisz("   największe zaćmienie: %s TDT (NASA 19:07:00.8), gamma %.4f (NASA -0.0041)" % (B.hms(tm), gam))
ta, tb = z.zakres_osi()
pisz("   UT      linia środkowa (nasza)   NASA                różnica  szer. pasa  trwanie    wys. Słońca")
maks = dict(c=0.0, szer=0.0, trw=0.0, wys=0.0, n=0.0, s=0.0)
for i, w in enumerate(tab):
    t = w["ut"] + z.dt / 3600.0
    o = z.os_cienia(t)
    dc = km(o["lat"], o["lon"], *w["C"])
    gn = z.granica(w["N"][1], +1, ta + 0.02, tb - 0.02)
    gs = z.granica(w["S"][1], -1, ta + 0.02, tb - 0.02)
    dn = abs(gn - w["N"][0]) * 111.2 if gn is not None else None
    ds = abs(gs - w["S"][0]) * 111.2 if gs is not None else None
    srodek = 8 <= i < len(tab) - 8          # przy wschodzie i zachodzie Słońca tabela (zaokrąglona do 0,1') jest mniej czuła
    if srodek:
        maks["c"] = max(maks["c"], dc)
        maks["szer"] = max(maks["szer"], abs(o["szer_km"] - w["szer_km"]))
        maks["trw"] = max(maks["trw"], abs(o["trwanie_s"] - w["trwanie_s"]))
        maks["wys"] = max(maks["wys"], abs(o["wys"] - w["wys"]))
        if dn is not None:
            maks["n"] = max(maks["n"], dn)
        if ds is not None:
            maks["s"] = max(maks["s"], ds)
    if i % 20 == 10:
        pisz("   %s  %7.3f° %9.3f°   %7.3f° %9.3f°  %5.2f km  %3.0f/%3d km  %5.1f/%5.1f s  %4.1f/%2d°"
             % (B.hms(w["ut"])[:5], o["lat"], o["lon"], w["C"][0], w["C"][1], dc, o["szer_km"], w["szer_km"],
                o["trwanie_s"], w["trwanie_s"], o["wys"], w["wys"]))
pisz("   Największe różnice (bez 8 minut przy wschodzie i zachodzie): linia środkowa %.2f km, granica północna %.2f km,"
     % (maks["c"], maks["n"]))
pisz("   południowa %.2f km, szerokość pasa %.1f km, czas trwania %.1f s, wysokość Słońca %.1f°."
     % (maks["s"], maks["szer"], maks["trw"], maks["wys"]))
pisz("   (Tabela NASA podaje położenia z dokładnością 0,1', czyli ok. 0,2 km, szerokość do 1 km, wysokość do 1°.)")
pisz()

# ---------------------------------------------------------------- 2. rok 790
strona = os.path.join(DANE, "zacmienie-0790", "nasa_SEsearchmap_07900716.html")
z, meta = B.z_tablicy_nasa(strona, "0790-07-16")
tor = B.tor_nasa(strona)
pisz("2. ZAĆMIENIE 16 LIPCA 790 – nasz rachunek a dane NASA dla tego zaćmienia")
tm, gam = z.maksimum()
o = z.os_cienia(tm)
pisz("   wielkość                 nasz rachunek        NASA")
pisz("   największe zaćmienie     %s TDT         19:49:25 TDT" % B.hms(tm))
pisz("   w czasie uniwersalnym    %s UT          18:59:10 UT   (ΔT = %.1f s)" % (B.hms(z.ut(tm)), z.dt))
pisz("   gamma                    %.4f              -0.0525" % gam)
pisz("   szerokość geogr.         %.4f° N           18.0331° N" % o["lat"])
pisz("   długość geogr.           %.4f° W          104.1354° W" % -o["lon"])
pisz("   wysokość Słońca          %.1f°                87.1°" % o["wys"])
pisz("   azymut Słońca            %.1f°                 5.6°" % o["az"])
pisz("   szerokość pasa           %.1f km             100.5 km" % o["szer_km"])
pisz("   czas trwania             %dm%02ds               03m03s" % (o["trwanie_s"] // 60, round(o["trwanie_s"] % 60)))
ta, tb = z.zakres_osi()
pisz("   oś cienia na Ziemi od %s do %s TDT (%s–%s UT)" % (B.hms(ta), B.hms(tb), B.hms(z.ut(ta)), B.hms(z.ut(tb))))
pisz()
pisz("   Tor: punkty NASA co 0,5° długości (linia środkowa %d, granica N %d, granica S %d punktów)."
     % (len(tor["C"]), len(tor["N"]), len(tor["S"])))
pisz("   dł. geogr.   linia środkowa: nasza / NASA      granica N: nasza / NASA      granica S: nasza / NASA")
slow = {k: {round(lon, 3): lat for lat, lon in v} for k, v in tor.items()}
rozn = dict(C=[], N=[], S=[])
for lat, lon in tor["C"]:
    if abs(lon * 2 - round(lon * 2)) > 1e-6:
        continue                                           # punkty skrajne (początek i koniec toru) pomijamy
    tc = z.czas_nad_dlugoscia(lon, ta + 0.03, tb - 0.03)
    if tc is None:
        continue
    c = z.os_cienia(tc)["lat"]
    n = z.granica(lon, +1, ta + 0.03, tb - 0.03)
    s = z.granica(lon, -1, ta + 0.03, tb - 0.03)
    nn, ns = slow["N"].get(round(lon, 3)), slow["S"].get(round(lon, 3))
    rozn["C"].append((abs(c - lat) * 111.2, lon))
    if n is not None and nn is not None:
        rozn["N"].append((abs(n - nn) * 111.2, lon))
    if s is not None and ns is not None:
        rozn["S"].append((abs(s - ns) * 111.2, lon))
    if lon in (-150.0, -130.0, -110.0, -100.0, -95.0, -92.0, -90.0, -85.0, -75.0, -60.0):
        pisz("   %7.1f°      %8.4f° / %8.4f°          %8.4f° / %8.4f°         %8.4f° / %8.4f°"
             % (lon, c, lat, n if n is not None else float("nan"), nn if nn is not None else float("nan"),
                s if s is not None else float("nan"), ns if ns is not None else float("nan")))
for k, nazwa in (("C", "linia środkowa"), ("N", "granica północna"), ("S", "granica południowa")):
    r = rozn[k]
    wsr = [a for a, lon in r if -150 <= lon <= -50]
    pisz("   %s: %d punktów; największa różnica szerokości %.2f km (na całym torze), %.2f km (150°W–50°W)"
         % (nazwa, len(r), max(a for a, _ in r), max(wsr)))
pisz()

# ---------------------------------------------------------------- 3. miejsca Majów (rok 790)
pisz("3. MIEJSCA (16 lipca 790, rachunek z elementów NASA)")
MIEJSCA = [("Santa Elena Poco Uinic (stela 3)", 16.5875, -91.7390), ("Palenque", 17.4842, -92.0464),
           ("Toniná", 16.9012, -92.0097), ("Tikal", 17.2221, -89.6236), ("Copán", 14.838, -89.1424),
           ("Calakmul", 18.105, -89.8106), ("Chichén Itzá", 20.6831, -88.5686)]
for nazwa, la, lo in MIEJSCA:
    k = z.okolicznosci(la, lo)
    zak = z.zakrycie(k["t_max"], la, lo)
    lok = (z.ut(k["t_max"]) + lo / 15.0) % 24
    cal = ""
    if k["c2"] is not None:
        cal = ", całkowite przez %.0f s" % ((k["c3"] - k["c2"]) * 3600)
    pisz("   %-33s maksimum %s UT (%s średniego czasu słonecznego), faza %.3f, zakryte %.1f%% tarczy, Słońce %2.0f° nad horyzontem%s"
         % (nazwa, B.hms(z.ut(k["t_max"])), B.hms(lok)[:5], k["faza"], zak * 100, k["wys"], cal))
# odległość Poco Uinic od granicy pasa
la, lo = 16.5875, -91.7390
gn = z.granica(lo, +1, ta + 0.03, tb - 0.03)
pisz("   Północna granica pasa całkowitości na południku Poco Uinic: %.3f° N, czyli %.0f km na południe od steli."
     % (gn, (la - gn) * 111.2))
# o ile trzeba zmienić ΔT, żeby pas objął Poco Uinic
for dd in range(0, 4001, 20):
    z2 = B.Zacmienie(z.cx, z.cy, z.cd, z.cmu, z.cl1, z.cl2, z.tan_f1, z.tan_f2, z.t0, z.dt + dd)
    k = z2.okolicznosci(la, lo)
    if k["c2"] is not None:
        pisz("   Pas objąłby stelę dopiero przy ΔT większym o ok. %d s (ΔT ≈ %.0f s zamiast %.0f s)." % (dd, z.dt + dd, z.dt))
        break
pisz()
pisz("4. KSIĘŻYC I SŁOŃCE Z ELEMENTÓW (chwila największego zaćmienia)")
m, zm = z.ksiezyc(tm)
s = z.slonce(tm)
dm = math.sqrt(sum(a * a for a in m))
dsl = math.sqrt(sum(a * a for a in s))
pisz("   odległość Księżyca od środka Ziemi: %.2f promienia Ziemi = %.0f km" % (dm, dm * B.R_KM))
pisz("   odległość Słońca: %.0f promieni Ziemi = %.1f mln km" % (dsl, dsl * B.R_KM / 1e6))
pp = z.punkt_podsloneczny(tm)
pisz("   Słońce w zenicie nad punktem %.2f° N, %.2f° W" % (pp[0], -pp[1]))


# ---------------------------------------------------------------- 5. niezależne sprawdzenie: efemeryda JPL DE441 (Horizons)
def horizons(nr):
    with open(os.path.join(DANE, "zacmienie-0790", "horizons", "horizons_%s.txt" % nr), encoding="utf-8", errors="replace") as f:
        s = f.read()
    w = s.split("$SOE")[1].split("$EOE")[0].split()
    return dict(ra=float(w[4]), dec=float(w[5]), odl_km=float(w[8]) * 149597870.7)      # współrzędne pozorne (równik daty)


pisz()
pisz("5. NIEZALEŻNE SPRAWDZENIE: JPL Horizons (efemeryda DE441), środek Ziemi, 16 VII 790, 20:29:30 TT")
t = 20.4915565
hs, hk = horizons("10"), horizons("301")
e = z.el(t)
m, zm = z.ksiezyc(t)
s = z.slonce(t)
k = z.osie(t)[2]
dm = math.sqrt(sum(a * a for a in m))
dsl = math.sqrt(sum(a * a for a in s))
dek_k = math.degrees(math.asin(m[2] / dm))
dra = (math.degrees(math.atan2(m[1], m[0]) - math.atan2(k[1], k[0])) + 180) % 360 - 180
pisz("   wielkość                              z elementów Bessela    JPL Horizons")
pisz("   deklinacja Słońca (osi cienia)        %9.4f°             %9.4f°" % (math.degrees(e["d"]), hs["dec"]))
pisz("   deklinacja Księżyca                   %9.4f°             %9.4f°" % (dek_k, hk["dec"]))
pisz("   rektascensja Księżyca minus Słońca    %9.4f°             %9.4f°" % (dra, hk["ra"] - hs["ra"]))
pisz("   odległość Księżyca                    %9.0f km           %9.0f km" % (dm * B.R_KM, hk["odl_km"]))
pisz("   odległość Słońca                      %9.1f mln km       %9.1f mln km" % (dsl * B.R_KM / 1e6, hs["odl_km"] / 1e6))
pisz("   (Elementy NASA liczono z teorii VSOP87/ELP2000-82, Horizons z DE441 – to dwa niezależne rachunki.)")

with open(os.path.join(TU, "sprawdzenie.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(wy) + "\n")
