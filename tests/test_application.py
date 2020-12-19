from magicgui import use_app
from magicgui.application import APPLICATION_NAME


def test_app_name():
    app = use_app("qt")
    assert app.native.applicationName() == APPLICATION_NAME
