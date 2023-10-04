"""# Password login

A password login field widget.
"""
from magicgui import magicgui


# note that "password" is a special keyword argument
# it will create a password field in the gui by default
# (unless you override "widget_type")
# whereas "password2" will be a normal text field
# (unless you override "widget_type")
@magicgui(password2={"widget_type": "Password"})
def login(username: str, password: str, password2: str):
    """User login credentials."""
    ...


login.show(run=True)
