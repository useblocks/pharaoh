---
name: pharaoh-write-plan
description: Use when you have an intent (e.g. "reverse-engineer features and reqs from this module") and need a concrete plan.yaml that pharaoh-execute-plan can run. Picks a plan template by intent, fills project-specific values, emits a plan that validates against schema.md. Does NOT execute anything.
---

# pharaoh-write-plan

## When to use

Invoke when you need a plan.yaml and do not already have one. Typical inputs: a short natural-language intent plus a project root and its tailoring files. Typical output: a plan ready to hand to `pharaoh-execute-plan`.

Do NOT use to execute plans (that is `pharaoh-execute-plan`). Do NOT use to review emitted artefacts (that is `pharaoh-quality-gate` or `pharaoh-req-review`). Do NOT use to discover feats or files at scale — discovery is expressed as tasks in the plan itself.

## Why this skill exists

The deleted composition skills (`pharaoh-feats-from-project`, `pharaoh-reqs-from-module`) attempted to orchestrate 6-12 atomic skills via prose. In practice an LLM executing them flattened the process and dropped steps. This skill replaces that pattern by emitting the orchestration as data (plan.yaml), consumed by a generic executor. The domain heuristics those skills carried — split_strategy choice, preseed ordering, quality-gate terminal placement, id-allocate positioning — live here, but they decide plan content, not runtime behaviour.

## Atomicity

- (a) **Indivisible.** One intent → one plan.yaml. Does not execute tasks. Does not write artefacts. Does not mutate `.papyrus/` or `.pharaoh/`. Pure transformation: intent + project state → plan text.
- (b) **Typed I/O.**
  - Input: `{intent: str, project_root: str, tailoring: {ubproject_toml_path?: str, pharaoh_toml_path?: str}, template_name?: str, vars?: dict[str, any]}`.
  - Output: `{plan_yaml: str, template_used: str, warnings: list[str]}`.
- (c) **Execution-based reward.** Fixture in `pharaoh-validation/fixtures/write-plan-smoke/` contains a minimal project (docs/ with 1 RST file, src/ with 3 Python files, `ubproject.toml` declaring `feat` + `comp_req` types). Scorer runs write-plan with intent `"reverse-engineer features and reqs"`. Assertions:
  1. Output is valid YAML parseable by PyYAML.
  2. Output passes `pharaoh-execute-plan/schema.md` static validation (ref parsing, skill existence, cycle detection).
  3. `preseed_papyrus` task appears before any task invoking `pharaoh-req-from-code`.
  4. `pharaoh-quality-gate` is the last task (no downstream deps).
  5. `pharaoh-id-allocate` appears before any `pharaoh-req-from-code`.
  5a. Every plan that schedules `pharaoh-req-from-code` also schedules a `review_comp_reqs` task invoking `pharaoh-req-review` AND a `grounding_check_comp_reqs` task invoking `pharaoh-req-code-grounding-check`, both with `foreach: ${reqs_from_code.emitted_ids}` and `depends_on: [reqs_from_code]` (or equivalent per-file dependency set). Both tasks must appear in `quality_gate.depends_on`. These are **explicit** plan tasks — they are NOT replaced by the skill's in-body `## Last step` self-invocation, which the LLM-executor drops under foreach fan-out.
  6. Every `skill:` references a directory present under `<pharaoh>/skills/` or `<papyrus>/skills/`.
  7. **Dep-probe enrichment with prerequisite insertion.** Fixture's `conf.py` declares only `['sphinx_needs']` (no mermaid extension). Scorer checks: (a) the emitted plan still contains every diagram-emitting task (`pharaoh-feat-component-extract`, `pharaoh-feat-flow-extract`) — tasks are NOT stripped; (b) the plan contains exactly one new task with `skill: pharaoh-sphinx-extension-add` whose `extensions` input lists `sphinxcontrib.mermaid`; (c) every diagram-emitting task's `depends_on` list includes the new prerequisite task id; (d) `warnings` contains at least one human-readable entry naming the missing `sphinxcontrib.mermaid` module and pointing to the prerequisite task.
