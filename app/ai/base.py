"""
Common interface every LLM provider must implement.

Why an abstract base: the rest of the app (suggestion pipeline, eval
harness) should never need to know WHICH provider it's talking to.
It just calls `.complete(prompt)` and gets back raw text. This is what
lets us swap Groq -> Gemini -> OpenAI as a fallback chain, and also
what lets the eval script loop over providers identically.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    name: str  # e.g. "groq", "gemini", "openai" -- used for logging/eval

    @abstractmethod
    def complete(self, prompt: str, system: str = "", temperature: float = 0.1) -> str:
        """
        Send a prompt, return the raw text response.
        Implementations must raise on failure (network error, bad key,
        rate limit) -- callers are responsible for catching and
        falling back to the next provider.
        """
        raise NotImplementedError


class LLMProviderError(Exception):
    """Raised by any provider implementation on failure, so the fallback
    chain has one exception type to catch regardless of which SDK
    raised the original error."""

    pass
