# Resume / Job Match + ATS Checker

Checks a resume against a job description two ways:

1. **ATS compatibility** — rule-based checks for the things Applicant Tracking
   Systems commonly choke on (missing contact info, missing standard section
   headers, inconsistent bullets/dates, decorative characters that don't parse).
2. **Job match** — splits the job description into individual requirements and
   the resume into bullets, embeds both with a local ML model, and matches by
   *meaning* (not exact keywords) so differently-worded but equivalent
   experience still counts as a match.
3. **(Optional) Claude gap analysis** — for weak/missing matches, asks Claude
   to explain the gap and suggest a rewrite if the underlying experience is
   probably already there but poorly phrased.

Comes with both a CLI (`main.py`) and a web UI (`app.py`, via Streamlit) —
see "Web interface" below. A Claude Code skill/hook wrapper is a natural
next step — see "Next steps" below.

## Setup

```bash
cd resume-match-checker
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

The first run will download the local embedding model (~90MB, one-time,
cached afterward).

### Optional: enable Claude gap analysis

```bash
setx ANTHROPIC_API_KEY "your-key-here"     # Windows, new terminal needed after
```

Without this set, the tool still runs fully — you just won't get the gap
explanations/rewrite suggestions section.

## Run it

```bash
python main.py --job data/sample_job.txt --resume data/sample_resume.txt
```

Try it on your own files next:

```bash
python main.py --job path/to/job_posting.txt --resume path/to/your_resume.pdf
```

Supports `.txt`, `.pdf`, and `.docx` for both inputs.

Output is written to `output/report.md` and a score summary is printed to
the terminal.

## Web interface

For a nicer, colored, drag-and-drop version of the same tool:

```bash
streamlit run app.py
```

This opens a browser tab (usually `http://localhost:8501`) with paste-or-upload
boxes for both the job description and resume, colored score cards, and
styled result tables. Same engine as the CLI — just a friendlier way to use it.

Note: the first "Analyze" click in a new session takes ~15-20 seconds while
the embedding model loads into memory; every click after that is near-instant.

## Public deployment (Streamlit Community Cloud)

1. Push this folder to a GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub,
   click "New app", pick the repo, and set the main file path to `app.py`.
3. Deploy. Do **not** set an `ANTHROPIC_API_KEY` secret for a public deployment
   — without it, the Claude gap-analysis feature automatically hides itself
   (see `analyzer.is_available()`), so public visitors only get the free
   ATS + embedding-match features. This avoids anyone spending your API credits.
4. First load after deploy (or after the app sleeps from inactivity) will be
   slow (~1-2 min) while it installs dependencies and downloads the embedding
   model — this is normal for Streamlit Community Cloud's free tier.

## Tuning

- Match thresholds (`STRONG_THRESHOLD` / `PARTIAL_THRESHOLD` in
  `src/matcher.py`) are a starting point — run it on a job you know you're a
  strong fit for and one you're not, and adjust until the scores feel right.
- ATS check weights live in `src/ats_check.py` if you want to emphasize
  different things.

## Next steps

- Wrap `main.py` as a Claude Code skill (`/match-job <job> <resume>`).
- Add a hook that re-runs the check automatically whenever you save a new
  resume draft.
- Hand-label a few requirement matches yourself and compare against the
  embedding model's strong/partial/missing calls to sanity-check the
  thresholds (this is the "meta-evaluation" step from the LLM-judge project —
  a natural next project once this one feels solid).
