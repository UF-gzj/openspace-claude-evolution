from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .drafts import build_draft_filename
from .patch_plans import ArtifactPatchPlan, PatchStep


@dataclass
class PatchDraftBlock:
    step: PatchStep
    current_excerpt: str
    proposed_excerpt: str


@dataclass
class ArtifactPatchDraft:
    patch_plan: ArtifactPatchPlan
    blocks: List[PatchDraftBlock] = field(default_factory=list)
    summary: str = ""

    @property
    def artifact(self):
        return self.patch_plan.artifact

    @property
    def draft_bucket(self) -> str:
        return self.patch_plan.draft_bucket

    def draft_name(self) -> str:
        rel_name = self.artifact.path.relative_to(self.artifact.workspace_root).as_posix()
        return build_draft_filename(rel_name, "patch-draft")


def build_patch_draft(plan: ArtifactPatchPlan) -> ArtifactPatchDraft:
    content = plan.artifact.path.read_text(encoding="utf-8")
    blocks = [
        PatchDraftBlock(
            step=step,
            current_excerpt=_extract_current_excerpt(content, step),
            proposed_excerpt=_build_proposed_excerpt(content, step),
        )
        for step in plan.steps
    ]
    summary = "未生成 patch draft，当前没有可执行 patch step。" if not blocks else f"生成 {len(blocks)} 段可审阅 patch draft。"
    return ArtifactPatchDraft(
        patch_plan=plan,
        blocks=blocks,
        summary=summary,
    )


def render_patch_draft(draft: ArtifactPatchDraft) -> str:
    artifact = draft.artifact
    blocks = "\n".join(_render_block(index, block) for index, block in enumerate(draft.blocks, start=1)) or "1. 暂无 patch draft。"
    return (
        f"# Claude Artifact Patch Draft\n\n"
        f"- 对象: `{artifact.artifact_id}`\n"
        f"- 类型: `{artifact.artifact_type.value}`\n"
        f"- 文件: `{artifact.path}`\n"
        f"- 结论: {draft.summary}\n\n"
        f"## Draft Blocks\n\n{blocks}\n"
    )


def _render_block(index: int, block: PatchDraftBlock) -> str:
    return (
        f"{index}. 操作：`{block.step.operation}`\n"
        f"目标区域：`{block.step.target_area}`\n"
        f"执行说明：{block.step.instruction}\n"
        f"锚点建议：`{block.step.anchor_hint or '按最接近职责段落插入'}`\n"
        f"当前片段：\n```md\n{block.current_excerpt}\n```\n"
        f"建议草稿：\n```md\n{block.proposed_excerpt}\n```\n"
    )


def _extract_current_excerpt(content: str, step: PatchStep) -> str:
    anchor = step.anchor_hint or ""
    anchor_token = _best_anchor_token(anchor, step)
    if anchor_token:
        idx = content.find(anchor_token)
        if idx >= 0:
            start = max(0, idx - 120)
            end = min(len(content), idx + max(len(anchor_token), 80))
            return content[start:end].strip()

    if step.operation == "rewrite_frontmatter":
        lines = content.splitlines()
        return "\n".join(lines[: min(12, len(lines))]).strip()

    return "\n".join(content.splitlines()[: min(20, len(content.splitlines()))]).strip()


def _build_proposed_excerpt(content: str, step: PatchStep) -> str:
    if step.operation == "rewrite_frontmatter":
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) == 3:
                body = parts[2].lstrip("\r\n")
        return f"{step.sample_text}\n{body[:240].rstrip()}".strip()

    if step.operation == "insert_heading_block":
        return step.sample_text

    if step.operation == "add_next_step_contract":
        return step.sample_text

    return step.sample_text or step.instruction


def _best_anchor_token(anchor_hint: str, step: PatchStep) -> str:
    candidates = [
        token.strip("` ")
        for token in [anchor_hint, step.target_area, step.sample_text]
        if token
    ]
    for candidate in candidates:
        if candidate and len(candidate) <= 40 and "\n" not in candidate:
            return candidate
    return ""
