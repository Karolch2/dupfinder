# Wyszukiwarka zduplikowanych plików

Projekt zaliczeniowy z przedmiotu *Zaawansowane techniki programowania w języku Python*.

Program przeszukuje podany folder (razem z podfolderami) i znajduje pliki o identycznej
zawartości – niezależnie od nazwy i miejsca. Pliki porównywane są po skrócie SHA-256,
który można liczyć sekwencyjnie, w wątkach albo w procesach.

## Wymagania

- Python 3.12+ (testowane na Pythonie 3.14, Windows)
- tylko biblioteka standardowa – nie trzeba nic instalować (dlatego nie ma `requirements.txt`)

## Uruchomienie

Wszystkie komendy uruchamiamy w głównym folderze projektu.

**1. Wygenerowanie danych testowych** (100 plików + 20 duplikatów, ok. 100 MB):
```
python scripts/generate_test_data.py
```
Opcjonalnie: `--files 500 --duplicates 50`. Dzięki stałemu ziarnu (`seed=42`) za każdym razem
powstają te same pliki.

**2. Szukanie duplikatów:**
```
python main.py test_data
python main.py test_data --ext txt,jpg
python main.py test_data --mode procesy --workers 8
python main.py C:\Users\jan\Downloads --verbose
python main.py --help
```

| Opcja | Opis |
|---|---|
| `folder` | folder do przeszukania (wymagany) |
| `--ext` | tylko wybrane rozszerzenia, np. `txt,jpg` |
| `--mode` | `sekwencyjnie`, `watki` (domyślnie) albo `procesy` |
| `--workers` | liczba wątków/procesów (1–32, domyślnie 4) |
| `--verbose` | dodatkowe komunikaty (poziom DEBUG) |

**3. Testy jednostkowe:**
```
python -m unittest discover tests -v
```

**4. Benchmark GIL:**
```
python benchmarks/gil_benchmark.py
```

## Struktura projektu

```
dupfinder/
├── main.py                  # uruchamianie programu (argparse, logging, raport)
├── dupfinder/
│   ├── decorators.py        # dekoratory timer i retry
│   ├── patterns.py          # wyrażenia regularne
│   ├── scanner.py           # generatory przeglądające foldery
│   ├── reader.py            # iterator ChunkReader
│   ├── hasher.py            # SHA-256 i suma kontrolna w czystym Pythonie
│   └── finder.py            # klasa DuplicateFinder (sekwencyjnie / wątki / procesy)
├── benchmarks/
│   └── gil_benchmark.py     # pomiar: sekwencyjnie / wątki / procesy
├── scripts/
│   └── generate_test_data.py
└── tests/
    └── test_dupfinder.py
```

## Tabela mapowania

| Zagadnienie | Gdzie w kodzie |
|---|---|
| Dekorator funkcji + `functools.wraps` | `dupfinder/decorators.py` → `timer` (użyty w `main.py` → `search`) |
| Dekorator z parametrami | `dupfinder/decorators.py` → `retry(attempts, delay)` (użyty w `hasher.py` → `hash_file`) |
| Dekorator metody korzystający z `self` | `dupfinder/finder.py` → `requires_scan` (na metodach `find_duplicates*`) |
| `@property` z setterem | `dupfinder/finder.py` → `DuplicateFinder.workers` |
| `@classmethod` | `dupfinder/finder.py` → `DuplicateFinder.from_text` |
| `@staticmethod` | `dupfinder/finder.py` → `DuplicateFinder.only_duplicates` |
| Iterator (`__iter__`, `__next__`) | `dupfinder/reader.py` → klasa `ChunkReader` |
| Generator + `yield from` | `dupfinder/scanner.py` → `walk_files` (rekurencja po podfolderach) |
| Wyrażenie generujące, potok generatorów | `dupfinder/scanner.py` → `filter_by_extension`; `finder.py` → `scan` |
| Regex – ekstrakcja (grupy nazwane) | `dupfinder/patterns.py` → `DATE_YMD_RE`, `DATE_DMY_RE`, `FILENAME_RE` |
| Regex – walidacja | `dupfinder/patterns.py` → `EXT_LIST_RE` (`parse_extensions`) |
| Wątki + `Lock` | `dupfinder/finder.py` → `find_duplicates_threads` (`ThreadPoolExecutor`) |
| Procesy | `dupfinder/finder.py` → `find_duplicates_processes` (`ProcessPoolExecutor`) |
| Pomiar GIL | `benchmarks/gil_benchmark.py` |
| Testy jednostkowe | `tests/test_dupfinder.py` (`unittest`) |
| CLI | `main.py` → `parse_args` (`argparse`) |
| Logowanie | `main.py`, `hasher.py`, `finder.py`, `decorators.py` (`logging`) |
| Obsługa błędów | `ValueError` przy złych danych, `safe_hash` + `retry` przy nieczytelnych plikach, `PermissionError` w `walk_files` |

