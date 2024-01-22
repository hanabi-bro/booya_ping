from configparser import ConfigParser

from os import path
import pathlib


class Config():
    def __init__(self):
        """"""
        self.conf = ConfigParser()
        self.config_file = path.join(path.dirname(__file__), 'config.ini')

    def read(self):
        self.conf.read(self.config_file, encoding='utf-8')

    def write(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.conf.write(f)

    def get_log_dir(self):
        self.read()
        log_dir = self.conf.get("default", "base_directory")
        return pathlib.Path(log_dir).expanduser().resolve()

    def get_base_dir(self):
        self.read()
        base_dir = self.conf.get("default", "base_directory")
        return pathlib.Path(base_dir).expanduser().resolve()


if __name__ == '__main__':
    config = Config()
    config.read()

    config.conf['default']['base_directory']
