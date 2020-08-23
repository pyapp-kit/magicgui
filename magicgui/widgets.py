"""magicgui Widget class that wraps all backend widgets."""
import inspect
import os
from enum import Enum, EnumMeta
from functools import wraps
from inspect import Signature
from pathlib import Path
from typing import (
    Any,
    Callable,
    MutableSequence,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    overload,
)

from magicgui import protocols, transforms
from magicgui.application import use_app
from magicgui.events import EventEmitter
from magicgui.signature import MagicParameter, MagicSignature, magic_signature
from magicgui.types import ChoicesType, PathLike, WidgetOptions

# Main Widget Types.

# -> Widget (wraps WidgetProtocol)
#     ↪ ValueWidget (wraps ValueWidgetProtocol)
#         - Label
#         - LineEdit
#         - TextEdit
#         - DateTimeEdit

#         ↪ ButtonWidget (wraps ButtonWidgetProtocol)
#             - PushButton
#             - CheckBox
#             - RadioButton

#         ↪ RangedWidget (wraps RangedWidgetProtocol)
#             - SpinBox
#             - FloatSpinBox

#             ↪ SliderWidget (wraps SliderWidgetProtocol)
#                 - Slider
#                 - FloatSlider

#         ↪ CategoricalWidget (wraps CategoricalWidgetProtocol)
#             - ComboBox

#     ↪ ContainerWidget (wraps ContainerProtocol)
#         - Container


