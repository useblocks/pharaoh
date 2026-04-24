---
name: pharaoh-bootstrap
description: "Use when a Sphinx project has no sphinx-needs configured and you need minimum viable scaffolding — adding the extension and declaring need types — so that sphinx-build produces a valid needs.json for downstream Pharaoh skills."
chains_to: [pharaoh-setup]
---

# pharaoh-bootstrap

## When to use

Invoke when a project has a working Sphinx setup (`conf.py` builds without sphinx-needs) but does not yet load `sphinx_needs` as an extension. This skill injects the minimum configuration required for sphinx-needs to produce a valid `needs.json` on the next build. Downstream skills (`pharaoh-setup`, `pharaoh-tailor-detect`, `pharaoh-req-draft`, etc.) require that output.

Do NOT invoke if `sphinx_needs` is already listed in extensions — use `pharaoh-setup` for that case. Do NOT invoke on a directory that is not yet a Sphinx project — `sphinx-quickstart` is a prerequisite, not part of this skill. Do NOT seed stub RST files, build the project, or write `pharaoh.toml` — those are separate concerns.

## sphinx-needs version policy

Pharaoh **recommends** `sphinx-needs >= 8.0.0` (8.x consolidated TOML loading, type-field schema validation, and extra-link declaration format). It does **not** require it. Many real projects pin older versions for lockfile stability or compliance reasons; the skill respects that choice.

The version handling is a three-way branch:

| Detected state | Default behavior |
|---|---|
| Not installed | Propose installing the latest available `sphinx-needs`. User confirms → install; rejects → abort (no config written, since no install = nothing to configure). |
| Installed, `>= recommended` | Proceed silently. |
| Installed, `< recommended` | Propose upgrading to recommended. User picks: (a) upgrade; (b) accept current version and proceed; (c) abort. |

The skill never silently installs or upgrades; every mutation is gated by explicit confirmation (or by a caller passing `on_version_mismatch="install"` / `"accept"` for unattended flows).

## Atomicity

- (a) Indivisible — one `project_dir` + config spec in → `conf.py` and/or `ubproject.toml` edits out, plus at most one sphinx-needs version-alignment action (install / upgrade) gated by user confirmation. No directory creation beyond opening existing files; no RST seeding; no docs content; no Pharaoh-level config. The install step is a guarded side effect — it runs only when the caller's confirmation is received, never speculatively.
- (b) Input: `{project_dir: str, config_target: "auto"|"conf.py"|"ubproject.toml", types: list[TypeSpec], extra_links?: list[LinkSpec], extra_options?: list[str], id_required?: bool, id_length?: int, recommended_sphinx_needs_version?: str, on_version_mismatch?: "fail"|"prompt"|"install"|"accept"}` where `TypeSpec = {directive: str, title: str, prefix: str, color?: str, style?: str}` and `LinkSpec = {option: str, incoming: str, outgoing: str}`. `extra_options` defaults to `["source_doc"]` (Pharaoh convention — emitters like `pharaoh-feat-draft-from-docs` set `:source_doc:` on every emitted need; without the declaration, `sphinx-build -nW` fails with `Unknown option 'source_doc'`). `recommended_sphinx_needs_version` defaults to `"8.0.0"`; skill uses this to compute "latest satisfying" when installing, and as the threshold for "older than recommended" proposals. `on_version_mismatch` defaults to `"prompt"`. Output: JSON `{files_modified: list[str], config_target_used: "conf.py"|"ubproject.toml", sphinx_needs_version_before: str|null, sphinx_needs_version_after: str, version_action: "installed"|"upgraded"|"accepted_current"|"already_ok", install_command_used: str|null, warnings: list[str], next_step: str}`. On `"prompt"` path → single JSON `{status: "needs_confirmation", proposal: ...}` with no file writes and no install.
- (c) Reward: fixture covers four scenarios in separate test environments:

  **(i) fresh env (no sphinx-needs installed), `on_version_mismatch="install"`** — scorer checks:
  1. After run, `import sphinx_needs` succeeds with version `>= recommended`.
  2. `version_action == "installed"`, `sphinx_needs_version_before == null`.
  3. Config written and `sphinx-build -b needs` succeeds, producing empty `needs.json`.

  **(ii) env with `sphinx-needs >= recommended`, any `on_version_mismatch`** — scorer checks:
  1. `version_action == "already_ok"`, `install_command_used == null`.
  2. `sphinx_needs_version_before == sphinx_needs_version_after`.
  3. Config written and build succeeds.

  **(iii) env with old version (6.3.0), `on_version_mismatch="accept"`** — scorer checks:
  1. `version_action == "accepted_current"`, `install_command_used == null`.
  2. Config written and build succeeds with the OLD version (assuming the old version is still functional — this is the "user pinned deliberately" path).
  3. Output contains a warning naming the version gap.

  **(iv) env with old version (6.3.0), `on_version_mismatch="prompt"`** — scorer checks:
  1. Output is `{status: "needs_confirmation", proposal: ...}`.
  2. Proposal offers both `upgrade` and `accept` paths.
  3. No files modified. `import sphinx_needs` still reports the old version.

  Idempotence: re-run in the already-aligned state is a no-op (`version_action == "already_ok"`).

  Pass = all scenarios pass their checks.
