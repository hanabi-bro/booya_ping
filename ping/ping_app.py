from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label, Static
from textual.containers import Horizontal, ScrollableContainer
from textual import on
from textual.widget import Widget
from csv import reader
import sys, os
from time import sleep
from datetime import datetime

from common.fire_and_forget import fire_and_forget
import common.iptoolz as itz
from ping import Ping
from select_target import SelectTarget
from env_setting import Config
from common.log import my_logger
from common.colors import COLORS
from validate import addr_validate_dst, addr_validate_src

logger = my_logger(__name__)

class PingRow(Static):
    def __init__(self, target={'dst': '1.1.1.1', 'src': None}, base_dir='booya_log'):
        super().__init__()

        self.mp = Ping(dummy=False, base_dir=base_dir)

        self.dst = ''
        self.src = ''
        self.dst_comment = ''
        self.validate_err = {}
        self.check_target(target)

        tmp_dst = self.dst
        if not target['dst_comment'] == '':
            tmp_dst = f"{self.dst}[{self.dst_comment}]"
    
        self.res_dst_src_col = Label(f'{tmp_dst}\n[#808080]({self.src})[/]', id='res_dst_src', classes='res_dst_src')
        self.res_count_col = Label(f'[green]-[/]\n[red]-[/]', id='res_count', classes='res_count')
        self.res_history_col = Label('', id='res_history', classes="res_history")

        self.pinging = False

        self.timeout = 1
        self.ttl = 128
        self.block_size = 64

        self.res_history = []

    def check_target(self, target):
        """"""
        self.dst = target['dst']
        self.src = target['src']
        self.dst_comment = target['dst_comment']
        self.validate_err = addr_validate_dst(self.dst, self.validate_err)
        if len(self.validate_err['err']) == 0:
            if target['src'] is None or target['src'] == '':
                self.src = itz.get_src_addr(target['dst'])
            self.validate_err = addr_validate_src(self.src, self.validate_err)

    def compose(self) -> ComposeResult:
        yield self.res_dst_src_col
        yield self.res_count_col
        yield self.res_history_col

    def on_mount(self) -> None:
        """"""
        if len(self.validate_err['warn']) > 0:
            self.res_dst_src_col.styles.background = 'yellow'
            self.res_dst_src_col.styles.color = 'black'
            self.res_count_col.styles.background = 'yellow'
            self.res_history_col.styles.background = 'yellow'
            self.res_history_col.styles.color = 'black'
            msg = [m for m in self.validate_err['warn']]
            self.res_history_col.update('\n'.join(msg))

        if len(self.validate_err['err']) > 0:
            self.res_dst_src_col.styles.background = 'red'
            self.res_dst_src_col.styles.color = 'black'
            self.res_count_col.styles.background = 'red'
            self.res_history_col.styles.background = 'red'
            self.res_history_col.styles.color = 'black'
            msg = [m for m in self.validate_err['err']]
            self.res_history_col.update('\n'.join(msg))

    @fire_and_forget
    def loop_start(self):
        """"""
        if len(self.validate_err['err']): return
        if self.pinging: return
        self.pinging = True

        while self.pinging == True:
            start_time = datetime.now()
            self.res = self.mp.run(self.dst, self.src, timeout=self.timeout, ttl=self.ttl, block_size=self.block_size)
            self.update_display(self.res)

            rtt = (datetime.now() - start_time).total_seconds()
            if self.timeout > rtt:
                sleep(self.timeout - rtt)


    def loop_stop(self):
        """"""
        self.pinging = False

    def update_display(self, res):
        self.res_history.append(res['type'])

        all_count = len(self.res_history)
        ok_count = self.res_history.count(0)
        ng_count = all_count - ok_count

        self.res_count_col.update(f'[green]{ok_count}[/]\n[red]{ng_count}[/]')

        tmp_history = []

        self.result_wrap = 30
        if len(self.res_history) > (self.result_wrap * 2):
            trancate = -((len(self.res_history) % self.result_wrap) + self.result_wrap)
            tmp_history = self.res_history[trancate:]
        else:
            tmp_history = self.res_history

        def set_display_char(num):
            if num == 0:
                char = '[green]☻[/]' #∘⌾⊚⍤◎●◉○◯☉☀☼☀☼
            elif num == 11:
                char = '[yellow]⧛[/]' #☺⦂⦙⦚⧘⧙⧚⧛⫶⫯⫰⫱⫲⫳⫴⫵☁⛅☽☾⯑
            else:
                char = '[red r]☠[/]' #✕✖✗✘❘❙❚⛔⁎⁕∗∙☣☂🌂☃❌
            return char

        tmp_history = [
            set_display_char(item) for item in tmp_history
        ]

        self.res_history_col.update(''.join(list(map(str, tmp_history))))

    def start(self) -> None:
        # self.check_tr_update.resume()
        if self.pinging: return

        self.loop_start()

    def stop(self) -> None:
        self.pinging = False

    def reset(self) -> None:
        """"""
        self.res_history = []

        self.res_count_col.update(f'[green]-[/]\n[red]-[/]')
        self.res_history_col.update('')


