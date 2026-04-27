# abstract-prose

Axis-8 failure case — the abstract-prose regression guard.

The CREQ body is lifted verbatim from an abstract-prose style observed
during a prior dogfooding session: "the component shall read the input
CSV file using the caller-configured column delimiter and text encoding,
surfacing a read error to its caller when...". Zero backticks, zero
verb-prefixed class names, zero function-call shapes. Every other
mechanical axis has nothing to complain about — but the CREQ adds no
verification information the source code does not already carry.

Axis 8 (`source_doc_resolves`) fails because the body names no symbols
that appear in the declared file — the CREQ is untestable against the
cited source. The failure surfaces that a fully abstract CREQ does not
ground-truth against the code even when prose mechanics pass.
