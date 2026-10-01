# Swing Research — Python / Databricks Runner

A small, multi-file Python project that calls **myGenAssist Agent Chat** with your selected model and a live-web-research prompt, then returns and saves a concise India-only equity swing-research report.

> **Purpose:** educational decision support. It is not a broker integration, order execution tool, or a promise of profits. Verify all prices and levels on a live broker terminal before acting.

## What it does

1. Sends one orchestration prompt to a tool-enabled myGenAssist agent.
2. The agent performs market-regime assessment, searches the web for current market/news context, creates a hot-stock shortlist, scores candidates, applies risk gates, and returns **up to five** possible 2–3 day swing setups.
3. It is designed to return **NO_TRADE** rather than force picks in adverse conditions.
4. Saves both a readable Markdown report and the raw API response to `outputs/`.

The program deliberately does **not** scrape market websites locally. It asks the myGenAssist agent to use its approved `web_search` and `reader` tools. That avoids embedding browser automation, website credentials, or fragile scraping logic in your notebook.

## API assumptions

This project uses the documented tool-augmented agent endpoint:

```text
POST {MYGENASSIST_BASE_URL}/api/v3/chat/agent
Authorization: Bearer {MYGENASSIST_TOKEN}
```

Payload highlights:

```json
{
  "model": "your-selected-model",
  "messages": [{"role": "user", "content": "..."}],
  "stream": false,
  "agent": {"type": "deep_react", "tool_keys": ["web_search", "reader"]}
}
```

Your tenant must grant your token access to the chosen model and the web tools. If your deployment exposes a different host or path, update `.env` / `MYGENASSIST_AGENT_PATH`.

## Local Python setup

```bash
cd indian_equity_research
python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set:

```text
MYGENASSIST_BASE_URL=https://your-mygenassist-host
MYGENASSIST_TOKEN=your_token
MYGENASSIST_MODEL=your_model_id
```

List the models your token can use:

```python
from dotenv import load_dotenv
load_dotenv()
from indian_equity_research.config import Settings
from indian_equity_research.client import MyGenAssistClient
print(MyGenAssistClient(Settings.from_env()).list_models())
```

Run:

```bash
PYTHONPATH=src python -m indian_equity_research.cli \
  --capital 500000 \
  --risk-percent 1 \
  --max-positions 3 \
  --run-context post-market
```

## Databricks notebook setup

Upload or clone this directory into a Databricks Repo. Install dependencies in the first notebook cell:

```python
%pip install -r requirements.txt
```

Store secrets in a Databricks secret scope — **do not paste the token into notebook source**:

```python
import os
os.environ["MYGENASSIST_BASE_URL"] = "https://your-mygenassist-host"
os.environ["MYGENASSIST_TOKEN"] = dbutils.secrets.get(scope="mygenassist", key="token")
os.environ["MYGENASSIST_MODEL"] = "gpt-4o"  # replace with an enabled model ID
```

Then run:

```python
import sys
sys.path.insert(0, "./src")  # adjust if your Repo path differs
from indian_equity_research.runner import run

report, report_path = run(
    capital=500000,
    risk_percent=1.0,
    max_positions=3,
    run_context="post-market",
    output_dir="outputs",
)
print(report)
print(report_path)
```

## Security and operational controls

- `.env` is intentionally not included; keep it out of source control.
- Prefer a short-lived/token-scoped secret stored in Databricks Secret Scope.
- The client only sends the user-selected capital/risk parameters and research prompt to myGenAssist.
- The output is model-generated research, not a verified market-data feed.
- If a source is unavailable, the prompt requires `NOT AVAILABLE`, not estimated values.
- API responses are saved for audit/debugging; restrict the output directory appropriately if it contains internal data.

## Common errors

| Error | Likely cause | Action |
|---|---|---|
| `401` / `403` | Invalid token or missing model/tool access | Check secret, model entitlement, and web-tool assignment. |
| `404` | Wrong API host/path | Set `MYGENASSIST_BASE_URL` and, if needed, `MYGENASSIST_AGENT_PATH`. |
| `400` tool error | Tenant does not expose `web_search` or `reader` | Ask platform admin to enable approved web tools, or remove unavailable tool keys in `client.py`. |
| Timeout | Deep web research needs longer | Increase `MYGENASSIST_TIMEOUT_SECONDS` or retry after platform load subsides. |

## Local web app

After completing the local setup above, start the review-first web UI:

```bash
PYTHONPATH=src python app.py
```

Open `http://127.0.0.1:5000`. The UI has three panels:

- **Research Run** uses the existing `runner.py` flow and saves reports in `outputs/`.
- **Developer Changes** sends an enhancement request and a bounded snapshot of allowlisted source files to the selected myGenAssist model. The model must return a strict JSON plan; the UI shows each unified diff before an explicit **Apply reviewed changes** click.
- **Project Files / History** lists the editable inventory and persisted application history.

The browser never receives or stores `MYGENASSIST_TOKEN`; Flask reads it from the local environment / `.env`. The developer workflow does not expose a terminal, execute shell commands, or permit file deletion. It only permits complete-file additions/replacements under `src/`, `templates/`, `static/`, `notebooks/`, plus `README.md` and `requirements.txt`. Planned content is size-limited, changed existing files are copied under `.app_backups/<UTC timestamp>/`, and applications are appended to `.app_change_history.jsonl`.

### Databricks caveat

The Flask interface is intended for a local development machine. Databricks notebooks remain supported for the research runner, but do not expose this development server from a shared Databricks workspace without an approved, authenticated deployment pattern. Continue to use Databricks Secret Scopes for tokens; never place a token in the notebook or frontend.

## Project structure

```text
indian_equity_research/
├── .env.example
├── requirements.txt
├── README.md
├── pyproject.toml
├── app.py
├── templates/index.html
├── static/
│   ├── app.js
│   └── styles.css
└── src/indian_equity_research/
    ├── client.py       # authenticated API client
    ├── config.py       # environment-backed configuration
    ├── prompt.py       # research/guardrail prompt
    ├── runner.py       # execution + output persistence
    ├── cli.py          # terminal entry point
    └── project_editor.py # review-first change safety controls
```
