import ctypes
from struct import pack
from typing import Any, List, Literal, Optional, Tuple, Union

import serial
from loguru import logger


class PeripheralControlComputer:
    """
    The `PeripheralControlComputer` class sends serial messages
    to the AVR peripheral control computer, via easy-to-use class methods.

    The class must be initialized with a
    [`pyserial`](https://pypi.org/project/pyserial/)
    [`serial.Serial`](https://pythonhosted.org/pyserial/pyserial_api.html#serial.Serial)
    or `bell.avr.serial.client.SerialLoop` class instance.

    Example:

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
    """

    def __init__(self, ser: serial.Serial) -> None:
        self.ser = ser

        self.PREAMBLE = (0x24, 0x50)

        self.HEADER_OUTGOING = (*self.PREAMBLE, 0x3C)
        self.HEADER_INCOMING = (*self.PREAMBLE, 0x3E)

        self.commands = [
            "SET_SERVO_OPEN_CLOSE",
            "SET_SERVO_MIN",
            "SET_SERVO_MAX",
            "SET_SERVO_PCT",
            "SET_SERVO_ABS",
            "SET_BASE_COLOR",
            "SET_TEMP_COLOR",
            "FIRE_LASER",
            "SET_LASER_ON",
            "SET_LASER_OFF",
            "RESET_AVR_PERIPH",
            "CHECK_SERVO_CONTROLLER",
        ]

        self.shutdown: bool = False

    def set_base_color(self, wrgb: Tuple[int, int, int, int]) -> None:
        """
        Set the color of the LED strip. Expects a tuple of 4 integers between
        0 and 255, inclusive. This is in the White, Red, Green, Blue format.
        """
        command = self.commands.index("SET_BASE_COLOR")
        wrgb_l = list(wrgb)

        # wrgb + code = 5
        if len(wrgb_l) != 4:
            wrgb_l = [0, 0, 0, 0]

        for i, color in enumerate(wrgb_l):
            if not isinstance(color, int) or color > 255 or color < 0:
                wrgb_l[i] = 0

        data = self._construct_payload(command, 1 + len(wrgb_l), wrgb_l)

        logger.debug(f"Setting base color: {data}")
        self.ser.write(data)

    def set_temp_color(
        self, wrgb: Tuple[int, int, int, int], duration: float = 0.5
    ) -> None:
        """
        Set the color of the LED strip for a specific duration.
        Expects a tuple of 4 integers between
        0 and 255, inclusive. This is in the White, Red, Green, Blue format.

        Duration defaults to 0.5 seconds if not given.
        """

        command = self.commands.index("SET_TEMP_COLOR")
        wrgb_l = list(wrgb)

        # wrgb + code = 5
        if len(wrgb_l) != 4:
            wrgb_l = [0, 0, 0, 0]

        for i, color in enumerate(wrgb_l):
            if not isinstance(color, int) or color > 255 or color < 0:
                wrgb_l[i] = 0

        time_bytes = self._list_pack("<f", duration)
        data = self._construct_payload(
            command, 1 + len(wrgb) + len(wrgb_l), wrgb_l + time_bytes
        )

        logger.debug(f"Setting temp color: {data}")
        self.ser.write(data)

    def set_servo_open_close(
        self, servo: int, action: Literal["open", "close"]
    ) -> None:
        """
        Opens or closes a servo. Expects the 0-indexed servo ID and the
        action to perform.
        """

        valid_command = False

        command = self.commands.index("SET_SERVO_OPEN_CLOSE")
        data = []

        # 128 is inflection point, over 128 == open; under 128 == close

        if action == "close":
            data = [servo, 100]
            valid_command = True

        elif action == "open":
            data = [servo, 150]
            valid_command = True

        if not valid_command:
            return

        length = 3
        data = self._construct_payload(command, length, data)

        logger.debug(f"Setting servo open/close: {data}")
        self.ser.write(data)

    def set_servo_min(self, servo: int, minimum: float) -> None:
        """
        Sets the minimum pulse width of a servo. Expects the 0-indexed servo ID and
        the minimum pulse width between 0 and 1000 non-inclusive.
        """

        valid_command = False

        command = self.commands.index("SET_SERVO_MIN")
        data = []

        if isinstance(minimum, (float, int)) and minimum < 1000 and minimum > 0:
            valid_command = True
            data = [servo, minimum]

        if not valid_command:
            return

        length = 3
        data = self._construct_payload(command, length, data)

        logger.debug(f"Setting servo min: {data}")
        self.ser.write(data)

    def set_servo_max(self, servo: int, maximum: float) -> None:
        """
        Sets the maximum pulse width of a servo. Expects the 0-indexed servo ID and
        the maximum pulse width between 0 and 1000 non-inclusive.
        """

        valid_command = False

        command = self.commands.index("SET_SERVO_MAX")
        data = []

        if isinstance(maximum, (float, int)) and maximum < 1000 and maximum > 0:
            valid_command = True
            data = [servo, maximum]

        if not valid_command:
            return

        length = 3
        data = self._construct_payload(command, length, data)

        logger.debug(f"Setting servo max: {data}")
        self.ser.write(data)

    def set_servo_pct(self, servo: int, pct: int) -> None:
        """
        Sets the percentage open of a servo. Expects the 0-indexed servo ID and
        the percentage open between 0 and 100 inclusive.
        """

        valid_command = False

        command = self.commands.index("SET_SERVO_PCT")
        data = []

        if isinstance(pct, (float, int)) and pct <= 100 and pct >= 0:
            valid_command = True
            data = [servo, int(pct)]

        if not valid_command:
            return

        length = 3
        data = self._construct_payload(command, length, data)

        logger.debug(f"Setting servo percent: {data}")
        self.ser.write(data)

    def set_servo_abs(self, servo: int, absolute: int) -> None:
        """
        Sets the absolute position of a servo. Expects the 0-indexed servo ID and
        the absolute position.
        """

        valid_command = False

        command = self.commands.index("SET_SERVO_ABS")
        data = []

        if isinstance(absolute, int):
            uint16_absolute = ctypes.c_uint16(absolute).value
            uint8_absolute_high = (uint16_absolute >> 8) & 0xFF
            uint8_absolute_low = uint16_absolute & 0xFF
            valid_command = True
            data = [servo, int(uint8_absolute_high), int(uint8_absolute_low)]

        if not valid_command:
            return

        length = 4
        data = self._construct_payload(command, length, data)

        logger.debug(f"Setting servo absolute: {data}")
        self.ser.write(data)

    def fire_laser(self) -> None:
        """
        Fires the laser for a 0.25 second pulse. Has a cooldown of 0.5 seconds.
        """

        command = self.commands.index("FIRE_LASER")

        length = 1
        data = self._construct_payload(command, length)

        logger.debug(f"Setting the laser on: {data}")
        self.ser.write(data)

    def set_laser_on(self) -> None:
        """
        Turns laser on for 0.1 second every 0.5 seconds.
        """

        command = self.commands.index("SET_LASER_ON")

        length = 1
        data = self._construct_payload(command, length)

        logger.debug(f"Setting the laser on: {data}")
        self.ser.write(data)

    def set_laser_off(self) -> None:
        """
        Turns the laser off. Does not prevent `fire_laser`.
        """
        command = self.commands.index("SET_LASER_OFF")

        length = 1
        data = self._construct_payload(command, length)

        logger.debug(f"Setting the laser off: {data}")
        self.ser.write(data)

    # def reset_avr_peripheral(self) -> None:
    #     command = self.commands.index("RESET_AVR_PERIPH")

    #     length = 1  # just the reset command
    #     data = self._construct_payload(command, length)

    #     logger.debug(f"Resetting the PCC: {data}")
    #     self.ser.write(data)

    #     self.ser.close()
    #     time.sleep(5)
    #     self.ser.open()

    def check_servo_controller(self) -> None:
        """
        Checks the servo controller.
        """
        command = self.commands.index("CHECK_SERVO_CONTROLLER")

        length = 1
        data = self._construct_payload(command, length)

        logger.debug(f"Checking servo controller: {data}")
        self.ser.write(data)

    def _construct_payload(
        self, code: int, size: int = 0, data: Optional[list] = None
    ) -> bytes:
        # [$][P][>][LENGTH-HI][LENGTH-LOW][DATA][CRC]
        payload = bytes()

        if data is None:
            data = []

        new_data = (
            ("<3b", self.HEADER_OUTGOING),
            (">H", [size]),
            ("<B", [code]),
            ("<%dB" % len(data), data),
        )

        for section in new_data:
            payload += pack(section[0], *section[1])

        crc = self._calc_crc(payload, len(payload))

        payload += pack("<B", crc)

        return payload

    def _list_pack(self, bit_format: Union[str, bytes], value: Any) -> List[int]:
        return list(pack(bit_format, value))

    def _crc8_dvb_s2(self, crc: int, a: int) -> int:
        # https://stackoverflow.com/a/52997726
        crc ^= a
        for _ in range(8):
            crc = ((crc << 1) ^ 0xD5) % 256 if crc & 0x80 else (crc << 1) % 256
        return crc

    def _calc_crc(self, string: bytes, length: int) -> int:
        """
        Calculates the crc for an input.
        """

        crc = 0
        for i in range(length):
            crc = self._crc8_dvb_s2(crc, string[i])
        return crc
