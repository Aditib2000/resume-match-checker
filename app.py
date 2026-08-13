"""Streamlit web UI for the Resume / Job Match + ATS Checker.

Run with: streamlit run app.py
"""

import streamlit as st

from src import ats_check, analyzer, matcher, report
from src.parse import extract_text_from_upload

st.set_page_config(
    page_title="Resume Match Checker",
    page_icon="\U0001F4C4",
    layout="wide",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700;800&display=swap');

:root {
    --brand-1: #6366f1;
    --brand-2: #a855f7;
    --brand-3: #ec4899;
    --header-1: #dc2626;
    --header-2: #f97316;
    --success-1: #10b981;
    --success-2: #34d399;
    --warning-1: #f59e0b;
    --warning-2: #fbbf24;
    --danger-1: #ef4444;
    --danger-2: #f87171;
    --ink: #1f2333;
    --muted: #6b7280;
}

.stApp {
    background:
        radial-gradient(1200px 500px at 10% -10%, rgba(99,102,241,0.10), transparent),
        radial-gradient(1000px 500px at 100% 0%, rgba(236,72,153,0.08), transparent),
        #f6f6fb;
}

.block-container { padding-top: 2.5rem; max-width: 1120px; }

.app-header {
    text-align: center;
    margin-bottom: 0.15rem;
    font-family: 'Poppins', 'Arial Black', 'Segoe UI', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
}
.app-header, .app-header > span:first-child {
    color: var(--header-1) !important;
}
.app-subheader {
    text-align: center;
    color: var(--muted);
    margin-bottom: 2rem;
    font-size: 1.02rem;
}

.section-title {
    font-weight: 700;
    font-size: 1.15rem;
    color: var(--ink);
    margin: 1.6rem 0 0.8rem 0;
    padding-left: 0.7rem;
    border-left: 5px solid var(--brand-1);
}

/* Score cards */
.score-card {
    border-radius: 18px;
    padding: 1.8rem 1rem;
    text-align: center;
    color: white;
    box-shadow: 0 10px 25px -8px rgba(0,0,0,0.25);
    position: relative;
    overflow: hidden;
}
.score-card::after {
    content: "";
    position: absolute;
    top: -40%; right: -20%;
    width: 140px; height: 140px;
    background: rgba(255,255,255,0.14);
    border-radius: 50%;
}
.score-icon { font-size: 1.6rem; margin-bottom: 0.2rem; }
.score-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    opacity: 0.95;
    font-weight: 600;
}
.score-value {
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1.15;
    text-shadow: 0 2px 10px rgba(0,0,0,0.15);
}
.score-out-of {
    font-size: 0.78rem;
    opacity: 0.9;
}

/* Badges */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.22rem 0.7rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    color: white;
    white-space: nowrap;
    box-shadow: 0 2px 6px -1px rgba(0,0,0,0.25);
}
.badge-strong  { background: linear-gradient(135deg, var(--success-1), var(--success-2)); }
.badge-partial { background: linear-gradient(135deg, var(--warning-1), var(--warning-2)); }
.badge-missing { background: linear-gradient(135deg, var(--danger-1), var(--danger-2)); }
.badge-pass    { background: linear-gradient(135deg, var(--success-1), var(--success-2)); }
.badge-fail    { background: linear-gradient(135deg, var(--danger-1), var(--danger-2)); }

/* Table card */
.table-card {
    background: white;
    border-radius: 16px;
    padding: 0.4rem 0.9rem;
    box-shadow: 0 8px 24px -12px rgba(31,35,51,0.18);
    margin-bottom: 1.6rem;
    overflow-x: auto;
}
table.results-table {
    width: 100%;
    border-collapse: collapse;
}
table.results-table th {
    text-align: left;
    padding: 0.7rem 0.6rem;
    border-bottom: 2px solid #eef0f6;
    font-size: 0.75rem;
    color: var(--brand-1);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 700;
}
table.results-table td {
    padding: 0.65rem 0.6rem;
    border-bottom: 1px solid #f1f1f6;
    font-size: 0.88rem;
    color: var(--ink);
    vertical-align: top;
}
table.results-table tbody tr:hover td {
    background: linear-gradient(90deg, rgba(99,102,241,0.06), transparent);
}
table.results-table tbody tr:last-child td { border-bottom: none; }

