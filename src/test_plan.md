# Test Plan - MailSense

Objective: Verify that the implemented pipeline performs end-to-end email -> summary -> extraction -> planning -> tool invocation and persistence.

Manual Acceptance Tests:
1. Ingest sample email #1 (meeting request)
   - Expected: extractor finds one schedule action with at least one date
   - Planner recommends schedule_event or compose_reply if ambiguous
   - create_task or schedule_event results in new entry in tasks.json or calendar.json

2. Ingest sample email #2 (invoice)
   - Expected: extractor finds invoice action with due date
   - Planner recommends create_task with priority high
   - tasks.json contains new task with status pending and due date

3. Ingest sample email #3 (informational)
   - Expected: extractor returns action.type "info" or no actions
   - Planner recommends "ignore"
   - No change to tasks.json

Metrics to record in logs/metrics.json:
- total_emails_processed
- total_actions_extracted
- tasks_created
- schedule_events_created
- avg_extraction_confidence

Repro steps for test:
- Use data/examples_emails.json entries.
- For each email, call ADK agent pipeline and observe outputs in notebook cells.
