---
name: pharaoh-setup
description: "Use when setting up Pharaoh in a sphinx-needs project for the first time, scaffolding Copilot agents, or reconfiguring project detection"
---

# pharaoh-setup

Scaffold Pharaoh into a sphinx-needs project. This skill detects the project structure, generates a `pharaoh.toml` configuration file, optionally installs GitHub Copilot agents, and recommends tooling for the best experience.

## When to Use

- First-time setup of Pharaoh in a sphinx-needs project.
- Adding GitHub Copilot agent support to an existing Pharaoh project.
- Reconfiguring project detection after structural changes (new need types, link types, or project layout changes).
- Migrating from `conf.py`-only configuration to `ubproject.toml`.

## Prerequisites

- The workspace must contain at least one sphinx-needs project (a directory with `ubproject.toml` or a `conf.py` that loads `sphinx_needs`).
- No other Pharaoh skills are required before running this one. `pharaoh:setup` has no workflow gates and runs freely in both advisory and enforcing modes.

---

## Process

Execute the following steps in order. Present results to the user at each major step and ask for confirmation before writing any files.

---

### Step 1: Detect Project Structure

Follow the full detection algorithm defined in `skills/shared/data-access.md`. The subsections below summarize what to detect and how to present it.

#### 1a. Find Sphinx project roots

Search for `ubproject.toml` files in the workspace root and up to two levels of subdirectories using Glob with pattern `**/ubproject.toml`. Each location is a candidate root.

For each candidate root, verify sphinx-needs is actually configured by checking either (a) a `[needs]` section or `[[needs.types]]` tables in `ubproject.toml`, or (b) `sphinx_needs` in the `extensions` list of a co-located `conf.py`. Candidates that fail this check are classified as **plain-Sphinx candidates** (no sphinx-needs), not sphinx-needs project roots.

If no `ubproject.toml` match is a true sphinx-needs root, search for `conf.py` files containing sphinx-needs configuration using Grep with pattern `sphinx_needs|needs_types|needs_from_toml` in `**/conf.py`. Each matching `conf.py` location is a sphinx-needs project root.

If no sphinx-needs roots are found at all, do a final pass: Glob `**/conf.py` and record every match as a **plain-Sphinx candidate** (these exist but do not load sphinx-needs).

Record every sphinx-needs root path and every plain-Sphinx candidate separately.

#### 1b. Read need types

For each project root, read the configured need types.

From `ubproject.toml`, read the `[needs]` section and extract the `types` array. Each entry has `directive`, `title`, `prefix`, `color`, and `style`. Build a list of directive names (e.g., `req`, `spec`, `impl`, `test`).

From `conf.py` (fallback), read `needs_types` or follow `needs_from_toml` to the referenced TOML file.

Record the list of need types per project root.

#### 1c. Read extra link types

From `ubproject.toml`, read `[needs.extra_links]`. Each key is a link option name with `incoming` and `outgoing` descriptions. Example: `implements = {incoming = "is implemented by", outgoing = "implements"}`.

From `conf.py` (fallback), read `needs_extra_links`.

Record the list of extra link types per project root.

#### 1d. Read ID settings

From `ubproject.toml`, read `id_required` and `id_length` from the `[needs]` section.

From `conf.py` (fallback), read `needs_id_required` and `needs_id_length`.

Record the ID settings per project root.

#### 1e. Detect sphinx-codelinks

Follow Step 4 of `skills/shared/data-access.md`:

- Check `ubproject.toml` for `sphinx_codelinks` or `sphinx-codelinks` in extensions or configuration sections.
- Check `conf.py` for `"sphinx_codelinks"` in the `extensions` list or `codelinks_*` configuration variables.

Record whether codelinks are configured per project root.

#### 1f. Check ubc CLI availability

Run `ubc --version` in a shell. If the command succeeds (exit code 0), record the version string and mark ubc CLI as available. If it fails, mark ubc CLI as unavailable.

#### 1g. Check ubCode MCP availability

Check the available tool list for MCP tools with names containing `ubcode` or `useblocks`. If found, record ubCode MCP as available. If not found, record it as unavailable.

#### 1h. Identify documentation source tree

For each project root, locate the documentation source files:

1. Check for a `docs/` subdirectory containing `.rst` or `.md` files.
2. Check for a `source/` subdirectory.
3. Check `conf.py` for `master_doc` or source directory configuration.
4. If none found, assume RST/MD files are in the project root itself.

Record the source directory per project root.

#### 1i. Present detection summary

Present a summary of everything detected. Format it as follows:

```
Pharaoh Project Detection
=========================

Project roots found: <count>

Project: <project name from ubproject.toml [project] name, or directory name>
  Root:        <path>
  Source dir:  <path>
  Config:      ubproject.toml | conf.py
  Types:       <comma-separated directive names>
  Extra links: <comma-separated link option names, or "none">
  ID required: <yes/no>
  ID length:   <number or "not set">
  Codelinks:   <detected/not detected>

<repeat for each project root>

Data access:
  ubc CLI:   <available (version) | not available>
  ubCode MCP: <available | not available>
  Fallback:  raw file parsing (always available)
```

If no sphinx-needs project roots were found, branch on whether plain-Sphinx candidates exist:

**Case A — No Sphinx project at all (no `conf.py` anywhere):**

```
No Sphinx project detected in this workspace.

Run `sphinx-quickstart` to create a Sphinx project, or provide the path
to an existing one.
```

