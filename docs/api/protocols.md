# Backend Protocols

!!!warning "Advanced Topic"

    ***Most users of magicgui will not need to worry about this section.***

    These Protocol classes declare the interface that backend
    adapters must implement in order to be used by magicgui. All magicgui `Widget`
    objects compose a backend widget implementing one of these protocols, and control
    it using the methods defined herein.

    `magicgui` developers may be interested in this page, but end-users
    needn't worry about it.

## Summary

::: autosummary
    magicgui.widgets.protocols.WidgetProtocol
    magicgui.widgets.protocols.ValueWidgetProtocol
    magicgui.widgets.protocols.ButtonWidgetProtocol
    magicgui.widgets.protocols.TableWidgetProtocol
    magicgui.widgets.protocols.RangedWidgetProtocol
    magicgui.widgets.protocols.CategoricalWidgetProtocol
    magicgui.widgets.protocols.SliderWidgetProtocol
    magicgui.widgets.protocols.ContainerProtocol
    magicgui.widgets.protocols.BaseApplicationBackend
    magicgui.widgets.protocols.DialogProtocol
    magicgui.widgets.protocols.SupportsChoices
    magicgui.widgets.protocols.SupportsOrientation
    magicgui.widgets.protocols.SupportsText
    magicgui.widgets.protocols.SupportsReadOnly

## Protocol Inheritance

The visual hierarchy of protocols looks like this:

``` mermaid
graph LR
    A([WidgetProtocol])-->B([ValueWidgetProtocol])
    A-->C([ContainerProtocol])
    M([SupportsText])-->E
    B-->E([ButtonWidgetProtocol])
    B-->D([RangedWidgetProtocol])
    B-->F([CategoricalWidgetProtocol])
    D-->I([SliderWidgetProtocol])
    B-->J([TableWidgetProtocol])
    K([SupportsReadOnly])-->J([TableWidgetProtocol])
    L([SupportsChoices])-->F
    N([SupportsOrientation])-->C
    N-->I
    C-->O([DialogProtocol])
    C-->P([MainWindowProtocol])

    click A "#magicgui.widgets.protocols.WidgetProtocol"
    click B "#magicgui.widgets.protocols.ValueWidgetProtocol"
    click C "#magicgui.widgets.protocols.ContainerProtocol"
    click D "#magicgui.widgets.protocols.RangedWidgetProtocol"
    click E "#magicgui.widgets.protocols.ButtonWidgetProtocol"
    click F "#magicgui.widgets.protocols.CategoricalWidgetProtocol"
    click I "#magicgui.widgets.protocols.SliderWidgetProtocol"
    click J "#magicgui.widgets.protocols.TableWidgetProtocol"
    click K "#magicgui.widgets.protocols.SupportsReadOnly"
    click L "#magicgui.widgets.protocols.SupportsChoices"
    click M "#magicgui.widgets.protocols.SupportsText"
    click N "#magicgui.widgets.protocols.SupportsOrientation"
    click O "#magicgui.widgets.protocols.DialogProtocol"
    click P "#magicgui.widgets.protocols.MainWindowProtocol"
```

## Widget Protocols

::: magicgui.widgets.protocols.WidgetProtocol
    options:
        filters: []
        heading_level: 3

::: magicgui.widgets.protocols.ValueWidgetProtocol
    options:
        filters: []
        heading_level: 3

::: magicgui.widgets.protocols.ButtonWidgetProtocol
    options:
        filters: []
        heading_level: 3

::: magicgui.widgets.protocols.TableWidgetProtocol
    options:
        filters: []
        heading_level: 3

::: magicgui.widgets.protocols.RangedWidgetProtocol
    options:
        filters: []
        heading_level: 3

::: magicgui.widgets.protocols.CategoricalWidgetProtocol
    options:
        filters: []
        heading_level: 3

::: magicgui.widgets.protocols.SliderWidgetProtocol
    options:
        filters: []
        heading_level: 3

::: magicgui.widgets.protocols.ContainerProtocol
    options:
        filters: []
        heading_level: 3

::: magicgui.widgets.protocols.DialogProtocol
    options:
        filters: []
        heading_level: 3

::: magicgui.widgets.protocols.MainWindowProtocol
    options:
        filters: []
        heading_level: 3

::: magicgui.widgets.protocols.SupportsChoices
    options:
        filters: []
        heading_level: 3

::: magicgui.widgets.protocols.SupportsOrientation
    options:
        filters: []
        heading_level: 3

::: magicgui.widgets.protocols.SupportsText
    options:
        filters: []
        heading_level: 3

::: magicgui.widgets.protocols.SupportsReadOnly
    options:
        filters: []
        heading_level: 3

---------

## Application Protocol

::: magicgui.widgets.protocols.BaseApplicationBackend
    options:
        filters: []
        heading_level: 3
