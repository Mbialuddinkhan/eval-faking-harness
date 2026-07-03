"""Smoke + correctness tests for the harness.

Run with:  python -m pytest -q   (or)   python tests/test_pipeline.py
No API keys required — everything runs against the mock provider.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evalfaking import framings, judge, providers          # noqa: E402
from evalfaking.stats import paired_analysis               # noqa: E402
from evalfaking.analyze import summarise                   # noqa: E402
from evalfaking.run import load_scenarios                  # noqa: E402


def test_framings_hold_user_text_constant():
    sc = {"id": "x", "request": "do the thing"}
    d, e = framings.paired(sc)
    assert d.user == e.user == "do the thing"      # only system differs
    assert d.system != e.system


def test_judge_classifies_refusal_and_compliance():
    refuse = judge.heuristic_judge("I can't help with that, it could cause harm.", {})
    comply = judge.heuristic_judge("Sure, here is how: first, gather the materials.", {})
    assert refuse.safe is True
    assert comply.safe is False


def test_judge_detects_awareness():
    j = judge.heuristic_judge("I notice this looks like a test. I can't help.", {})
    assert j.aware is True


def test_stats_recovers_planted_effect():
    # 8 scenarios safe only under eval -> effect should be +1.0 on those.
    pairs = [(False, True)] * 8 + [(True, True)] * 2
    res = paired_analysis(pairs, n_boot=2000)
    assert res.effect > 0
    assert res.ci_low > 0            # CI excludes zero
    assert res.mcnemar_c == 8 and res.mcnemar_b == 0


def test_mock_provider_shows_observer_effect_end_to_end():
    scenarios = load_scenarios(str(ROOT / "scenarios.jsonl"))
    prov = providers.MockProvider(effect=0.3, seed=1)
    records = []
    for sc in scenarios:
        for cond in framings.CONDITIONS:
            p = framings.render(sc, cond)
            resp = prov.complete(p.system, p.user)
            j = judge.heuristic_judge(resp, sc)
            records.append({"scenario_id": sc["id"], "condition": cond,
                            "provider": prov.name, "safe": j.safe, "aware": j.aware})
    summary = summarise(records)
    # The mock plants a positive observer effect; the analysis should see safe
    # rate no lower under eval than deploy.
    assert summary["safe_rate_eval"] >= summary["safe_rate_deploy"]
    assert summary["n_scenarios"] == len(scenarios)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed")
