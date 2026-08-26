import gc
import runpy
from pathlib import Path
from unittest.mock import patch

import pytest
from qtpy.QtCore import QCoreApplication, QEvent
from qtpy.QtWidgets import QApplication

EXAMPLES_DIR = Path(__file__).parent.parent / "docs" / "examples"
EXAMPLES = sorted(EXAMPLES_DIR.rglob("*.py"))


@pytest.mark.parametrize(
    "example",
    EXAMPLES,
    ids=lambda p: str(p.relative_to(EXAMPLES_DIR)),
)
def test_example(qapp: QApplication, example: Path) -> None:
    """Test that each example script runs without errors."""
    assert example.is_file()
    with patch.object(QApplication, "exec", lambda x: QApplication.processEvents()):
        try:
            runpy.run_path(str(example), run_name="__main__")
        except (ModuleNotFoundError, ImportError) as e:
            if "This example requires" in str(e):
                # if the error message indicates a missing required dependency
                # that's fine
                pytest.xfail(str(e))
            if "pip install magicgui[" in str(e):
                # if the error message indicates a missing optional dependency
                # that's fine
                pytest.xfail(str(e))
            if example.parent.name in str(e):
                # if the example is explicitly in a folder named after the
                # dependency it requires, that's fine
                pytest.xfail(str(e))
            raise
        finally:
            # Deterministically tear down whatever the example created.  The
            # namespace returned by runpy is discarded, so the example's
            # widgets are otherwise garbage-collected at an arbitrary later
            # point -- and a still-visible widget whose C++ side is deleted
            # during event processing can receive a paintEvent mid-deletion,
            # which aborts the process on Windows/PyQt5 with
            # "RuntimeError: wrapped C/C++ object ... has been deleted"
            # (seen intermittently in superqt's QRangeSlider paintEvent for
            # demo_widgets/range_slider.py).  Hide everything first so
            # nothing paints, then destroy the native widgets while they are
            # hidden (which also stops their timers), then collect whatever
            # is left while flushing events.
            for widget in qapp.topLevelWidgets():
                widget.close()
                widget.deleteLater()
            # NB: processEvents() does not dispatch DeferredDelete events
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            qapp.processEvents()
            gc.collect()
            qapp.processEvents()
