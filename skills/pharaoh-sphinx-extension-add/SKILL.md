---
name: pharaoh-sphinx-extension-add
description: Use when you need to idempotently add one or more sphinx extension modules to a project's `conf.py` extensions list, optionally installing the corresponding pypi packages via the detected package manager. Invoked by plans produced by pharaoh-write-plan when a diagram-emitting task requires a renderer extension that `conf.py` does not yet load. Does NOT emit RST. Does NOT build.
---

# pharaoh-sphinx-extension-add

## When to use

Invoke when a plan requires a Sphinx extension that `conf.py` does not currently load (e.g. `sphinxcontrib.mermaid` for Mermaid diagrams, `sphinxcontrib.plantuml` for PlantUML, `sphinx_needs` for sphinx-needs itself). Typical caller: `pharaoh-execute-plan` executing a task that `pharaoh-write-plan` inserted as a prerequisite to a diagram-emitting task when Step 3.5's dep probe found a missing extension.

Do NOT invoke to set arbitrary `conf.py` variables — this skill only touches the `extensions` list (and optionally triggers a pypi install). Do NOT invoke to load `sphinx_needs` on a project that never had sphinx-needs — that is `pharaoh-bootstrap`'s indivisible concern (which already includes extension injection as part of the bootstrap transaction).

## Atomicity

- (a) **Indivisible.** One `conf.py` + one extension list in → one updated `conf.py` (and optionally one package-manager install) out. No other `conf.py` mutation. No RST edits. No downstream skill invocation.
- (b) **Typed I/O.**
  - Input: `{conf_py: str, extensions: list[str], install_if_missing: bool, on_package_manager_missing?: "fail"|"warn"|"skip", reporter_id: str}`.
  - Output: `{files_modified: list[str], extensions_added: list[str], extensions_already_present: list[str], install_command_used: str | null, packages_installed: list[str], warnings: list[str]}`. Idempotent: when the extensions are already present AND (installed OR `install_if_missing == false`), `files_modified` and `install_command_used` are empty.
- (c) **Execution-based reward.** Fixture `pharaoh-validation/fixtures/pharaoh-sphinx-extension-add/`:
  - `case_fresh/conf.py` — has `extensions = ['sphinx_needs']`. Call with `extensions: ['sphinxcontrib.mermaid']`, `install_if_missing: true`. Scorer asserts (1) `conf.py` now has both entries, (2) `sphinxcontrib-mermaid` is importable, (3) `extensions_added == ['sphinxcontrib.mermaid']`, (4) `packages_installed == ['sphinxcontrib-mermaid']`.
  - `case_already_present/conf.py` — has `['sphinx_needs', 'sphinxcontrib.mermaid']`. Same call. Scorer asserts (1) `conf.py` unchanged (byte-identical), (2) `extensions_added == []`, `extensions_already_present == ['sphinxcontrib.mermaid']`, (3) `install_command_used is null`.
  - `case_no_install/conf.py` — has `['sphinx_needs']`, extension `sphinxcontrib.plantuml` NOT installed. Call with `install_if_missing: false`. Scorer asserts (1) `conf.py` now has the entry, (2) `packages_installed == []`, (3) `warnings` contains one entry naming the missing package.
  - Idempotence: re-running any case returns `files_modified == []`, `extensions_added == []`.
- (d) **Reusable.** Any Sphinx project, any extension. Not tied to diagrams — a future use case might be adding `sphinxcontrib.bibtex` or `myst_parser`.
- (e) **Composable.** Invoked inline (by `pharaoh-execute-plan` per plan task) or by humans via the CLI. Does not call other skills.

## Input

