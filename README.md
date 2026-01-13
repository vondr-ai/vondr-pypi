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

1) Ensure Poetry is installed (`pipx install poetry` is recommended).
2) Install dependencies: `poetry install`.
3) Run tests: `poetry run pytest`.

## Release (bump, build, publish)

Use the helper script to bump the version, tag, build, and publish. Set your PyPI token as `POETRY_PYPI_TOKEN_PYPI` (or `POETRY_PYPI_TOKEN_TESTPYPI` when targeting TestPyPI) in your environment first.

```powershell
./scripts/release.ps1 -Version 0.1.1          # publishes to PyPI
./scripts/release.ps1 -Version 0.1.1 -Repository testpypi  # publish to TestPyPI
```

The script will:

- Update the version in `pyproject.toml`
- Install deps, run tests
- Build the wheel and sdist
- Publish via Poetry using your configured token
- Commit, tag, and push if a git remote exists

## Git and merge controls

- Initialize git locally with `git init` (already done here).
- Set your public remote (e.g., GitHub): `git remote add origin git@github.com:org/vondr.git`.
- Protect the default branch so only admins can push/merge. On GitHub: Settings → Branches → Add rule for `main`, check *Restrict who can push* (admins) and require status checks and code owner review. Similar settings exist on GitLab (Protected branches, Maintainer only).
- CODEOWNERS is set to require admin review; adjust handles in `.github/CODEOWNERS`.

