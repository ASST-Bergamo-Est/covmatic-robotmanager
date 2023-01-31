# RobotManager
# ============
# a simple manager to control EVA robot and provide a safe interfate to be used by others.

import logging
from enum import Enum

from .movement import Movement, MovementException
from .EvaHelper import EvaHelper


class GripperStatus(Enum):
    open = 0,
    closed = 1,
    undefined = 2


class RobotException(Exception):
    pass


class Robot:
    def __init__(self, eva_ip_address, token, position_filepath, logger=logging.getLogger(__name__)):
        self._logger = logger
        self._eva_helper = EvaHelper()
        self._eva_helper.connect(eva_ip_address, token)
        self._movement = Movement(position_filepath)

    def unlock(self):
        self._eva_helper.disconnect()

    def save_position(self, name: str, joints=None):
        self._movement.save_position(name, joints)

    def move_to_position(self, name: str, speed: float = None, offset: dict = None):
        self._logger.info("Moving to position {} with offset: {}".format(name, offset))
        self._movement.go_to_position(name, speed, offset)

    def transfer_plate(self, source_pos, dest_pos, max_speed=None, detach_plate=False):
        self._movement.transfer_plate(source_pos, dest_pos, max_speed, detach_plate=detach_plate)

    def pick_up_plate(self, position):
        self._logger.info("Requested pickup from {}".format(position))
        try:
            self._movement.pick_plate(position)
        except MovementException as e:
            self._logger.error("Exception during pickup: {}".format(e))
            raise RobotException(str(e))

    def drop_plate(self, position):
        self._logger.info("Requested drop to {}".format(position))
        try:
            self._movement.drop_plate(position)
        except MovementException as e:
            self._logger.error("Exception during pickup: {}".format(e))
            raise RobotException(str(e))

