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

def generate_report_llm(payload, audience):
    import os
    import json
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment")

    client = OpenAI(api_key=api_key)

    prompt = f"""
You are a professional project manager.

Audience: {audience}

Generate a weekly status report with exactly these sections:
1. Weekly Accomplishments
2. Ongoing Work
3. Risks / Issues
4. Upcoming Milestones

Rules:
- INTERNAL: detailed, operational
- LEADERSHIP: high-level, no owners
- CUSTOMER: no internal language, no blame, no blockers

Data:
{json.dumps(payload, indent=2)}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        temperature=0.2
    )

    return response.output_text
