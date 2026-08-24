import typing
from collections.abc import Mapping, Sequence
from concurrent.futures import Future

from magicgui._util import safe_issubclass


class TestSafeIsSubclass:
    def test_basic(self):
        assert safe_issubclass(int, int)
        assert safe_issubclass(int, object)

    def test_generic_base(self):
        assert safe_issubclass(typing.List[int], list)
        assert safe_issubclass(typing.List[int], typing.List)

    def test_multiple_generic_base(self):
        assert safe_issubclass(typing.List[int], (typing.List, typing.Dict))

    def test_no_exception(self):
        assert not safe_issubclass(int, 1)

    def test_typing_inheritance(self):
        assert safe_issubclass(typing.List, list)
        assert safe_issubclass(list, typing.List)
        assert safe_issubclass(typing.Tuple, tuple)
        assert safe_issubclass(tuple, typing.Tuple)
        assert safe_issubclass(typing.Dict, dict)
        assert safe_issubclass(dict, typing.Dict)

    def test_inheritance_generic_list(self):
        assert safe_issubclass(list, typing.Sequence)
        assert safe_issubclass(typing.List, typing.Sequence)
        assert safe_issubclass(typing.List[int], typing.Sequence[int])
        assert safe_issubclass(typing.List[int], typing.Sequence)
        assert safe_issubclass(typing.List[int], Sequence)

    def test_no_inheritance_generic_super(self):
        assert not safe_issubclass(list, typing.List[int])

    def test_inheritance_generic_mapping(self):
        assert safe_issubclass(dict, typing.Mapping)
        assert safe_issubclass(typing.Dict, typing.Mapping)
        assert safe_issubclass(typing.Dict[int, str], typing.Mapping[int, str])
        assert safe_issubclass(typing.Dict[int, str], typing.Mapping)
        assert safe_issubclass(typing.Dict[int, str], Mapping)

    def test_typing_builtins_list(self):
        assert safe_issubclass(list[int], list)
        assert safe_issubclass(list[int], Sequence)
        assert safe_issubclass(list[int], typing.Sequence)
        assert safe_issubclass(list[int], typing.Sequence[int])
        assert safe_issubclass(list[int], typing.List[int])
        assert safe_issubclass(typing.List[int], list)
        assert safe_issubclass(typing.List[int], list[int])

    def test_typing_builtins_dict(self):
        assert safe_issubclass(dict[int, str], dict)
        assert safe_issubclass(dict[int, str], Mapping)
        assert safe_issubclass(dict[int, str], typing.Mapping)
        assert safe_issubclass(dict[int, str], typing.Mapping[int, str])
        assert safe_issubclass(dict[int, str], typing.Dict[int, str])
        assert safe_issubclass(typing.Dict[int, str], dict)
        assert safe_issubclass(typing.Dict[int, str], dict[int, str])

    def test_tuple_check(self):
        assert safe_issubclass(typing.Tuple[int, str], tuple)
        assert safe_issubclass(typing.Tuple[int], typing.Sequence[int])
        assert safe_issubclass(typing.Tuple[int, int], typing.Sequence[int])
        assert safe_issubclass(typing.Tuple[int, ...], typing.Sequence[int])
        assert safe_issubclass(typing.Tuple[int, ...], typing.Iterable[int])
        assert not safe_issubclass(typing.Tuple[int, ...], typing.Dict[int, typing.Any])
        assert safe_issubclass(typing.Tuple[int, ...], typing.Tuple[int, ...])
        assert safe_issubclass(typing.Tuple[int, int], typing.Tuple[int, ...])
        assert not safe_issubclass(typing.Tuple[int, int], typing.Tuple[int, str])
        assert not safe_issubclass(typing.Tuple[int, int], typing.Tuple[int, int, int])

    def test_subclass_future(self):
        assert safe_issubclass(Future[list[int]], Future[list[int]])
        assert safe_issubclass(Future[list[int]], Future[list])
        assert safe_issubclass(Future[list[int]], Future[list[int]])
        assert not safe_issubclass(Future[list[int]], Future[list[str]])

    def test_subclass_new_type(self):
        new_int = typing.NewType("new_int", int)

        assert safe_issubclass(new_int, new_int)
        assert safe_issubclass(list[new_int], typing.List[new_int])
        assert safe_issubclass(typing.List[new_int], list[new_int])
        assert safe_issubclass(list[new_int], typing.Sequence[new_int])
        assert safe_issubclass(list[new_int], list[new_int])
