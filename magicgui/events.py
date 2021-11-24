"""deprecation strategy"""

import warnings
from collections import namedtuple
from typing import Callable, Dict, cast

import psygnal


def _new_style_slot(slot: Callable) -> bool:
    sig = psygnal._signal.signature(slot)
    if len(sig.parameters) != 1:
        return True
    p0 = list(sig.parameters.values())[0]
    return p0.annotation is not p0.empty and (
        (getattr(p0.annotation, "__name__", "") != "Event")
        or (str(p0.annotation) == "Event")
    )


Event = namedtuple("Event", ("value", "type", "source"))


class SignalInstance(psygnal.SignalInstance):
    _new_callback: Dict[psygnal._signal.NormedCallback, bool] = {}

    def connect(
        self,
        slot=None,
        *,
        check_nargs=None,
        check_types=None,
        unique=False,
    ):
        is_new_style = _new_style_slot(slot)
        if not is_new_style:
            name = getattr(self._instance, "name", "") or "widget"
            signame = self.name
            warnings.warn(
                "\n\nmagicgui 0.4.0 will change the way that callbacks are called.\n"
                "Instead of a single `Event` instance, with an `event.value` attribute,"
                "\ncallbacks will receive the value(s) directly:\n\n"
                f"@{name}.{signame}.connect\n"
                "def my_callback(*args):\n"
                "    # *args are the value(s) themselves!"
                "\n\nTo silence this warning you may either provide a callback that "
                "has more\nor less than 1 parameter.  Or annotate the single parameter "
                "as anything\n*other* than `Event`, e.g. `def callback(x: int): ...`"
                "\nFor details, see: https://github.com/napari/magicgui/issues/255",
                FutureWarning,
                stacklevel=2,
            )
        result = super().connect(
            slot, check_nargs=check_nargs, check_types=check_types, unique=unique
        )
        self._new_callback[self._normalize_slot(slot)] = is_new_style
        return result

    def _run_emit_loop(self, args) -> None:
        rem = []
        # allow receiver to query sender with Signal.current_emitter()
        with self._lock:
            with Signal._emitting(self):
                for (slot, max_args) in self._slots:
                    if isinstance(slot, tuple):
                        _ref, name, method = slot
                        obj = _ref()
                        if obj is None:
                            rem.append(slot)  # add dead weakref
                            continue
                        if method is not None:
                            cb = method
                        else:
                            cb = getattr(obj, name, None)
                            if cb is None:  # pragma: no cover
                                rem.append(slot)  # object has changed?
                                continue
                    else:
                        cb = slot

                    # TODO: add better exception handling
                    if self._new_callback.get(slot):
                        cb(*args[:max_args])
                    else:
                        cb(Event(args[0], self.name, self.instance))

            for slot in rem:
                self.disconnect(slot)

        return None

    def __call__(self, *args, **kwds):
        if kwds:
            name = getattr(self._instance, "name", "") or "widget"
            signame = self.name
            args = args + tuple(kwds.values())
            argrepr = ", ".join(repr(s) for s in args)
            kwargrepr = ",".join(f"{k}={v!r}" for k, v in kwds.items())
            warnings.warn(
                "\n\nmagicgui 0.4.0 is using psygnal for event emitters.\n"
                f"Keyword arguments ({set(kwds)!r}) are no longer accepted by the event"
                f" emitter.\nUse '{name}.{signame}({argrepr})' instead of "
                f"{name}.{signame}({kwargrepr}).\nIn the future this will be an error."
                "\nFor details, see: https://github.com/napari/magicgui/issues/255",
                FutureWarning,
                stacklevel=2,
            )
        return self._run_emit_loop(args)


class Signal(psygnal.Signal):
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        signal_instance = SignalInstance(
            self.signature,
            instance=instance,
            name=self._name,
            check_nargs_on_connect=self._check_nargs_on_connect,
            check_types_on_connect=self._check_types_on_connect,
        )
        setattr(instance, cast(str, self._name), signal_instance)
        return signal_instance
