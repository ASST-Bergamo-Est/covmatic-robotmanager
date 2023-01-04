# RobotManager
# ============
# a simple manager to control EVA robot and provide a safe interfate to be used by others.

import logging
import time

from .robot_manager import Robot
from . import __version__

# EVA Configuration
EVA_IP_ADDRESS = "10.213.55.80"
EVA_TOKEN = '35ad1b7da935684d10afdc09a5842d5e6403b0f8'

# Server configuration
SERVER_PORT = 80

logger = logging.getLogger(__name__)
logger.info("Starting version {}".format(__version__))

robot = Robot(EVA_IP_ADDRESS, EVA_TOKEN, logger)


if __name__ == '__main__':
    robot.pick_up_plate("OT2-TC", "PLATE1")
    robot.drop_plate("OT2-WORK1", "PLATE1")

    robot.pick_up_plate("OT2-WORK1", "REAGENT")
    robot.drop_plate("OT2-TC", "REAGENT")





