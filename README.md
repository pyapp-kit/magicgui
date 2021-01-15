# ![icon](https://raw.githubusercontent.com/napari/magicgui/master/resources/logo_long.png)

[![License](https://img.shields.io/github/license/napari/magicgui)](LICENSE)
[![Version](https://img.shields.io/pypi/v/magicgui.svg)](https://pypi.python.org/pypi/magicgui)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/magicgui)](https://anaconda.org/conda-forge/magicgui)
[![Python Version](https://img.shields.io/pypi/pyversions/magicgui.svg)](https://python.org)
[![Build Status](https://img.shields.io/travis/napari/magicgui.svg)](https://travis-ci.com/napari/magicgui)
[![codecov](https://codecov.io/gh/napari/magicgui/branch/master/graph/badge.svg)](https://codecov.io/gh/napari/magicgui)

**magicgui**: build GUIs from functions, using magic.

## 📖 [Docs](https://napari.org/magicgui)

## Installation

`magicgui` uses `qtpy` to support both `pyside2` and `pyqt5` backends.  However, you
must have one of those installed for magicgui to work.

install with pip

```bash
pip install magicgui[pyqt5]
# or
pip install magicgui[pyside2]
```

or with conda:

```bash
conda install -c conda-forge magicgui pyqt  # or pyside2 instead of pyqt
```

> :information_source: If you'd like to help us extend support to a different backend,
> please open an [issue](https://github.com/napari/magicgui/issues).

## Basic usage

```python
from magicgui import magicgui
from enum import Enum

class Medium(Enum):
    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003

# decorate your function with the @magicgui decorator
@magicgui(call_button="calculate", result_widget=True)
def snells_law(aoi=30.0, n1=Medium.Glass, n2=Medium.Water, degrees=True):
    import math

    aoi = math.radians(aoi) if degrees else aoi
    try:
        result = math.asin(n1.value * math.sin(aoi) / n2.value)
        return math.degrees(result) if degrees else result
    except ValueError:
        return "Total internal reflection!"

# your function is now capable of showing a GUI
snells_law.show(run=True)
```

![snells](https://raw.githubusercontent.com/napari/magicgui/master/resources/snells.png)

But that's just the beginning!  Please see [Documentation](https://napari.org/magicgui) for many more details
and usage examples.

## Contributing

Contributions are welcome!

Please note: `magicgui` attempts to adhere to strict coding rules and employs the
following static analysis tools to prevent errors from being introduced into the
codebase:

- [black](https://github.com/psf/black) - code formatting
- [flake8](https://github.com/PyCQA/flake8) - linting
- [pydocstyle](https://github.com/PyCQA/pydocstyle/) - docstring conventions
- [mypy](http://mypy-lang.org/) - static type anaylsis
- [codecov](https://codecov.io/) - test coverage

To prevent continuous integration failures when contributing, please consider installing
[pre-commit](https://pre-commit.com/) in your environment to run all of these checks
prior to checking in new code.

```shell
pre-commit install
```
