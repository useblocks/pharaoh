# Pharaoh - Design Document

**Date:** 2026-02-11
**Status:** Draft

## Vision

Pharaoh is a skill-based AI assistant framework for sphinx-needs projects. It combines structured development workflows (inspired by [superpowers](https://github.com/obra/superpowers)) with requirements engineering intelligence (inspired by [syspilot](https://github.com/enthali/syspilot)) to help teams author, analyze, trace, and validate requirements using AI.

### Core Principles

- **Static-first data access** - Parse RST/MD source files directly; use ubc CLI or ubCode MCP when available for speed and accuracy
- **Advisory by default, strict when configured** - `pharaoh.toml` controls enforcement level; no config = advisory mode with guardrails
- **Platform-native UX** - Skills in Claude Code (`/pharaoh:change`), agents in Copilot (`@pharaoh.change`), same logic underneath
- **Safety-critical ready** - Designed for A-SPICE/ISO 26262 workflows but usable by any sphinx-needs team
- **Zero mandatory dependencies** - Works with just the AI reading files; ubc CLI and ubCode are recommended accelerators

### What Pharaoh Is NOT

- Not a Sphinx build tool or replacement for sphinx-needs
- Not a general-purpose coding workflow (superpowers already does that)
- Focused exclusively on the requirements/documentation engineering domain

### Sphinx-Codelinks Support

When a project uses [sphinx-codelinks](https://sphinx-codelinks.useblocks.com/), Pharaoh follows codelink references in its traceability analysis. A change to a requirement surfaces affected code files, not just other requirements.

```
User Story -> Requirement -> Spec -> Implementation -> Test
                                          |
                                     Code (via sphinx-codelinks)
```

## Target Audience

- **Primary:** Automotive/safety-critical engineers following A-SPICE, ISO 26262, or similar standards who manage thousands of requirements in sphinx-needs
- **Secondary:** Any team using sphinx-needs for structured documentation who wants AI-assisted requirements workflows

## Platform Support

| Platform | Integration Mechanism |
|---|---|
| Claude Code | Plugin with skills that auto-trigger (`/pharaoh:change`) |
| GitHub Copilot | `.github/agents` + `.github/prompts` scaffolded into user projects (`@pharaoh.change`) |

Both platforms share identical analysis logic encoded in the skill/agent instructions. The AI is the runtime.

## Capabilities

Eight skills/agents, each with a clear responsibility:

| Skill / Agent | Purpose |
|---|---|
| `pharaoh:setup` / `@pharaoh.setup` | Scaffold Pharaoh into a project - detect structure, generate `pharaoh.toml`, install Copilot agents |
| `pharaoh:change` / `@pharaoh.change` | Analyze impact of a change - trace through needs links AND codelinks, produce a Change Document listing all affected items |
| `pharaoh:trace` / `@pharaoh.trace` | Navigate traceability in any direction - show everything linked to a need across all levels including code |
| `pharaoh:mece` / `@pharaoh.mece` | Gap and redundancy analysis - find requirements without specs, specs without tests, orphaned items, MECE violations |
| `pharaoh:author` / `@pharaoh.author` | AI-assisted requirement authoring - create new needs with proper IDs, types, attributes, and links following project schema |
| `pharaoh:verify` / `@pharaoh.verify` | Validate implementations against linked requirements - check that specs satisfy their parent requirements |
| `pharaoh:release` / `@pharaoh.release` | Release management - changelog from requirements, version tracking, change document summaries |
| `pharaoh:plan` / `@pharaoh.plan` | Structured implementation planning - break requirement changes into tasks, enforce workflow order per `pharaoh.toml` strictness |

## Architecture

### Pure Prompt Architecture

Pharaoh has no runtime binary or Python package. All analysis logic is encoded in skill/agent markdown instructions. The AI executes the logic using its built-in tools (bash, read, grep, glob).

### Three-Tier Data Access

Skills instruct the AI to use the best available data source, in priority order:

```
1. ubc CLI        (best)      Fast, deterministic, JSON output
2. ubCode MCP     (VS Code)   Real-time indexed data, automatic in VS Code
3. Raw files      (fallback)  AI reads RST/MD directly, always works
```

```
+----------------------------------------------+
|  Pharaoh (pure prompts/skills - no runtime)  |
|  Skills instruct the AI to:                  |
|  - Call ubc CLI for data and validation      |
|  - Call ubCode MCP when in VS Code           |
|  - Read RST/MD directly as last resort       |
|  - Apply analysis logic from instructions    |
+------------------+---------------------------+
                   | AI uses tools (bash, read, grep)
        +----------+----------+
        v          v          v
     ubc CLI    ubCode MCP   Raw files
     (best)     (VS Code)    (fallback)
```

**ubc CLI capabilities used by Pharaoh:**

| Pharaoh need | ubc command |
|---|---|
| Build needs index | `ubc build needs --format json` |
| Lint/validate | `ubc check` |
| Schema validation | `ubc schema validate` |
| Diff/impact analysis | `ubc diff` with impact tracing |
| Project config | `ubc config` (resolved JSON) |

### Project Detection

When invoked, Pharaoh detects the project structure automatically. Detection priority:

1. **`ubproject.toml`** - Authoritative source for sphinx-needs config. Contains `[needs]` section with types, links, ID settings. Overrides `conf.py` (matches sphinx-needs 4.1.0+ behavior).
2. **`conf.py`** - Fallback. Read `needs_types`, `needs_extra_links`, `needs_from_toml`, etc.
3. **`pharaoh.toml`** - Pharaoh-specific workflow config (strictness, workflow rules, traceability requirements). Does NOT duplicate sphinx-needs config.
4. **Sphinx-codelinks config** - Detect if codelinks extension is configured.
5. **ubc CLI availability** - Probe with `ubc --version`.
6. **ubCode MCP availability** - Check if MCP server is reachable.
7. **RST/MD source tree** - Scan for documentation files.

Pharaoh auto-detects single-project and multi-project Sphinx setups without configuration.

## Configuration

### `pharaoh.toml`

Optional. When absent, advisory mode applies with sensible defaults.

```toml
[pharaoh]
strictness = "enforcing"  # "advisory" (default) | "enforcing"

[pharaoh.id_scheme]
pattern = "{TYPE}-{MODULE}-{NUMBER}"  # e.g. REQ-BRAKE-001
auto_increment = true

[pharaoh.workflow]
require_change_analysis = true    # must run pharaoh:change before pharaoh:author
require_verification = true       # must run pharaoh:verify before pharaoh:release
require_mece_on_release = false   # optional MECE check before release

[pharaoh.traceability]
required_links = [
    "req -> spec",        # every req must link to at least one spec
    "spec -> impl",       # every spec must link to an impl
    "impl -> test",       # every impl must link to a test
]

[pharaoh.codelinks]
enabled = true  # follow sphinx-codelinks in change analysis
```

### Relationship to `ubproject.toml`

Pharaoh reads need types, link types, and ID settings from `ubproject.toml` (or `conf.py`). It never re-defines these. `pharaoh.toml` only controls Pharaoh's own behavior on top.

## Workflow & Strictness Model

### Advisory Mode (default)

Any skill can be invoked in any order. Pharaoh suggests the recommended workflow but never blocks.

```
User runs pharaoh:author ->
  Pharaoh: "Tip: Consider running pharaoh:change first to
            understand the impact of this modification."
  -> User can proceed anyway.
```

### Enforcing Mode

Skills respect dependency gates defined in `pharaoh.toml`.

```
User runs pharaoh:author ->
  Pharaoh: "Blocked: Change analysis required before authoring.
            Run pharaoh:change for REQ-BRAKE-001 first."
  -> User must complete change analysis to proceed.
```

Default gates when `strictness = "enforcing"`:

- `pharaoh:author` requires `pharaoh:change` (acknowledged)
- `pharaoh:release` requires `pharaoh:verify` (passed)
- `pharaoh:release` requires `pharaoh:mece` (if `require_mece_on_release = true`)

### Session State

Workflow progress is tracked in `.pharaoh/session.json` (ephemeral, gitignored):

```json
{
  "changes": {
    "REQ-BRAKE-001": {
      "change_analysis": "2026-02-11T17:30:00Z",
      "acknowledged": true,
      "authored": false,
      "verified": false
    }
  }
}
```

## Claude Code Integration

### Plugin Structure

```
skills/
  pharaoh-setup/skill.md
  pharaoh-change/skill.md
  pharaoh-trace/skill.md
  pharaoh-mece/skill.md
  pharaoh-author/skill.md
  pharaoh-verify/skill.md
  pharaoh-release/skill.md
  pharaoh-plan/skill.md
agents/
  sphinx-needs-expert/agent.md
```

### Skill Behavior

Each skill contains:
- **When to use** - Trigger conditions (explicit invocation or auto-trigger in enforcing mode)
- **Process** - Step-by-step instructions for the AI
- **Data access** - How to get needs data (ubc -> ubCode MCP -> raw files)
- **Strictness handling** - Advisory vs enforcing behavior
- **Output format** - How to present results

### Auto-Triggering (Enforcing Mode)

In enforcing mode, skills gate each other. For example, `pharaoh:author` checks `.pharaoh/session.json` for whether `pharaoh:change` was completed and refuses to proceed if not.

## GitHub Copilot Integration

### Template Structure

Scaffolded into user projects by `pharaoh:setup`:

```
.github/
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

### Agent Structure

Each agent uses YAML frontmatter with handoff definitions:

```yaml
---
description: Analyze impact of a requirement change.
handoffs:
  - label: Implement Changes
    agent: pharaoh.author
    prompt: Author the changes from the Change Document
  - label: MECE Check
    agent: pharaoh.mece
    prompt: Check affected level for gaps
  - label: Trace Requirement
    agent: pharaoh.trace
    prompt: Trace the changed requirement through all levels
---
```

### Handoff Chains

Guided workflows in VS Code Copilot Chat:

```
@pharaoh.change -> @pharaoh.author -> @pharaoh.verify -> @pharaoh.release
                -> @pharaoh.mece   (optional branch)
                -> @pharaoh.trace  (optional branch)
```

### Prompt Files

Minimal entry points referencing the full agent:

```yaml
---
agent: pharaoh.change
---
```

## ubCode MCP Integration

When ubCode is installed in VS Code, its MCP server provides pre-indexed data:

| Capability | Without ubCode | With ubCode MCP |
|---|---|---|
| Need extraction | AI parses RST/MD | Pre-indexed, instant |
| Link resolution | AI follows links manually | Graph already built |
| Linting | Basic (AI checks patterns) | Full schema validation |
| External needs | AI must find and parse files | Already imported |

Detection: Skills check for MCP availability at invocation time. Graceful degradation to ubc CLI or raw file parsing.

For Copilot users, ubCode MCP is naturally available when the extension is running. For Claude Code users, `pharaoh:setup` guides MCP server configuration.

## Project Structure

```
pharaoh/
  skills/                          # Claude Code plugin
    pharaoh-setup/skill.md
    pharaoh-change/skill.md
    pharaoh-trace/skill.md
    pharaoh-mece/skill.md
    pharaoh-author/skill.md
    pharaoh-verify/skill.md
    pharaoh-release/skill.md
    pharaoh-plan/skill.md
  agents/                          # Claude Code subagent definitions
    sphinx-needs-expert/agent.md
  copilot/                         # Templates scaffolded into user projects
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
  docs/
    plans/                         # Design documents
  pharaoh.toml.example             # Template config
  LICENSE                          # MIT
  README.md
```

## Distribution

### Install Flow

```bash
# Claude Code - just install the plugin
/plugin install pharaoh

# Copilot - run setup to scaffold agents into your project
@pharaoh.setup

# For best experience (recommended, not required):
# 1. Install ubCode VS Code extension
# 2. Install ubc CLI: https://ubcode.useblocks.com/ubc/installation.html
```

### Three Experience Tiers

| Tier | What's installed | Experience |
|---|---|---|
| Basic | Pharaoh plugin/agents only | AI reads files directly - works everywhere, slower on large projects |
| Good | + ubc CLI | Fast deterministic indexing, JSON output, CI/CD compatible |
| Best | + ubc CLI + ubCode extension | Real-time indexing, MCP integration, live validation, full schema checks |

## License

MIT
