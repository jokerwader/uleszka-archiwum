# Klip „tikal-kompas”

17 s, 1920×1080, 25 kl./s. Rozdziały 08 „Siedemnaście stopni Daenikena” i 09 „Jak to wygląda w praktyce?”.

## Co pokazuje

Plan centrum Tikal w 3D w stylu szkicu Leszka `zrodlo/webacja/02uskok/tikal.jpg`: miętowe tło,
czarne bryły z białym obrysem, czerwone linie przerywane, granatowa strzałka „Pn”.

1. (0–3 s) Budowle wyłaniają się z planu; świątynie I–V jako schodkowe piramidy z numerami.
2. (2,5–4 s) Gruba czerwona linia przerywana: dzisiejsza północ, przez Plac Główny (jak na szkicu) i strzałka „Pn”.
3. (4,3–6 s) Cieńsza czerwona linia przerywana: drugi kierunek ze szkicu, „na wschód od” północy.
4. (6–8 s) Nad Świątynią I pojawia się róża wiatrów; jej igła (długa złota oś przerywana) wskazuje północ.
5. (8,2–10,5 s) Igła obraca się o 17° na północny wschód, rysuje się łuk i napis „kompas Daenikena (17°)”,
   żeby było jasne, że 17° pochodzi z cytatu, a nie ze szkicu.
6. (11,7–15 s) Złoty trójkąt świątyń IV, I i V z cytatu Daenikena, ze znakiem kąta prostego przy Świątyni I.
7. (15–17 s) Spokojna końcowa klatka ze wszystkim naraz.

## Szkic Leszka a plan z Wikimedia Commons

Szkic Leszka jest schematyczny i nie ma podpisów. Porównanie z planem z Commons:
- Gruba czerwona linia na szkicu biegnie z północy na południe przez skupisko trzech małych budowli w środku
  (Plac Główny ze Świątyniami I i II) aż do budowli na północy, gdzie leży zespół bliźniaczych piramid O. W klipie: tak samo.
- Cieńsza linia na szkicu odchodzi od Placu Głównego **o ok. 45° na wschód** (zmierzone na rysunku: 650 px w poziomie
  na 655 px w pionie, w 6-krotnym powiększeniu) i trafia w znak „krzyżyka z czterech kwadratów” w prawym górnym rogu.
  To zespoły bliźniaczych piramid Q i R na północnym wschodzie. W klipie cienka linia ma 45°, jak na szkicu.
- **17° nie ma na szkicu.** Pochodzi z cytatu Daenikena (rozdział 08). Dlatego w klipie 17° pokazuje osobno
  róża wiatrów nad Świątynią I (tam, gdzie Daeniken stał z kompasem), a nie cienka linia Leszka.
  Tak ustaliła sesja główna (16.11.2026): linia 45° wierna szkicowi, 17° tylko jako „kompas Daenikena”.
- Świątyń III, IV i V szkic nie obejmuje albo nie da się ich na nim pewnie wskazać, więc ich położenia są z planu.

Co wynika z planu (do wiadomości, w klipie bez komentarza): kąt przy Świątyni I w trójkącie IV–I–V wynosi ok. 91°,
a ramiona są odchylone od kierunków świata o ok. 12–13° (I→V: azymut 191,6°, I→IV: 282,9°), nie o 17°.
Złota oś 17° przechodzi więc obok Świątyni V, nie przez nią. Klip pokazuje to, co mówi cytat, i to, co jest na planie.

## Położenia

- Świątynie I–V i piramida 5C-54 w Mundo Perdido: te same współrzędne co w klipie `tikal-przelot`
  (metry od środka Placu Głównego, z planu S. Burchella przeskalowanego według współrzędnych z Wikipedii).
- Pozostałe budowle: wielokąty przepisane z pliku SVG (niżej) i przeliczone na metry dopasowaniem afinicznym do
  sześciu punktów powyżej (błąd dopasowania 10–31 m). Place i drogi (groble) pominięte, bo nie ma ich na szkicu.
- Wysokości budowli przewyższone 1,4 raza, żeby świątynie były widoczne na planie o szerokości 1,5 km.

## Źródła i licencje

- Szkic: Leszek Klimek, uleszka.net (2004–2007).
- Plan: „Tikal map vector.svg”, autor Simon Burchell, Wikimedia Commons, licencja CC BY-SA 3.0,
  https://commons.wikimedia.org/wiki/File:Tikal_map_vector.svg (pochodzi z File:Tikal map.JPG tego autora).
  Uznanie autorstwa i ta sama licencja dotyczą przerysowanego planu w tym klipie.
- Cytat Daenikena („Dzień, w którym przybyli bogowie”) jest w tekście odcinka; w klipie jest tylko napis „kompas Daenikena (17°)” i numery świątyń.
- `klip.json`: pierwsza fraza z rozdziału 09 (szkic Tikal), druga z rozdziału 08 (cytat Daenikena).
- Czcionki: Georgia Bold i Arial Bold (Windows), tylko do renderu.

## Render

`S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/tikal-kompas/scena.py`
(kadry próbne: `... -- --test 1,100,230,330,425`). EEVEE, 48 próbek, 425 klatek w 31 min (1877 s), ale karta była wtedy zajęta grą i innymi renderami; sama scena jest lekka.
