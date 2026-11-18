"""Benchmark GIL - porownanie: sekwencyjnie / watki / procesy."""
import os
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

from dupfinder.hasher import hash_file, simple_checksum
from dupfinder.scanner import walk_files

REPEATS = 3  # kazdy pomiar powtarzam i biore najlepszy czas
WORKERS = min(os.cpu_count() or 4, 8)  # tyle watkow/procesow ile rdzeni (max 8)


def run(func: Callable, files: list[Path], mode: str) -> float:
    """Odpala func na wszystkich plikach w danym trybie i zwraca czas w sekundach."""
    start = time.perf_counter()
    if mode == "sekwencyjnie":
        list(map(func, files))
    elif mode == "watki":
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            list(executor.map(func, files))
    elif mode == "procesy":
        with ProcessPoolExecutor(max_workers=WORKERS) as executor:
            list(executor.map(func, files, chunksize=8))
    else:
        raise ValueError(f"Nieznany tryb: {mode}")
    return time.perf_counter() - start


def best_time(func: Callable, files: list[Path], mode: str) -> float:
    """Robi kilka pomiarow i zwraca najkrotszy (najmniej zaklocony)."""
    return min(run(func, files, mode) for _ in range(REPEATS))


if __name__ == "__main__":
    test_dir = Path(__file__).resolve().parent.parent / "test_data"
    files = list(walk_files(test_dir))
    if not files:
        raise SystemExit("Brak plikow - najpierw odpal scripts/generate_test_data.py")

    total_mb = sum(f.stat().st_size for f in files) / 1024 / 1024
    print(f"Plikow: {len(files)} ({total_mb:.0f} MB), watkow/procesow: {WORKERS}, powtorzen: {REPEATS}\n")

    tasks = {
        "SHA-256 (hashlib)": hash_file,
        "suma w czystym Pythonie": simple_checksum,
    }
    modes = ["sekwencyjnie", "watki", "procesy"]

    # wypisuje od razu w formacie tabeli markdown - do wklejenia w README
    print("| Zadanie | Sekwencyjnie | Watki | Procesy |")
    print("|---|---|---|---|")
    for name, func in tasks.items():
        times = [best_time(func, files, mode) for mode in modes]
        print(f"| {name} | {times[0]:.2f} s | {times[1]:.2f} s | {times[2]:.2f} s |")