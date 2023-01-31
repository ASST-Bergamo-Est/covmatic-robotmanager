# RobotManager
# ============
# a simple manager to control EVA robot and provide a safe interfate to be used by others.

from .config import Config
Config.pull(__doc__)

import logging
import sys
import multiprocessing
from flask import Flask
from waitress import serve

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
    serve(app, listen="*:{}".format(Config().port), expose_tracebacks=Config().debug_mode)
    # app.run(host='::', port=Config().port, debug=True, use_reloader=False)        # Werkezeug only for development


def main_loop():
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=start_app, args=(q,))
    logger.info("Starting server process...")
    p.start()
    logger.info("Server process {} is waiting for shutdown.".format(p.pid))
    token = q.get(block=True)
    logger.info("Terminating process {}".format(p.pid))
    p.terminate()
    logger.info("Exiting")


def main():
    if Config().test_only:
        logger.info("Test only run, exiting...")
    else:
        main_loop()


if __name__ == '__main__':
    sys.exit(main())
