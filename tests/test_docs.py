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
            if "raises-exception" in header.group():
                with pytest.raises(Exception):
                    exec(cell, globalns)
                continue
        exec(cell, globalns)


@pytest.mark.parametrize(
    "fname", [f for f in glob("examples/*.py") if "napari" not in f]
)
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


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11")
def test_setuppy():
    """Ensure that setup.py matches pyproject deps.

    (setup.py is only there for github)
    """
    import ast

    import tomllib

    setup = Path(__file__).parent.parent / "setup.py"
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    settxt = setup.read_text(encoding="utf-8")
    deps = ast.literal_eval(settxt.split("install_requires=")[-1].split("]")[0] + "]")

    with open(pyproject, "rb") as f:
        data = tomllib.load(f)

    projdeps = set(data["project"]["dependencies"])
    assert projdeps == set(deps)

    min_req = data["project"]["optional-dependencies"]["min-req"]
    assert {k.replace(">=", "==") for k in projdeps} == set(min_req)
