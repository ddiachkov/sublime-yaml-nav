import sublime
import sublime_plugin

current_symbol = None

def get_yaml_symbols(view):
    """
    Returns YAML key paths and associated regions for given view.
    Paths calculated by key indentation level -- it's more efficient and secure, but doesn't support inline hashes.
    """

    regions = view.find_by_selector("entity.name.tag.yaml")

    symbols = []
    current_path = []

    for region in regions:
        key = view.substr(region).rstrip(":")
        line = view.line(region)

        # Characters count from line beginning to key start position
        indent_level = region.begin() - line.begin()

        # Pop items from current_path while its indentation level less than current key indentation
        while len(current_path) > 0 and current_path[-1]["indent"] >= indent_level:
            current_path.pop()

        current_path.append({"key": key, "indent": indent_level})

        symbol_name = ".".join(map(lambda item: item["key"], current_path))
        symbols.append({"name": symbol_name, "region": region})

    return symbols


class GotoYamlSymbolCommand(sublime_plugin.WindowCommand):
    """
    Opens quick panel with YAML symbols.
    """
    def run(self):
        self.view = self.window.active_view()
        self.symbols = get_yaml_symbols(self.view)
        self.window.show_quick_panel(list(map(lambda x: x["name"], self.symbols)), self.on_symbol_selected)

    def on_symbol_selected(self, index):
        if index >= 0:
            region = self.symbols[index]["region"]

            self.view.show_at_center(region)

            # Set cursor after YAML key
            self.view.sel().clear()
            self.view.sel().add(sublime.Region(region.end() + 1))


class DisplayYamlPathCommand(sublime_plugin.WindowCommand):
    """
    Displays YAML symbol in focus.
    """
    def run(self):
        global current_symbol
        view = self.window.active_view()
        selection = view.sel()

        # 1 cursor
        if len(selection) == 1:
            selected_lines = view.lines(selection[0])

            # 1 selected line
            if len(selected_lines) == 1:
                cursor_line = selected_lines[0]

                # Need to reverse -- we searching for deepest key
                yaml_symbols = reversed(get_yaml_symbols(view))

                for symbol in yaml_symbols:
                    if cursor_line.intersects(symbol["region"]):
                        current_symbol = symbol["name"]
                        display_message(current_symbol)
                        return
            else:
                display_message("multiple lines!")

        else:
            display_message("multiple cursors!")

class CopyYamlSymbolToClipboardCommand(sublime_plugin.WindowCommand):
    """
    Copies selected symbol into clipboard.
    """
    def run(self):
        global current_symbol

        if len(current_symbol) > 0:
            sublime.set_clipboard(current_symbol)
            display_message("%s - copied to clipboard!" % current_symbol)
        else:
            display_message("nothing selected!")

def display_message(message):
    sublime.active_window().active_view().set_status("yaml_path", "YAML path: %s" % message)

class YamlNavListener(sublime_plugin.EventListener):
    def on_selection_modified_async(self, view):
        # Only if current buffer contains YAML
        if view.score_selector(0, "source.yaml") > 0:
            sublime.active_window().run_command("display_yaml_path")
            
