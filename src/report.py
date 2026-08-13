"""Build a markdown report from ATS checks + requirement match results."""

from .matcher import MatchResult, overall_match_score

STATUS_EMOJI_FREE = {"strong": "STRONG", "partial": "PARTIAL", "missing": "MISSING"}


def build_report(
    ats_results: dict,
    match_results: list[MatchResult],
    explanations: dict[str, str] | None = None,
) -> str:
    explanations = explanations or {}
    lines = []

    lines.append("# Resume / Job Match Report\n")

    # --- Overall scores ---
    match_score = overall_match_score(match_results)
    lines.append("## Overall Scores\n")
    lines.append(f"- **ATS compatibility score:** {ats_results['score']}/100")
    lines.append(f"- **Job match score:** {match_score}/100\n")

    # --- ATS section ---
    lines.append("## ATS Compatibility Checks\n")
    lines.append("| Check | Result | Detail |")
    lines.append("|---|---|---|")
    for c in ats_results["checks"]:
        result = "PASS" if c.passed else "FAIL"
        lines.append(f"| {c.name} | {result} | {c.message} |")
    lines.append("")

    # --- Requirement match section ---
    lines.append("## Job Requirement Match\n")
    lines.append("| Requirement | Best Matching Bullet | Score | Status |")
    lines.append("|---|---|---|---|")
    for r in sorted(match_results, key=lambda r: r.score):
        status = STATUS_EMOJI_FREE[r.status]
        lines.append(f"| {r.requirement} | {r.best_bullet} | {r.score:.2f} | {status} |")
    lines.append("")

    # --- Gap explanations (Stage 2, optional) ---
    if explanations:
        lines.append("## Gap Analysis & Suggestions\n")
        for req, explanation in explanations.items():
            lines.append(f"**{req}**\n")
            lines.append(f"{explanation}\n")

    return "\n".join(lines)
