# fresh-from-bootstrap

Represents the pre-2026-04-22 shape — every gate shipped at its advisory default (`strictness = "advisory"`, all four booleans `false`). This is the baseline the ladder was designed to unstick.

Expected outcome: `pharaoh-gate-advisor` walks the ladder, finds step 1 (`require_verification`) still off, and recommends it. `blocker` for step 1 is `"none — safe to enable now"` — the review skills are ready out of the box, so the project can flip this flag immediately. The remaining four ladder entries ship verbatim in the output so the user sees the full path, not just the next step.

Exercise: the no-flags-enabled happy path of the detection rule's step-1 iteration over the fixed ladder.
