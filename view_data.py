"""
Helper module to attach custom data to a sublime view instances.

Unfortunately sublime don't allows us to add custom attributes to views,
so we need some kind of external storage.
"""

# Dictionary: view ID => view data
__view_data = dict()


class ViewData(dict):
    """
    Custom dictionary to store view data. Allows get/set attributes using
    dynamic methods.
    """

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
    __missing__ = lambda self, key: None


def get(view):
    """
    Returns data for given view.
    """

    vid = view.id()

    if vid not in __view_data:
        __view_data[vid] = ViewData()

    return __view_data[vid]


def clear(view):
    """
    Clears data for given view.
    """

    vid = view.id()

    if vid in __view_data:
        del __view_data[vid]
