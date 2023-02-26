from __future__ import annotations

import pytest
from pytest_mock.plugin import MockerFixture

from bell.avr.serial.pcc import PeripheralControlComputer
from tests.models import MQTTModuleTest


@pytest.fixture()
def mqtt_module(mocker: MockerFixture) -> MQTTModuleTest:
    """
    Create an MQTTModule with a test handler function.
    """
    module = MQTTModuleTest()
    mocker.patch.object(module, "test_handler")
    mocker.patch.object(module, "test_handler_empty")
    mocker.patch.object(module, "_mqtt_client")

    return module


@pytest.fixture()
def pcc(mocker: MockerFixture) -> PeripheralControlComputer:
    """
    Create a PeripheralControlComputer with a mocked serial client.
    """
    pcc = PeripheralControlComputer(mocker.MagicMock())
    mocker.patch.object(pcc, "ser")

    return pcc
