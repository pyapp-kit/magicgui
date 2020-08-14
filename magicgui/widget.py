"""magicgui Widget class that wraps all backend widgets."""
from __future__ import annotations

import inspect
import os
from enum import EnumMeta
from inspect import Signature
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    MutableSequence,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypedDict,
    Union,
    overload,
)

from magicgui.application import AppRef, use_app
from magicgui.bases import (
    BaseButtonWidget,
    BaseCategoricalWidget,
    BaseContainer,
    BaseRangedWidget,
    BaseValueWidget,
    BaseWidget,
    SupportsChoices,
)
from magicgui.constants import FileDialogMode, WidgetKind
from magicgui.event import EventEmitter
from magicgui.type_map import _get_backend_widget, pick_widget_type

if TYPE_CHECKING:
    from magicgui.signature import MagicSignature


WidgetRef = Optional[str]
TypeMatcher = Callable[[Any, Optional[Type], Optional[dict]], WidgetRef]
_TYPE_MATCHERS: Set[TypeMatcher] = set()
ChoicesIterable = Union[Iterable[Tuple[str, Any]], Iterable[Any]]
ChoicesCallback = Callable[["CategoricalWidget"], ChoicesIterable]
ChoicesType = Union[EnumMeta, ChoicesIterable, ChoicesCallback, "ChoicesDict"]


class ChoicesDict(TypedDict):
    """Dict Type for setting choices in a categorical widget."""

    choices: ChoicesIterable
    key: Callable[[Any], str]


