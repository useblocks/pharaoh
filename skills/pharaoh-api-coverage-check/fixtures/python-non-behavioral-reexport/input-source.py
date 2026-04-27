"""Package __init__ that re-exports symbols from submodules.

Holds no behavior of its own — every name below is an import or a
module-level constant. The file should classify as non-behavioral and
be skipped by the coverage gate.
"""
from .client import InventoryClient
from .errors import InventoryError
from .loader import load_items, save_items

DEFAULT_TIMEOUT = 30
SUPPORTED_FORMATS = ("csv", "json", "parquet")

__all__ = [
    "InventoryClient",
    "InventoryError",
    "load_items",
    "save_items",
    "DEFAULT_TIMEOUT",
    "SUPPORTED_FORMATS",
]
