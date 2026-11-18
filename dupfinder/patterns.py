"""Regexy używane w projekcie."""
import re

# wyciaga date z nazwy pliku, np. plik_007_2024-03-15.jpg -> 2024-03-15
DATE_RE = re.compile(r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})")

# dzieli nazwe pliku na czesc przed ostatnia kropka i rozszerzenie
FILENAME_RE = re.compile(r"^(?P<stem>.+)\.(?P<ext>[A-Za-z0-9]+)$")

# sprawdza czy lista rozszerzen od uzytkownika jest ok (np. txt,jpg,pdf)
EXT_LIST_RE = re.compile(r"^[a-z0-9]+(,[a-z0-9]+)*$")


def extract_date(filename: str) -> str | None:
    """Wyciaga date z nazwy pliku, jak nie ma daty to zwraca None."""
    match = DATE_RE.search(filename)  # search bo data jest w srodku nazwy
    if match is None:
        return None
    return f"{match['year']}-{match['month']}-{match['day']}"


def get_extension(filename: str) -> str | None:
    """Zwraca rozszerzenie pliku malymi literami, jak go nie ma to None."""
    match = FILENAME_RE.match(filename)
    if match is None:  # np. plik README bez kropki
        return None
    return match["ext"].lower()  # zeby JPG i jpg to bylo to samo


def parse_extensions(text: str) -> set[str]:
    """Zamienia tekst typu "txt,jpg" na zbior {"txt", "jpg"}.

    Jak tekst jest zle wpisany to rzuca ValueError.
    """
    cleaned = text.strip().lower().replace(" ", "")  # wywalam spacje i duze litery
    if not EXT_LIST_RE.fullmatch(cleaned):
        raise ValueError(f"Nieprawidłowa lista rozszerzeń: {text!r}")
    return set(cleaned.split(","))


if __name__ == "__main__":
    # testuje czy wszystko dziala
    print(extract_date("plik_007_2024-03-15.jpg"))   # 2024-03-15
    print(extract_date("notatki.txt"))               # None
    print(get_extension("kopia_001_plik_007.JPG"))   # jpg
    print(get_extension("README"))                   # None
    print(parse_extensions("txt, JPG,pdf"))          # {'txt', 'jpg', 'pdf'}

    # celowo zla lista, powinien byc blad
    try:
        parse_extensions("txt;;jpg")
    except ValueError as error:
        print("Błąd:", error)