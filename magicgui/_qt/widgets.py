def __getattr__(attr):
    known = {
        "LiteralEvalEdit": "LiteralEvalLineEdit",
        "MagicFileDialog": "FileEdit",
        "MagicFilesDialog": "FileEdit",
        "QDoubleSlider": "FloatSlider",
        "QLogSlider": "LogSlider",
        "QDataComboBox": "ComboBox",
    }
    if attr in known:
        import warnings

        warnings.warn(
            "\n\nThe 'magicgui._qt.widgets' module has been removed.\n"
            f"For {attr!r}, please use 'magicgui.widgets.{known[attr]}' directly.\n"
            f"(Or just use the string `widget_type={known[attr]!r}`)\n"
            "In the future this will raise an exception.\n",
            FutureWarning,
        )
        return known[attr]
    raise AttributeError(
        f"magicgui._qt.widgets has no attribute {attr}... But you should'nt be looking"
        "In here in the first place! The 'magicgui._qt.widgets' module has been removed"
        " in v0.2.0"
    )
