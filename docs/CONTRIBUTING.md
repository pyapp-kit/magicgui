# Contributing

Contributions are welcome!

## Development

To install `magicgui` for development, first clone the repository:

```bash
git clone https://github.com/pyapp-kit/magicgui
cd magicgui
```

Then install the package in editable mode with the `dev` extra:

```bash
pip install -e .[dev]
```

To run the tests:

```bash
pytest
```

## Code Quality

`magicgui` attempts to adhere to strict coding rules and employs the following
static analysis tools to prevent errors from being introduced into the codebase:

- [black](https://github.com/psf/black) - code formatting
- [ruff](https://github.com/charliermarsh/ruff) - linting
- [mypy](http://mypy-lang.org/) - static type analysis
- [codecov](https://codecov.io/) - test coverage

To prevent continuous integration failures when contributing, please consider
installing [pre-commit](https://pre-commit.com/) in your environment to run all
of these checks prior to checking in new code.

```shell
pre-commit install
```

To run the checks manually, you can use:

```shell
pre-commit run --all-files
```

## Adding a widget

> *These instructions may change in the future as the repo structures changes.
> If they appear outdated as you follow them, please open an issue.*

To add a new widget, you will need to:

1. Create a new class in `magicgui/widgets/_concrete.py` that inherits from the
   base class most appropriate for your widget (e.g. `ValueWidget`, or
   `CategoricalWidget`).

    > *In some (complex) cases, you may need to extend one of the base classes.
    > If so, it is likely that you will also need to extend one of the
    > `Protocols` found in `magicgui.widgets.protocols`.  This is where all of
    > protocols that backend classes need to implement to work with a given
    > widget type. (Don't hesitate to open an issue if you're confused).*

1. Most likely, you will want to decorate the class with `@backend_widget`.
   Using this decorator implies that there is a class with the same name in any
   any backend modules that will support this widget type (e.g.
   `magicgui.backends._qtpy.widgets` for Qt support.).
1. Make any changes necessary to your new concrete class. For example, you may
   need to change the `value` property and corresponding setter to handle a
   specific type.  This part of the code should be backend agnostic.
1. Export the new class in `magicgui/widgets/__init__.py` so that it can be
   imported from `magicgui.widgets`.
1. Implement the backend widget class (using the same class name) in the
   appropriate backend module (e.g. `magicgui.backends._qtpy.widgets` for Qt
   support).  Usually this will mean implementing the appropriate
   `_mgui_get/set_...` methods for the `Protocol` of the corresponding widget
   base class your chose to extend.
1. Export the backend widget class in the `__init__.py` of the backend module
   (e.g. `magicgui.backends._qtpy.__init__.py` for Qt support).  This is
   important, as that is where the `@backend_widget` decorator will look.
1. Add a test for your new widget.

> *For an example of a minimal PR adding a new widget, see
> [\#483](https://github.com/pyapp-kit/magicgui/pull/483/files), which added a
> `QuantityWidget` to be used with `pint.Quantity` objects.*

### Associating a widget with a type

To associate your new widget with a specific type such that it will be used when
someone annotates a parameter with that type, you will need to update code in
`magicgui.type_map._type_map`.

In the simplest of cases, this will mean adding a new entry to the
`magicgui.type_map._type_map._SIMPLE_TYPES` dict.  This is a mapping from a
python type to a widget class.  (Note that all subclasses of the type will also
be matched.)

For more complex cases, you can add a new conditional to the body of the
`match_type` function.  That function should always return a tuple of widget
type, and kwargs that will be passed to the widget constructor. For example:
`return widgets.MyNewWidget, {}`.

### Building the documentation

To build the documentation locally, you will need to install the `docs` extra:

```bash
pip install -e .[docs]
```

Then, from the root of the repository, run:

```bash
mkdocs serve
```

This will start a local server at `http://127.0.0.1:8000/` where you can view
the documentation as you edit it.
