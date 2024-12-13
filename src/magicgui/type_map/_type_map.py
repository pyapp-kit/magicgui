"""Functions in this module are responsible for mapping type annotations to widgets."""

from __future__ import annotations

import datetime
import inspect
import itertools
import os
import pathlib
import sys
import types
import warnings
from collections import defaultdict
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from enum import EnumMeta
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    ForwardRef,
    Literal,
    TypeVar,
    Union,
    cast,
    overload,
)

from typing_extensions import ParamSpec, get_args, get_origin

from magicgui import widgets
from magicgui._type_resolution import resolve_single_type
from magicgui._util import safe_issubclass
from magicgui.application import AppRef, use_app
from magicgui.types import PathLike, ReturnCallback, Undefined, _Undefined
from magicgui.widgets import protocols
from magicgui.widgets.protocols import WidgetProtocol, assert_protocol

if TYPE_CHECKING:
    from magicgui.type_map._magicgui import MagicFactory

__all__: list[str] = ["get_widget_class", "register_type"]


# redefining these here for the sake of sphinx autodoc forward refs
WidgetClass = Union[type[widgets.Widget], type[WidgetProtocol]]
WidgetRef = Union[str, WidgetClass]
WidgetTuple = tuple[WidgetRef, dict[str, Any]]


class MissingWidget(RuntimeError):
    """Raised when a backend widget cannot be found."""


_T = TypeVar("_T", bound=type)
_P = ParamSpec("_P")
_R = TypeVar("_R")

_SIMPLE_ANNOTATIONS_DEFAULTS = {
    PathLike: widgets.FileEdit,
}

_SIMPLE_TYPES_DEFAULTS: dict[type, type[widgets.Widget]] = {
    bool: widgets.CheckBox,
    int: widgets.SpinBox,
    float: widgets.FloatSpinBox,
    str: widgets.LineEdit,
    pathlib.Path: widgets.FileEdit,
    datetime.time: widgets.TimeEdit,
    datetime.timedelta: widgets.TimeEdit,
    datetime.date: widgets.DateEdit,
    datetime.datetime: widgets.DateTimeEdit,
    range: widgets.RangeEdit,
    slice: widgets.SliceEdit,
    Sequence[pathlib.Path]: widgets.FileEdit,
    tuple: widgets.TupleEdit,
    Sequence: widgets.ListEdit,
    os.PathLike: widgets.FileEdit,
}

_ADDITIONAL_KWARGS_DEFAULTS: dict[type, dict[str, Any]] = {
    Sequence[pathlib.Path]: {"mode": "rm"}
}