**Case B — Plain-Sphinx candidates exist but none loads sphinx-needs:**

```
Sphinx project(s) detected at:
  - <path>
  ...

sphinx-needs is not configured in any of them.

Pharaoh requires sphinx-needs to be loaded as an extension and at least
one need type to be declared.

Run `pharaoh-bootstrap` first to inject the minimum sphinx-needs
configuration into the chosen project, then re-run this skill to author
pharaoh.toml.
```

In either case, ask the user how to proceed before writing any files.

---

### Step 2: Generate pharaoh.toml

#### 2a. Ask about strictness preference

Ask the user which strictness mode they prefer:

```
Strictness mode controls whether Pharaoh enforces workflow order.

  advisory  (default) - Pharaoh suggests the recommended workflow
                        but never blocks you from proceeding.
  enforcing           - Pharaoh checks prerequisites before each
                        skill and blocks if they are not met.
                        (e.g., pharaoh:change must run before
                        any authoring skill)

Which mode would you like? [advisory/enforcing]
```

If the user does not specify, default to `"advisory"`.

#### 2a.bis. Detect and confirm project mode

Pharaoh's workflow gates (`require_change_analysis`, `require_verification`, `require_mece_on_release`) have different natural defaults depending on where the project sits in its lifecycle. Hardcoding the example's values is what produced the pilot feedback: a reverse-engineering project had `require_change_analysis = true` on day one, alarming every newly-drafted need because there was no Pharaoh change issue yet.

Classify the project into one of three modes by inspecting **declared types in `ubproject.toml`** and **existing RST content under the source tree** — not by `needs.json` existence. `needs.json` is a gitignored build artefact; using it as a signal misclassifies every fresh clone as `reverse-eng` until `sphinx-build` runs.

Apply rules in order; the first matching branch wins:

| Signal                                                                                                                                                                                                                          | Inferred mode  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| `[[needs.types]]` declared **and** the source tree has at least one `.. <directive>::` block in any `.rst` file under the source dir **and** ≥10% of those needs carry a status from a "matured" set (`approved`, `closed`, `reviewed`, `passed`). | `steady-state` |
| `[[needs.types]]` declared **and** the source tree has at least one `.. <directive>::` block in any `.rst` file. (Active drafting; not enough matured-status needs to qualify as steady-state yet.)                              | `reverse-eng`  |
| `[[needs.types]]` declared **but** no `.. <directive>::` blocks found in any `.rst` file. (Types declared, no needs authored.)                                                                                                   | `greenfield`   |
| `[[needs.types]]` **not** declared. Step 1 already routed this case to `pharaoh-bootstrap`; should not reach here. If it does, FAIL.                                                                                            | (n/a)          |

The classifier reads RST files directly; it does NOT depend on `needs.json` and does NOT depend on prose-feature heuristics. The heuristic "`docs/` has prose files with imperative verbs" was previously used to disambiguate `reverse-eng` vs `greenfield` — it is replaced by the cleaner test "are there sphinx-needs directives in the RST tree".

Present the detected mode and ask the user to confirm or override:

```
Detected project mode: <reverse-eng | greenfield | steady-state>

  reverse-eng   - Codebase exists and has feature-level documentation, but
                  sphinx-needs artefacts are being created now. Workflow
                  gates start permissive; tighten them once the catalogue
                  stabilises.
  greenfield    - Minimal scaffolding. Verification matters from day one
                  (every new need should have a verification path), but
                  change-analysis and MECE gates are noise until the
                  catalogue grows.
  steady-state  - Mature catalogue (≥10 needs). Full gating: change
                  analysis before edits, verification required, MECE at
                  release.

Confirm detected mode, or choose a different one
[reverse-eng/greenfield/steady-state]?
```

Record the chosen mode. Per-mode `[pharaoh.workflow]` defaults (applied in Step 2b):

| Mode           | `require_change_analysis` | `require_verification` | `require_mece_on_release` |
| -------------- | ------------------------- | ---------------------- | ------------------------- |
| `reverse-eng`  | `false`                   | `true`                 | `false`                   |
| `greenfield`   | `false`                   | `true`                 | `false`                   |
| `steady-state` | `true`                    | `true`                 | `true`                    |

`require_verification = true` is uniform across all three modes — step 1 of the gate-enablement ladder (see `skills/shared/gate-enablement.md`) is safe to enable out of the box because the review skills are ship-ready and read-only. A project that runs `pharaoh-setup` → `pharaoh-gate-advisor` immediately lands on step 2 as its next recommendation, not step 1. Mode still differentiates `require_change_analysis` and `require_mece_on_release` because those gates have pre-work that is not safe to assume on every project.

A caller running this skill non-interactively MAY pass `mode` as an explicit override input. When present, Step 2a.bis uses that value and skips the confirmation prompt.

#### 2b. Build pharaoh.toml content

Generate the `pharaoh.toml` content using the detected project data. Use `pharaoh.toml.example` as the structural template, but populate values from detection results.

**`[pharaoh]` section:**
- Set `strictness` to the user's choice from Step 2a.

**`[pharaoh.id_scheme]` section:**

Detect the ID pattern descriptively from existing IDs in the RST tree. Do NOT default to `{TYPE}_{NUMBER}` without first checking whether observed IDs conform to it.

