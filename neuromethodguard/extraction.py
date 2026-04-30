from __future__ import annotations

import re
from collections import OrderedDict
from typing import Iterable, Optional

from .schemas import EvidenceLevel, ExtractedField, ExtractedMethods


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？.!?])\s+|\n+")


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def split_sentences(text: str) -> list[str]:
    chunks = [c.strip() for c in _SENTENCE_SPLIT_RE.split(text) if c.strip()]
    # If a methods section is written as a long paragraph, keep line-sized fallback chunks.
    out: list[str] = []
    for c in chunks:
        if len(c) > 800:
            out.extend([c[i : i + 500] for i in range(0, len(c), 500)])
        else:
            out.append(c)
    return out


def find_sentence(text: str, patterns: Iterable[str]) -> Optional[str]:
    sentences = split_sentences(text)
    compiled = [re.compile(p, flags=re.I | re.S) for p in patterns]
    for sentence in sentences:
        if any(p.search(sentence) for p in compiled):
            return _clean(sentence)
    return None


def find_value(text: str, patterns: Iterable[str]) -> tuple[Optional[str], Optional[str]]:
    """Return (value, evidence sentence) for the first capturing regex match."""
    sentences = split_sentences(text)
    compiled = [re.compile(p, flags=re.I | re.S) for p in patterns]
    for sentence in sentences:
        for pattern in compiled:
            match = pattern.search(sentence)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                return _clean(value), _clean(sentence)
    return None, None


def make_field(name: str, value: Optional[str], evidence: Optional[str], confidence: float = 0.75) -> ExtractedField:
    if value:
        return ExtractedField(
            name=name,
            value=value,
            evidence=evidence or value,
            evidence_level=EvidenceLevel.DIRECT,
            confidence=confidence,
        )
    return ExtractedField(name=name)


def extract_components(text: str) -> ExtractedField:
    component_terms = [
        "N1", "P1", "N2", "P2", "N170", "P3", "P300", "N400", "LPP", "ERN",
        "FRN", "MMN", "CNV", "N200", "P200", "EPN", "SPN", "RewP", "N450",
    ]
    found: OrderedDict[str, None] = OrderedDict()
    for term in component_terms:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", text, re.I):
            found[term.upper()] = None
    if found:
        evidence = find_sentence(text, [r"\b(" + "|".join(map(re.escape, component_terms)) + r")\b"])
        return make_field("erp_components", ", ".join(found.keys()), evidence, 0.9)
    return ExtractedField("erp_components")


