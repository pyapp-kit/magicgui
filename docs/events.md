# Events

All magicgui widgets emit events when certain properties change.  For each event
there is a corresponding signal attribute on the widget that can be connected to
a callback function. For example, a [`PushButton`][magicgui.widgets.PushButton]
emits an event when it is clicked, and all
[`ValueWidget`][magicgui.widgets.bases.ValueWidget] subclasses (like
[`Slider`][magicgui.widgets.Slider] or [`LineEdit`][magicgui.widgets.LineEdit])
emit an event when their value changes.

## Connecting to events

To connect a callback to an event, use the `connect` method of the signal
attribute.  The exact signals available on each widget are mostly defined in
the [base classes](api/widgets/bases.md), and are listed on the [API page
for each respective widget](api/widgets/index.md).

For example, to connect a callback to a [`LineEdit`][magicgui.widgets.LineEdit]
widget's `changed` event:

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

!!! info  "It's all `psygnal` under the hood"

    **magicgui** uses [psygnal](https://psygnal.readthedocs.io/) for its event
    system.  For greater detail on the `connect` method and its options, see
    the [Usage section](https://psygnal.readthedocs.io/en/latest/usage/)
    of psygnal's documentation, or the [`psygnal.SignalInstance.connect`][psygnal._signal.SignalInstance.connect] API
    reference.

!!! tip
    Note that `connect` returns the callable that it was passed, so you can
    use it as a decorator if you prefer.

    ```python
    text = widgets.LineEdit(value='type something')

    # this works
    text.changed.connect(lambda val: print(f"Text changed to: {val}"))

    # so does this
    @text.changed.connect
    def on_text_changed(val):
        print(f"Text changed to: {val}")
    ```
