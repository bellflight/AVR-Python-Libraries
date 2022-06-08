# VRC-Python-Libraries

## Install

To install the base package, run:

```bash
pip install bell-vrc-libraries
```

Additionally, the `mqtt` and `serial` extras are available if you want to use
the MQTT or PCC functionality.

```bash
pip install bell-vrc-libraries[mqtt,serial]
```

## Usage

### MQTT

```python
from bell.vrc import mqtt
```

These are MQTT utilities that are used to have a consistent messaging protocol
throughout all the VRC software modules.

The first part of this are the payloads for the MQTT messages themselves. As VRC
exclusively uses JSON, these are all
[`TypedDict`](https://docs.python.org/3/library/typing.html#typing.TypedDict)s
that have all of the required fields for a message.

Example:

```python
from bell.vrc.mqtt.payloads import VrcPcmSetBaseColorPayload

payload = VrcPcmSetBaseColorPayload((128, 232, 142, 0))
```

The second part of the MQTT libraries, is the `MQTTModule` class.
This is a boilerplate module for VRC that makes it very easy to send
and recieve MQTT messages and do something with them.

Example:

```python
from bell.vrc.mqtt.client import MQTTModule
from bell.vrc.mqtt.payloads import VrcFcmVelocityPayload, VrcPcmSetServoOpenClosePayload


class Sandbox(MQTTModule):
    def __init__(self) -> None:
        self.topic_map = {"vrc/fcm/velocity": self.show_velocity}

    def show_velocity(self, payload: VrcFcmVelocityPayload) -> None:
        vx = payload["vX"]
        vy = payload["vY"]
        vz = payload["vZ"]
        v_ms = (vx, vy, vz)
        print(f"Velocity information: {v_ms} m/s")

    def open_servo(self) -> None:
        payload = VrcPcmSetServoOpenClosePayload(servo=0, action="open")
        self.send_message("vrc/pcm/set_servo_open_close", payload)


if __name__ == "__main__":
    box = Sandbox()
    box.run()
```

The `topic_map` dictionary is a class attribute that maps topics to subscribe to
and a function that will handle an incoming payload. The `payload` argument
should match the appropriate `Payload` class for that topic.

Additionally, the `message_cache` attribute is a dictionary that holds
a copy of the last payload sent by that module on a given topic. The keys are the
topic strings, and the values are the topic payloads.

### Utils

```python
from bell.vrc import utils
```

These are general purpose utilities.

#### Decorators

```python
from bell.vrc.utils import decorators
```

There are 3 different function decorators available, which are helpful for MQTT
message callbacks. First is the `try_except` decorator, which wraps the
function in a `try: except:` statement and will log any exceptions to the console:

```python
    @decorators.try_except
    def assemble_hil_gps_message(self) -> None:
        ...
```

Additionally, there is the `reraise` argument, which can be set to `True` to raise
any exceptions that are encountered. This is helpful if you still want exceptions
to propagate up, but log them.

There is an async version of this decorator as well with an `async_` prefix.

```python
    @decorators.async_try_except()
    async def connected_status_telemetry(self) -> None:
        ...
```

The last decorator is `run_forever` which will run the wrapped function forever,
with a given `period` or `frequency`.

```python
    @decorators.run_forever(frequency=5)
    def read_data(self) -> None:
        ...
```

#### Timing

```python
from bell.vrc.utils import timing
```

Here is a `rate_limit` function which take a callable and a
period or frequency, and only run the callable at that given rate.

```python
for _ in range(10):
    # add() will only run twice
    timing.rate_limit(add, period=5)
    time.sleep(1)
```

This works tracking calls to the `rate_limit` function from a line number
within a file, so multiple calls to `rate_limit` say within a loop
with the same callable and period will be treated seperately. This allows
for dynamic frequency manipulation.

### Serial

```python
from bell.vrc import serial
```

These are serial utilities that help facilitate finding and communicating
with the VRC peripherial control computer.

#### Client

```python
from bell.vrc.serial import client
```

The `SerialLoop` class is a small wrapper around the `pyserial` `serial.Serial`
class which adds a `run` method that will try to read data from the serial device
as fast as possible.

```python
ser = client.SerialLoop()
```

#### PCC

```python
from bell.vrc.serial import client
```

The `PeripheralControlComputer` class sends serial messages
to the VRC peripherial control computer, via easy-to-use class methods.

```python
import bell.vrc.serial
import threading

client = bell.vrc.serial.client.SerialLoop()
client.port = port
client.baudrate = baudrate

pcc = bell.vrc.serial.pcc.PeripheralControlComputer(client)

client_thread = threading.Thread(target=client.run)
client_thread.start()

pcc.set_servo_max(0, 100)
```

#### Ports

```python
from bell.vrc.serial import ports
```

Here is a `list_serial_ports` function which returns a list of detected serial
ports connected to the system.

```python
serial_ports = ports.list_serial_ports()
# ["COM1", "COM5", ...]
```

## Development

Install [`poetry`](https://python-poetry.org/) and run
`poetry install --extras mqtt --extras serial` to install of the dependencies
inside a virtual environment.

Build the auto-generated code with `poetry run python build.py`. From here,
you can now produce a package with `poetry build`.

To add new message definitions, add entries to the `bell/vrc/mqtt/messages.jsonc` file.
The 3 parts of a new message are as follows:

1. "topic": This is the full topic path for the message. This must be all lower case and
   start with "vrc/".
2. "payload": These are the keys of the payload for the message.
   This is a list of key entries (see below).
3. "docs": This is an optional list of Markdown strings that explains what this
   message does. Each list item is a new line.

The key entries for a message have the following elements:

1. "key": This is the name of the key. Must be a valid Python variable name.
2. "type": This is the data type of the key such as `Tuple[int, int, int, int]`.
   Must be a valid Python type hint. Otherwise, this can be a list of more
   key entries, effectively creating a nested dictionary.
3. "docs": This is an optional list of Markdown strings that explains what the
   key is. Each list item is a new line.

The `bell/vrc/mqtt/schema.json` file will help ensure the correct schema is maintained,
assuming you are using VS Code.