def extract_regex_methods(text: str, source_name: str = "input") -> ExtractedMethods:
    normalized = _clean(text)
    em = ExtractedMethods(source_name=source_name, raw_text_length=len(text))

    value, ev = find_value(normalized, [
        r"(?:N\s*=\s*|n\s*=\s*)(\d{1,4})\s*(?:participants?|subjects?|被试|参与者)?",
        r"(?:participants?|subjects?|被试|参与者|样本量).{0,40}?(\d{1,4})",
        r"(\d{1,4})\s*(?:participants?|subjects?|students?|被试|参与者)",
        r"((?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)(?:[-\s](?:one|two|three|four|five|six|seven|eight|nine))?).{0,40}?(?:participants?|subjects?|students?)",
    ])
    em.participant_n = make_field("participant_n", value, ev, 0.65)

    value, ev = find_value(normalized, [
        r"(\d{2,3})\s*[-\s]?(?:channels?|electrodes?|电极|导联)",
        r"(\d{2,3}).{0,20}?(?:electrodes?|电极|导联)",
        r"(?:channels?|electrodes?|电极|导联).{0,25}?(\d{2,3})",
    ])
    em.channels = make_field("channels", value, ev, 0.8)

    value, ev = find_value(normalized, [
        r"((?:10\s*[-–]\s*20|10\s*[-–]\s*10|10\s*[-–]\s*5)\s*(?:system|系统)?)",
        r"(BioSemi|EGI|Brain Products|Neuroscan|ANT Neuro|HydroCel|actiCAP|easycap)",
    ])
    em.montage = make_field("montage", value, ev, 0.75)

    value, ev = find_value(normalized, [
        r"(?:sampling rate|sampled at|sampling frequency|采样率|采样频率).{0,40}?(\d+(?:\.\d+)?)\s*(?:Hz|hz)",
        r"(\d+(?:\.\d+)?)\s*(?:Hz|hz).{0,20}?(?:sampling|sampled|采样)",
    ])
    em.sampling_rate = make_field("sampling_rate", value + " Hz" if value else None, ev, 0.85)

    ev_ref = find_sentence(normalized, [r"reference|referenced|re-reference|rereferenced|参考|重参考|linked mastoids|average mastoids|Cz|nose"])
    if ev_ref:
        em.online_reference = make_field("online_reference", ev_ref[:180], ev_ref, 0.55)
        if re.search(r"re-?referenc|offline|重新参考|离线|平均参考|average reference|linked mastoids|average mastoids", ev_ref, re.I):
            em.offline_reference = make_field("offline_reference", ev_ref[:180], ev_ref, 0.65)
    
    value, ev = find_value(normalized, [
        r"(?:impedance|阻抗).{0,40}?((?:below|under|<|less than|小于|低于)?\s*\d+(?:\.\d+)?\s*(?:k?Ω|kohm|kΩ|kOhm|ohm))",
    ])
    em.impedance = make_field("impedance", value, ev, 0.75)

    # Band-pass expressions supply high-pass and low-pass simultaneously.
    value, ev = find_value(normalized, [
        r"(?:band[-\s]?pass|带通|滤波|filter(?:ed)?).{0,60}?(\d+(?:\.\d+)?)\s*(?:Hz|hz)?\s*(?:-|–|—|to|至|到|和)\s*(\d+(?:\.\d+)?)\s*(?:Hz|hz)",
    ])
    if value and ev:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:Hz|hz)?\s*(?:-|–|—|to|至|到|和)\s*(\d+(?:\.\d+)?)\s*(?:Hz|hz)", ev, re.I)
        if m:
            em.high_pass = make_field("high_pass", m.group(1) + " Hz", ev, 0.85)
            em.low_pass = make_field("low_pass", m.group(2) + " Hz", ev, 0.85)

    if not em.high_pass.present:
        value, ev = find_value(normalized, [
            r"(?:high[-\s]?pass|高通).{0,40}?(\d+(?:\.\d+)?)\s*(?:Hz|hz)",
        ])
        em.high_pass = make_field("high_pass", value + " Hz" if value else None, ev, 0.85)
    if not em.low_pass.present:
        value, ev = find_value(normalized, [
            r"(?:low[-\s]?pass|低通).{0,40}?(\d+(?:\.\d+)?)\s*(?:Hz|hz)",
        ])
        em.low_pass = make_field("low_pass", value + " Hz" if value else None, ev, 0.85)

    ev_filter = find_sentence(normalized, [r"filter|filtered|滤波|高通|低通|带通|Butterworth|FIR|IIR|zero-phase|零相位"])
    if ev_filter:
        em.filter_details = make_field("filter_details", ev_filter[:200], ev_filter, 0.6)

    value, ev = find_value(normalized, [
        r"(?:notch|陷波).{0,40}?((?:50|60)\s*(?:Hz|hz))",
        r"((?:50|60)\s*(?:Hz|hz).{0,35}?(?:notch|陷波))",
    ])
    em.notch_filter = make_field("notch_filter", value, ev, 0.75)

    value, ev = find_value(normalized, [
        r"(?:epoch|epochs|segmented|分段|时间窗).{0,80}?(-?\d+(?:\.\d+)?\s*(?:ms|s|毫秒|秒)?\s*(?:to|-|–|—|至|到)\s*\+?\d+(?:\.\d+)?\s*(?:ms|s|毫秒|秒))",
        r"(-?\d+(?:\.\d+)?\s*(?:ms|s|毫秒|秒)?\s*(?:to|-|–|—|至|到)\s*\+?\d+(?:\.\d+)?\s*(?:ms|s|毫秒|秒)).{0,50}?(?:epoch|epochs|分段)",
    ])
    em.epoch_window = make_field("epoch_window", value, ev, 0.85)

    value, ev = find_value(normalized, [
        r"(?:baseline|基线).{0,80}?(-?\d+(?:\.\d+)?\s*(?:ms|s|毫秒|秒)?\s*(?:to|-|–|—|至|到)\s*\+?\d+(?:\.\d+)?\s*(?:ms|s|毫秒|秒))",
        r"(-?\d+(?:\.\d+)?\s*(?:ms|s|毫秒|秒)?\s*(?:to|-|–|—|至|到)\s*\+?\d+(?:\.\d+)?\s*(?:ms|s|毫秒|秒)).{0,50}?(?:baseline|基线)",
    ])
    em.baseline = make_field("baseline", value, ev, 0.85)

    ev_artifact = find_sentence(normalized, [r"±|\d+\s*(?:µV|μV|uV|microvolt)|threshold|阈值|peak[-\s]?to[-\s]?peak"])
    if not ev_artifact:
        ev_artifact = find_sentence(normalized, [r"artifact|artefact|reject|rejection|剔除|伪迹|坏段|bad epoch"])
    if ev_artifact:
        em.artifact_rejection = make_field("artifact_rejection", ev_artifact[:220], ev_artifact, 0.7)

    ev_ica = find_sentence(normalized, [r"\bICA\b|independent component|独立成分"])
    if ev_ica:
        em.ica = make_field("ica", ev_ica[:220], ev_ica, 0.8)

    ev_eog = find_sentence(normalized, [r"EOG|HEOG|VEOG|blink|眼电|眨眼|saccade|眼动"])
    if ev_eog:
        em.eog_handling = make_field("eog_handling", ev_eog[:220], ev_eog, 0.75)

    ev_bad = find_sentence(normalized, [r"bad channels?|bad electrodes?|坏道|坏导|interpolat|插值|bad epochs?|坏段"])
    if ev_bad:
        em.bad_channels_epochs = make_field("bad_channels_epochs", ev_bad[:220], ev_bad, 0.7)

    value, ev = find_value(normalized, [
        r"(?:accepted|remaining|retained|valid|usable|artifact[-\s]?free|final|保留|有效).{0,50}?(?:trials?|epochs?|试次).{0,50}?(\d{1,4})",
        r"(\d{1,4})\s*(?:accepted|remaining|retained|valid|usable|artifact[-\s]?free)?\s*(?:trials?|试次).{0,60}?(?:per condition|each condition|每条件|remained|retained|accepted|valid|usable)?",
        r"(?:trials?|试次).{0,80}?(\d{1,4}).{0,40}(?:per condition|each condition|每条件|remained|retained)",
    ])
    em.trial_count = make_field("trial_count", value, ev, 0.65)

    ev_roi = find_sentence(normalized, [r"ROI|region of interest|electrode cluster|cluster of electrodes|centro[-\s]?parietal|fronto[-\s]?central|parietal ROI|电极点|兴趣区|脑区|(?:measured|quantified|analy[sz]ed).{0,80}(?:Fz|FCz|Cz|Pz|Oz|PO7|PO8|P7|P8)|(?:Fz|FCz|Cz|Pz|Oz|PO7|PO8|P7|P8).{0,80}(?:ROI|electrode|电极|measured|quantified)"])
    if ev_roi:
        em.roi_electrodes = make_field("roi_electrodes", ev_roi[:220], ev_roi, 0.65)

    value, ev = find_value(normalized, [
        r"(?:time window|latency window|时间窗|潜伏期窗口).{0,80}?(\d{2,4}\s*(?:ms|毫秒)?\s*(?:to|-|–|—|至|到)\s*\d{2,4}\s*(?:ms|毫秒))",
        r"(?:N170|P3|P300|N400|LPP|ERN|FRN|MMN|ERP).{0,120}?(\d{2,4}\s*(?:ms|毫秒)?\s*(?:to|-|–|—|至|到)\s*\d{2,4}\s*(?:ms|毫秒))",
        r"(\d{2,4}\s*(?:ms|毫秒)?\s*(?:to|-|–|—|至|到)\s*\d{2,4}\s*(?:ms|毫秒)).{0,60}?(?:N170|P3|P300|N400|LPP|ERP|time window|时间窗)",
    ])
    em.time_window = make_field("time_window", value, ev, 0.75)

    em.erp_components = extract_components(normalized)

    ev_stats = find_sentence(normalized, [
        r"ANOVA|MANOVA|mixed[-\s]?effects|linear mixed|LMM|GLMM|regression|t[-\s]?test|cluster[-\s]?based|permutation|Bayes|贝叶斯|方差分析|线性混合|回归|置换"
    ])
    if ev_stats:
        em.statistics = make_field("statistics", ev_stats[:240], ev_stats, 0.75)

    ev_mc = find_sentence(normalized, [
        r"Bonferroni|Holm|FDR|false discovery|cluster[-\s]?based|permutation|TFCE|multiple comparison|family[-\s]?wise|校正|多重比较"
    ])
    if ev_mc:
        em.multiple_comparison = make_field("multiple_comparison", ev_mc[:240], ev_mc, 0.8)

    ev_eff = find_sentence(normalized, [r"\beffect size\b|Cohen|\bbeta\b|β|\bpartial eta\b|\beta\b|η|confidence interval|\bCI\b|置信区间|效应量"])
    if ev_eff:
        em.effect_size_ci = make_field("effect_size_ci", ev_eff[:220], ev_eff, 0.7)

    ev_pre = find_sentence(normalized, [r"pre[-\s]?registered|preregistration|registered report|OSF|预注册"])
    if ev_pre:
        em.preregistration = make_field("preregistration", ev_pre[:220], ev_pre, 0.75)

    ev_excl = find_sentence(normalized, [r"exclusion|excluded|excluding|剔除被试|排除标准|纳入标准|inclusion criteria"])
    if ev_excl:
        em.exclusion_criteria = make_field("exclusion_criteria", ev_excl[:220], ev_excl, 0.65)

    return em


def merge_llm_extraction(base: ExtractedMethods, llm_json: dict) -> ExtractedMethods:
    """Merge LLM extraction into regex extraction without overwriting direct high-confidence evidence blindly."""
    for field in base.fields():
        incoming = llm_json.get(field.name)
        if incoming is None:
            continue
        if isinstance(incoming, dict):
            value = incoming.get("value")
            evidence = incoming.get("evidence") or "LLM extracted from document"
        else:
            value = str(incoming)
            evidence = "LLM extracted from document"
        if value and (not field.present or field.confidence < 0.7):
            field.value = str(value)
            field.evidence = str(evidence)
            field.evidence_level = EvidenceLevel.LLM
            field.confidence = max(field.confidence, 0.6)
    return base


def numeric_first(value: str | None) -> Optional[float]:
    if not value:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(m.group(0)) if m else None
