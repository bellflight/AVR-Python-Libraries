import os
from unittest import mock

from bell.avr.utils.env import get_env_int


def test_default() -> None:
    assert get_env_int("DOESN'T EXIST") is None
    assert get_env_int("DOESN'T EXIST", 42) == 42


@mock.patch.dict(os.environ, {"BELL_TEST": "42"})
def test_value() -> None:
    assert get_env_int("BELL_TEST") == 42
    assert get_env_int("BELL_TEST", 36) == 42


@mock.patch.dict(os.environ, {"BELL_TEST": "abc"})
def test_invalid_value() -> None:
    assert get_env_int("BELL_TEST") is None
    assert get_env_int("BELL_TEST", 36) == 36
