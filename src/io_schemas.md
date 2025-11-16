# IO Schemas - MailSense

1) Ingested email (input)
{
  "email_id": "e123",
  "subject": "Meeting request",
  "body": "Hi Arshwin — are you free Friday 3–4pm for a haircut? If not, next week Tue afternoon works. — Priya",
  "from": "priya@example.com",
  "to": "you@example.com",
  "received_at": "2025-11-16T09:40:00+05:30"
}

2) Extractor output (example)
{
  "email_id": "e123",
  "summary_text": "Priya requests a haircut on Friday 3–4pm or next Tuesday afternoon.",
  "actions": [
    {
      "id": "a1",
      "type": "schedule",
      "title": "Haircut with Priya",
      "description": "Request for haircut; prefers Fri 3-4pm or Tue afternoon",
      "dates": ["2025-11-21T15:00:00+05:30", "2025-11-25T15:00:00+05:30"],
      "contacts": [{"name":"Priya","email":"priya@example.com"}],
      "priority": "medium",
      "confidence": 0.92
    }
  ]
}

3) Planner output (example)
{
  "email_id": "e123",
  "plans": [
    {
      "action_id": "a1",
      "recommendation": "schedule_event",
      "confidence": 0.9,
      "reason": "Exact time provided",
      "tool_call": {
        "name": "schedule_event",
        "args": {"title":"Haircut with Priya","start":"2025-11-21T15:00:00+05:30","attendees":["priya@example.com"]}
      }
    }
  ]
}