1. Sample existing need IDs: glob `<source-dir>/**/*.rst`, extract the `:id:` value from every sphinx-needs directive (`.. <directive>:: <ID>` or `:id: <ID>`). Take up to 20 samples (or all if fewer exist).
2. Classify the dominant shape:

   | Observed shape                                              | Pattern token             | Example                |
   | ----------------------------------------------------------- | ------------------------- | ---------------------- |
   | `<TYPE-PREFIX-FROM-needs.types>_<digits>`                   | `{TYPE}_{NUMBER}`         | `REQ_001`, `FEAT_42`   |
   | `<TYPE-PREFIX>-<UPPER-MODULE>-<digits>`                     | `{TYPE}-{MODULE}-{NUMBER}`| `REQ-BRAKE-001`        |
   | `<UPPER-DOMAIN>_<digits>` where the leading token is **not** any declared type prefix in `[[needs.types]]` | `{DOMAIN}_{NUMBER}`       | `BRAKE_CTRL_01`, `FSR_POWER_01` |
   | Heterogeneous / no clear shape                              | (no pattern)              | (mixed)                |

   The `{DOMAIN}_{NUMBER}` test is what catches the `useblocks/sphinx-needs-demo` case: IDs lead with a domain name (e.g. `BRAKE_CTRL`) rather than the directive's declared type prefix.

3. Emit the detected pattern as `pattern = "{TYPE}_{NUMBER}"` / `pattern = "{DOMAIN}_{NUMBER}"` / etc. and a comment recording the sample size:

   ```toml
   [pharaoh.id_scheme]
   # Inferred from 20 sampled IDs in source-dir/**/*.rst.
   # Observed shape: {DOMAIN}_{NUMBER} (e.g. BRAKE_CTRL_01).
   pattern = "{DOMAIN}_{NUMBER}"
   auto_increment = true
   ```

4. **No-evidence fallback.** If zero IDs are found in the RST tree (greenfield), fall back to `pattern = "{TYPE}_{NUMBER}"` with a comment marking the value as a default not derived from observation:

   ```toml
   pattern = "{TYPE}_{NUMBER}"  # default; no IDs observed in RST tree
   ```

5. **Heterogeneous fallback.** If observed IDs do not fit any single shape, emit `pattern = "{ANY}"` with a TODO comment asking the user to declare the project's convention manually. Do NOT silently force `{TYPE}_{NUMBER}`.

6. `auto_increment = true` is unchanged.

The matching `id_regex` for `.pharaoh/project/id-conventions.yaml` (Step 5b) is derived from the same observation: for `{DOMAIN}_{NUMBER}` emit `^[A-Z][A-Z0-9_]*_[0-9]+$`; for `{TYPE}_{NUMBER}` emit the union of declared `[[needs.types]] prefix` values + digits anchor; etc.

**`[pharaoh.workflow]` section:**
- Persist the chosen mode as a real key (`mode = "reverse-eng" | "greenfield" | "steady-state"`). The key lives in `pharaoh.toml` alongside the gate flags so a later reader (and any skill that wants to reason about lifecycle stage) can parse it directly. Do NOT persist it as a comment-only line — comments are not parseable.
- Populate the three gate flags from the mode table in Step 2a.bis based on the mode the user confirmed. Do NOT blindly copy values from `pharaoh.toml.example` — that file documents the steady-state shape, not the day-one defaults for every mode.
- Emit a short rationale comment above the gate flags naming the assumption that produced these values:
  ```toml
  [pharaoh.workflow]
  mode = "reverse-eng"
  # Gates tuned for reverse-eng — tighten as the catalogue stabilises.
  require_change_analysis = false
  require_verification = true
  require_mece_on_release = false
  ```

**`[pharaoh.traceability]` section:**

`required_links` declares chains in the form `"source-type -> target-type"`. The semantics enforced by `pharaoh:mece` are: every need of `source-type` must have at least one outgoing link to a need of `target-type` (see `skills/pharaoh-mece/SKILL.md` Step 2). The chain direction is therefore the direction the link option resolves, **not** the direction of the conceptual type hierarchy. Both conventions exist in the wild — some projects put `:implements:` on the `impl` directive (child references parent, chain `impl -> spec`); others put `:specifies:` on the `spec` directive (parent references child, chain `spec -> impl`). Inferring direction from the link option name picks one convention and emits inverted chains for projects on the other; `pharaoh:mece` then reports 100% gaps for the source type. Resolve direction from ground truth instead.

Apply the following sources in priority order. For each link option, stop at the first source that resolves a direction.

**Source 1 — built `needs.json` (preferred, when available).** If the project has a built `needs.json` (typical paths: `<source-dir>/_build/needs/needs.json`, `<source-dir>/_build/html/needs.json`, or any `needs.json` under `_build/`), parse it and inspect the actual edges:

For each declared link option `L` (including the standard `:links:`) and each ordered pair of declared types `(X, Y)`:

1. Let `n_X` = count of needs of type `X` whose `:L:` value is non-empty.
2. Let `n_X_to_Y` = count of those needs whose `:L:` resolves to at least one need of type `Y`.
3. Emit `"X -> Y"` only if `n_X >= 3` and `n_X_to_Y / n_X >= 0.9`.

The thresholds (`>= 3` instances, `>= 90%` coverage) suppress chains inferred from a single accidental edge while still emitting chains the project consistently produces. Include a comment recording the sample size:

```toml
required_links = [
    "spec -> req",   # needs.json: 18/18 spec needs link to req via :reqs:
    "impl -> spec",  # needs.json: 35/35 impl needs link to spec via :implements:
]
```

