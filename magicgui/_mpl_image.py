"""Most code in this module is vendored from matplotlib

License agreement for matplotlib versions 1.3.0 and later
=========================================================

1. This LICENSE AGREEMENT is between the Matplotlib Development Team
("MDT"), and the Individual or Organization ("Licensee") accessing and
otherwise using matplotlib software in source or binary form and its
associated documentation.

2. Subject to the terms and conditions of this License Agreement, MDT
hereby grants Licensee a nonexclusive, royalty-free, world-wide license
to reproduce, analyze, test, perform and/or display publicly, prepare
derivative works, distribute, and otherwise use matplotlib
alone or in any derivative version, provided, however, that MDT's
License Agreement and MDT's notice of copyright, i.e., "Copyright (c)
2012- Matplotlib Development Team; All Rights Reserved" are retained in
matplotlib  alone or in any derivative version prepared by
Licensee.

3. In the event Licensee prepares a derivative work that is based on or
incorporates matplotlib or any part thereof, and wants to
make the derivative work available to others as provided herein, then
Licensee hereby agrees to include in any such work a brief summary of
the changes made to matplotlib .

4. MDT is making matplotlib available to Licensee on an "AS
IS" basis.  MDT MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, MDT MAKES NO AND
DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF MATPLOTLIB
WILL NOT INFRINGE ANY THIRD PARTY RIGHTS.

5. MDT SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF MATPLOTLIB
 FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR
LOSS AS A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING
MATPLOTLIB , OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF
THE POSSIBILITY THEREOF.

6. This License Agreement will automatically terminate upon a material
breach of its terms and conditions.

7. Nothing in this License Agreement shall be deemed to create any
relationship of agency, partnership, or joint venture between MDT and
Licensee.  This License Agreement does not grant permission to use MDT
trademarks or trade name in a trademark sense to endorse or promote
products or services of Licensee, or any third party.

8. By copying, installing or otherwise using matplotlib ,
Licensee agrees to be bound by the terms and conditions of this License
Agreement.
"""

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Collection, Union

try:
    import numpy as np
except ImportError as e:  # pragma: no cover
    msg = "Numpy required to use images in magicgui: use `pip install magicgui[image]`"
    raise type(e)(msg) from e

_log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pathlib import Path

    import PIL.Image


def _is_mpl_norm(norm):
    try:
        from matplotlib import colors
    except ImportError:
        return False
    else:
        return isinstance(norm, colors.Normalize)


def _is_mpl_cmap(cmap):
    try:
        from matplotlib import colors
    except ImportError:
        return False
    else:
        return isinstance(cmap, colors.Colormap)


def _is_pil_image(image):
    try:
        from PIL.Image import Image
    except ImportError:
        return False
    else:
        return isinstance(image, Image)


# NOT from mpl
class Colormap:
    """Colormap that relates intensity values to colors.

    This colormap class is borrowed from napari, not mpl, but
    the ``__call__`` function has a similar API (without alpha).
    magicgui is also compatible with mpl colormap instances.

    Attributes
    ----------
    colors : array, shape (N, 4)
        Data used in the colormap.
    controls : array, shape (N,) or (N+1,)
        Control points of the colormap.
    interpolation : str
        Colormap interpolation mode, either 'linear' or
        'zero'. If 'linear', ncontrols = ncolors (one
        color per control point). If 'zero', ncontrols
        = ncolors+1 (one color per bin).
    """

    def __init__(
        self,
        colors: Collection = [[0.0, 0.0, 0.0, 1.0], [1.0, 1.0, 1.0, 1.0]],
        controls: Collection = np.zeros((0, 4)),
        interpolation: str = "linear",
    ) -> None:
        self.interpolation = interpolation
        self._colors = np.atleast_2d(colors)
        self._controls = controls

        if len(self.controls) == 0:
            n_controls = len(self._colors) + int(self.interpolation == "nearest")
            self._controls = np.linspace(0, 1, n_controls)

    @property
    def colors(self):
        return self._colors

    @property
    def controls(self):
        return self._controls

    def __call__(self, values, bytes=False):
        values = np.atleast_1d(values)

        lut = self.colors
        if self.interpolation == "linear":
            # One color per control point
            cols = [np.interp(values, self.controls, lut[:, i]) for i in range(4)]
            cols = np.stack(cols, axis=-1)
        elif self.interpolation == "nearest":
            # One color per bin
            indices = np.clip(np.searchsorted(self.controls, values) - 1, 0, len(lut))
            cols = lut[indices.astype(np.int32)]
        else:
            raise ValueError("Unrecognized Colormap Interpolation Mode")

        if bytes:
            cols = (cols * 255).astype(np.uint8)

        return cols


