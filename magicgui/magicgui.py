import functools
import inspect
from enum import Enum
from typing import Any, Callable, Dict, NamedTuple, Type, TypeVar, Union, Optional

from qtpy.QtCore import SignalInstance
from qtpy.QtWidgets import (
    QAbstractButton,
    QAbstractSlider,
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

QWidgetType = TypeVar("QWidget")
QWidgetInstance = TypeVar("QWidgetInstance")


class GetSetOnChange(NamedTuple):
    getter: Callable[[], Any]
    setter: Callable[[Any], None]
    onchange: SignalInstance


def getter_setter_onchange(widget: QWidgetInstance) -> GetSetOnChange:
    if isinstance(widget, QComboBox):
        return GetSetOnChange(
            widget.currentText,
            lambda x: widget.setCurrentText(str(x.name) if isinstance(x, Enum) else x),
            widget.currentTextChanged,
        )
    elif isinstance(widget, QStatusBar):
        return GetSetOnChange(
            widget.currentMessage, widget.showMessage, widget.messageChanged
        )
    elif isinstance(widget, QLineEdit):
        return GetSetOnChange(widget.text, widget.setText, widget.textChanged)
    elif isinstance(widget, (QAbstractButton, QGroupBox)):
        return GetSetOnChange(widget.isChecked, widget.setChecked, widget.toggled)
    elif isinstance(widget, QDateTimeEdit):
        return GetSetOnChange(
            widget.dateTime, widget.setDateTime, widget.dateTimeChanged
        )
    elif isinstance(widget, (QAbstractSpinBox, QAbstractSlider)):
        return GetSetOnChange(widget.value, widget.setValue, widget.valueChanged)
    elif isinstance(widget, QTabWidget):
        return GetSetOnChange(
            widget.currentIndex, widget.setCurrentIndex, widget.currentChanged
        )
    elif isinstance(widget, QSplitter):
        return GetSetOnChange(widget.sizes, widget.setSizes, widget.splitterMoved)
    raise ValueError(f"Unrecognized widget Type: {widget}")


def type2widget(type_: type) -> QWidgetType:

    simple: Dict[type, QWidgetType] = {
        bool: QCheckBox,
        int: QSpinBox,
        float: QDoubleSpinBox,
        str: QLineEdit,
    }
    if type_ in simple:
        return simple[type_]
    elif issubclass(type_, Enum):
        return QComboBox


class Layout(Enum):
    vertical = QVBoxLayout
    horizontal = QHBoxLayout
    grid = QGridLayout
    form = QFormLayout

    @classmethod
    def _missing_(cls, value: object) -> Any:
        options = cls._member_names_
        raise ValueError(f"'{value}' is not a valid Layout. Options include: {options}")


def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition(".")
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split("."))


class WidgetDescriptor:
    def __init__(self, widget: QWidgetInstance, name: Optional[str] = None) -> None:
        self.widget = widget
        self.name = name
        self.getter, self.setter, self.onchange = getter_setter_onchange(widget)

    def __get__(self, obj, objtype) -> Any:
        return self.getter()

    def __set__(self, obj, val) -> None:
        self.setter(val)

    def __delete__(self, obj) -> None:
        self.widget.parent().layout().removeWidget(self.widget)
        self.widget.deleteLater()
        if self.name:
            delattr(type(obj), self.name)


class MagicGui(QWidget):
    def __init__(self, func, layout=QHBoxLayout, parent=None) -> None:
        self.func = func
        super().__init__(parent=parent)
        self.setLayout(layout.value(self))
        params = inspect.signature(func).parameters
        for argname, param in params.items():
            arg_type = (
                type(param.default)
                if param.annotation is param.empty
                else param.annotation
            )

            widget = type2widget(arg_type)(parent=self)
            if isinstance(widget, QComboBox) and issubclass(arg_type, Enum):
                widget.addItems(list(map(str, arg_type._member_names_)))
            setattr(self, argname + "_widget", widget)
            setattr(MagicGui, argname, WidgetDescriptor(widget, argname))
            setattr(
                MagicGui.__init__,
                "__doc__",
                f'MagicGui generated for function "{func.__name__}"',
            )
            if param.default:
                setattr(self, argname, param.default)
            self.layout().addWidget(widget)

    def __repr__(self):
        return f"<MagicGui for '{self.func.__name__}' at {id(self)}>"


def magicgui(
    function: Callable = None, layout: Union[Layout, str] = "horizontal"
) -> Callable:
    _layout = Layout[layout] if isinstance(layout, str) else layout

    def inner_func(func: Callable) -> Type:
        setattr(func, "Gui", functools.partial(MagicGui, func, _layout))
        return func

    return inner_func if function is None else inner_func(function)


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication

    class MyEnum(Enum):
        Oil = 1.515
        Water = 1.33
        Air = 1.0

    @magicgui
    def test_function(
        a: str = "hello", b: int = 3, immersion: MyEnum = MyEnum.Water, empty=7.1
    ) -> None:
        """my docs"""
        print(a, b)

    app = QApplication([])

    w = test_function.Gui()
    w.show()

    app.exec_()
