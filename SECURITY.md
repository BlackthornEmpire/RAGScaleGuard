# Security Policy

RAGScaleGuard is intended for enterprise retrieval evaluation and diagnostics. Treat all corpora, questions, reports, and traces as potentially sensitive.

## Supported Versions

Security fixes target the current `main` branch until the project starts publishing tagged releases.

## Reporting a Vulnerability

Please report vulnerabilities privately through GitHub Security Advisories, or by contacting the maintainers listed by the project owner. Do not open public issues for vulnerabilities involving credential leakage, prompt/report injection, unsafe data handling, or corpus data exfiltration.

Include:

- Affected file and line range
- Reproduction steps
- Impact and trust boundary crossed
- Python version and package version or commit SHA

## Security Model

RAGScaleGuard is a library and evaluation toolkit, not a hosted service. It does not authenticate users, store secrets, or execute model calls by default.

Security boundaries expected from integrators:

- Keep corpora and enterprise exports outside version control.
- Run evaluations in isolated environments when using proprietary corpora.
- Do not send raw documents, prompts, reports, or traces to hosted evaluators without explicit approval.
- Apply access control, audit logging, retention, and deletion policies in the host platform.
- Treat generated Markdown/JSON reports as sensitive artefacts.

## Built-In Controls

- Report output redacts common secret patterns.
- Markdown reports escape corpus-controlled fields to reduce report injection risk.
- The default package has no network dependencies.
- The model reranker is only an adapter and does not call external services unless an integrator supplies one.

## Known Non-Goals

- Multi-tenant isolation
- Hosted API security
- Key management
- Policy enforcement across external vector stores or model providers
