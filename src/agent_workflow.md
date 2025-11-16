# Agent Workflow - MailSense

Overview:
MailSense ingests an email (subject + body), produces a short human summary, extracts structured action items (tasks, deadlines, contacts), decides a recommended action (create task, schedule meeting, draft reply template, ignore), and optionally executes the action via a registered tool.

High-level stages:
1. Input ingestion
   - Source: plain text email (subject + body)
   - Validation: non-empty subject/body

2. Extraction stage (Extractor Agent / module)
   - Outputs:
     - summary_text (1-2 sentences)
     - actions_list: list of extracted actions (see schema)
   - Techniques: rule-based + lightweight NLP (entity/date parsing). The ADK tool `extract_actions` will provide these outputs.

3. Planning stage (Planner Agent / module)
   - Input: actions_list + memory context
   - Behavior: apply planner rules to pick a recommended action for each extracted action.
   - Output: action_plan (one recommended action per extracted action), with optional confidence score.

4. Action execution stage (Tool Use)
   - Tools available: `create_task`, `schedule_event`, `compose_reply`, `log_action`
   - The planner invokes tools depending on recommended action (via ADK tool calls).

5. Memory update
   - New tasks/actions saved into persistent memory (memory.json)
   - Update metadata: last_seen, count, tags

6. Observability & Logging
   - Each stage logs start/end, key variables (summary, extracted dates, chosen action)
   - Logs stored to `logs/agent.log` and metrics to `logs/metrics.json`

Notes:
- All tools must be registered in ADK and callable by the Planner agent.
- For reproducibility in the capstone, the tools will have deterministic behavior (no external paid APIs).
