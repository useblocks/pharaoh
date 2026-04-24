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

Classify the project into one of three modes using the following heuristic (first matching branch wins):

| Signal                                                                                           | Inferred mode  |
| ------------------------------------------------------------------------------------------------ | -------------- |
| `needs.json` exists (e.g. `docs/_build/needs/needs.json`) and contains ≥10 needs.                 | `steady-state` |
| No `needs.json` or <10 needs, AND the source tree has ≥5 code files AND `docs/` has prose files with section headers that read like user-facing features (e.g. imperative verbs, capability lists). | `reverse-eng`  |
| Otherwise (thin project: no needs, minimal src, placeholder docs).                                | `greenfield`   |

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
- Analyze existing need IDs across all project roots to detect the ID pattern.
- Look for common patterns: `{TYPE}_{NUMBER}` (e.g., `REQ_001`), `{TYPE}-{MODULE}-{NUMBER}` (e.g., `REQ-BRAKE-001`), or other conventions.
- Set `pattern` to the detected pattern. If no clear pattern is detected, use `"{TYPE}_{NUMBER}"` as a reasonable default.
- Set `auto_increment = true`.

**`[pharaoh.workflow]` section:**
- Populate the three flags from the mode table in Step 2a.bis based on the mode the user confirmed. Do NOT blindly copy values from `pharaoh.toml.example` — that file documents the steady-state shape, not the day-one defaults for every mode.
- Emit a one-line comment above the three flags naming the chosen mode, so a later reader of `pharaoh.toml` can see what assumption produced these values:
  ```toml
  [pharaoh.workflow]
  # mode: reverse-eng — tighten as the catalogue stabilises
  require_change_analysis = false
  require_verification = false
  require_mece_on_release = false
  ```

**`[pharaoh.traceability]` section:**
- Build `required_links` from the detected extra link types, but **only for type pairs where BOTH types are declared in `ubproject.toml` `[[needs.types]]`.** A chain `comp_req -> test` where `test` is not a declared type is dead config — it alarms on every `comp_req` from day one. Skip it.
- For each extra link type, determine the source and target types by examining the link's usage in existing need directives. If the link name is `implements`, and it appears on `impl` directives pointing to `spec` directives, generate `"spec -> impl"` only if both `impl` and `spec` are declared.
- If usage cannot be determined from existing needs, infer from naming conventions:
  - `implements` or `realizes` -> `"spec -> impl"`
  - `tests` or `verifies` -> `"impl -> test"`
  - `satisfies` or `fulfills` -> `"req -> spec"`
  - `derives` or `derives_from` -> `"req -> req"` (parent to child)
- Also check for standard `links` usage to detect implicit traceability chains (e.g., specs linking to reqs via `:links:`).
- If the project has a clear type hierarchy (e.g., req -> spec -> impl -> test), generate the full chain — but filter out any edges whose target type is not declared:
  ```toml
  required_links = [
      "req -> spec",
      "spec -> impl",
      # "impl -> test",  # SKIPPED: 'test' is not declared in [[needs.types]]
  ]
  ```
- If no link types are detected, leave `required_links` as an empty array with a comment explaining how to add entries.

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

### Step 5b: Bootstrap tailoring from declared types

After `pharaoh.toml` is written, invoke `pharaoh-tailor-bootstrap` with `project_root` = the workspace root and `on_missing_config` = `"prompt"` (so the user confirms the generated content).

This produces `.pharaoh/project/{workflows,id-conventions,artefact-catalog}.yaml` plus `checklists/<type>.md` per declared type. Without this step, every emitted need has `:status: draft` forever with no defined lifecycle transitions.

If the user rejects the proposal, skip — the caller may run `pharaoh-tailor-fill` later (after needs exist) as the alternative path.

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
