# KCWorks Test Fixtures

A collection of shared python test fixtures for the knowledge-commons-works package and its dependency submodules.

Version 1.0.0

## Peer checkout sync

`scripts/update_fixtures.sh` finds the kcworks monorepo (a directory that has `site/kcworks/dependencies`), then runs `git checkout main && git pull` in every other fixtures checkout under that tree, including the parent project's `tests/fixtures`. It skips the checkout that contains the script being run.

`githooks/post-commit` pushes the new commit to `origin`, then runs that script.

**You must register the hook manually.** Git does not enable committed hooks by default, and cloning or updating this submodule will not turn them on. In each fixtures checkout where you commit (the kcworks `tests/fixtures` tree and any dependency nested copy), run this once from that checkout’s root:

```bash
git config core.hooksPath githooks
```

Confirm with `git config --get core.hooksPath` (it should print `githooks`). Without that setting, commits will not push or sync peer checkouts automatically.

## Copyright

Copyright MESH Research, 2026

## License

Licensed under the MIT license
