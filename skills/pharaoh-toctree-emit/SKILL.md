---
name: pharaoh-toctree-emit
description: Use when a composition skill has just emitted a set of RST files into a directory and needs to add (or regenerate) an `index.rst` with a Sphinx toctree over them. Prevents orphan-file warnings under `sphinx-build -W`. Does NOT modify the emitted RST files. Does NOT wire the emitted directory into any parent toctree — that is a caller concern.
---

# pharaoh-toctree-emit

## When to use

Invoke at the end of a plan (emitted by `pharaoh-write-plan`, executed by `pharaoh-execute-plan`) that writes N RST files into a directory (e.g. `docs/source/features/`). Without an `index.rst` with a matching toctree, Sphinx treats every generated file as orphan and `sphinx-build -W` fails. This skill writes that index, and only that index.

Do NOT use to wire the emitted directory into its parent (e.g. updating the project-root `index.rst` to reference `features/index`). That is a separate caller concern — changes to the parent toctree are outside this skill's scope.

Do NOT use to patch an existing `index.rst` with different content — if an existing index disagrees with what this skill would write, the skill warns and does not overwrite. Caller decides whether to delete the existing file or merge manually.

## Atomicity

- (a) Indivisible — one directory + one glob + one caption in → one `index.rst` file written (or no-op if already matches). No modifications to other RST files. No parent-toctree edits.
- (b) Input: `{target_dir: str, file_glob: str, parent_caption: str, maxdepth?: int, exclude?: list[str]}`. Output: JSON `{toctree_path: str, files_included: list[str], files_modified: bool}`.
- (c) Reward: fixture `pharaoh-validation/fixtures/pharaoh-toctree-emit/input_dir/` containing three files (`csv_export.rst`, `jama_pull.rst`, `reqif_import.rst`). With `target_dir` = that path, `file_glob` = `"*.rst"`, `parent_caption` = `"Features"`, `maxdepth` = `1` → skill writes `<target_dir>/index.rst` whose content exactly matches the `expected_index.rst` fixture (same alphabetical ordering of stems, same caption, same maxdepth, same blank lines).
- (d) Reusable for any sphinx-needs project with dynamically emitted RST sets (features, modules, decisions, releases).
- (e) Composable: one directory per call. A plan emitted by `pharaoh-write-plan` may include N toctree-emit tasks (one per target_dir) dispatched by `pharaoh-execute-plan`, but this skill itself handles exactly one.

## Input

- `target_dir`: absolute path to the directory whose RST files should be indexed.
- `file_glob`: glob pattern applied within `target_dir` (e.g. `"*.rst"`, `"*.md"`). Non-recursive — toctrees are one level deep by convention.
- `parent_caption`: human-readable heading shown above the toctree (`Features`, `Modules`, `Decisions`, etc.).
- `maxdepth` (optional): `:maxdepth:` option for the toctree. Default `1`.
- `exclude` (optional): list of filename globs to exclude from the toctree. Default `["index.rst"]` (never self-reference).

## Output

```json
{
  "toctree_path": "/abs/path/to/target_dir/index.rst",
  "files_included": ["csv_export", "jama_pull", "reqif_import"],
  "files_modified": true
}
```

`files_included` contains stems (filename without `.rst` extension), in the order they appear in the emitted toctree (alphabetical).

`files_modified`:
- `true` if the skill wrote a new `index.rst` or overwrote one with matching content (idempotent write).
- `false` if `index.rst` already existed with CONTENT MATCHING what this skill would have written — no-op.
- `false` PLUS a warning in the return if `index.rst` exists with different content — skill did not overwrite; caller must handle merge.

## Process

### Step 1: Enumerate files

Glob `target_dir/<file_glob>` non-recursively. Subtract `exclude` matches. Sort alphabetically by filename. Strip file extensions to produce toctree entries (Sphinx toctree entries omit `.rst`).

If zero files remain, FAIL: `"no files matched <file_glob> under <target_dir>; nothing to index"`.

### Step 2: Build toctree content

Emit content in this exact shape:

```rst
<parent_caption>
<underline of = characters, exact length of parent_caption>

.. toctree::
   :maxdepth: <maxdepth>

   <stem_1>
   <stem_2>
   <stem_3>
```

- Single blank line between the caption underline and `.. toctree::`.
- Single blank line between `:maxdepth:` line and the first stem.
- Stems indented with 3 spaces (Sphinx toctree convention).
- No trailing blank lines after the last stem.

### Step 3: Check existing index.rst

If `target_dir/index.rst` does not exist → write the new content, return `files_modified=true`.

If it exists and its content (after normalizing line endings and trailing whitespace) exactly equals what would be written → no-op, return `files_modified=false`, `warnings=[]`.

If it exists with different content → no-op, return `files_modified=false`, warnings include `"index.rst exists with different content — not overwriting; delete manually or merge to regenerate"`.

### Step 4: Return

Return the JSON shape per Output section.

## Last step

No dedicated `*-review` atom exists for toctree emission; the operation is structural (write one `index.rst` listing N files) and its correctness is checked mechanically rather than via a prose-judgement review atom. This skill therefore performs an inline self-verification in Step 4 before returning:

1. Every entry in the emitted `toctree` block resolves to an existing file under `target_dir` (no dangling references).
2. The emitted `index.rst` contains exactly one `.. toctree::` directive (no accidental duplication).
3. No entry appears twice in the toctree body.

If any check fails, do not write `index.rst`; return `status: "failed"` with evidence.

Coverage is mechanically enforced at plan level by `pharaoh-quality-gate`'s orphan / link-completeness invariants plus `sphinx-build -W` itself (which fails on orphan RST files). See [`shared/self-review-invariant.md`](../shared/self-review-invariant.md) for the rationale.

## Failure modes

- `target_dir` does not exist → FAIL.
- `target_dir` is not a directory → FAIL.
- Zero files matched glob (after exclude) → FAIL per Step 1.

## Non-goals

- No parent-toctree updates. The caller (human or a future composition skill) wires `<target_dir>/index.rst` into the project root's `index.rst` manually.
- No inter-file toctree. This skill assumes a flat glob over one directory — nested toctrees require separate invocations.
- No .md support beyond passing `*.md` as `file_glob`. Sphinx's myst_parser must already be configured in the project for Markdown files to resolve.