class Widget:
    """Basic Widget, wrapping the BaseWidget protocol."""

    _widget: BaseWidget

    # TODO: add widget_type
    @staticmethod
    def create(
        value: Any = None,
        annotation=None,
        options: dict = {},
        name: Optional[str] = None,
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        app: AppRef = None,
        gui_only=False,
    ):
        """Widget factory. All widgets should be created with this method."""
        # Make sure that the app is active
        kwargs = locals().copy()
        _app = use_app(kwargs.pop("app"))

        widget_type = pick_widget_type(value, annotation, options)
        if widget_type is None:
            raise ValueError(
                f"Could not determine widget type for value={value!r}, "
                f"annotation={annotation!r}, options={options}, app={app}"
            )
        if widget_type is WidgetKind.FILE_EDIT:
            del kwargs["options"]
            return FileEdit(**kwargs)

        wdg_class = _get_backend_widget(widget_type, app)
        assert _app.native
        kwargs["wdg_class"] = wdg_class
        if isinstance(wdg_class, BaseCategoricalWidget):
            return CategoricalWidget(**kwargs)
        if isinstance(wdg_class, BaseRangedWidget):
            return RangedWidget(**kwargs)
        if isinstance(wdg_class, BaseButtonWidget):
            return ButtonWidget(**kwargs)
        if isinstance(wdg_class, BaseValueWidget):
            return ValueWidget(**kwargs)
        return Widget(**kwargs)

    def __init__(
        self,
        wdg_class: Type[BaseWidget],
        name: Optional[str] = None,
        value: Any = None,
        annotation=None,
        options: dict = {},
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        gui_only=False,
    ):
        self.name = name
        self.default = value
        self.annotation = annotation
        self._options = options
        self._kind = kind
        self.gui_only = gui_only

        self._widget = wdg_class()
        # put the magicgui widget on the native object...may cause error on some backend
        self.native._magic_widget = self

        self._post_init()

        if options.get("disabled", False) or not options.get("enabled", True):
            self.enabled = False
        if not options.get("visible", True):
            self.hide()
        if self.default:
            self.value = self.default

    def _post_init(self):
        """For subclasses, so they don't have to recreate init signature."""
        pass

    @property
    def is_mandatory(self) -> bool:
        """Whether the parameter represented by this widget is mandatory."""
        if self._kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.POSITIONAL_ONLY,
        ):
            return self.default is inspect.Parameter.empty
        return False

    @property
    def native(self):
        """Return native backend widget."""
        return self._widget._mg_get_native_widget()

    def show(self):
        """Show widget."""
        self._widget._mg_show_widget()

    def hide(self):
        """Hide widget."""
        self._widget._mg_hide_widget()

    @property
    def enabled(self) -> bool:
        return self._widget._mg_get_enabled()

    @enabled.setter
    def enabled(self, value: bool):
        self._widget._mg_set_enabled(value)

    @property
    def parent(self) -> Widget:
        return self._widget._mg_get_parent()

    @parent.setter
    def parent(self, value: Widget):
        self._widget._mg_set_parent(value)

    @property
    def widget_type(self) -> str:
        """Return type of widget."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        """Return representation of widget of instsance."""
        return (
            f"Widget(value={self.value!r}, annotation={self.annotation!r}, "
            f"options={self._options}, name={self.name!r}, kind={self._kind})"
        )


class ValueWidget(Widget):
    """Widget with a value, wrapping the BaseValueWidget protocol."""

    _widget: BaseValueWidget
    changed: EventEmitter

    def _post_init(self):
        super()._post_init()
        self.changed = EventEmitter(source=self, type="changed")
        # TODO: fix this pattern
        self._widget._mg_bind_change_callback(lambda x: self.changed(value=x))

    @property
    def value(self):
        """Return current value of the widget.  This may be interpreted by backends."""
        return self._widget._mg_get_value()

    @value.setter
    def value(self, value):
        return self._widget._mg_set_value(value)


class ButtonWidget(ValueWidget):
    """Widget with a value, wrapping the BaseValueWidget protocol."""

    _widget: BaseButtonWidget
    changed: EventEmitter

    def _post_init(self):
        super()._post_init()
        self.text = self._options.get("text", "button")

    @property
    def text(self):
        """Text of the widget."""
        return self._widget._mg_get_text()

    @text.setter
    def text(self, value):
        self._widget._mg_set_text(value)


class RangedWidget(ValueWidget):
    """Widget with a contstrained value wraps BaseRangedWidget protocol."""

    DEFAULT_MIN = 0
    DEFAULT_MAX = 100
    DEFAULT_STEP = 1
    _widget: BaseRangedWidget

    def _post_init(self):
        super()._post_init()
        self.minimum = self._options.get("minimum", self.DEFAULT_MIN)
        self.maximum = self._options.get("maximum", self.DEFAULT_MAX)
        self.step = self._options.get("step", self.DEFAULT_STEP)

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


class CategoricalWidget(ValueWidget):
    """Widget with a value and choices, wrapping the BaseCategoricalWidget protocol."""

    _widget: BaseCategoricalWidget

    def _post_init(self):
        super()._post_init()
        self._default_choices = self._options.get("choices")
        if not isinstance(self._widget, SupportsChoices):
            raise ValueError(f"widget {self._widget!r} does not support 'choices'")
        self.reset_choices()

    def reset_choices(self):
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

    def __repr__(self):
        """Return string representation of widget."""
        _type = type(self.native)
        backend = f"{_type.__module__}.{_type.__qualname__}"
        return f"<MagicCategoricalWidget ({backend!r}) at {hex(id(self))}>"


class Container(MutableSequence[Widget], Widget):
    changed: EventEmitter
    _widget: BaseContainer

    def __init__(
        self,
        *,
        orientation="horizontal",
        widgets: Sequence[Widget] = [],
        app=None,
        return_annotation=Signature.empty,
        name: Optional[str] = None,
        value: Any = None,
        annotation=None,
        options: dict = {},
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        gui_only=False,
    ):
        self._app = use_app(app)
        assert self._app.native
        Widget.__init__(
            self,
            wdg_class=self._app.get_obj("Container"),
            name=name,
            value=value,
            annotation=annotation,
            options=options,
            kind=kind,
            gui_only=gui_only,
        )
        self.changed = EventEmitter(source=self, type="changed")
        self._return_annotation = return_annotation
        for w in widgets:
            self.append(w)

    def __getattr__(self, name: str):
        for widget in self:
            if name == widget.name:
                return widget
        raise AttributeError(f"'Container' object has no attribute {name!r}")

    def __delitem__(self, key: Union[int, slice]):
        if isinstance(key, slice):
            for idx in range(*key.indices(len(self))):
                self._widget._mg_remove_index(idx)
        else:
            self._widget._mg_remove_index(key)

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

        item = self._widget._mg_get_index(key)
        if not item:
            raise IndexError("Container index out of range")
        return item

    def __len__(self) -> int:
        return self._widget._mg_count()

    def __setitem__(self, key, value):
        raise NotImplementedError("magicgui.Container does not support item setting.")

    def insert(self, key: int, widget: Widget):
        if isinstance(widget, ValueWidget):
            widget.changed.connect(lambda x: self.changed(value=self))
        self._widget._mg_insert_widget(key, widget)

    @property
    def native_layout(self):
        return self._widget._mg_get_native_layout()

    @classmethod
    def from_signature(cls, sig: Signature, **kwargs) -> Container:
        from magicgui.signature import MagicSignature

        return MagicSignature.from_signature(sig).to_container(**kwargs)

    @classmethod
    def from_callable(
        cls, obj: Callable, gui_options: Optional[dict] = None, **kwargs
    ) -> Container:
        from magicgui.signature import magic_signature

        return magic_signature(obj, gui_options=gui_options).to_container(**kwargs)

    def to_signature(self) -> MagicSignature:
        from magicgui.signature import MagicParameter, MagicSignature

        params = [
            MagicParameter(
                name=w.name,
                kind=w._kind,
                default=w.value,
                annotation=w.annotation,
                gui_options=w._options,
            )
            for w in self
            if w.name and not w.gui_only
        ]
        return MagicSignature(params, return_annotation=self._return_annotation)

    def __repr__(self) -> str:
        return f"<Container {self.to_signature()}>"


PathLike = Union[Path, str, bytes]


class FileEdit(Container):
    """A LineEdit widget with a button that opens a FileDialog"""

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        value: Optional[PathLike] = None,
        annotation=None,
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        gui_only=False,
        orientation="horizontal",
        app: AppRef = None,
        mode: FileDialogMode = FileDialogMode.EXISTING_FILE,
    ):
        self.line_edit = Widget.create(options={"widget_type": "LineEdit"})
        self.choose_btn = Widget.create(options={"widget_type": "PushButton"})
        self.mode = mode
        super().__init__(
            orientation=orientation,
            widgets=[self.line_edit, self.choose_btn],
            app=app,
            name=name,
            value=value,
            annotation=annotation,
            kind=kind,
            gui_only=gui_only,
        )
        self._show_file_dialog = self._app.get_obj("show_file_dialog")
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
        return f"<LineEdit mode={self.mode.value!r}, value={self.value!r}>"
