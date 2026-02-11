# Pharaoh Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the Pharaoh skill-based AI assistant framework for sphinx-needs projects, supporting both Claude Code (plugin with skills) and GitHub Copilot (agents + prompts).

**Architecture:** Pure prompt architecture - no runtime binary. All analysis logic is encoded in skill/agent markdown instructions. The AI is the runtime. Three-tier data access: ubc CLI (best) > ubCode MCP (VS Code) > raw file parsing (fallback).

**Tech Stack:** Markdown (SKILL.md, agent.md), YAML frontmatter, TOML (pharaoh.toml), JSON (plugin manifest)

**Reference:** See `docs/plans/2026-02-11-pharaoh-design.md` for full design document.

---

## Phase 1: Project Foundation

### Task 1: Project Scaffolding

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `LICENSE`
- Create: `.gitignore`
- Create: `pharaoh.toml.example`

**Step 1: Create plugin manifest**

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "pharaoh",
  "description": "AI assistant framework for sphinx-needs projects: change analysis, traceability, MECE, authoring, verification, and release management",
  "version": "0.1.0",
  "author": {
    "name": "patdhlk"
  },
  "repository": "https://github.com/patdhlk/pharaoh",
  "license": "MIT",
  "keywords": ["sphinx-needs", "requirements", "traceability", "change-analysis", "mece", "safety-critical", "automotive"]
}
```

**Step 2: Create marketplace manifest**

Create `.claude-plugin/marketplace.json`:

```json
{
  "name": "pharaoh-dev",
  "description": "Development marketplace for Pharaoh sphinx-needs AI assistant",
  "owner": {
    "name": "patdhlk"
  },
  "plugins": [
    {
      "name": "pharaoh",
      "description": "AI assistant framework for sphinx-needs projects",
      "version": "0.1.0",
      "source": "./",
      "author": {
        "name": "patdhlk"
      }
    }
  ]
}
```

**Step 3: Create LICENSE**

Create `LICENSE` with MIT license text, year 2026, copyright holder "patdhlk".

**Step 4: Create .gitignore**

Create `.gitignore`:

```
.pharaoh/
*.pyc
__pycache__/
.DS_Store
```

**Step 5: Create pharaoh.toml.example**

Create `pharaoh.toml.example`:

```toml
# Pharaoh configuration
# Copy to pharaoh.toml and adjust to your project needs.
# All settings are optional. Without this file, advisory mode applies.

[pharaoh]
# "advisory" (default) - suggests workflow but never blocks
# "enforcing" - skills gate each other per workflow rules
strictness = "advisory"

[pharaoh.id_scheme]
# Pattern for generating new need IDs
# Available placeholders: {TYPE}, {MODULE}, {NUMBER}
pattern = "{TYPE}-{MODULE}-{NUMBER}"
auto_increment = true

[pharaoh.workflow]
# Require pharaoh:change before pharaoh:author
require_change_analysis = true
# Require pharaoh:verify before pharaoh:release
require_verification = true
# Require pharaoh:mece before pharaoh:release (optional)
require_mece_on_release = false

[pharaoh.traceability]
# Required link chains - pharaoh:mece reports violations
# Format: "source_type -> target_type"
required_links = [
    "req -> spec",
    "spec -> impl",
    "impl -> test",
]

[pharaoh.codelinks]
# Follow sphinx-codelinks in change analysis
enabled = true
```

**Step 6: Commit**

```bash
git add .claude-plugin/ LICENSE .gitignore pharaoh.toml.example
git commit -m "Add project scaffolding: plugin manifest, license, config template"
```

---

### Task 2: Test Fixture

Create a minimal sphinx-needs project to verify skills against.

**Files:**
- Create: `tests/fixtures/basic-project/conf.py`
- Create: `tests/fixtures/basic-project/ubproject.toml`
- Create: `tests/fixtures/basic-project/docs/requirements.rst`
- Create: `tests/fixtures/basic-project/docs/specifications.rst`
- Create: `tests/fixtures/basic-project/docs/implementations.rst`
- Create: `tests/fixtures/basic-project/docs/tests.rst`

**Step 1: Create conf.py**

Create `tests/fixtures/basic-project/conf.py`:

```python
extensions = ["sphinx_needs"]
needs_from_toml = "ubproject.toml"
```

**Step 2: Create ubproject.toml**

Create `tests/fixtures/basic-project/ubproject.toml`:

```toml
[project]
name = "Brake System"

