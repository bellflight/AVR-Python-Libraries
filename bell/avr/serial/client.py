import serial
from bell.avr.utils.decorators import run_forever


class SerialLoop(serial.Serial):
    """
    Like the normal pyserial class, but with a method to run forever.
    """

    @run_forever(period=0.01)
    def run(self) -> None:
        while self.in_waiting > 0:
            self.read(1)
