"""CSV reader with four distinct observable branches."""

import csv


class CSVReadError(Exception):
    pass


def read_csv(path: str) -> list[dict]:
    try:
        with open(path, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
    except UnicodeDecodeError as exc:
        raise CSVReadError(f"encoding failure: {exc}") from exc
    except csv.Error as exc:
        raise CSVReadError(f"csv parse failure: {exc}") from exc

    if not rows:
        raise CSVReadError("input file produced zero rows")

    return rows
