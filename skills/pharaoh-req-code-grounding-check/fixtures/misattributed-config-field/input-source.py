"""Exporter consumes a config object via attribute access only.

Literal default values (e.g. field defaults) live in the config module
under config/ — not in this consumer module.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Exporter:
    config: object

    def export(self, needs: list[dict]) -> Path:
        target = self.config.target_path
        for need in needs:
            need[self.config.uuid_target] = need["id"]
        target.write_bytes(b"<reqif/>")
        return target
