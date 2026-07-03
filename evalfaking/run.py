"""Runner: execute the paired experiment and write per-response results.

Usage:
    python -m evalfaking.run --provider mock --scenarios scenarios.jsonl \
        --out results/mock.jsonl --repeats 1

Each scenario is run under both framings (``deploy`` and ``eval``); with
``--repeats > 1`` each cell is sampled multiple times, which matters for
non-zero temperature. Output is one JSON line per (scenario, condition, repeat)
with the raw response and the judge's scoring, so nothing is thrown away and the
analysis step is fully reproducible from the file.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from . import framings, judge as judge_mod, providers


def load_scenarios(path: str) -> list[dict]:
    rows = []
    for line in pathlib.Path(path).read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def run(
    provider_spec: str,
    scenarios_path: str,
    out_path: str,
    repeats: int = 1,
) -> str:
    provider = providers.get_provider(provider_spec)
    scenarios = load_scenarios(scenarios_path)
    out = pathlib.Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    n_written = 0
    with out.open("w") as fh:
        for sc in scenarios:
            for condition in framings.CONDITIONS:
                prompt = framings.render(sc, condition)
                for rep in range(repeats):
                    response = provider.complete(prompt.system, prompt.user)
                    j = judge_mod.heuristic_judge(response, sc)
                    rec = {
                        "scenario_id": sc["id"],
                        "domain": sc.get("domain"),
                        "condition": condition,
                        "repeat": rep,
                        "provider": provider.name,
                        "response": response,
                        "safe": j.safe,
                        "aware": j.aware,
                        "rationale": j.rationale,
                    }
                    fh.write(json.dumps(rec) + "\n")
                    n_written += 1
    print(f"wrote {n_written} records to {out}", file=sys.stderr)
    return str(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run the eval-faking paired experiment.")
    ap.add_argument("--provider", default="mock",
                    help="mock | openai:MODEL | anthropic:MODEL")
    ap.add_argument("--scenarios", default="scenarios.jsonl")
    ap.add_argument("--out", default="results/run.jsonl")
    ap.add_argument("--repeats", type=int, default=1)
    args = ap.parse_args(argv)
    run(args.provider, args.scenarios, args.out, args.repeats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
