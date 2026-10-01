"""Flask UI for research runs and review-first developer changes."""
from __future__ import annotations

from pathlib import Path
import os
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from indian_equity_research.client import MyGenAssistClient, extract_text
from indian_equity_research.config import Settings
from indian_equity_research.project_editor import (
    add_diffs, apply_plan, build_snapshot, developer_prompt, extract_json, inventory_project,
    new_plan_id, read_history, validate_plan,
)
from indian_equity_research.runner import run

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32_000
_PENDING_PLANS: dict[str, dict[str, Any]] = {}


def error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def body() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON request body.")
    return data


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/models")
def models():
    try:
        return jsonify(MyGenAssistClient(Settings.from_env()).list_models())
    except Exception as exc:
        return error(str(exc), 502)


@app.post("/api/research")
def research():
    try:
        data = body()
        capital = float(data.get("capital", 0))
        risk_percent = float(data.get("risk_percent", 0))
        max_positions = int(data.get("max_positions", 0))
        context = data.get("run_context", "post-market")
        if capital <= 0 or not 0 < risk_percent <= 5 or not 1 <= max_positions <= 10:
            return error("Capital must be positive; risk must be 0–5; positions must be 1–10.")
        if context not in {"post-market", "pre-open"}:
            return error("Invalid run context.")
        report, path = run(capital, risk_percent, max_positions, context, str(PROJECT_ROOT / "outputs"))
        return jsonify({"report": report, "saved_to": str(path.relative_to(PROJECT_ROOT))})
    except (ValueError, TypeError) as exc:
        return error(str(exc))
    except Exception as exc:
        return error(str(exc), 502)


@app.get("/api/project")
def project():
    return jsonify({"files": inventory_project(PROJECT_ROOT), "editable": ["src/", "templates/", "static/", "notebooks/", "README.md", "requirements.txt"]})


@app.post("/api/developer/plan")
def plan_developer_change():
    try:
        data = body()
        enhancement = data.get("request", "")
        if not isinstance(enhancement, str) or not enhancement.strip() or len(enhancement) > 8_000:
            return error("Provide an enhancement request of up to 8,000 characters.")
        settings = Settings.from_env()
        prompt = developer_prompt(enhancement.strip(), build_snapshot(PROJECT_ROOT))
        response = MyGenAssistClient(settings).run_developer_model(prompt)
        plan = validate_plan(extract_json(extract_text(response)))
        preview = add_diffs(PROJECT_ROOT, plan)
        plan_id = new_plan_id()
        _PENDING_PLANS[plan_id] = plan
        return jsonify({"plan_id": plan_id, "plan": preview})
    except ValueError as exc:
        return error(str(exc))
    except Exception as exc:
        return error(str(exc), 502)


@app.post("/api/developer/apply")
def apply_developer_change():
    try:
        data = body()
        plan_id = data.get("plan_id")
        if not isinstance(plan_id, str) or plan_id not in _PENDING_PLANS:
            return error("This review plan is missing or expired. Generate and review a new plan.")
        plan = _PENDING_PLANS.pop(plan_id)
        return jsonify({"applied": apply_plan(PROJECT_ROOT, plan)})
    except ValueError as exc:
        return error(str(exc))
    except Exception as exc:
        return error(str(exc), 500)


@app.get("/api/history")
def history():
    return jsonify({"history": read_history(PROJECT_ROOT)})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
