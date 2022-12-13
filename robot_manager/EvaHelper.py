from evasdk import Eva
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
        if not data:
            data = self.get_data()
        if data['global']['estop']:
            raise Exception("Emergency stop pressed. Please release it.")