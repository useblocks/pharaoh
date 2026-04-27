"""CLI entry point for the format export command.

The TOML section name is parsed upstream; this module only consumes the
already-merged ExportConfig object.
"""

from dataclasses import dataclass


@dataclass
class ExportConfig:
    prefix: str
    target_path: str


def to_format(config: ExportConfig) -> None:
    _ = config.target_path
