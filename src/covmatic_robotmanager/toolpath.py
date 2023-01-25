import logging

from .EvaHelper import EvaHelper
from contextlib import nullcontext

MAX_SPEED = 0.25  # Default max speed

TRAJECTORIES = ["joint_space", "linear", "pass-through"]
DEFAULT_TRAJECTORY = "joint_space"


class Toolpath:
    def __init__(self, max_speed=MAX_SPEED):
        self._max_speed = max_speed or MAX_SPEED
        self._toolpath = {}
        self._timeline = []
        self._waypoints = []
        self.clear_movements()
        self._logger = logging.getLogger(__name__)

    @property
    def toolpath(self):
        return {
            "metadata": self.metadata,
            "waypoints": self.waypoints,
            "timeline": self.timeline
        }

    @property
    def metadata(self) -> dict:
        return {
                "version": 2,
                "default_max_speed": self._max_speed,
                "payload": 0,
                "analog_modes": {
                    "i0": "voltage",
                    "i1": "voltage",
                    "o0": "voltage",
                    "o1": "voltage"
                },
                "next_label_id": self.next_label_id
            }

    @property
    def next_label_id(self) -> int:
        return max(self.labels_id, default=-1) + 1

    @property
    def waypoints(self):
        return [w for w in self._waypoints]

    @property
    def timeline(self):
        return self._timeline

    @property
    def labels_id(self) -> list:
        return [w["label_id"] for w in self._waypoints]

    def add_waypoint(self, label: str, joints: list, label_id: int = None):
        labels_text = [w["label_text"] for w in self._waypoints]

        if label_id is None:
            label_id = self.next_label_id

        if label_id in self.labels_id:
            raise Exception("Label id {} for waypoint {} already present in list: {}".format(label_id, label, labels_id))

        if label in labels_text:
            raise Exception("Label text {} already present in list: {}".format(label, labels_text))

        self._waypoints.append({
            "label_id": label_id,
            "label_text": label,
            "joints": joints
        })
        self._logger.debug("Now waypoint contains: {}".format(self._waypoints))

    @property
    def _is_timeline_empty(self):
        return len(self._timeline) == 0

    def add_movement(self, label: str, trajectory: str = DEFAULT_TRAJECTORY, max_speed: float = None):
        if trajectory not in TRAJECTORIES:
            raise Exception("Trajectory {} not found in {}".format(trajectory, TRAJECTORIES))

        for i, w in enumerate(self._waypoints):
            if w["label_text"] == label:
                waypoint = w
                index = i
                break
        else:
            raise Exception("Waypoint label {} not found".format(label))

        self._logger.info("Adding waypoint {} with index {}".format(waypoint, index))

        if self._is_timeline_empty:
            self._logger.info("Timeline is empty!!")
            to_append = {
                "type": "home",
                "waypoint_id": index
            }
        else:
            to_append = {
                "type": "trajectory",
                "waypoint_id": index
            }

            if trajectory == "pass-through":
                to_append["pass_through"] = True
            elif len(self._timeline) > 0 and self._timeline[-1].get("pass_through", False):
                to_append["trajectory"] = "spline"
            else:
                to_append["trajectory"] = trajectory
            if max_speed:
                to_append["max_speed"] = max_speed

        self._logger.info("Appending {}".format(to_append))
        self._timeline.append(to_append)
        self._logger.debug("Timeline is {}".format(self._timeline))

    def clear_movements(self):
        self._timeline = []


class ToolpathExecute:
    def __init__(self, tp: Toolpath, logger=logging.getLogger(__name__)):
        self._eh = EvaHelper()
        self._tp = tp
        self._logger = logger

    def __enter__(self) -> Toolpath:
        self._tp.clear_movements()
        return self._tp

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.toolpath_load_and_execute()

    def toolpath_load_and_execute(self):
        with self._eh.eva.lock() if not self._eh.is_locked() else nullcontext():
            self._eh.check_data_emergency_stop()
            self._eh.check_and_clear_errors()

            self._logger.info("Saving toolpath: {}".format(self._tp.toolpath))
            self._eh.eva.toolpaths_use(self._tp.toolpath)

            self._logger.info("Going to home")
            self._eh.eva.control_home()

            self._logger.info("Running toolpath...")
            self._eh.eva.control_run(loop=1)
            self._logger.info("Finished")