- (d) Reusable: any first-time sphinx-needs adoption; migration from plain Sphinx; reverse-engineering pilots on projects that start without requirements. Independent of downstream Pharaoh workflow.
- (e) Composable: edits config + at most one guarded install. Does not call other skills, does not write `.pharaoh/`, does not build.

## Input

- `project_dir`: absolute path to the Sphinx project root. Must contain `conf.py`.
- `config_target`: where to declare sphinx-needs settings.
  - `"auto"` (default): if `ubproject.toml` exists in `project_dir`, use it; otherwise use `conf.py`.
  - `"ubproject.toml"`: force TOML. Create the file if missing.
  - `"conf.py"`: force Python-level declarations (`needs_types`, `needs_extra_links`, etc.).
- `types`: list of need types to declare. **Only declare types that will have at least one need on day one.** Declaring speculative types (e.g. adding `test` because you plan to write tests "eventually") produces dead type registrations and forces downstream `pharaoh.toml` traceability chains to alarm on empty targets — observed during dogfooding where declaring `test` + `verifies` link made 100% of `comp_req` needs appear unverified on day one. Add new types when the first need of that type lands, not before.

  Each `TypeSpec` has:
  - `directive` (required): snake_case directive name, e.g. `"req"`, `"spec"`, `"impl"`, `"test"`.
  - `title` (required): human-readable title, e.g. `"Requirement"`.
  - `prefix` (required): ID prefix used by sphinx-needs, e.g. `"REQ_"`.
  - `color` (optional): hex color or name; defaults left to sphinx-needs.
  - `style` (optional): node style; defaults left to sphinx-needs.

  At least one type is required; sphinx-needs builds with defaults but Pharaoh workflows expect explicit declarations.
