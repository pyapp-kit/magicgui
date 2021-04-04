import pytest


# for now, the only backend is qt, and pytest-qt's qapp provides some nice pre-post
# test cleanup that prevents some segfaults.  Once we start testing multiple backends
# this will need to change.
@pytest.fixture(autouse=True, scope="session")
def always_qapp(qapp):
    return qapp
