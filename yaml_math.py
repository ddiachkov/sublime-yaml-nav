"""
This module provides functions for calculating YAML symbols.
"""

import sublime
import threading
import queue


def get_yaml_symbols(view):
    """
    Returns YAML key paths and associated regions for given sublime view.
    Paths calculated by key indentation level -- it's more efficient and secure, but doesn't support inline hashes.
    """

    # Get regions with YAML tags
    regions = get_view_regions(view, "entity.name.tag.yaml")

    # Read the entire buffer content into the memory: it is much much faster than multiple substr's
    content = get_view_content(view)

    symbols = []
    current_path = []

    for region in regions:
        key = content[region.begin():region.end() - 1]

        # Characters count from line beginning to key start position
        indent_level = region.begin() - content.rfind("\n", 0, region.begin()) - 1

        # Pop items from current_path while its indentation level less than current key indentation
        while len(current_path) > 0 and current_path[-1]["indent"] >= indent_level:
            current_path.pop()

        current_path.append({"key": key, "indent": indent_level})

        symbol_name = ".".join(map(lambda item: item["key"], current_path))
        symbols.append({"name": symbol_name, "region": region})

    return symbols


def get_selected_yaml_symbol(symbols, view):
    """
    Returns YAML symbol from given list for currently selected region in given
    sublime view.
    """

    if not symbols:
        return None

    selection = get_view_selected_lines(view)

    # 1 cursor
    if len(selection) == 1:
        # Reversing list because we are searching for the deepest key
        yaml_symbols = reversed(symbols)

        # Search for 1 intersection
        for selected_region in selection:
            for symbol in yaml_symbols:
                if selected_region.intersects(symbol["region"]):
                    return symbol

    else:
        # Ambigous symbol: multiple cursors
        return None


def get_view_regions(view, selector):
    """
    Returns regions for given selector in given view.
    """
    return execute_in_sublime_main_thread(lambda: view.find_by_selector( selector ))


def get_view_content(view):
    """
    Returns view content as string.
    """
    return execute_in_sublime_main_thread(lambda: view.substr(sublime.Region(0, view.size())))


def get_view_selected_lines(view):
    """
    Returns selected lines as regions in given view.
    """
    return execute_in_sublime_main_thread(lambda: [line for sel in view.sel() for line in view.lines(sel)])


# Main sublime thread
MAIN_THREAD = threading.current_thread()


def execute_in_sublime_main_thread(callback):
    """
    Executes callback in main sublime thread and returns its result.
    This is needed to mitigate memory leak in plugin_host.
    See https://github.com/DamnWidget/anaconda/issues/97
    """

    # If we already in main thread then just call th callback,
    # otherwise block current thread and schedule callback in main thread
    if threading.current_thread() == MAIN_THREAD:
        return callback()
    else:
        q = queue.Queue()
        sublime.set_timeout(lambda: q.put(callback()), 0)
        return q.get(block=True)
