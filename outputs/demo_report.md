# NeuroMethodGuard EEG/ERP 方法学自动审查报告

- **Source**: `erp_method_bad.md`
- **Generated at**: 2026-04-30T14:19:28
- **LLM enabled**: False
- **Risk score**: **0/100**
- **Risk label**: **very high risk**

## 1. 执行摘要

自动审查共识别 11 个问题（high=5, medium=6）。优先处理：high: 缺少关键 EEG/ERP 方法参数：reference; high: 高通滤波可能影响慢波/晚期成分解释; high: 报告了 ERP 成分但缺少量化时间窗; high: ROI 或时间窗可能存在事后选择风险; high: 多重比较校正缺失或不清楚。

## 2. 自动抽取的 EEG/ERP 方法参数

| 参数 | 抽取值 | 证据 | 置信度 |
|---|---:|---|---:|
| participant_n | Thirty-two | # Example EEG/ERP Methods Text with Deliberate Reporting Gaps Thirty-two undergraduate students participated in the experiment. | 0.65 |
| channels | 64 | EEG was recorded with a 64-channel Brain Products system. | 0.80 |
| montage | Brain Products | EEG was recorded with a 64-channel Brain Products system. | 0.75 |
| sampling_rate | 500 Hz | The EEG was sampled at 500 Hz. | 0.85 |
| online_reference | 未报告/未识别 |  | 0.00 |
| offline_reference | 未报告/未识别 |  | 0.00 |
| impedance | 未报告/未识别 |  | 0.00 |
| high_pass | 0.5 Hz | Data were filtered from 0.5 to 30 Hz and segmented from -200 ms to 800 ms relative to stimulus onset. | 0.85 |
| low_pass | 30 Hz | Data were filtered from 0.5 to 30 Hz and segmented from -200 ms to 800 ms relative to stimulus onset. | 0.85 |
| notch_filter | 未报告/未识别 |  | 0.00 |
| filter_details | Data were filtered from 0.5 to 30 Hz and segmented from -200 ms to 800 ms relative to stimulus onset. | Data were filtered from 0.5 to 30 Hz and segmented from -200 ms to 800 ms relative to stimulus onset. | 0.60 |
| epoch_window | -200 ms to 800 ms | Data were filtered from 0.5 to 30 Hz and segmented from -200 ms to 800 ms relative to stimulus onset. | 0.85 |
| baseline | -200 to 0 ms | Baseline correction used the -200 to 0 ms interval. | 0.85 |
| artifact_rejection | Trials with large artifacts were rejected. | Trials with large artifacts were rejected. | 0.70 |
| ica | ICA was used to remove ocular artifacts. | ICA was used to remove ocular artifacts. | 0.80 |
| eog_handling | 未报告/未识别 |  | 0.00 |
| bad_channels_epochs | 未报告/未识别 |  | 0.00 |
| trial_count | 28 | After preprocessing, approximately 28 trials per condition remained. | 0.65 |
| roi_electrodes | The N170 was measured at PO7 and PO8. | The N170 was measured at PO7 and PO8. | 0.65 |
| time_window | 未报告/未识别 |  | 0.00 |
| erp_components | N170, P3, N400, LPP | For the ERP analysis, we focused on N170, N400 and LPP. | 0.90 |
| statistics | Repeated-measures ANOVAs were conducted for each component. | Repeated-measures ANOVAs were conducted for each component. | 0.75 |
| multiple_comparison | 未报告/未识别 |  | 0.00 |
| effect_size_ci | 未报告/未识别 |  | 0.00 |
| preregistration | 未报告/未识别 |  | 0.00 |
| exclusion_criteria | 未报告/未识别 |  | 0.00 |

## 3. 风险问题清单

