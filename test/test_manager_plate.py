import logging
import pytest

from ..robot_manager.robot_manager import Movement
from ..robot_manager.robot_manager import Robot, RobotManagerException
from ..robot_manager.EvaHelper import EvaHelper
from mock import patch, Mock

FAKE_IP_ADDRESS = "fakeipaddress"
FAKE_TOKEN = "faketoken"
fake_logger = logging.getLogger()

PICK_POS1 = "OT1-SLOT1"
PICK_POS2 = "OT1-SLOT2"
DROP_POS1 = "OT2-SLOT5"
DROP_POS2 = "OT2-SLOT6"
PLATE_NAME1 = "REAGENT"
PLATE_NAME2 = "WASH"


class FakeEvaHelper:
    def __init__(self):
        pass

    def connect(self, *args, **kwargs):
        pass


class FakeMovement:
    transfer_calls = 0

    def __init__(self):
        self.__class__.transfer_calls = 0

    @classmethod
    def transfer_plate(cls, *args, **kwargs):
        cls.transfer_calls += 1

    @classmethod
    def reset_calls(cls):
        cls.transfer_calls = 0

    @classmethod
    def check_calls(cls, calls):
        if cls.transfer_calls != calls:
            raise Exception("Calls expected {} got {}".format(calls, cls.transfer_calls))


@pytest.fixture
@patch.object(Movement, "__init__", FakeMovement.__init__)
@patch.object(EvaHelper, "connect")
def robot(mock_connect):
    _robot = Robot(eva_ip_address=FAKE_IP_ADDRESS, token=FAKE_TOKEN, logger=fake_logger)
    return _robot


def test_instance_creation(robot):
    assert robot


def test_pickup_plate_position_is_saved(robot):
    robot.pick_up_plate(PICK_POS1, PLATE_NAME1)
    assert robot._pickup_pos == PICK_POS1


def test_pickup_plate_name_is_saved(robot):
    robot.pick_up_plate(PICK_POS1, PLATE_NAME1)
    assert robot._plate == PLATE_NAME1


def test_drop_plate_position_is_saved(robot):
    robot.drop_plate(DROP_POS1, PLATE_NAME1)
    assert robot._drop_pos == DROP_POS1


def test_drop_plate_name_is_saved(robot):
    robot.drop_plate(DROP_POS1, PLATE_NAME1)
    assert robot._plate == PLATE_NAME1


def test_error_if_multiple_pickup(robot):
    robot.pick_up_plate(PICK_POS1, PLATE_NAME1)
    with pytest.raises(RobotManagerException):
        robot.pick_up_plate(PICK_POS1, PLATE_NAME2)


def test_error_if_multiple_drop(robot):
    robot.drop_plate(PICK_POS1, PLATE_NAME1)
    with pytest.raises(RobotManagerException):
        robot.drop_plate(PICK_POS1, PLATE_NAME2)


## Test using the movement mock
@patch.object(Movement, "transfer_plate", FakeMovement.transfer_plate)
def test_plate_not_transferred_pickup(robot):
    FakeMovement.reset_calls()
    robot.pick_up_plate(PICK_POS1, PLATE_NAME1)
    FakeMovement.check_calls(0)


@patch.object(Movement, "transfer_plate", FakeMovement.transfer_plate)
def test_complete_transfer(robot):
    FakeMovement.reset_calls()
    robot.pick_up_plate(PICK_POS1, PLATE_NAME1)
    robot.drop_plate(DROP_POS1, PLATE_NAME1)
    FakeMovement.check_calls(1)


@patch.object(Movement, "transfer_plate", FakeMovement.transfer_plate)
def test_plate_not_transferred_drop(robot):
    FakeMovement.reset_calls()
    robot.drop_plate(DROP_POS1, PLATE_NAME1)
    FakeMovement.check_calls(0)



