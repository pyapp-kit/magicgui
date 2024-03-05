from magicgui import magicgui, widgets


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
