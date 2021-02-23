from functools import wraps
from time import time


def rate_limited(t):
    """Prevent a function from being called more than once in `t` seconds."""

    def decorator(f):
        last = [0.0]

        @wraps(f)
        def wrapper(*args, **kwargs):
            if last[0] and (time() - last[0] < t):
                return
            last[0] = time()
            return f(*args, **kwargs)

        return wrapper

    return decorator
