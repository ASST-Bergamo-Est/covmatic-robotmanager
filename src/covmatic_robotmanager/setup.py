import logging
import os
import subprocess

from .config import Config
from .utils import FunctionCaseStartWith


setup = FunctionCaseStartWith(os.sys.platform)


@setup.case('linux')
def linux_setup():
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    file_path = Config.get_desktop_file_path()
    if file_path:
        directory_path = os.path.split(file_path)[0]
        if not os.path.exists(directory_path):
            logging.getLogger().info("Creating directory {}".format(directory_path))
            os.makedirs(directory_path)
        with open(file_path, "w") as df:
            with open(os.path.join(template_dir, "covmatic.desktop"), "r") as tf:
                df.write(tf.read().format(os.path.join(template_dir, "Covmatic-robotmanager_Icon.png")))
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

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    if Config.get_desktop_file_path():
        with winshell.shortcut(Config.get_desktop_file_path()) as link:
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