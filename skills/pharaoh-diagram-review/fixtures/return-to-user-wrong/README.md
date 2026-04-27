# return-to-user-wrong

The call stack induced by the arrows is `[CLI, SettingsService]` (CLI called SettingsService, SettingsService called Store). The Store return pops down to SettingsService correctly. The final return `SettingsService -->> User` then terminates at `User` — a participant that was declared but never issued a call, and is NOT the declared entrypoint (first declared caller is `CLI`).

This is the "invented User" failure mode: the diagram introduces a free-floating `User` participant and routes the terminal return there instead of back to `CLI`. The detection rule's stack walk records the mismatch and fails the axis with `return_from`, `return_to`, and the live stack in evidence.

Note: simply declaring `User` as a participant is not enough to make it a legitimate return target. The entrypoint exemption only applies when `User` is the FIRST caller in the diagram (see `return-to-caller-correct/`).
