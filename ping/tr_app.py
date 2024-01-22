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
from tr import TraceRoute
from select_target import SelectTarget
from env_setting import Config
from common.log import my_logger
from common.colors import COLORS
from validate import addr_validate_dst, addr_validate_src

logger = my_logger(__name__)

class TrRow(Static):
    def __init__(self, target={'dst': '1.1.1.1', 'src': None}, base_dir='booya_log'):
        super().__init__()

        self.tr = TraceRoute(base_dir=base_dir)

        self.dst = ''
        self.src = ''
        self.validate_err = {}
        self.check_target(target)
        self.res_dst_src_col = Label(f'{self.dst}\n[#808080]({self.src})[/]', id='res_dst_src', classes='res_dst_src')
        self.res_count_col = Label(f'[green]-[/]\n[red]-[/]', id='res_count', classes='res_count')
        self.res_history_col = Label('', id='res_history', classes="res_history")

        self.pinging = False

        self.timeout = 3
        self.tr_delay = 0.2
        self.block_size = 64
        self.ttl = 16

        self.route_history = []
        self.res_history = []

    def check_target(self, target):
        """"""
        self.dst = target['dst']
        self.src = target['src']
        self.validate_err = addr_validate_dst(self.dst, self.validate_err)
        if len(self.validate_err['err']) == 0:
            if target['src'] is None or target['src'] == '':
                self.src = itz.get_src_addr(target['dst'])
            self.validate_err = addr_validate_src(self.src, self.validate_err)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield self.res_dst_src_col
            yield self.res_count_col
            yield self.res_history_col

    def on_mount(self) -> None:
        """"""
        if len(self.validate_err['warn']) > 0:
            logger.info(self.validate_err)
            self.res_dst_src_col.styles.background = 'yellow'
            self.res_dst_src_col.styles.color = 'black'
            self.res_count_col.styles.background = 'yellow'
            self.res_history_col.styles.background = 'yellow'
            self.res_history_col.styles.color = 'black'
            msg = [m for m in self.validate_err['warn']]
            self.res_history_col.update('\n'.join(msg))

        if len(self.validate_err['err']) > 0:
            logger.info(self.validate_err)
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
            # if self.pinging == False:
            #     sys.sys_exit()

            start_time = datetime.now()

            self.res = self.tr.traceroute(self.dst, self.src)
            self.update_display(self.res)

            rtt = (datetime.now() - start_time).total_seconds()
            if self.timeout > rtt:
                sleep(self.timeout - rtt)

            
    def loop_stop(self):
        """"""
        self.pinging = False
    
    def update_display(self, res):
        self.route_history.append(res["route_num"])
        self.res_history.append(res["result"])

        all_count = len(self.res_history)
        ok_count = self.res_history.count('OK')
        ng_count = all_count - ok_count

        self.res_count_col.update(f'[green]{ok_count}[/]\n[red]{ng_count}[/]')

        tmp_route = []

        self.result_wrap = 15
        if len(self.route_history) >= (self.result_wrap):
            trancate = -((len(self.route_history) % self.result_wrap) + self.result_wrap)
            tmp_route = self.route_history[trancate:]
            tmp_res = self.res_history[trancate:]
        else:
            tmp_route = self.route_history
            tmp_res = self.res_history

        mod_route = []
        for res_num, item in  enumerate(tmp_route):
            rs = ''
            if tmp_res[res_num] == 'NG':
                rs = ' r'

            # mod_route.append(f"[{COLORS[item]}{rs}]{item:02}[/]")
            mod_route.append(f"[{COLORS[item]}{rs}]{item}[/]")
            # ①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳
            # ①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳

        self.res_history_col.update(','.join(list(map(str, mod_route))))

    def start(self) -> None:
        if self.pinging: return

        self.loop_start()

    def stop(self) -> None:
        self.pinging = False

    def reset(self) -> None:
        """"""
        self.route_history = []
        self.res_history = []

        self.res_count_col.update(f'[green]-[/]\n[red]-[/]')
        self.res_history_col.update('')

    def cache_clear(self):
        """"""
        self.tr.clear_route_cache()
        self.reset()


