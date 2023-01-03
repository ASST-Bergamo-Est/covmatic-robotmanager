# RobotManager
# ============
# a simple manager to control EVA robot and provide a safe interfate to be used by others.

import logging
import time
from enum import Enum

from evasdk import Eva
from . import __version__
from .EvaHelper import EvaHelper
from .gripper import EvaGripper
from .movement import Movement


class GripperStatus(Enum):
    open = 0,
    closed = 1,
    undefined = 2


class Robot:
    def __init__(self, eva_ip_address, token, logger: logging.getLogger(__name__)):
        self._logger = logger
        self._eva_helper = EvaHelper()
        self._eva_helper.connect(eva_ip_address, token)
        self._gripper = EvaGripper()
        self._movement = Movement()

    def unlock(self):
        self._eva_helper.disconnect()

    def open_gripper(self):
        self._logger.info("Opening gripper")
        self._gripper.open()

    def close_gripper(self):
        self._logger.info("Closing gripper")
        self._gripper.close()

    # def pick_up(self, position):
    #     self._movement.move_to(position)

    def home(self):
        self._movement.move_to("HOME")

    def check_gripper_has_plate(self):
        if not self._gripper.has_plate():
            self._gripper.open()
            raise Exception("Plate not grabbed")

    def save_position(self, name: str, joints=None):
        self._movement.save_position(name, joints)

    def move_to_position(self, name: str, speed: float = None, offset: dict = None):
        self._logger.info("Moving to position {} with offset: {}".format(name, offset))
        self._movement.go_to_position(name, speed, offset)

    def test_pick_up(self):
        position_name = "OT1-SLOT1"

        for i in range(10):
            self._movement.approach_linear(position_name)

            self._gripper.close()

            if not self._gripper.has_plate():
                self._gripper.open()
                raise Exception("Plate not grabbed")

            self._movement.raise_vertically(0.005)

            self._gripper.open()

    def test_toolpath(self):
        self._movement.test_toolpath()

    def transfer_plate(self, source_pos, dest_pos, max_speed=None, detach_plate=False):
        self._movement.transfer_plate(source_pos, dest_pos, max_speed, detach_plate=detach_plate)

    def lock_for_seconds(self, seconds=10):
        # DEBUG ONLY, to be substituted with something else
        self._logger.info("Locking robot")
        with self._eva_helper.eva.lock():
            self._eva_helper.check_and_clear_errors()
            time.sleep(seconds)
        self._logger.info("Robot unlocked")

    def get_state(self):
        return self._eva_helper.eva.data_snapshot()
