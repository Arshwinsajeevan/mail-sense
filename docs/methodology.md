# MailSense – Methodology and Reproducibility

## 1. Project Overview

**MailSense** is an AI-powered email summarizer and action planner.

Given an email (subject + body), MailSense:

1. Generates a short human-readable **summary**.
2. Extracts **structured actions** (task type, dates, contacts, priority).
3. Uses a **planner** to decide what to do:
   - create a task,
   - schedule an event (stored as a task placeholder),
   - compose a reply template,
   - or ignore the email.
4. Executes the plan using **tools** (functions like `create_task`, `compose_reply`).
5. Stores results in simple JSON files (`tasks.json`, `memory.json`) for persistence.

This project is built for the **Kaggle Agents Intensive – Capstone Project**.

- **Track:** Concierge
- **Author:** *Arshwin sajeevan*
- **Tech stack:** Python, rule-based NLP, `dateparser`, simple JSON storage.

---

## 2. Course Concepts Demonstrated

This project explicitly demonstrates at least **three key concepts** from the 5-day AI Agents Intensive:

1. **Tool Use (Unit 2)**
   - Tools implemented in `src/tools.py`.
   - Main tools:
     - `summarize_email(subject, body)`
     - `extract_actions(subject, body)`
     - `create_task(action, source_email)`
     - `schedule_event` (represented as a task placeholder)
     - `compose_reply(action, preferred_slot)`
   - The refined agent (`src/agent_main_refined.py`) calls these tools based on planner decisions.

2. **Memory (Unit 3 – Context & Memory)**
   - Persistent memory stored in `memory.json`.
   - Implemented in `src/memory.py`:
     - `load_memory`, `save_memory`
     - `add_recent_email`
     - `add_task_index`
   - Memory keeps:
     - recent emails,
     - a simple tasks index,
     - basic user profile (name, email, preferred hours, timezone).

3. **Planning / Multi-step Reasoning (Units 1 & 5)**
   - Implemented in `src/planner_refined.py` (`plan_actions_refined`).
   - The planner:
     - classifies actions (invoice, schedule, task, delegate, info),
     - infers priority,
     - checks for simple date conflicts,
     - chooses a recommended action and which tool to call.

> Optional concept: **Observability** can be added later by logging decisions and metrics, but is not required for the core project.

---

## 3. Architecture

### 3.1 High-level Flow

1. **Input**: JSON email with fields:
   - `subject`, `body`, `from`, `to`, `received_at`  
   (example emails are in `data/examples_emails.json`)

2. **Extraction (`extract_actions`)**
   - Uses `dateparser` to find date/time expressions.
   - Uses keyword heuristics to decide type:
     - `"invoice" / "due" / "payment"` → `invoice`
     - `"meeting" / "schedule / call"` → `schedule`
     - polite requests → `task`
     - forwarding / delegation language → `delegate`
     - otherwise → `info`.
   - Returns:
     - `summary_text`
     - list of `actions` with:
       - `id`, `type`, `title`, `description`, `dates[]`, `contacts[]`, `priority`, `confidence`.

3. **Planning (`plan_actions_refined`)**
   - Reads **memory** (`load_memory`) and **tasks.json**.
   - Applies rules:
     - Invoice or currency amount → `create_task` with high priority.
     - Schedule with an exact datetime:
       - If conflict with existing due date → `compose_reply` asking for another slot.
       - Else → `schedule_event`.
     - Generic task → `create_task`.
     - Delegation → `compose_reply`.
     - Info / low confidence → `ignore`.

4. **Tool Execution**
   - Dispatcher in `src/agent_main_refined.py` maps planner output to real tool functions:
     - `create_task` → saves to `tasks.json` and updates `memory.json`.
     - `schedule_event` → saved as a task placeholder.
     - `compose_reply` → returns a reply template (string) for the user.

5. **Persistence**
   - `tasks.json` contains all created tasks (including pseudo-events).
   - `memory.json` tracks recent emails and task IDs.

---

## 4. Data & Preprocessing

### 4.1 Example Emails

- Example inputs are stored in: `data/examples_emails.json`.
- Each entry has:
  - `id`, `subject`, `body`.
- Examples include:
  - meeting request,
  - invoice with due date and amount,
  - informational update,
  - generic follow-up,
  - call scheduling,
  - request for quote.

### 4.2 Preprocessing Steps

- Simple text concatenation of `subject` + `body`.
- `dateparser.search.search_dates` is used to find dates.
- Simple regex is used to extract email addresses.
- Currency-like patterns are detected using a regex in `src/tools_enhanced.py`.

---

## 5. Planner & Tools Details

### 5.1 Tools

All tools are defined in `src/tools.py` and helpers in `src/tools_enhanced.py`.

Key tools:

- `summarize_email(subject, body)`  
  → returns `{ "summary_text": str, "summary_length": int }`

- `extract_actions(subject, body)`  
  → returns `{ "email_id": str, "summary_text": str, "actions": [...] }`

- `create_task(action, source_email)`  
  → appends a task to `tasks.json` and updates memory.

- `schedule_event`  
  → currently implemented as creating a task with a chosen start datetime.

- `compose_reply(action, preferred_slot)`  
  → returns a template text, e.g. “Hi X, thanks — could you confirm which of these slots works for you?”.

### 5.2 Planner

- Basic rules are implemented in `plan_actions_refined`:

  - **Invoices & amounts**:
    - If invoice-like content or currency amount found → `create_task` with high priority.

  - **Scheduling**:
    - If exact datetime exists → try `schedule_event`, unless conflict.
    - If conflict or ambiguous dates → `compose_reply`.

  - **Generic tasks**:
    - → `create_task` with inferred priority.

  - **Delegation**:
    - → `compose_reply`.

  - **Others**:
    - → `ignore`.

---

## 6. Environment & Reproducibility

### 6.1 Python & Packages

- **Python version:** 3.10+ recommended.
- Main packages (see `requirements.txt`):
  - `dateparser`
  - `python-dateutil`
  - `pandas`
  - `pyyaml`
  - `tqdm`

### 6.2 Local Setup (CLI)

From the project root:

```bash
# create virtual environment
python -m venv venv

# activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# or (macOS/Linux)
# source venv/bin/activate

# install dependencies
pip install -r requirements.txt

# run refined agent pipeline
python -m src.agent_main_refined