class Widget:
    """Basic Widget, wrapping a class that implements WidgetProtocol."""

    _widget: protocols.WidgetProtocol

    @staticmethod
    def create(
        name: str = "",
        kind: str = "POSITIONAL_OR_KEYWORD",
        default: Any = None,
        annotation: Any = None,
        gui_only=False,
        app=None,
        widget_type: Union[str, Type[protocols.WidgetProtocol], None] = None,
        options: WidgetOptions = dict(),
    ):
        kwargs = locals()
        _app = use_app(kwargs.pop("app"))
        assert _app.native
        if isinstance(widget_type, protocols.WidgetProtocol):
            wdg_class = widget_type
        else:
            from magicgui.type_map import get_widget_class

            if widget_type:
                options["widget_type"] = widget_type
            wdg_class, opts = get_widget_class(default, annotation, options)

            if issubclass(wdg_class, Widget):
                opts.update(kwargs.pop("options"))
                kwargs.update(opts)
                kwargs.pop("widget_type", None)
                return wdg_class(**kwargs)

        # pick the appropriate subclass for the given protocol
        # order matters
        for p in ("Categorical", "Ranged", "Button", "Value", ""):
            prot = getattr(protocols, f"{p}WidgetProtocol")
            if isinstance(wdg_class, prot):
                return globals()[f"{p}Widget"](
                    widget_type=wdg_class, **kwargs, **kwargs.pop("options")
                )

        raise TypeError(f"{wdg_class!r} does not implement any known widget protocols")

    def __init__(
        self,
        widget_type: Type[protocols.WidgetProtocol],
        name: str = "",
        kind: str = "POSITIONAL_OR_KEYWORD",
        default: Any = None,
        annotation: Any = None,
        gui_only=False,
    ):
        prot = getattr(protocols, self.__class__.__annotations__["_widget"].__name__)
        if not isinstance(widget_type, prot):
            raise TypeError(f"{widget_type!r} does not implement the proper protocol")
        self._widget = widget_type()

        self.name: str = name
        self.kind: inspect._ParameterKind = inspect._ParameterKind[kind.upper()]
        self.default = default
        self.annotation: Any = annotation
        self.gui_only = gui_only
        self.visible: bool = True
        self.parent_changed = EventEmitter(source=self, type="parent_changed")
        self._widget._mg_bind_parent_change_callback(
            lambda *x: self.parent_changed(value=self.parent)
        )

        # put the magicgui widget on the native object...may cause error on some backend
        self.native._magic_widget = self
        self._post_init()

    def _post_init(self):
        pass

    @property
    def options(self) -> dict:
        return {"enabled": self.enabled, "visible": self.visible}

    @property
    def native(self):
        """Return native backend widget."""
        return self._widget._mg_get_native_widget()

    def show(self):
        """Show widget."""
        self._widget._mg_show_widget()
        self.visible = True

    def hide(self):
        """Hide widget."""
        self._widget._mg_hide_widget()
        self.visible = False

    @property
    def enabled(self) -> bool:
        return self._widget._mg_get_enabled()

    @enabled.setter
    def enabled(self, value: bool):
        self._widget._mg_set_enabled(value)

    @property
    def parent(self) -> "Widget":
        return self._widget._mg_get_parent()

    @parent.setter
    def parent(self, value: "Widget"):
        self._widget._mg_set_parent(value)

    @property
    def widget_type(self) -> str:
        """Return type of widget."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        """Return representation of widget of instsance."""
        return f"{self.widget_type}(annotation={self.annotation!r}, name={self.name!r})"


class ValueWidget(Widget):
    """Widget with a value, wrapping the BaseValueWidget protocol."""

    _widget: protocols.ValueWidgetProtocol
    changed: EventEmitter

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.default is not None:
            self.value = self.default

    def _post_init(self):
        super()._post_init()
        self.changed = EventEmitter(source=self, type="changed")
        self._widget._mg_bind_change_callback(
            lambda *x: self.changed(value=x[0] if x else None)
        )

    @property
    def value(self):
        """Return current value of the widget.  This may be interpreted by backends."""
        return self._widget._mg_get_value()

    @value.setter
    def value(self, value):
        return self._widget._mg_set_value(value)

    def __repr__(self) -> str:
        """Return representation of widget of instsance."""
        return (
            f"{self.widget_type}(value={self.value!r}, annotation={self.annotation!r}, "
            f"name={self.name!r})"
        )


class ButtonWidget(ValueWidget):
    """Widget with a value, wrapping the BaseValueWidget protocol."""

    _widget: protocols.ButtonWidgetProtocol
    changed: EventEmitter

    def __init__(self, text: str = "Text", **kwargs):
        super().__init__(**kwargs)
        self.text = text

    @property
    def options(self) -> dict:
        d = super().options.copy()
        d.update({"text": self.text})
        return d

    @property
    def text(self):
        """Text of the widget."""
        return self._widget._mg_get_text()

    @text.setter
    def text(self, value):
        self._widget._mg_set_text(value)


class RangedWidget(ValueWidget):
    """Widget with a contstrained value wraps BaseRangedWidget protocol."""

    _widget: protocols.RangedWidgetProtocol

    def __init__(
        self, minimum: float = 0, maximum: float = 100, step: float = 1, **kwargs
    ):
        super().__init__(**kwargs)

        self.minimum = minimum
        self.maximum = maximum
        self.step = step

    @property
    def options(self) -> dict:
        d = super().options.copy()
        d.update({"minimum": self.minimum, "maximum": self.maximum, "step": self.step})
        return d

    @property
    def minimum(self) -> float:
        """Minimum allowable value for the widget."""
        return self._widget._mg_get_minimum()

    @minimum.setter
    def minimum(self, value: float):
        self._widget._mg_set_minimum(value)

    @property
    def maximum(self) -> float:
        """Maximum allowable value for the widget."""
        return self._widget._mg_get_maximum()

    @maximum.setter
    def maximum(self, value: float):
        self._widget._mg_set_maximum(value)

    @property
    def step(self) -> float:
        """Step size for widget values."""
        return self._widget._mg_get_step()

    @step.setter
    def step(self, value: float):
        self._widget._mg_set_step(value)

    @property
    def range(self) -> Tuple[float, float]:
        """Range of allowable values for the widget."""
        return self.minimum, self.maximum

    @range.setter
    def range(self, value: Tuple[float, float]):
        self.minimum, self.maximum = value


class SliderWidget(RangedWidget):

    _widget: protocols.SliderWidgetProtocol

    def __init__(self, orientation: str = "horizontal", **kwargs):
        super().__init__(**kwargs)

        self.orientation = orientation

    @property
    def options(self) -> dict:
        d = super().options.copy()
        d.update({"orientation": self.orientation})
        return d


class CategoricalWidget(ValueWidget):
    """Widget with a value and choices, wrapping the BaseCategoricalWidget protocol."""

    _widget: protocols.CategoricalWidgetProtocol

    def __init__(self, choices: ChoicesType = (), **kwargs):
        self._default_choices = choices
        super().__init__(**kwargs)

    def _post_init(self):
        super()._post_init()
        self.reset_choices()
        self.parent_changed.connect(self.reset_choices)

    @property
    def options(self) -> dict:
        d = super().options.copy()
        d.update({"choices": self._default_choices})
        return d

    def reset_choices(self, event=None):
        """Reset choices to the default state.

        If self._default_choices is a callable, this may NOT be the exact same set of
        choices as when the widget was instantiated, if the callable relies on external
        state.
        """
        self.choices = self._default_choices

    @property
    def choices(self):
        """Available value choices for this widget."""
        return tuple(i[0] for i in self._widget._mg_get_choices())

    @choices.setter
    def choices(self, choices: ChoicesType):
        if isinstance(choices, EnumMeta):
            str_func: Callable = lambda x: str(x.name)
        else:
            str_func = str
        if isinstance(choices, dict):
            if not ("choices" in choices and "key" in choices):
                raise ValueError(
                    "When setting choices with a dict, the dict must have keys "
                    "'choices' (Iterable), and 'key' (callable that takes a each value "
                    "in `choices` and returns a string."
                )
            _choices = choices["choices"]
            str_func = choices["key"]
        elif not isinstance(choices, EnumMeta) and callable(choices):
            _choices = choices(self)
        else:
            _choices = choices
        if not all(isinstance(i, tuple) and len(i) == 2 for i in _choices):
            _choices = [(str_func(i), i) for i in _choices]
        return self._widget._mg_set_choices(_choices)


class ContainerWidget(Widget, MutableSequence[Widget]):
    """Widget that can contain other widgets."""

    changed: EventEmitter
    _widget: protocols.ContainerProtocol

    def __init__(
        self,
        orientation: str = "horizontal",
        widgets: Sequence[Widget] = (),
        return_annotation: Any = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.changed = EventEmitter(source=self, type="changed")
        self._return_annotation = return_annotation
        for w in widgets:
            self.append(w)

    def __getattr__(self, name: str):
        for widget in self:
            if name == widget.name:
                return widget
        return object.__getattribute__(self, name)

    @overload
    def __getitem__(self, key: int) -> Widget:
        ...

    @overload
    def __getitem__(self, key: slice) -> MutableSequence[Widget]:  # noqa: F811
        ...

    def __getitem__(self, key):  # noqa: F811
        if isinstance(key, slice):
            out = []
            for idx in range(*key.indices(len(self))):
                item = self._widget._mg_get_index(idx)
                if item:
                    out.append(item)
            return out
        elif isinstance(key, int):
            if key < 0:
                key += len(self)
        item = self._widget._mg_get_index(key)
        if not item:
            raise IndexError("Container index out of range")
        return item

    def __delattr__(self, name: str):
        self.remove(getattr(self, name))

    def __delitem__(self, key: Union[int, slice]):
        if isinstance(key, slice):
            for idx in range(*key.indices(len(self))):
                self._widget._mg_remove_index(idx)
        else:
            if key < 0:
                key += len(self)
            self._widget._mg_remove_index(key)

    def __len__(self) -> int:
        return self._widget._mg_count()

    def __setitem__(self, key, value):
        raise NotImplementedError("magicgui.Container does not support item setting.")

    def __dir__(self) -> List[str]:
        d = list(super().__dir__())
        d.extend([w.name for w in self if not w.gui_only])
        return d

    def insert(self, key: int, widget: Widget):
        if isinstance(widget, ValueWidget):
            widget.changed.connect(lambda x: self.changed(value=self))
        self._widget._mg_insert_widget(key, widget)

    @property
    def native_layout(self):
        return self._widget._mg_get_native_layout()

    @classmethod
    def from_signature(cls, sig: Signature, **kwargs) -> "Container":
        return MagicSignature.from_signature(sig).to_container(**kwargs)

    @classmethod
    def from_callable(
        cls, obj: Callable, gui_options: Optional[dict] = None, **kwargs
    ) -> "Container":
        return magic_signature(obj, gui_options=gui_options).to_container(**kwargs)

    @property
    def __signature__(self) -> inspect.Signature:
        """Return signature object, for compatibility with inspect.signature()."""
        return self.to_signature()

    def reset_choices(self, event=None):
        for widget in self:
            if isinstance(widget, CategoricalWidget):
                widget.reset_choices()

    def to_signature(self) -> "MagicSignature":
        params = [
            MagicParameter.from_widget(w) for w in self if w.name and not w.gui_only
        ]
        return MagicSignature(params, return_annotation=self._return_annotation)

    def __repr__(self) -> str:
        return f"<Container {self.to_signature()}>"


# Specific Wrappers of Backend Widgets ================================================


def backend_widget(cls=None, widget_name=None, transform=None):
    @wraps(cls)
    def wrapper(cls) -> Type[Widget]:
        def __init__(self, **kwargs):
            app = use_app()
            assert app.native
            widget = app.get_obj(widget_name or cls.__name__)
            if transform:
                widget = transform(widget)
            kwargs["widget_type"] = widget
            super(cls, self).__init__(**kwargs)

        params = {}
        for klass in reversed(inspect.getmro(cls)):
            sig = inspect.signature(getattr(klass, "__init__"))
            for name, param in sig.parameters.items():
                if name in ("self", "widget_type", "kwargs", "args", "kwds"):
                    continue
                params[name] = param

        cls.__init__ = __init__
        cls.__signature__ = inspect.Signature(
            sorted(params.values(), key=lambda x: x.kind)
        )
        return cls

    return wrapper(cls) if cls else wrapper


_widget_doc = """{}

    Parameters
    ----------
    name : str, optional
        The name of the parameter represented by this widget. by default ""
    kind : str, optional
        The ``inspect._ParameterKind`` represented by this widget.  Used in building
        signatures from multiple widgets, by default "POSITIONAL_OR_KEYWORD"
    default : Any, optional
        The default & starting value for the widget, by default None
    annotation : Any, optional
        The type annotation for the parameter represented by the widget, by default None
    gui_only : bool, optional
        Whether the widget should be considered "only for the gui", or if it should be
        included in any widget container signatures, by default False"""

_button_widget_doc = _widget_doc
_button_widget_doc += """
    text : str, optional
        The text to display on the button. by default "Text\""""

