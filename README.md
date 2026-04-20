# Pharaoh

AI assistant framework for [sphinx-needs](https://sphinx-needs.readthedocs.io/) projects. Pharaoh combines structured development workflows with requirements engineering intelligence to help teams author, analyze, trace, and validate requirements using AI.

Pharaoh has no runtime binary or Python package. All analysis logic is encoded in skill/agent markdown instructions. The AI is the runtime.

## Quick Start

### Claude Code

```bash
# Install the plugin
/plugin install pharaoh

# Run setup to detect your project and generate pharaoh.toml
/pharaoh:setup

# Analyze the impact of a change
/pharaoh:change REQ_001

# Check for traceability gaps
/pharaoh:mece
```

### GitHub Copilot

```
# Run setup to scaffold agents into your project
@pharaoh.setup

# Analyze the impact of a change
@pharaoh.change REQ_001

# Check for traceability gaps
@pharaoh.mece
```

## Skills / Agents

**Core workflow skills:**

| Skill (Claude Code) | Purpose |
|---------------------|---------|
| `pharaoh:setup` | Scaffold Pharaoh into a project -- detect structure, generate `pharaoh.toml`, install Copilot agents |
| `pharaoh:change` | Analyze impact of a change -- trace through needs links and codelinks, produce a Change Document |
| `pharaoh:trace` | Navigate traceability in any direction -- show everything linked to a need across all levels |
| `pharaoh:mece` | Gap and redundancy analysis -- find orphans, missing links, MECE violations |
| `pharaoh:release` | Release management -- changelog from requirements, traceability coverage metrics |
| `pharaoh:plan` | Structured implementation planning -- break changes into tasks with workflow enforcement |
| `pharaoh:spec` | Generate spec from requirements -- read needs hierarchy, record decisions, produce spec with plan table |
| `pharaoh:decide` | Record design decisions -- create `decision` needs with alternatives, rationale, and traceability links |

**Atomic authoring and review chain:**

| Skill (Claude Code) | Purpose |
|---------------------|---------|
| `pharaoh:req-draft` | Draft a single requirement directive with ID, status, and shall-clause body |
| `pharaoh:req-review` | Audit a requirement against ISO 26262-8 §6 axes -- per-axis findings with action items |
| `pharaoh:req-regenerate` | Regenerate a requirement to address findings from req-review |
| `pharaoh:arch-draft` | Draft a single architecture element directive from a parent requirement |
| `pharaoh:arch-review` | Audit an architecture element against ISO 26262-8 §6 axes |
| `pharaoh:vplan-draft` | Draft a test-case directive linking to a parent requirement |
| `pharaoh:vplan-review` | Audit a test case against ISO 26262-8 §6 axes plus vplan-specific axes |
| `pharaoh:fmea` | Derive a failure-mode entry (FMEA/DFA row) from a requirement or architecture element |
| `pharaoh:flow` | Orchestrate the full V-model chain (req → arch → vplan → fmea) for one feature context |

**Analysis and audit skills:**

| Skill (Claude Code) | Purpose |
|---------------------|---------|
| `pharaoh:coverage-gap` | Detect one gap category (orphan / unverified / duplicate / ...) in a corpus |
| `pharaoh:process-audit` | Full-corpus audit across all gap categories with prioritized findings |
| `pharaoh:lifecycle-check` | Verify artefact lifecycle state and legality of a state transition |
| `pharaoh:standard-conformance` | Evaluate an artefact against a regulatory standard (ISO 26262-8, ASPICE 4.0, ISO/SAE 21434) |

**Tailoring skills:**

| Skill (Claude Code) | Purpose |
|---------------------|---------|
| `pharaoh:tailor-detect` | Inspect a project and emit detected conventions for tailoring |
| `pharaoh:tailor-fill` | Author `.pharaoh/project/` tailoring files from detected conventions |
| `pharaoh:tailor-review` | Audit tailoring files against schemas and cross-file consistency |

## Workflow

```
pharaoh:spec   -> pharaoh:decide (for gaps)
               -> produces spec doc with plan table
                    |
pharaoh:plan   -> pharaoh:change -> pharaoh:req-draft  -> pharaoh:req-review  -> pharaoh:release
                                 -> pharaoh:arch-draft -> pharaoh:arch-review
                                 -> pharaoh:vplan-draft -> pharaoh:vplan-review
                                 -> pharaoh:fmea
                                 -> pharaoh:mece   (optional, for gap analysis)
                                 -> pharaoh:trace  (optional, for exploration)
```

## Experience Tiers

Pharaoh works with just the AI reading files. Install additional tools for a better experience.

| Tier | What's installed | Experience |
|------|-----------------|------------|
| Basic | Pharaoh only | AI reads RST/MD files directly. Works everywhere, slower on large projects. |
| Good | + [ubc CLI](https://ubcode.useblocks.com/ubc/installation.html) | Fast deterministic indexing, JSON output, CI/CD compatible. |
| Best | + ubc CLI + [ubCode extension](https://ubcode.useblocks.com/) | Real-time indexing, MCP integration, live validation, full schema checks. |

## Configuration

### `pharaoh.toml`

Optional. Controls Pharaoh's workflow behavior. Without this file, advisory mode applies with sensible defaults.

```toml
[pharaoh]
strictness = "advisory"  # "advisory" (default) | "enforcing"

[pharaoh.id_scheme]
pattern = "{TYPE}-{MODULE}-{NUMBER}"
auto_increment = true

[pharaoh.workflow]
require_change_analysis = true
require_verification = true
require_mece_on_release = false

[pharaoh.traceability]
required_links = [
    "req -> spec",
    "spec -> impl",
    "impl -> test",
]

[pharaoh.codelinks]
enabled = true
```

See [`pharaoh.toml.example`](pharaoh.toml.example) for a fully commented template.

### Advisory vs Enforcing Mode

- **Advisory** (default): Skills suggest the recommended workflow but never block. Tips are shown for skipped steps.
- **Enforcing**: Skills check prerequisites and block if not met. For example, authoring skills (e.g. `pharaoh:req-draft`) require `pharaoh:change` to be run and acknowledged first.

### Project Configuration

Pharaoh reads need types, link types, and ID settings from your existing sphinx-needs configuration:
- `ubproject.toml` (preferred) -- the `[needs]` section
- `conf.py` (fallback) -- `needs_types`, `needs_extra_links`, etc.

Pharaoh never re-defines these settings. `pharaoh.toml` only controls Pharaoh's own behavior on top.

## sphinx-codelinks Support

When a project uses [sphinx-codelinks](https://sphinx-codelinks.useblocks.com/), Pharaoh follows codelink references in change analysis and traceability. A change to a requirement surfaces affected code files, not just other requirements.

## License

MIT
