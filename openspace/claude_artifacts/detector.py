from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ClaudeWorkspace:
    workspace_root: Path
    claude_dir: Path
    commands_dir: Path
    templates_dir: Path
    reference_dir: Path
    evolution_drafts_dir: Path


def detect_claude_workspace(workspace_root: Optional[str | Path]) -> Optional[ClaudeWorkspace]:
    if not workspace_root:
        return None

    root = Path(workspace_root).expanduser().resolve()
    claude_dir = root / ".claude"
    if not claude_dir.is_dir():
        return None

    return ClaudeWorkspace(
        workspace_root=root,
        claude_dir=claude_dir,
        commands_dir=claude_dir / "commands",
        templates_dir=claude_dir / "templates",
        reference_dir=claude_dir / "reference",
        evolution_drafts_dir=claude_dir / "evolution-drafts",
    )
