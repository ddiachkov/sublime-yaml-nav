import sublime
import sublime_plugin

# Global var with current symbol; updated in YamlNavListener
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


def get_current_yaml_symbol(view):
    """
    Returns current YAML key path for currently selected region in given view.
    """

    selection = view.sel()

    # 1 cursor
    if len(selection) == 1:
        selected_lines = view.lines(selection[0])

        # 1 selected line
        if len(selected_lines) == 1:
            cursor_line = selected_lines[0]

            # Reversing list because we are searching for the deepest key
            yaml_symbols = reversed(get_yaml_symbols(view))

            for symbol in yaml_symbols:
                if cursor_line.intersects(symbol["region"]):
                    return symbol["name"]

            return None

        else:
            # Ambigous symbol: multiple lines selected
            return None

    else:
        # Ambigous symbol: multiple cursors
        return None

def display_message(message):
    """
    Displays given message in the status bar.
    """

    if message:
        sublime.active_window().active_view().set_status("yaml_path", "YAML path: %s" % message)
    else:
        sublime.active_window().active_view().erase_status("yaml_path")


class YamlNavListener(sublime_plugin.EventListener):
    """
    Listens for cursor movement and updates current YAML symbol.
    """

    def on_selection_modified_async(self, view):
        global current_symbol

        # Only if current buffer contains YAML
        if view.score_selector(0, "source.yaml") > 0:
            current_symbol = get_current_yaml_symbol(view)
            sublime.active_window().run_command("display_yaml_path")


class DisplayYamlPathCommand(sublime_plugin.WindowCommand):
    """
    Displays current YAML symbol.
    """
    def run(self):
        global current_symbol
        display_message(current_symbol)

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

            # We need manually update current symbol because nav listener
            # won't be triggered after we move the cursor
            global current_symbol
            current_symbol = self.symbols[index]["name"]
            self.window.run_command("display_yaml_path")

class CopyYamlSymbolToClipboardCommand(sublime_plugin.WindowCommand):
    """
    Copies selected symbol into clipboard.
    """
    def run(self):
        global current_symbol

        if current_symbol:
            sublime.set_clipboard(current_symbol)
            display_message("%s - copied to clipboard!" % current_symbol)
        else:
            display_message("nothing selected!")
