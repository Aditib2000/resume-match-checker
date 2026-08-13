"""Rule-based ATS (Applicant Tracking System) compatibility checks for a resume.

These are heuristics, not a real ATS engine -- the goal is to catch the same
kinds of things ATS parsers commonly choke on: missing contact info, missing
standard section headers, inconsistent bullets/dates, and characters that
don't parse cleanly as plain text.
"""

import re
from dataclasses import dataclass

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")

STANDARD_SECTIONS = {
    "experience": [r"\bexperience\b", r"\bwork history\b", r"\bemployment\b"],
    "education": [r"\beducation\b"],
    "skills": [r"\bskills\b", r"\btechnical skills\b", r"\bcore competencies\b"],
}

BULLET_CHARS = ("-", "*", "•", "●", "◦", "▪", "‣")

# Characters that commonly break ATS text extraction (icons, emoji, decorative glyphs).
SUSPICIOUS_CHAR_RE = re.compile(
    "[" "\U0001F300-\U0001FAFF" "←-⇿" "☀-➿" "⬀-⯿" "]"
)

DATE_PATTERNS = {
    "mon_yyyy_range": re.compile(
        r"\b[A-Z][a-z]{2,8}\.?\s\d{4}\s*[-–—]\s*(?:[A-Z][a-z]{2,8}\.?\s\d{4}|Present|Current)\b"
    ),
    "mm_yyyy_range": re.compile(r"\b\d{1,2}/\d{4}\s*[-–—]\s*(?:\d{1,2}/\d{4}|Present|Current)\b"),
    "yyyy_range": re.compile(r"\b\d{4}\s*[-–—]\s*(?:\d{4}|Present|Current)\b"),
}


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    weight: int


def check_contact_info(text: str) -> list[CheckResult]:
    results = []
    email_found = bool(EMAIL_RE.search(text))
    phone_found = bool(PHONE_RE.search(text))
    results.append(CheckResult(
        "Email present", email_found,
        "Found an email address." if email_found else "No email address detected — ATS may reject with no contact info.",
        weight=10,
    ))
    results.append(CheckResult(
        "Phone present", phone_found,
        "Found a phone number." if phone_found else "No phone number detected.",
        weight=5,
    ))
    return results


def check_section_headers(text: str) -> list[CheckResult]:
    results = []
    lower = text.lower()
    for section, patterns in STANDARD_SECTIONS.items():
        found = any(re.search(p, lower) for p in patterns)
        results.append(CheckResult(
            f"'{section.title()}' section header", found,
            f"Standard '{section}' header found." if found
            else f"No standard '{section}' header found — ATS parsers look for this exact kind of heading to categorize content.",
            weight=10,
        ))
    return results


def check_bullet_consistency(text: str) -> list[CheckResult]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return [CheckResult("Bullet consistency", False, "No content to check.", weight=5)]

    bullet_lines = [l for l in lines if l.startswith(BULLET_CHARS)]
    distinct_bullet_chars = {l[0] for l in bullet_lines}

    if not bullet_lines:
        return [CheckResult(
            "Bullet consistency", False,
            "No bullet-point lines detected — ATS and recruiters both expect scannable bullets for experience.",
            weight=5,
        )]

    consistent = len(distinct_bullet_chars) == 1
    return [CheckResult(
        "Bullet consistency", consistent,
        "Bullets use a single consistent character." if consistent
        else f"Multiple bullet characters used ({', '.join(distinct_bullet_chars)}) — pick one style consistently.",
        weight=5,
    )]


def check_special_characters(text: str) -> list[CheckResult]:
    matches = SUSPICIOUS_CHAR_RE.findall(text)
    found = len(matches) > 0
    sample = "".join(sorted(set(matches))[:10])
    return [CheckResult(
        "No decorative/icon characters", not found,
        "No icon/emoji-style characters found." if not found
        else f"Found {len(matches)} decorative character(s) (e.g. {sample}) — some ATS parsers render these as garbage or drop the line.",
        weight=10,
    )]


def check_length(text: str) -> list[CheckResult]:
    word_count = len(text.split())
    ok = 300 <= word_count <= 1200
    return [CheckResult(
        "Resume length", ok,
        f"{word_count} words — reasonable length." if ok
        else f"{word_count} words — {'too short, ATS/recruiters may see this as underqualified' if word_count < 300 else 'likely too long, trim to the most relevant experience'}.",
        weight=5,
    )]


def check_date_format_consistency(text: str) -> list[CheckResult]:
    shapes_used = [name for name, pattern in DATE_PATTERNS.items() if pattern.search(text)]
    if not shapes_used:
        return [CheckResult(
            "Date formatting", False,
            "No recognizable date ranges found (e.g. 'Jan 2021 - Present') — ATS uses these to compute years of experience.",
            weight=5,
        )]
    consistent = len(shapes_used) == 1
    return [CheckResult(
        "Date formatting", consistent,
        "Dates use a single consistent format." if consistent
        else f"Multiple date formats used ({', '.join(shapes_used)}) — standardize on one, e.g. 'Jan 2021 - Present'.",
        weight=5,
    )]


def run_all_checks(resume_text: str) -> dict:
    checks: list[CheckResult] = []
    checks += check_contact_info(resume_text)
    checks += check_section_headers(resume_text)
    checks += check_bullet_consistency(resume_text)
    checks += check_special_characters(resume_text)
    checks += check_length(resume_text)
    checks += check_date_format_consistency(resume_text)

    total_weight = sum(c.weight for c in checks)
    earned_weight = sum(c.weight for c in checks if c.passed)
    score = round(100 * earned_weight / total_weight) if total_weight else 0

    return {
        "score": score,
        "checks": checks,
    }
