import logging
from time import sleep
from unittest.mock import patch

from src.covmatic_robotmanager.robot import RobotException
from src.covmatic_robotmanager.robot_manager import RobotManager, RobotManagerException
from test.common import BaseTestClass, setup_log

setup_log()

PICK_ACTION = "pick"
DROP_ACTION = "drop"

MACHINE1 = "OT1"
SLOT1 = "SLOT1"
PLATE1 = "PLATE1"


MACHINE2 = "OT2"
SLOT2 = "SLOT2"
PLATE2 = "PLATE2"

MAC_1_SLOT_1 = "{}-{}".format(MACHINE1, SLOT1)
MAC_1_SLOT_2 = "{}-{}".format(MACHINE1, SLOT2)
MAC_2_SLOT_2 = "{}-{}".format(MACHINE2, SLOT2)

ERROR_PLATE_CODE = "ERROR"

WRONG_ACTION = "wrong"
FAKE_ACTION_ID = "fakeaction"


class TestRobotManager(BaseTestClass):
    """ Base class to subclass for test execution """
    def setUp(self) -> None:
        self._robot_patcher = patch("src.covmatic_robotmanager.robot_manager.Robot")
        self._mock_robot = self._robot_patcher.start()
        self._config_patcher = patch("src.covmatic_robotmanager.robot_manager.Config")
        self._mock_config = self._config_patcher.start()
        self._rm = RobotManager.reset(start_thread=False)

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
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_scheduler()
        self._mock_robot().pick_up_plate.assert_not_called()

    def test_action_scheduler_pick_action_called(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_scheduler()

        self._rm.action_request(DROP_ACTION, MACHINE2, SLOT1, PLATE1)
        self._rm.action_scheduler()
        self._mock_robot().pick_up_plate.assert_called_once()

    def test_action_scheduler_pick_action_called_different_input_order(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_request(DROP_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_scheduler()
        self._mock_robot().pick_up_plate.assert_called_once()

    def test_action_scheduler_drop_action_do_nothing_on_state(self):
        self._rm.action_request(DROP_ACTION, MACHINE2, SLOT1, PLATE1)

        self._rm.action_scheduler()
        assert self._rm._current_plate is None

    def test_action_scheduler_drop_action_do_nothing_on_plate(self):
        self._rm.action_request(DROP_ACTION, MACHINE2, SLOT1, PLATE1)

        self._rm.action_scheduler()
        assert self._rm._current_plate != PLATE1

    def test_both_action_present_ordered_final_state(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_request(DROP_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_scheduler()

        assert self._rm._current_plate is None

    def test_both_done_action_are_set_as_finished(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_request(DROP_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_scheduler()

        self.assertEqual(0, len(self._rm._pending_actions))

    def test_pending_action_is_present(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_request(DROP_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_request(PICK_ACTION, MACHINE2, SLOT1, PLATE1)
        self._rm.action_scheduler()

        self.assertEqual(1, len(self._rm._pending_actions))

    def test_pick_different_plate_stay_queued(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_scheduler()

        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE2)
        self._rm.action_request(DROP_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_scheduler()

        self.assertEqual(1, len(self._rm._pending_actions))

    def test_pick_different_plate_plate_not_modified(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_scheduler()

        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE2)
        self._rm.action_request(DROP_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_scheduler()

        self.assertIsNone(self._rm._current_plate)


class TestPickDropSameMachine(TestRobotManager):
    def test_check_default_value(self):
        self.assertFalse(self._rm._pick_drop_same_machine)

    def test_pick_different_machines(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_request(DROP_ACTION, MACHINE2, SLOT1, PLATE1)
        self._rm.action_scheduler()
        self._mock_robot().pick_up_plate.assert_called_with(MAC_1_SLOT_1, False)

    def test_pick_same_machine_same_slot(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_request(DROP_ACTION, MACHINE1, SLOT2, PLATE1)
        self._rm.action_scheduler()
        self._mock_robot().pick_up_plate.assert_called_with(MAC_1_SLOT_1, True)

    def test_drop_different_machines(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_request(DROP_ACTION, MACHINE2, SLOT2, PLATE1)
        self._rm.action_scheduler()
        self._mock_robot().drop_plate.assert_called_with(MAC_2_SLOT_2, False)

    def test_drop_same_machine_same_slot(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_request(DROP_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_scheduler()
        self._mock_robot().drop_plate.assert_called_with(MAC_1_SLOT_1, True)

    def test_drop_same_machine_different_slot(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_request(DROP_ACTION, MACHINE1, SLOT2, PLATE1)
        self._rm.action_scheduler()
        self._mock_robot().drop_plate.assert_called_with(MAC_1_SLOT_2, True)

    def test_parameter_reset_after_drop(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_request(DROP_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_scheduler()
        self.assertFalse(self._rm._pick_drop_same_machine)


class TestCheckAction(TestRobotManager):
    def setUp(self) -> None:
        super().setUp()
        self._action_id_pick = self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._action_id_drop = self._rm.action_request(DROP_ACTION, MACHINE2, SLOT1, PLATE1)
        print(self._rm._actions)

    def test_function_exists(self):
        self._rm.check_action(self._action_id_pick)

    def test_action_contains_state(self):
        answer = self._rm.check_action(self._action_id_pick)
        self.assertIn("state", answer)

    def test_state_pending_action(self):
        answer = self._rm.check_action(self._action_id_pick)
        self.assertIs(answer["state"], "pending")

    def test_state_finished_action_pick(self):
        self._rm.action_scheduler()
        self._rm.action_scheduler()
        answer = self._rm.check_action(self._action_id_pick)
        self.assertIs(answer["state"], "finished")

    def test_action_queued_but_not_read(self):
        """ Case to check that if executor thread has not run the result will be pending """
        action_id = self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        answer = self._rm.check_action(action_id)
        self.assertIs(answer["state"], "pending")

    # def test_check_action_not_existing(self):
    #     with self.assertRaises(RobotManagerException):
    #         self._rm.check_action(FAKE_ACTION_ID)


class TestPickError(TestRobotManager):
    def setUp(self) -> None:
        super().setUp()

        self._action_id_pick = self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._action_id_drop = self._rm.action_request(DROP_ACTION, MACHINE2, SLOT1, PLATE1)

        self._mock_robot().pick_up_plate.side_effect = RobotException("Pick error!")
        self._rm.action_scheduler()
        self._rm.action_scheduler()

    def test_error_in_pick_return_aborted(self):
        logging.getLogger().info("TEST")
        for _ in range(10):
            print(self._rm.check_action(self._action_id_pick))
            sleep(0.1)
        answer = self._rm.check_action(self._action_id_pick)
        logging.getLogger().info("TEST 2")
        self.assertIs(answer["state"], "aborted")

    def test_error_in_pick_return_aborted_for_drop(self):
        answer = self._rm.check_action(self._action_id_drop)
        self.assertIs(answer["state"], "aborted")

    def test_error_in_pick_plate_is_reset(self):
        self._rm.action_request(PICK_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_request(DROP_ACTION, MACHINE1, SLOT1, PLATE1)
        self._rm.action_scheduler()
        self.assertIsNone(self._rm._current_plate)
