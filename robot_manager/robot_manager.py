# RobotManager
# ============
# a simple manager to control EVA robot and provide a safe interfate to be used by others.

import logging
import time

from evasdk import Eva
from . import __version__


logger = logging.getLogger(__name__)


class Robot:
    def __init__(self, eva_ip_address, token, logger: logging.getLogger(__name__)):
        self._eva_ip_address = eva_ip_address
        self._token = token
        self._logger = logger
        self._eva = None

    def connect(self):
        logger.info("Config IP Address: {}".format(self._eva_ip_address))
        logger.info("Attempting to connect to robot...")
        self._eva = Eva(self._eva_ip_address, self._token)
        logger.info("Connected to Eva {} with API version {}".format(
            self._eva.name()["name"],
            self._eva.versions()))

    def test_gripper(self):
        self._logger.info("Trying to acquire lock")
        with self._eva.lock():
            self._logger.info("Lock acquired")
            for _ in range(6):
                if self._eva.gpio_get("ee_d0", "output"):
                    self._eva.gpio_set("ee_d0", False)
                    self._eva.gpio_set("ee_d1", True)
                else:
                    self._eva.gpio_set("ee_d1", False)
                    self._eva.gpio_set("ee_d0", True)
                time.sleep(0.5)
        self._logger.info("Lock released")

