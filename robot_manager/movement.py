# Movement class to manage approaching and moving of robot
import json
import logging
from . import positions
from . import gripper
from .positions import Positions
from .EvaHelper import EvaHelper
from .toolpath import Toolpath
from .utils import *

MAX_SPEED = 0.25       # Max speed in m/s


class Movement:
    def __init__(self, logger=logging.getLogger(__name__)):
        self._eva = EvaHelper().eva
        self._positions = Positions()
        self._logger = logger
        self._eva_helper = EvaHelper()
        self._logger.info("Loaded Eva: {}".format(self._eva_helper.get_robot_info()))

    def move_to(self, position):
        xyz = self._positions.get_position(position)
        self._logger.info("going to position: {}".format(xyz))

    def get_angles(self):
        self._eva_helper.check_data_emergency_stop()
        joints = self._eva.data_servo_positions()
        self._logger.info("Got joints: {}".format(joints))
        return joints

    def get_forward_kinematics_from_angles(self, angles):
        forward_k = self._eva.calc_forward_kinematics(angles)

        if forward_k["result"] != "success":
            raise Exception("Forward kinematics calculation error for angles {}.\nResult: {}".format(angles, forward_k))
        del forward_k["result"]

        self._logger.info("Calculated forward kinematics:\n{}\nfor angles:{}\n".format(forward_k, rad2deg(angles)))
        return forward_k

    def save_position(self, name):
        joints = self.get_angles()
        self._positions.save_joints(name, joints)
        self._positions.save_xyz(name, self.get_forward_kinematics_from_angles(joints))

    def get_inverse_kinematics(self, position_and_orientation):
        eva_guess = [0, 0, 0, 0, 0, 0]
        joints = self._eva.calc_inverse_kinematics(eva_guess,
                                                   position_and_orientation["position"],
                                                   position_and_orientation["orientation"])

        self._logger.info("Got joints: {}".format(joints))

    def go_to_position(self, position_name, speed: float = None, offset: dict = None):
        self._logger.info("Going to position {}".format(position_name))

        if not speed:
            speed = MAX_SPEED



        self._eva_helper.check_data_emergency_stop()
        with self._eva.lock():
            self._eva.control_go_to(joints, max_speed=speed)

    def get_joints_from_updated_position(self, name, offset: dict):
        self._logger.info("Updating position {}".format(name))

        joints = self._positions.get_joints(name)

        for o in offset:
            self._logger.info("Updating offset {} with value: {}".format(o, offset[o]))
            self._logger.info("Old joints: {}".format(joints))

            joints = self._eva.calc_nudge(joints, direction=o, offset=offset[o])
            self._logger.info("New joints: {}".format(joints))
        return joints

    def get_joints(self, position_name, offset: dict = None):
        if offset:
            joints = self.get_joints_from_updated_position(position_name, offset)
        else:
            joints = self._positions.get_joints(position_name)
        return joints

    def test_toolpath(self):
        tp = Toolpath(max_speed=0.1)
        tp.add_waypoint(1, self._positions.get_joints("HOME"))
        tp.add_waypoint(2, self.get_joints_from_updated_position("HOME", offset={"x": 0.3}))
        tp.add_movement(1)
        tp.add_movement(2, "linear")
        tp.add_movement(1)

        with self._eva.lock():
            self._eva.toolpaths_use(tp.toolpath)
            self._eva.control_run(loop=2)

        # Test toolpath output
        with open("test_toolpath.json", "w") as fp:
            self._logger.info("{}".format(tp.toolpath))
            json.dump(tp.toolpath, fp)
