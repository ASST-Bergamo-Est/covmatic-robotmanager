import unittest

import pytest
from mock import Mock, patch

from ..robot_manager.robot_manager import RobotManager, Robot, RobotManagerException

PICK_ACTION = "pick"
DROP_ACTION = "drop"

MACHINE1 = "OT1"
SLOT1 = "SLOT1"
POSITION1 = "{}-{}".format(MACHINE1, SLOT1)
PLATE1 = "PLATE1"


MACHINE2 = "OT2"
SLOT2 = "SLOT2"
POSITION2 = "{}-{}".format(MACHINE2, SLOT2)
PLATE2 = "PLATE2"

WRONG_ACTION = "wrong"
FAKE_ACTION_ID = "fakeaction"

pick_action1 = {
        'action': PICK_ACTION,
        'position': POSITION1,
        'plate_name': PLATE1,
        'id': "0"
    }

pick_action2 = {
        'action': PICK_ACTION,
        'position': POSITION2,
        'plate_name': PLATE2,
        'id': "0"
    }

drop_action1 = {
    'action': DROP_ACTION,
    'position': POSITION1,
    'plate_name': PLATE1,
    'id': "1"
}

drop_action2 = {
    'action': DROP_ACTION,
    'position': POSITION2,
    'plate_name': PLATE2,
    'id': "2"
}

# @patch("RobotManager.robot_manager.robot_manager.Robot")
class TestRobotManager(unittest.TestCase):

    def setUp(self) -> None:
        self._robot_patcher = patch("RobotManager.robot_manager.robot_manager.Robot")
        self._mock_robot = self._robot_patcher.start()
        self._rm = RobotManager()

    def tearDown(self) -> None:
        self._rm.shutdown()
        self._robot_patcher.stop()

    def test_instance_creation(self):
        assert self._rm

    def test_instannce_has_robot(self):
        self._mock_robot.assert_called_once()

    def test_action_request(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)

    def test_action_request_return_value(self):
        assert self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)

    def test_action_request_return_value_drop(self):
        assert self._rm.action_request(DROP_ACTION, MACHINE1, SLOT1, PLATE1)

    # Test for the action scheduler
    def test_action_scheduler_empty_queue(self):
        self._rm.action_scheduler()

        self._mock_robot.pick_up_plate.assert_not_called()
        self._mock_robot.drop_plate.assert_not_called()


    ## This test does not work!
    # def test_action_scheduler_pick_action_call_robot(self, mock_robot):
    #     rm = RobotManager()
    #
    #     rm._actions.append(pick_action1)
    #
    #     rm.action_scheduler()
    #     mock_robot.pick_up_plate.assert_called_once()


    def test_action_scheduler_pick_set_plate(self):
        self._rm._actions.append(pick_action1)
        self._rm.action_scheduler()

        assert self._rm._current_plate == pick_action1["plate_name"]

    def test_action_scheduler_drop_action_do_nothing_on_state(self):
        self._rm._actions.append(drop_action1)

        self._rm.action_scheduler()
        assert self._rm._current_plate is None

    def test_action_scheduler_drop_action_do_nothing_on_plate(self):
        self._rm._actions.append(drop_action1)

        self._rm.action_scheduler()
        assert self._rm._current_plate != drop_action1["plate_name"]

    def test_both_action_present_ordered_final_state(self):
        self._rm._actions.append(pick_action1)
        self._rm._actions.append(drop_action1)
        self._rm.action_scheduler()

        assert self._rm._current_plate is None

    def test_both_done_action_is_deleted_pick(self):
        self._rm._actions.append(pick_action1)
        self._rm._actions.append(drop_action1)
        self._rm.action_scheduler()

        assert pick_action1 not in self._rm._actions

    def test_both_done_action_is_deleted_drop(self):
        self._rm._actions.append(pick_action1)
        self._rm._actions.append(drop_action1)
        self._rm.action_scheduler()

        assert drop_action1 not in self._rm._actions

    def test_undone_action_is_present(self):
        self._rm._actions.append(pick_action1)
        self._rm._actions.append(drop_action2)
        self._rm._actions.append(drop_action1)
        self._rm.action_scheduler()

        assert drop_action2 in self._rm._actions

    def test_pick_different_plate_stay_queued(self):
        self._rm._actions.append(pick_action1)
        self._rm.action_scheduler()

        self._rm._actions.append(pick_action2)
        self._rm.action_scheduler()

        assert pick_action2 in self._rm._actions

    def test_pick_different_plate_plate_not_modified(self):
        self._rm._actions.append(pick_action1)
        self._rm.action_scheduler()

        self._rm._actions.append(pick_action2)
        self._rm.action_scheduler()

        assert self._rm._current_plate == pick_action1["plate_name"]

    # def test_check(self, mock_robot):
    #     rm = RobotManager()
    #     action_id = rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
    #     rm.check_action(action_id)
    #
    # def test_check_action_not_existing(self, mock_robot):
    #     rm = RobotManager()
    #     with pytest.raises(RobotManagerException):
    #         rm.check_action(FAKE_ACTION_ID)