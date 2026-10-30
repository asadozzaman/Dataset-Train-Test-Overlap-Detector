# Contributing

Useful contributions improve evidence accuracy, path handling, explainability,
performance bounds or report usability. Open an issue for a substantial change
before implementing it. Describe the concrete trigger and expected behavior.

## Development setup

Python 3.10+ is required. Create a virtual environment, then install:

```bash
python -m pip install -e '.[dev,similarity]'
```

On Windows, use `.\.venv\Scripts\python.exe` explicitly if the environment is not
activated. On Linux, use `.venv/bin/python`.

Before a pull request:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m build
```

For showcase changes, follow [the showcase guide](showcase/README.md), build a new
output directory and run `npm ci` followed by `npm test` from `showcase/`. Review the
actual desktop/mobile layout where browser access is available; DOM tests do not
prove visual quality.

## Evidence and scope

- Exact bytes, reviewed metadata assertions and visual candidates must remain distinct.
- Missing provenance must never silently become verified independence.
- Add meaningful regressions for false-clean results, evidence classification and path semantics.
- Keep audits non-destructive, CPU-only and deterministic for identical inputs/paths.
- Preserve explicit work/memory bounds for optional similarity checks.
- Keep runtime dependencies small; do not add training, authentication or hosted services.
- Update [architecture](docs/ARCHITECTURE.md) and [contracts](docs/CONTRACTS.md) when behavior changes.

## Public data and privacy

Default Python tests run offline. Public-data verification is an explicit network
opt-in. Keep third-party images, archives and generated reports outside Git. Use
clearly labeled synthetic provenance for tests; never invent authentic histories.
Honor [dataset source terms](THIRD_PARTY_NOTICES.md).

When reporting a bug, share a minimal YAML/CSV, application/Python version, command,
expected result and sanitized error or JSON excerpt. Avoid private images, local
usernames, access tokens and sensitive recording logs. For sensitive vulnerabilities,
use GitHub's private security-reporting option when available.

Keep pull requests focused. Explain the resulting behavior and verification so a
reviewer can assess it without the surrounding conversation. Contributions are
provided under the project's [MIT license](LICENSE).
