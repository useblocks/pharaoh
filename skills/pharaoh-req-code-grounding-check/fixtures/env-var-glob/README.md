# env-var-glob

Axis-5 filter-step-#4 exercise. The CREQ cites `JAMA_*` as a glob
pattern over a family of environment variables. The literal string
`JAMA_*` is not a Python identifier and would fail a naive substring
lookup.

The env-glob filter detects the trailing `*`, strips it, compiles a
`\bJAMA_\w+\b` regex, and runs it against the source. At least one
match in the source (here: `JAMA_URL_ENV`, `JAMA_USERNAME_ENV`, etc.)
resolves the token.

Also exercises filter step #2 (file path / CLI command): `jama check`
is a user-facing command string, not a Python symbol — skipped.
