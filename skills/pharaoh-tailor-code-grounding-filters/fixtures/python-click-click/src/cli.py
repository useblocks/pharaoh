"""Click CLI — no Opt TypeAlias convention."""

from dataclasses import dataclass, field

import click


@dataclass
class RunConfig:
    mode: str = field(default="prod")


@click.command()
@click.option("--license-key", help="License key")
def from_csv(license_key: str) -> None:
    _ = RunConfig()
