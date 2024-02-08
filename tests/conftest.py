import pytest

from magicgui.application import use_app


@pytest.fixture(scope="session")
def qapp():
    yield use_app("qt").native


# for now, the only backend is qt, and pytest-qt's qapp provides some nice pre-post
# test cleanup that prevents some segfaults.  Once we start testing multiple backends
# this will need to change.
@pytest.fixture(autouse=True, scope="function")
def always_qapp(qapp):
    yield qapp
    for w in qapp.topLevelWidgets():
        w.close()
        w.deleteLater()


@pytest.fixture(autouse=True, scope="function")
def _clean_return_callbacks():
    from magicgui.type_map._type_map import _RETURN_CALLBACKS

    yield

    _RETURN_CALLBACKS.clear()
