from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple, Union

from ._bases import ValueWidget
from ._concrete import backend_widget

if TYPE_CHECKING:
    import matplotlib.colors
    import numpy as np
    import PIL.Image

    from magicgui import _mpl_image

    from ._protocols import ValueWidgetProtocol


@backend_widget
class Image(ValueWidget):
    """A non-editable image display."""

    _widget: "ValueWidgetProtocol"
    _image: Optional["_mpl_image.Image"] = None

    @property
    def value(self):
        """Return current image array."""
        return self._image._A if self._image else None

    @value.setter
    def value(self, value):
        self.set_data(value)

    def set_data(
        self,
        val: Union[str, Path, "np.ndarray", "PIL.Image.Image"],
        cmap: Union[str, "_mpl_image.Colormap", "matplotlib.colors.Colormap"] = None,
        norm: Union["_mpl_image.Normalize", "matplotlib.colors.Normalize"] = None,
        vmin: float = None,
        vmax: float = None,
        format: str = None,
    ):
        """Set image data with various optional display parameters.

        Parameters
        ----------
        val : [type]
            [description]
        cmap : [type], optional
            [description], by default None
        norm : [type], optional
            [description], by default None
        vmin : [type], optional
            [description], by default None
        vmax : [type], optional
            [description], by default None
        format : [type], optional
            [description], by default None

        Raises
        ------
        TypeError
            [description]
        """
        from magicgui import _mpl_image

        if self._image is None:
            self._image = _mpl_image.Image()

        self._image.set_data(val, format=format)
        self._image.set_clim(vmin, vmax)
        self._image.set_cmap(cmap)
        self._image.set_norm(norm)

        im = self._image.make_image()
        self.width = im.shape[1]
        self.height = im.shape[0]
        self._widget._mgui_set_value(im)

    @property
    def image_rgba(self) -> Optional["np.ndarray"]:
        """Return rendered numpy array."""
        if self._image is None:
            return None
        return self._image.make_image()

    @property
    def image_data(self) -> Optional["np.ndarray"]:
        """Return image data."""
        if self._image is None:
            return None
        return self._image._A

    def get_clim(self) -> Tuple[Optional[float], Optional[float]]:
        """Get contrast limits (for monochromatic images)."""
        return self._image.get_clim() if self._image else (None, None)

    def set_clim(self, vmin: float = None, vmax: float = None):
        """Set contrast limits (for monochromatic images)."""
        if self._image is None:
            raise RuntimeError("You add data with `set_data` before setting clims")
        self._image.set_clim(vmin, vmax)
        self._widget._mgui_set_value(self._image.make_image())

    def set_cmap(
        self, cmap: Union[str, "_mpl_image.Colormap", "matplotlib.colors.Colormap"]
    ):
        """Set colormap (for monochromatic images)."""
        if self._image is None:
            raise RuntimeError("You add data with `set_data` before setting cmaps")
        self._image.set_cmap(cmap)
        self._widget._mgui_set_value(self._image.make_image())

    def set_norm(
        self, norm: Union["_mpl_image.Normalize", "matplotlib.colors.Normalize"]
    ):
        """Set normalization method."""
        if self._image is None:
            raise RuntimeError("You add data with `set_data` before setting norm")
        self._image.set_norm(norm)
        self._widget._mgui_set_value(self._image.make_image())
