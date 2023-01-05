# RobotManager
# ============
# a simple manager to control EVA robot and provide a safe interfate to be used by others.

import logging
import time

from flask import Flask, request

from .api import RobotManagerApi
from .robot_manager import RobotManager
from . import __version__

logger = logging.getLogger(__name__)
logger.info("Starting version {}".format(__version__))


class RobotManagerApp(Flask):
    def __init__(self, name=__name__, *args, **kwargs):
        super(RobotManagerApp, self).__init__(name, *args, **kwargs)
        RobotManagerApi().init_app(self)


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


if __name__ == '__main__':
    # rm = RobotManager()
    # rm.
    app = RobotManagerApp()

    @app.route('/shutdown', methods=['GET'])
    def shutdown():
        shutdown_server()
        return "Server is shutting down..."

    app.run(host='::', port=5000, debug=True)




