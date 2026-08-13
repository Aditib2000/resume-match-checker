"""Embedding-based matching of job requirements against resume bullets.

This is the RAG-style piece: instead of exact keyword matching, each
requirement and each resume bullet is embedded into a vector, and we match
by cosine similarity -- so "led cross-functional team" can correctly match
a job requirement like "stakeholder management" even though the wording
is completely different.
"""

import re
from dataclasses import dataclass

import numpy as np

_MODEL = None
MODEL_NAME = "all-MiniLM-L6-v2"

STRONG_THRESHOLD = 0.55
PARTIAL_THRESHOLD = 0.35


def get_model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer(MODEL_NAME)
    return _MODEL


BULLET_PREFIX_RE = re.compile(r"^[\s]*[-*•●◦▪‣]\s+")
EMAIL_LINE_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# Bare section-header lines that sometimes end up alone on a line and
# shouldn't be treated as content (e.g. "Skills", "Experience:").
HEADER_ONLY_RE = re.compile(
    r"^(requirements?|responsibilities|qualifications|summary|objective|"
    r"experience|education|skills|projects|certifications)\s*:?\s*$",
    re.IGNORECASE,
)


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def extract_bullet_lines(text: str) -> list[str]:
    """Lines that were explicitly formatted as bullets in the source text."""
    bullets = []
    for line in text.splitlines():
        stripped = line.strip()
        if BULLET_PREFIX_RE.match(stripped):
            content = BULLET_PREFIX_RE.sub("", stripped).strip()
            if len(content) > 3 and not HEADER_ONLY_RE.match(content):
                bullets.append(content)
    return bullets


def split_job_requirements(job_text: str) -> list[str]:
    # Prefer actual bullet lines -- job postings almost always list
    # requirements as bullets, so this avoids picking up the title/intro text.
    bullets = extract_bullet_lines(job_text)
    if not bullets:
        # fallback: no bullets found, treat non-header sentences as requirements
        bullets = [
            l.strip() for l in job_text.splitlines()
            if len(l.strip()) > 3 and not HEADER_ONLY_RE.match(l.strip())
        ]

    # further split long lines on sentence boundaries so multi-requirement
    # bullets ("3+ years Python; SQL; Agile experience") get separated out
    requirements = []
    for line in bullets:
        parts = re.split(r"[;.]\s+(?=[A-Z])", line)
        requirements.extend(p.strip() for p in parts if len(p.strip()) > 3)

    return _dedupe(requirements)


def split_resume_bullets(resume_text: str) -> list[str]:
    # Resumes mix real bullets (experience) with plain lines (education,
    # skills list, summary) -- unlike job postings, both kinds carry real
    # content here, so combine them rather than preferring one.
    bullets = extract_bullet_lines(resume_text)
    for line in resume_text.splitlines():
        stripped = line.strip()
        if not stripped or len(stripped) <= 3:
            continue
        if BULLET_PREFIX_RE.match(stripped):
            continue  # already captured above
        if HEADER_ONLY_RE.match(stripped):
            continue
        if EMAIL_LINE_RE.search(stripped):
            continue  # contact-info line, not a content line
        bullets.append(stripped)
    return _dedupe(bullets)


def embed_texts(texts: list[str]) -> np.ndarray:
    model = get_model()
    return model.encode(texts, normalize_embeddings=True)


def cosine_sim_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # embeddings are already normalized, so dot product == cosine similarity
    return a @ b.T


@dataclass
class MatchResult:
    requirement: str
    best_bullet: str
    score: float
    status: str  # "strong" | "partial" | "missing"


def classify(score: float) -> str:
    if score >= STRONG_THRESHOLD:
        return "strong"
    if score >= PARTIAL_THRESHOLD:
        return "partial"
    return "missing"


def match_requirements(job_text: str, resume_text: str) -> list[MatchResult]:
    requirements = split_job_requirements(job_text)
    bullets = split_resume_bullets(resume_text)

    if not requirements or not bullets:
        return []

    req_vecs = embed_texts(requirements)
    bullet_vecs = embed_texts(bullets)
    sims = cosine_sim_matrix(req_vecs, bullet_vecs)

    results = []
    for i, req in enumerate(requirements):
        best_j = int(np.argmax(sims[i]))
        score = float(sims[i][best_j])
        results.append(MatchResult(
            requirement=req,
            best_bullet=bullets[best_j],
            score=score,
            status=classify(score),
        ))
    return results


def overall_match_score(results: list[MatchResult]) -> int:
    if not results:
        return 0
    weights = {"strong": 1.0, "partial": 0.5, "missing": 0.0}
    total = sum(weights[r.status] for r in results)
    return round(100 * total / len(results))
