---
name: pharaoh-link-completeness-check
description: Use when verifying outgoing-link coverage across a full needs.json graph. For each declared link type in `artefact-catalog.yaml`, confirms every need of the governed type carries a non-empty value AND every target id resolves to an existing need. Closes the "catalogue declares `verifies` required but half the reqs ship without it" failure class.
---

# pharaoh-link-completeness-check

## When to use

Invoke from `pharaoh-quality-gate.required_checks` (invariant `link-types-covered`) or from any corpus-level lint that wants to fail the build when declared link coverage slips. Reads one `artefact-catalog.yaml` + one `needs.json`, returns coverage metrics per link type plus the list of uncovered need ids.

Scope clarification — NOT a schema check for individual directive blocks. Use `pharaoh-output-validate` for block-level schema validation (required fields present, no unknown options, well-formed RST / YAML / JSON). This atom operates on the full needs.json graph: coverage of link types across all needs of each type, link-target resolution, per-type policy enforcement.

Do NOT use to author the catalog (that is `pharaoh-tailor-fill`). Do NOT use to re-link or patch missing links (read-only). Do NOT use to grade prose quality of the linked needs.

## Atomicity

- (a) Indivisible: one artefact catalog + one needs.json in → one findings JSON out. No re-linking, no re-authoring, no dispatch of other skills.
- (b) Input: `{artefact_catalog_path: str, needs_json_path: str}`. Output: findings JSON per the shape in `## Output` below.
- (c) Reward: fixtures under `skills/pharaoh-link-completeness-check/fixtures/`:
  1. `all-covered/` — every need of every governed type carries every declared-required outgoing link AND every target resolves → `expected-output.json` with `overall: "pass"`, zero `missing` across `coverage_by_link_type`, empty `uncovered_needs`.
  2. `partial-coverage/` — some `comp_req` needs lack `:verifies:` and one need points at a non-existent id → `overall: "fail"`, `coverage_by_link_type.verifies.missing > 0`, `uncovered_needs` lists every failing id once.
  3. `tailoring-declares-verifies-optional/` — artefact-catalog marks `verifies` as optional for `comp_req`; those needs have no `:verifies:` field → `overall: "pass"`, `coverage_by_link_type.verifies.required: false`, no entries in `uncovered_needs` for that link type.

  Pass = each fixture's actual output matches `expected-output.json` modulo ordering of list elements.
- (d) Reusable across projects — consumes only the generic `artefact-catalog.yaml` + `needs.json` shapes. No project-specific link names or prefixes baked in. Tailoring extension point: the set of governed types and their `required_links` / `optional_links` is declared entirely in the catalog.
- (e) Read-only. Does not modify catalog, needs, or any on-disk state. Running twice on identical inputs produces identical output.

## Input

- `artefact_catalog_path`: absolute path to `artefact-catalog.yaml`. Each top-level key is a need `type`. Each type may declare `required_links: [<link_name>, ...]` and `optional_links: [<link_name>, ...]`. If a type declares neither, it is skipped (no policy, no failures). If a link name appears in both lists, `required_links` wins.
- `needs_json_path`: absolute path to `needs.json` produced by `sphinx-build`. Must contain a top-level `needs` object keyed by need id. Each need dict carries at least `type`, `id`, and any link-name keys whose values are lists of target ids.

Edge cases: empty `needs.json` (no needs) → `overall: "pass"`, `needs_checked: 0`, empty `coverage_by_link_type`; missing `artefact-catalog.yaml` → fail with `overall: "error"`, `errors: ["artefact_catalog not found: <path>"]`; malformed YAML / JSON → fail with `overall: "error"` and the parser message; needs of a type not declared in the catalog → counted in `needs_checked` but contribute no link-coverage rows.

## Output

```json
{
  "needs_checked": 40,
  "coverage_by_link_type": {
    "satisfies": {"required": true, "covered": 40, "missing": 0},
    "verifies":  {"required": true, "covered": 11, "missing": 29}
  },
  "uncovered_needs": ["comp_req__auth_login", "comp_req__auth_logout"],
  "unresolved_targets": [
    {"need_id": "comp_req__auth_login", "link": "verifies", "target": "tc__auth_login_ok", "reason": "target id not in needs.json"}
  ],
  "overall": "fail"
}
```