class TrWidget(Widget):
    def __init__(self, base_dir='booya_log', options=False):
        super().__init__()

        config = Config()
        config.read()
        base_dir = config.get_log_dir()
        self.base_dir = base_dir
        self.target_list_dir = os.path.join(base_dir, './conf')
        os.makedirs(self.target_list_dir, exist_ok=True)

        self.btn_start = Button('Start', id='start_all_tr', classes='start_all')
        self.btn_stop  = Button('Stop', id='stop_all_tr', classes='stop_all')
        self.btn_reset = Button('Reset', id='reset_all_tr', classes='reset_all')
        self.btn_cache_clear = Button('ChacheClear', id='chache_clear_all_tr', classes='chache_clear_all')

        self.tr_row_list = []

        self.select_target = SelectTarget([], id='select_target', classes='select_target')
        self.select_target.set_base_dir(self.target_list_dir)

        self.running = False

        self.menu_btns = [
            self.btn_start,
            self.btn_stop,
            self.btn_reset,
            self.btn_cache_clear,
            self.select_target,
        ]

        self.options = options
        self.header = Label()

    def compose(self) -> ComposeResult:
        yield self.header
        with Horizontal(id='head_row', classes='head_row_tr'):
            yield self.btn_start
            yield self.btn_stop
            yield self.btn_reset
            yield self.btn_cache_clear
            yield self.select_target
        with Horizontal(id='res_heder_row', classes='res_heder_row'):
            yield Label(f'宛先\n[#808080](送信元)[/]', id='res_header_dst_src', classes='res_header_dst_src')
            yield Label(f'[green]OK[/]\n[red]NG[/]', id='res_header_count', classes='res_header_count')
            yield Label('結果', id='res_history', classes="res_header_history")
        with ScrollableContainer(id='res_rows', classes='res_rows'):
            """"""

    def on_mount(self) -> None:
        self.header.update(f'Traceroute | {self.base_dir}')

        if self.options and self.options['tr']:
            self.cli_set_target(self.options['file'], self.options['list'])
            if self.options['cache-clear'] or self.options['cache-clear'] is not None:
                self.tr_cache_clear()
            self.tr_start()
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
                self.target_list.append({'dst': l, 'src': None})
            self.set_target()
        elif target_file:
            self.load_target_list(target_file)
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

    def set_target(self, target_list=None) -> None:
        if target_list is not None:
            self.target_list = target_list
        self.remove_all()
        self.mount_all()

    def remove_all(self):
        self.remove_row()

    def mount_all(self):
        for t in self.target_list:
            self.mount_row(t)
        self.btn_state()

    def mount_row(self, target) -> None:
        new_tr_row = TrRow(target=target, base_dir=self.base_dir)
        self.tr_row_list.append(new_tr_row)
        self.query_one('#res_rows').mount(new_tr_row)

    def remove_row(self, target=None) -> None:
        self.query_one("#res_rows").remove_children()

    def close_app(self):
        self.tr_stop()

    def tr_start(self):
        self.btn_state('disable')
        if self.running: return
        self.running = True
        for row in self.tr_row_list:
            row.start()
        self.btn_state()

    def tr_stop(self):
        self.btn_state('disable')
        for row in self.tr_row_list:
            row.stop()
        self.running = False
        self.btn_state()

    def tr_reset(self):
        self.btn_state('disable')
        for row in self.tr_row_list:
            row.reset()
        self.btn_state()

    def tr_cache_clear(self):
        if self.running: return
        for row in self.tr_row_list:
            row.cache_clear()

    def tr_select_target(self):
        self.btn_state('disable')
        if self.running: return
        self.select_target.action_pre_show_overlay()
        self.btn_state()

    def btn_state(self, state=None):
        # self.btn_start,
        # self.btn_stop,
        # self.btn_reset,
        # self.btn_cache_clear,
        # self.select_target,
        if state == 'init':
            disabled_states = [True, True, True, False, False]
        elif state == 'disable':
            disabled_states = [True, True, True, True, True]
        elif self.running:
            disabled_states = [True, False, False, True, True]
        else:
            disabled_states = [False, True, False, False, False]

        for i, btn in enumerate(self.menu_btns):
            btn.disabled = disabled_states[i]


class TrApp(App):
    CSS_PATH = 'booya_ping.tcss'
    BINDINGS = [
        ("q", "quiet_app", "Quit This Application"),
        ("s", "start_tr", "Start Traceroute"),
        ("e", "stop_tr", "Stop Traceroute"),
        ("r", "reset_tr", "Reset Results"),
        ("c", "chache_clear_tr", "Cache Clear"),
        ("t", "select_target_tr", "Target Select"), 
    ]

    def __init__(self, base_dir='booya_log', options=False):
        super().__init__()
        self.tr_widget = TrWidget(options=options)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield self.tr_widget

    def on_mount(self) -> None:
        """"""

    def action_quiet_app(self):
        self.action_stop_tr()
        self.exit()

    @on(Button.Pressed, "#start_all_tr")
    def action_start_tr(self):
        self.tr_widget.btn_state('disable')
        self.tr_widget.tr_start()
        self.tr_widget.btn_state()

    @on(Button.Pressed, "#stop_all_tr")
    def action_stop_tr(self):
        self.tr_widget.btn_state('disable')
        self.tr_widget.tr_stop()
        self.tr_widget.btn_state()

    @on(Button.Pressed, "#reset_all_tr")
    def action_reset_tr(self):
        self.tr_widget.btn_state('disable')
        self.tr_widget.tr_reset()
        self.tr_widget.btn_state()

    @on(Button.Pressed, "#chache_clear_all_tr")
    def action_chache_clear_tr(self):
        self.tr_widget.btn_state('disable')
        self.tr_widget.tr_cache_clear()
        self.tr_widget.btn_state()

    def action_select_target_tr(self):
        self.tr_widget.btn_state('disable')
        self.tr_widget.tr_select_target()
        self.tr_widget.btn_state()


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser(description='booya ping and traceroute tui')
    # parser.add_argument('-p', '--ping', action='store_true', help='execute ping')
    parser.add_argument('-t', '--tr',  action='store_true', help='execute traceroute')
    # parser.add_argument('-f', '--file',  help='target list file name')
    parser.add_argument('-l', '--list', help='target list. delimita is , \ne.g.) booya_ping -p -l 1.1.1.1,8.8.8.8')
    parser.add_argument('-c', '--cache-clear', action='store_true', help='clear route cache of traceroute')
    args = parser.parse_args()

    target_lsit = []
    if args.list:
        target_lsit = args.list.split(',')

    mode = ''
    options = False
    if args.tr:
        mode = 'tr'
        options = {
            'mode': mode,
        #    'file': args.file,
            'list': target_lsit,
            'cache-clear': args.cache_clear,
        }
    

    try:
        tr_app = TrApp(options=options)
        tr_app.run()
    except Exception as e:
        logger.info(e.args)
    finally:
        tr_app.action_quiet_app()
