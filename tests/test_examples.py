import runpy
from pathlib import Path
from unittest.mock import patch

import pytest
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
