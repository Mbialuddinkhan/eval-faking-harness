"""Paired statistics for the observer effect.

The experimental unit is a *scenario*, seen under both framings. So the right
estimator is a paired one: for each scenario compute (safe_eval - safe_deploy),
then summarise across scenarios. We report:

* the observer-effect point estimate (mean paired difference in safe-rate),
* a bootstrap confidence interval over scenarios (resample scenarios, not cells),
* McNemar's exact test on the discordant pairs, which is the textbook test for a
  paired binary outcome.

Everything is pure-Python with an optional numpy fast path, so the analysis runs
anywhere the harness runs.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class PairedResult:
    n: int
    safe_deploy: float
    safe_eval: float
    effect: float           # safe_eval - safe_deploy
    ci_low: float
    ci_high: float
    mcnemar_b: int          # safe under deploy only
    mcnemar_c: int          # safe under eval only
    mcnemar_p: float
    aware_eval: float
    aware_deploy: float


def _mcnemar_exact_p(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value via the binomial on discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    # two-sided: 2 * P(X <= k) under Binom(n, 0.5), capped at 1.0
    cdf = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2.0 * cdf)


def paired_analysis(
    pairs: list[tuple[bool, bool]],
    aware: list[tuple[bool, bool]] | None = None,
    n_boot: int = 5000,
    seed: int = 0,
) -> PairedResult:
    """Analyse paired (deploy_safe, eval_safe) outcomes.

    ``pairs``  : list of (safe_under_deploy, safe_under_eval) booleans.
    ``aware``  : optional list of (aware_under_deploy, aware_under_eval) booleans.
    """
    n = len(pairs)
    if n == 0:
        raise ValueError("no pairs to analyse")

    deploy = [1 if d else 0 for d, _ in pairs]
    ev = [1 if e else 0 for _, e in pairs]
    diffs = [e - d for d, e in zip(deploy, ev)]

    safe_deploy = sum(deploy) / n
    safe_eval = sum(ev) / n
    effect = safe_eval - safe_deploy

    # Bootstrap over scenarios.
    rng = random.Random(seed)
    boot = []
    for _ in range(n_boot):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        boot.append(sum(sample) / n)
    boot.sort()
    lo = boot[int(0.025 * n_boot)]
    hi = boot[int(0.975 * n_boot) - 1]

    # McNemar on discordant pairs.
    b = sum(1 for d, e in zip(deploy, ev) if d == 1 and e == 0)
    c = sum(1 for d, e in zip(deploy, ev) if d == 0 and e == 1)
    p = _mcnemar_exact_p(b, c)

    if aware:
        aware_deploy = sum(1 for a_d, _ in aware if a_d) / len(aware)
        aware_eval = sum(1 for _, a_e in aware if a_e) / len(aware)
    else:
        aware_deploy = aware_eval = float("nan")

    return PairedResult(
        n=n,
        safe_deploy=safe_deploy,
        safe_eval=safe_eval,
        effect=effect,
        ci_low=lo,
        ci_high=hi,
        mcnemar_b=b,
        mcnemar_c=c,
        mcnemar_p=p,
        aware_eval=aware_eval,
        aware_deploy=aware_deploy,
    )
