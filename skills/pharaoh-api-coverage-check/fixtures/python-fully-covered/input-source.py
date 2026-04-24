"""Inventory client module."""


class InventoryError(Exception):
    """Base class for inventory errors."""


def load_items(path):
    if not path:
        raise InventoryError("path required")
    return []


def save_items(path, items):
    if items is None:
        raise InventoryError("items required")
    return True


class InventoryClient:
    def connect(self):
        return True

    def _reset(self):
        # private helper — not part of the public surface
        return None
