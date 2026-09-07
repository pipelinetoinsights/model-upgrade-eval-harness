# model-upgrade-eval-harness

A small, provider-agnostic harness for deciding whether a newly released LLM is
worth adopting in a workflow or agent you **already run in production** — not
general LLM evaluation from scratch.

It takes two model versions, runs them over a fixed set of *your own* tasks
several times each, scores the outputs the same way, and returns a decision table
across the four axes that actually cost you money and sleep:

| Axis | What it measures |
|---|---|
| Output quality on your task | Does it produce the answer you'd have written |
| Cost per run | Price per run at the tokens you actually send/receive |
| Latency | Wall-clock per call at p50 and p95 |
| Failure-mode changes | Which specific cases newly pass, which newly break |

The example task throughout is a **pipeline-failure triage agent**: given an error
message, stack trace, or failed log line, classify the likely root cause and
suggest the next step. Swap `golden_set.yaml` and the prompt in `run_harness.py`
for your own task.

Companion post: *4 Checks to Run Before Swapping a New LLM Into a Workflow You
Already Depend On* — https://pipeline2insights.substack.com (link to be added on publish).

## Layout

| File | Role |
|---|---|
| `client.py` | Thin provider-agnostic wrapper. The **only** file with a vendor SDK in it. |
| `golden_set.yaml` | The fixed, version-controlled task set. This is the whole game. |
| `run_harness.py` | Runs every case `RUNS_PER_CASE` times against both models → `raw_outputs.jsonl` |
| `judge.py` | `judge()` — grades one output against its reference answer |
| `score.py` | Applies `judge()` over `raw_outputs.jsonl` → `scored_outputs.jsonl` |
| `report.py` | Aggregates and diffs the scored runs → decision table |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export LLM_API_KEY="your-key"          # kept out of the code on purpose
export MODEL_CURRENT_ID="..."          # the model you run today
export MODEL_CANDIDATE_ID="..."        # the release you're evaluating
export MODEL_JUDGE_ID="..."            # pinned for the whole comparison
```

## Run

```bash
python run_harness.py     # -> raw_outputs.jsonl
python score.py           # -> scored_outputs.jsonl
python report.py          # -> decision table on stdout
```

Roughly `cases x RUNS_PER_CASE x 2` model calls plus one judge call each. With the
shipped set that is about 140 requests — cheap to run, but wire it into a
pre-upgrade checklist, not into CI on every commit.

## The two judge disciplines

1. **Hand-label first.** Score 20–30 outputs yourself before writing the judge
   prompt in `judge.py`; build its criteria from what you actually noticed.
2. **Spot-check the verdicts.** Read ~20% of the judge's scores against the raw
   output every run. If you disagree more than once or twice, fix the judge
   prompt before trusting any aggregate.

Pin `MODEL_JUDGE_ID` for the whole comparison. If you change the judge, earlier
scores are no longer comparable and you re-baseline.

## Limits

- Small sample. Treat single-digit percentage deltas as "no meaningful
  difference" and let the case-level diff carry the decision.
- The golden set reflects past failures and goes stale. Add a row for every new
  incident; retire cases whose root cause can no longer occur.
- The judge is a model with its own biases and can't see quality your reference
  answers don't describe. The human spot-check is not optional.

## License

MIT — see `LICENSE`.