_range_widget_doc = _widget_doc
_range_widget_doc += """
    minimum : float, optional
        The minimum allowable value, by default 0
    maximum : float, optional
        The maximum allowable value, by default 100
    step : float, optional
        The step size for incrementing the value, by default 1"""

_slider_widget_doc = _range_widget_doc
_slider_widget_doc += """
    orientation : str, {{'horizontal', 'vertical'}}
        The orientation for the slider, by default "horizontal\""""

_combo_box_doc = _widget_doc
_combo_box_doc += """
    choices : Enum, Iterable, or Callable
        Available choices displayed in the combo box."""


@backend_widget
class Label(ValueWidget):  # noqa: D101
    __doc__ = _widget_doc.format("A non-editable text or image display.")


@backend_widget
class LineEdit(ValueWidget):  # noqa: D101
    __doc__ = _widget_doc.format("A one-line text editor.")


@backend_widget(widget_name="LineEdit", transform=transforms.make_literal_eval)
class LiteralEvalLineEdit(ValueWidget):  # noqa: D101
    __doc__ = _widget_doc.format(
        "A one-line text editor that evaluates strings as python literals."
    )


@backend_widget
class TextEdit(ValueWidget):  # noqa: D101
    __doc__ = _widget_doc.format(
        "A widget to edit and display both plain and rich text."
    )


