"""Turn analyze.py's JSON output + Claude-authored gap explanations into a PDF.

Usage: python build_pdf_from_json.py <results.json> <explanations.json> <output.pdf>

results.json is whatever analyze.py printed. explanations.json is a plain
{requirement: explanation_text} object that Claude writes itself after
reading the analyze.py output -- no Anthropic API call happens in this
script or analyze.py, only report formatting.
"""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from src import report


def main():
    if len(sys.argv) != 4:
        print("Usage: python build_pdf_from_json.py <results.json> <explanations.json> <output.pdf>", file=sys.stderr)
        sys.exit(1)

    results_path, explanations_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]
    data = json.loads(Path(results_path).read_text(encoding="utf-8"))
    explanations = json.loads(Path(explanations_path).read_text(encoding="utf-8"))

    ats_results = {
        "score": data["ats_score"],
        "checks": [SimpleNamespace(**c) for c in data["ats_checks"]],
    }
    match_results = [SimpleNamespace(**m) for m in data["matches"]]

    pdf_bytes = report.build_pdf(ats_results, match_results, explanations)
    Path(output_path).write_bytes(pdf_bytes)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