def get_cmap(name):
    if isinstance(name, Colormap) or _is_mpl_cmap(name):
        return name
    elif isinstance(name, str):
        try:
            import matplotlib.cm
        except ImportError:
            raise ImportError("must install matplotlib to specify colormaps by name")
        else:
            return matplotlib.cm.get_cmap(name)
    return Colormap()


class Normalize:
    """
    A class which, when called, linearly normalizes data into the
    ``[0.0, 1.0]`` interval.
    """

    def __init__(self, vmin=None, vmax=None, clip=False):
        """
        Parameters
        ----------
        vmin, vmax : float or None
            If *vmin* and/or *vmax* is not given, they are initialized from the
            minimum and maximum value, respectively, of the first input
            processed; i.e., ``__call__(A)`` calls ``autoscale_None(A)``.

        clip : bool, default: False
            If ``True`` values falling outside the range ``[vmin, vmax]``,
            are mapped to 0 or 1, whichever is closer, and masked values are
            set to 1.  If ``False`` masked values remain masked.

            Clipping silently defeats the purpose of setting the over, under,
            and masked colors in a colormap, so it is likely to lead to
            surprises; therefore the default is ``clip=False``.

        Notes
        -----
        Returns 0 if ``vmin == vmax``.
        """
        self.vmin = vmin
        self.vmax = vmax
        self.clip = clip

    @staticmethod
    def process_value(value):
        """
        Homogenize the input *value* for easy and efficient normalization.

        *value* can be a scalar or sequence.

        Returns
        -------
        result : masked array
            Masked array with the same shape as *value*.
        is_scalar : bool
            Whether *value* is a scalar.

        Notes
        -----
        Float dtypes are preserved; integer types with two bytes or smaller are
        converted to np.float32, and larger types are converted to np.float64.
        Preserving float32 when possible, and using in-place operations,
        greatly improves speed for large arrays.
        """
        is_scalar = not np.iterable(value)
        if is_scalar:
            value = [value]
        dtype = np.min_scalar_type(value)
        if np.issubdtype(dtype, np.integer) or dtype.type is np.bool_:
            # bool_/int8/int16 -> float32; int32/int64 -> float64
            dtype = np.promote_types(dtype, np.float32)
        # ensure data passed in as an ndarray subclass are interpreted as
        # an ndarray. See issue #6622.
        mask = np.ma.getmask(value)
        data = np.asarray(value)
        result = np.ma.array(data, mask=mask, dtype=dtype, copy=True)
        return result, is_scalar

    def __call__(self, value, clip=None):
        """
        Normalize *value* data in the ``[vmin, vmax]`` interval into the
        ``[0.0, 1.0]`` interval and return it.

        Parameters
        ----------
        value
            Data to normalize.
        clip : bool
            If ``None``, defaults to ``self.clip`` (which defaults to
            ``False``).

        Notes
        -----
        If not already initialized, ``self.vmin`` and ``self.vmax`` are
        initialized using ``self.autoscale_None(value)``.
        """
        if clip is None:
            clip = self.clip

        result, is_scalar = self.process_value(value)

        self.autoscale_None(result)
        # Convert at least to float, without losing precision.
        (vmin,), _ = self.process_value(self.vmin)
        (vmax,), _ = self.process_value(self.vmax)
        if vmin == vmax:
            result.fill(0)  # Or should it be all masked?  Or 0.5?
        elif vmin > vmax:
            raise ValueError("minvalue must be less than or equal to maxvalue")
        else:
            if clip:
                mask = np.ma.getmask(result)
                result = np.ma.array(
                    np.clip(result.filled(vmax), vmin, vmax), mask=mask
                )
            # ma division is very slow; we can take a shortcut
            resdat = result.data
            resdat -= vmin
            resdat /= vmax - vmin
            result = np.ma.array(resdat, mask=result.mask, copy=False)
        if is_scalar:
            result = result[0]
        return result

    def autoscale(self, A):
        """Set *vmin*, *vmax* to min, max of *A*."""
        A = np.asanyarray(A)
        self.vmin = A.min()
        self.vmax = A.max()

    def autoscale_None(self, A):
        """If vmin or vmax are not set, use the min/max of *A* to set them."""
        A = np.asanyarray(A)
        if self.vmin is None and A.size:
            self.vmin = A.min()
        if self.vmax is None and A.size:
            self.vmax = A.max()

    def scaled(self):
        """Return whether vmin and vmax are set."""
        return self.vmin is not None and self.vmax is not None


