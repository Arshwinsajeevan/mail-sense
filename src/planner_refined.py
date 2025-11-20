# src/planner_refined.py
from typing import Dict, Any
from src.memory import load_memory
from src.tools_enhanced import extract_amounts, infer_priority_from_text
from datetime import datetime
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def _normalize_date_iso(dt_str: str):
    if not dt_str:
        return None
    try:
        return dt_str.split("T")[0]
    except Exception:
        return dt_str

def _read_tasks():
    p = ROOT / "tasks.json"
    if not p.exists():
        return {"tasks": []}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"tasks": []}

def _conflicts_with_memory_or_tasks(due_iso: str, memory):
    # check tasks.json for overlapping date
    tasks_obj = _read_tasks()
    if not due_iso:
        return False
    date_key = _normalize_date_iso(due_iso)
    for t in tasks_obj.get("tasks", []):
        if t.get("due") and _normalize_date_iso(t.get("due")) == date_key:
            return True
    return False

def plan_actions_refined(extractor_output: Dict[str, Any]) -> Dict[str, Any]:
    plans = []
    memory = load_memory()
    actions = extractor_output.get("actions", [])
    for a in actions:
        a_id = a.get("id")
        a_type = a.get("type")
        dates = a.get("dates", []) or []
        desc = a.get("description") or ""
        priority = a.get("priority") or infer_priority_from_text(desc)
        reason = ""
        recommendation = "ignore"
        confidence = 0.6
        tool_call = None

        # Invoice with amount -> high priority
        amount_matches = extract_amounts(desc)
        if a_type == "invoice" or amount_matches:
            recommendation = "create_task"
            confidence = 0.97 if amount_matches else 0.9
            reason = f"Invoice/amount detected: {amount_matches}" if amount_matches else "Invoice-like content"
            tool_call = {"name": "create_task", "args": {"action": a, "priority": "high"}}

        elif a_type == "schedule" and dates:
            exact = [d for d in dates if "T" in d]
            if exact:
                chosen = exact[0]
                if _conflicts_with_memory_or_tasks(chosen, memory):
                    recommendation = "compose_reply"
                    confidence = 0.6
                    reason = "Conflict detected with existing scheduled item"
                    tool_call = {"name": "compose_reply", "args": {"action": a, "preferred_slot": None}}
                else:
                    recommendation = "schedule_event"
                    confidence = 0.92
                    reason = "Exact time present"
                    tool_call = {"name": "schedule_event", "args": {"action": a, "start": chosen}}
            else:
                # prefer suggesting slots if ambiguous
                recommendation = "compose_reply"
                confidence = 0.7
                reason = "Ambiguous date; will ask user to confirm"
                tool_call = {"name": "compose_reply", "args": {"action": a, "preferred_slot": None}}

        elif a_type == "task":
            recommendation = "create_task"
            confidence = 0.8
            reason = "Generic task detected"
            tool_call = {"name": "create_task", "args": {"action": a, "priority": priority}}

        elif a_type == "delegate" and a.get("contacts"):
            recommendation = "compose_reply"
            confidence = 0.85
            reason = "Delegation action; compose reply"
            tool_call = {"name": "compose_reply", "args": {"action": a}}

        else:
            recommendation = "ignore"
            confidence = 0.55
            reason = "No clear action"

        plans.append({
            "action_id": a_id,
            "recommendation": recommendation,
            "confidence": float(confidence),
            "reason": reason,
            "tool_call": tool_call
        })

    return {"email_id": extractor_output.get("email_id"), "plans": plans}
