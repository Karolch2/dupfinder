"""Dekoratory."""
import functools
import logging
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("dupfinder")

def timer(func: Callable) -> Callable:
    """Dekorator ktory mierzy ile trwa wykonanie funkcji."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()  # czas startu
        result = func(*args, **kwargs)  # odpalam oryginalna funkcje
        elapsed = time.perf_counter() - start
        print(f"[timer] {func.__name__} trwalo {elapsed:.3f} s")
        return result

    return wrapper


def retry(attempts: int = 3, delay: float = 0.5) -> Callable:
    """Dekorator z parametrami - jak funkcja rzuci OSError to probuje jeszcze raz.

    attempts - ile razy max probowac, delay - ile sekund czekac miedzy probami.
    """
    if attempts < 1:
        raise ValueError("attempts musi byc co najmniej 1")

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)  # udalo sie - koniec
                except OSError as error:
                    if attempt == attempts:  # to byla ostatnia proba
                        raise
                    logger.warning("%s: proba %d nieudana (%s), ponawiam...", func.__name__, attempt, error)

        return wrapper

    return decorator

if __name__ == "__main__":
    # sprawdzam dekorator na prostej funkcji
    @timer
    def slow_add(a: int, b: int) -> int:
        """Dodaje powoli dwie liczby."""
        time.sleep(1)
        return a + b

    print("Wynik:", slow_add(2, 3))
    print("Nazwa funkcji:", slow_add.__name__)
    print("Opis funkcji:", slow_add.__doc__)

    # test retry - funkcja ktora 2 razy sie nie udaje a za 3 razem dziala
    calls = 0

    @retry(attempts=3, delay=0.1)
    def flaky() -> str:
        """Udaje plik ktory jest chwilowo zablokowany."""
        global calls
        calls += 1
        if calls < 3:
            raise OSError("plik zablokowany")
        return "udalo sie!"

    print(flaky())