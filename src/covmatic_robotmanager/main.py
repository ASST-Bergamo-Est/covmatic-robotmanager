# RobotManager
# ============
# a simple manager to control EVA robot and provide a safe interfate to be used by others.
import os
import time
from typing import Optional
from . import __version__
from .config import Config
Config.pull(__doc__)

import logging
import sys
import multiprocessing
from flask import Flask
from waitress import serve

from .api import RobotManagerApi

main_logger = logging.getLogger()
main_logger.level = logging.DEBUG


class RobotManagerApp(Flask):
    def __init__(self, name=__name__, *args, **kwargs):
        super(RobotManagerApp, self).__init__(name, *args, **kwargs)
        self._api = RobotManagerApi()
        self._api.init_app(self)

    def shutdown(self):
        self._api.shutdown()


def start_app(terminate_queue: multiprocessing.Queue) -> None:
    logger_setup()
    main_logger.info("Starting version {}".format(__version__))

    app = RobotManagerApp()

    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        main_logger.info("Shutting down app...")
        app.shutdown()
        main_logger.info("Releasing process for shutdown")
        terminate_queue.put("")
        return "Shutdown complete"
    serve(app, listen="*:{}".format(Config().port), expose_tracebacks=Config().debug_mode)
    # app.run(host='::', port=Config().port, debug=True, use_reloader=False)        # Werkezeug only for development


def logger_setup(log_file_format: Optional[str] = '%(asctime)s %(name)s %(levelname)s %(message)s',
                 log_file_date_format: Optional[str] = '%Y-%m-%d %H:%M:%S'):
    log_filename = "covmatic-robotmanager_{}.log".format(time.strftime("%Y_%m_%d__%H_%M_%S"))
    log_filepath = os.path.join(Config.get_base_log_folder(), log_filename)

    main_logger.info("Setting up log file to {}".format(log_filepath))

    file_handler = logging.FileHandler(log_filepath)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_file_format, log_file_date_format))
    main_logger.addHandler(file_handler)


def main_loop():
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=start_app, args=(q,))
    main_logger.info("Starting server process...")
    p.start()
    main_logger.info("Server process {} is up and waiting.".format(p.pid))
    token = q.get(block=True)
    main_logger.info("Terminating process {}".format(p.pid))
    p.terminate()
    main_logger.info("Exiting")


def main():
    if Config().test_only:
        main_logger.info("Test only run, exiting...")
    else:
        main_loop()


if __name__ == '__main__':
    sys.exit(main())
