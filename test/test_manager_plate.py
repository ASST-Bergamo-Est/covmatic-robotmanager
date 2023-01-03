import logging
import pytest

from ..robot_manager.robot_manager import Movement
from ..robot_manager.robot_manager import Robot
from ..robot_manager.EvaHelper import EvaHelper
from mock import patch, Mock

FAKE_IP_ADDRESS = "fakeipaddress"
FAKE_TOKEN = "faketoken"
fake_logger = logging.getLogger()


class FakeEvaHelper:
    def __init__(self):
        pass

    def connect(self, *args, **kwargs):
        pass


class FakeMovement:
    def __init__(self):
        pass


@patch.object(Movement, "__init__", FakeMovement.__init__)
@patch.object(EvaHelper, "connect")
def test_instance_creation(mock_connect):
    robot = Robot(eva_ip_address=FAKE_IP_ADDRESS, token=FAKE_TOKEN, logger=fake_logger)

