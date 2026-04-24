---
name: pharaoh-reproducibility-check
description: Use when diffing two output directories produced by running the same plan twice to confirm the build is reproducible. Consumes a baseline directory, a rerun directory, and an optional list of mask rules for known-non-deterministic fields (timestamps, randomly-generated ids); emits a list of drifted files with per-file changed-field summaries. Does NOT run the plan — running is the caller's responsibility (`pharaoh-execute-plan`).
---

# pharaoh-reproducibility-check

## When to use

Invoke from a reproducibility-audit CI job (or directly by a human) after the caller has produced two output directories from two independent runs of the same plan. Takes the two directories plus an optional list of `mask_rules` for known-non-deterministic fields and emits a findings JSON listing which files drifted and which fields inside them changed. Passes when every file is byte-identical after masking; fails when at least one file differs.

**This skill does NOT run the plan.** Running the plan twice is the caller's responsibility — `pharaoh-execute-plan` is the atom that executes plans, and the orchestrator that calls `pharaoh-execute-plan` twice and then this check is future work (deferred from this plan's scope). This atom only diffs two pre-existing output directories.

Do NOT use to re-author artefacts, to regenerate the rerun directory, or to repair drift — read-only. Do NOT use to mask the baseline in place or rewrite it with placeholders — the masking is done on in-memory copies for the comparison only. Do NOT use to infer mask rules automatically — the caller declares them; no hardcoded Pharaoh-specific masks.

## Atomicity

- (a) Indivisible: one baseline directory + one rerun directory + optional mask rules in → one drift report out. No plan execution, no artefact emission, no side effects.
- (b) Input: `{plan_path: str, baseline_output_dir: str, rerun_output_dir: str, mask_rules: list[{path: str, field: str, regex: str}]}`. Output: findings JSON per the shape in `## Output` below.
- (c) Reward: fixtures under `skills/pharaoh-reproducibility-check/fixtures/` — one per outcome:
  1. `identical-output/` — baseline and rerun are byte-identical after masking (timestamps masked out; everything else matches) → `overall: "pass"`, `drifted_files: []`, empty `drift_summary`.
  2. `drifted-titles/` — rerun has different need titles (e.g. `"Login requirement"` → `"Login req"`) that no mask rule targets → `overall: "fail"`, `drifted_files` names the file, `drift_summary[file].fields_changed` lists the `.title` paths of the drifted records.
  3. `drifted-ids-but-masked/` — rerun has different generated need ids (`REQ_abc123` vs `REQ_def456`) but `mask_rules` includes an entry that replaces any matching `id` value with a placeholder; after masking the files are equal → `overall: "pass"`.

  Pass = each fixture's actual output matches `expected-output.json` modulo ordering of `drifted_files` (sorted ascending) and `fields_changed` (also sorted ascending).
- (d) Reusable across projects — the diff is tree-of-files generic and the mask rules are data-driven. No Pharaoh-specific field names, id shapes, or timestamp formats are baked in. Works for any plan whose output directory is a tree of JSON / YAML / text files.
- (e) Read-only. Does not modify the baseline or rerun directories, does not write the masked copies to disk, does not touch the plan file. Running twice on identical inputs yields byte-identical output.

## Input

- `plan_path`: absolute path to the plan YAML the two runs came from. Used as diagnostic metadata in the emitted report (echoed under the plan key in a future shape) but is NOT semantically load-bearing for the diff itself — the skill does not re-read or re-execute the plan. An unreadable or missing path is surfaced as a blocker but does not abort the diff if both output directories are readable.
- `baseline_output_dir`: absolute path to the output directory produced by the first plan run. Must exist and be readable.
- `rerun_output_dir`: absolute path to the output directory produced by the second plan run on the same plan. Must exist and be readable.
- `mask_rules`: optional list of `{path: str, field: str, regex: str}` entries. Each entry declares that, inside every file matched by `path` (a glob relative to the output-dir root), before comparing, replace the value at `field` (a dotted JSON-path into the parsed file) with the placeholder string `"<masked>"` if the current value matches `regex`. Defaults to `[]` (no masking).

Edge cases:
- `baseline_output_dir` or `rerun_output_dir` missing → `overall: "fail"`, `blockers: ["baseline_output_dir unresolved: <path>"]` (or the rerun equivalent).
- One side contains files the other does not — file-level drift: the absent file is listed in `drifted_files` with `drift_summary[file] = {"fields_changed": [], "reason": "file only present in <baseline|rerun>"}`.
- A `mask_rules` entry's `regex` fails to compile → `overall: "fail"`, blocker `"mask regex invalid: <entry>"`; no files are diffed.
- A mask rule targets a path that no file matches, or a field that no parsed record carries → silently ignored for that file (masking is best-effort per-entry).
- Non-parseable files (binary, malformed JSON) are compared byte-for-byte; masking is skipped for them and any bytes-difference is reported as `fields_changed: ["<byte-diff>"]`.

