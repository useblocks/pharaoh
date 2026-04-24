# fully-reviewed-enforcing

Release-gate happy path. Every need is past `draft` — one `reviewed`, one `approved`, one `released`; `enforce: true`. Expected verdict is `overall: "pass"` with `draft_count: 0` and an empty `blockers` list. Confirms the binary gate lets a fully-promoted corpus through and does not accidentally fail on needs that stopped at `reviewed` or `approved` (past draft is sufficient; the gate does not require `released`).
