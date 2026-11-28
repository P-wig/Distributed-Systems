"""Name -> algorithm lookup used by experiment configs and the demo."""

from dtc.algorithms.base import Algorithm

ALGORITHMS: dict[str, type[Algorithm]] = {}


def register(cls: type[Algorithm]) -> type[Algorithm]:
    """Class decorator that registers an algorithm under `cls.name`."""
    ALGORITHMS[cls.name] = cls
    return cls


def get_algorithm(name: str) -> type[Algorithm]:
    try:
        return ALGORITHMS[name]
    except KeyError:
        raise KeyError(f"unknown algorithm {name!r}; registered: {sorted(ALGORITHMS)}") from None