**Source 2 — declared semantics from `[needs.links.<name>]` (greenfield, no `needs.json`).** The `outgoing` and `incoming` descriptions identify the verb and which side bears the link option, but they do not, on their own, identify the type pair: any type can carry any link option. Without empirical edges or an explicit hint, the source and target types are unknown.

Use this source only when `ubproject.toml` carries an explicit hint (e.g., a future `[needs.links.<name>] from = "<type>", to = "<type>"` extension). Do not invent the type pair from the link option name.

**Source 3 — refuse to guess.** When neither source resolves a link option to a `(source-type, target-type)` pair, do **not** emit a chain for that link. Emit a TODO comment in its place so the user sees what was skipped and why:

```toml
required_links = [
    "spec -> req",  # needs.json: 18/18 spec needs link to req via :reqs:
    # TODO: link option `implements` is declared but no `needs.json` was
    #   found. Build the docs once and re-run `pharaoh:setup`, or add an
    #   explicit chain manually in the form "source-type -> target-type".
]
```

The previous heuristic-name table (`implements -> "spec -> impl"`, `tests -> "impl -> test"`, etc.) is removed: it encoded one project convention as universal and produced inverted chains on every project that used the opposite convention.

**Coverage note.** Source 1 iterates over **every** link option declared in `[needs.links.<name>]` (and the built-in `:links:`). There is no per-link-name allow-list. A `useblocks/sphinx-needs-demo`-style project declaring `verifies`, `satisfies`, `implements`, `triggers`, `derives_from`, etc. has every option evaluated against the same coverage threshold. This closes the PR #14 follow-up: the direction-inference rule is uniform across the full declared set, not specific to a fixed list of relations.

**Type-pair filter (applied to every source).** Emit a chain only when both the source type and the target type are declared in `ubproject.toml` `[[needs.types]]`. When Source 1 resolves an edge whose target type is not declared, drop it with a comment naming the dropped target — the chain is dead config that would alarm on every source need from day one:

```toml
required_links = [
    "req -> spec",
    "spec -> impl",
    # "impl -> test",  # SKIPPED: 'test' is not declared in [[needs.types]]
]
```

**Empty-array fallback.** If no link option resolves to a chain by any source, emit:

```toml
required_links = [
    # No traceability chains inferred. Add entries of the form
    # "source-type -> target-type" once the link conventions stabilise,
    # or build the docs and re-run `pharaoh:setup` to infer from `needs.json`.
]
```

**`[pharaoh.codelinks]` section:**
- Set `enabled = true` if sphinx-codelinks was detected in Step 1e.
- Set `enabled = false` if not detected.

#### 2c. Check for existing pharaoh.toml

Before writing, check if `pharaoh.toml` already exists in the workspace root.

If it exists:
1. Read the existing file.
2. Show a diff between the existing content and the newly generated content.
3. Ask the user:
   ```
   pharaoh.toml already exists. What would you like to do?
     1. Overwrite with the new configuration
     2. Keep the existing file
     3. Show both side by side so I can choose specific settings
   ```
4. Proceed according to the user's choice.

If it does not exist, proceed to write.

#### 2d. Present and write pharaoh.toml

Show the user the complete `pharaoh.toml` content that will be written:

```
The following pharaoh.toml will be created at <workspace root>/pharaoh.toml:

---
<file content>
---

Write this file? [yes/no]
```

After the user confirms, write the file to the workspace root (the same directory as `ubproject.toml` or `conf.py`). If there are multiple project roots, write to the top-level workspace root.

---

### Step 3: Scaffold Copilot Agents (if requested)

#### 3a. Ask if user wants Copilot support

```
Would you like to set up GitHub Copilot agent support?

This will create agent and prompt files in your .github/ directory,
enabling @pharaoh.change, @pharaoh.trace, and other agents in
VS Code Copilot Chat.

Set up Copilot agents? [yes/no]
```

If the user declines, skip to Step 4.

#### 3b. Locate Copilot templates

The Copilot templates live in the Pharaoh plugin directory under `.github/`. Pharaoh dogfoods its own agents — the same `.github/` tree it copies out is the one it uses on itself. Locate this directory relative to the plugin installation path.

The expected template structure is:

```
.github/
  agents/
    pharaoh.*.agent.md        (discovered via glob, not hardcoded)
  prompts/
    pharaoh.*.prompt.md       (discovered via glob, not hardcoded)
  copilot-instructions.md
```

Do NOT hardcode the agent or prompt file list in the skill — enumerate them at runtime with Glob on `.github/agents/pharaoh.*.agent.md` and `.github/prompts/pharaoh.*.prompt.md`. The set grows as new atomic skills land; a hardcoded list rots on every release.

If the `.github/agents/` directory is not found in the plugin dir, inform the user:

```
Copilot templates not found in the Pharaoh plugin directory
(expected .github/agents/ and .github/prompts/).
This may indicate an incomplete installation. Skipping Copilot setup.

You can manually create Copilot agents later by running pharaoh:setup again
after reinstalling the plugin.
```

Then skip to Step 4.

#### 3c. Check for existing .github/ files

Before copying, check if any of the target files already exist in the user's project:

- `.github/agents/` -- any `pharaoh.*.agent.md` files
- `.github/prompts/` -- any `pharaoh.*.prompt.md` files
- `.github/copilot-instructions.md`

