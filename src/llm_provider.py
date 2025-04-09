from typing import Protocol

import anthropic
from openai import OpenAI


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


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def create(self, prompt: str) -> str:
        try:
            response = self.client.responses.create(
                model="gpt-4o",
                input=prompt,
            )
            return response.output_text
        except Exception as e:
            print(f"[OpenAIProvider Error] {e}")
            return ""
