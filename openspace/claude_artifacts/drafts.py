from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable


DEFAULT_DRAFT_SUBDIRS = (
    "commands",
    "templates",
    "reference",
    "memory",
    "reports",
)


def ensure_evolution_draft_dirs(root: Path, subdirs: Iterable[str] = DEFAULT_DRAFT_SUBDIRS) -> Dict[str, Path]:
    root.mkdir(parents=True, exist_ok=True)
    created: Dict[str, Path] = {}
    for subdir in subdirs:
        path = root / subdir
        path.mkdir(parents=True, exist_ok=True)
        created[subdir] = path
    return created


def build_draft_filename(artifact_name: str, action: str, *, now: datetime | None = None) -> str:
    stamp = (now or datetime.now()).strftime("%Y-%m-%d")
    safe_name = artifact_name.strip().replace(" ", "-").replace("/", "-").replace("\\", "-")
    safe_action = action.strip().replace(" ", "-")
    return f"{stamp}-{safe_name}-{safe_action}.draft.md"
