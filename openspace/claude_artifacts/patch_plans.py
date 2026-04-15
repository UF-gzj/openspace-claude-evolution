from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .drafts import build_draft_filename
from .proposals import ArtifactProposal, ProposalAction


@dataclass
class PatchStep:
    operation: str
    target_area: str
    instruction: str
    anchor_hint: str = ""
    sample_text: str = ""


@dataclass
class ArtifactPatchPlan:
    proposal: ArtifactProposal
    steps: List[PatchStep] = field(default_factory=list)
    summary: str = ""

    @property
    def artifact(self):
        return self.proposal.artifact

    @property
    def draft_bucket(self) -> str:
        return self.proposal.draft_bucket

    def draft_name(self) -> str:
        rel_name = self.artifact.path.relative_to(self.artifact.workspace_root).as_posix()
        return build_draft_filename(rel_name, "patch-plan")


def build_patch_plan(proposal: ArtifactProposal) -> ArtifactPatchPlan:
    steps = [_step_for_action(action, proposal) for action in proposal.actions]
    steps = [item for item in steps if item is not None]
    summary = "未生成 patch plan，当前没有需要落草稿的修复动作。" if not steps else f"生成 {len(steps)} 条结构化 patch step。"
    return ArtifactPatchPlan(
        proposal=proposal,
        steps=steps,
        summary=summary,
    )


def render_patch_plan_draft(plan: ArtifactPatchPlan) -> str:
    artifact = plan.artifact
    steps = "\n".join(_render_step(index, step) for index, step in enumerate(plan.steps, start=1)) or "1. 暂无 patch step。"
    return (
        f"# Claude Artifact Patch Plan Draft\n\n"
        f"- 对象: `{artifact.artifact_id}`\n"
        f"- 类型: `{artifact.artifact_type.value}`\n"
        f"- 文件: `{artifact.path}`\n"
        f"- 结论: {plan.summary}\n\n"
        f"## Patch Steps\n\n{steps}\n"
    )


def _render_step(index: int, step: PatchStep) -> str:
    lines = [
        f"{index}. 操作：`{step.operation}`",
        f"目标区域：`{step.target_area}`",
        f"执行说明：{step.instruction}",
    ]
    if step.anchor_hint:
        lines.append(f"锚点建议：`{step.anchor_hint}`")
    if step.sample_text:
        lines.append("建议样例：")
        lines.append("```md")
        lines.append(step.sample_text)
        lines.append("```")
    return "\n".join(lines) + "\n"


