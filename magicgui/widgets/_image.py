from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple, Union

from ._bases import ValueWidget
from ._concrete import backend_widget

if TYPE_CHECKING:
    from pathlib import Path

    import matplotlib.colors
    import numpy as np
    import PIL.Image

    from magicgui import _mpl_image
    from magicgui.types import Colormap, Normalize

    from ._protocols import ValueWidgetProtocol


@backend_widget
class Image(ValueWidget):
    """A non-editable image display."""

    _widget: ValueWidgetProtocol
    _image: Optional[_mpl_image.Image] = None

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
        val: Union[str, Path, np.ndarray, PIL.Image.Image],
        cmap: Union[str, Colormap, matplotlib.colors.Colormap] = None,
        norm: Union[_mpl_image.Normalize, matplotlib.colors.Normalize] = None,
        vmin: float = None,
        vmax: float = None,
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
        self.width = im.shape[1]
        self.height = im.shape[0]
        self._widget._mgui_set_value(im)

    @property
    def image_rgba(self) -> Optional[np.ndarray]:
        """Return rendered numpy array."""
        return self._image.make_image() if self._image is not None else None

    @property
    def image_data(self) -> Optional[np.ndarray]:
        """Return image data."""
        return self._image._A if self._image is not None else None

    def get_clim(self) -> Tuple[Optional[float], Optional[float]]:
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

    def set_cmap(self, cmap: Union[str, Colormap, matplotlib.colors.Colormap]):
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

    def set_norm(self, norm: Union[Normalize, matplotlib.colors.Normalize]):
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
