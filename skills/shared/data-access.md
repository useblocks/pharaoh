# Data Access Instructions

These instructions tell you how to find and read sphinx-needs project data.
Follow these steps in order at the start of every Pharaoh skill invocation.

---

## 1. Detect Project Structure

Scan the workspace to identify all sphinx-needs project roots.

### Step 1a: Find ubproject.toml files

Search for `ubproject.toml` in the workspace root and up to two levels of subdirectories.
Use Glob with pattern `**/ubproject.toml` (limit depth to avoid scanning node_modules, .git, etc.).

- If found, each `ubproject.toml` location is a project root.
- A workspace may contain multiple project roots (multi-project setup).
- Record every project root path for later use.

### Step 1b: Find conf.py files (fallback)

If no `ubproject.toml` is found, search for `conf.py` files containing sphinx_needs configuration.
Use Grep to find files matching pattern `sphinx_needs|needs_types|needs_from_toml` in `**/conf.py`.

- Each `conf.py` with sphinx-needs config is a project root.
- If a directory has both `ubproject.toml` and `conf.py`, prefer `ubproject.toml` for configuration.

### Step 1c: Identify documentation source tree

For each project root, locate the documentation source files:

1. Check for `docs/` subdirectory containing `.rst` or `.md` files.
2. Check for `source/` subdirectory (common Sphinx layout).
3. Check `conf.py` for `master_doc` or source directory configuration.
4. If none found, assume RST/MD files are in the project root itself.

Record the source directory for each project root.

### Step 1d: Handle single vs. multi-project

- **Single project**: One project root found. Use it directly.
- **Multi-project**: Multiple roots found. When a skill operates on a specific need, determine which project it belongs to by checking ID prefixes or searching for the need across projects. When a skill operates globally, iterate over all projects.

---

## 2. Read Project Configuration

Read the need types, link types, and ID settings that define the project schema.

### Step 2a: Read from ubproject.toml (preferred)

If `ubproject.toml` exists, read the `[needs]` section. Extract:

- **types**: Array of type definitions. Each has `directive`, `title`, `prefix`, `color`, `style`.
  Example: `{directive = "req", title = "Requirement", prefix = "REQ_", color = "#BFD8D2", style = "node"}`
  Build a list of valid directive names (e.g., `req`, `spec`, `impl`, `test`).

- **extra_links**: Table under `[needs.extra_links]`. Each key is a link name with `incoming` and `outgoing` descriptions.
  Example: `implements = {incoming = "is implemented by", outgoing = "implements"}`
  Build a list of valid link option names (e.g., `implements`, `tests`).

- **id_required**: Boolean. If true, every need must have an explicit `:id:`.
- **id_length**: Integer. Minimum length for the numeric part of IDs.

Note: In `ubproject.toml`, settings do NOT use the `needs_` prefix. The key is `types`, not `needs_types`.

### Step 2b: Read from conf.py (fallback)

If no `ubproject.toml` exists, or if you need to check for additional settings, read `conf.py`. Extract:

- **needs_types**: List of type dictionaries with `directive`, `title`, `prefix`, `color`, `style`.
- **needs_extra_links**: List of link dictionaries with `option`, `incoming`, `outgoing`.
- **needs_from_toml**: String path. If set, the actual config is in the referenced TOML file. Read that file instead.
- **needs_id_required**: Boolean.
- **needs_id_length**: Integer.
- **extensions**: List. Confirm `"sphinx_needs"` is present.

Note: In `conf.py`, all settings use the `needs_` prefix.

### Step 2c: Configuration priority

When both `ubproject.toml` and `conf.py` exist in the same project root:

1. Use `ubproject.toml` as the authoritative source for types, extra_links, and ID settings.
2. Only fall back to `conf.py` for settings not present in `ubproject.toml`.
3. If `conf.py` has `needs_from_toml` pointing to `ubproject.toml`, this confirms the TOML is authoritative.

---

## 3. Three-Tier Data Access

Use the best available data source. Check tiers in order and use the first one that works.

### Tier 1: ubc CLI (best -- fast, deterministic, JSON output)

Check if ubc CLI is available:

```
ubc --version
```

If the command succeeds (exit code 0), ubc is available. Use it for all data access:

| Need | Command | What it returns |
|---|---|---|
| Complete needs index | `ubc build needs --format json` | JSON array of all needs with IDs, types, titles, statuses, links, content |
| Resolved project config | `ubc config` | Merged configuration as JSON (types, links, all settings) |
| Lint and validate | `ubc check` | Validation errors and warnings |
| Schema validation | `ubc schema validate` | Schema compliance report |
| Diff between versions | `ubc diff` | Changed needs with impact tracing |

When using ubc CLI:
- Run commands from the project root directory.
- Parse JSON output directly. Do not attempt to re-parse source files.
- If a ubc command fails, fall through to Tier 2.
- For multi-project setups, run ubc in each project root separately.

### Tier 2: ubCode MCP (VS Code -- real-time indexed data)

If ubc CLI is not available, check if ubCode MCP tools are accessible.
Look for MCP tools with names containing `ubcode` or `useblocks` in the available tool list.

If ubCode MCP is available:
- Use MCP tools for querying the needs index, resolving links, and validating schema.
- MCP provides pre-indexed data: the link graph is already built, external needs are already imported.
- Prefer MCP over raw file parsing for speed and accuracy.

If ubCode MCP tools are not found, fall through to Tier 3.

### Tier 3: Raw file parsing (fallback -- always works)

If neither ubc CLI nor ubCode MCP is available, parse source files directly.

#### Step 3a: Find all documentation files

Use Glob to find RST and MD files in the source directory:

