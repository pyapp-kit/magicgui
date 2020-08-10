from __future__ import annotations

from inspect import Signature
from typing import Callable, MutableSequence, Optional, Sequence, Union, overload

from magicgui.application import use_app
from magicgui.base import BaseContainer
from magicgui.event import EventEmitter
from magicgui.signature import MagicParameter, MagicSignature, magic_signature
from magicgui.widget import ValueWidget, Widget


class Container(MutableSequence[Widget]):
    changed: EventEmitter

    def __init__(
        self,
        *,
        orientation="horizontal",
        widgets: Sequence[Widget] = [],
        app=None,
        return_annotation=Signature.empty,
    ):
        _app = use_app(app)
        assert _app.native
        self.changed = EventEmitter(source=self, type="changed")
        self._base: BaseContainer = _app.get_obj("Container")(orientation)
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
                self._base._mg_remove_index(idx)
        else:
            self._base._mg_remove_index(key)

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
                item = self._base._mg_get_index(idx)
                if item:
                    out.append(item)
            return out

        item = self._base._mg_get_index(key)
        if not item:
            raise IndexError("Container index out of range")
        return item

    def __len__(self) -> int:
        return self._base._mg_count()

    def __setitem__(self, key, value):
        raise NotImplementedError("magicgui.Container does not support item setting.")

    def insert(self, key: int, widget: Widget):
        if isinstance(widget, ValueWidget):
            widget.changed.connect(lambda x: self.changed())
        self._base._mg_insert_widget(key, widget)

    @property
    def native(self):
        return self._base._mg_get_native_layout()

    def __repr__(self) -> str:
        return f"<magicgui.Container at {hex(id(self))} with {len(self)} widgets>"

    @classmethod
    def from_signature(cls, sig: Signature, **kwargs) -> Container:
        return MagicSignature.from_signature(sig).to_container(**kwargs)

    @classmethod
    def from_callable(
        cls, obj: Callable, gui_options: Optional[dict] = None, **kwargs
    ) -> Container:
        return magic_signature(obj, gui_options=gui_options).to_container(**kwargs)

    def to_signature(self) -> MagicSignature:
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

    def show(self):
        self._base._mg_show_widget()

    def hide(self):
        self._base._mg_hide_widget()
