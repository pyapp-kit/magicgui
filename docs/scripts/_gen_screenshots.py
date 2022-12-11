import re
import subprocess
from itertools import count
from pathlib import Path

import mkdocs_gen_files
from qtpy.QtWidgets import QApplication

DOCS = Path(__file__).parent.parent
CODE_BLOCK = re.compile(r"```python\n([^`]*)```", re.DOTALL)


def _set_dark_mode(dark_mode: bool):
    """Set the system to dark mode or not."""
    cmd = ["osascript", "-l", "JavaScript", "-e"]
    if dark_mode:
        cmd += ["Application('System Events').appearancePreferences.darkMode = true"]
    else:
        cmd += ["Application('System Events').appearancePreferences.darkMode = false"]
    subprocess.run(cmd)


def _write_markdown_result_image(src: str, ns: dict, dest: str) -> bool:

    wdg = set(QApplication.topLevelWidgets())
    exec(src, ns, ns)
    new_wdg = set(QApplication.topLevelWidgets()) - wdg
    if new_wdg:
        for w in new_wdg:
            w.setMinimumWidth(200)
            w.show()
            w.activateWindow()
            w.update()

            QApplication.processEvents()
            with mkdocs_gen_files.open(dest.replace(".png", "_light.png"), "wb") as f:
                success = w.grab().save(f.name)

            # Not working
            # if DO_DARK:
            #     _set_dark_mode(True)
            #     with mkdocs_gen_files.open(dest.replace(".png", "_dark.png"), "wb") as f2:  # noqa
            #         w.grab().save(f2.name)
            #     _set_dark_mode(False)

            w.close()
            w.deleteLater()
    return success


for mdfile in DOCS.rglob("*.md"):
    md = mdfile.read_text()
    w_iter = count()
    namespace: dict = {}
    for _n, match in enumerate(CODE_BLOCK.finditer(md)):
        code = match.group(1)
        if ".show()" not in code:
            continue
        dest = f"_images/{mdfile.stem}_{next(w_iter)}.png"
        _write_markdown_result_image(code, namespace, dest)