@backend_widget
class DateTimeEdit(ValueWidget):  # noqa: D101
    __doc__ = _widget_doc.format("A widget for editing dates and times.")


@backend_widget
class PushButton(ButtonWidget):  # noqa: D101
    __doc__ = _button_widget_doc.format("A command button.")


@backend_widget
class CheckBox(ButtonWidget):  # noqa: D101
    __doc__ = _button_widget_doc.format("A checkbox with a text label.")


@backend_widget
class RadioButton(ButtonWidget):  # noqa: D101
    __doc__ = _button_widget_doc.format("A radio button with a text label")


@backend_widget
class SpinBox(RangedWidget):  # noqa: D101
    __doc__ = _range_widget_doc.format(
        "A widget to edit an integer with clickable up/down arrows."
    )


@backend_widget
class FloatSpinBox(RangedWidget):  # noqa: D101
    __doc__ = _range_widget_doc.format(
        "A widget to edit a float with clickable up/down arrows."
    )


@backend_widget
class Slider(SliderWidget):  # noqa: D101
    __doc__ = _slider_widget_doc.format(
        "A slider widget to adjust a numerical value within a range."
    )


@backend_widget(widget_name="Slider", transform=transforms.make_float)
class FloatSlider(SliderWidget):  # noqa: D101
    __doc__ = _slider_widget_doc.format(
        "A slider widget to adjust a float value within a range."
    )


