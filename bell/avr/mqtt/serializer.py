"""
Using these functions ensure consistent serialization and deserialization of
MQTT payloads.
"""

import json
from typing import Any

import pydantic

from bell.avr.mqtt.constants import MQTTTopicPayload
from bell.avr.mqtt.payloads import AVREmptyMessage


def deserialize_payload(topic: str, payload: bytes) -> Any:
    """
    Deserializes an MQTT payload bytes into a pydantic model. If the topic is
    not known, deserialized JSON will be returned.

    A `ValueError` will be raised if the payload is not valid JSON.

    Additionally, a `ValueError` will be raised if the given topic is known
    and the payload does not match the required schema.
    """

    # so json.loads doesn't choke on an empty string
    if payload in {None, "", b""}:
        payload = b"{}"

    # we talk JSON, no exceptions
    payload = json.loads(payload)

    # load the json into a pydantic model
    if topic in MQTTTopicPayload:
        return MQTTTopicPayload[topic](**payload)

    # if we have an empty dict, manually convert it
    elif payload == {}:
        return AVREmptyMessage()

    # whatever the user gave us
    return payload


def serialize_payload(topic: str, payload: Any) -> str:
    """
    Serializes a payload into a string we can send over MQTT. If the topic is
    not known, serialized JSON will be returned.

    A `ValueError` will be raised if the payload is a string or bytes
    and is not valid JSON.

    Additionally, a `ValueError` will be raised if the given topic is known
    and the payload does not match the required schema.
    """

    # if no payload given, use empty message
    if payload in [None, "", b"", {}]:
        payload = AVREmptyMessage()

    # first, convert to a dict if appropriate
    if isinstance(payload, (str, bytes)):
        payload = json.loads(payload)

    # if this is a known topic
    if topic in MQTTTopicPayload:
        klass = MQTTTopicPayload[topic]

        # if payload is already a pydantic model, check to make sure it's the right
        # one
        if isinstance(payload, pydantic.BaseModel) and not isinstance(payload, klass):
            raise ValueError(f"{topic} payload must be of type {klass}")

        # if not, convert to a pydantic model
        if not isinstance(payload, pydantic.BaseModel):
            payload = MQTTTopicPayload[topic](**payload)

    # convert pydantic models to json
    if isinstance(payload, pydantic.BaseModel):
        return payload.model_dump_json()

    # convert any other data type to json
    return json.dumps(payload)
