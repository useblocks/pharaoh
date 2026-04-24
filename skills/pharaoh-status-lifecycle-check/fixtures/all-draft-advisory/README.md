# all-draft-advisory

Advisory mode over the same fully unreviewed corpus. Every need is `status: draft`; `enforce: false`. Expected verdict is `overall: "pass"` — the gate does not block pre-release development. `draft_count` still reports the true count so consumers (dashboards, pharaoh-quality-gate summaries) see the distribution, and `blockers` carries a single informational line flagging the advisory drafts rather than failing.
