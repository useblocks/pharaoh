# all-draft-enforcing

Release-gate mode with a fully unreviewed corpus. Every need is `status: draft`; `enforce: true`. Expected verdict is `overall: "fail"` — `draft_count` equals the total, and `blockers` carries a summary line plus one entry per draft need id. The `needs_by_status` map shows declared states with zero buckets for the ones nothing has reached yet, proving the skill reports the full shape rather than only observed keys.
