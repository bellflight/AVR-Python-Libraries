from typing import Any

import pytest

from bell.avr.mqtt.payloads import AVREmptyMessage, AVRPCMServo
from bell.avr.mqtt.serializer import deserialize_payload, serialize_payload


@pytest.mark.parametrize(
    "topic, payload, expected",
    [
        (  # pydantic class for a known topic
            "avr/pcm/servo/open",
            AVRPCMServo(servo=2),
            '{"servo":2}',
        ),
        (  # pydantic class for an unknown topic
            "notreal",
            AVRPCMServo(servo=2),
            '{"servo":2}',
        ),
        (  # dict for a known topic
            "avr/pcm/servo/open",
            {"servo": 2},
            '{"servo":2}',
        ),
        (  # dict for an unknown topic
            "notreal",
            {"servo": 2},
            '{"servo": 2}',
        ),
        (  # json string for a known topic
            "avr/pcm/servo/open",
            '{"servo": 2}',
            '{"servo":2}',
        ),
        (  # json string for an unknown topic
            "notreal",
            '{"servo": 2}',
            '{"servo": 2}',
        ),
        (  # no payload for a known topic
            "avr/pcm/laser/fire",
            None,
            "{}",
        ),
        (  # no payload for an unknown topic
            "notreal",
            None,
            "{}",
        ),
        (  # empty string for a known topic
            "avr/pcm/laser/fire",
            "",
            "{}",
        ),
        (  # empty string for an unknown topic
            "notreal",
            "",
            "{}",
        ),
        (  # empty json for a known topic
            "avr/pcm/laser/fire",
            "{}",
            "{}",
        ),
        (  # empty json for an unknown topic
            "notreal",
            "{}",
            "{}",
        ),
        (  # empty payload for a known topic
            "avr/pcm/laser/fire",
            AVREmptyMessage(),
            "{}",
        ),
        (  # empty payload for an unknown topic
            "notreal",
            AVREmptyMessage(),
            "{}",
        ),
        (  # unexepcted payload for an unknown topic
            "notreal",
            False,
            "false",
        ),
    ],
)
def test_serialize_payload(topic: str, payload: Any, expected: str) -> None:
    assert serialize_payload(topic, payload) == expected


@pytest.mark.parametrize(
    "topic, payload",
    [
        (  # pydantic class for wrong topic
            "avr/fcm/position/local",
            AVRPCMServo(servo=2),
        ),
        (  # pydantic validation error from dict
            "avr/fcm/position/local",
            {"n": 1, "e": 2},  # no 'd' key
        ),
        (  # pydantic validation error from json string
            "avr/fcm/position/local",
            '{"n": 1, "e": 2}',  # no 'd' key
        ),
        ("doesntmatter", '{"n": 1, "e":'),  # invalid json string
        (  # dict for wrong topic
            "avr/fcm/position/local",
            {"servo": 2},
        ),
        (  # nothing for wrong topic
            "avr/fcm/position/local",
            None,
        ),
        (  # nothing for wrong topic
            "avr/fcm/position/local",
            {},
        ),
    ],
)
def test_serialize_payload_exception(topic: str, payload: Any) -> None:
    with pytest.raises(ValueError):
        serialize_payload(topic, payload)


@pytest.mark.parametrize(
    "topic, payload, expected",
    [
        (  # json string for a known topic
            "avr/pcm/servo/open",
            b'{"servo": 2}',
            AVRPCMServo(servo=2),
        ),
        (  # empty json string for a known topic
            "avr/pcm/laser/fire",
            b"{}",
            AVREmptyMessage(),
        ),
        (  # empty string for a known topic
            "avr/pcm/laser/fire",
            b"",
            AVREmptyMessage(),
        ),
        (  # no payload for a known topic
            "avr/pcm/laser/fire",
            None,
            AVREmptyMessage(),
        ),
        (  # json string for an unknown topic
            "notreal",
            b'{"servo": 2}',
            {"servo": 2},
        ),
        (  # empty json string for an unknown topic
            "notreal",
            b"{}",
            AVREmptyMessage(),
        ),
        (  # empty string for an unknown topic
            "notreal",
            b"",
            AVREmptyMessage(),
        ),
        (  # no payload for an unknown topic
            "notreal",
            None,
            AVREmptyMessage(),
        ),
    ],
)
def test_deserialize_payload(topic: str, payload: Any, expected: str) -> None:
    assert deserialize_payload(topic, payload) == expected


@pytest.mark.parametrize(
    "topic, payload",
    [
        (  # too many fields for a known topic
            "avr/pcm/laser/fire",
            b'{"servo": 2}',
        ),
        (  # too few fields for a known topic
            "avr/pcm/servo/open",
            b"{}",
        ),
        (  # invalid json
            "notreal",
            b"abc",
        ),
    ],
)
def test_deserialize_payload_exception(topic: str, payload: Any) -> None:
    with pytest.raises(ValueError):
        deserialize_payload(topic, payload)
