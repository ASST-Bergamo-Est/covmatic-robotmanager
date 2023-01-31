# Save a robot position

from .config import Config
Config().pull("")

import os
from .robot_manager import Robot
import logging


logger = logging.getLogger(__name__)


class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


quit_requested = False
offset = {}
steps = [0.005, 0.001, 0.0005]
step_index = len(steps)-1

total_offset = {
    'x': 0,
    'y': 0,
    'z': 0,
    'rx': 0,
    'ry': 0,
    'rz': 0
}

initial_angles = []


def reset_offsets():
    global total_offset
    for t in total_offset:
        total_offset[t] = 0


def update_initial_angles_with_offset(r: Robot, offset: dict):
    global total_offset, initial_angles
    pos_offset = {}
    rot_offset = {}

    for o in offset:
        total_offset[o] += offset[o]

    print("Received offset: {}".format(offset))
    print("Total offset: {}".format(total_offset))

    for pos_id in ['x', 'y', 'z']:
        pos_offset[pos_id] = total_offset[pos_id]

    for rot_id in ['rx', 'ry', 'rz']:
        new_key = rot_id[1:]
        rot_offset[new_key] = total_offset[rot_id]

    print("Applying offset: {}; rotation: {}".format(pos_offset, rot_offset))
    new_angles = r._movement.update_joints_with_rotation(initial_angles, rot_offset)
    new_angles = r._movement.update_joints_with_offset(new_angles, pos_offset)

    return new_angles


def move_current_with_offset(r: Robot, offset):
    new_angles = update_initial_angles_with_offset(r, offset)
    r._movement.go_to_joints(new_angles, max_speed=0.01)


def quit_program(r, *args, **kwargs):
    global quit_requested
    quit_requested = True
    return {}


def step(*args, **kwargs):
    return steps[step_index]


def rstep(*args, **kwargs):
    return steps[step_index] * 5


def go_ahead(r, *args, **kwargs):
    move_current_with_offset(r, {'y': -step()})


def go_back(r, *args, **kwargs):
    move_current_with_offset(r, {'y': step()})


def go_right(r, *args, **kwargs):
    move_current_with_offset(r, {'x': -step()})


def go_left(r, *args, **kwargs):
    move_current_with_offset(r, {'x': step()})


def go_up(r, *args, **kwargs):
    move_current_with_offset(r, {'z': -step()})


def go_down(r, *args, **kwargs):
    move_current_with_offset(r, {'z': step()})


def rot_x(r, *args, **kwargs):
    move_current_with_offset(r, {'rx': rstep()})


def rot_bx(r, *args, **kwargs):
    move_current_with_offset(r, {'rx': -rstep()})


def rot_y(r, *args, **kwargs):
    move_current_with_offset(r, {'ry': rstep()})


def rot_by(r, *args, **kwargs):
    move_current_with_offset(r, {'ry': -rstep()})


def rot_z(r, *args, **kwargs):
    move_current_with_offset(r, {'rz': rstep()})


def rot_bz(r, *args, **kwargs):
    move_current_with_offset(r, {'rz': -rstep()})

def step_decrease(*args, **kwargs):
    global step_index
    if step_index < (len(steps)-1):
        step_index += 1


def step_increase(*args, **kwargs):
    global step_index
    if step_index > 0:
        step_index -= 1


def test_position(r: Robot, position_name, *args, **kwargs):
    new_angles = update_initial_angles_with_offset(r, offset)
    r.save_position(position_name, new_angles)
    r._movement.move_to_home_from_current(r._movement._positions.get_pos_owner(position_name))
    r._movement.move_to_position_from_current(position_name, 0.1)


def load_position(r: Robot, position_name, *args, **kwargs):
    global initial_angles
    reset_offsets()
    initial_angles = r._movement.get_joints(position_name)
    r.move_to_position(position_name, speed=0.05)


def save_position(r: Robot, position_name, *args, **kwargs):
    new_angles = update_initial_angles_with_offset(r, offset)
    r.save_position(position_name, new_angles)


actions = [
    [b'q', "quit program and save position", quit_program],
    [b'o', "go ahead", go_ahead],
    [b'l', "go back", go_back],
    [b'p', "go right", go_right],
    [b'i', "go left", go_left],
    [b'u', "go up", go_up],
    [b'j', "go down", go_down],
    [b'e', "rotate x positive", rot_x],
    [b'r', "rotate y positive", rot_y],
    [b't', "rotate z positive", rot_z],
    [b'd', "rotate x negative", rot_bx],
    [b'f', "rotate y negative", rot_by],
    [b'g', "rotate z negative", rot_bz],
    [b'a', "increase step", step_increase],
    [b'z', "decrease step", step_decrease],
    [b'x', "load position saved", load_position],
    [b's', "save position", save_position],
    [b'w', "test position", test_position]
]

def check_default_positions_exist_for_owner(r: Robot, owner, current_position):
    needed_positions = ["HOME", "DECK", "HMAX"]

    if current_position not in needed_positions:
        for p in needed_positions:
            default_position = "{}-{}".format(owner, p)
            try:
                r._movement._positions.get_joints(default_position)
            except Exception as e:
                print("Error received: {}".format(e))
                raise Exception(
                    "Position {} not calibrated; please calibrate it before any other position for robot {}".format(
                        default_position, owner))


def check_position_exist_and_load(r: Robot, position):
    global initial_angles
    cls()
    try:
        initial_angles = r._movement._positions.get_joints(position)
        answer = input("Saved position found! Do you want to move the robot to it? (y/n) ")
        if answer == "y":
            r._movement.move_to_position_from_current(position, 0.05)
    except Exception as e:
        print("Error found in retrieving position {}: {}".format(position, e))
        print("\n\nMove the robot manually to the desidered position than press enter")
        wait = input()
        initial_angles = r._movement.get_angles()

def cls():
    os.system('cls' if os.name=='nt' else 'clear')


def main_loop():
    global quit_requested, initial_angles

    getch = _Getch()

    robot = Robot(Config().eva_ip, Config().eva_token, Config().positions_filepath, logger)
    owner = input("Insert name of target robot: ")

    pos_name = input("Insert name of position for robot {}: ".format(owner))

    check_default_positions_exist_for_owner(robot, owner, pos_name)

    pos_name = "{}-{}".format(owner, pos_name)
    print("Actual position {}".format(pos_name))

    with robot._eva_helper.eva.lock():
        check_position_exist_and_load(robot, pos_name)

        while not quit_requested:
            print("Position: {}".format(pos_name))
            print("Step: {}mm".format(step()*1000))
            for action in actions:
                print("Press {} to {}".format(str(action[0]), action[1]))
            ch = getch()
            cls()

            for action in actions:
                if action[0] == ch:
                    action[2](robot, position_name=pos_name)
                    break
            else:
                print("Action not recognized!")

            print("Received {};".format(ch))
        try:
            robot._movement.move_to_home_from_current(robot._movement._positions.get_pos_owner(pos_name), 0.1)
        except Exception as e:
            print("Receive exception while trying to move home: {}".format(e))
            print("\n\nMove the robot manually to a safe position than press enter")
            wait = input()


def main():
    if Config().test_only:
        logger.info("Test only run, exiting...")
    else:
        main_loop()


if __name__ == '__main__':
    main()



