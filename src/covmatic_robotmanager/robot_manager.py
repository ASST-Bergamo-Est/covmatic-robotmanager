import concurrent
from enum import Enum
from threading import Event, Thread

from .robot import Robot, RobotException
from .singleton import Singleton
from .config import Config
from queue import Queue
import logging
import uuid


class RobotManagerException(Exception):
    pass


class RobotManager(Singleton):
    def __init__(self, logger=logging.getLogger(__name__)):
        self._robot = Robot(eva_ip_address=Config().eva_ip,
                            token=Config().eva_token,
                            position_filepath=Config().positions_filepath)
        self._logger = logger
        self._logger.info("RobotManager initilized)")
        self._actions = []
        self._current_plate = None
        self._actions_queue = Queue()
        self._kill_event = Event()
        self._threads = []
        self.start_threads()

    def start_threads(self):
        for f in [self.action_processor_thread]:
            th = Thread(target=f, name=f.__name__)
            self._threads.append(th)
            self._logger.info("Starting thread {}".format(th.name))
            th.start()

    def action_request(self, action, machine, slot, plate_name, options=None):
        position = "{}-{}".format(machine, slot)
        self._logger.info("Requested action {} for {} plate {}".format(action, position, plate_name))
        action_id = str(uuid.uuid4())
        action_element = {
            'action': action,
            'position': position,
            'plate_name': plate_name,
            'id': action_id,
        }
        self._actions_queue.put(action_element)
        return action_id

    def shutdown(self):
        self._logger.info("Shutdown command received")
        self._kill_event.set()
        self._actions_queue.put({"action": "terminate"})
        for th in self._threads:
            self._logger.info("Joining thread {}".format(th.name))
            th.join()
        self._logger.info("Shutdown exiting")

    def action_scheduler(self):
        done_actions = []
        self._logger.info("Scheduler: actions are {}".format(self._actions))
        for i, a in enumerate(self._actions):
            print("\nevaluating {}".format(a))
            print("current_plate: {}".format(self._current_plate))

            if a["action"] == "pick" and self._current_plate is None:
                self._current_plate = a["plate_name"]
                self.execute_action(a)
                done_actions.append(a)

            if a["action"] == "drop" \
                    and a["plate_name"] == self._current_plate:
                print("Drop plate!")
                self.execute_action(a)
                self._current_plate = None
                done_actions.append(a)
            print("Ended cycle {}; actions: {}".format(i, self._actions))

        for da in done_actions:
            self._actions.remove(da)

    def execute_action(self, a):
        action = a["action"]
        position = a["position"]
        self._logger.info("Executing action {} position {}".format(action, position))
        try:
            if action == "pick":
                self._robot.pick_up_plate(position)
            elif action == "drop":
                self._robot.drop_plate(position)
            else:
                raise RobotManagerException("Action {} not implemented".format(action))
        except RobotException as e:
            self._logger.error("Error from robot during action: {}".format(e))
            self.error_handler()

    def action_processor_thread(self):
        self._logger.info("Entered action processor thread")
        while not self._kill_event.isSet():
            self._logger.info("action processor thread waiting for element")
            new_action = self._actions_queue.get()
            if new_action['action'] == "terminate":
                break
            if new_action['action'] == "pick":
                self._logger.info("Adding action in the beginning: {}".format(new_action))
                self._actions.insert(0, new_action)
            else:
                self._actions.append(new_action)
            self._logger.info("action processor thread elaborating element")
            self.action_scheduler()
        self._logger.info("action processor thread exiting")

    def check_action(self, action_id):
        self._logger.info("Checking action id {}".format(action_id))

        state = "pending"
        if self._actions_queue.empty() and self._is_action_finished(action_id):
            state = "finished"

        self._logger.info("Action id {} state {}".format(action_id, state))
        return {"state": state}

    def _is_action_finished(self, action_id):
        """ Check the actions array to know if the action id passed is finished """
        for a in self._actions:
            if a["id"] == action_id:
                return False
        return True

    def error_handler(self):
        """ This function should handle error in some way.
            for now we just set an internal state to avoid unwanted movement """
        self._logger.info("Error handling function")
        self._current_plate = "ERROR"


