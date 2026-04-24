---
name: pharaoh-tailor-code-grounding-filters
description: Use when authoring a project's `code-grounding-filters.yaml` from observed stack conventions. Detects language + CLI framework + config-object style in the project source tree and emits a tailoring YAML populated with the four parameterised filter strategies. Does not invoke `pharaoh-req-code-grounding-check`; purely produces tailoring.
chains_to: [pharaoh-tailor-review]
---

# pharaoh-tailor-code-grounding-filters

## When to use

Invoke once per project, before running `pharaoh-req-code-grounding-check` at scale, to populate `.pharaoh/project/code-grounding-filters.yaml`. Inspects a project source tree, detects which CLI framework / import syntax / config-default idiom the code uses, and emits a filter YAML whose `filters:` entries wire up the four strategies in [`../shared/code-grounding-filters.md`](../shared/code-grounding-filters.md) to the detected stack.

Do NOT invoke to validate an existing filter YAML — that is part of `pharaoh-tailor-review`. Do NOT invoke to apply filters to a CREQ — that is `pharaoh-req-code-grounding-check`. This skill only reads the codebase and writes one YAML.

## Atomicity

- (a) Indivisible: one source-tree in → one filter-YAML + detection report out. No CREQ scoring, no plan dispatch, no coupling to other tailor skills beyond emitting YAML in the format the target skill reads.
- (b) Input: `{project_root: str, output_path?: str, on_existing?: "fail"|"overwrite"|"skip"}`. Output: JSON `{detected: {language, cli_framework, config_style, import_style}, emitted_filters: [...], yaml_path: str, warnings: [...]}` plus the YAML written to `output_path`.
- (c) Reward: fixtures under `skills/pharaoh-tailor-code-grounding-filters/fixtures/`:
  1. `python-typer/` — source tree with `import typer`, `def from_csv(...)`, `TypeAlias = Annotated[..., typer.Option(...)]` markers → emits `typer_kebab` (with `Opt` morphology), `python_import`, `python_dataclass_default`, and `env_var_glob` (if `os.environ` or `envvar=` usages detected).
  2. `python-click-click/` — source tree with `import click`, `@click.command()`, `click.option(...)` markers → emits `click_kebab` (no `Opt` morphology because Click projects do not use the `Opt` TypeAlias convention), `python_import`, `python_dataclass_default`.
  3. `rust-clap/` — source tree with `use clap::...`, `#[derive(Parser)]`, `#[arg(long)]` markers → emits `clap_kebab`, `rust_use_clause`, `rust_serde_default` (when `serde(default="...")` is detected).

  Pass = each fixture's emitted YAML matches `expected-filters.yaml` by substring inclusion of every declared filter's `strategy` + `name`, and the detection report matches `expected-report.json` on `detected.*` fields.
- (d) Reusable: any project regardless of language — the detection matrix is a bounded table (roughly: Python, Rust, TypeScript, Go), each detection slot independently optional.
- (e) Read-only wrt source code. Writes one YAML file at `output_path`. Running twice with `on_existing="skip"` is a no-op.

## Input

- `project_root`: absolute path to the project root. The skill walks up to 3 levels deep looking for source files; skips `node_modules`, `target`, `.venv`, `dist`, `build`, `__pycache__`.
- `output_path`: absolute path to write the YAML. Default: `<project_root>/.pharaoh/project/code-grounding-filters.yaml`.
- `on_existing`: `"fail"` (default — refuse to overwrite), `"overwrite"` (replace the file), `"skip"` (if file exists, return without writing; still returns the detection report for review).

## Detection matrix

The skill walks the source tree and greps for language + framework markers. Each detection is boolean (present / absent). Multiple languages can coexist; the emitted YAML gets filters for every detected stack.

### Language detection

| language | markers (any-of) |
|---|---|
| python | file extension `.py` AND (`^import\s` OR `^from\s.*\simport\s` OR `^def\s` OR `^class\s`) |
| rust | file extension `.rs` AND (`^use\s` OR `^fn\s` OR `^struct\s` OR `^enum\s`) |
| typescript | file extension `.ts` or `.tsx` AND (`^import\s` OR `^export\s`) |
| go | file extension `.go` AND (`^package\s` OR `^import\s`) |

### CLI framework detection (Python)

| framework | markers (any-of) |
|---|---|
| typer | `import typer` OR `typer.Typer()` OR `typer.Option` OR `@.*_app\.command` |
| click | `import click` OR `@click\.command` OR `click\.option` |
| argparse | `argparse\.ArgumentParser` |
| none | no matches |

### CLI framework detection (Rust)

| framework | markers (any-of) |
|---|---|
| clap | `use clap::` OR `#\[derive\(.*Parser.*\)\]` OR `#\[arg\(` OR `#\[command\(` |
| structopt | `use structopt::` OR `#\[derive\(.*StructOpt.*\)\]` |
| none | no matches |

### CLI framework detection (Go)

| framework | markers (any-of) |
|---|---|
| cobra | `github.com/spf13/cobra` OR `cobra.Command` |
| urfave-cli | `github.com/urfave/cli` |
| flag | `"flag"` import |
| none | no matches |

### Config-default idiom detection

