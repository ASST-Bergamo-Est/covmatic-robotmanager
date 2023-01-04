# RobotManager
# ============
# a simple manager to control EVA robot and provide a safe interfate to be used by others.

import logging
import time
from enum import Enum

from .movement import Movement
from .EvaHelper import EvaHelper


class GripperStatus(Enum):
    open = 0,
    closed = 1,
    undefined = 2


class RobotManagerException(Exception):
    pass


class Robot:
    def __init__(self, eva_ip_address, token, logger: logging.getLogger(__name__)):
        self._logger = logger
        self._eva_helper = EvaHelper()
        self._eva_helper.connect(eva_ip_address, token)
        self._movement = Movement()
        self._pickup_pos = None
        self._drop_pos = None
        self._plate = None

    def unlock(self):
        self._eva_helper.disconnect()

    def save_position(self, name: str, joints=None):
        self._movement.save_position(name, joints)

    def move_to_position(self, name: str, speed: float = None, offset: dict = None):
        self._logger.info("Moving to position {} with offset: {}".format(name, offset))
        self._movement.go_to_position(name, speed, offset)

    def transfer_plate(self, source_pos, dest_pos, max_speed=None, detach_plate=False):
        self._movement.transfer_plate(source_pos, dest_pos, max_speed, detach_plate=detach_plate)

    def pick_up_plate(self, position, plate_name):
        self._logger.info("Requested pickup from {} for plate {}".format(position, plate_name))
        self._pickup_pos = position
        self._check_and_set_plate_name(plate_name)
        self._check_and_execute_transfer()

    def drop_plate(self, position, plate_name):
        self._logger.info("Requested drop to {} for plate {}".format(position, plate_name))
        self._drop_pos = position
        self._check_and_set_plate_name(plate_name)
        self._check_and_execute_transfer()

    def _check_and_set_plate_name(self, plate_name):
        if not self._plate:
            self._plate = plate_name
        elif self._plate != plate_name:
            raise RobotManagerException("New plate {} not assigned: already present {} plate".format(plate_name, self._plate))

    def _check_and_execute_transfer(self):
        if self._plate and self._pickup_pos and self._drop_pos:
            self._movement.transfer_plate(self._pickup_pos, self._drop_pos)
            self.clear_transfer()

    def clear_transfer(self):
        self._plate = None
        self._pickup_pos = None
        self._drop_pos = None

