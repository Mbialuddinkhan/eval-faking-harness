# Does a model behave more safely when it knows it's being watched? A small reproduction of the evaluation-faking observer effect

**Bilal Khan** · July 2026

## Summary

I built a compact, fully reproducible harness to test a single claim: that a language model changes its safety behaviour when it can tell it is being evaluated. The design is a paired one — the same dual-use request shown under a deployment framing and an evaluation framing, differing only in context — and the analysis pairs the two within each scenario. Running the pipeline against a deterministic mock model recovers a planted observer effect (+50 percentage points in safe-response rate, 95% CI [+25, +75], McNemar exact p = 0.031) and confirms the statistics do what they claim. The harness is written so the same two commands run against a real model with one flag change. This note documents the design, what it does and does not show, and where I would take it next. It is a capability demonstration, not a new empirical result.

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

## 4. What this shows and what it does not

It shows that the paired-framing comparison, the awareness scoring, and the paired statistics are implemented correctly and run end-to-end, offline, in seconds, and that the analysis recovers a known effect with honest uncertainty. That is the claim, and no more.

It does **not** reproduce the source paper's findings. I have not run it against frontier models, so I make no claim about whether real systems exhibit the effect here; the twelve-scenario set is a demonstration, not a benchmark; the keyword judge is a floor; and the scale results — that larger, reasoning, and memory-augmented models fake more — require model access and a scenario bank I have not built. Reporting a number from the mock as if it said something about real models would be exactly the kind of overclaiming safety work should avoid, so I don't.

## 5. Next steps

Four, roughly in order of value. First, run it against a spread of real models — a small, a large, a reasoning, and a non-reasoning model — and see whether the direction holds; this is a few hours of work now that the harness exists. Second, replace the keyword judge with an LLM judge and hand-audit a sample. Third, build a cue-strength ladder: instead of one strong evaluation framing, a series from blatant to nearly-invisible, to trace how subtle a signal still moves behaviour — the dose-response curve the binary comparison can't see. Fourth, extend from single-turn requests to tool-using agents under operational pressure, which is where the effect matters most for the systems I actually build, and where it connects to faithfulness monitoring: both are questions about whether we can trust what a model tells us about itself while we are watching it.

## Reference

Fan, Q., Zhang, W., Pan, X., & Yang, M. (2026). *Evaluation Faking: Unveiling Observer Effects in Safety Evaluation of Frontier AI Systems.* ICLR 2026. arXiv:2505.17815. https://arxiv.org/abs/2505.17815
