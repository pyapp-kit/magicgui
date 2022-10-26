import os
import sys

import pytest

if os.getenv("CI") and not sys.platform.startswith("linux"):
    pytest.skip("Typing tests not working here at the moment.", allow_module_level=True)
