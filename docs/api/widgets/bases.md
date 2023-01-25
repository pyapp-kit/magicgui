# `magicgui.widgets.bases`

The `magicgui.widgets.bases` module contains the base classes for all widgets.

While most users will never instantiate these classes directly, the methods and properties
of these classes are inherited by all widgets, and define the common API for all
widgets.  Therefore, it is worth being aware of the type of widget you are working with.

## Summary

::: autosummary
    magicgui.widgets.bases.Widget
    magicgui.widgets.bases.ButtonWidget
    magicgui.widgets.bases.CategoricalWidget
    magicgui.widgets.bases.ContainerWidget
    magicgui.widgets.bases.DialogWidget
    magicgui.widgets.bases.MainWindowWidget
    magicgui.widgets.bases.RangedWidget
    magicgui.widgets.bases.SliderWidget
    magicgui.widgets.bases.ValueWidget

## Class Hierarchy

In visual form, the widget class hierarchy looks like this:

``` mermaid
classDiagram
    Widget <|-- ValueWidget
    Widget <|-- ContainerWidget
    BackendWidget ..|> WidgetProtocol : implements a
    ValueWidget <|-- RangedWidget
    ValueWidget <|-- ButtonWidget
    ValueWidget <|-- CategoricalWidget
    RangedWidget <|-- SliderWidget
    Widget --* WidgetProtocol : controls a
    <<Interface>> WidgetProtocol
    class WidgetProtocol {
        _mgui_get_X()
        _mgui_set_X()
    }
    class Widget{
        name: str
        annotation: Any
        label: str
        tooltip: str
        visible: bool
        enabled: bool
        native: Any
        height: int
        width: int
        hide()
        show()
        close()
        render()
    }
    class ValueWidget{
        value: Any
        changed: SignalInstance
        bind(value, call) Any
        unbind()
    }
    class RangedWidget{
        value: float | tuple
        min: float
        max: float
        step: float
        adaptive_step: bool
        range: tuple[float, float]
    }
    class SliderWidget{
        orientation: str
    }
    class ButtonWidget{
        value: bool
        clicked: SignalInstance
        text: str
    }
    class CategoricalWidget{
        choices: List[Any]
    }
    class ContainerWidget{
        widgets: List[Widget]
        labels: bool
        layout: str
        margins: tuple[int, int, int, int]
        reset_choices()
        asdict() Dict[str, Any]
        update(mapping)
    }

    click Widget href "#magicgui.widgets.bases.Widget"
    click ValueWidget href "#magicgui.widgets.bases.ValueWidget"
    click RangedWidget href "#magicgui.widgets.bases.RangedWidget"
    click SliderWidget href "#magicgui.widgets.bases.SliderWidget"
    click ButtonWidget href "#magicgui.widgets.bases.ButtonWidget"
    click CategoricalWidget href "#magicgui.widgets.bases.CategoricalWidget"
    click ContainerWidget href "#magicgui.widgets.bases.ContainerWidget"

```

## Base Widget Classes

::: magicgui.widgets.bases.Widget
    options:
        heading_level: 3
::: magicgui.widgets.bases.ButtonWidget
    options:
        heading_level: 3
::: magicgui.widgets.bases.CategoricalWidget
    options:
        heading_level: 3
::: magicgui.widgets.bases.ContainerWidget
    options:
        heading_level: 3
::: magicgui.widgets.bases.DialogWidget
    options:
        heading_level: 3
::: magicgui.widgets.bases.MainWindowWidget
    options:
        heading_level: 3
::: magicgui.widgets.bases.RangedWidget
    options:
        heading_level: 3
::: magicgui.widgets.bases.SliderWidget
    options:
        heading_level: 3
::: magicgui.widgets.bases.ValueWidget
    options:
        heading_level: 3
