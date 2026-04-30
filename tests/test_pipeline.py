from pathlib import Path

from neuromethodguard.agents import NeuroMethodGuardPipeline


def test_rule_pipeline_flags_bad_example():
    text = Path("examples/erp_method_bad.md").read_text(encoding="utf-8")
    report = NeuroMethodGuardPipeline(use_llm=False).run_text(text, source_name="test")
    assert report.score < 100
    assert any(i.issue_id == "POST_HOC_ROI_TIMEWINDOW" for i in report.issues)
    assert any(i.issue_id in {"ARTIFACT_THRESHOLD_UNCLEAR", "ICA_CRITERIA_UNCLEAR"} for i in report.issues)


def test_rule_pipeline_extracts_better_example():
    text = Path("examples/erp_method_better.md").read_text(encoding="utf-8")
    report = NeuroMethodGuardPipeline(use_llm=False).run_text(text, source_name="test")
    assert report.extracted.channels.present
    assert report.extracted.sampling_rate.present
    assert report.extracted.baseline.present
    assert report.extracted.trial_count.present
