import time
from contextlib import contextmanager


averages: dict[str, list[float]] = {}
last_prints: dict[str, float] = {}


@contextmanager
def measure(name: str):
    averages.setdefault(name, [])
    last_prints.setdefault(name, 0)

    start = time.time()
    yield
    duration = (time.time() - start) * 1000
    averages[name].append(duration)

    time_since_print = time.time() - last_prints[name]
    PRINT_DELAY = 0.25
    if time_since_print < PRINT_DELAY:
        return

    last_prints[name] = time.time()
    avg_duration = sum(averages[name]) / len(averages[name])
    print(f"{name}: {avg_duration:.3f}ms")
