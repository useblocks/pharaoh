"""Dispatcher — routes items by origin, but not for the origin the CREQ claims."""


def dispatch_item(item: dict) -> str:
    origin_field = item.get("origin_field", "")
    if origin_field != "Sphinx-Needs":
        return "routed-to-default"
    return "skipped"
