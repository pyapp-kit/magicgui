# Installation

**magicgui** is a pure Python package, and can be installed with `pip`:

```bash
pip install magicgui
```

or with `conda`:

```bash
conda install -c conda-forge magicgui
```

## Backends

**magicgui** requires a backend to be installed in order to function, but it
does not specify a particular backend by default.  The following backends are
available:

- `PyQt5`:  `pip install magicgui[pyqt5]`
- `PyQt6`:  `pip install magicgui[pyqt6]`
- `PySide2`:  `pip install magicgui[pyside2]`
- `PySide6`:  `pip install magicgui[pyside6]`
- `Jupyter Widgets`:  `pip install magicgui[jupyter]`

!!!important

    Note not all widgets are necessarily implemented for all backends.
    Most widgets in the [widget docs](../api/widgets/) specify which backends
    are supported.

## Extras

The [`Image`][magicgui.widgets.Image] widget requires `pillow`. You may use the `image` extra:

```bash
pip install magicgui[image]
```

The `magicgui.tqdm` module requires `tqdm`. You may use the `tqdm` extra:

```bash
pip install magicgui[tqdm]
```

The [`QuantityEdit`][magicgui.widgets.QuantityEdit] widget requires `pint`.
You may use the `quantity` extra:

```bash
pip install magicgui[quantity]
```
