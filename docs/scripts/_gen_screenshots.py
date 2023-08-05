import re
import subprocess
from itertools import count
from pathlib import Path
from textwrap import dedent

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


# internally used trick to leave a window open at the end of a cell
# add this to the end of a cell to leave it open
LEAVE_OPEN = "# leave open"
LEFT_OPEN = False


def _clear_left_open() -> None:
    global LEFT_OPEN
    for w in QApplication.topLevelWidgets():
        w.close()
        w.deleteLater()
    QApplication.processEvents()
    LEFT_OPEN = False


def _write_markdown_result_image(src: str, ns: dict, dest: str) -> None:
    global LEFT_OPEN
    top_widgets = set(QApplication.topLevelWidgets())
    try:
        exec(src, ns, ns)
    except NameError as e:
        raise NameError(
            f"Error evaluating code for {dest!r} with namespace {set(ns)!r}:\n\n{src}. "
            f"{e}"
        ) from e

    if not LEFT_OPEN:
        top_widgets = set(QApplication.topLevelWidgets()) - top_widgets
    if not top_widgets:
        print("No top level widgets found for", dest)
    if len(top_widgets) > 1:
        name = re.search(r"([^\s\.]+).show\(\)", src, re.DOTALL)[1]
        try:
            top_widgets = {ns[name].native}
        except KeyError:
            pass  # FIXME... it's probably an attribute
    for w in top_widgets:
        w.setMinimumWidth(200)
        w.show()
        w.activateWindow()
        w.update()

        with mkdocs_gen_files.open(dest, "wb") as f:
            if not w.grab().save(f.name):
                print("Error saving", dest)

        if LEAVE_OPEN in src:
            LEFT_OPEN = True
        else:
            _clear_left_open()


EXCLUDE = {"migration.md"}


def main() -> None:
    for mdfile in sorted(DOCS.rglob("*.md"), reverse=True):
        if mdfile.name in EXCLUDE:
            continue
        _clear_left_open()

        md = mdfile.read_text()
        w_iter = count()
        code_blocks = list(CODE_BLOCK.finditer(md))
        has_show = any(".show()" in match.group(0) for match in code_blocks)
        if has_show:
            namespace: dict = {}
            for match in code_blocks:
                code = dedent(match.group(1))
                if ".show()" in match.group(0):
                    dest = f"_images/{mdfile.stem}_{next(w_iter)}.png"
                    _write_markdown_result_image(code, namespace, dest)
                else:
                    # still need to execute the code to populate the namespace
                    # for later code blocks
                    exec(code, namespace, namespace)


main()
