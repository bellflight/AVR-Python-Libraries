from bell.avr.serial.pcc import PeripheralControlComputer

# these tests are not great


def test_set_base_color(pcc: PeripheralControlComputer) -> None:
    pcc.set_base_color(wrgb=(1, 2, 3, 4))
    pcc.ser.write.assert_called_once_with(b"$P<\x00\x05\x05\x01\x02\x03\x04\xd9")


def test_set_temp_color(pcc: PeripheralControlComputer) -> None:
    pcc.set_temp_color(wrgb=(1, 2, 3, 4), duration=5)
    pcc.ser.write.assert_called_once_with(
        b"$P<\x00\t\x06\x01\x02\x03\x04\x00\x00\xa0@6"
    )


def test_set_servo_open(pcc: PeripheralControlComputer) -> None:
    pcc.set_servo_open_close(2, "open")
    pcc.ser.write.assert_called_once_with(b"$P<\x00\x03\x00\x02\x96\xe3")


def test_set_servo_close(pcc: PeripheralControlComputer) -> None:
    pcc.set_servo_open_close(2, "close")
    pcc.ser.write.assert_called_once_with(b"$P<\x00\x03\x00\x02d\x18")


def test_set_servo_min(pcc: PeripheralControlComputer) -> None:
    pcc.set_servo_min(2, 50)
    pcc.ser.write.assert_called_once_with(b"$P<\x00\x03\x01\x022\xd5")


def test_set_servo_max(pcc: PeripheralControlComputer) -> None:
    pcc.set_servo_max(2, 50)
    pcc.ser.write.assert_called_once_with(b"$P<\x00\x03\x02\x022\x85")


def test_set_servo_pct(pcc: PeripheralControlComputer) -> None:
    pcc.set_servo_pct(2, 50)
    pcc.ser.write.assert_called_once_with(b"$P<\x00\x03\x03\x022\x06")


def test_set_servo_abs(pcc: PeripheralControlComputer) -> None:
    pcc.set_servo_abs(2, 50)
    pcc.ser.write.assert_called_once_with(b"$P<\x00\x04\x04\x02\x002\xbd")


def test_fire_laser(pcc: PeripheralControlComputer) -> None:
    pcc.fire_laser()
    pcc.ser.write.assert_called_once_with(b"$P<\x00\x01\x07\xcc")


def test_set_laser_on(pcc: PeripheralControlComputer) -> None:
    pcc.set_laser_on()
    pcc.ser.write.assert_called_once_with(b"$P<\x00\x01\x08\xb1")


def test_set_laser_off(pcc: PeripheralControlComputer) -> None:
    pcc.set_laser_off()
    pcc.ser.write.assert_called_once_with(b"$P<\x00\x01\td")


def test_check_servo_controller(pcc: PeripheralControlComputer) -> None:
    pcc.check_servo_controller()
    pcc.ser.write.assert_called_once_with(b"$P<\x00\x01\x0b\x1b")
