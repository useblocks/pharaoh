---
name: pharaoh-author
description: "Use when creating or modifying sphinx-needs requirements, specifications, implementations, or test cases with proper IDs, types, attributes, and links"
---

# pharaoh-author

AI-assisted creation and modification of sphinx-needs directives. This skill ensures correct RST syntax, proper IDs following the project's naming scheme, all required attributes, and valid links between needs. It respects the project schema defined in `ubproject.toml` or `conf.py`, including types, extra_links, ID rules, and extra_options.

---

## Strictness Check

Before executing any authoring operation, follow the instructions in `skills/shared/strictness.md`.

### Enforcing mode

1. Read `.pharaoh/session.json`.
2. Identify the need IDs affected by the authoring request:
   - For **new needs**: identify the parent need(s) the new need will link to.
   - For **modifications**: identify the need ID being modified.
3. Check if `require_change_analysis = true` in `pharaoh.toml` (or use the default of `true`).
4. For each affected need ID, verify that `changes.<need_id>.acknowledged` is `true` in session state.
5. If any affected need lacks an acknowledged change analysis, block:

```
Blocked: Change analysis required before authoring.
Run pharaoh:change for the affected requirements first.
Needs missing change analysis: <list of need IDs>
```

6. Do not proceed. Do not partially execute. Stop at the gate.

### Advisory mode

Execute the authoring request fully. After completion, check whether a change analysis was performed for the affected needs. If not, append a single tip:

```
Tip: Consider running pharaoh:change first to understand the impact of this modification.
```

Do not show this tip if it was already shown in the current session.

---

## Process

### Step 1: Understand the request

Determine what the user is asking for:

- **Create a new need**: The user wants a new requirement, specification, implementation, test case, or other configured need type.
- **Modify an existing need**: The user wants to change an attribute (status, tags, content, links) of an existing need.

Clarify with the user if any of the following are ambiguous:

- **Type**: Which need type should be used? (req, spec, impl, test, or a custom type)
- **Content**: What is the requirement text or description?
- **Links**: Which existing needs should this need link to? What link types apply?
- **File placement**: Where should the need be written?

If the user provides enough context to determine all of these, proceed without asking.

---

### Step 2: Read project schema

Follow the instructions in `skills/shared/data-access.md` to detect the project structure and read the configuration. Specifically, you need:

#### 2a. Need types

Read the `types` array from `ubproject.toml` (under `[needs]`) or `needs_types` from `conf.py`. Record:

- `directive`: The RST directive name (e.g., `req`, `spec`, `impl`, `test`)
- `prefix`: The ID prefix for this type (e.g., `REQ_`, `SPEC_`, `IMPL_`, `TEST_`)
- `title`: The display title (e.g., `Requirement`, `Specification`)

Validate that the requested type exists in the project configuration. If it does not, warn the user and list available types.

#### 2b. Extra links

Read `extra_links` from `ubproject.toml` (under `[needs.extra_links]`) or `needs_extra_links` from `conf.py`. Record each link type:

- The option name (e.g., `implements`, `tests`)
- The `incoming` label (e.g., `is implemented by`)
- The `outgoing` label (e.g., `implements`)

These are the valid link option names that can appear in a need directive in addition to the standard `:links:` option.

#### 2c. ID settings

Read from `ubproject.toml` or `conf.py`:

- `id_required`: Whether every need must have an explicit `:id:` (boolean).
- `id_length`: Minimum length of the numeric portion of the ID (integer).

#### 2d. ID scheme (pharaoh-specific)

Read from `pharaoh.toml` if it exists:

- `[pharaoh.id_scheme].pattern`: Template for generating IDs (e.g., `"{TYPE}-{MODULE}-{NUMBER}"`).
- `[pharaoh.id_scheme].auto_increment`: Whether to auto-increment the numeric portion.

If `pharaoh.toml` does not exist or has no `id_scheme` section, IDs will be inferred from existing needs in Step 3.

#### 2e. Extra options

Read `extra_options` from `ubproject.toml` or `needs_extra_options` from `conf.py`. These are additional metadata fields that can appear on need directives (e.g., `priority`, `version`, `author`).

#### 2f. Traceability requirements

