import logging
import time

from .EvaHelper import EvaHelper

GRIPPER_HAS_PLATE_LOW_THRESHOLD = 1.0
GRIPPER_HAS_PLATE_HIGH_THRESHOLD = 5.0


class EvaGripper:
    def __init__(self, logger=logging.getLogger(__name__)):
        self._eva = EvaHelper().eva
        self._logger = logger

    def open(self):
        with self._eva.lock():
            self._eva.gpio_set("ee_d0", False)
            self._eva.gpio_set("ee_d1", True)
            time.sleep(0.1)
            self._eva.gpio_set("ee_d1", False)

    def close(self):
        with self._eva.lock():
            self._eva.gpio_set("ee_d1", False)
            self._eva.gpio_set("ee_d0", True)
            time.sleep(0.1)
            self._eva.gpio_set("ee_d0", False)

    def has_plate(self) -> bool:
        self._logger.info("Checking gripper has plate")
        for i in range(3):
            gripper_analog_feedback = self._eva.data_snapshot()['global.inputs']['ee_a0']
            self._logger.info("Gripper analog feedback: {}".format(gripper_analog_feedback))
            if GRIPPER_HAS_PLATE_HIGH_THRESHOLD > gripper_analog_feedback > GRIPPER_HAS_PLATE_LOW_THRESHOLD:
                return True
            time.sleep(0.1)
            self._logger.info("Gripper analog feedback out of range for {} times".format(i+1))
        return False