- `conf_py` (required): absolute path to a Sphinx `conf.py`. Must exist and be parseable Python.
- `extensions` (required): list of extension module paths (the strings that go inside `extensions = [...]`). Example: `["sphinxcontrib.mermaid"]`, `["sphinxcontrib.plantuml", "myst_parser"]`.
- `install_if_missing` (required): bool. If `true` and an extension module is not importable, attempt a package install before editing `conf.py` (order: install first, then edit, so a failed install does not leave `conf.py` referencing a missing module). If `false`, edit `conf.py` regardless of importability; record a warning per missing module.
- `on_package_manager_missing` (optional): `"fail"` | `"warn"` | `"skip"`. Default `"warn"`. Applies only when `install_if_missing` is `true` and no package manager is detectable (see package-manager detection table below).
  - `"fail"`: abort before any edit.
  - `"warn"`: log warning, proceed to edit `conf.py` anyway (user will install manually).
  - `"skip"`: silently proceed to edit (no warning). Used by callers that intentionally edit `conf.py` in environments where pypi installation is handled elsewhere (e.g. CI build image pre-baked).
- `reporter_id` (required): short agent id, for audit logs.

## Output

```json
{
  "files_modified": ["docs/conf.py"],
  "extensions_added": ["sphinxcontrib.mermaid"],
  "extensions_already_present": [],
  "install_command_used": "uv pip install sphinxcontrib-mermaid",
  "packages_installed": ["sphinxcontrib-mermaid"],
  "warnings": []
}
```

`install_command_used` is `null` when nothing was installed.

`packages_installed` lists the pypi package names (not the extension module paths — those differ: module `sphinxcontrib.mermaid` ships in pypi package `sphinxcontrib-mermaid`; see the extension → package resolution table).

## Process

### Step 0: Parse `conf.py`'s current extensions list

Read `conf_py`. Locate the `extensions = [...]` assignment. Three cases:

1. **Assignment present and parseable.** Extract the current list as a Python list of strings.
2. **Assignment missing.** Record empty list; the Edit step will append a new assignment.
3. **Parse error on the assignment** (e.g. `extensions = get_extensions()`). Abort:
   ```
   FAIL: extensions = ... in conf.py is not a literal list. This skill cannot safely mutate computed extension lists. Edit manually.
   ```

### Step 1: Classify each requested extension

For each entry in input `extensions`:

- **Already present** in the parsed current list → add to `extensions_already_present`, skip.
- **Missing AND importable** (`python -c "import <module_path>"` exits zero) → target for edit only, no install.
- **Missing AND not importable** → target for install + edit (if `install_if_missing`), or edit + warn (if not).

### Step 2: Install (conditional)

Only if `install_if_missing == true` AND the target set from Step 1 includes one or more non-importable modules.

**2a. Resolve pypi package names.** Use the extension → pypi resolution table:

| Extension module          | Pypi package             |
| ------------------------- | ------------------------ |
| `sphinxcontrib.mermaid`   | `sphinxcontrib-mermaid`  |
| `sphinxcontrib.plantuml`  | `sphinxcontrib-plantuml` |
| `sphinxcontrib.bibtex`    | `sphinxcontrib-bibtex`   |
| `myst_parser`             | `myst-parser`            |
| `sphinx_copybutton`       | `sphinx-copybutton`      |
| `sphinx_design`           | `sphinx-design`          |
| `sphinx_needs`            | `sphinx-needs`           |
| `sphinx_codelinks`        | `sphinx-codelinks`       |
| `sphinxcontrib.<name>`    | `sphinxcontrib-<name>`   (default rule when not otherwise listed) |
| `<other>`                 | `<other>` with `_` → `-` (default rule) |

Unknown extensions use the default rule. If the caller is certain about the pypi name, they can pass it as the module path anyway — the skill treats the input as authoritative and derives the install target via the rule above; the install-or-fail outcome is self-correcting.

**2b. Detect package manager.** Same six-row table as `pharaoh-bootstrap` Step 0c (rye / uv / poetry / pipenv / pdm / pip-venv). Closer indicator wins.

If no package manager is detected, branch on `on_package_manager_missing`:
- `"fail"` → abort before editing `conf.py`.
- `"warn"` → emit warning; go to Step 3 (edit `conf.py`); `packages_installed` stays empty.
- `"skip"` → go to Step 3 silently.

