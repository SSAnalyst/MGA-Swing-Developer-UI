"""Safe, review-first project change planning and application utilities.

This module never runs shell commands.  It only writes reviewed file content inside a
small allowlist rooted at the checked-out project.
"""
from __future__ import annotations

from datetime import datetime, timezone
import difflib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
from typing import Any
from uuid import uuid4

EDITABLE_PREFIXES = ("src/", "templates/", "static/", "notebooks/")
EDITABLE_FILES = {"README.md", "requirements.txt", "app.py"}
MAX_FILE_BYTES = 100_000
MAX_PLAN_BYTES = 400_000
MAX_SNAPSHOT_BYTES = 120_000
MAX_SNAPSHOT_FILES = 30
HISTORY_FILE = ".app_change_history.jsonl"
BACKUP_DIR = ".app_backups"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _normalise_path(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Every planned file must have a non-empty path.")
    path = PurePosixPath(value.replace("\\", "/"))
    if (
        path.is_absolute()
        or ".." in path.parts
        or "." in path.parts
        or "__pycache__" in path.parts
        or any(part.startswith(".") for part in path.parts)
    ):
        raise ValueError(f"Unsafe project path: {value!r}")
    normalised = path.as_posix()
    if normalised.startswith(EDITABLE_PREFIXES) or normalised in EDITABLE_FILES:
        return normalised
    raise ValueError(
        f"Path {normalised!r} is not editable. Allowed: src/, templates/, static/, "
        "notebooks/, README.md, requirements.txt."
    )


def safe_path(project_root: Path, relative_path: str) -> Path:
    """Return an allowlisted path and confirm it remains below project_root."""
    normalised = _normalise_path(relative_path)
    root = project_root.resolve()
    destination = (root / normalised).resolve()
    if root not in destination.parents:
        raise ValueError("Path escapes the project root.")
    return destination


def _is_snapshot_candidate(relative: str) -> bool:
    return relative.startswith(EDITABLE_PREFIXES) or relative in EDITABLE_FILES


def inventory_project(project_root: Path, include_content: bool = False) -> list[dict[str, Any]]:
    """Inventory editable regular files; hidden folders and generated files are excluded."""
    records: list[dict[str, Any]] = []
    for path in sorted(project_root.rglob("*")):
        if not path.is_file() or any(part.startswith(".") for part in path.relative_to(project_root).parts):
            continue
        relative = path.relative_to(project_root).as_posix()
        if not _is_snapshot_candidate(relative):
            continue
        size = path.stat().st_size
        record: dict[str, Any] = {"path": relative, "size": size}
        if include_content and size <= MAX_FILE_BYTES:
            try:
                record["content"] = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                record["content"] = "[Non-text file omitted]"
        records.append(record)
    return records


def build_snapshot(project_root: Path) -> str:
    """Produce a bounded source snapshot for a developer model, without secrets."""
    chunks: list[str] = []
    used = 0
    for item in inventory_project(project_root, include_content=True)[:MAX_SNAPSHOT_FILES]:
        content = item.get("content", "")
        if not isinstance(content, str) or content.startswith("[Non-text"):
            continue
        header = f"\n--- FILE: {item['path']} ---\n"
        remaining = MAX_SNAPSHOT_BYTES - used - len(header)
        if remaining <= 0:
            break
        clipped = content[:remaining]
        chunks.append(header + clipped)
        used += len(header) + len(clipped)
        if used >= MAX_SNAPSHOT_BYTES:
            break
    return "".join(chunks)


def developer_prompt(request: str, snapshot: str) -> str:
    return f'''You are a careful Python web-app developer. Plan the smallest safe change for the enhancement request below using only the provided project snapshot. Do not execute code, shell commands, tests, or tools. Do not delete files. Do not include secrets, tokens, or environment values.

Enhancement request:
{request}

Project snapshot:
{snapshot}

Return ONLY a strict JSON object, with no prose or Markdown fences, exactly in this shape:
{{"summary":"...","assumptions":["..."],"files":[{{"path":"src/example.py","content":"complete replacement content","reason":"..."}}],"manual_steps":["..."],"tests":["..."]}}

Rules: files is a list of complete file replacements or additions only; never use patch syntax. Every path must be under src/, templates/, static/, or notebooks/, or exactly README.md or requirements.txt. Do not propose deletions. Keep each file under 100000 UTF-8 bytes and the total under 400000 bytes.''' 


def extract_json(text: str) -> dict[str, Any]:
    """Parse a JSON response, accepting a fenced JSON object when necessary."""
    if not isinstance(text, str):
        raise ValueError("The model response was not text.")
    candidate = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1).strip()
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Model did not return a JSON object.") from None
        try:
            parsed = json.loads(candidate[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("Model returned invalid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Model plan must be a JSON object.")
    return parsed


def validate_plan(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalise a model plan before it can be previewed or applied."""
    if not isinstance(raw.get("summary"), str) or not raw["summary"].strip():
        raise ValueError("Plan requires a summary.")
    files = raw.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("Plan requires at least one file change.")
    if len(files) > 20:
        raise ValueError("Plan may change at most 20 files.")
    result_files: list[dict[str, str]] = []
    total = 0
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("Each file entry must be an object.")
        path = _normalise_path(item.get("path"))
        content, reason = item.get("content"), item.get("reason")
        if not isinstance(content, str) or not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"File {path} needs string content and a reason.")
        size = len(content.encode("utf-8"))
        if size > MAX_FILE_BYTES:
            raise ValueError(f"File {path} exceeds the {MAX_FILE_BYTES}-byte limit.")
        if path in seen:
            raise ValueError(f"Plan contains {path} more than once.")
        seen.add(path)
        total += size
        result_files.append({"path": path, "content": content, "reason": reason.strip()})
    if total > MAX_PLAN_BYTES:
        raise ValueError("Total planned content exceeds the safety limit.")

    def strings(key: str) -> list[str]:
        value = raw.get(key, [])
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            raise ValueError(f"Plan field {key} must be a list of strings.")
        return value

    return {
        "summary": raw["summary"].strip(), "assumptions": strings("assumptions"),
        "files": result_files, "manual_steps": strings("manual_steps"), "tests": strings("tests"),
    }


def add_diffs(project_root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    preview = dict(plan)
    preview_files = []
    for item in plan["files"]:
        destination = safe_path(project_root, item["path"])
        before = destination.read_text(encoding="utf-8") if destination.exists() else ""
        diff = "\n".join(difflib.unified_diff(
            before.splitlines(), item["content"].splitlines(), fromfile=f"a/{item['path']}",
            tofile=f"b/{item['path']}", lineterm="",
        ))
        preview_files.append({**item, "exists": destination.exists(), "diff": diff or "(No textual change)"})
    preview["files"] = preview_files
    return preview


def apply_plan(project_root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    """Back up existing targets, then atomically write the already validated plan."""
    stamp = utc_stamp()
    backup_root = project_root / BACKUP_DIR / stamp
    changed: list[str] = []
    for item in plan["files"]:
        destination = safe_path(project_root, item["path"])
        if destination.exists():
            backup = backup_root / item["path"]
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".app_tmp")
        temporary.write_text(item["content"], encoding="utf-8")
        temporary.replace(destination)
        changed.append(item["path"])
    event = {"timestamp": stamp, "summary": plan["summary"], "files": changed}
    with (project_root / HISTORY_FILE).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return {**event, "backup_dir": str(backup_root.relative_to(project_root)) if backup_root.exists() else None}


def read_history(project_root: Path, limit: int = 50) -> list[dict[str, Any]]:
    path = project_root / HISTORY_FILE
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(records))


def new_plan_id() -> str:
    return uuid4().hex
