# Module to handle positions
import json
import os
import logging


class Positions:
    def __init__(self,
                 positions_file_path: str,
                 logger=logging.getLogger(__name__)):
        self._logger = logger
        self._abs_path = os.path.abspath(positions_file_path)
        self._logger.info("Checking path {}...".format(self._abs_path))

        if not os.path.exists(self._abs_path):
            raise Exception("Position file passed must exist: {}".format(self._abs_path))

        with open(self._abs_path, "r") as fp:
            self._positions = json.load(fp)

        self._logger.debug("Loaded positions: {}".format(self._positions))

    def save(self, name, field, data):
        self._logger.info("Saving position name {} field {} data {}".format(name, field, data))
        if not name in self._positions:
            self._logger.info("Creating position {}".format(name))
            self._positions[name] = {}
        self._positions[name][field] = data
        self._save_positions()

    def save_joints(self, name, data):
        self.save(name, "joints", data)

    def save_xyz(self, name, data):
        self.save(name, "xyz", data)

    def get_position(self, name: str):
        self._logger.info("Requested position {}".format(name))
        if name in self._positions:
            return self._positions[name]
        raise Exception("Position {} not found.".format(name))

    def get_joints(self, name):
        return self.get_position(name)["joints"]

    def get_xyz(self, name):
        return self.get_position(name)["xyz"]

    def _save_positions(self):
        self._logger.info("Saving positions to file {}".format(self._abs_path))
        with open(self._abs_path, "w") as fp:
            json.dump(self._positions, fp)

    @staticmethod
    def get_pos_owner(name: str):
        return name.split("-")[0]
