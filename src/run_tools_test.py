# src/run_tools_test.py
import json
from pathlib import Path

from src.tools import extract_actions, create_task
from src.memory import add_recent_email

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "examples_emails.json"
TASKS_PATH = ROOT / "tasks.json"


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        emails = json.load(f)

    for e in emails:
        subject = e.get("subject", "")
        body = e.get("body", "")
        print("=" * 60)
        print("Email subject:", subject)
        out = extract_actions(subject, body)
        print("Summary:", out["summary_text"])
        actions = out.get("actions", [])
        # attach email id to source for create_task
        source_email = {"email_id": out.get("email_id"), "subject": subject, "body": body}
        # add to recent memory
        add_recent_email({"email_id": source_email["email_id"], "subject": subject, "summary": out["summary_text"]})
        for a in actions:
            print("Action detected:", a["type"], "| Title:", a["title"], "| Dates:", a["dates"])
            # simple rule: create task if invoice, or if task, or schedule with exact date
            if a["type"] in ("invoice", "task"):
                res = create_task(a, source_email)
                print("Created task:", res)
            elif a["type"] == "schedule" and a.get("dates"):
                # create task for schedule as a placeholder event
                res = create_task(a, source_email)
                print("Created schedule placeholder task:", res)
            else:
                print("No auto-action taken for this item.")

    # final tasks.json print
    if TASKS_PATH.exists():
        with open(TASKS_PATH, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        print("\nFinal tasks.json content:")
        print(json.dumps(tasks, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
