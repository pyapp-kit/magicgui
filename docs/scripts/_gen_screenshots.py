import re
import subprocess
from itertools import count
from pathlib import Path

import mkdocs_gen_files
from qtpy.QtWidgets import QApplication

DOCS = Path(__file__).parent.parent
CODE_BLOCK = re.compile("``` ?python\n([^`]*)```", re.DOTALL)


def _set_dark_mode(dark_mode: bool):
    """Set the system to dark mode or not."""
    cmd = ["osascript", "-l", "JavaScript", "-e"]
    if dark_mode:
        cmd += ["Application('System Events').appearancePreferences.darkMode = true"]
    else:
        cmd += ["Application('System Events').appearancePreferences.darkMode = false"]
    subprocess.run(cmd)


LEFT_OPEN = False


def _clear_left_open() -> None:
    global LEFT_OPEN
    for w in QApplication.topLevelWidgets():
        w.close()
        w.deleteLater()
    QApplication.processEvents()
    LEFT_OPEN = False


def _write_markdown_result_image(src: str, ns: dict, dest: str):
    global LEFT_OPEN
    top_widgets = set(QApplication.topLevelWidgets())
    exec(src, ns, ns)
    if not LEFT_OPEN:
        top_widgets = set(QApplication.topLevelWidgets()) - top_widgets
    for w in top_widgets:
        w.setMinimumWidth(200)
        w.show()
        w.activateWindow()
        w.update()

        with mkdocs_gen_files.open(dest.replace(".png", "_light.png"), "wb") as f:
            if not w.grab().save(f.name):
                print("Error saving", dest)

        if "# leave open" in src:
            LEFT_OPEN = True
        else:
            _clear_left_open()


for mdfile in sorted(DOCS.rglob("*.md"), reverse=True):
    _clear_left_open()

    md = mdfile.read_text()
    w_iter = count()
    namespace: dict = {}
    for match in CODE_BLOCK.finditer(md):
        if ".show()" not in match.group(0):
            continue
        code = match.group(1)
        dest = f"_images/{mdfile.stem}_{next(w_iter)}.png"
        _write_markdown_result_image(code, namespace, dest)