def _step_for_action(action: ProposalAction, proposal: ArtifactProposal) -> PatchStep | None:
    title = action.title
    artifact_name = proposal.artifact.path.name

    if "frontmatter" in title:
        return PatchStep(
            operation="rewrite_frontmatter",
            target_area=artifact_name,
            instruction="补充或重写 YAML frontmatter，保留简单键值结构，不引入复杂列表或嵌套。",
            anchor_hint="文件开头的 `--- ... ---` 区块",
            sample_text="---\ndescription: 简要说明\n---",
        )

    if "关键契约词" in title:
        term = _extract_backtick(action.title)
        return PatchStep(
            operation="insert_contract_term",
            target_area=artifact_name,
            instruction=f"在最相关的职责段落中显式写入 `{term}`，确保上下游承接关系可见。",
            anchor_hint="优先放在“适用场景 / 下一步 / 读取规则 / 绑定关系”附近",
            sample_text=f"- 需要时显式读取 `{term}`",
        )

    if "结构段落" in title:
        heading = _extract_backtick(action.title)
        return PatchStep(
            operation="insert_heading_block",
            target_area=artifact_name,
            instruction=f"补齐缺失的标准段落 `{heading}`，并在该段下填入最小必要内容。",
            anchor_hint="按模板顺序插入，不要堆到文末",
            sample_text=f"{heading}\n待补充",
        )

    mapping = {
        "明确别名映射": PatchStep(
            operation="clarify_alias_mapping",
            target_area=artifact_name,
            instruction="补充别名到正式命令的显式映射说明，避免后续自动识别不稳定。",
            anchor_hint="frontmatter 或正文开头的简介段",
            sample_text="alias_for: /prim",
        ),
        "补清下一步承接": PatchStep(
            operation="add_next_step_contract",
            target_area=artifact_name,
            instruction="新增一段固定的下一步决策说明，并强调不会自动执行。",
            anchor_hint="正文末尾的流程收口位置",
            sample_text=_next_step_sample(artifact_name),
        ),
        "绑定 validation-context": PatchStep(
            operation="bind_validation_context",
            target_area=artifact_name,
            instruction="在验证命令或验证相关说明里显式要求优先读取 validation-context.md。",
            anchor_hint="执行过程 / 验证准备 / 输入上下文段落",
            sample_text="- 执行前先读取 `validation-context.md`，以其为验证现实来源。",
        ),
        "绑定 _knowledge-template": PatchStep(
            operation="bind_knowledge_template",
            target_area=artifact_name,
            instruction="把 reference 生成或升级动作明确绑定到 `_knowledge-template.md`。",
            anchor_hint="知识分流 / 长期知识升级段落",
            sample_text="- 新增或升级 `reference/*.md` 时，必须按 `_knowledge-template.md` 的完整结构生成。",
        ),
        "绑定 knowledge-index": PatchStep(
            operation="bind_knowledge_index",
            target_area=artifact_name,
            instruction="在 prime 或知识路由相关说明里显式引用 knowledge-index，并写清首轮低噪音数量。",
            anchor_hint="首轮读取规则 / 路由规则",
            sample_text="- 首轮先按 `knowledge-index.md` 命中 1-3 篇，复杂任务再扩展。",
        ),
        "补数据库协作验证契约": PatchStep(
            operation="add_db_validation_contract",
            target_area=artifact_name,
            instruction="新增数据库协作验证章节或模板槽位，并明确默认只读与命令承接。",
            anchor_hint="validation-context 相关模板或验证段落",
            sample_text="## 数据库协作验证\n- 默认只读\n- 真实连接信息由项目上下文提供\n- /vald 执行时使用",
        ),
        "补 feedback 闭环链接": PatchStep(
            operation="link_feedback_loop",
            target_area=artifact_name,
            instruction="在知识索引或模板里补充 knowledge-feedback 的闭环说明和使用入口。",
            anchor_hint="知识索引的读取规则或模板说明部分",
            sample_text="- 命中效果与调整建议统一记录到 `knowledge-feedback.md`。",
        ),
        "补卡片读取规则": PatchStep(
            operation="add_card_reading_rules",
            target_area=artifact_name,
            instruction="在 knowledge-index 中新增卡片读取规则，明确命中后如何阅读和裁剪。",
            anchor_hint="knowledge-index 的规则说明部分",
            sample_text="## 卡片读取规则\n- 先看适用边界\n- 再看标准做法/反模式\n- 高风险时再看验证方式",
        ),
        "统一 feedback 模板": PatchStep(
            operation="normalize_feedback_template",
            target_area=artifact_name,
            instruction="补齐 knowledge-feedback 的统一记录模板，避免反馈字段漂移。",
            anchor_hint="knowledge-feedback 的模板/记录格式段落",
            sample_text="## 记录模板\n- 加载原因\n- 是否真正有帮助\n- 调整动作\n- 下次建议",
        ),
        "按现有文风补强知识卡片结构": PatchStep(
            operation="strengthen_reference_card_structure",
            target_area=artifact_name,
            instruction="补齐知识卡片的边界、做法、反模式、验证信息，但保持现有章节名和叙述风格，不要整篇硬改成模板标题。",
            anchor_hint="优先在已有相近章节下补内容；没有时再新增最小必要章节",
            sample_text="建议动作：先在现有“适用场景 / 检查清单 / 常见误区 / 输出建议”附近补齐缺的结构信息，而不是整篇重排。",
        ),
        "补 prime 到 validation 的转向提示": PatchStep(
            operation="add_prime_validation_handoff",
            target_area=artifact_name,
            instruction="在 prime-context 中增加何时切到 validation-context 的低噪音提示。",
            anchor_hint="默认路由或高频误判提醒段落",
            sample_text="- 遇到真实验证、数据库核对或环境事实时，转向 `validation-context.md`。",
        ),
        "补数据库协作验证章节": PatchStep(
            operation="add_db_validation_section",
            target_area=artifact_name,
            instruction="为 validation-context 增加数据库协作验证章节，明确连接信息来源与只读边界。",
            anchor_hint="validation-context 的验证方式部分",
            sample_text="## 数据库协作验证\n- 默认只读\n- 先确认 schema 与常查表\n- 验证结果写回验证报告",
        ),
        "补项目主链路事实": PatchStep(
            operation="add_project_routing_facts",
            target_area=artifact_name,
            instruction="把项目真实模块/目录入口补进正文，让 prime 相关文件能直接承接代码主链路。",
            anchor_hint="关键目录 / 常见任务入口 / 当前项目事实",
            sample_text="## 关键目录\n- <module-a>/\n- <module-b>/\n\n## 常见任务入口\n- 场景 A: <controller/service>\n- 场景 B: <module/path>",
        ),
        "修正测试现实": PatchStep(
            operation="normalize_test_reality",
            target_area=artifact_name,
            instruction="把默认测试命令改成条件化表述，只在存在真实测试资产时才作为主验证路径。",
            anchor_hint="当前测试现状 / 默认验证路径 / 测试命令段落",
            sample_text="## 当前测试现状\n- 若未扫描到稳定 `src/test/`，默认先编译与烟测\n- 只有真实测试资产存在时，才把测试命令作为主验证手段",
        ),
        "补项目事实槽位": PatchStep(
            operation="add_project_fact_slots",
            target_area=artifact_name,
            instruction="在模板里新增项目目录、任务入口等槽位，让生成产物更容易贴近实际代码结构。",
            anchor_hint="项目事实 / 关键目录 / 常见任务入口",
            sample_text="## 关键目录\n- <module-or-package>\n\n## 常见任务入口\n- 任务类型: <入口类/目录>",
        ),
        "弱化测试占位符假设": PatchStep(
            operation="weaken_test_placeholder",
            target_area=artifact_name,
            instruction="把模板中的测试命令占位从默认存在改为条件化填写，避免初始化阶段编造测试能力。",
            anchor_hint="测试命令模板 / 默认验证路径",
            sample_text="- 基础测试命令: 无 / 待确认 / 仅当真实测试资产存在时填写",
        ),
        "校正 validate 的测试语气": PatchStep(
            operation="tone_down_test_command",
            target_area=artifact_name,
            instruction="把 validate 命令里的测试建议改成以项目事实为前提的条件化说明。",
            anchor_hint="验证层级 / 默认验证命令 / 跳过测试说明",
            sample_text="- 若项目未确认存在稳定测试资产，不要默认执行测试命令；先编译与烟测。",
        ),
        "补配置事实入口": PatchStep(
            operation="add_config_entry_fact",
            target_area=artifact_name,
            instruction="把项目真实配置文件入口写进验证上下文，避免验证阶段只看代码不看配置。",
            anchor_hint="环境前提 / 默认验证路径 / 高风险专项验证",
            sample_text="- 配置入口优先检查 `bootstrap.yml` / `application.yml` 的真实开关与映射。",
        ),
    }
    return mapping.get(title)


