from .contracts import ArtifactContract, infer_contract
from .types import ClaudeArtifact, ClaudeArtifactType, ClaudeLifecycleStatus
from .detector import ClaudeWorkspace, detect_claude_workspace
from .drafts import DEFAULT_DRAFT_SUBDIRS, build_draft_filename, ensure_evolution_draft_dirs
from .patch_drafts import ArtifactPatchDraft, PatchDraftBlock, build_patch_draft, render_patch_draft
from .evaluation import ArtifactEvaluation, ArtifactFinding, evaluate_artifact, render_evaluation_draft
from .patch_plans import ArtifactPatchPlan, PatchStep, build_patch_plan, render_patch_plan_draft
from .proposals import ArtifactProposal, ProposalAction, build_proposal, render_proposal_draft
from .manager import ClaudeArtifactManager

__all__ = [
    "ArtifactContract",
    "ArtifactPatchDraft",
    "ArtifactEvaluation",
    "ArtifactFinding",
    "ArtifactPatchPlan",
    "ArtifactProposal",
    "ClaudeArtifact",
    "ClaudeArtifactType",
    "ClaudeLifecycleStatus",
    "ClaudeWorkspace",
    "PatchDraftBlock",
    "PatchStep",
    "ProposalAction",
    "detect_claude_workspace",
    "DEFAULT_DRAFT_SUBDIRS",
    "build_draft_filename",
    "ensure_evolution_draft_dirs",
    "infer_contract",
    "evaluate_artifact",
    "build_patch_draft",
    "build_patch_plan",
    "build_proposal",
    "render_patch_draft",
    "render_evaluation_draft",
    "render_patch_plan_draft",
    "render_proposal_draft",
    "ClaudeArtifactManager",
]
