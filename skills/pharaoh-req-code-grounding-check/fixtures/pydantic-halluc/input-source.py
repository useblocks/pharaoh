"""Row record — dataclass, NOT pydantic."""

from dataclasses import dataclass


@dataclass
class RowRecord:
    sku: str
    quantity: int
    price: float


def parse_row(raw: dict) -> RowRecord:
    return RowRecord(
        sku=str(raw["sku"]),
        quantity=int(raw["quantity"]),
        price=float(raw["price"]),
    )
