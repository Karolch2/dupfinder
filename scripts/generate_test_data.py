"""Generuje katalog z danymi testowymi: losowe pliki + celowe duplikaty"""
import argparse
import random
import shutil
from pathlib import Path


def generate(target: Path, n_unique: int, n_duplicates: int, seed: int = 42) -> None:
    """Tworzy n_unique losowych plików i n_duplicates kopii w podkatalogach."""
    rng = random.Random(seed)
    if target.exists():
        shutil.rmtree(target)
    subdirs = [target / "docs", target / "photos" / "2024", target / "backup" / "old"]
    for d in subdirs:
        d.mkdir(parents=True, exist_ok=True)

    extensions = [".txt", ".jpg", ".pdf", ".log"]
    originals: list[Path] = []
    for i in range(n_unique):
        folder = rng.choice(subdirs) #losowy folder
        ext = rng.choice(extensions) #losowe rozszerzenie
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        # losuje format daty zeby sprawdzic czy regex lapie rozne zapisy
        date_formats = [
            f"2024-{month:02d}-{day:02d}",  # rrrr-mm-dd
            f"{day:02d}.{month:02d}.2024",  # dd.mm.rrrr
            f"2024_{month:02d}_{day:02d}",  # rrrr_mm_dd
        ]
        name = f"plik_{i:03d}_{rng.choice(date_formats)}{ext}"
        size = rng.randint(1_000, 2_000_000)  # losowy rozmiar od 1 KB do ~2 MB
        path = folder / name
        path.write_bytes(rng.randbytes(size)) #zapis losowych bajtów
        originals.append(path)

    for j in range(n_duplicates):
        src = rng.choice(originals)  # losowanie oryginału
        dst = rng.choice(subdirs) / f"kopia_{j:03d}_{src.name}"
        shutil.copyfile(src, dst) # kopiowanie pod inna nazwą

    print(f"Utworzono {n_unique} plików i {n_duplicates} duplikatów w: {target}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generator danych testowych")
    project_root = Path(__file__).resolve().parent.parent
    parser.add_argument("--out", type=Path, default=project_root / "test_data")
    parser.add_argument("--files", type=int, default=100)
    parser.add_argument("--duplicates", type=int, default=20)
    args = parser.parse_args()
    generate(args.out, args.files, args.duplicates)