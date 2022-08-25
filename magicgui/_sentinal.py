class _Undefined:
    """Sentinel class to indicate the lack of a value when ``None`` is ambiguous.

    ``_Undefined`` is a singleton.
    """

    _singleton = None

    def __new__(cls):
        if _Undefined._singleton is None:
            _Undefined._singleton = super().__new__(cls)
        return _Undefined._singleton

    def __repr__(self):
        return "<Undefined>"

    def __bool__(self):
        return False


Undefined = _Undefined()
