# Databricks notebook source
# MAGIC %pip install -r ../requirements.txt

# COMMAND ----------

import os
import sys

# Set this to the repository root path when running inside Databricks Repos.
PROJECT_ROOT = "."
sys.path.insert(0, "/Workspace/Users/saurabh.shinde2.ext@bayer.com/indian_equity_research_developer_ui/src")

# Never hard-code a token. Create it in a Databricks secret scope first.
os.environ["MYGENASSIST_BASE_URL"] = "https://chat.int.bayer.com/"
os.environ["MYGENASSIST_TOKEN"] ="mga-916664352489a2f6732b61a817286636014fbe62"
os.environ["MYGENASSIST_MODEL"] = "gpt-4o"  # replace with an enabled model ID

# COMMAND ----------

from indian_equity_research.runner import run

report, report_path = run(
    capital=500_000,
    risk_percent=1.0,
    max_positions=3,
    run_context="post-market",
    output_dir="outputs",
)
print(report)
print(f"Saved report: {report_path}")

# COMMAND ----------

# DBTITLE 1,Start Flask app on driver with proxy URL
import threading
import socket
import time

# Add src to path (already done in Cell 2, but ensure it's set)
project_root = "/Workspace/Users/saurabh.shinde2.ext@bayer.com/indian_equity_research_developer_ui"
if f"{project_root}/src" not in sys.path:
    sys.path.insert(0, f"{project_root}/src")

os.chdir(project_root)  # so templates/ and static/ are found

# Force-reload in case modules were cached from earlier cells
for mod_name in list(sys.modules):
    if mod_name.startswith("indian_equity_research") or mod_name == "app":
        del sys.modules[mod_name]

from app import app  # noqa: E402

# Find a free port (kernel restart freed previous ports)
PORT = 5000
for p in range(5000, 5020):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if s.connect_ex(("127.0.0.1", p)) != 0:
            PORT = p
            break

# Start Flask in a background thread so the cell doesn't block
def _run_flask():
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

flask_thread = threading.Thread(target=_run_flask, daemon=True)
flask_thread.start()
time.sleep(3)

# Build the driver proxy URL
workspace_host = spark.conf.get("spark.databricks.workspaceUrl")
org_id = spark.conf.get("spark.databricks.clusterUsageTags.orgId")
cluster_id = spark.conf.get("spark.databricks.clusterUsageTags.clusterId")
proxy_url = f"https://{workspace_host}/driver-proxy/o/{org_id}/{cluster_id}/{PORT}/"

print(f"Flask server started on port {PORT}")
print(f"\nAccess the app at:\n{proxy_url}")
displayHTML(f'<a href="{proxy_url}" target="_blank">Open Indian Equity Research UI</a>')