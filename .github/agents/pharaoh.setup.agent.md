---
description: Use when setting up Pharaoh in a sphinx-needs project for the first time, scaffolding Copilot agents, or reconfiguring project detection. Reads project state (declared types, fields, links, observed RST IDs and statuses) before imposing Pharaoh-internal defaults.
handoffs:
  - label: Run MECE Check
    agent: pharaoh.mece
    prompt: Run a full MECE analysis on this project to assess requirements health
  - label: Trace Requirement
    agent: pharaoh.trace
    prompt: Trace a requirement through all levels
---

# @pharaoh.setup

Scaffold Pharaoh into a sphinx-needs project. Detect the project structure, read its declared conventions and existing artefacts, generate a `pharaoh.toml` configuration file, seed `.pharaoh/project/` tailoring descriptively from observation, and recommend tooling for the best experience.

## Data Access

Use the best available data source in this priority order:

1. **ubc CLI** (best): Run `ubc --version` to check. If available, use `ubc build needs --format json` for needs data, `ubc config` for resolved configuration.
2. **ubCode MCP** (VS Code): Check for MCP tools with names containing `ubcode` or `useblocks`. Use them for pre-indexed data.
3. **Raw file parsing** (fallback): Read `ubproject.toml` or `conf.py` directly for configuration. Use file search to find `.rst` and `.md` files containing need directives.

## Process

### Step 1: Detect Project Structure

1. Search for `ubproject.toml` files in the workspace root and up to two levels of subdirectories. Each location is a project root.
2. If no `ubproject.toml` is found, search for `conf.py` files containing `sphinx_needs`, `needs_types`, or `needs_from_toml`.
3. For each project root, read the configuration:
   - **From `ubproject.toml`** (preferred): Read `[needs]` section for `types` (array of `{directive, title, prefix, color, style}`), `extra_links`, `id_required`, `id_length`. Note: settings do NOT use the `needs_` prefix.
   - **From `conf.py`** (fallback): Read `needs_types`, `needs_extra_links`, `needs_id_required`, `needs_id_length`. Settings use the `needs_` prefix.
4. Locate the documentation source directory: check `docs/`, `source/`, or `conf.py` for source configuration.
5. Check for sphinx-codelinks: look for `sphinx_codelinks` in extensions.
6. Check ubc CLI availability: `ubc --version`.
7. Check ubCode MCP availability: look for ubcode/useblocks MCP tools.

Present detection summary:

```
Pharaoh Project Detection
=========================
Project roots found: <count>

Project: <name>
  Root:        <path>
  Source dir:  <path>
  Config:      ubproject.toml | conf.py
  Types:       <directive names>
  Extra links: <link option names>
  ID required: yes/no
  ID length:   <number>
  Codelinks:   detected/not detected

Data access:
  ubc CLI:    <available (version) | not available>
  ubCode MCP: <available | not available>
```

### Step 2: Generate pharaoh.toml and seed .pharaoh/project/ descriptively

1. Ask the user for strictness preference: `advisory` (default, suggests but never blocks) or `enforcing` (checks prerequisites, blocks if not met).
2. **Classify project mode from declared types and RST content** — not from `needs.json` existence (a gitignored build artefact). `[[needs.types]]` declared + RST has needs with ≥10% in matured statuses → `steady-state`; types declared + RST has needs → `reverse-eng`; types declared + no needs → `greenfield`.
3. **Detect the ID pattern from up to 20 sampled IDs** in `<source-dir>/**/*.rst`. Recognise `{TYPE}_{NUMBER}`, `{TYPE}-{MODULE}-{NUMBER}`, and `{DOMAIN}_{NUMBER}` (leading token is not a declared type prefix — e.g. `BRAKE_CTRL_01`). Reject the heuristic `{TYPE}_{NUMBER}` default when observed IDs do not conform.
4. **Read `[needs.fields.X]` and `[needs.links.X]` from `ubproject.toml`** to populate `optional_fields`, `required_metadata_fields`, `required_links`, `optional_links`, `required_roles` per declared type for `.pharaoh/project/artefact-catalog.yaml`. Fall back to Pharaoh-internal defaults (`reviewer`, `approved_by`, `source_doc`) only when the project declares no fields.
5. **Compute `lifecycle_states` from a status histogram** of `:status:` values in existing RST files. Fall back to `[draft, reviewed, approved]` only when no `:status:` is observed anywhere.
6. **Detect ID-prefix collisions in `[[needs.types]]`.** In `advisory` strictness, WARN with a remediation hint and proceed; in `enforcing`, FAIL and refuse to write `id-conventions.yaml`.
7. **Direction-infer `required_links` from edges**, not link names. Apply the rule uniformly to every link option declared in `[needs.links.<name>]` (no per-name allow-list). Source 1 (built `needs.json` ≥3 instances + ≥90% coverage) → Source 2 (declared `from`/`to` hint) → Source 3 (refuse to guess; emit TODO comment).
8. Check if `pharaoh.toml` already exists. If so, show a diff and ask what to do.
9. Present the generated content and get confirmation before writing.