`overall` is `"pass"` iff every required link type has `missing == 0` AND `unresolved_targets` is empty. A single required-link gap OR a single unresolved target promotes `overall: "fail"`. Optional link types are reported in `coverage_by_link_type` with `required: false` and never contribute to the gate outcome — their `missing` counts are informational only. Needs whose type is absent from the catalog are counted in `needs_checked` but never populate `uncovered_needs`.

`uncovered_needs` lists each need id at most once, even when it misses more than one required link type. `unresolved_targets` enumerates every broken target separately so the caller can name each dangling pointer.

On input errors, the shape is `{"overall": "error", "errors": [<msg>, ...]}` with no other keys — callers branch on `overall` first.

## Detection rule

Three passes over the inputs; all mechanical, no LLM judgement.

### 1. Load and index

**Check:** Parse `artefact-catalog.yaml` into `{type: {required_links: set, optional_links: set}}`. Parse `needs.json` into `{need_id: need_dict}`. Build `known_ids = set(needs.keys())`.

**Detection:**
```python
catalog = yaml.safe_load(open(artefact_catalog_path))
needs  = json.load(open(needs_json_path))["needs"]
known_ids = set(needs.keys())
```

### 2. Per-need outgoing-link coverage

**Check:** For each need, look up the catalog entry for its `type`. For every link name in `required_links`, the need's dict must have that key AND the value must be a non-empty list. Missing key OR empty list records the need id in `uncovered_needs` and increments `coverage_by_link_type[<link>].missing`.

Needs whose type is not declared in the catalog contribute to `needs_checked` but generate no coverage rows. Optional links that are absent do not fail; when present, their targets are still resolved (step 3).

**Detection:**
```python
for nid, need in needs.items():
    policy = catalog.get(need["type"])
    if not policy:
        continue
    for link_name in policy.get("required_links", []):
        value = need.get(link_name) or []
        if not value:
            uncovered.add(nid)
            coverage[link_name]["missing"] += 1
        else:
            coverage[link_name]["covered"] += 1
```

### 3. Target resolution

**Check:** For every link value (required OR optional) whose list is non-empty, each target id must appear in `known_ids`. A target absent from `known_ids` records an entry in `unresolved_targets` with `{need_id, link, target, reason}`. Unresolved targets count as coverage failures even when the link itself is present and non-empty — a link that points nowhere is worse than no link.

**Detection:**
```python
for nid, need in needs.items():
    policy = catalog.get(need["type"])
    if not policy:
        continue
    all_links = set(policy.get("required_links", [])) | set(policy.get("optional_links", []))
    for link_name in all_links:
        for target in need.get(link_name) or []:
            if target not in known_ids:
                unresolved.append({
                    "need_id": nid,
                    "link": link_name,
                    "target": target,
                    "reason": "target id not in needs.json",
                })
```

### 4. Aggregate

**Check:** `overall = "pass"` iff every required link has `missing == 0` AND `unresolved_targets == []`. Otherwise `"fail"`. `uncovered_needs` is the deduplicated sorted list of need ids that missed at least one required link.

## Tailoring extension point

All policy is declared in `artefact-catalog.yaml` — no frontmatter knobs on this skill. Projects add or remove link types by editing the catalog entry for each type:

```yaml
comp_req:
  required_links: [satisfies, verifies]
  optional_links: [refines, supersedes]
```

Moving a link name from `required_links` to `optional_links` (or vice versa) is the single tailoring lever. The base skill ships with zero hardcoded link names.

## Composition

Role: `atom-check`.

Called from `pharaoh-quality-gate.required_checks` under the invariant key `link-types-covered`, which passes iff `overall == "pass"`. Also directly invokable from any corpus-level lint or CI job that produces a `needs.json`.

Never invoked by end users mid-authoring — authoring-time link checks belong in `pharaoh-req-review` / `pharaoh-arch-review` for the single artefact in hand. This atom is for full-graph sweeps after `sphinx-build` has produced `needs.json`.
