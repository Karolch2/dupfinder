"""Glowna klasa programu - szukanie duplikatow."""
import functools
import logging
import threading
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from typing import Any

from dupfinder.hasher import safe_hash
from dupfinder.patterns import parse_extensions
from dupfinder.scanner import filter_by_extension, walk_files

logger = logging.getLogger("dupfinder")


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
        logger.debug("Skanuje folder %s (rozszerzenia: %s)", self.root, self.extensions or "wszystkie")
        self.files = list(filter_by_extension(walk_files(self.root), self.extensions))
        return len(self.files)

    @requires_scan
    def find_duplicates(self) -> dict[str, list[Path]]:
        """Liczy skroty po kolei i zwraca tylko grupy z wiecej niz 1 plikiem."""
        groups: dict[str, list[Path]] = defaultdict(list)
        for path in self.files:
            file_hash = safe_hash(path)
            if file_hash is not None:  # None = pliku nie dalo sie przeczytac, pomijam
                groups[file_hash].append(path)
        return self.only_duplicates(groups)

    @requires_scan
    def find_duplicates_threads(self) -> dict[str, list[Path]]:
        """To samo co find_duplicates, ale skroty licza sie w kilku watkach naraz."""
        groups: dict[str, list[Path]] = defaultdict(list)
        lock = threading.Lock()  # klodka na wspolny slownik groups

        def worker(path: Path) -> None:
            file_hash = safe_hash(path)  # to moze sie dziac w wielu watkach naraz
            if file_hash is None:
                return
            with lock:  # ale do slownika wpisuje tylko jeden watek na raz
                groups[file_hash].append(path)

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            list(executor.map(worker, self.files))  # list() zeby poczekac na wszystkie
        return self.only_duplicates(groups)

    @requires_scan
    def find_duplicates_processes(self) -> dict[str, list[Path]]:
        """To samo, ale skroty licza sie w osobnych procesach (kazdy ma wlasny GIL)."""
        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            # procesy tylko licza skroty i odsylaja je z powrotem, w tej samej kolejnosci co pliki
            hashes = list(executor.map(safe_hash, self.files, chunksize=8))

        # slownik wypelnia tutaj, w glownym procesie, wiec klodka nie jest potrzebna
        groups: dict[str, list[Path]] = defaultdict(list)
        for path, file_hash in zip(self.files, hashes):
            if file_hash is not None:
                groups[file_hash].append(path)
        return self.only_duplicates(groups)

    @staticmethod
    def only_duplicates(groups: dict[str, list[Path]]) -> dict[str, list[Path]]:
        """Zostawia tylko grupy w ktorych jest wiecej niz 1 plik."""
        logger.debug("Policzono skroty, unikalnych zawartosci: %d", len(groups))
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

    # test watkow - wynik ma byc taki sam jak sekwencyjnie, tylko szybciej
    import time

    start = time.perf_counter()
    seq = finder.find_duplicates()
    print(f"Sekwencyjnie: {time.perf_counter() - start:.2f} s")

    start = time.perf_counter()
    thr = finder.find_duplicates_threads()
    print(f"Watki:        {time.perf_counter() - start:.2f} s")

    # porownuje czy obie wersje znalazly to samo (sortuje bo watki koncza w roznej kolejnosci)
    same = {h: sorted(p) for h, p in seq.items()} == {h: sorted(p) for h, p in thr.items()}
    print("Te same wyniki:", same)

    # test procesow
    start = time.perf_counter()
    prc = finder.find_duplicates_processes()
    print(f"Procesy:      {time.perf_counter() - start:.2f} s")
    same = {h: sorted(p) for h, p in seq.items()} == {h: sorted(p) for h, p in prc.items()}
    print("Te same wyniki:", same)