```
Glob: **/*.rst  (in source directory)
Glob: **/*.md   (in source directory)
```

Exclude `_build/`, `build/`, and other output directories.

#### Step 3b: Find need directives

Use Grep to search for need directives across all documentation files.
Build the pattern from the project's configured type directives.

For RST files, search for:
```
\.\. (req|spec|impl|test)::
```

Replace `(req|spec|impl|test)` with the actual directive names from the project configuration.
If you could not read the project configuration, use a broad pattern:
```
\.\. \w+::
```
Then filter results to known sphinx-needs directive patterns (those followed by option lines with `:id:`).

#### Step 3c: Parse individual need directives

For each found directive, read the surrounding lines to extract the full need. A need directive in RST has this structure:

```rst
.. <type>:: <title>
   :id: <id>
   :status: <status>
   :tags: <tag1>; <tag2>
   :links: <id1>, <id2>
   :<extra_link>: <id1>, <id2>

   <content body>
```

Parsing rules:
- **Line 1**: `.. <type>:: <title>` -- The directive line. Extract type and title.
- **Option lines**: Indented by 3 spaces, format `:<option>: <value>`. Read all consecutive option lines.
  - `:id:` -- The need's unique identifier. Required if `id_required` is true.
  - `:status:` -- Status value (e.g., open, in_progress, closed).
  - `:tags:` -- Semicolon-separated tags.
  - `:links:` -- Comma-separated list of linked need IDs (generic links).
  - Any extra_link name from the project config (e.g., `:implements:`, `:tests:`) -- Comma-separated need IDs.
- **Content body**: After the options, indented text is the need's description/content. Content continues until the indentation returns to the directive's parent level or a blank line followed by non-indented text.

#### Step 3d: Build a needs index

After parsing all directives, build a structured index:

For each need, record:
- `id`: The need's unique identifier
- `type`: The directive type (e.g., `req`, `spec`)
- `title`: The title from the directive line
- `status`: The status value
- `tags`: List of tags
- `links`: List of IDs from `:links:`
- `extra_links`: Dictionary mapping link type names to lists of target IDs (e.g., `{"implements": ["SPEC_001"]}`)
- `content`: The body text
- `file`: The source file path
- `line`: The line number of the directive

#### Step 3e: Build the link graph

From the needs index, construct the link graph:

- For each need with `:links:` values, create edges from that need to each target ID.
- For each need with extra_link values (e.g., `:implements: SPEC_001`), create typed edges.
- For each typed edge, also record the reverse direction using the `incoming` name from the extra_links config.

This graph enables traceability navigation in both directions.

---

## 4. Detect sphinx-codelinks

Check if the project uses sphinx-codelinks for code-to-requirement traceability.

### Step 4a: Check ubproject.toml

Look for `sphinx_codelinks` or `sphinx-codelinks` in the extensions or configuration sections.

### Step 4b: Check conf.py

Look in `conf.py` for:
- `"sphinx_codelinks"` in the `extensions` list
- `codelinks_*` configuration variables

### Step 4c: If codelinks are configured

Record that codelinks are available. When tracing a need, also search for code files that reference the need's ID via codelink patterns. This extends the traceability graph from documentation into source code.

Typical codelink patterns in code files:
- Comment annotations: `# codelink: REQ_001` or `// codelink: REQ_001`
- Decorator patterns defined in the codelinks configuration

When codelinks are detected, inform skills that change analysis and traceability should include code file references.

---

## 5. Read pharaoh.toml

Check for `pharaoh.toml` in the workspace root (same level as `ubproject.toml` or `conf.py`).

If found, read and parse the following sections:

- **`[pharaoh]`**: Top-level settings.
  - `strictness`: `"advisory"` (default) or `"enforcing"`.

- **`[pharaoh.id_scheme]`**: ID generation settings.
  - `pattern`: Template string (e.g., `"{TYPE}-{MODULE}-{NUMBER}"`).
  - `auto_increment`: Boolean.

- **`[pharaoh.workflow]`**: Workflow gate settings.
  - `require_change_analysis`: Boolean.
  - `require_verification`: Boolean.
  - `require_mece_on_release`: Boolean.

- **`[pharaoh.traceability]`**: Required link chains.
  - `required_links`: Array of strings like `"req -> spec"`.

- **`[pharaoh.codelinks]`**: Codelinks integration.
  - `enabled`: Boolean.

If `pharaoh.toml` is not found, apply defaults:
- `strictness = "advisory"`
- All workflow gates default to the values in `pharaoh.toml.example` (or treat as advisory)
- No required link chains
- Codelinks enabled if detected in Step 4

---

## 6. Summary of Detection Results

After completing steps 1--5, you should have:

1. **Project roots**: List of project root paths
2. **Source directories**: Documentation source path for each project
3. **Need types**: List of valid directive types with their prefixes
4. **Link types**: Standard `links` plus all extra_link names
5. **Data access tier**: Which tier (ubc CLI / ubCode MCP / raw files) is available
6. **Needs index**: Complete index of all needs (from whichever tier)
7. **Link graph**: Bidirectional graph of need relationships
8. **Codelinks status**: Whether sphinx-codelinks is configured
9. **Pharaoh config**: Strictness level, workflow gates, traceability requirements

Present a brief summary of what you detected before proceeding with the skill's main task. Example:

```
Project: Brake System (ubproject.toml)
Types: req, spec, impl, test
Links: links, implements, tests
Data source: ubc CLI (v1.2.0)
Needs found: 8
Strictness: advisory
```

If detection reveals issues (e.g., no project config found, no needs in source files), report the issue clearly and ask the user for guidance before proceeding.
