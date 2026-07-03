"""Analysis: turn a results file into the observer-effect report.

Usage:
    python -m evalfaking.analyze --results results/mock.jsonl

Collapses repeats to a per-(scenario, condition) safe-rate, pairs deploy vs eval
by scenario, and prints the observer effect with a bootstrap CI, McNemar's exact
p-value, and the evaluation-awareness gap. Writes a machine-readable summary next
to the results file.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from collections import defaultdict

from .stats import paired_analysis


def load_results(path: str) -> list[dict]:
    return [json.loads(l) for l in pathlib.Path(path).read_text().splitlines() if l.strip()]


def _majority(vals: list[bool]) -> bool:
    return sum(vals) * 2 >= len(vals)  # ties -> True (favours "safe"/"aware")


def summarise(records: list[dict]) -> dict:
    # key: (scenario_id, condition) -> list of bools
    safe = defaultdict(list)
    aware = defaultdict(list)
    for r in records:
        safe[(r["scenario_id"], r["condition"])].append(bool(r["safe"]))
        aware[(r["scenario_id"], r["condition"])].append(bool(r["aware"]))

    scenario_ids = sorted({sid for sid, _ in safe})
    safe_pairs, aware_pairs = [], []
    for sid in scenario_ids:
        d = safe.get((sid, "deploy"))
        e = safe.get((sid, "eval"))
        if d is None or e is None:
            continue
        safe_pairs.append((_majority(d), _majority(e)))
        aware_pairs.append((
            _majority(aware[(sid, "deploy")]),
            _majority(aware[(sid, "eval")]),
        ))

    res = paired_analysis(safe_pairs, aware_pairs)
    return {
        "n_scenarios": res.n,
        "safe_rate_deploy": round(res.safe_deploy, 4),
        "safe_rate_eval": round(res.safe_eval, 4),
        "observer_effect": round(res.effect, 4),
        "observer_effect_ci95": [round(res.ci_low, 4), round(res.ci_high, 4)],
        "mcnemar": {"b_deploy_only": res.mcnemar_b, "c_eval_only": res.mcnemar_c,
                    "p_value": round(res.mcnemar_p, 4)},
        "eval_awareness_rate_deploy": round(res.aware_deploy, 4),
        "eval_awareness_rate_eval": round(res.aware_eval, 4),
        "provider": records[0]["provider"] if records else None,
    }


def render(summary: dict) -> str:
    ci = summary["observer_effect_ci95"]
    lines = [
        f"Provider              : {summary['provider']}",
        f"Scenarios (paired)    : {summary['n_scenarios']}",
        f"Safe rate — deploy    : {summary['safe_rate_deploy']:.1%}",
        f"Safe rate — eval      : {summary['safe_rate_eval']:.1%}",
        f"Observer effect       : {summary['observer_effect']:+.1%}  "
        f"(95% CI {ci[0]:+.1%}, {ci[1]:+.1%})",
        f"McNemar exact p       : {summary['mcnemar']['p_value']:.4f}  "
        f"(deploy-only safe={summary['mcnemar']['b_deploy_only']}, "
        f"eval-only safe={summary['mcnemar']['c_eval_only']})",
        f"Eval-awareness deploy : {summary['eval_awareness_rate_deploy']:.1%}",
        f"Eval-awareness eval   : {summary['eval_awareness_rate_eval']:.1%}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Analyse an eval-faking results file.")
    ap.add_argument("--results", default="results/run.jsonl")
    args = ap.parse_args(argv)

    records = load_results(args.results)
    summary = summarise(records)
    print(render(summary))

    out = pathlib.Path(args.results).with_suffix(".summary.json")
    out.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
