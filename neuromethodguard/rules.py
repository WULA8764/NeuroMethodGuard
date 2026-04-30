from __future__ import annotations

import re
from collections import Counter

from .extraction import numeric_first
from .schemas import ExtractedMethods, Issue, Severity


SEVERITY_WEIGHT = {
    Severity.CRITICAL: 25,
    Severity.HIGH: 14,
    Severity.MEDIUM: 7,
    Severity.LOW: 3,
    Severity.INFO: 0,
}


def audit_methods(extracted: ExtractedMethods, raw_text: str) -> list[Issue]:
    issues: list[Issue] = []
    text = raw_text or ""

    def add(
        issue_id: str,
        title: str,
        severity: Severity,
        category: str,
        description: str,
        evidence: str = "",
        recommendation: str = "",
        rationale: str = "",
    ) -> None:
        issues.append(
            Issue(
                issue_id=issue_id,
                title=title,
                severity=severity,
                category=category,
                description=description,
                evidence=evidence,
                recommendation=recommendation,
                rationale=rationale,
            )
        )

    if extracted.raw_text_length < 600:
        add(
            "DOC_SHORT",
            "输入文本过短，难以形成可靠方法学审查",
            Severity.MEDIUM,
            "document",
            "当前输入看起来不像完整方法部分或预注册方案，自动审查会低估遗漏项。",
            evidence=f"raw_text_length={extracted.raw_text_length}",
            recommendation="上传完整 Methods、EEG preprocessing、ERP quantification 和 Statistical analysis 段落。",
        )

    # Core acquisition reporting.
    required_high = [
        ("channels", extracted.channels, "报告电极/通道数量，例如 64-channel EEG。"),
        ("sampling_rate", extracted.sampling_rate, "报告采样率，例如 500 Hz 或 1000 Hz。"),
        ("reference", extracted.offline_reference if extracted.offline_reference.present else extracted.online_reference, "区分在线参考与离线重参考。"),
        ("epoch_window", extracted.epoch_window, "报告 epoch 相对事件的起止时间，例如 -200 to 800 ms。"),
        ("baseline", extracted.baseline, "报告 baseline correction 的时间窗，例如 -200 to 0 ms。"),
        ("artifact_rejection", extracted.artifact_rejection, "报告伪迹剔除或校正规则，包括阈值、坏导、坏段、EOG/ICA 处理。"),
    ]
    for name, field, rec in required_high:
        if not field.present:
            add(
                f"MISSING_{name.upper()}",
                f"缺少关键 EEG/ERP 方法参数：{name}",
                Severity.HIGH,
                "reporting",
                f"未在文本中稳定识别到 {name}。这会削弱可重复性，也会让审稿人无法判断 ERP 测量是否可靠。",
                evidence="not reported or not detected",
                recommendation=rec,
            )

    if not extracted.participant_n.present:
        add(
            "MISSING_SAMPLE_SIZE",
            "缺少有效样本量或被试数",
            Severity.HIGH,
            "design/statistics",
            "未报告纳入最终 EEG/ERP 分析的被试数量。",
            evidence="not reported or not detected",
            recommendation="区分招募样本、剔除样本和最终进入 ERP 统计分析的 N。",
        )
    else:
        n = numeric_first(extracted.participant_n.value)
        if n is not None and n < 20:
            add(
                "VERY_SMALL_N",
                "ERP 样本量很小，统计功效和稳定性风险高",
                Severity.HIGH,
                "design/statistics",
                "自动抽取到的被试数低于 20。该阈值不是硬性规则，但对常规组内/组间 ERP 效应通常风险较高。",
                evidence=extracted.participant_n.evidence,
                recommendation="补充先验功效分析、效应量依据、剔除后 N，并避免强因果或强神经机制结论。",
            )
        elif n is not None and n < 30:
            add(
                "SMALL_N",
                "样本量偏小，需要功效与稳健性说明",
                Severity.MEDIUM,
                "design/statistics",
                "自动抽取到的被试数低于 30。对多条件、多 ROI、多时间窗 ERP 分析，稳定性仍可能不足。",
                evidence=extracted.participant_n.evidence,
                recommendation="报告功效分析、置信区间、剔除比例，并谨慎解释非显著结果。",
            )

    if not extracted.high_pass.present and not extracted.low_pass.present:
        add(
            "MISSING_FILTER_CUTOFFS",
            "缺少滤波截止频率",
            Severity.HIGH,
            "preprocessing",
            "未识别到 high-pass / low-pass 或 band-pass 截止频率。滤波设置会影响 ERP 振幅、潜伏期和慢波成分。",
            evidence="not reported or not detected",
            recommendation="报告 high-pass、low-pass、notch、滤波器类型、阶数/长度、相位特性以及滤波发生在 epoch 前还是后。",
        )
    elif not extracted.high_pass.present or not extracted.low_pass.present:
        add(
            "PARTIAL_FILTER_REPORTING",
            "滤波参数报告不完整",
            Severity.MEDIUM,
            "preprocessing",
            "只识别到部分滤波参数。审稿人通常需要完整 cutoff 与滤波器实现细节。",
            evidence=(extracted.high_pass.evidence or extracted.low_pass.evidence),
            recommendation="同时报告 high-pass、low-pass、notch、滤波器类型和相位处理。",
        )

    hp = numeric_first(extracted.high_pass.value)
    components = (extracted.erp_components.value or "").upper()
    slow_components = any(c in components for c in ["N400", "LPP", "CNV", "SPN"])
    if hp is not None and hp > 0.3 and slow_components:
        add(
            "HIGH_PASS_SLOW_COMPONENT_RISK",
            "高通滤波可能影响慢波/晚期成分解释",
            Severity.HIGH,
            "preprocessing",
            "文本中提到慢波或晚期 ERP 成分，同时自动抽取的 high-pass cutoff 高于 0.3 Hz。对 N400/LPP/CNV/SPN 等成分，这可能改变波形形态或振幅。",
            evidence=extracted.high_pass.evidence,
            recommendation="说明滤波选择依据；必要时提供低截止频率敏感性分析，例如 0.1 Hz 与当前设置的对比。",
        )
    elif hp is not None and hp > 0.5:
        add(
            "HIGH_PASS_GENERAL_RISK",
            "高通滤波截止频率偏高，需要解释依据",
            Severity.MEDIUM,
            "preprocessing",
            "自动抽取的 high-pass cutoff 高于 0.5 Hz。该设置未必错误，但可能影响低频 ERP 成分。",
            evidence=extracted.high_pass.evidence,
            recommendation="补充滤波依据和敏感性检查，避免把滤波诱发的形态变化解释为心理过程。",
        )

    if extracted.filter_details.present and not re.search(r"FIR|IIR|Butterworth|zero[-\s]?phase|two[-\s]?pass|order|slope|阶|零相位|双向|滤波器", extracted.filter_details.evidence, re.I):
        add(
            "FILTER_IMPLEMENTATION_UNCLEAR",
            "滤波器实现细节不足",
            Severity.MEDIUM,
            "preprocessing",
            "文本似乎报告了滤波，但未清楚说明滤波器类型、阶数/长度、相位特性或软件实现。",
            evidence=extracted.filter_details.evidence,
            recommendation="补充 FIR/IIR、阶数或滤波器长度、单向/双向/零相位、软件和版本。",
        )

    if extracted.ica.present and not re.search(r"ICLabel|MARA|ADJUST|SASICA|EOG|blink|correlation|visual|manual|criteria|component|成分|标准|眼电|眨眼", extracted.ica.evidence, re.I):
        add(
            "ICA_CRITERIA_UNCLEAR",
            "ICA 使用标准不清楚",
            Severity.MEDIUM,
            "artifact",
            "文本提到 ICA，但未识别到成分识别标准或眼电/肌电成分处理规则。",
            evidence=extracted.ica.evidence,
            recommendation="说明 ICA 算法、运行数据、剔除成分数量、成分判定标准，以及是否由盲法/多人评估。",
        )

    if extracted.artifact_rejection.present and not re.search(r"\d+\s*(µV|μV|uV|microvolt)|threshold|±|SD|standard deviation|ICLabel|MARA|ADJUST|阈值|标准差", extracted.artifact_rejection.evidence, re.I):
        add(
            "ARTIFACT_THRESHOLD_UNCLEAR",
            "伪迹剔除标准不够可复现",
            Severity.MEDIUM,
            "artifact",
            "文本提到 artifact rejection，但未识别到明确阈值或算法标准。",
            evidence=extracted.artifact_rejection.evidence,
            recommendation="报告电压阈值、峰峰值阈值、EOG 规则、坏段比例、坏导插值规则和剔除后 trial 数。",
        )

    if not extracted.trial_count.present:
        add(
            "MISSING_TRIAL_COUNT",
            "缺少剔除后每条件 trial 数",
            Severity.HIGH,
            "data quality",
            "未报告每个条件进入 ERP 平均的 trial 数。trial 数直接影响 ERP 信噪比和条件间可比性。",
            evidence="not reported or not detected",
            recommendation="报告每条件平均 trial 数、范围/标准差、剔除比例，并说明组间/条件间 trial 数是否平衡。",
        )
    else:
        trials = numeric_first(extracted.trial_count.value)
        if trials is not None and trials < 20:
            add(
                "LOW_TRIAL_COUNT",
                "每条件 trial 数偏低，ERP 信噪比风险高",
                Severity.HIGH,
                "data quality",
                "自动抽取到的 trial/epoch 数低于 20。该阈值不是通用硬性标准，但对许多 ERP 成分通常偏低。",
                evidence=extracted.trial_count.evidence,
                recommendation="增加试次数、合并条件、报告可靠性指标，或降低结论强度。",
            )
        elif trials is not None and trials < 35:
            add(
                "MODEST_TRIAL_COUNT",
                "trial 数可能不足，需要报告稳定性",
                Severity.MEDIUM,
                "data quality",
                "自动抽取到的 trial/epoch 数低于 35。对小振幅或晚期成分可能不稳定。",
                evidence=extracted.trial_count.evidence,
                recommendation="报告每条件 trial 分布和剔除比例；必要时加入 trial 数作为协变量或敏感性分析。",
            )

    if extracted.erp_components.present and not extracted.time_window.present:
        add(
            "MISSING_COMPONENT_TIME_WINDOW",
            "报告了 ERP 成分但缺少量化时间窗",
            Severity.HIGH,
            "ERP quantification",
            "文本中识别到 ERP 成分，但未识别到清楚的 mean amplitude/peak amplitude 时间窗。",
            evidence=extracted.erp_components.evidence,
            recommendation="对每个成分预先定义时间窗，例如 N170: 140–200 ms；并说明依据来自文献、预注册或独立 localizer。",
        )

    if extracted.erp_components.present and not extracted.roi_electrodes.present:
        add(
            "MISSING_ROI_ELECTRODES",
            "报告了 ERP 成分但缺少 ROI/电极簇定义",
            Severity.HIGH,
            "ERP quantification",
            "文本中识别到 ERP 成分，但未识别到明确 ROI 或电极簇。",
            evidence=extracted.erp_components.evidence,
            recommendation="预先定义电极簇/ROI，并说明选取依据。避免基于显著性图事后挑选电极。",
        )

    posthoc_roi_patterns = r"based on.*(?:grand average|significant|largest|maximal)|selected.*(?:significant|largest|maximal)|根据.*(?:显著|最大|总平均|波形)|事后|post hoc"
    if re.search(posthoc_roi_patterns, text, re.I):
        add(
            "POST_HOC_ROI_TIMEWINDOW",
            "ROI 或时间窗可能存在事后选择风险",
            Severity.HIGH,
            "ERP quantification/statistics",
            "文本出现基于显著性、最大振幅或总平均波形选择 ROI/time-window 的迹象。该做法可能引入 circular analysis。",
            evidence=_first_match_sentence(text, posthoc_roi_patterns),
            recommendation="将 ROI/time-window 依据改为先验文献、预注册、独立数据集/localizer，或使用全时空 cluster-based permutation 并如实说明探索性。",
        )

    if not extracted.statistics.present:
        add(
            "MISSING_STATISTICAL_MODEL",
            "缺少统计模型说明",
            Severity.HIGH,
            "statistics",
            "未识别到 ANOVA、mixed-effects、permutation、regression 等统计模型描述。",
            evidence="not reported or not detected",
            recommendation="明确因变量、固定效应、随机效应/误差项、被试内因素、协变量、软件和版本。",
        )

    many_tests_hint = re.search(r"all electrodes|all channels|each electrode|each time point|sample-by-sample|逐点|所有电极|每个电极|每个时间点", text, re.I)
    multi_factor_hint = _count_reported_components(extracted.erp_components.value) >= 2 or _count_time_windows(text) >= 2
    if (many_tests_hint or multi_factor_hint) and not extracted.multiple_comparison.present:
        add(
            "MISSING_MULTIPLE_COMPARISON_CORRECTION",
            "多重比较校正缺失或不清楚",
            Severity.HIGH,
            "statistics",
            "文本暗示存在多个电极、时间点、成分、条件或 ROI 检验，但未识别到多重比较控制。",
            evidence=(many_tests_hint.group(0) if many_tests_hint else extracted.erp_components.evidence),
            recommendation="说明 family 的定义，并使用 Holm/Bonferroni/FDR、cluster-based permutation 或预注册的少量主检验。",
        )
    elif not extracted.multiple_comparison.present:
        add(
            "MULTIPLE_COMPARISON_UNSPECIFIED",
            "未报告多重比较处理策略",
            Severity.MEDIUM,
            "statistics",
            "即使主分析数量较少，ERP 研究通常也需要说明多重比较 family 与控制策略。",
            evidence="not reported or not detected",
            recommendation="说明哪些检验是 confirmatory，哪些是 exploratory，并报告相应校正策略。",
        )

    if not extracted.effect_size_ci.present:
        add(
            "MISSING_EFFECT_SIZE_CI",
            "缺少效应量或置信区间",
            Severity.MEDIUM,
            "statistics/reporting",
            "未识别到效应量或置信区间。仅报告 p 值不足以支撑效应大小和不确定性判断。",
            evidence="not reported or not detected",
            recommendation="报告 partial eta squared、Cohen's d、beta/OR 及其置信区间，至少对主要效应报告。",
        )

    if not extracted.exclusion_criteria.present:
        add(
            "MISSING_EXCLUSION_CRITERIA",
            "缺少被试/epoch 排除标准",
            Severity.MEDIUM,
            "reproducibility",
            "未识别到被试或 epoch 的排除标准。EEG 数据质量处理若不透明，会影响可重复性。",
            evidence="not reported or not detected",
            recommendation="报告剔除标准、剔除人数、剔除原因、最终 N、坏导/坏段比例。",
        )

    # Component interpretation guard: flag strong psychologizing language.
    interp_sentence = _first_match_sentence(
        text,
        r"(?:N170|P3|P300|N400|LPP|ERN|FRN|MMN).{0,120}(?:reflects|indexes|indicates|demonstrates|proves|表明|证明|反映|代表|说明).{0,120}(?:attention|emotion|semantic|conflict|reward|motivation|意识|注意|情绪|语义|冲突|奖赏|动机)",
    )
    if interp_sentence:
        add(
            "COMPONENT_OVERINTERPRETATION_RISK",
            "ERP 成分解释可能过度心理化",
            Severity.MEDIUM,
            "interpretation",
            "文本把 ERP 成分较直接地等同于心理过程。ERP 成分通常不能单独证明特定心理机制，需要结合任务、拓扑、时间窗、统计和替代解释。",
            evidence=interp_sentence,
            recommendation="将 strong claim 降调为 task-conditional interpretation，并讨论替代解释，例如注意、任务难度、低层视觉差异或 trial 数差异。",
        )

    return _deduplicate_issues(issues)


