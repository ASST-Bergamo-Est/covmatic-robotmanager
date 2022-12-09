# Module to handle positions
import json
import os
import logging

POSITIONS_FILE = 'positions.json'


class Positions:
    def __init__(self, positions_file_path: str = POSITIONS_FILE, logger=logging.getLogger(__name__)):
        self._logger = logger

        self._abs_path = os.path.abspath(positions_file_path)
        self._logger.info("Checking path {}...".format(self._abs_path))

        if not os.path.exists(self._abs_path):
            raise Exception("Position file passed must exist: {}".format(self._abs_path))

        with open(self._abs_path, "r") as fp:
            self._positions = json.load(fp)

        self._logger.info("Loaded positions: {}".format(self._positions))

    def get_position(self, name: str):
        self._logger.info("Requested position {}".format(name))
        if name in self._positions:
            return self._positions[name]

    def save(self, forward_kinematics_pos, name):
        self._logger.info("Saving position {} with name {}".format(forward_kinematics_pos, name))
        self._positions[name] = forward_kinematics_pos
        self._save_positions()

    def _save_positions(self):
        self._logger.info("Saving positions to file {}".format(self._abs_path))
        with open(self._abs_path, "w") as fp:
            json.dump(self._positions, fp)
