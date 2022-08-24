import os

import pytest

if os.name == "nt":
    pytest.skip(allow_module_level=True)
