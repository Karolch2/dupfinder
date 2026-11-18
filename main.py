"""Wyszukiwarka zduplikowanych plikow - glowny plik do uruchamiania."""
import argparse
import logging
import sys
from pathlib import Path

from dupfinder.decorators import timer
from dupfinder.finder import DuplicateFinder
from dupfinder.patterns import extract_date

logger = logging.getLogger("dupfinder")


def parse_args() -> argparse.Namespace:
    """Czyta opcje podane w terminalu."""
    parser = argparse.ArgumentParser(description="Szuka zduplikowanych plikow w folderze.")
    parser.add_argument("folder", help="folder do przeszukania")
    parser.add_argument("--ext", help="tylko te rozszerzenia, np. txt,jpg")
    parser.add_argument(
        "--mode",
        choices=["sekwencyjnie", "watki", "procesy"],
        default="watki",
        help="jak liczyc skroty (domyslnie: watki)",
    )
    parser.add_argument("--workers", type=int, default=4, help="ile watkow/procesow (1-32)")
    parser.add_argument("--verbose", action="store_true", help="pokazuj wiecej informacji")
    return parser.parse_args()


@timer
def search(finder: DuplicateFinder, mode: str) -> dict[str, list[Path]]:
    """Odpala szukanie w wybranym trybie."""
    if mode == "sekwencyjnie":
        return finder.find_duplicates()
    if mode == "procesy":
        return finder.find_duplicates_processes()
    return finder.find_duplicates_threads()


def print_report(duplicates: dict[str, list[Path]]) -> None:
    """Wypisuje znalezione duplikaty."""
    if not duplicates:
        print("Nie znaleziono duplikatow.")
        return

    extra_copies = sum(len(paths) - 1 for paths in duplicates.values())
    wasted = sum(paths[0].stat().st_size * (len(paths) - 1) for paths in duplicates.values())
    print(f"\nZnaleziono {len(duplicates)} grup duplikatow "
          f"({extra_copies} zbednych kopii, {wasted / 1024 / 1024:.1f} MB do odzyskania)\n")

    for number, paths in enumerate(duplicates.values(), start=1):
        size_kb = paths[0].stat().st_size / 1024
        print(f"Grupa {number} ({len(paths)} pliki, {size_kb:.0f} KB kazdy):")
        for path in sorted(paths):
            date = extract_date(path.name)
            date_info = f"   [data: {date}]" if date else ""
            print(f"  {path}{date_info}")
        print()


def main() -> int:
    """Glowna funkcja - zwraca kod wyjscia (0 = ok, 1 = blad)."""
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        finder = DuplicateFinder.from_text(args.folder, args.ext)
        finder.workers = args.workers
    except ValueError as error:  # zly folder, zle rozszerzenia albo zla liczba workers
        logger.error(error)
        return 1

    count = finder.scan()
    logger.info("Plikow do sprawdzenia: %d (tryb: %s, workers: %d)", count, args.mode, finder.workers)

    duplicates = search(finder, args.mode)
    print_report(duplicates)
    return 0


if __name__ == "__main__":
    sys.exit(main())