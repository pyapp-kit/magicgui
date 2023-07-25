import warnings
from pathlib import Path

import napari
import qtgallery
from mkdocs_gallery.gen_data_model import GalleryScript
from mkdocs_gallery.scrapers import figure_md_or_html, matplotlib_scraper
from qtpy.QtWidgets import QApplication

warnings.filterwarnings("ignore", category=DeprecationWarning)


def qt_window_scraper(block, script: GalleryScript):
    """Scrape screenshots from open Qt windows.

    Parameters
    ----------
    block : tuple
        A tuple containing the (label, content, line_number) of the block.
    script : GalleryScript
        Script being run

    Returns
    -------
    md : str
        The ReSTructuredText that will be rendered to HTML containing
        the images. This is often produced by :func:`figure_md_or_html`.
    """
    imgpath_iter = script.run_vars.image_path_iterator

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    app.processEvents()

    # get top-level widgets that aren't hidden
    widgets = [w for w in app.topLevelWidgets() if not w.isHidden()]

    image_paths = []
    for widg, imgpath in zip(widgets, imgpath_iter):
        pixmap = widg.grab()
        pixmap.save(str(imgpath))
        image_paths.append(imgpath)
        widg.close()

    return figure_md_or_html(image_paths, script)


def napari_image_scraper(block, script: GalleryScript):
    """Scrape screenshots from napari windows.

    Parameters
    ----------
    block : tuple
        A tuple containing the (label, content, line_number) of the block.
    script : GalleryScript
        Script being run

    Returns
    -------
    md : str
        The ReSTructuredText that will be rendered to HTML containing
        the images. This is often produced by :func:`figure_md_or_html`.
    """
    viewer = napari.current_viewer()
    if viewer is not None:
        image_path = next(script.run_vars.image_path_iterator)
        viewer.screenshot(canvas_only=False, flash=False, path=image_path)
        viewer.close()
        return figure_md_or_html([image_path], script)
    else:
        return ""


def _reset_napari(gallery_conf, file: Path):
    # Close all open napari windows and reset theme
    while napari.current_viewer() is not None:
        napari.current_viewer().close()
    settings = napari.settings.get_settings()
    settings.appearance.theme = "dark"
    # qtgallery manages the event loop so it
    # is not completely blocked by napari.run()
    qtgallery.reset_qapp(gallery_conf, file)


conf = {
    "image_scrapers": [napari_image_scraper, qt_window_scraper, matplotlib_scraper],
    "reset_modules": [_reset_napari, qtgallery.reset_qapp],
}
