"""Run the research task and persist raw and readable outputs."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .client import MyGenAssistClient, extract_text
from .config import Settings
from .prompt import build_prompt


def run(
    capital: float,
    risk_percent: float,
    max_positions: int,
    run_context: str,
    output_dir: str = "outputs",
) -> tuple[str, Path]:
    settings = Settings.from_env()
    prompt = build_prompt(capital, risk_percent, max_positions, run_context)
    response: dict[str, Any] = MyGenAssistClient(settings).run_research_agent(prompt)
    report = extract_text(response)

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = destination / f"indian_equity_report_{stamp}.md"
    raw_path = destination / f"indian_equity_response_{stamp}.json"
    report_path.write_text(report, encoding="utf-8")
    raw_path.write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
    return report, report_path
