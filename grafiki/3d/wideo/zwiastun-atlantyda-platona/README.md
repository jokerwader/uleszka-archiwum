# zwiastun-atlantyda-platona

Klip do zwiastuna (odcinek 0 „Wstęp”), 18 s. Rodzaj: **hipoteza**.

## Co pokazuje

Lektor: „Atlantyda istniała naprawdę, ale nikt nie kwapi się z jej odszukaniem…”.

Przelot od morza wzdłuż kanału do stolicy Atlantydy zbudowanej dokładnie według liczb z dialogu Platona „Kritias”.
Nikt Atlantydy nie znalazł: klip pokazuje opis Platona, a nie odkrycie. Leszek pisze o tym szerzej w artykule
„Atlantyda” (`artykuly/01-cywilizacja-bogow/012-atlantyda.md`), gdzie mowa o „słynnych kolistych kanałach”.

| Co | Według Platona | W scenie (1 jednostka = 1 stadion) |
|---|---|---|
| Wyspa środkowa | średnica 5 stadiów | promień 2,5 |
| Pierścienie wody (od środka) | 1, 2 i 3 stadia | 2,5–3,5; 5,5–7,5; 10,5–13,5 |
| Pierścienie lądu (od środka) | 2 i 3 stadia | 3,5–5,5; 7,5–10,5 |
| Kanał do morza | długość 50 stadiów, szerokość 300 stóp (3 pletry), głębokość 100 stóp | 50 × 0,5 |
| Mosty | szerokość 1/6 stadionu (pletr) | 1/6 |
| Świątynia Posejdona | długa na stadion, szeroka na pół stadionu, kryta srebrem, szczyty złote | 1 × 0,5, srebrne ściany, złoty dach |
| Tor wyścigów konnych | szeroki na stadion, dookoła większego pierścienia lądu | pas 8,5–9,5 |
| Mury | zewnętrzny kryty mosiądzem, następny cyną, mur cytadeli orichalkiem | trzy pierścienie murów w tych barwach |
| Mur miejski | wszędzie 50 stadiów od największego pierścienia i portu | okrąg o promieniu 63,5 |
| Kamień | biały, czarny i czerwony | domy w trzech barwach |

Miarka w kadrze podaje szerokości w stadiach. Przelicznik „1 stadion to ok. 180 m” jest taki, jakiego używa Leszek
(3000 stadiów = 540 km).

## Co jest umowne

Platon nie podaje układu ulic, liczby i kształtu domów, wysokości brzegów ani barw pól. Te rzeczy są dodane
tylko po to, żeby miasto dało się zobaczyć. Mosty i droga biegną w osi kanału (Platon mówi, że przy mostach
przekopano przejścia dla okrętów). W kadrze nie ma ludzi, okręty to same kadłuby.

## Źródła

- Platon, „Kritias” 113c–117e. Liczby sprawdzone w przekładzie B. Jowetta (domena publiczna):
  https://en.wikisource.org/wiki/Critias_(Jowett)
- Żadnych pobranych plików: geometria i materiały powstają w `scena.py`.

## Sprawdzenie (audyt 16.11.2026)

Wszystkie liczby z tabeli porównano ponownie z tekstem przekładu Jowetta (Wikisource): średnica wyspy 5 stadiów,
pierścienie 3, 3, 2, 2 i 1 stadion, kanał 300 stóp × 100 stóp × 50 stadiów, most szeroki na szóstą część stadionu,
świątynia stadion na pół stadionu, tor wyścigów szeroki na stadion, mur 50 stadiów od największego pierścienia.
Zgadzają się.

## Render

`S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-atlantyda-platona/scena.py`
(EEVEE, 450 klatek; kadry próbne: `-- --proba 40,150,300,450`). Wspólny kod: `_wspolne/globus.py`, `_wspolne/zwiastun.py`.
Uwaga techniczna: mgiełka jest bryłą nad ziemią, a nie objętością świata (objętość świata gasi słońce i tło).