class TypeMap:
    """Storage for mapping from types to widgets and callbacks."""

    def __init__(
        self,
        *,
        simple_types: dict | None = None,
        simple_annotations: dict | None = None,
        type_defs: dict | None = None,
        return_callbacks: dict | None = None,
        additional_kwargs: dict | None = None,
    ):
        if simple_types is None:
            simple_types = _SIMPLE_TYPES_DEFAULTS.copy()
        if simple_annotations is None:
            simple_annotations = _SIMPLE_ANNOTATIONS_DEFAULTS.copy()
        if additional_kwargs is None:
            additional_kwargs = _ADDITIONAL_KWARGS_DEFAULTS.copy()
        self._simple_types = simple_types
        self._simple_annotations = simple_annotations
        self._type_defs = type_defs or {}
        self._return_callbacks: defaultdict[type, list[ReturnCallback]] = defaultdict(
            list, return_callbacks or {}
        )
        self._additional_kwargs = additional_kwargs

    @staticmethod
    def global_instance() -> TypeMap:
        """Get the global type map."""
        return _GLOBAL_TYPE_MAP

    def copy(self) -> TypeMap:
        """Return a copy of the type map."""
        return TypeMap(
            simple_types=self._simple_types.copy(),
            simple_annotations=self._simple_annotations.copy(),
            type_defs=self._type_defs.copy(),
            return_callbacks=self._return_callbacks.copy(),
            additional_kwargs=self._additional_kwargs.copy(),
        )

    def match_type(self, type_: Any, default: Any | None = None) -> WidgetTuple | None:
        """Check simple type mappings."""
        if type_ in self._simple_annotations:
            return self._simple_annotations[type_], {}

        if type_ is widgets.ProgressBar:
            return widgets.ProgressBar, {"bind": lambda widget: widget, "visible": True}

        if type_ in self._simple_types:
            return self._simple_types[type_], self._additional_kwargs.get(type_, {})
        for key in self._simple_types.keys():
            if safe_issubclass(type_, key):
                return self._simple_types[key], self._additional_kwargs.get(key, {})

        if type_ in (types.FunctionType,):
            return widgets.FunctionGui, {"function": default}

        origin = get_origin(type_) or type_
        choices, nullable = _literal_choices(type_)
        if choices is not None:  # it's a Literal type
            return widgets.ComboBox, {"choices": choices, "nullable": nullable}

        if safe_issubclass(origin, set):
            for arg in get_args(type_):
                if get_origin(arg) is Literal:
                    return widgets.Select, {"choices": get_args(arg)}

        pint = sys.modules.get("pint")
        if pint and safe_issubclass(origin, pint.Quantity):
            return widgets.QuantityEdit, {}

        return None

    def match_return_type(self, type_: Any) -> WidgetTuple | None:
        """Check simple type mappings for result widgets."""
        if type_ in self._simple_types:
            return widgets.LineEdit, {"gui_only": True}

        if type_ is widgets.Table:
            return widgets.Table, {}

        table_types = [
            resolve_single_type(x) for x in ("pandas.DataFrame", "numpy.ndarray")
        ]

        if any(
            safe_issubclass(type_, tt)
            for tt in table_types
            if not isinstance(tt, ForwardRef)
        ):
            return widgets.Table, {}

        return None

    @overload
    def register_type(
        self,
        type_: _T,
        *,
        widget_type: WidgetRef | None = None,
        return_callback: ReturnCallback | None = None,
        **options: Any,
    ) -> _T: ...

    @overload
    def register_type(
        self,
        type_: Literal[None] | None = None,
        *,
        widget_type: WidgetRef | None = None,
        return_callback: ReturnCallback | None = None,
        **options: Any,
    ) -> Callable[[_T], _T]: ...

    def register_type(
        self,
        type_: _T | None = None,
        *,
        widget_type: WidgetRef | None = None,
        return_callback: ReturnCallback | None = None,
        **options: Any,
    ) -> _T | Callable[[_T], _T]:
        """Register a ``widget_type`` to be used for all parameters with type `type_`.

        Note: registering a Union (or Optional) type effectively registers all types in
        the union with the arguments.

        Parameters
        ----------
        type_ : type
            The type for which a widget class or return callback will be provided.
        widget_type : WidgetRef, optional
            A widget class from the current backend that should be used whenever `type_`
            is used as the type annotation for an argument in a decorated function,
            by default None
        return_callback: callable, optional
            If provided, whenever `type_` is declared as the return type of a decorated
            function, `return_callback(widget, value, return_type)` will be called
            whenever the decorated function is called... where `widget` is the Widget
            instance, and `value` is the return value of the decorated function.
        options
            key value pairs where the keys are valid `dict`

        Raises
        ------
        ValueError
            If none of `widget_type`, `return_callback`, `bind` or `choices` are
            provided.
        """
        if all(
            x is None
            for x in [
                return_callback,
                options.get("bind"),
                options.get("choices"),
                widget_type,
            ]
        ):
            raise ValueError(
                "At least one of `widget_type`, `return_callback`, `bind` or `choices` "
                "must be provided."
            )

        def _deco(type__: _T) -> _T:
            resolved_type = resolve_single_type(type__)
            self._register_type_callback(resolved_type, return_callback)
            self._register_widget(resolved_type, widget_type, **options)
            return type__

        return _deco if type_ is None else _deco(type_)

    @contextmanager
    def type_registered(
        self,
        type_: _T,
        *,
        widget_type: WidgetRef | None = None,
        return_callback: ReturnCallback | None = None,
        **options: Any,
    ) -> Iterator[None]:
        """Context manager that temporarily registers a widget type for a given `type_`.

        When the context is exited, the previous widget type associations for `type_` is
        restored.

        Parameters
        ----------
        type_ : _T
            The type for which a widget class or return callback will be provided.
        widget_type : Optional[WidgetRef]
            A widget class from the current backend that should be used whenever `type_`
            is used as the type annotation for an argument in a decorated function,
            by default None
        return_callback: Optional[callable]
            If provided, whenever `type_` is declared as the return type of a decorated
            function, `return_callback(widget, value, return_type)` will be called
            whenever the decorated function is called... where `widget` is the Widget
            instance, and `value` is the return value of the decorated function.
        options
            key value pairs where the keys are valid `dict`
        """
        resolved_type = resolve_single_type(type_)

        # store any previous widget_type and options for this type

        revert_list = self._register_type_callback(resolved_type, return_callback)
        prev_type_def = self._register_widget(resolved_type, widget_type, **options)

        new_type_def: WidgetTuple | None = self._type_defs.get(resolved_type, None)
        try:
            yield
        finally:
            # restore things to before the context
            if return_callback is not None:  # this if is only for mypy
                for return_callback_type in revert_list:
                    self._return_callbacks[return_callback_type].remove(return_callback)

            if self._type_defs.get(resolved_type, None) is not new_type_def:
                warnings.warn("Type definition changed during context", stacklevel=2)

            if prev_type_def is not None:
                self._type_defs[resolved_type] = prev_type_def
            else:
                self._type_defs.pop(resolved_type, None)

    def type2callback(self, type_: type) -> list[ReturnCallback]:
        """Return any callbacks that have been registered for ``type_``.

        Parameters
        ----------
        type_ : type
            The type_ to look up.

        Returns
        -------
        list of callable
            Where a return callback accepts two arguments (gui, value) and does
            something.
        """
        if type_ is inspect.Parameter.empty:
            return []

        # look for direct hits ...
        # if it's an Optional, we need to look for the type inside the Optional
        type_ = resolve_single_type(type_)
        if type_ in self._return_callbacks:
            return self._return_callbacks[type_]

        # look for subclasses
        for registered_type in self._return_callbacks:  # sourcery skip: use-next
            if safe_issubclass(type_, registered_type):
                return self._return_callbacks[registered_type]
        return []

    def get_widget_class(
        self,
        value: Any = Undefined,
        annotation: Any = Undefined,
        options: dict | None = None,
        is_result: bool = False,
        raise_on_unknown: bool = True,
    ) -> tuple[WidgetClass, dict]:
        """Return a [Widget][magicgui.widgets.Widget] subclass for the `value`/`annotation`.

        Parameters
        ----------
        value : Any, optional
            A python value.  Will be used to determine the widget type if an
            `annotation` is not explicitly provided by default None
        annotation : Optional[Type], optional
            A type annotation, by default None
        options : dict, optional
            Options to pass when constructing the widget, by default {}
        is_result : bool, optional
            Identifies whether the returned widget should be tailored to
            an input or to an output.
        raise_on_unknown : bool, optional
            Raise exception if no widget is found for the given type, by default True

        Returns
        -------
        Tuple[WidgetClass, dict]
            The WidgetClass, and dict that can be used for params. dict
            may be different than the options passed in.
        """  # noqa: E501
        widget_type, options_ = self._pick_widget_type(
            value=value,
            annotation=annotation,
            options=options,
            is_result=is_result,
            raise_on_unknown=raise_on_unknown,
        )

        if isinstance(widget_type, str):
            widget_class = _import_wdg_class(widget_type)
        else:
            widget_class = widget_type

        if not safe_issubclass(widget_class, widgets.bases.Widget):
            assert_protocol(widget_class, WidgetProtocol)

        return widget_class, options_

    def create_widget(
        self,
        value: Any = Undefined,
        annotation: Any | None = None,
        name: str = "",
        param_kind: str | inspect._ParameterKind = "POSITIONAL_OR_KEYWORD",
        label: str | None = None,
        gui_only: bool = False,
        app: AppRef = None,
        widget_type: str | type[WidgetProtocol] | None = None,
        options: dict | None = None,
        is_result: bool = False,
        raise_on_unknown: bool = True,
    ) -> widgets.Widget:
        """Create and return appropriate widget subclass.

        This factory function can be used to create a widget appropriate for the
        provided `value` and/or `annotation` provided. See
        [Type Mapping Docs](../type_map.md) for details on how the widget type is
        determined from type annotations.

        Parameters
        ----------
        value : Any, optional
            The starting value for the widget, by default `None`
        annotation : Any, optional
            The type annotation for the parameter represented by the widget, by default
            `None`.
        name : str, optional
            The name of the parameter represented by this widget. by default `""`
        param_kind : str, optional
            The :attr:`inspect.Parameter.kind` represented by this widget. Used in
            building signatures from multiple widgets, by default
            `"POSITIONAL_OR_KEYWORD"`
        label : str
            A string to use for an associated Label widget (if this widget is being
            shown in a [`Container`][magicgui.widgets.Container] widget, and labels are
            on). By default, `name` will be used. Note: `name` refers the name of
            the parameter, as might be used in a signature, whereas label is just the
            label for that widget in the GUI.
        gui_only : bool, optional
            Whether the widget should be considered "only for the gui", or if it should
            be included in any widget container signatures, by default False
        app : str, optional
            The backend to use, by default `None`
        widget_type : str or Type[WidgetProtocol] or None
            A class implementing a widget protocol or a string with the name of a
            magicgui widget type (e.g. "Label", "PushButton", etc...).
            If provided, this widget type will be used instead of the type
            autodetermined from `value` and/or `annotation` above.
        options : dict, optional
            Dict of options to pass to the Widget constructor, by default dict()
        is_result : boolean, optional
            Whether the widget belongs to an input or an output. By default, an input
            is assumed.
        raise_on_unknown : bool, optional
            Raise exception if no widget is found for the given type, by default True

        Returns
        -------
        Widget
            An instantiated widget subclass

        Raises
        ------
        TypeError
            If the provided or autodetected `widget_type` does not implement any known
            [widget protocols](protocols.md)

        Examples
        --------
        ```python
        from magicgui.widgets import create_widget

        # create a widget from a string value
        wdg = create_widget(value="hello world")
        assert wdg.value == "hello world"

        # create a widget from a string annotation
        wdg = create_widget(annotation=str)
        assert wdg.value == ""
        ```
        """
        options_ = options.copy() if options is not None else {}
        kwargs = {
            "value": value,
            "annotation": annotation,
            "name": name,
            "label": label,
            "gui_only": gui_only,
        }

        assert use_app(app).native
        if isinstance(widget_type, protocols.WidgetProtocol):
            wdg_class = widget_type
        else:
            if widget_type:
                options_["widget_type"] = widget_type
            # special case parameters named "password" with annotation of str
            if (
                not options_.get("widget_type")
                and (name or "").lower() == "password"
                and annotation is str
            ):
                options_["widget_type"] = "Password"

            wdg_class, opts = self.get_widget_class(
                value, annotation, options_, is_result, raise_on_unknown
            )

            if issubclass(wdg_class, widgets.Widget):
                widget = wdg_class(**{**kwargs, **opts, **options_})
                if param_kind:
                    widget.param_kind = param_kind  # type: ignore
                return widget

        # pick the appropriate subclass for the given protocol
        # order matters
        for p in ("Categorical", "Ranged", "Button", "Value", ""):
            prot = getattr(protocols, f"{p}WidgetProtocol")
            if isinstance(wdg_class, prot):
                options_ = kwargs.pop("options", None)
                cls = getattr(widgets.bases, f"{p}Widget")
                widget = cls(**{**kwargs, **(options_ or {}), "widget_type": wdg_class})
                if param_kind:
                    widget.param_kind = param_kind  # type: ignore
                return widget

        raise TypeError(f"{wdg_class!r} does not implement any known widget protocols")

    @overload
    def magicgui(
        self,
        function: Callable[_P, _R],
        *,
        layout: str = "horizontal",
        scrollable: bool = False,
        labels: bool = True,
        tooltips: bool = True,
        call_button: bool | str | None = None,
        auto_call: bool = False,
        result_widget: bool = False,
        main_window: Literal[False] = False,
        app: AppRef | None = None,
        persist: bool = False,
        raise_on_unknown: bool = False,
        **param_options: dict,
    ) -> widgets.FunctionGui[_P, _R]: ...

    @overload
    def magicgui(
        self,
        function: Literal[None] | None = None,
        *,
        layout: str = "horizontal",
        scrollable: bool = False,
        labels: bool = True,
        tooltips: bool = True,
        call_button: bool | str | None = None,
        auto_call: bool = False,
        result_widget: bool = False,
        main_window: Literal[False] = False,
        app: AppRef | None = None,
        persist: bool = False,
        raise_on_unknown: bool = False,
        **param_options: dict,
    ) -> Callable[[Callable[_P, _R]], widgets.FunctionGui[_P, _R]]: ...

    @overload
    def magicgui(
        self,
        function: Callable[_P, _R],
        *,
        layout: str = "horizontal",
        scrollable: bool = False,
        labels: bool = True,
        tooltips: bool = True,
        call_button: bool | str | None = None,
        auto_call: bool = False,
        result_widget: bool = False,
        main_window: Literal[True],
        app: AppRef | None = None,
        persist: bool = False,
        raise_on_unknown: bool = False,
        **param_options: dict,
    ) -> widgets.MainFunctionGui[_P, _R]: ...

    @overload
    def magicgui(
        self,
        function: Literal[None] | None = None,
        *,
        layout: str = "horizontal",
        scrollable: bool = False,
        labels: bool = True,
        tooltips: bool = True,
        call_button: bool | str | None = None,
        auto_call: bool = False,
        result_widget: bool = False,
        main_window: Literal[True],
        app: AppRef | None = None,
        persist: bool = False,
        raise_on_unknown: bool = False,
        **param_options: dict,
    ) -> Callable[[Callable[_P, _R]], widgets.MainFunctionGui[_P, _R]]: ...

    def magicgui(
        self,
        function: Callable | None = None,
        *,
        layout: str = "vertical",
        scrollable: bool = False,
        labels: bool = True,
        tooltips: bool = True,
        call_button: bool | str | None = None,
        auto_call: bool = False,
        result_widget: bool = False,
        main_window: bool = False,
        app: AppRef | None = None,
        persist: bool = False,
        raise_on_unknown: bool = False,
        **param_options: dict,
    ) -> Callable | widgets.FunctionGui:
        """Return a [`FunctionGui`][magicgui.widgets.FunctionGui] for `function`.

        Parameters
        ----------
        function : Callable, optional
            The function to decorate.  Optional to allow bare decorator with optional
            arguments. by default `None`
        layout : str, optional
            The type of layout to use. Must be `horizontal` or `vertical`
            by default "vertical".
        scrollable : bool, optional
            Whether to enable scroll bars or not. If enabled, scroll bars will
            only appear along the layout direction, not in both directions.
        labels : bool, optional
            Whether labels are shown in the widget. by default True
        tooltips : bool, optional
            Whether tooltips are shown when hovering over widgets. by default True
        call_button : bool or str, optional
            If `True`, create an additional button that calls the original
            function when clicked.  If a `str`, set the button text. If None (the
            default), it defaults to True when `auto_call` is False, and False
            otherwise.
        auto_call : bool, optional
            If `True`, changing any parameter in either the GUI or the widget attributes
            will call the original function with the current settings. by default False
        result_widget : bool, optional
            Whether to display a LineEdit widget the output of the function when called,
            by default False
        main_window : bool
            Whether this widget should be treated as the main app window, with menu bar,
            by default False.
        app : magicgui.Application or str, optional
            A backend to use, by default `None` (use the default backend.)
        persist : bool, optional
            If `True`, when parameter values change in the widget, they will be stored
            to disk and restored when the widget is loaded again with `persist = True`.
            Call `magicgui._util.user_cache_dir()` to get the default cache location.
            By default False.
        raise_on_unknown : bool, optional
            If `True`, raise an error if magicgui cannot determine widget for function
            argument or return type. If `False`, ignore unknown types. By default False.
        param_options : dict[str, dict]
            Any additional keyword arguments will be used as parameter-specific options.
            Keywords must match the name of one of the arguments in the function
            signature, and the value must be a dict of keyword arguments to pass to the
            widget constructor.

        Returns
        -------
        result : FunctionGui or Callable[[F], FunctionGui]
            If `function` is not `None` (such as when this is used as a bare decorator),
            returns a FunctionGui instance, which is a list-like container of
            autogenerated widgets corresponding to each parameter in the function.
            If `function` is `None` such as when arguments are provided like
            `magicgui(auto_call=True)`, then returns a function that can be used as a
            decorator.

        Examples
        --------
        >>> @magicgui
        ... def my_function(a: int = 1, b: str = "hello"):
        ...     pass
        >>> my_function.show()
        >>> my_function.a.value == 1  # True
        >>> my_function.b.value = "world"
        """
        return self._magicgui(
            function=function,
            layout=layout,
            scrollable=scrollable,
            labels=labels,
            tooltips=tooltips,
            call_button=call_button,
            auto_call=auto_call,
            result_widget=result_widget,
            main_window=main_window,
            app=app,
            persist=persist,
            raise_on_unknown=raise_on_unknown,
            param_options=param_options,
        )

    @overload
    def magic_factory(
        self,
        function: Callable[_P, _R],
        *,
        layout: str = "horizontal",
        scrollable: bool = False,
        labels: bool = True,
        tooltips: bool = True,
        call_button: bool | str | None = None,
        auto_call: bool = False,
        result_widget: bool = False,
        main_window: Literal[False] = False,
        app: AppRef | None = None,
        persist: bool = False,
        widget_init: Callable[[widgets.FunctionGui], None] | None = None,
        raise_on_unknown: bool = False,
        **param_options: dict,
    ) -> MagicFactory[widgets.FunctionGui[_P, _R]]: ...

    @overload
    def magic_factory(
        self,
        function: Literal[None] | None = None,
        *,
        layout: str = "horizontal",
        scrollable: bool = False,
        labels: bool = True,
        tooltips: bool = True,
        call_button: bool | str | None = None,
        auto_call: bool = False,
        result_widget: bool = False,
        main_window: Literal[False] = False,
        app: AppRef | None = None,
        persist: bool = False,
        widget_init: Callable[[widgets.FunctionGui], None] | None = None,
        raise_on_unknown: bool = False,
        **param_options: dict,
    ) -> Callable[[Callable[_P, _R]], MagicFactory[widgets.FunctionGui[_P, _R]]]: ...

    @overload
    def magic_factory(
        self,
        function: Callable[_P, _R],
        *,
        layout: str = "horizontal",
        scrollable: bool = False,
        labels: bool = True,
        tooltips: bool = True,
        call_button: bool | str | None = None,
        auto_call: bool = False,
        result_widget: bool = False,
        main_window: Literal[True],
        app: AppRef | None = None,
        persist: bool = False,
        widget_init: Callable[[widgets.FunctionGui], None] | None = None,
        raise_on_unknown: bool = False,
        **param_options: dict,
    ) -> MagicFactory[widgets.MainFunctionGui[_P, _R]]: ...

    @overload
    def magic_factory(
        self,
        function: Literal[None] | None = None,
        *,
        layout: str = "horizontal",
        scrollable: bool = False,
        labels: bool = True,
        tooltips: bool = True,
        call_button: bool | str | None = None,
        auto_call: bool = False,
        result_widget: bool = False,
        main_window: Literal[True],
        app: AppRef | None = None,
        persist: bool = False,
        widget_init: Callable[[widgets.FunctionGui], None] | None = None,
        raise_on_unknown: bool = False,
        **param_options: dict,
    ) -> Callable[
        [Callable[_P, _R]], MagicFactory[widgets.MainFunctionGui[_P, _R]]
    ]: ...

    def magic_factory(
        self,
        function: Callable | None = None,
        *,
        layout: str = "vertical",
        scrollable: bool = False,
        labels: bool = True,
        tooltips: bool = True,
        call_button: bool | str | None = None,
        auto_call: bool = False,
        result_widget: bool = False,
        main_window: bool = False,
        app: AppRef | None = None,
        persist: bool = False,
        widget_init: Callable[[widgets.FunctionGui], None] | None = None,
        raise_on_unknown: bool = False,
        **param_options: dict,
    ) -> Callable | MagicFactory:
        """Return a [`MagicFactory`][magicgui.type_map._magicgui.MagicFactory] for function.

        `magic_factory` is nearly identical to the [`magicgui`][magicgui.magicgui]
        decorator with the following differences:

        1. Whereas `magicgui` returns a `FunctionGui` instance, `magic_factory` returns
        a callable that returns a `FunctionGui` instance. (Technically, it returns an
        instance of [`MagicFactory`][magicgui.type_map._magicgui.MagicFactory] which you
        behaves exactly like a [`functools.partial`][functools.partial]
        for a `FunctionGui` instance.)
        2. `magic_factory` adds a `widget_init` method: a callable that will be called
            immediately after the `FunctionGui` instance is created.  This can be used
            to add additional widgets to the layout, or to connect signals to the
            widgets.

        !!!important
            Whereas decorating a function with `magicgui` will **immediately** create a
            widget instance, `magic_factory` will **not** create a widget instance until
            the decorated object is called.  This is often what you want in a library,
            whereas `magicgui` is useful for rapid, interactive development.

        Parameters
        ----------
        function : Callable, optional
            The function to decorate.  Optional to allow bare decorator with optional
            arguments. by default `None`
        layout : str, optional
            The type of layout to use. Must be `horizontal` or `vertical`
            by default "vertical".
        scrollable : bool, optional
            Whether to enable scroll bars or not. If enabled, scroll bars will
            only appear along the layout direction, not in both directions.
        labels : bool, optional
            Whether labels are shown in the widget. by default True
        tooltips : bool, optional
            Whether tooltips are shown when hovering over widgets. by default True
        call_button : bool or str, optional
            If `True`, create an additional button that calls the original
            function when clicked.  If a `str`, set the button text. If None (the
            default), it defaults to True when `auto_call` is False, and False
            otherwise.
        auto_call : bool, optional
            If `True`, changing any parameter in either the GUI or the widget
            attributes will call the original function with the current settings. by
            default False
        result_widget : bool, optional
            Whether to display a LineEdit widget the output of the function when called,
            by default False
        main_window : bool
            Whether this widget should be treated as the main app window, with menu bar,
            by default False.
        app : magicgui.Application or str, optional
            A backend to use, by default `None` (use the default backend.)
        persist : bool, optional
            If `True`, when parameter values change in the widget, they will be stored
            to disk and restored when the widget is loaded again with `persist = True`.
            Call `magicgui._util.user_cache_dir()` to get the default cache location.
            By default False.
        widget_init : callable, optional
            A function that will be called with the newly created widget instance as its
            only argument.  This can be used to customize the widget after it is
            created. by default `None`.
        raise_on_unknown : bool, optional
            If `True`, raise an error if magicgui cannot determine widget for function
            argument or return type. If `False`, ignore unknown types. By default False.
        param_options : dict of dict
            Any additional keyword arguments will be used as parameter-specific widget
            options. Keywords must match the name of one of the arguments in the
            function signature, and the value must be a dict of keyword arguments to
            pass to the widget constructor.

        Returns
        -------
        result : MagicFactory or Callable[[F], MagicFactory]
            If `function` is not `None` (such as when this is used as a bare
            decorator), returns a MagicFactory instance.
            If `function` is `None` such as when arguments are provided like
            `magic_factory(auto_call=True)`, then returns a function that can be used
            as a decorator.

        Examples
        --------
        >>> @magic_factory
        ... def my_function(a: int = 1, b: str = "hello"):
        ...     pass
        >>> my_widget = my_function()
        >>> my_widget.show()
        >>> my_widget.a.value == 1  # True
        >>> my_widget.b.value = "world"
        """  # noqa: E501
        return self._magicgui(
            factory=True,
            function=function,
            layout=layout,
            scrollable=scrollable,
            labels=labels,
            tooltips=tooltips,
            call_button=call_button,
            auto_call=auto_call,
            result_widget=result_widget,
            main_window=main_window,
            app=app,
            persist=persist,
            widget_init=widget_init,
            raise_on_unknown=raise_on_unknown,
            param_options=param_options,
        )

    def _pick_widget_type(
        self,
        value: Any = Undefined,
        annotation: Any = Undefined,
        options: dict | None = None,
        is_result: bool = False,
        raise_on_unknown: bool = True,
    ) -> WidgetTuple:
        """Pick the appropriate widget type for ``value`` with ``annotation``."""
        annotation, options_ = _split_annotated_type(annotation)
        options = {**options_, **(options or {})}
        choices = options.get("choices")

        if is_result and annotation is inspect.Parameter.empty:
            annotation = str

        if (
            value is Undefined
            and annotation in (Undefined, inspect.Parameter.empty)
            and not choices
            and "widget_type" not in options
        ):
            return widgets.EmptyWidget, {"visible": False, **options}

        type_, optional = _type_optional(value, annotation)
        options.setdefault("nullable", optional)
        choices = choices or (isinstance(type_, EnumMeta) and type_)
        literal_choices, nullable = _literal_choices(annotation)
        if literal_choices is not None:
            choices = literal_choices
            options["nullable"] = nullable

        if "widget_type" in options:
            widget_type = options.pop("widget_type")
            if choices:
                if widget_type == "RadioButton":
                    widget_type = "RadioButtons"
                    warnings.warn(
                        f"widget_type of 'RadioButton' (with dtype {type_}) is"
                        " being coerced to 'RadioButtons' due to choices or Enum type.",
                        stacklevel=2,
                    )
                options.setdefault("choices", choices)
            return widget_type, options

        # look for subclasses
        for registered_type in self._type_defs:
            if type_ == registered_type or safe_issubclass(type_, registered_type):
                cls_, opts = self._type_defs[registered_type]
                return cls_, {**options, **opts}

        if is_result:
            widget_type_ = self.match_return_type(type_)
            if widget_type_:
                cls_, opts = widget_type_
                return cls_, {**opts, **options}
            # Chosen for backwards/test compatibility
            return widgets.LineEdit, {"gui_only": True}

        if choices:
            options["choices"] = choices
            wdg = widgets.Select if options.get("allow_multiple") else widgets.ComboBox
            return wdg, options

        widget_type_ = self.match_type(type_, value)
        if widget_type_:
            cls_, opts = widget_type_
            return cls_, {**opts, **options}

        if raise_on_unknown:
            raise ValueError(
                f"No widget found for type {type_} and annotation {annotation!r}"
            )

        options["visible"] = False
        return widgets.EmptyWidget, options

    def _register_type_callback(
        self,
        resolved_type: _T,
        return_callback: ReturnCallback | None = None,
    ) -> list[type]:
        modified_callbacks = []
        if return_callback is None:
            return []
        _validate_return_callback(return_callback)
        # if the type is a Union, add the callback to all of the types in the union
        # (except NoneType)
        if get_origin(resolved_type) is Union:
            for type_per in _generate_union_variants(resolved_type):
                if return_callback not in self._return_callbacks[type_per]:
                    self._return_callbacks[type_per].append(return_callback)
                    modified_callbacks.append(type_per)

            for t in get_args(resolved_type):
                if (
                    not _is_none_type(t)
                    and return_callback not in self._return_callbacks[t]
                ):
                    self._return_callbacks[t].append(return_callback)
                    modified_callbacks.append(t)
        elif return_callback not in self._return_callbacks[resolved_type]:
            self._return_callbacks[resolved_type].append(return_callback)
            modified_callbacks.append(resolved_type)
        return modified_callbacks

    def _register_widget(
        self,
        resolved_type: _T,
        widget_type: WidgetRef | None = None,
        **options: Any,
    ) -> WidgetTuple | None:
        _options = cast(dict, options)

        previous_widget = self._type_defs.get(resolved_type)

        if "choices" in _options:
            self._type_defs[resolved_type] = (widgets.ComboBox, _options)
            if widget_type is not None:
                warnings.warn(
                    "Providing `choices` overrides `widget_type`. Categorical widget "
                    f"will be used for type {resolved_type}",
                    stacklevel=2,
                )
        elif widget_type is not None:
            if not isinstance(widget_type, (str, WidgetProtocol)) and not (
                inspect.isclass(widget_type) and issubclass(widget_type, widgets.Widget)
            ):
                raise TypeError(
                    '"widget_type" must be either a string, WidgetProtocol, or '
                    "Widget subclass"
                )
            self._type_defs[resolved_type] = (widget_type, _options)
        elif "bind" in _options:
            # if we're binding a value to this parameter, it doesn't matter what type
            # of ValueWidget is used... it usually won't be shown
            self._type_defs[resolved_type] = (widgets.EmptyWidget, _options)
        return previous_widget

    def _magicgui(
        self,
        function: Callable | None = None,
        factory: bool = False,
        widget_init: Callable | None = None,
        main_window: bool = False,
        **kwargs: Any,
    ) -> Callable:
        """Actual private magicui decorator.

        if factory is `True` will return a MagicFactory instance, that can be called
        to return a `FunctionGui` instance.  See docstring of ``magicgui`` for
        parameters. Otherwise, this will return a FunctionGui instance directly.
        """
        from magicgui.type_map._magicgui import MagicFactory

        def inner_func(func: Callable) -> widgets.FunctionGui | MagicFactory:
            if not callable(func):
                raise TypeError("the first argument must be callable")

            magic_class = (
                widgets.MainFunctionGui if main_window else widgets.FunctionGui
            )

            if factory:
                return MagicFactory(
                    func,
                    magic_class=magic_class,
                    widget_init=widget_init,
                    type_map=self,
                    **kwargs,
                )
            # MagicFactory is unnecessary if we are immediately instantiating the
            # widget, so we shortcut that and just return the FunctionGui here.
            return cast(widgets.FunctionGui, magic_class(func, type_map=self, **kwargs))

        return inner_func if function is None else inner_func(function)


