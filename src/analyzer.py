"""Claude-powered gap analysis for weak/missing requirement matches.

Only runs if ANTHROPIC_API_KEY is set in the environment. If it's not set,
callers should skip this step -- everything else in the pipeline (ATS
checks + embedding match) works without it.
"""

import os

from .matcher import MatchResult

MODEL = "claude-sonnet-5"

PROMPT_TEMPLATE = """You are helping someone improve their resume for a specific job application.

Job requirement: "{requirement}"
Closest matching resume bullet found (weak or partial match): "{bullet}"
Match strength: {status}

In 2-3 sentences:
1. Explain briefly why this is a weak match (or confirm it's a genuine gap in experience).
2. If the underlying experience is plausibly already there but poorly phrased, suggest a rewritten
   version of the bullet that would better speak to this requirement. Do NOT invent experience that
   isn't implied by the original bullet -- only rephrase/reframe what's already there.
3. If it looks like a genuine gap (no related experience at all), say so plainly instead of forcing a rewrite.

Keep the response tight, no preamble."""


def is_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def explain_gap(result: MatchResult) -> str:
    import anthropic

    client = anthropic.Anthropic()
    prompt = PROMPT_TEMPLATE.format(
        requirement=result.requirement,
        bullet=result.best_bullet,
        status=result.status,
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def analyze_weak_matches(results: list[MatchResult]) -> dict[str, str]:
    """Return {requirement: explanation} for every non-strong match."""
    explanations = {}
    for r in results:
        if r.status != "strong":
            explanations[r.requirement] = explain_gap(r)
    return explanations
