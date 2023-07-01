import pytest


def test_import() -> None:
    # This doesn't really do anything, other than get pydantic
    # to parse the file, and make sure there are no catastrophic issues
    from bell.avr.mqtt.payloads import AVREmptyMessage  # noqa


@pytest.mark.parametrize("value", (0, 100, 255))
def test_root_model_pass(value: int) -> None:
    # Test that a root model works correctly.
    from bell.avr.mqtt.payloads import AVRPCMColorSetWrgbItem

    wrgb_item = AVRPCMColorSetWrgbItem(value)  # pyright: ignore
    assert int(wrgb_item) == value


@pytest.mark.parametrize("value", (-1, 256, 123.45))
def test_root_model_fail(value: int) -> None:
    # Test that a root model works correctly.
    from bell.avr.mqtt.payloads import AVRPCMColorSetWrgbItem

    with pytest.raises(ValueError):
        AVRPCMColorSetWrgbItem(value)  # pyright: ignore


def test_root_model_container() -> None:
    # Test that the validator of a class which contains a list of root model
    # objects properly converts types
    from bell.avr.mqtt.payloads import AVRPCMColorSet

    # make sure we actually get a tuple back
    color_set = AVRPCMColorSet(wrgb=(1, 2, 3, 4))
    assert isinstance(color_set.wrgb, tuple)

    # make sure the tuple contains ints
    assert isinstance(color_set.wrgb[0], int)