def score_issues(issues: list[Issue]) -> tuple[int, str]:
    penalty = sum(SEVERITY_WEIGHT[i.severity] for i in issues)
    score = max(0, 100 - penalty)
    if score >= 85:
        label = "low risk"
    elif score >= 70:
        label = "moderate risk"
    elif score >= 50:
        label = "high risk"
    else:
        label = "very high risk"
    return score, label


def summarize_issues(issues: list[Issue]) -> str:
    if not issues:
        return "未发现明显方法学报告缺口；仍建议人工复核原文、数据和分析脚本。"
    counts = Counter(i.severity.value for i in issues)
    top = sorted(issues, key=lambda i: SEVERITY_WEIGHT[i.severity], reverse=True)[:5]
    count_text = ", ".join(f"{k}={v}" for k, v in counts.items())
    top_text = "; ".join(f"{i.severity.value}: {i.title}" for i in top)
    return f"自动审查共识别 {len(issues)} 个问题（{count_text}）。优先处理：{top_text}。"


def recommended_revision_text(extracted: ExtractedMethods, issues: list[Issue]) -> str:
    missing = [i for i in issues if i.issue_id.startswith("MISSING")]
    lines = [
        "建议在 Methods 中补充一个独立小节，例如 'EEG recording and preprocessing' 与 'ERP quantification and statistical analysis'。",
        "最低限度应明确：采集系统、通道数、采样率、在线/离线参考、阻抗、滤波、epoch、baseline、伪迹处理、ICA 标准、剔除后 trial 数、ROI/time-window、统计模型、多重比较校正、效应量/置信区间。",
    ]
    if missing:
        lines.append("当前最关键的缺失项包括：" + "、".join(i.title for i in missing[:8]) + "。")
    if extracted.erp_components.present:
        lines.append(
            f"已识别 ERP 成分：{extracted.erp_components.value}。请逐一给出先验时间窗、ROI、电极簇和心理解释边界。"
        )
    lines.append(
        "除非 ROI/time-window 已预注册或来自独立 localizer，否则应把相关分析标注为 exploratory，并使用合适的多重比较控制。"
    )
    return "\n".join(lines)


def _first_match_sentence(text: str, pattern: str) -> str:
    from .extraction import split_sentences

    compiled = re.compile(pattern, flags=re.I | re.S)
    for sentence in split_sentences(text):
        if compiled.search(sentence):
            return re.sub(r"\s+", " ", sentence).strip()
    m = compiled.search(text or "")
    return re.sub(r"\s+", " ", m.group(0)).strip() if m else ""


def _count_reported_components(value: str | None) -> int:
    if not value:
        return 0
    return len([x for x in re.split(r"[,;/\s]+", value) if x.strip()])


def _count_time_windows(text: str) -> int:
    return len(re.findall(r"\b\d{2,4}\s*(?:ms)?\s*(?:-|–|—|to|至|到)\s*\d{2,4}\s*ms\b", text, re.I))


def _deduplicate_issues(issues: list[Issue]) -> list[Issue]:
    seen: set[str] = set()
    out: list[Issue] = []
    for issue in issues:
        if issue.issue_id not in seen:
            seen.add(issue.issue_id)
            out.append(issue)
    return out
