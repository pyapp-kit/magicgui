"""Backend modules implementing applications and widgets."""

from __future__ import annotations

BACKENDS: dict[str, tuple[str, str]] = {
    "Qt": ("_qtpy", "qtpy"),
    "ipynb": ("_ipynb", "ipynb"),
}

for key in list(BACKENDS):
    if not key.islower():
        BACKENDS[key.lower()] = BACKENDS.pop(key)
