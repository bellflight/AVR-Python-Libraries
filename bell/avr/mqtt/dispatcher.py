from typing import Any

from bell.avr.mqtt.constants import _MQTTTopicCallableTypedDict
from bell.avr.mqtt.payloads import AVREmptyMessage


def dispatch_message(
    topic_callbacks: _MQTTTopicCallableTypedDict, topic: str, payload: Any
) -> None:
    """
    Given a dictionary of topics and callbacks,
    this executes the appropriate callback with the correct arguments.
    """
    if topic not in topic_callbacks:
        return

    # execute callback
    if isinstance(payload, AVREmptyMessage):
        topic_callbacks[topic]()
    else:
        topic_callbacks[topic](payload)