- `extra_links` (optional): list of `LinkSpec` entries for typed relationships beyond the default `links` option.
- `extra_options` (optional): list of custom option names to declare. Default `["source_doc"]`. Pharaoh emitters (e.g. `pharaoh-feat-draft-from-docs`) always set `:source_doc:` on emitted needs to track provenance back to the authoring document; without this declaration, `sphinx-build -nW` fails with `Unknown option 'source_doc'`. Caller may pass additional option names — the skill unions them with the default. Passing `[]` explicitly suppresses the default (caller accepts the -nW warning as trade-off). Declaration SHAPE is version-dependent: on sphinx-needs ≥ 8.0.0 the skill emits `[needs.fields.NAME]` dict-of-dicts (config option `needs_fields`); on < 8 it emits the legacy `[[needs.extra_options]]` / `needs_extra_options`. The input name stays `extra_options` for API stability — callers pass a list of names and the skill picks the right shape.
- `id_required` (optional): if `true`, declare `needs_id_required = True`. Default: omit (sphinx-needs default is `False`).
- `id_length` (optional): integer; if provided, declare `needs_id_length`. Default: omit (sphinx-needs default).
- `recommended_sphinx_needs_version` (optional): the version Pharaoh recommends. Default `"8.0.0"`. Used as (a) the threshold for "older than recommended" proposals, and (b) the version installed when the skill runs in install mode (or the latest release that satisfies `>=recommended` — see Step 0c). Compared with `packaging.version.parse`.
- `on_version_mismatch` (optional): `"fail"` | `"prompt"` | `"install"` | `"accept"`. Default `"prompt"`. Applies when the detected version is absent OR `< recommended`:
  - `"fail"`: abort with a remediation-focused error.
  - `"prompt"`: emit a `needs_confirmation` proposal with BOTH an upgrade option and an accept-current option (or install/abort if nothing is installed). The caller picks one and re-invokes with `"install"` or `"accept"`.
  - `"install"`: if nothing installed → install recommended; if older version installed → upgrade to recommended. Non-interactive.
  - `"accept"`: proceed with whatever is installed. If nothing is installed → FAIL (there is no "current" to accept).

## Output

A single JSON object — no prose wrapper. Shape:

```json
{
  "files_modified": ["docs/conf.py"],
  "config_target_used": "conf.py",
  "sphinx_needs_version_before": "6.3.0",
  "sphinx_needs_version_after": "8.0.0",
  "version_action": "upgraded",
  "install_command_used": "uv pip install --upgrade sphinx-needs==8.0.0",
  "sphinx_build_command": "sphinx-build -b needs docs docs/_build/needs",
  "warnings": [],
  "next_step": "Run `sphinx-build -b needs docs docs/_build/needs` (see sphinx_build_command) to generate needs.json, then run pharaoh-setup."
}
```

`sphinx_build_command` is a concrete, copy-pasteable invocation that assumes the caller's cwd is the project root. Resolution:
- Builder flag: `-b needs`.
- `<sourcedir>`: the relative path from the detected project root to `project_dir` (the argument the skill was invoked with). If `project_dir` contains both `conf.py` and the .rst source tree (typical `sphinx-quickstart` flat layout), `<sourcedir>` is the project_dir path. If `conf.py` lives in one directory and .rst sources live in a sibling (e.g. `conf.py` in `docs/` but RST files under `docs/source/`), the command uses `-c <conf_dir> <source_dir>`; the skill detects this by checking whether the `conf.py` directory contains any `*.rst` files.
- `<outdir>`: `<sourcedir>/_build/needs` by convention.
- If the skill cannot resolve the project root relative to `project_dir` (e.g. `project_dir` is absolute with no parent that looks like a project root), it falls back to absolute paths.

`version_action` is one of:
- `"installed"` — was missing, installed recommended
- `"upgraded"` — was older than recommended, upgraded
- `"accepted_current"` — was older than recommended, user opted to keep it
- `"already_ok"` — detected version already `>= recommended`, no action taken

When `on_version_mismatch == "prompt"` and a mismatch is detected, response is:

