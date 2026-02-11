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

Search for `ubproject.toml` files in the workspace root and up to two levels of subdirectories using Glob with pattern `**/ubproject.toml`. Each location is a project root.

If no `ubproject.toml` is found, search for `conf.py` files containing sphinx-needs configuration using Grep with pattern `sphinx_needs|needs_types|needs_from_toml` in `**/conf.py`. Each matching `conf.py` location is a project root.

Record every project root path.

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

If no project roots were found, report the issue clearly:

```
No sphinx-needs project detected in this workspace.

Looked for:
  - ubproject.toml files (up to 2 levels deep)
  - conf.py files with sphinx_needs configuration

Please ensure this workspace contains a sphinx-needs project, or
provide the path to your project root.
```

Then ask the user for the project root path before proceeding.

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
                        pharaoh:author)

Which mode would you like? [advisory/enforcing]
```

If the user does not specify, default to `"advisory"`.

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
- Use the defaults from `pharaoh.toml.example`:
  - `require_change_analysis = true`
  - `require_verification = true`
  - `require_mece_on_release = false`

**`[pharaoh.traceability]` section:**
- Build `required_links` from the detected extra link types.
- For each extra link type, determine the source and target types by examining the link's usage in existing need directives. If the link name is `implements`, and it appears on `impl` directives pointing to `spec` directives, generate `"spec -> impl"`.
- If usage cannot be determined from existing needs, infer from naming conventions:
  - `implements` or `realizes` -> `"spec -> impl"`
  - `tests` or `verifies` -> `"impl -> test"`
  - `satisfies` or `fulfills` -> `"req -> spec"`
  - `derives` or `derives_from` -> `"req -> req"` (parent to child)
- Also check for standard `links` usage to detect implicit traceability chains (e.g., specs linking to reqs via `:links:`).
- If the project has a clear type hierarchy (e.g., req -> spec -> impl -> test), generate the full chain:
  ```toml
  required_links = [
      "req -> spec",
      "spec -> impl",
      "impl -> test",
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

The Copilot templates live in the Pharaoh plugin directory under `copilot/`. Locate this directory relative to the plugin installation path.

The expected template structure is:

```
copilot/
  agents/
    pharaoh.setup.agent.md
    pharaoh.change.agent.md
    pharaoh.trace.agent.md
    pharaoh.mece.agent.md
    pharaoh.author.agent.md
    pharaoh.verify.agent.md
    pharaoh.release.agent.md
    pharaoh.plan.agent.md
  prompts/
    pharaoh.change.prompt.md
    pharaoh.trace.prompt.md
    pharaoh.mece.prompt.md
    pharaoh.author.prompt.md
    pharaoh.verify.prompt.md
    pharaoh.release.prompt.md
    pharaoh.plan.prompt.md
  copilot-instructions.md
```

If the template directory is not found, inform the user:

```
Copilot templates not found in the Pharaoh plugin directory.
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

Show a summary of all files that will be created or updated:

```
The following files will be created in your project:

  New files:
    .github/agents/pharaoh.setup.agent.md
    .github/agents/pharaoh.change.agent.md
    .github/agents/pharaoh.trace.agent.md
    .github/agents/pharaoh.mece.agent.md
    .github/agents/pharaoh.author.agent.md
    .github/agents/pharaoh.verify.agent.md
    .github/agents/pharaoh.release.agent.md
    .github/agents/pharaoh.plan.agent.md
    .github/prompts/pharaoh.change.prompt.md
    .github/prompts/pharaoh.trace.prompt.md
    .github/prompts/pharaoh.mece.prompt.md
    .github/prompts/pharaoh.author.prompt.md
    .github/prompts/pharaoh.verify.prompt.md
    .github/prompts/pharaoh.release.prompt.md
    .github/prompts/pharaoh.plan.prompt.md
    .github/copilot-instructions.md

Proceed? [yes/no]
```

After user confirms, create the necessary directories (`.github/agents/`, `.github/prompts/`) and copy each template file to the user's project.

---

### Step 4: Configure .gitignore

#### 4a. Check for .gitignore

Look for a `.gitignore` file in the workspace root.

#### 4b. Add .pharaoh/ entry

If `.gitignore` exists, read its contents and check whether `.pharaoh/` is already listed (matching the exact string `.pharaoh/` or `.pharaoh` on its own line).

- If already present, do nothing. Report: `".pharaoh/" already in .gitignore -- no changes needed.`
- If not present, append `.pharaoh/` to the file on a new line. If the file does not end with a newline, add one before the entry. Report: `Added ".pharaoh/" to .gitignore.`

If `.gitignore` does not exist, create it with the following content:

```
# Pharaoh session state (ephemeral, do not commit)
.pharaoh/
```

Report: `Created .gitignore with ".pharaoh/" entry.`

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

### Step 6: Summary

Present a final summary of everything that was configured:

```
Pharaoh Setup Complete
======================

Configuration:
  pharaoh.toml:  <created | updated | skipped>  (<path>)
  Strictness:    <advisory | enforcing>
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
  pharaoh:setup    - This skill (project setup and configuration)
  pharaoh:change   - Analyze impact of a requirement change
  pharaoh:trace    - Navigate traceability links in any direction
  pharaoh:mece     - Check for gaps, redundancies, and inconsistencies
  pharaoh:author   - Create or modify needs with proper schema compliance
  pharaoh:verify   - Validate implementations against requirements
  pharaoh:release  - Generate changelogs and release summaries
  pharaoh:plan     - Break changes into structured implementation tasks
```

If Copilot agents were installed, also show:

```
Available agents (GitHub Copilot):
  @pharaoh.setup    @pharaoh.change   @pharaoh.trace   @pharaoh.mece
  @pharaoh.author   @pharaoh.verify   @pharaoh.release @pharaoh.plan

Workflow: @pharaoh.change -> @pharaoh.author -> @pharaoh.verify -> @pharaoh.release
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