**2c. Run install.** For each pypi package not yet installed, run the add/install command (e.g. `rye add sphinxcontrib-mermaid`, `uv pip install sphinxcontrib-mermaid`). Capture exit code per package. If any install fails:

- If other packages in the batch succeeded, record the failure in `warnings` but proceed to edit `conf.py` for the successful ones; skip `conf.py` entry for the failed ones.
- If ALL installs failed, abort without editing. Record all failures in `warnings`.

### Step 3: Edit `conf.py`

For each target in Step 1's "missing" set that passed Step 2 (installed or skipped by design):

1. **Extensions assignment exists.** Insert the extension string as the last entry, preserving indentation and trailing-comma conventions. If the existing list is on one line, append inline; if multi-line, append as a new line matching the indent of the last existing entry.
2. **Extensions assignment missing.** Append a new line `extensions = ["<ext>"]` after the last existing top-level assignment. Add a blank line before for readability.

Preserve comments and blank lines around the assignment. Do NOT reorder existing entries.

### Step 4: Verify the edit

Re-read `conf_py`. Parse the `extensions = [...]` assignment again. Confirm every requested extension is present. If any is missing (edit did not take effect), abort with `FAIL: edit verification failed for <ext>; conf.py may be in an inconsistent state`.

### Step 5: Return

Emit the output JSON. Populate:

- `files_modified`: `[conf_py]` if any edit happened; `[]` otherwise.
- `extensions_added`: extensions the edit introduced.
- `extensions_already_present`: extensions that were already in the list.
- `install_command_used`: the package-manager-specific command (e.g. `uv pip install sphinxcontrib-mermaid`) if any install ran; `null` otherwise. If multiple packages installed in separate commands, this is the last one (kept simple — callers who want the full history read `packages_installed`).
- `packages_installed`: pypi names of packages actually installed.
- `warnings`: any warning surfaced along the way.

## Failure modes

| Condition                                               | Response                                                    |
| ------------------------------------------------------- | ----------------------------------------------------------- |
| `conf_py` missing                                       | FAIL naming the path.                                       |
| `extensions` empty list                                 | FAIL: `"extensions input must contain at least one entry"`. |
| `extensions = ...` in `conf.py` is not a literal list   | FAIL per Step 0.                                            |
| All installs fail                                       | FAIL without editing. Record failures in warnings.          |
| Partial install failure                                 | Edit for the successes; warn for the failures; no edit for failures. |
| Package manager not detected AND `on_package_manager_missing == "fail"` | FAIL before editing.                                        |

## Non-goals

- **No `conf.py` mutation outside the `extensions` list.** Related settings (`mermaid_output_format`, `plantuml` path config) are deliberately not touched. Callers that need those set should invoke a different skill (or author a future `pharaoh-sphinx-option-set`).
- **No multi-file edits.** Only the named `conf_py` file. Multi-project Sphinx trees with multiple `conf.py` files need one invocation per file.
- **No `pyproject.toml` pinning.** The install command may or may not persist the dependency to `pyproject.toml` depending on the package manager (rye/uv/poetry/pdm persist; raw `pip install` does not). The skill does not second-guess the caller's pinning strategy.
- **No dry-run mode.** If the caller wants to preview changes, they can diff `conf.py` after the call — the skill is fast and idempotent, so a "run, review, revert" loop is cheaper than a separate dry-run code path.

## Composition

- `pharaoh-write-plan` Step 3.5 (dep probe) transitions from warn-only to task-insertion: when `conf.py` is missing a renderer extension required by a diagram-emitting task, the plan emits a `pharaoh-sphinx-extension-add` task as a dependency of the diagram task (or group of diagram tasks). The probe's warnings still include the install command as a human-readable handoff.
- `pharaoh-bootstrap` remains the authoritative entry for `sphinx_needs` itself (the bootstrap transaction covers extension + types + `needs_from_toml` as one atomic step). This skill is for post-bootstrap additions.
- `pharaoh-quality-gate` does NOT run this skill. Gate is read-only; extension adds are plan tasks.
