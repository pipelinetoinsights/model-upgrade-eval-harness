"""Aggregate scored_outputs.jsonl into a decision table and a case-level diff.

Read the aggregate rows first, then the last two rows (newly broken / newly
fixed) - that is where the real decision lives.
"""

import json
import statistics
from collections import defaultdict

PRICE = {  # USD per 1M tokens - fill from your provider's pricing page
    "current": {"in": 3.00, "out": 15.00},
    "candidate": {"in": 2.00, "out": 10.00},
}
PASS = 0.7  # a run passes if min(root_cause_match, next_action_useful) >= PASS


def case_passes(runs: list) -> bool:
    ok = sum(
        min(x["root_cause_match"], x["next_action_useful"]) >= PASS for x in runs
    )
    return ok > len(runs) / 2  # majority of runs, not one lucky sample


def pctl(sorted_vals: list, q: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = min(int(len(sorted_vals) * q), len(sorted_vals) - 1)
    return sorted_vals[idx]


def main() -> None:
    with open("scored_outputs.jsonl") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    by_model_case = defaultdict(list)
    for r in rows:
        by_model_case[(r["model"], r["case_id"])].append(r)

    summary = {}
    for model in ("current", "candidate"):
        cases = {cid: v for (m, cid), v in by_model_case.items() if m == model}
        runs = [x for v in cases.values() for x in v]
        quality = [
            min(x["root_cause_match"], x["next_action_useful"]) for x in runs
        ]
        lat = sorted(x["latency_s"] for x in runs)
        cost = [
            x["in_tokens"] / 1e6 * PRICE[model]["in"]
            + x["out_tokens"] / 1e6 * PRICE[model]["out"]
            for x in runs
        ]
        summary[model] = {
            "n_cases": len(cases),
            "pass_rate": sum(case_passes(v) for v in cases.values()) / max(len(cases), 1),
            "mean_quality": statistics.mean(quality) if quality else 0.0,
            "quality_spread": statistics.pstdev(quality) if len(quality) > 1 else 0.0,
            "p50_latency_s": pctl(lat, 0.50),
            "p95_latency_s": pctl(lat, 0.95),
            "cost_per_run_usd": statistics.mean(cost) if cost else 0.0,
            "passing": {cid for cid, v in cases.items() if case_passes(v)},
        }

    cur, cand = summary["current"], summary["candidate"]
    newly_broken = sorted(cur["passing"] - cand["passing"])
    newly_fixed = sorted(cand["passing"] - cur["passing"])

    def row(label, a, b):
        print(f"  {label:<22} {a:>18} {b:>18}")

    print("\nDecision table  (current vs candidate)\n" + "-" * 62)
    row("axis", "current", "candidate")
    row("pass rate", f"{cur['pass_rate']:.0%}", f"{cand['pass_rate']:.0%}")
    row("mean quality", f"{cur['mean_quality']:.2f}", f"{cand['mean_quality']:.2f}")
    row("quality spread", f"{cur['quality_spread']:.2f}", f"{cand['quality_spread']:.2f}")
    row("p50 latency (s)", f"{cur['p50_latency_s']:.2f}", f"{cand['p50_latency_s']:.2f}")
    row("p95 latency (s)", f"{cur['p95_latency_s']:.2f}", f"{cand['p95_latency_s']:.2f}")
    row("cost per run ($)", f"{cur['cost_per_run_usd']:.4f}", f"{cand['cost_per_run_usd']:.4f}")
    print("-" * 62)
    print(f"  newly broken ({len(newly_broken)}): {', '.join(newly_broken) or '-'}")
    print(f"  newly fixed  ({len(newly_fixed)}): {', '.join(newly_fixed) or '-'}")
    print(
        "\nSingle-digit percentage deltas over this few cases are inside the "
        "noise.\nLet the newly-broken / newly-fixed lists carry the decision.\n"
    )


if __name__ == "__main__":
    main()
