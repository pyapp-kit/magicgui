<h1 align="center">
    <img src="https://raw.githubusercontent.com/pyapp-kit/magicgui/main/resources/logo_long.png" alt="magicgui" />
</h1>

<p align="center">
  <a href="https://github.com/pyapp-kit/magicgui/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/pyapp-kit/magicgui" alt="magicgui is released under the MIT license." />
  </a>
  <a href="https://pypi.python.org/pypi/magicgui">
    <img src="https://img.shields.io/pypi/v/magicgui.svg" alt="magicgui on PyPI" />
  </a>
  <a href="https://anaconda.org/conda-forge/magicgui">
    <img src="https://img.shields.io/conda/vn/conda-forge/magicgui" alt="magicgui on conda-forge" />
  </a>
  </p>
  <p align="center">
  <a href="https://github.com/pyapp-kit/magicgui/actions/workflows/test_and_deploy.yml">
    <img src="https://github.com/pyapp-kit/magicgui/actions/workflows/test_and_deploy.yml/badge.svg" alt="magicgui build status" />
  </a>
  <a href="https://codecov.io/gh/pyapp-kit/magicgui">
    <img src="https://codecov.io/gh/pyapp-kit/magicgui/branch/main/graph/badge.svg" alt="magicgui code coverage" />
  </a>
  <a href="https://zenodo.org/badge/latestdoi/238805437">
    <img src="https://zenodo.org/badge/238805437.svg" alt="cite magicgui" />
  </a>
</p>

<p align="center">
 <em>build GUIs from type annotations, using magic.</em>
</p>


## 📖 Docs

[https://pyapp-kit.github.io/magicgui/](https://pyapp-kit.github.io/magicgui/)

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
> please open an [issue](https://github.com/pyapp-kit/magicgui/issues).

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

![snells](https://raw.githubusercontent.com/pyapp-kit/magicgui/main/resources/snells.png)

But that's just the beginning!  Please see [Documentation](https://pyapp-kit.github.io/magicgui/) for many more details
and usage examples.

## Contributing

Contributions are welcome!

See contributing guide [here](https://github.com/pyapp-kit/magicgui/blob/main/CONTRIBUTING.md).
