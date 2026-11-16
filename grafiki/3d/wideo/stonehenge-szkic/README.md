# stonehenge-szkic

Ożywiony szkic Leszka Klimka „Naui Ollin i Stonehenge”. Rozdział 12 „Po co przekazano nam wiedzę astronomiczną?”,
część „Naui Ollin i Stonehenge”. 20 s. Rodzaj: `rysunek-leszka`.

## Który rysunek

W zleceniu podano `zrodlo/webacja/02uskok/stonehenge.jpg`, ale to mały (107×100 px) rysunek z innego miejsca rozdziału
(kierunek „wejścia” do kręgu, akapit o Akpatoku): krąg, dwa skrzyżowane pasy, litera W i strzałka, **bez punktów A–F**.
Szkic, który tekst opisuje literami A, B, C, D, E, F, z liniami do gwiazd i planet, to
`zrodlo/webacja/02uskok/ollinstone.jpg` (350×308 px, w artykule pod nim podpis „Naui Ollin i Stonehenge”).
Klip ożywia ten drugi; `klip.json` wskazuje `ollinstone.jpg`.

## Co widać (kolejność jak w tekście)

1. Zielona tablica jak tło rysunku; zielone wały i kręgi wyrastają z niej w 3D (obwałowania), szara strzałka „Pn”.
2. Jasna figura w środku z czarnymi kamieniami (jak na rysunku).
3. „Punkty A, C i E, jako jedyne, są wyróżnione obwałowaniem z ziemi” – czerwone przerywane okręgi A, C, E.
4. „Kamienie D i F leżą na kręgu złożonym tylko z tzw. jam Aubreya” – okręgi D i F, potem B.
5. „Linia łącząca obserwatora z punktami A i B, najbardziej chyba wyróżniona” – żółta linia od środka przez B i A
   do gwiazdy Wega.
6. „Linie prowadzone przez wyróżnione punkty kreślą wyraźną symetrię” – linie Alamak–C–E–Spica i Jowisz–D–F–Wenus
   rosną od środka; na końcach białe gwiazdki i żółte etykiety jak na rysunku.
7. Niebieski pas Zodiaku odsłania się od lewej góry do prawej, ze znakami (Byk, Bliźnięta, Rak, Lew, Panna, Waga)
   i białymi podpisami LEW, PANNA, WAGA.
8. Znak Ollin w lewym dolnym rogu (czarny rysunek z oryginału).

Kamera zaczyna prawie z góry (jak rysunek), powoli się pochyla, żeby było widać wały, i na końcu wraca prawie do pionu.

## Wierność rysunkowi

- Wszystkie położenia odczytane z pikseli rysunku: środki i promienie czerwonych okręgów, gwiazdki, etykiety,
  litery, końce linii, pas Zodiaku (jego środek wypada dokładnie w punkcie przecięcia linii, 176/133,5 px,
  promienie 123–149 px), strzałka Pn. Kolory próbkowane z rysunku.
- Wały, jasna figura w środku, czarne kamienie i znak Ollin to maski kolorów z rysunku, powiększone 4× i wygładzone
  (wały dostały też wysokość). Czerwone okręgi i żółte linie zasłaniały na rysunku fragmenty wałów – te miejsca
  uzupełniono zielenią z sąsiedztwa.
- Niczego nie dodano od siebie: żadnych nowych podpisów ani kierunków. Linie, etykiety, gwiazdki i znaki Zodiaku
  narysowano na nowo (ostrzej), w tych samych miejscach. Znaki Zodiaku z czcionki Segoe UI Symbol.

## Źródła i licencje

- Rysunek: Leszek Klimek, uleszka.net (2004–2007), `zrodlo/webacja/02uskok/ollinstone.jpg` (materiał archiwum).
- Czcionki: Arial, Segoe UI Symbol (Windows), tylko do renderu.

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/stonehenge-szkic/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/stonehenge-szkic/scena.py -- --proba 150,500
```
