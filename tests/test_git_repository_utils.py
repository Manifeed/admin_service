from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from app.utils.git_repository_utils import GitRepositorySyncError, run_git_command


def test_run_git_command_wraps_missing_git_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise FileNotFoundError(2, "No such file or directory", "git")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(GitRepositorySyncError) as exception_info:
        run_git_command(["status"], cwd=Path("/tmp/repository"))

    assert str(exception_info.value) == (
        "Git executable is not available in the runtime environment: git"
    )
