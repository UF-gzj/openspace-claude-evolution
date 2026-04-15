from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class LifecycleSubjectType(str, Enum):
    NATIVE_SKILL = "native_skill"
    CLAUDE_ARTIFACT = "claude_artifact"


class LifecycleStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATE_CANDIDATE = "deprecate_candidate"
    SOFT_DEMOTED = "soft_demoted"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class HardStandardEvidence:
    """Hard gate for model-upgrade retirement decisions.

    These fields intentionally stay explicit so retirement decisions are
    auditable and cannot be made from vague LLM impressions alone.
    """

    benchmark_suite_id: str = ""
    scorer_version: str = ""
    baseline_model: str = ""
    candidate_model: str = ""
    sample_size: int = 0
    shadow_run_count: int = 0
    manual_review_passed: bool = False

    assisted_success_rate: Optional[float] = None
    unassisted_success_rate: Optional[float] = None
    assisted_hallucination_rate: Optional[float] = None
    unassisted_hallucination_rate: Optional[float] = None
    assisted_closure_rate: Optional[float] = None
    unassisted_closure_rate: Optional[float] = None
    assisted_validation_truth_rate: Optional[float] = None
    unassisted_validation_truth_rate: Optional[float] = None
    assisted_knowledge_routing_rate: Optional[float] = None
    unassisted_knowledge_routing_rate: Optional[float] = None

    def validate(self, subject_type: LifecycleSubjectType) -> List[str]:
        errors: List[str] = []

        if not self.benchmark_suite_id:
            errors.append("benchmark_suite_id is required")
        if not self.scorer_version:
            errors.append("scorer_version is required")
        if not self.baseline_model:
            errors.append("baseline_model is required")
        if not self.candidate_model:
            errors.append("candidate_model is required")
        if self.sample_size < 30:
            errors.append("sample_size must be >= 30")
        if self.shadow_run_count < 2:
            errors.append("shadow_run_count must be >= 2")
        if not self.manual_review_passed:
            errors.append("manual_review_passed must be true")

        if self.assisted_success_rate is None or self.unassisted_success_rate is None:
            errors.append("success rates are required")
        elif self.unassisted_success_rate < self.assisted_success_rate - 0.02:
            errors.append("unassisted_success_rate falls below assisted_success_rate by more than 0.02")

        if self.assisted_hallucination_rate is None or self.unassisted_hallucination_rate is None:
            errors.append("hallucination rates are required")
        elif self.unassisted_hallucination_rate > self.assisted_hallucination_rate + 0.01:
            errors.append("unassisted_hallucination_rate exceeds assisted_hallucination_rate by more than 0.01")

        if subject_type == LifecycleSubjectType.CLAUDE_ARTIFACT:
            if self.assisted_closure_rate is None or self.unassisted_closure_rate is None:
                errors.append("closure rates are required for .claude artifacts")
            elif self.unassisted_closure_rate < self.assisted_closure_rate - 0.02:
                errors.append("unassisted_closure_rate falls below assisted_closure_rate by more than 0.02")

            if self.assisted_validation_truth_rate is None or self.unassisted_validation_truth_rate is None:
                errors.append("validation truth rates are required for .claude artifacts")
            elif self.unassisted_validation_truth_rate < self.assisted_validation_truth_rate - 0.01:
                errors.append("unassisted_validation_truth_rate falls below assisted_validation_truth_rate by more than 0.01")

            if self.assisted_knowledge_routing_rate is None or self.unassisted_knowledge_routing_rate is None:
                errors.append("knowledge routing rates are required for .claude artifacts")
            elif self.unassisted_knowledge_routing_rate < self.assisted_knowledge_routing_rate - 0.02:
                errors.append("unassisted_knowledge_routing_rate falls below assisted_knowledge_routing_rate by more than 0.02")

        return errors

    def to_dict(self) -> Dict[str, object]:
        return {
            "benchmark_suite_id": self.benchmark_suite_id,
            "scorer_version": self.scorer_version,
            "baseline_model": self.baseline_model,
            "candidate_model": self.candidate_model,
            "sample_size": self.sample_size,
            "shadow_run_count": self.shadow_run_count,
            "manual_review_passed": self.manual_review_passed,
            "assisted_success_rate": self.assisted_success_rate,
            "unassisted_success_rate": self.unassisted_success_rate,
            "assisted_hallucination_rate": self.assisted_hallucination_rate,
            "unassisted_hallucination_rate": self.unassisted_hallucination_rate,
            "assisted_closure_rate": self.assisted_closure_rate,
            "unassisted_closure_rate": self.unassisted_closure_rate,
            "assisted_validation_truth_rate": self.assisted_validation_truth_rate,
            "unassisted_validation_truth_rate": self.unassisted_validation_truth_rate,
            "assisted_knowledge_routing_rate": self.assisted_knowledge_routing_rate,
            "unassisted_knowledge_routing_rate": self.unassisted_knowledge_routing_rate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "HardStandardEvidence":
        return cls(
            benchmark_suite_id=str(data.get("benchmark_suite_id", "")),
            scorer_version=str(data.get("scorer_version", "")),
            baseline_model=str(data.get("baseline_model", "")),
            candidate_model=str(data.get("candidate_model", "")),
            sample_size=int(data.get("sample_size", 0) or 0),
            shadow_run_count=int(data.get("shadow_run_count", 0) or 0),
            manual_review_passed=bool(data.get("manual_review_passed", False)),
            assisted_success_rate=_float_or_none(data.get("assisted_success_rate")),
            unassisted_success_rate=_float_or_none(data.get("unassisted_success_rate")),
            assisted_hallucination_rate=_float_or_none(data.get("assisted_hallucination_rate")),
            unassisted_hallucination_rate=_float_or_none(data.get("unassisted_hallucination_rate")),
            assisted_closure_rate=_float_or_none(data.get("assisted_closure_rate")),
            unassisted_closure_rate=_float_or_none(data.get("unassisted_closure_rate")),
            assisted_validation_truth_rate=_float_or_none(data.get("assisted_validation_truth_rate")),
            unassisted_validation_truth_rate=_float_or_none(data.get("unassisted_validation_truth_rate")),
            assisted_knowledge_routing_rate=_float_or_none(data.get("assisted_knowledge_routing_rate")),
            unassisted_knowledge_routing_rate=_float_or_none(data.get("unassisted_knowledge_routing_rate")),
        )


@dataclass
class LifecycleEntry:
    subject_id: str
    subject_type: LifecycleSubjectType
    subject_path: str = ""
    status: LifecycleStatus = LifecycleStatus.ACTIVE
    source: str = ""
    rationale: str = ""
    evidence: Optional[HardStandardEvidence] = None
    notes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    last_evaluated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, object]:
        return {
            "subject_id": self.subject_id,
            "subject_type": self.subject_type.value,
            "subject_path": self.subject_path,
            "status": self.status.value,
            "source": self.source,
            "rationale": self.rationale,
            "evidence": self.evidence.to_dict() if self.evidence else None,
            "notes": self.notes,
            "tags": self.tags,
            "last_evaluated_at": self.last_evaluated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "LifecycleEntry":
        evidence = data.get("evidence")
        return cls(
            subject_id=str(data["subject_id"]),
            subject_type=LifecycleSubjectType(str(data["subject_type"])),
            subject_path=str(data.get("subject_path", "")),
            status=LifecycleStatus(str(data.get("status", LifecycleStatus.ACTIVE.value))),
            source=str(data.get("source", "")),
            rationale=str(data.get("rationale", "")),
            evidence=HardStandardEvidence.from_dict(evidence) if isinstance(evidence, dict) else None,
            notes=[str(item) for item in data.get("notes", []) or []],
            tags=[str(item) for item in data.get("tags", []) or []],
            last_evaluated_at=datetime.fromisoformat(
                str(data.get("last_evaluated_at", datetime.now().isoformat()))
            ),
        )


def _float_or_none(value: object) -> Optional[float]:
    if value is None or value == "":
        return None
    return float(value)
