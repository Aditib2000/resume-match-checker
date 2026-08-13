"""CLI entrypoint: python main.py --job data/sample_job.txt --resume data/sample_resume.txt"""

import argparse
from pathlib import Path

from src import ats_check, analyzer, matcher, report
from src.parse import extract_text


def main():
    parser = argparse.ArgumentParser(description="Resume / Job Match + ATS Checker")
    parser.add_argument("--job", required=True, help="Path to job description file (.txt/.pdf/.docx)")
    parser.add_argument("--resume", required=True, help="Path to resume file (.txt/.pdf/.docx)")
    parser.add_argument("--out", default="output/report.md", help="Where to write the markdown report")
    parser.add_argument("--no-claude", action="store_true", help="Skip Claude gap analysis even if API key is set")
    args = parser.parse_args()

    print(f"Reading job description: {args.job}")
    job_text = extract_text(args.job)
    print(f"Reading resume: {args.resume}")
    resume_text = extract_text(args.resume)

    print("Running ATS compatibility checks...")
    ats_results = ats_check.run_all_checks(resume_text)

    print("Embedding + matching requirements against resume bullets...")
    match_results = matcher.match_requirements(job_text, resume_text)

    explanations = {}
    if not args.no_claude and analyzer.is_available():
        print("Running Claude gap analysis on weak/missing matches...")
        explanations = analyzer.analyze_weak_matches(match_results)
    elif not args.no_claude:
        print("ANTHROPIC_API_KEY not set -- skipping Claude gap analysis (ATS + match results still generated).")

    md = report.build_report(ats_results, match_results, explanations)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")

    print(f"\nATS score: {ats_results['score']}/100")
    print(f"Job match score: {matcher.overall_match_score(match_results)}/100")
    print(f"Full report written to: {out_path}")


if __name__ == "__main__":
    main()
