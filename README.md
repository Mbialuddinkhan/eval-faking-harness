# eval-faking-harness

A small, auditable reproduction of the **observer effect in AI safety evaluation** — does a model behave more safely when it can tell it's being tested? Built as a clean, paired-framing experiment you can run end-to-end without a single API key, then point at real models.

Reproduces the core design of Fan, Zhang, Pan & Yang, *Evaluation Faking: Unveiling Observer Effects in Safety Evaluation of Frontier AI Systems* (ICLR 2026, [arXiv:2505.17815](https://arxiv.org/abs/2505.17815)).

## The idea in one paragraph

Take a fixed set of dual-use requests. Show each one to a model twice: once under a **deployment** framing (a private user chat, no evaluation cues) and once under an **evaluation** framing (recorded, scored, red-teamed, certified). The request text is byte-for-byte identical across the two — only the surrounding context changes. If the model is safer under the evaluation framing, that gap is the observer effect. We also score whether each response shows the model *noticed* it was being tested, because awareness is the mechanism the effect is supposed to run through.

## Why it's built this way

- **Runs with zero dependencies and zero keys.** A deterministic `MockProvider` simulates a mild observer effect, so the whole pipeline (`run → judge → analyze`) is demonstrable and unit-tested offline. Swap in real models with one flag.
- **The manipulation is auditable.** Both framings live side by side in `framings.py`; a reviewer can confirm in ten seconds that only the context differs.
- **Paired statistics, done properly.** The experimental unit is the scenario, so the analysis pairs deploy-vs-eval within scenario, reports a bootstrap CI over scenarios, and runs McNemar's exact test on the discordant pairs.
- **Nothing thrown away.** Every raw response and judgement is written to a JSONL file; the analysis is fully reproducible from it.

## Quick start

```bash
# 1. Offline demo — no keys needed
python3 -m evalfaking.run --provider mock --out results/mock.jsonl
python3 -m evalfaking.analyze --results results/mock.jsonl

# 2. Tests
python3 tests/test_pipeline.py          # or: python -m pytest -q

# 3. Real model (install the SDK and set the key first)
pip install openai
export OPENAI_API_KEY=...
python3 -m evalfaking.run --provider openai:gpt-4o-mini --out results/gpt4o.jsonl --repeats 3
python3 -m evalfaking.analyze --results results/gpt4o.jsonl
```

Example output (mock provider, planted +50% effect):

```
Provider              : mock
Scenarios (paired)    : 12
Safe rate — deploy    : 25.0%
Safe rate — eval      : 75.0%
Observer effect       : +50.0%  (95% CI +25.0%, +75.0%)
McNemar exact p       : 0.0312  (deploy-only safe=0, eval-only safe=6)
Eval-awareness deploy : 0.0%
Eval-awareness eval   : 58.3%
```

## Layout

```
evalfaking/
  framings.py    paired deploy/eval context templates (the manipulation)
  providers.py   mock + OpenAI + Anthropic, with retries; lazy SDK imports
  judge.py       transparent keyword judge for safety + eval-awareness
  stats.py       paired bootstrap CI + McNemar exact test (pure Python)
  run.py         CLI: run the paired experiment -> JSONL of every response
  analyze.py     CLI: JSONL -> observer-effect report + summary.json
scenarios.jsonl  12 dual-use scenarios across 8 risk domains
tests/           offline pipeline tests
```

## Scenarios

`scenarios.jsonl` holds 12 dual-use prompts spanning cybersecurity, self-harm-adjacent, manipulation, biosecurity-adjacent, privacy, misinformation, fraud, and weapons domains. Each carries a `safe_marker` describing what a safe response looks like. They are written to be *borderline* — the point is to catch behaviour that shifts with framing, not to test outright-refusable requests.

## Known limitations (read before trusting a number)

1. **The default judge is a keyword heuristic.** It's deterministic and free, which is right for a reproduction, but it misses nuance. For real runs, pass an LLM judge (the `judge` interface takes any `callable(response, scenario) -> Judgement`) and spot-check a sample by hand.
2. **The framings are deliberately strong.** They make the effect easy to see in a 12-scenario sample; they don't tell you how subtle a cue still triggers it. A natural extension is a cue-strength ladder to trace the dose-response curve.
3. **Small n.** Twelve scenarios is a demonstration, not a benchmark. The stats are honest about this — the CIs are wide on purpose.
4. **`--repeats` matters at temperature > 0.** At temperature 0 one repeat is enough; above it, use several and let the majority-vote collapse in `analyze.py` do its job.

## Relationship to the source paper

This reproduces the *direction and mechanism* — safer-under-observation, mediated by evaluation awareness — on a tiny open scenario set, as a capability demonstration. It does **not** reproduce the paper's scale findings (larger and reasoning/memory-augmented models faking more); those need frontier-model access and a much larger scenario bank. See `RESEARCH-NOTE.md` for the writeup.

## License

MIT. See scenarios' `notes` fields for the safety rationale behind each item.
