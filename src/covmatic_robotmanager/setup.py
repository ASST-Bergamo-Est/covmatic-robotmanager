import logging
import os
import subprocess

from src.covmatic_robotmanager.config import Config
from src.covmatic_robotmanager.utils import FunctionCaseStartWith

Config.pull(__doc__)

setup = FunctionCaseStartWith(os.sys.platform)


@setup.case('linux')
def linux_setup():
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    if Config().desktop_file:
        with open(Config().desktop_file, "w") as df:
            with open(os.path.join(template_dir, "covmatic.desktop"), "r") as tf:
                df.write(tf.read().format(os.path.join(template_dir, "Covmatic_Icon.ico")))
    else:
        logging.getLogger().warning("No desktop file specified, skipping")

    home_config = Config.get_config_file_path()
    if not os.path.exists(home_config):
        with open(home_config, "w"):
            pass
    subprocess.Popen(["xdg-open", home_config])


@setup.case(('win32', 'cygwin'))
def win_setup():
    import winshell

    print(Config().__dict__)

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    if Config().desktop_file:
        with winshell.shortcut(Config().desktop_file) as link:
            link.path = os.sys.executable
            link.arguments = "-m covmatic_robotmanager.main"
            link.description = "Covmatic Robotmanager server"
            # link.show_cmd = "min"
            link.icon_location = (os.path.join(template_dir, "Covmatic-robotmanager_Icon.ico"), 0)
    else:
        logging.getLogger().warning("No desktop file specified, skipping")

    home_config = Config.get_config_file_path()
    if not os.path.exists(home_config):
        with open(home_config, "w"):
            pass
    subprocess.Popen(["notepad", home_config])


@setup.case('')
def other_setup():
    logging.getLogger().warning("No setup action defined for platform {}".format(os.sys.platform))


if __name__ == "__main__":
    setup()