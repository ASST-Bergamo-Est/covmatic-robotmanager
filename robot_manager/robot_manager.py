from .robot import Robot
from .singleton import Singleton
from . import EVA_IP_ADDRESS, EVA_TOKEN
import logging


class RobotManager(Singleton):
    def __init__(self, logger=logging.getLogger(__name__)):
        self._robot = Robot(eva_ip_address=EVA_IP_ADDRESS, token=EVA_TOKEN)
        self._logger = logger
        self._logger.info("RobotManager initilized)")


robot_manager = RobotManager()