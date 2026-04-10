# Pharaoh - AI Assistant for sphinx-needs Projects

Pharaoh is a skill-based AI assistant framework for sphinx-needs projects. It helps teams author, analyze, trace, and validate requirements using AI. Pharaoh is designed for safety-critical workflows (A-SPICE, ISO 26262) but works with any sphinx-needs project.

## Core Principles

- **Static-first data access**: Parse RST/MD source files directly; use ubc CLI or ubCode MCP when available for speed and accuracy.
- **Advisory by default, strict when configured**: `pharaoh.toml` controls enforcement level; no config = advisory mode with guardrails.
- **Safety-critical ready**: Designed for A-SPICE/ISO 26262 workflows but usable by any sphinx-needs team.

## Available Agents

| Agent | Purpose |
|-------|---------|
| `@pharaoh.setup` | Scaffold Pharaoh into a project -- detect structure, generate `pharaoh.toml` |
| `@pharaoh.change` | Analyze impact of a change -- trace through needs links and codelinks, produce a Change Document |
| `@pharaoh.trace` | Navigate traceability in any direction -- show everything linked to a need across all levels |
| `@pharaoh.mece` | Gap and redundancy analysis -- find orphans, missing links, MECE violations |
| `@pharaoh.author` | AI-assisted requirement authoring -- create/modify needs with proper IDs, types, and links |
| `@pharaoh.verify` | Validate implementations against requirements -- content-level satisfaction checks |
| `@pharaoh.release` | Release management -- changelog from requirements, traceability coverage metrics |
| `@pharaoh.plan` | Structured implementation planning -- break changes into tasks with workflow enforcement |
| `@pharaoh.spec` | Generate spec from requirements -- read needs hierarchy, record decisions, produce spec with plan table |
| `@pharaoh.decide` | Record design decisions -- create `decision` needs with alternatives, rationale, and traceability links |

## Recommended Workflow

```
@pharaoh.spec   -> @pharaoh.decide (for gaps)
                -> produces spec doc with plan table
                     |
@pharaoh.plan   -> @pharaoh.change -> @pharaoh.author -> @pharaoh.verify -> @pharaoh.release
                                   -> @pharaoh.mece   (optional, for gap analysis)
                                   -> @pharaoh.trace  (optional, for exploration)
```

## Data Access Tiers

Agents automatically use the best available data source:

1. **ubc CLI** (best): Fast, deterministic JSON output. Install from https://ubcode.useblocks.com/ubc/installation.html
2. **ubCode MCP** (VS Code): Real-time indexed data via the ubCode extension. Automatic when the extension is running.
3. **Raw file parsing** (fallback): AI reads RST/MD files directly. Always works, slower on large projects.

## Configuration

### Project Configuration

Agents read need types, link types, and ID settings from:
- `ubproject.toml` (preferred) -- the `[needs]` section
- `conf.py` (fallback) -- `needs_types`, `needs_extra_links`, etc.

### Pharaoh Configuration (`pharaoh.toml`)

Optional. Controls Pharaoh's workflow behavior, not sphinx-needs configuration.

```toml
[pharaoh]
strictness = "advisory"  # or "enforcing"

[pharaoh.workflow]
require_change_analysis = true
require_verification = true
require_mece_on_release = false

[pharaoh.traceability]
required_links = ["req -> spec", "spec -> impl", "impl -> test"]

[pharaoh.codelinks]
enabled = true
```

### Advisory vs Enforcing Mode

- **Advisory** (default): Agents suggest the recommended workflow but never block. Tips are shown for skipped steps.
- **Enforcing**: Agents check prerequisites and block if not met (e.g., `@pharaoh.author` requires `@pharaoh.change` first).

## sphinx-codelinks Integration

When a project uses sphinx-codelinks, Pharaoh follows codelink references in change analysis and traceability. A change to a requirement surfaces affected code files, not just other requirements.

## Session State

Workflow progress is tracked in `.pharaoh/session.json` (ephemeral, gitignored). This enables enforcing mode gates and tracks which needs have been analyzed, authored, and verified.
