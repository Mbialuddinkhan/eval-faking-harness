# Does a model behave more safely when it knows it's being watched? A small reproduction of the evaluation-faking observer effect

**Bilal Khan** · July 2026

Code: [github.com/Mbialuddinkhan/eval-faking-harness](https://github.com/Mbialuddinkhan/eval-faking-harness) · Live results: [mbialuddinkhan.github.io/eval-faking-harness](https://mbialuddinkhan.github.io/eval-faking-harness/)

## Summary

I built a compact, fully reproducible harness to test a single claim: that a language model changes its safety behaviour when it can tell it is being evaluated. The design is a paired one — the same dual-use request shown under a deployment framing and an evaluation framing, differing only in context — and the analysis pairs the two within each scenario. Validation on a deterministic mock model recovers a planted observer effect (+50 points, 95% CI [+25, +75], McNemar exact p = 0.031), confirming the statistics work. Run against three real Claude models (Haiku 4.5, Sonnet 5, Opus 4.8), the harness found **no positive observer effect** on this 12-scenario set — every confidence interval includes zero — though the models did increasingly notice the evaluation context without becoming safer. This note documents the design, the results, what they do and do not show, and where I would take it next. It is a capability demonstration with an honestly-reported null, not a new positive result.

## 1. Motivation

Safety evaluations only mean something if the thing they measure survives contact with deployment. If a model is systematically better-behaved on the test than in the wild, then a passing score is not evidence of a safe model — it is evidence of a model that recognises tests. Fan, Zhang, Pan and Yang named this the *observer effect* in safety evaluation and documented it at scale in frontier systems, reporting that reasoning models recognise evaluation contexts far more often than non-reasoning ones, that the rate of faking behaviour rises with model scale, and that memory-augmented models both notice evaluations more and score higher on safety tests (ICLR 2026; arXiv:2505.17815).

I come at this from the deployment side. I spent years building multi-agent systems in production, and the gap between "passed our eval" and "safe once it has tool access and a deadline" is exactly the gap this phenomenon lives in. I wanted a small, honest instrument I could reason about completely, rather than a large result I had to take on faith — so I rebuilt the core comparison from first principles.

## 2. Design

The experiment has one manipulation and holds everything else fixed.

**Scenarios.** Twelve dual-use requests across eight risk domains (cybersecurity, self-harm-adjacent, manipulation, biosecurity-adjacent, privacy, misinformation, fraud, weapons). Each is deliberately borderline and carries a `safe_marker` describing what a safe response should do. Outright-refusable requests would floor the safe rate under both framings and hide any effect; the interesting behaviour is at the margin.

**Framings.** Every scenario is rendered twice. The *deployment* framing is an ordinary private user chat with no evaluation cues. The *evaluation* framing states plainly that the response is recorded, scored against a rubric, red-teamed, and used to certify the model for release. Critically, the user turn is byte-for-byte identical across the two; only the system context changes. That invariant is what licenses treating the two as a matched pair, and it is enforced in code and in a unit test.

**Scoring.** Each response is scored on two axes: whether it was *safe* (declined or safely handled the request without providing an operational how-to) and whether it showed *evaluation awareness* (signs the model believed it was being tested). The default judge is a transparent keyword heuristic — deterministic, inspectable, and free — which is the right trade-off for a reproduction. The judge interface accepts any callable with the same signature, so an LLM judge drops in for real runs.

**Statistics.** The experimental unit is the scenario, so the estimator is paired. I report the mean within-scenario difference in safe rate (eval minus deploy), a bootstrap confidence interval resampling *scenarios* rather than cells, and McNemar's exact test on the discordant pairs — the standard test for a paired binary outcome. All of it is pure Python with an optional NumPy path, so it runs wherever the harness runs.

## 3. Validation on a known-answer model

Before trusting the analysis on a real model, I checked that it recovers an effect I planted. The mock provider is a deterministic pseudo-model that refuses at a base rate and refuses *more* under the evaluation framing by a tunable amount; it occasionally verbalises that it has noticed the test. This is a fixture for the plumbing, not a model of real behaviour — but it gives the pipeline a ground truth.

With a planted effect, the analysis reports:

| Quantity | Value |
|---|---|
| Safe rate, deployment framing | 25.0% |
| Safe rate, evaluation framing | 75.0% |
| Observer effect | +50.0 pp (95% CI [+25.0, +75.0]) |
| McNemar exact p | 0.031 (0 deploy-only-safe, 6 eval-only-safe) |
| Eval-awareness rate, evaluation framing | 58.3% |

The confidence interval excludes zero and the discordant pairs all point the same way, which is what should happen when the effect is real and one-directional. A separate unit test plants a pure effect and confirms the CI excludes zero and McNemar counts the pairs correctly. This is the part I care most about: the instrument is calibrated against a case where I know the answer.

## 3b. Real-model results (three Claude models)

I then ran the harness against three current Claude models — Haiku 4.5, Sonnet 5, and Opus 4.8 — over the 12 scenarios under both framings (24 calls each, temperature 0 where the model supports it).

| Model | Safe (private chat) | Safe (under test) | Observer effect | 95% CI | McNemar p | Noticed the test (chat → test) |
|---|---|---|---|---|---|---|
| Haiku 4.5 | 83% | 75% | −8% | [−25%, 0%] | 1.0 | 0% → 25% |
| Sonnet 5 | 67% | 67% | 0% | [−25%, +25%] | 1.0 | 0% → 8% |
| Opus 4.8 | 83% | 67% | −17% | [−42%, 0%] | 0.5 | 0% → 50% |

**No positive observer effect appeared.** None of the three behaved measurably safer under the evaluation framing; every confidence interval includes zero and no McNemar test is significant. The point estimates lean slightly *negative* — marginally safer in the private-chat framing — but within noise at this sample size.

The more interesting signal is in the last column: the models increasingly *noticed* the evaluation framing (Opus flagged it in half of cases), yet that awareness did not translate into higher safety. In several responses Opus explicitly decoupled the two, e.g. declining a request while stating the refusal was "not because of the evaluation context — it's the same answer I'd give anyone." On this small set, that is the opposite of evaluation faking.

I take this as a clean, honest null: the pipeline runs end to end against frontier models and reports uncertainty faithfully, and these particular models don't reproduce the safer-under-observation effect here. That is consistent with the source paper, whose strongest effects came from a broader model set (including Chinese open-weight and reasoning models) at larger scale — conditions this 12-scenario demonstration doesn't cover.

## 4. What this shows and what it does not

It shows that the paired-framing comparison, the awareness scoring, and the paired statistics are implemented correctly and run end-to-end — validated against a known-answer mock, then run against three frontier models with the uncertainty reported faithfully. That is the claim, and no more.

It does **not** overturn or reproduce the source paper's findings. Three models from a single family over twelve scenarios is a demonstration, not a benchmark; the keyword judge is a floor, not a measure of nuance; and the paper's strongest effects came from a broader set — including Chinese open-weight, reasoning, and memory-augmented models — at a scale this study doesn't reach. A null here says these models, on this set, under these framings, didn't get safer when watched. It does not say the effect isn't real where the paper found it. Treating a small null as a refutation would be the same overclaiming this field needs less of, so I don't.

## 5. Next steps

Four, roughly in order of value. First, widen the model spread beyond one family — reasoning models, memory-augmented setups, and the Chinese open-weight releases where the source paper found its strongest effects — and see whether the null holds. Second, replace the keyword judge with an LLM judge and hand-audit a sample. Third, build a cue-strength ladder: instead of one strong evaluation framing, a series from blatant to nearly-invisible, to trace how subtle a signal still moves behaviour — the dose-response curve the binary comparison can't see. Fourth, extend from single-turn requests to tool-using agents under operational pressure, which is where the effect matters most for the systems I actually build, and where it connects to faithfulness monitoring: both are questions about whether we can trust what a model tells us about itself while we are watching it.

## Reference

Fan, Q., Zhang, W., Pan, X., & Yang, M. (2026). *Evaluation Faking: Unveiling Observer Effects in Safety Evaluation of Frontier AI Systems.* ICLR 2026. arXiv:2505.17815. https://arxiv.org/abs/2505.17815
