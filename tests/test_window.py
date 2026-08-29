import importlib.util

import pytest

from magicgui import magicgui, use_app, widgets

params = ["qt"]
if importlib.util.find_spec("ipywidgets"):
    params.insert(0, "ipynb")


# it's important that "qt" be last here, so that it's used for
# the rest of the tests
@pytest.fixture(scope="module", params=params)
def backend(request):
    return request.param


def test_main_function_gui():
    """Test that main_window makes the widget a top level main window with menus."""

    @magicgui(main_window=True)
    def add(num1: int, num2: int) -> int:
        """Adds the given two numbers, returning the result.

        The function assumes that the two numbers can be added and does
        not perform any prior checks.

        Parameters
        ----------
        num1 , num2 : int
            Numbers to be added

        Returns
        -------
        int
            Resulting integer
        """

    assert not add.visible
    add.show()
    assert add.visible

    assert isinstance(add, widgets.MainFunctionGui)
    add._show_docs()
    assert isinstance(add._help_text_edit, widgets.TextEdit)
    assert add._help_text_edit.value.startswith("Adds the given two numbers")
    assert add._help_text_edit.read_only
    add.close()


def test_main_window_central_widget(backend):
    """The MainWindow is a Container; children go into the central widget."""
    use_app(backend)
    main = widgets.MainWindow()
    button = widgets.PushButton(text="central")
    main.append(button)
    assert len(main) == 1
    assert main[0] is button
    label = widgets.Label(value="also central")
    main.insert(0, label)
    assert len(main) == 2
    assert main[0] is label
    main.remove(label)
    assert len(main) == 1
    main.close()


def test_main_window_dock_and_tool_bars(backend):
    use_app(backend)
    main = widgets.MainWindow()
    for area in ("left", "right", "top", "bottom"):
        main.add_dock_widget(widgets.Label(value=area), area=area)

    tool_bar = widgets.ToolBar()
    tool_bar.add_button(text="Folder", icon="folder")
    tool_bar.add_spacer()
    main.add_tool_bar(tool_bar, area="top")
    main.close()


def test_main_window_tool_bar_type_error():
    use_app("qt")
    main = widgets.MainWindow()
    with pytest.raises(TypeError):
        main.add_tool_bar(widgets.Label(value="not a toolbar"))
    main.close()


def test_main_window_status_bar(backend):
    use_app(backend)
    main = widgets.MainWindow()
    status_bar = main.status_bar  # lazily created and attached
    assert status_bar is main.status_bar
    status_bar.set_message("Hello Status!")
    assert status_bar.message == "Hello Status!"
    status_bar.message = ""
    assert not status_bar.message

    label = widgets.Label(value="perm")
    status_bar.add_widget(label)
    status_bar.remove_widget(label)

    main.status_bar = None
    main.close()


def test_main_window_menus(backend):
    use_app(backend)
    main = widgets.MainWindow()
    fired = []

    file_menu = main.menu_bar.add_menu("File")
    assert file_menu is main.menu_bar["File"]
    assert file_menu.title == "File"
    file_menu.add_action("Open", callback=lambda: fired.append("open"))
    file_menu.add_separator()
    file_menu.add_action("Close", callback=lambda: fired.append("close"))

    # trigger the "Open" action the way the frontend would
    if backend == "qt":
        action = next(a for a in file_menu.native.actions() if a.text() == "Open")
        action.trigger()
    else:
        dropdown = file_menu.native
        value = next(v for label, v in dropdown.options if label == "Open")
        dropdown.value = value
        # selection resets to the title placeholder after triggering
        assert dropdown.value == file_menu._widget._TITLE
    assert fired == ["open"]

    if backend == "qt":
        submenu = file_menu.add_menu("Submenu")
        submenu.add_action("Subaction", callback=lambda: fired.append("sub"))
    else:
        with pytest.raises(NotImplementedError):
            file_menu.add_menu("Submenu")

    file_menu.clear()
    main.menu_bar.clear()
    with pytest.raises(KeyError):
        main.menu_bar["File"]
    if backend == "qt":
        assert not file_menu.native.actions()
        assert not main.menu_bar.native.actions()
    else:
        assert len(file_menu.native.options) == 1  # only the title placeholder
        assert main.menu_bar.native.children == ()
    main.menu_bar = None
    main.close()


def test_main_window_create_menu_item(backend):
    """The legacy create_menu_item pathway."""
    use_app(backend)
    main = widgets.MainWindow()
    if backend == "qt":
        main.create_menu_item("Help", "About", callback=lambda: None)
    else:
        with pytest.raises(NotImplementedError):
            main.create_menu_item("Help", "About")
    main.close()
