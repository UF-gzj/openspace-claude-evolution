from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ClaudeArtifactType(str, Enum):
    COMMAND_ALIAS = "command_alias"
    COMMAND_WORKFLOW = "command_workflow"
    CLAUDE_TEMPLATE = "claude_template"
    CLAUDE_MEMORY = "claude_memory"
    REFERENCE_CARD = "reference_card"
    REFERENCE_INDEX = "reference_index"
    REFERENCE_FEEDBACK = "reference_feedback"
    REFERENCE_TEMPLATE = "reference_template"


class ClaudeLifecycleStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATE_CANDIDATE = "deprecate_candidate"
    SOFT_DEMOTED = "soft_demoted"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class ClaudeArtifact:
    artifact_id: str
    artifact_type: ClaudeArtifactType
    path: Path
    workspace_root: Path
    lifecycle_status: ClaudeLifecycleStatus = ClaudeLifecycleStatus.ACTIVE
    consumers: List[str] = field(default_factory=list)
    producers: List[str] = field(default_factory=list)
    project_name: Optional[str] = None
    notes: str = ""
