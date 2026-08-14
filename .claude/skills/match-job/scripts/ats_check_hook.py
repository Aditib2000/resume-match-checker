"""PostToolUse hook: after Claude edits/writes a file whose name contains
"resume", re-run the ATS check and surface the updated score.

Reads the hook payload JSON from stdin (Claude Code's standard hook input),
so this has no dependency on jq or any particular shell. Exits silently
(no output) for any tool call that isn't a resume-file edit, so it doesn't
interfere with normal Edit/Write calls elsewhere in the project.
"""

import json
import sys
from pathlib import Path


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    file_path = payload.get("tool_input", {}).get("file_path", "")
    if not file_path or "resume" not in Path(file_path).name.lower():
        return

    path = Path(file_path)
    if not path.exists() or path.suffix.lower() not in (".txt", ".pdf", ".docx"):
        return

    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    try:
        from src import ats_check
        from src.parse import extract_text

        text = extract_text(str(path))
        results = ats_check.run_all_checks(text)
    except Exception as e:
        print(json.dumps({"systemMessage": f"ATS check hook failed on {path.name}: {e}"}))
        return

    failed = [c for c in results["checks"] if not c.passed]
    score = results["score"]

    if failed:
        detail_lines = [f"- {c.name}: {c.message}" for c in failed]
        summary = f"ATS check: {path.name} scored {score}/100. Failed: " + "; ".join(c.name for c in failed)
        full_detail = f"ATS check on {path.name}: {score}/100.\nFailed checks:\n" + "\n".join(detail_lines)
    else:
        summary = f"ATS check: {path.name} scored {score}/100. All checks passed."
        full_detail = summary

    output = {
        "systemMessage": summary,
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": full_detail,
        },
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
