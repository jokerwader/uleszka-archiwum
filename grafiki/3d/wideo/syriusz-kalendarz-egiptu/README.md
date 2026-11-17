# syriusz-kalendarz-egiptu

Wschód Syriusza przed świtem i koło roku egipskiego. Rozdział 12 „Po co przekazano nam wiedzę astronomiczną?”, zdanie:
„…kolejni faraonowie wstępujący na tron w starożytnym Egipcie składali przysięgę iż w żadnym wypadku nie zmienią kalendarza…”. 17 s.
Rodzaj: `ilustracja` (budowa kalendarza i cykl Syriusza to fakty). O samej przysiędze faraonów mówi tekst Leszka;
klip jej nie pokazuje i nie potwierdza, pokazuje tylko, co wynikało z niezmienianego kalendarza.

## Co widać

1. Lewa część kadru: niebo przed świtem nad doliną Nilu w Memfis, widok na wschód-południowy wschód, policzone na
   świt 19 lipca 1322 r. p.n.e. (napis w kadrze). Nad horyzontem stoi Orion, pod nim wschodzi Syriusz.
   Z lewej jaśnieje łuna świtu, z kierunku, w którym pod horyzontem stało Słońce.
2. Prawa część: koło roku egipskiego. Zewnętrzny pierścień to 12 miesięcy po 30 dni (Thot … Mesore) i czerwony klin
   5 dni dodatkowych; wewnętrzny to trzy pory roku: Achet (wylew), Peret (zasiewy), Szemu (żniwa).
3. Licznik lat biegnie od 0 do 1460, a jasny znacznik „dzień wschodu Syriusza” obiega koło: co 4 lata o 1 dzień później.
4. Na końcu znacznik wraca na Nowy Rok: „po 1460 latach znów w Nowy Rok (cykl sotisowy)”.

## Skąd liczby

- Kalendarz cywilny Egiptu: 365 dni, bez dnia przestępnego. Rok słoneczny (i rok Syriusza) ma ok. 365,25 dnia,
  więc kalendarz „uciekał” o 1 dzień na 4 lata, a pełny obieg trwał 4 × 365 = 1460 lat (cykl sotisowy, znany z Cenzoryna).
- Wschód heliakalny Syriusza (pierwszy widoczny wschód przed świtem po okresie niewidoczności) zapowiadał w Egipcie wylew Nilu.
- Niebo: Memfis (29,85°N), świt 19 lipca 1322 r. p.n.e. według kalendarza juliańskiego. To początek cyklu sotisowego,
  który skończył się w 139 r. n.e., kiedy według Cenzoryna („De die natali”, 238 r.) wschód Syriusza znów wypadł
  w egipski Nowy Rok (139 − 1460 = −1321, czyli 1322 r. p.n.e.; ten początek łączy się z „erą Menofresa” u Teona
  z Aleksandrii). Dokładny rok i dzień nie są znane ze źródeł; to data wyliczona.
- Gwiazdy: katalog HYG v4.4 przeliczony na tę datę (`_wspolne/epoka.py`): ruch własny z katalogu (dla Syriusza 1,2°
  przez 3300 lat) i precesja (wzory IAU 1976, Meeus rozdz. 21). Syriusz miał wtedy deklinację −17,8° (dziś −16,7°),
  wschodził w azymucie 110,6° i przy wysokości 3° stał w azymucie 112,5°; Betelgeza była wtedy 29° nad horyzontem
  w azymucie 108°, Rigel 22° w azymucie 127°.
- Słońce: długość ekliptyczna 102° (Meeus rozdz. 25); w chwili, gdy Syriusz ma wysokość 3°, stoi 7,5° pod horyzontem
  w azymucie 58°. Łuna świtu świeci z tego kierunku (kształt i barwy łuny są malowane). W klipie mija ok. 35 minut:
  Syriusz od 1° pod horyzontem do 6° nad nim, Słońce od −11° do −5°.
- Kontrola rachunku: te same wzory dla 139 r. n.e. dają wschód heliakalny w Memfis 20–21 lipca (Słońce 8–9° pod
  horyzontem przy Syriuszu 3° nad nim), czyli datę podaną przez Cenzoryna.
- Poprawka z 16.11.2026 (audyt): wcześniej niebo było dzisiejsze (J2000) dla 30°N, a łuna stała w azymucie 73°.
  Orion był przez to inaczej ustawiony względem horyzontu (Betelgeza w azymucie 97°, Rigel 26° nad horyzontem).
- Krajobraz (dolina, rzeka, wzgórza na horyzoncie) jest umowny. Refrakcji przy horyzoncie nie liczono.
- Nazwy miesięcy w spolszczonej formie greckiej: Thot, Paofi, Athyr, Choiak, Tybi, Mechir, Famenot, Farmuti, Pachons, Pauni, Epifi, Mesore.

## Źródła i licencje

- Gwiazdy: katalog HYG v4.4 (D. Nash, CC BY-SA 4.0), `_dane/hyg/gwiazdy_mag6_ruch.csv`; rachunki w `_wspolne/epoka.py`
  (precesja, ruch własny, Słońce) i `_wspolne/niebo.py`.
- Koło kalendarza, krajobraz, napisy: od zera w `scena.py`. Czcionki Georgia i Arial (Windows), tylko do renderu.

## Render

`S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/syriusz-kalendarz-egiptu/scena.py`
(425 klatek, EEVEE, 32 próbki). Kadry próbne: `-- --proba 100,300,425`.
