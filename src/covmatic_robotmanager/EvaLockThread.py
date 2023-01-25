import logging
import time

from evasdk import Eva
import threading


class EvaLockThread(threading.Thread):
    def __init__(self, eva: Eva, logger=logging.getLogger(__name__), *args, **kwargs):
        super(EvaLockThread, self).__init__(*args, **kwargs)
        self._eva = eva
        self._logger = logger
        self._enabled = True
        self._logger.info("Current state: {}".format(self._eva.lock_status()))
        if self.is_eva_locked:
            self._logger.info("Eva is locked, trying to unlock...")
            self._eva.unlock()
        self._logger.info("Eva is locked: {}".format(self.is_eva_locked))

    @property
    def is_eva_locked(self) -> bool:
        return self._eva.lock_status()["status"] == "locked"

    def run(self):
        self._logger.info("Locking")
        self._eva.lock(wait=True, timeout=5)

        while self._enabled:
            self._logger.info("Renewing lock; lock_status is: {}".format(self._eva.lock_status()))
            self._eva.lock_renew()
            self._logger.info("Lock renewed")
            time.sleep(2)

        self._logger.info("Unlocking; current lock status is: {}".format(self._eva.lock_status()))
        self._eva.unlock()

    def stop(self):
        self._enabled = False
        self._logger.info("Stop; enabled is: {}".format(self._enabled))


class EvaLockManager:
    def __init__(self, eva: Eva, logger=logging.getLogger(__name__)):
        self._lock = None
        self._eva = eva
        self._lock_thread = EvaLockThread(self._eva)
        self._logger = logger

    def start_locking(self):
        self._logger.info("Start locking for Eva: {}".format(self._eva.name()))
        self._logger.info("Starting thread")
        self._lock_thread.start()

    def stop_locking(self):
        self._logger.info("Stop thread")
        self._lock_thread.stop()
        self._logger.info("Waiting for join")
        self._lock_thread.join()



