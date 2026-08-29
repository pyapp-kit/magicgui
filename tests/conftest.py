import os

import pytest

from magicgui.application import use_app

# Disable tqdm's TMonitor thread to prevent race conditions with Qt threading
# that can cause intermittent segfaults on CI (especially with PySide6 on Linux).
# See: https://github.com/tqdm/tqdm/issues/469
try:
    from tqdm import tqdm as _tqdm_std

    _tqdm_std.monitor_interval = 0
except ImportError:
    pass


@pytest.fixture(scope="session")
def qapp():
    yield use_app("qt").native


# for now, the only backend is qt, and pytest-qt's qapp provides some nice pre-post
# test cleanup that prevents some segfaults.  Once we start testing multiple backends
# this will need to change.
@pytest.fixture(autouse=True, scope="function")
def always_qapp(qapp):
    yield qapp
    if not os.getenv("CI"):
        # I suspect, but can't prove, that this code causes occasional segfaults on CI.
        for w in qapp.topLevelWidgets():
            w.close()
            w.deleteLater()
        qapp.processEvents()


@pytest.fixture(autouse=True, scope="function")
def _clean_type_map():
    """Undo any mutation of the global type map made during a test.

    `register_type` mutates the global `TypeMap` in place, and not every caller
    undoes it -- example scripts run by `test_examples.py` register widget types
    at import time (e.g. `matplotlib/waveform.py` maps `int` -> `Slider`), which
    would otherwise change widget selection for every subsequent test.
    """
    from magicgui.type_map import TypeMap

    type_map = TypeMap.global_instance()
    mappings = (
        type_map._simple_types,
        type_map._simple_annotations,
        type_map._type_defs,
        type_map._additional_kwargs,
    )
    before = [dict(mapping) for mapping in mappings]
    # values here are lists, which tests may append to in place
    callbacks_before = {k: list(v) for k, v in type_map._return_callbacks.items()}

    yield

    for mapping, snapshot in zip(mappings, before, strict=False):
        mapping.clear()
        mapping.update(snapshot)
    type_map._return_callbacks.clear()
    type_map._return_callbacks.update(callbacks_before)
