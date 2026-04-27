"""Logger wrapper around rich.console.Console."""

from rich.console import Console


class Logger:
    def __init__(self) -> None:
        self.console = Console()

    def info(self, message: str) -> None:
        self.console.print(message)
