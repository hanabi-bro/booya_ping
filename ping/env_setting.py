from configparser import ConfigParser
from textwrap import dedent
from os import path
import pathlib
from glob import glob

class Config():
    def __init__(self):
        """"""
        self.conf = ConfigParser()
        self.config_file = path.join(path.dirname(__file__), 'config.ini')

    def __gen_config_init(self):
        body = dedent('''\
            [default]
            # base_directory = C:\opt\log\\booya_log
            base_directory = ~/booya_log
        ''')[:-1]
        with open(self.config_file, 'w', encoding='UTF-8') as f:
            print(body, file=f)

    def __gen_target_init(self):
        body = dedent('''\
            1.1.1.1,,CloudFlare CDN DNS
            1.1.1.2,,Security Filter DNS
            1.1.1.3,,Family Filter DNS
            8.8.8.8,,Google DNS
        ''')[:-1]

        base_dir = self.conf.get("default", "base_directory")
        target_dir = pathlib.Path(base_dir, 'conf').expanduser().resolve()
        target_dir.mkdir(exist_ok=True, parents=True)
        target_file = pathlib.Path(target_dir, 'sample.csv').expanduser().resolve()

        with open(target_file, 'w', encoding='UTF-8') as f:
            print(body, file=f)

    def read(self):
        if not path.isfile(self.config_file):
            self.__gen_config_init()
        self.conf.read(self.config_file, encoding='utf-8')

        base_dir = self.conf.get("default", "base_directory")
        target_dir = pathlib.Path(base_dir, 'conf').expanduser().resolve()
        if not list(target_dir.glob('**/*.csv')):
            self.__gen_target_init()

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

    def get_conf_dir(self):
        base_dir = self.conf.get("default", "base_directory")
        return pathlib.Path(base_dir, 'conf').expanduser().resolve()

if __name__ == '__main__':
    config = Config()
    config.read()

    config.conf['default']['base_directory']
