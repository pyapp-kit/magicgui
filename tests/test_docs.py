import re
import runpy
import sys
from glob import glob
from pathlib import Path

import pytest

from magicgui import type_map, use_app


@pytest.mark.parametrize(
    "fname",
    [
        f
        for f in glob("docs/**/*.md", recursive=True)
        if "_build" not in f and Path(f).read_text(encoding="utf-8").startswith("-")
    ],
)
def test_doc_code_cells(fname):
    """Make sure that all code cells in documentation perform as expected."""
    globalns = globals()
    text = Path(fname).read_text()
    code_cells = re.findall(r"```{code-cell}[^\n]+\n(.*?)`{3}", text, re.S)
    for cell in code_cells:
        header = re.search(r"-{3}(.+?)-{3}", cell, re.S)
        if header:
            cell = cell.replace(header.group(), "")
            if "warns" in header.group():
                with pytest.warns(None):
                    exec(cell, globalns)
                continue
        exec(cell, globalns)


EXAMPLES = Path(__file__).parent.parent / "docs" / "examples"
# leaving out image only because finding the image file in both
# tests and docs is a pain...
# range_slider has periodic segfaults
EXCLUDED = {"napari", "image", "range_slider"}
example_files = [
    str(f) for f in EXAMPLES.rglob("*.py") if all(x not in str(f) for x in EXCLUDED)
]

# if os is Linux and python version is 3.9 and backend is PyQt5
LINUX = sys.platform.startswith("linux")
PY39 = sys.version_info >= (3, 9)
PYQT5 = "PyQt5" in sys.modules
if LINUX and PY39 and PYQT5:
    # skip range_slider example because of superqt c++ wrapped item bug
    example_files = [f for f in example_files if "range_slider" not in f]


@pytest.mark.parametrize("fname", example_files)
def test_examples(fname, monkeypatch):
    """Make sure that all code cells in documentation perform as expected."""
    if "values_dialog" in str(fname):
        from magicgui.backends._qtpy.widgets import QtW  # type: ignore

        try:
            monkeypatch.setattr(QtW.QDialog, "exec", lambda s: None)
        except AttributeError:
            monkeypatch.setattr(QtW.QDialog, "exec_", lambda s: None)
    app = use_app()
    app.start_timer(50 if "table" in str(fname) else 5, app.quit)
    try:
        runpy.run_path(fname)
    except ImportError as e:
        if "Numpy required to use images" in str(e):
            pytest.skip("numpy unavailable: skipping image example")
    finally:
        if "waveform" in fname:
            type_map._type_map._TYPE_DEFS.pop(int, None)
            type_map._type_map._TYPE_DEFS.pop(float, None)
