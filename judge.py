"""Grade one triage answer against its known-good reference.

Read 20-30 outputs by hand and score them yourself before trusting this prompt.
The criteria here should come from what you noticed, not from what sounds
reasonable. Pin MODEL_JUDGE_ID for the whole comparison.
"""

import json
import os
import re

from client import complete

JUDGE_MODEL = os.environ.get("MODEL_JUDGE_ID", "MODEL_JUDGE_ID")

JUDGE_SYSTEM = """You are grading a pipeline-triage answer against a known-good reference.
Score two things from 0 to 1:
- root_cause_match: does the answer identify the same underlying cause as the reference
- next_action_useful: would the reference author accept this next step as correct and specific
Return JSON only: {"root_cause_match": <float>, "next_action_useful": <float>, "note": "<one line>"}"""


def _extract_json(text: str) -> dict:
    """Models sometimes wrap JSON in prose or code fences. Pull the first object."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def judge(case: dict, answer_text: str) -> dict:
    user = (
        f"CASE INPUT:\n{case['input']}\n\n"
        f"REFERENCE ROOT CAUSE: {case['expected_root_cause']}\n"
        f"REFERENCE NEXT ACTION: {case['expected_next_action']}\n\n"
        f"ANSWER UNDER TEST:\n{answer_text}"
    )
    r = complete(JUDGE_MODEL, JUDGE_SYSTEM, user)
    verdict = _extract_json(r["text"])
    return {
        "root_cause_match": float(verdict["root_cause_match"]),
        "next_action_useful": float(verdict["next_action_useful"]),
        "note": verdict.get("note", ""),
    }
