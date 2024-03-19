from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import MarkdownViewer, Markdown, Label, Header, Footer
from textual.widget import Widget
import os

class HelpScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Cloase Help")]

    help_file_name = 'README.md'
    help_file_path = os.path.join(os.path.dirname(__file__), help_file_name)
    if os.path.isfile(help_file_path):
        pass
    elif os.path.join(os.path.dirname(__file__),  '..', help_file_name):
        help_file_path = os.path.join(os.path.dirname(__file__), '..', help_file_name)
    with open(help_file_path, 'r', encoding='utf-8-sig') as f:
        help_doc = f.read()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield MarkdownViewer(self.help_doc, show_table_of_contents=False)

class HelpApp(App):
    SCREENS = {'help': HelpScreen()}
    BINDINGS = [("h", "push_screen('help')", "Help")]


    def compose(self) -> ComposeResult:
        yield Footer()

if __name__ == "__main__":
    app = HelpApp()
    app.run()
