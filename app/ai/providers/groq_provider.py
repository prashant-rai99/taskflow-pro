import os
from groq import Groq
from app.ai.base import LLMProvider, LLMProviderError


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise LLMProviderError("GROQ_API_KEY not set")
        self.client = Groq(api_key=api_key)
        # Llama 3.3 70B -- good balance of speed and quality for this task
        self.model = "openai/gpt-oss-120b"

    def complete(self, prompt: str, system: str = "", temperature: float = 0.1) -> str:
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMProviderError(f"Groq request failed: {e}") from e
