# zwiastun-domek-z-kart

Klip do zwiastuna (odcinek 0 „Wstęp”), 14 s. Rodzaj: **hipoteza** (ilustracja oceny autora, nie faktu).

## Co pokazuje

Porównanie z tekstu Leszka: „…ale nasza najstarsza historia jest domkiem z kart i wyjęcie jednej karty,
poruszenie jej czy nawet delikatne dmuchnięcie grozi jego zawaleniem.”

Czteropiętrowy domek z 26 kart stoi na ciemnym blacie. Po ok. 2 s jedna karta z dolnego piętra wysuwa się
w stronę widza, a budowla zaczyna się uginać i wali się do końca. Ostatni kadr: rozsypane karty.

## Jak powstał

- Upadek liczy symulacja brył sztywnych Blendera. Ręcznie animowane jest tylko wysunięcie jednej karty;
  pozostałe karty od klatki 60 podlegają grawitacji i tarciu. Symulacja jest lekko zwolniona (ok. 2 razy).
- Karty mają same ozdobne ramki i romb (awers) oraz kratkę (rewers), bez figur i bez ludzi.
- Karta ma wymiary 0,63 × 0,88 jednostki (dziesięć razy więcej niż prawdziwa), żeby symulacja była stabilna.

## Źródła

Tekst: `podcast/00-wstep/rozdzialy-studio/01-wstep.txt`. Żadnych pobranych plików: wszystko powstaje w `scena.py`.

## Render

`S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-domek-z-kart/scena.py`
(EEVEE, 350 klatek; kadry próbne: `-- --proba 1,75,110,140,350`). Wspólny kod: `_wspolne/globus.py`, `_wspolne/zwiastun.py`.
