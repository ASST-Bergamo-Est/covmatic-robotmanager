# Movement class to manage approaching and moving of robot
import json
import logging
import time

from . import positions
from .gripper import EvaGripper
from .positions import Positions
from .EvaHelper import EvaHelper
from .toolpath import Toolpath, ToolpathExecute
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
            self._eva.control_go_to(self.get_joints(position_name, offset=offset), max_speed=speed)

    def get_joints_from_updated_position(self, name, offset: dict):
        self._logger.info("Updating position {}".format(name))

        joints = self._positions.get_joints(name)

        for o in offset:
            self._logger.debug("Updating offset {} with value: {}".format(o, offset[o]))
            self._logger.debug("Old joints: {}".format(joints))
            joints = self._eva.calc_nudge(joints, direction=o, offset=offset[o])
            self._logger.debug("New joints: {}".format(joints))
        return joints

    def get_joints(self, position_name, offset: dict = None):
        if offset:
            joints = self.get_joints_from_updated_position(position_name, offset)
        else:
            joints = self._positions.get_joints(position_name)
        return joints

    def get_raising_height(self, pos: str):

        owner = self._positions.get_pos_owner(pos)

        max_labware_height_from_deck = 0.17

        max_z = self._positions.get_xyz("{}-HMAX".format(owner))["position"]["z"]
        deck_z = self._positions.get_xyz("{}-DECK".format(owner))["position"]["z"]
        self._logger.info("Deck Z for object {} is {}. Max z is {}".format(owner, deck_z, max_z))

        z_to_reach = deck_z + max_labware_height_from_deck
        self._logger.info("Z to reach {}".format(z_to_reach))

        pos_z = self._positions.get_xyz("{}".format(pos))["position"]["z"]
        raising_height = -(z_to_reach - pos_z)     # Changed sign since with normal orientaion positive it toward bottom

        self._logger.info("We've to raise of {}".format(raising_height))
        return raising_height

    def transfer_plate(self, source_pos, dest_pos, max_speed=None):

        gripper = EvaGripper()

        near_height = -0.01
        grip_height = 0.008

        source_raising_height = self.get_raising_height(source_pos)
        dest_raising_height = self.get_raising_height(dest_pos)

        source_owner = self._positions.get_pos_owner(source_pos)
        dest_owner = self._positions.get_pos_owner(dest_pos)
        is_different_owner = source_owner != dest_owner

        self._logger.info("Source owner {}; dest owner {}; are different: {}".format(source_owner, dest_owner, is_different_owner))
        source_home_pos = self.get_joints("{}-HOME".format(source_owner))
        dest_home_pos = self.get_joints("{}-HOME".format(dest_owner))

        approach_speed = 0.025

        self._eva_helper.check_data_emergency_stop()

        with self._eva.lock():
            self._eva_helper.check_and_clear_errors()

        tp = Toolpath(max_speed=max_speed)
        tp.add_waypoint("pick_home", source_home_pos)
        tp.add_waypoint("pick_pos_up", self.get_joints(source_pos, offset={"z": source_raising_height}))
        tp.add_waypoint("pick_pos_near", self.get_joints(source_pos, offset={"z": near_height}))
        tp.add_waypoint("pick_pos",  self.get_joints(source_pos, offset={"z": grip_height}))

        tp.add_waypoint("drop_home", dest_home_pos)
        tp.add_waypoint("drop_pos_up", self.get_joints(dest_pos, offset={"z": dest_raising_height}))
        tp.add_waypoint("drop_pos_near", self.get_joints(dest_pos, offset={"z": near_height}))
        tp.add_waypoint("drop_pos", self.get_joints(dest_pos, offset={"z": grip_height}))

        gripper.close()

        with ToolpathExecute(tp):
            tp.add_movement("pick_home")
            tp.add_movement("pick_pos_up")
            tp.add_movement("pick_pos_near", "linear")

        gripper.open()

        with ToolpathExecute(tp):
            tp.add_movement("pick_pos_near")
            tp.add_movement("pick_pos", "linear", max_speed=approach_speed)

        gripper.close()
        if not gripper.has_plate():
            raise Exception("Plate not grabbed!")

        with ToolpathExecute(tp):
            tp.add_movement("pick_pos")
            tp.add_movement("pick_pos_near", "linear", max_speed=approach_speed)
            tp.add_movement("pick_pos_up", "linear")

            if is_different_owner:
                tp.add_movement("pick_home")
                tp.add_movement("drop_home")

            tp.add_movement("drop_pos_up")
            tp.add_movement("drop_pos_near", "linear")
            tp.add_movement("drop_pos", "linear", max_speed=approach_speed)

        gripper.open()

        with ToolpathExecute(tp):
            tp.add_movement("drop_pos")
            tp.add_movement("drop_pos_near", "linear", max_speed=approach_speed)

        gripper.close()

        with ToolpathExecute(tp):
            tp.add_movement("drop_pos_near")
            tp.add_movement("drop_pos_up", "linear")
            tp.add_movement("drop_home")

    def move_list(self, data: list):
        self._logger.info("Move list called with: {}".format(data))

        arguments_to_copy = ["trajectory", "max_speed"]

        tp = Toolpath()

        for i, d in enumerate(data):
            if not "joints" in d:
                raise Exception("Mandatory \'joints\' key not found in {}".format(d))

            waypoint_label = "WP_{}".format(i)
            tp.add_waypoint(waypoint_label, d["joints"])

            arguments = {"label": waypoint_label}

            for a in arguments_to_copy:
                self._logger.debug("Checking argument {}".format(a))
                if a in d:
                    arguments[a] = d[a]
            self._logger.debug("Arguments now are: {}".format(arguments))

            tp.add_movement(**arguments)

        self.toolpath_load_and_execute(tp.toolpath)

    def approach_linear(self, position_name, start_height=0.1,  max_speed=0.05):
        """ Approach in a linear way to a defined position
            :param position_name: the name of the target position
            :param start_height: the height above the position at which start the linear phase
            :param max_speed: the maximum speed at which move in the linear phase
        """

        position = self.get_joints(position_name)
        position_above = self.get_joints(position_name, offset={"z": -start_height})

        moves = [{"joints": position_above},
                 {"joints": position, "trajectory": "linear", "max_speed": max_speed}]

        self.move_list(moves)

    def raise_vertically(self, height, max_speed=0.05):
        current_pos = self.get_angles()
        updated_pos = self._eva.calc_nudge(current_pos, "z", -height)

        moves = [{"joints": current_pos},
                 {"joints": updated_pos, "trajectory": "linear", "max_speed": max_speed}]

        self.move_list(moves)

    # # Test toolpath output
    # with open("test_toolpath.json", "w") as fp:
    #     self._logger.info("{}".format(tp.toolpath))
    #     json.dump(tp.toolpath, fp)
