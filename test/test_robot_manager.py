from unittest.mock import patch

from src.covmatic_robotmanager.robot import RobotException
from src.covmatic_robotmanager.robot_manager import RobotManager
from test.common import BaseTestClass

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

ERROR_PLATE_CODE = "ERROR"

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
        'id': "1"
    }

drop_action1 = {
    'action': DROP_ACTION,
    'position': POSITION1,
    'plate_name': PLATE1,
    'id': "2"
}

drop_action2 = {
    'action': DROP_ACTION,
    'position': POSITION2,
    'plate_name': PLATE2,
    'id': "3"
}


class TestRobotManager(BaseTestClass):
    """ Base class to subclass for test execution """
    def setUp(self) -> None:
        self._robot_patcher = patch("src.covmatic_robotmanager.robot_manager.Robot")
        self._mock_robot = self._robot_patcher.start()
        self._config_patcher = patch("src.covmatic_robotmanager.robot_manager.Config")
        self._mock_config = self._config_patcher.start()
        self._rm = RobotManager()

    def tearDown(self) -> None:
        self._rm.shutdown()
        self._robot_patcher.stop()
        self._config_patcher.stop()


class TestBasicActions(TestRobotManager):
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

    def test_action_return_different_values(self):
        id1 = self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        id2 = self._rm.action_request(DROP_ACTION, MACHINE1, SLOT1, PLATE1)
        self.assertNotEqual(id1, id2)

class TestActionScheduler(TestRobotManager):
    def test_action_scheduler_empty_queue(self):
        self._rm.action_scheduler()

        self._mock_robot().pick_up_plate.assert_not_called()
        self._mock_robot().drop_plate.assert_not_called()

    def test_action_scheduler_pick_action_call_robot(self):
        self._rm._actions.append(pick_action1)
        self._rm.action_scheduler()
        self._mock_robot().pick_up_plate.assert_called_once()


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

    def test_error_during_action_clear_states(self):
        self._mock_robot().pick_up_plate.side_effect = RobotException("Test")
        self._rm._actions.append(pick_action1)
        self._rm.action_scheduler()
        self.assertIs(self._rm._current_plate, ERROR_PLATE_CODE)

class TestCheckAction(TestRobotManager):

    def setUp(self) -> None:
        super().setUp()
        self._rm._actions = [pick_action1, drop_action1]

    def test_function_exists(self):
        self._rm.check_action(pick_action1["id"])

    def test_action_contains_state(self):
        answer = self._rm.check_action(pick_action1["id"])
        self.assertIn("state", answer)

    def test_state_pending_action(self):
        answer = self._rm.check_action(pick_action1["id"])
        self.assertIs(answer["state"], "pending")

    def test_state_finished_action(self):
        answer = self._rm.check_action(pick_action2["id"])
        self.assertIs(answer["state"], "finished")

    def test_action_queued_but_not_read(self):
        """ Case to check that if executor thread has not run the result will be pending """
        action_id = self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        answer = self._rm.check_action(action_id)
        self.assertIs(answer["state"], "pending")

    # def test_check_action_not_existing(self, mock_robot):
    #     rm = RobotManager()
    #     with pytest.raises(RobotManagerException):
    #         rm.check_action(FAKE_ACTION_ID)