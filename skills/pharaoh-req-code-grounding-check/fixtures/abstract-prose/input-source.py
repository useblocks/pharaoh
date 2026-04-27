"""CSV importer — concrete implementation that the abstract CREQ ignores."""

import csv


class CSVReadError(Exception):
    pass


def read_csv(path: str, delimiter: str = ",", encoding: str = "utf-8") -> list[dict]:
    try:
        with open(path, encoding=encoding) as fh:
            return list(csv.DictReader(fh, delimiter=delimiter))
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise CSVReadError(str(exc)) from exc
