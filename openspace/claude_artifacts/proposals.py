from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .drafts import build_draft_filename
from .evaluation import ArtifactEvaluation, ArtifactFinding


@dataclass
class ProposalAction:
    title: str
    rationale: str
    target_area: str
    suggested_change: str


@dataclass
class ArtifactProposal:
    evaluation: ArtifactEvaluation
    actions: List[ProposalAction] = field(default_factory=list)
    summary: str = ""

    @property
    def artifact(self):
        return self.evaluation.artifact

    @property
    def draft_bucket(self) -> str:
        return self.evaluation.contract.draft_bucket

    def draft_name(self) -> str:
        rel_name = self.artifact.path.relative_to(self.artifact.workspace_root).as_posix()
        return build_draft_filename(rel_name, "proposal")


def build_proposal(evaluation: ArtifactEvaluation) -> ArtifactProposal:
    actions = [_proposal_for_finding(finding, evaluation) for finding in evaluation.findings]
    actions = [item for item in actions if item is not None]
    summary = "未生成修复提案，当前契约检查通过。" if not actions else f"生成 {len(actions)} 条可审阅修复提案。"
    return ArtifactProposal(
        evaluation=evaluation,
        actions=actions,
        summary=summary,
    )


def render_proposal_draft(proposal: ArtifactProposal) -> str:
    artifact = proposal.artifact
    actions = "\n".join(
        _render_action(index, action)
        for index, action in enumerate(proposal.actions, start=1)
    ) or "1. 暂无提案，维持现状。"
    return (
        f"# Claude Artifact Proposal Draft\n\n"
        f"- 对象: `{artifact.artifact_id}`\n"
        f"- 类型: `{artifact.artifact_type.value}`\n"
        f"- 文件: `{artifact.path}`\n"
        f"- 结论: {proposal.summary}\n"
        f"- 契约角色: {proposal.evaluation.contract.role}\n\n"
        f"## 修复提案\n\n{actions}\n"
    )


def _render_action(index: int, action: ProposalAction) -> str:
    return (
        f"{index}. {action.title}\n"
        f"目标区域：`{action.target_area}`\n"
        f"原因：{action.rationale}\n"
        f"建议变更：{action.suggested_change}\n"
    )


def _proposal_for_finding(
    finding: ArtifactFinding,
    evaluation: ArtifactEvaluation,
) -> ProposalAction | None:
    artifact_name = evaluation.artifact.path.name

    if finding.code == "missing_frontmatter":
        return ProposalAction(
            title="补齐 frontmatter",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="为该文件增加最小可解析的 YAML frontmatter，并只保留稳定键值，避免复杂嵌套结构。",
        )

    if finding.code == "malformed_frontmatter":
        return ProposalAction(
            title="收紧 frontmatter 结构",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="把 frontmatter 收敛为简单键值对，去掉难以稳定解析的复杂 YAML 写法。",
        )

    if finding.code.startswith("missing_term:"):
        term = finding.code.split(":", 1)[1]
        return ProposalAction(
            title=f"补充关键契约词 `{term}`",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change=f"在保持低噪音的前提下，把 `{term}` 明确写回正文，使上下游命令或知识流转关系可见。",
        )

    if finding.code.startswith("missing_heading:"):
        heading = finding.code.split(":", 1)[1]
        return ProposalAction(
            title=f"补齐结构段落 `{heading}`",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="按当前正式模板补齐缺失段落，不要只在文末追加零散说明。",
        )

    mapping = {
        "alias_contract_weak": ProposalAction(
            title="明确别名映射",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="在别名命令里加入正式命令映射说明，例如 alias_for 或等价中文说明，避免别名解析漂移。",
        ),
        "missing_next_step_contract": ProposalAction(
            title="补清下一步承接",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="补一段清晰的下一步决策说明，并强调“不会自动执行”，避免流程断裂。",
        ),
        "missing_validation_context_binding": ProposalAction(
            title="绑定 validation-context",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="在 `/vald` 相关正文里显式要求优先读取 `validation-context.md`，并用其作为验证现实来源。",
        ),
        "missing_knowledge_template_binding": ProposalAction(
            title="绑定 _knowledge-template",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="对新增或升级 `reference/*.md` 的动作，显式要求遵循 `_knowledge-template.md` 的完整结构。",
        ),
        "missing_knowledge_index_binding": ProposalAction(
            title="绑定 knowledge-index",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="在 `/prim` 路由说明里显式引用 `knowledge-index.md`，并保持首轮 1-3 篇的低噪音规则。",
        ),
        "missing_db_validation_contract": ProposalAction(
            title="补数据库协作验证契约",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="在模板中加入数据库协作验证章节，明确默认只读、真实命令来源和 `/vald` 承接关系。",
        ),
        "missing_feedback_link": ProposalAction(
            title="补 feedback 闭环链接",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="在知识索引模板中显式写出 `knowledge-feedback.md` 的作用和使用入口，避免索引与反馈脱节。",
        ),
        "missing_card_reading_rules": ProposalAction(
            title="补卡片读取规则",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="在 knowledge-index 中增加命中后如何阅读卡片的规则，强调先边界、再做法、后验证。",
        ),
        "missing_feedback_template": ProposalAction(
            title="统一 feedback 模板",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="为 knowledge-feedback 增加固定记录模板，至少包含加载原因、帮助程度、调整动作、下次建议。",
        ),
        "reference_card_structure_weak": ProposalAction(
            title="按现有文风补强知识卡片结构",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="参考 `_knowledge-template.md` 补齐边界、标准做法、反模式、验证方式等信息，但沿用当前卡片的章节命名和叙述风格，不要机械重写成模板标题。",
        ),
        "missing_validation_routing_hint": ProposalAction(
            title="补 prime 到 validation 的转向提示",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="在 prime-context 中补一句：遇到真实验证、数据库核对或环境事实时，转向 validation-context。",
        ),
        "missing_db_validation_section": ProposalAction(
            title="补数据库协作验证章节",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="在 validation-context 中增加数据库协作验证章节，明确连接信息来源、只读边界和适用场景。",
        ),
        "missing_project_module_routing": ProposalAction(
            title="补项目主链路事实",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="根据当前项目真实模块/目录，把主链路入口写进 prime-context，而不是只保留抽象描述。",
        ),
        "test_reality_mismatch": ProposalAction(
            title="修正测试现实",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="把 validation-context 改成“先编译/烟测，只有真实测试资产存在时再跑测试命令”，避免默认承诺不存在的测试能力。",
        ),
        "template_missing_project_fact_slots": ProposalAction(
            title="补项目事实槽位",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="在 prime-context 模板里补“关键目录 / 常见任务入口”等槽位，让生成后的正式文件能承接项目主链路。",
        ),
        "template_test_placeholder_too_strong": ProposalAction(
            title="弱化测试占位符假设",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="把 validation-context 模板里的测试命令占位改成“无/待确认/仅当真实测试资产存在时填写”，降低生成假测试命令的风险。",
        ),
        "validate_command_test_reality_mismatch": ProposalAction(
            title="校正 validate 的测试语气",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="把 validate 命令里的测试建议改成条件化表述，明确是否存在真实测试资产必须先由项目事实确认。",
        ),
        "missing_bootstrap_config_fact": ProposalAction(
            title="补配置事实入口",
            rationale=finding.message,
            target_area=artifact_name,
            suggested_change="在 validation-context 中显式写出 `bootstrap.yml` 或等价配置入口，避免验证时漏掉真实配置链路。",
        ),
    }
    return mapping.get(finding.code)
