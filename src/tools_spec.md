# Tools Specification - MailSense

Each tool is a plain Python function (or ADK tool) that the agent will call. Below are the required tools, their input and output schema, and expected side-effects.

1) summarize_email
- Purpose: Create a concise human-readable summary of the email.
- Input:
  - { "subject": str, "body": str }
- Output:
  - { "summary_text": str, "summary_length": int }  # summary_length = number of sentences or approx words
- Side effects: none

2) extract_actions
- Purpose: Extract structured actions from the email body and subject.
- Input:
  - { "subject": str, "body": str }
- Output:
  - {
      "actions": [
        {
          "id": str,               # unique local id, e.g., "a1"
          "type": str,             # "schedule" | "task" | "invoice" | "info" | "delegate"
          "title": str,            # short label e.g., "Haircut with Priya"
          "description": str,      # text snippet describing the action
          "dates": [str],          # ISO 8601 strings if found, e.g., "2025-11-21T15:00:00"
          "contacts": [ { "name": str, "email": str|null } ],
          "priority": "low"|"medium"|"high"|null,
          "confidence": float      # 0.0 - 1.0
        }
      ]
    }
- Side effects: none

3) create_task
- Purpose: Persist an action as a task in the task store (tasks.json)
- Input:
  - { "action_id": str, "title": str, "due": str|null, "notes": str, "priority": str|null }
- Output:
  - { "status": "ok"|"error", "task_id": str|null, "message": str }
- Side effects:
  - Appends object to `tasks.json` with metadata {created_at, source_email_id}

4) schedule_event
- Purpose: Create a scheduled event (mock) in schedule store (tasks.json or calendar.json)
- Input:
  - { "action_id": str, "title": str, "start": str, "end": str|null, "attendees": [str] }
- Output:
  - { "status": "ok"|"error", "event_id": str|null, "message": str }
- Side effects:
  - Appends object to `calendar.json` or `tasks.json` with schedule metadata

5) compose_reply
- Purpose: Produce a short reply template for the user to copy/paste
- Input:
  - { "action_id": str, "intent": str, "preferred_slot": str|null }
- Output:
  - { "status": "ok", "reply_text": str }
- Side effects: none

6) log_action
- Purpose: Write logs/traces for observability
- Input:
  - { "stage": str, "message": str, "meta": dict|null }
- Output:
  - { "status": "ok" }
- Side effects:
  - Append to `logs/agent.log` and update `logs/metrics.json` counters
