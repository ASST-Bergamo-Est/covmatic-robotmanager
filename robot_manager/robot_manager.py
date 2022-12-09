# RobotManager
# ============
# a simple manager to control EVA robot and provide a safe interfate to be used by others.

import logging
import time
from enum import Enum

from evasdk import Eva
from . import __version__
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
        self._eva_ip_address = eva_ip_address
        self._token = token
        self._logger = logger
        self._eva = None
        self._gripper = None
        self._movement = None

    def connect(self):
        logger.info("Config IP Address: {}".format(self._eva_ip_address))
        logger.info("Attempting to connect to robot...")
        self._eva = Eva(self._eva_ip_address, self._token)
        self._gripper = EvaGripper(self._eva)
        self._movement = Movement(self._eva)
        logger.info("Connected to Eva {} with API version {}".format(
            self._eva.name()["name"],
            self._eva.versions()))

    def get_robot_info(self):
        return {"name": self._eva.name()["name"],
                "versions": self._eva.versions()}

    def get_data(self):
        data = self._eva.data_snapshot()
        return data

    def print_data(self):
        data = self.get_data()
        logger.info("Data:")
        for d in data:
            logger.info("{}: {}".format(d, data[d]))

    def check_data_emergency_stop(self, data=None):
        if not data:
            data = self.get_data()
        if data['global']['estop']:
            raise Exception("Emergency stop pressed. Please release it.")

    def open_gripper(self):
        logger.info("Opening gripper")
        self.check_data_emergency_stop()
        self._gripper.open()

    def close_gripper(self):
        logger.info("Closing gripper")
        self.check_data_emergency_stop()
        self._gripper.close()

    # def pick_up(self, position):
    #     self._movement.move_to(position)

    def home(self):
        self._movement.move_to("HOME")

    def check_gripper_has_plate(self):
        if not self._gripper.has_plate():
            self._gripper.open()
            raise Exception("Plate not grabbed")

    def test_gripper(self):
        self._logger.info("Trying to acquire lock")
        with self._eva.lock():
            self._logger.info("Lock acquired")
            self.close_gripper()
            self.check_gripper_has_plate()
            time.sleep(1)
            self.open_gripper()
        self._logger.info("Lock released")

    def save_position(self, name: str):
        self._movement.save_position(name)

