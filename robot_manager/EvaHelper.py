from evasdk import Eva, EvaError
import logging
from .singleton import Singleton


class EvaHelper(Singleton):
    _logger = logging.getLogger(__name__)
    _eva = None

    def connect(self, eva_ip_address, token):
        self._logger.info("Trying to connect to Eva ip {}...".format(eva_ip_address))
        self._eva = Eva(eva_ip_address, token)
        self._logger.info("Connected to Eva!")

    @property
    def eva(self):
        return self._eva

    def get_robot_info(self):
        return {"name": self._eva.name()["name"],
                "versions": self._eva.versions()}

    def get_data(self):
        data = self._eva.data_snapshot()
        return data

    def print_data(self):
        data = self.get_data()
        self._logger.info("Data:")
        for d in data:
            self._logger.info("{}: {}".format(d, data[d]))

    def check_data_emergency_stop(self, data=None):
        """ Check the robot data to know
            if the emergency button has been pressed
        """
        if not data:
            data = self.get_data()
        if data['global']['estop']:
            raise Exception("Emergency stop pressed. Please release it.")

    def check_and_clear_errors(self):
        """ Check for hard error and try to reset them.
            Must have lock.
        """
        try:
            self._eva.control_wait_for_ready()
        except EvaError as e:
            self._logger.info("Found robot in error state: {}. Trying to reset".format(e))
            self._eva.control_reset_errors()
            self._eva.control_wait_for_ready()
