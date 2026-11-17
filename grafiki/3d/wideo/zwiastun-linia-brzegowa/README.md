# zwiastun-linia-brzegowa

Klip do zwiastuna (odcinek 0 „Wstęp”), 18 s. Rodzaj: **hipoteza**.

## Co pokazuje

Lektor: „Jeśli jednak uwzględnić hipotezę Hapgooda o możliwości zaistnienia wielkiego uskoku skorupy ziemskiej
i przyjąć, że taki zaistniał w przeszłości i to niejednokrotnie, to zmiany w ukształtowaniu terenu mogą być bardzo
znaczne, a co za tym idzie, wiele „rzeczy” opisywanych przez starożytnych może znajdować się pod wodą,
a niektóre zniknęły pod ziemią naniesioną przez wielkie tsunami.”

Makieta wycinka wybrzeża z widocznym przekrojem ziemi:

1. Brzeg z dwiema budowlami: kamienna budowla tuż nad morzem i piramida schodkowa w głębi lądu.
   Złota linia to linia brzegowa.
2. „Wielki uskok skorupy ziemskiej”: ląd pochyla się ku morzu, woda wchodzi w głąb lądu. Złota linia zostaje
   pod wodą jako „dawna linia brzegowa”, pierwsza budowla jest „pod wodą”.
3. Wielka fala przechodzi przez nowy brzeg i zostawia warstwę ziemi. Druga budowla znika
   „pod ziemią naniesioną przez wielkie tsunami” (widać ją przez półprzezroczystą warstwę).

## Uwagi

- To ilustracja tezy z tekstu. Nauka nie potwierdza gwałtownych przesunięć skorupy ziemskiej opisanych przez Hapgooda.
- Makieta jest umowna: nie przedstawia żadnego konkretnego miejsca ani budowli, skala pionowa jest przesadzona,
  pochylenie lądu (5°) i grubość naniesionej warstwy są dobrane tak, żeby zjawisko było widać.
- W kadrze nie ma ludzi. Podpisy w kadrze są słowami z tekstu Leszka.

## Źródła

Tekst: `podcast/00-wstep/rozdzialy-studio/01-wstep.txt`. Żadnych pobranych plików: teren, woda i budowle powstają w `scena.py`.

## Render

`S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/zwiastun-linia-brzegowa/scena.py`
(EEVEE, 450 klatek; kadry próbne: `-- --proba 40,130,240,322,345,450`). Wspólny kod: `_wspolne/globus.py`, `_wspolne/zwiastun.py`.
