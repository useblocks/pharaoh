# language-override

Python source held in a `.txt` file. With `language: "auto"` the extension-based resolver would fail (no row matches `.txt`), but the caller supplies `language: "python"` via `input-meta.yaml` to bypass extension resolution. The Python AST classifier then applies — the `raise GreetError(...)` statement satisfies the exception-surface rule → `behavioral`. Three needs cite the file and `GreetError` appears in CREQ content. Expected verdict: `overall: "pass"` with `language: "python"` in the output.
