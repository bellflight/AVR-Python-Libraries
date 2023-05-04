from __future__ import annotations

import os
import uuid
from typing import Any, Union

import paho.mqtt.client as paho_mqtt
from loguru import logger

from bell.avr.mqtt.constants import _MQTTTopicCallableTypedDict
from bell.avr.utils.env import get_env_int


class MQTTClient:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create the MQTT client
        # Currently using MQTT v3.1.1
        # No reason we can't use v5, just type hinting needs to change
        # for some `on_` functions.
        self._mqtt_client = paho_mqtt.Client(
            client_id=f"{self.__class__.__name__}_{uuid.uuid4()}",
            protocol=paho_mqtt.MQTTv311,
        )

        # set up the on connect and on message handlers
        self._mqtt_client.on_connect = self.on_connect

        # dictionary of MQTT topics to callback functions
        # this is intended to be overwritten by the child class
        self.topic_callbacks: _MQTTTopicCallableTypedDict = {}

        # flag to subscribe to all topics on connection
        self.subscribe_to_all_topics: bool = False
        # flag to subscribe to all `avr/` topics on connection
        self.subscribe_to_all_avr_topics: bool = False

        # enable verbose logging
        self.enable_verbose_logging: bool = False

        # record if we were started with loop forever
        self._looped_forever = False

    def on_connect(
        self, client: paho_mqtt.Client, userdata: Any, flags: dict, rc: int
    ) -> None:
        """
        On connection callback. Subscribes to MQTT topics in the topic map,
        plus any additional `self.subscribe_to` flags.
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

    def connect_(self, host: str, port: int) -> None:
        """
        Connect the MQTT client to the broker. This method cannot be named "connect"
        as this conflicts with the connect methods of Qt Signals.
        """
        if self.enable_verbose_logging:
            logger.info(f"Connecting to MQTT broker at {host}:{port}")

        self._mqtt_client.connect(host=host, port=port, keepalive=60)

        logger.success("Connected to MQTT broker")

        # if an on_message callback has been defined, connect it
        if hasattr(self, "on_message"):
            self._mqtt_client.on_message = self.on_message  # type: ignore

    def stop(self) -> None:
        """
        Stops the MQTT loop and disconnects from the broker.
        """
        if self.enable_verbose_logging:
            logger.info("Disconnecting from MQTT server")

        self._mqtt_client.disconnect()
        self._mqtt_client.loop_stop()

        if self.enable_verbose_logging:
            logger.info("Disconnected from MQTT server")

    def run(
        self,
        host: str = os.getenv("MQTT_HOST", "mqtt"),
        port: int = get_env_int("MQTT_PORT", 18830),
    ) -> None:
        """
        Class entrypoint. Connects to the MQTT broker and starts the MQTT loop
        in a blocking manner.
        """
        # connect the MQTT client
        self.connect_(host, port)
        # run forever
        self._looped_forever = True
        self._mqtt_client.loop_forever()

    def run_non_blocking(
        self,
        host: str = os.getenv("MQTT_HOST", "mqtt"),
        port: int = get_env_int("MQTT_PORT", 18830),
    ) -> None:
        """
        Class entrypoint. Connects to the MQTT broker and starts the MQTT loop
        in a non-blocking manner.
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
