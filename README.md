# Pharaoh

AI assistant framework for [sphinx-needs](https://sphinx-needs.readthedocs.io/) projects. Pharaoh combines structured development workflows with requirements engineering intelligence to help teams author, analyze, trace, and validate requirements using AI.

Pharaoh has no runtime binary or Python package. All analysis logic is encoded in skill/agent markdown instructions. The AI is the runtime.

## Quick Start

### Claude Code

```bash
# Add the marketplace, then install the plugin
/plugin marketplace add useblocks/pharaoh
/plugin install pharaoh@pharaoh-dev

# Reload to activate
/reload-plugins
```

```bash
# Run setup to detect your project and generate pharaoh.toml
/pharaoh:setup

# Analyze the impact of a change
/pharaoh:change REQ_001

# Check for traceability gaps
/pharaoh:mece
```

To pin to a released version, append a git ref to the marketplace add:

```bash
/plugin marketplace add useblocks/pharaoh#v1.0.0
```

### GitHub Copilot

```bash
# Add the marketplace, then install the plugin
copilot plugin marketplace add useblocks/pharaoh
copilot plugin install pharaoh@pharaoh-dev
```

```
# Run setup to scaffold agents into your project
@pharaoh.setup

# Analyze the impact of a change
@pharaoh.change REQ_001

# Check for traceability gaps
@pharaoh.mece
```

## Skills / Agents

71 atomic skills, organised by purpose. Names below are Claude Code form
(`pharaoh:<name>`); GitHub Copilot form is `pharaoh.<name>`.

**Core workflow:**

| Skill | Purpose |
|-------|---------|
| `pharaoh:setup` | Set up Pharaoh in a sphinx-needs project -- detect structure, scaffold Copilot agents |
| `pharaoh:change` | Analyse the impact of a requirement change, including traceability to code via codelinks |
| `pharaoh:trace` | Navigate traceability links across requirements, specs, implementations, tests, and code |
| `pharaoh:mece` | Gap and redundancy analysis -- orphans, missing links, MECE violations |
| `pharaoh:plan` | Break requirement changes into structured implementation tasks with workflow enforcement |
| `pharaoh:spec` | Generate a Superpowers-compatible spec and plan document from sphinx-needs requirements |
| `pharaoh:decide` | Record a design decision as a traceable `decision` need with alternatives and rationale |
| `pharaoh:release` | Generate changelog from requirements, summarise requirement changes for version management |

**Plan-driven orchestration:**

| Skill | Purpose |
|-------|---------|
| `pharaoh:write-plan` | Pick a plan template by intent and emit a `plan.yaml` that validates against schema.md |
| `pharaoh:execute-plan` | Run a `plan.yaml` as a DAG -- dispatch tasks (inline or subagent), thread outputs, validate, persist |
| `pharaoh:audit-fanout` | Run a full project audit in parallel by dispatching 5 atomic audit skills with deduplicated findings |
| `pharaoh:context-gather` | Retrieve rationale memories from a Papyrus workspace before invoking a draft or review skill |
| `pharaoh:finding-record` | Record an audit finding in the shared Papyrus workspace with deterministic deduplication |
| `pharaoh:decision-record` | Record a canonical decision/fact/preference in Papyrus with dedup on (type, canonical_name) |
| `pharaoh:quality-gate` | Final validation step over an aggregated review/MECE/coverage summary -- pass/fail with breaches |
| `pharaoh:gate-advisor` | Read `pharaoh.toml` and report the recommended next gate to switch on, per the phased ladder |
| `pharaoh:dispatch-signal-check` | Verify a plan's declared `execution_mode` matches observed subagent artefacts in `runs/` |
| `pharaoh:reproducibility-check` | Diff two output directories from running the same plan twice to confirm reproducibility |
| `pharaoh:self-review-coverage-check` | Verify every artefact emitted during a plan run received a matching review |
| `pharaoh:output-validate` | Validate a subagent's output against a documented schema (RST/YAML/JSON) before writing to disk |
| `pharaoh:id-allocate` | Pre-allocate globally-unique sphinx-needs IDs before dispatching a fan-out of emission subagents |

**Atomic authoring and review chain:**

| Skill | Purpose |
|-------|---------|
| `pharaoh:req-draft` | Draft a single requirement directive with ID, status, and shall-clause body |
| `pharaoh:req-review` | Audit a requirement against the 11 ISO 26262-8 §6 axes -- per-axis findings with action items |
| `pharaoh:req-regenerate` | Regenerate a requirement to address findings from req-review |
| `pharaoh:req-from-code` | Read a source file and emit one or more requirement RST directives describing its observable behavior |
| `pharaoh:req-codelink-annotate` | Insert a codelink or backref one-line comment into source code, carrying the trace |
| `pharaoh:req-code-grounding-check` | Verify a drafted requirement against the source file it cites via `:source_doc:` |
| `pharaoh:arch-draft` | Draft a single architecture element directive from a parent requirement |
| `pharaoh:arch-review` | Audit an architecture element against ISO 26262-8 §6 axes plus traceability to its requirement |
| `pharaoh:vplan-draft` | Draft a test-case directive linking to a parent requirement |
| `pharaoh:vplan-review` | Audit a test case against ISO 26262-8 §6 axes plus vplan-specific axes |
| `pharaoh:fmea` | Derive a failure-mode entry (FMEA/DFA row) -- cause, effect, severity, occurrence, detection, RPN |
| `pharaoh:fmea-review` | Audit an FMEA entry against the generic FMEA review axes plus per-project addenda |
| `pharaoh:decision-review` | Audit a recorded decision against context/alternatives/consequences and traceability axes |
| `pharaoh:flow` | Orchestrate the full V-model chain (req → arch → vplan → fmea) with a review pass after each step |

**Diagrams:**

| Skill | Purpose |
|-------|---------|
| `pharaoh:use-case-diagram-draft` | Draft a use-case diagram for a single feat -- actors, use cases, system boundary |
| `pharaoh:component-diagram-draft` | Draft a component-relationship diagram for a bounded scope -- one feature/module/view |
| `pharaoh:sequence-diagram-draft` | Draft a sequence diagram showing ordered interactions between participants |
| `pharaoh:class-diagram-draft` | Draft a class diagram showing types/entities with fields, methods, relationships |
| `pharaoh:state-diagram-draft` | Draft a state-machine diagram showing lifecycle/behavioral states with transitions |
| `pharaoh:activity-diagram-draft` | Draft an activity diagram showing control flow for one procedure or algorithm |
| `pharaoh:block-diagram-draft` | Draft a SysML BDD or IBD showing block structure or part interconnections |
| `pharaoh:deployment-diagram-draft` | Draft a deployment diagram showing physical nodes, deployed artefacts, and channels |
| `pharaoh:fault-tree-diagram-draft` | Draft a fault tree (FTA) decomposing a top hazard event through AND/OR gates |
| `pharaoh:diagram-review` | Audit a diagram block (Mermaid or PlantUML) against trace/parser/required-elements axes |
| `pharaoh:diagram-lint` | Validate Mermaid/PlantUML blocks across a directory by piping each to the renderer parser |

**Feature reverse-engineering:**

| Skill | Purpose |
|-------|---------|
| `pharaoh:feat-draft-from-docs` | Read existing prose docs and emit feature-level RST directives for documented capabilities |
| `pharaoh:feat-file-map` | Map one feature to the source files that implement it -- `{feat_id: {files, rationale}}` |
| `pharaoh:feat-component-extract` | Walk import edges between a feat's source files and emit a component composition diagram |
| `pharaoh:feat-flow-extract` | Walk the call graph from a feat's entry point and emit a sequence diagram of its control flow |
| `pharaoh:feat-balance` | Check feature granularity -- under/over-decomposition, fused sub-features, redundant pairs |
| `pharaoh:feat-review` | Audit a feature-level need against generic feat axes plus per-project addenda |

**Analysis and audit:**

| Skill | Purpose |
|-------|---------|
| `pharaoh:coverage-gap` | Detect one gap category (orphan / unverified / duplicate / contradictory / lifecycle / ...) |
| `pharaoh:process-audit` | Full-corpus audit -- orchestrates `coverage-gap` across all gap categories plus consistency checks |
| `pharaoh:standard-conformance` | Evaluate an artefact against ISO 26262-8 §6, ASPICE 4.0, or ISO/SAE 21434 |
| `pharaoh:lifecycle-check` | Verify an artefact's lifecycle state and legality of a state transition |
| `pharaoh:status-lifecycle-check` | Release-gate check -- confirm zero needs remain in `draft` status across the corpus |
| `pharaoh:link-completeness-check` | Verify outgoing-link coverage across a needs.json graph for every declared link type |
| `pharaoh:id-convention-check` | Verify every need id matches the regex declared for its type in `id-conventions.yaml` |
| `pharaoh:review-completeness` | Flag needs missing required `:reviewer:` or `:approved_by:` fields per the artefact catalog |
| `pharaoh:api-coverage-check` | Verify a source file is covered by the need catalogue (CREQ source_doc + exception class names) |
| `pharaoh:papyrus-non-empty-check` | Verify a Papyrus workspace received writes during a plan run -- counts directives across `.papyrus/memory/` |

**Tailoring:**

| Skill | Purpose |
|-------|---------|
| `pharaoh:tailor-detect` | Inspect a project and emit a structured report of detected conventions |
| `pharaoh:tailor-fill` | Author `.pharaoh/project/` tailoring files from detected-conventions JSON |
| `pharaoh:tailor-bootstrap` | Generate minimal tailoring files from declared types post-bootstrap, pre any needs authoring |
| `pharaoh:tailor-code-grounding-filters` | Author a project's `code-grounding-filters.yaml` from observed stack conventions |
| `pharaoh:tailor-review` | Audit tailoring files against schemas plus cross-file consistency |

**Setup utilities:**

| Skill | Purpose |
|-------|---------|
| `pharaoh:bootstrap` | Add sphinx-needs extension and declare need types so `sphinx-build` produces a valid needs.json |
| `pharaoh:sphinx-extension-add` | Idempotently add sphinx extensions to `conf.py` and install corresponding pypi packages |
| `pharaoh:toctree-emit` | Emit or regenerate an `index.rst` toctree over a set of generated RST files, preventing orphan warnings |
| `pharaoh:prose-migrate` | Sentence-by-sentence migration proposal when generated feat RST would collide with prose docs |

## Workflow

Authoring orchestration is plan-driven: `pharaoh:write-plan` emits a `plan.yaml`,
`pharaoh:execute-plan` runs it as a DAG dispatching atomic skills.

```
pharaoh:spec       -> pharaoh:decide (for gaps)
                   -> produces spec doc with plan table

pharaoh:write-plan -> emits .pharaoh/plans/<intent>.yaml
                   -> pharaoh:execute-plan
                          |-- pharaoh:req-draft   -> pharaoh:req-review
                          |-- pharaoh:arch-draft  -> pharaoh:arch-review
                          |-- pharaoh:vplan-draft -> pharaoh:vplan-review
                          |-- pharaoh:fmea        -> pharaoh:fmea-review
                          |-- pharaoh:*-diagram-draft -> pharaoh:diagram-review
                          |-- pharaoh:quality-gate (terminal)

pharaoh:flow       -> shortcut for the V-model chain on one feature context
pharaoh:change     -> impact analysis, feeds plan inputs
pharaoh:mece       -> gap analysis (standalone or as a plan task)
pharaoh:trace      -> traceability exploration
pharaoh:release    -> reads completed artefacts, emits changelog
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

When a project uses [sphinx-codelinks](https://codelinks.useblocks.com/), Pharaoh follows codelink references in change analysis and traceability. A change to a requirement surfaces affected code files, not just other requirements.

## License

MIT
