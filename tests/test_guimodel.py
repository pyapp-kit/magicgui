"""For now, this module assumes qt backend.
"""

from datetime import datetime
from typing import Optional
import pydantic
from dataclasses import dataclass
from attrs import define


class User:
    id: int
    name = "John Doe"
    signup_ts: datetime


dUser = dataclass(User)
aUser = define(User)
pUser = pydantic.create_model("User", **User.__annotations__)


def dataclass_base(obj):
    # dataclasses
    if hasattr(obj, "__dataclass_fields__"):
        return obj.__dataclass_fields__
    # attrs
    if hasattr(obj, "__attrs_attrs__"):
        return obj.__attrs_attrs__
    # pydantic
    if hasattr(obj, "__fields__"):
        return obj.__fields__

# named tuple
# typed dict