For each existing file:
1. Read both the existing file and the template.
2. Show the diff.
3. Ask the user whether to overwrite, skip, or merge.

For files that do not exist, list them as new files to be created.

#### 3d. Present file list and copy

Enumerate the actual template files via Glob (see Step 3b) and show a summary. Example shape (exact list depends on the current plugin version):

```
The following files will be created in your project:

  New files (N agents, M prompts):
    .github/agents/pharaoh.<name>.agent.md     × N
    .github/prompts/pharaoh.<name>.prompt.md   × M
    .github/copilot-instructions.md

Proceed? [yes/no]
```

Show the full enumerated list to the user — do not print the `× N` shorthand. The shorthand above is just for this skill spec; the runtime output must list every file by name so the user can review before confirming.

After user confirms, create the necessary directories (`.github/agents/`, `.github/prompts/`) and copy each template file to the user's project.

---

### Step 4: Configure .gitignore

#### 4a. Check for .gitignore

Look for a `.gitignore` file in the workspace root.

#### 4b. Add Pharaoh ephemeral paths (narrow, not wholesale)

`.pharaoh/` contains a mix of committed tailoring and ephemeral run state. Ignoring the whole tree is wrong — it hides `.pharaoh/project/` tailoring which IS shared across the team. The skill ignores only the ephemeral subpaths:

| Path                    | Purpose                                                  | Commit? |
| ----------------------- | -------------------------------------------------------- | ------- |
| `.pharaoh/project/`     | Tailoring: workflows, id-conventions, artefact-catalog, checklists | **yes** |
| `.pharaoh/runs/`        | `pharaoh-execute-plan` run artefacts (report.yaml, staged RST) | no     |
| `.pharaoh/plans/`       | plan.yaml files emitted by `pharaoh-write-plan`           | no     |
| `.pharaoh/session.json` | Session / gate state                                      | no      |
| `.pharaoh/cache/`       | Derived caches                                            | no      |

Emitted entries:

```
.pharaoh/runs/
.pharaoh/plans/
.pharaoh/session.json
.pharaoh/cache/
```

If `.gitignore` exists, read its contents and branch:

1. **Wide form already present.** If the file contains a bare `.pharaoh/` or `.pharaoh` line (no trailing path segment), emit a warning and leave it alone — do not auto-migrate, respect user control:
   > `.pharaoh/ is ignored as a whole — this hides .pharaoh/project/ tailoring which should be committed. Consider narrowing to: .pharaoh/runs/, .pharaoh/plans/, .pharaoh/session.json, .pharaoh/cache/.`
   Report: `".pharaoh/" entry is too wide; left in place with a warning.`
2. **All four narrow entries already present.** Do nothing. Report: `".pharaoh/ ephemeral paths already ignored -- no changes needed."`
3. **Some narrow entries missing.** Append the missing entries on new lines. If the file does not end with a newline, add one first. Report: `"Added <count> Pharaoh ephemeral-path entries to .gitignore."`

If `.gitignore` does not exist, create it with:

```
# Pharaoh ephemeral state (do not commit). Project tailoring at .pharaoh/project/ IS committed.
.pharaoh/runs/
.pharaoh/plans/
.pharaoh/session.json
.pharaoh/cache/
```

Report: `Created .gitignore with Pharaoh ephemeral-path entries.`

---

### Step 5: Recommend Tooling

#### 5a. ubc CLI recommendation

If ubc CLI was not found in Step 1f, present:

```
Recommendation: Install the ubc CLI for faster, more accurate data access.

ubc provides deterministic JSON output for needs indexing, validation,
and impact analysis. It is the fastest data source Pharaoh can use.

Install: https://ubcode.useblocks.com/ubc/installation.html

Without ubc, Pharaoh falls back to reading RST/MD files directly.
This works but is slower on large projects.
```

If ubc CLI was found, present:

```
ubc CLI detected (version <version>). Pharaoh will use it for
fast, deterministic data access.
```

#### 5b. ubCode extension recommendation

If ubCode MCP was not found in Step 1g, present:

```
Recommendation: Install the ubCode VS Code extension for the best experience.

ubCode provides real-time indexing, MCP integration, and live
validation directly in your editor. Combined with ubc CLI, it
gives Pharaoh instant access to pre-indexed project data.

Install from the VS Code marketplace: search for "ubCode".
```

If ubCode MCP was found, present:

```
ubCode MCP detected. Pharaoh will use it for real-time indexed
data access when available.
```

#### 5c. Present experience tiers

```
Pharaoh Experience Tiers
========================

Tier     | What you have          | Experience
---------|------------------------|---------------------------------------------
Basic    | Pharaoh only           | AI reads files directly. Works everywhere,
         |                        | slower on large projects.
Good     | + ubc CLI              | Fast deterministic indexing, JSON output,
         |                        | CI/CD compatible.
Best     | + ubc CLI + ubCode     | Real-time indexing, MCP integration, live
         |                        | validation, full schema checks.

Your current tier: <Basic|Good|Best>
```

Determine the current tier:
- **Best**: Both ubc CLI and ubCode MCP are available.
- **Good**: ubc CLI is available but ubCode MCP is not.
- **Basic**: Neither ubc CLI nor ubCode MCP is available.

---

### Step 5b: Bootstrap tailoring from declared types and observed RST content

