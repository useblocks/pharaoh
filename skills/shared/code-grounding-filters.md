# Code-grounding filter schema

Shared schema for the pluggable false-positive filter chain used by
`pharaoh-req-code-grounding-check` axis #5 (`backtick_symbol_in_source_doc`).

The base skill ships three universal filters (TOML section header, file-path /
command-string, short-prose acronym). Everything else — language-specific
import syntax, CLI framework conventions, env-var globs, literal-default
heuristics — comes from the project's `.pharaoh/project/code-grounding-filters.yaml`.
A project without the YAML runs only the three universal filters; authors get
more signal but more false positives, and the skill stays usable in any
language.

This file defines four parameterised **strategies**. The YAML lists which
strategies to enable and how to configure them. Strategies are the universal
shape (kebab transform, glob expansion, import-clause lookup, cross-file
default resolution); the parameters make them language-specific.

## Schema

```yaml
# .pharaoh/project/code-grounding-filters.yaml
filters:
  - name: <human-readable identifier>
    strategy: <one of: kebab_to_snake_or_pascal |
                        prefix_glob_expansion |
                        dotted_import_resolution |
                        cross_file_literal_default>
    token_regex: <Python regex matched against the bare backtick-quoted token>
    # per-strategy parameters (see below)
```

Filters run in declaration order; the first filter whose `token_regex` matches
AND whose strategy resolves the token short-circuits the chain. A token that
matches no filter and is not literally in `:source_doc:` fails axis #5.

## Strategy 1 — `kebab_to_snake_or_pascal`

Purpose: CREQ prose cites CLI flag or subcommand names in kebab form
(`--license-key`, `from-csv`) which CLI frameworks render from snake-case or
CamelCase identifiers in source.

Parameters:

| parameter | purpose | example |
|---|---|---|
| `morphology_prefixes` | list of CamelCase prefixes to also try (e.g. `["Opt"]` for Typer `TypeAlias` wrappers, `["Cmd"]` for some Clap patterns) | `["Opt"]` |
| `strip_leading` | characters to strip from the token before transform; empty list = no strip | `["--"]` |

Resolution: strip leading chars from token, replace `-` with `_`, check if
resulting `snake_case` string is in source. Additionally for each
`morphology_prefix`, check if `<prefix><PascalCase-snake-converted>` is in
source. Any hit resolves.

Example (Python / Typer):

```yaml
- name: typer_kebab
  strategy: kebab_to_snake_or_pascal
  token_regex: "^(--)?[a-z][a-z0-9]*(-[a-z0-9]+)+$"
  strip_leading: ["--"]
  morphology_prefixes: ["Opt"]
```

Example (Rust / Clap — same strategy, no morphology prefix):

```yaml
- name: clap_kebab
  strategy: kebab_to_snake_or_pascal
  token_regex: "^(--)?[a-z][a-z0-9]*(-[a-z0-9]+)+$"
  strip_leading: ["--"]
  morphology_prefixes: []
```

## Strategy 2 — `prefix_glob_expansion`

Purpose: CREQ cites a family of identifiers sharing a prefix via a trailing
`*` (`JAMA_*`, `OPT_*`).

Parameters:

| parameter | purpose | example |
|---|---|---|
| `separator_character` | char or empty string before `*` to strip in addition to the `*` itself | `"_"` |

Resolution: strip `*` and the `separator_character` suffix from the token,
compile regex `\b<prefix>[<separator>]?\w+\b`, search source. At least one
match resolves.

Example:

```yaml
- name: env_var_glob
  strategy: prefix_glob_expansion
  token_regex: "^[A-Z][A-Z0-9_]*_?\\*$"
  separator_character: "_"
```

## Strategy 3 — `dotted_import_resolution`

Purpose: CREQ cites an external symbol via a dotted path
(`rich.console.Console`, `std::fs::File`, `@nestjs/common:Injectable`) which
the source imports under a different surface form.

Parameters:

