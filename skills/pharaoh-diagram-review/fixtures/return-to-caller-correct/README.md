# return-to-caller-correct

Same source as `return-to-user-wrong/`, but the diagram legitimately declares `User` as the entrypoint actor AND `User` is the source of the first call (`User->>CLI`). The stack walk builds `[User, CLI, SettingsService]`; every return arrow pops to a prior caller on the stack:

- `Store -->> SettingsService` pops to SettingsService (top of stack after Store call).
- `SettingsService -->> CLI` pops to CLI.
- `CLI -->> User` pops to User — the declared entrypoint, which issued the first call.

All three returns terminate at a caller from the stack, so `returns_match_call_stack` passes. Contrast with `return-to-user-wrong/` where `User` was declared but never called, making the terminal return to `User` an invented target.
