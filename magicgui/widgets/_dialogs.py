from typing import Any, Dict, Hashable, Iterable, Mapping, Optional, Tuple, Type, Union

from magicgui.types import FileDialogMode
from magicgui.widgets._bases.create_widget import create_widget

from ._concrete import Dialog


def show_file_dialog(
    mode: Union[str, FileDialogMode] = FileDialogMode.EXISTING_FILE,
    caption: str = None,
    start_path: str = None,
    filter: str = None,
    parent=None,
) -> Optional[str]:
    """Immediately show an 'open file' dialog and block.

    Parameters
    ----------
    mode : str or magicgui.types.FileDialogMode, optional
        The mode of the dialog.  Allowed strings are:
        - r: returns one existing file.
        - rm: return one or more existing files.
        - w: return one file name that does not have to exist.
        - d: returns one existing directory.
    caption : str, optional
        Caption for the dialog, by default None
    start_path : str, optional
        Starting directory, by default None
    filter : str, optional
        The filter is used to specify the kind of files that should be shown.
        It should be a glob-style string, like ``'*.png'`` (this may be
        backend-specific), by default None
    parent : widget, optional
        The parent widget, by default None

    Returns
    -------
    str or None
        The the path selected, or None if canceled.
    """
    from magicgui import use_app

    app = use_app()
    assert app.native
    return app.get_obj("show_file_dialog")(mode, caption, start_path, filter, parent)


def request_values(
    values: Union[Mapping, Iterable[Tuple[Hashable, Any]]] = (),
    *,
    title: str = "",
    parent: Any = None,
    **kwargs: Union[Type, Dict]
) -> Optional[Dict[str, Any]]:
    """Show a dialog with a set of values and request the user to enter them.

    Dialog is modal and immediately blocks execution until user closes it.
    If the dialog is accepted, the values are returned as a dictionary, otherwise
    returns `None`.

    See also the docstring of :func:`magicgui.widgets.create_widget` for more
    information.

    Parameters
    ----------
    values : Union[Mapping, Iterable[Tuple[Hashable, Any]]], optional
        A mapping of name to arguments to create_widget.  Values can be a dict, in which
        case they are kwargs to `create_widget`, or a single value, in which case it is
        interpreted as the `annotation` in `create_widget`, by default ()
    title : str
        An optional label to put at the top., by default ""
    parent : Widget, optional
        An optional parent widget, by default None.
        The dialog will inherit style from the parent object.
        CAREFUL: if a parent is set, and subsequently deleted, this widget will likely
        be deleted as well (depending on the backend), and will no longer be usable.

    **kwargs : Union[Type, Dict]
        Additional keyword arguments are used as name -> annotation arguments to
        `create_widget`.

    Returns
    -------
    Optional[Dict[str, Any]]
        Dictionary of values if accepted, or `None` if canceled.

    Examples
    --------
    >>> from magicgui.widgets import request_values

    >>> request_values(age=int, name=str, title="Hi! Who are you?")

    >>> request_values(
    ...     age=dict(value=40),
    ...     name=dict(annotation=str, label="Enter your name:"),
    ...     title="Hi! Who are you?"
    ... )

    >>> request_values(
    ...     values={'age': int, 'name': str},
    ...     title="Hi! Who are you?"
    ... )
    """
    widgets = []
    if title:
        from . import Label

        widgets.append(Label(value=title))

    for key, val in dict(values, **kwargs).items():
        kwargs = val if isinstance(val, dict) else dict(annotation=val)
        kwargs.setdefault("name", key)
        widgets.append(create_widget(**kwargs))  # type: ignore

    d = Dialog(widgets=widgets, parent=parent)
    if d.exec():
        return d.asdict()
    return None
