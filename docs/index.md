---
jupytext:
  cell_metadata_filter: -all
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.12
    jupytext_version: 1.7.1
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# magicgui 🧙

[![License](https://img.shields.io/pypi/l/magicgui.svg)](https://github.com/napari/magicgui/blob/main/LICENSE)
[![Version](https://img.shields.io/pypi/v/magicgui.svg)](https://pypi.python.org/pypi/magicgui)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/magicgui)](https://anaconda.org/conda-forge/magicgui)
[![Python Version](https://img.shields.io/pypi/pyversions/magicgui.svg)](https://python.org)

Type-based GUI autogeneration for python.

## installation

```shell
# via pip
pip install magicgui

# via conda
conda install -c conda-forge magicgui
```

## from types to widgets

The core feature of `magicgui` is the [@magicgui](magicgui.magicgui) decorator,
which can autogenerate a graphical user interface (GUI) by inspecting a
function signature and adding an appropriate GUI widget for each parameter type.

```{code-cell} python
from magicgui import magicgui

@magicgui
def add(my_number: int, some_word: str = 'hello', maybe = True):
  ...

add.show()
```

## configuration and advanced usage

The `@magicgui` decorator takes a number of options that allow you to configure the GUI
and it's behavior.  See [configuration](usage/configuration) for more information.
