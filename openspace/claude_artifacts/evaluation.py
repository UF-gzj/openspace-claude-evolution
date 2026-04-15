from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import re

from openspace.skill_engine.skill_utils import parse_frontmatter

from .contracts import ArtifactContract, infer_contract
from .drafts import build_draft_filename
from .types import ClaudeArtifact, ClaudeArtifactType


@dataclass
class ArtifactFinding:
    code: str
    severity: str
    message: str


@dataclass
class ArtifactEvaluation:
    artifact: ClaudeArtifact
    contract: ArtifactContract
    findings: List[ArtifactFinding] = field(default_factory=list)
    summary: str = ""

    @property
    def is_clean(self) -> bool:
        return not self.findings

    @property
    def draft_bucket(self) -> str:
        return self.contract.draft_bucket

    def draft_name(self) -> str:
        rel_name = self.artifact.path.relative_to(self.artifact.workspace_root).as_posix()
        return build_draft_filename(rel_name, "evaluation")


def evaluate_artifact(artifact: ClaudeArtifact) -> ArtifactEvaluation:
    content = artifact.path.read_text(encoding="utf-8")
    contract = infer_contract(artifact)
    findings: List[ArtifactFinding] = []

    if _expects_frontmatter(artifact) and not content.startswith("---"):
        findings.append(
            ArtifactFinding(
                code="missing_frontmatter",
                severity="high",
                message="文件缺少 YAML frontmatter，无法稳定承接结构化路由和演化判断。",
            )
        )

    if _expects_frontmatter(artifact) and content.startswith("---"):
        fm = parse_frontmatter(content)
        if not fm:
            findings.append(
                ArtifactFinding(
                    code="malformed_frontmatter",
                    severity="high",
                    message="frontmatter 看起来存在，但无法稳定解析，建议收紧为简单键值结构。",
                )
            )

    for term in contract.required_terms:
        if term not in content:
            findings.append(
                ArtifactFinding(
                    code=f"missing_term:{term}",
                    severity="medium",
                    message=f"缺少关键契约词 `{term}`，可能导致生成物无法承接上下游命令或知识流转。",
                )
            )

    for heading in contract.required_headings:
        if heading not in content:
            findings.append(
                ArtifactFinding(
                    code=f"missing_heading:{heading}",
                    severity="high",
                    message=f"缺少模板/知识卡片必需结构 `{heading}`。",
                )
            )

    if artifact.artifact_type == ClaudeArtifactType.COMMAND_ALIAS:
        _check_command_alias(content, findings)
    elif artifact.artifact_type == ClaudeArtifactType.COMMAND_WORKFLOW:
        _check_command_workflow(artifact.path.name.lower(), content, findings)
    elif artifact.artifact_type == ClaudeArtifactType.CLAUDE_TEMPLATE:
        _check_template_contract(artifact.path.name.lower(), content, findings)
    elif artifact.artifact_type == ClaudeArtifactType.REFERENCE_INDEX:
        _check_reference_index(content, findings)
    elif artifact.artifact_type == ClaudeArtifactType.REFERENCE_FEEDBACK:
        _check_reference_feedback(content, findings)
    elif artifact.artifact_type == ClaudeArtifactType.REFERENCE_CARD:
        _check_reference_card(content, findings)
    elif artifact.artifact_type == ClaudeArtifactType.CLAUDE_MEMORY:
        _check_memory_contract(artifact.path.name.lower(), content, findings)

    summary = "未发现硬规则漂移。" if not findings else f"发现 {len(findings)} 项需要关注的契约问题。"
    return ArtifactEvaluation(
        artifact=artifact,
        contract=contract,
        findings=findings,
        summary=summary,
    )


def render_evaluation_draft(evaluation: ArtifactEvaluation) -> str:
    artifact = evaluation.artifact
    findings = "\n".join(
        f"- [{finding.severity}] `{finding.code}`: {finding.message}"
        for finding in evaluation.findings
    ) or "- 无"
    producers = "\n".join(f"- {item}" for item in evaluation.contract.producers) or "- 无"
    consumers = "\n".join(f"- {item}" for item in evaluation.contract.consumers) or "- 无"
    required_terms = "\n".join(f"- `{item}`" for item in evaluation.contract.required_terms) or "- 无"
    required_headings = "\n".join(f"- `{item}`" for item in evaluation.contract.required_headings) or "- 无"
    return (
        f"# Claude Artifact Evaluation Draft\n\n"
        f"- 对象: `{artifact.artifact_id}`\n"
        f"- 类型: `{artifact.artifact_type.value}`\n"
        f"- 文件: `{artifact.path}`\n"
        f"- 角色: {evaluation.contract.role}\n"
        f"- 结论: {evaluation.summary}\n\n"
        f"## 上游生产者\n\n{producers}\n\n"
        f"## 下游消费者\n\n{consumers}\n\n"
        f"## 必需契约词\n\n{required_terms}\n\n"
        f"## 必需结构\n\n{required_headings}\n\n"
        f"## 检查结果\n\n{findings}\n"
    )


def _expects_frontmatter(artifact: ClaudeArtifact) -> bool:
    return artifact.artifact_type in {
        ClaudeArtifactType.COMMAND_WORKFLOW,
        ClaudeArtifactType.REFERENCE_CARD,
        ClaudeArtifactType.REFERENCE_INDEX,
        ClaudeArtifactType.REFERENCE_FEEDBACK,
        ClaudeArtifactType.REFERENCE_TEMPLATE,
    }


def _check_command_alias(content: str, findings: List[ArtifactFinding]) -> None:
    lower = content.lower()
    if "alias_for" not in lower and "简写别名" not in content and "short alias" not in lower:
        findings.append(
            ArtifactFinding(
                code="alias_contract_weak",
                severity="medium",
                message="别名命令缺少明确的 alias 说明，后续自动识别正式命令时会不稳定。",
            )
        )


