# src/agent_main.py
import json
import sys
from pathlib import Path
from typing import Dict, Any

from src.tools import extract_actions, create_task, summarize_email
from src.planner import plan_actions
from src.memory import add_recent_email

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "examples_emails.json"


def execute_tool_call(tool_call: Dict[str, Any], source_email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool execution dispatcher. Matches the tool_call['name'] to actual functions.
    Tool arg shapes follow src/tools_spec.md.
    """
    if not tool_call:
        return {"status": "noop", "message": "No tool call provided"}
    name = tool_call.get("name")
    args = tool_call.get("args", {}) or {}

    # map to real functions
    if name == "create_task":
        action = args.get("action")
        return create_task(action, source_email)
    elif name == "schedule_event":
        # For now, schedule_event will be treated as a task placeholder using create_task
        action = args.get("action")
        data = args.get("start")
        # attach chosen start time into action for persistence
        if data:
            action["dates"] = [data]
        return create_task(action, source_email)
    elif name == "compose_reply":
        # return a simple reply template
        action = args.get("action")
        preferred = args.get("preferred_slot")
        reply = f"Hi {action.get('contacts')[0].get('name') if action.get('contacts') else 'there'}, I can do {preferred or 'please suggest a slot'}."
        return {"status": "ok", "reply_text": reply}
    else:
        return {"status": "error", "message": f"Unknown tool {name}"}


def process_email_obj(email_obj: Dict[str, Any]) -> None:
    subject = email_obj.get("subject", "")
    body = email_obj.get("body", "")
    print("\n" + "=" * 60)
    print("Processing email:", subject)
    extractor_out = extract_actions(subject, body)
    print("Summary:", extractor_out.get("summary_text"))
    # add to memory recent
    add_recent_email({"email_id": extractor_out.get("email_id"), "subject": subject, "summary": extractor_out.get("summary_text")})
    plans = plan_actions(extractor_out)
    for p in plans.get("plans", []):
        print(f"Plan for action {p['action_id']}: {p['recommendation']} (conf={p['confidence']}) — reason: {p['reason']}")
        if p.get("tool_call"):
            res = execute_tool_call(p["tool_call"], {"email_id": extractor_out.get("email_id"), "subject": subject, "body": body})
            print("Tool execution result:", res)
        else:
            print("No tool call for this plan.")


def main(batch_file: Path = DATA_PATH):
    # load list of emails (batch)
    if not batch_file.exists():
        print(f"No data file found at {batch_file}. Provide path to single email JSON as argument.")
        return
    with open(batch_file, "r", encoding="utf-8") as f:
        emails = json.load(f)
    for e in emails:
        process_email_obj(e)
    print("\nAgent run complete.")


if __name__ == "__main__":
    # allow optional CLI argument: path to a single email json file
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        main(path)
    else:
        main()
