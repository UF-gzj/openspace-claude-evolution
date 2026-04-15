from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import List

from .types import ClaudeArtifact, ClaudeArtifactType

_IGNORE_DIR_NAMES = {
    ".git",
    ".idea",
    ".vscode",
    ".claude",
    ".openspace",
    "node_modules",
    "target",
    "dist",
    "build",
    "__pycache__",
}


@dataclass
class CodeFactFinding:
    code: str
    severity: str
    message: str
    evidence: List[str] = field(default_factory=list)


@dataclass
class ProjectFacts:
    workspace_root: Path
    top_level_dirs: List[str] = field(default_factory=list)
    module_dirs: List[str] = field(default_factory=list)
    java_package_prefixes: List[str] = field(default_factory=list)
    has_src_test: bool = False
    has_bootstrap_yml: bool = False
    has_application_yml: bool = False


def collect_project_facts(workspace_root: Path) -> ProjectFacts:
    root = workspace_root.resolve()
    top_level_dirs = sorted(
        path.name
        for path in root.iterdir()
        if path.is_dir() and path.name not in _IGNORE_DIR_NAMES
    )

    module_dirs: List[str] = []
    for name in top_level_dirs:
        path = root / name
        if (path / "pom.xml").is_file() or (path / "src" / "main" / "java").is_dir():
            module_dirs.append(name)

    java_packages = _collect_java_package_prefixes(root)
    has_src_test = any(root.rglob("src/test"))
    has_bootstrap_yml = any(root.rglob("bootstrap.yml")) or any(root.rglob("bootstrap.yaml"))
    has_application_yml = any(root.rglob("application.yml")) or any(root.rglob("application.yaml"))

    return ProjectFacts(
        workspace_root=root,
        top_level_dirs=top_level_dirs[:20],
        module_dirs=module_dirs[:12],
        java_package_prefixes=java_packages[:8],
        has_src_test=has_src_test,
        has_bootstrap_yml=has_bootstrap_yml,
        has_application_yml=has_application_yml,
    )


def review_artifact_with_project_facts(
    artifact: ClaudeArtifact,
    *,
    content: str,
    facts: ProjectFacts,
) -> List[CodeFactFinding]:
    artifact_name = artifact.path.name.lower()
    findings: List[CodeFactFinding] = []

    if artifact.artifact_type == ClaudeArtifactType.CLAUDE_MEMORY:
        if artifact_name == "prime-context.md":
            findings.extend(_review_prime_context(content, facts))
        elif artifact_name == "validation-context.md":
            findings.extend(_review_validation_context(content, facts))
    elif artifact.artifact_type == ClaudeArtifactType.CLAUDE_TEMPLATE:
        if artifact_name == "prime-context.template.md":
            findings.extend(_review_prime_context_template(content, facts))
        elif artifact_name == "validation-context.template.md":
            findings.extend(_review_validation_context_template(content, facts))
    elif artifact.artifact_type == ClaudeArtifactType.COMMAND_WORKFLOW:
        if artifact_name == "validate.md":
            findings.extend(_review_validate_command(content, facts))

    return findings


def _review_prime_context(content: str, facts: ProjectFacts) -> List[CodeFactFinding]:
    findings: List[CodeFactFinding] = []
    evidence = _build_routing_evidence(facts)
    if not evidence:
        return findings

    if not _contains_any_token(content, evidence):
        findings.append(
            CodeFactFinding(
                code="missing_project_module_routing",
                severity="medium",
                message="prime-context 缺少项目真实模块/目录事实，首轮路由可能过于抽象，难以贴近当前代码结构。",
                evidence=evidence,
            )
        )
    return findings


def _review_validation_context(content: str, facts: ProjectFacts) -> List[CodeFactFinding]:
    findings: List[CodeFactFinding] = []

    if not facts.has_src_test and _looks_like_unconditional_test_command(content):
        findings.append(
            CodeFactFinding(
                code="test_reality_mismatch",
                severity="high",
                message="项目代码未发现稳定 `src/test` 资产，但 validation-context 仍像是在默认要求测试命令，验证现实可能失真。",
                evidence=["workspace: no tracked src/test directory"],
            )
        )

    if facts.has_bootstrap_yml and "bootstrap.yml" not in content and "bootstrap.yaml" not in content:
        findings.append(
            CodeFactFinding(
                code="missing_bootstrap_config_fact",
                severity="medium",
                message="项目代码存在 `bootstrap.yml`，但 validation-context 没有显式提到配置事实入口，可能漏掉真实配置核对路径。",
                evidence=["workspace: bootstrap.yml exists"],
            )
        )

    return findings


