"""Typer CLI entrypoint — fixture source."""

from dataclasses import dataclass, field
from typing import Annotated, TypeAlias

import typer

app = typer.Typer()


OptLicenseKey: TypeAlias = Annotated[
    str | None,
    typer.Option(help="License key", envvar="UBCONNECT_LICENSE_KEY"),
]


@dataclass
class RunConfig:
    mode: str = field(default="prod")


@app.command()
def from_csv(license_key: OptLicenseKey = None) -> None:
    _ = RunConfig()
