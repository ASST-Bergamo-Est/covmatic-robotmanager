# RobotManager
# ============
# a simple manager to control EVA robot and provide a safe interfate to be used by others.

import logging
from .robot_manager import Robot
from . import __version__

# Configuration section
EVA_IP_ADDRESS = "10.213.55.80"
SERVER_PORT = 80
token = '35ad1b7da935684d10afdc09a5842d5e6403b0f8'


logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Starting version {}".format(__version__))
    robot = Robot(EVA_IP_ADDRESS, token, logger)
    robot.connect()
    robot.test_gripper()
