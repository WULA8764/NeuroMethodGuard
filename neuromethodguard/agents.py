from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .extraction import extract_regex_methods, merge_llm_extraction
from .llm_client import LLMClient
from .report import render_markdown_report
from .rules import audit_methods, recommended_revision_text, score_issues, summarize_issues
from .schemas import AgentTrace, AuditReport
from .text_io import read_text_file


EXTRACTION_SYSTEM = """你是 EEG/ERP 方法学信息抽取 Agent。任务是从论文方法部分或预注册方案中抽取参数。
只输出 JSON object。不要输出 markdown。不要编造；没有报告就用 null。
每个字段输出 {"value": string|null, "evidence": string|null}。
字段包括：participant_n, channels, montage, sampling_rate, online_reference, offline_reference,
impedance, high_pass, low_pass, notch_filter, filter_details, epoch_window, baseline,
artifact_rejection, ica, eog_handling, bad_channels_epochs, trial_count, roi_electrodes,
time_window, erp_components, statistics, multiple_comparison, effect_size_ci,
preregistration, exclusion_criteria。
"""


REVISION_SYSTEM = """你是严格的 EEG/ERP 审稿人和方法学编辑。根据自动审查结果，生成一段可直接放进 Methods 或审稿回复中的修改建议。
要求：中文；克制；不夸大；明确区分缺失项、风险和建议；不要伪造不存在的数据。
"""


class DocumentParserAgent:
    name = "DocumentParserAgent"

    def run(self, text: str, source_name: str, llm: Optional[LLMClient]) -> tuple[object, AgentTrace]:
        extracted = extract_regex_methods(text, source_name=source_name)
        detail = {
            "regex_detected_fields": [f.name for f in extracted.fields() if f.present],
            "text_length": len(text),
        }
        if llm and llm.enabled:
            snippet = text[:14000]
            llm_json = llm.complete_json(EXTRACTION_SYSTEM, snippet, temperature=0.0, max_output_tokens=2200)
            if llm_json:
                extracted = merge_llm_extraction(extracted, llm_json)
                detail["llm_merge"] = True
                detail["llm_detected_fields"] = [k for k, v in llm_json.items() if v]
            else:
                detail["llm_merge"] = False
        return extracted, AgentTrace(self.name, "ok", "完成 EEG/ERP 方法参数抽取。", detail)


class MethodsAuditAgent:
    name = "MethodsAuditAgent"

    def run(self, extracted, text: str) -> tuple[list, AgentTrace]:
        issues = audit_methods(extracted, text)
        severity_counts: dict[str, int] = {}
        for issue in issues:
            severity_counts[issue.severity.value] = severity_counts.get(issue.severity.value, 0) + 1
        return issues, AgentTrace(
            self.name,
            "ok",
            f"完成规则化方法学审查，发现 {len(issues)} 个问题。",
            {"severity_counts": severity_counts},
        )


class StatisticsAuditAgent:
    name = "StatisticsAuditAgent"

    def run(self, issues: list, extracted) -> AgentTrace:
        stat_issue_ids = [i.issue_id for i in issues if "STAT" in i.issue_id or i.category.startswith("statistics")]
        return AgentTrace(
            self.name,
            "ok",
            "完成统计风险聚合。",
            {
                "statistical_model": extracted.statistics.value,
                "multiple_comparison": extracted.multiple_comparison.value,
                "effect_size_ci": extracted.effect_size_ci.value,
                "stat_issue_ids": stat_issue_ids,
            },
        )


class ComponentInterpretationAgent:
    name = "ComponentInterpretationAgent"

    def run(self, issues: list, extracted) -> AgentTrace:
        component_issue_ids = [
            i.issue_id for i in issues if i.category in {"interpretation", "ERP quantification", "ERP quantification/statistics"}
        ]
        return AgentTrace(
            self.name,
            "ok",
            "完成 ERP 成分解释和量化风险聚合。",
            {
                "components": extracted.erp_components.value,
                "roi": extracted.roi_electrodes.value,
                "time_window": extracted.time_window.value,
                "component_issue_ids": component_issue_ids,
            },
        )


class ReportAgent:
    name = "ReportAgent"

    def run(self, extracted, issues: list, llm: Optional[LLMClient]) -> tuple[AuditReport, AgentTrace]:
        score, label = score_issues(issues)
        summary = summarize_issues(issues)
        revision = recommended_revision_text(extracted, issues)

        if llm and llm.enabled:
            payload = {
                "extracted_present_fields": {f.name: f.value for f in extracted.fields() if f.present},
                "issues": [i.to_dict() for i in issues[:14]],
                "score": score,
                "risk_label": label,
            }
            llm_revision = llm.complete_text(
                REVISION_SYSTEM,
                json.dumps(payload, ensure_ascii=False),
                temperature=0.1,
                max_output_tokens=1200,
            )
            if llm_revision and not llm_revision.startswith("LLM_CALL_FAILED"):
                revision = llm_revision.strip()

        report = AuditReport(
            extracted=extracted,
            issues=issues,
            score=score,
            risk_label=label,
            executive_summary=summary,
            recommended_revision=revision,
            traces=[],
            llm_enabled=bool(llm and llm.enabled),
        )
        return report, AgentTrace(
            self.name,
            "ok",
            "完成 Markdown/JSON 报告生成。",
            {"score": score, "risk_label": label},
        )


class NeuroMethodGuardPipeline:
    """Multi-agent orchestration pipeline."""

    def __init__(self, model: Optional[str] = None, use_llm: bool = True):
        self.llm = LLMClient(model=model, enabled=use_llm)
        self.parser = DocumentParserAgent()
        self.methods_audit = MethodsAuditAgent()
        self.stats_audit = StatisticsAuditAgent()
        self.component_audit = ComponentInterpretationAgent()
        self.report_agent = ReportAgent()

    def run_text(self, text: str, source_name: str = "input") -> AuditReport:
        traces: list[AgentTrace] = []
        extracted, trace = self.parser.run(text, source_name, self.llm)
        traces.append(trace)
        issues, trace = self.methods_audit.run(extracted, text)
        traces.append(trace)
        traces.append(self.stats_audit.run(issues, extracted))
        traces.append(self.component_audit.run(issues, extracted))
        report, trace = self.report_agent.run(extracted, issues, self.llm)
        traces.append(trace)
        report.traces = traces
        return report

    def run_file(self, path: str | Path) -> AuditReport:
        text = read_text_file(path)
        return self.run_text(text, source_name=Path(path).name)


def save_report(report: AuditReport, markdown_path: str | Path, json_path: Optional[str | Path] = None) -> None:
    markdown_path = Path(markdown_path)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown_report(report), encoding="utf-8")
    if json_path:
        json_path = Path(json_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
