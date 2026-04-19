---
name: pharaoh-context-gather
description: Atomic — retrieve rationale memories relevant to an authoring context from a Papyrus workspace. Returns a structured list of memories (memory_id, text, relevance_score). Does NOT draft, review, or modify artefacts.
---

# pharaoh-context-gather

## When to use

Invoke BEFORE any draft skill (`pharaoh-req-draft`, `pharaoh-arch-draft`, `pharaoh-vplan-draft`, `pharaoh-fmea`) when the project directory contains a `.papyrus/` workspace. The output is a compact bundle of rationale decisions (past design choices, constraints, conventions) that the downstream draft skill must respect.

Do NOT invoke for project directories without `.papyrus/` — this skill is a no-op in that case. Do NOT invoke after drafting; the purpose is precondition-retrieval only.

## Atomicity

- (a) Indivisible — single retrieval action. Does not draft, review, route, or modify artefacts.
- (b) Input: `{feature_context: str, artefact_type: "req"|"arch"|"vplan"|"fmea", project_dir: path}`. Output: JSON list of `{memory_id, text, relevance_score}`.
- (c) Reward: recall@k + MRR vs ground-truth relevant IDs. Deterministic, IR-style.
- (d) Reusable: consumed by all 4 draft skills; standalone "show rationale for this change" flow.
- (e) Composable: read-only upstream; never mutates artefact files.

## Process

### Step 1: Detect workspace

Check that `<project_dir>/.papyrus/` exists as a directory AND contains
`memory/` OR `.papyrus/index.json` (Papyrus's internal index). If no
`.papyrus/` at all, return `[]` (no memories, no error) and stop.
If the `project_dir` passed in already points at a path whose basename
is `.papyrus`, treat that as the workspace directly.

### Step 2: Run semantic recall

Pass `feature_context` verbatim as the query; Papyrus does cosine similarity
over pre-embedded memory vectors. Requires the workspace to have been indexed
via `papyrus rebuild-index` (with the `papyrus[semantic]` extra installed).

```bash
papyrus --workspace <project_dir>/.papyrus recall --semantic \
  -q "<feature_context>" --top-k 10 --show-scores --format full
```

The output is plaintext with one memory per block. Each block is prefixed by
a line `[score=<cosine>]` and starts with a line `# <id>` (e.g.
`# dec__utc_only`), followed by header lines (`Type:`, `Status:`,
`Confidence:`, `Scope:`, `Title:`, `Tags:`, `Source:`), an empty line, and
the body paragraphs. Optional `Links:` block follows the body.

Parse by splitting on `^\[score=...\]\s*\n# ` and extracting:
- `id`: the token after `# ` on the line following the score
- `score`: the float inside `[score=...]`
- `text`: everything between the empty-line-after-headers and the start of the `Links:` block (or end of block, whichever comes first)

### Step 3: Score relevance

Use the cosine `score` parsed from `[score=<cosine>]` verbatim as
`relevance_score`. Scores are already in `[0, 1]` and already ranked by
Papyrus.

### Step 4: (reserved)

### Step 5: Emit structured output

Return a JSON list ordered by relevance_score descending, top 10 only:

```json
[
  {
    "memory_id": "dec__utc_only",
    "text": "All timestamps recorded by the tooling SHALL use UTC. ...",
    "relevance_score": 1.0
  },
  ...
]
```

Print as a single fenced block:

````
```json
<list>
```
````

No surrounding prose.

## Input

- `feature_context` (from the caller): 1-3 sentences describing the feature being authored.
- `artefact_type`: one of `req`, `arch`, `vplan`, `fmea` (reserved for future filtering; v1 does not use it).
- `project_dir` (from the caller or inferred from cwd): path whose `.papyrus/` is searched.

## Output

JSON array of 0-10 memory objects. Empty array means no workspace or no matches — not an error.

## Failure modes

- `papyrus` binary missing → return `[]` (skill is a best-effort assist; do not block chain).
- Workspace empty → return `[]`.
- `papyrus recall` exits non-zero → return `[]`.
- Semantic extra not installed (exits non-zero with "requires papyrus[semantic]") → return `[]`. Caller should install `papyrus[semantic]` and run `papyrus rebuild-index` to enable.

## Composition

Upstream: any draft skill. The draft skill reads this skill's JSON output and inserts the memory `text` entries as a "Design decisions to respect" section in its own input context.
