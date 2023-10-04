import pytest

from magicgui import magicgui, use_app, widgets


@pytest.mark.parametrize("scrollable", [False, True])
def test_container_widget(scrollable):
    """Test basic container functionality."""
    container = widgets.Container(labels=False, scrollable=scrollable)
    labela = widgets.Label(value="hi", name="labela")
    labelb = widgets.Label(value="hi", name="labelb")
    container.append(labela)
    container.extend([labelb])
    # different ways to index
    assert container[0] == labela
    assert container["labelb"] == labelb
    assert container[:1] == [labela]
    assert container[-1] == labelb

    with pytest.raises(RuntimeError):
        container[0] = "something"

    assert container.layout == "vertical"
    with pytest.raises(NotImplementedError):
        container.layout = "horizontal"

    assert all(x in dir(container) for x in ["labela", "labelb"])

    assert container.margins
    container.margins = (8, 8, 8, 8)
    assert container.margins == (8, 8, 8, 8)

    del container[1:]
    del container[-1]
    assert not container
    container.close()


@pytest.mark.parametrize("scrollable", [False, True])
def test_container_label_widths(scrollable):
    """Test basic container functionality."""
    container = widgets.Container(layout="vertical", scrollable=scrollable)
    labela = widgets.Label(value="hi", name="labela")
    labelb = widgets.Label(value="hi", name="I have a very long label")

    def _label_width():
        measure = use_app().get_obj("get_text_width")
        return max(
            measure(w.label)
            for w in container
            if not isinstance(w, widgets.bases.ButtonWidget)
        )

    container.append(labela)
    before = _label_width()
    container.append(labelb)
    assert _label_width() > before
    container.close()


@pytest.mark.parametrize("scrollable", [False, True])
def test_labeled_widget_container(scrollable):
    """Test that _LabeledWidgets follow their children."""
    from magicgui.widgets._concrete import _LabeledWidget

    w1 = widgets.Label(value="hi", name="w1")
    w2 = widgets.Label(value="hi", name="w2")
    container = widgets.Container(
        widgets=[w1, w2], layout="vertical", scrollable=scrollable
    )
    assert w1._labeled_widget
    lw = w1._labeled_widget()
    assert isinstance(lw, _LabeledWidget)
    assert not lw.visible
    container.show()
    assert w1.visible
    assert lw.visible
    w1.hide()
    assert not w1.visible
    assert not lw.visible
    w1.label = "another label"
    assert lw._label_widget.value == "another label"
    container.close()


@pytest.mark.parametrize("scrollable", [False, True])
def test_visible_in_container(scrollable):
    """Test that visibility depends on containers."""
    w1 = widgets.Label(value="hi", name="w1")
    w2 = widgets.Label(value="hi", name="w2")
    w3 = widgets.Label(value="hi", name="w3", visible=False)
    container = widgets.Container(widgets=[w2, w3], scrollable=scrollable)
    assert not w1.visible
    assert not w2.visible
    assert not w3.visible
    assert not container.visible
    container.show()
    assert container.visible
    assert w2.visible
    assert not w3.visible
    w1.show()
    assert w1.visible
    container.close()


def test_delete_widget():
    """We can delete widgets from containers."""
    a = widgets.Label(name="a")
    container = widgets.Container(widgets=[a])
    # we can delete widgets
    del container.a
    with pytest.raises(AttributeError):
        _ = container.a

    # they disappear from the layout
    with pytest.raises(ValueError):
        container.index(a)


def test_reset_choice_recursion():
    """Test that reset_choices recursion works for multiple types of widgets."""
    x = 0

    def get_choices(widget):
        nonlocal x
        x += 1
        return list(range(x))

    @magicgui(c={"choices": get_choices})
    def f(c):
        pass

    assert f.c.choices == (0,)

    container = widgets.Container(widgets=[f])
    container.reset_choices()
    assert f.c.choices == (0, 1)
    container.reset_choices()
    assert f.c.choices == (0, 1, 2)


def test_container_indexing_with_native_mucking():
    """Mostly make sure that the inner model isn't messed up.

    keeping indexes with a manipulated native model *may* be something to do in future.
    """
    l1 = widgets.Label(name="l1")
    l2 = widgets.Label(name="l2")
    l3 = widgets.Label(name="l3")
    c = widgets.Container(widgets=[l1, l2, l3])
    assert c[-1] == l3
    # so far they should be in sync
    native = c.native.layout()
    assert native.count() == len(c)
    # much with native layout
    native.addStretch()
    # haven't changed the magicgui container
    assert len(c) == 3
    assert c[-1] == l3
    # though it has changed the native model
    assert native.count() == 4


def test_containers_show_nested_containers():
    """make sure showing a container shows a nested FunctionGui."""

    @magicgui
    def func(x: int, y: str):
        pass

    assert not func.visible
    c2 = widgets.Container(widgets=[func])
    assert not c2.visible
    c2.show()
    assert c2.visible and func.visible
    c2.close()
    assert not func.visible


def test_container_removal():
    c = widgets.Container()
    s = widgets.Slider(label="label")
    assert len(c) == 0
    assert c.native.layout().count() == 0

    c.append(s)
    assert len(c) == 1
    assert c.native.layout().count() == 1

    c.pop()
    assert len(c) == 0
    assert c.native.layout().count() == 0


def test_connection_during_init() -> None:
    class C(widgets.Container):
        def __init__(self) -> None:
            btn = widgets.PushButton()
            btn.changed.connect(self._on_clicked)
            super().__init__(widgets=[btn])

        def _on_clicked(self):
            ...

    assert isinstance(C(), widgets.Container)


def test_parent():
    lbl = widgets.Label()
    inner = widgets.Container(widgets=[lbl])
    outer = widgets.Container()
    outer.append(inner)

    assert lbl.parent is inner
    assert inner.parent is outer
    assert outer.parent is None
