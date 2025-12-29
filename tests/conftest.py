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
def _clean_return_callbacks():
    from magicgui.type_map import TypeMap

    yield

    TypeMap.global_instance()._return_callbacks.clear()