- (d) **Reusable.** Any intent matching an available template. Adding a new workflow = adding a new template, not modifying this skill.
- (e) **Composable.** Called by humans or by future wrapper skills (`pharaoh-reverse-engineer` could chain write-plan → execute-plan → quality-gate interpretation).

## Input

- `intent`: short phrase, normalised against the template index. Accepted phrasings map to templates:
  - `"reverse-engineer project"`, `"reverse-engineer features and reqs"`, `"rev-eng full project"` → `templates/reverse-engineer-project.yaml.j2`
  - `"reverse-engineer module"`, `"reqs from module"`, `"extract reqs from files"` → `templates/reverse-engineer-module.yaml.j2`
  - When the intent does not match any template, emit a `warnings` entry and return `template_used: none`; do not fabricate a plan.
- `project_root`: absolute path to the target project.
- `tailoring.ubproject_toml_path`: path to `ubproject.toml` for type/prefix lookup. Optional if the project has no tailoring (use baseline defaults from `pharaoh-bootstrap`).
- `tailoring.pharaoh_toml_path`: path to `pharaoh.toml` for source-layout discovery.
- `template_name` (optional): overrides intent-based dispatch; names a template file under `templates/` without the `.yaml.j2` suffix.
- `vars` (optional): dict of additional template variables (e.g. `{"docs_root": "docs/source", "src_root": "src/<project>"}`). Caller-provided values win over skill-inferred ones. Notable optional vars consumed by the reverse-engineer-project template:
  - `target_docs_path`: where emitted artefacts finally live (`toctree-emit` and `quality-gate` read from this path). Default `${workspace}/artefacts`. Set this when the caller wants reverse-engineered spec to land directly under the project's docs tree (e.g. `docs/source/spec/feature/`) without having to override `workspace_dir`.

## Output

```yaml
plan_yaml: |
  name: ...
  version: 1
  ...
template_used: reverse-engineer-project
warnings:
  - "inferred docs_root as docs/source (no explicit value in pharaoh.toml)"
```

`plan_yaml` is the full text to hand to `pharaoh-execute-plan`. `template_used` records provenance for audit. `warnings` surfaces inference decisions (e.g., guessed paths, missing optional inputs).

## Templates

Templates live under `templates/` with filename `<name>.yaml.j2`. Each template:

1. Begins with a YAML front-matter block (actual YAML, not Jinja) declaring `required_vars` and `optional_vars`.
2. Is a Jinja2-style text template with `{{ var }}` placeholders and `{% for %}` loops only.
3. Produces a plan.yaml body below the front-matter.

Supported Jinja constructs:
- `{{ var }}` simple substitution.
- `{% for item in list %}` ... `{% endfor %}` iteration (rare — most iteration should be expressed as `foreach:` in the emitted plan, not unrolled at write time).
- `{% if cond %}` ... `{% endif %}` for optional tasks (e.g., include diagram tasks only when tailoring declares a diagram renderer).

No arbitrary Python expressions, no filters beyond `| default(...)`. If a template needs richer logic, split it into two templates.

## Process

### Step 1: Resolve template

1. If `template_name` is provided, use it directly.
2. Else normalise `intent` (lowercase, strip punctuation, collapse whitespace) and look up in the intent→template map above.
3. If no match, return `template_used: "none"`, `plan_yaml: ""`, and add a warning `"no template matched intent '<intent>'; valid intents: <list>"`.

### Step 2: Gather variables

Combine variables in this precedence (higher wins):

1. Defaults baked into the template's front-matter.
2. Inferred from `tailoring.pharaoh_toml_path` (if present):
   - `src_root` from `[pharaoh.codelinks].src_dir` or `[source_discover].src_dir`.
   - `docs_root` from sphinx conf lookup (`docs/source/conf.py`, `docs/conf.py`, `conf.py`).
3. Inferred from `tailoring.ubproject_toml_path` (if present):
   - `feat_directive`, `feat_prefix`, `comp_req_directive`, `comp_req_prefix` from the `[[needs.types]]` array.
