from tests.models import MQTTModuleTest


def test_subscriptions_topic_callbacks(mqtt_module: MQTTModuleTest) -> None:
    """
    Ensure topic_callbacks keys are subscribed to.
    """
    mqtt_module.topic_callbacks = {
        "avr/pcm/servo/open": mqtt_module.test_handler,
    }
    mqtt_module.on_connect(mqtt_module._mqtt_client, None, None, None)  # type: ignore

    mqtt_module._mqtt_client.subscribe.assert_called_once_with("avr/pcm/servo/open")


def test_subscriptions_all_avr(mqtt_module: MQTTModuleTest) -> None:
    """
    Ensure all avr topics can be subscribed to
    """
    mqtt_module.subscribe_to_all_avr_topics = True
    mqtt_module.on_connect(mqtt_module._mqtt_client, None, None, None)  # type: ignore

    mqtt_module._mqtt_client.subscribe.assert_called_once_with("avr/#")


def test_subscriptions_all(mqtt_module: MQTTModuleTest) -> None:
    """
    Ensure all topics can be subscribed to
    """
    mqtt_module.subscribe_to_all_topics = True
    mqtt_module.on_connect(mqtt_module._mqtt_client, None, None, None)  # type: ignore

    mqtt_module._mqtt_client.subscribe.assert_called_once_with("#")
