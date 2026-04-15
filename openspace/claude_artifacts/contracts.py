from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .types import ClaudeArtifact, ClaudeArtifactType


@dataclass
class ArtifactContract:
    role: str
    producers: List[str] = field(default_factory=list)
    consumers: List[str] = field(default_factory=list)
    required_terms: List[str] = field(default_factory=list)
    required_headings: List[str] = field(default_factory=list)
    draft_bucket: str = "reports"


def infer_contract(artifact: ClaudeArtifact) -> ArtifactContract:
    name = artifact.path.name.lower()

    if artifact.artifact_type == ClaudeArtifactType.COMMAND_ALIAS:
        return ArtifactContract(
            role="short command alias for manual entry",
            consumers=["human operator"],
            required_terms=["/"],
            draft_bucket="commands",
        )

    if artifact.artifact_type == ClaudeArtifactType.COMMAND_WORKFLOW:
        by_name = {
            "prime.md": ArtifactContract(
                role="low-noise first-read router",
                producers=["user task intake"],
                consumers=["/pln", "/bref", "manual execution"],
                draft_bucket="commands",
            ),
            "plan.md": ArtifactContract(
                role="implementation planning workflow",
                producers=["/prim", "/bref"],
                consumers=["/exec"],
                draft_bucket="commands",
            ),
            "backend-review-plan.md": ArtifactContract(
                role="backend review gate before planning",
                producers=["/prim"],
                consumers=["/pln"],
                draft_bucket="commands",
            ),
            "execute.md": ArtifactContract(
                role="implementation execution workflow",
                producers=["/pln"],
                consumers=["/vald", "/revu", "/xrep"],
                draft_bucket="commands",
            ),
            "validate.md": ArtifactContract(
                role="validation workflow bound to validation context",
                producers=["/exec", "/fix", "/iter"],
                consumers=["/revu", "/iter", "/xrep"],
                draft_bucket="commands",
            ),
            "review.md": ArtifactContract(
                role="review workflow after validation",
                producers=["/vald"],
                consumers=["/iter", "/xrep"],
                draft_bucket="commands",
            ),
            "execution-report.md": ArtifactContract(
                role="execution feedback and candidate knowledge routing",
                producers=["/vald", "/revu", "/fix"],
                consumers=["/srev", "/cmit"],
                draft_bucket="commands",
            ),
            "system-review.md": ArtifactContract(
                role="system-level knowledge routing decision",
                producers=["/xrep"],
                consumers=["/cmit", "formal knowledge updates"],
                draft_bucket="commands",
            ),
            "iterate.md": ArtifactContract(
                role="iteration decision workflow for failed or partial validation",
                producers=["/vald", "/revu"],
                consumers=["/exec", "/xrep", "/srev"],
                draft_bucket="commands",
            ),
            "rca.md": ArtifactContract(
                role="bug root-cause workflow",
                producers=["bug report"],
                consumers=["/fix", "/bref", "/xrep"],
                draft_bucket="commands",
            ),
            "implement-fix.md": ArtifactContract(
                role="bugfix execution workflow",
                producers=["/rca"],
                consumers=["/vald", "/xrep", "/srev"],
                draft_bucket="commands",
            ),
            "commit.md": ArtifactContract(
                role="commit gate with knowledge backfill checks",
                producers=["/xrep", "/srev", "manual final review"],
                consumers=["git commit", "manual submission"],
                draft_bucket="commands",
            ),
            "init-project.md": ArtifactContract(
                role="project bootstrap workflow",
                producers=["new project", "mature project refresh"],
                consumers=["formal memories", "reference cards"],
                draft_bucket="commands",
            ),
            "refresh-project-context.md": ArtifactContract(
                role="project context refresh workflow",
                producers=["mature project scan"],
                consumers=["formal memories", "bootstrap drafts"],
                draft_bucket="commands",
            ),
        }
        return by_name.get(
            name,
            ArtifactContract(
                role="workflow command",
                consumers=["manual execution"],
                required_terms=["下一步"],
                draft_bucket="commands",
            ),
        )

    if artifact.artifact_type == ClaudeArtifactType.CLAUDE_TEMPLATE:
        by_name = {
            "claude.template.md": ArtifactContract(
                role="template for high-frequency stable project rules",
                producers=["/pinit", "/refr"],
                consumers=["/prim", "/pln", "/exec"],
                draft_bucket="templates",
            ),
            "prd.template.md": ArtifactContract(
                role="template for business and module map",
                producers=["/pinit", "/refr"],
                consumers=["/prim", "/pln"],
                draft_bucket="templates",
            ),
            "prime-context.template.md": ArtifactContract(
                role="template for low-noise prime routing context",
                producers=["/pinit", "/refr"],
                consumers=["/prim"],
                draft_bucket="templates",
            ),
            "validation-context.template.md": ArtifactContract(
                role="template for validation reality and database collaboration",
                producers=["/pinit", "/refr"],
                consumers=["/vald", "/pln", "/bref"],
                draft_bucket="templates",
            ),
            "knowledge-index.template.md": ArtifactContract(
                role="template for knowledge routing index",
                producers=["/pinit", "/refr"],
                consumers=["/prim", "/vald", "/revu"],
                draft_bucket="templates",
            ),
            "knowledge-feedback.template.md": ArtifactContract(
                role="template for feedback and knowledge promotion loop",
                producers=["/xrep", "/srev"],
                consumers=["knowledge-index.md", "reference cards"],
                draft_bucket="templates",
            ),
        }
        return by_name.get(
            name,
            ArtifactContract(
                role="template artifact",
                producers=["/pinit", "/refr"],
                consumers=["generated formal markdown"],
                draft_bucket="templates",
            ),
        )

    if artifact.artifact_type == ClaudeArtifactType.REFERENCE_CARD:
        return ArtifactContract(
            role="long-term reusable knowledge card",
            producers=["/xrep", "/srev", "/pinit"],
            consumers=["/prim", "/vald", "/revu"],
            draft_bucket="reference",
        )

    if artifact.artifact_type == ClaudeArtifactType.REFERENCE_INDEX:
        return ArtifactContract(
            role="reference routing index",
            producers=["/pinit", "/srev"],
            consumers=["/prim", "/vald", "/revu"],
            draft_bucket="reference",
        )

    if artifact.artifact_type == ClaudeArtifactType.REFERENCE_FEEDBACK:
        return ArtifactContract(
            role="feedback ledger for knowledge usefulness",
            producers=["/xrep", "/srev"],
            consumers=["knowledge-index.md", "reference cards"],
            draft_bucket="reference",
        )

    if artifact.artifact_type == ClaudeArtifactType.REFERENCE_TEMPLATE:
        return ArtifactContract(
            role="reference card generation template",
            producers=["/pinit", "/srev"],
            consumers=["reference_card generation"],
            required_headings=[
                "## 1. 问题 / 背景",
                "## 2. 适用边界",
                "## 3. 标准做法",
                "## 4. 反模式",
                "## 5. 验证方式",
                "## 6. 关联文档",
                "## 7. 变更记录",
            ],
            draft_bucket="reference",
        )

    if artifact.artifact_type == ClaudeArtifactType.CLAUDE_MEMORY:
        by_name = {
            "claude.md": ArtifactContract(
                role="high-frequency stable rules and anti-drift guardrails",
                producers=["/pinit", "/refr", "/srev"],
                consumers=["/prim", "/pln", "/exec"],
                draft_bucket="memory",
            ),
            "prd.md": ArtifactContract(
                role="business and module map",
                producers=["/pinit", "/refr"],
                consumers=["/prim", "/pln"],
                draft_bucket="memory",
            ),
            "prime-context.md": ArtifactContract(
                role="low-noise prime routing memory",
                producers=["/pinit", "/refr"],
                consumers=["/prim"],
                draft_bucket="memory",
            ),
            "validation-context.md": ArtifactContract(
                role="validation reality and database collaboration memory",
                producers=["/pinit", "/refr"],
                consumers=["/vald", "/pln", "/bref"],
                draft_bucket="memory",
            ),
        }
        return by_name.get(
            name,
            ArtifactContract(
                role="formal project memory",
                producers=["/pinit", "/refr"],
                consumers=["manual routing"],
                draft_bucket="memory",
            ),
        )

    return ArtifactContract(role="unknown artifact")
