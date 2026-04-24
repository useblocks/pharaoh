# external-dotted-path

Axis-5 filter-step-#5 exercise. The CREQ cites `rich.console.Console`,
a third-party import path. The literal string does not appear in the
source `.py` as an identifier (the source has `from rich.console
import Console` and then uses bare `Console`).

The dotted-path filter splits the token into module + attribute and
checks for a matching `from <module> import <attr>` clause. When
present, the token is treated as resolved.