_GLOBAL_TYPE_MAP = TypeMap()
get_widget_class = _GLOBAL_TYPE_MAP.get_widget_class
register_type = _GLOBAL_TYPE_MAP.register_type
type2callback = _GLOBAL_TYPE_MAP.type2callback
type_registered = _GLOBAL_TYPE_MAP.type_registered


def _is_none_type(type_: Any) -> bool:
    return any(type_ is x for x in {None, type(None), Literal[None]})


def _type_optional(
    default: Any = Undefined,
    annotation: type[Any] | _Undefined = Undefined,
) -> tuple[Any, bool]:
    type_ = annotation
    if annotation in (Undefined, None, inspect.Parameter.empty):
        if default is not Undefined:
            type_ = type(default)
    else:
        try:
            type_ = resolve_single_type(annotation)
        except (NameError, ImportError) as e:
            raise type(e)(f"Magicgui could not resolve {annotation}: {e}") from e

    # look for Optional[Type], which manifests as Union[Type, None]
    nullable = default is None
    if type_ is not Undefined:
        args = get_args(type_)
        for arg in args:
            if _is_none_type(arg) or arg is Any or arg is object:
                nullable = True
                if len(args) == 2:
                    type_ = next(i for i in args if i is not arg)
                break

    return type_, nullable


