# vondr

Minimal Python utilities packaged for PyPI. Managed with Poetry and ready for CI and guarded merges.

## Installation

```bash
pip install vondr
```

## Quick start

```python
from vondr import greet

print(greet("Vondr"))
# -> "Hello, Vondr!"
```

## Development

1) Install Poetry (`pipx install poetry` recommended).
2) Install deps: `poetry install`.
3) Run tests: `poetry run pytest`.

## Release (bump, build, publish)

Set your token before publishing: `POETRY_PYPI_TOKEN_PYPI` (or `POETRY_PYPI_TOKEN_TESTPYPI` when targeting TestPyPI).

```powershell
./scripts/release.ps1 -Version 0.1.1          # publish to PyPI
./scripts/release.ps1 -Version 0.1.1 -Repository testpypi  # publish to TestPyPI
```

The script will bump the version in `pyproject.toml`, install deps, run tests, build wheel+sdist, publish, then commit/tag/push if a git remote exists.

## Branch protection (only admins merge)

- Set up a public remote (e.g., GitHub) and enable branch protection on `main`.
- Require CI (`CI` workflow) and code owner review.
- Restrict pushes/merges to admins/maintainers only; see `.github/CODEOWNERS` for who can approve.