| parameter | purpose | example |
|---|---|---|
| `separator` | dotted-path separator in the CREQ token | `"."` |
| `import_patterns` | list of regex patterns that resolve the token, using `${mod}`, `${attr}`, `${tok}` placeholders | see below |

Resolution: split the token on `separator` into `mod` (everything before the
last separator) and `attr` (last segment). Substitute placeholders into each
pattern, compile regex, search source. Any hit resolves.

Example (Python):

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

Example (Rust):

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

Example (TypeScript):

```yaml
- name: ts_named_import
  strategy: dotted_import_resolution
  token_regex: "^@?[a-z][\\w/.-]*:[A-Z]\\w+$"
  separator: ":"
  import_patterns:
    - "import\\s*\\{[^}]*\\b${attr}\\b[^}]*\\}\\s*from\\s*['\"]${mod}['\"]"
```

## Strategy 4 — `cross_file_literal_default`

Purpose: CREQ cites a default-value literal (e.g. `"reqif_uuid"`) that lives
only in the config module, NOT in the consumer module named by `:source_doc:`.
Raised specifically for this flavour because the literal IS somewhere in the
project tree — just not in the cited file — and the review should distinguish
"token absent" from "token cited against the wrong file".

Parameters:

| parameter | purpose | example |
|---|---|---|
| `hint_dir_pattern` | directory glob where the defining module is expected to live; evidence names it when the heuristic fires | `"config/"` |
| `field_regex` | regex with `${tok}` placeholder, matched against the suspected defining file; captures the "this IS a default-value literal" signal | `field\\(default=["']${tok}["']\\)` |
| `search_root` | project subtree to scan for the defining module; default: inferred as the package root containing `:source_doc:` | `"src/"` |

Resolution: scan `search_root`. For each file whose path matches
`hint_dir_pattern`, apply `field_regex` with `${tok}` substituted. If any
file matches, DO NOT resolve — instead, emit evidence
`"'${tok}' is a default-value literal; lives in <matched-file>. Cite the
consumer-side attribute or retarget :source_doc: to <matched-file>."` so the
author knows which remediation to apply.

This is the one strategy that explicitly FAILS rather than resolves — because
the finding IS the value. A token that matches this strategy fails axis #5
with actionable evidence; without this strategy, the same token would fail
with the generic `"token not in source_doc"` message and the author would not
know where to look.

Example (Python dataclass `field(default=...)`):

```yaml
- name: python_dataclass_default
  strategy: cross_file_literal_default
  token_regex: "^[a-z_][a-z0-9_]*$"
  hint_dir_pattern: "config/"
  field_regex: "field\\(default=[\"']${tok}[\"']\\)"
```

Example (Rust `serde(default = "...")`):

```yaml
- name: rust_serde_default
  strategy: cross_file_literal_default
  token_regex: "^[a-z_][a-z0-9_]*$"
  hint_dir_pattern: "src/config/"
  field_regex: "#\\[serde\\(default\\s*=\\s*\"${tok}\"\\)\\]"
```

## Authoring

A fresh project obtains the YAML via `pharaoh-tailor-code-grounding-filters`.
That skill scans the codebase, detects which CLI framework / config style is
in use, and proposes a filter set. Humans review and accept.

Projects that want zero filters simply omit the YAML — the three universal
filters in the base skill cover the highest-signal false positives
(TOML section, file path, short prose) and the rest runs as plain substring
lookup in `:source_doc:`.

## Running without tailoring

Absent-or-empty `code-grounding-filters.yaml` is a legitimate configuration.
The base skill's three universal filters run unconditionally; nothing else
applies. The corpus gets stricter checking: tokens that would otherwise
resolve via language-specific conventions now fail axis #5 with
`"token not in source_doc"`. That is the correct default — the skill does
not guess the language / framework.

## Strategy addition

New strategies are added by extending this file and the base skill's
implementation. Do not encode project-specific semantics in strategy
parameters beyond the four listed above — projects that need a fundamentally
different resolution shape (e.g. macro expansion, cross-repo symbol lookup)
should land a new named strategy here rather than overloading one of the
existing four.
