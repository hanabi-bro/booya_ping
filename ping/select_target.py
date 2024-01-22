from textual import on, events
from textual.app import App, ComposeResult
from textual.widgets import Header, Select
from textual.reactive import reactive

LINES = """I must not fear.
Fear is the mind-killer.
Fear is the little-death that brings total obliteration.
I will face my fear.
I will permit it to pass over me and through me.""".splitlines()

import sys, os, glob

from common.log import my_logger
logger = my_logger(__name__)


class SelectTarget(Select):
    BINDINGS = [('enter,down,space,up', 'pre_show_overlay')]
    base_dir = 'booya_log'

    def set_base_dir(self, base_dir):
        self.base_dir = base_dir

    def get_target_file_list(self, base_dir='booya_ping'):
        self.base_dir = base_dir
        # 指定したディレクトリ内の .csv ファイルの一覧を取得
        csvfiles = glob.glob("**/*.csv", root_dir=self.base_dir, recursive=True)
        # 'results"ディレクトリを除外
        self.csvfiles = [file for file in csvfiles if 'results' not in file.split(os.path.sep)]

    def action_pre_show_overlay(self):
        csvfiles = glob.glob("**/*.csv", root_dir=self.base_dir, recursive=True)
        # 'results"ディレクトリを除外
        options = [file for file in csvfiles if 'results' not in file.split(os.path.sep)]
        options = [(str(v), v) for i, v in enumerate(options)]
        self.set_options(options)
        self.compose()
        self.action_show_overlay()

    async def _on_click(self, event: events.Click) -> None:
        csvfiles = glob.glob("**/*.csv", root_dir=self.base_dir, recursive=True)
        # 'results"ディレクトリを除外
        options = [file for file in csvfiles if 'results' not in file.split(os.path.sep)]
        options = [(str(v), v) for i, v in enumerate(options)]
        self.set_options(options)
        self.compose()

class SelectApp(App):
    def __init__(self, base_dir='booya_log'):
        super().__init__()
        self.base_dir = base_dir

        self.select_target = SelectTarget([])
        self.select_target.set_base_dir(base_dir)

    def compose(self) -> ComposeResult:
        yield Header()
        yield SelectTarget([])

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.title = str(event.value)


if __name__ == "__main__":
    app = SelectApp()
    app.run()