# Part of KCWorks Test Fixtures
# Copyright (C) 2024-2026, MESH Research
#
# This code is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Pytest fixtures for cli tests."""

from __future__ import annotations

from typing import Any

import pytest


class _ResultWithCombinedOutput:
    """Click ``Result`` proxy that appends pytest-captured stdout/stderr.

    Some Invenio service calls rebind ``sys.stdout`` mid-command so later
    ``click.echo`` / ``print`` output bypasses ``CliRunner`` isolation and
    lands in pytest's capture instead. Merging both matches what the user
    would see and what older Click versions effectively exposed via
    ``result.output``.
    """

    def __init__(self, result: Any, extra: str) -> None:
        self._result = result
        self._extra = extra

    @property
    def output(self) -> str:
        return f"{self._result.output}{self._extra}"

    @property
    def stdout(self) -> str:
        return f"{self._result.stdout}{self._extra}"

    def __getattr__(self, name: str) -> Any:
        return getattr(self._result, name)


@pytest.fixture()
def cli_runner(base_app, capsys):
    """Create a CLI runner for testing a CLI command.

    Uses Click ``capture="fd"`` and merges any output that escaped into
    pytest's capture (see ``_ResultWithCombinedOutput``).

    Returns:
        function: CLI runner function.
    """

    def cli_invoke(command, *args, input=None):
        result = base_app.test_cli_runner(capture="fd").invoke(
            command, args, input=input
        )
        captured = capsys.readouterr()
        extra = f"{captured.out}{captured.err}"
        if not extra:
            return result
        return _ResultWithCombinedOutput(result, extra)

    return cli_invoke