```json
{
  "status": "needs_confirmation",
  "proposal": {
    "detected_version": "6.3.0",
    "recommended_version": "8.0.0",
    "detected_package_manager": "rye",
    "options": [
      {
        "action": "upgrade",
        "description": "Install sphinx-needs 8.0.0 (recommended). Unlocks TOML loading, schema validation, new extra-link format.",
        "install_command": "rye add sphinx-needs~=8.0.0",
        "alt_commands": [
          "uv pip install --upgrade sphinx-needs==8.0.0",
          "pip install --upgrade sphinx-needs==8.0.0"
        ],
        "pyproject_patch": {
          "target_file": "pyproject.toml",
          "section": "[project].dependencies",
          "replace": {"sphinx-needs>=6.3.0": "sphinx-needs>=8.0.0"}
        }
      },
      {
        "action": "accept",
        "description": "Keep sphinx-needs 6.3.0. Bootstrap proceeds against the current version. Some Pharaoh features that depend on 8.x (schema validation, latest TOML loader) may be degraded or unavailable.",
        "caveats": [
          "Downstream Pharaoh skills may warn about missing features.",
          "Upgrade can be deferred — re-run pharaoh-bootstrap later to revisit."
        ]
      },
      {
        "action": "abort",
        "description": "Cancel bootstrap without writing config or installing anything."
      }
    ],
    "rationale": "Pharaoh recommends sphinx-needs >= 8.0.0 for the richest feature set, but respects pinned older versions where the project has stability or compliance constraints."
  }
}
```

No files are modified and no installs happen when the response is `needs_confirmation`. The caller (human or outer LLM) picks an option and re-invokes with `on_version_mismatch` set accordingly (`"install"` for upgrade, `"accept"` for accept, or simply stop for abort).

The "nothing installed" variant of the same proposal drops the `accept` option (since there is no current version to accept) and the `upgrade` action becomes `install`.

## Process

### Step 0: Determine sphinx-needs version action

Before touching any config file, resolve what the skill should do about `sphinx-needs` — install, upgrade, accept, or proceed without action.

**0a. Detect current version.**

Run `python -c "import sphinx_needs; print(sphinx_needs.__version__)"` in the project's interpreter (virtualenv-preferred, active shell Python as fallback).

- Import succeeds → record printed version.
- Import fails → record `null`.

**0b. Classify and branch.**

Three classes:

1. **Installed and `>= recommended_sphinx_needs_version`** → set `version_action = "already_ok"`, `install_command_used = null`, `sphinx_needs_version_before = sphinx_needs_version_after = detected`. Skip to Step 1.

2. **Not installed** → branch on `on_version_mismatch`:
   - `"fail"` → FAIL with remediation message.
   - `"prompt"` → emit `needs_confirmation` proposal with options `["install", "abort"]` (no `accept` — nothing to accept). Return.
   - `"install"` → go to Step 0c with action=install.
   - `"accept"` → FAIL: `"on_version_mismatch='accept' requires an existing install, but sphinx-needs is not installed."`

3. **Installed but `< recommended`** → branch on `on_version_mismatch`:
   - `"fail"` → FAIL with remediation.
   - `"prompt"` → emit `needs_confirmation` proposal with options `["upgrade", "accept", "abort"]`. Return.
   - `"install"` → go to Step 0c with action=upgrade.
   - `"accept"` → set `version_action = "accepted_current"`, emit a warning naming the version gap, set `sphinx_needs_version_before = sphinx_needs_version_after = detected`, `install_command_used = null`. Skip to Step 1.

**0c. Detect package manager and run install/upgrade.**

Only reached when `on_version_mismatch == "install"`. Detect package manager by scanning `project_dir` and up to 3 parent levels:

| Indicator | Package manager | Install command | Upgrade command |
|---|---|---|---|
| `.python-version` + `pyproject.toml` with `[tool.rye]` or `rye.lock` | rye | `rye add sphinx-needs~=<rec>` | `rye add sphinx-needs~=<rec>` (rye resolves by constraint) |
| `uv.lock` or `pyproject.toml` with `[tool.uv]` | uv | `uv add sphinx-needs==<rec>` | `uv pip install --upgrade sphinx-needs==<rec>` |
| `poetry.lock` | poetry | `poetry add sphinx-needs@^<rec>` | `poetry add sphinx-needs@^<rec>` |
| `Pipfile.lock` | pipenv | `pipenv install sphinx-needs==<rec>` | `pipenv install sphinx-needs==<rec>` |
| `pdm.lock` | pdm | `pdm add sphinx-needs==<rec>` | `pdm update sphinx-needs` |
| otherwise, with active venv detectable via `VIRTUAL_ENV` or `project_dir/.venv` | pip (venv) | `<venv_python> -m pip install sphinx-needs==<rec>` | `<venv_python> -m pip install --upgrade sphinx-needs==<rec>` |
| otherwise | unknown | FAIL: "Cannot detect package manager. Install sphinx-needs manually and re-run with `on_version_mismatch='accept'` or `'install'` after install." |

