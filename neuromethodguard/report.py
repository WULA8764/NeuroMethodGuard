from __future__ import annotations

import html
from datetime import datetime

from .schemas import AuditReport, ExtractedField, Issue, Severity


SEVERITY_ICON = {
    Severity.CRITICAL: "🛑",
    Severity.HIGH: "🔴",
    Severity.MEDIUM: "🟠",
    Severity.LOW: "🟡",
    Severity.INFO: "ℹ️",
}


def _md(s: object) -> str:
    if s is None:
        return ""
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def _short(s: str, n: int = 220) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def render_markdown_report(report: AuditReport) -> str:
    extracted = report.extracted
    lines: list[str] = []
    lines.append("# NeuroMethodGuard EEG/ERP 方法学自动审查报告")
    lines.append("")
    lines.append(f"- **Source**: `{_md(extracted.source_name)}`")
    lines.append(f"- **Generated at**: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"- **LLM enabled**: {report.llm_enabled}")
    lines.append(f"- **Risk score**: **{report.score}/100**")
    lines.append(f"- **Risk label**: **{report.risk_label}**")
    lines.append("")
    lines.append("## 1. 执行摘要")
    lines.append("")
    lines.append(report.executive_summary)
    lines.append("")
    lines.append("## 2. 自动抽取的 EEG/ERP 方法参数")
    lines.append("")
    lines.append("| 参数 | 抽取值 | 证据 | 置信度 |")
    lines.append("|---|---:|---|---:|")
    for field in extracted.fields():
        value = field.value if field.present else "未报告/未识别"
        evidence = _short(field.evidence, 260) if field.evidence else ""
        lines.append(f"| {_md(field.name)} | {_md(value)} | {_md(evidence)} | {field.confidence:.2f} |")
    lines.append("")
    lines.append("## 3. 风险问题清单")
    lines.append("")
    if not report.issues:
        lines.append("未发现明确风险项。注意：这不是人工审稿或统计复核的替代。")
    else:
        lines.append("| 严重性 | 类别 | 问题 | 证据 | 建议 |")
        lines.append("|---|---|---|---|---|")
        for issue in sorted(report.issues, key=_issue_sort_key):
            icon = SEVERITY_ICON.get(issue.severity, "")
            lines.append(
                f"| {icon} {_md(issue.severity.value)} | {_md(issue.category)} | "
                f"**{_md(issue.title)}**<br>{_md(issue.description)} | "
                f"{_md(_short(issue.evidence, 200))} | {_md(_short(issue.recommendation, 260))} |"
            )
    lines.append("")
    lines.append("## 4. 建议修改方向")
    lines.append("")
    lines.append(report.recommended_revision)
    lines.append("")
    lines.append("## 5. Agent 运行轨迹")
    lines.append("")
    lines.append("| Agent | 状态 | 摘要 | 细节 |")
    lines.append("|---|---|---|---|")
    for trace in report.traces:
        lines.append(f"| {_md(trace.agent)} | {_md(trace.status)} | {_md(trace.summary)} | `{_md(trace.details)}` |")
    lines.append("")
    lines.append("## 6. 使用边界")
    lines.append("")
    lines.append(
        "本报告是方法学自动质控，不是对研究结论真实性的证明。所有标记项都需要研究者结合原始数据、分析脚本、预注册和领域文献进行人工复核。"
    )
    return "\n".join(lines)


def render_html_report(report: AuditReport) -> str:
    markdown = render_markdown_report(report)
    escaped = html.escape(markdown)
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>NeuroMethodGuard Report</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; line-height: 1.55; max-width: 1000px; margin: 40px auto; padding: 0 20px; }}
pre {{ white-space: pre-wrap; background: #f7f7f7; padding: 16px; border-radius: 8px; }}
</style></head>
<body><pre>{escaped}</pre></body>
</html>"""


def _issue_sort_key(issue: Issue) -> int:
    order = {
        Severity.CRITICAL: 0,
        Severity.HIGH: 1,
        Severity.MEDIUM: 2,
        Severity.LOW: 3,
        Severity.INFO: 4,
    }
    return order.get(issue.severity, 9)