class PingWidget(Widget):
    def __init__(self, base_dir='booya_log', options=False):
        super().__init__()

        config = Config()
        config.read()
        base_dir = config.get_log_dir()
        self.base_dir = base_dir
        self.target_list_dir = os.path.join(base_dir, 'conf')
        os.makedirs(self.target_list_dir, exist_ok=True)

        self.btn_start = Button('Start', id='start_all_ping', classes='start_all')
        self.btn_stop  = Button('Stop', id='stop_all_ping', classes='stop_all')
        self.btn_reset = Button('Reset', id='reset_all_ping', classes='reset_all')

        self.ping_row_list = []

        self.select_target = SelectTarget([], id='select_target', classes='select_target')
        self.select_target.set_base_dir(self.target_list_dir)

        self.running = False

        self.menu_btns = [
            self.btn_start,
            self.btn_stop,
            self.btn_reset,
            self.select_target,
        ]

        self.options = options
        self.header = Label()

    def compose(self) -> ComposeResult:
        yield self.header
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

    def on_mount(self) -> None:
        self.header.update(f'Ping | {self.base_dir}')

        if self.options and self.options['ping']:
            self.cli_set_target(self.options['file'], self.options['list'])
            self.mp_start()
            self.btn_state()
        else:
            self.btn_state('init')

    @on(SelectTarget.Changed)
    def select_changed(self, event: SelectTarget.Changed) -> None:
        target_file_path = os.path.abspath(os.path.join(self.target_list_dir, str(event.value)))
        # self.title = str(target_file)
        self.load_target_list(target_file_path)
        self.set_target()

    def cli_set_target(self, target_file=False, target_list=False):
        self.target_list = []
        if target_list:
            for l in target_list:
                self.target_list.append({'dst': l, 'src': None, 'dst_comment': None})
            self.set_target()
        elif target_file:
            self.load_target_list(target_file)
            self.set_target()

    # Target CSV Load
    def load_target_list(self, target_file_path=None) -> None:
        if target_file_path is not None:
            self.target_file_path = target_file_path
        with open(self.target_file_path, 'r', encoding='UTF-8') as f:
            rows = reader(f)
            self.target_list = []
            for row in rows:
                if not row:
                    continue
                elif len(row) == 1:
                    row += ['', '']
                elif len(row) >= 2:
                    row += ['']
                self.target_list.append({'dst': row[0], 'src': row[1], 'dst_comment': row[2]})
        
    def set_target(self, target_list=None) -> None:
        if target_list is not None:
            self.target_list = target_list
        self.remove_all()
        self.mount_rows()

    def remove_all(self):
        self.remove_row()

    def mount_rows(self):
        # textual 5.x ?からmount_allが組み込み関数に追加されてるっぽいのでrename
        for t in self.target_list:
            self.mount_row(t)
        self.btn_state()

    def mount_row(self, target) -> None:
        new_tr_row = PingRow(target=target, base_dir=self.base_dir)
        self.ping_row_list.append(new_tr_row)
        self.query_one('#res_rows').mount(new_tr_row)

    def remove_row(self, target=None) -> None:
        self.query_one("#res_rows").remove_children()

    def close_app(self):
        self.tr_stop()

    def mp_start(self):
        self.btn_state('disable')
        if self.running: return
        self.running = True
        for ping_row in self.ping_row_list:
            ping_row.start()
        self.btn_state()

    def mp_stop(self):
        self.btn_state('disable')
        for ping_row in self.ping_row_list:
            ping_row.stop()
        self.running = False
        self.btn_state()

    def mp_reset(self):
        self.btn_state('disable')
        for ping_row in self.ping_row_list:
            ping_row.reset()
        self.btn_state()

    def mp_select_target(self):
        self.btn_state('disable')
        if self.running: return
        self.select_target.action_pre_show_overlay()
        self.btn_state()

    def btn_state(self, state=None):
        # btn_ids = ['#start_all', '#stop_all', '#reset_all', '#select_target']

        if state == 'init':
            disabled_states = [True, True, True, False]
        elif state == 'disable':
            disabled_states = [True, True, True, True, True]
        elif self.running:
            disabled_states = [True, False, False, True]
        else:
            disabled_states = [False, True, False, False]

        for i, btn in enumerate(self.menu_btns):
            btn.disabled = disabled_states[i]