After `pharaoh.toml` is written, generate `.pharaoh/project/{workflows,id-conventions,artefact-catalog}.yaml` plus `checklists/<type>.md` per declared type. The bootstrap is **descriptive**: it captures what the project already declares and what existing RST content already uses, falling back to Pharaoh-internal defaults only when no project signal is available.

The base shapes and fallbacks are documented in `pharaoh-tailor-bootstrap` — invoke it for the structural emission. Before invoking it, gather the project-state inputs below and pass them as overrides so the emitted tailoring matches the project's reality, not a Pharaoh-internal placeholder set.

#### 5b.1. Read `[needs.fields.X]` from `ubproject.toml` (artefact-catalog `optional_fields` and `required_metadata_fields`)

For each declared `[needs.fields.<name>]` table in `ubproject.toml`:

- The `<name>` is a sphinx-needs option key (e.g. `asil`, `severity`, `exposure`, `controllability`, `safe_state`).
- If the table declares `required = true` (or any explicit-required marker the project uses), add `<name>` to that type's `required_metadata_fields`.
- Otherwise, add `<name>` to that type's `optional_fields`.
- Scope: if `[needs.fields.<name>]` declares `applies_to = ["<type1>", "<type2>"]`, restrict to those types. Without an `applies_to`, treat as global and add to every declared type's `optional_fields`.

When `[needs.fields.X]` is **declared** in `ubproject.toml`, the Pharaoh-internal placeholder set (`reviewer`, `approved_by`, `source_doc`) is appended only for types that do not already have at least one project-declared field — i.e., we add Pharaoh defaults on top of the project's own fields, never as a replacement.

When `[needs.fields.X]` is **absent**, fall back to `pharaoh-tailor-bootstrap`'s built-in default (`optional_fields: [reviewer, approved_by, source_doc]`).

#### 5b.2. Compute lifecycle from RST status histogram (`workflows.yaml lifecycle_states`)

Glob `<source-dir>/**/*.rst` and parse `:status: <value>` from every sphinx-needs directive. Build a histogram of observed values.

- If the histogram is non-empty and at least two distinct values appear, set `lifecycle_states` to the observed values, ordered by frequency descending. Emit a comment recording the histogram counts.
- If only one distinct value appears (e.g. every need has `:status: open`), still emit it as the first lifecycle state but append the Pharaoh defaults (`draft`, `reviewed`, `approved`) so transitions are at least defined.
- If no `:status:` fields are found anywhere, fall back to `pharaoh-tailor-bootstrap`'s default `[draft, reviewed, approved]`.

Worked example for `useblocks/sphinx-needs-demo`-style histogram (`open: 145, closed: 16, passed: 7, approved: 2`):

```yaml
# workflows.yaml — generated by pharaoh-setup with histogram override
# Observed status counts in <source-dir>/**/*.rst:
#   open: 145, closed: 16, passed: 7, approved: 2
lifecycle_states:
  - open
  - closed
  - passed
  - approved

transitions:
  - {from: open, to: passed, requires: []}
  - {from: open, to: closed, requires: []}
  - {from: passed, to: approved, requires: []}
  # Add the inverse (passed -> open, approved -> open) only if the histogram or
  # explicit project policy suggests they are reachable. The default is to
  # leave the state machine as observed.
```

The transition graph is **not** inferred from the histogram (the histogram does not record transitions). The skill emits a permissive forward-only chain `state[i] -> state[i+1]`. The user is expected to edit transitions to match project policy; emit a comment naming this expectation.

#### 5b.3. Detect ID-prefix collisions (`id-conventions.yaml prefixes`)

Read `[[needs.types]]` from `ubproject.toml`. Build a map `prefix -> [directive...]`. Any prefix mapping to ≥2 directives is a collision.

Real-world example from `useblocks/sphinx-needs-demo`:
- `R_` declared on both `req` and `release`
- `T_` declared on both `test` and `team`
- (empty prefix `""`) declared on both `arch` and `need`

Behaviour by strictness mode (the value chosen in Step 2a):

- **`advisory`** — emit a WARN to the user listing each collision with a remediation hint, and proceed with the prefixes as-declared (`pharaoh-id-convention-check` will then surface ambiguous IDs at runtime). The warning text:

  ```
  WARNING: ID-prefix collisions detected in [[needs.types]]:
    - R_ used for: req, release
    - T_ used for: test, team
    - "" (empty) used for: arch, need

  Disambiguate by giving each declared type a unique prefix in
  ubproject.toml, e.g. release -> REL_, team -> TEAM_, need -> NEED_.
  Until disambiguated, pharaoh-id-convention-check cannot tell a release
  ID from a requirement ID and pharaoh-id-allocate may emit colliding IDs.
  ```

- **`enforcing`** — FAIL with the same message and refuse to write `id-conventions.yaml`. The user must fix `[[needs.types]]` first.

When no collisions are detected, emit `prefixes` directly from `[[needs.types]]` as today.

#### 5b.4. Detect ID regex from observed IDs (`id-conventions.yaml id_regex`)

Use the same sample collected in Step 2b's `[pharaoh.id_scheme]` detection:

- If the dominant observed shape is `{TYPE}_{NUMBER}` and observed IDs match the union of declared prefixes + digits, emit the union-of-prefixes regex (current default).
- If the dominant shape is `{DOMAIN}_{NUMBER}` (leading token does not match any declared type prefix), emit a regex matching the observation:

  ```yaml
  id_regex: "^[A-Z][A-Z0-9_]*_[0-9]+$"
  ```

  with a comment naming the sampled IDs.

