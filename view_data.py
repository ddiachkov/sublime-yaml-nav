"""
Helper module to attach custom data to sublime views.
"""

from collections import defaultdict

try:
    from . import utils
except:
    # ST2
    import utils


# Dictionary: view ID => view data
__view_data = defaultdict(lambda: defaultdict(None))


def get(view, key):
    """
    Returns data for the given view.
    """

    return __view_data[view_id(view)].get(key)


def set(view, key, value):
    """
    Sets data for the given view.
    """

    __view_data[view_id(view)][key] = value


def clear(view):
    """
    Clears data for the given view.
    """

    vid = view_id(view)

    if vid in __view_data:
        del __view_data[vid]


def view_id(view):
    """
    Returns views ID.
    """

    return utils.execute_in_sublime_main_thread(lambda: view.id())