## Output

```json
{
  "baseline": "/abs/path/baseline/",
  "rerun":    "/abs/path/rerun/",
  "drifted_files": [
    "docs/_build/needs/needs.json"
  ],
  "drift_summary": {
    "docs/_build/needs/needs.json": {
      "fields_changed": [
        "comp_req__foo_01.title"
      ],
      "count": 1
    }
  },
  "overall": "fail"
}
```

Fields (in canonical order):
- `baseline`: echo of the input `baseline_output_dir`.
- `rerun`: echo of the input `rerun_output_dir`.
- `drifted_files`: list of file paths (relative to the respective output-dir roots) that differ after masking, sorted ascending.
- `drift_summary`: mapping from each drifted file path to `{fields_changed: list[str], count: int}`. `fields_changed` is the sorted list of dotted field paths whose values changed; `count` is `len(fields_changed)`. For files that exist on only one side, `fields_changed` is empty and an extra `reason` field explains the asymmetry. For byte-level diffs on non-parseable files, `fields_changed` is `["<byte-diff>"]`.
- `overall`: `"pass"` iff `drifted_files` is empty AND no blocker fired. `"fail"` otherwise.

On input errors (unresolved paths, invalid mask regex) the shape still carries every field with empty `drifted_files`, empty `drift_summary`, `overall: "fail"`, plus a top-level `blockers` list containing the error strings, so downstream callers can diff one shape.

**What counts as drift.** Drift is reported at two granularities: the outer `drifted_files` list names files at file-level (present on both sides but differing, OR present on only one side), and the inner `drift_summary` reports field-level detail for each drifted parseable file. The gate is file-level (any entry in `drifted_files` fails the check); the per-field detail exists so the caller can see WHAT drifted without re-running the diff.

## Process

### Step 1: Validate inputs

Resolve `baseline_output_dir` and `rerun_output_dir`. If either is missing or unreadable, populate `blockers` and emit the error shape. Compile every `mask_rules[i].regex` eagerly; on any `re.error`, populate `blockers` with `"mask regex invalid: <entry>"` and emit the error shape. `plan_path` is echoed into diagnostic logs but validation is soft — a missing plan file does not abort the diff.

### Step 2: Enumerate files

Walk `baseline_output_dir` recursively, collect the relative path of every file. Do the same for `rerun_output_dir`. Compute the union of the two sets. For each file path in the union:

- If present on only one side, flag it as drifted with `reason: "file only present in <baseline|rerun>"`.
- If present on both sides, continue to Step 3.

### Step 3: Load and mask

For each file present on both sides:

1. Attempt to parse both copies (JSON for `*.json`, YAML for `*.yaml`/`*.yml`, plain text otherwise). Non-parseable files short-circuit to byte-comparison (Step 4b).
2. For each `mask_rules` entry whose `path` glob matches the current file's relative path, apply the mask: traverse `field` (dotted JSON-path, e.g. `needs.comp_req__foo_01.created_at`; supports `*` wildcard segments for per-item masking like `needs.*.created_at`) on the parsed structure. At each leaf the mask visits, if the current value is a string matching `regex`, replace it with `"<masked>"`. Apply masks to both the baseline and rerun copies in memory.
3. Proceed to Step 4a.

### Step 4: Compare

**4a (parseable files):** Deep-compare the two masked structures. Any field whose value differs is added to `fields_changed` for this file, expressed as a dotted path (`<top-key>.<sub-key>...`). Added or removed keys are reported as `<path>` with a trailing `+` or `-` respectively. If `fields_changed` is non-empty, the file is drifted.

**4b (byte-comparable files):** Byte-compare the two files. If they differ, the file is drifted with `fields_changed: ["<byte-diff>"]`.

### Step 5: Emit the findings JSON

Populate every field per the `## Output` shape. Sort `drifted_files` ascending; sort each `fields_changed` ascending. `overall` is `"pass"` iff `drifted_files` is empty and no blocker fired; `"fail"` otherwise.

## Detection rule

One mechanical check, implemented as the five-step process above. No LLM judgement.

Minimum viable Python reference implementation (≤ 60 lines, omitting glob and dotted-path helpers for brevity):

