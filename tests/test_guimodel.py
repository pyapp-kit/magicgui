"""For now, this module assumes qt backend.
"""
from datetime import date
from magicgui import GUIModel, Field
from magicgui.widgets import Container


def test_basic_model(qapp):
    class MyModel(GUIModel):
        name: str
        age: int
        married: bool
        salary: float = Field(..., ge=0, le=999999)
        birthday: date

    obj = MyModel(
        name="Frank", age=55, married=True, salary=100000, birthday=date(1980, 1, 1)
    )
    assert obj._gui is None
    assert isinstance(obj.gui, Container)
    assert obj._gui is not None

    obj.age = 42
    assert obj.age == 42 == obj.gui.age.value
    obj.gui.age.value = 44
    assert obj.age == 44 == obj.gui.age.value

    obj.birthday = date(2020, 1, 1)
    assert obj.birthday == date(2020, 1, 1) == obj.gui.birthday.value
