import typing
from collections.abc import Mapping, Sequence
from concurrent.futures import Future

from magicgui._util import safe_issubclass


class TestSafeIsSubclass:
    def test_basic(self):
        assert safe_issubclass(int, int)
        assert safe_issubclass(int, object)

    def test_generic_base(self):
        assert safe_issubclass(list[int], list)
        assert safe_issubclass(list[int], list)

    def test_multiple_generic_base(self):
        assert safe_issubclass(list[int], (list, dict))

    def test_no_exception(self):
        assert not safe_issubclass(int, 1)

    def test_typing_inheritance(self):
        assert safe_issubclass(list, list)
        assert safe_issubclass(list, list)
        assert safe_issubclass(tuple, tuple)
        assert safe_issubclass(tuple, tuple)
        assert safe_issubclass(dict, dict)
        assert safe_issubclass(dict, dict)

    def test_inheritance_generic_list(self):
        assert safe_issubclass(list, typing.Sequence)
        assert safe_issubclass(list, typing.Sequence)
        assert safe_issubclass(list[int], typing.Sequence[int])
        assert safe_issubclass(list[int], typing.Sequence)
        assert safe_issubclass(list[int], Sequence)

    def test_no_inheritance_generic_super(self):
        assert not safe_issubclass(list, list[int])

    def test_inheritance_generic_mapping(self):
        assert safe_issubclass(dict, typing.Mapping)
        assert safe_issubclass(dict, typing.Mapping)
        assert safe_issubclass(dict[int, str], typing.Mapping[int, str])
        assert safe_issubclass(dict[int, str], typing.Mapping)
        assert safe_issubclass(dict[int, str], Mapping)

    def test_typing_builtins_list(self):
        assert safe_issubclass(list[int], list)
        assert safe_issubclass(list[int], Sequence)
        assert safe_issubclass(list[int], typing.Sequence)
        assert safe_issubclass(list[int], typing.Sequence[int])
        assert safe_issubclass(list[int], list[int])
        assert safe_issubclass(list[int], list)
        assert safe_issubclass(list[int], list[int])

    def test_typing_builtins_dict(self):
        assert safe_issubclass(dict[int, str], dict)
        assert safe_issubclass(dict[int, str], Mapping)
        assert safe_issubclass(dict[int, str], typing.Mapping)
        assert safe_issubclass(dict[int, str], typing.Mapping[int, str])
        assert safe_issubclass(dict[int, str], dict[int, str])
        assert safe_issubclass(dict[int, str], dict)
        assert safe_issubclass(dict[int, str], dict[int, str])

    def test_tuple_check(self):
        assert safe_issubclass(tuple[int, str], tuple)
        assert safe_issubclass(tuple[int], typing.Sequence[int])
        assert safe_issubclass(tuple[int, int], typing.Sequence[int])
        assert safe_issubclass(tuple[int, ...], typing.Sequence[int])
        assert safe_issubclass(tuple[int, ...], typing.Iterable[int])
        assert not safe_issubclass(tuple[int, ...], dict[int, typing.Any])
        assert safe_issubclass(tuple[int, ...], tuple[int, ...])
        assert safe_issubclass(tuple[int, int], tuple[int, ...])
        assert not safe_issubclass(tuple[int, int], tuple[int, str])
        assert not safe_issubclass(tuple[int, int], tuple[int, int, int])

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
