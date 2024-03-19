from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label
from textual.containers import Horizontal, ScrollableContainer, Container
from textual.reactive import reactive
from textual import on
from textual.widget import Widget

import os, sys

from env_setting import Config
from csv import reader

from select_target import SelectTarget

from ping.common.log import my_logger
logger = my_logger(__name__)

from ping_row import TrRow as PingRow

class TrWidget(Widget):
    def __init__(self, base_dir='booya_log'):
        super().__init__()

        config = Config()
        config.read()
        # base_dir='booya_log'
        base_dir = config.get_log_dir()
        target_list_dir = os.path.join(base_dir, './conf')

        self.btn_start = Button('Start', id='start_all', classes='start_all')
        self.btn_stop  = Button('Stop', id='stop_all', classes='stop_all')
        self.btn_reset = Button('Reset', id='reset_all', classes='reset_all')
        self.select_target = SelectTarget([], id='select_target', classes='select_target')
        self.select_target.set_base_dir(base_dir)

        self.base_dir = base_dir
        self.target_list = []
        self.ping_row_list = []

    def compose(self) -> ComposeResult:
        yield Header()
        # yield Footer()
        with Horizontal(id='head_row', classes='head_row'):
            yield self.btn_start
            yield self.btn_stop
            yield self.btn_reset
            yield self.select_target
        with Horizontal(id='res_heder_row', classes='res_heder_row'):
            yield Label(f'宛先\n[#808080](送信元)[/]', id='res_header_dst_src', classes='res_header_dst_src')
            yield Label(f'[green]OK[/]\n[red]NG[/]', id='res_header_count', classes='res_header_count')
            yield Label('結果', id='res_history', classes="res_header_history")
        with ScrollableContainer(id='res_rows', classes='res_rows'):
            """"""

    @on(SelectTarget.Changed)
    def select_changed(self, event: SelectTarget.Changed) -> None:
        target_file_path = os.path.abspath(os.path.join(self.base_dir, str(event.value)))
        # self.title = str(target_file)
        self.load_target_list(target_file_path)
        self.set_target()

    # Target CSV Load
    def load_target_list(self, target_file_path=None) -> None:
        if target_file_path is not None:
            self.target_file_path = target_file_path
        with open(self.target_file_path, encoding='UTF-8') as f:
            rows = reader(f)
            self.target_list = []
            for row in rows:
                if not row:
                    continue
                elif len(row) == 1:
                    row.append('')
                self.target_list.append({'dst': row[0], 'src': row[1]})
        
    def action_remove_all(self):
        self.remove_row()

    def action_mount_all(self):
        for t in self.target_list:
            self.mount_row(t)
        self.btn_state()

    def action_close_app(self):
        for ping_row in self.ping_row_list:
            ping_row.stop()
        
        sys.exit()

    def set_target(self, target_list=None) -> None:
        if target_list is not None:
            self.target_list = target_list
        self.action_remove_all()
        self.action_mount_all()

    def mount_row(self, target) -> None:
        new_ping_row = PingRow(target=target, base_dir=self.base_dir)
        self.ping_row_list.append(new_ping_row)
        self.query_one('#res_rows').mount(new_ping_row)

    def remove_row(self, target=None) -> None:
        self.query_one("#res_rows").remove_children()


    def btn_state(self):
        """"""

class TrApp(App):
    CSS_PATH = 'booya_ping_test.tcss'
    BINDINGS = [
        ("q", "close_app", "Quit This Application"),
        ("s", "start", "Start Traceroute"),
        ("e", "stop", "Stop Traceroute"),
        ("r", "reset", "Reset Results"),
        ("t", "select_target", "Target Select"), 
    ]

    def __init__(self, base_dir='booya_log'):
        super().__init__()
        self.tr_widget = TrWidget()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield self.tr_widget


if __name__ == '__main__':
    tr_app = TrApp()
    tr_app.run()