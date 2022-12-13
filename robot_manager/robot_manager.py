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
from .positions import Positions

logger = logging.getLogger(__name__)


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

    def open_gripper(self):
        logger.info("Opening gripper")
        self._gripper.open()

    def close_gripper(self):
        logger.info("Closing gripper")
        self._gripper.close()

    # def pick_up(self, position):
    #     self._movement.move_to(position)

    def home(self):
        self._movement.move_to("HOME")

    def check_gripper_has_plate(self):
        if not self._gripper.has_plate():
            self._gripper.open()
            raise Exception("Plate not grabbed")

    def save_position(self, name: str):
        self._movement.save_position(name)

    def move_to_position(self, name: str, speed: float = None, offset: dict = None):
        self._logger.info("Moving to position {} with offset: {}".format(name, offset))
        self._movement.go_to_position(name, speed, offset)
