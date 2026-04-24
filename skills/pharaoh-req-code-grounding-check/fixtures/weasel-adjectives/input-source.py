"""Diagnostic report writer — emits a list[dict] per row."""

import json


def write_report(rows: list[dict], out_path: str) -> None:
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
