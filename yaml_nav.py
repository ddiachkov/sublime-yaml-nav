import sublime
import sublime_plugin


class GotoYamlSymbolCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.view = self.window.active_view()
        self.symbols = self.get_yaml_symbols()
        self.window.show_quick_panel(list(map(lambda x: x["name"], self.symbols)), self.on_symbol_selected)


    def on_symbol_selected(self, index):
        if index >= 0:
            region = self.symbols[index]["region"]

            self.view.show_at_center(region)

            # Set cursor after YAML key
            self.view.sel().clear()
            self.view.sel().add(sublime.Region(region.end() + 1))

    def get_yaml_symbols(self):
        """
        Returns YAML keys paths.
        Paths calculated by key indentation level -- it's more efficient and secure, but doesn't support inline hashes.
        """

        regions = self.view.find_by_selector("entity.name.tag.yaml")

        symbols = []
        current_path = []

        for region in regions:
            key = self.view.substr(region).rstrip(":")
            line = self.view.line(region)

            # Character count from line beginning to key start position
            ident_level = region.begin() - line.begin()

            # Pop items from current_path while its indentation level less than current key indentation
            while len(current_path) > 0 and current_path[-1]["ident"] >= ident_level:
                current_path.pop()

            current_path.append({"key": key, "ident": ident_level})

            symbol_name = ".".join(map(lambda item: item["key"], current_path))
            symbols.append({"name": symbol_name, "region": region})

        return symbols
