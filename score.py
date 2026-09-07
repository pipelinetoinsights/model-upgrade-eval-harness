"""Apply judge() over raw_outputs.jsonl -> scored_outputs.jsonl.

This is the glue between run_harness.py and report.py: it carries every raw field
through and adds root_cause_match, next_action_useful, and the judge's note.
"""

import json

import yaml

from judge import judge

CASES_BY_ID = {c["id"]: c for c in yaml.safe_load(open("golden_set.yaml"))}


def main() -> None:
    with open("raw_outputs.jsonl") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    with open("scored_outputs.jsonl", "w") as out:
        for i, row in enumerate(rows, 1):
            case = CASES_BY_ID[row["case_id"]]
            try:
                verdict = judge(case, row["output"])
            except Exception as exc:  # judge returned unparseable output
                verdict = {
                    "root_cause_match": 0.0,
                    "next_action_useful": 0.0,
                    "note": f"judge error: {exc}",
                }
            out.write(json.dumps({**row, **verdict}) + "\n")
            print(f"[{i}/{len(rows)}] {row['case_id']:<24} {row['model']:<10} "
                  f"rc={verdict['root_cause_match']:.2f} na={verdict['next_action_useful']:.2f}")


if __name__ == "__main__":
    main()
