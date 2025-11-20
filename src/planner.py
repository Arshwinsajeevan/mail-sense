# src/planner.py
from typing import Dict, Any, List
from datetime import datetime
from src.memory import load_memory  # uses load_memory from src/memory.py


def _normalize_date_iso(dt_str: str):
    """Return prefix up to date/time for simple comparisons (handle None)."""
    if not dt_str:
        return None
    try:
        # attempt to normalize
        return dt_str.split("T")[0]  # compare by date (YYYY-MM-DD)
    except Exception:
        return dt_str


def _conflicts_with_memory(due_iso: str, memory: Dict[str, Any]) -> bool:
    """Simple conflict check: if any existing task has same due date."""
    if not due_iso:
        return False
    date_key = _normalize_date_iso(due_iso)
    tasks_idx = memory.get("tasks_index", [])
    # A simple approach: if memory contains tasks (we don't load full tasks file here),
    # we cannot check details. For more robust, the planner can read tasks.json directly.
    # We'll attempt to read 'tasks.json' if present for accurate check.
    try:
        from pathlib import Path
        import json
        P = Path(__file__).resolve().parents[1] / "tasks.json"
        if P.exists():
            with open(P, "r", encoding="utf-8") as f:
                tasks_obj = json.load(f)
            for t in tasks_obj.get("tasks", []):
                if t.get("due"):
                    if _normalize_date_iso(t.get("due")) == date_key:
                        return True
    except Exception:
        # fallback to simple index-based heuristic
        return False
    return False


def plan_actions(extractor_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes the extractor output and returns planner results.
    Output shape:
    {
      "email_id": str,
      "plans": [
         { "action_id": str, "recommendation": str, "confidence": float, "reason": str, "tool_call": {...} }
      ]
    }
    """
    plans: List[Dict[str, Any]] = []
    memory = load_memory()
    actions = extractor_output.get("actions", [])

    for a in actions:
        a_id = a.get("id")
        a_type = a.get("type")
        dates = a.get("dates", []) or []
        contacts = a.get("contacts", [])
        confidence = 0.6
        recommendation = "ignore"
        reason = "Default fallback"
        tool_call = None

        # Rule 1: invoice
        if a_type == "invoice" or any(k in (a.get("description") or "").lower() for k in ["invoice", "due", "payment", "amount"]):
            recommendation = "create_task"
            confidence = 0.95
            reason = "Invoice/payment detected"
            tool_call = {"name": "create_task", "args": {"action": a}}
        # Rule 2: schedule with dates
        elif a_type == "schedule" and dates:
            # prefer exact date/time (has 'T')
            exact = [d for d in dates if "T" in d]
            if exact:
                chosen = exact[0]
                # conflict check
                if _conflicts_with_memory(chosen, memory):
                    recommendation = "compose_reply"
                    confidence = 0.6
                    reason = "Conflict with existing task; ask for alternate slot"
                    tool_call = {"name": "compose_reply", "args": {"action": a, "preferred_slot": None}}
                else:
                    recommendation = "schedule_event"
                    confidence = 0.9
                    reason = "Exact time provided"
                    tool_call = {"name": "schedule_event", "args": {"action": a, "start": chosen}}
            else:
                recommendation = "compose_reply"
                confidence = 0.7
                reason = "Ambiguous dates — ask to confirm slot"
                tool_call = {"name": "compose_reply", "args": {"action": a, "preferred_slot": None}}
        # Rule 3: task without date
        elif a_type == "task":
            recommendation = "create_task"
            confidence = 0.8
            reason = "General task detected"
            tool_call = {"name": "create_task", "args": {"action": a}}
        # Rule 4: delegate
        elif a_type == "delegate" and contacts:
            recommendation = "compose_reply"
            confidence = 0.85
            reason = "Delegation detected"
            tool_call = {"name": "compose_reply", "args": {"action": a}}
        # Rule 5: info or low confidence
        else:
            recommendation = "ignore"
            confidence = 0.6
            reason = "No actionable intent or low confidence"

        plans.append({
            "action_id": a_id,
            "recommendation": recommendation,
            "confidence": float(confidence),
            "reason": reason,
            "tool_call": tool_call
        })

    return {"email_id": extractor_output.get("email_id"), "plans": plans}
