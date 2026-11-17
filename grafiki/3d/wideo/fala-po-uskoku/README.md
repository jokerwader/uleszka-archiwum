# fala-po-uskoku

Ogólnoświatowe tsunami po „wielkim uskoku”: ilustracja hipotezy z tekstu (rozdziały 02 i 06). 16 s (400 klatek, 25 kl./s).
Rodzaj: `hipoteza` (nauka tego nie potwierdza). Wersja 2 z 16.11.2026 (większy globus, wyraźna fala, podpisy etapów).

## Na czym się opiera

- Rozdz. 02: „Najpierw bezwładnie przesunęły się w kierunku południowym, a następnie gigantycznym tsunami
  ruszyły z powrotem. Fala o wysokości kilku kilometrów (…) spłukiwała wszystko co stanęło na jej drodze.”
- Rozdz. 06: „To prawdopodobnie ogromne tsunami, przetaczając się przez ląd, oprócz wody niosło z sobą
  olbrzymie ilości osadów i wypłukanej ziemi.”

## Co widać

Po prawej duży globus w kolorach rysunków Leszka (zielone lądy, niebieskie morze, jak w `uskok-globus`),
po lewej lista trzech etapów; aktywny etap jest jasny i podkreślony złotą kreską. Przez pierwsze 6 s globus
rośnie (promień z 420 do 620 px), potem widok idzie za falą na północ.

1. **Oceany przesuwają się na południe** (0,5–3,5 s): drobne fale na oceanach i sześć białych strzałek suną na południe.
2. **Gigantyczna fala wraca na północ** (3,5–11,5 s): biały grzbiet z cieniowanym wałem wody biegnie od Antarktydy
   na północ, przed nim ciemniejsza dolina, za nim spieniona woda i trzy słabsze grzbiety. Fala wchodzi na lądy
   i zalewa wybrzeża (jasnoniebieski pas, znikają m.in. Floryda, Jukatan i Ameryka Środkowa).
3. **Woda spływa z lądów, zostają osady** (11,5–16 s): zalany pas się kurczy, na lądzie zostaje brązowy pas mułu.

Ostatnia klatka: spokojny ocean, lądy z pasem osadów, lista z podświetlonym etapem 3.

To schemat, nie symulacja: zasięg zalania zależy tylko od odległości od brzegu (średnio ok. 4°, najwyżej ok. 8°,
z szumem), wysokość terenu nie jest brana pod uwagę, kształt i prędkość fali są umowne. Kierunki ruchu wody
(najpierw południe, potem północ) są wzięte dosłownie z tekstu.

## Dane i licencje

- Lądy: Natural Earth 1:10 mln, domena publiczna (`_dane/natural-earth/`).
- Odległość od brzegu policzona z tej samej maski lądów (erozja w numpy).
- Napisy: czcionki systemowe Georgia i Arial. Bez zdjęć i cudzych grafik.

## Uruchomienie

```
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/fala-po-uskoku/scena.py
S:\Blender\blender.exe -b --factory-startup --python grafiki/3d/wideo/fala-po-uskoku/scena.py -- --proba 20,60,130,180,232,270,330,400
```

`kadr.jpg`: klatka 232 (fala na północnym Atlantyku).

## Render (16.11.2026)

EEVEE, 32 próbki, 400 klatek: 317 s (ok. 0,8 s na klatkę, RTX 2060 SUPER).
