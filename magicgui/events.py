"""deprecation strategy"""

import weakref

from psygnal import Signal as _Sig
from psygnal import SignalInstance as _SI


class Event:
    def __init__(self, value, type, source) -> None:
        self.value = value
        self.type = type
        self.source = source


class SignalInstance(_SI):
    _new_callback = {}  # type: ignore

    def connect(
        self,
        slot=None,
        *,
        check_nargs=None,
        check_types=None,
        unique=False,
        new_callback=False,
    ):

        if not new_callback:
            import warnings

            name = getattr(self._instance, "name", "widget")
            signame = self.name
            warnings.warn(
                "\nmagicgui 0.3.0 will change the way that callbacks are called.\n"
                "Instead of a single `Event` instance, with an `event.value` attribute,"
                "\ncallbacks will receive the value(s) directly:\n\n"
                f"@{name}.{signame}.connect\n"
                "def my_callback(*args):\n"
                "    # *args are the value(s) themselves!"
                "\n\nTo silence this warning use `.connect(..., new_callback=True)`"
                "\nFor details, see: https://github.com/napari/magicgui/issues/255",
                FutureWarning,
            )
        result = super().connect(
            slot, check_nargs=check_nargs, check_types=check_types, unique=unique
        )
        self._new_callback[self._normalize_slot(slot)] = new_callback
        return result

    def _run_emit_loop(self, args) -> None:

        rem = []
        # allow receiver to query sender with Signal.current_emitter()
        with self._lock:
            with Signal._emitting(self):
                for _slt in self._slots:
                    (slot, max_args) = _slt
                    if isinstance(slot, tuple):
                        _ref, method_name = slot
                        obj = _ref()
                        if obj is None:
                            rem.append(slot)  # add dead weakref
                            continue
                        cb = getattr(obj, method_name, None)
                        if cb is None:  # pragma: no cover
                            rem.append(slot)  # object has changed?
                            continue
                    else:
                        cb = slot

                    # TODO: add better exception handling
                    if self._new_callback.get(_slt):
                        cb(*args[:max_args])
                    else:
                        cb(Event(args[0], "hi", self.instance))

            for slot in rem:
                self.disconnect(slot)

        return None


class Signal(_Sig):
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        d = self._signal_instances.setdefault(self, weakref.WeakKeyDictionary())
        return d.setdefault(
            instance,
            SignalInstance(
                self.signature,
                instance=instance,
                name=self._name,
                check_nargs_on_connect=self._check_nargs_on_connect,
                check_types_on_connect=self._check_types_on_connect,
            ),
        )
