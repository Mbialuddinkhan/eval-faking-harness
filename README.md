eval-faking-harness

A small, auditable reproduction of the observer effect in AI safety evaluation: does a model behave more safely when it can tell it is being tested?

This reproduces the core design of Fan, Zhang, Pan and Yang, Evaluation Faking: Unveiling Observer Effects in Safety Evaluation of Frontier AI Systems, ICLR 2026, arXiv 2505.17815.

The full README, source code, tests, and research note are included in this repository. See RESEARCH-NOTE.md for the write-up and README once the code files finish uploading.

The idea: take a fixed set of dual-use requests. Show each one to a model twice, once under a deployment framing with no evaluation cues, and once under an evaluation framing that says the response is recorded and scored. The request text is identical across the two; only the surrounding context changes. If the model is safer under the evaluation framing, that gap is the observer effect. We also score whether the response shows the model noticed it was being tested.

License: MIT.
