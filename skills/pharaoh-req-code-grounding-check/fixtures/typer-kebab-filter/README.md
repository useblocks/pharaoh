# typer-kebab-filter

Axis-5 filter-step-#3 exercise. Typer renders `license_key: str =
typer.Option(...)` on the CLI as `--license-key`. Authors prose-cite
the kebab form, which does not literally appear in the source. The
kebab filter strips `--`, converts `-` → `_`, and re-checks; all three
flags resolve this way.

Covers a false-positive class that would otherwise poison any project
using Typer or Click — and prevents the check skill from fighting a
convention upstream of Pharaoh.
