"""MagicSignature objects are an extension to inspect.Signature objects.

The basic idea is that there is a tight connection between an individual Parameter
in a function signature and an individual magicgui.Widget, and a connection between
a full function Signature (a collection of parameters) and a magicgui.Container
(a collection of widgets).  It should be easy to go from function signature to Container
(with ``MagicSignature.to_container()``) and from Container to signature (using
``ContainerWidget.to_signature()``).

calling ``inspect.signature`` on a function decorated with `magicgui` still works,
(it returns a ``MagicSignature``, which is a subclass of ``inspect.Signature``)

"""
from __future__ import annotations

import inspect
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, Sequence, cast

from typing_extensions import Annotated, get_args, get_origin

from magicgui.types import Undefined

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from magicgui.application import AppRef
    from magicgui.widgets import Container, Widget
    from magicgui.widgets.bases._container_widget import ContainerKwargs

TZ_EMPTY = "__no__default__"


def make_annotated(annotation: Any = Any, options: dict | None = None) -> Any:
    """Merge a annotation and an options dict into an Annotated type.

    Parameters
    ----------
    annotation : Any, optional
        Type Annotation, by default Any
    options : dict, optional
        widget options, by default None

    Returns
    -------
    Annotated
        Annotated type with form ``Annotated[annotation, options]``

    Raises
    ------
    TypeError
        If options is provided and is not a dict
        If ``annotation`` is an Annotated option but the metadata is not a dict
        If ``annotation`` is not a valid type.
    """
    if options and not isinstance(options, dict):
        raise TypeError("'options' must be a dict")
    _options = (options or {}).copy()

    if get_origin(annotation) is Annotated:
        # nested Annotated type results in multiple dicts.
        annotation, *anno_options = get_args(annotation)
        for opt in anno_options:
            try:
                _opt = dict(opt)
            except (TypeError, ValueError) as e:
                raise TypeError(
                    f"Every item in Annotated must be castable to a dict, got: {opt!r}"
                ) from e
            _options.update(_opt)
    return Annotated[annotation, _options]


class _void:
    """private sentinel."""


class MagicParameter(inspect.Parameter):
    """A Parameter subclass that is closely linked to a magicgui.Widget object.

    Parameters
    ----------
    name : str, optional
        The name of the parameter represented by this widget. by default ""
    kind : inspect._ParameterKind, optional
        The :attr:`inspect.Parameter.kind` represented by this widget.  Used in building
        signatures from multiple widgets, by default "POSITIONAL_OR_KEYWORD"
    default : Any, optional
        The default value for the parameter, by default None
    annotation : Any, optional
        The type annotation for the parameter represented by the widget, by default
        None
    options : dict, optional
        Dict of options to pass to the Widget constructor, by default dict()

    """

    def __init__(
        self,
        name: str,
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        *,
        default: Any = inspect.Parameter.empty,
        annotation: Any = inspect.Parameter.empty,
        gui_options: dict | None = None,
        raise_on_unknown: bool = False,
    ):
        _annotation = make_annotated(annotation, gui_options)
        super().__init__(name, kind, default=default, annotation=_annotation)
        self.raise_on_unknown = raise_on_unknown

    @property
    def options(self) -> dict:
        """Return just this options part of the annotation."""
        return cast(dict, get_args(self.annotation)[1])

    def __repr__(self) -> str:
        """Return __repr__, replacing NoneType if present."""
        rep = f"{super().__repr__()[:-1]} {self.options}>"
        rep = rep.replace(": NoneType = ", "=")
        return rep

    def __str__(self) -> str:
        """Return string representation of the Parameter in a signature."""
        hint, _ = get_args(self.annotation)
        return str(
            inspect.Parameter(
                self.name, self.kind, default=self.default, annotation=hint
            )
        )

    def to_widget(self, app: AppRef | None = None) -> Widget:
        """Create and return a widget for this object."""
        from magicgui.widgets import create_widget

        value = Undefined if self.default in (self.empty, TZ_EMPTY) else self.default
        widget = create_widget(
            name=self.name,
            value=value,
            annotation=self.annotation,
            app=app,
            raise_on_unknown=self.raise_on_unknown,
        )
        widget.param_kind = self.kind
        return widget

    @classmethod
    def from_widget(cls, widget: Widget) -> MagicParameter:
        """Create a MagicParameter object representing a widget."""
        return cls(
            name=str(widget.name),
            kind=widget.param_kind,
            default=getattr(widget, "value", inspect.Parameter.empty),
            annotation=widget.annotation,
            gui_options=widget.options,
        )

    @classmethod
    def from_parameter(
        cls,
        param: inspect.Parameter,
        gui_options: dict | None = None,
        raise_on_unknown: bool = False,
    ) -> MagicParameter:
        """Create MagicParameter from an inspect.Parameter."""
        if isinstance(param, MagicParameter):
            return param
        return cls(
            param.name,
            param.kind,
            default=param.default,
            annotation=param.annotation,
            gui_options=gui_options,
            raise_on_unknown=raise_on_unknown,
        )


