# step-1-enabled

Represents the post-2026-04-22 bootstrap-default shape. `pharaoh-setup` now lands `require_verification = true` out of the box (step 1 of the ladder), so a fresh project that runs `pharaoh-setup` → `pharaoh-gate-advisor` lands on this fixture's state, not `fresh-from-bootstrap/`.

Expected outcome: advisor walks the ladder, sees step 1 already enabled, advances to step 2 (`require_change_analysis`), and returns it as the next recommended gate. The rationale names the blocker — `pharaoh-change` must be tailored for the project before flipping the flag is meaningful, otherwise every authoring task alarms without a mitigation path.

Exercise: the step-1-already-enabled branch of the detection rule — proves the ladder walk advances past enabled flags instead of re-recommending step 1.
