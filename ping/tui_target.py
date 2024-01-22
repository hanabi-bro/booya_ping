from textual import on
from textual.app import ComposeResult
from textual.widgets import Button, DirectoryTree, Static
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import var
from textual.widget import Widget
from rich.syntax import Syntax
from rich.traceback import Traceback

from os.path import join, abspath, isdir, isfile
from os import makedirs
from csv import reader

from env_setting import Config


class TargetTui(Widget):
    config = Config()
    config.read()
    base_dir = config.get_log_dir()

    target_list_dir = join(base_dir, './conf')

    if not isdir(target_list_dir):
        makedirs(target_list_dir, exist_ok=True)

    file_path = abspath(join(target_list_dir, 'target.csv'))

    if not isfile(file_path):
        with open(join(target_list_dir, 'target.csv'), 'w', encoding='UTF-8') as f:
            f.write('8.8.4.4,' + '\n')
            f.write('1.0.0.1,' + '\n')
            f.write('10.0.0.1,' + '\n')

    show_tree = var(True)
    btn_select_target = Button('適用', id='select_target_file')

    def compose(self) -> ComposeResult:
        yield DirectoryTree(self.target_list_dir, id="tree-view")
        with Horizontal(id='target_file_select', classes='contorollers'):
            yield Button('適用', id='select_target_file')
            yield Button('ディレクトリ再読み込み', id='tree_reload')
            yield Static(id='file_path')
        with VerticalScroll(id="code-view"):
            yield Static(id="code", expand=True)

    def on_mount(self) -> None:
        """ """
    ### Target Select
    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when the user click a file in the directory tree."""
        event.stop()
        code_view = self.query_one("#code", Static)
        try:
            syntax = Syntax.from_path(
                str(event.path),
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark",
            )
            self.file_path = abspath(join('.', str(event.path)))
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
        else:
            code_view.update(syntax)
            self.query_one("#code-view").scroll_home(animate=False)
            self.sub_title = str(event.path)
            self.query_one("#file_path", Static).update(self.file_path)

    @on(Button.Pressed, "#select_target_file")
    def select_target_file(self) -> None:
        self.load_target_list()

    @on(Button.Pressed, "#tree_reload")
    def target_tree_reload(self) -> None:
        self.query_one("#tree-view").reload()

    # Target CSV Load
    def load_target_list(self, file_path=None) -> None:
        if file_path is not None:
            self.file_path = file_path
        with open(self.file_path, encoding='UTF-8') as f:
            rows = reader(f)
            self.ping_data = []
            for row in rows:
                if not row:
                    continue
                elif len(row) == 1:
                    row.append('')
                
                self.ping_data.append(row[:2])
        
        return self.ping_data


