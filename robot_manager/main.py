# RobotManager
# ============
# a simple manager to control EVA robot and provide a safe interfate to be used by others.

import logging
import signal

from .robot_manager import Robot
from . import __version__

# Configuration section
EVA_IP_ADDRESS = "10.213.55.80"
SERVER_PORT = 80
token = '35ad1b7da935684d10afdc09a5842d5e6403b0f8'


logger = logging.getLogger(__name__)
logger.info("Starting version {}".format(__version__))

robot = Robot(EVA_IP_ADDRESS, token, logger)


# def handler(signum, frame):
#     logger.error("Signal received: {}".format(signum))
#     robot.kill()
#
#
# signal.signal(signal.SIGALRM, handler)
# signal.signal(signal.SIGTERM, handler)
# signal.signal(signal.SIGKILL, handler)
# signal.signal(signal.SIGINT, handler)
# signal.signal(signal.SIGHUP, handler)
# signal.signal(signal.SIGABRT, handler)


if __name__ == '__main__':
    # robot.test_toolpath()
    # robot.unlock()

    # Test code for movement
    robot.move_to_position("HOME")
    robot.move_to_position("HOME", offset={"y": -0.1, "z": +0.1, "x": +0.1})
    robot.close_gripper()
    robot.move_to_position("HOME")
    robot.open_gripper()

    # Test code to save current position with a name
    # First move the robot to the needed position, than run this instruction
    # robot.save_position("OT1-SLOT1")