def _check_command_workflow(name: str, content: str, findings: List[ArtifactFinding]) -> None:
    if (
        name != "commit.md"
        and "下一步" not in content
        and "可选下一步" not in content
        and "不会自动执行" not in content
    ):
        findings.append(
            ArtifactFinding(
                code="missing_next_step_contract",
                severity="medium",
                message="命令缺少清晰的下一步承接提示，容易造成流程断裂。",
            )
        )

    if name == "validate.md" and "validation-context.md" not in content:
        findings.append(
            ArtifactFinding(
                code="missing_validation_context_binding",
                severity="high",
                message="`/vald` 没有显式绑定 `validation-context.md`，容易脱离项目真实验证现实。",
            )
        )

    if name in {"execution-report.md", "system-review.md", "iterate.md", "rca.md", "implement-fix.md", "init-project.md"}:
        if "_knowledge-template.md" not in content:
            findings.append(
                ArtifactFinding(
                    code="missing_knowledge_template_binding",
                    severity="high",
                    message="涉及长期知识生成/升级的命令未显式绑定 `_knowledge-template.md`。",
                )
            )

    if name == "prime.md" and "knowledge-index.md" not in content:
        findings.append(
            ArtifactFinding(
                code="missing_knowledge_index_binding",
                severity="high",
                message="`/prim` 缺少对 `knowledge-index.md` 的显式依赖，知识路由会漂移。",
            )
        )


def _check_template_contract(name: str, content: str, findings: List[ArtifactFinding]) -> None:
    if name == "validation-context.template.md":
        has_db_section = "数据库协作验证" in content
        has_read_only_boundary = (
            "只读" in content
            or "只允许 `SELECT`" in content
            or "只允许 `SELECT`、`SHOW`" in content
            or "默认使用边界" in content
        )
        if not has_db_section or not has_read_only_boundary:
            findings.append(
                ArtifactFinding(
                    code="missing_db_validation_contract",
                    severity="high",
                    message="验证上下文模板没有完整承接数据库协作验证契约。",
                )
            )

    if name == "knowledge-index.template.md" and "knowledge-feedback.md" not in content:
        findings.append(
            ArtifactFinding(
                code="missing_feedback_link",
                severity="high",
                message="知识索引模板没有显式承接 knowledge-feedback，后续闭环会断。",
            )
        )


def _check_reference_index(content: str, findings: List[ArtifactFinding]) -> None:
    if "卡片读取规则" in content:
        return

    if (
        ("先看适用边界" in content or "先读适用边界" in content)
        and ("标准做法" in content or "反模式" in content or "误区" in content)
        and "验证" in content
    ):
        return

    if "knowledge-feedback.md" not in content:
        findings.append(
            ArtifactFinding(
                code="missing_feedback_link",
                severity="medium",
                message="knowledge-index 没有显式提到 knowledge-feedback，索引调优闭环不够清晰。",
            )
        )

    findings.append(
        ArtifactFinding(
            code="missing_card_reading_rules",
            severity="medium",
            message="knowledge-index 缺少卡片读取规则，命中后的使用方式不够稳定。",
        )
    )


def _check_reference_feedback(content: str, findings: List[ArtifactFinding]) -> None:
    if "记录模板" in content or "建议模板" in content:
        return

    if (
        ("加载原因" in content or "为什么加载" in content)
        and ("是否真正有帮助" in content or "命中质量" in content)
        and ("调整动作" in content or "调整建议" in content or "是否需要调整索引" in content)
    ):
        return

        findings.append(
            ArtifactFinding(
                code="missing_feedback_template",
                severity="medium",
                message="knowledge-feedback 缺少统一记录模板，反馈字段容易漂移。",
            )
        )


def _check_reference_card(content: str, findings: List[ArtifactFinding]) -> None:
    # Existing reference cards in mature `.claude` workspaces often keep
    # project-specific section titles instead of mirroring the template
    # headings verbatim. We only flag cards that are truly under-structured.
    h2_headings = re.findall(r"^##\s+.+$", content, flags=re.MULTILINE)
    numbered_h2 = re.findall(r"^##\s+\d+[\.\u3001]\s*.+$", content, flags=re.MULTILINE)
    has_frontmatter = content.startswith("---")
    has_verification = "验证" in content
    has_antipattern = "反模式" in content or "误区" in content

    if not has_frontmatter:
        findings.append(
            ArtifactFinding(
                code="missing_frontmatter",
                severity="high",
                message="文件缺少 YAML frontmatter，无法稳定承接结构化路由和演化判断。",
            )
        )
        return

    if len(h2_headings) >= 6:
        return

    if len(h2_headings) >= 4 and (has_verification or has_antipattern or len(numbered_h2) >= 3):
        return

    findings.append(
        ArtifactFinding(
            code="reference_card_structure_weak",
            severity="medium",
            message="知识卡片结构偏弱，建议参考 `_knowledge-template.md` 补齐边界、做法、验证等关键段落，但应保持当前项目文风，不要机械改写为模板标题。",
        )
    )


def _check_memory_contract(name: str, content: str, findings: List[ArtifactFinding]) -> None:
    if name == "prime-context.md" and "validation-context.md" not in content:
        findings.append(
            ArtifactFinding(
                code="missing_validation_routing_hint",
                severity="medium",
                message="prime-context 没有提示何时转向 validation-context，首轮路由可能过慢。",
            )
        )

    if name == "validation-context.md" and "数据库协作验证" not in content:
        findings.append(
            ArtifactFinding(
                code="missing_db_validation_section",
                severity="high",
                message="validation-context 缺少数据库协作验证章节，难以支撑真实查库验证。",
            )
        )