- If the observed shape is `{TYPE}-{MODULE}-{NUMBER}`, emit:

  ```yaml
  id_regex: "^(REQ|SPEC|IMPL|TEST)-[A-Z]+-[0-9]+$"
  ```

  (substituting actually-declared prefixes).

- If observed IDs don't conform to a single shape, emit `id_regex: ".+"` with a TODO comment asking the user to declare the convention manually.

Reject the heuristic union-of-prefixes regex when observed IDs do not match it — the regex would fail validation on every existing need.

#### 5b.5. Emit Phase-5 release-gate fields per type (artefact-catalog)

For each declared type, emit `required_links`, `optional_links`, `required_metadata_fields`, `required_roles` per the canonical schema (see `schemas/artefact-catalog.schema.json`):

- **`required_links`:** for each `[needs.links.<name>]` (also written `[needs.extra_links]` in older sphinx-needs configs) declared with `required = true` — or, when the project has a built `needs.json`, for each link option that 100% of existing needs of this type carry (per Source 1 in `[pharaoh.traceability]` direction inference) — include the option name.
- **`optional_links`:** every other declared link option that is legal on this type (per `[needs.links.<name>] applies_to`, or default to "any declared option not in `required_links`"). Drop overlap with `required_links`.
- **`required_metadata_fields`:** every `[needs.fields.<name>]` declared with `required = true` for this type, plus `status` (every governed type has a lifecycle, so `status` is always required). When the project declares no required fields, emit `[status]`.
- **`required_roles`:** if the project declares any field whose name implies a role (`reviewer`, `approver`, `approved_by`, `responsible`, `assignee`), include the matching options. Otherwise emit `[]` — explicit "no policy", surfaced by `pharaoh-tailor-review` C6 if the user later wants to enforce a review gate.

`pharaoh-tailor-bootstrap` handles the structural emission; `pharaoh-setup` supplies the derived inputs above.

#### 5b.6. Invoke `pharaoh-tailor-bootstrap`

After gathering 5b.1 through 5b.5, invoke `pharaoh-tailor-bootstrap` with:
- `project_root` = the workspace root.
- `on_missing_config` = `"prompt"` (so the user confirms the generated content).
- An overrides bundle carrying the descriptive values from 5b.1–5b.5. When `pharaoh-tailor-bootstrap` does not yet support an explicit overrides input, the caller is responsible for editing the emitted YAML in place to apply the overrides before showing the user the final form. Document this gap; the structural shape is unchanged.

If the user rejects the proposal, skip — the caller may run `pharaoh-tailor-fill` later (after needs exist) as the alternative path. The `pharaoh-tailor-fill` skill is in fact the canonical descriptive author for matured projects (≥10 needs); `pharaoh-setup` here only seeds the file with what's available at setup time so the project doesn't sit with placeholder defaults.

#### 5b.7. Worked example — `useblocks/sphinx-needs-demo`

Concrete walk-through showing how Steps 2 through 5b together emit descriptive tailoring on a project that exposes every defect listed in issue #13 §8.

**Input — `ubproject.toml` excerpt (paraphrased):**

```toml
[[needs.types]]
directive = "req"
prefix = "R_"

[[needs.types]]
directive = "release"
prefix = "R_"          # collision with req

[[needs.types]]
directive = "test"
prefix = "T_"

[[needs.types]]
directive = "team"
prefix = "T_"          # collision with test

[[needs.types]]
directive = "fsr"
prefix = "FSR_"

[needs.fields.asil]
applies_to = ["fsr", "safety_goal", "hazard"]
required = true

[needs.fields.severity]
applies_to = ["hazard"]

[needs.fields.scenario]
[needs.fields.safe_state]
[needs.fields.customer]

[needs.links.satisfies]
[needs.links.verifies]
[needs.links.derives_from]
```

**Input — observed RST IDs and statuses:**

- `BRAKE_CTRL_01`, `BRAKE_CTRL_02`, `FSR_POWER_01`, `FSR_POWER_02`, ... (20 sampled, all matching `^[A-Z][A-Z0-9_]*_[0-9]+$`, none matching `^(R_|T_|FSR_)[0-9]+$`)
- Status histogram: `open: 145, closed: 16, passed: 7, approved: 2`.

**Output — `pharaoh.toml`:**

```toml
[pharaoh]
strictness = "advisory"

[pharaoh.id_scheme]
# Inferred from 20 sampled IDs in source-dir/**/*.rst.
# Observed shape: {DOMAIN}_{NUMBER} (e.g. BRAKE_CTRL_01, FSR_POWER_01).
# Note: declared type prefixes (R_, T_, FSR_) do not match the leading
# token of observed IDs — IDs lead with a domain name, not a type prefix.
pattern = "{DOMAIN}_{NUMBER}"
auto_increment = true

[pharaoh.workflow]
mode = "reverse-eng"
# Gates tuned for reverse-eng — tighten as the catalogue stabilises.
require_change_analysis = false
require_verification = true
require_mece_on_release = false

[pharaoh.traceability]
# Direction inferred from needs.json edges (Source 1).
required_links = [
    "spec -> req",          # 100% of spec needs link to req via :satisfies:
    "fsr -> safety_goal",   # 100% of fsr needs link to safety_goal via :derives_from:
]

[pharaoh.codelinks]
enabled = false
```

**Output — pre-bootstrap WARNINGS (advisory mode):**

