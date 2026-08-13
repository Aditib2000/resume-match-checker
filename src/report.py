"""Build a markdown report from ATS checks + requirement match results."""

from .matcher import MatchResult, overall_match_score

STATUS_EMOJI_FREE = {"strong": "STRONG", "partial": "PARTIAL", "missing": "MISSING"}

_PDF_CHAR_REPLACEMENTS = {
    "—": "-", "–": "-",   # em dash, en dash
    "‘": "'", "’": "'",   # curly single quotes
    "“": '"', "”": '"',   # curly double quotes
    "…": "...",                 # ellipsis
    "•": "-", "●": "-", "◦": "-", "▪": "-", "‣": "-",  # bullets
}


def _pdf_safe(text: str) -> str:
    """PDF core fonts only support Latin-1 -- normalize common unicode punctuation
    and replace with '?' for anything else, so arbitrary pasted text can't crash it."""
    for char, replacement in _PDF_CHAR_REPLACEMENTS.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")


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


def build_pdf(
    ats_results: dict,
    match_results: list[MatchResult],
    explanations: dict[str, str] | None = None,
) -> bytes:
    from fpdf import FPDF
    from fpdf.fonts import FontFace

    explanations = explanations or {}
    match_score = overall_match_score(match_results)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Resume / Job Match Report", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"ATS Compatibility Score: {ats_results['score']}/100", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Job Match Score: {match_score}/100", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    header_style = FontFace(emphasis="BOLD", fill_color=(238, 240, 246))

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "ATS Compatibility Checks", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    with pdf.table(col_widths=(45, 20, 100), text_align="LEFT") as table:
        header = table.row()
        for h in ("Check", "Result", "Detail"):
            header.cell(h, style=header_style)
        for c in ats_results["checks"]:
            row = table.row()
            row.cell(_pdf_safe(c.name))
            row.cell("PASS" if c.passed else "FAIL")
            row.cell(_pdf_safe(c.message))

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Job Requirement Match", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    with pdf.table(col_widths=(55, 55, 15, 25), text_align="LEFT") as table:
        header = table.row()
        for h in ("Requirement", "Best Matching Bullet", "Score", "Status"):
            header.cell(h, style=header_style)
        for r in sorted(match_results, key=lambda r: r.score):
            row = table.row()
            row.cell(_pdf_safe(r.requirement))
            row.cell(_pdf_safe(r.best_bullet))
            row.cell(f"{r.score:.2f}")
            row.cell(STATUS_EMOJI_FREE[r.status])

    if explanations:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Gap Analysis & Suggestions", new_x="LMARGIN", new_y="NEXT")
        for req, explanation in explanations.items():
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, _pdf_safe(req), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, _pdf_safe(explanation), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

    return bytes(pdf.output())
