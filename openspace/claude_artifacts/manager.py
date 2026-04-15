from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from openspace.utils.logging import Logger
from openspace.skill_engine.skill_utils import parse_frontmatter

from .contracts import infer_contract
from .detector import ClaudeWorkspace, detect_claude_workspace
from .drafts import ensure_evolution_draft_dirs
from .patch_drafts import ArtifactPatchDraft, build_patch_draft, render_patch_draft
from .evaluation import ArtifactEvaluation, evaluate_artifact, render_evaluation_draft
from .patch_plans import ArtifactPatchPlan, build_patch_plan, render_patch_plan_draft
from .proposals import ArtifactProposal, build_proposal, render_proposal_draft
from .types import ClaudeArtifact, ClaudeArtifactType

logger = Logger.get_logger(__name__)


class ClaudeArtifactManager:
    """Sidecar manager for `.claude` workspaces.

    This manager intentionally avoids interfering with the native skill engine.
    It only detects `.claude` artifacts, prepares draft directories, and
    exposes a typed inventory for future evaluators and lifecycle managers.
    """

    def __init__(self, workspace_root: Optional[str | Path]) -> None:
        self._workspace: Optional[ClaudeWorkspace] = detect_claude_workspace(workspace_root)

    @property
    def workspace(self) -> Optional[ClaudeWorkspace]:
        return self._workspace

    def is_enabled(self) -> bool:
        return self._workspace is not None

    def ensure_draft_dirs(self) -> dict[str, Path]:
        if not self._workspace:
            return {}
        created = ensure_evolution_draft_dirs(self._workspace.evolution_drafts_dir)
        logger.info("Ensured .claude evolution draft dirs under %s", self._workspace.evolution_drafts_dir)
        return created

    def discover_artifacts(self) -> List[ClaudeArtifact]:
        if not self._workspace:
            return []

        ws = self._workspace
        artifacts: List[ClaudeArtifact] = []
        artifacts.extend(self._scan_commands(ws))
        artifacts.extend(self._scan_templates(ws))
        artifacts.extend(self._scan_reference(ws))
        artifacts.extend(self._scan_memory(ws))
        return artifacts

    def _scan_commands(self, ws: ClaudeWorkspace) -> List[ClaudeArtifact]:
        if not ws.commands_dir.is_dir():
            return []
        artifacts: List[ClaudeArtifact] = []
        for path in ws.commands_dir.rglob("*.md"):
            rel = path.relative_to(ws.claude_dir).as_posix()
            artifact_type = self._infer_command_artifact_type(path, ws)
            artifacts.append(
                self._decorate_artifact(
                    ClaudeArtifact(
                    artifact_id=f"claude:{artifact_type.value}:{rel}",
                    artifact_type=artifact_type,
                    path=path,
                    workspace_root=ws.workspace_root,
                    )
                )
            )
        return artifacts

    def _infer_command_artifact_type(self, path: Path, ws: ClaudeWorkspace) -> ClaudeArtifactType:
        if path.parent != ws.commands_dir:
            return ClaudeArtifactType.COMMAND_WORKFLOW

        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return ClaudeArtifactType.COMMAND_WORKFLOW

        lower = content.lower()
        frontmatter = parse_frontmatter(content) if content.startswith("---") else None
        if isinstance(frontmatter, dict) and frontmatter.get("alias_for"):
            return ClaudeArtifactType.COMMAND_ALIAS

        if "短命令别名" in content or "简写别名" in content or "short alias" in lower:
            return ClaudeArtifactType.COMMAND_ALIAS

        return ClaudeArtifactType.COMMAND_WORKFLOW

    def _scan_templates(self, ws: ClaudeWorkspace) -> List[ClaudeArtifact]:
        if not ws.templates_dir.is_dir():
            return []
        artifacts: List[ClaudeArtifact] = []
        for path in ws.templates_dir.glob("*.md"):
            rel = path.relative_to(ws.claude_dir).as_posix()
            artifacts.append(
                self._decorate_artifact(
                    ClaudeArtifact(
                    artifact_id=f"claude:{ClaudeArtifactType.CLAUDE_TEMPLATE.value}:{rel}",
                    artifact_type=ClaudeArtifactType.CLAUDE_TEMPLATE,
                    path=path,
                    workspace_root=ws.workspace_root,
                    )
                )
            )
        return artifacts

    def _scan_reference(self, ws: ClaudeWorkspace) -> List[ClaudeArtifact]:
        if not ws.reference_dir.is_dir():
            return []
        artifacts: List[ClaudeArtifact] = []
        for path in ws.reference_dir.glob("*.md"):
            rel = path.relative_to(ws.claude_dir).as_posix()
            if path.name == "knowledge-index.md":
                artifact_type = ClaudeArtifactType.REFERENCE_INDEX
            elif path.name == "knowledge-feedback.md":
                artifact_type = ClaudeArtifactType.REFERENCE_FEEDBACK
            elif path.name == "_knowledge-template.md":
                artifact_type = ClaudeArtifactType.REFERENCE_TEMPLATE
            else:
                artifact_type = ClaudeArtifactType.REFERENCE_CARD
            artifacts.append(
                self._decorate_artifact(
                    ClaudeArtifact(
                    artifact_id=f"claude:{artifact_type.value}:{rel}",
                    artifact_type=artifact_type,
                    path=path,
                    workspace_root=ws.workspace_root,
                    )
                )
            )
        return artifacts

    def _scan_memory(self, ws: ClaudeWorkspace) -> List[ClaudeArtifact]:
        artifacts: List[ClaudeArtifact] = []
        for name in ("CLAUDE.md", "PRD.md", "prime-context.md", "validation-context.md"):
            path = ws.claude_dir / name
            if not path.is_file():
                continue
            rel = path.relative_to(ws.claude_dir).as_posix()
            artifacts.append(
                self._decorate_artifact(
                    ClaudeArtifact(
                    artifact_id=f"claude:{ClaudeArtifactType.CLAUDE_MEMORY.value}:{rel}",
                    artifact_type=ClaudeArtifactType.CLAUDE_MEMORY,
                    path=path,
                    workspace_root=ws.workspace_root,
                    )
                )
            )
        return artifacts

    def evaluate_artifacts(self, artifacts: Optional[List[ClaudeArtifact]] = None) -> List[ArtifactEvaluation]:
        targets = artifacts or self.discover_artifacts()
        return [evaluate_artifact(item) for item in targets]

    def write_evaluation_drafts(
        self,
        evaluations: Optional[List[ArtifactEvaluation]] = None,
        *,
        clean_only: bool = False,
    ) -> List[Path]:
        if not self._workspace:
            return []

        created_dirs = self.ensure_draft_dirs()
        results: List[Path] = []
        for evaluation in evaluations or self.evaluate_artifacts():
            if clean_only and not evaluation.is_clean:
                continue
            bucket = created_dirs.get(evaluation.draft_bucket)
            if not bucket:
                continue
            draft_path = bucket / evaluation.draft_name()
            draft_path.write_text(render_evaluation_draft(evaluation), encoding="utf-8")
            results.append(draft_path)
        return results

    def build_proposals(
        self,
        evaluations: Optional[List[ArtifactEvaluation]] = None,
    ) -> List[ArtifactProposal]:
        return [build_proposal(item) for item in (evaluations or self.evaluate_artifacts())]

    def write_proposal_drafts(
        self,
        proposals: Optional[List[ArtifactProposal]] = None,
        *,
        actionable_only: bool = True,
    ) -> List[Path]:
        if not self._workspace:
            return []

        created_dirs = self.ensure_draft_dirs()
        results: List[Path] = []
        for proposal in proposals or self.build_proposals():
            if actionable_only and not proposal.actions:
                continue
            bucket = created_dirs.get(proposal.draft_bucket)
            if not bucket:
                continue
            draft_path = bucket / proposal.draft_name()
            draft_path.write_text(render_proposal_draft(proposal), encoding="utf-8")
            results.append(draft_path)
        return results

    def build_patch_plans(
        self,
        proposals: Optional[List[ArtifactProposal]] = None,
    ) -> List[ArtifactPatchPlan]:
        return [build_patch_plan(item) for item in (proposals or self.build_proposals())]

    def write_patch_plan_drafts(
        self,
        patch_plans: Optional[List[ArtifactPatchPlan]] = None,
        *,
        actionable_only: bool = True,
    ) -> List[Path]:
        if not self._workspace:
            return []

        created_dirs = self.ensure_draft_dirs()
        results: List[Path] = []
        for plan in patch_plans or self.build_patch_plans():
            if actionable_only and not plan.steps:
                continue
            bucket = created_dirs.get(plan.draft_bucket)
            if not bucket:
                continue
            draft_path = bucket / plan.draft_name()
            draft_path.write_text(render_patch_plan_draft(plan), encoding="utf-8")
            results.append(draft_path)
        return results

    def build_patch_drafts(
        self,
        patch_plans: Optional[List[ArtifactPatchPlan]] = None,
    ) -> List[ArtifactPatchDraft]:
        return [build_patch_draft(item) for item in (patch_plans or self.build_patch_plans())]

    def write_patch_drafts(
        self,
        patch_drafts: Optional[List[ArtifactPatchDraft]] = None,
        *,
        actionable_only: bool = True,
    ) -> List[Path]:
        if not self._workspace:
            return []

        created_dirs = self.ensure_draft_dirs()
        results: List[Path] = []
        for draft in patch_drafts or self.build_patch_drafts():
            if actionable_only and not draft.blocks:
                continue
            bucket = created_dirs.get(draft.draft_bucket)
            if not bucket:
                continue
            draft_path = bucket / draft.draft_name()
            draft_path.write_text(render_patch_draft(draft), encoding="utf-8")
            results.append(draft_path)
        return results

    def _decorate_artifact(self, artifact: ClaudeArtifact) -> ClaudeArtifact:
        contract = infer_contract(artifact)
        artifact.consumers = list(contract.consumers)
        artifact.producers = list(contract.producers)
        artifact.notes = contract.role
        artifact.project_name = artifact.workspace_root.name
        return artifact
