"""Client module that raises both a project-defined and a stdlib exception."""

from errors import CatalogError


def load_entry(row: dict) -> dict:
    """Validate and load one catalog entry."""
    if not row:
        raise ValueError("empty row")
    if "id" not in row:
        raise CatalogError("row missing id")
    if len(row["id"]) < 1:
        raise ValueError("empty id")
    return {"id": row["id"], "data": row.get("data")}
