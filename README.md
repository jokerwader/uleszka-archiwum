# Archiwum uleszka.net

Archiwum polskiego serwisu **uleszka.net** z lat ok. 2004–2007. Serwis był prywatną stroną z tekstami o dawnych cywilizacjach, Atlantydzie, piramidach, potopie, kalendarzach i katastrofach kosmicznych, a także o medycynie naturalnej, zdrowiu i żywności. Do tego publicystyka i fotografie.

Repozytorium ma dwa cele:

1. **Zachować i uporządkować** wszystkie artykuły serwisu w niezmienionej formie.
2. **Umożliwić rozmowę z archiwum** przez asystenta AI (np. Claude) za pomocą serwera MCP. Można wtedy omawiać teksty, wyszukiwać w nich i porównywać je z dzisiejszą wiedzą.

## Co jest w środku

| Miejsce | Zawartość |
|---|---|
| [`KATALOG.md`](KATALOG.md) | Spis treści: wszystkie 148 stron w kolejności z menu serwisu, podzielone na działy |
| [`artykuly/`](artykuly) | Każda strona serwisu jako osobny plik Markdown (UTF-8), z opisem na górze (tytuł, dział, adres oryginału) |
| [`zrodlo/`](zrodlo) | Oryginalna kopia serwisu: pliki HTML i ok. 1500 zdjęć, bajt w bajt |
| [`src/`](src) | Serwer MCP |
| [`scripts/`](scripts) | Konwerter HTML → Markdown, kontrola wierności, testy |

Działy (tak jak w menu serwisu): **Cywilizacja Bogów** (39 stron), **Zapomniana medycyna** (47), **Różności** (59, w tym galerie zdjęć), **Pamiętam** (1) oraz **Strona główna** (2).

### Wierność tekstów

Teksty w `artykuly/` są przeniesione bez zmian. Zmieniony jest tylko zapis: zamiast HTML jest Markdown, a zamiast starego kodowania polskich znaków (ISO-8859-2) jest UTF-8. Usunięte są elementy techniczne: ramki, menu i licznik odwiedzin.

Każdy może to sprawdzić:

```bash
npm run sprawdz
```

Skrypt porównuje litera po literze tekst każdego oryginalnego pliku HTML z plikiem Markdown. Wynik: `Sprawdzono 148 artykułów (3642740 liter i cyfr). Różnic: 0.`

Błędne linki z oryginału (np. adresy, które autor wpisał z pomyłką) też zostały zachowane. Poprawione są tylko adresy zewnętrzne, które program kopiujący stronę zapisał jako ścieżki lokalne.

## Serwer MCP: rozmowa z archiwum

MCP (Model Context Protocol) to standard, przez który asystent AI może korzystać z zewnętrznych źródeł. Po podłączeniu tego serwera asystent może sam przeglądać archiwum, wyszukiwać w nim i czytać całe artykuły.

### Narzędzia

| Narzędzie | Co robi |
|---|---|
| `list_articles` | Spis treści (całość albo jeden dział) |
| `search` | Wyszukiwanie pełnotekstowe. Działa też bez polskich znaków („zrodla” znajdzie „źródła”) i przy literówkach; zwraca cytaty |
| `read_article` | Pełny tekst artykułu. Długie artykuły są podzielone na części po ok. 15 tys. znaków |
| `find_in_article` | Wszystkie miejsca w artykule, gdzie pada dane słowo, z kontekstem |
| `get_image` | Lista zdjęć artykułu albo samo zdjęcie |

Gotowe polecenia (prompty):

- `omow_artykul`: wierne streszczenie tez artykułu, a potem zestawienie każdej tezy z dzisiejszą wiedzą.
- `szukaj_odzwierciedlen`: wszystko, co archiwum mówi na dany temat, plus odzwierciedlenia w obecnych badaniach i wydarzeniach.

Porównanie z obecną wiedzą asystent robi na podstawie własnej wiedzy i wyszukiwarki internetowej (jeśli ją ma włączoną). Serwer MCP daje mu dokładne, oryginalne teksty.

### Instalacja

Potrzebny jest [Node.js](https://nodejs.org) w wersji 20 lub nowszej.

```bash
git clone https://github.com/jokerwader/uleszka-archiwum.git
```

```bash
cd uleszka-archiwum && npm install
```

`npm install` od razu buduje serwer (folder `dist/`).

### Podłączenie do Claude Desktop

W Claude Desktop: *Settings → Developer → Edit Config*. W pliku `claude_desktop_config.json` dopisz (ścieżkę zmień na swoją):

```json
{
  "mcpServers": {
    "uleszka": {
      "command": "node",
      "args": ["C:\\sciezka\\do\\uleszka-archiwum\\dist\\server.js"]
    }
  }
}
```

Potem uruchom Claude Desktop ponownie.

### Podłączenie do Claude Code

```bash
claude mcp add uleszka -- node /sciezka/do/uleszka-archiwum/dist/server.js
```

### Przykładowe pytania

- „Jakie artykuły są w dziale Cywilizacja Bogów?”
- „Co autor pisał o Tiahuanaco? Zacytuj najważniejsze fragmenty.”
- „Omów artykuł o potopie i porównaj jego tezy z dzisiejszą wiedzą geologiczną.”
- „Co archiwum mówi o fluorze, a co mówią aktualne badania?”
- „Które przewidywania z artykułu o roku 2012 się sprawdziły?”

## Dla programistów

```bash
npm run konwertuj   # odtwarza artykuly/ i KATALOG.md z zrodlo/
```

```bash
npm run sprawdz     # kontrola wierności tekstów
```

```bash
npm run build && npm test   # buduje serwer i testuje wszystkie narzędzia przez prawdziwe połączenie MCP
```

Kolejność stron i przydział do działów wynikają z menu serwisu. Strony, do których prowadzą linki z artykułu (np. podrozdziały, galerie), są umieszczone pod nim jako podstrony.

## Prawa autorskie

Treści serwisu uleszka.net (`artykuly/`, `zrodlo/`, `KATALOG.md`) należą do ich autora i **nie** są objęte licencją MIT. Archiwum ma charakter dokumentacyjny: chroni przed zniknięciem serwis, który nie działa już w sieci. Jeśli jesteś autorem tych treści i masz zastrzeżenia, załóż zgłoszenie (Issue), a treści zostaną usunięte.

Licencja MIT ([LICENSE](LICENSE)) dotyczy tylko kodu (`src/`, `scripts/`).