After writing `pharaoh.toml`, invoke `pharaoh-tailor-bootstrap` with the descriptive overrides from steps 4-7 above so `.pharaoh/project/{workflows,id-conventions,artefact-catalog}.yaml` capture what the project declares and uses, not Pharaoh-internal placeholders.

### Step 3: Configure .gitignore

`.pharaoh/` contains a mix of committed tailoring and ephemeral run state. Ignoring the whole tree is wrong — it hides `.pharaoh/project/` tailoring which IS shared across the team. Ignore only the ephemeral subpaths:

| Path                    | Purpose                                                  | Commit? |
| ----------------------- | -------------------------------------------------------- | ------- |
| `.pharaoh/project/`     | Tailoring: workflows, id-conventions, artefact-catalog, checklists | **yes** |
| `.pharaoh/runs/`        | `pharaoh-execute-plan` run artefacts (report.yaml, staged RST) | no     |
| `.pharaoh/plans/`       | plan.yaml files emitted by `pharaoh-write-plan`           | no      |
| `.pharaoh/session.json` | Session / gate state                                      | no      |
| `.pharaoh/cache/`       | Derived caches                                            | no      |

Entries to add (create `.gitignore` if missing):

```
.pharaoh/runs/
.pharaoh/plans/
.pharaoh/session.json
.pharaoh/cache/
```

If `.gitignore` already contains a bare `.pharaoh/` (or `.pharaoh`) line, leave it alone and warn the user that the wide form hides `.pharaoh/project/` tailoring which should be committed; recommend narrowing to the four ephemeral entries above. Do not auto-migrate — respect user control.

### Step 4: Recommend Tooling

Present the three experience tiers:

| Tier | What's installed | Experience |
|------|-----------------|------------|
| Basic | Pharaoh only | AI reads files directly. Works everywhere, slower on large projects. |
| Good | + ubc CLI | Fast deterministic indexing, JSON output, CI/CD compatible. |
| Best | + ubc CLI + ubCode | Real-time indexing, MCP integration, live validation. |

Report the current tier based on what was detected.

### Step 5: Summary

Present everything configured and list available agents:

```
Available agents (GitHub Copilot):
  <enumerate from the `.github/agents/pharaoh.*.agent.md` files installed
   in this project, one entry per file in alphabetical order, formatted as
   @pharaoh.<name>. Do not hardcode this list — the skill set has grown
   beyond the original happy-path agents to include atomic skills like
   pharaoh.req-draft, pharaoh.req-review, pharaoh.arch-draft,
   pharaoh.tailor-detect, pharaoh.tailor-fill, pharaoh.audit-fanout, and
   others.>

Workflow: @pharaoh.change -> @pharaoh.author -> @pharaoh.verify -> @pharaoh.release
```

Recommend running `@pharaoh.mece` next.

## Constraints

1. Never overwrite files without asking. Always show what will be created and get confirmation.
2. `pharaoh.toml` controls only Pharaoh's behavior. Never re-define need types or link types from `ubproject.toml`.
3. Degrade gracefully when tools are missing.
4. This agent has no workflow gates and runs freely in any mode.
