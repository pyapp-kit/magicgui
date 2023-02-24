import sys

sys.stderr.write(
    """
===============================
Unsupported installation method
===============================
magicgui does not support installation with `python setup.py install`.
Please use `python -m pip install .` instead.
"""
)
sys.exit(1)


# The below code will never execute, however GitHub is particularly
# picky about where it finds Python packaging metadata.
# See: https://github.com/github/feedback/discussions/6456
#
# To be removed once GitHub catches up.

setup(
    name="magicgui",
    install_requires=[
        "docstring_parser>=0.7",
        "psygnal>=0.5.0",
        "qtpy>=1.7.0",
        "superqt>=0.4.0",
        "typing_extensions",
    ],
)
