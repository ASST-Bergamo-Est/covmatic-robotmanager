from .robot import Robot
from .singleton import Singleton
from . import EVA_IP_ADDRESS, EVA_TOKEN
import logging


class RobotManagerException(Exception):
    pass


class RobotManager(Singleton):
    def __init__(self, logger=logging.getLogger(__name__)):
        self._robot = Robot(eva_ip_address=EVA_IP_ADDRESS, token=EVA_TOKEN)
        self._logger = logger
        self._logger.info("RobotManager initilized)")

    def action_request(self, action, machine, slot, plate_name, options=None):
        position = "{}-{}".format(machine, slot)
        self._logger.info("Requested action {} for {} plate {}".format(action, position, slot))
        if action == "pick":
            self._robot.pick_up_plate(position, plate_name)
        elif action == "drop":
            self._robot.drop_plate(position, plate_name)
        else:
            raise RobotManagerException("Action {} not found".format(action))

