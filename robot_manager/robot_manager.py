from enum import Enum

from .robot import Robot
from .singleton import Singleton
from . import EVA_IP_ADDRESS, EVA_TOKEN
from queue import Queue
import logging


class RobotManagerException(Exception):
    pass


class RobotManager(Singleton):
    def __init__(self, logger=logging.getLogger(__name__)):
        self._robot = Robot(eva_ip_address=EVA_IP_ADDRESS, token=EVA_TOKEN)
        self._logger = logger
        self._logger.info("RobotManager initilized)")
        self._actions = []
        self._current_plate = None

    def action_request(self, action, machine, slot, plate_name, options=None):
        position = "{}-{}".format(machine, slot)
        self._logger.info("Requested action {} for {} plate {}".format(action, position, plate_name))
        action_id = "action_id"
        self._actions.append({
            'action': action,
            'position': position,
            'plate_name': plate_name,
            'id': action_id,
        })
        self.action_scheduler()
        return action_id
        # if action == "pick":
        #     self._robot.pick_up_plate(position, plate_name)
        # elif action == "drop":
        #     self._robot.drop_plate(position, plate_name)
        # else:
        #     raise RobotManagerException("Action {} not found".format(action))
        # return plate_name       # returning plate name as id

    def action_scheduler(self):
        done_actions = []
        for i, a in enumerate(self._actions):
            print("\nevaluating {}".format(a))
            print("current_plate: {}".format(self._current_plate))

            if a["action"] == "pick" and self._current_plate is None:
                print("action is pick")
                self._current_plate = a["plate_name"]
                self._robot.pick_up_plate(a["position"], a["plate_name"])
                done_actions.append(a)
                # print("Dropped {}; now actions are: {}".format(a, self._actions))

            if a["action"] == "drop" \
                    and a["plate_name"] == self._current_plate:
                print("Drop plate!")
                self._robot.drop_plate(a["position"], a["plate_name"])
                self._current_plate = None
                done_actions.append(a)
            print("Ended cycle {}; actions: {}".format(i, self._actions))

        for da in done_actions:
            self._actions.remove(da)