class ScalarMappable:
    """
    A mixin class to map scalar data to RGBA.

    The ScalarMappable applies data normalization before returning RGBA colors
    from the given colormap.
    """

    def __init__(self, norm=None, cmap=None):
        """

        Parameters
        ----------
        norm : `matplotlib.colors.Normalize` (or subclass thereof)
            The normalizing object which scales data, typically into the
            interval ``[0, 1]``.
            If *None*, *norm* defaults to a *colors.Normalize* object which
            initializes its scaling based on the first data processed.
        cmap : str or `~matplotlib.colors.Colormap`
            The colormap used to map normalized data values to RGBA colors.
        """
        self._A = None
        self.norm = None  # So that the setter knows we're initializing.
        self.set_norm(norm)  # The Normalize instance of this ScalarMappable.
        self.cmap = None  # So that the setter knows we're initializing.
        self.set_cmap(cmap)  # The Colormap instance of this ScalarMappable.
        #: The last colorbar associated with this ScalarMappable. May be None.
        self.colorbar = None

    def to_rgba(self, x, bytes=False, norm=True):
        """Return a normalized rgba array corresponding to *x*.

        In the normal case, *x* is a 1-D or 2-D sequence of scalars, and
        the corresponding ndarray of rgba values will be returned,
        based on the norm and colormap set for this ScalarMappable.

        There is one special case, for handling images that are already
        rgb or rgba, such as might have been read from an image file.
        If *x* is an ndarray with 3 dimensions,
        and the last dimension is either 3 or 4, then it will be
        treated as an rgb or rgba array, and no mapping will be done.
        The array can be uint8, or it can be floating point with
        values in the 0-1 range; otherwise a ValueError will be raised.
        If it is a masked array, the mask will be ignored.
        If the last dimension is 3, the *alpha* kwarg (defaulting to 1)
        will be used to fill in the transparency.  If the last dimension
        is 4, the *alpha* kwarg is ignored; it does not
        replace the pre-existing alpha.  A ValueError will be raised
        if the third dimension is other than 3 or 4.

        In either case, if *bytes* is *False* (default), the rgba
        array will be floats in the 0-1 range; if it is *True*,
        the returned rgba array will be uint8 in the 0 to 255 range.

        If norm is False, no normalization of the input data is
        performed, and it is assumed to be in the range (0-1).

        """
        # First check for special case, image input:
        try:
            if x.ndim == 3:
                if x.shape[2] == 3:
                    alpha = 1
                    if x.dtype == np.uint8:
                        alpha = np.uint8(alpha * 255)
                    m, n = x.shape[:2]
                    xx = np.empty(shape=(m, n, 4), dtype=x.dtype)
                    xx[:, :, :3] = x
                    xx[:, :, 3] = alpha
                elif x.shape[2] == 4:
                    xx = x
                else:
                    raise ValueError("Third dimension must be 3 or 4")
                if xx.dtype.kind == "f":
                    if norm and (xx.max() > 1 or xx.min() < 0):
                        raise ValueError(
                            "Floating point image RGB values "
                            "must be in the 0..1 range."
                        )
                    if bytes:
                        xx = (xx * 255).astype(np.uint8)
                elif xx.dtype == np.uint8:
                    if not bytes:
                        xx = xx.astype(np.float32) / 255
                else:
                    raise ValueError(
                        "Image RGB array must be uint8 or "
                        "floating point; found %s" % xx.dtype
                    )
                return xx
        except AttributeError:
            # e.g., x is not an ndarray; so try mapping it
            pass

        # This is the normal case, mapping a scalar array:
        x = np.ma.asarray(x)
        if norm:
            x = self.norm(x)
        rgba = self.cmap(x, bytes=bytes)
        return rgba

    def get_cmap(self):
        """Return the `.Colormap` instance."""
        return self.cmap

    def get_clim(self):
        """Return the values (min, max) that are mapped to the colormap limits."""
        return self.norm.vmin, self.norm.vmax

    def set_clim(self, vmin=None, vmax=None):
        """Set the norm limits for image scaling.

        Parameters
        ----------
        vmin, vmax : float
             The limits.

             The limits may also be passed as a tuple (*vmin*, *vmax*) as a
             single positional argument.

             .. ACCEPTS: (vmin: float, vmax: float)
        """
        if vmax is None:
            try:
                vmin, vmax = vmin
            except (TypeError, ValueError):
                pass
        if vmin is not None:
            self.norm.vmin = vmin
        if vmax is not None:
            self.norm.vmax = vmax
        self.changed()

    def set_cmap(self, cmap):
        """Set the colormap for luminance data.

        Parameters
        ----------
        cmap : `.Colormap` or str or None
        """
        in_init = self.cmap is None
        cmap = get_cmap(cmap)
        self.cmap = cmap
        if not in_init:
            self.changed()  # Things are not set up properly yet.

    def set_norm(self, norm):
        """Set the normalization instance.

        Parameters
        ----------
        norm : `.Normalize` or None

        Notes
        -----
        If there are any colorbars using the mappable for this norm, setting
        the norm of the mappable will reset the norm, locator, and formatters
        on the colorbar to default.
        """
        if norm is not None and not (isinstance(norm, Normalize) or _is_mpl_norm(norm)):
            raise TypeError(
                "`norm` must be an instance of mpl.Normalize or magicgui.Normalize"
            )
        in_init = self.norm is None
        if norm is None:
            norm = Normalize()
        self.norm = norm
        if not in_init:
            self.changed()  # Things are not set up properly yet.

    def autoscale(self):
        """
        Autoscale the scalar limits on the norm instance using the
        current array
        """
        if self._A is None:
            raise TypeError("You must first set_array for mappable")
        self.norm.autoscale(self._A)
        self.changed()

    def autoscale_None(self):
        """
        Autoscale the scalar limits on the norm instance using the
        current array, changing only limits that are None
        """
        if self._A is None:
            raise TypeError("You must first set_array for mappable")
        self.norm.autoscale_None(self._A)
        self.changed()

    def changed(self):
        pass


