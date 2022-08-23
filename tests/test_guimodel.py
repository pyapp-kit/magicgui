"""For now, this module assumes qt backend.
"""
import ipaddress
import uuid
from datetime import date
from enum import Enum
from typing import List, Optional

from magicgui import Field, GUIModel
from magicgui.widgets import Container


def test_basic_model(qapp):
    class Degree(Enum):
        BACHELOR = "Bachelor"
        MASTER = "Master"
        PHD = "PhD"

    class Person(GUIModel):
        name: str
        age: int
        birthday: date
        married: bool = False
        salary: Optional[float] = Field(None, ge=0, le=999999)
        children: List[ipaddress.IPv4Address] = []
        uid: uuid.UUID = Field(default_factory=uuid.uuid4)
        degree: Degree = Degree.BACHELOR

    obj = Person(name="Frank", age=55, married=True, birthday=date(1965, 1, 1))
    assert obj._gui is None
    assert isinstance(obj.gui, Container)
    assert obj._gui is not None

    obj.age = 42
    assert obj.age == 42 == obj.gui.age.value
    obj.gui.age.value = 44
    assert obj.age == 44 == obj.gui.age.value

    obj.birthday = date(2020, 1, 1)
    assert obj.birthday == date(2020, 1, 1) == obj.gui.birthday.value