## Wyniki pomiarów

Dane: 120 plików (108 MB), 8 wątków/procesów, każdy pomiar powtórzony 3 razy (najlepszy czas).
Windows, Python 3.14, CPU: AMD Ryzen 7 9800X3D(8 rdzeni / 16 wątków).

| Zadanie | Sekwencyjnie | Wątki | Procesy |
|---|---|---|---|
| SHA-256 (`hashlib`) | 0.06 s | 0.03 s | 0.17 s |
| suma kontrolna w czystym Pythonie | 1.97 s | 1.98 s | 0.42 s |

Suma kontrolna w czystym Pythonie (`hasher.py` → `simple_checksum`) nie jest potrzebna do
szukania duplikatów – dodałem ją celowo, żeby w benchmarku było zadanie, które trzyma GIL.

## Wnioski dotyczące GIL

Wyniki pokazują, że to, czy wątki przyspieszają program, zależy od tego, czy kod trzyma GIL.
Przy SHA-256 wątki były ok. 2 razy szybsze od wersji sekwencyjnej, bo `hashlib` jest napisany
w C i zwalnia GIL podczas liczenia skrótu, więc kilka wątków naprawdę liczy jednocześnie.
Procesy były przy tym zadaniu najwolniejsze, bo samo liczenie trwało ułamek sekundy, a
uruchomienie 8 procesów na Windowsie (tryb spawn) i przesyłanie danych między nimi kosztuje
więcej niż zysk z równoległości. Przy sumie kontrolnej w czystym Pythonie wątki nie dały żadnego
przyspieszenia (1.97 s vs 1.98 s), bo pętla po bajtach cały czas trzyma GIL i wątki wykonują się
po kolei. Procesy przyspieszyły to zadanie prawie 5 razy, bo każdy proces ma własny interpreter
i własny GIL, więc korzystają z wielu rdzeni. Wniosek jest taki, że wątki opłacają się przy
zadaniach I/O i przy bibliotekach w C, które zwalniają GIL, a procesy przy obliczeniach w czystym
Pythonie. W naszym programie najlepszym wyborem do liczenia skrótów są więc wątki i dlatego są
domyślnym trybem w `main.py`.

## Napotkane problemy

- **Folder z danymi testowymi tworzył się w złym miejscu.** PyCharm uruchamia skrypt z jego
  własnego folderu, a terminal z głównego, więc `test_data` raz lądował w `scripts/`, a raz
  w głównym katalogu. Rozwiązanie: ścieżka liczona od położenia pliku
  (`Path(__file__).resolve().parent.parent`).
- **Różne formaty dat w nazwach plików.** Pierwszy regex łapał tylko `RRRR-MM-DD`, a prawdziwe
  pliki mają też `DD.MM.RRRR` czy `RRRR_MM_DD`. Dodałem drugi wzorzec i separator `[-._]`,
  a generator danych losuje teraz różne formaty, żeby dało się to przetestować.
- **Procesy na Windowsie.** Windows uruchamia nowe procesy metodą *spawn*, czyli każdy proces
  importuje plik od nowa – dlatego cały kod uruchamiający musi być w `if __name__ == "__main__":`,
  a do procesów można przekazywać tylko funkcje, które da się zaimportować (np. `safe_hash`),
  a nie funkcje zdefiniowane w środku metody.
- **Wyścig przy wątkach.** Wątki dopisują wyniki do jednego wspólnego słownika, więc bez
  `Lock` mogłyby nadpisać sobie nawzajem dane. Kłódka obejmuje tylko dopisywanie, a liczenie
  skrótu odbywa się poza nią, żeby nie tracić równoległości.
- **Wyniki benchmarku inne niż w teorii.** Spodziewałem się, że przy SHA-256 wątki nic nie dadzą
  przez GIL, a okazały się najszybsze, bo `hashlib` zwalnia GIL. Żeby pokazać działanie GIL,
  dodałem drugie zadanie w czystym Pythonie.
- **Nieczytelne pliki na prawdziwym dysku.** Pliki zablokowane albo bez uprawnień wywalały
  program. Dodałem `@retry` na `hash_file` i funkcję `safe_hash`, która pomija taki plik
  i zapisuje ostrzeżenie w logach.