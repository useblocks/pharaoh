# rust-clap

Rust + Clap + serde. Validates that the skill generalises across languages:
different separator (`::` not `.`), different import pattern (`use X::Y` not
`from X import Y`), different literal-default idiom (`#[serde(default=...)]`
not `field(default=...)`), different default directory hint (`src/config/`
included). Demonstrates that the four strategies carry enough parameters to
handle a language stack that shares zero syntax with Python.
