# src/tools.py
import re
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import dateparser.search
from dateparser import parse as parse_date

from src.memory import add_task_index, add_recent_email  # relative import from package layout

ROOT = Path(__file__).resolve().parents[1]
TASKS_PATH = ROOT / "tasks.json"


def _ensure_tasks_file():
    if not TASKS_PATH.exists():
        TASKS_PATH.write_text(json.dumps({"tasks": []}, indent=2, ensure_ascii=False))


def summarise_by_sentences(text: str, max_sentences: int = 2) -> str:
    # naive sentence splitter
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    if not parts:
        return text.strip()
    return " ".join(parts[:max_sentences])


def summarize_email(subject: str, body: str) -> Dict[str, Any]:
    """
    Return a short summary dictionary.
    """
    # prioritize subject, then first two sentences of body
    subject = subject.strip() if subject else ""
    body = body.strip() if body else ""
    if subject and len(subject) < 80 and ("request" in subject.lower() or "inv" in subject.lower() or "meeting" in subject.lower()):
        summary_text = subject
    else:
        # combine subject + first sentences of body
        summary_text = (subject + ". " if subject else "") + summarise_by_sentences(body, max_sentences=2)
    return {"summary_text": summary_text.strip(), "summary_length": len(summary_text.split())}


def _detect_type_and_priority(text: str) -> (str, Optional[str]):
    txt = text.lower()
    if any(k in txt for k in ["invoice", "due", "payment", "amount", "invoice#"]):
        return "invoice", "high"
    if any(k in txt for k in ["schedule", "meet", "meeting", "call", "available", "free", "book"]):
        return "schedule", None
    if any(k in txt for k in ["please", "kindly", "request", "could you", "can you", "send"]):
        return "task", None
    if any(k in txt for k in ["forward", "delegate", "cc:", "please assign"]):
        return "delegate", None
    return "info", None


def _extract_contact_candidates(text: str) -> List[Dict[str, str]]:
    # very naive email extraction and name heuristics
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    contacts = []
    for e in emails:
        name_part = e.split("@")[0].replace(".", " ").replace("_", " ")
        contacts.append({"name": name_part.title(), "email": e})
    return contacts


def extract_actions(subject: str, body: str) -> Dict[str, Any]:
    """
    Return structured actions extracted from subject+body.
    """
    full = (subject + "\n\n" + body).strip()
    # find dates using dateparser.search
    dates_raw = []
    try:
        search = dateparser.search.search_dates(full, settings={"PREFER_DATES_FROM": "future"})
        if search:
            dates_raw = [d[1].isoformat() for d in search]
    except Exception:
        dates_raw = []

    detected_type, priority = _detect_type_and_priority(full)
    contacts = _extract_contact_candidates(full)

    # build a single action for now (simple)
    action_id = "a-" + uuid.uuid4().hex[:8]
    # short title heuristics
    title = ""
    if detected_type == "schedule":
        title = "Schedule: " + (subject if subject else "Meeting")
    elif detected_type == "invoice":
        title = "Invoice Action: " + (subject if subject else "Payment due")
    elif detected_type == "task":
        title = "Task: " + (subject if subject else "Action required")
    else:
        title = subject if subject else full[:40]

    action = {
        "id": action_id,
        "type": detected_type,
        "title": title,
        "description": (body[:280] + "...") if len(body) > 280 else body,
        "dates": dates_raw,
        "contacts": contacts,
        "priority": priority,
        "confidence": 0.9 if detected_type != "info" else 0.4
    }
    return {"email_id": "e-" + uuid.uuid4().hex[:8], "summary_text": summarize_email(subject, body)["summary_text"], "actions": [action]}


def _read_tasks() -> Dict[str, Any]:
    _ensure_tasks_file()
    with open(TASKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_tasks(obj: Dict[str, Any]) -> None:
    TASKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TASKS_PATH, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def create_task(action: Dict[str, Any], source_email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persist a task to tasks.json; return status dict.
    action: single action dict returned by extract_actions
    source_email: the original email object (id, subject, body)
    """
    _ensure_tasks_file()
    tasks_obj = _read_tasks()
    new_task_id = "t-" + uuid.uuid4().hex[:8]
    now_iso = datetime.now().isoformat()

    # choose due date if available else None
    due = action.get("dates", [None])[0] if action.get("dates") else None

    new_task = {
        "task_id": new_task_id,
        "title": action.get("title"),
        "description": action.get("description"),
        "created_at": now_iso,
        "due": due,
        "status": "pending",
        "source_email_id": source_email.get("email_id"),
        "priority": action.get("priority") or "medium",
        "tags": [action.get("type")]
    }

    tasks_obj.setdefault("tasks", []).append(new_task)
    _write_tasks(tasks_obj)

    # update memory index
    add_task_index(new_task_id)

    return {"status": "ok", "task_id": new_task_id, "message": "Task created"}


# small helper to create_task_index since memory.add_task_index imported uses a different name
def add_task_index(task_id: str) -> None:
    try:
        add_task_index  # noqa: F401
    except Exception:
        # avoid circular issue if imported badly; call memory function directly
        from src.memory import add_task_index as _add
        _add(task_id)
