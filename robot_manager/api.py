import json

from flask import request
from flask_restful import Api, Resource
from . import __version__
from .robot_manager import RobotManager

robot_manager = RobotManager()


class RobotManagerApi(Api):
    def __init__(self, *args, **kwargs):
        super(RobotManagerApi, self).__init__(*args, **kwargs)
        self.add_resource(Version, '/version')
        self.add_resource(CheckAction, '/action/check/<string:action_id>')
        self.add_resource(RequestAction, '/action/<string:action>/<string:machine>/<string:slot>/<string:plate_name>')

    @staticmethod
    def shutdown():
        robot_manager.shutdown()



class Version(Resource):
    def get(self):
        return {
            'name': 'RobotManager server',
            'version': '{}'.format(__version__)
        }


class CheckAction(Resource):
    def get(self, action_id):
        return robot_manager.check_action(action_id)


class RequestAction(Resource):
    def post(self, action, machine, slot, plate_name):
        try:
            print("Received options: {}".format(request.get_json()))
        except TypeError as e:
            print("Got error: {}".format(e))
        action_id = robot_manager.action_request(action, machine, slot, plate_name)
        return {'action_id': action_id}
