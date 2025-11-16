# Planner Rules - MailSense

The Planner receives an extracted action object and memory context. It returns a recommended action in the shape:
{ "action_id": str, "recommendation": str, "confidence": float, "reason": str, "tool_call": {...} }

Decision Rules (applied in this order):

1. If action.type == "invoice" or body contains keywords ["invoice","due","payment","amount"]:
   - recommendation = "create_task"
   - confidence = 0.95
   - reason = "Invoice detected; requires payment action"
   - tool_call = create_task with priority = "high" and due = extracted date or inferred date

2. Else if action.type == "schedule" and action.dates is non-empty:
   - If one date is exact (contains time):
       - recommendation = "schedule_event"
       - confidence = 0.9
       - reason = "Exact time provided"
       - tool_call = schedule_event using the earliest exact date
   - Else if dates contain ambiguous dates (e.g., "next week Tue afternoon"):
       - recommendation = "compose_reply"
       - confidence = 0.7
       - reason = "Ambiguous time — ask for confirmation"
       - tool_call = compose_reply with suggested slots

3. Else if action.type == "task" and no date:
   - recommendation = "create_task"
   - confidence = 0.8
   - reason = "General task with no due date"
   - tool_call = create_task with priority inferred from keywords (urgent/high/low)

4. Else if action.type == "delegate" and contacts present:
   - recommendation = "compose_reply"
   - confidence = 0.85
   - reason = "Delegation detected — prepare reply or forward template"
   - tool_call = compose_reply with delegate instruction

5. Else if action.type == "info" or no actionable intent with low confidence (<0.5):
   - recommendation = "ignore" (or "archive")
   - confidence = 0.6
   - reason = "No action required"

Additional checks:
- Memory conflict check:
   - If extracted date conflicts with an existing pending task in memory (overlapping time range), downgrade schedule_event confidence by 0.25 and recommend compose_reply offering alternate slots.
- Duplicate detection:
   - If a similar task (same title or very similar description) exists in memory within last 7 days, recommendation becomes "notify_user" with a link to existing task.
