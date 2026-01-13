# Contributing to Vondr

Thanks for your interest! To keep releases safe, merges are limited to admins/maintainers.

## Ground rules

- All changes go through pull requests against `main`.
- CI (`.github/workflows/ci.yml`) must pass before merge.
- A code owner must review and approve (see `.github/CODEOWNERS`).
- Direct pushes to `main` are disabled via branch protection; only admins/maintainers may merge.

## Branch protection setup (GitHub)

1. Settings → Branches → Add rule for `main`.
2. Require status checks to pass (`CI`).
3. Require pull request approval by code owners.
4. Restrict who can push to matching branches: add your admin team.
5. Enable "Do not allow bypassing the above settings" to keep merges limited to admins.

For GitLab: Settings → Repository → Protected Branches → Protect `main` and set "Allowed to push" and "Allowed to merge" to Maintainers.

