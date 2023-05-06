import contextlib
import os
from typing import Optional, overload


@overload
def get_env_int(key: str, default: None = None) -> Optional[int]:
    ...


@overload
def get_env_int(key: str, default: int) -> int:
    ...


def get_env_int(key: str, default: Optional[int] = None) -> Optional[int]:
    """
    Similar to [`os.getenv`](https://docs.python.org/3/library/os.html#os.getenv),
    this will get an environment variable that is an integer.
    If the value is not an integer, will return the default value,
    or if no default value is set, will return None.

    Example:

    ```python
    from bell.avr.utils.env import get_env_int

    get_env_int("MQTT_HOST", 18830)
    # returns the value of MQTT_HOST as an integer
    # or 1883 if the environment variable is not set
    # or not an integer.
    ```
    """
    final_value = default
    _env_value = os.getenv(key)

    # try to convert string to int
    if isinstance(_env_value, str):
        with contextlib.suppress(ValueError):
            final_value = int(_env_value)

    return final_value
