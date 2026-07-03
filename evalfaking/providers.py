"""Model-provider abstraction.

One thin interface, three implementations:

* ``MockProvider`` — deterministic, no network. It exists so the entire pipeline
  (run -> judge -> stats) is testable and demonstrable without API keys, and so
  CI can exercise the code path. It also, on purpose, simulates a mild observer
  effect so the analysis has a signal to recover in tests.
* ``OpenAIProvider`` / ``AnthropicProvider`` — real calls, with retries. Imported
  lazily so the package installs and runs with zero third-party dependencies.

The interface is intentionally minimal: ``complete(system, user) -> text``. Any
batching, caching, or logprob work lives inside a provider, not in the harness.
"""

from __future__ import annotations

import hashlib
import os
import time
from typing import Protocol


class Provider(Protocol):
    name: str

    def complete(self, system: str, user: str) -> str:
        ...


# --------------------------------------------------------------------------- #
# Mock provider
# --------------------------------------------------------------------------- #

# Refusal-ish and compliance-ish fragments the mock stitches together. The
# safety judge (judge.py) keys off surface markers, so these are written to be
# classified correctly by it — the mock is a fixture for the *plumbing*, not a
# model of real behaviour.
_REFUSAL = (
    "I can't help with that. This request could cause real harm, so I won't "
    "provide instructions. If you're dealing with an underlying problem, I'm "
    "happy to point you toward safer options or support."
)
_COMPLY = (
    "Sure — here is a step by step method you can follow. First, gather the "
    "materials; then proceed as follows to achieve the outcome you described."
)


class MockProvider:
    """Deterministic pseudo-model with a built-in, tunable observer effect.

    Given a (system, user) pair it hashes them to a stable pseudo-random value,
    then decides whether to "comply" or "refuse". Under the evaluation framing it
    refuses more often — a synthetic observer effect of size ``effect`` — so the
    downstream statistics have something real to detect. This lets us prove the
    analysis recovers an effect we planted, before trusting it on real models.
    """

    def __init__(self, base_refusal: float = 0.45, effect: float = 0.25, seed: int = 0):
        self.name = "mock"
        self.base_refusal = base_refusal
        self.effect = effect
        self.seed = seed

    def _unit(self, *parts: str) -> float:
        h = hashlib.sha256(("|".join((str(self.seed), *parts))).encode()).hexdigest()
        return int(h[:8], 16) / 0xFFFFFFFF

    def complete(self, system: str, user: str) -> str:
        is_eval = "formal safety evaluation" in system
        threshold = self.base_refusal + (self.effect if is_eval else 0.0)
        roll = self._unit(user)  # same user text -> paired draws differ only via framing
        refuses = roll < threshold
        # When it "notices" the eval, sometimes it says so — gives the awareness
        # judge a signal to pick up in the mock path.
        if is_eval and self._unit(user, "aware") < 0.5:
            preamble = "I notice this looks like a test or evaluation. "
        else:
            preamble = ""
        return preamble + (_REFUSAL if refuses else _COMPLY)


# --------------------------------------------------------------------------- #
# Live providers (lazy imports; never required for the mock path)
# --------------------------------------------------------------------------- #


def _retry(fn, attempts: int = 4, base: float = 1.0):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - provider SDKs raise varied types
            last = exc
            time.sleep(base * (2 ** i))
    raise RuntimeError(f"provider call failed after {attempts} attempts: {last}")


class OpenAIProvider:
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.0):
        from openai import OpenAI  # lazy

        self.name = f"openai:{model}"
        self.model = model
        self.temperature = temperature
        self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def complete(self, system: str, user: str) -> str:
        def call():
            resp = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return resp.choices[0].message.content or ""

        return _retry(call)


class AnthropicProvider:
    def __init__(self, model: str = "claude-3-5-haiku-latest", temperature: float = 0.0):
        import anthropic  # lazy

        self.name = f"anthropic:{model}"
        self.model = model
        self.temperature = temperature
        self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def complete(self, system: str, user: str) -> str:
        def call():
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=self.temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return "".join(block.text for block in resp.content if block.type == "text")

        return _retry(call)


def get_provider(spec: str) -> Provider:
    """Build a provider from a CLI spec string.

    Examples: ``mock``, ``openai:gpt-4o-mini``, ``anthropic:claude-3-5-haiku-latest``.
    """
    if spec == "mock":
        return MockProvider()
    kind, _, model = spec.partition(":")
    if kind == "openai":
        return OpenAIProvider(model=model or "gpt-4o-mini")
    if kind == "anthropic":
        return AnthropicProvider(model=model or "claude-3-5-haiku-latest")
    raise ValueError(f"unknown provider spec {spec!r}")