```
WARNING: ID-prefix collisions detected in [[needs.types]]:
  - R_ used for: req, release
  - T_ used for: test, team

Disambiguate by giving each declared type a unique prefix in
ubproject.toml, e.g. release -> REL_, team -> TEAM_.
```

**Output — `.pharaoh/project/workflows.yaml`:**

```yaml
# Observed status counts in <source-dir>/**/*.rst:
#   open: 145, closed: 16, passed: 7, approved: 2
lifecycle_states:
  - open
  - closed
  - passed
  - approved

transitions:
  - {from: open, to: passed, requires: []}
  - {from: open, to: closed, requires: []}
  - {from: passed, to: approved, requires: []}
```

**Output — `.pharaoh/project/id-conventions.yaml`:**

```yaml
prefixes:
  req: R_
  release: R_      # COLLISION — flagged, not silently merged
  test: T_
  team: T_         # COLLISION — flagged
  fsr: FSR_
id_regex: "^[A-Z][A-Z0-9_]*_[0-9]+$"
separator: "_"
```

**Output — `.pharaoh/project/artefact-catalog.yaml` excerpt for `fsr`:**

```yaml
fsr:
  required_fields: [id, status, title, asil]
  optional_fields: [scenario, safe_state, customer, reviewer, approved_by, source_doc]
  lifecycle: [open, closed, passed, approved]
  required_links: [derives_from]
  optional_links: [satisfies, verifies]
  required_metadata_fields: [status, asil]
  required_roles: []
```

Compare to the prescriptive default this skill emitted before the rewrite, which would have produced `optional_fields: [reviewer, approved_by, source_doc]` (Pharaoh-internal placeholder set), `lifecycle: [draft, reviewed, approved]` (Pharaoh-internal default), `required_metadata_fields: [status]` (no `asil` despite the project declaring it required), `id_regex: "^(R_|T_|FSR_)[0-9]+$"` (which fails on every actual ID in the project), and `pattern = "{TYPE}_{NUMBER}"` (which assumes the project's IDs lead with a declared type prefix).

The descriptive emission captures what the project already declares and uses; the prescriptive emission imposed a Pharaoh-internal world-view onto a project that had never agreed to it.

---

### Step 6: Summary

Present a final summary of everything that was configured:

```
Pharaoh Setup Complete
======================

Configuration:
  pharaoh.toml:  <created | updated | skipped>  (<path>)
  Strictness:    <advisory | enforcing>
  Mode:          <reverse-eng | greenfield | steady-state>
  Workflow:      change=<on|off>, verification=<on|off>, mece=<on|off>
  Codelinks:     <enabled | disabled>
  Traceability:  <N required link chains | no required links>

Copilot agents:  <installed (<count> agents, <count> prompts) | skipped>

.gitignore:      <updated | already configured | created>

Data access tier: <Basic | Good | Best>

Detected projects:
  <project name> (<path>)
    Types: <comma-separated>
    Links: <comma-separated>

Available skills (Claude Code):
  <enumerate from `skills/pharaoh-*/SKILL.md` frontmatter at runtime —
   do not hardcode. The skill list has grown beyond the original 8 happy-path
   agents to include atomic skills like pharaoh:req-draft, pharaoh:req-review,
   pharaoh:arch-draft, pharaoh:arch-review, pharaoh:vplan-draft,
   pharaoh:vplan-review, pharaoh:fmea, pharaoh:tailor-detect,
   pharaoh:tailor-fill, pharaoh:audit-fanout, and others.>
```

If Copilot agents were installed, also show:

```
Available agents (GitHub Copilot):
  <enumerate from the copied .github/agents/pharaoh.*.agent.md files —
   do not hardcode. One entry per installed agent, formatted as @pharaoh.<name>.>

Orchestration agents (coordinate atomic agents for end-to-end flows):
  @pharaoh.flow, @pharaoh.process-audit, @pharaoh.write-plan, @pharaoh.execute-plan, ...
  (again, discover from installed agents rather than hardcoding)

For reverse-engineering requirements or architecture from code, use
  @pharaoh.write-plan to generate a plan.yaml (choose a template such as
  reverse-engineer-project or reverse-engineer-module) and @pharaoh.execute-plan
  to run it. The deleted @pharaoh.reqs-from-module skill has been replaced by
  this plan-based flow.
```

End with a recommendation to run the MECE check:

```
Next step: Run pharaoh:mece to get an overview of your project's
requirements health -- gaps, orphans, and traceability coverage.
```

---

## Key Constraints

1. **Never overwrite files without asking.** Always check if a target file exists before writing. If it exists, show a diff and ask the user what to do.
2. **Always show what will be created or modified before doing it.** Present file contents or file lists and get explicit confirmation.
3. **Work with any sphinx-needs project structure.** Handle single-project and multi-project setups. Handle `ubproject.toml`, `conf.py`, or both. Handle projects with or without sphinx-codelinks.
4. **Do not duplicate sphinx-needs configuration.** `pharaoh.toml` controls only Pharaoh's own behavior. Need types, link types, and ID settings are read from `ubproject.toml` or `conf.py` -- never re-defined in `pharaoh.toml`.
5. **Degrade gracefully.** If ubc CLI is not available, do not fail. If Copilot templates are missing, skip Copilot setup with a clear message. If no project is detected, ask the user for guidance.
6. **This skill has no workflow gates.** It runs freely regardless of strictness mode. It does not read or write `.pharaoh/session.json`.
