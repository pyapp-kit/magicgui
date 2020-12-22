# Installation

Install via pip:

```shell
pip install magicgui
```

or Conda:

```shell
conda install -c conda-forge magicgui
```

````{important}
You will need to have a supported GUI backend also installed in your environment.
Currently, the only supported backend is [Qt](https://www.qt.io/), via
[qtpy](https://github.com/spyder-ide/qtpy) (but [open an
issue](https://github.com/napari/magicgui/issues) if you would like to see a
different backend supported).

To use with Qt, you will also need to have either
[PyQt5](https://pypi.org/project/PyQt5/) or
[PySide2](https://pypi.org/project/PySide2/) installed in your environment. For
example:

```bash
pip install magicgui[pyqt5]
# or
pip install magicgui[pyside2]
```

or with conda:
```bash
conda install -c conda-forge magicgui pyqt5
```
````
