""" Config module to manage file-based configuration

    original code: covmatic-localwebserver

"""
import argparse
import configargparse
import os
import logging
from .singleton import SingletonMeta


class Config(argparse.Namespace, metaclass=SingletonMeta):
    _logger = logging.getLogger(__name__)

    @classmethod
    def get_base_config_folder(cls):
        config_dir = os.path.join(os.path.expanduser("~"), ".covmatic")
        cls.create_directory(config_dir)
        return config_dir

    @classmethod
    def get_config_file_path(cls) -> str:
        return os.path.join(cls.get_base_config_folder(), "robotmanager.conf")

    @classmethod
    def get_default_positions_file_path(cls) -> str:
        return os.path.join(cls.get_base_config_folder(), "positions.json")

    @classmethod
    def parse(cls, description):
        cls._logger.info("Checking for arguments in config file {}".format(cls.get_config_file_path()))
        parser = configargparse.ArgParser(description=description,
                                          default_config_files=[cls.get_config_file_path()],
                                          add_config_file_help=True)
        parser.add_argument('-E', '--eva-ip', metavar='address',  required=True, help="Eva hostname or ip address")
        parser.add_argument('-T', '--eva-token', metavar='token', required=True, help="Eva token")
        parser.add_argument('-P', '--port', type=int, metavar="port", default=5000, help="Server port for requests")
        parser.add_argument('--positions-filepath', metavar="path", type=str, default=cls.get_default_positions_file_path(), help="JSON File to save positions data")
        parser.add_argument('--test-only', dest="test_only", action="store_true", help="enable test-only execution")
        parser.add_argument('--debug-mode', dest="debug_mode", action="store_true", help="enable debug mode to show unhandled exceptions.")
        return cls.reset(**parser.parse_known_args()[0].__dict__)

    @classmethod
    def pull(cls, description):
        if not cls().__dict__:
            cls.parse(description)
        return cls()

    @classmethod
    def create_directory(cls, directory):
        try:
            os.makedirs(directory)
            cls._logger.info("Created directory {}".format(directory))
        except OSError:
            cls._logger.debug("Directory {} already existing".format(directory))
