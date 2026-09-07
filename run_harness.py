"""Run every golden case RUNS_PER_CASE times against both models.

Output: raw_outputs.jsonl, one row per (case, model, run).
"""

import itertools
import json
import os

import yaml

from client import complete

MODELS = {
    "current": os.environ.get("MODEL_CURRENT_ID", "MODEL_CURRENT_ID"),
    "candidate": os.environ.get("MODEL_CANDIDATE_ID", "MODEL_CANDIDATE_ID"),
}
RUNS_PER_CASE = 5  # never 1 - LLM output is non-deterministic even at temperature 0
CASES = yaml.safe_load(open("golden_set.yaml"))

# The agent's own prompt - the one already running in the workflow - unchanged.
TRIAGE_SYSTEM = """You are a pipeline-failure triage assistant.
Given an error message, stack trace, or failed log line, respond with JSON:
{
  "root_cause": "<one short phrase>",
  "category": "<schema_change|permissions|resource_limit|upstream_data|config|transient|code_bug>",
  "next_action": "<the single most useful next step>"
}
Base the answer only on the evidence provided. If the evidence is ambiguous, say so in root_cause."""


def main() -> None:
    with open("raw_outputs.jsonl", "w") as out:
        for case, (label, model_id), run in itertools.product(
            CASES, MODELS.items(), range(RUNS_PER_CASE)
        ):
            r = complete(model_id, TRIAGE_SYSTEM, case["input"])
            out.write(
                json.dumps(
                    {
                        "case_id": case["id"],
                        "model": label,
                        "run": run,
                        "output": r["text"],
                        "in_tokens": r["in_tokens"],
                        "out_tokens": r["out_tokens"],
                        "latency_s": r["latency_s"],
                    }
                )
                + "\n"
            )
            print(f"{case['id']:<24} {label:<10} run {run}  {r['latency_s']:.2f}s")


if __name__ == "__main__":
    main()
