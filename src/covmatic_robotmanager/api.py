import json
import logging

from flask import request
from flask_restful import Api, Resource
from . import __version__
from .robot_manager import RobotManager


class RobotManagerApi(Api):
    def __init__(self, *args, **kwargs):
        super(RobotManagerApi, self).__init__(*args, **kwargs)
        self._robot_manager = RobotManager()
        self.add_resource(Version, '/version', resource_class_args=(self._robot_manager,))
        self.add_resource(CheckAction, '/action/check/<string:action_id>', resource_class_args=(self._robot_manager,))
        self.add_resource(RequestAction, '/action/<string:action>/<string:machine>/<string:slot>/<string:plate_name>', resource_class_args=(self._robot_manager,))

    def shutdown(self):
        logging.getLogger().info("Api shutdown called")
        self._robot_manager.shutdown()


class RobotManagerResource(Resource):
    def __init__(self, robot_manager):
        super().__init__()
        self._robot_manager = robot_manager


class Version(RobotManagerResource):
    def get(self):
        return {
            'name': 'RobotManager server',
            'version': '{}'.format(__version__)
        }


class CheckAction(RobotManagerResource):
    def get(self, action_id):
        return self._robot_manager.check_action(action_id)


class RequestAction(RobotManagerResource):
    def post(self, action, machine, slot, plate_name):
        try:
            print("Received options: {}".format(request.get_json()))
        except TypeError as e:
            print("Got error: {}".format(e))
        action_id = self._robot_manager.action_request(action, machine, slot, plate_name)
        return {'action_id': action_id}
