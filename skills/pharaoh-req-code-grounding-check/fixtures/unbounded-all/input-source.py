"""Validator pipeline with thirteen distinct validators."""


def _check_sku(row):
    return row.get("sku") and True


def _check_quantity_positive(row):
    return row.get("quantity", 0) > 0


def _check_quantity_int(row):
    return isinstance(row.get("quantity"), int)


def _check_price_positive(row):
    return row.get("price", 0) > 0


def _check_price_float(row):
    return isinstance(row.get("price"), (int, float))


def _check_currency_set(row):
    return "currency" in row


def _check_currency_iso(row):
    return row.get("currency", "") in {"USD", "EUR", "GBP"}


def _check_supplier_set(row):
    return "supplier" in row


def _check_supplier_known(row):
    return row.get("supplier", "") != ""


def _check_category_set(row):
    return "category" in row


def _check_category_known(row):
    return row.get("category", "") in {"A", "B", "C"}


def _check_timestamp_set(row):
    return "timestamp" in row


def _check_timestamp_iso(row):
    return str(row.get("timestamp", "")).count("-") == 2


VALIDATORS = [
    _check_sku,
    _check_quantity_positive,
    _check_quantity_int,
    _check_price_positive,
    _check_price_float,
    _check_currency_set,
    _check_currency_iso,
    _check_supplier_set,
    _check_supplier_known,
    _check_category_set,
    _check_category_known,
    _check_timestamp_set,
    _check_timestamp_iso,
]


def validate(row: dict) -> list[str]:
    errors: list[str] = []
    for fn in VALIDATORS:
        if not fn(row):
            errors.append(fn.__name__)
    return errors
