import inspect
from typing import Callable, Dict
import wrapt
import napari
from napari import layers
from skimage import filters, data
from functools import partial
from magicgui import magicgui, register_type
from ast import literal_eval
from numpydoc.docscrape import FunctionDoc
from qtpy.QtWidgets import QSlider
from qtpy.QtCore import Qt
from collections import defaultdict
from pydoc import locate


class QDoubleSlider(QSlider):
    PRECISION = 1000

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent=parent)
        self.setMaximum(10)

    def value(self):
        return super().value() / self.PRECISION

    def setValue(self, value):
        super().setValue(value * self.PRECISION)

    def setMaximum(self, value):
        super().setMaximum(value * self.PRECISION)


def docstring_dtypes(func: Callable) -> Dict[str, type]:
    dtypes = {}
    for p in FunctionDoc(func).get("Parameters"):
        type_name = p.type.split(",")[0]
        type_name = "numpy.ndarray" if type_name.startswith("array") else type_name
        _type = locate(type_name)
        if _type:
            dtypes[p.name] = _type
    return dtypes


def docstring_choices(func: Callable) -> Dict[str, set]:
    """Finds parameters in the signature of `func` that declare a set of valid options.

    Parameters
    ----------
    func : Callable
        the function

    Returns
    -------
    Dict[str, set]
        param_name: {choices}
    """
    choices = {}
    for p in FunctionDoc(func).get("Parameters"):
        if p.type.startswith("{'"):
            try:
                choices[p.name] = literal_eval(p.type.split("},")[0] + "}")
            except Exception:
                pass
    return choices


def get_parameter_position(func: Callable, param: str) -> int:
    """Returns the position of `param` in the signature of function `func`.

    Parameters
    ----------
    func : Callable
        A function with a signature
    param : str
        The name of the parameter to search for

    Returns
    -------
    int
        The position of the parameter in the signature, or -1 if not found.
    """
    try:
        return next(
            i
            for i, p in enumerate(inspect.signature(func).parameters.values())
            if p.name == param
        )
    except StopIteration:
        return -1


def argspec_factory(wrapped, replace_annotations=None, ns=None):
    """given a function, returns a new function"""
    ns = ns or dict()
    replace_annotations = replace_annotations or dict()

    sig = inspect.signature(wrapped)
    new_params = []
    for param in sig.parameters.values():
        if param.name in replace_annotations:
            new_annotation = replace_annotations[param.name]
            param = param.replace(annotation=new_annotation)
        new_params.append(param)
    new_sig = sig.replace(parameters=new_params)
    exec(f"def adapter{new_sig}: pass", ns, ns)
    return ns["adapter"]


image2layer = partial(
    argspec_factory,
    replace_annotations={"image": napari.layers.Layer},
    ns={"napari": napari},
)


@wrapt.decorator(adapter=wrapt.adapter_factory(image2layer))
def layer_adaptor(wrapped, instance=None, args=None, kwargs=None):
    print("CALLED ", args, kwargs)
    image_idx = get_parameter_position(wrapped, "image")
    if len(args) >= (image_idx + 1):
        args = list(args)
        if hasattr(args[image_idx], "data"):
            args[image_idx] = args[image_idx].data
    elif "image" in kwargs:
        if hasattr(kwargs["image"], "data"):
            kwargs["image"] = kwargs["image"].data
    return wrapped(*args, **kwargs)


def get_image_functions(module) -> Dict[str, Callable]:
    adapted_functions = {}
    for funcname in dir(module):
        if funcname.startswith("_"):
            continue
        func = getattr(module, funcname)
        if not inspect.isfunction(func):
            continue
        sig = inspect.signature(func)
        if "image" in sig.parameters:
            adapted_functions[funcname] = layer_adaptor(func)
    return adapted_functions

register_type(float, widget_type=QDoubleSlider)
register_type(int, widget_type=QDoubleSlider)

adapted_functions = get_image_functions(filters)
guis = {}
for k, func in adapted_functions.items():
    opts = defaultdict(dict)
    opts.update({"ignore": ["output"], "auto_call": True})
    choices = docstring_choices(func)
    dtypes = docstring_dtypes(func)
    if choices:
        for pname, choice in choices.items():
            opts[pname]["choices"] = choice
    if dtypes:
        for pname, dtype in dtypes.items():
            opts[pname]["dtype"] = dtype
    guis[k] = magicgui(func, **opts)


def get_layers(layer_type):
    return tuple(l for l in viewer.layers if isinstance(l, layer_type))


register_type(layers.Layer, choices=get_layers)


with napari.gui_qt():
    # create a viewer and add a couple image layers
    viewer = napari.Viewer()
    viewer.add_image(data.astronaut().mean(-1))

    fun = guis['hessian']
    # instantiate the widget
    gui = fun.Gui()

    def show_result(result):
        """callback function for whenever the image_arithmetic functions is called"""
        try:
            outlayer = viewer.layers["blurred"]
            outlayer.data = result
        except KeyError:
            outlayer = viewer.add_image(data=result, name="blurred")

    fun.called.connect(show_result)
    viewer.window.add_dock_widget(gui)
    viewer.layers.events.added.connect(lambda x: gui.fetch_choices("image"))
    viewer.layers.events.removed.connect(lambda x: gui.fetch_choices("image"))
