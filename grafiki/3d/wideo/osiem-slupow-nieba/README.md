# osiem-slupow-nieba

Ilustracja **mitu** do rozdziału 01 „Czy boimy się zrozumieć?”, przy cytacie z K'ü Jüana (Qu Yuan) „Pytam niebiosa”
(„Tianwen”): „Gdy runął K'ang-huei, czemu ziemia na południowy wschód się kłoni? … Gdzie osiem słupów?
Czemu zbrakło jednego na południo-wschodzie?”. 16 s.

Rodzaj: `ilustracja`, bo pokazuje treść mitu, a nie zjawisko ani hipotezę. **To mit, nie opis prawdziwego świata.**
Leszek przytacza ten tekst jako dawny przekaz, który może mówić o przesunięciu skorupy ziemskiej.

## Co widać

1. Stylizowany obraz świata w duchu dawnej chińskiej kosmologii („niebo okrągłe, ziemia kwadratowa”):
   kwadratowa żółta ziemia z napisami kierunków, nad nią przezroczysta kopuła nieba z gwiazdami i złotymi
   kołami, wsparta na ośmiu czerwonych słupach w ośmiu kierunkach (złote południki kopuły kończą się na słupach).
   U góry napis „Osiem słupów podpiera niebo – mit chiński”.
2. Słup południowo-wschodni drży, przewraca się na zewnątrz i znika. Na ziemi pojawia się napis „Południowy wschód”.
3. Ziemia razem z niebem przechyla się (o ok. 8,5°) na południowy wschód. Poziom wody jest stały, więc woda
   zbiera się w opadającym narożniku południowo-wschodnim. Napis „Brak słupa na południowym wschodzie –
   ziemia kłoni się w tę stronę”. Kamera przez cały czas powoli obchodzi scenę od południowego zachodu ku południowi.

## Uproszczenia i dodatki

- Wygląd (czerwone słupy, złote okucia, podział ziemi na dziewięć pól, gwiazdy) jest stylizacją, nie kopią
  konkretnego dawnego rysunku. Tekst Qu Yuana nie opisuje, jak słupy wyglądały.
- W tradycji (np. mit o Gonggongu) mówi się też, że niebo przechyliło się na północny zachód. Klip pokazuje tylko to,
  co jest w cytacie Leszka: brak słupa na południowym wschodzie i ziemię kłoniącą się w tę stronę.
- Północ jest z tyłu sceny, wschód po prawej.

## Dane i licencje

- Bez danych zewnętrznych: cała scena jest zbudowana w skrypcie.
- Czcionki napisów: Georgia (systemowa).

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/osiem-slupow-nieba/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/osiem-slupow-nieba/scena.py -- --proba 1,165,260,400
```

Wspólny kod: `grafiki/3d/wideo/_wspolne/globus.py`.

## Render

EEVEE, 1920×1080, 25 kl./s, 400 klatek: 302 s na RTX 2060 SUPER (16.11.2026, karta dzielona z innymi sesjami).
