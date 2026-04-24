# toml-section-filter

Axis-5 filter-step-#1 exercise. The CREQ cites `[myapp.to_format]`
in backticks — a TOML section header, not a Python identifier. Without
the filter, the token would fail axis 5 because it cannot be found in
any Python source. With the filter, it is skipped from the symbol
lookup (but the CREQ still has two other resolving tokens, so density
is healthy).

This covers the false-positive class where authors legitimately cite
configuration file anchors.
