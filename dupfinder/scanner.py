"""Przegladanie folderow - generatory."""
import os
from collections.abc import Iterable, Iterator
from pathlib import Path

from dupfinder.patterns import get_extension


def walk_files(root: Path) -> Iterator[Path]:
    """Generator - zwraca po kolei wszystkie pliki z folderu i jego podfolderow."""
    try:
        entries = list(os.scandir(root))
    except PermissionError:
        return  # nie mam dostepu do folderu, wiec go pomijam

    for entry in entries:
        if entry.is_dir(follow_symlinks=False):
            yield from walk_files(Path(entry.path))  # wchodze do podfolderu
        elif entry.is_file(follow_symlinks=False):
            yield Path(entry.path)


def filter_by_extension(files: Iterable[Path], extensions: set[str] | None) -> Iterator[Path]:
    """Zostawia tylko pliki z podanymi rozszerzeniami (None = wszystkie)."""
    if not extensions:
        return iter(files)
    # wyrazenie generujace - nic sie nie liczy dopoki ktos nie zacznie brac plikow
    return (f for f in files if get_extension(f.name) in extensions)


if __name__ == "__main__":
    # testuje na naszych danych testowych
    test_dir = Path(__file__).resolve().parent.parent / "test_data"

    all_files = list(walk_files(test_dir))
    print("Wszystkich plikow:", len(all_files))

    only_txt = list(filter_by_extension(walk_files(test_dir), {"txt"}))
    print("Plikow .txt:", len(only_txt))
    print("Przyklad:", only_txt[0].name)