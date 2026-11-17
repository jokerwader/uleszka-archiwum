# zwiastun-nadchodzi-przeszlosc

Klip do zwiastuna (odcinek 0 „Wstęp”), 16 s. Rodzaj: **hipoteza**.

## Co pokazuje

Ożywiona ilustracja ze wstępu Leszka do „Cywilizacji Bogów”: obrazek `zrodlo/webacja/tsunami.jpg` z podpisem
„Nadchodzi przeszłość ...”. Na obrazku ogromna zielononiebieska fala z załamującym się grzbietem góruje nad
Statuą Wolności. W klipie fala rośnie na horyzoncie i nadciąga nad posąg, kamera podchodzi nisko nad wodą,
a ostatni kadr odpowiada obrazkowi: chwila tuż przed uderzeniem. W kadrze jest podpis Leszka, bez zmian.

Lektor czyta w tym miejscu: „Nadchodzi przeszłość ...”, potem „Dlatego, że o tym wszystkim decyduje garstka arogantów…”.
Fraza w `klip.json` to koniec poprzedniego zdania („zasadnicze pytania dotyczące zarania naszej cywilizacji”),
bo w tekście artykułu między tym zdaniem a podpisem stoi wstawka z obrazkiem i dłuższa fraza nie jest znajdowana.
Klip wchodzi ok. 2 s przed słowami „Nadchodzi przeszłość”, a napis pojawia się w kadrze razem z nimi.

## Uwagi

- Takiej fali nikt nie zaobserwował. To obraz ostrzeżenia z tekstu, nie rekonstrukcja zdarzenia, stąd znaczek „hipoteza”.
- Obrazek we wstępie jest fotomontażem nieznanego autora (nie rysunkiem Leszka), dlatego rodzaj to „hipoteza”,
  a nie „rysunek-leszka”. Klip nie używa tego pliku: cała scena jest zbudowana od zera w Blenderze.
- Posąg jest uproszczoną bryłą z prostych kształtów (pomnik, nie człowiek). W kadrze nie ma ludzi.
- Skala: 1 jednostka = 10 m. Posąg z cokołem ma 93 m (sam posąg 46 m), fala w ostatnim kadrze ok. 300 m,
  czyli ok. trzy razy więcej niż posąg, tak jak na obrazku.

## Źródła

- Treść kadru: `zrodlo/webacja/tsunami.jpg` i podpis ze wstępu (`podcast/00-wstep/rozdzialy-studio/01-wstep.txt`).
- Wysokość Statuy Wolności (46 m posąg, 93 m od ziemi do pochodni): Wikipedia, „Statue of Liberty” (CC BY-SA 4.0).
  Posąg z 1886 r. jest w domenie publicznej.
- Żadnych pobranych plików: geometria, materiały i światło powstają w `scena.py`.

## Render

`S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-nadchodzi-przeszlosc/scena.py`
(EEVEE, 400 klatek; kadry próbne: `-- --proba 1,140,290,400`). Wspólny kod: `_wspolne/globus.py`, `_wspolne/zwiastun.py`.
