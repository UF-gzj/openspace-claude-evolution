from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from openspace.claude_artifacts import ClaudeArtifact, ClaudeArtifactManager, build_draft_filename
from openspace.skill_engine.registry import SkillMeta
from openspace.skill_engine.types import SkillRecord
from openspace.utils.logging import Logger

from .store import LifecycleStore
from .types import HardStandardEvidence, LifecycleEntry, LifecycleStatus, LifecycleSubjectType

logger = Logger.get_logger(__name__)


class LifecycleManager:
    """Lifecycle sidecar for native skills and `.claude` artifacts.

    The manager only records governance state and draft reports. It does not
    mutate OpenSpace's native skill store or formal `.claude` files directly.
    """

    def __init__(
        self,
        workspace_root: Optional[str | Path],
        *,
        claude_manager: Optional[ClaudeArtifactManager] = None,
    ) -> None:
        root = Path(workspace_root).expanduser().resolve() if workspace_root else Path.cwd()
        self._workspace_root = root
        self._claude_manager = claude_manager
        self._store = LifecycleStore(root / ".openspace" / "lifecycle")

    @property
    def store_path(self) -> Path:
        return self._store.path

    def list_entries(self) -> List[LifecycleEntry]:
        return self._store.list_entries()

    def sync_native_skills(self, skills: Iterable[SkillMeta | SkillRecord]) -> int:
        count = 0
        entries = self._store.load_all()
        for skill in skills:
            skill_id = getattr(skill, "skill_id")
            path = str(getattr(skill, "path", ""))
            existing = entries.get(skill_id)
            if existing is None:
                entries[skill_id] = LifecycleEntry(
                    subject_id=skill_id,
                    subject_type=LifecycleSubjectType.NATIVE_SKILL,
                    subject_path=path,
                    source="inventory_sync",
                )
                count += 1
            elif path and existing.subject_path != path:
                existing.subject_path = path
                existing.last_evaluated_at = datetime.now()
        self._store.save_all(entries)
        return count

    def sync_claude_artifacts(self, artifacts: Iterable[ClaudeArtifact]) -> int:
        count = 0
        entries = self._store.load_all()
        for artifact in artifacts:
            existing = entries.get(artifact.artifact_id)
            if existing is None:
                entries[artifact.artifact_id] = LifecycleEntry(
                    subject_id=artifact.artifact_id,
                    subject_type=LifecycleSubjectType.CLAUDE_ARTIFACT,
                    subject_path=str(artifact.path),
                    source="inventory_sync",
                    tags=[artifact.artifact_type.value],
                )
                count += 1
            else:
                existing.subject_path = str(artifact.path)
                if artifact.artifact_type.value not in existing.tags:
                    existing.tags.append(artifact.artifact_type.value)
                existing.last_evaluated_at = datetime.now()
        self._store.save_all(entries)
        return count

    def mark_deprecate_candidate(
        self,
        subject_id: str,
        subject_type: LifecycleSubjectType,
        *,
        evidence: HardStandardEvidence,
        rationale: str,
        source: str,
    ) -> LifecycleEntry:
        errors = evidence.validate(subject_type)
        if errors:
            raise ValueError("Hard-standard validation failed: " + "; ".join(errors))

        entries = self._store.load_all()
        entry = entries.get(subject_id)
        if entry is None:
            entry = LifecycleEntry(
                subject_id=subject_id,
                subject_type=subject_type,
            )

        entry.status = LifecycleStatus.DEPRECATE_CANDIDATE
        entry.rationale = rationale
        entry.source = source
        entry.evidence = evidence
        entry.last_evaluated_at = datetime.now()
        entries[subject_id] = entry
        self._store.save_all(entries)
        self._write_transition_report(entry, "deprecate-candidate")
        return entry

    def soft_demote(self, subject_id: str, note: str) -> LifecycleEntry:
        entry = self._require_transition(subject_id, {LifecycleStatus.DEPRECATE_CANDIDATE}, LifecycleStatus.SOFT_DEMOTED)
        entry.notes.append(note)
        self._write_transition_report(entry, "soft-demoted")
        return entry

    def deprecate(self, subject_id: str, note: str) -> LifecycleEntry:
        entry = self._require_transition(subject_id, {LifecycleStatus.SOFT_DEMOTED}, LifecycleStatus.DEPRECATED)
        entry.notes.append(note)
        self._write_transition_report(entry, "deprecated")
        return entry

    def archive(self, subject_id: str, note: str) -> LifecycleEntry:
        entry = self._require_transition(subject_id, {LifecycleStatus.DEPRECATED}, LifecycleStatus.ARCHIVED)
        entry.notes.append(note)
        self._write_transition_report(entry, "archived")
        return entry

    def _require_transition(
        self,
        subject_id: str,
        allowed: set[LifecycleStatus],
        new_status: LifecycleStatus,
    ) -> LifecycleEntry:
        entries = self._store.load_all()
        entry = entries.get(subject_id)
        if entry is None:
            raise KeyError(f"Unknown lifecycle subject: {subject_id}")
        if entry.status not in allowed:
            allowed_names = ", ".join(sorted(item.value for item in allowed))
            raise ValueError(f"{subject_id} must be in [{allowed_names}] before moving to {new_status.value}")
        entry.status = new_status
        entry.last_evaluated_at = datetime.now()
        entries[subject_id] = entry
        self._store.save_all(entries)
        return entry

    def _write_transition_report(self, entry: LifecycleEntry, action: str) -> None:
        if (
            entry.subject_type == LifecycleSubjectType.CLAUDE_ARTIFACT
            and self._claude_manager
            and self._claude_manager.workspace
        ):
            reports_dir = self._claude_manager.ensure_draft_dirs().get("reports")
            if not reports_dir:
                return
            filename = build_draft_filename(entry.subject_id.replace(":", "-"), action)
            report_path = reports_dir / filename
            report_path.write_text(self._render_report(entry, action), encoding="utf-8")
            return

        reports_dir = self._workspace_root / ".openspace" / "lifecycle" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"{datetime.now().strftime('%Y-%m-%d')}-{entry.subject_id.replace(':', '-')}-{action}.md"
        report_path.write_text(self._render_report(entry, action), encoding="utf-8")

    def _render_report(self, entry: LifecycleEntry, action: str) -> str:
        evidence = entry.evidence.to_dict() if entry.evidence else {}
        metrics = "\n".join(
            f"- `{key}`: `{value}`"
            for key, value in evidence.items()
            if value not in (None, "", [])
        ) or "- 无"
        notes = "\n".join(f"- {item}" for item in entry.notes) or "- 无"
        return (
            f"# Lifecycle Transition Draft\n\n"
            f"- 对象: `{entry.subject_id}`\n"
            f"- 类型: `{entry.subject_type.value}`\n"
            f"- 动作: `{action}`\n"
            f"- 当前状态: `{entry.status.value}`\n"
            f"- 来源: `{entry.source}`\n"
            f"- 路径: `{entry.subject_path}`\n"
            f"- 评估时间: `{entry.last_evaluated_at.isoformat()}`\n\n"
            f"## 理由\n\n{entry.rationale or '待补充'}\n\n"
            f"## 硬标准证据\n\n{metrics}\n\n"
            f"## 备注\n\n{notes}\n"
        )
