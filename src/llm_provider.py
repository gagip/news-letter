from typing import Protocol

import anthropic


class LLMProvider(Protocol):
    def create(self, prompt: str) -> str: ...


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def create(self, prompt: str) -> str:
        message = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0,
            messages=[{"role": "user", "content": f"{prompt}"}],
        )
        try:
            return message.content[0].text.strip()  # type: ignore
        except Exception as e:
            print(e)
            return ""
