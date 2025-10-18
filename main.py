"""Command-line interface for the Excel QA system."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from excel_qa import ExcelQASystem


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run questions against an Excel workbook.",
    )
    parser.add_argument("workbook", type=Path, help="Path to the Excel file")
    parser.add_argument(
        "question",
        nargs="*",
        help="Optional free-form question. If omitted, the CLI enters interactive mode.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print the answer payload as JSON instead of a formatted summary.",
    )
    return parser


def render_answer(answer, as_json: bool) -> str:
    if as_json:
        return answer.to_json()

    lines = [f"نوع پاسخ: {answer.type}", f"نتیجه: {answer.answer}"]
    if answer.preview:
        lines.append("نمونه نتایج:")
        for row in answer.preview:
            lines.append("  - " + json.dumps(row, ensure_ascii=False))
    lines.append("منطق سیستم:")
    lines.append(json.dumps(answer.rationale, ensure_ascii=False, indent=2))
    return "\n".join(lines)


def interactive_loop(system: ExcelQASystem, as_json: bool) -> int:
    print("📊 Excel QA آماده است. برای خروج CTRL+C را فشار دهید.")
    try:
        while True:
            question = input("سوال خود را وارد کنید: ").strip()
            if not question:
                continue
            answer = system.answer(question)
            print(render_answer(answer, as_json))
            print("-" * 40)
    except KeyboardInterrupt:
        print("\nخروج...")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.workbook.exists():
        parser.error(f"فایل '{args.workbook}' پیدا نشد.")

    system = ExcelQASystem(str(args.workbook))

    if args.question:
        question = " ".join(args.question)
        answer = system.answer(question)
        print(render_answer(answer, args.as_json))
        return 0

    return interactive_loop(system, args.as_json)


if __name__ == "__main__":
    sys.exit(main())
