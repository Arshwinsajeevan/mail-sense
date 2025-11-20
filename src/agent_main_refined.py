# src/agent_main_refined.py
import json
import sys
from pathlib import Path
from typing import Dict, Any

from src.tools import extract_actions, create_task, summarize_email
from src.planner_refined import plan_actions_refined
from src.memory import add_recent_email

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "examples_emails.json"

def execute_tool_call(tool_call: Dict[str, Any], source_email: Dict[str, Any]) -> Dict[str, Any]:
    if not tool_call:
        return {"status": "noop", "message": "No tool call provided"}
    name = tool_call.get("name")
    args = tool_call.get("args", {}) or {}
    if name == "create_task":
        action = args.get("action")
        # pass priority if provided
        if "priority" in args:
            action["priority"] = args.get("priority")
        return create_task(action, source_email)
    elif name == "schedule_event":
        action = args.get("action")
        data = args.get("start")
        if data:
            action["dates"] = [data]
        return create_task(action, source_email)
    elif name == "compose_reply":
        action = args.get("action")
        preferred = args.get("preferred_slot")
        # craft a simple reply using available contact name
        name = (action.get("contacts") or [{}])[0].get("name") or "there"
        reply = f"Hi {name}, thanks — could you confirm: {preferred or 'which of these slots works for you?'}"
        return {"status": "ok", "reply_text": reply}
    else:
        return {"status": "error", "message": f"Unknown tool {name}"}

def process_email_obj(email_obj: Dict[str, Any]) -> Dict[str, Any]:
    subject = email_obj.get("subject", "")
    body = email_obj.get("body", "")
    extractor_out = extract_actions(subject, body)
    add_recent_email({"email_id": extractor_out.get("email_id"), "subject": subject, "summary": extractor_out.get("summary_text")})
    plans = plan_actions_refined(extractor_out)
    report = {"email": {"subject": subject, "summary": extractor_out.get("summary_text")}, "plans": []}
    for p in plans.get("plans", []):
        entry = {"action_id": p["action_id"], "recommendation": p["recommendation"], "confidence": p["confidence"], "reason": p["reason"], "tool_result": None}
        if p.get("tool_call"):
            res = execute_tool_call(p["tool_call"], {"email_id": extractor_out.get("email_id"), "subject": subject, "body": body})
            entry["tool_result"] = res
        report["plans"].append(entry)
    return report

def run_batch(batch_file: Path = DATA_PATH):
    if not batch_file.exists():
        print(f"No data file found at {batch_file}.")
        return []
    with open(batch_file, "r", encoding="utf-8") as f:
        emails = json.load(f)
    results = []
    for e in emails:
        r = process_email_obj(e)
        results.append(r)
    return results

if __name__ == "__main__":
    out = run_batch()
    import pprint
    pprint.pprint(out)
    print("Refined agent run complete.")
