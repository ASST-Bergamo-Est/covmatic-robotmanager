# RobotManager
# ============
# a simple manager to control EVA robot and provide a safe interfate to be used by others.
import os
import sys

import requests

from .config import Config
Config.pull(__doc__)

import logging
from flask import Flask, request

import multiprocessing

from . import __version__
from .api import RobotManagerApi


logger = logging.getLogger(__name__)
logger.info("Starting version {}".format(__version__))


class RobotManagerApp(Flask):
    def __init__(self, name=__name__, *args, **kwargs):
        super(RobotManagerApp, self).__init__(name, *args, **kwargs)
        self._api = RobotManagerApi()
        self._api.init_app(self)

    def shutdown(self):
        self._api.shutdown()


def start_app(terminate_queue: multiprocessing.Queue) -> None:
    app = RobotManagerApp()

    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        logger.info("Shutting down app...")
        app.shutdown()
        logger.info("Releasing process for shutdown")
        terminate_queue.put("")
        return "Shutdown complete"

    app.run(host='::', port=Config().port, debug=False)


def main():
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=start_app, args=(q,))
    logger.info("Starting server process...")
    p.start()
    logger.info("Server process {} is waiting for shutdown.".format(p.pid))

    if Config().test_only:
        logger.info("Test only run: requesting shutdown")
        requests.post('http://localhost:{}/shutdown'.format(Config().port))

    token = q.get(block=True)
    logger.info("Terminating process {}".format(p.pid))
    p.terminate()
    logger.info("Exiting")


if __name__ == '__main__':
    sys.exit(main())
