from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Literal

from ._bases import ValueWidget
from ._concrete import backend_widget

if TYPE_CHECKING:
    from pathlib import Path

    import matplotlib.colors
    import numpy as np
    import PIL.Image

    from magicgui import _mpl_image
    from magicgui._mpl_image import Colormap, Normalize

    from ._protocols import ValueWidgetProtocol


@backend_widget
class Image(ValueWidget):
    """A non-editable image display."""

    _widget: ValueWidgetProtocol
    _image: _mpl_image.Image | None = None

    @property
    def value(self):
        """Return current image array."""
        return self._image._A if self._image else None

    @value.setter
    def value(self, value):
        """Set current data.  Alias for ``image.set_data(value)``."""
        self.set_data(value)

    def set_data(
        self,
        val: str | Path | np.ndarray | PIL.Image.Image,
        cmap: str | Colormap | matplotlib.colors.Colormap = None,
        norm: _mpl_image.Normalize | matplotlib.colors.Normalize = None,
        vmin: float = None,
        vmax: float = None,
        width: int | Literal["auto"] | None = None,
        height: int | Literal["auto"] | None = None,
        format: str = None,
    ):
        """Set image data with various optional display parameters.

        Parameters
        ----------
        val : str, Path, np.ndarray or PIL.Image.Image
            The image data or file to load. Data must be 2D (monochromatic), or
            3D: MxNx3 (RGB) or MxNx4 (RGBA).
        cmap : str, magicgui.types.Colormap, or matplotlib.colors.Colormap, optional
            A colormap to use for monochromatic images.  If a string, matplotlib must
            be installed and the colormap will be selected with ``cm.get_cmap(cmap)``.
        norm : magicgui.types.Normalize, or matplotlib.colors.Normalize, optional
            A normalization object to use for rendering images.  Accepts matplotlib
            Normalize objects.
        vmin : float, optional
            The min contrast limit to use when scaling monochromatic images
        vmax : float, optional
            The max contrast limit to use when scaling monochromatic images
        width : int or "auto", optional
            Set the width of the widget. If "auto", sets the widget size to the image
            size (1:1). If width is provided, height is auto-set based on aspect ratio.
        height : int or "auto", optional
            Set the height of the widget. If "auto", sets the widget size to the image
            size (1:1).  If width is provided, height is auto-set based on aspect ratio.
        format : str, optional
            Force image format type for ``imread`` when ``val`` is provided as a string,
            by default None

        Raises
        ------
        TypeError
            If the provided data shape or type is invalid.
        ImportError
            If a string is provided for ``val`` and PIL is not installed.
        RuntimeError
            If a ``PIL.Image.Image`` instance is provided as data, with an unrecognized
            image mode.
        """
        if self._image is None:
            from magicgui import _mpl_image

            self._image = _mpl_image.Image()

        self._image.set_data(val, format=format)
        self._image.set_clim(vmin, vmax)
        self._image.set_cmap(cmap)
        self._image.set_norm(norm)

        im = self._image.make_image()
        im_height, im_width, *_ = im.shape
        if "auto" in (height, width):
            self.scale_widget_to_image_size()
        elif width:
            self.width = width  # type: ignore
            self.height = width * im_height / im_width
        elif height:
            self.height = height  # type: ignore
            self.width = height * im_width / im_height
        self._widget._mgui_set_value(im)

    def scale_widget_to_image_size(self):
        """Set the size of the widget to the size of the image."""
        if self._image is not None:
            im = self._image.make_image()
            self.width = im.shape[1]
            self.height = im.shape[0]

    @property
    def image_rgba(self) -> np.ndarray | None:
        """Return rendered numpy array."""
        return self._image.make_image() if self._image is not None else None

    @property
    def image_data(self) -> np.ndarray | None:
        """Return image data."""
        return self._image._A if self._image is not None else None

    def get_clim(self) -> tuple[float | None, float | None]:
        """Get contrast limits (for monochromatic images)."""
        return self._image.get_clim() if self._image is not None else (None, None)

    def set_clim(self, vmin: float = None, vmax: float = None):
        """Set contrast limits (for monochromatic images).

        Parameters
        ----------
        vmin : float, optional
            The min contrast limit to use when scaling monochromatic images
        vmax : float, optional
            The max contrast limit to use when scaling monochromatic images
        """
        if self._image is None:
            raise RuntimeError("You add data with `set_data` before setting clims")
        self._image.set_clim(vmin, vmax)
        self._widget._mgui_set_value(self._image.make_image())

    def set_cmap(self, cmap: str | Colormap | matplotlib.colors.Colormap):
        """Set colormap (for monochromatic images).

        Parameters
        ----------
        cmap : str, magicgui.types.Colormap, or matplotlib.colors.Colormap, optional
            A colormap to use for monochromatic images.  If a string, matplotlib must
            be installed and the colormap will be selected with ``cm.get_cmap(cmap)``.
        """
        if self._image is None:
            raise RuntimeError("You add data with `set_data` before setting cmaps")
        self._image.set_cmap(cmap)
        self._widget._mgui_set_value(self._image.make_image())

    def set_norm(self, norm: Normalize | matplotlib.colors.Normalize):
        """Set normalization method.

        Parameters
        ----------
        norm : magicgui.types.Normalize, or matplotlib.colors.Normalize, optional
            A normalization object to use for rendering images.  Accepts matplotlib
            Normalize objects.
        """
        if self._image is None:
            raise RuntimeError("You add data with `set_data` before setting norm")
        self._image.set_norm(norm)
        self._widget._mgui_set_value(self._image.make_image())

    def __repr__(self) -> str:
        """Return representation of widget of instsance."""
        d = self.image_data
        shape = "x".join(map(str, d.shape)) if d is not None else "<no data>"
        return f"{self.widget_type}({shape}, name={self.name!r})"
