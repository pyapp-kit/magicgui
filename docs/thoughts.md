# thoughts

!!! warning "API in flux!"
    This is an experimental project at the moment... these are just some thoughts.

## type inference

`magicgui` determines the `type` of an argument as follows:

1. If a [type hint](https://docs.python.org/3/library/typing.html) is provided, it is
   used (regardless of the `type` of the default value, if provided).
2. If no type hint is provided, the `type` of the default value is used, if one is
   provided.
3. If a bare argument is defined without a `type` annotation or default value, it is
   assumed to be a string.

```python
# arg is assumed to be a float
def function(arg: float = 1):
    ...

# arg is assumed to be a float
def function(arg = 1.0):
    ...

# arg is assumed to be a str
def function(arg):
    ...
```

## type-to-widget conversion

## drop-down menus

to get a [drop-down list](https://en.wikipedia.org/wiki/Drop-down_list):

- use an `Enum` as either the default value or type hint for an argument

```python
class RefractiveIndex(Enum):
    Oil = 1.515
    Water = 1.33
    Air = 1.0

def function(ri = RefractiveIndex.Water):
    ...
```

- use `arg['choices']` when calling `@magicgui`.

```python
@magicgui(arg={"choices": ["Oil", "Water", "Air"]})
def function(ri="Water"):
    ...
```

!!! note

    when getting and setting attributes on a ComboBox widget in a `magicgui` widget, the
    value will always be converted to and return as a `str`.  You must handle conversion
    from `str` type back to your internal type.  

    ```python
    a, b, c = MyClass('a'), MyClass('b'), MyClass('c')
    @magicgui(item={'choices': [a, b, c]})
    def function(item: MyClass = b):
        ...
    
    widget = function.Gui()
    # when you get the current value, it will be returned as a str
    current = widget.item
    print(current)  # 'b'
    type(current)  # str

    # when you set the current value, in will be cast as a str
    widget.item = a  # same as str(a)

    ```
