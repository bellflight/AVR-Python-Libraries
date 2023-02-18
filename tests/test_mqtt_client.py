from bell.avr.mqtt.client import MQTTModule
from bell.avr.mqtt.payloads import AVRPCMServo
import json
from tests.models import MQTTModuleTest


def test_send_message_pydantic_class(mqtt_module: MQTTModule) -> None:
    """
    Make sure Pydantic classes on a known topic are serialized correctly.
    """
    mqtt_module.send_message("avr/pcm/servo/open", AVRPCMServo(servo=2))
    mqtt_module._mqtt_client.publish.assert_called_once_with(
        "avr/pcm/servo/open", json.dumps({"servo": 2})
    )


def test_send_message_pydantic_class_unknown_topic(mqtt_module: MQTTModule) -> None:
    """
    Make sure Pydantic classes are serialized correctly,
    even for a topic that doesn't exist.
    """
    mqtt_module.send_message("notreal", AVRPCMServo(servo=2))  # type: ignore
    mqtt_module._mqtt_client.publish.assert_called_once_with(
        "notreal", json.dumps({"servo": 2})
    )


def test_send_message_dict(mqtt_module: MQTTModule) -> None:
    """
    Make sure dicts on a kwown topic are serialized correctly.
    """
    mqtt_module.send_message("avr/pcm/servo/open", {"servo": 2})
    mqtt_module._mqtt_client.publish.assert_called_once_with(
        "avr/pcm/servo/open", json.dumps({"servo": 2})
    )


def test_send_message_dict_unknown_topic(mqtt_module: MQTTModule) -> None:
    """
    Make sure dicts are serialized correctly,
    even for a topic that doesn't exist.
    """
    mqtt_module.send_message("notreal", {"servo": 2})  # type: ignore
    mqtt_module._mqtt_client.publish.assert_called_once_with(
        "notreal", json.dumps({"servo": 2})
    )


def test_send_message_none(mqtt_module: MQTTModule) -> None:
    """
    Make sure no payload is allowed
    """
    mqtt_module.send_message("avr/pcm/laser/fire")
    mqtt_module._mqtt_client.publish.assert_called_once_with(
        "avr/pcm/laser/fire", json.dumps({})
    )


def test_send_message_non_schema(mqtt_module: MQTTModule) -> None:
    """
    Make sure message that is not in the schema is allowed
    """
    mqtt_module.send_message("test/notreal", False)  # type: ignore
    mqtt_module._mqtt_client.publish.assert_called_once_with(
        "test/notreal", json.dumps(False)
    )


def test_receive_message_pydantic_class(mqtt_module: MQTTModuleTest) -> None:
    """
    Make sure Pydantic classes are deserialized correctly on a known topic.
    """
    # setup message handler
    mqtt_module.topic_map = {"avr/pcm/servo/open": mqtt_module.test_handler}
    mqtt_module.run_non_blocking()

    # use test harness to send message
    mqtt_module.recieve_message("avr/pcm/servo/open", json.dumps({"servo": 2}))

    # make sure handler recieved deserialized message
    mqtt_module.test_handler.assert_called_once_with(AVRPCMServo(servo=2))


def test_receive_message_none(mqtt_module: MQTTModuleTest) -> None:
    """
    Make sure topics with an empty message work.
    """
    # setup message handler
    mqtt_module.topic_map = {"avr/pcm/laser/fire": mqtt_module.test_handler_empty}
    mqtt_module.run_non_blocking()

    # use test harness to send message
    mqtt_module.recieve_message("avr/pcm/laser/fire", json.dumps({}))

    # make sure handler was called with no arguments
    mqtt_module.test_handler_empty.assert_called_once_with()


def test_receive_message_non_schema(mqtt_module: MQTTModuleTest) -> None:
    """
    Make sure message that is not in the schema is allowed
    """
    # setup message handler
    mqtt_module.topic_map = {"test/notreal": mqtt_module.test_handler}  # type: ignore
    mqtt_module.run_non_blocking()

    # use test harness to send message
    mqtt_module.recieve_message("test/notreal", json.dumps({"servo": 2}))

    # make sure handler recieved deserialized message
    mqtt_module.test_handler.assert_called_once_with({"servo": 2})


def test_receive_message_none_non_schema(mqtt_module: MQTTModuleTest) -> None:
    """
    Make sure empty message that is not in the schema is allowed
    """
    # setup message handler
    mqtt_module.topic_map = {"test/notreal": mqtt_module.test_handler_empty}  # type: ignore
    mqtt_module.run_non_blocking()

    # use test harness to send message
    mqtt_module.recieve_message("test/notreal", "")

    # make sure handler was called with no arguments
    mqtt_module.test_handler_empty.assert_called_once_with()
