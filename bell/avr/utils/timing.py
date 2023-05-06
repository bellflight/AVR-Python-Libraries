import sys
import time
from typing import Callable, Optional

_LAST_EXECUTION_TIME = {}


def rate_limit(
    fun: Callable, period: Optional[float] = None, frequency: Optional[float] = None
) -> None:
    """
    Run the given callable every `period` seconds, or `frequency` times per second.
    Either `period` or `frequency` must be set.

    Example:

    ```python
    for _ in range(10):
        # add() will only run twice
        timing.rate_limit(add, period=5)
        time.sleep(1)
    ```

    This works by tracking calls to the `rate_limit` function from a line number
    within a file, so multiple calls to `rate_limit` say within a loop
    with the same callable and period will be treated separately. This allows
    for dynamic frequency manipulation.
    """
    if frequency is not None:
        period = 1 / frequency

    assert period is not None

    # in order to allow dynamic rate limits, record things based on the
    # file and line number it came from. Not impervious to live ast rewriting
    # but that seems unlikely
    frame = sys._getframe(1)
    context = frame.f_globals.get("__name__", frame.f_code.co_filename)
    lineno = frame.f_lineno
    instance = f"{context}:{lineno}"

    # see if this instance has never run before, or too much time has elapsed
    if (
        instance not in _LAST_EXECUTION_TIME
        or (time.time() - _LAST_EXECUTION_TIME[instance]) > period
    ):
        fun()
        _LAST_EXECUTION_TIME[instance] = time.time()
