from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EvidenceLevel(str, Enum):
    DIRECT = "direct_text_evidence"
    INFERRED = "inferred_from_text"
    ABSENT = "not_reported"
    RULE = "rule_based_flag"
    LLM = "llm_judgment"


@dataclass
class ExtractedField:
    name: str
    value: Optional[str] = None
    evidence: str = ""
    evidence_level: EvidenceLevel = EvidenceLevel.ABSENT
    confidence: float = 0.0

    @property
    def present(self) -> bool:
        return bool(self.value and str(self.value).strip())


@dataclass
class ExtractedMethods:
    source_name: str = "input"
    participant_n: ExtractedField = field(default_factory=lambda: ExtractedField("participant_n"))
    channels: ExtractedField = field(default_factory=lambda: ExtractedField("channels"))
    montage: ExtractedField = field(default_factory=lambda: ExtractedField("montage"))
    sampling_rate: ExtractedField = field(default_factory=lambda: ExtractedField("sampling_rate"))
    online_reference: ExtractedField = field(default_factory=lambda: ExtractedField("online_reference"))
    offline_reference: ExtractedField = field(default_factory=lambda: ExtractedField("offline_reference"))
    impedance: ExtractedField = field(default_factory=lambda: ExtractedField("impedance"))
    high_pass: ExtractedField = field(default_factory=lambda: ExtractedField("high_pass"))
    low_pass: ExtractedField = field(default_factory=lambda: ExtractedField("low_pass"))
    notch_filter: ExtractedField = field(default_factory=lambda: ExtractedField("notch_filter"))
    filter_details: ExtractedField = field(default_factory=lambda: ExtractedField("filter_details"))
    epoch_window: ExtractedField = field(default_factory=lambda: ExtractedField("epoch_window"))
    baseline: ExtractedField = field(default_factory=lambda: ExtractedField("baseline"))
    artifact_rejection: ExtractedField = field(default_factory=lambda: ExtractedField("artifact_rejection"))
    ica: ExtractedField = field(default_factory=lambda: ExtractedField("ica"))
    eog_handling: ExtractedField = field(default_factory=lambda: ExtractedField("eog_handling"))
    bad_channels_epochs: ExtractedField = field(default_factory=lambda: ExtractedField("bad_channels_epochs"))
    trial_count: ExtractedField = field(default_factory=lambda: ExtractedField("trial_count"))
    roi_electrodes: ExtractedField = field(default_factory=lambda: ExtractedField("roi_electrodes"))
    time_window: ExtractedField = field(default_factory=lambda: ExtractedField("time_window"))
    erp_components: ExtractedField = field(default_factory=lambda: ExtractedField("erp_components"))
    statistics: ExtractedField = field(default_factory=lambda: ExtractedField("statistics"))
    multiple_comparison: ExtractedField = field(default_factory=lambda: ExtractedField("multiple_comparison"))
    effect_size_ci: ExtractedField = field(default_factory=lambda: ExtractedField("effect_size_ci"))
    preregistration: ExtractedField = field(default_factory=lambda: ExtractedField("preregistration"))
    exclusion_criteria: ExtractedField = field(default_factory=lambda: ExtractedField("exclusion_criteria"))
    raw_text_length: int = 0

    def fields(self) -> list[ExtractedField]:
        return [
            value
            for key, value in self.__dict__.items()
            if isinstance(value, ExtractedField)
        ]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Issue:
    issue_id: str
    title: str
    severity: Severity
    category: str
    description: str
    evidence: str = ""
    recommendation: str = ""
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


@dataclass
class AgentTrace:
    agent: str
    status: str
    summary: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditReport:
    extracted: ExtractedMethods
    issues: list[Issue]
    score: int
    risk_label: str
    executive_summary: str
    recommended_revision: str
    traces: list[AgentTrace] = field(default_factory=list)
    llm_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "extracted": self.extracted.to_dict(),
            "issues": [i.to_dict() for i in self.issues],
            "score": self.score,
            "risk_label": self.risk_label,
            "executive_summary": self.executive_summary,
            "recommended_revision": self.recommended_revision,
            "traces": [t.to_dict() for t in self.traces],
            "llm_enabled": self.llm_enabled,
        }
