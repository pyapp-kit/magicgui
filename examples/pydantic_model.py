from enum import Enum
from typing import Optional, Tuple

from pydantic import BaseModel, Field, conint

from magicgui import magicgui


class S(BaseModel):
    x: int = 1
    s: str = "hi"
    b: bool = True


class E(Enum):
    a = 1
    b = 2
    c = 3


@magicgui
class T(BaseModel):
    boolean: bool
    integer: int = 0
    enum: E = E.b
    optional_str: Optional[str] = None
    string: str = "str"
    constrained: conint(ge=1, le=10) = 5
    constrain_slider: int = Field(25, ge=10, lt=200, ui_widget_type="Slider")
    const: str = Field("some_constant", const=True)
    s: S = Field(default_factory=S)
    tup_int_str: Tuple[int, str, float] = (1, "sr", 12.0)


T.show(run=True)