Closer indicator wins if multiple match. `<rec>` substituted with `recommended_sphinx_needs_version`.

Run the selected command. Capture exit code and stdout/stderr.

**0d. Verify post-install.**

Re-run the probe from 0a. Determine final state:

- Import still fails → FAIL naming the attempted command and exit code.
- Version now `>= recommended` → set `version_action = "installed"` (if 0b class was "not installed") or `"upgraded"` (if class was "older"). Record `install_command_used` = the command. Proceed to Step 1.
- Version below recommended but installed (install appeared to succeed but resolver picked an older version, e.g. constrained by lockfile) → emit warning, set `version_action = "accepted_current"`, proceed. The caller's lockfile constraints win over Pharaoh's recommendation.

### Step 1: Verify project_dir is a Sphinx project

Read `<project_dir>/conf.py`. If it does not exist, FAIL:

```
FAIL: <project_dir>/conf.py not found.
This skill scaffolds sphinx-needs INTO an existing Sphinx project.
Run `sphinx-quickstart` first to create a Sphinx project, then re-invoke.
```

### Step 2: Verify sphinx-needs is not already configured

Search `conf.py` and (if present) `ubproject.toml` for the string `sphinx_needs`. If found in either file, FAIL:

```
FAIL: sphinx_needs is already referenced in <file>.
This skill is for projects without sphinx-needs. Use pharaoh-setup instead.
```

Rationale: mutating an existing config belongs to a separate skill (future: `pharaoh-setup-reconfigure`). Atomicity demands that `pharaoh-bootstrap` only handles first-time injection.

### Step 3: Resolve config_target

If `config_target == "auto"`:
- If `<project_dir>/ubproject.toml` exists → use `"ubproject.toml"`.
- Else → use `"conf.py"`.

Record the resolved target. Emit a warning if the caller passed `"ubproject.toml"` but the file does not exist (the skill will create it).

### Step 4: Inject `sphinx_needs` into the `extensions` list

This always happens in `conf.py`, regardless of `config_target` (sphinx loads extensions from `conf.py` only).

Read `conf.py`. Locate the `extensions = [...]` assignment. Two cases:

**4a. Extensions list exists.** Append `"sphinx_needs"` as the last entry, preserving existing indentation and trailing comma conventions. If the list is empty (`extensions = []`), replace with `extensions = ["sphinx_needs"]`.

**4b. Extensions list missing.** Append a new line `extensions = ["sphinx_needs"]` after the last existing top-level assignment (heuristic: find the last line that looks like `NAME = ...` at column 0, insert after it). Add a blank line before for readability.

Do NOT reorder, rename, or reflow existing content. Do NOT add comments.

### Step 5: Declare need types

**5a. If `config_target_used == "ubproject.toml"`:**

If the file does not exist, create it with a `$schema` header pointing at the public ubproject schema:

```toml
"$schema" = "https://ubcode.useblocks.com/ubproject.schema.json"
```

Append a `[needs]` section with the types array. Example:

```toml
[[needs.types]]
directive = "req"
title = "Requirement"
prefix = "REQ_"

[[needs.types]]
directive = "spec"
title = "Specification"
prefix = "SPEC_"
```

Include `color` and `style` entries only if the caller provided them.