Read `[pharaoh.traceability].required_links` from `pharaoh.toml` if it exists. These define expected link chains (e.g., `"req -> spec"`) that indicate which link types should connect need types. Use this information to suggest appropriate links when creating new needs.

---

### Step 3: Generate ID (for new needs)

When creating a new need, generate a unique ID.

#### 3a. Check pharaoh.toml id_scheme

If `pharaoh.toml` has an `[pharaoh.id_scheme]` section with a `pattern`:

1. Parse the pattern. Supported placeholders:
   - `{TYPE}` -- replaced with the type prefix (e.g., `REQ`, `SPEC`). Use the prefix from the type definition, stripped of trailing underscores or hyphens.
   - `{MODULE}` -- replaced with the module name. Determine the module from:
     - The user's explicit input (e.g., "create a braking requirement")
     - The file location (e.g., `docs/braking/requirements.rst` suggests module `BRAKING`)
     - The parent need's ID if it contains a module segment
     - Ask the user if the module cannot be determined.
   - `{NUMBER}` -- replaced with a zero-padded sequential number.

2. If `auto_increment = true`, find the highest existing number for the same type and module combination, then increment by 1. Pad the number to match `id_length` from the project configuration.

3. Example: pattern `"{TYPE}-{MODULE}-{NUMBER}"` with type `req`, module `BRAKE`, next number `004` produces `REQ-BRAKE-004`.

#### 3b. Infer from existing IDs (fallback)

If no `id_scheme` is configured:

1. Use the needs index (from ubc CLI, ubCode MCP, or raw file parsing) to find all existing needs of the same type.
2. Extract their IDs and identify the naming pattern. Common patterns:
   - `PREFIX_NNN` (e.g., `REQ_001`, `REQ_002`)
   - `PREFIX-MODULE-NNN` (e.g., `REQ-BRAKE-001`)
   - `PREFIXNNN` (e.g., `REQ001`)
3. Find the highest sequential number for the given type/prefix.
4. Increment by 1 and pad to match the existing number width.
5. Use the type's prefix from the configuration.

#### 3c. Validate uniqueness

After generating the ID, verify it does not already exist in the needs index. If it does (due to gaps in numbering or manual IDs), increment until a unique ID is found.

---

### Step 4: Create or modify the directive

#### 4a. Creating a new need

Generate a complete RST directive. Follow this structure exactly:

```rst
.. <type>:: <title>
   :id: <generated_id>
   :status: <status>
   :tags: <tag1>; <tag2>
   :links: <id1>, <id2>
   :<extra_link>: <id1>, <id2>

   <content body>
```

Formatting rules:

- **Directive line**: `.. <type>:: <title>` with exactly one space after `..` and one space after `::`.
- **Options**: Each option is indented by exactly 3 spaces. Format: `:<option>: <value>`.
- **Blank line**: One blank line separates the options from the content body.
- **Content body**: Indented by 3 spaces. May span multiple lines.
- **Trailing blank line**: One blank line after the content body to separate from the next directive or content.

Required attributes for every new need:

- `:id:` -- Always include. Generated in Step 3.
- `:status:` -- Default to `open` unless the user specifies otherwise. Use the project's status vocabulary if one is configured.

Recommended attributes:

- `:tags:` -- Include if the user provides tags or if the parent need has tags that should propagate. Separate tags with semicolons and spaces: `safety; braking`.
- `:links:` -- Include for generic bidirectional links.
- Extra link options (`:implements:`, `:tests:`, etc.) -- Use the appropriate extra link type based on the relationship. Prefer typed links over generic `:links:` when the relationship matches a configured extra_link.

Content body:

- Write clear, unambiguous text.
- For requirements, use "shall" statements (e.g., "The system shall...").
- Include the user's description verbatim if they provided specific wording.
- If the user provided only a brief description, expand it into a proper requirement statement while preserving the original intent. Confirm with the user before writing if the expansion changes the meaning.

#### 4b. Modifying an existing need

1. Locate the existing need in the source files using the needs index (file path and line number).
2. Read the full directive from the source file, including all options and content.
3. Make only the requested changes. Preserve:
   - The original indentation style (3 spaces for options, 3 spaces for content).
   - All attributes that were not requested to change.
   - The content body if not requested to change.
   - The position in the file.
