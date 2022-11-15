"""Backend modules implementing applications and widgets."""

BACKENDS = {"Qt": ("_qtpy", "qtpy"), "ipynb": ("_ipynb", "ipynb")}

for key, value in list(BACKENDS.items()):
    if not key.islower():
        BACKENDS[key.lower()] = BACKENDS.pop(key)
