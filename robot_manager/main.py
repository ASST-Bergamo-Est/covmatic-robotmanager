# RobotManager
# ============
# a simple manager to control EVA robot and provide a safe interfate to be used by others.

import logging
import signal
import time

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
    max_speed = 0.25
    plate_order = ["OT1-SLOT1", "OT2-SLOT1", "OT1-SLOT1", "OT1-SLOT3", "OT1-SLOT2", "OT1-SLOT4", "OT1-SLOT11"]

    for j in range(10):
        print("Cycle {}".format(j+1))
        for i, _ in enumerate(plate_order):
            dest_plate = plate_order[i]
            pick_plate = plate_order[i-1]

            print("Transferring from {} to {}".format(pick_plate, dest_plate))
            robot.transfer_plate(pick_plate, dest_plate, max_speed=max_speed)
            print("waiting...")
            time.sleep(2)

    # for i in range(10):
    #
    #     robot.transfer_plate("OT2-SLOT1", "OT1-SLOT1", max_speed=max_speed)
    #     robot.transfer_plate("OT1-SLOT1", "OT1-SLOT3", max_speed=max_speed)
    #     robot.transfer_plate("OT1-SLOT3", "OT1-SLOT2", max_speed=max_speed)
    #     robot.transfer_plate("OT1-SLOT2", "OT1-SLOT4", max_speed=max_speed)
    #     robot.transfer_plate("OT1-SLOT4", "OT1-SLOT1", max_speed=max_speed)
    #     time.sleep(2)

    # robot.transfer_plate("OT1-SLOT2", "OT1-SLOT1", "OT1-HOME", max_speed=0.1)

    #     print("Waiting for cycle {}".format(i+1))
    #     time.sleep(2)

    # robot.unlock()

    # Test code for movement
    # robot.move_to_position("HOME")
    # robot.move_to_position("HOME", offset={"y": -0.1, "z": +0.1, "x": +0.1})
    # robot.close_gripper()
    # robot.move_to_position("HOME")
    # robot.open_gripper()

    # Test code to save current position with a name
    # First move the robot to the needed position, than run this instruction
    # robot.save_position("OT1-SLOT1")