/* Streamlit widget polish */
[data-testid="stTextArea"] textarea {
    border-radius: 12px !important;
    border: 1.5px solid #e5e7eb !important;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--brand-1) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}
[data-testid="stFileUploaderDropzone"] {
    border-radius: 12px !important;
    background: linear-gradient(180deg, #fafaff, #f4f4fb) !important;
}
button[kind="primary"] {
    background: linear-gradient(90deg, var(--brand-1), var(--brand-2)) !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    box-shadow: 0 8px 20px -6px rgba(99,102,241,0.55) !important;
    transition: transform 0.12s ease !important;
}
button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 24px -6px rgba(99,102,241,0.65) !important;
}
.stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
.stTabs [data-testid="stTab"],
.stTabs [data-testid="stTab"] p {
    border-radius: 10px 10px 0 0;
    font-weight: 800 !important;
    color: #2563eb !important;
}
[data-testid="stExpander"] {
    border-radius: 12px !important;
    border: 1px solid #eef0f6 !important;
    box-shadow: 0 4px 14px -8px rgba(31,35,51,0.15);
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading embedding model (one-time)...")
def load_embedding_model():
    return matcher.get_model()


def score_tier(score: int) -> tuple[str, str]:
    """Return (gradient_css, icon) for a score."""
    if score >= 75:
        return "linear-gradient(135deg, #10b981, #34d399)", "\U0001F7E2"
    if score >= 50:
        return "linear-gradient(135deg, #f59e0b, #fbbf24)", "\U0001F7E1"
    return "linear-gradient(135deg, #ef4444, #f87171)", "\U0001F534"


def score_card_html(label: str, score: int) -> str:
    gradient, icon = score_tier(score)
    return f"""
    <div class="score-card" style="background:{gradient};">
        <div class="score-icon">{icon}</div>
        <div class="score-label">{label}</div>
        <div class="score-value">{score}</div>
        <div class="score-out-of">out of 100</div>
    </div>
    """


def get_text(label: str, key_prefix: str) -> str:
    paste_tab, upload_tab = st.tabs(["Paste text", "Upload file"])
    pasted = ""
    uploaded_text = ""

    with paste_tab:
        pasted = st.text_area(
            f"Paste {label} text",
            height=280,
            key=f"{key_prefix}_paste",
            label_visibility="collapsed",
            placeholder=f"Paste the {label.lower()} here...",
        )

    with upload_tab:
        uploaded_file = st.file_uploader(
            f"Upload {label}",
            type=["txt", "pdf", "docx"],
            key=f"{key_prefix}_upload",
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            try:
                uploaded_text = extract_text_from_upload(uploaded_file)
                st.success(f"Loaded {uploaded_file.name} ({len(uploaded_text.split())} words)")
            except Exception as e:
                st.error(f"Couldn't read that file: {e}")

    # uploaded file takes priority if both are provided
    return uploaded_text.strip() or pasted.strip()


def ats_table_html(ats_results: dict) -> str:
    rows = []
    for c in ats_results["checks"]:
        badge = (
            '<span class="badge badge-pass">&#10003; PASS</span>' if c.passed
            else '<span class="badge badge-fail">&#10007; FAIL</span>'
        )
        rows.append(f"<tr><td>{c.name}</td><td>{badge}</td><td>{c.message}</td></tr>")
    return f"""
    <div class="table-card">
    <table class="results-table">
        <thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
    </div>
    """


def match_table_html(match_results: list) -> str:
    badge_class = {"strong": "badge-strong", "partial": "badge-partial", "missing": "badge-missing"}
    badge_icon = {"strong": "&#10003;", "partial": "&#8776;", "missing": "&#10007;"}
    rows = []
    for r in sorted(match_results, key=lambda r: r.score):
        badge = f'<span class="badge {badge_class[r.status]}">{badge_icon[r.status]} {r.status.upper()}</span>'
        rows.append(
            f"<tr><td>{r.requirement}</td><td>{r.best_bullet}</td>"
            f"<td>{r.score:.2f}</td><td>{badge}</td></tr>"
        )
    return f"""
    <div class="table-card">
    <table class="results-table">
        <thead><tr><th>Job Requirement</th><th>Best Matching Resume Line</th><th>Score</th><th>Status</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
    </div>
    """


st.markdown('<h1 class="app-header">Resume Match Checker</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="app-subheader">Check ATS compatibility and how well your resume matches a job description.</p>',
    unsafe_allow_html=True,
)

col_job, col_resume = st.columns(2)
with col_job:
    st.markdown('<div class="section-title">\U0001F4CB Job Description</div>', unsafe_allow_html=True)
    job_text = get_text("Job Description", "job")
with col_resume:
    st.markdown('<div class="section-title">\U0001F4C4 Resume</div>', unsafe_allow_html=True)
    resume_text = get_text("Resume", "resume")

use_claude = False
if analyzer.is_available():
    use_claude = st.checkbox("Include Claude gap analysis & rewrite suggestions", value=True)
else:
    st.info(
        "Set the `ANTHROPIC_API_KEY` environment variable to also get Claude's gap explanations "
        "and rewrite suggestions. ATS + match scoring below works without it.",
        icon="ℹ️",
    )

analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)

if analyze_clicked:
    if not job_text or not resume_text:
        st.warning("Please provide both a job description and a resume (paste text or upload a file).")
    else:
        load_embedding_model()

        with st.spinner("Running ATS checks..."):
            ats_results = ats_check.run_all_checks(resume_text)

        with st.spinner("Matching requirements against your resume..."):
            match_results = matcher.match_requirements(job_text, resume_text)

        explanations = {}
        if use_claude and match_results:
            with st.spinner("Asking Claude to explain gaps..."):
                explanations = analyzer.analyze_weak_matches(match_results)

        st.divider()

        score_col1, score_col2 = st.columns(2)
        with score_col1:
            st.markdown(score_card_html("ATS Compatibility", ats_results["score"]), unsafe_allow_html=True)
        with score_col2:
            st.markdown(
                score_card_html("Job Match", matcher.overall_match_score(match_results)),
                unsafe_allow_html=True,
            )

        st.write("")
        st.markdown('<div class="section-title">\U0001F6E1️ ATS Compatibility Checks</div>', unsafe_allow_html=True)
        st.markdown(ats_table_html(ats_results), unsafe_allow_html=True)

        st.markdown('<div class="section-title">\U0001F3AF Job Requirement Match</div>', unsafe_allow_html=True)
        if match_results:
            st.markdown(match_table_html(match_results), unsafe_allow_html=True)
        else:
            st.warning("Couldn't extract any requirements/bullets to compare — check your inputs have bullet points or clear line breaks.")

        if explanations:
            st.markdown('<div class="section-title">\U0001F4A1 Gap Analysis & Suggestions</div>', unsafe_allow_html=True)
            for req, explanation in explanations.items():
                with st.expander(req):
                    st.write(explanation)

        report_md = report.build_report(ats_results, match_results, explanations)
        st.download_button(
            "Download full report (.md)",
            data=report_md,
            file_name="resume_match_report.md",
            mime="text/markdown",
        )
