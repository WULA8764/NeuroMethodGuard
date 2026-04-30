# NeuroMethodGuard 🧠

面向 EEG/ERP 研究的**方法学审查与自动质控 Agent**。这是一个可运行 MVP，不是正式验证过的科研审稿系统。

它支持：

- 读取 `.txt` / `.md` / `.pdf` / `.docx` 方法部分或预注册文本
- 自动抽取 EEG/ERP 关键参数
- 按规则检查采集、预处理、ERP 量化、统计分析与成分解释风险
- 生成 Markdown 报告和 JSON trace
- 可选使用 OpenAI LLM 增强参数抽取与修改建议
- Streamlit 本地网页演示
- 命令行演示，方便录屏和提交证明材料

---

## 1. 快速安装

```bash
cd NeuroMethodGuard
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2. 不使用 API：规则引擎模式

```bash
python -m neuromethodguard.cli examples/erp_method_bad.md \
  --no-llm \
  --out outputs/demo_report.md \
  --json outputs/demo_trace.json \
  --print
```

输出：

- `outputs/demo_report.md`: 自动方法学审查报告
- `outputs/demo_trace.json`: Agent 运行轨迹和结构化问题清单

---

## 3. 使用 OpenAI LLM 增强模式，可选

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env`：

```bash
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4.1
```

运行：

```bash
python -m neuromethodguard.cli examples/erp_method_bad.md \
  --out outputs/demo_report_llm.md \
  --json outputs/demo_trace_llm.json
```

如果没有配置 `OPENAI_API_KEY`，程序会自动退回规则引擎模式。

---

## 4. 本地网页演示

```bash
streamlit run app.py
```

打开浏览器后，可以上传论文方法部分、预注册方案或直接粘贴文本。

---

## 5. Multi-Agent 工作流

```text
DocumentParserAgent
  └─ 抽取 participant_n, channels, sampling_rate, reference, filter, epoch, baseline, ICA, trial_count, ROI, time-window, statistics 等

MethodsAuditAgent
  └─ 基于规则检查 EEG/ERP 方法学报告缺口和预处理风险

StatisticsAuditAgent
  └─ 聚合统计模型、多重比较、效应量/CI 风险

ComponentInterpretationAgent
  └─ 聚合 ERP 成分量化和解释过度风险

ReportAgent
  └─ 生成 Markdown 报告、JSON trace、建议修改方向
```

---

## 6. 当前规则覆盖

| 模块 | 检查内容 |
|---|---|
| 采集参数 | 被试数、通道数、采样率、参考、阻抗 |
| 预处理 | 滤波、epoch、baseline、artifact rejection、ICA、EOG、坏导/坏段 |
| 数据质量 | 剔除后每条件 trial 数、trial 数偏低风险 |
| ERP 量化 | 成分、ROI/电极簇、time-window、事后选择风险 |
| 统计 | 统计模型、多重比较、效应量、置信区间 |
| 解释 | ERP 成分是否被直接等同于心理过程 |

---

## 7. 适合提交的证明材料

运行后建议准备：

1. 终端运行日志截图
2. Streamlit 运行录屏
3. `outputs/demo_report.md`
4. `outputs/demo_trace.json`
5. GitHub 仓库链接
6. 若启用 API，可附 30 天账单或调用日志截图

---

## 8. 使用边界

- 这是方法学自动质控，不是论文审稿替代。
- 规则阈值是启发式，不是领域共识的硬性标准。
- 对 EEG/ERP 论文的最终判断仍需结合原始数据、分析脚本、预注册、任务范式和相关文献。
- LLM 输出可能遗漏或误判；因此保留 JSON trace 和证据句，便于人工复核。
