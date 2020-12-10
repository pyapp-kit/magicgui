"""Backend modules implementing applications and widgets."""

BACKENDS = {"Qt": ("_qtpy", "qtpy")}

for key, value in list(BACKENDS.items()):
    if not key.islower():
        BACKENDS[key.lower()] = BACKENDS.pop(key)
