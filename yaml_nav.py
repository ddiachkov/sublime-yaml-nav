"""
Main plugin module with sublime commands and listeners.
"""

import sublime
import sublime_plugin
import re

from . import yaml_math, view_data

# Status key for sublime status bar
STATUS_BAR_ID = "yaml_nav"

# Filename with plugin settings
SETTINGS_FILE = "YAML Nav.sublime-settings"


def set_status(view, message):
    """
    Displays given message in the status bar of given view.
    """

    if message:
        view.set_status(STATUS_BAR_ID, "YAML path: %s" % message)
    else:
        view.erase_status(STATUS_BAR_ID)


def is_yaml_view(view):
    """
    Returns true if given view contains YAML code.
    """

    return view.score_selector(0, "source.yaml") > 0


class YamlNavListener(sublime_plugin.EventListener):
    """
    Listens for file modification/cursor movement and updates list of
    YAML symbols/currently selected symbol.
    """

    def on_load_async(self, view):
        if is_yaml_view(view):
            # Build list after file load
            self.update_yaml_symbols(view)

    def on_new_async(self, view):
        if is_yaml_view(view):
            # Build list after new buffer created
            self.update_yaml_symbols(view)

    def on_activated_async(self, view):
        if is_yaml_view(view):
            if not view.is_loading() and not view_data.get(view).yaml_symbols:
                # Rebuild list after plugin reload
                self.update_yaml_symbols(view)

            # Update current symbol after view change/quick navigation
            self.update_current_yaml_symbol(view)

    def on_modified_async(self, view):
        if is_yaml_view(view):
            # Rebuild list after file modification
            self.update_yaml_symbols(view)

    def on_selection_modified_async(self, view):
        if is_yaml_view(view):
            # Update current symbol after cursor movement
            self.update_current_yaml_symbol(view)

    def on_close(self, view):
        # Clear list after view close
        self.clear_yaml_symbols(view)

    def update_yaml_symbols(self, view):
        """
        Generates YAML symbol list and saves it in the view data.
        """

        data = view_data.get(view)
        data.yaml_symbols = yaml_math.get_yaml_symbols(view)

    def update_current_yaml_symbol(self, view):
        """
        Calculates current selected YAML symbol and saves it in the view data.
        """

        data = view_data.get(view)
        data.current_yaml_symbol = yaml_math.get_selected_yaml_symbol(data.yaml_symbols, view)

        if data.current_yaml_symbol:
            set_status(view, data.current_yaml_symbol["name"])
        else:
            set_status(view, None)

    def clear_yaml_symbols(self, view):
        """
        Clears the view data.
        """

        view_data.clear(view)


class GotoYamlSymbolCommand(sublime_plugin.TextCommand):
    """
    Opens quick panel with YAML symbols.
    """
    def run(self, edit):
        symbols = view_data.get(self.view).yaml_symbols or []

        def on_symbol_selected(index):
            if index >= 0:
                region = symbols[index]["region"]

                self.view.show_at_center(region)

                # Set cursor after YAML key
                self.view.sel().clear()
                self.view.sel().add(sublime.Region(region.end() + 1))

        self.view.window().show_quick_panel(list(map(lambda x: x["name"], symbols)), on_symbol_selected)

    def is_enabled(self):
        return is_yaml_view(self.view)


class CopyYamlSymbolToClipboardCommand(sublime_plugin.TextCommand):
    def __init__(self, *args):
        sublime_plugin.TextCommand.__init__(self, *args)

        # Load settings
        self.settings = sublime.load_settings(SETTINGS_FILE)
        self.detect_locale_filename_re = re.compile(self.settings.get("detect_locale_filename_re"), re.I)
        self.trim_language_tag_on_copy_from_locales = self.settings.get("trim_language_tag_on_copy_from_locales")

    """
    Copies selected YAML symbol into clipboard.
    """
    def run(self, edit):
        current_symbol = view_data.get(self.view).current_yaml_symbol

        if current_symbol:
            current_symbol_name = current_symbol["name"]

            # Automatically detect localization YAML and trim first tag
            # (if enabled in settings)
            if self.trim_language_tag_on_copy_from_locales and self.is_locale_file():
                current_symbol_name = re.sub("^(.+?)\\.", "", current_symbol_name)

            sublime.set_clipboard(current_symbol_name)
            set_status(self.view, "%s - copied to clipboard!" % current_symbol_name)
        else:
            set_status(self.view, "nothing selected - can't copy!")

    def is_enabled(self):
        return is_yaml_view(self.view)

    def is_locale_file(self):
        """
        Returns true if current file is localization file.
        """
        return self.detect_locale_filename_re.search(self.view.file_name()) is not None
