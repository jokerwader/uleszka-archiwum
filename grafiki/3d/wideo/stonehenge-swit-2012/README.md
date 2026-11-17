# stonehenge-swit-2012

Niebo nad Stonehenge 22 grudnia 2012 r. między 6:00 a 6:23 i punkty A–F ze szkicu Leszka. Rozdział 12, scena z druidem:
„Około 6.00 Wega zacznie nasuwać się nad Heel Stone (kamień "A"), Spica nad ognisko "E", a Alamak (gamma Andromedy) nad "C"…”. 20 s.
Rodzaj: `hipoteza`. Położenia gwiazd i planet są policzone i prawdziwe, ale to, że kamienie celowo wskazują te gwiazdy
w tym dniu, jest przypuszczeniem Leszka („Może będzie tak…”), a zgodność kierunków jest tylko przybliżona (tabela niżej).
Bez ludzi: druida nie ma, są tylko ogniska w dołach „E” i „C”, o których mówi tekst.

## Co widać

Kamera wisi 10 m nad środkiem kręgu i obraca się; u góry zegar od 6:00 do 6:23.
1. Północny zachód: Jowisz nisko nad horyzontem przy linii punktu D, Alamak przy linii punktu C (ognisko).
2. Północny wschód: Wega na prawo od linii punktu A (Heel Stone); bliżej punkt B (kamień leżący przy wejściu).
3. Południowy wschód: Spica przy linii punktu E (ognisko), a ok. 6:20 nad horyzontem pojawia się Wenus, na prawo od linii punktu F.
   Podpis: „6:23 – Wenus wschodzi, Jowisz po drugiej stronie nieba zachodzi”.

Złote linie: na ziemi od kręgu do punktu, na niebie przerywany pion w tym samym azymucie. Czerwone okręgi: punkty ze szkicu.

## Wynik rachunku

Azymuty punktów odczytane z pikseli szkicu `zrodlo/webacja/02uskok/ollinstone.jpg` (północ u góry), położenia ciał
policzone dla 51,179°N, 1,826°W (czas uniwersalny = czas zimowy w Anglii):

| Ciało | Punkt i jego azymut | Azymut ciała 6:00 → 6:23 | Wysokość 6:00 → 6:23 | Różnica azymutu |
|---|---|---|---|---|
| Wega | A, 51° | 57° → 61° | 24° → 27° | 6–10° (nad linią stała ok. 5:25) |
| Spica | E, 164° | 156° → 162° | 25° → 26° | 8° → 2° |
| Alamak | C, 344° | 337° → 341° | 7,5° → 6° | 7° → 3° |
| Jowisz | D, 300° | 300° → 305° | 3° → 0° (zachodzi ok. 6:24) | 0° → 5° |
| Wenus | F, 117° | 121° → 125° | −2° → +1° (wschodzi ok. 6:16–6:20) | 4° → 8° |

Wniosek: opis z tekstu zgadza się z prawdziwym niebem tego ranka (Wenus rzeczywiście wschodzi, gdy Jowisz zachodzi,
ok. 6:20), a gwiazdy stoją w pobliżu wskazanych kierunków, lecz nie dokładnie na nich. Refrakcji przy horyzoncie nie liczono.

## Sprawdzenie (audyt 16.11.2026)

Położenia porównane z efemerydą JPL Horizons (DE441, https://ssd.jpl.nasa.gov/horizons/, bez refrakcji) dla tych samych
współrzędnych i chwil:

| Ciało | Klip, 6:00 (azymut / wysokość) | JPL Horizons, 6:00 | Klip, 6:23 | JPL Horizons, 6:23 |
|---|---|---|---|---|
| Wenus | 120,8° / −2,2° | 120,7° / −2,3° | 125,3° / +0,9° | 125,1° / +0,8° |
| Jowisz | 300,2° / +3,2° | 300,0° / +3,4° | 304,6° / +0,2° | 304,4° / +0,3° |
| Saturn | 141,0° / 18,8° | 140,9° / 18,6° | 146,6° / 20,9° | 146,4° / 20,8° |

Różnice 0,1–0,2° to głównie precesja z 13 lat, której klip nie liczy (gwiazdy i planety stoją w układzie J2000);
dla Wegi, Spiki i Alamaka daje ona błąd do 0,17°. Według Horizons Wenus przekracza horyzont o 6:17, a Jowisz o 6:25
(bez refrakcji; z refrakcją Wenus widać kilka minut wcześniej, Jowisza kilka minut dłużej). Słońce stoi 19–15° pod
horyzontem w azymucie 104–108°.

Układ kamieni zgadza się z planem zabytku: stoi 17 sarsenów kręgu (nr 1–7, 10, 11, 16, 21–23, 27–30), nadproża leżą
na parach 29–30, 30–1, 1–2, 4–5, 6–7 i 21–22, oś przechodzi między kamieniami 30 i 1 (azymut 51°), Heel Stone 77 m
od środka, jamy Aubreya na okręgu o promieniu 43,3 m. Punkty C i E ze szkicu to kopce kamieni stacyjnych 94 i 92,
D i F to kamienie stacyjne 93 i 91.

## Co jest uproszczone

- Model kręgu to proste bloki w dzisiejszym układzie (17 stojących sarsenów, 6 nadproży, trylity, kilka leżących głazów,
  błękitne kamienie, Heel Stone, kamienie stacyjne, wał i rów, jamy Aubreya) – nie jest to pomiar zabytku.
- Odległości punktów od środka według planu zabytku: A 77 m, pozostałe ok. 43 m. Kopce C i E to dzisiejsze „North Barrow” i „South Barrow”.
- Gwiazdy: katalog HYG, epoka J2000 (bez precesji z 13 lat – poniżej 0,2°). Planety: średnie elementy orbit JPL (błąd rzędu ułamka stopnia).
  Jasności Wenus i Jowisza zmniejszono, żeby nie zalały kadru. Na niebie jest też Saturn (bez podpisu, na prawo od Spiki).
- Łuna przedświtu na południowym wschodzie jest malowana i mocniejsza niż naprawdę (Słońce było 19–15° pod horyzontem).
- Ognisty blask na kopcach i słabe „światło gwiazd” na kamieniach są umowne.

## Źródła i licencje

- Szkic Leszka Klimka „Naui Ollin i Stonehenge” (`ollinstone.jpg`) – tylko azymuty punktów A–F.
- Gwiazdy: katalog HYG v4.4 (D. Nash, CC BY-SA 4.0), `_dane/hyg/`. Rachunki (czas gwiazdowy, planety): `_wspolne/niebo.py`.
- Geometria, materiały, napisy: od zera w `scena.py`.

## Render

`S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/stonehenge-swit-2012/scena.py`
(500 klatek, EEVEE, 32 próbki). Kadry próbne: `-- --proba 60,230,420,500`. Skrypt wypisuje też tabelę wysokości i azymutów.
