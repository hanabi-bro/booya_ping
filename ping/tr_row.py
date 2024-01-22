from textual.app import ComposeResult
from textual.widgets import Label, Static
from textual.containers import Horizontal
from textual.reactive import reactive

from ping.common.log import my_logger
logger = my_logger(__name__)

from multi_ping import MultiPing

class TestRow(Static):
    mp_result = reactive({'result_history': []})
    mp_result_history = reactive([])

    def __init__(self, target={'dst': '1.1.1.1', 'src': None}, base_dir='booya_log'):
        super().__init__()

        self.mp = MultiPing(dummy=False, base_dir=base_dir)
        self.mp.set_target([target])
        self.key = list(self.mp.get_results().keys())[0]
        table = str.maketrans('.', '_', '')
        self.id = f'id_{self.key.translate(table)}'

        self.dst = target['dst']
        self.src = self.mp.get_ping_list()[0]['src']
        self.btn_visible = False

        self.res_dst_src_col = Label(f'{self.dst}\n[#808080]({self.src})[/]', id='res_dst_src', classes='res_dst_src')
        self.res_count_col = Label(f'[green]-[/]\n[red]-[/]', id='res_count', classes='res_count')
        self.res_history_col = Label('', id='res_history', classes="res_history")

    def compose(self) -> ComposeResult:
        with Horizontal(id=self.id, classes='result_row'):
            yield self.res_dst_src_col
            yield self.res_count_col
            yield self.res_history_col

    def on_mount(self) -> None:
        self.check_mp_result = self.set_interval(1/10, self.update_mp_result, pause=True)
        logger.info('on mount')

    def update_mp_result(self) -> None:
        res = self.mp.get_results()[self.key]
        self.mp_result = res.copy()

    def watch_mp_result(self, mp_result) -> None:
        fmt_result = self.format_result_history(mp_result)
        self.res_history_col.update(fmt_result['display_history'])
        self.res_count_col.update(f"[green]{fmt_result['ok_count']}[/]\n[red]{fmt_result['ng_count']}[/]")

    def format_result_history(self, mp_result) -> str:
        tmp_history = mp_result['result_history']
        ok_count = tmp_history.count(0)
        ng_count = len(tmp_history) - ok_count

        self.result_wrap = 30
        if len(tmp_history) > (self.result_wrap * 2):
            trancate = -((len(tmp_history) % self.result_wrap) + self.result_wrap)
            tmp_history = tmp_history[trancate:]

        tmp_history = [
            '[green]☻[/]' if item == 0 else '[red]☠[/]' for item in tmp_history
        ]
        display_history = ''.join(list(map(str, tmp_history)))

        return {'ok_count': ok_count, 'ng_count': ng_count, 'display_history': display_history}

    def start(self) -> None:
        self.check_mp_result.resume()
        self.mp.start()

    def stop(self) -> None:
        self.mp.stop()
        self.update_mp_result()
        self.check_mp_result.pause()

    def reset(self) -> None:
        self.mp.reset()
        self.update_mp_result()

