from __future__ import annotations

import os
import uuid
from typing import Any, Optional, Union

import paho.mqtt.client as paho_mqtt
from loguru import logger

from bell.avr.mqtt.constants import _MQTTTopicCallableTypedDict
from bell.avr.utils.env import get_env_int


class MQTTClient:
    def __init__(self):
        """
        This class is *not meant to be used directly*! This meant to serve as the
        foundation for MQTT interactions. Please use the
        `bell.avr.mqtt.module.MQTTModule`
        or `bell.avr.mqtt.qt_widget.MQTTWidget` classes instead.
        """

        # create the MQTT client
        # Currently using MQTT v3.1.1
        # No reason we can't use v5, just type hinting needs to change
        # for some `on_` functions.
        self._mqtt_client = paho_mqtt.Client(
            client_id=f"{self.__class__.__name__}_{uuid.uuid4()}",
            protocol=paho_mqtt.MQTTv311,
        )

        # set up the on connect handler
        self._mqtt_client.on_connect = self.on_connect

        # dictionary of MQTT topics to callback functions
        # this is intended to be overwritten by the child class
        self.topic_callbacks: _MQTTTopicCallableTypedDict = {}
        """
        This dictionary is where you can put a mapping of topics and functions
        to run when a message is recieved on that topic. The function must expect
        the payload for that topic as it's only argument. If the payload is
        `bell.avr.mqtt.payloads.AVREmptyMessage`, then the function does
        not need to expect any arguments.

        This MUST be set after `super().__init__()`

        Example:

        ```python
        from bell.avr.mqtt.client import MQTTClient
        from bell.avr.mqtt.payloads import AVRFCMBattery

        class MyClient(MQTTClient):
            def __init__(self):
                super().__init__()

                self.topic_callbacks = {
                    "avr/fcm/battery": self.handle_battery,
                    "avr/pcm/laser/fire": self.handle_laser
                }

            def handle_battery(self, payload: AVRFCMBattery) -> None:
                ...

            def handle_laser(self) -> None:
                ...
        ```
        """

        self.subscribe_to_all_topics: bool = False
        """
        Set this to `True` to subscribe to ALL MQTT topics.

        Example:

        ```python
        from bell.avr.mqtt.client import MQTTClient

        class MyClient(MQTTClient):
            def __init__(self):
                super().__init__()

                self.subscribe_to_all_topics = True
        ```
        """

        self.subscribe_to_all_avr_topics: bool = False
        """
        Set this to `True` to subscribe to all MQTT topics starting with `avr/`.

        Example:

        ```python
        from bell.avr.mqtt.client import MQTTClient

        class MyClient(MQTTClient):
            def __init__(self):
                super().__init__()

                self.subscribe_to_all_avr_topics = True
        ```
        """

        self.enable_verbose_logging: bool = False
        """
        Set this to `True` to enable verbose logging.

        Example:

        ```python
        from bell.avr.mqtt.client import MQTTClient

        class MyClient(MQTTClient):
            def __init__(self):
                super().__init__()

                self.enable_verbose_logging = True
        ```
        """

        # record if we were started with loop forever
        self._looped_forever = False

    def on_connect(
        self, client: paho_mqtt.Client, userdata: Any, flags: dict, rc: int
    ) -> None:
        """
        On connection callback. Subscribes to MQTT topics in `self.topic_callbacks`,
        plus the `subscribe_to_all_topics` and `subscribe_to_all_avr_topics`
        flags.
        """
        logger.debug(f"Connected with result {rc}")

        for topic in self.topic_callbacks.keys():
            client.subscribe(topic)
            logger.success(f"Subscribed to: {topic}")

        if self.subscribe_to_all_topics:
            client.subscribe("#")
            logger.success("Subscribed to all topics")

        elif self.subscribe_to_all_avr_topics:
            client.subscribe("avr/#")
            logger.success("Subscribed to: avr/#")

    def on_disconnect(
        self,
        client: paho_mqtt.Client,
        userdata: Any,
        rc: int,
    ) -> None:
        """
        Callback when the MQTT client disconnects.
        """
        logger.debug("Disconnected from MQTT server")

    def connect_(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """
        Connect the MQTT client to the broker. This method cannot be named "connect"
        as this conflicts with the connect methods of Qt Signals.

        This will be called automatically by `run` or `run_non_blocking`.
        """
        if host is None:
            host = os.getenv("MQTT_HOST", "mqtt")

        if port is None:
            port = get_env_int("MQTT_PORT", 18830)

        if self.enable_verbose_logging:
            logger.info(f"Connecting to MQTT broker at {host}:{port}")

        self._mqtt_client.connect(host=host, port=port, keepalive=60)

        logger.success("Connected to MQTT broker")

        # if an on_message callback has been defined, connect it
        if hasattr(self, "on_message"):
            self._mqtt_client.on_message = self.on_message  # type: ignore

    def stop(self) -> None:
        """
        Stops the MQTT event loop and disconnects from the broker.
        """
        if self.enable_verbose_logging:
            logger.info("Disconnecting from MQTT server")

        self._mqtt_client.disconnect()
        self._mqtt_client.loop_stop()

        if self.enable_verbose_logging:
            logger.info("Disconnected from MQTT server")

    def run(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """
        Main class entrypoint. Connects to the MQTT broker and starts the MQTT event
        loop in a blocking manner. If not provided, the broker hostname
        will be pulled from the `MQTT_HOST` environment variable, with a default of
        `mqtt`. If not provided, the broker port
        will be pulled from the `MQTT_PORT` environment variable, with a default of
        `18830`.

        Until this is or `run_non_blocking` is called, the MQTT event loop has not been started
        and messages will not be sent or received.
        """
        # connect the MQTT client
        self.connect_(host, port)
        # run forever
        self._looped_forever = True
        self._mqtt_client.loop_forever()

    def run_non_blocking(
        self, host: Optional[str] = None, port: Optional[int] = None
    ) -> None:
        """
        Main class entrypoint. Connects to the MQTT broker and starts the MQTT event
        loop in a non-blocking manner. If not provided, the broker hostname
        will be pulled from the `MQTT_HOST` environment variable, with a default of
        `mqtt`. If not provided, the broker port
        will be pulled from the `MQTT_PORT` environment variable, with a default of
        `18830`.

        Until this is or `run` is called, the MQTT event loop has not been started
        and messages will not be sent or received.
        """
        # connect the MQTT client
        self.connect_(host, port)
        # run in background
        self._mqtt_client.loop_start()

    def _publish(
        self, topic: str, payload: Union[str, bytes], force_write: bool = False
    ) -> None:
        """
        Raw publish function that expects a topic and a payload as a string or bytes.
        """
        if self.enable_verbose_logging:
            logger.debug(f"Publishing message to {topic}: {payload}")

        self._mqtt_client.publish(topic, payload)

        # https://github.com/eclipse/paho.mqtt.python/blob/9782ab81fe7ee3a05e74c7f3e1d03d5611ea4be4/src/paho/mqtt/client.py#L1563
        # pre-emptively write network data while still in a callback, bypassing
        # the thread mutex.
        # can only be used if run with .loop_forever()
        # https://www.bellavrforum.org/t/sending-messages-to-pcc-from-sandbox/311/8
        if self._looped_forever or force_write:
            self._mqtt_client.loop_write()
