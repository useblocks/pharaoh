"""Typer-style CLI with snake_case parameters rendered as kebab flags."""

from dataclasses import dataclass


@dataclass
class LicenseContext:
    license_key: str
    license_user: str
    license_stage: str


def run_command(
    license_key: str = "",
    license_user: str = "",
    license_stage: str = "",
) -> LicenseContext:
    return LicenseContext(license_key, license_user, license_stage)
