import pytest
from pytest_mock.plugin import MockerFixture
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
