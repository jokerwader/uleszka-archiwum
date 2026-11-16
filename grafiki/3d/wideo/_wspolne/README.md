# _wspolne – kod wspólny klipów-globusów

- `globus.py` – Natural Earth (`_dane/natural-earth`) -> maska lądów (rasteryzacja numpy, cache w `%TEMP%\uskok3d_cache`),
  geometria kuli (`ll2xyz`, `luk`, `azymut`), sfera z mapą UV, tło granatowe, napisy, render z blokadą `.renderuje`
  (`renderuj`: `--proba 1,100` = tylko kadry PNG, `--bez-blokady`), składanie mp4 i `kadr.jpg` ffmpeg-iem.
- `wezly.py` – pomocnik do budowania shaderów z Pythona.

Zmienne środowiskowe (opcjonalne):
- `USKOK3D_PROBKI` – liczba próbek (domyślnie EEVEE 32, w próbach 16),
- `USKOK3D_SILNIK=CYCLES` – render Cycles na procesorze (gdy karta jest zajęta); nie używać dla `tektonika-globus`.