4. Inferred from `docs_root` (after it resolves):
   - `docs`: list of relative paths (relative to `project_root`) produced by globbing `<project_root>/<docs_root>/**/*.rst` and `**/*.md`, sorted alphabetically. Excludes `index.rst` / `index.md` (toctree parent is not a feature doc). Empty list if the directory is absent. This satisfies the `doc_files` shape that `pharaoh-feat-draft-from-docs` expects; templates iterate `docs` at write time rather than passing `docs_root` through to the skill.
5. Caller-supplied `vars`.

Any required_var missing after this merge → add a warning, leave placeholder intact in the emitted plan (caller must fill before executing), do not fabricate a value.

### Step 3: Render template

Substitute `{{ var }}` tokens. Evaluate `{% if %}`/`{% for %}` blocks. Emit the rendered body (the part below the template's front-matter) as the plan.

### Step 3.5: Probe required sphinx extensions and insert prerequisite tasks

Before validating the rendered plan, probe `conf.py` to verify that the renderers required by diagram-emitting tasks are loaded. When a required extension is missing, this step enriches the plan with a `pharaoh-sphinx-extension-add` prerequisite task — it does NOT strip the diagram task. The plan body gains a task; no task is removed. This preserves the B1 invariant ("enrich, never strip") while also giving the executor an actionable step instead of a human handoff.

**Probe procedure:**

1. Resolve `conf.py` using the same lookup chain as Step 2 (`<docs_root>/conf.py` → `docs/source/conf.py` → `docs/conf.py` → `<project_root>/conf.py`). If absent, emit a warning and skip this step.
2. Parse `extensions = [...]` from the resolved `conf.py`. Flatten to a set of imported extension module paths.
3. Scan the rendered plan for diagram-emitting skills. Each has a fixed renderer surface:

   | Skill                          | Default renderer | Required extension module | pypi package           |
   | ------------------------------ | ---------------- | ------------------------- | ---------------------- |
   | `pharaoh-feat-component-extract` | mermaid (or uml) | `sphinxcontrib.mermaid`   | `sphinxcontrib-mermaid` |
   | `pharaoh-feat-flow-extract`    | mermaid (or uml) | `sphinxcontrib.mermaid`   | `sphinxcontrib-mermaid` |
   | `pharaoh-diagram-lint`         | both             | `sphinxcontrib.mermaid` AND/OR `sphinxcontrib.plantuml` | same, by renderer |

   If a task's inputs include `renderer_override: "plantuml"`, the required extension becomes `sphinxcontrib.plantuml` (pypi: `sphinxcontrib-plantuml`). If the template does not set `renderer_override`, fall back to `pharaoh.toml [pharaoh.diagrams].renderer` when readable, else `mermaid`.
4. Collect the set of missing extensions (present in the "required" column for some diagram task but absent from `conf.py` extensions list). If empty, skip to Step 4.
5. **Insert a prerequisite task into the plan body.** For all missing extensions (batched into one task invocation — `pharaoh-sphinx-extension-add` accepts a list), append a task with deterministic id `sphinx_extension_add`:

   ```yaml
     - id: sphinx_extension_add
       skill: pharaoh-sphinx-extension-add
       inputs:
         conf_py: <resolved conf_py path>
         extensions: [<list of missing extension modules>]
         install_if_missing: true
         on_package_manager_missing: warn
         reporter_id: "write-plan:sphinx-extension-add"
       depends_on: []
   ```

   Place this task before any diagram-emitting task in the plan's task list.

6. **Rewrite `depends_on` of every diagram-emitting task** so it includes `sphinx_extension_add` as a dependency. This preserves the diagram task's existing dependencies and adds `sphinx_extension_add` to the list.
7. For each missing extension, ALSO append a warning entry (human-readable handoff in case someone inspects the plan without running it):

   ```
   diagram task '<task_id>' emits <renderer> blocks but conf.py does not load '<ext_module>'. Plan includes prerequisite task 'sphinx_extension_add' that will install '<pypi_pkg>' and update conf.py before diagram tasks run. Requires a resolvable package manager in the execution environment.
   ```

**Design notes:**

- No task is ever REMOVED. This step is plan-body enrichment: one new task + `depends_on` additions, no deletions. This preserves the B1 invariant.
- If `pharaoh-sphinx-extension-add` is itself missing from the skills tree (e.g. an old installation), log a warning and fall back to warn-only mode (do not insert the task).
- If probing fails (e.g. `conf.py` unparseable), emit one warning naming the parse failure and proceed without insertion. Do not abort.
- The prerequisite task is always batched (one task per plan, not one per missing extension), keeping the plan's task count bounded.

### Step 4: Validate against schema

Invoke the static-validation portion of `pharaoh-execute-plan/schema.md` mentally:

1. Parse rendered text as YAML.
2. Confirm required top-level fields present.
3. Confirm every `skill:` references an existing skill directory under `<pharaoh>/skills/` or `<papyrus>/skills/`.
4. **Terminal quality-gate invariant (unconditional).** Compute the set of tasks with no downstream dependents (no other task lists them in `depends_on`). That set must be non-empty and every task in it must have `skill: pharaoh-quality-gate`. Rationale: when quality gate is absent or non-terminal, executors skip it under cost pressure and ID/body/satisfies checks go unenforced. Every reverse-engineering template ships with a terminal `quality_gate`; this check prevents custom templates from drifting away from that invariant.
5. Confirm the ordering invariants specific to reverse-engineering intents:
   - preseed_papyrus before any req-emission task.
   - id-allocate before any req-emission task referring to allocated IDs.
6. On any violation: abort, return empty `plan_yaml`, add the violation to `warnings`.

### Step 5: Return

Return `{plan_yaml, template_used, warnings}`.

## Heuristics carried from deleted composition skills

These are the domain bits that used to live in prose inside `pharaoh-feats-from-project` and `pharaoh-reqs-from-module`. They now live in template content and in the variable-inference logic above. Enumerated for auditability:

1. **split_strategy per file.** Templates emit `split_strategy: ${heuristics.split_strategy(${item.file})}` on every `pharaoh-req-from-code` task, so the executor's helper evaluates it at dispatch time (no LOC counting at write time). The helper's rule: LOC ≤ 500 → single; 500 < LOC ≤ 2000 and section markers → sections; else → top_level_symbols.
2. **preseed Papyrus before reqs (unconditional).** Templates always emit a `preseed_papyrus` task (using `pharaoh-decision-record` or a dedicated future skill) with `depends_on: []` and a `depends_on: [preseed_papyrus]` on every req-emission task. Preseed registers canonical feat names in Papyrus, not file-level associations. Every feat-emission agent queries the same canonical-name namespace regardless of which files it touches, so preseed is always useful even when concurrent agents work on disjoint file sets.
3. **id-allocate before reqs.** Templates emit `pharaoh-id-allocate` after file discovery (feat-file-map or module-file-enum), producing `allowed_ids` that req-emission tasks consume via ref.
4. **Multi-parent reqs.** When a file maps to multiple feats (feat-file-map's `shared_with`), the template emits a single req-from-code task with `parent_feat_ids: ${item.parents}` (a list), not one task per parent.
5. **Quality-gate terminal.** Templates always include `pharaoh-quality-gate` as the last task, taking `artefacts_dir: ${workspace}/artefacts`.
6. **file-per-feature layout.** Templates produce one artefact per feat via the `pharaoh-toctree-emit` task's inputs, matching the layout committed in `pharaoh-feats-from-project` Task 6 of the prior plan.
7. **Diagram dep probe (enrich, never strip).** Write-plan reads `conf.py` extensions and, when a plan includes diagram-emitting tasks whose renderer extension is absent, inserts a `pharaoh-sphinx-extension-add` prerequisite task into the plan body (see Step 3.5). The diagram tasks remain in place and gain the new task as a dependency. A warning is still emitted alongside for human inspection. The contract is: write-plan informs AND enriches, never drops; the diagram deliverable is both visible and actually runnable end-to-end.

## Review invariant (self-review)

Every emission task in a plan is followed by its matching review task in the DAG. Mapping in [`shared/self-review-map.yaml`](../shared/self-review-map.yaml). The template handles this automatically — user does not need to request review tasks.

The terminal `pharaoh-quality-gate` task lists all review tasks in its `depends_on` and configures `gate_spec.invariants.self_review_coverage: true` so that missing reviews fail the gate. See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md).

The two companion invariants are also unconditional:

- `papyrus_non_empty` — enabled when the plan ran `preseed_papyrus`. Catches the LLM-executor-skipped-Papyrus-writes failure class.
- `dispatch_signal_matches_plan` — always enabled. Catches the LLM-executor-collapsed-parallel-to-inline failure class.

Both delegate to atomic check skills; the gate itself stays a pure aggregator.

## Failure modes

| Condition                                   | Response                                                 |
| ------------------------------------------- | -------------------------------------------------------- |
| Intent matches no template                  | Return empty plan; warning enumerating valid intents.    |
| Required var missing after merge            | Leave placeholder; warning; caller must fill.            |
| Template references a non-existent skill    | Abort with warning; return empty plan.                   |
| Rendered YAML fails schema validation       | Abort with warning; return empty plan.                   |
| tailoring paths unreadable                  | Proceed with defaults; warning per missing file.         |

## Framework for remaining *-diagram-draft skills

`pharaoh-use-case-diagram-draft` is the first concrete implementation of the `*-diagram-draft` family. It demonstrates the pattern every future draft skill must follow:

1. Frontmatter `name`, `description` starting "Use when", `chains_from` / `chains_to: [pharaoh-diagram-review]`.
2. Atomicity section showing (a)-(e).
3. Input section naming `renderer` + `tailoring_path` + per-diagram-type scope inputs.
4. Output section with `{diagram_block, element_count, renderer}` shape.
5. Two "How to emit" subsections — one per renderer (mermaid, plantuml).
6. "Safe labels" subsection linking to `shared/diagram-safe-labels.md`.
7. "Relationship semantics" subsection linking to `shared/uml-relationship-semantics.md` if the diagram kind uses structural relationships.
8. "Last step" subsection invoking `pharaoh-diagram-review` per the self-review invariant.

Agent cross-ref in `.github/agents/pharaoh.<name>.agent.md` required for CI.

Diagram-draft skill catalogue (one per UML / SysML view the emitter supports):

- `pharaoh-use-case-diagram-draft` — **shipped**, runnable end-to-end.
- `pharaoh-sequence-diagram-draft` — design-only scaffold.
- `pharaoh-component-diagram-draft` — design-only scaffold.
- `pharaoh-class-diagram-draft` — design-only scaffold.
- `pharaoh-state-diagram-draft` — design-only scaffold.
- `pharaoh-activity-diagram-draft` — design-only scaffold.
- `pharaoh-block-diagram-draft` — design-only scaffold.
- `pharaoh-deployment-diagram-draft` — design-only scaffold.
- `pharaoh-fault-tree-diagram-draft` — design-only scaffold.

Shipped skills follow the canonical skeleton (frontmatter → input → output → process → review invocation) and have a matching agent under `.github/agents/`. Design-only scaffolds declare the same frontmatter + agent pair for plan-authoring and CI validation, but their process body is a `DESIGN ONLY` placeholder with a sentinel FAIL — implementation lands per-kind when a flow actually needs that view. Use-case extraction is handled end-to-end by `pharaoh-use-case-diagram-draft`; component and flow views are currently extracted directly from code by `pharaoh-feat-component-extract` and `pharaoh-feat-flow-extract` (not by the draft skills).

## Non-goals

- No skill discovery beyond checking directory existence. If a template references `pharaoh-foo` and that directory exists, write-plan trusts its contents are valid.
- No file enumeration. File lists come from tasks in the plan at execute time (e.g., `pharaoh-feat-file-map`).
- No artefact emission. This skill emits a plan, not artefacts.
- No branching at runtime. If an intent has two variants ("with diagrams" vs "without"), add two templates.
