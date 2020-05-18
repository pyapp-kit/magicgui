# ![icon](resources/logo_long.png)

[![License](https://img.shields.io/pypi/l/magicgui.svg)](LICENSE)
[![Version](https://img.shields.io/pypi/v/magicgui.svg)](https://pypi.python.org/pypi/magicgui)
[![Python Version](https://img.shields.io/pypi/pyversions/magicgui.svg)](https://python.org)
[![Build Status](https://img.shields.io/travis/napari/magicgui.svg)](https://travis-ci.com/napari/magicgui)
[![Docs](https://readthedocs.org/projects/magicgui/badge/?version=latest)](https://magicgui.readthedocs.io/en/latest/?badge=latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![codecov](https://codecov.io/gh/napari/magicgui/branch/master/graph/badge.svg)](https://codecov.io/gh/napari/magicgui)

**magicgui**: build GUIs from functions, using magic.

## 📖 [Docs](https://magicgui.readthedocs.io/)

## Installation

`magicgui` uses `pyqt` to support both `pyside2` and `pyqt5` backends.  However, you
must have one of those installed for magicgui to work.

```bash
pip install magicgui pyside2  # or pyqt5 instead of pyside2
```

> :information_source: If you'd like to help us extend support to a different backend,
> please open an [issue](https://github.com/napari/magicgui/issues).

## Basic usage

```python
class Medium(Enum):
    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003

# decorate your function with the @magicgui decorator
@magicgui(call_button="calculate")
def snells_law(aoi=30.0, n1=Medium.Glass, n2=Medium.Water, degrees=True):
    aoi = math.radians(aoi) if degrees else aoi
    try:
        result = math.asin(n1.value * math.sin(aoi) / n2.value)
        return math.degrees(result) if degrees else result
    except ValueError:
        return "Total internal reflection!"

# your function will now have a new attribute "Gui"
# call it to create (and optionally show) the new GUI!
snell_gui = snells_law.Gui(show=True)
```

Please see [Documentation](https://magicgui.readthedocs.io/) for many more details
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