class Image(ScalarMappable):
    def __init__(self, cmap=None, norm=None):
        super().__init__(norm, cmap)
        self._imcache = None

    def set_data(
        self, A: Union[str, "Path", "np.ndarray", "PIL.Image.Image"], format: str = None
    ):
        """Set the image array.

        Note that this function does *not* update the normalization used.

        Parameters
        ----------
        A : array-like or `PIL.Image.Image`
        """
        from pathlib import Path

        if isinstance(A, Path):
            A = str(A)
        if isinstance(A, str):
            A = imread(A, format=format)
        elif _is_pil_image(A):
            A = pil_to_array(A)  # Needed e.g. to apply png palette.

        if not isinstance(A, np.ndarray):
            raise TypeError(
                "Image data must be a string, Path, numpy array, or PIL.Image"
            )

        # self._A = cbook.safe_masked_invalid(A, copy=True)
        self._A = A.copy()

        if self._A.dtype != np.uint8 and not np.can_cast(
            self._A.dtype, float, "same_kind"
        ):
            raise TypeError(
                "Image data of dtype {} cannot be converted to "
                "float".format(self._A.dtype)
            )

        if self._A.ndim == 3 and self._A.shape[-1] == 1:
            # If just one dimension assume scalar and apply colormap
            self._A = self._A[:, :, 0]

        if not (self._A.ndim == 2 or self._A.ndim == 3 and self._A.shape[-1] in [3, 4]):
            raise TypeError(
                f"Invalid shape {self._A.shape} for image data. Data must be 2D "
                "(monochromatic), or 3D: MxNx3 (RGB) or MxNx4 (RGBA)"
            )

        if self._A.ndim == 3:
            # If the input data has values outside the valid range (after
            # normalisation), we issue a warning and then clip X to the bounds
            # - otherwise casting wraps extreme values, hiding outliers and
            # making reliable interpretation impossible.
            high = 255 if np.issubdtype(self._A.dtype, np.integer) else 1
            if self._A.min() < 0 or high < self._A.max():
                _log.warning(
                    "Clipping input data to the valid range for imshow with "
                    "RGB data ([0..1] for floats or [0..255] for integers)."
                )
                self._A = np.clip(self._A, 0, high)
            # Cast unsupported integer types to uint8
            if self._A.dtype != np.uint8 and np.issubdtype(self._A.dtype, np.integer):
                self._A = self._A.astype(np.uint8)

        self._imcache = None

    def changed(self):
        self._imcache = None

    def make_image(self):
        return self._make_image(self._A)

    def _make_image(self, A):
        """Normalize, rescale, and colormap the image *A*

        Returns
        -------
        image : (M, N, 4) uint8 array
            The RGBA image, resampled unless *unsampled* is True.
        x, y : float
            The upper left corner where the image should be drawn, in pixel
            space.
        trans : Affine2D
            The affine transformation from image to pixel space.
        """
        if A is None:
            raise RuntimeError(
                "You must first set the image " "array or the image attribute"
            )
        if A.size == 0:
            raise RuntimeError(
                "_make_image must get a non-empty image. "
                "Your Artist's draw method must filter before "
                "this method is called."
            )

        if self._imcache is None:
            self._imcache = self.to_rgba(A, bytes=True, norm=(A.ndim == 2))

        return self._imcache


