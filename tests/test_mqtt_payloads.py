def test_import() -> None:
    # This doesn't really do anything, other than get pydantic
    # to parse the file, and make sure there are no catastrophic issues
    from bell.avr.mqtt.payloads import AVREmptyMessage  # noqa
