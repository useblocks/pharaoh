"""Schema module — defines the config fields the consumer reads."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ExportConfig:
    target_path: Path = field(default=Path("needs.archive"))
    uuid_target: str = field(default="default_format")
    archive_suffix: str = field(default=".archive")
