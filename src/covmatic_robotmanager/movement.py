# Movement class to manage approaching and moving of robot
import logging
import math

from .gripper import EvaGripper
from .positions import Positions
from .EvaHelper import EvaHelper
from .toolpath import Toolpath, ToolpathExecute
from .utils import rad2deg

MAX_SPEED = 0.25       # Max speed in m/s

EVA_TCP = {
    "offsets": {"x": 0, "y": 0, "z": 0.09},
    "radius": 0.07,
    "rotations": {"x": 0, "y": 0, "z": 0}}


class MovementException(Exception):
    pass


class Movement:
    def __init__(self, position_filepath: str, logger=logging.getLogger(__name__)):
        self._eva = EvaHelper().eva
        self._positions = Positions(position_filepath)
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

    def save_position(self, name, joints=None):
        if not joints:
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
        self._eva.control_go_to(self.get_joints(position_name, offset=offset), max_speed=speed)

    def go_to_joints(self, joints, max_speed=None):
        self._eva_helper.check_data_emergency_stop()
        self._eva.control_go_to(joints, max_speed=max_speed)

    def get_joints_from_updated_position(self, name, offset: dict):
        self._logger.info("Updating position {}".format(name))

        joints = self._positions.get_joints(name)

        for o in offset:
            self._logger.debug("Updating offset {} with value: {}".format(o, offset[o]))
            self._logger.debug("Old joints: {}".format(joints))
            joints = self._eva.calc_nudge(joints, direction=o, offset=offset[o])
            self._logger.debug("New joints: {}".format(joints))
        return joints

    def get_joints(self, position_name, offset: dict = None, rotate: dict = None):
        joints = self._positions.get_joints(position_name)
        if rotate:
            joints = self.update_joints_with_rotation(joints, rotate)
        if offset:
            joints = self.update_joints_with_offset(joints, offset)

        return joints

    def update_joints_with_offset(self, joints, offset: dict):
        for o in offset:
            self._logger.debug("Updating offset {} with value: {}".format(o, offset[o]))
            self._logger.debug("Old joints: {}".format(joints))
            joints = self._eva.calc_nudge(joints, direction=o, offset=offset[o])
            self._logger.debug("New joints: {}".format(joints))
        return joints

    def update_joints_with_rotation(self, joints, rotate: dict):
        for r in rotate:
            self._logger.info("Updating rotate {} with value: {}".format(r, rotate[r]))
            self._logger.info("Old joints: {}".format(joints))
            joints = self._eva.calc_rotate(joints, axis=r, offset=rotate[r], tcp_config=EVA_TCP)
            self._logger.info("New joints: {}".format(joints))
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
        if raising_height > 0:
            raising_height = 0
        self._logger.info("We've to raise of {}".format(raising_height))
        return raising_height

    def toolpath_raise_and_detach(self, tp, joints, z_amount: float, z_step: float, rotation_amount=0.005, max_speed=None):
        steps = math.floor(z_amount/z_step)
        movement_names = []
        waypoint_base_name = "{}".format(tp.next_label_id)

        for i in range(steps):
            waypoint_name = "WP{}-STEP{}".format(waypoint_base_name, i)
            updated_joints = self.update_joints_with_offset(joints, offset={"z": (-z_step*i)})
            tp.add_waypoint("{}".format(waypoint_name), updated_joints)
            tp.add_waypoint("{}a".format(waypoint_name), self.update_joints_with_rotation(updated_joints, {"x": rotation_amount}))
            tp.add_waypoint("{}b".format(waypoint_name), self.update_joints_with_rotation(updated_joints, {"x": -rotation_amount}))

            tp.add_movement(waypoint_name, max_speed=max_speed)
            tp.add_movement("{}a".format(waypoint_name), max_speed=max_speed)
            tp.add_movement("{}b".format(waypoint_name), max_speed=max_speed)
            tp.add_movement(waypoint_name, max_speed=max_speed)

    def test_position(self, position_name, max_speed):

        approach_speed = 0.025

        pos_raising_height = self.get_raising_height(position_name)
        owner = self._positions.get_pos_owner(position_name)
        home_pos = self.get_joints("{}-HOME".format(owner))

        self._eva_helper.check_data_emergency_stop()

        tp = Toolpath(max_speed=max_speed)

        tp.add_waypoint("home", home_pos)
        tp.add_waypoint("pos_up", self.get_joints(position_name, offset={"z": pos_raising_height}))
        tp.add_waypoint("pos", self.get_joints(position_name))

        with ToolpathExecute(tp):
            tp.add_movement("home")
            tp.add_movement("pos_up", "linear")
            tp.add_movement("pos", "linear", max_speed=approach_speed)

    def move_to_home_from_current(self, owner, max_speed=None):
        approach_speed = 0.025

        home_pos = self.get_joints("{}-HOME".format(owner))
        current_pos_name = "{}-CURRENT".format(owner)

        self.save_position(current_pos_name)

        pos_raising_height = self.get_raising_height(current_pos_name)

        self._eva_helper.check_data_emergency_stop()

        tp = Toolpath(max_speed=max_speed)

        tp.add_waypoint("home", home_pos)
        tp.add_waypoint("pos_up", self.get_joints(current_pos_name, offset={"z": pos_raising_height}))
        tp.add_waypoint("pos", self.get_joints(current_pos_name))

        with ToolpathExecute(tp):
            tp.add_movement("pos")
            tp.add_movement("pos_up", "linear", max_speed=approach_speed)
            tp.add_movement("home", "linear")

    def move_to_position_from_current(self, position: str, max_speed=None):
        approach_speed = 0.025
        owner = self._positions.get_pos_owner(position)
        current_pos_name = "{}-CURRENT".format(owner)

        self.save_position(current_pos_name)

        current_pos_raising_height = self.get_raising_height(current_pos_name)
        target_pos_raising_height = self.get_raising_height(position)

        self._eva_helper.check_data_emergency_stop()

        tp = Toolpath(max_speed=max_speed)

        tp.add_waypoint("current", self.get_joints(current_pos_name))
        tp.add_waypoint("current_up", self.get_joints(current_pos_name, offset={"z": current_pos_raising_height}))
        tp.add_waypoint("target_up", self.get_joints(position, offset={"z": target_pos_raising_height}))
        tp.add_waypoint("target", self.get_joints(position))

        with ToolpathExecute(tp):
            tp.add_movement("current")
            tp.add_movement("current_up", "linear", max_speed=approach_speed)
            tp.add_movement("target_up", "linear", max_speed=max_speed)
            tp.add_movement("target", "linear", max_speed=approach_speed)

    def transfer_plate(self, source_pos, dest_pos, max_speed=None, home_after=True, detach_plate=False):
        self.pick_plate(source_pos, max_speed=max_speed, detach_plate=detach_plate)
        self.drop_plate(dest_pos, max_speed=max_speed, home_after=home_after)

    def pick_plate(self, source_pos, max_speed=None, detach_plate=False):

        gripper = EvaGripper()

        near_height = -0.01
        grip_height = 0.008
        approach_speed = 0.025

        source_raising_height = self.get_raising_height(source_pos)

        source_owner = self._positions.get_pos_owner(source_pos)
        source_home_pos_name = "{}-HOME".format(source_owner)
        source_home_pos = self.get_joints(source_home_pos_name)
        pick_pos = self.get_joints(source_pos, offset={"z": grip_height})

        self._eva_helper.check_data_emergency_stop()

        with self._eva.lock():
            self._eva_helper.check_and_clear_errors()

        tp = Toolpath(max_speed=max_speed)
        tp.add_waypoint("pick_home", source_home_pos)
        tp.add_waypoint("pick_pos_up", self.get_joints(source_pos, offset={"z": source_raising_height}))
        tp.add_waypoint("pick_pos_near", self.get_joints(source_pos, offset={"z": near_height}))
        tp.add_waypoint("pick_pos", pick_pos)

        gripper.close()

        with ToolpathExecute(tp):
            tp.add_movement("pick_home")
            tp.add_movement("pick_pos_up", "linear")
            tp.add_movement("pick_pos_near", "linear")

        gripper.open()

        with ToolpathExecute(tp):
            tp.add_movement("pick_pos_near")
            tp.add_movement("pick_pos", "linear", max_speed=approach_speed)

        gripper.close()

        with ToolpathExecute(tp):
            if detach_plate:
                self.toolpath_raise_and_detach(tp, pick_pos, 0.003, 0.001, max_speed=approach_speed)
            else:
                tp.add_movement("pick_pos")
            tp.add_movement("pick_pos_near", "linear", max_speed=approach_speed)

        if not gripper.has_plate():
            gripper.open()
            with ToolpathExecute(tp):
                tp.add_movement("pick_pos_near", )
                tp.add_movement("pick_pos_up", "linear", max_speed=approach_speed)
            gripper.close()
            with ToolpathExecute(tp):
                tp.add_movement("pick_pos_up")
                tp.add_movement("pick_home", "linear")

            raise MovementException("Plate not grabbed!")

        with ToolpathExecute(tp):
            tp.add_movement("pick_pos_near")
            tp.add_movement("pick_pos_up", "linear")
            tp.add_movement("pick_home", "linear")

    def drop_plate(self, dest_pos, max_speed=None, home_after=True):

        gripper = EvaGripper()

        near_height = -0.01
        grip_height = 0.008
        approach_speed = 0.025

        dest_raising_height = self.get_raising_height(dest_pos)
        dest_owner = self._positions.get_pos_owner(dest_pos)
        dest_home_pos_name = "{}-HOME".format(dest_owner)
        dest_home_pos = self.get_joints(dest_home_pos_name)

        self._eva_helper.check_data_emergency_stop()

        with self._eva.lock():
            self._eva_helper.check_and_clear_errors()

        tp = Toolpath(max_speed=max_speed)
        tp.add_waypoint("drop_home", dest_home_pos)
        tp.add_waypoint("drop_pos_up", self.get_joints(dest_pos, offset={"z": dest_raising_height}))
        tp.add_waypoint("drop_pos_near", self.get_joints(dest_pos, offset={"z": near_height}))
        tp.add_waypoint("drop_pos", self.get_joints(dest_pos, offset={"z": grip_height}))

        if home_after:
            tp.add_waypoint("home", self.get_joints("HOME"))

        with ToolpathExecute(tp):
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
            tp.add_movement("drop_home", "linear")
            if home_after:
                tp.add_movement("home")

