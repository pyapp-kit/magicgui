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


def show_values_dialog(
    values: Union[Mapping, Iterable[Tuple[Hashable, Any]]] = (),
    *,
    title: str = "",
    **kwargs: Union[Type, Dict]
) -> Dict[str, Any]:

    widgets = []
    if title:
        from . import Label

        widgets.append(Label(value=title))

    for key, val in dict(values, **kwargs).items():
        if isinstance(val, dict):
            val.setdefault("name", key)
            widget = create_widget(**val)
        else:
            widget = create_widget(name=key, annotation=val)
        widgets.append(widget)

    d = Dialog(widgets=widgets)
    d.exec()
    return d.asdict()