```python
import json, os, re, fnmatch, yaml
from pathlib import Path

def walk(root):
    root = Path(root)
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}

def load(p):
    s = open(p, "rb").read()
    try:
        if p.endswith(".json"):
            return "parsed", json.loads(s)
        if p.endswith((".yaml", ".yml")):
            return "parsed", yaml.safe_load(s)
    except Exception:
        pass
    return "bytes", s

def apply_masks(obj, field_path, regex):
    # Traverse dotted field_path (with `*` wildcards). At each leaf, if the
    # current value is a string matching regex, replace it with "<masked>".
    segs = field_path.split(".")
    def visit(node, i):
        if i == len(segs):
            return "<masked>" if isinstance(node, str) and regex.search(node) else node
        if segs[i] == "*" and isinstance(node, dict):
            return {k: visit(v, i + 1) for k, v in node.items()}
        if isinstance(node, dict) and segs[i] in node:
            node[segs[i]] = visit(node[segs[i]], i + 1)
        return node
    return visit(obj, 0)

def diff(a, b, prefix=""):
    changed = []
    if type(a) != type(b):
        return [prefix or "<root>"]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            p = f"{prefix}.{k}" if prefix else k
            if k not in a:  changed.append(p + "+")
            elif k not in b: changed.append(p + "-")
            else:            changed += diff(a[k], b[k], p)
        return changed
    if a != b: return [prefix or "<root>"]
    return []

# Main
compiled = [(r["path"], r["field"], re.compile(r["regex"])) for r in mask_rules]
b_files, r_files = walk(baseline), walk(rerun)
drifted, summary = [], {}

for rel in sorted(b_files | r_files):
    if rel not in b_files:
        drifted.append(rel); summary[rel] = {"fields_changed": [], "count": 0,
                                             "reason": "file only present in rerun"}; continue
    if rel not in r_files:
        drifted.append(rel); summary[rel] = {"fields_changed": [], "count": 0,
                                             "reason": "file only present in baseline"}; continue

    kind_b, a = load(os.path.join(baseline, rel))
    kind_r, c = load(os.path.join(rerun, rel))
    if kind_b != kind_r or kind_b == "bytes":
        if a != c:
            drifted.append(rel); summary[rel] = {"fields_changed": ["<byte-diff>"], "count": 1}
        continue

    for glob, field, rx in compiled:
        if fnmatch.fnmatch(rel, glob):
            a = apply_masks(a, field, rx); c = apply_masks(c, field, rx)

    fc = sorted(diff(a, c))
    if fc:
        drifted.append(rel); summary[rel] = {"fields_changed": fc, "count": len(fc)}

overall = "pass" if not drifted else "fail"
```

The full implementation adds the blocker propagation for unresolved paths, the eager regex compilation, and the canonical-field emission order.

## Failure modes

- **Dotted field paths are a simplified JSON-pointer.** Segments are literal keys; `*` wildcards any key at that level; arrays are addressed by index (`needs.0.title`). Projects whose data has keys containing literal dots must split those keys before emitting the output — documented limitation, acceptable for every Pharaoh output shape observed to date.
- **Masking is per-leaf, not per-subtree.** A mask rule targeting `needs.*.created_at` replaces only the `created_at` scalar, not the whole need record. Projects wanting to mask out entire subtrees should declare a rule per leaf field or pre-process the output.
- **Regex matching is `re.search`, not `re.fullmatch`.** The rule fires when the regex finds a match anywhere in the string value; this is deliberate so a regex like `\d{10,}` can mask out Unix timestamps without requiring the field value to be exactly a timestamp.
- **Binary or malformed files fall back to byte compare.** A corrupt JSON on either side is compared byte-for-byte. That is usually what the caller wants (a malformed file is itself drift), but a project relying on lenient parsing should repair the file before invoking this check.
- **`plan_path` is metadata-only.** The skill does NOT parse or execute the plan; it does not verify that the two output directories actually came from it. Callers that need that assurance should assert it before invoking.
- **File-level is the gate.** Any drifted file fails the check. The per-field detail does not downgrade a one-field diff to a warning — reproducibility is binary. Projects that want per-field tolerance should encode it via mask rules.

## Tailoring extension point

- `tailoring.reproducibility_mask_rules`: projects can declare a canonical list of mask rules in their tailoring and pipe it into this skill's `mask_rules` input. Typical entries cover timestamps (`created_at`, `updated_at`, `build_timestamp`) and randomly-generated ids (`run_id`, `session_id`). No other knobs are exposed.

No other knobs. The skill is deliberately a thin diff engine — every policy decision (what to mask, what threshold) lives in the caller or the tailoring.

## Composition

Role: `atom-check`.

Callable standalone from any CI job that already holds two output directories plus a mask-rule list. The orchestrator that invokes `pharaoh-execute-plan` twice and then this check is out of scope for this atom. Never dispatches other skills. Never modifies the baseline or rerun directories.

Complements `pharaoh-dispatch-signal-check` (which audits whether a plan's declared execution mode was respected in `runs/`) — that skill checks run structure, this skill checks output-byte stability across reruns. The two atoms operate on different artefacts and neither dispatches the other.
