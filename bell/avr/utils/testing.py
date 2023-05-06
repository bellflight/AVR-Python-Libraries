from functools import wraps
from typing import Any, Callable


def dont_run_forever(*args, **kwargs) -> Callable:
    """
    Decorator to overwrite the `bell.avr.utils.decorators.run_forever` decorator when writing tests.
    Use like so:

    ```python
    # pip install pytest-mock

    from bell.avr.utils.testing import dont_run_forever
    from pytest_mock.plugin import MockerFixture

    def test_function(mocker: MockerFixture):
        mocker.patch("bell.avr.utils.decorators.run_forever", dont_run_forever)
    ```
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            return f(*args, **kwargs)

        return wrapper

    return decorator