Emit typed links and custom fields. **The shape depends on the detected `sphinx_needs_version_after` from Step 0.** sphinx-needs 8.x deprecated the pre-8 array-of-tables shape in favour of dict-of-dicts keyed by option name; emitting the legacy shape on 8.x triggers deprecation warnings at every build (`Config option "needs_extra_options" is deprecated. Please use "needs_fields" instead.`), and emitting the new shape on < 8 fails to load. The skill picks the right shape for the detected version.

**sphinx-needs ≥ 8.0.0 — dict-of-dicts:**

```toml
[needs.links.satisfies]
incoming = "is satisfied by"
outgoing = "satisfies"

[needs.fields.source_doc]
description = "Relative path to the documentation file that authored this need (Pharaoh provenance)."
schema = "string"
default = ""
```

On 8.x, `description` + `schema` + `default` are all required on each field entry; omitting any of them triggers a backward-compatibility warning. For caller-supplied option names without explicit metadata, the skill synthesises: `description = "<NAME> (Pharaoh-declared custom field)"`, `schema = "string"`, `default = ""`.

**sphinx-needs < 8.0.0 — array-of-tables (legacy shape):**

```toml
[[needs.extra_links]]
option = "satisfies"
incoming = "is satisfied by"
outgoing = "satisfies"

[[needs.extra_options]]
name = "source_doc"
```

On pre-8, `[[needs.extra_links]]` MUST be an array of tables — dict form (`[needs.extra_links.satisfies]`) fails with `TypeError: string indices must be integers`.

Version comparison uses `packaging.version.parse`. Resolved `extra_options` = default `["source_doc"]` unioned with caller-provided extras, deduplicated, sorted for determinism.

If caller explicitly passed `extra_options = []`, emit no field/option section and record a warning: `"extra_options suppressed by caller; Pharaoh emitters that set :source_doc: will trigger -nW warnings"`.

Include `id_required` and `id_length` only if the caller provided them:

```toml
[needs]
id_required = true
id_length = 8
```

Also add the `needs_from_toml` hook to `conf.py` so sphinx-needs reads the TOML:

```python
needs_from_toml = "ubproject.toml"
```

Insert this line after the `extensions = [...]` assignment that was touched in Step 4.

**5b. If `config_target_used == "conf.py"`:**

Append `needs_types` plus version-dependent link/field declarations plus optional ID settings directly to `conf.py` after the `extensions` assignment. The config-option names match the TOML shape chosen in Step 5a.

**sphinx-needs ≥ 8.0.0 — `needs_links` / `needs_fields` dicts:**

```python
needs_types = [
    {"directive": "req", "title": "Requirement", "prefix": "REQ_"},
    {"directive": "spec", "title": "Specification", "prefix": "SPEC_"},
]

needs_links = {
    "satisfies": {
        "incoming": "is satisfied by",
        "outgoing": "satisfies",
    },
}

needs_fields = {
    "source_doc": {
        "description": "Relative path to the documentation file that authored this need.",
        "schema": "string",
        "default": "",
    },
}

needs_id_required = True
needs_id_length = 8
```

**sphinx-needs < 8.0.0 — legacy `needs_extra_links` / `needs_extra_options`:**

```python
needs_types = [
    {"directive": "req", "title": "Requirement", "prefix": "REQ_"},
    {"directive": "spec", "title": "Specification", "prefix": "SPEC_"},
]

needs_extra_links = [
    {"option": "satisfies", "incoming": "is satisfied by", "outgoing": "satisfies"},
]

needs_extra_options = ["source_doc"]

needs_id_required = True
needs_id_length = 8
```

Omit link/field declarations the caller did not supply (no `extra_links` input AND default `extra_options` not suppressed → emit only the `source_doc` field/option). Omit `needs_id_*` entries the caller did not supply. Always emit the `source_doc` declaration unless caller explicitly passed `extra_options = []` (in which case omit and warn — see Step 5a). Do NOT add comments.

### Step 6: Emit output

