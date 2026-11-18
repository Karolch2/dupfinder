"""Glowna klasa programu - szukanie duplikatow."""
import functools
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dupfinder.hasher import hash_file
from dupfinder.patterns import parse_extensions
from dupfinder.scanner import filter_by_extension, walk_files


def requires_scan(method: Callable) -> Callable:
    """Dekorator metody - nie pozwala jej odpalic zanim nie zrobimy scan()."""

    @functools.wraps(method)
    def wrapper(self: "DuplicateFinder", *args: Any, **kwargs: Any) -> Any:
        if self.files is None:  # tu korzystam z self
            raise RuntimeError(f"Najpierw wywolaj scan(), dopiero potem {method.__name__}()")
        return method(self, *args, **kwargs)

    return wrapper


class DuplicateFinder:
    """Szuka zduplikowanych plikow w folderze."""

    def __init__(self, root: Path, extensions: set[str] | None = None, workers: int = 4) -> None:
        if not root.is_dir():
            raise ValueError(f"To nie jest folder: {root}")
        self.root = root
        self.extensions = extensions
        self.workers = workers  # to idzie przez setter nizej, wiec tez jest sprawdzane
        self.files: list[Path] | None = None  # None = jeszcze nie skanowalem

    @property
    def workers(self) -> int:
        """Ile watkow/procesow uzywac."""
        return self._workers

    @workers.setter
    def workers(self, value: int) -> None:
        if not 1 <= value <= 32:
            raise ValueError("workers musi byc od 1 do 32")
        self._workers = value

    @classmethod
    def from_text(cls, root: str, ext_text: str | None = None) -> "DuplicateFinder":
        """Tworzy obiekt z tekstu, np. od uzytkownika: from_text("test_data", "txt,jpg")."""
        extensions = parse_extensions(ext_text) if ext_text else None
        return cls(Path(root), extensions)

    def scan(self) -> int:
        """Zbiera liste plikow do sprawdzenia, zwraca ile ich jest."""
        self.files = list(filter_by_extension(walk_files(self.root), self.extensions))
        return len(self.files)

    @requires_scan
    def find_duplicates(self) -> dict[str, list[Path]]:
        """Liczy skroty po kolei i zwraca tylko grupy z wiecej niz 1 plikiem."""
        groups: dict[str, list[Path]] = defaultdict(list)
        for path in self.files:
            groups[hash_file(path)].append(path)
        return {h: paths for h, paths in groups.items() if len(paths) > 1}


if __name__ == "__main__":
    test_dir = Path(__file__).resolve().parent.parent / "test_data"
    finder = DuplicateFinder(test_dir)

    # test dekoratora metody - find_duplicates przed scan() ma dac blad
    try:
        finder.find_duplicates()
    except RuntimeError as error:
        print("Blad:", error)

    # test settera - zla wartosc
    try:
        finder.workers = 100
    except ValueError as error:
        print("Blad:", error)

    print("Plikow:", finder.scan())
    duplicates = finder.find_duplicates()
    print("Grup duplikatow:", len(duplicates))
    for paths in list(duplicates.values())[:2]:  # pokazuje tylko 2 pierwsze grupy
        print([p.name for p in paths])

    # test classmethod
    txt_finder = DuplicateFinder.from_text(str(test_dir), "txt")
    print("Plikow .txt:", txt_finder.scan())