# MailSense

MailSense — AI Email Summarizer & Action Planner (Kaggle Capstone)

**Track:** Concierge

**Short description:** MailSense ingests email text, summarizes it, extracts actionable items (tasks, deadlines, contacts), recommends next actions, and can execute mock task creation.

**How to run (quick start):** Open `notebooks/final_submission.ipynb` and run the cells top-to-bottom.

**Prepared to license under CC-BY-SA 4.0 if required.**

## Running the refined agent
A refined agent runtime is available at `src/agent_main_refined.py`. To run it (after creating and activating the virtual environment and installing requirements), execute:


This produces a structured report for each example email and persists created tasks to `tasks.json`.
