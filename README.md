# AVR-Python-Libraries

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Install

To install the base package, run:

```bash
pip install bell-avr-libraries
```

Additionally, the `serial` and `qt` extras are available if you want to use
the PCC or PySide functionality.

```bash
pip install bell-avr-libraries[serial,qt]
```

## Usage

### MQTT

```python
from bell.avr import mqtt
```

These are MQTT utilities that are used to have a consistent messaging protocol
throughout all the AVR software modules.

The first part of this are the payloads for the MQTT messages themselves. As AVR
exclusively uses JSON, these are all [Pydantic](https://docs.pydantic.dev/) classes
that have all of the required fields for a message.

Example:

```python
from bell.avr.mqtt.payloads import AVRPCMColorSet

payload = AVRPCMColorSet(wrgb=(128, 232, 142, 0))
```

The second part of the MQTT libraries is the `MQTTModule` class.
This is a boilerplate module for AVR that makes it very easy to send
and receive MQTT messages and do something with them.

Example:

```python
from bell.avr.mqtt.module import MQTTModule
from bell.avr.mqtt.payloads import AVRFCMVelocity, AVRPCMServo


class Sandbox(MQTTModule):
    def __init__(self) -> None:
        super().__init__()
        self.topic_callbacks = {"avr/fcm/velocity": self.show_velocity}

    def show_velocity(self, payload: AVRFCMVelocity) -> None:
        v_ms = (payload.vN, payload.vE, payload.vd)
        print(f"Velocity information: {v_ms} m/s")

    def open_servo(self) -> None:
        payload = AVRPCMServo(servo=0)
        self.send_message("avr/pcm/servo/open", payload)


if __name__ == "__main__":
    box = Sandbox()
    box.run()
```

The `topic_callbacks` dictionary is a class attribute that maps topics to
subscribe to and a function that will handle an incoming payload.
The `payload` argument should match the appropriate class for that
topic. This can be determined from the documentation at
[https://bellflight.github.io/AVR-Python-Libraries](https://bellflight.github.io/AVR-Python-Libraries)

Additionally, the `message_cache` attribute is a dictionary that holds
a copy of the last payload sent by that module on a given topic. The keys are the
topic strings, and the values are the topic payloads.

### Utils

```python
from bell.avr import utils
```

These are general purpose utilities.

#### Decorators

```python
from bell.avr.utils import decorators
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
from bell.avr.utils import timing
```

Here is a `rate_limit` function which takes a callable and a
period or frequency, and only runs the callable at that given rate.

```python
for _ in range(10):
    # add() will only run twice
    timing.rate_limit(add, period=5)
    time.sleep(1)
```

This works by tracking calls to the `rate_limit` function from a line number
within a file, so multiple calls to `rate_limit` say within a loop
with the same callable and period will be treated separately. This allows
for dynamic frequency manipulation.

#### Env

```python
from bell.avr.utils import env
```

The function `get_env_int` is like the `os.getenv` function, except it is only meant
for environment variables which contain an integer.

```python
env.get_env_int("MQTT_HOST", 1883)
# returns the value of MQTT_HOST as an integer
# or 1883 if the environment variable is not set
# or not an integer.
```

### Serial

```python
from bell.avr import serial
```

These are serial utilities that help facilitate finding and communicating
with the AVR peripheral control computer.

#### Client

```python
from bell.avr.serial import client
```

The `SerialLoop` class is a small wrapper around the `pyserial` `serial.Serial`
class which adds a `run` method that will try to read data from the serial device
as fast as possible.

```python
ser = client.SerialLoop()
```

#### PCC

```python
from bell.avr.serial import pcc
```

The `PeripheralControlComputer` class sends serial messages
to the AVR peripheral control computer, via easy-to-use class methods.

```python
import bell.avr.serial.client
import bell.avr.serial.pcc
import threading

client = bell.avr.serial.client.SerialLoop()
client.port = port
client.baudrate = baudrate
client.open()

pcc = bell.avr.serial.pcc.PeripheralControlComputer(client)

client_thread = threading.Thread(target=client.run)
client_thread.start()

pcc.set_servo_max(0, 100)
```

#### Ports

```python
from bell.avr.serial import ports
```

Here is a `list_serial_ports` function which returns a list of detected serial
ports connected to the system.

```python
serial_ports = ports.list_serial_ports()
# ["COM1", "COM5", ...]
```

## Development

It's assumed you have a version of Python installed from
[python.org](https://python.org) that is the same or newer as
defined in the [`.python-version`](.python-version) file.

First, install [Poetry](https://python-poetry.org/):

```bash
python -m pip install pipx --upgrade
pipx ensurepath
pipx install poetry
# (Optionally) Add pre-commit plugin
poetry self add poetry-pre-commit-plugin
```

Now, you can clone the repo and install dependencies:

```bash
git clone https://github.com/bellflight/AVR-Python-Libraries
cd AVR-Python-Libraries
poetry install --sync --all-extras
poetry run pre-commit install --install-hooks
```

Run

```bash
poetry shell
```

to activate the virtual environment.

Build the auto-generated code with `poetry run python build.py`. From here,
you can now produce a package with `poetry build`.

To add new message definitions, add entries to the `bell/avr/mqtt/asyncapi.yml` file.
This is an [AsyncAPI](https://www.asyncapi.com/) definition,
which is primarily [JSONSchema](https://json-schema.org/) with some association
of classes and topics.

The generator that turns this definition file into Python code is the homebrew
[build.py](build.py), so double-check that the output makes sense.

To generate the documentation, run the `build.py` script with the `--docs` option.
This requies that Node.js is installed, and `npm` install hs been run.
