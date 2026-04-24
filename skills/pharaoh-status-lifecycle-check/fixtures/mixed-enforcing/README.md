# mixed-enforcing

Release-gate mode over a partially reviewed corpus. Two needs are `draft`, one is `reviewed`, one is `approved`; `enforce: true`. Expected verdict is `overall: "fail"` — the binary gate blocks on any remaining drafts. `blockers` lists only the two draft need ids, not the reviewed or approved ones, proving the skill enumerates drafts rather than "everything not released". `needs_by_status` reports the four buckets with observed counts.
