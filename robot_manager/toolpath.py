import logging

MAX_SPEED = 0.25  # Default max speed

TRAJECTORIES = ["joint_space", "linear", "spline"]
DEFAULT_TRAJECTORY = "joint_space"


class Toolpath:
    def __init__(self, max_speed=MAX_SPEED):
        self._max_speed = max_speed
        self._toolpath = {}
        self._waypoints = []
        self._timeline = []
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
                "next_label_id": 3
            }

    @property
    def waypoints(self):
        return [w for w in self._waypoints]

    @property
    def timeline(self):
        return self._timeline

    def add_waypoint(self, label: str, joints: list, label_id: int = None):
        labels_id = [w["label_id"] for w in self._waypoints]
        labels_text = [w["label_text"] for w in self._waypoints]

        if label_id is None:
            label_id = max(labels_id, default=-1) + 1

        if label_id in labels_id:
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
            to_append = {
                "type": "home",
                "waypoint_id": index
            }
        else:
            to_append = {
                "type": "trajectory",
                "trajectory": trajectory,
                "waypoint_id": index,
            }
            if max_speed:
                to_append["max_speed"] = max_speed

        self._timeline.append(to_append)
        self._logger.debug("Timeline is {}".format(self._timeline))