4. Common modifications:
   - **Status change**: Replace the `:status:` value.
   - **Add a link**: Append to the existing `:links:` or extra link option. If the option does not exist yet, add it as a new option line after the existing options.
   - **Update tags**: Replace the `:tags:` value.
   - **Update content**: Replace the content body.
   - **Add an attribute**: Insert a new option line in the options block.
5. Use the Edit tool with the exact `old_string` and `new_string` to make precise, minimal changes.

---

### Step 5: Validate

After generating or modifying the directive, perform these checks before writing to disk.

#### 5a. Link target existence

For every ID referenced in `:links:` or any extra link option:

1. Check that the target ID exists in the needs index.
2. If a target ID does not exist, warn the user:

```
Warning: Link target "<ID>" does not exist in the project.
Check that the ID is correct, or create the target need first.
```

3. Ask the user whether to proceed with the non-existent link or remove it.

#### 5b. Link type validity

For every extra link option used (e.g., `:implements:`, `:tests:`):

1. Verify that the option name is a configured extra_link in the project.
2. If not, warn the user and suggest the correct option name or fall back to `:links:`.

#### 5c. ID format

Verify that the generated or existing ID:

1. Uses the correct prefix for the need type.
2. Meets the `id_length` requirement.
3. Matches the `id_regex` pattern if one is configured.

#### 5d. Run ubc check (if available)

If ubc CLI is available (check with `ubc --version`):

1. After writing the file, run `ubc check` from the project root.
2. Parse the output for errors and warnings related to the authored need.
3. If errors are found, report them and offer to fix:

```
ubc check found issues:
- ERROR: <description>
- WARNING: <description>

Shall I fix these issues?
```

---

### Step 6: Place in correct file

#### 6a. For modifications

The file is already known from the needs index. Write the changes to that file using the Edit tool.

#### 6b. For new needs

Determine the target file:

1. **User specifies a file**: Use the user's specified file path.
2. **Convention by type**: Check if the project organizes needs by type in separate files:
   - Look for files named by type: `requirements.rst`, `specifications.rst`, `implementations.rst`, `tests.rst` (or similar patterns).
   - If such a convention exists, place the new need in the corresponding file for its type.
3. **Convention by module**: Check if needs are organized by module in subdirectories:
   - Look for directory structures like `docs/braking/`, `docs/steering/`.
   - If the new need has a module context, place it in the corresponding directory.
4. **Same file as parent**: If the new need links to a parent need, consider placing it in the same file as the parent if there is no stronger convention.
5. **Ask the user**: If the placement cannot be determined, ask the user where to put the need.

#### 6c. Insertion position

When adding a new need to an existing file:

1. Place it after the last need of the same type in the file.
2. If no needs of the same type exist in the file, place it at the end of the file.
3. Ensure proper spacing: one blank line before the directive and one blank line after the content body.

#### 6d. Creating a new file

If a new file is needed:

1. Follow the project's file naming conventions (e.g., lowercase, underscores or hyphens).
2. Add a proper RST title at the top of the file:

```rst
<Title>
<underline matching title length>

.. <type>:: <title>
   :id: <id>
   ...
```

3. Use `=` for the title underline, matching the length of the title text.

---

### Step 7: Update session state

After successfully writing the need:

1. Read `.pharaoh/session.json` (or start with an empty structure if it does not exist).
2. Create the `.pharaoh/` directory if it does not exist.
3. For the authored need ID, set `changes.<need_id>.authored = true`.
4. If the need ID does not have an entry in `changes`, create one:

```json
{
  "<need_id>": {
    "change_analysis": null,
    "acknowledged": false,
    "authored": true,
    "verified": false
  }
}
```

5. Set `updated` to the current ISO 8601 timestamp.
6. Write the updated JSON back to `.pharaoh/session.json`.

### Follow-up suggestion

After authoring, suggest the next workflow step:

```
Next step: Run pharaoh:verify to validate the new/modified need against its linked requirements.
```

---

## Examples

### Example 1: Creating a new requirement

**User request**: "Create a new requirement for ABS activation threshold"

