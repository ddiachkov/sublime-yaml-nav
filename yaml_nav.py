"""
Main plugin module with sublime commands and listeners.
"""

import sublime
import sublime_plugin
import re
import time

try:
    from . import yaml_math, view_data, worker, utils
except:
    # ST2
    import yaml_math
    import view_data
    import worker
    import utils


# Status key for sublime status bar
STATUS_BAR_ID = "yaml_nav"

# Filename with plugin settings
SETTINGS_FILE = "YAML Nav.sublime-settings"

# Delay in seconds after which symbols will be updated on buffer modification
UPDATE_SYMBOLS_DELAY = 0.4


def set_status(view, message):
    """
    Displays given message in the status bar of given view.
    """

    if message:
        utils.execute_in_sublime_main_thread(
            lambda: view.set_status(STATUS_BAR_ID, "YAML path: %s" % message))
    else:
        utils.execute_in_sublime_main_thread(
            lambda: view.erase_status(STATUS_BAR_ID))


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

    def on_load(self, view):
        if is_yaml_view(view):
            # Build list after file load
            self.update_yaml_symbols(view)

    def on_new(self, view):
        if is_yaml_view(view):
            # Build list after new buffer created
            self.update_yaml_symbols(view)

    def on_activated(self, view):
        if is_yaml_view(view):
            if not view.is_loading() and not view_data.get(view, "yaml_symbols"):
                # Rebuild list after plugin reload
                self.update_yaml_symbols(view)

            # Update current symbol after view change/quick navigation
            self.update_current_yaml_symbol(view)

    def on_modified(self, view):
        if is_yaml_view(view):
            # Save modification time to throttle symbols update
            view_data.set(view, "modified_at", time.time())

            # Rebuild list after file modification
            self.update_yaml_symbols(view)

    def on_selection_modified(self, view):
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

        def do_update():
            """
            Do actual symbols update in separate thread.
            """

            view_data.set(view, "yaml_symbols", yaml_math.get_yaml_symbols(view))

            # Also update current symbol because it may be changed
            self.update_current_yaml_symbol(view)

        def schedule_update():
            """
            Schedules symbols update.
            """

            modified_at = view_data.get(view, "modified_at")

            # Update symbols if last modification was more than UPDATE_SYMBOLS_DELAY ms. ago,
            # otherwise reschedule update
            if not modified_at or time.time() - modified_at > UPDATE_SYMBOLS_DELAY:
                view_data.set(view, "symbols_update_scheduled", False)
                worker.execute(do_update)
            else:
                view_data.set(view, "symbols_update_scheduled", True)
                sublime.set_timeout(schedule_update, int(UPDATE_SYMBOLS_DELAY * 1000))

        # Schedule update unless it already scheduled
        if not view_data.get(view, "symbols_update_scheduled"):
            view_data.set(view, "symbols_update_scheduled", True)
            sublime.set_timeout(schedule_update, int(UPDATE_SYMBOLS_DELAY * 1000))

    def update_current_yaml_symbol(self, view):
        """
        Calculates current selected YAML symbol and saves it in the view data.
        """

        all_symbols = view_data.get(view, "yaml_symbols")
        current_yaml_symbol = yaml_math.get_selected_yaml_symbol(all_symbols, view)

        view_data.set(view, "current_yaml_symbol", current_yaml_symbol)

        if current_yaml_symbol:
            set_status(view, current_yaml_symbol["name"])
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
        symbols = view_data.get(self.view, "yaml_symbols") or []

        def on_symbol_selected(index):
            if index >= 0:
                region = symbols[index]["region"]

                self.view.show_at_center(region)

                # Set cursor after YAML key
                self.view.sel().clear()
                self.view.sel().add(sublime.Region(region.end() + 1))

        self.view.window().show_quick_panel(
            list(map(lambda x: x["name"], symbols)), on_symbol_selected)

    def is_enabled(self):
        return is_yaml_view(self.view)


class CopyYamlSymbolToClipboardCommand(sublime_plugin.TextCommand):
    def __init__(self, *args):
        sublime_plugin.TextCommand.__init__(self, *args)

        # Load settings
        self.settings = sublime.load_settings(SETTINGS_FILE)
        self.detect_locale_filename_re = re.compile(self.settings.get("detect_locale_filename_re"), re.I)
        self.trim_language_tag_on_copy_from_locales = self.settings.get("trim_language_tag_on_copy_from_locales")

    def run(self, edit):
        """
        Copies selected YAML symbol into clipboard.
        """

        current_symbol = view_data.get(self.view, "current_yaml_symbol")

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