| idiom | markers (any-of) |
|---|---|
| python_dataclass | `@dataclass` AND `field\(default=` |
| python_pydantic | `from pydantic` AND `Field\(default=` |
| python_attrs | `import attr` OR `@attr.s` |
| rust_serde | `#\[derive\(.*Deserialize.*\)\]` AND `#\[serde\(default` |
| go_struct_tag | `` `json:"` `` with `default:` stanza |
| none | no matches |

### Env-var convention detection

| style | markers |
|---|---|
| uppercase-prefix | ≥3 distinct `[A-Z][A-Z0-9_]+_\w+` identifiers declared as env var strings, sharing a common prefix of ≥3 chars |
| none | fewer than 3 |

If uppercase-prefix style IS detected, also detect the **prefix** — the longest common uppercase run across observed env-var identifiers (e.g. `JAMA_` from `JAMA_URL_ENV`, `JAMA_USERNAME_ENV`, ...). The prefix is NOT encoded into the filter (prefix is per-call from the CREQ token), only the strategy itself is enabled.

## Emission rules

After detection, build the `filters:` list in this order (deterministic for fixture comparison):

1. **Kebab filter** — one entry if any CLI framework was detected. Name the filter after the framework (`typer_kebab`, `click_kebab`, `clap_kebab`, `cobra_kebab`). Parameters:
   - `token_regex`: `"^(--)?[a-z][a-z0-9]*(-[a-z0-9]+)+$"`
   - `strip_leading`: `["--"]`
   - `morphology_prefixes`: `["Opt"]` only for `typer` (that convention is Typer-specific); `[]` otherwise.

2. **Env-var glob** — one entry if uppercase-prefix style was detected. Name `env_var_glob`. Parameters:
   - `token_regex`: `"^[A-Z][A-Z0-9_]*_?\\*$"`
   - `separator_character`: `"_"`

3. **Dotted import resolution** — one entry per language with a known import syntax. Parameters differ by language:

   **Python:**
   ```yaml
   - name: python_import
     strategy: dotted_import_resolution
     token_regex: "^[a-z][\\w.]*\\.[A-Z]\\w+$"
     separator: "."
     import_patterns:
       - "from\\s+${mod}\\s+import\\s+${attr}"
       - "import\\s+${mod}\\b"
       - "${tok}"
   ```

   **Rust:**
   ```yaml
   - name: rust_use_clause
     strategy: dotted_import_resolution
     token_regex: "^[a-z][\\w]*(::[\\w]+)+$"
     separator: "::"
     import_patterns:
       - "use\\s+${tok}"
       - "use\\s+${mod}::\\{[^}]*\\b${attr}\\b[^}]*\\}"
       - "${tok}"
   ```

   **TypeScript:**
   ```yaml
   - name: ts_named_import
     strategy: dotted_import_resolution
     token_regex: "^@?[a-z][\\w/.-]*:[A-Z]\\w+$"
     separator: ":"
     import_patterns:
       - "import\\s*\\{[^}]*\\b${attr}\\b[^}]*\\}\\s*from\\s*['\"]${mod}['\"]"
   ```

   **Go:**
   ```yaml
   - name: go_import
     strategy: dotted_import_resolution
     token_regex: "^[a-z][\\w/.-]*\\.[A-Z]\\w+$"
     separator: "."
     import_patterns:
       - "\"${mod}\"\\s*$"
       - "${tok}"
   ```

4. **Literal-default** — one entry per detected config-default idiom:

   - `python_dataclass` → `python_dataclass_default` with `field\\(default=[\"']${tok}[\"']\\)` and `hint_dir_pattern: "config/"`.
   - `python_pydantic` → `python_pydantic_default` with `Field\\(default=[\"']${tok}[\"']\\)` and `hint_dir_pattern: "config/|models/"`.
   - `rust_serde` → `rust_serde_default` with `#\\[serde\\(default\\s*=\\s*\"${tok}\"\\)\\]` and `hint_dir_pattern: "config/|src/config/"`.
   - Absent → omit this filter (the skill's other axes still catch the CREQ; the actionable evidence is just missing).

## Output

```json
{
  "detected": {
    "languages": ["python"],
    "cli_framework": "typer",
    "config_default_idiom": "python_dataclass",
    "env_var_style": "uppercase-prefix",
    "detected_env_prefix": "JAMA_"
  },
  "emitted_filters": [
    "typer_kebab",
    "env_var_glob",
    "python_import",
    "python_dataclass_default"
  ],
  "yaml_path": "/abs/path/to/.pharaoh/project/code-grounding-filters.yaml",
  "warnings": []
}
```

`warnings` surfaces any ambiguity: two CLI frameworks co-detected (emits filters for both and warns), no language detected (emits empty `filters:` and warns), config idiom detected without matching dirs on disk (emits filter, warns that `hint_dir_pattern` may not match anything at review time).

## Composition

Role: `tailor-author`.

Runs once per project during bootstrap, typically chained after `pharaoh-tailor-detect` and before `pharaoh-tailor-review`. Its output feeds `pharaoh-req-code-grounding-check` via the `tailoring_path` input. Never invokes emission or review skills; produces YAML that other skills consume.