class PingApp(App):
    CSS_PATH = 'booya_ping.tcss'
    BINDINGS = [
        ("q", "quiet_app", "Quit This Application"),
        ("s", "start_ping", "Start Ping"),
        ("e", "stop_ping", "Stop Ping"),
        ("r", "reset_ping", "Reset Results"),
        ("t", "select_target_ping", "Target Select"), 
    ]

    def __init__(self, base_dir='booya_log', options=False):
        super().__init__()
        self.mp_widget = PingWidget(options=options)

    def compose(self) -> ComposeResult:
        yield Footer()
        yield self.mp_widget

    def on_mount(self) -> None:
        """"""

    def action_quiet_app(self):
        self.mp_widget.mp_stop()
        self.exit()

    @on(Button.Pressed, "#start_all_ping")
    def action_start_ping(self):
        self.mp_widget.mp_start()

    @on(Button.Pressed, "#stop_all_ping")
    def action_stop_ping(self):
        self.mp_widget.mp_stop()

    @on(Button.Pressed, "#reset_all_ping")
    def action_reset_ping(self):
        self.mp_widget.mp_reset()

    def action_select_target_ping(self):
        self.mp_widget.mp_select_target()


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser(description='booya ping and traceroute tui')
    parser.add_argument('-p', '--ping', action='store_true', help='execute ping')
    # parser.add_argument('-t', '--tr',  action='store_true', help='execute traceroute')
    parser.add_argument('-f', '--file',  help='[not impremnt] target list file name')
    parser.add_argument('-l', '--list', help='target list. delimita is , \ne.g.) booya_ping -p -l 1.1.1.1,8.8.8.8')
    # parser.add_argument('-c', '--cache-clear', action='store_true', help='clear route cache of traceroute')
    args = parser.parse_args()

    target_lsit = []
    if args.list:
        target_lsit = args.list.split(',')

    mode = ''
    options = False
    if args.ping:
        options = {
            'ping': args.ping,
            'file': args.file,
            'list': target_lsit,
        }

    try:
        ping_app = PingApp(options=options)
        ping_app.run(clear_on_exit=False)
    except Exception as e:
        logger.info(e.args)
    finally:
        ping_app.action_quiet_app()