def _literal_choices(annotation: Any) -> tuple[list | None, bool]:
    """Return choices and nullable for a Literal type.

    if annotation is not a Literal type, returns (None, False)
    """
    origin = get_origin(annotation) or annotation
    choices: list | None = None
    nullable = False
    if origin is Literal:
        choices = []
        for choice in get_args(annotation):
            if choice is None:
                nullable = True
            else:
                choices.append(choice)
    return choices, nullable


def _split_annotated_type(annotation: Any) -> tuple[Any, dict]:
    """Split an Annotated type into its base type and options dict."""
    if get_origin(annotation) is not Annotated:
        return annotation, {}

    type_, meta_, *_ = get_args(annotation)

    try:
        meta = dict(meta_)
    except TypeError:
        meta = {}

    return type_, meta


def _import_wdg_class(class_name: str) -> WidgetClass:
    import importlib

    # import from magicgui widgets if not explicitly namespaced
    if "." not in class_name:
        class_name = f"magicgui.widgets.{class_name}"

    mod_name, name = class_name.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    return cast(WidgetClass, getattr(mod, name))


def _validate_return_callback(func: Callable) -> None:
    try:
        sig = inspect.signature(func)
        # the signature must accept three arguments
        sig.bind(1, 2, 3)  # (gui, result, return_type)
    except TypeError as e:
        raise TypeError(f"object {func!r} is not a valid return callback: {e}") from e


def _generate_union_variants(type_: Any) -> Iterator[type]:
    type_args = get_args(type_)
    for i in range(2, len(type_args) + 1):
        for per in itertools.combinations(type_args, i):
            yield cast(type, Union[per])
