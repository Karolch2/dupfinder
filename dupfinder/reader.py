"""Czytanie plikow kawalkami - wlasny iterator."""
from pathlib import Path


class ChunkReader:
    """Iterator ktory czyta plik po kawalku, zamiast calego naraz."""

    def __init__(self, path: Path, chunk_size: int = 64 * 1024) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size musi byc wiekszy od 0")
        self.path = path
        self.chunk_size = chunk_size  # domyslnie 64 KB
        self._file = None

    def __iter__(self) -> "ChunkReader":
        return self

    def __next__(self) -> bytes:
        if self._file is None:
            self._file = open(self.path, "rb")  # rb = czytanie bajtow
        chunk = self._file.read(self.chunk_size)
        if not chunk:  # pusty kawalek = koniec pliku
            self._file.close()
            raise StopIteration
        return chunk


if __name__ == "__main__":
    # biore pierwszy plik z danych testowych i czytam go kawalkami
    from dupfinder.scanner import walk_files

    test_dir = Path(__file__).resolve().parent.parent / "test_data"
    file = next(walk_files(test_dir))

    chunks = 0
    total = 0
    for chunk in ChunkReader(file):
        chunks += 1
        total += len(chunk)

    print("Plik:", file.name)
    print("Kawalkow:", chunks)
    print("Przeczytane bajty:", total)
    print("Rozmiar pliku:    ", file.stat().st_size)