Emit the JSON object per the Output shape. Populate:
- `files_modified`: every file the skill wrote to, relative to `project_dir`.
- `config_target_used`: resolved target from Step 3.
- `warnings`: accumulated warnings (e.g., created `ubproject.toml` that did not exist).
- `sphinx_build_command`: resolved per the rules in the Output section. Prefer paths relative to the detected project root (the nearest ancestor of `project_dir` that contains a `pyproject.toml`, `.git`, or similar marker). If no project root is detectable, use absolute paths. If `project_dir` does not contain any `*.rst` files but `<project_dir>/source/` does (separated layout), emit `sphinx-build -b needs -c <project_dir> <project_dir>/source <project_dir>/source/_build/needs`.
- `next_step`: interpolate `sphinx_build_command` into the sentence `"Run \`<sphinx_build_command>\` to generate needs.json, then run pharaoh-setup."`

## Guardrails

**G1 — No Sphinx project.** `conf.py` missing → FAIL per Step 1.

**G2 — sphinx-needs already present.** Any reference to `sphinx_needs` found → FAIL per Step 2. Do not attempt merge; that is a different skill.

**G3 — Empty types list.** If `types == []`, FAIL:

```
FAIL: At least one type must be declared.
Pharaoh workflows expect explicit type declarations. Provide at least one TypeSpec.
```

**G4 — Directive collision.** If two entries in `types` have the same `directive`, FAIL with the offending directive name. Deduplication is the caller's responsibility.

**G5 — Partial write.** If Step 4 succeeds but Step 5 fails, revert Step 4's change so the project is not left in a half-configured state. Report the failure and the rollback.

## Advisory chain

After successfully emitting output, always advise with the CONCRETE command resolved for this project (the value of the `sphinx_build_command` output field), not a placeholder:

```
Run `<sphinx_build_command>` to generate needs.json.
Then invoke `pharaoh-setup` to detect the fresh configuration and author pharaoh.toml.
```

Rationale: prior dogfooding had `conf.py` in `docs/` and RST files in `docs/source/`; the generic `<source> <outdir>` template forced the caller to grep `pyproject.toml` to find the right `-c` flag before the first build succeeded. Surfacing the concrete invocation in the bootstrap report removes that lookup.

## Worked example

**User input:**
```json
{
  "project_dir": "/work/my-project/docs",
  "config_target": "auto",
  "types": [
    {"directive": "feat", "title": "Feature", "prefix": "FEAT_"},
    {"directive": "comp_req", "title": "Component Requirement", "prefix": "CREQ_"}
  ],
  "extra_links": [
    {"option": "satisfies", "incoming": "is satisfied by", "outgoing": "satisfies"}
  ]
}
```

**Step 1:** `/work/my-project/docs/conf.py` exists. OK.

**Step 2:** Neither `conf.py` nor `ubproject.toml` mentions `sphinx_needs`. OK.

**Step 3:** `ubproject.toml` exists in `/work/my-project/docs/` → resolve to `"ubproject.toml"`.

**Step 4:** Append `"sphinx_needs"` to the existing `extensions = [...]` list in `conf.py`.

**Step 5:** Add `[[needs.types]]` tables for `feat` and `comp_req` to `ubproject.toml`. Emit link and field declarations in the shape matching the detected sphinx-needs version — `[needs.links.satisfies]` and `[needs.fields.source_doc]` on ≥ 8.0.0, or the legacy `[[needs.extra_links]]` / `[[needs.extra_options]]` on < 8. Add `needs_from_toml = "ubproject.toml"` to `conf.py`.

**Step 6 output:**

```json
{
  "files_modified": ["conf.py", "ubproject.toml"],
  "config_target_used": "ubproject.toml",
  "sphinx_build_command": "sphinx-build -b needs docs docs/_build/needs",
  "warnings": [],
  "next_step": "Run `sphinx-build -b needs docs docs/_build/needs` to generate needs.json, then run pharaoh-setup."
}
```
