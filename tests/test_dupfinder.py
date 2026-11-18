"""Testy jednostkowe projektu (unittest)."""
import tempfile
import unittest
from pathlib import Path

from dupfinder.finder import DuplicateFinder
from dupfinder.hasher import hash_file, safe_hash
from dupfinder.patterns import extract_date, get_extension, parse_extensions
from dupfinder.reader import ChunkReader


class TestPatterns(unittest.TestCase):
    """Testy regexow."""

    def test_extract_date_both_formats(self) -> None:
        self.assertEqual(extract_date("plik_2024-03-15.jpg"), "2024-03-15")
        self.assertEqual(extract_date("plik_15.03.2024.jpg"), "2024-03-15")
        self.assertIsNone(extract_date("notatki.txt"))

    def test_get_extension(self) -> None:
        self.assertEqual(get_extension("zdjecie.JPG"), "jpg")
        self.assertIsNone(get_extension("README"))

    def test_parse_extensions(self) -> None:
        self.assertEqual(parse_extensions("txt, JPG"), {"txt", "jpg"})
        with self.assertRaises(ValueError):  # zla lista ma dac blad
            parse_extensions("txt;;jpg")


class TestFiles(unittest.TestCase):
    """Testy na prawdziwych plikach - tworze je w folderze tymczasowym."""

    def setUp(self) -> None:
        # odpala sie przed kazdym testem - robie swiezy folder z plikami
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "sub").mkdir()
        (self.root / "a.txt").write_bytes(b"ala ma kota")
        (self.root / "sub" / "kopia_a.txt").write_bytes(b"ala ma kota")  # duplikat a.txt
        (self.root / "b.jpg").write_bytes(b"cos zupelnie innego")

    def tearDown(self) -> None:
        # odpala sie po kazdym tescie - sprzatam
        self.tmp.cleanup()

    def test_chunk_reader_reads_whole_file(self) -> None:
        chunks = list(ChunkReader(self.root / "a.txt", chunk_size=4))
        self.assertEqual(b"".join(chunks), b"ala ma kota")
        self.assertEqual(len(chunks), 3)  # 11 bajtow po 4 = 3 kawalki

    def test_chunk_reader_bad_size(self) -> None:
        with self.assertRaises(ValueError):
            ChunkReader(self.root / "a.txt", chunk_size=0)

    def test_hash_same_and_different(self) -> None:
        self.assertEqual(hash_file(self.root / "a.txt"), hash_file(self.root / "sub" / "kopia_a.txt"))
        self.assertNotEqual(hash_file(self.root / "a.txt"), hash_file(self.root / "b.jpg"))

    def test_safe_hash_missing_file(self) -> None:
        with self.assertLogs("dupfinder", level="WARNING"):  # ma byc ostrzezenie w logach
            self.assertIsNone(safe_hash(self.root / "nie_ma.txt"))

    def test_finder_all_modes_find_same_duplicates(self) -> None:
        finder = DuplicateFinder(self.root, workers=2)
        self.assertEqual(finder.scan(), 3)
        expected = {self.root / "a.txt", self.root / "sub" / "kopia_a.txt"}
        for result in (finder.find_duplicates(), finder.find_duplicates_threads(),
                       finder.find_duplicates_processes()):
            self.assertEqual(len(result), 1)  # jedna grupa duplikatow
            self.assertEqual(set(next(iter(result.values()))), expected)

    def test_finder_extension_filter(self) -> None:
        finder = DuplicateFinder.from_text(str(self.root), "jpg")
        self.assertEqual(finder.scan(), 1)
        self.assertEqual(finder.find_duplicates(), {})  # sam jpg nie ma duplikatu

    def test_finder_requires_scan(self) -> None:
        with self.assertRaises(RuntimeError):
            DuplicateFinder(self.root).find_duplicates()

    def test_finder_bad_input(self) -> None:
        with self.assertRaises(ValueError):
            DuplicateFinder(self.root / "nie_ma_folderu")
        with self.assertRaises(ValueError):
            DuplicateFinder(self.root, workers=0)


if __name__ == "__main__":
    unittest.main()