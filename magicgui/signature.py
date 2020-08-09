from enum import EnumMeta
from inspect import Parameter, Signature, _ParameterKind, signature
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

from typing_extensions import Annotated, _AnnotatedAlias

from magicgui.application import AppRef
from magicgui.widget import Widget

if TYPE_CHECKING:
    from magicgui.container import Container


def make_annotated(annotation=Any, options: Optional[dict] = None) -> _AnnotatedAlias:
    """Merge a annotation and an options dict into an Annotated type.

    Parameters
    ----------
    annotation : [type], optional
        [description], by default Any
    options : Optional[dict], optional
        [description], by default None

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
    _options = (options or dict()).copy()
    if isinstance(annotation, EnumMeta):
        _options.setdefault("choices", annotation)

    if isinstance(annotation, _AnnotatedAlias):
        hint, anno_options = split_annotated_type(annotation)
        _options.update(anno_options)
        annotation = hint
    annotation = Any if annotation is Parameter.empty else annotation
    return Annotated[annotation, _options]


def split_annotated_type(annotation: _AnnotatedAlias) -> Tuple[Any, Dict[str, Any]]:
    if not isinstance(annotation, _AnnotatedAlias):
        raise TypeError("Type hint must be an 'Annotated' type.")
    if not isinstance(annotation.__metadata__[0], dict):
        raise TypeError(
            "Invalid Annotated format for magicgui. First arg must be a dict"
        )
    return annotation.__args__[0], annotation.__metadata__[0]


class MagicParameter(Parameter):
    def __init__(
        self,
        name: str,
        kind: _ParameterKind = Parameter.POSITIONAL_OR_KEYWORD,
        *,
        default: Any = Parameter.empty,
        annotation: Any = Parameter.empty,
        options: Optional[dict] = None,
    ):
        if annotation is Parameter.empty:
            annotation = Any if default is Parameter.empty else type(default)
        _annotation = make_annotated(annotation, options)
        super().__init__(name, kind, default=default, annotation=_annotation)

    @classmethod
    def from_parameter(cls, param: Parameter):
        if isinstance(param, MagicParameter):
            return param
        return cls(
            param.name, param.kind, default=param.default, annotation=param.annotation
        )

    @property
    def options(self) -> dict:
        return split_annotated_type(self.annotation)[1]

    @property
    def is_mandatory(self) -> bool:
        if self.kind in (self.POSITIONAL_OR_KEYWORD, self.POSITIONAL_ONLY):
            return self.default is self.empty
        return False

    def __repr__(self):
        return super().__repr__()[:-1] + f" {self.options}>"

    def __str__(self):
        # discard options for repr
        hint, _ = split_annotated_type(self.annotation)
        return str(
            Parameter(self.name, self.kind, default=self.default, annotation=hint)
        )

    def to_widget(self, app: AppRef = None):
        value = None if self.default is self.empty else self.default
        annotation, options = split_annotated_type(self.annotation)
        return Widget(
            value, annotation, options=options, app=app, name=self.name, kind=self.kind,
        )


class MagicSignature(Signature):
    parameters: Mapping[str, MagicParameter]

    def __init__(
        self,
        parameters: Optional[Sequence[Parameter]] = None,
        *,
        return_annotation=Signature.empty,
    ):
        params = [MagicParameter.from_parameter(p) for p in parameters or []]
        super().__init__(params, return_annotation=return_annotation)

    @classmethod
    def from_signature(cls, sig: Signature):
        if type(sig) is cls:
            return sig
        elif not isinstance(sig, Signature):
            raise TypeError("'sig' must be an instance of 'inspect.Signature'")
        return cls(
            list(sig.parameters.values()), return_annotation=sig.return_annotation,
        )

    def widgets(self, app: AppRef = None):
        return MappingProxyType(
            {n: p.to_widget(app) for n, p in self.parameters.items()}
        )

    def to_container(self, app: AppRef = None) -> "Container":
        from magicgui.container import Container

        return Container(
            app=app,
            widgets=list(self.widgets(app).values()),
            return_annotation=self.return_annotation,
        )


def magic_signature(obj: Callable, *, follow_wrapped: bool = True) -> MagicSignature:
    sig = signature(obj, follow_wrapped=follow_wrapped)
    return MagicSignature.from_signature(sig)
