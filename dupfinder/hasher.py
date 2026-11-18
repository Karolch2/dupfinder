"""Liczenie skrotu SHA-256 pliku."""
import hashlib
import logging
from pathlib import Path

from dupfinder.decorators import retry
from dupfinder.reader import ChunkReader

logger = logging.getLogger("dupfinder")


@retry(attempts=3, delay=0.2)
def hash_file(path: Path) -> str:
    """Liczy SHA-256 pliku czytajac go kawalkami, zwraca skrot jako tekst."""
    sha = hashlib.sha256()
    for chunk in ChunkReader(path):
        sha.update(chunk)  # dorzucam kolejny kawalek do liczenia
    return sha.hexdigest()

def safe_hash(path: Path) -> str | None:
    """Jak hash_file, ale jak pliku nie da sie przeczytac to zwraca None zamiast wywalac program."""
    try:
        return hash_file(path)
    except OSError as error:
        logger.warning("Pomijam plik %s (%s)", path, error)
        return None


def simple_checksum(path: Path, limit: int = 256 * 1024) -> int:
    """Prosta suma kontrolna w czystym Pythonie - tylko do benchmarku GIL.
    Liczy z pierwszych `limit` bajtow pliku. Petla po bajtach w Pythonie
    caly czas trzyma GIL, wiec watki tu nie pomoga (w przeciwienstwie do hashlib).
    """
    with open(path, "rb") as file:
        data = file.read(limit)  # biore tylko poczatek pliku zeby benchmark nie trwal wiecznie
    total = 0
    for byte in data:
        total = (total * 31 + byte) % 4_294_967_296  # zeby liczba nie rosla w nieskonczonosc
    return total

if __name__ == "__main__":
    # szukam jakiejs kopii i jej oryginalu, i porownuje skroty
    from dupfinder.scanner import walk_files

    test_dir = Path(__file__).resolve().parent.parent / "test_data"
    files = list(walk_files(test_dir))

    copy = next(f for f in files if f.name.startswith("kopia_"))
    original_name = copy.name.split("_", 2)[2]  # "kopia_003_plik_028..." -> "plik_028..."
    original = next(f for f in files if f.name == original_name)
    other = next(f for f in files if f != original and f != copy)

    print("Oryginal:", original.name, hash_file(original))
    print("Kopia:   ", copy.name, hash_file(copy))
    print("Inny:    ", other.name, hash_file(other))

    # suma w czystym Pythonie - oryginal i kopia tez musza miec taka sama
    print("Suma oryginalu:", simple_checksum(original))
    print("Suma kopii:    ", simple_checksum(copy))

    # plik ktorego nie ma - retry sprobuje 3 razy, a safe_hash zwroci None
    print("Brakujacy plik:", safe_hash(test_dir / "nie_ma_mnie.txt"))