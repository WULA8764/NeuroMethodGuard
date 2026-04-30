from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from neuromethodguard.agents import NeuroMethodGuardPipeline
from neuromethodguard.report import render_markdown_report
from neuromethodguard.text_io import read_text_file


st.set_page_config(page_title="NeuroMethodGuard", page_icon="🧠", layout="wide")
st.title("🧠 NeuroMethodGuard")
st.caption("EEG/ERP 方法学审查与自动质控 Agent · MVP")

with st.sidebar:
    st.header("运行设置")
    use_llm = st.checkbox("启用 OpenAI LLM 增强抽取/改写", value=False)
    model = st.text_input("模型", value="gpt-4.1")
    st.info("未配置 OPENAI_API_KEY 时会自动退回规则引擎模式。")

uploaded = st.file_uploader("上传 EEG/ERP 方法部分、预注册方案或论文草稿", type=["txt", "md", "pdf", "docx"])
manual_text = st.text_area("或直接粘贴文本", height=260, placeholder="粘贴 Methods / EEG preprocessing / ERP analysis 段落……")

run = st.button("开始审查", type="primary")

if run:
    if not uploaded and not manual_text.strip():
        st.error("请上传文件或粘贴文本。")
        st.stop()

    if uploaded:
        suffix = Path(uploaded.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getbuffer())
            tmp_path = tmp.name
        try:
            text = read_text_file(tmp_path)
            source_name = uploaded.name
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    else:
        text = manual_text
        source_name = "manual_input"

    with st.spinner("Agent 正在抽取参数、检查风险并生成报告……"):
        pipeline = NeuroMethodGuardPipeline(model=model, use_llm=use_llm)
        report = pipeline.run_text(text, source_name=source_name)

    st.subheader("总览")
    c1, c2, c3 = st.columns(3)
    c1.metric("Risk score", f"{report.score}/100")
    c2.metric("Risk label", report.risk_label)
    c3.metric("Issues", len(report.issues))
    st.write(report.executive_summary)

    st.subheader("抽取参数")
    extracted_rows = []
    for field in report.extracted.fields():
        extracted_rows.append(
            {
                "parameter": field.name,
                "value": field.value or "未报告/未识别",
                "confidence": field.confidence,
                "evidence": field.evidence,
            }
        )
    st.dataframe(pd.DataFrame(extracted_rows), use_container_width=True, hide_index=True)

    st.subheader("风险问题")
    if report.issues:
        issue_rows = [
            {
                "severity": i.severity.value,
                "category": i.category,
                "title": i.title,
                "evidence": i.evidence,
                "recommendation": i.recommendation,
            }
            for i in report.issues
        ]
        st.dataframe(pd.DataFrame(issue_rows), use_container_width=True, hide_index=True)
    else:
        st.success("未发现明确风险项；仍需人工复核。")

    st.subheader("建议修改方向")
    st.markdown(report.recommended_revision)

    md = render_markdown_report(report)
    js = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    st.download_button("下载 Markdown 报告", md, file_name="neuromethodguard_report.md", mime="text/markdown")
    st.download_button("下载 JSON trace", js, file_name="neuromethodguard_trace.json", mime="application/json")

    with st.expander("查看完整 Markdown 报告"):
        st.markdown(md)
