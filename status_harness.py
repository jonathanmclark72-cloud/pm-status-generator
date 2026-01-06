import json
from datetime import date
from dateutil import parser as date_parser

DEFAULT_COLUMN_MAPPING = {
    "item_name": "Task Name",
    "status_raw": "Status",
    "notes_raw": "Notes",
    "risk_flag_raw": "Risk Flag",
    "due_date_raw": "Due Date",
    "owner_raw": "Owner",
    "workstream_raw": "Workstream",
    "milestone_flag_raw": "Milestone",
}

def normalize_dataframe(df, mapping, file_name, sheet_name):
    records = []
    today = date.today()

    for _, row in df.iterrows():
        item = str(row.get(mapping["item_name"], "")).strip()
        status_raw = str(row.get(mapping["status_raw"], "")).lower()
        notes_raw = str(row.get(mapping["notes_raw"], "")).strip()

        if "block" in status_raw or "risk" in status_raw:
            status_norm = "BLOCKED"
        elif "complete" in status_raw or "done" in status_raw:
            status_norm = "COMPLETE"
        else:
            status_norm = "IN_PROGRESS"

        records.append({
            "item_name": item,
            "status_normalized": status_norm,
            "notes_clean": notes_raw
        })

    return {
        "meta": {
            "file_name": file_name,
            "sheet_name": sheet_name
        },
        "lists": {
            "complete": [r for r in records if r["status_normalized"] == "COMPLETE"],
            "in_progress": [r for r in records if r["status_normalized"] == "IN_PROGRESS"],
            "blocked": [r for r in records if r["status_normalized"] == "BLOCKED"],
        }
    }

from openai_client import get_openai_client

# =========================
# SYSTEM PROMPT (GLOBAL)
# =========================
SYSTEM_PROMPT = """
You are a senior enterprise Project Management consultant.

You specialize in:
- Executive communication
- Risk identification and escalation
- Clear, concise weekly status reporting
- Translating raw project data into decision-ready insights

Your tone is professional, confident, and concise.
You avoid fluff, repetition, and generic language.
You surface risks early and provide actionable recommendations.
"""

def generate_report_llm(payload: dict, audience: str) -> str:
    USER_PROMPT = f"""
Using the provided project data, generate a Weekly Project Status Report suitable for executives and stakeholders.

Audience: {audience}

STRICT REQUIREMENTS:
1. Begin with an Overall Project Status using one of:
   - 🟢 Green (On Track)
   - 🟡 Yellow (At Risk)
   - 🔴 Red (Off Track)

2. Structure the report using the following sections EXACTLY:
   - Overall Status
   - Key Accomplishments (This Week)
   - Current Focus (In Progress)
   - Risks & Blockers (Attention Required)
   - Upcoming Milestones (Next 1–2 Weeks)
   - PM Recommendation

3. Focus on:
   - Outcomes over activities
   - Risks, dependencies, and blockers
   - Clear executive-level language
   - Brevity and scannability

4. In the “Risks & Blockers” section:
   - Clearly label blockers
   - Explain impact if unresolved

5. End with a concise PM Recommendation that advises leadership on next actions or decisions.

Project Data:
{payload}
"""

    client = get_openai_client()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
    )

    return response.choices[0].message.content

