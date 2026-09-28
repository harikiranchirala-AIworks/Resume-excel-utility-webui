"""
applications_crm.py
Manages persistent storage and stage pipeline for job applications (Kanban CRM).
"""
import json
import uuid
from datetime import datetime
from pathlib import Path

CRM_FILE = Path(__file__).parent / "applications_crm.json"

VALID_STAGES = ["SAVED", "APPLIED", "INTERVIEWING", "OFFER", "ARCHIVED"]


def load_applications() -> list:
    """Load all tracked job applications from JSON file."""
    if not CRM_FILE.exists():
        return []
    try:
        with open(CRM_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def save_application(app_data: dict) -> dict:
    """Create or update a job application record."""
    applications = load_applications()

    app_id = app_data.get("id") or str(uuid.uuid4())[:8]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    existing_idx = next((i for i, a in enumerate(applications) if a.get("id") == app_id), -1)

    record = {
        "id": app_id,
        "title": str(app_data.get("title", "Untitled Role")).strip(),
        "company": str(app_data.get("company", "Target Company")).strip(),
        "track": str(app_data.get("track", "AI")).strip().upper(),
        "status": str(app_data.get("status", "SAVED")).strip().upper(),
        "salary": str(app_data.get("salary", "Not specified")).strip(),
        "work_mode": str(app_data.get("work_mode", "Hybrid")).strip(),
        "job_url": str(app_data.get("job_url", "")).strip(),
        "jd_text": str(app_data.get("jd_text", "")).strip(),
        "applied_date": str(app_data.get("applied_date", now_str)).strip(),
        "interview_date": str(app_data.get("interview_date", "")).strip(),
        "notes": str(app_data.get("notes", "")).strip(),
        "match_score_pct": app_data.get("match_score_pct", 0),
        "tailored_resume_md": str(app_data.get("tailored_resume_md", "")).strip(),
        "updated_at": now_str
    }

    if record["status"] not in VALID_STAGES:
        record["status"] = "SAVED"

    if existing_idx >= 0:
        applications[existing_idx] = record
    else:
        record["created_at"] = now_str
        applications.insert(0, record)

    with open(CRM_FILE, "w", encoding="utf-8") as f:
        json.dump(applications, f, indent=2, ensure_ascii=False)

    return record


def update_application_status(app_id: str, new_status: str) -> dict:
    """Update the pipeline stage of an application."""
    applications = load_applications()
    status_upper = str(new_status).strip().upper()
    if status_upper not in VALID_STAGES:
        status_upper = "SAVED"

    for app in applications:
        if app.get("id") == app_id:
            app["status"] = status_upper
            app["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(CRM_FILE, "w", encoding="utf-8") as f:
                json.dump(applications, f, indent=2, ensure_ascii=False)
            return app

    return {}


def delete_application(app_id: str) -> bool:
    """Delete an application record."""
    applications = load_applications()
    filtered = [a for a in applications if a.get("id") != app_id]

    if len(filtered) < len(applications):
        with open(CRM_FILE, "w", encoding="utf-8") as f:
            json.dump(filtered, f, indent=2, ensure_ascii=False)
        return True
    return False