[needs]
id_required = true
id_length = 3
types = [
    {directive = "req", title = "Requirement", prefix = "REQ_", color = "#BFD8D2", style = "node"},
    {directive = "spec", title = "Specification", prefix = "SPEC_", color = "#FEDCD2", style = "node"},
    {directive = "impl", title = "Implementation", prefix = "IMPL_", color = "#DF744A", style = "node"},
    {directive = "test", title = "Test Case", prefix = "TEST_", color = "#DCB239", style = "node"},
]

[needs.extra_links]
implements = {incoming = "is implemented by", outgoing = "implements"}
tests = {incoming = "is tested by", outgoing = "tests"}
```

**Step 3: Create requirements.rst**

Create `tests/fixtures/basic-project/docs/requirements.rst`:

```rst
Requirements
============

.. req:: Brake response time
   :id: REQ_001
   :status: open
   :tags: safety; braking

   The brake system shall respond within 100ms of pedal input.

.. req:: Brake force distribution
   :id: REQ_002
   :status: open
   :tags: safety; braking
   :links: REQ_001

   The brake system shall distribute force proportionally across all wheels.

.. req:: Emergency brake activation
   :id: REQ_003
   :status: open
   :tags: safety; emergency

   The emergency brake shall activate when deceleration exceeds 8m/s².
```

**Step 4: Create specifications.rst**

Create `tests/fixtures/basic-project/docs/specifications.rst`:

```rst
Specifications
==============

.. spec:: Brake pedal sensor interface
   :id: SPEC_001
   :status: open
   :links: REQ_001

   The brake pedal sensor shall use CAN bus at 500kbps.
   Signal update rate: 10ms.

.. spec:: Force distribution algorithm
   :id: SPEC_002
   :status: open
   :links: REQ_002

   Electronic brake force distribution using wheel speed sensors.
   Algorithm: proportional distribution based on axle load.

.. spec:: Emergency detection logic
   :id: SPEC_003
   :status: open
   :links: REQ_003

   Deceleration threshold detection using IMU sensor data.
   Sampling rate: 1kHz. Trigger threshold: 8m/s² sustained for 50ms.
```

**Step 5: Create implementations.rst**

Create `tests/fixtures/basic-project/docs/implementations.rst`:

```rst
Implementations
===============

.. impl:: Brake pedal driver
   :id: IMPL_001
   :status: open
   :implements: SPEC_001

   CAN driver for brake pedal sensor communication.

.. impl:: EBD module
   :id: IMPL_002
   :status: open
   :implements: SPEC_002

   Electronic brake force distribution module.
```

**Step 6: Create tests.rst**

Create `tests/fixtures/basic-project/docs/tests.rst`:

```rst
Test Cases
==========

.. test:: Brake response time test
   :id: TEST_001
   :status: open
   :tests: IMPL_001

   Verify brake response within 100ms under nominal conditions.

.. test:: Force distribution test
   :id: TEST_002
   :status: open
   :tests: IMPL_002

   Verify proportional force distribution across all wheels.
