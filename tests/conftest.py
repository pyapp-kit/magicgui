from unittest.mock import MagicMock, PropertyMock, create_autospec, patch

import pytest

from magicgui.application import Application, use_app
from magicgui.widgets.protocols import BaseApplicationBackend


@pytest.fixture(scope="session")
def qapp():
    yield use_app("qt").native


# for now, the only backend is qt, and pytest-qt's qapp provides some nice pre-post
# test cleanup that prevents some segfaults.  Once we start testing multiple backends
# this will need to change.
@pytest.fixture(scope="function")
def always_qapp(qapp):
    yield qapp
    for w in qapp.topLevelWidgets():
        w.close()
        w.deleteLater()


@pytest.fixture
def mock_app():
    MockAppBackend: MagicMock = create_autospec(BaseApplicationBackend, spec_set=True)
    mock_app = Application(MockAppBackend)

    backend_module = MagicMock()
    p = PropertyMock()
    setattr(type(backend_module), "some name", p)
    setattr(mock_app, "_prop", p)

    mock_app._backend_module = backend_module
    with patch.object(Application, "_instance", mock_app):
        yield mock_app
