from pathlib import Path

import pytest

from magicgui.widgets import Image

_mpl_image = pytest.importorskip("magicgui._mpl_image")
np = pytest.importorskip("numpy")
pilImage = pytest.importorskip("PIL.Image")


def test_image_widget():
    # png works
    image = Image(value=Path(__file__).parent / "_test.png")
    assert isinstance(image._image, _mpl_image.Image)
    assert isinstance(image.image_data, np.ndarray)
    assert isinstance(image.image_rgba, np.ndarray)
    assert image.image_data.shape == (200, 232, 3)
    assert image.image_rgba.shape == (200, 232, 4)

    prev = image.image_data.copy()
    # jpg works works
    image.value = Path(__file__).parent / "_test.jpg"
    # png and jpg different enough
    assert not np.allclose(image.image_data, prev)
    assert image.image_data.shape == (200, 232, 3)
    assert image.image_rgba.shape == (200, 232, 4)

    # 2D float
    image.value = np.random.rand(64, 64)
    assert image.image_data.shape == (64, 64)
    assert image.image_rgba.shape == (64, 64, 4)

    # 2D uint8
    image.value = np.random.randint(0, 255, (60, 60)).astype("uint8")
    assert image.image_data.shape == (60, 60)
    assert image.image_rgba.shape == (60, 60, 4)

    # RGBA float
    image.value = np.random.rand(60, 60, 4).astype("float")
    assert image.image_data.shape == (60, 60, 4)
    assert image.image_rgba.shape == (60, 60, 4)


def test_clim():

    # 2D uint8
    image = Image()
    image.value = np.random.rand(60, 60)
    rendered = image.image_rgba
    assert isinstance(rendered, np.ndarray)
    assert rendered.shape == (60, 60, 4)
    image.set_clim(0.5, 0.7)
    rendered2 = image.image_rgba
    assert not np.allclose(rendered, rendered2)
    assert image.get_clim() == (0.5, 0.7)


def test_empty_image():
    image = Image()
    assert image.image_data is None
    assert image.image_rgba is None
    assert image.get_clim() == (None, None)

    with pytest.raises(RuntimeError):
        image.set_clim(0, 100)
    with pytest.raises(RuntimeError):
        image.set_clim(0, 100)
    with pytest.raises(RuntimeError):
        image.set_cmap("turbo")
    with pytest.raises(RuntimeError):
        image.set_norm(1)


def test_pilImage():

    with pilImage.open(Path(__file__).parent / "_test.jpg") as img:
        image = Image(value=img)
    assert isinstance(image._image, _mpl_image.Image)
    assert isinstance(image.image_data, np.ndarray)
    assert image.image_data.shape == (200, 232, 3)
    assert image._image.make_image().shape == (200, 232, 4)


def test_internal_cmap():
    cmap = _mpl_image.Colormap([[0, 0, 0, 1], [1, 0, 0, 1]])
    image = Image()
    data = np.random.randint(0, 255, (60, 60)).astype("uint8")
    image.set_data(data, cmap=cmap)
    rendered = image.image_rgba
    assert isinstance(rendered, np.ndarray)
    assert rendered.shape == (60, 60, 4)

    image.set_cmap(
        _mpl_image.Colormap([[0, 0, 0, 1], [1, 0, 0, 1]], interpolation="nearest")
    )
    rendered2 = image.image_rgba
    assert isinstance(rendered2, np.ndarray)
    assert not np.allclose(rendered, rendered2)


def test_mpl_cmap():
    cm = pytest.importorskip("matplotlib.cm")

    # 2D uint8
    image = Image()
    data = np.random.randint(0, 255, (60, 60)).astype("uint8")
    image.set_data(data)
    rendered = image.image_rgba
    assert isinstance(rendered, np.ndarray)
    # without a colormap, the output data should be nearly identical
    assert data.size - np.count_nonzero(rendered[..., 0] == data) < data.size * 0.01
    assert isinstance(rendered, np.ndarray)
    assert rendered.shape == (60, 60, 4)

    image.set_cmap("magma")
    rendered2 = image.image_rgba
    assert isinstance(rendered2, np.ndarray)
    # the colormap has been applied
    assert data.size - np.count_nonzero(rendered2[..., 0] == data) > 3000

    # can also use an mpl colormap instance
    image.set_cmap(cm.get_cmap("viridis"))
    rendered3 = image.image_rgba
    assert isinstance(rendered3, np.ndarray)
    # the colormap has been applied
    assert not np.allclose(rendered2, rendered3)


def test_mpl_norm():
    mplcolor = pytest.importorskip("matplotlib.colors")

    # 2D uint8
    image = Image()
    data = np.random.randint(0, 255, (60, 60)).astype("uint8")
    image.set_data(data)
    rendered = image.image_rgba
    assert isinstance(rendered, np.ndarray)
    assert rendered.shape == (60, 60, 4)

    image.set_norm(mplcolor.PowerNorm(0.5))
    rendered2 = image.image_rgba
    assert isinstance(rendered2, np.ndarray)
    assert rendered2.shape == (60, 60, 4)
    assert not np.allclose(rendered, rendered2)
