# KCWorks Test Fixtures

A collection of shared python test fixtures for the knowledge-commons-works package and its dependency submodules.

Version 1.0.0

## Peer checkout sync

`scripts/update_fixtures.sh` finds the kcworks monorepo (a directory that has `site/kcworks/dependencies`), then updates every other **kcworks-test-fixtures** checkout under that tree (including the parent project's `tests/fixtures`). It skips the checkout that contains the script being run, and skips directories whose `origin` is not `kcworks-test-fixtures` (e.g. plain `tests/fixtures` trees inside upstream packages).

For each peer it:

1. `git fetch origin` and hard-resets `main` to `origin/main` (refuses dirty trees unless `UPDATE_FIXTURES_FORCE=1`)
2. Stages the updated submodule gitlink in the enclosing package/monorepo repo

It does **not** commit those parent repos — commit the staged `tests/fixtures` pointer bumps yourself (in each dependency package and/or the monorepo).

`githooks/post-commit` pushes the new fixtures commit to `origin`, then runs that script.

**You must register the hook manually.** Git does not enable committed hooks by default, and cloning or updating this submodule will not turn them on. In each fixtures checkout where you commit (the kcworks `tests/fixtures` tree and any dependency nested copy), run this once from that checkout’s root:

```bash
git config core.hooksPath githooks
```

Confirm with `git config --get core.hooksPath` (it should print `githooks`). Without that setting, commits will not push or sync peer checkouts automatically.

## Copyright

Copyright MESH Research, 2026

## License

Licensed under the MIT license
