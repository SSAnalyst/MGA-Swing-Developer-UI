"""Minimal myGenAssist Agent Chat API client."""
from __future__ import annotations

import json
from typing import Any
import requests

from .config import Settings


class MyGenAssistClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def list_models(self) -> dict[str, Any]:
        response = requests.get(
            f"{self.settings.base_url}/api/v2/models",
            headers=self._headers(),
            timeout=self.settings.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def run_research_agent(self, prompt: str) -> dict[str, Any]:
        """Invoke a tool-augmented agent. Tool availability is tenant-specific."""
        payload = {
            "model": self.settings.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "agent": {
                "type": "deep_react",
                # These are the documented tool keys. The API may reject a key
                # unavailable in the caller's tenant; error handling surfaces it.
                "tool_keys": ["web_search", "reader"],
            },
        }
        return self._post_chat(payload, tool_hint="whether web_search/reader are enabled")

    def run_developer_model(self, prompt: str) -> dict[str, Any]:
        """Invoke the selected model for structured code planning without tools."""
        payload = {
            "model": self.settings.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        return self._post_chat(payload, tool_hint="that the selected model is enabled")

    def _post_chat(self, payload: dict[str, Any], tool_hint: str) -> dict[str, Any]:
        response = requests.post(
            f"{self.settings.base_url}{self.settings.agent_path}",
            headers=self._headers(),
            json=payload,
            timeout=self.settings.timeout_seconds,
        )
        if not response.ok:
            detail = response.text[:3000]
            raise RuntimeError(
                f"myGenAssist request failed ({response.status_code}). {detail}\n"
                f"Check your base URL, token, model access, and {tool_hint}."
            )
        return response.json()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }


def extract_text(response: dict[str, Any]) -> str:
    """Handle common OpenAI-compatible and agent response shapes safely."""
    choices = response.get("choices") or []
    if choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
    for key in ("output", "result", "content", "message"):
        value = response.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, dict) and isinstance(value.get("content"), str):
            return value["content"]
    return json.dumps(response, indent=2, ensure_ascii=False)
