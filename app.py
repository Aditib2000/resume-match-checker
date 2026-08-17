"""Streamlit web UI for the Resume / Job Match + ATS Checker.

Run with: streamlit run app.py
"""

from pathlib import Path

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
    margin-bottom: 1.5rem;
    font-size: 1.02rem;
}

/* Feature chips */
.feature-row {
    display: flex;
    justify-content: center;
    gap: 0.7rem;
    flex-wrap: wrap;
    margin-bottom: 1.6rem;
}
.feature-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: white;
    border-radius: 999px;
    padding: 0.5rem 1.1rem;
    box-shadow: 0 4px 14px -7px rgba(31,35,51,0.25);
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--ink);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.feature-chip:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 18px -7px rgba(31,35,51,0.3);
}

/* Fade-in entrance animation */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fadeInUp 0.55s ease both; }
.fade-in-delay-1 { animation: fadeInUp 0.55s ease both; animation-delay: 0.08s; }
.fade-in-delay-2 { animation: fadeInUp 0.55s ease both; animation-delay: 0.16s; }

/* Circular score gauge */
.gauge-wrap { text-align: center; }
.gauge {
    --size: 176px;
    width: var(--size);
    height: var(--size);
    border-radius: 50%;
    margin: 0 auto 0.9rem auto;
    display: flex;
    align-items: center;
    justify-content: center;
    background: conic-gradient(var(--gcolor) calc(var(--pct) * 1%), #e9e9f4 0);
    box-shadow: 0 14px 30px -12px rgba(31,35,51,0.35);
    transition: transform 0.15s ease;
}
.gauge:hover { transform: scale(1.02); }
.gauge-inner {
    width: calc(var(--size) - 26px);
    height: calc(var(--size) - 26px);
    border-radius: 50%;
    background: white;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}
.gauge-icon { font-size: 1.3rem; margin-bottom: -0.1rem; }
.gauge-value { font-size: 2.5rem; font-weight: 800; color: var(--ink); line-height: 1.1; }
.gauge-outof { font-size: 0.7rem; color: var(--muted); }
.gauge-title {
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--ink);
}

/* Footer */
.app-footer {
    text-align: center;
    color: var(--muted);
    font-size: 0.82rem;
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid #e5e7eb;
}
.app-footer a {
    color: var(--brand-1);
    font-weight: 600;
    text-decoration: none;
}
.app-footer a:hover { text-decoration: underline; }

.section-title {
    font-weight: 700;
    font-size: 1.15rem;
    color: var(--ink);
    margin: 1.6rem 0 0.8rem 0;
    padding-left: 0.7rem;
    border-left: 5px solid var(--brand-1);
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
[data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p,
[data-testid="stCheckbox"] label {
    color: var(--ink) !important;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading embedding model (one-time)...")
def load_embedding_model():
    return matcher.get_model()


DATA_DIR = Path(__file__).resolve().parent / "data"


@st.cache_data
def load_sample_data() -> tuple[str, str]:
    job = (DATA_DIR / "sample_job.txt").read_text(encoding="utf-8")
    resume = (DATA_DIR / "sample_resume.txt").read_text(encoding="utf-8")
    return job, resume


def score_tier(score: int) -> tuple[str, str]:
    """Return (solid color, icon) for a score."""
    if score >= 75:
        return "#10b981", "\U0001F7E2"
    if score >= 50:
        return "#f59e0b", "\U0001F7E1"
    return "#ef4444", "\U0001F534"


def gauge_html(label: str, score: int) -> str:
    color, icon = score_tier(score)
    return f"""
    <div class="gauge-wrap fade-in">
        <div class="gauge" style="--pct:{score}; --gcolor:{color};">
            <div class="gauge-inner">
                <div class="gauge-icon">{icon}</div>
                <div class="gauge-value">{score}</div>
                <div class="gauge-outof">/ 100</div>
            </div>
        </div>
        <div class="gauge-title">{label}</div>
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
        color = "#10b981" if c.passed else "#ef4444"
        badge = (
            '<span class="badge badge-pass">&#10003; PASS</span>' if c.passed
            else '<span class="badge badge-fail">&#10007; FAIL</span>'
        )
        rows.append(
            f'<tr><td style="border-left:4px solid {color}; padding-left:0.7rem;">{c.name}</td>'
            f"<td>{badge}</td><td>{c.message}</td></tr>"
        )
    return f"""
    <div class="table-card fade-in-delay-1">
    <table class="results-table">
        <thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
    </div>
    """


def match_table_html(match_results: list) -> str:
    badge_class = {"strong": "badge-strong", "partial": "badge-partial", "missing": "badge-missing"}
    badge_icon = {"strong": "&#10003;", "partial": "&#8776;", "missing": "&#10007;"}
    row_color = {"strong": "#10b981", "partial": "#f59e0b", "missing": "#ef4444"}
    rows = []
    for r in sorted(match_results, key=lambda r: r.score):
        badge = f'<span class="badge {badge_class[r.status]}">{badge_icon[r.status]} {r.status.upper()}</span>'
        rows.append(
            f'<tr><td style="border-left:4px solid {row_color[r.status]}; padding-left:0.7rem;">{r.requirement}</td>'
            f"<td>{r.best_bullet}</td><td>{r.score:.2f}</td><td>{badge}</td></tr>"
        )
    return f"""
    <div class="table-card fade-in-delay-2">
    <table class="results-table">
        <thead><tr><th>Job Requirement</th><th>Best Matching Resume Line</th><th>Score</th><th>Status</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
    </div>
    """


st.markdown('<h1 class="app-header">Resume Match Checker</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="app-subheader">Check ATS compatibility and how well your resume matches a job description '
    '&mdash; in seconds, for free.</p>',
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="feature-row">
        <div class="feature-chip">\U0001F3AF Smart semantic matching</div>
        <div class="feature-chip">\U0001F6E1️ ATS compatibility check</div>
        <div class="feature-chip">⚡ Instant &amp; free</div>
    </div>
    """,
    unsafe_allow_html=True,
)

_, sample_col, _ = st.columns([1, 1.4, 1])
with sample_col:
    if st.button("✨ Try it with sample data", use_container_width=True):
        sample_job, sample_resume = load_sample_data()
        st.session_state["job_paste"] = sample_job
        st.session_state["resume_paste"] = sample_resume
        st.rerun()

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
            st.markdown(gauge_html("ATS Compatibility", ats_results["score"]), unsafe_allow_html=True)
        with score_col2:
            st.markdown(
                gauge_html("Job Match", matcher.overall_match_score(match_results)),
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

        pdf_bytes = report.build_pdf(ats_results, match_results, explanations)
        st.download_button(
            "Download full report (.pdf)",
            data=pdf_bytes,
            file_name="resume_match_report.pdf",
            mime="application/pdf",
        )

st.markdown(
    '<div class="app-footer">Built with local embeddings + Streamlit &middot; '
    '<a href="https://github.com/Aditib2000/resume-match-checker" target="_blank">View source on GitHub</a></div>',
    unsafe_allow_html=True,
)