@backend_widget(widget_name="Slider", transform=transforms.make_log)
class LogSlider(SliderWidget):  # noqa: D101
    __doc__ = _slider_widget_doc.format(
        "A slider widget to adjust a numerical value logarithmically within a range."
    )


@backend_widget
class ComboBox(CategoricalWidget):  # noqa: D101
    __doc__ = _combo_box_doc.format(
        "A categorical widget, allowing selection between multiple choices."
    )


@backend_widget
class Container(ContainerWidget):  # noqa: D101
    pass


class FileDialogMode(Enum):
    """FileDialog mode options.

    EXISTING_FILE - returns one existing file.
    EXISTING_FILES - return one or more existing files.
    OPTIONAL_FILE - return one file name that does not have to exist.
    EXISTING_DIRECTORY - returns one existing directory.
    """

    EXISTING_FILE = "r"
    EXISTING_FILES = "rm"
    OPTIONAL_FILE = "w"
    EXISTING_DIRECTORY = "d"


class FileEdit(Container):
    """A LineEdit widget with a button that opens a FileDialog."""

    def __init__(
        self,
        name: str = "",
        kind: str = "POSITIONAL_OR_KEYWORD",
        default: Any = inspect.Parameter.empty,
        annotation=None,
        gui_only=False,
        orientation="horizontal",
        mode: FileDialogMode = FileDialogMode.EXISTING_FILE,
    ):
        self.line_edit = LineEdit()
        self.choose_btn = PushButton()
        self.mode = mode  # sets the button text too
        super().__init__(
            orientation=orientation,
            widgets=[self.line_edit, self.choose_btn],
            name=name,
            kind=kind,
            default=default,
            annotation=annotation,
            gui_only=gui_only,
        )
        self._show_file_dialog = use_app().get_obj("show_file_dialog")
        self.choose_btn.changed.connect(self._on_choose_clicked)

    @property
    def mode(self) -> FileDialogMode:
        """Mode for the FileDialog."""
        return self._mode

    @mode.setter
    def mode(self, value: Union[FileDialogMode, str]):
        self._mode = FileDialogMode(value)
        self.choose_btn.text = self._btn_text

    @property
    def _btn_text(self) -> str:
        if self.mode is FileDialogMode.EXISTING_DIRECTORY:
            return "Choose directory"
        else:
            return "Select file" + ("s" if self.mode.name.endswith("S") else "")

    def _on_choose_clicked(self, event=None):
        _p = self.value
        start_path: Path = _p[0] if isinstance(_p, tuple) else _p
        start_path = os.fspath(start_path.expanduser().absolute())
        result = self._show_file_dialog(
            self.mode, caption=self._btn_text, start_path=start_path
        )
        if result:
            self.value = result

    @property
    def value(self) -> Union[Tuple[Path, ...], Path]:
        """Return current value of the widget.  This may be interpreted by backends."""
        text = self.line_edit.value
        if self.mode is FileDialogMode.EXISTING_FILES:
            return tuple(Path(p) for p in text.split(", "))
        return Path(text)

    @value.setter
    def value(self, value: Union[Sequence[PathLike], PathLike]):
        """Set current file path."""
        if isinstance(value, (list, tuple)):
            value = ", ".join([os.fspath(p) for p in value])
        if not isinstance(value, (str, Path)):
            raise TypeError(
                f"value must be a string, or list/tuple of strings, got {type(value)}"
            )
        self.line_edit.value = os.fspath(Path(value).expanduser().absolute())

    def __repr__(self) -> str:
        """String representation."""
        return f"<FileEdit mode={self.mode.value!r}, value={self.value!r}>"
