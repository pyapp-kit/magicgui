"""
The vast majority of this module is borrowed with modification from
`pydantic.fields` and `pydantic.typing`.

this module removes all of the field validation logic, and adds
some forward_ref resolution methods.

The MIT License (MIT)

Copyright (c) 2017, 2018, 2019, 2020, 2021 Samuel Colvin and other contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import sys
from collections import abc
from inspect import Parameter
from typing import _eval_type  # type: ignore  # noqa
from typing import (
    Any,
    Callable,
    Counter,
    DefaultDict,
    Deque,
    Dict,
    ForwardRef,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    NewType,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from typing_extensions import Annotated, Literal, get_args, get_origin

__all__ = ["TypeWrapper"]


Required: Any = Ellipsis


class SHAPE:
    SINGLETON = 1
    LIST = 2
    SET = 3
    MAPPING = 4
    TUPLE = 5
    TUPLE_ELLIPSIS = 6
    SEQUENCE = 7
    FROZENSET = 8
    ITERABLE = 9
    GENERIC = 10
    DEQUE = 11
    DICT = 12
    DEFAULTDICT = 13
    COUNTER = 14

    MAPPING_LIKE: Set[int] = {DEFAULTDICT, DICT, MAPPING, COUNTER}
    SEQUENCE_LIKE: Set[int] = {LIST, TUPLE, TUPLE_ELLIPSIS, SEQUENCE, DEQUE}
    NAME_LOOKUP = {
        LIST: "List[{}]",
        SET: "Set[{}]",
        TUPLE_ELLIPSIS: "Tuple[{}, ...]",
        SEQUENCE: "Sequence[{}]",
        FROZENSET: "FrozenSet[{}]",
        ITERABLE: "Iterable[{}]",
        DEQUE: "Deque[{}]",
        DICT: "Dict[{}]",
        DEFAULTDICT: "DefaultDict[{}]",
        COUNTER: "Counter[{}]",
    }


class TypeWrapper:
    SHAPE = SHAPE

    def __init__(
        self, type_: Union[str, Type[Any], None, ForwardRef] = None, default: Any = None
    ) -> None:
        if default is None and type_ in (None, Parameter.empty):
            raise ValueError("Either `type_` or `default` must be defined.")

        if type_ is not None:
            type_ = resolve_annotation(type_)

        self.type_: Any = type_
        self.default: Any = default
        self.required: bool = None  # type: ignore  # will be set in _prepare

        self.outer_type_: Any = type_
        self.allow_none: bool = False
        self.sub_fields: Optional[List[TypeWrapper]] = None
        self._annotated_meta: tuple = ()
        self.key_field: Optional[TypeWrapper] = None
        self.shape: int = SHAPE.SINGLETON
        self._prepare()

    @property
    def is_union(self):
        return is_union(get_origin(self.type_))

    def is_subclass(self, class_or_tuple: Union[Type, Tuple[Union[Type, Tuple], ...]]):
        try:
            return issubclass(self.outer_type_, class_or_tuple)
        except TypeError:
            return False

    def is_superclass(self, other: Type):
        try:
            return issubclass(other, self.outer_type_)
        except TypeError:
            types = tuple(sf.outer_type_ for sf in self.sub_fields or ())
            try:
                return issubclass(other, types)
            except TypeError:
                pass
        return False

    @property
    def is_resolved(self) -> bool:
        if self.type_.__class__ is ForwardRef:
            return False
        if self.outer_type_.__class__ is ForwardRef:
            return False
        if self.sub_fields:
            return all(f.is_resolved for f in self.sub_fields)
        return True

    def resolve(self, ns: Optional[Mapping[str, Any]] = None, allow_import=True):
        """May raise a NameError, or a ModuleNotFoundError."""
        if self.is_resolved:
            return self.outer_type_

        err_msg = f"Magicgui could not resolve {self._type_display()}"
        try:
            self.type_ = resolve_annotation(
                self.type_, ns, allow_import=allow_import, raise_=True
            )
            self.outer_type_ = resolve_annotation(
                self.outer_type_, ns, allow_import=allow_import, raise_=True
            )
            for f in self.sub_fields or ():
                f.resolve(ns, allow_import=allow_import)
        except (NameError, ImportError) as e:
            raise type(e)(f"{err_msg}: {e}") from e
        return self.outer_type_

    def _prepare(self) -> None:
        """not idempotent"""
        self._set_default_and_type()
        if self.type_.__class__ is not ForwardRef:
            self._type_analysis()
        if self.required is None:
            self.required = True

    def _set_default_and_type(self) -> Any:
        if self.default is not None:
            if self.type_ in (None, Parameter.empty):
                self.outer_type_ = self.type_ = self.default.__class__
        elif self.required is False:
            self.allow_none = True

    def _type_analysis(self):
        # See pydantic.fields.ModelField._type_analysis
        if isinstance(self.type_, TypeVar):
            if self.type_.__bound__:
                self.type_ = self.type_.__bound__
            elif self.type_.__constraints__:
                # constraints will always be len > 1 if present
                self.type_ = Union[self.type_.__constraints__]
            else:
                self.type_ = Any
        elif is_new_type(self.type_):
            self.type_ = new_type_supertype(self.type_)
        if self.type_ is Any or self.type_ is object:
            if self.required is None:
                self.required = False
            self.allow_none = True
            return
        elif is_literal_type(self.type_):
            return

        origin = get_origin(self.type_)

        if origin is Annotated:
            self.type_, *rest = get_args(self.type_)
            self._annotated_meta = tuple(rest)
            self._type_analysis()
            return

        # add extra check for `collections.abc.Hashable` for python 3.10+ where origin
        # is not `None`
        if origin is None or origin is abc.Hashable:
            # field is not "typing" object eg. Union, Dict, List etc.
            # allow None for virtual superclasses of NoneType, e.g. Hashable
            if isinstance(self.type_, type) and isinstance(None, self.type_):
                self.allow_none = True
            return
        elif origin is Callable:
            return
        elif is_union(origin):
            types_ = []
            for type_ in get_args(self.type_):
                if is_none_type(type_) or type_ is Any or type_ is object:
                    if self.required is None:
                        self.required = False
                    self.allow_none = True
                if is_none_type(type_):
                    continue
                types_.append(type_)

            if len(types_) == 1:
                # Optional[]
                self.type_ = types_[0]
                # this is the one case where the "outer type" isn't just
                # the original type
                self.outer_type_ = self.type_
                # re-run to correctly interpret the new self.type_
                self._type_analysis()
            else:
                self.sub_fields = [self.__class__(type_=t) for t in types_]
            return
        elif issubclass(origin, Tuple):  # type: ignore [arg-type]
            # origin == Tuple without item type
            args = get_args(self.type_)
            if not args:  # plain tuple
                self.type_ = Any
                self.shape = SHAPE.TUPLE_ELLIPSIS
            elif len(args) == 2 and args[1] is Ellipsis:  # e.g. Tuple[int, ...]
                self.type_ = args[0]
                self.shape = SHAPE.TUPLE_ELLIPSIS
                self.sub_fields = [self.__class__(type_=args[0])]
            elif args == ((),):  # Tuple[()] means empty tuple
                self.shape = SHAPE.TUPLE
                self.type_ = Any
                self.sub_fields = []
            else:
                self.shape = SHAPE.TUPLE
                self.sub_fields = [self.__class__(type_=t) for t in args]
            return
        elif issubclass(origin, List):
            self.type_ = get_args(self.type_)[0]
            self.shape = SHAPE.LIST
        elif issubclass(origin, Set):
            self.type_ = get_args(self.type_)[0]
            self.shape = SHAPE.SET
        elif issubclass(origin, FrozenSet):
            self.type_ = get_args(self.type_)[0]
            self.shape = SHAPE.FROZENSET
        elif issubclass(origin, Deque):
            self.type_ = get_args(self.type_)[0]
            self.shape = SHAPE.DEQUE
        elif issubclass(origin, Sequence):
            self.type_ = get_args(self.type_)[0]
            self.shape = SHAPE.SEQUENCE
        # priority to most common mapping: dict
        elif origin is dict or origin is Dict:
            args = get_args(self.type_)
            self.key_field = self.__class__(type_=args[0])
            self.type_ = args[1]
            self.shape = SHAPE.DICT
        elif issubclass(origin, DefaultDict):
            args = get_args(self.type_)
            self.key_field = self.__class__(type_=args[0])
            self.type_ = args[1]
            self.shape = SHAPE.DEFAULTDICT
        elif issubclass(origin, Counter):
            self.key_field = self.__class__(type_=get_args(self.type_)[0])
            self.type_ = int
            self.shape = SHAPE.COUNTER
        elif issubclass(origin, Mapping):
            args = get_args(self.type_)
            self.key_field = self.__class__(type_=args[0])
            self.type_ = args[1]
            self.shape = SHAPE.MAPPING
        # Equality check as almost everything inherits form Iterable, including str
        # check for Iterable and CollectionsIterable, as it could receive one even
        # when declared with the other
        elif origin in {Iterable, abc.Iterable}:
            self.type_ = get_args(self.type_)[0]
            self.shape = SHAPE.ITERABLE
            self.sub_fields = [self.__class__(type_=self.type_)]
        elif issubclass(origin, Type):  # type: ignore
            return
        else:
            self.shape = SHAPE.GENERIC
            self.sub_fields = [self.__class__(type_=t) for t in get_args(self.type_)]
            self.type_ = origin
            return

        # type_ has been refined eg. as the type of a List
        # sub_fields needs to be populated
        self.sub_fields = [self.__class__(type_=self.type_)]

    def _create_sub_type(self, type_: Type[Any]) -> "TypeWrapper":
        return self.__class__(type_=type_)

    def _type_display(self) -> str:
        t = display_as_type(self.type_)

        # have to do this since display_as_type(self.outer_type_) is different
        # (and wrong) on python 3.6
        if self.shape in SHAPE.MAPPING_LIKE:
            t = f"Mapping[{display_as_type(self.key_field.type_)}, {t}]"  # type: ignore
        elif self.shape == SHAPE.TUPLE:
            t = "Tuple[{}]".format(
                ", ".join(display_as_type(f.type_) for f in self.sub_fields or ())
            )
        elif self.shape == SHAPE.GENERIC:
            assert self.sub_fields
            t = "{}[{}]".format(
                display_as_type(self.type_),
                ", ".join(display_as_type(f.type_) for f in self.sub_fields),
            )
        elif self.shape != SHAPE.SINGLETON:
            t = SHAPE.NAME_LOOKUP[self.shape].format(t)

        if self.allow_none and (self.shape != SHAPE.SINGLETON or not self.sub_fields):
            t = f"Optional[{t}]"
        return str(t)

    def __repr__(self) -> str:
        args = [("type", self._type_display()), ("required", self.required)]
        if not self.required:
            args.append(("default", self.default))
        repr_str = ", ".join(repr(v) if a is None else f"{a}={v!r}" for a, v in args)
        return f"{self.__class__.__name__}({repr_str})"


def resolve_annotation(
    annotation: Union[str, Type[Any], None, ForwardRef],
    namespace: Optional[Mapping[str, Any]] = None,
    *,
    allow_import=False,
    raise_=False,
) -> Union[Type[Any], ForwardRef]:
    """[summary]

    part of typing.get_type_hints.

    Parameters
    ----------
    annotation : Type[Any]
        Type hint, string, or `None` to resolve
    namespace : Optional[Mapping[str, Any]], optional
        Optional namespace in which to resolve, by default None

    Raises
    ------
    NameError
        If the annotation cannot be resolved with the provided namespace
    """
    if annotation is None:
        annotation = type(None)

    if isinstance(annotation, str):
        kwargs = dict(is_argument=False)
        if (3, 10) > sys.version_info >= (3, 9, 8) or sys.version_info >= (3, 10, 1):
            kwargs["is_class"] = True
        annotation = ForwardRef(annotation, **kwargs)

    try:
        return _eval_type(annotation, namespace, None)
    except NameError as e:
        if allow_import:
            # try to import the top level name and try again
            msg = str(e)
            if msg.startswith("name ") and msg.endswith(" is not defined"):
                from importlib import import_module

                name = msg.split()[1].strip("\"'")
                ns = dict(namespace) if namespace else {}
                if name not in ns:
                    ns[name] = import_module(name)
                    return resolve_annotation(
                        annotation, ns, allow_import=allow_import, raise_=raise_
                    )
        if raise_:
            raise
    return annotation


_newtype = NewType("_newtype", str)


def is_new_type(type_: Type[Any]) -> bool:
    """Check whether type_ was created using typing.NewType."""
    return isinstance(type_, type(_newtype)) and hasattr(type_, "__supertype__")


def new_type_supertype(type_: Type[Any]) -> Type[Any]:
    while hasattr(type_, "__supertype__"):
        type_ = type_.__supertype__
    return type_


def is_literal_type(type_: Type[Any]) -> bool:
    return Literal is not None and get_origin(type_) is Literal


try:
    from typing import GenericAlias as TypingGenericAlias  # type: ignore
except ImportError:
    # python < 3.9 does not have GenericAlias (list[int], tuple[str, ...] and so on)
    TypingGenericAlias = ()

if sys.version_info < (3, 10):

    def is_union(tp: Optional[Type[Any]]) -> bool:
        return tp is Union

    WithArgsTypes = (TypingGenericAlias,)

else:
    import types

    def is_union(tp: Optional[Type[Any]]) -> bool:
        return tp is Union or tp is types.UnionType  # noqa: E721

    WithArgsTypes = (TypingGenericAlias, types.GenericAlias, types.UnionType)


NONE_TYPES: Tuple[Any, Any, Any] = (None, type(None), Literal[None])


if sys.version_info[:2] == (3, 8):
    # We can use the fast implementation for 3.8 but there is a very weird bug
    # where it can fail for `Literal[None]`.
    # We just need to redefine a useless `Literal[None]` inside the function body to fix

    def is_none_type(type_: Any) -> bool:
        Literal[None]  # fix edge case
        return any(type_ is none_type for none_type in NONE_TYPES)

else:

    def is_none_type(type_: Any) -> bool:
        return any(type_ is none_type for none_type in NONE_TYPES)


try:
    from typing import _TypingBase as typing_base  # type: ignore
except ImportError:
    from typing import _Final as typing_base  # type: ignore


def display_as_type(v: Type[Any]) -> str:
    if (
        not isinstance(v, typing_base)
        and not isinstance(v, WithArgsTypes)
        and not isinstance(v, type)
    ):
        v = v.__class__

    if is_union(get_origin(v)):
        return f'Union[{", ".join(map(display_as_type, get_args(v)))}]'

    if isinstance(v, WithArgsTypes):
        # Generic alias are constructs like `list[int]`
        return str(v).replace("typing.", "")

    try:
        return v.__name__
    except AttributeError:
        # happens with typing objects
        return str(v).replace("typing.", "")


def resolve_forward_refs(value: Any) -> Any:
    """Resolve forward refs in value, using TypeWrapper"""
    if value in (None, Parameter.empty):
        return value
    v = TypeWrapper(type_=value)
    return v.outer_type_ if v.is_resolved else v.resolve()
