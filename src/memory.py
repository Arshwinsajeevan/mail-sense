# src/memory.py
import json
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[1]
MEMORY_PATH = ROOT / "memory.json"

DEFAULT_MEMORY = {
    "user_profile": {
        "name": "Arshwin",
        "email": "you@example.com",
        "preferences": {
            "preferred_hours": ["09:00-12:00", "15:00-18:00"],
            "timezone": "Asia/Kolkata"
        }
    },
    "recent_emails": [],
    "tasks_index": []
}


def load_memory() -> Dict[str, Any]:
    """Load memory.json; create default if missing."""
    if not MEMORY_PATH.exists():
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # if corrupted, overwrite with default
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()


def save_memory(mem: Dict[str, Any]) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)


def add_recent_email(email_obj: Dict[str, Any]) -> None:
    mem = load_memory()
    recent = mem.get("recent_emails", [])
    recent.insert(0, email_obj)
    # keep only last 50 emails
    mem["recent_emails"] = recent[:50]
    save_memory(mem)


def add_task_index(task_id: str) -> None:
    mem = load_memory()
    idx = mem.get("tasks_index", [])
    if task_id not in idx:
        idx.append(task_id)
    mem["tasks_index"] = idx
    save_memory(mem)
