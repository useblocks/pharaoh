# python-typer

Typer + dataclass + uppercase env-var convention. Exercises all four filter
strategies being emitted together. Validates that:

- Kebab filter includes `morphology_prefixes: ["Opt"]` (Typer-specific).
- Env-var glob is emitted because ≥3 `JAMA_*` identifiers share a prefix.
- Python import strategy is emitted because `import` / `from … import` are
  observed.
- Dataclass-default literal strategy is emitted because `field(default=...)`
  is observed.
