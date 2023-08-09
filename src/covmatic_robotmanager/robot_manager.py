from threading import Event, Thread, Lock
from .robot import Robot, RobotException
from .singleton import SingletonMeta
from .config import Config
from queue import Queue
import logging
import uuid


class RobotManagerException(Exception):
    pass


class RobotManager(metaclass=SingletonMeta):
    def __init__(self, logger=logging.getLogger("robotmanager.robotmanager"), start_thread: bool = True):
        self._robot = Robot(eva_ip_address=Config().eva_ip,
                            token=Config().eva_token,
                            position_filepath=Config().positions_filepath)
        self._logger = logger
        self._logger.info("RobotManager initilized)")
        self._actions = []
        self._current_plate = None
        self._pick_drop_same_machine = False
        self._kill_event = Event()
        self._threads = []
        self._actions_lock = Lock()
        self._start_execution_queue = Queue()
        if start_thread:
            self.start_threads()

    @property
    def _pending_actions(self):
        with self._actions_lock:
            return list(filter(lambda x: x['state'] == 'pending', self._actions))

    def start_threads(self):
        for f in [self.action_processor_thread]:
            th = Thread(target=f, name=f.__name__)
            self._threads.append(th)
            self._logger.info("Starting thread {}".format(th.name))
            th.start()

    @staticmethod
    def get_position(machine: str, slot: str) -> str:
        return "{}-{}".format(machine, slot)

    @staticmethod
    def get_machine_from_position(position: str) -> str:
        return position.split('-')[0]

    def action_request(self, action, machine, slot, plate_name, options=None):
        position = self.get_position(machine, slot)
        self._logger.info("Requested action {} for {} plate {}".format(action, position, plate_name))
        action_id = str(uuid.uuid4())
        action_element = {
            'action': action,
            'position': position,
            'plate_name': plate_name,
            'id': action_id,
            'state': 'pending'
        }
        if action == "pick" or action == "terminate":
            self._logger.info("action request adding action in the beginning: {}".format(action_element))
            with self._actions_lock:
                self._actions.insert(0, action_element)
        else:
            self._logger.info("action request appending action: {}".format(action_element))
            with self._actions_lock:
                self._actions.append(action_element)
        self._start_execution_queue.put(True)
        return action_id

    def shutdown(self):
        self._logger.info("Shutdown command received")
        self._kill_event.set()
        self.action_request("terminate", "", "", "")
        for th in self._threads:
            self._logger.info("Joining thread {}".format(th.name))
            th.join()
        self._logger.info("Shutdown exiting")

    def action_scheduler(self):
        while True:
            pending_actions = self._pending_actions
            self._logger.info("Scheduler: actions are {}".format(self._actions))
            self._logger.info("Scheduler: pending actions are {}".format(pending_actions))

            pick_plate_names = list(map(lambda y: y['plate_name'], filter(lambda x: x['action'] == 'pick', pending_actions)))
            drop_plate_names = list(map(lambda y: y['plate_name'], filter(lambda x: x['action'] == 'drop', pending_actions)))

            a = None
            self._logger.debug("Current plate: {}".format(self._current_plate))
            if self._current_plate is None:         # We can pick a plate
                for p in pick_plate_names:
                    if p in drop_plate_names:
                        self._logger.debug("Plate {} found in pick and drop.".format(p))
                        a_pick = list(filter(lambda x: x['action'] == 'pick' and x['plate_name'] == p, pending_actions))[0]
                        a_drop = list(filter(lambda x: x['action'] == 'drop' and x['plate_name'] == p, pending_actions))[0]
                        a = a_pick

                        self._pick_drop_same_machine = (self.get_machine_from_position(a_pick['position']) == self.get_machine_from_position(a_drop['position']))
                        self._logger.debug("Pick drop same machine set to: {}".format(self._pick_drop_same_machine))
                        self._current_plate = p

                        break
            else:
                if self._current_plate in drop_plate_names:
                    a = list(filter(lambda x: x['action'] == 'drop' and x['plate_name'] == self._current_plate, pending_actions))[0]
                    self._current_plate = None

            if a is None:
                break

            self._logger.info("Scheduler executing action: {}".format(a))
            try:
                self.execute_action(a)

                self._logger.info("Removing action {} from list".format(a))
                self.mark_action_as_finished(a)

            except Exception as e:
                self._logger.error("handling error {}".format(e))
                self.handle_error(a)

    def execute_action(self, a):
        action = a["action"]
        position = a["position"]
        self._logger.info("Executing action {} position {}".format(action, position))
        self._logger.info("Pick Drop same machine is: {}".format(self._pick_drop_same_machine))
        try:
            if action == "pick":
                self._robot.pick_up_plate(position, self._pick_drop_same_machine)
            elif action == "drop":
                self._robot.drop_plate(position, self._pick_drop_same_machine)
                self._pick_drop_same_machine = False
            else:
                raise RobotManagerException("Action {} not implemented".format(action))
        except RobotException as e:
            raise RobotManagerException("Error during robot action: {}".format(e))

    def mark_action_as_finished(self, action):
        with self._actions_lock:
            action["state"] = "finished"

    def action_processor_thread(self):
        self._logger.info("APT Entered action processor thread")
        while not self._kill_event.isSet():
            self._start_execution_queue.get()       # Wait for the signal to start

            if self._actions[0]['action'] == "terminate":
                self._logger.debug("APT Terminate action received")
                break

            self.action_scheduler()
        self._logger.info("APT action processor thread exiting")

    def check_action(self, action_id):
        self._logger.info("Checking action id {}".format(action_id))

        state = self._action_get_state(action_id)

        self._logger.info("Action id {} state {}".format(action_id, state))
        return {"state": state}

    def _get_action_with_id(self, action_id):
        found_action = None
        with self._actions_lock:
            for a in self._actions:
                if a["id"] == action_id:
                    found_action = a

        if found_action is None:
            raise RobotManagerException("Action with id {} not found.".format(action_id))
        return found_action

    def _action_get_state(self, action_id):
        self._logger.debug("Action get state for id {}".format(action_id))
        state = self._get_action_with_id(action_id)["state"]

        self._logger.debug("action id {} state {}".format(action_id, state))
        self._logger.debug("Action get state actions are: {}".format(self._actions))
        return state

    def handle_error(self, a):
        """ This function will set the 'aborted' state on the passed action;
            if the action is 'pick' it will set the 'aborted' state also on linked drop action
        """

        with self._actions_lock:
            a['state'] = 'aborted'
        self._logger.info("Handle error actions are: {}".format(self._actions))

        if a['action'] == 'pick':
            with self._actions_lock:
                drop_action = list(filter(lambda x: x['action'] == 'drop' and x['plate_name'] == a['plate_name'], self._actions))[0]
                self._logger.info("Found drop action to abort: {}".format(drop_action))
                drop_action['state'] = 'aborted'

        self._current_plate = None
