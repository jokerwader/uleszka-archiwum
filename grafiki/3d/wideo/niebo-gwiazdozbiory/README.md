# Niebo nad obserwatorium Majów: biegun niebieski, Zodiak i ekliptyka

**Rodzaj:** ilustracja · **Długość:** 20 s (500 klatek, 25 kl./s) · **Rozdział:** 12 „Po co przekazano nam wiedzę astronomiczną?”

Noc w Chichén Itzá (szerokość 20,68° N). Najpierw patrzymy na północ. Nad sylwetką obserwatorium El Caracol
i dalekiej piramidy El Castillo gwiazdy krążą wokół bieguna niebieskiego (20,7° nad horyzontem) i zostawiają ślady.
Potem kamera obraca się na wschód, gdzie wschodzą gwiazdozbiory Zodiaku. Kolejno pojawiają się ekliptyka
oraz linie i nazwy Lwa, Raka i Bliźniąt.

## Dane

| Co | Źródło | Licencja |
|---|---|---|
| Gwiazdy (położenia, jasności, barwy) | Katalog HYG v4.4 (D. Nash, astronexus), gwiazdy do 6,0 mag, wyciąg w `../_dane/hyg/gwiazdy_mag6.csv` (opis w `../_dane/ZRODLA.md`) | CC BY-SA 4.0 |
| Ekliptyka | Wielkie koło nachylone do równika o 23,4393° (epoka J2000) | fakt |
| Linie gwiazdozbiorów | Narysowane w scenie według zwyczajowych figur (oznaczenia Bayera z katalogu): Lew, Rak, Bliźnięta (także Panna i Byk, poza kadrem) | własne |
| El Caracol | Dolna platforma ok. 67 × 52 m, taras ok. 26 × 30 m, okrągła wieża ok. 16 m średnicy u podstawy, szczyt częściowo zawalony, razem ok. 22,5 m (przewodniki po Chichén Itzá, m.in. cancun-adventure.com, theyucatantimes.com) | fakty |
| El Castillo | Podstawa ok. 55 m, 9 tarasów, 24 m + świątynia ok. 6 m. Stoi ok. 410 m na NNE od El Caracol | fakty |

## Co trzeba wiedzieć

- Czas jest przyspieszony: czas gwiazdowy biegnie od 1,3 h do 6,3 h, czyli ok. 5 godzin w 20 s. Na początku obrót
  jest szybszy, żeby narysowały się ślady gwiazd, potem płynnie zwalnia. Tak wygląda niebo na przykład w nocy
  z końca listopada, od wieczora do świtu. Planet i Księżyca nie pokazujemy.
- Jasność i wielkość punktów rosną z jasnością gwiazdy, a barwa wynika ze wskaźnika B−V z katalogu.
- Tło nieba ma kolory plansz filmu (granat `#1b2a4d` przy horyzoncie, `#05070c` w zenicie). Linie i napisy są złote (`#f0c46f`).
- Sylwetki budowli są uproszczone: to kształty według podanych wymiarów, bez detali.
- W ostatnim kadrze dolna część Lwa (Denebola) wchodzi w dolny pas, gdzie `wideo.ts` kładzie podpis. Napisy są ponad nim.

## Sprawdzenie (audyt 16.11.2026)

- To niebo **dzisiejsze** (położenia gwiazd J2000) nad dzisiejszą ruiną z częściowo zawaloną wieżą. Biegun niebieski
  stoi 20,7° nad horyzontem, bo taka jest szerokość geograficzna miejsca; to się nie zmienia. Zmienia się gwiazda
  przy biegunie: dziś Gwiazda Polarna leży 0,7° od bieguna, a ok. 906 r., gdy budowano El Caracol, leżała 6,7° od niego
  (policzone: ruch własny i precesja, `_wspolne/epoka.py`).
- Wymiary budowli sprawdzone ponownie: El Caracol ma platformę 67 × 52 m, okrągłą wieżę o średnicy 16 m i ok. 23 m
  wysokości razem; El Castillo ma podstawę 55,3 m i 24 m wysokości oraz 6 m świątyni (Wikipedia, „El Castillo,
  Chichen Itza”; opisy INAH). Ze współrzędnych z Wikipedii (20,6829°N 88,5686°W i 20,6792°N 88,5707°W) El Castillo
  stoi ok. 460 m od El Caracol, w azymucie ok. 28° (410 m na północ i 220 m na wschód).
- Nachylenie ekliptyki 23,4393° to wartość dla epoki J2000 (Meeus).

## Pliki

- `scena.py`: buduje scenę od zera i renderuje (Blender 5.3, EEVEE). Kadry próbne: `-- probne 1,150,230,300,420,500`, pełny render: `-- pelny`.
- `klip.mp4`: 1920×1080, H.264, CRF 18 · `kadr.jpg`: klatka 480 · `klip.json`: opis dla `wideo.ts`.

Render: 500 klatek w 1222 s (ok. 2,4 s na klatkę, EEVEE, RTX 2060 SUPER, karta współdzielona z innymi programami), 16.11.2026.