def _extract_backtick(text: str) -> str:
    start = text.find("`")
    end = text.rfind("`")
    if start >= 0 and end > start:
        return text[start + 1:end]
    return text


def _next_step_sample(artifact_name: str) -> str:
    by_name = {
        "execute.md": "## 下一步（不会自动执行）\n- 先执行 `/vald`\n- 验证通过后再按需要进入 `/revu`、`/xrep`",
        "plan.md": "## 下一步（不会自动执行）\n- 计划确认后进入 `/exec`",
        "backend-review-plan.md": "## 下一步（不会自动执行）\n- 评审通过后进入 `/pln`\n- 若仍有方案分歧，先补充评审结论再继续",
        "refresh-project-context.md": "## 下一步（不会自动执行）\n- 先人工审阅新生成的 bootstrap 草稿与 merge plan\n- 确认后再合并正式记忆文件",
        "execution-report.md": "## 下一步（不会自动执行）\n- 将候选知识与执行偏差提交给 `/srev` 做最终分流",
        "system-review.md": "## 下一步（不会自动执行）\n- 知识分流确认后再进入 `/cmit` 或手工更新正式文件",
        "review.md": "## 下一步（不会自动执行）\n- 小问题直接修复后重跑 `/vald`\n- 复杂问题转 `/iter`",
        "iterate.md": "## 下一步（不会自动执行）\n- 简单修正后回到 `/vald`\n- 需要沉淀经验时继续进入 `/xrep` / `/srev`",
        "rca.md": "## 下一步（不会自动执行）\n- 根因明确后进入 `/fix`\n- 若仍存在多方案分歧，可先走 `/bref`",
        "implement-fix.md": "## 下一步（不会自动执行）\n- 修复完成后先执行 `/vald`\n- 再按结果进入 `/revu` / `/xrep` / `/srev`",
    }
    return by_name.get(
        artifact_name.lower(),
        "## 下一步（不会自动执行）\n- 根据当前命令职责选择最直接的后续命令或人工审阅动作",
    )