def pil_to_array(pilImage):
    """Load a `PIL image`_ and return it as a numpy int array.

    .. _PIL image: https://pillow.readthedocs.io/en/latest/reference/Image.html

    Returns
    -------
    numpy.array

        The array shape depends on the image type:

        - (M, N) for grayscale images.
        - (M, N, 3) for RGB images.
        - (M, N, 4) for RGBA images.
    """
    if pilImage.mode in ["RGBA", "RGBX", "RGB", "L"]:
        # return MxNx4 RGBA, MxNx3 RBA, or MxN luminance array
        return np.asarray(pilImage)
    elif pilImage.mode.startswith("I;16"):
        # return MxN luminance array of uint16
        raw = pilImage.tobytes("raw", pilImage.mode)
        if pilImage.mode.endswith("B"):
            x = np.frombuffer(raw, ">u2")
        else:
            x = np.frombuffer(raw, "<u2")
        return x.reshape(pilImage.size[::-1]).astype("=u2")
    else:  # try to convert to an rgba image
        try:
            pilImage = pilImage.convert("RGBA")
        except ValueError as err:
            raise RuntimeError("Unknown image mode") from err
        return np.asarray(pilImage)  # return MxNx4 RGBA array


@lru_cache()
def _get_ssl_context():
    try:
        import certifi
    except ImportError:
        return None
    import ssl

    return ssl.create_default_context(cafile=certifi.where())


def imread(fname, format=None):
    """Read an image from a file into an array.

    Parameters
    ----------
    fname : str or file-like
        The image file to read: a filename, a URL or a file-like object opened
        in read-binary mode.
    format : str, optional
        The image file format assumed for reading the data. If not
        given, the format is deduced from the filename.  If nothing can
        be deduced, PNG is tried.

    Returns
    -------
    `numpy.array`
        The image data. The returned array has shape

        - (M, N) for grayscale images.
        - (M, N, 4) for RGBA images. (RGB will be padded to RGBA)
    """
    # hide imports to speed initial import on systems with slow linkers
    from pathlib import Path
    from urllib import parse

    try:
        import PIL.Image
        import PIL.PngImagePlugin
    except ImportError as e:  # pragma: no cover
        msg = (
            f"{e}. To load images from files or urls `pip install pillow`, "
            "or use the image extra: `pip install magicgui[image]`"
        )
        raise type(e)(msg)

    if format is None:
        if isinstance(fname, str):
            parsed = parse.urlparse(fname)
            # If the string is a URL (Windows paths appear as if they have a
            # length-1 scheme), assume png.
            if len(parsed.scheme) > 1:
                ext = parsed.path.rsplit(".", maxsplit=1)[-1] or "png"
            else:
                ext = Path(fname).suffix.lower()[1:]
        elif hasattr(fname, "geturl"):  # Returned by urlopen().
            # We could try to parse the url's path and use the extension, but
            # returning png is consistent with the block above.  Note that this
            # if clause has to come before checking for fname.name as
            # urlopen("file:///...") also has a name attribute (with the fixed
            # value "<urllib response>").
            ext = "png"
        elif hasattr(fname, "name"):
            ext = Path(fname.name).suffix.lower()[1:]
        else:
            ext = "png"
    else:
        ext = format
    img_open = PIL.PngImagePlugin.PngImageFile if ext == "png" else PIL.Image.open
    if isinstance(fname, str):

        parsed = parse.urlparse(fname)
        if len(parsed.scheme) > 1:  # Pillow doesn't handle URLs directly.
            # hide imports to speed initial import on systems with slow linkers
            from urllib import request

            ssl_ctx = _get_ssl_context()
            if ssl_ctx is None:
                from warnings import warn

                warn("Could not get certifi ssl context, https may not work.")
            with request.urlopen(fname, context=ssl_ctx) as response:
                import io

                try:
                    response.seek(0)
                except (AttributeError, io.UnsupportedOperation):
                    response = io.BytesIO(response.read())
                return imread(response, format=ext)
    with img_open(fname) as image:
        return pil_to_array(image)