**Project context** (from `ubproject.toml`):
- Types: `req` (prefix `REQ_`), `spec`, `impl`, `test`
- Existing needs: REQ_001, REQ_002, REQ_003
- No `pharaoh.toml` id_scheme configured

**Process**:

1. Type: `req` (user asked for a requirement).
2. Next ID: REQ_004 (highest existing is REQ_003, increment by 1).
3. No parent link specified by user, so no `:links:` needed.

**Output written to `requirements.rst`**:

```rst
.. req:: ABS activation threshold
   :id: REQ_004
   :status: open
   :tags: safety; abs

   The anti-lock braking system shall activate when wheel slip exceeds 15% of vehicle speed.
```

---

### Example 2: Creating a specification linked to a requirement

**User request**: "Create a spec for REQ_004 covering the ABS sensor interface"

**Project context**:
- Extra links: `implements` (but for spec->req the standard `:links:` is appropriate)
- Existing specs: SPEC_001, SPEC_002, SPEC_003
- Traceability requirement: `req -> spec`

**Process**:

1. Type: `spec` (user asked for a spec).
2. Next ID: SPEC_004.
3. Link to REQ_004 using `:links:` (spec to req is a generic link in this project's configuration).
4. Validate that REQ_004 exists in the needs index.

**Output written to `specifications.rst`**:

```rst
.. spec:: ABS sensor interface
   :id: SPEC_004
   :status: open
   :links: REQ_004

   The ABS controller shall read wheel speed from four individual wheel speed sensors
   via CAN bus. Sensor sampling rate: 500Hz. Signal resolution: 0.1 km/h.
```

---

### Example 3: Modifying an existing need's status

**User request**: "Set REQ_001 status to approved"

**Process**:

1. Locate REQ_001 in the needs index. Found in `docs/requirements.rst` at line 4.
2. Read the directive. Current status is `open`.
3. Replace `:status: open` with `:status: approved`.
4. Preserve all other attributes and content.

**Edit applied** (only the changed line):

```
old: "   :status: open"
new: "   :status: approved"
```

The rest of the directive remains unchanged:

```rst
.. req:: Brake response time
   :id: REQ_001
   :status: approved
   :tags: safety; braking

   The brake system shall respond within 100ms of pedal input.
```

---

### Example 4: Adding a link to an existing need

**User request**: "Add an implements link from IMPL_001 to SPEC_003"

**Project context**:
- Extra links: `implements` is configured
- IMPL_001 currently has `:implements: SPEC_001`

**Process**:

1. Locate IMPL_001 in the needs index. Found in `docs/implementations.rst` at line 4.
2. Read the directive. Current `:implements:` value is `SPEC_001`.
3. Validate that SPEC_003 exists in the needs index.
4. Append SPEC_003 to the existing `:implements:` option.

**Edit applied**:

```
old: "   :implements: SPEC_001"
new: "   :implements: SPEC_001, SPEC_003"
```

The full directive after modification:

```rst
.. impl:: Brake pedal driver
   :id: IMPL_001
   :status: open
   :implements: SPEC_001, SPEC_003

   CAN driver for brake pedal sensor communication.
```

---

### Example 5: Creating a need with pharaoh.toml id_scheme

**User request**: "Create a test case for IMPL_002 in the braking module"

**Project context**:
- `pharaoh.toml` id_scheme: `pattern = "{TYPE}-{MODULE}-{NUMBER}"`, `auto_increment = true`
- Extra links: `tests` is configured
- Existing tests with `BRAKE` module: TEST-BRAKE-001, TEST-BRAKE-002

**Process**:

1. Type: `test`.
2. Module: `BRAKE` (user said "braking module").
3. Pattern: `{TYPE}-{MODULE}-{NUMBER}` resolves to `TEST-BRAKE-003`.
4. Link to IMPL_002 using `:tests:` (the configured extra link for test-to-implementation relationships).
5. Validate that IMPL_002 exists.

**Output written to `docs/braking/tests.rst`**:

```rst
.. test:: EBD module integration test
   :id: TEST-BRAKE-003
   :status: open
   :tests: IMPL_002

   Verify that the electronic brake force distribution module correctly distributes
   braking force across all wheels under varying load conditions.
   Test conditions: dry road, wet road, split-mu surface.
```
