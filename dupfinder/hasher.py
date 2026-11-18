"""Liczenie skrotu SHA-256 pliku."""
import hashlib
from pathlib import Path

from dupfinder.reader import ChunkReader


def hash_file(path: Path) -> str:
    """Liczy SHA-256 pliku czytajac go kawalkami, zwraca skrot jako tekst."""
    sha = hashlib.sha256()
    for chunk in ChunkReader(path):
        sha.update(chunk)  # dorzucam kolejny kawalek do liczenia
    return sha.hexdigest()


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