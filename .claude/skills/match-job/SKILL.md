---
name: match-job
description: Run the resume-match-checker project's ATS compatibility check and job-requirement match against a resume and job description, then write the gap analysis and rewrite suggestions directly as Claude instead of calling the paid Anthropic API. Use this whenever the user asks to check a resume against a job posting, run /match-job, wants ATS scoring, or wants resume gap suggestions without spending API credits -- this is the free, local-only path through the resume-match-checker project at this repo.
---

## Why this skill exists

The resume-match-checker project has two ways to get gap analysis (the "why is
this a weak match, and how would you rewrite it" explanations):

1. `src/analyzer.py` calls the Anthropic API directly with a billed API key --
   costs a small amount of real money per run.
2. This skill: you (Claude, already running in this session) read the match
   results and write the same kind of explanation yourself, in the
   conversation. No API key, no per-token billing -- it's covered by the
   user's existing Claude Code access.

Use this skill instead of `src/analyzer.py` whenever the user wants gap
analysis without incurring API costs.

## Steps

### 1. Run the local pipeline (no LLM needed for this part)

From the project root (`resume-match-checker/`), run the bundled script using
the project's own virtual environment so `sentence-transformers` etc. are
available:

```bash
.venv\Scripts\python.exe .claude\skills\match-job\scripts\analyze.py <job_description_path> <resume_path>
```

This prints JSON with `ats_score`, `ats_checks` (list of `{name, passed,
message}`), `match_score`, and `matches` (list of `{requirement,
best_bullet, score, status}` where status is `"strong"`, `"partial"`, or
`"missing"`).

If the user gave you pasted text instead of file paths, write it to a temp
`.txt` file first (any path works, `.txt`/`.pdf`/`.docx` are all supported).

The first run in a new session takes ~15-20 seconds while the local
embedding model loads; that's normal, not an error.

### 2. Write the gap analysis yourself

For every entry in `matches` where `status` is `"partial"` or `"missing"`,
write your own explanation using this exact framing (this is the same
prompt used by `src/analyzer.py`, just answered by you directly instead of
through an API call):

> Job requirement: "{requirement}"
> Closest matching resume bullet found (weak or partial match): "{best_bullet}"
> Match strength: {status}
>
> In 2-3 sentences:
> 1. Explain briefly why this is a weak match (or confirm it's a genuine gap in experience).
> 2. If the underlying experience is plausibly already there but poorly phrased, suggest a rewritten
>    version of the bullet that would better speak to this requirement. Do NOT invent experience that
>    isn't implied by the original bullet -- only rephrase/reframe what's already there.
> 3. If it looks like a genuine gap (no related experience at all), say so plainly instead of forcing a rewrite.
>
> Keep the response tight, no preamble.

Do this reasoning yourself in the conversation -- don't shell out to any API
for it. Build a `{requirement: explanation}` mapping as you go; you'll need
it as JSON in step 4 if the user wants a PDF.

### 3. Present the results in chat

Show the user, in this order:
- ATS Compatibility Score and Job Match Score (out of 100)
- The ATS checks -- call out the FAILs specifically, since those are actionable
- The requirement match table, weakest first, so gaps are easy to scan
- Your gap analysis from step 2, one entry per partial/missing requirement

Keep it readable in chat -- a markdown table works well for the match
results; don't dump raw JSON at the user.

### 4. Optional: generate a PDF

Only do this if the user asks for a file/PDF (not every invocation needs
one). Write your explanations dict from step 2 to a temp JSON file, then run:

```bash
.venv\Scripts\python.exe .claude\skills\match-job\scripts\build_pdf_from_json.py <results.json> <explanations.json> <output.pdf>
```

where `<results.json>` is the raw output saved from step 1 and
`<explanations.json>` is your `{requirement: explanation}` mapping. Tell the
user where the PDF was saved (or use a file-delivery tool if one is
available in this session).

## Notes

- This skill is scoped to the `resume-match-checker` project specifically --
  the paths above assume you're working from that project's root directory.
- If the user's question is actually about the public-facing Streamlit web
  app (`app.py`) rather than a one-off local check, this skill isn't the
  right tool -- the web app intentionally has no Claude analysis for public
  visitors (see `README.md`'s "Public deployment" section for why).
