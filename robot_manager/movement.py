# Movement class to manage approaching and moving of robot

import logging
from . import positions
from . import gripper
from .positions import Positions
from .utils import *

class Movement:
    def __init__(self, eva, logger = logging.getLogger(__name__)):
        self._eva = eva
        self._positions = Positions()
        self._logger = logger

    def move_to(self, position):
        xyz = self._positions.get_position(position)
        self._logger.info("going to position: {}".format(xyz))

    def get_forward_kinematics(self):
        angles = self._eva.data_servo_positions()
        forward_k = self._eva.calc_forward_kinematics(angles)

        if forward_k["result"] != "success":
            raise Exception("Forward kinematics calculation error for angles {}.\nResult: {}".format(angles, forward_k))
        del forward_k["result"]

        self._logger.info("Calculated forward kinematics:\n{}\nfor angles:{}\n".format(forward_k, rad2deg(angles)))
        return forward_k

    def save_position(self, name):
        self._positions.save(self.get_forward_kinematics(), name)
