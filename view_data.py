"""
Helper module to attach custom data to a sublime view instances.

Unfortunately sublime don't allows us to add custom attributes to views,
so we need some kind of external storage.
"""

from collections import defaultdict

# Dictionary: view ID => view data
__view_data = defaultdict(lambda: defaultdict(None))


def get(view, key):
    """
    Returns data for given view.
    """

    return __view_data[view.id()].get(key)


def set(view, key, value):
    """
    Sets data for given view.
    """
    __view_data[view.id()][key] = value


def clear(view):
    """
    Clears data for given view.
    """

    vid = view.id()

    if vid in __view_data:
        del __view_data[vid]
