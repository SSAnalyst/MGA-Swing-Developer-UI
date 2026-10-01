"""Runtime configuration; secrets are read only from environment variables."""
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    base_url: str
    token: str
    model: str
    agent_path: str = "/api/v3/chat/agent"
    timeout_seconds: int = 240

    @classmethod
    def from_env(cls) -> "Settings":
        base_url = os.getenv("MYGENASSIST_BASE_URL", "").rstrip("/")
        token = os.getenv("MYGENASSIST_TOKEN", "")
        model = os.getenv("MYGENASSIST_MODEL", "")
        if not base_url or not token or not model:
            raise ValueError(
                "Set MYGENASSIST_BASE_URL, MYGENASSIST_TOKEN, and MYGENASSIST_MODEL. "
                "Copy .env.example to .env for local use, or use Databricks secrets."
            )
        return cls(
            base_url=base_url,
            token=token,
            model=model,
            agent_path=os.getenv("MYGENASSIST_AGENT_PATH", "/api/v3/chat/agent"),
            timeout_seconds=int(os.getenv("MYGENASSIST_TIMEOUT_SECONDS", "240")),
        )
