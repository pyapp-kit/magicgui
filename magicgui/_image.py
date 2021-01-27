import numpy as np


class Colormap:
    """Colormap that relates intensity values to colors.

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
        colors: np.ndarray,
        controls: np.ndarray = np.zeros((0, 4)),
        interpolation: str = "linear",
    ) -> None:
        self.colors = np.atleast_2d(colors)
        self.controls = controls
        self.interpolation = interpolation

        if len(self.controls) == 0:
            n_controls = len(self.colors) + int(self.interpolation == "nearest")
            self.controls = np.linspace(0, 1, n_controls)

    def __call__(self, values):
        values = np.atleast_1d(values)
        if self.interpolation == "linear":
            # One color per control point
            cols = [
                np.interp(values, self.controls, self.colors[:, i]) for i in range(4)
            ]
            cols = np.stack(cols, axis=1)
        elif self.interpolation == "nearest":
            # One color per binƒ
            indices = np.clip(
                np.searchsorted(self.controls, values) - 1, 0, len(self.colors)
            )
            cols = self.colors[indices.astype(np.int32)]
        else:
            raise ValueError("Unrecognized Colormap Interpolation Mode")

        return cols


from functools import lru_cache


@lru_cache()
def _get_ssl_context():
    try:
        import certifi
    except ImportError:
        return None
    import ssl

    return ssl.create_default_context(cafile=certifi.where())


def imread(fname, format=None):
    """
    Read an image from a file into an array.

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
    from urllib import parse
    from pathlib import Path
    import PIL.Image
    import PIL.PngImagePlugin

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


def _array_to_rgba8888(array):
    if array.ndim == 3:
        if array.shape[-1] == 3:
            shp = array.shape[:2] + (1,)
            _dt = array.dtype
            pad = np.ones(shp, dtype=_dt) * (2 ** (_dt.itemsize * 8) - 1)
            array = np.concatenate((array, pad), axis=-1)
        array = _unmultiplied_rgba8888_to_premultiplied_argb32(array)
    return array


def _unmultiplied_rgba8888_to_premultiplied_argb32(rgba8888):
    """
    Convert an unmultiplied RGBA8888 buffer to a premultiplied ARGB32 buffer.
    """
    import sys
    import numpy as np

    if sys.byteorder == "little":
        argb32 = np.take(rgba8888, [2, 1, 0, 3], axis=2)
        rgb24 = argb32[..., :-1]
        alpha8 = argb32[..., -1:]
    else:
        argb32 = np.take(rgba8888, [3, 0, 1, 2], axis=2)
        alpha8 = argb32[..., :1]
        rgb24 = argb32[..., 1:]
    # Only bother premultiplying when the alpha channel is not fully opaque,
    # as the cost is not negligible.  The unsafe cast is needed to do the
    # multiplication in-place in an integer buffer.
    if alpha8.min() != 0xFF:
        np.multiply(rgb24, alpha8 / 0xFF, out=rgb24, casting="unsafe")
    return argb32


def pil_to_array(pilImage):
    """
    Load a `PIL image`_ and return it as a numpy int array.

    .. _PIL image: https://pillow.readthedocs.io/en/latest/reference/Image.html

    Returns
    -------
    numpy.array

        The array shape depends on the image type:

        - (M, N) for grayscale images.
        - (M, N, 3) for RGB images.
        - (M, N, 4) for RGBA images.
    """
    if pilImage.mode in ["RGBA", "RGBX", "L"]:
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
