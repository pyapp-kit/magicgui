# Events

All magicgui widgets emit events when certain properties change. For example, a
`PushButton` emits an event when it is clicked, and all
[`ValueWidget`][magicgui.widgets.bases.ValueWidget] subclasses (like `Slider` or
`LineEdit`) emit an event when their value changes.  You can connect callbacks
to these events to respond to them.

!!! info  "It's all `psygnal` under the hood"

    **magicgui** uses [psygnal](https://psygnal.readthedocs.io/) for its event
    system.  For greater detail on the `connect` method and its options, see
    the [Usage section](https://psygnal.readthedocs.io/en/latest/usage/)
    of psygnal's documentation.

## Connecting to events

To connect a callback to an event, use the `connect` method of the event
attribute.  For example, to connect a callback to a
[`LineEdit`][magicgui.widgets.LineEdit] widget's `changed` event:

=== "Widget API"

    ```python
    from magicgui import widgets

    text = widgets.LineEdit(value='type something')
    text.changed.connect(lambda val: print(f"Text changed to: {val}"))
    ```

=== "`magicgui` decorator"

    ```python
    from magicgui import magicgui

    @magicgui
    def my_function(text: str):
        ...

    my_function.text.changed.connect(lambda val: print(f"Text changed to: {val}"))
    ```

=== "`magic_factory` decorator"

    ```python
    from magicgui import magic_factory

    def _on_init(widget):
        widget.text.changed.connect(lambda val: print(f"Text changed to: {val}"))

    @magic_factory(widget_init=_on_init)
    def my_function(text: str):
        ...

    my_widget = my_function()
    ```