def _review_prime_context_template(content: str, facts: ProjectFacts) -> List[CodeFactFinding]:
    findings: List[CodeFactFinding] = []
    if "关键目录" not in content and "常见任务入口" not in content:
        evidence = _build_routing_evidence(facts)
        if evidence:
            findings.append(
                CodeFactFinding(
                    code="template_missing_project_fact_slots",
                    severity="medium",
                    message="prime-context 模板缺少显式的项目目录/任务入口槽位，生成后的正式文件不易承接真实代码主链路。",
                    evidence=evidence,
                )
            )
    return findings


def _review_validation_context_template(content: str, facts: ProjectFacts) -> List[CodeFactFinding]:
    findings: List[CodeFactFinding] = []
    if (
        not facts.has_src_test
        and "<project-default-test-command>" in content
        and _placeholder_lacks_local_guard(
            content,
            "<project-default-test-command>",
        )
    ):
        findings.append(
            CodeFactFinding(
                code="template_test_placeholder_too_strong",
                severity="medium",
                message="validation-context 模板仍可能诱导默认存在测试命令，和当前项目现实不一致时容易生成假验证路径。",
                evidence=["workspace: no tracked src/test directory"],
            )
        )
    return findings


def _review_validate_command(content: str, facts: ProjectFacts) -> List[CodeFactFinding]:
    findings: List[CodeFactFinding] = []
    if not facts.has_src_test and _looks_like_unconditional_test_command(content):
        findings.append(
            CodeFactFinding(
                code="validate_command_test_reality_mismatch",
                severity="medium",
                message="项目代码未发现稳定 `src/test` 资产，但 validate 命令仍保留偏默认的测试命令语气，可能让验证建议高于项目现实。",
                evidence=["workspace: no tracked src/test directory"],
            )
        )
    return findings


def _collect_java_package_prefixes(root: Path) -> List[str]:
    package_counter: Counter[str] = Counter()
    checked = 0
    for path in root.rglob("*.java"):
        if any(part in _IGNORE_DIR_NAMES for part in path.parts):
            continue
        if "src" not in path.parts or "main" not in path.parts or "java" not in path.parts:
            continue
        checked += 1
        if checked > 300:
            break
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        match = re.search(r"^\s*package\s+([a-zA-Z0-9_.]+)\s*;", content, flags=re.MULTILINE)
        if not match:
            continue
        parts = match.group(1).split(".")
        prefix = ".".join(parts[: min(len(parts), 5)])
        if prefix:
            package_counter[prefix] += 1
    return [item for item, _ in package_counter.most_common(8)]


def _contains_any_token(content: str, tokens: List[str]) -> bool:
    lowered = content.lower()
    return any(token.lower() in lowered for token in tokens if token)


def _build_routing_evidence(facts: ProjectFacts) -> List[str]:
    ordered = facts.module_dirs[:5] + facts.top_level_dirs[:5] + facts.java_package_prefixes[:5]
    unique: List[str] = []
    seen = set()
    for item in ordered:
        normalized = item.lower()
        if item and normalized not in seen:
            unique.append(item)
            seen.add(normalized)
    return unique


def _placeholder_lacks_local_guard(content: str, placeholder: str) -> bool:
    guard_terms = [
        "真实测试资产",
        "仅当",
        "如存在",
        "若存在",
        "待确认",
        "无",
        "不要默认",
        "未扫描到",
    ]
    matches = list(re.finditer(re.escape(placeholder), content))
    if not matches:
        return False

    for match in matches:
        start = max(0, match.start() - 120)
        end = min(len(content), match.end() + 120)
        local_window = content[start:end]
        if any(term in local_window for term in guard_terms):
            return False
    return True


def _looks_like_unconditional_test_command(content: str) -> bool:
    lowered = content.lower()
    if "<project-default-test-command>" in content or "mvn test" in lowered or "pytest" in lowered:
        if "<project-default-test-command>" in content:
            return _placeholder_lacks_local_guard(content, "<project-default-test-command>")

        guard_terms = [
            "真实测试资产",
            "仅当",
            "如存在",
            "若存在",
            "待确认",
            "无",
            "不要默认",
            "未扫描到",
        ]
        return not any(term in content for term in guard_terms)
    return False