| 严重性 | 类别 | 问题 | 证据 | 建议 |
|---|---|---|---|---|
| 🔴 high | reporting | **缺少关键 EEG/ERP 方法参数：reference**<br>未在文本中稳定识别到 reference。这会削弱可重复性，也会让审稿人无法判断 ERP 测量是否可靠。 | not reported or not detected | 区分在线参考与离线重参考。 |
| 🔴 high | preprocessing | **高通滤波可能影响慢波/晚期成分解释**<br>文本中提到慢波或晚期 ERP 成分，同时自动抽取的 high-pass cutoff 高于 0.3 Hz。对 N400/LPP/CNV/SPN 等成分，这可能改变波形形态或振幅。 | Data were filtered from 0.5 to 30 Hz and segmented from -200 ms to 800 ms relative to stimulus onset. | 说明滤波选择依据；必要时提供低截止频率敏感性分析，例如 0.1 Hz 与当前设置的对比。 |
| 🔴 high | ERP quantification | **报告了 ERP 成分但缺少量化时间窗**<br>文本中识别到 ERP 成分，但未识别到清楚的 mean amplitude/peak amplitude 时间窗。 | For the ERP analysis, we focused on N170, N400 and LPP. | 对每个成分预先定义时间窗，例如 N170: 140–200 ms；并说明依据来自文献、预注册或独立 localizer。 |
| 🔴 high | ERP quantification/statistics | **ROI 或时间窗可能存在事后选择风险**<br>文本出现基于显著性、最大振幅或总平均波形选择 ROI/time-window 的迹象。该做法可能引入 circular analysis。 | The N400 and LPP were selected based on the largest difference in the grand average waveforms. | 将 ROI/time-window 依据改为先验文献、预注册、独立数据集/localizer，或使用全时空 cluster-based permutation 并如实说明探索性。 |
| 🔴 high | statistics | **多重比较校正缺失或不清楚**<br>文本暗示存在多个电极、时间点、成分、条件或 ROI 检验，但未识别到多重比较控制。 | For the ERP analysis, we focused on N170, N400 and LPP. | 说明 family 的定义，并使用 Holm/Bonferroni/FDR、cluster-based permutation 或预注册的少量主检验。 |
| 🟠 medium | preprocessing | **滤波器实现细节不足**<br>文本似乎报告了滤波，但未清楚说明滤波器类型、阶数/长度、相位特性或软件实现。 | Data were filtered from 0.5 to 30 Hz and segmented from -200 ms to 800 ms relative to stimulus onset. | 补充 FIR/IIR、阶数或滤波器长度、单向/双向/零相位、软件和版本。 |
| 🟠 medium | artifact | **ICA 使用标准不清楚**<br>文本提到 ICA，但未识别到成分识别标准或眼电/肌电成分处理规则。 | ICA was used to remove ocular artifacts. | 说明 ICA 算法、运行数据、剔除成分数量、成分判定标准，以及是否由盲法/多人评估。 |
| 🟠 medium | artifact | **伪迹剔除标准不够可复现**<br>文本提到 artifact rejection，但未识别到明确阈值或算法标准。 | Trials with large artifacts were rejected. | 报告电压阈值、峰峰值阈值、EOG 规则、坏段比例、坏导插值规则和剔除后 trial 数。 |
| 🟠 medium | data quality | **trial 数可能不足，需要报告稳定性**<br>自动抽取到的 trial/epoch 数低于 35。对小振幅或晚期成分可能不稳定。 | After preprocessing, approximately 28 trials per condition remained. | 报告每条件 trial 分布和剔除比例；必要时加入 trial 数作为协变量或敏感性分析。 |
| 🟠 medium | statistics/reporting | **缺少效应量或置信区间**<br>未识别到效应量或置信区间。仅报告 p 值不足以支撑效应大小和不确定性判断。 | not reported or not detected | 报告 partial eta squared、Cohen's d、beta/OR 及其置信区间，至少对主要效应报告。 |
| 🟠 medium | reproducibility | **缺少被试/epoch 排除标准**<br>未识别到被试或 epoch 的排除标准。EEG 数据质量处理若不透明，会影响可重复性。 | not reported or not detected | 报告剔除标准、剔除人数、剔除原因、最终 N、坏导/坏段比例。 |

## 4. 建议修改方向

建议在 Methods 中补充一个独立小节，例如 'EEG recording and preprocessing' 与 'ERP quantification and statistical analysis'。
最低限度应明确：采集系统、通道数、采样率、在线/离线参考、阻抗、滤波、epoch、baseline、伪迹处理、ICA 标准、剔除后 trial 数、ROI/time-window、统计模型、多重比较校正、效应量/置信区间。
当前最关键的缺失项包括：缺少关键 EEG/ERP 方法参数：reference、报告了 ERP 成分但缺少量化时间窗、多重比较校正缺失或不清楚、缺少效应量或置信区间、缺少被试/epoch 排除标准。
已识别 ERP 成分：N170, P3, N400, LPP。请逐一给出先验时间窗、ROI、电极簇和心理解释边界。
除非 ROI/time-window 已预注册或来自独立 localizer，否则应把相关分析标注为 exploratory，并使用合适的多重比较控制。

## 5. Agent 运行轨迹

| Agent | 状态 | 摘要 | 细节 |
|---|---|---|---|
| DocumentParserAgent | ok | 完成 EEG/ERP 方法参数抽取。 | `{'regex_detected_fields': ['participant_n', 'channels', 'montage', 'sampling_rate', 'high_pass', 'low_pass', 'filter_details', 'epoch_window', 'baseline', 'artifact_rejection', 'ica', 'trial_count', 'roi_electrodes', 'erp_components', 'statistics'], 'text_length': 886}` |
| MethodsAuditAgent | ok | 完成规则化方法学审查，发现 11 个问题。 | `{'severity_counts': {'high': 5, 'medium': 6}}` |
| StatisticsAuditAgent | ok | 完成统计风险聚合。 | `{'statistical_model': 'Repeated-measures ANOVAs were conducted for each component.', 'multiple_comparison': None, 'effect_size_ci': None, 'stat_issue_ids': ['MISSING_MULTIPLE_COMPARISON_CORRECTION', 'MISSING_EFFECT_SIZE_CI']}` |
| ComponentInterpretationAgent | ok | 完成 ERP 成分解释和量化风险聚合。 | `{'components': 'N170, P3, N400, LPP', 'roi': 'The N170 was measured at PO7 and PO8.', 'time_window': None, 'component_issue_ids': ['MISSING_COMPONENT_TIME_WINDOW', 'POST_HOC_ROI_TIMEWINDOW']}` |
| ReportAgent | ok | 完成 Markdown/JSON 报告生成。 | `{'score': 0, 'risk_label': 'very high risk'}` |

## 6. 使用边界

本报告是方法学自动质控，不是对研究结论真实性的证明。所有标记项都需要研究者结合原始数据、分析脚本、预注册和领域文献进行人工复核。