```

**Step 7: Commit**

```bash
git add tests/
git commit -m "Add test fixture: minimal brake system sphinx-needs project"
```

---

## Phase 2: Core Skills (Claude Code)

### Task 3: Shared Data Access Instructions

Before writing individual skills, create a shared reference document that all skills include for the three-tier data access pattern and project detection logic.

**Files:**
- Create: `skills/shared/data-access.md`
- Create: `skills/shared/strictness.md`

**Step 1: Create data-access.md**

Create `skills/shared/data-access.md` containing instructions for:
1. Detecting project structure (ubproject.toml > conf.py)
2. Checking ubc CLI availability (`ubc --version`)
3. Using ubc CLI commands (`ubc build needs --format json`, `ubc config`, etc.)
4. Falling back to ubCode MCP tools if available
5. Falling back to raw RST/MD parsing using grep/read tools
6. Reading pharaoh.toml for workflow config
7. Detecting sphinx-codelinks configuration

This document is referenced by all skills that need project data. Full content specified in implementation.

**Step 2: Create strictness.md**

Create `skills/shared/strictness.md` containing instructions for:
1. Reading pharaoh.toml strictness setting
2. Advisory mode behavior (suggest, don't block)
3. Enforcing mode behavior (check session.json, block if prerequisites missing)
4. Session state management (.pharaoh/session.json)

**Step 3: Commit**

```bash
git add skills/shared/
git commit -m "Add shared skill instructions: data access and strictness handling"
```

---

### Task 4: pharaoh-setup Skill

**Files:**
- Create: `skills/pharaoh-setup/SKILL.md`

**Step 1: Write the skill**

Create `skills/pharaoh-setup/SKILL.md` with:
- YAML frontmatter: `name: pharaoh-setup`, `description: "Use when setting up Pharaoh in a sphinx-needs project for the first time or scaffolding Copilot agents"`
- Project detection logic (find conf.py, ubproject.toml, detect structure)
- Generate pharaoh.toml from detected settings
- Scaffold Copilot agents into .github/ (copy from copilot/ templates)
- Check ubc CLI availability and recommend installation
- Guide ubCode MCP configuration for Claude Code users
- Add .pharaoh/ to .gitignore

**Step 2: Verify skill format**

Check that SKILL.md has valid YAML frontmatter, name uses only letters/numbers/hyphens, description starts with "Use when".

**Step 3: Commit**

```bash
git add skills/pharaoh-setup/
git commit -m "Add pharaoh-setup skill: project detection and scaffolding"
```

---

### Task 5: pharaoh-trace Skill

**Files:**
- Create: `skills/pharaoh-trace/SKILL.md`

**Step 1: Write the skill**

Create `skills/pharaoh-trace/SKILL.md` with:
- YAML frontmatter: `name: pharaoh-trace`, `description: "Use when navigating traceability links between requirements, specifications, implementations, tests, and code"`
- Data access instructions (reference shared/data-access.md)
- Given a need ID, trace upstream (what does it satisfy?) and downstream (what satisfies it?)
- Follow all link types: standard links, extra_links (implements, tests, etc.), codelinks
- Present results as a traceability tree/table
- Support tracing from any level in any direction
- Handle multi-project setups (external needs)

**Step 2: Verify against test fixture**

Mentally verify the skill instructions would correctly trace REQ_001 -> SPEC_001 -> IMPL_001 -> TEST_001 in the test fixture.

**Step 3: Commit**

```bash
git add skills/pharaoh-trace/
git commit -m "Add pharaoh-trace skill: traceability navigation"
```

---

### Task 6: pharaoh-change Skill

**Files:**
- Create: `skills/pharaoh-change/SKILL.md`

**Step 1: Write the skill**

Create `skills/pharaoh-change/SKILL.md` with:
- YAML frontmatter: `name: pharaoh-change`, `description: "Use when analyzing the impact of changing a requirement, specification, or any sphinx-needs item"`
- Data access instructions (reference shared/data-access.md)
- Identify target need(s) from user input
- Trace all links from target (using pharaoh-trace logic) in both directions
- If codelinks enabled, find affected code files
- Produce a Change Document with:
  - Directly affected needs (one hop)
  - Transitively affected needs (full graph)
  - Affected code files (via codelinks)
  - Suggested action per affected item (update/review/no change needed)
- Write session state to .pharaoh/session.json
- Strictness handling (reference shared/strictness.md)

**Step 2: Verify against test fixture**

Mentally verify: changing REQ_001 should surface SPEC_001, IMPL_001, TEST_001 and REQ_002 (linked via links:).

**Step 3: Commit**

```bash
git add skills/pharaoh-change/
git commit -m "Add pharaoh-change skill: change impact analysis"
```

---

### Task 7: pharaoh-mece Skill

**Files:**
- Create: `skills/pharaoh-mece/SKILL.md`

**Step 1: Write the skill**

Create `skills/pharaoh-mece/SKILL.md` with:
- YAML frontmatter: `name: pharaoh-mece`, `description: "Use when checking for gaps, redundancies, and inconsistencies in sphinx-needs requirements"`
- Data access instructions (reference shared/data-access.md)
- MECE analysis:
  - **Gaps**: Requirements without specifications, specs without implementations, impls without tests (based on pharaoh.toml required_links)
  - **Orphans**: Needs with no incoming or outgoing links
  - **Redundancy**: Multiple needs covering the same concern (semantic similarity check)
  - **Status inconsistencies**: Parent open but child closed, etc.
  - **ID scheme violations**: IDs not matching the configured pattern
- If ubc available, use `ubc check` and `ubc schema validate` for additional validation
- Present results grouped by category with severity (error/warning/info)

**Step 2: Verify against test fixture**

Mentally verify: REQ_003 -> SPEC_003 exists, but SPEC_003 has no impl, and there's no test for it. MECE should flag these gaps.

**Step 3: Commit**

```bash
git add skills/pharaoh-mece/
git commit -m "Add pharaoh-mece skill: gap and redundancy analysis"
```

---

### Task 8: pharaoh-author Skill

**Files:**
- Create: `skills/pharaoh-author/SKILL.md`

**Step 1: Write the skill**

Create `skills/pharaoh-author/SKILL.md` with:
- YAML frontmatter: `name: pharaoh-author`, `description: "Use when creating or modifying sphinx-needs requirements, specifications, implementations, or test cases"`
- Strictness check: if enforcing, verify pharaoh:change was run first (check session.json)
- Read project schema from ubproject.toml/conf.py (need types, extra_links, ID patterns)
- Generate new need ID following the project's ID scheme (pharaoh.toml id_scheme or auto-detect from existing IDs)
- Create need directive with proper RST/MD syntax, all required attributes, and links
- When modifying existing needs, preserve formatting and only change specified attributes
- Validate the new/modified need against project schema
- Advisory tip: suggest running pharaoh:verify after authoring

**Step 2: Verify against test fixture**

Mentally verify: creating a new impl for SPEC_003 should generate IMPL_003 with `:implements: SPEC_003` in the correct RST format.

**Step 3: Commit**

```bash
git add skills/pharaoh-author/
git commit -m "Add pharaoh-author skill: AI-assisted requirement authoring"
```

---

### Task 9: pharaoh-verify Skill

**Files:**
- Create: `skills/pharaoh-verify/SKILL.md`

**Step 1: Write the skill**

Create `skills/pharaoh-verify/SKILL.md` with:
- YAML frontmatter: `name: pharaoh-verify`, `description: "Use when validating that implementations satisfy their linked requirements and specifications"`
- Data access instructions (reference shared/data-access.md)
- For each need with outgoing links (e.g., spec -> req):
  - Read the parent need's content
  - Read the child need's content
  - Assess whether the child adequately addresses the parent
  - Flag mismatches, incomplete coverage, contradictions
- If ubc available, run `ubc check` and `ubc schema validate`
- Present verification results per need pair with pass/fail/warning
- Update session state (.pharaoh/session.json) with verification results
- Strictness: required before pharaoh:release in enforcing mode

**Step 2: Verify against test fixture**

Mentally verify: SPEC_001 should satisfy REQ_001 (both about brake response time and CAN interface).

**Step 3: Commit**

```bash
git add skills/pharaoh-verify/
git commit -m "Add pharaoh-verify skill: requirement satisfaction validation"
```

---

### Task 10: pharaoh-release Skill

**Files:**
- Create: `skills/pharaoh-release/SKILL.md`

**Step 1: Write the skill**

Create `skills/pharaoh-release/SKILL.md` with:
- YAML frontmatter: `name: pharaoh-release`, `description: "Use when preparing a release, generating changelogs, or summarizing requirement changes for version management"`
- Strictness check: if enforcing, verify pharaoh:verify passed and optionally pharaoh:mece
- If ubc available, use `ubc diff` for impact analysis between versions
- Otherwise, use git diff to find changed need directives
- Generate:
  - Change summary: new/modified/removed needs grouped by type
  - Traceability impact: which links were added/removed/changed
  - Verification status: which needs passed verification
  - Release notes in markdown format
- Support versioned output (link to git tags or manual version input)

**Step 2: Commit**

```bash
git add skills/pharaoh-release/
git commit -m "Add pharaoh-release skill: release management and changelogs"
```

---

### Task 11: pharaoh-plan Skill

**Files:**
- Create: `skills/pharaoh-plan/SKILL.md`

**Step 1: Write the skill**

Create `skills/pharaoh-plan/SKILL.md` with:
- YAML frontmatter: `name: pharaoh-plan`, `description: "Use when breaking requirement changes into structured implementation tasks with workflow enforcement"`
- Given a set of requirement changes (from pharaoh:change output or user description):
  - Break into ordered tasks: change analysis -> authoring -> verification -> release
  - Each task specifies which needs to modify and what changes to make
  - Respect pharaoh.toml workflow gates
  - Estimate scope (number of needs affected, files to modify)
- Present plan as a numbered task list with dependencies
- Offer to execute tasks sequentially using pharaoh skills

**Step 2: Commit**

```bash
git add skills/pharaoh-plan/
git commit -m "Add pharaoh-plan skill: structured implementation planning"
```

---

## Phase 3: Subagent

### Task 12: sphinx-needs-expert Agent

**Files:**
- Create: `agents/sphinx-needs-expert/agent.md`

**Step 1: Write the agent**

Create `agents/sphinx-needs-expert/agent.md` with:
- YAML frontmatter: `name: sphinx-needs-expert`, `description` with example interactions, `model: inherit`
- Role: Deep analysis expert for sphinx-needs projects
- Capabilities: parse complex RST/MD need structures, resolve traceability across multiple projects, analyze large requirement sets
- Used by skills that need to delegate heavy analysis (e.g., MECE on large projects, complex traceability queries)
- Includes data access instructions (three-tier pattern)

**Step 2: Commit**

```bash
git add agents/
git commit -m "Add sphinx-needs-expert subagent for deep analysis tasks"
```

---

## Phase 4: Copilot Integration

### Task 13: Copilot Agents

**Files:**
- Create: `copilot/agents/pharaoh.setup.agent.md`
- Create: `copilot/agents/pharaoh.change.agent.md`
- Create: `copilot/agents/pharaoh.trace.agent.md`
- Create: `copilot/agents/pharaoh.mece.agent.md`
- Create: `copilot/agents/pharaoh.author.agent.md`
- Create: `copilot/agents/pharaoh.verify.agent.md`
- Create: `copilot/agents/pharaoh.release.agent.md`
- Create: `copilot/agents/pharaoh.plan.agent.md`

**Step 1: Create all 8 Copilot agents**

Each agent mirrors its corresponding Claude Code skill but uses Copilot agent format:
- YAML frontmatter with `description` and `handoffs` (defining workflow transitions)
- Same analysis logic as the Claude skill
- References ubc CLI and ubCode MCP for data access
- Falls back to raw file parsing

Handoff chains:
- `pharaoh.change` -> `pharaoh.author`, `pharaoh.mece`, `pharaoh.trace`
- `pharaoh.author` -> `pharaoh.verify`
- `pharaoh.verify` -> `pharaoh.release`
- `pharaoh.mece` -> `pharaoh.author`
- `pharaoh.plan` -> `pharaoh.change`

**Step 2: Commit**

```bash
git add copilot/agents/
git commit -m "Add Copilot agents: all 8 pharaoh agents with handoff chains"
```

---

### Task 14: Copilot Prompts and Instructions

**Files:**
- Create: `copilot/prompts/pharaoh.change.prompt.md`
- Create: `copilot/prompts/pharaoh.trace.prompt.md`
- Create: `copilot/prompts/pharaoh.mece.prompt.md`
- Create: `copilot/prompts/pharaoh.author.prompt.md`
- Create: `copilot/prompts/pharaoh.verify.prompt.md`
- Create: `copilot/prompts/pharaoh.release.prompt.md`
- Create: `copilot/prompts/pharaoh.plan.prompt.md`
- Create: `copilot/copilot-instructions.md`

**Step 1: Create prompt files**

Each prompt file is minimal YAML referencing its agent:

```yaml
---
agent: pharaoh.change
---
```

No prompt file for `pharaoh.setup` - it's invoked directly as an agent.

**Step 2: Create copilot-instructions.md**

General Pharaoh context for Copilot:
- What Pharaoh is and its core principles
- Available agents and when to use them
- Three-tier data access pattern
- Advisory vs enforcing mode explanation
- Recommended workflow: change -> author -> verify -> release

**Step 3: Commit**

```bash
git add copilot/prompts/ copilot/copilot-instructions.md
git commit -m "Add Copilot prompts and general instructions"
```

---

## Phase 5: Finalize

### Task 15: README

**Files:**
- Create: `README.md`

**Step 1: Write README**

Create `README.md` covering:
- What Pharaoh is (one paragraph)
- Quick start for Claude Code (`/plugin install pharaoh`)
- Quick start for Copilot (`@pharaoh.setup`)
- Three experience tiers (basic / good with ubc / best with ubCode)
- Available skills/agents table
- Configuration (pharaoh.toml)
- Advisory vs enforcing mode
- Links to design document
- License (MIT)

**Step 2: Commit**

```bash
git add README.md
git commit -m "Add README with quick start guides and documentation"
```

---

## Execution Order & Dependencies

```
Task 1  (scaffolding)        ─┐
Task 2  (test fixture)        ├─> Task 3 (shared data access)
                               │
Task 3  (shared instructions) ─┤
                               ├─> Task 4 (setup)
                               ├─> Task 5 (trace)
                               │      │
                               │      ├─> Task 6 (change)
                               │      │      │
                               │      │      ├─> Task 8 (author)
                               │      │      └─> Task 11 (plan)
                               │      │
                               │      └─> Task 7 (mece)
                               │
                               ├─> Task 9 (verify)
                               └─> Task 10 (release)

Task 12 (subagent)           ─── independent

Task 13 (copilot agents)     ─── after all Claude skills (Tasks 4-11)
Task 14 (copilot prompts)    ─── after Task 13
Task 15 (README)             ─── after all tasks
```
