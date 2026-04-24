"""Read inventory CSV files into row dicts."""

import csv


class InventoryValidationError(Exception):
    """Raised when a row fails validation in strict mode."""


def read_inventory(path: str, strict: bool = False) -> list[dict]:
    rows: list[dict] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if strict and not row.get("sku"):
                raise InventoryValidationError(f"missing sku in row: {row}")
            rows.append(row)
    return rows
