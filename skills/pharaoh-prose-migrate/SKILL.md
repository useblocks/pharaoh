---
name: pharaoh-prose-migrate
description: Use when a reverse-engineering run (a plan emitted by pharaoh-write-plan) finds pre-existing prose documentation files in the target output directory that would collide with generated feat RST files. Produces a sentence-by-sentence migration proposal — keep-as-user-guide, merge-into-feat-body, discard. Does NOT overwrite anything; the caller applies the proposal manually.
---

# pharaoh-prose-migrate

## When to use

Invoke when a feature-extraction run is about to write `features/<stem>.rst` into a directory that already contains a human-authored prose file with a colliding stem (e.g. `features/reqif.rst` was written by a human as user documentation; the orchestrator is about to emit `features/reqif_export.rst` and `features/reqif_import.rst`). Without migration guidance, both files end up in the tree with no cross-reference and unclear canonicity — the exact confusion observed during dogfooding.

Do NOT use to apply a migration (that is a future `pharaoh-prose-apply` skill). Do NOT use to generate new prose — this skill only processes existing content.

## Atomicity

- (a) Indivisible — one prose file + one set of emitted feats → one migration proposal. No file mutation. No deletion. No writes to the new feat RSTs.
- (b) Input: `{prose_file: str, emitted_feats: list[{id: str, title: str, body: str, source_doc: str}]}`. Output: YAML migration proposal (see Output schema).
- (c) Reward: fixture `pharaoh-validation/fixtures/pharaoh-prose-migrate/` contains `input_reqif.rst` (a prose file describing ReqIF usage) and `expected_proposal.yaml`. Scorer:
  1. Output parses as YAML.
  2. `decisions` covers every sentence (sentence count in `decisions[*].source_sentences` sums to the total sentence count of `input_reqif.rst`).
  3. Sentences classified as `merge_into_feat_body` target an `emitted_feats[*].id`.
  4. Sentences classified as `keep_as_user_guide` have a `target_file` under `user_guide/`.
  5. Sentences classified as `discard` include a rationale naming why (boilerplate, outdated, changelog-like).
  6. `summary` totals match the `decisions` aggregation.

  Pass = all 6.
- (d) Reusable for any project with pre-existing prose in its docs/source/features/ directory.
- (e) Composable: emits only a proposal. Never mutates. Caller decides whether to apply.

## Input

- `prose_file`: absolute path to the existing prose RST file to migrate.
- `emitted_feats`: list of features just emitted by `pharaoh-feat-draft-from-docs` that may cover content in `prose_file`. Each entry has:
  - `id`: feat ID (e.g. `FEAT_reqif_export`)
  - `title`: short title
  - `body`: one-sentence feat statement
  - `source_doc`: the doc the feat was derived from (used to distinguish "this feat's source was this prose file" from "this feat came from elsewhere")

## Output

```yaml
source_file: <relative path>
decisions:
  - type: keep_as_user_guide
    target_file: user_guide/<stem>.rst
    source_sentences: [<line-numbers or sentence-indices>]
    content_preview: "<first 40 chars of the preserved sentences>"
    rationale: <string>
  - type: merge_into_feat_body
    target_feat_id: FEAT_<name>
    source_sentences: [<indices>]
    content_preview: "<first 40 chars>"
    rationale: <string>
  - type: discard
    source_sentences: [<indices>]
    content_preview: "<first 40 chars>"
    rationale: <string>
summary:
  total_sentences: <int>
  keep_as_user_guide: <int>
  merge_into_feat: <int>
  discard: <int>
```

## Process

### Step 1: Read and sentence-split

Read `prose_file`. Strip RST directives (lines starting `.. ` and their indented bodies) from the split candidates — directives are not migratable prose. On the remaining text, split into sentences via a simple splitter:

```python
re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
```

Index sentences 1..N. Preserve their original text for `content_preview`.

### Step 2: Classify each sentence

Apply classification rules in order; first match wins:

**discard** — matches any of:
- Contains `TODO`, `FIXME`, `XXX`, `deprecated`, `see also`, or matches a changelog pattern (`Version \d+\.\d+`, `- Added:`, `- Fixed:`).
- Is pure boilerplate: ≤ 5 words with no noun-phrase content (e.g. "More details below.", "The following sections explain this.").
- References an outdated feature that is not in `emitted_feats`.

**keep_as_user_guide** — matches any of:
- Imperative voice addressing the user ("You can ...", "Users should ...", "To import, run ...", "Invoke the CLI with ...").
- Describes CLI commands, config syntax, or step-by-step instructions.
- Contains an RST code block reference (fenced with `::` or `.. code-block::`).
- Describes usage scenarios with concrete inputs/outputs.

Target file: `user_guide/<stem>.rst` where `<stem>` is derived from `prose_file`'s basename (e.g. `reqif.rst` → `user_guide/reqif.rst`). This keeps user documentation co-located with the feature name.

**merge_into_feat_body** — matches any of:
- Describes what the system does in declarative voice ("The system imports ReqIF files.", "ReqIF export preserves hierarchy.").
- Overlaps semantically with one of `emitted_feats[*].title + body`. Use substring match on feat title keywords as a first pass; if multiple feats match, pick the one with highest keyword overlap.
- Target: the matching feat's `id`.

**discard (fallthrough)** — if none of the above rules fire after three passes, classify as `discard` with rationale `"Sentence did not fit any migration category — likely boilerplate or stale."`

### Step 3: Group consecutive same-class sentences

Adjacent sentences with the same `type` and same `target_file`/`target_feat_id` are grouped into one `decisions` entry with `source_sentences` listing all their indices.

### Step 4: Emit summary

Count per-type:
- `total_sentences` = sum of all `source_sentences` lengths.
- `keep_as_user_guide`, `merge_into_feat`, `discard` = per-type counts.

### Step 5: Return

Return the YAML proposal.

## Failure modes

- `prose_file` not readable → FAIL.
- `emitted_feats` empty and no `discard`-only output possible → FAIL: `"no feats provided to merge into, and prose_file has no discardable content"`.
- All sentences fall through to `discard` → emit the proposal anyway with 100% discard. The caller likely misinvoked this skill; the output makes that clear.

## Non-goals

- No automatic application. The caller reviews the proposal, manually moves sentences, deletes the legacy prose file (or leaves it — skill does not prescribe).
- No cross-file prose migration. One prose file per invocation.
- No LLM re-writing of sentences. The proposal is sentence-by-sentence verbatim; the caller edits after applying.
- No user_guide/ directory creation. If the caller applies `keep_as_user_guide` decisions, they create the directory themselves.
