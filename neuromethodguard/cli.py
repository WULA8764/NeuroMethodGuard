from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agents import NeuroMethodGuardPipeline, save_report
from .report import render_markdown_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="neuromethodguard",
        description="EEG/ERP methods auditing and QC report agent.",
    )
    parser.add_argument("input", help="Input .txt/.md/.pdf/.docx file")
    parser.add_argument("--out", default="outputs/report.md", help="Markdown report output path")
    parser.add_argument("--json", default=None, help="Optional JSON trace output path")
    parser.add_argument("--model", default=None, help="OpenAI model name. Defaults to OPENAI_MODEL or gpt-4.1")
    parser.add_argument("--no-llm", action="store_true", help="Disable OpenAI calls and run deterministic rule engine only")
    parser.add_argument("--print", action="store_true", help="Print report to stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pipeline = NeuroMethodGuardPipeline(model=args.model, use_llm=not args.no_llm)
    report = pipeline.run_file(args.input)
    save_report(report, args.out, args.json)
    if args.print:
        print(render_markdown_report(report))
    else:
        print(f"Saved Markdown report: {Path(args.out).resolve()}")
        if args.json:
            print(f"Saved JSON trace: {Path(args.json).resolve()}")
        print(json.dumps({"score": report.score, "risk_label": report.risk_label, "issues": len(report.issues)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
