"""Run the ATS + embedding-match pipeline and print structured JSON.

No LLM involved here -- this is the free, local, deterministic part
(rule-based ATS checks + local embedding-model matching). The skill
that calls this script is responsible for the Claude-authored gap
analysis on top, done directly in conversation instead of via a paid
API call.

Usage: python analyze.py <job_description_path> <resume_path>
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from src import ats_check, matcher
from src.parse import extract_text


def main():
    if len(sys.argv) != 3:
        print("Usage: python analyze.py <job_description_path> <resume_path>", file=sys.stderr)
        sys.exit(1)

    job_path, resume_path = sys.argv[1], sys.argv[2]
    job_text = extract_text(job_path)
    resume_text = extract_text(resume_path)

    ats_results = ats_check.run_all_checks(resume_text)
    match_results = matcher.match_requirements(job_text, resume_text)

    output = {
        "ats_score": ats_results["score"],
        "ats_checks": [
            {"name": c.name, "passed": c.passed, "message": c.message}
            for c in ats_results["checks"]
        ],
        "match_score": matcher.overall_match_score(match_results),
        "matches": [
            {
                "requirement": r.requirement,
                "best_bullet": r.best_bullet,
                "score": round(r.score, 2),
                "status": r.status,
            }
            for r in match_results
        ],
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
