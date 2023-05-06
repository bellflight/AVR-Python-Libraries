import serial

from bell.avr.utils.decorators import run_forever


class SerialLoop(serial.Serial):
    """
    The `SerialLoop` class is a small wrapper around the
    [`pyserial`](https://pypi.org/project/pyserial/)
    [`serial.Serial`](https://pythonhosted.org/pyserial/pyserial_api.html#serial.Serial)
    class which adds a `run` method that will try to read data from the serial device
    as fast as possible.

    See the `bell.avr.serial.pcc.PeripheralControlComputer` class for more usage.
    """

    @run_forever(period=0.01)
    def run(self) -> None:
        """
        This method attempts to read data from the serial connection forever
        at 100Hz.
        """
        while self.in_waiting > 0:
            self.read(1)
