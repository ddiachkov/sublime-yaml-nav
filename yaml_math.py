"""
This module provides functions for calculating YAML symbols.
"""

def get_yaml_symbols(view):
    """
    Returns YAML key paths and associated regions for given sublime view.
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


def get_selected_yaml_symbol(symbols, view):
    """
    Returns YAML symbol from given list for currently selected region in given
    sublime view.
    """

    if not symbols:
        return None

    selection = view.sel()

    # 1 cursor
    if len(selection) == 1:
        selected_lines = view.lines(selection[0])

        # 1 selected line
        if len(selected_lines) == 1:
            cursor_line = selected_lines[0]

            # Reversing list because we are searching for the deepest key
            yaml_symbols = reversed(symbols)

            for symbol in yaml_symbols:
                if cursor_line.intersects(symbol["region"]):
                    return symbol

            return None

        else:
            # Ambigous symbol: multiple lines selected
            return None

    else:
        # Ambigous symbol: multiple cursors
        return None
