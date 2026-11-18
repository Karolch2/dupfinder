"""Dekoratory."""
import functools
import time
from collections.abc import Callable
from typing import Any


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