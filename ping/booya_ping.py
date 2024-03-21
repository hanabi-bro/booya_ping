from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tabs, TabbedContent, TabPane, Button
from textual.containers import Container
from textual import on
import os, sys

from env_setting import Config
from csv import reader

from common.log import my_logger
logger = my_logger(__name__)

from ping_app import PingWidget
from tr_app import TrWidget

from help_app import HelpScreen
class BooyaPing(App):
    CSS_PATH = 'booya_ping.tcss'

    bindings = {
        "ping" : [
            ("q", "quiet_app", "Quit This Application"),
            ("s", "start_ping", "Start Ping"),
            ("e", "stop_ping", "Stop Ping"),
            ("r", "reset_ping", "Reset Results"),
            ("t", "select_target_ping", "Target Select"),
            ("h", "push_screen('help')", "Help"),
        ],
        "tr" : [
            ("q", "quiet_app", "Quit This Application"),
            ("s", "start_tr", "Start Traceroute"),
            ("e", "stop_tr", "Stop Traceroute"),
            ("r", "reset_tr", "Reset Results"),
            ("c", "chache_clear_tr", "Cache Clear"),
            ("t", "select_target_tr", "Target Select"),
            ("h", "push_screen('help')", "Help"),
        ],
    }

    header = Header()
    footer = Footer()

    SCREENS = {'help': HelpScreen()}

    def __init__(self, base_dir='booya_log', options=False):
        super().__init__()

        config = Config()
        config.read()
        base_dir = config.get_log_dir()
        self.base_dir = base_dir
        self.target_list_dir = os.path.join(base_dir, 'conf')
        os.makedirs(self.target_list_dir, exist_ok=True)

        self.mp_widget = PingWidget(base_dir=base_dir, options=options)
        self.tr_widget = TrWidget(base_dir=base_dir, options=options)

        self.initial_tab = 'ping'
        if options and not options['ping'] and options['tr']:
            self.initial_tab = 'tr'

        self.BINDINGS = self.bindings[self.initial_tab]

    def compose(self) -> ComposeResult:
        yield self.header
        yield self.footer
        with TabbedContent(initial=self.initial_tab):
            ### Target Select
            with TabPane("Ping", id="ping"):
                with Container():
                    yield self.mp_widget
            with TabPane("Traceroute", id="tr"):
                with Container():
                    yield self.tr_widget

    @on(TabbedContent.TabActivated)
    def on_tab_changed(self, message) -> None:
        current_tab = self.query_one(Tabs).active_tab.id
        # textual version 5から？ active_tab.id で取得できるidが変わってしまった・・・・
        current_tab = current_tab.replace('--content-tab-', "")
        logger.info(current_tab)
        self.update_bindings(self.bindings[current_tab])

    def update_bindings(self, new_bindings: list[tuple[str, str, str]]) -> None:
        # # デフォルトキーを残す場合
        # default_bindings = {b.key for b in App.BINDINGS}  # type: ignore

        # デフォルトキーを残さない場合
        default_bindings = {}

        # 既存のキーバインドを削除
        for key in list(self._bindings.keys):
            if key not in default_bindings:
                self._bindings.keys.pop(key)

        # デフォルトキーを変更
        self.bind(keys='ctrl+c', action='quiet_app', description='Quit', show=False, key_display=None)

        # 新しいキーバインディング
        for key, action, description in new_bindings:
            self.bind(keys=key, action=action, description=description, show=True, key_display=None)

        # Footerに反映
        self.footer._bindings_changed(None)

    ### Ping Buttons
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

    ### Traceroute Buttons
    @on(Button.Pressed, "#start_all_tr")
    def action_start_tr(self):
        self.tr_widget.tr_start()

    @on(Button.Pressed, "#stop_all_tr")
    def action_stop_tr(self):
        self.tr_widget.tr_stop()

    @on(Button.Pressed, "#reset_all_tr")
    def action_reset_tr(self):
        self.tr_widget.tr_reset()

    @on(Button.Pressed, "#chache_clear_all_tr")
    def action_chache_clear_tr(self):
        self.tr_widget.tr_cache_clear()

    def action_select_target_tr(self):
        self.tr_widget.tr_select_target()

    def action_quiet_app(self):
        self.mp_widget.mp_stop()
        self.tr_widget.tr_stop()
        self.exit()


if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    class MyArgumentParser(ArgumentParser):
        def error(self, message):
            print('error occured while parsing args : '+ str(message))
            self.print_help() 
            exit()

    parser = MyArgumentParser(description='booya ping and traceroute tui')
    parser.add_argument('-p', '--ping', action='store_true', help='execute ping')
    parser.add_argument('-t', '--tr',  action='store_true', help='execute traceroute')
    parser.add_argument('-f', '--file',  help='target list file name')
    parser.add_argument('-l', '--list', help='target list. delimita is , \ne.g.) booya_ping -p -l 1.1.1.1,8.8.8.8')
    parser.add_argument('-c', '--cache-clear', action='store_true', help='clear route cache of traceroute')
    args = parser.parse_args()

    target_lsit = []
    if args.list:
        target_lsit = args.list.split(',')

    # if not any((args.ping, args.tr)) and any([args.file, args.list]):
    #     pass
    # elif any((args.ping, args.tr)) and any([args.file, args.list]):
    #     pass
    # else:
    #     print('!!! booya ping notise')
    #     print('--file or --list option need with --ping or --tr')
    #     print(args)

    options=False
    if args.ping or args.tr:
        options = {
            'ping': args.ping,
            'tr': args.tr,
            'file': args.file,
            'list': target_lsit,
            'cache-clear': args.cache_clear,
        }

    app = BooyaPing(options=options)

    try:
        app.run()
    except Exception as e:
        logger.debug(e.args)
    finally:
        app.action_quiet_app()