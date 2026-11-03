"""Prevent cross-commit test contamination when executing historical real bugs.

Each source revision has its own checked-out Git worktree and Python import
cache directory. Python bytecode writing is disabled for the probe process.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping


def worktree_path(root: Path, label: str) -> Path:
    if label not in ("buggy", "fixed"):
        raise ValueError("Only explicitly labelled revisions are allowed")
    return Path(root) / "revision_worktrees" / label


def isolated_python_env(checkout: Path, base: Mapping[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if base is None else base)
    env.update({
        "PYTHONPATH": str(Path(checkout).resolve()),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    return env