class MagicSignature(inspect.Signature):
    """A Signature subclass that is closely linked to a magicgui.Container object.

    Parameters
    ----------
    parameters : Optional[Sequence[inspect.Parameter]], optional
        A list of parameters to include in the Signature, by default None
    return_annotation : Type or str, optional
        An optional return annotation to use when representing this container of
        widgets as an inspect.Signature, by default inspect.Signature.empty
    gui_options : Optional[Dict[str, dict]], optional
        A mapping of parameter name to options for each individual parameter,
        by default None
    """

    parameters: MappingProxyType[str, MagicParameter]

    def __init__(
        self,
        parameters: Sequence[inspect.Parameter] | None = None,
        *,
        return_annotation: Any = inspect.Signature.empty,
        gui_options: dict[str, dict] | None = None,
        raise_on_unknown: bool = False,
    ) -> None:
        params = [
            MagicParameter.from_parameter(
                p, (gui_options or {}).get(p.name), raise_on_unknown
            )
            for p in parameters or []
        ]
        super().__init__(params, return_annotation=return_annotation)

    @classmethod
    def from_signature(
        cls,
        sig: inspect.Signature,
        gui_options: dict | None = None,
        raise_on_unknown: bool = False,
    ) -> MagicSignature:
        """Convert regular inspect.Signature to MagicSignature."""
        if type(sig) is cls:
            return sig
        elif not isinstance(sig, inspect.Signature):
            raise TypeError("'sig' must be an instance of 'inspect.Signature'")
        return cls(
            list(sig.parameters.values()),
            return_annotation=sig.return_annotation,
            gui_options=gui_options,
            raise_on_unknown=raise_on_unknown,
        )

    def widgets(self, app: AppRef | None = None) -> MappingProxyType:
        """Return mapping from parameters to widgets for all params in Signature."""
        return MappingProxyType(
            {n: p.to_widget(app) for n, p in self.parameters.items()}
        )

    def to_container(
        self, app: AppRef | None = None, **kwargs: Unpack[ContainerKwargs]
    ) -> Container:
        """Return a ``magicgui.widgets.Container`` for this MagicSignature."""
        from magicgui.widgets import Container

        kwargs["widgets"] = list(self.widgets(app).values())
        return Container(**kwargs)

    def replace(  # type: ignore[override]
        self,
        *,
        parameters: Sequence[inspect.Parameter] | type[_void] = _void,
        return_annotation: Any = _void,
    ) -> MagicSignature:
        """Create a customized copy of the Signature.

        Pass ``parameters`` and/or ``return_annotation`` arguments
        to override them in the new copy.
        """
        if parameters is _void:
            parameters = list(self.parameters.values())

        if return_annotation is _void:
            return_annotation = self.return_annotation

        return type(self)(
            cast(Sequence[inspect.Parameter], parameters),
            return_annotation=return_annotation,
        )


def magic_signature(
    obj: Callable,
    *,
    gui_options: dict[str, dict] | None = None,
    follow_wrapped: bool = True,
    raise_on_unknown: bool = False,
) -> MagicSignature:
    """Create a MagicSignature from a callable object.

    This is magicgui's equivalent of ``inspect.signature`` and is a core
    part of the FunctionGui creation when using the `@magicgui` decorator.

    Parameters
    ----------
    obj : Callable
        The function being inspected.
    gui_options : Optional[Dict[str, dict]], optional
        A dict of name: widget_options dict for each parameter in the function.
        Will be passed to `MagicSignature.from_signature` by default None
    follow_wrapped : bool, optional
        passed to inspect.signature, by default True
    raise_on_unknown : bool, optional
        If True, raise an error if a parameter annotation is not recognized.

    Returns
    -------
    MagicSignature
        Signature object representing the callable.

    Raises
    ------
    ValueError
        If ``gui_options`` are provided with keyword arguments that do not match
        parameters in the decorated function.
    TypeError
        If any of the values in ``gui_options`` are not dicts.
    """
    sig = inspect.signature(obj, follow_wrapped=follow_wrapped)
    if gui_options:
        invalid = set(gui_options) - set(sig.parameters)
        if invalid:
            raise ValueError(
                f"Received parameter option key(s) {invalid} that do not match "
                f"parameters in the provided function: {sig}"
            )
        bad = {v for v in gui_options.values() if not isinstance(v, dict)}
        if bad:
            s = "s" if len(bad) > 1 else ""
            raise TypeError(f"Value for parameter{s} {bad} must be a dict")

    return MagicSignature.from_signature(
        sig, gui_options=gui_options, raise_on_unknown=raise_on_unknown
    )
